from pages.common.base_page import BasePage


class RcsUsageAnalyticsPage(BasePage):

    REPORT_URL = "/rcs/analytics/product"
    TABLE_NAME = "rcs_product_report"

    # Confirmed column order from the live <thead> (table-head-0 .. -13)
    COLUMN_INDEX = {
        "duration": 0, "total_count": 1, "sent_count": 2,
        "delivered_count": 3, "read_count": 4, "failed_count": 5,
        "rejected_count": 6, "dlr_awaited_count": 7, "interactions": 8,
        "quick_reply_total": 9, "quick_reply_unique": 10,
        "cta_total_clicks": 11, "cta_unique_clicks": 12,
        "total_charges": 13,
    }

    # ── Page header ───────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'RCS Usage Analytics')]"

    # ── Top filter bar ───────────────────────────────────────────────────────
    DATE_RANGE_PICKER = "#rcs-product-date-range-picker"
    REPORT_TYPE_SELECT = "#rcs-product-report-type-select"
    GROUP_BY_LABEL = "#rcs-product-dimension-multiselect-label"
    GROUP_BY_BUTTON = "xpath=//span[@id='rcs-product-dimension-multiselect-label']/ancestor::button[1]"
    GROUP_BY_DROPDOWN = "#rcs-product-dimension-multiselect-dropdown"

    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search by Usage']"

    # ── Filters popover ──────────────────────────────────────────────────────
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')]"
    FILTER_DEPARTMENT_INPUT = ".async-select-filter-department input[placeholder='Search Department']"
    FILTER_USER_INPUT = ".async-select-filter-user input[placeholder='Search User']"
    FILTER_SOURCE_WRAPPER = f"#{TABLE_NAME}-filter-source-wrapper"
    FILTER_PRODUCT_WRAPPER = f"#{TABLE_NAME}-filter-product-wrapper"
    FILTER_SOURCE_SELECT_ALL = f"#{TABLE_NAME}-filter-source-select-all"
    FILTER_PRODUCT_SELECT_ALL = f"#{TABLE_NAME}-filter-product-select-all"

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
        return "/rcs/analytics/product" in url and "login" not in url.lower()

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

    # ── Filters popover ──────────────────────────────────────────────────────

    def open_filters_popover(self):
        if self._is_visible(self.FILTER_DEPARTMENT_INPUT, timeout=1000):
            return
        self._js_click(self.FILTERS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def _select_first_async_option(self, container_css):
        """Best-effort: after typing into an async-select search box, click
        the first appearing option in its results list. Same caveat as
        SMS Usage Report: the listbox container (div[x-ref='options']
        [role='listbox']) IS confirmed, but no populated option-item markup
        was captured (only the empty 'No results found' state) — returns
        False if none match, rather than guessing further."""
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

    def toggle_source_filter_option(self, value):
        """value: 'Campaign' | 'API' | 'Flow' | 'Incoming' (CONFIRMED live
        DOM values — RCS's "Incoming" replaces SMS's "SMPP")."""
        self.open_filters_popover()
        cb = self.h.wait_for_element_visible(
            f"#{self.TABLE_NAME}-filter-source-wrapper input[value='{value}']")
        cb.scroll_into_view_if_needed()
        cb.click(force=True)
        self.page.wait_for_timeout(1500)

    def toggle_product_filter_option(self, value):
        """value: 'promotional' | 'transactional' | 'otp' | 'multi_use'
        (CONFIRMED live DOM — four options here, matching RCS's own
        service types, vs three on SMS Usage Report).

        Migration note (carried over from the Selenium version): the
        checkbox is NOT wrapped in any element with id
        "{TABLE_NAME}-filter-product-wrapper" — the real captured DOM shows
        the outer container is a plain <div class="rounded-md shadow-sm">
        with no id attribute at all. FILTER_PRODUCT_WRAPPER is kept only
        for reference; the checkboxes themselves DO have confirmed unique
        ids following the pattern "{TABLE_NAME}-filter-product-0/1/2/3"
        alongside their "value" attribute, so this targets that id prefix
        directly instead of relying on the non-existent wrapper."""
        self.open_filters_popover()
        cb = self.h.wait_for_element_visible(
            f"input[id^='{self.TABLE_NAME}-filter-product-'][value='{value}']")
        cb.scroll_into_view_if_needed()
        cb.click(force=True)
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
        """dim: 'product' | 'source' | 'department' | 'user' (all four
        CONFIRMED live DOM, same set as SMS Usage Report)."""
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
