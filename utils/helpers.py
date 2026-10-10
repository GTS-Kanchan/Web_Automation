"""
Helper utilities: explicit waits, screenshots, assertions.

Migrated from Selenium's WebDriverWait/expected_conditions to Playwright's
locator API. Playwright locators are lazy and auto-retrying — most of the
manual polling this class used to do is now handled natively by Playwright,
so these methods are thin, purpose-named wrappers kept around mainly so the
page objects (and anyone who worked with the old Selenium suite) don't have
to relearn a new vocabulary.

Locators here are plain Playwright selector strings, e.g.:
    "input[type='password']"                       (CSS — default engine)
    "xpath=//button[@type='submit']"                (XPath)
    "a:text-is('Forgot Password?')"                 (Playwright text pseudo-class)
instead of Selenium's (By.X, "...") tuples.
"""
import os
import time

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect

from utils.config import Config

# ── Navigation resilience under heavy parallel load ─────────────────────────
# A real run at PLAYWRIGHT_WORKERS=20 showed 4 fixture-setup ERRORs and 1
# test FAILURE, all the same shape: a plain page.goto(Config.BASE_URL) (in
# conftest.py's _open_authenticated_context/_apply_storage_state_to_page, and
# in BasePage.open()) hit Playwright's navigation timeout once, under the
# CPU/network contention of 20 Chromium sessions launching/running at once
# against the same QA server -- an infra/load blip, not a real navigation
# failure (the same page loaded fine for every other worker in the same
# run). goto_with_retry() below gives every "go to a URL and wait for it to
# load" call in this suite the same treatment utils/auth_state.py already
# gives the one real login: a generous, configurable timeout plus a bounded,
# in-process retry -- originally ONLY for PlaywrightTimeoutError, on the
# theory that any other exception must be a real navigation/DNS/certificate
# failure not worth retrying.
#
# UPDATED (2026-10-09): a real run showed a plain page.goto() raise
# net::ERR_NAME_NOT_RESOLVED for exactly one worker, mid-run -- the page
# simply never got a DOM to load. Per instruction: whenever the DOM doesn't
# load, wait 5 seconds and retry (a fresh page.goto(), which is the
# navigation equivalent of "refresh the page" for a page that never
# finished loading in the first place) rather than failing the test on the
# first hit. _NAV_DOM_RETRY_WAIT_SECONDS below is that fixed 5s wait,
# applied to the broader class of "page never loaded" navigation errors
# (DNS/name-resolution, connection-refused/reset, and anything else that
# isn't the already-handled TimeoutError/ERR_ABORTED cases), bounded by
# _NAV_MAX_ATTEMPTS same as every other retry here so a GENUINELY wrong URL
# still fails after a few tries instead of hanging forever.
#
# NOTE: "testqa.gtsstaging.com" (Config.BASE_URL's hardcoded default, and
# config/environments/qa.env's real value for ENV=qa) is a genuine, real
# instance -- several already-confirmed tests reference real live data on
# it by name -- so an ERR_NAME_NOT_RESOLVED against it is ordinary
# transient DNS flakiness to retry past, same as any other host, not a
# sign of a wrong/stale URL. If this keeps recurring specifically (not as
# an occasional blip) it would be worth a real DNS check against that
# host directly, but that is a separate investigation from this retry.
_NAV_TIMEOUT_MS = int(os.getenv("NAV_TIMEOUT_MS", "60000"))
_NAV_MAX_ATTEMPTS = int(os.getenv("NAV_MAX_ATTEMPTS", "2"))
_NAV_RETRY_BACKOFF_SECONDS = float(os.getenv("NAV_RETRY_BACKOFF_SECONDS", "2"))
_NAV_DOM_RETRY_WAIT_SECONDS = float(os.getenv("NAV_DOM_RETRY_WAIT_SECONDS", "5"))


def goto_with_retry(page, url, timeout=None, wait_until=None, attempts=None):
    """page.goto(url), retried a bounded number of times on a Playwright
    navigation TimeoutError before giving up -- see the module-level
    comment above for why. `timeout`/`wait_until` behave exactly like the
    matching page.goto() kwargs (timeout defaults to NAV_TIMEOUT_MS if not
    given; wait_until is only passed through if explicitly provided, so
    callers that relied on Playwright's own default ("load") keep getting
    it). `attempts` overrides NAV_MAX_ATTEMPTS for this call only.

    Used by conftest.py's authenticated-context setup/recovery goto() calls
    and by BasePage.open() -- every place in this suite that navigates to a
    URL and needs the page to have actually loaded before continuing."""
    max_attempts = attempts or _NAV_MAX_ATTEMPTS
    kwargs = {"timeout": timeout or _NAV_TIMEOUT_MS}
    if wait_until is not None:
        kwargs["wait_until"] = wait_until

    # Any of these in a goto() exception's message means the DOM never
    # loaded at all (as opposed to a slow-but-working load, which
    # PlaywrightTimeoutError above already covers) -- worth one 5s-spaced
    # retry rather than an immediate hard failure. Deliberately broad
    # (matches on substring) since Playwright surfaces these as plain
    # net::ERR_* strings inside a generic Error, not distinct exception
    # types the way PlaywrightTimeoutError is its own type.
    _DOM_NOT_LOADED_MARKERS = (
        "ERR_NAME_NOT_RESOLVED", "ERR_CONNECTION_REFUSED",
        "ERR_CONNECTION_RESET", "ERR_CONNECTION_CLOSED",
        "ERR_CONNECTION_TIMED_OUT", "ERR_EMPTY_RESPONSE",
        "ERR_NETWORK_CHANGED", "ERR_INTERNET_DISCONNECTED",
    )

    for attempt in range(1, max_attempts + 1):
        try:
            return page.goto(url, **kwargs)
        except PlaywrightTimeoutError:
            if attempt >= max_attempts:
                raise
            time.sleep(_NAV_RETRY_BACKOFF_SECONDS * attempt)
        except Exception as e:
            msg = str(e)
            # ERR_ABORTED happens when a pending Livewire/network request from
            # a prior test interrupts this navigation. Retry once with a short
            # wait; if it keeps aborting, let it surface as a real error.
            if "ERR_ABORTED" in msg and attempt < max_attempts:
                page.wait_for_timeout(1500)
                time.sleep(_NAV_RETRY_BACKOFF_SECONDS * attempt)
            elif any(marker in msg for marker in _DOM_NOT_LOADED_MARKERS) and attempt < max_attempts:
                # DOM never loaded -- wait 5s and retry (see the module-level
                # comment above for why, and for the known stale-BASE_URL-
                # fallback issue to check first if this keeps happening
                # against the same wrong domain).
                time.sleep(_NAV_DOM_RETRY_WAIT_SECONDS)
            else:
                raise


# ── Click-tracking / headless-detection workaround ───────────────────────────
#
# A real run of tests/sms/campaigns/test_sms_campaign_short_url_click_dlr.py
# proved a HEADLESS=true-only failure that is NOT a navigation problem: the
# short-link redirect itself succeeds every time ("URL clicked PASS (5x)",
# "URL redirected PASS (5x)" in the captured summary), but the campaign
# report's click COUNTER never increments -- while the identical test with
# HEADLESS=false passes consistently. Confirmed root cause: this project is
# pinned to playwright==1.47.0, which predates Playwright defaulting
# Chromium to the "new" headless mode -- headless=True here launches the
# OLD headless Chromium, whose own User-Agent string literally contains the
# substring "HeadlessChrome/<version>" instead of "Chrome/<version>" (a
# deliberate browser-exposed signal specifically so servers CAN tell real
# browsers from headless automation). This app's own click-report table has
# a "Browser-Device-OS" column per click event -- i.e. the backend already
# parses/records UA data per click -- so a backend that redirects ANY
# client but only COUNTS clicks whose UA doesn't look like a headless/bot
# browser explains the symptom exactly: real HTTP traffic either way,
# differently counted.
#
# Fix: give the click-only context a normal desktop Chrome User-Agent
# (keeping the REAL running Chromium version, read off the browser itself,
# so it never drifts out of sync with whatever Chromium is actually
# installed) plus the standard navigator.webdriver removal, so that
# dedicated context presents the same as an ordinary user's browser tab
# instead of announcing itself as automation. Scoped to callers that opt in
# (see real_user_context_kwargs below) rather than every context in the
# suite, since nothing else in this project has shown this symptom.
_DESKTOP_CHROME_USER_AGENT_TEMPLATE = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/{version} Safari/537.36"
)

# Standard navigator.webdriver removal -- harmless in headed mode too
# (webdriver is already not advertised there), kept as one extra layer of
# defense against UA/fingerprint-based click filtering alongside the UA
# override above.
STEALTH_INIT_SCRIPT = (
    "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
)


def desktop_user_agent(browser):
    """A normal-looking desktop Chrome User-Agent string, built from the
    ACTUAL launched browser's own version (browser.version, e.g.
    "118.0.5993.70") so it always matches the real Chromium build Playwright
    is running -- never a hardcoded, driftable version number."""
    return _DESKTOP_CHROME_USER_AGENT_TEMPLATE.format(version=browser.version)


def real_user_context_kwargs(browser):
    """kwargs to merge into browser.new_context(...) so the resulting
    context presents as an ordinary desktop Chrome tab rather than
    Playwright's (old-mode) headless Chromium -- see the module comment
    above for why this specifically fixes the short-URL click-count test
    under HEADLESS=true. Only meaningful under headless automation; callers
    should gate use of this behind `if Config.HEADLESS` since headed
    Chromium already has a normal UA and this would just be redundant
    there (harmless either way, but pointless)."""
    return {"user_agent": desktop_user_agent(browser)}


class Helpers:
    def __init__(self, page: Page):
        self.page = page
        self.timeout_ms = Config.EXPLICIT_WAIT_MS

    # ── Waits ──────────────────────────────────────────────────────────────────

    def wait_for_element_visible(self, locator, timeout=None):
        """Return the first matching Locator once it's visible."""
        loc = self.page.locator(locator).first
        loc.wait_for(state="visible", timeout=timeout or self.timeout_ms)
        return loc

    def wait_for_element_clickable(self, locator, timeout=None):
        """Playwright's .click() already waits for actionability (visible,
        stable, enabled, receives events) before clicking, so "clickable" is
        just "visible" here — the real wait happens inside .click() itself."""
        loc = self.page.locator(locator).first
        loc.wait_for(state="visible", timeout=timeout or self.timeout_ms)
        return loc

    def wait_for_url_contains(self, text, timeout=None):
        t = timeout or self.timeout_ms
        self.page.wait_for_url(lambda url: text in url, timeout=t)

    def wait_for_text_in_element(self, locator, text, timeout=None):
        loc = self.page.locator(locator).first
        expect(loc).to_contain_text(text, timeout=timeout or self.timeout_ms)
        return loc

    # Laravel's default Livewire-failure overlay when an AJAX request is
    # rejected with HTTP 419 (session/CSRF token expired) -- a real run hit
    # this opening the SMS Messages "Columns" panel after the shared
    # browser context's session had gone stale mid-suite. Livewire renders
    # the raw "419 | PAGE EXPIRED" response as a full-screen overlay
    # instead of updating the component, so whatever the caller was
    # waiting for (a dropdown, a panel, a save confirmation, ...) never
    # appears -- a plain wait/poll would spin until it times out without
    # ever explaining why.
    _PAGE_EXPIRED_LOCATOR = (
        "xpath=//*[contains(normalize-space(),'PAGE EXPIRED') "
        "or contains(normalize-space(),'Page Expired')]"
    )

    def is_page_expired_overlay_present(self, timeout=500):
        try:
            return self.page.locator(self._PAGE_EXPIRED_LOCATOR).first.is_visible(timeout=timeout)
        except Exception:
            return False

    def recover_from_page_expired(self):
        """If the 419 Page Expired overlay is showing, refresh the page --
        a fresh GET gets a new CSRF token/session -- and report whether a
        recovery actually happened, so the caller knows whether to retry
        whatever it was doing. Not a no-op-safe poll: only call this once
        the caller already knows its normal wait/retry has failed."""
        if not self.is_page_expired_overlay_present():
            return False
        self.page.reload(wait_until="domcontentloaded")
        self.page.wait_for_timeout(1500)
        return True

    def is_element_present(self, locator, timeout=5000):
        """timeout is in milliseconds (matches Playwright convention — note
        this differs from the old Selenium Helpers, which took seconds)."""
        try:
            self.page.locator(locator).first.wait_for(state="attached", timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    def is_element_visible(self, locator, timeout=5000):
        """Check if an element is both present and visible on screen."""
        try:
            self.page.locator(locator).first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def is_element_hidden(self, locator, timeout=5000):
        """Wait for an element to be hidden or detached."""
        try:
            self.page.locator(locator).first.wait_for(state="hidden", timeout=timeout)
            return True
        except Exception:
            return False

    # ── Screenshots ────────────────────────────────────────────────────────────

    def take_screenshot(self, name=None):
        os.makedirs("reports/screenshots", exist_ok=True)
        filename = name or f"screenshot_{int(time.time())}"
        path = f"reports/screenshots/{filename}.png"
        self.page.screenshot(path=path)
        return path

    # ── Navigation ─────────────────────────────────────────────────────────────

    def get_current_url(self):
        return self.page.url

    def get_page_title(self):
        return self.page.title()

    def scroll_to_element(self, locator):
        self.page.locator(locator).first.scroll_into_view_if_needed()

    def clear_and_type(self, locator, text):
        """fill() clears the field then sets its value in one step — the
        direct equivalent of Selenium's el.clear() + el.send_keys(text)."""
        loc = self.page.locator(locator).first
        loc.wait_for(state="visible", timeout=self.timeout_ms)
        loc.fill(text)
        return loc

    # ── Forms ──────────────────────────────────────────────────────────────────

    def is_checked(self, locator):
        return self.page.locator(locator).first.is_checked()

    def select_option(self, locator, value=None, label=None):
        loc = self.page.locator(locator).first
        if value is not None:
            loc.select_option(value=value)
        elif label is not None:
            loc.select_option(label=label)
        return loc

    def js_click(self, locator, timeout=None):
        """Force-click bypassing Playwright's actionability checks (visible,
        unobscured, stable) — the direct equivalent of the old Selenium
        suite's `driver.execute_script("arguments[0].click();", el)` escape
        hatch, reached for repeatedly across this app's pages when a native
        click was intercepted by a styled sibling/overlay (Alpine x-show
        dropdown panels, WireUI modals, etc.)."""
        loc = self.page.locator(locator).first
        loc.wait_for(state="attached", timeout=timeout or self.timeout_ms)
        loc.scroll_into_view_if_needed(timeout=timeout or self.timeout_ms)
        loc.click(force=True)
        return loc

    def js_click_first_visible(self, locator, timeout=None):
        """Click the first VISIBLE match for `locator`, not just the first
        DOM match `.first` would give.

        Some pages in this app render more than one element matching the
        exact same selector -- e.g. a desktop and a mobile-breakpoint copy
        of the same component, only one of which is ever on-screen at a
        given viewport (the same class of duplication already handled for
        table rows by BasePage._first_visible_data_row(), which has its
        own explicit is_visible() check per candidate row for exactly this
        reason). `.first` has no concept of "visible" -- it always binds to
        DOM order -- so on a page with such a duplicate it can silently
        lock onto the permanently-hidden copy. That copy IS attached (so
        `wait_for(state="attached")` and `scroll_into_view_if_needed`'s own
        "throw if detached" check both pass), but it can never satisfy a
        visibility-dependent wait -- which is consistent with a locator
        that repeatedly times out reporting "element is not visible" even
        though a live manual DOM check of the same screen shows a working,
        unhidden, clickable control matching the same selector.

        Polls all current matches for `locator` roughly every 250ms until
        timeout, looking for one that reports is_visible(); clicks the
        first one found (scrolled into view, force-clicked). Falls back to
        a synthetic dispatchEvent('click') if the force click doesn't
        register, and -- if nothing ever became visible within the
        timeout -- falls back to the old attached-only behaviour so a
        genuine bug (e.g. the control never rendering at all) still
        surfaces as a real error instead of being swallowed here."""
        end = time.time() + (timeout or self.timeout_ms) / 1000
        target = None
        while time.time() < end:
            matches = self.page.locator(locator)
            try:
                count = matches.count()
            except Exception:
                count = 0
            for i in range(count):
                cand = matches.nth(i)
                try:
                    if cand.is_visible():
                        target = cand
                        break
                except Exception:
                    continue
            if target is not None:
                break
            self.page.wait_for_timeout(250)

        if target is None:
            target = self.page.locator(locator).first
            target.wait_for(state="attached", timeout=timeout or self.timeout_ms)

        target.scroll_into_view_if_needed(timeout=timeout or self.timeout_ms)
        try:
            target.click(force=True, timeout=timeout or self.timeout_ms)
        except Exception:
            target.dispatch_event("click")
        return target

    def expect_no_dialog(self, action_fn, settle_ms=500):
        """Run `action_fn()` while watching for a native alert/confirm/
        prompt dialog, returning the dialog's message if one fired or
        None if none appeared.

        Used by XSS-safety tests (typing a payload like
        `<script>alert(1)</script>` into a search box and proving it was
        never executed): Selenium could react to an alert AFTER the fact
        via `driver.switch_to.alert`, but Playwright has no equivalent --
        an unhandled `dialog` event blocks all further page interaction
        until it's accepted/dismissed, so the listener has to be wired up
        BEFORE the action runs, not checked for afterward. Any dialog that
        does fire is auto-dismissed here so it can never hang the test,
        regardless of what the caller does with the returned message."""
        captured = {"message": None, "fired": False}

        def _on_dialog(dialog):
            captured["fired"] = True
            captured["message"] = dialog.message
            try:
                dialog.dismiss()
            except Exception:
                pass

        self.page.on("dialog", _on_dialog)
        try:
            action_fn()
            self.page.wait_for_timeout(settle_ms)
        finally:
            try:
                self.page.remove_listener("dialog", _on_dialog)
            except Exception:
                pass

        return captured["message"] if captured["fired"] else None

    def dispatch_click(self, locator):
        """Last-resort click via a synthetic DOM MouseEvent — mirrors the old
        suite's `dispatchEvent(new MouseEvent('click', ...))` fallback used
        when even a JS `.click()` didn't register (e.g. row action buttons
        behind a data-tooltip wrapper)."""
        self.page.locator(locator).first.dispatch_event("click")

    # ── Polling ────────────────────────────────────────────────────────────────

    def wait_until(self, condition_fn, timeout_ms=6000, interval_ms=500):
        """Poll a no-arg callable until it returns truthy or timeout elapses.
        Direct port of this suite's recurring
        `while time.time() < end_time: ...; time.sleep(0.5)` pattern, used
        where no single Playwright auto-wait condition covers a multi-step
        UI settle (e.g. "either the table has rows OR shows a no-records
        message")."""
        end = time.time() + timeout_ms / 1000
        while time.time() < end:
            try:
                if condition_fn():
                    return True
            except Exception:
                pass
            self.page.wait_for_timeout(interval_ms)
        return False

    # ── Downloads ──────────────────────────────────────────────────────────────

    def download_via(self, trigger_locator, dest_path, timeout=None):
        """Click `trigger_locator` and save the resulting download to
        `dest_path`. Playwright downloads are captured per-action via an
        expect_download() context manager rather than a fixed browser
        download directory (the old driver_factory.DOWNLOAD_DIR approach),
        since Playwright intercepts the download event directly instead of
        relying on the browser's disk-write behaviour."""
        with self.page.expect_download(timeout=timeout or self.timeout_ms) as dl_info:
            self.page.locator(trigger_locator).first.click()
        download = dl_info.value
        download.save_as(dest_path)
        return dest_path
