from playwright.sync_api import Page

from utils.helpers import Helpers, goto_with_retry
from utils.config import Config


class BasePage:
    def __init__(self, page: Page):
        self.page = page
        self.h = Helpers(page)

    def open(self, path=""):
        # goto_with_retry (utils/helpers.py): generous, configurable timeout
        # + one bounded retry on a Playwright navigation TimeoutError only —
        # a real run at PLAYWRIGHT_WORKERS=20 showed this exact goto() time
        # out once under load even at the old flat 60000ms with no retry.
        goto_with_retry(
            self.page, f"{Config.BASE_URL}{path}", wait_until="domcontentloaded"
        )

    def get_title(self):
        return self.page.title()

    def get_current_url(self):
        return self.page.url

    def take_screenshot(self, name=None):
        return self.h.take_screenshot(name)

    def is_element_present(self, locator, timeout=5000):
        return self.h.is_element_present(locator, timeout)

    def is_element_visible(self, locator, timeout=5000):
        return self.h.is_element_visible(locator, timeout)

    def is_element_hidden(self, locator, timeout=5000):
        return self.h.is_element_hidden(locator, timeout)

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

    def _js_click_first_visible(self, locator, timeout=10000):
        """Like `_js_click`, but binds to the first VISIBLE match for
        `locator` rather than the first DOM match -- see
        Helpers.js_click_first_visible for why that distinction matters
        (duplicate desktop/mobile copies of the same control). Use this
        over `_js_click` for any control that a live DOM check has proven
        exists and is clickable but that `_js_click` still times out
        waiting on."""
        return self.h.js_click_first_visible(locator, timeout=timeout)

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

    def get_cell_text(self, row_index, col_index, table_rows_css=None):
        """Generic (row, col) 0-based cell text reader, added to BasePage
        so every page object gets it for free instead of re-implementing
        the same 3-line body per page (the exact pattern already
        confirmed working, independently, on several page objects in
        this project -- e.g. SmsCampaignMessageReportPage.get_cell_text(),
        SMSCampaignPage.get_cell_text()). Uses `self.TABLE_ROWS` (every
        page object in this project already defines this class attribute
        for its own table) unless a page needs a different rows locator
        for this one call (`table_rows_css` override). Never raises --
        returns "" on any error, matching the existing per-page
        implementations' contract."""
        try:
            rows = self.page.locator(table_rows_css or self.TABLE_ROWS)
            cells = rows.nth(row_index).locator("td")
            return cells.nth(col_index).inner_text().strip()
        except Exception:
            return ""

    def get_column_index(self, header_name):
        """Generic 0-based index of the column whose header equals
        *header_name* (case-insensitive, whitespace-trimmed), or None.
        Reuses whatever `get_visible_column_headers()` the concrete page
        object already provides (every page object in this project
        defines one, typically via `self._get_headers_safe(self.TABLE_HEADERS)`)
        rather than re-reading headers itself -- same convention as the
        get_column_index() already confirmed working independently on
        SmsCampaignMessageReportPage and SMSCampaignPage."""
        for i, h in enumerate(self.get_visible_column_headers()):
            if h.strip().lower() == header_name.strip().lower():
                return i
        return None

    def get_raw_headers(self, headers_locator):
        """Return EVERY header cell's text, in DOM order, INCLUDING blank
        entries (e.g. an icon-only Action column with no text label) --
        unlike `_get_headers_safe(headers_locator)` / most page objects'
        `get_visible_column_headers()`, which filter blank header text
        out.

        This matters whenever a header's INDEX (not just its presence)
        will be used to read a cell via `get_cell_text(row, col_index)`:
        that method indexes into the FULL, unfiltered `<td>` list, so a
        column-index computed from a BLANK-FILTERED header list silently
        points at the wrong cell the moment any earlier column's header
        renders empty text -- confirmed as a real bug in this project (a
        blank "Action" header column shifted every later column's
        filtered-list index left by one, so a "Created At" lookup built
        from the filtered header list actually read the next column's
        cell, e.g. Phone Number or Product, instead).

        Always use THIS (not the page's own get_visible_column_headers())
        to build a header-name -> cell-index mapping; use the filtered
        get_visible_column_headers() only when checking a column's mere
        PRESENCE, where a shifted index doesn't matter."""
        try:
            headers = self.page.locator(headers_locator)
            return [h.strip() for h in headers.all_inner_texts()]
        except Exception:
            return []
