import os

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR


class SmsIncomingMessagesPage(BasePage):

    REPORT_URL = "/channels/sms/incoming-messages"
    TABLE_NAME = "sms_incoming_messages"

    # Confirmed column order (ALL 6 columns selected by default).
    COLUMN_INDEX = {
        "action": 0, "campaign_name": 1, "sender_id": 2,
        "country_code": 3, "user_number": 4, "received_at": 5,
    }

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'SMS Incoming Messages')]"
    BREADCRUMB = "nav[aria-label='Breadcrumb']"

    # ── Top action buttons (confirmed) ──────────────────────────────────────
    REFRESH_BTN = (
        "xpath=//a[contains(@href,'/channels/sms/incoming-messages') and contains(normalize-space(.),'Refresh')]"
    )
    EXPORT_CSV_BTN = "xpath=//button[contains(normalize-space(.),'Export CSV')]"

    # ── Search ───────────────────────────────────────────────────────────────
    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search']"

    # ── Filters popover (confirmed: Sender ID select + native Received
    # From/To date+time pickers -- NOT flatpickr). ──────────────────────────
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')]"
    FILTER_SENDER_SELECT = "#sms_incoming_messages-filter-sender"
    FILTER_RECEIVED_FROM_DATE = "#sms_incoming_messages-filter-created_from-wrapper input[type='date']"
    FILTER_RECEIVED_FROM_TIME = "#sms_incoming_messages-filter-created_from-wrapper select"
    FILTER_RECEIVED_TO_DATE = "#sms_incoming_messages-filter-created_to-wrapper input[type='date']"
    FILTER_RECEIVED_TO_TIME = "#sms_incoming_messages-filter-created_to-wrapper select"
    # Best-effort: no rendered "Clear filters" pill was captured (no filter
    # was applied at DOM-capture time), but the wire:snapshot's listeners
    # array confirms a real "clearFilters"/"clear-filters" Livewire method
    # exists on this component.
    CLEAR_FILTERS_BTN = (
        "xpath=//button[contains(@*[name()='wire:click'],'clearFilters') "
        "or contains(@*[name()='wire:click.prevent'],'clearFilters') "
        "or normalize-space()='Clear']"
    )

    # ── Sorting ──────────────────────────────────────────────────────────────
    SORT_RECEIVED_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('created_at')\")]"
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
    # Best-effort: no genuine empty state was ever rendered in the captured
    # dump (6 real records existed) -- broadened case-insensitive locator,
    # same proven approach used on the Blocked Numbers page.
    NO_RECORDS_MSG = (
        "xpath=//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no record') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no data') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no result') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'not found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'nothing found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no messages')]"
    )

    # ── Action (View) ────────────────────────────────────────────────────────
    ACTION_VIEW_BTN_IN_ROW = "xpath=.//button[contains(@data-tooltip-target,'tooltip-view-')]"
    MODAL_CONTAINER = "#modal-container"

    # ── Pagination ───────────────────────────────────────────────────────────
    PAGINATION_RESULTS_TEXT = ".total-pagination-results"

    # ── Navigation / page state ─────────────────────────────────────────────

    def navigate_to_report(self):
        self.open(self.REPORT_URL)
        self.page.wait_for_timeout(2000)
        return self

    def is_report_page(self):
        url = self.get_current_url()
        return "/channels/sms/incoming-messages" in url and "login" not in url.lower()

    def get_page_title_text(self):
        return self.h.wait_for_element_visible(self.PAGE_TITLE).inner_text().strip()

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

    def _wait_for_search_to_settle(self, timeout=8000):
        end_time = self.page.evaluate("() => Date.now()") + timeout
        last_state = None
        while self.page.evaluate("() => Date.now()") < end_time:
            current = self.get_row_count()
            no_msg = self.is_element_present(self.NO_RECORDS_MSG, timeout=500)
            state = (current, no_msg)
            if state == last_state:
                return
            last_state = state
            self.page.wait_for_timeout(600)

    def search(self, value):
        """JS-driven single 'input' dispatch (not type char-by-char) to
        avoid a wire:model.live per-keystroke race -- same fix proven
        necessary on the SMS Error Codes and Blocked Numbers pages."""
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.evaluate(
            "(el, v) => { el.value = v; "
            "el.dispatchEvent(new Event('input', {bubbles: true})); "
            "el.dispatchEvent(new Event('change', {bubbles: true})); }",
            value
        )
        box.focus()
        box.press("Enter")
        box.blur()
        self.page.wait_for_timeout(500)
        self._wait_for_search_to_settle()
        self.page.wait_for_timeout(300)

    def clear_search(self):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.evaluate(
            "(el) => { el.value = ''; "
            "el.dispatchEvent(new Event('input', {bubbles: true})); "
            "el.dispatchEvent(new Event('change', {bubbles: true})); }"
        )
        self.page.wait_for_timeout(500)
        self._wait_for_search_to_settle()
        self.page.wait_for_timeout(300)

    # ── Table / rows ─────────────────────────────────────────────────────────

    def has_records(self):
        return self.is_element_present(self.TABLE_ROWS, timeout=5000) and self.get_row_count() > 0

    @staticmethod
    def _is_empty_state_row(tds):
        """Same rappasoft/laravel-livewire-tables empty-state placeholder
        detection proven necessary on the Blocked Numbers page (single
        <tr><td colspan="N">) -- reused verbatim since this is the same
        underlying table package."""
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
        if self._is_visible(self.FILTER_SENDER_SELECT, timeout=1000):
            return
        self._js_click(self.FILTERS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def filter_by_received_date_range(self, days_back=60):
        """Sets Received From = today-days_back, Received To = today (no
        time component -- the confirmed Alpine updateDateTime() logic
        falls back to 'T00:00' when only a date is set). Dispatches a
        native 'change' event since the confirmed Alpine binding listens
        on x-on:change, not x-on:input."""
        from datetime import date, timedelta

        self.open_filters_popover()
        from_input = self.h.wait_for_element_visible(self.FILTER_RECEIVED_FROM_DATE)
        from_value = (date.today() - timedelta(days=days_back)).isoformat()
        from_input.evaluate(
            "(el, v) => { el.value = v; el.dispatchEvent(new Event('change', {bubbles: true})); }",
            from_value
        )
        box.press("Enter")
        self.page.wait_for_timeout(500)
        to_input = self.h.wait_for_element_visible(self.FILTER_RECEIVED_TO_DATE)
        to_value = date.today().isoformat()
        to_input.evaluate(
            "(el, v) => { el.value = v; el.dispatchEvent(new Event('change', {bubbles: true})); }",
            to_value
        )
        box.press("Enter")
        self.page.wait_for_timeout(1500)
        return True

    def get_filter_received_from_value(self):
        # input_value(), not get_attribute('value') -- a real pytest run
        # showed this always returning None after
        # filter_by_received_date_range() sets the field via JS (el.value = v).
        # Setting .value in JS updates the live DOM property but NOT the
        # 'value' HTML attribute, and get_attribute('value') reads only the
        # attribute -- so it stayed at whatever it was before (nothing,
        # usually). input_value() reads the live property instead, which is
        # what actually reflects a JS-set value (same fix pattern already
        # used elsewhere in this project, e.g. the RCS download-center
        # filter verification).
        el = self.h.wait_for_element_visible(self.FILTER_RECEIVED_FROM_DATE)
        return el.input_value()

    def get_filter_received_to_value(self):
        el = self.h.wait_for_element_visible(self.FILTER_RECEIVED_TO_DATE)
        return el.input_value()

    def filter_by_sender(self, value):
        self.open_filters_popover()
        self.h.select_option(self.FILTER_SENDER_SELECT, value=value)
        self.page.wait_for_timeout(1500)

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
        """Restores the CONFIRMED default: ALL 6 columns checked."""
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
        """No explicit in-modal close button was captured (modal content
        was empty at DOM-capture time). Uses the confirmed
        x-on:keydown.escape.window handler instead."""
        try:
            self.page.keyboard.press("Escape")
        except Exception:
            pass
        self.page.wait_for_timeout(1000)

    # ── Export CSV ───────────────────────────────────────────────────────────

    def export_csv(self, timeout=30000):
        """Triggers the Export CSV button and captures the resulting
        download via Playwright's native download event (replaces the
        Selenium mtime-polling approach)."""
        try:
            btn = self.h.wait_for_element_clickable(self.EXPORT_CSV_BTN, timeout=10000)
            btn.scroll_into_view_if_needed()
            with self.page.expect_download(timeout=timeout) as dl_info:
                btn.click(force=True)
            download = dl_info.value
            filename = download.suggested_filename or "sms_incoming_messages_export.csv"
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
        return self.h.wait_for_element_visible(self.PAGINATION_RESULTS_TEXT).inner_text().strip()

    # ── Performance ──────────────────────────────────────────────────────────

    def get_page_load_time_ms(self):
        try:
            return self.page.evaluate(
                "() => window.performance.timing.loadEventEnd - "
                "window.performance.timing.navigationStart"
            )
        except Exception:
            return None
