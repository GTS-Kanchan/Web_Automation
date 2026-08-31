from playwright.sync_api import Page

from utils.helpers import Helpers
from utils.config import Config


class BasePage:
    def __init__(self, page: Page):
        self.page = page
        self.h = Helpers(page)

    def open(self, path=""):
        self.page.goto(f"{Config.BASE_URL}{path}", timeout=60000, wait_until="domcontentloaded")

    def get_title(self):
        return self.page.title()

    def get_current_url(self):
        return self.page.url

    def take_screenshot(self, name=None):
        return self.h.take_screenshot(name)

    def is_element_present(self, locator, timeout=5000):
        return self.h.is_element_present(locator, timeout)

    def _count_data_rows(self, rows_locator, retries=2):
        """Count rows matched by `rows_locator` that contain at least one
        non-empty <td> — i.e. genuine data rows, not decorative/empty
        placeholder rows.

        Migration note: the Selenium version of this method existed to work
        around StaleElementReferenceException when Livewire re-rendered a
        table's <tbody> mid-iteration (search/filter changes re-render the
        DOM out from under a previously-fetched element list). Playwright's
        Locator API re-resolves elements fresh on every call — `.all()`
        below always queries the live DOM rather than replaying a cached
        ElementHandle list — so the underlying race is structurally gone.
        The retry loop is kept anyway as a defensive measure (a re-render
        landing mid-`.all_inner_texts()` read on very slow pages could still
        theoretically return a transiently inconsistent snapshot), but it is
        expected to rarely if ever trigger in practice."""
        attempt = 0
        while True:
            try:
                rows = self.page.locator(rows_locator)
                count = 0
                for i in range(rows.count()):
                    row = rows.nth(i)
                    tds = row.locator("td")
                    n = tds.count()
                    if n == 0:
                        continue
                    texts = [t.strip() for t in tds.all_inner_texts()]
                    if any(texts):
                        count += 1
                return count
            except Exception:
                attempt += 1
                if attempt > retries:
                    return 0
                self.page.wait_for_timeout(500)

    def _get_headers_safe(self, headers_locator, retries=2):
        """Return visible header text for `headers_locator`, retrying on
        transient errors (see _count_data_rows docstring — same Livewire
        re-render concern, structurally mitigated by Playwright's
        auto-re-resolving locators but retried defensively)."""
        attempt = 0
        while True:
            try:
                headers = self.page.locator(headers_locator)
                texts = [t.strip() for t in headers.all_inner_texts()]
                return [t for t in texts if t]
            except Exception:
                attempt += 1
                if attempt > retries:
                    return []
                self.page.wait_for_timeout(500)

    # A dismissible dark overlay behind mobile/off-canvas sidebars and some
    # modals recurs across this app's pages (Tags, Contacts, Segmentation, …)
    # and has repeatedly intercepted clicks meant for the element underneath
    # it — hoisted here from what was a copy-pasted private method on each
    # of those page objects in the Selenium suite.
    _SIDEBAR_OVERLAY = (
        "xpath=//div[contains(@class,'fixed') and contains(@class,'inset-0') "
        "and contains(@class,'bg-black') and not(contains(@style,'display: none'))]"
    )

    def _close_sidebar_overlay(self, overlay_locator=None):
        overlay_locator = overlay_locator or self._SIDEBAR_OVERLAY
        try:
            overlay = self.page.locator(overlay_locator).first
            if overlay.is_visible():
                overlay.click(force=True)
                self.page.wait_for_timeout(500)
        except Exception:
            pass
        try:
            self.page.evaluate("""
                document.querySelectorAll('div.fixed.inset-0.bg-black').forEach(function(el){
                    if (el.offsetParent !== null) { el.style.display = 'none'; }
                });
            """)
        except Exception:
            pass

    def _js_click(self, locator, timeout=10000):
        """Kept for call-site parity with the Selenium suite's `_js_click`
        (scroll into view + force click) — thin pass-through to
        Helpers.js_click."""
        return self.h.js_click(locator, timeout=timeout)

    def _first_visible_data_row(self, table_rows_css="table tbody tr"):
        """Return the first genuinely VISIBLE row Locator (scoped to a
        single row, e.g. `rows.nth(i)`) containing real (non-empty) cell
        data. Row-scoped action buttons (view/edit/delete/blacklist/etc.)
        must be located WITHIN this specific row via a relative selector
        (`row.locator("...")`) rather than an unscoped page-wide query.
        Tailwind-responsive layouts in this app can render more than one
        <table> (e.g. a mobile-only copy hidden via a breakpoint class), so
        the first DOM match is not guaranteed to be the visible one — hence
        the explicit is_visible() check on each candidate row below."""
        try:
            rows = self.page.locator(table_rows_css)
            count = rows.count()
        except Exception:
            return None
        for i in range(count):
            row = rows.nth(i)
            try:
                if not row.is_visible():
                    continue
                tds = row.locator("td")
                if tds.count() == 0:
                    continue
                if not any(t.strip() for t in tds.all_inner_texts()):
                    continue
                return row
            except Exception:
                continue
        return None
