from pages.common.base_page import BasePage


class RcsErrorCodeAnalyticsPage(BasePage):

    REPORT_URL = "/rcs/analytics/error-code"
    TABLE_NAME = "rcs_error_code_report"

    # Confirmed column order from the live <thead> (table-head-0 .. -5)
    COLUMN_INDEX = {
        "duration": 0, "product": 1, "error_code": 2,
        "error_description": 3, "total_count": 4, "percentage_share": 5,
    }

    # ── Page header ───────────────────────────────────────────────────────────
    # CONFIRMED live DOM: both the breadcrumb and this page's own <h1> read
    # "RCS Error Code Report" — this report does NOT follow the
    # "RCS {X} Analytics" title pattern used by every sibling report.
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'RCS Error Code Report')]"

    # ── Top filter bar ───────────────────────────────────────────────────────
    DATE_RANGE_PICKER = "#rcs-error-code-date-range-picker"
    REPORT_TYPE_SELECT = "#rcs-error-code-report-type-select"
    GROUP_BY_LABEL = "#rcs-error-code-dimension-multiselect-label"
    GROUP_BY_BUTTON = "xpath=//span[@id='rcs-error-code-dimension-multiselect-label']/ancestor::button[1]"
    GROUP_BY_DROPDOWN = "#rcs-error-code-dimension-multiselect-dropdown"

    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search by error/provider']"

    # ── Filters popover ──────────────────────────────────────────────────────
    # CONFIRMED live DOM: no Agent/Department/User fields on this report at
    # all — only Product and Source, both checkbox multiselects.
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')]"
    FILTER_PRODUCT_SELECT_ALL = f"#{TABLE_NAME}-filter-product-select-all"
    FILTER_SOURCE_SELECT_ALL = f"#{TABLE_NAME}-filter-source-select-all"
    # CONFIRMED live DOM option values, in captured order
    PRODUCT_FILTER_VALUES = ["promotional", "transactional", "otp", "multi_use"]
    SOURCE_FILTER_VALUES = ["Campaign", "API", "Flow", "Incoming"]

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
        return "/rcs/analytics/error-code" in url and "login" not in url.lower()

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
        rows = self.page.locator(self.TABLE_ROWS)
        count = rows.count()
        if count == 1:
            text = rows.first.inner_text().lower()
            return any(x in text for x in ["no ", "0", "not found", "nothing"])
        return count == 0

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

    # ── Filters popover (Product / Source checkbox multiselects) ───────────

    def open_filters_popover(self):
        if self._is_visible(self.FILTER_PRODUCT_SELECT_ALL, timeout=1000):
            return
        self._js_click(self.FILTERS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def _filter_checkbox_locator(self, field, value):
        """CONFIRMED live DOM: each option checkbox carries its raw filter
        value in a `value` attribute, scoped inside the
        {TABLE_NAME}-filter-{field}-wrapper block. Matching on value is more
        robust than the numeric -{n} id suffix, which is positional."""
        return f"#{self.TABLE_NAME}-filter-{field}-wrapper input[type='checkbox'][value='{value}']"

    def toggle_product_filter(self, value):
        """value: one of PRODUCT_FILTER_VALUES ('promotional' | 'transactional'
        | 'otp' | 'multi_use'). CONFIRMED live DOM: checkbox multiselect, NOT
        a plain <select> — unlike every other RCS Analytics report's Product
        filter."""
        self.open_filters_popover()
        cb = self.h.wait_for_element_visible(self._filter_checkbox_locator("product", value))
        cb.scroll_into_view_if_needed()
        cb.click(force=True)
        self.page.wait_for_timeout(1500)

    def is_product_filter_checked(self, value):
        cb = self.h.wait_for_element_visible(self._filter_checkbox_locator("product", value))
        return cb.is_checked()

    def toggle_source_filter(self, value):
        """value: one of SOURCE_FILTER_VALUES ('Campaign' | 'API' | 'Flow' |
        'Incoming'). CONFIRMED live DOM: checkbox multiselect."""
        self.open_filters_popover()
        cb = self.h.wait_for_element_visible(self._filter_checkbox_locator("source", value))
        cb.scroll_into_view_if_needed()
        cb.click(force=True)
        self.page.wait_for_timeout(1500)

    def is_source_filter_checked(self, value):
        cb = self.h.wait_for_element_visible(self._filter_checkbox_locator("source", value))
        return cb.is_checked()

    def select_all_product_filter(self):
        """Clicks the 'All' checkbox for Product (wire:input=
        "selectAllFilterOptions('product')", CONFIRMED live DOM)."""
        self.open_filters_popover()
        self._js_click(self.FILTER_PRODUCT_SELECT_ALL, timeout=10000)
        self.page.wait_for_timeout(1500)

    def select_all_source_filter(self):
        """Clicks the 'All' checkbox for Source (wire:input=
        "selectAllFilterOptions('source')", CONFIRMED live DOM)."""
        self.open_filters_popover()
        self._js_click(self.FILTER_SOURCE_SELECT_ALL, timeout=10000)
        self.page.wait_for_timeout(1500)

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
        """dim: 'product' | 'source' | 'provider'. CONFIRMED live DOM: THIS
        report's three dimensions are product/source/provider — genuinely
        different from every other RCS Analytics report's product/
        department/user set. Also note 'product' is PRE-CHECKED by default
        on page load (CONFIRMED wire:snapshot dimensions:["product"])."""
        self.open_group_by_dropdown()
        cb = self.h.wait_for_element_visible(f"input[data-dimension='{dim}']")
        cb.scroll_into_view_if_needed()
        cb.click(force=True)
        self.page.wait_for_timeout(1000)

    def is_group_by_dimension_checked(self, dim):
        cb = self.h.wait_for_element_visible(f"input[data-dimension='{dim}']")
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
        'total-count') on success, or None if there was nothing to uncheck.
        CONFIRMED live DOM: only 2 toggleable columns exist here
        (total-count, percentage-share)."""
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

    def click_export_csv(self):
        self._js_click(self.EXPORT_CSV_BUTTON, timeout=10000)
        self.page.wait_for_timeout(1500)

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
