import os
import time

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR


class SmsTemplateReportPage(BasePage):

    REPORT_URL = "/channels/sms/reports/template"
    TABLE_NAME = "sms_template_report"

    # Confirmed column order from the live <thead> (table-head-0 .. -20)
    COLUMN_INDEX = {
        "duration": 0, "template_name": 1, "dlt_template_id": 2, "product": 3,
        "total_count": 4, "submitted_count": 5, "delivered_count": 6,
        "failed_count": 7, "rejected_count": 8, "dlr_awaited_count": 9,
        "total_units": 10, "submitted_units": 11, "delivered_units": 12,
        "failed_units": 13, "rejected_units": 14, "dlr_awaited_units": 15,
        "total_charges": 16, "delivery_charges": 17, "surcharge": 18,
        "delivery_surcharge": 19, "delivery_pct": 20,
    }

    # ── Page header ───────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'Template Report')]"

    # ── Top filter bar ───────────────────────────────────────────────────────
    DATE_RANGE_PICKER = "#template-date-range-picker"
    REPORT_TYPE_SELECT = "#report-type-select"
    GROUP_BY_LABEL = "#template-dimension-multiselect-label"
    GROUP_BY_BUTTON = "xpath=//span[@id='template-dimension-multiselect-label']/ancestor::button[1]"
    GROUP_BY_DROPDOWN = "#template-dimension-multiselect-dropdown"

    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search by Template']"

    # ── Filters popover ──────────────────────────────────────────────────────
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')]"
    FILTER_PRODUCT_SELECT = f"#{TABLE_NAME}-filter-product"
    FILTER_DEPARTMENT_INPUT = ".async-select-filter-department input[placeholder='Search Department']"
    FILTER_USER_INPUT = ".async-select-filter-user input[placeholder='Search User']"

    # ── Columns dropdown ─────────────────────────────────────────────────────
    COLUMNS_BUTTON = "xpath=//button[contains(normalize-space(.),'Columns')]"
    # NOTE: Chrome's native document.evaluate() rejects the "@wire:key" /
    # "@wire:click" XPath shorthand as an unresolvable namespace prefix —
    # use @*[name()='wire:key'] / @*[name()='wire:click'] instead everywhere.
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
        return "/channels/sms/reports/template" in url and "login" not in url.lower()

    def get_page_title_text(self):
        return self.h.wait_for_element_visible(self.PAGE_TITLE).inner_text().strip()

    def are_filters_visible(self):
        return (self.is_element_present(self.DATE_RANGE_PICKER, timeout=5000)
                and self.is_element_present(self.REPORT_TYPE_SELECT, timeout=5000)
                and self.is_element_present(self.GROUP_BY_LABEL, timeout=5000))

    def _is_visible(self, locator, timeout=1000):
        """Presence + visibility check, used to make the Filters/Group
        By/Columns toggle buttons idempotent (each is a plain Alpine
        `open = !open` toggle, so calling _js_click a second time while
        already open would close it instead of being a no-op)."""
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
        self.h.wait_until(
            lambda: self.has_records() or self.has_no_records_message(),
            timeout_ms=6000, interval_ms=500
        )
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
        
        for _ in range(3):
            try:
                rows = self.page.locator(self.TABLE_ROWS).all()
                values = []
                for row in rows:
                    tds = row.locator("td").all()
                    if len(tds) > idx:
                        values.append(tds[idx].inner_text().strip())
                return values
            except Exception:
                self.page.wait_for_timeout(500)
        return []

    def sort_by_duration(self):
        self._js_click(self.DURATION_SORT_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    # ── Filters popover ──────────────────────────────────────────────────────

    def open_filters_popover(self):
        if self._is_visible(self.FILTER_PRODUCT_SELECT, timeout=1000):
            return
        self._js_click(self.FILTERS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def filter_by_product(self, value):
        """value: '' (All) | 'P' (Promotional) | 'T' (Transactional) | 'O' (OTP)"""
        self.open_filters_popover()
        self.h.select_option(self.FILTER_PRODUCT_SELECT, value=value)
        self.page.wait_for_timeout(1500)

    def _select_first_async_option(self, container_css):
        """Best-effort: after typing into an async-select search box, click
        the first appearing option in its results list. Same caveat as
        every other SMS report suite: the listbox container (div[x-ref=
        'options'][role='listbox']) IS confirmed, but no populated option-
        item markup was captured (only the empty 'No results found' state)
        — returns False if none match, rather than guessing further."""
        try:
            options = self.page.locator(
                f"{container_css} [x-ref='options'] [role='option'], "
                f"{container_css} [x-ref='options'] li, "
                f"{container_css} [x-ref='options'] button")
            for i in range(options.count()):
                opt = options.nth(i)
                if opt.is_visible():
                    opt.click(force=True)
                    self.page.wait_for_timeout(1000)
                    return True
        except Exception:
            pass
        return False

    def filter_by_department(self, text):
        self.open_filters_popover()
        box = self.h.wait_for_element_visible(self.FILTER_DEPARTMENT_INPUT)
        box.click()
        box.type(text)
        self.page.wait_for_timeout(1000)
        return self._select_first_async_option(".async-select-filter-department")

    def filter_by_user(self, text):
        self.open_filters_popover()
        box = self.h.wait_for_element_visible(self.FILTER_USER_INPUT)
        box.click()
        box.type(text)
        self.page.wait_for_timeout(1000)
        return self._select_first_async_option(".async-select-filter-user")

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
        """dim: 'product' | 'department' | 'user'"""
        self.open_group_by_dropdown()
        cb = self.h.wait_for_element_visible(f"input[data-dimension='{dim}']")
        cb.scroll_into_view_if_needed()
        cb.click(force=True)
        self.page.wait_for_timeout(1000)

    def get_group_by_label_text(self):
        return self.h.wait_for_element_visible(self.GROUP_BY_LABEL).inner_text().strip()

    # ── Date range (flatpickr) ───────────────────────────────────────────────

    def open_date_range_picker(self):
        self._js_click(self.DATE_RANGE_PICKER, timeout=10000)
        self.page.wait_for_timeout(500)

    _DAY_CELLS_CSS = (".flatpickr-calendar.open .flatpickr-day:not(.flatpickr-disabled)"
                       ":not(.prevMonthDay):not(.nextMonthDay)")

    def select_date_range(self, from_day_offset=10, to_day_offset=3):
        """Same flatpickr range-mode interaction as every other SMS report
        suite (CONFIRMED live DOM: div.flatpickr-calendar.rangeMode,
        maxDate: 'today'). Playwright's Locator API re-resolves fresh on
        every call, so no stale-element retry is needed the way the
        Selenium version required.

        Returns False (rather than asserting) if the grid doesn't have
        enough selectable same-month cells."""
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
        """Re-check a specific column checkbox by its `value` attribute.
        Same sessionStorage-persistence gotcha as every other SMS report
        suite — column visibility survives a plain navigate_to_report(),
        so this restores state after uncheck_first_optional_column() in
        tests."""
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
        page.expect_download() (previously just clicked and slept, without
        capturing anything).

        Returns {"elapsed_s", "file_path", "file_size"} on success, or
        None on failure -- never-raises contract, same as the other SMS
        report pages, so any existing caller that discards the return
        value is unaffected.
        """
        try:
            btn = self.h.wait_for_element_clickable(self.EXPORT_CSV_BUTTON, timeout=10000)
            btn.scroll_into_view_if_needed()
            start = time.time()
            with self.page.expect_download(timeout=timeout_ms) as dl_info:
                self._js_click(self.EXPORT_CSV_BUTTON, timeout=10000)
            download = dl_info.value
            filename = download.suggested_filename or "sms_template_report_export.csv"
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

    def is_next_page_enabled(self):
        """Returns True if the Next Page button exists, is visible, and is not disabled."""
        locators = self.page.locator(self.NEXT_PAGE_BTN).all()
        for loc in locators:
            if loc.is_visible():
                return loc.get_attribute("disabled") is None
        return False

    def click_next_page(self):
        self._js_click(self.NEXT_PAGE_BTN + " >> visible=true", timeout=10000)
        self.page.wait_for_timeout(1500)


    # ── Performance ──────────────────────────────────────────────────────────

    def get_page_load_time_ms(self):
        """Uses the standard browser Performance Timing API (not app-
        specific) to measure real navigation-to-load time."""
        try:
            return self.page.evaluate(
                "() => window.performance.timing.loadEventEnd - "
                "window.performance.timing.navigationStart"
            )
        except Exception:
            return None
