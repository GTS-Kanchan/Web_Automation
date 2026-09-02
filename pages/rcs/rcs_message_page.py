import csv
import glob
import os

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR
from utils.file_validator import read_file_headers


class RcsMessagePage(BasePage):

    MESSAGES_PATH = "/rcs/message"

    # Status filter option values (native <select>, confirmed lowercase)
    STATUS_PENDING   = "queued"
    STATUS_SENT      = "sent"
    STATUS_DELIVERED = "delivered"
    STATUS_READ      = "read"
    STATUS_FAILED    = "failed"
    STATUS_RECEIVED  = "received"
    STATUS_REJECTED  = "rejected"

    # Source filter option values (native <select>, confirmed)
    SOURCE_CAMPAIGN = "u"
    SOURCE_API      = "a"
    SOURCE_FLOW     = "f"
    SOURCE_INCOMING = "w"

    # Confirmed column order from the live <thead>
    COLUMN_INDEX = {
        "action": 0, "contact": 1, "source": 2, "sub-source": 3, "status": 4,
        "submitted-at": 5, "delivered-at": 6, "read-at": 7,
        "failed-at": 8, "created-at": 9, "clicks": 10,
        "button-type": 11, "button-value": 12, "clicked-at": 13,
    }

    # ── Page header ────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[normalize-space()='RCS Messages']"

    # ── Table ──────────────────────────────────────────────────────────────
    TABLE         = "#table-table"
    TABLE_HEADERS = "#table-table thead th"
    TABLE_ROWS    = "#table-table tbody tr"
    # App-wide confirmed empty-state text (see sms_error_codes_page.py).
    NO_RECORDS_MSG = (
        "xpath=//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no items found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no record') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no data') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no result')]"
    )
    PAGINATION_RESULTS_TEXT = ".paged-pagination-results"

    # ── Search ─────────────────────────────────────────────────────────────
    SEARCH_BOX = "input[placeholder='Search Mobile Number']"

    # ── Filters panel ──────────────────────────────────────────────────────
    BTN_FILTER = "xpath=//button[contains(normalize-space(.),'Filters')][not(ancestor::table)]"
    FILTER_STATUS_SELECT = "#table-filter-status"
    FILTER_SOURCE_SELECT = "#table-filter-source"
    BTN_CLEAR_FILTER = (
        "xpath=//button[.//*[normalize-space()='Clear'] or normalize-space()='Clear']"
        "[not(ancestor::table)]"
    )

    # ── Export / Refresh / Columns ──────────────────────────────────────────
    EXPORT_LINK = (
        "xpath=//a[contains(@href,'/rcs/messages/export')]"
        " | //a[contains(normalize-space(.),'Export')]"
    )
    REFRESH_LINK = "xpath=//a[contains(normalize-space(.),'Refresh')]"

    BTN_COLUMNS = "xpath=//button[contains(normalize-space(.),'Columns')][not(ancestor::table)]"
    COLUMN_CHECKBOX_BY_VALUE_XPATH = "xpath=//input[@type='checkbox' and @value='{value}']"

    # ── Sorting ──────────────────────────────────────────────────────────────
    SORT_CREATED_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('created_at')\")]"
    APPLIED_SORT_PILL = (
        "xpath=//small[contains(normalize-space(.),'Applied Sorting')]"
        "/following-sibling::span[1]"
    )

    # ── Row view action ──────────────────────────────────────────────────────
    ROW_VIEW_BTN = "xpath=(//button[contains(@data-tooltip-target,'tooltip-view-')])[1]"

    # ── Pagination ─────────────────────────────────────────────────────────
    NEXT_PAGE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"nextPage('page')\")]"
    PREV_PAGE_BTN = "xpath=//span[normalize-space()='« Previous'] | //button[normalize-space()='« Previous']"

    # -------------------------------------------------------------------------
    # Navigation
    # -------------------------------------------------------------------------

    def navigate(self):
        self.open(self.MESSAGES_PATH)
        self.page.wait_for_timeout(1500)

    def is_messages_page(self):
        return "/rcs/message" in self.get_current_url().lower()

    def get_page_title_text(self):
        try:
            return self.h.wait_for_element_visible(self.PAGE_TITLE, timeout=8000).inner_text().strip()
        except Exception:
            return ""

    def wait_for_table_load(self, timeout=15000):
        self.h.wait_until(lambda: self.get_row_count() > 0 or self.is_no_records_visible(),
                           timeout_ms=timeout, interval_ms=800)

    # -------------------------------------------------------------------------
    # Table helpers
    # -------------------------------------------------------------------------

    def get_row_count(self):
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            count = 0
            for i in range(rows.count()):
                row = rows.nth(i)
                if row.is_visible() and row.inner_text().strip():
                    count += 1
            return count
        except Exception:
            return 0

    def get_table_headers(self):
        return self._get_headers_safe(self.TABLE_HEADERS)

    def get_cell_text(self, row_idx, col_idx):
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            if row_idx >= rows.count():
                return ""
            cells = rows.nth(row_idx).locator("td")
            if col_idx >= cells.count():
                return ""
            return cells.nth(col_idx).inner_text().strip()
        except Exception:
            return ""

    def get_all_values_in_column(self, col_name):
        idx = self.COLUMN_INDEX.get(col_name)
        if idx is None:
            return []
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            values = []
            for i in range(rows.count()):
                cells = rows.nth(i).locator("td")
                if idx < cells.count():
                    values.append(cells.nth(idx).inner_text().strip())
            return values
        except Exception:
            return []

    def is_no_records_visible(self):
        return self.is_element_present(self.NO_RECORDS_MSG, timeout=3000)

    def get_page_info_text(self):
        try:
            return self.page.locator(self.PAGINATION_RESULTS_TEXT).first.inner_text().strip()
        except Exception:
            return ""

    # -------------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------------

    def search(self, text):
        try:
            box = self.h.wait_for_element_clickable(self.SEARCH_BOX, timeout=10000)
            box.fill(text)
            self.page.wait_for_timeout(1500)
        except Exception:
            pass

    def clear_search(self):
        try:
            box = self.page.locator(self.SEARCH_BOX).first
            box.fill("")
            box.press("Enter")
            self.page.wait_for_timeout(1000)
        except Exception:
            pass

    def has_campaign_message_for_number(self, phone_number: str, timeout: int = 20000) -> bool:
        """Navigate to the RCS Messages report, filter Source = Campaign
        (SOURCE_CAMPAIGN), search *phone_number*, and return whether at
        least one matching row is present within *timeout*. Added so the
        RCS Campaign opt-out validation tests (TC156/TC157) can verify,
        from a real report, whether a launched campaign actually sent to
        (or excluded) a given number -- instead of only trusting the
        create-page's own success/redirect signal, which says nothing
        about which individual contacts were actually messaged."""
        self.navigate()
        try:
            self.open_filter_panel()
            self.set_filter_source(self.SOURCE_CAMPAIGN)
        except Exception:
            pass
        self.search(phone_number)

        deadline = self.page.evaluate("() => Date.now()") + timeout
        while self.page.evaluate("() => Date.now()") < deadline:
            if self.get_row_count() > 0:
                return True
            if self.is_no_records_visible():
                return False
            self.page.wait_for_timeout(800)
        return self.get_row_count() > 0

    # -------------------------------------------------------------------------
    # Filters
    # -------------------------------------------------------------------------

    def open_filter_panel(self):
        try:
            self._js_click(self.BTN_FILTER, timeout=10000)
            self.page.wait_for_timeout(600)
        except Exception:
            pass

    def set_filter_status(self, value):
        try:
            self.h.select_option(self.FILTER_STATUS_SELECT, value=value)
            self.page.wait_for_timeout(1500)
            return True
        except Exception:
            return False

    def set_filter_source(self, value):
        try:
            self.h.select_option(self.FILTER_SOURCE_SELECT, value=value)
            self.page.wait_for_timeout(1500)
            return True
        except Exception:
            return False

    def set_date_filter(self, from_date, to_date):
        """
        Set the Created From / Created To range via a direct Livewire JS
        call — required because the actual date+time controls live inside
        Alpine x-data components with no static id and update Livewire via
        $wire.set() rather than wire:model.

        from_date / to_date: 'YYYY-MM-DD' (time defaults to T00:00) or
        'YYYY-MM-DDTHH:MM'.
        """
        def _to_dt(val):
            return val if "T" in str(val) else f"{val}T00:00"

        from_dt = _to_dt(from_date)
        to_dt = _to_dt(to_date)

        try:
            self.page.evaluate(
                "(v) => { window.Livewire && window.Livewire.all().forEach(function(c) {"
                "  try { c.set('filterComponents.created_from', v); } catch(e) {}"
                "}); }",
                from_dt
            )
            self.page.wait_for_timeout(400)
        except Exception:
            pass
        try:
            self.page.evaluate(
                "(v) => { window.Livewire && window.Livewire.all().forEach(function(c) {"
                "  try { c.set('filterComponents.created_to', v); } catch(e) {}"
                "}); }",
                to_dt
            )
            self.page.wait_for_timeout(1500)
        except Exception:
            pass

    def apply_filter(self):
        """No-op: filters are wire:model.live — kept for API parity."""
        self.page.wait_for_timeout(1500)

    def clear_filter(self):
        try:
            self._js_click(self.BTN_CLEAR_FILTER, timeout=5000)
            self.page.wait_for_timeout(1500)
            return
        except Exception:
            pass
        try:
            self.page.evaluate(
                "() => { window.Livewire && window.Livewire.all().forEach(function(c) {"
                "  try {"
                "    c.set('filterComponents', {created_from: null, created_to: null, status: null, source: null});"
                "    c.set('search', '');"
                "  } catch(e) {}"
                "}); }"
            )
            self.page.wait_for_timeout(1500)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Export
    # -------------------------------------------------------------------------

    def click_export(self):
        """Migration note: the Selenium version clicked a plain <a> export
        link and polled the OS download folder by mtime. Playwright
        captures the download event directly and saves it to
        Config.DOWNLOAD_DIR, recording the path on self._last_download_path
        for wait_for_download() to return."""
        self._last_download_path = None
        try:
            link = self.h.wait_for_element_clickable(self.EXPORT_LINK, timeout=10000)
            link.scroll_into_view_if_needed()
            with self.page.expect_download(timeout=15000) as dl_info:
                link.click()
            download = dl_info.value
            filename = download.suggested_filename or "rcs_messages_export.csv"
            dest = os.path.join(DOWNLOAD_DIR, filename)
            download.save_as(dest)
            self._last_download_path = dest
            self.page.wait_for_timeout(500)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Refresh (<a> link, not a <button>)
    # -------------------------------------------------------------------------

    def click_refresh(self):
        try:
            self._js_click(self.REFRESH_LINK, timeout=8000)
            self.page.wait_for_timeout(2500)
        except Exception:
            try:
                self.page.reload()
                self.page.wait_for_timeout(2500)
            except Exception:
                pass

    # -------------------------------------------------------------------------
    # Columns dropdown
    # -------------------------------------------------------------------------

    def open_columns_panel(self):
        try:
            self._js_click(self.BTN_COLUMNS, timeout=10000)
            self.page.wait_for_timeout(500)
        except Exception:
            pass

    def is_column_checkbox_present(self, value):
        try:
            xpath = self.COLUMN_CHECKBOX_BY_VALUE_XPATH.format(value=value)
            return self.page.locator(xpath).count() > 0
        except Exception:
            return False

    def toggle_column(self, value):
        """Toggle a column's visibility checkbox by its confirmed value
        (action/contact/department/user/source/status/submitted-at/
        delivered-at/read-at/failed-at/created-at/clicks/button-type/
        button-value/clicked-at/message-id)."""
        try:
            xpath = self.COLUMN_CHECKBOX_BY_VALUE_XPATH.format(value=value)
            cb = self.page.locator(xpath).first
            cb.wait_for(state="attached", timeout=5000)
            cb.click(force=True)
            self.page.wait_for_timeout(800)
            return True
        except Exception:
            return False

    def get_column_checkbox_state(self, value):
        try:
            xpath = self.COLUMN_CHECKBOX_BY_VALUE_XPATH.format(value=value)
            return self.page.locator(xpath).first.is_checked()
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # Sorting
    # -------------------------------------------------------------------------

    def click_created_at_header(self):
        try:
            self._js_click(self.SORT_CREATED_AT_BTN, timeout=10000)
            self.page.wait_for_timeout(1500)
        except Exception:
            try:
                self.page.evaluate(
                    "() => { window.Livewire && window.Livewire.all().forEach(function(c) {"
                    "  try { c.call('sortBy', 'created_at'); } catch(e) {}"
                    "}); }"
                )
                self.page.wait_for_timeout(1500)
            except Exception:
                pass

    def get_applied_sort_pill_text(self):
        try:
            return self.page.locator(self.APPLIED_SORT_PILL).first.inner_text().strip()
        except Exception:
            return ""

    # -------------------------------------------------------------------------
    # Row view action
    # -------------------------------------------------------------------------

    def click_view_icon(self, row_idx=0):
        try:
            btns = self.page.locator("xpath=//button[contains(@data-tooltip-target,'tooltip-view-')]")
            if row_idx < btns.count():
                btn = btns.nth(row_idx)
                btn.scroll_into_view_if_needed()
                btn.click(force=True)
            else:
                el = self.h.wait_for_element_clickable(self.ROW_VIEW_BTN, timeout=8000)
                el.click(force=True)
            self.page.wait_for_timeout(1500)
            return True
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # Pagination
    # -------------------------------------------------------------------------

    def click_next_page(self):
        try:
            self._js_click(self.NEXT_PAGE_BTN, timeout=5000)
            self.page.wait_for_timeout(2000)
            return True
        except Exception:
            return False

    def is_next_page_enabled(self):
        try:
            btns = self.page.locator(self.NEXT_PAGE_BTN)
            for i in range(btns.count()):
                b = btns.nth(i)
                if b.is_enabled() and b.is_visible():
                    return True
            return False
        except Exception:
            return False

    def is_prev_page_enabled(self):
        """The Previous control renders as a plain disabled <span> on page 1
        (confirmed) — only a real, clickable Previous <button> counts as
        'enabled'."""
        try:
            btns = self.page.locator("xpath=//button[normalize-space()='« Previous']")
            for i in range(btns.count()):
                b = btns.nth(i)
                if b.is_enabled() and b.is_visible():
                    return True
            return False
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # Download file helpers
    # -------------------------------------------------------------------------

    _INCOMPLETE_SUFFIXES = (".crdownload", ".part", ".tmp")
    _last_download_path = None

    def clear_download_dir(self):
        for f in glob.glob(os.path.join(DOWNLOAD_DIR, "*")):
            if os.path.isfile(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    def snapshot_downloads(self):
        """Kept for API parity with the Selenium suite's before/after
        snapshot pattern; click_export() now records the downloaded path
        directly via Playwright's download event, so wait_for_download()
        doesn't need to diff a filesystem snapshot."""
        try:
            return {f for f in glob.glob(os.path.join(DOWNLOAD_DIR, "*")) if os.path.isfile(f)}
        except Exception:
            return set()

    def wait_for_download(self, timeout=60, before=None):
        """Returns the path captured by the most recent click_export()
        call (Playwright captures the download event directly rather than
        polling the OS download folder)."""
        return self._last_download_path

    def get_csv_headers(self, file_path):
        """Return the downloaded export's header row, whatever format it
        actually turns out to be -- delegates to
        utils/file_validator.py's read_file_headers() (the same
        format-dispatching reader proven for SMS: .csv/.xlsx/.xls, or a
        .zip wrapping one of those) instead of a hand-rolled plain-CSV
        parse that silently returned [] for anything else."""
        try:
            return read_file_headers(file_path)
        except Exception:
            return []

    def get_csv_row_count(self, file_path):
        try:
            with open(file_path, newline="", encoding="utf-8-sig") as fh:
                return max(0, len(list(csv.reader(fh))) - 1)
        except Exception:
            return 0
