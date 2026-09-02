import os
import time

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR


class RcsCampaignAnalyticsPage(BasePage):

    REPORT_URL = "/rcs/analytics/campaign"
    TABLE_NAME = "rcs_campaign_report"

    # Confirmed column order from the live <thead> (table-head-0 .. -18)
    COLUMN_INDEX = {
        "action": 0, "duration": 1, "product": 2, "agent": 3,
        "campaign_name": 4, "template_name": 5, "total_count": 6,
        "sent_count": 7, "delivered_count": 8, "read_count": 9,
        "failed_count": 10, "rejected_count": 11, "dlr_awaited_count": 12,
        "interactions": 13, "quick_reply_total": 14, "quick_reply_unique": 15,
        "cta_total_clicks": 16, "cta_unique_clicks": 17, "total_charges": 18,
    }

    # ── Page header ───────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'RCS Campaign Analytics')]"

    # ── Top filter bar ───────────────────────────────────────────────────────
    DATE_RANGE_PICKER = "#rcs-campaign-date-range-picker"
    REPORT_TYPE_SELECT = "#rcs-campaign-report-type-select"
    GROUP_BY_LABEL = "#rcs-campaign-dimension-multiselect-label"
    GROUP_BY_BUTTON = "xpath=//span[@id='rcs-campaign-dimension-multiselect-label']/ancestor::button[1]"
    GROUP_BY_DROPDOWN = "#rcs-campaign-dimension-multiselect-dropdown"

    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search by Campaign']"

    # ── Filters popover ──────────────────────────────────────────────────────
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')]"
    FILTER_AGENT_INPUT = "input[placeholder='Search Agent']"
    FILTER_DEPARTMENT_INPUT = "input[placeholder='Search Department']"
    FILTER_USER_INPUT = "input[placeholder='Search User']"
    FILTER_PRODUCT_SELECT = f"#{TABLE_NAME}-filter-product"

    # ── Columns dropdown ─────────────────────────────────────────────────────
    COLUMNS_BUTTON = "xpath=//button[contains(normalize-space(.),'Columns')]"
    COLUMN_CHECKBOXES = (
        f"xpath=//div[contains(@*[name()='wire:key'],'{TABLE_NAME}-columnSelect-') and "
        f"not(contains(@*[name()='wire:key'],'columnSelect-selectAll'))]//input[@type='checkbox']"
    )

    # ── Export ────────────────────────────────────────────────────────────────
    EXPORT_CSV_BUTTON = "xpath=//button[contains(normalize-space(.),'Export CSV')]"

    # ── Table ─────────────────────────────────────────────────────────────────
    TABLE = f"#table-{TABLE_NAME}"
    TABLE_HEADERS = f"#table-{TABLE_NAME} thead th"
    TABLE_ROWS = f"#table-{TABLE_NAME} tbody tr"
    DURATION_SORT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('duration')\")]"
    # First row's Preview/status-modal trigger button (CONFIRMED live DOM:
    # wire:click.prevent="openCampaignStatusModal(...)", tooltip "Preview").
    ROW_PREVIEW_BTN = f"#table-{TABLE_NAME} tbody tr [wire\\:click\\.prevent*='openCampaignStatusModal']"
    NO_RECORDS_MSG = (
        "xpath=//*[contains(text(),'No records') or contains(text(),'No data') "
        "or contains(text(),'No results')]"
    )

    # ── Pagination ────────────────────────────────────────────────────────────
    PAGINATION_RESULTS_TEXT = ".paged-pagination-results"
    NEXT_PAGE_BTN = f"xpath=//button[contains(@*[name()='wire:click'],\"nextPage('{TABLE_NAME}')\")]"

    # ── Navigation / page state ─────────────────────────────────────────────

    def navigate_to_report(self):
        self.open(self.REPORT_URL)
        self.page.wait_for_timeout(2000)
        return self

    def is_report_page(self):
        url = self.get_current_url()
        return "/rcs/analytics/campaign" in url and "login" not in url.lower()

    def get_page_title_text(self):
        return self.h.wait_for_element_visible(self.PAGE_TITLE).inner_text().strip()

    def are_filters_visible(self):
        return (self.is_element_present(self.DATE_RANGE_PICKER, timeout=5000)
                and self.is_element_present(self.REPORT_TYPE_SELECT, timeout=5000)
                and self.is_element_present(self.GROUP_BY_LABEL, timeout=5000))

    def _is_visible(self, locator, timeout=1000):
        try:
            return self.page.locator(locator).first.is_visible()
        except Exception:
            return False

    # ── Search ────────────────────────────────────────────────────────────────

    def search(self, value):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.fill(value)
        self.page.wait_for_timeout(1500)

    def clear_search(self):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.fill("")
        self.page.wait_for_timeout(500)
        self.h.wait_until(lambda: self.has_records() or self.has_no_records_message(),
                           timeout_ms=6000, interval_ms=500)
        self.page.wait_for_timeout(500)
        import re
        current_url = self.get_current_url()
        if re.search(r"[?&][\w-]*search=(?!&|$)[^&]+", current_url):
            self.navigate_to_report()

    # ── Table / rows ─────────────────────────────────────────────────────────

    def has_records(self):
        return self.is_element_present(self.TABLE_ROWS, timeout=5000) and self.get_row_count() > 0

    def has_no_records_message(self):
        if self.is_element_present(self.NO_RECORDS_MSG, timeout=3000):
            return True
        return self.get_row_count() == 0

    def get_row_count(self):
        return self._count_data_rows(self.TABLE_ROWS)

    def get_visible_column_headers(self):
        return self._get_headers_safe(self.TABLE_HEADERS)

    def get_column_values(self, column_name):
        idx = self.COLUMN_INDEX.get(column_name)
        if idx is None:
            return []
        rows = self.page.locator(self.TABLE_ROWS)
        values = []
        for i in range(rows.count()):
            tds = rows.nth(i).locator("td")
            if tds.count() > idx:
                values.append(tds.nth(idx).inner_text().strip())
        return values

    def sort_by_duration(self):
        self._js_click(self.DURATION_SORT_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def click_first_row_preview(self):
        """Clicks the first row's Preview/status-modal trigger button.
        Only verifies the click doesn't error/break the page — modal
        internals are UNCONFIRMED, so this deliberately does not assert on
        modal content."""
        self._js_click(self.ROW_PREVIEW_BTN, timeout=10000)
        self.page.wait_for_timeout(1000)

    # ── Filters popover ──────────────────────────────────────────────────────

    def open_filters_popover(self):
        if self._is_visible(self.FILTER_AGENT_INPUT, timeout=1000):
            return
        self._js_click(self.FILTERS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def _select_first_async_option(self):
        """Best-effort: after typing into an async-select search box, click
        the first appearing option in its results list."""
        try:
            options = self.page.locator(
                "[x-ref='options'] [role='option'], "
                "[x-ref='options'] li, "
                "[x-ref='options'] button")
            for i in range(options.count()):
                opt = options.nth(i)
                if opt.is_visible():
                    opt.scroll_into_view_if_needed()
                    opt.click(force=True)
                    self.page.wait_for_timeout(1000)
                    return True
        except Exception:
            pass
        return False

    def filter_by_agent(self, text):
        """CONFIRMED live DOM: Agent is a NEW async-select filter on this
        report not present on Usage Analytics."""
        self.open_filters_popover()
        box = self.h.wait_for_element_visible(self.FILTER_AGENT_INPUT)
        box.click()
        box.type(text)
        self.page.wait_for_timeout(1000)
        return self._select_first_async_option()

    def filter_by_department(self, text):
        self.open_filters_popover()
        box = self.h.wait_for_element_visible(self.FILTER_DEPARTMENT_INPUT)
        box.click()
        box.type(text)
        self.page.wait_for_timeout(1000)
        return self._select_first_async_option()

    def filter_by_user(self, text):
        self.open_filters_popover()
        box = self.h.wait_for_element_visible(self.FILTER_USER_INPUT)
        box.click()
        box.type(text)
        self.page.wait_for_timeout(1000)
        return self._select_first_async_option()

    def select_product_filter(self, value):
        """value: '' (All) | 'Transactional' | 'Promotional' | 'OTP'."""
        self.open_filters_popover()
        self.h.select_option(self.FILTER_PRODUCT_SELECT, value=value)
        self.page.wait_for_timeout(1500)

    def get_product_filter_value(self):
        return self.h.wait_for_element_visible(self.FILTER_PRODUCT_SELECT).input_value()

    # ── Report Type ──────────────────────────────────────────────────────────

    def select_report_type(self, value):
        """value: 'daily' | 'weekly' | 'monthly'"""
        self.h.select_option(self.REPORT_TYPE_SELECT, value=value)
        self.page.wait_for_timeout(1500)

    def get_report_type(self):
        return self.h.wait_for_element_visible(self.REPORT_TYPE_SELECT).input_value()

    # ── Group By ─────────────────────────────────────────────────────────────

    def open_group_by_dropdown(self):
        if self._is_visible(self.GROUP_BY_DROPDOWN, timeout=1000):
            return
        self._js_click(self.GROUP_BY_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def toggle_group_by_dimension(self, dim):
        """dim: 'product' | 'department' | 'user'. CONFIRMED live DOM: only
        THREE dimensions here — no 'source', unlike Usage Analytics' four.
        Also note 'product' is PRE-CHECKED by default on page load."""
        self.open_group_by_dropdown()
        cb = self.h.wait_for_element_visible(f"input[data-dimension='{dim}'], input[value='{dim}']")
        cb.scroll_into_view_if_needed()
        cb.click(force=True)
        self.page.wait_for_timeout(1000)

    def is_group_by_dimension_checked(self, dim):
        cb = self.h.wait_for_element_visible(f"input[data-dimension='{dim}'], input[value='{dim}']")
        return cb.is_checked()

    def get_group_by_label_text(self):
        return self.h.wait_for_element_visible(self.GROUP_BY_LABEL).inner_text().strip()

    # ── Date range (flatpickr) ───────────────────────────────────────────────

    def open_date_range_picker(self):
        self._js_click(self.DATE_RANGE_PICKER, timeout=10000)
        self.page.wait_for_timeout(500)

    _DAY_CELLS_CSS = (".flatpickr-calendar.open .flatpickr-day:not(.flatpickr-disabled)"
                       ":not(.prevMonthDay):not(.nextMonthDay)")

    def select_date_range(self, from_day_offset=10, to_day_offset=3):
        self.open_date_range_picker()

        def _click_cell(offset_from_end):
            days = self.page.locator(self._DAY_CELLS_CSS)
            count = days.count()
            if count <= offset_from_end:
                return False
            days.nth(count - offset_from_end - 1).click(force=True)
            return True

        if not _click_cell(from_day_offset):
            return False
        self.page.wait_for_timeout(300)
        if not _click_cell(to_day_offset):
            return False
        self.page.wait_for_timeout(1500)
        return True

    def get_date_range_value(self):
        # flatpickr sets the input's live DOM *value property* via JS, not
        # the static HTML "value" *attribute* -- browsers never sync the
        # attribute back when script assigns .value, so get_attribute
        # ("value") always read None here even after a real selection.
        # input_value() reads the live property instead.
        return self.h.wait_for_element_visible(self.DATE_RANGE_PICKER).input_value()

    # ── Columns dropdown ─────────────────────────────────────────────────────

    def open_columns_dropdown(self):
        if self._is_visible(self.COLUMN_CHECKBOXES, timeout=1000):
            return
        self._js_click(self.COLUMNS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def uncheck_first_optional_column(self):
        """Returns the unchecked checkbox's `value` attribute (e.g.
        'total-count') on success, or None if there was nothing to uncheck."""
        self.open_columns_dropdown()
        checkboxes = self.page.locator(self.COLUMN_CHECKBOXES)
        for i in range(checkboxes.count()):
            cb = checkboxes.nth(i)
            if cb.is_checked():
                value = cb.get_attribute("value")
                cb.scroll_into_view_if_needed()
                cb.click(force=True)
                self.page.wait_for_timeout(800)
                return value
        return None

    def check_column(self, value):
        self.open_columns_dropdown()
        cb = self.page.locator(f"input[type='checkbox'][value='{value}']")
        if cb.count() == 0:
            return False
        cb = cb.first
        if not cb.is_checked():
            cb.scroll_into_view_if_needed()
            cb.click(force=True)
            self.page.wait_for_timeout(800)
        return True

    # ── Export ────────────────────────────────────────────────────────────────

    def click_export_csv(self, timeout_ms=30000):
        """Clicks Export CSV, capturing the resulting download via
        page.expect_download() -- previously just clicked and slept
        (self._js_click + wait_for_timeout(1500)) without capturing
        anything, the same broken pattern originally found (and fixed)
        on several SMS report pages and RcsErrorCodeAnalyticsPage (see
        pages/sms/sms_usage_report_page.py's click_export_csv()
        docstring for the reference fix).

        Returns {"elapsed_s", "file_path", "file_size"} on success, or
        None on failure (timeout / no download triggered) -- kept as a
        never-raises contract so every existing caller of this method,
        which discards the return value, is unaffected.
        """
        try:
            btn = self.h.wait_for_element_clickable(self.EXPORT_CSV_BUTTON, timeout=10000)
            btn.scroll_into_view_if_needed()
            start = time.time()
            with self.page.expect_download(timeout=timeout_ms) as dl_info:
                self._js_click(self.EXPORT_CSV_BUTTON, timeout=10000)
            download = dl_info.value
            filename = download.suggested_filename or "rcs_campaign_report_export.csv"
            dest = os.path.join(DOWNLOAD_DIR, filename)
            download.save_as(dest)
            return {
                "elapsed_s": time.time() - start,
                "file_path": dest,
                "file_size": os.path.getsize(dest),
            }
        except Exception:
            return None

    # ── Pagination ────────────────────────────────────────────────────────────

    def get_pagination_results_text(self):
        return self.h.wait_for_element_visible(self.PAGINATION_RESULTS_TEXT).inner_text().strip()

    def click_next_page(self):
        self._js_click(self.NEXT_PAGE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    # ── Performance ──────────────────────────────────────────────────────────

    def get_page_load_time_ms(self):
        try:
            return self.page.evaluate(
                "() => window.performance.timing.loadEventEnd - window.performance.timing.navigationStart"
            )
        except Exception:
            return None
