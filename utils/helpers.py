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

    def is_element_present(self, locator, timeout=5000):
        """timeout is in milliseconds (matches Playwright convention — note
        this differs from the old Selenium Helpers, which took seconds)."""
        try:
            self.page.locator(locator).first.wait_for(state="attached", timeout=timeout)
            return True
        except PlaywrightTimeoutError:
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
