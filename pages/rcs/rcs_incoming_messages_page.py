import glob
import os

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR


class RcsIncomingMessagesPage(BasePage):

    REPORT_URL = "/rcs/incoming-messages"
    TABLE_NAME = "rcs_incoming_messages"

    # Confirmed column order
    COLUMN_INDEX = {
        "action": 0, "campaign_name": 1, "agent": 2,
        "country_code": 3, "user_number": 4, "type": 5,
        "received_at": 6, "created_at": 7
    }

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'RCS Incoming Messages')]"
    BREADCRUMB = "nav[aria-label='Breadcrumb']"

    # ── Top action buttons (confirmed) ───────────────────────────────────────
    REFRESH_BTN = (
        "xpath=//a[contains(@href,'/rcs/incoming-messages') and contains(normalize-space(.),'Refresh')]"
    )
    EXPORT_CSV_BTN = "xpath=//a[contains(normalize-space(.),'Export CSV')]"

    # ── Search ───────────────────────────────────────────────────────────────
    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search']"

    # ── Filters popover ──────────────────────────────────────────────────────
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')]"
    FILTER_AGENT_SELECT = "#rcs_incoming_messages-filter-agent_id"
    FILTER_RECEIVED_FROM_DATE = "#rcs_incoming_messages-filter-received_from-wrapper input[type='date']"
    FILTER_RECEIVED_FROM_TIME = "#rcs_incoming_messages-filter-received_from-wrapper select"
    FILTER_RECEIVED_TO_DATE = "#rcs_incoming_messages-filter-received_to-wrapper input[type='date']"
    FILTER_RECEIVED_TO_TIME = "#rcs_incoming_messages-filter-received_to-wrapper select"
    # Best-effort clear-filters button (clearFilters Livewire method confirmed
    # in wire:snapshot listeners, but no rendered pill was captured since no
    # filter was applied at DOM-capture time).
    CLEAR_FILTERS_BTN = (
        "xpath=//button[contains(@*[name()='wire:click'],'clearFilters') "
        "or contains(@*[name()='wire:click.prevent'],'clearFilters') "
        "or normalize-space()='Clear']"
    )

    # ── Sorting ──────────────────────────────────────────────────────────────
    SORT_RECEIVED_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('received_at')\")]"
    CLEAR_SORT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"clearSort\")]"
    CLEAR_ALL_SORTS_BTN = "xpath=//button[contains(@*[name()='wire:click'],'clearSorts')]"

    # ── Columns dropdown ─────────────────────────────────────────────────────
    COLUMNS_BUTTON = "xpath=//button[contains(normalize-space(.),'Columns')]"
    COLUMN_CHECKBOXES = (
        f"xpath=//div[contains(@*[name()='wire:key'],'{TABLE_NAME}-columnSelect-') and "
        f"not(contains(@*[name()='wire:key'],'columnSelect-selectAll'))]//input[@type='checkbox']"
    )
    SELECT_ALL_COLUMNS_CHECKBOX = (
        f"xpath=//div[contains(@*[name()='wire:key'],'{TABLE_NAME}-columnSelect-selectAll-')]//input[@type='checkbox']"
    )

    # ── Table ────────────────────────────────────────────────────────────────
    TABLE = f"#table-{TABLE_NAME}"
    TABLE_HEADERS = f"#table-{TABLE_NAME} thead th"
    TABLE_ROWS = f"#table-{TABLE_NAME} tbody tr"
    NO_RECORDS_MSG = (
        "xpath=//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no record') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no data') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no result') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'not found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'nothing found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no messages') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no items found')]"
    )

    # ── Action (View) ────────────────────────────────────────────────────────
    ACTION_VIEW_BTN_IN_ROW = "xpath=.//button[contains(@data-tooltip-target,'tooltip-view-')]"
    MODAL_CONTAINER = "#modal-container"

    # ── Pagination ───────────────────────────────────────────────────────────
    PAGINATION_RESULTS_TEXT = ".total-pagination-results"

    # ── Navigation / page state ──────────────────────────────────────────────

    def navigate_to_report(self):
        self.open(self.REPORT_URL)
        self.page.wait_for_timeout(2000)
        return self

    def is_report_page(self):
        url = self.get_current_url()
        return "/rcs/incoming-messages" in url and "login" not in url.lower()

    def get_page_title_text(self):
        el = self.h.wait_for_element_visible(self.PAGE_TITLE)
        return el.inner_text().strip()

    def _is_visible(self, locator, timeout=1000):
        try:
            return self.page.locator(locator).first.is_visible()
        except Exception:
            return False

    # ── Top action buttons ───────────────────────────────────────────────────

    def click_refresh(self):
        self._js_click(self.REFRESH_BTN, timeout=10000)
        self.page.wait_for_timeout(2000)

    # ── Search ───────────────────────────────────────────────────────────────

    def _current_table_state(self):
        current = self.get_row_count()
        no_msg = self.is_element_present(self.NO_RECORDS_MSG, timeout=500)
        return (current, no_msg)

    def _wait_for_search_to_settle(self, timeout=8000, baseline=None):
        """Poll (row_count, no-records-shown) until two consecutive reads
        agree, treating that as "the table has stopped changing".

        `baseline`, if given, is the table state read BEFORE the
        search/clear input was dispatched. Confirmed live (test_tc005):
        under parallel (-n) execution, the debounced wire:model.live
        request can still not have reached the server by the time the
        very first poll below runs, so that first read (and often the one
        600ms after it) can both just be the UNCHANGED pre-search table --
        two consecutive matching reads of the OLD state look "stable" to
        this loop even though the real update hasn't started yet, and
        search() returned control while the table was still about to
        change out from under the caller (has_records() then raced the
        real update and lost). When `baseline` is given, a state equal to
        it is never accepted as evidence of settling until at least one
        different state has been observed -- except the loop still
        returns once `timeout` genuinely elapses, so a search that
        legitimately doesn't change the row count/no-records state still
        returns instead of always burning the full budget."""
        end_time = self.page.evaluate("() => Date.now()") + timeout
        last_state = None
        seen_change = baseline is None
        while self.page.evaluate("() => Date.now()") < end_time:
            state = self._current_table_state()
            if not seen_change and state != baseline:
                seen_change = True
            if state == last_state and seen_change:
                return
            last_state = state
            self.page.wait_for_timeout(600)

    def search(self, value):
        """JS-driven single 'input' dispatch (not type char-by-char) to avoid
        a wire:model.live per-keystroke race — same fix proven necessary on
        the SMS Error Codes, Blocked Numbers, and SMS Incoming Messages
        pages."""
        baseline = self._current_table_state()
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.evaluate(
            "(el, v) => { el.value = v; "
            "el.dispatchEvent(new Event('input', {bubbles: true})); "
            "el.dispatchEvent(new Event('change', {bubbles: true})); }",
            value
        )
        self.page.wait_for_timeout(500)
        self._wait_for_search_to_settle(baseline=baseline)
        self.page.wait_for_timeout(300)

    def clear_search(self):
        baseline = self._current_table_state()
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.evaluate(
            "(el) => { el.value = ''; "
            "el.dispatchEvent(new Event('input', {bubbles: true})); "
            "el.dispatchEvent(new Event('change', {bubbles: true})); }"
        )
        self.page.wait_for_timeout(500)
        self._wait_for_search_to_settle(baseline=baseline)
        self.page.wait_for_timeout(300)

    # ── Table / rows ─────────────────────────────────────────────────────────

    def has_records(self):
        return self.is_element_present(self.TABLE_ROWS, timeout=5000) and self.get_row_count() > 0

    @staticmethod
    def _is_empty_state_row(tds):
        """Same rappasoft/laravel-livewire-tables empty-state placeholder
        detection proven necessary on the Blocked Numbers and SMS Incoming
        Messages pages (single <tr><td colspan="N">) — reused verbatim since
        this is the same underlying table package."""
        return len(tds) == 1 and tds[0].get_attribute("colspan")

    def has_no_records_message(self):
        if self.is_element_present(self.NO_RECORDS_MSG, timeout=3000):
            return True
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            if rows.count() == 1:
                tds = rows.nth(0).locator("td")
                td_list = [tds.nth(i) for i in range(tds.count())]
                if self._is_empty_state_row(td_list):
                    return True
        except Exception:
            pass
        return self.get_row_count() == 0

    def get_row_count(self):
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            count = 0
            for i in range(rows.count()):
                row = rows.nth(i)
                tds = row.locator("td")
                n = tds.count()
                if n == 0:
                    continue
                td_list = [tds.nth(j) for j in range(n)]
                if self._is_empty_state_row(td_list):
                    continue
                if any(td.inner_text().strip() for td in td_list):
                    count += 1
            return count
        except Exception:
            return 0

    def get_visible_column_headers(self):
        return self._get_headers_safe(self.TABLE_HEADERS)

    def get_column_values(self, column_name):
        idx = self.COLUMN_INDEX.get(column_name)
        if idx is None:
            return []
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            values = []
            for i in range(rows.count()):
                tds = rows.nth(i).locator("td")
                if tds.count() > idx:
                    values.append(tds.nth(idx).inner_text().strip())
            return values
        except Exception:
            return []

    def get_first_data_row(self):
        return self._first_visible_data_row(f"#table-{self.TABLE_NAME} tbody tr")

    def sort_by_received_at(self):
        self._js_click(self.SORT_RECEIVED_AT_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    # ── Filters popover ──────────────────────────────────────────────────────

    def open_filters_popover(self):
        if self._is_visible(self.FILTER_AGENT_SELECT, timeout=1000):
            return
        self._js_click(self.FILTERS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def filter_by_received_date_range(self, days_back=60):
        """Sets Received From = today-days_back, Received To = today using the
        native <input type='date'> controls inside the Alpine wrapper.
        Dispatches a native 'change' event so Alpine's x-on:change=
        "updateDateTime()" handler fires and updates Livewire."""
        from datetime import date, timedelta

        self.open_filters_popover()
        from_input = self.h.wait_for_element_visible(self.FILTER_RECEIVED_FROM_DATE)
        from_value = (date.today() - timedelta(days=days_back)).isoformat()
        from_input.evaluate(
            "(el, v) => { el.value = v; el.dispatchEvent(new Event('change', {bubbles: true})); }",
            from_value
        )
        self.page.wait_for_timeout(500)
        to_input = self.h.wait_for_element_visible(self.FILTER_RECEIVED_TO_DATE)
        to_value = date.today().isoformat()
        to_input.evaluate(
            "(el, v) => { el.value = v; el.dispatchEvent(new Event('change', {bubbles: true})); }",
            to_value
        )
        self.page.wait_for_timeout(1500)
        return True

    def get_filter_received_from_value(self):
        el = self.h.wait_for_element_visible(self.FILTER_RECEIVED_FROM_DATE)
        return el.get_attribute("value")

    def get_filter_received_to_value(self):
        el = self.h.wait_for_element_visible(self.FILTER_RECEIVED_TO_DATE)
        return el.get_attribute("value")

    def filter_by_sender(self, value):
        # NOTE: mirrors a pre-existing gap in the original Selenium source —
        # FILTER_SENDER_SELECT was never defined on this page (only an Agent
        # filter exists here, see FILTER_AGENT_SELECT). Not exercised by any
        # test in the suite; left unimplemented for parity.
        self.open_filters_popover()
        self.h.select_option(self.FILTER_AGENT_SELECT, value=value)
        self.page.wait_for_timeout(1500)

    def get_available_sender_options(self):
        """Returns list of (value, text) tuples for all options in the Agent
        filter select (excluding the 'All' option with an empty value).
        NOTE: not exercised by any test in this suite."""
        self.open_filters_popover()
        try:
            opts = self.page.locator(f"{self.FILTER_AGENT_SELECT} option")
            result = []
            for i in range(opts.count()):
                o = opts.nth(i)
                val = o.get_attribute("value")
                if val:
                    result.append((val, o.inner_text().strip()))
            return result
        except Exception:
            return []

    def click_clear_filters(self):
        if not self.is_element_present(self.CLEAR_FILTERS_BTN, timeout=5000):
            return False
        self._js_click(self.CLEAR_FILTERS_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)
        return True

    # ── Columns dropdown ─────────────────────────────────────────────────────

    def open_columns_dropdown(self):
        if self._is_visible(self.COLUMN_CHECKBOXES, timeout=1000):
            return
        self._js_click(self.COLUMNS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def toggle_column(self, value):
        """value: 'action' | 'campaign-name' | 'sender-id' | 'country-code'
        | 'user-number' | 'received-at'"""
        self.open_columns_dropdown()
        cb = self.h.wait_for_element_visible(f"input[type='checkbox'][value='{value}']")
        cb.scroll_into_view_if_needed()
        cb.click(force=True)
        self.page.wait_for_timeout(800)

    def is_column_checked(self, value):
        self.open_columns_dropdown()
        try:
            cb = self.page.locator(f"input[type='checkbox'][value='{value}']").first
            return cb.is_checked()
        except Exception:
            return None

    def restore_default_columns(self):
        """Restores the confirmed default: ALL 6 columns checked."""
        defaults = {
            "action": True, "campaign-name": True, "sender-id": True,
            "country-code": True, "user-number": True, "received-at": True,
        }
        for value, should_be_checked in defaults.items():
            self.open_columns_dropdown()
            try:
                cb = self.page.locator(f"input[type='checkbox'][value='{value}']").first
                if cb.count() == 0:
                    continue
            except Exception:
                continue
            try:
                if cb.is_checked() != should_be_checked:
                    cb.scroll_into_view_if_needed()
                    cb.click(force=True)
                    self.page.wait_for_timeout(500)
            except Exception:
                continue

    # ── Action (View) / Modal ────────────────────────────────────────────────

    def click_view_on_first_row(self):
        row = self.get_first_data_row()
        if row is None:
            return False
        try:
            btn = row.locator(self.ACTION_VIEW_BTN_IN_ROW).first
            if btn.count() == 0:
                return False
        except Exception:
            return False
        try:
            btn.scroll_into_view_if_needed()
            btn.click(force=True)
        except Exception:
            return False
        self.page.wait_for_timeout(1500)
        return True

    def is_modal_open(self, timeout=10000):
        try:
            self.page.locator(self.MODAL_CONTAINER).first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def close_modal(self):
        """Closes via the confirmed x-on:keydown.escape.window handler.
        No explicit in-modal close button was captured (modal content was
        empty at DOM-capture time — same situation as SMS incoming messages)."""
        try:
            self.page.keyboard.press("Escape")
        except Exception:
            pass
        self.page.wait_for_timeout(1000)

    # ── Export CSV ───────────────────────────────────────────────────────────

    def export_csv(self, timeout=30000):
        """Triggers the Export CSV button (Alpine @click="$wire.incomingMessageExport()")
        and captures the resulting download via Playwright's native download
        event (replaces the Selenium mtime-polling approach)."""
        try:
            link = self.h.wait_for_element_clickable(self.EXPORT_CSV_BTN, timeout=10000)
            link.scroll_into_view_if_needed()
            with self.page.expect_download(timeout=timeout) as dl_info:
                link.click()
            download = dl_info.value
            filename = download.suggested_filename or "rcs_incoming_messages_export.csv"
            dest = os.path.join(DOWNLOAD_DIR, filename)
            download.save_as(dest)
            return {
                "elapsed_s": None,
                "file_path": dest,
                "file_size": os.path.getsize(dest),
            }
        except Exception:
            return None

    # ── Pagination ───────────────────────────────────────────────────────────

    def get_pagination_results_text(self):
        el = self.h.wait_for_element_visible(self.PAGINATION_RESULTS_TEXT)
        return el.inner_text().strip()

    # ── Performance ──────────────────────────────────────────────────────────

    def get_page_load_time_ms(self):
        try:
            return self.page.evaluate(
                "() => window.performance.timing.loadEventEnd - "
                "window.performance.timing.navigationStart"
            )
        except Exception:
            return None
