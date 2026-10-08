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
import html
import json
import platform
import datetime
import subprocess
import sys
import time

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

from reporting import collector as _reporting_collector
from reporting import summary as _reporting_summary
from reporting import history as _reporting_history
from reporting import trend as _reporting_trend
from reporting import artifacts as _reporting_artifacts
from reporting import html_report as _reporting_html

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
# <REPORTS_DIR>/screenshots/<worker> -- REPORTS_DIR is the instance-aware
# root (utils/config.py): the flat "reports/screenshots" path unless
# INSTANCE is set, in which case it nests under reports/<env>/<instance>/
# [<run-id>]/screenshots instead.
SCREENSHOT_DIR = worker_scoped_dir(os.path.join(Config.REPORTS_DIR, "screenshots"))
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

# Wall-clock start of this pytest invocation (controller process) --
# used only for the summary.json "duration_seconds" field (Environment
# and Instance Configuration work, requirement #14). Set in
# pytest_configure, read back in pytest_sessionfinish.
_RUN_START_TIME = time.time()

# Advanced Reporting work -- populated by the new pytest_runtest_logreport
# hook below (xdist-safe: on the controller, xdist replays each worker's
# report through this SAME hook -- see worker_testreport() in
# xdist/dsession.py, which sets report.node before calling
# pytest_runtest_logreport -- so this list is only ever meaningfully
# populated in the controller process; a worker process's own copy is
# never read). Consumed by pytest_sessionfinish -> _build_reporting_context
# -> (stashed) -> pytest_unconfigure -> _finalize_reports.
_reporting_records = []

# Platform-error captures (utils.error_monitor.ErrorCapture), appended
# from the existing error-monitor block in pytest_runtest_makereport
# below -- feeds reporting.summary.platform_health(). Same xdist-safety
# reasoning as _reporting_records.
_platform_error_captures = []

# Set by pytest_sessionfinish, consumed by pytest_unconfigure (file I/O --
# history/HTML/artifact copying -- is deferred to pytest_unconfigure so it
# runs AFTER pytest-html and the junitxml plugin have both finished
# writing their own files; see _finalize_reports()'s docstring).
_final_report_context = None


def _report_worker_id(report) -> str:
    """"gw0"/"gw1"/... under -n, "master" otherwise -- NOT the same as
    utils.parallel.worker_id() when called from the CONTROLLER process
    (that always returns "master" there; the actual worker that ran this
    particular test is only recoverable from the report object itself,
    via the WorkerController xdist attaches as report.node before
    replaying the hook on the controller -- see worker_testreport() in
    xdist/dsession.py)."""
    node = getattr(report, "node", None)
    gateway = getattr(node, "gateway", None)
    gw_id = getattr(gateway, "id", None)
    return gw_id or worker_id()


def _report_exc_type_and_message(report):
    """Best-effort (exc_type, message) from a failed/skipped report's
    longrepr. Never raises -- worst case returns ("", str(longrepr))."""
    longrepr = getattr(report, "longrepr", None)
    if longrepr is None:
        return "", ""
    crash = getattr(longrepr, "reprcrash", None)
    full = getattr(crash, "message", None) if crash else None
    if full is None:
        full = str(longrepr)
    if ":" in full:
        exc_type, message = full.split(":", 1)
        return exc_type.strip(), message.strip()
    return "", full.strip()


def _report_status(report) -> str:
    """passed/failed/skipped, upgraded to xfailed/xpassed when pytest
    marked the report as an xfail outcome (requirement #29: "the
    collector must correctly handle ... xfail/xpass")."""
    if getattr(report, "wasxfail", None) is not None or report.keywords.get("xfail"):
        if report.skipped:
            return "xfailed"
        if report.passed:
            return "xpassed"
    if report.failed:
        return "failed"
    if report.skipped:
        return "skipped"
    return "passed"


def pytest_runtest_logreport(report):
    """Collects ONE canonical record per test (requirement #29/#30):
      - "call" phase: the normal pass/fail/skip/xfail/xpass outcome.
      - "setup" phase: ONLY when it itself failed or skipped (a fixture
        error, or a skip decided before the test body ever ran) -- a
        passing setup is not a separate test outcome.
      - "teardown" phase: ONLY when it itself failed -- recorded as an
        ADDITIONAL record (teardown failing after a passing call is a
        real, distinct problem worth surfacing, not a duplicate of the
        call-phase result).
    xdist-safe: see _reporting_records' own comment above."""
    if report.when == "call":
        pass
    elif report.when == "setup" and (report.failed or report.skipped):
        pass
    elif report.when == "teardown" and report.failed:
        pass
    else:
        return

    status = _report_status(report)
    exc_type, message = ("", "")
    longrepr_text = ""
    if status in ("failed", "skipped"):
        exc_type, message = _report_exc_type_and_message(report)
        longrepr_text = str(getattr(report, "longrepr", "") or "")

    worker = _report_worker_id(report)
    screenshot = getattr(report, "_screenshot_rel", None)
    log_rel = os.path.join("logs", f"{worker}.jsonl")
    log_path = log_rel if os.path.isfile(os.path.join(Config.REPORTS_DIR, log_rel)) else None

    record = _reporting_collector.build_record(
        nodeid=report.nodeid,
        status=status,
        duration=getattr(report, "duration", 0.0),
        when=report.when,
        marker=getattr(report, "_marker", "-"),
        worker=worker,
        exc_type=exc_type,
        message=message,
        longrepr_text=longrepr_text,
        screenshot=screenshot,
        log=log_path,
    )
    _reporting_records.append(record)



def _git_commit_short():
    """Short git commit hash for the current checkout, or None if this
    isn't a git checkout / git isn't available -- never raises, since a
    missing commit/build number is explicitly optional (requirement #13:
    "if available")."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            commit = result.stdout.strip()
            return commit or None
    except Exception:
        pass
    return None


def _channel_from_args(config):
    """Best-effort channel label for summary.json (requirement #14: "Use
    the actual collected/executed test counts... must work for SMS, RCS,
    WhatsApp, Email, Common, Chatbot, Full suite... do not make it
    SMS-specific"). Derived from whatever path(s) were given on the
    pytest command line -- `pytest tests/sms` -> "sms", `pytest
    tests/sms tests/rcs` -> "sms+rcs", no path / `pytest tests` -> "full
    suite". Purely a label for the summary file; never used to change
    test SELECTION, which is entirely pytest's own job."""
    args = [a for a in getattr(config, "args", []) if not a.startswith("-")]
    if not args:
        return "full suite"
    channels = []
    for a in args:
        norm = a.replace("\\", "/").strip("/")
        parts = norm.split("/")
        if parts[0] == "tests" and len(parts) > 1:
            channels.append(parts[1])
        elif norm == "tests":
            return "full suite"
        else:
            channels.append(os.path.basename(norm) or norm)
    # de-dupe while preserving order
    seen = []
    for c in channels:
        if c not in seen:
            seen.append(c)
    return "+".join(seen) if seen else "full suite"


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
        # Environment and Instance Configuration work, requirement #13:
        # show which real environment/instance this run targeted, right
        # in the HTML report's own metadata table -- never a secret (see
        # utils.config.is_secret_name/mask_value; none of these fields are
        # ever masked because none of their NAMES match a secret marker).
        meta["Environment"] = Config.ENV
        meta["Instance"]    = Config.INSTANCE or "(none)"
        meta["Target URL"] = Config.BASE_URL
        meta["Browser"]    = _browser_name.capitalize()
        meta["Headless"]   = str(Config.HEADLESS)
        workers = config.getoption("numprocesses", default=None) if hasattr(config.option, "numprocesses") else None
        meta["Workers"]    = str(workers) if workers else "1 (no -n)"
        meta["Python"]     = sys.version.split()[0]
        meta["Platform"]   = platform.platform()
        meta["Run date"]   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        meta["Tester"]     = os.getenv("TESTER_NAME", "Automation Suite")
        git_commit = _git_commit_short()
        if git_commit:
            meta["Git commit"] = git_commit


# ══════════════════════════════════════════════════════════════════════════════
# JSON -> syntax-highlighted HTML, for the "Response" extras block below
# ══════════════════════════════════════════════════════════════════════════════

_JSON_KEY_COLOR     = "#0f766e"   # teal
_JSON_STRING_COLOR  = "#b45309"   # amber
_JSON_LITERAL_COLOR = "#7c3aed"   # violet (numbers / true / false / null)
_JSON_PUNCT_COLOR   = "#64748b"   # slate (braces / brackets / commas)


def _json_to_html(value, indent=0):
    """Render a parsed JSON value as indented, colour-coded HTML.

    Walks the actual Python object (not the dumped text), so every string
    is coloured/escaped as a single atomic unit -- a phone number, UUID or
    timestamp INSIDE a string can never be mistaken for a separate numeric
    literal the way a regex pass over already-formatted text can (that
    exact bug was caught before this shipped: a regex-based version here
    reached inside quoted values and mis-coloured digits like the "4131"
    inside a message_id UUID, or the digits of a phone number)."""
    pad = "  " * indent
    pad_in = "  " * (indent + 1)
    punct = lambda s: f'<span style="color:{_JSON_PUNCT_COLOR}">{s}</span>'

    if isinstance(value, dict):
        if not value:
            return punct("{}")
        items = []
        for k, v in value.items():
            key_html = (
                f'<span style="color:{_JSON_KEY_COLOR}">'
                f'&quot;{html.escape(str(k))}&quot;</span>'
            )
            items.append(f"{pad_in}{key_html}{punct(':')} {_json_to_html(v, indent + 1)}")
        body = punct(",") + "\n"
        body = body.join(items)
        return punct("{") + "\n" + body + "\n" + pad + punct("}")

    if isinstance(value, list):
        if not value:
            return punct("[]")
        items = [f"{pad_in}{_json_to_html(v, indent + 1)}" for v in value]
        body = (punct(",") + "\n").join(items)
        return punct("[") + "\n" + body + "\n" + pad + punct("]")

    if isinstance(value, str):
        return (
            f'<span style="color:{_JSON_STRING_COLOR}">'
            f'&quot;{html.escape(value)}&quot;</span>'
        )

    if isinstance(value, bool):
        return f'<span style="color:{_JSON_LITERAL_COLOR}">{"true" if value else "false"}</span>'

    if value is None:
        return f'<span style="color:{_JSON_LITERAL_COLOR}">null</span>'

    # int / float
    return f'<span style="color:{_JSON_LITERAL_COLOR}">{value}</span>'


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

    # ── Surface record_property("Response", ...) in the HTML report ───────────
    # record_property() values land in JUnit XML / item.user_properties, but
    # pytest-html's per-test "Log" section only shows captured stdout/logging
    # -- it never renders user_properties, so a passing SMS API test (see
    # tests/sms/api/*.py, which all call record_property("Response",
    # response.text) right after every api_client call) showed nothing
    # ("No log output captured.") even though the property was recorded.
    # report.extras (via pytest_html.extras.html(...)) is this suite's
    # already-established, confirmed-working mechanism for visible per-test
    # content -- it's exactly how the failure-screenshot block below renders
    # -- so mirror that here instead of relying on record_property's own
    # (non-existent) HTML rendering. Runs on every outcome (pass/fail/skip),
    # not just report.when == "call" failures, since the goal is specifically
    # to make a PASSING test's response visible too.
    if report.when == "call":
        try:
            response_text = None
            for pname, pval in getattr(item, "user_properties", []):
                if pname == "Response":
                    response_text = pval
                    break
            if response_text is not None:
                # Pretty-print + colour if it parses as JSON (the common
                # case for this suite's APIs); fall back to the raw text,
                # HTML-escaped but otherwise untouched, for a non-JSON
                # body so nothing is ever silently dropped.
                try:
                    parsed = json.loads(response_text)
                    body_html = _json_to_html(parsed)
                    label = "Response (JSON):"
                except (TypeError, ValueError):
                    body_html = html.escape(str(response_text))
                    label = "Response:"

                resp_html = (
                    '<div style="margin-top:8px;padding:10px;background:#f8fafc;'
                    'border:1px solid #cbd5e1;border-radius:6px">'
                    f'<b>{label}</b>'
                    '<pre style="white-space:pre-wrap;word-break:break-word;'
                    'margin:6px 0 0;font-size:12px;line-height:1.5">' + body_html + '</pre>'
                    '</div>'
                )
                extras = getattr(report, "extras", [])
                try:
                    from pytest_html import extras as html_extras
                    extras.append(html_extras.html(resp_html))
                    report.extras = extras
                except ImportError:
                    pass
        except Exception:
            pass

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
    # true no-op for everything else. "module_logged_in_page" added
    # alongside the other two: a real gap this surfaced -- a test that
    # requests the shared module-scoped page directly (rather than via a
    # module-scoped page-object fixture, whose funcargs value already
    # has a `.page` attribute and is caught by Pass 2 above) produced NO
    # failure screenshot at all, since none of the three passes above
    # recognized it under any of its usual shapes.
    if pw_page is None:
        req = getattr(item, "_request", None)
        if req is not None:
            for fname in ("page", "logged_in_page", "module_logged_in_page"):
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
                _platform_error_captures.append({
                    "pattern": error_capture.pattern,
                    "test": item.name,
                    "url": error_capture.url,
                })
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
                # pytest-rerunfailures re-executes a failed item's "call"
                # phase in place under the SAME nodeid, so without a
                # distinguishing marker a retry's screenshot could land on
                # the same filename as the initial attempt's if both land
                # in the same wall-clock second (the timestamp below
                # already makes that rare, but not impossible). The
                # plugin tracks the current attempt on item.execution_count
                # (1 = first/only attempt, 2 = first rerun, ...) -- only
                # tag the filename when that's > 1, so a normal run with
                # no reruns (the common case, and every run before this
                # feature existed) keeps the exact same filename format as
                # before.
                attempt      = getattr(item, "execution_count", 1)
                attempt_tag  = f"_retry{attempt - 1}" if attempt > 1 else ""
                ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                safe     = "".join(c if c.isalnum() or c in "-_" else "_" for c in item.name)
                path     = os.path.join(SCREENSHOT_DIR, f"{safe}_{ts}{attempt_tag}.png")
                pw_page.screenshot(path=path)
                # Advanced Reporting work -- relative to REPORTS_DIR, so the
                # dashboard HTML (which lives under reports/current/ and
                # reports/runs/<run-id>/, both siblings of screenshots/) can
                # link to it portably instead of embedding an absolute path.
                try:
                    report._screenshot_rel = os.path.relpath(path, Config.REPORTS_DIR)
                except ValueError:
                    report._screenshot_rel = None

                with open(path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()

                attempt_label = f" (retry {attempt - 1})" if attempt > 1 else ""
                img_html = (
                    '<div style="margin-top:8px">'
                    f'<b>📸 Screenshot at failure{attempt_label}:</b><br>'
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

    _write_summary_json(session)

    # Advanced Reporting work -- build the context now (while we still
    # have `session`), but defer actually WRITING any of it to disk until
    # pytest_unconfigure (see _finalize_reports()'s docstring for why).
    global _final_report_context
    try:
        _final_report_context = _build_reporting_context(session)
    except Exception as exc:  # noqa: BLE001 -- never let reporting break the run
        print(f"[reporting] REPORT_GENERATION_FAILED (context build): {exc}", file=sys.stderr)
        _final_report_context = None


def pytest_unconfigure(config):
    """Fires once per process, LAST -- including after pytest-html and
    the junitxml plugin have both finished writing their own files. A
    worker process under xdist also calls this; `_final_report_context`
    is only ever non-None in the controller (it's set from
    pytest_sessionfinish, itself gated on the same terminalreporter-
    is-None check every other controller-only step in this file uses),
    so a worker's call here is always a no-op."""
    ctx = globals().get("_final_report_context")
    if not ctx:
        return
    _finalize_reports(ctx)


def _derive_test_type(config) -> str:
    """Derived from the actual `-m` marker expression pytest was invoked
    with (never hardcoded, never a second selection mechanism -- this is
    a LABEL only, read back from pytest's own already-applied selection).
    "full" when no -m was given, matching scripts/run_tests.py's own
    smoke/regression/full vocabulary (CI/CD work, requirement #14;
    Advanced Reporting work, requirement #4)."""
    markexpr = (config.getoption("markexpr", default="") or "").strip()
    if not markexpr:
        return "full"
    return markexpr


def _git_branch():
    """Short-circuits to BITBUCKET_BRANCH when set (CI/CD work,
    Advanced Reporting requirement #25) -- a detached-HEAD checkout (the
    normal state for a CI runner) has no real local branch name, so the
    CI-provided value is authoritative there; falls back to a real git
    lookup for local runs, then to None."""
    ci_branch = os.environ.get("BITBUCKET_BRANCH", "").strip()
    if ci_branch:
        return ci_branch
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
            return branch or None
    except Exception:
        pass
    return None


def _ci_metadata() -> dict:
    """Advanced Reporting work, requirement #25: capture Bitbucket's own
    CI variables ONLY IF they're actually present -- "Not available"
    (never a crash, never a fabricated value) when running locally, where
    none of these exist. The SAME reporting code must work identically
    both places."""
    def _env_or_na(name):
        value = os.environ.get(name, "").strip()
        return value or "Not available"

    return {
        "pipeline_id": _env_or_na("BITBUCKET_PR_ID"),
        "build_number": _env_or_na("BITBUCKET_BUILD_NUMBER"),
        "repo_slug": _env_or_na("BITBUCKET_REPO_SLUG"),
    }


def _build_reporting_context(session):
    """Assembles everything the Advanced Reporting work's HTML/JSON
    artifacts need, from the records _reporting_records/
    _platform_error_captures already collected during the run, PLUS
    history/trend lookups against reports/history/ (filesystem-based,
    requirement #22). Does NOT write any file -- see _finalize_reports(),
    called later from pytest_unconfigure, for why that's deferred.

    Returns None (and the caller skips finalization entirely) when this
    isn't the controller process -- callers already only reach this point
    after the same terminalreporter-is-None xdist-worker guard every
    other session-finish step in this file already relies on."""
    workers = session.config.getoption("numprocesses", default=None) \
        if hasattr(session.config.option, "numprocesses") else None
    test_type = _derive_test_type(session.config)
    channel = _channel_from_args(session.config)
    started_at_iso = datetime.datetime.fromtimestamp(_RUN_START_TIME).isoformat(timespec="seconds")
    finished_at_iso = datetime.datetime.now().isoformat(timespec="seconds")
    ci = _ci_metadata()

    meta = {
        "run_id": Config.RUN_ID,
        "environment": Config.ENV,
        "instance": Config.INSTANCE or None,
        "channel": channel,
        "test_type": test_type,
        "git_commit": _git_commit_short() or "Not available",
        "git_branch": _git_branch() or "Not available",
        "pipeline_id": ci["pipeline_id"],
        "build_number": ci["build_number"],
        "started_at": started_at_iso,
        "finished_at": finished_at_iso,
        "duration_seconds": round(time.time() - _RUN_START_TIME, 1),
        "workers": workers or 1,
        "browser": (globals().get("_browser_name") or "chromium"),
        "headless": bool(Config.HEADLESS),
    }

    # Snapshot the records list NOW -- nothing else appends to it after
    # sessionfinish, but copying defensively costs nothing and protects
    # against a future hook ordering change.
    records = list(_reporting_records)

    summary_doc = _reporting_summary.build_summary(records, meta)
    channel_summary = _reporting_summary.group_by(records, "channel")
    feature_summary = _reporting_summary.group_by(records, "feature")
    slowest = _reporting_summary.slowest(records)
    duration_stats = _reporting_summary.duration_stats(records)
    platform_health = _reporting_summary.platform_health(_platform_error_captures)
    dlr_summary = _reporting_summary.dlr_summary(records)

    current_tests = {r["test"]: r["status"] for r in records}
    previous = _reporting_history.load_previous_comparable(
        Config.REPORTS_DIR, meta["environment"], meta["instance"],
        meta["channel"], meta["test_type"], exclude_run_id=meta["run_id"],
    )
    trend_result = _reporting_trend.compute_new_recurring_recovered(current_tests, previous)
    history_records = _reporting_history.load_all_comparable(
        Config.REPORTS_DIR, meta["environment"], meta["instance"],
        meta["channel"], meta["test_type"], exclude_run_id=meta["run_id"],
    )
    flaky = _reporting_trend.compute_flaky(history_records, current_tests)

    failures_json = []
    new_set = set(trend_result["new"])
    recurring_set = set(trend_result["recurring"])
    for r in records:
        if r["status"] != "failed":
            continue
        entry = dict(r)
        entry["is_new"] = r["test"] in new_set
        entry["is_recurring"] = r["test"] in recurring_set
        failures_json.append(entry)

    return {
        "meta": meta,
        "records": records,
        "summary": summary_doc,
        "channel_summary": channel_summary,
        "feature_summary": feature_summary,
        "slowest": slowest,
        "duration_stats": duration_stats,
        "platform_health": platform_health,
        "dlr_summary": dlr_summary,
        "trend": trend_result,
        "flaky": flaky,
        "failures_json": failures_json,
    }


def _finalize_reports(ctx: dict) -> None:
    """Writes every Advanced Reporting artifact to disk. Deliberately
    called from pytest_unconfigure (not pytest_sessionfinish) so it runs
    AFTER pytest-html and the junitxml plugin have both finished writing
    reports/test_report.html and reports/junit.xml -- copying those files
    any earlier risks copying a not-yet-finalized version.

    requirement #31: report generation must never hide a test failure --
    this function cannot change pytest's exit status (pytest_unconfigure
    has no such hook), so any exception here is caught, logged as
    REPORT_GENERATION_FAILED, and swallowed; it can never flip a failed
    run into a reported "success"."""
    try:
        reports_root = Config.REPORTS_DIR
        run_id = ctx["meta"]["run_id"]

        # 1. summary.json + failures.json -- the source of truth
        #    (requirement #5/#21), written to BOTH reports/current/ and
        #    reports/runs/<run_id>/.
        run_dir = _reporting_artifacts.run_dir(reports_root, run_id)
        current_dir = _reporting_artifacts.current_dir(reports_root)
        for target_dir in (run_dir, current_dir):
            with open(os.path.join(target_dir, "summary.json"), "w", encoding="utf-8") as fh:
                json.dump(ctx["summary"], fh, indent=2)
            with open(os.path.join(target_dir, "failures.json"), "w", encoding="utf-8") as fh:
                json.dump(ctx["failures_json"], fh, indent=2)

        # 2. Advanced dashboard HTML -- presentation layer only, built
        #    entirely from the dicts already written above (requirement:
        #    "make summary.json/failures.json the source of truth").
        dashboard_html = _reporting_html.render_html({
            "summary": ctx["summary"],
            "channel_summary": ctx["channel_summary"],
            "feature_summary": ctx["feature_summary"],
            "failures": ctx["records"],
            "trend": ctx["trend"],
            "flaky": ctx["flaky"],
            "slowest": ctx["slowest"],
            "duration_stats": ctx["duration_stats"],
            "platform_health": ctx["platform_health"],
            "dlr_summary": ctx["dlr_summary"],
        })
        for target_dir in (run_dir, current_dir):
            with open(os.path.join(target_dir, "dashboard.html"), "w", encoding="utf-8") as fh:
                fh.write(dashboard_html)

        # 3. Copy the EXISTING pytest-html / junitxml outputs alongside
        #    the new artifacts (requirement #33: backward compatibility --
        #    reports/test_report.html keeps being generated exactly as
        #    before; this only additionally copies it next to the new
        #    per-run artifacts, never replaces it).
        _reporting_artifacts.publish_files(reports_root, run_id, {
            "test_report.html": os.path.join(reports_root, "test_report.html"),
            "junit.xml": os.path.join(reports_root, "junit.xml"),
        })

        # 4. screenshots/ + logs -- ONLY the specific files this run's own
        #    records reference (never the whole, long-lived
        #    reports/screenshots//reports/logs/ trees, which accumulate
        #    across every run ever executed -- see
        #    publish_referenced_files()'s docstring for why a whole-tree
        #    copy here would grow reports/runs/ without bound). Copied
        #    into reports/runs/<run_id>/ ONLY, never into reports/current/
        #    or reports/history/ (requirement #22/#26). reports/.auth/ is
        #    never referenced here at all.
        referenced = [r.get("screenshot") for r in ctx["records"]] + [r.get("log") for r in ctx["records"]]
        _reporting_artifacts.publish_referenced_files(reports_root, run_id, referenced)

        # 5. History (requirement #22) -- summary/result metadata only,
        #    never screenshots -- used by the NEXT run's trend/flaky
        #    computation.
        _reporting_history.save_history(reports_root, ctx["summary"], ctx["records"])
    except Exception as exc:  # noqa: BLE001 -- see docstring: never raise from here
        print(f"[reporting] REPORT_GENERATION_FAILED: {exc}", file=sys.stderr)


def _write_summary_json(session):
    """reports/<...>/summary.json -- machine-readable run summary
    (Environment and Instance Configuration work, requirement #14). Uses
    the SAME aggregated, xdist-safe counts _final_stats above was just
    populated from (real collected/executed totals, never hardcoded), and
    works identically for every channel (SMS/RCS/WhatsApp/Email/Common/
    Chatbot) or the full suite -- see _channel_from_args()."""
    passed  = _final_stats["passed"]
    failed  = _final_stats["failed"]
    skipped = _final_stats["skipped"]
    total   = passed + failed + skipped

    workers = session.config.getoption("numprocesses", default=None) \
        if hasattr(session.config.option, "numprocesses") else None

    test_type = _derive_test_type(session.config)

    summary = {
        "environment": Config.ENV,
        "instance": Config.INSTANCE or None,
        "channel": _channel_from_args(session.config),
        "test_type": test_type,
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration_seconds": round(time.time() - _RUN_START_TIME, 1),
        "workers": workers or 1,
        "status": "passed" if failed == 0 else "failed",
        "git_commit": _git_commit_short(),
        "pipeline_build_number": os.environ.get("BITBUCKET_BUILD_NUMBER") or None,
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    try:
        path = os.path.join(Config.REPORTS_DIR, "summary.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
    except OSError:
        pass  # a failure writing the summary must never fail the test run itself


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
        # Environment and Instance Configuration work, requirement #13:
        # this banner (unlike config._metadata above, which this plugin
        # version combination doesn't actually render -- confirmed by
        # testing: even pre-existing fields like "Project"/"Target URL"
        # never appear in the generated HTML) is the one place already
        # CONFIRMED to render real values into the report, so Environment/
        # Instance go here too rather than only in the silently-dropped
        # metadata table.
        f"Env: {Config.ENV} | Instance: {Config.INSTANCE or '(none)'} | "
        f"{run_time} | {browser_str} | {Config.BASE_URL}"
        "</div></div>"
    )
    prefix.append(banner)
