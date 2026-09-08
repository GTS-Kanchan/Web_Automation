"""
conftest.py — pytest-playwright fixtures + enhanced HTML report hooks.
Compatible with pytest-html 4.x (no py.xml dependency).

Migrated from the Selenium suite's conftest.py:
  • `driver` fixture (Selenium WebDriver) -> pytest-playwright's built-in
    `page` fixture (a fresh browser context + page per test function).
  • `browser_type_launch_args` / `browser_context_args` fixtures replace
    utils/driver_factory.py's manual ChromeOptions/FirefoxOptions setup.
  • Browser engine (chromium/firefox/webkit) is now chosen via the
    `--browser` CLI flag (see pytest.ini) instead of the old BROWSER env var.

Report features (unchanged from the Selenium suite):
  • Environment metadata block (browser, URL, run date, Python, OS)
  • Screenshot on every FAILED test — embedded inline in the HTML
  • Marker badge column (smoke / regression / negative)
  • Colour-coded duration column (green <5s, amber <15s, red >=15s)
  • Pass-rate summary banner at top of report
"""

import os
import base64
import json
import platform
import datetime
import sys

import pytest

from utils.auth_state import (
    AuthenticationError,
    ensure_authenticated_state,
    reauthenticate_if_still_stale,
    state_mtime,
)
from utils.config import Config
from utils.error_monitor import check_page_for_errors, ERROR_SCREENSHOT_DIR
from utils.helpers import goto_with_retry
from utils.parallel import worker_id, worker_scoped_dir
from pages.common.login_page import LoginPage

# ══════════════════════════════════════════════════════════════════════════════
# Channel/fixture plugin registration — see fixtures/*.py. These add
# channel-scoped fixtures (sms_channel, correlation_id, test_logger, ...)
# plus `authenticated_storage_state` (fixtures/common_fixtures.py), the
# single-login-per-run authentication fixture that `logged_in_page` /
# `module_logged_in_page` below are built on top of — see
# utils/auth_state.py for the cross-worker login-once mechanism itself.
# ══════════════════════════════════════════════════════════════════════════════
pytest_plugins = [
    "fixtures.common_fixtures",
    "fixtures.sms_fixtures",
    "fixtures.whatsapp_fixtures",
    "fixtures.rcs_fixtures",
    "fixtures.email_fixtures",
]

# Screenshots/error-screenshots are namespaced per xdist worker
# (reports/screenshots/<worker_id>/) so two workers writing a same-named
# screenshot in the same second (e.g. the same parametrized test failing on
# two workers at once) can never collide. worker_id() is "master" outside
# of -n, so a plain single-process `pytest` run is laid out exactly as
# before, just one directory level deeper.
SCREENSHOT_DIR = worker_scoped_dir(os.path.join(os.path.dirname(__file__), "reports", "screenshots"))
os.makedirs(ERROR_SCREENSHOT_DIR, exist_ok=True)

# Populated in pytest_configure from the --browser CLI flag, used in the
# summary banner (replaces the old Config.BROWSER).
_browser_name = "chromium"

# Final pass/fail/skip counts for the summary banner. Populated ONCE, in
# pytest_sessionfinish, from pytest's own aggregated terminalreporter stats
# — NOT hand-incremented per-test in pytest_runtest_makereport. That old
# approach was global mutable state that silently broke under pytest-xdist:
# pytest_runtest_makereport only ever runs inside the WORKER process that
# executed the test, so a worker-local counter dict never reflects what
# happened in the other workers, and the controller process (which is the
# one that actually renders the HTML report) would see a permanently-zero
# count. terminalreporter.stats, by contrast, is populated in the
# controller from every worker's forwarded reports, so it's correct with
# or without -n.
_final_stats = {"passed": 0, "failed": 0, "skipped": 0}


# ══════════════════════════════════════════════════════════════════════════════
# Playwright launch / context configuration
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Headless comes from .env (HEADLESS=true/false), same as the old
    driver_factory.get_driver(). Engine (chromium/firefox/webkit) is chosen
    with `--browser` on the command line — see pytest.ini.

    When running headed (HEADLESS=false — e.g. so a human can watch the
    run or visually compare it against a normal Chrome window),
    --start-maximized is added so the OS gives Chromium its actual
    available desktop area, the same starting point a normal maximized
    Chrome window gets. See browser_context_args below for why this alone
    is not sufficient (Playwright still forces its own viewport unless
    told not to)."""
    args = list(browser_type_launch_args.get("args") or [])
    if not Config.HEADLESS and "--start-maximized" not in args:
        args = args + ["--start-maximized"]
    return {**browser_type_launch_args, "headless": Config.HEADLESS, "args": args}


def _viewport_context_args():
    """Two deliberately different modes, chosen by Config.HEADLESS:

    • Headless (CI / default automated runs) — a FIXED 1920x1080 viewport
      with device_scale_factor=1. There's no real monitor involved, so this
      is fully deterministic across machines, and 1920x1080 matches this
      app's Tailwind desktop breakpoints (lg:hidden etc.).

    • Headed (HEADLESS=false — a human is watching the visible Chromium
      window, e.g. to compare it against a normal Chrome window) —
      no_viewport=True. This tells Playwright NOT to force its own virtual
      viewport size at all; the page's content area just follows whatever
      the real, --start-maximized Chromium window actually is on your real
      screen — exactly what a normal Chrome window does.

      This split exists because forcing a virtual 1920x1080 viewport in
      headed mode broke on a real 1920x1080 monitor running Windows
      display scaling (125%/150% is the default on most laptops/monitors):
      Windows' *logical* desktop area shrinks below 1920x1080 once scaling
      is applied (e.g. ~1536x864 at 125%), so a window that insists on a
      logical 1920x1080 client area literally cannot fit inside the real
      desktop — parts of it render off-screen. A plain Chrome window never
      hits this because it just asks the OS to maximize into whatever the
      real (scaled) desktop area is, instead of requesting a fixed pixel
      size — no_viewport=True + --start-maximized reproduces that same
      behavior for Playwright's Chromium."""
    if Config.HEADLESS:
        return {"viewport": {"width": 1920, "height": 1080}, "device_scale_factor": 1}
    return {"no_viewport": True}


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """accept_downloads=True replaces the old Chrome download-directory
    prefs + CDP override — Playwright captures downloads as events per-page
    (see Helpers.download_via) rather than writing to a fixed OS directory.
    See _viewport_context_args() above for the headless-vs-headed viewport
    split."""
    return {
        **browser_context_args,
        **_viewport_context_args(),
        "accept_downloads": True,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Shared fixtures
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
def login_page(page):
    """Deliberately built on pytest-playwright's own `page` fixture, which
    is a genuinely fresh, unauthenticated context — NOT the shared
    storage_state used by logged_in_page/module_logged_in_page below. This
    fixture (and tests/common/test_login.py, test_forgot_password.py, which
    depend on it) exercises the login form itself, including invalid-
    credential/empty-field negative cases, so it must never start
    pre-authenticated."""
    lp = LoginPage(page)
    lp.navigate()
    return lp


def _open_authenticated_context(browser, storage_state_path):
    """Build a context+page from `storage_state_path` and confirm it's
    actually authenticated (landed inside the app, not bounced back to
    /login). Returns (context, page).

    Session expiration handling (requirement #12): if the cached session
    turns out to be expired, this does exactly ONE controlled
    re-authentication via reauthenticate_if_still_stale() — lock-guarded
    AND mtime-guarded, so even if several contexts hit this at the same
    instant, only one of them performs the real re-login; the rest detect
    that someone else already refreshed the file (its mtime moved past
    what they observed) and just reuse it instead of relogging in
    themselves. It never loops/retries login on its own beyond that one
    attempt, and never sleeps an arbitrary delay; if the retry still isn't
    authenticated, it raises AuthenticationError so the fixture fails
    loudly instead of silently running tests against a logged-out session."""
    def _new_context(path):
        ctx = browser.new_context(
            storage_state=path,
            **_viewport_context_args(),
            accept_downloads=True,
        )
        pg = ctx.new_page()
        # goto_with_retry (utils/helpers.py): a real PLAYWRIGHT_WORKERS=20
        # run showed this exact goto() time out under load (Playwright's
        # plain default here has no retry) even though the same URL loaded
        # fine for every other worker in the same run -- see that module's
        # comment for why only a Playwright TimeoutError gets retried.
        goto_with_retry(pg, Config.BASE_URL)
        return ctx, pg

    observed_mtime = state_mtime()
    context, pg = _new_context(storage_state_path)
    if "login" not in pg.url:
        return context, pg

    # Cached session didn't hold -- controlled single-flight re-auth. Pass
    # the mtime we observed BEFORE opening this context so a concurrent
    # worker that already fixed this can't have its fresh file clobbered.
    context.close()
    refreshed_path = reauthenticate_if_still_stale(browser, observed_mtime)
    context, pg = _new_context(refreshed_path)
    if "login" in pg.url:
        context.close()
        raise AuthenticationError(
            "Re-authentication did not recover a valid session -- still on "
            "/login after a fresh login. Not retrying further."
        )
    return context, pg


@pytest.fixture(scope="function")
def logged_in_page(browser):
    """Equivalent of the old `logged_in_driver` fixture — returns a
    Playwright Page that is already authenticated, WITHOUT performing its
    own UI login. Builds a fresh, isolated context per test (worker-safe:
    no context/page is ever shared across tests or workers) from the
    shared, single-login storage_state (see utils/auth_state.py) instead of
    navigating to /login and submitting credentials every time this fixture
    is used — this is what turns "one login per test" into "one login for
    the entire run" across every test that uses this fixture, directly or
    via module_logged_in_page below."""
    state_path = ensure_authenticated_state(browser)
    context, pg = _open_authenticated_context(browser, state_path)
    yield pg
    context.close()


@pytest.fixture(scope="module")
def module_page(browser):
    """A single Playwright Page shared for an entire test module. Several
    suites in the original Selenium project intentionally run as one
    continuous, stateful browser session — a module-scoped `driver` fixture
    (e.g. test_tags_flow.py, test_sms_sender_id.py) — rather than a fresh
    browser per test function, usually because later tests in the file
    depend on state created by earlier ones (e.g. edit/delete tests acting
    on a record a create test just seeded). This is the Playwright
    equivalent: a module-scoped context + page, built from pytest-playwright's
    session-scoped `browser` fixture using the same viewport/download args as
    the default per-test `page` fixture (see _viewport_context_args())."""
    context = browser.new_context(**_viewport_context_args(), accept_downloads=True)
    pg = context.new_page()
    yield pg
    context.close()


@pytest.fixture(scope="module")
def module_logged_in_page(browser):
    """Module-scoped equivalent of `logged_in_page` — one context/page
    shared by every test function in the module (see module_page's
    docstring above for why some suites need this), authenticated from the
    shared, single-login storage_state instead of performing its own UI
    login. This is the fixture the majority of the suite (SMS/RCS/WhatsApp/
    Email's module-scoped "single sequential flow" files) depends on, so
    this one change is what eliminates the login storm for ~55 test files
    without editing any of them."""
    state_path = ensure_authenticated_state(browser)
    context, pg = _open_authenticated_context(browser, state_path)
    yield pg
    context.close()


def _apply_storage_state_to_page(page, storage_state_path):
    """Replace an ALREADY-OPEN page/context's cookies + localStorage with
    the contents of `storage_state_path`, in place -- used for mid-run
    session recovery (see _recover_if_logged_out below). We can't just open
    a fresh context/page the way _open_authenticated_context() does at
    fixture setup: module-scoped tests already hold a reference to THIS
    EXACT `page` object (module_logged_in_page yields it once for the whole
    module), so recovery has to refresh what that object is authenticated
    as, not replace it."""
    with open(storage_state_path, encoding="utf-8") as f:
        state = json.load(f)
    page.context.clear_cookies()
    if state.get("cookies"):
        page.context.add_cookies(state["cookies"])
    for origin in state.get("origins", []):
        # localStorage is per-origin -- navigate there before setting it so
        # each key lands on the right origin's storage.
        page.goto(origin["origin"])
        for item in origin.get("localStorage", []):
            page.evaluate(
                "([k, v]) => window.localStorage.setItem(k, v)",
                [item["name"], item["value"]],
            )
    # goto_with_retry: see the comment in _open_authenticated_context above
    # -- same load-sensitive goto(), same treatment.
    goto_with_retry(page, Config.BASE_URL)


def _recover_if_logged_out(page):
    """Call at the START of every test that uses a shared authenticated
    page (module_logged_in_page / logged_in_page). _open_authenticated_context()
    above only guards fixture SETUP -- once a module-scoped page has been
    running for a while (a long SMS/RCS/WhatsApp/Email "single sequential
    flow" file, or just real elapsed time / real app session TTL), the
    underlying session can still expire mid-file, silently bouncing the
    shared page to /login with no recovery. Left unhandled, every remaining
    test in that module then fails or errors against a logged-out page --
    exactly the "redirected to /login mid-suite, never logs back in, rest
    of the file fails/skips" failure mode this fixes.

    Same single-flight, lock-guarded, mtime-guarded re-authentication as
    fixture setup (reauthenticate_if_still_stale) -- if several parallel
    workers detect this at the same moment, only one of them performs the
    real re-login; the rest reuse whatever it produces."""
    if "login" not in page.url:
        return
    observed_mtime = state_mtime()
    browser = page.context.browser
    refreshed_path = reauthenticate_if_still_stale(browser, observed_mtime)
    _apply_storage_state_to_page(page, refreshed_path)
    if "login" in page.url:
        raise AuthenticationError(
            "Mid-run session recovery failed -- still on /login after "
            "re-authenticating. Not retrying further."
        )


@pytest.fixture(autouse=True)
def _recover_shared_session(request):
    """Autouse, function-scoped: runs before every test in the suite.
    Cheap no-op for tests that don't use a shared authenticated page (e.g.
    test_login.py/test_forgot_password.py, which must stay unauthenticated
    -- they don't request logged_in_page/module_logged_in_page so this
    exits immediately). For tests that do, this is what catches a session
    that expired mid-module and recovers it BEFORE the test body runs,
    instead of letting the test fail/error against a logged-out page.

    request.getfixturevalue() on an already-created module-scoped fixture
    returns the cached page rather than creating a second one, so this is
    safe to call regardless of fixture declaration order."""
    for fixture_name in ("module_logged_in_page", "logged_in_page"):
        if fixture_name in request.fixturenames:
            _recover_if_logged_out(request.getfixturevalue(fixture_name))
            break
    yield


# ══════════════════════════════════════════════════════════════════════════════
# Markers + environment metadata
# ══════════════════════════════════════════════════════════════════════════════

# ── Configurable worker count (PLAYWRIGHT_WORKERS) ─────────────────────────
# NOTE: this is deliberately NOT implemented as a conftest.py hook.
# pytest-xdist decides whether/how many workers to fork inside its own
# `pytest_cmdline_main` hookimpl (tryfirst=True), which reads
# `config.option.numprocesses` as parsed from the raw command line BEFORE
# any conftest.py's `pytest_configure` runs, and before
# `pytest_load_initial_conftests` even applies to this file (that hook only
# affects conftests that haven't been loaded yet — not the rootdir conftest
# it's defined in). Both approaches were implemented and empirically
# verified NOT to trigger worker forking (`pytest` ran single-process, no
# gw0/gw1 in the output, despite PLAYWRIGHT_WORKERS being set) before this
# comment replaced them. The only reliable place to turn PLAYWRIGHT_WORKERS
# into an actual `-n`/`--dist` flag is before the pytest process's argv is
# built — see scripts/run_tests.py, which every documented run command in
# this project uses. Calling `pytest -n <N> --dist loadscope` directly
# still works exactly as pytest-xdist has always supported; PLAYWRIGHT_WORKERS
# is purely a convenience on top of that via the wrapper script.


def pytest_configure(config):
    global _browser_name

    config.addinivalue_line("markers", "smoke: core smoke tests")
    config.addinivalue_line("markers", "regression: full regression suite")
    config.addinivalue_line("markers", "negative: negative / boundary tests")
    # Channel + feature tags (requirement: run e.g. `pytest -m sms`,
    # `pytest -m "sms and smoke"`, `pytest -m "sms or whatsapp"` — the
    # pytest-marker equivalent of the spec's --grep @sms syntax). Also
    # declared in pytest.ini; declared here too so a marker used before
    # pytest.ini is read (or in a context that only loads this conftest)
    # never produces an "unknown marker" warning.
    for tag in (
        "sms", "whatsapp", "rcs", "email",
        "campaign", "template", "sender_id", "messaging", "report", "opt_out",
    ):
        config.addinivalue_line("markers", f"{tag}: {tag} channel/feature tag")


    try:
        _browser_name = config.getoption("--browser") or "chromium"
        if isinstance(_browser_name, list):  # pytest-playwright allows repeating --browser
            _browser_name = _browser_name[0] if _browser_name else "chromium"
    except (ValueError, KeyError):
        _browser_name = "chromium"

    meta = getattr(config, "_metadata", None)
    if meta is not None:
        meta["Project"]    = "CPaaS+ Playwright Automation"
        meta["Target URL"] = Config.BASE_URL
        meta["Browser"]    = _browser_name.capitalize()
        meta["Headless"]   = str(Config.HEADLESS)
        meta["Python"]     = sys.version.split()[0]
        meta["Platform"]   = platform.platform()
        meta["Run date"]   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        meta["Tester"]     = os.getenv("TESTER_NAME", "Automation Suite")


# ══════════════════════════════════════════════════════════════════════════════
# Screenshot on failure + marker/duration tagging
# ══════════════════════════════════════════════════════════════════════════════

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report  = outcome.get_result()

    # Tag marker on the report object
    marker = "—"
    for m in ("smoke", "regression", "negative"):
        if item.get_closest_marker(m):
            marker = m
            break
    report._marker = marker

    # Grab the Playwright Page — works whether the test asked for the raw
    # `page` fixture directly, or a page-object fixture (login_page,
    # dashboard, etc.) that wraps a Page as `.page`.
    pw_page = None

    # Pass 1: direct funcargs lookup (fast path — pytest-playwright's own
    # `page` fixture, if the test requested it directly)
    val = item.funcargs.get("page")
    if val is not None:
        pw_page = val

    # Pass 2: scan ALL funcargs values for anything wrapping a Page (our
    # BasePage subclasses expose `.page`)
    if pw_page is None:
        for val in item.funcargs.values():
            p = getattr(val, "page", None)
            if p is not None:
                pw_page = p
                break

    # Pass 3: for class-based / module-scoped tests where funcargs may be
    # empty, ask pytest's fixture manager directly via getfixturevalue()
    #
    # IMPORTANT: only for a fixture this test ACTUALLY requested (directly
    # or transitively) -- req.fixturenames reflects that closure without
    # instantiating anything. getfixturevalue() itself does not just look
    # up an existing value: calling it on a fixture the test never asked
    # for CREATES that fixture on the spot, which for "page"/"logged_in_page"
    # cascades into launching a real Chromium browser. Non-UI suites (e.g.
    # tests/sms/api, which use Playwright's APIRequestContext and never
    # touch a Page) have no page/logged_in_page anywhere in their fixture
    # graph, so Pass 1 and 2 above always miss and this fallback used to
    # fire unconditionally on every phase of every test -- silently
    # launching (and, in headed mode, visibly popping open) a browser
    # window for pure API tests that never wanted one. Guarding on
    # fixturenames keeps this fallback working exactly as before for
    # tests that genuinely use page/logged_in_page, while making it a
    # true no-op for everything else.
    if pw_page is None:
        req = getattr(item, "_request", None)
        if req is not None:
            for fname in ("page", "logged_in_page"):
                if fname not in req.fixturenames:
                    continue
                try:
                    val = req.getfixturevalue(fname)
                    if val is not None:
                        pw_page = getattr(val, "page", val)
                        break
                except Exception:
                    pass

    # ── Error monitor: check for platform errors after every call phase ───────
    if report.when == "call" and pw_page:
        try:
            error_capture = check_page_for_errors(pw_page, test_name=item.name)
            if error_capture:
                # Build the embedded-image block (same style as failure screenshots)
                img_tag = ""
                try:
                    if os.path.isfile(error_capture.path):
                        with open(error_capture.path, "rb") as f:
                            b64 = base64.b64encode(f.read()).decode()
                        img_tag = (
                            '<br><img src="data:image/png;base64,' + b64 + '" '
                            'style="max-width:100%;border:1px solid #fca5a5;'
                            'border-radius:6px;margin-top:6px"/>'
                        )
                except Exception:
                    pass

                err_html = (
                    '<div style="margin-top:8px;padding:10px;background:#fef2f2;'
                    'border:1px solid #fca5a5;border-radius:6px">'
                    '<b style="color:#dc2626">&#9888; Platform Error Detected!</b><br>'
                    '<span style="font-size:12px;color:#7f1d1d">'
                    'Pattern: <code>' + error_capture.pattern[:80] + '</code><br>'
                    'URL: ' + error_capture.url + '<br>'
                    'File: <code>' + error_capture.path + '</code>'
                    '</span>'
                    + img_tag +
                    '</div>'
                )
                extras = getattr(report, "extras", [])
                try:
                    from pytest_html import extras as html_extras
                    extras.append(html_extras.html(err_html))
                except ImportError:
                    pass
                report.extras = extras
        except Exception:
            pass

    # ── Screenshot on failure ─────────────────────────────────────────────────
    if report.when == "call" and report.failed:
        if pw_page:
            try:
                ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                safe     = "".join(c if c.isalnum() or c in "-_" else "_" for c in item.name)
                path     = os.path.join(SCREENSHOT_DIR, f"{safe}_{ts}.png")
                pw_page.screenshot(path=path)

                with open(path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()

                img_html = (
                    '<div style="margin-top:8px">'
                    '<b>📸 Screenshot at failure:</b><br>'
                    f'<img src="data:image/png;base64,{b64}" '
                    'style="max-width:100%;border:1px solid #ccc;'
                    'border-radius:6px;margin-top:6px"/>'
                    '</div>'
                )
                extras = getattr(report, "extras", [])
                try:
                    from pytest_html import extras as html_extras
                    extras.append(html_extras.html(img_html))
                except ImportError:
                    pass
                report.extras = extras
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════════════════════
# Custom table columns — Marker + Duration (pytest-html 4.x compatible)
# ══════════════════════════════════════════════════════════════════════════════

def pytest_html_results_table_header(cells):
    cells.insert(2, '<th class="sortable" col="marker">Marker</th>')
    cells.insert(3, '<th class="sortable numeric" col="duration">Duration</th>')


def pytest_html_results_table_row(report, cells):
    # ── Marker badge ──
    marker = getattr(report, "_marker", "—")
    colour = {
        "smoke":      "#2563eb",
        "regression": "#7c3aed",
        "negative":   "#dc2626",
    }.get(marker, "#6b7280")
    badge = (
        f'<span style="background:{colour};color:#fff;padding:2px 8px;'
        f'border-radius:9999px;font-size:11px;font-weight:600;'
        f'text-transform:uppercase">{marker}</span>'
    )
    cells.insert(2, f'<td>{badge}</td>')

    # ── Duration ──
    dur = getattr(report, "duration", 0) or 0
    dur_col = "#16a34a" if dur < 5 else ("#d97706" if dur < 15 else "#dc2626")
    cells.insert(3, (
        f'<td><span style="color:{dur_col};font-weight:600">'
        f'{dur:.2f}s</span></td>'
    ))


# ══════════════════════════════════════════════════════════════════════════════
# Report title
# ══════════════════════════════════════════════════════════════════════════════

def pytest_html_report_title(report):
    report.title = "CPaaS+ Test Automation Report (Playwright)"


# ══════════════════════════════════════════════════════════════════════════════
# Summary banner (pass-rate widget at top of report)
# ══════════════════════════════════════════════════════════════════════════════

def pytest_sessionfinish(session, exitstatus):
    """Runs once, in the controller process (with or without -n), after all
    workers have finished and pytest's own terminalreporter has aggregated
    every worker's results. This is the xdist-safe replacement for the old
    per-test _results counter — see the comment where _final_stats is
    declared above."""
    terminalreporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if terminalreporter is None:
        return
    stats = getattr(terminalreporter, "stats", {})
    _final_stats["passed"]  = len(stats.get("passed", []))
    _final_stats["failed"]  = len(stats.get("failed", [])) + len(stats.get("error", []))
    _final_stats["skipped"] = len(stats.get("skipped", []))


def pytest_html_results_summary(prefix, summary, postfix):
    passed  = _final_stats["passed"]
    failed  = _final_stats["failed"]
    skipped = _final_stats["skipped"]
    total   = passed + failed + skipped
    rate    = round(passed / total * 100, 1) if total else 0
    rate_col = "#16a34a" if rate >= 90 else ("#d97706" if rate >= 70 else "#dc2626")

    browser_str = _browser_name.capitalize()
    run_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    banner = (
        "<div style=\"background:#f8fafc;border:1px solid #e2e8f0;"
        "border-radius:10px;padding:20px 28px;margin-bottom:20px;"
        "display:flex;gap:36px;align-items:center;"
        "font-family:system-ui,sans-serif;flex-wrap:wrap\">"
        f"<div style=\"text-align:center;min-width:90px\">"
        f"<div style=\"font-size:42px;font-weight:800;color:{rate_col}\">{rate}%</div>"
        "<div style=\"font-size:12px;color:#64748b;letter-spacing:1px\">PASS RATE</div>"
        "</div>"
        "<div style=\"display:flex;gap:24px;flex-wrap:wrap\">"
        f"<div style=\"text-align:center\">"
        f"<div style=\"font-size:28px;font-weight:700;color:#16a34a\">{passed}</div>"
        "<div style=\"font-size:11px;color:#64748b\">PASSED</div></div>"
        f"<div style=\"text-align:center\">"
        f"<div style=\"font-size:28px;font-weight:700;color:#dc2626\">{failed}</div>"
        "<div style=\"font-size:11px;color:#64748b\">FAILED</div></div>"
        f"<div style=\"text-align:center\">"
        f"<div style=\"font-size:28px;font-weight:700;color:#d97706\">{skipped}</div>"
        "<div style=\"font-size:11px;color:#64748b\">SKIPPED</div></div>"
        f"<div style=\"text-align:center\">"
        f"<div style=\"font-size:28px;font-weight:700;color:#475569\">{total}</div>"
        "<div style=\"font-size:11px;color:#64748b\">TOTAL</div></div>"
        "</div>"
        f"<div style=\"margin-left:auto;font-size:12px;color:#94a3b8\">"
        f"{run_time} | {browser_str} | {Config.BASE_URL}"
        "</div></div>"
    )
    prefix.append(banner)
