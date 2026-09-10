from pages.common.base_page import BasePage


class WhatsappUsageAnalyticsPage(BasePage):

    REPORT_URL = "/whatsapp/analytics/usage"
    TABLE_NAME = "whatsapp_product_report"

    # Confirmed column order from the live <thead> (table-head-0 .. -13).
    # NOTE: no product/waba-number/other identifier columns exist on this
    # report at all — only duration + the 13 metrics.
    COLUMN_INDEX = {
        "duration": 0, "total": 1, "sent": 2, "delivered": 3, "read": 4,
        "failed": 5, "rejected": 6, "dlr_awaited": 7, "interactions": 8,
        "quick_reply_total": 9, "quick_reply_unique": 10,
        "cta_total_clicks": 11, "cta_unique_clicks": 12, "total_charges": 13,
    }

    # ── Page header ───────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'Usage Analytics')]"

    # ── Top filter bar ───────────────────────────────────────────────────────
    # NOTE: id prefix is "whatsapp-product-*", NOT "whatsapp-usage-*" —
    # CONFIRMED live DOM naming-convention break, unique to this report.
    DATE_RANGE_PICKER = "#whatsapp-product-date-range-picker"
    REPORT_TYPE_SELECT = "#whatsapp-product-report-type-select"
    GROUP_BY_LABEL = "#whatsapp-product-dimension-multiselect-label"
    GROUP_BY_BUTTON = (
        "xpath=//span[@id='whatsapp-product-dimension-multiselect-label']/ancestor::button[1]"
    )
    GROUP_BY_DROPDOWN = "#whatsapp-product-dimension-multiselect-dropdown"

    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search by Product']"

    # ── Filters popover ──────────────────────────────────────────────────────
    # CONFIRMED live DOM: Product and Source are BOTH checkbox multiselects
    # here (unlike every other WhatsApp Analytics report, where Product is a
    # plain <select> and there is no Source filter at all).
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')]"
    FILTER_PRODUCT_SELECT_ALL = f"#{TABLE_NAME}-filter-product-select-all"
    FILTER_SOURCE_SELECT_ALL = f"#{TABLE_NAME}-filter-source-select-all"
    # CONFIRMED live DOM option values, in captured order (note "MMLite"
    # mixed-case, different from the plain-<select> reports' "MMLITE")
    PRODUCT_FILTER_VALUES = ["AUTHENTICATION", "MARKETING", "MMLite", "UTILITY"]
    SOURCE_FILTER_VALUES = ["Campaign", "API", "Flow"]
    FILTER_DEPARTMENT_INPUT = ".async-select-filter-department input[placeholder='Search Department']"
    FILTER_USER_INPUT = ".async-select-filter-user input[placeholder='Search User']"

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

    _DAY_CELLS_CSS = (".flatpickr-calendar.open .flatpickr-day:not(.flatpickr-disabled)"
                       ":not(.prevMonthDay):not(.nextMonthDay)")

    # ── Navigation / page state ─────────────────────────────────────────────

    def navigate_to_report(self):
        self.open(self.REPORT_URL)
        self.page.wait_for_timeout(2000)
        return self

    def is_report_page(self):
        url = self.get_current_url()
        return "/whatsapp/analytics/usage" in url and "login" not in url.lower()

    def get_page_title_text(self):
        el = self.h.wait_for_element_visible(self.PAGE_TITLE)
        return el.inner_text().strip()

    def are_filters_visible(self):
        return (self.is_element_present(self.DATE_RANGE_PICKER, timeout=5000)
                and self.is_element_present(self.REPORT_TYPE_SELECT, timeout=5000)
                and self.is_element_present(self.GROUP_BY_LABEL, timeout=5000))

    def _is_visible(self, locator, timeout=1000):
        """Presence + visibility check, used to make the Filters/Group By/
        Columns toggle buttons idempotent (same rationale as every other
        report page in this project)."""
        try:
            loc = self.page.locator(locator)
            for i in range(loc.count()):
                if loc.nth(i).is_visible():
                    return True
            return False
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
        # Delegates to BasePage._count_data_rows() — see whatsapp_campaign_
        # analytics_page.get_row_count() docstring for the confirmed
        # Livewire re-render race this guards against. CONFIRMED via a real
        # pytest run in this project (WhatsApp Usage Analytics TC11: a
        # Livewire re-render mid-iteration, triggered by clear_search()
        # right after an invalid search, raised a StaleElementReference
        # error in the original Selenium suite).
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

    # ── Filters popover (Product / Source checkbox multiselects + async) ────

    def open_filters_popover(self):
        for _ in range(5):
            if self._is_visible(self.FILTER_DEPARTMENT_INPUT, timeout=1000):
                return
            self._js_click(self.FILTERS_BUTTON, timeout=5000)
            self.page.wait_for_timeout(1000)

    def _filter_checkbox_locator(self, field, value):
        """CONFIRMED live DOM: each option checkbox carries its raw filter
        value in a `value` attribute, scoped inside the
        {TABLE_NAME}-filter-{field}-wrapper block (same pattern as RCS
        Error Code Analytics' checkbox-multiselect filters)."""
        return f"#{self.TABLE_NAME}-filter-{field}-wrapper input[type='checkbox'][value='{value}']"

    def toggle_product_filter(self, value):
        """value: one of PRODUCT_FILTER_VALUES ('AUTHENTICATION' |
        'MARKETING' | 'MMLite' | 'UTILITY'). CONFIRMED live DOM: checkbox
        multiselect, NOT a plain <select> — unlike every other WhatsApp
        Analytics report's Product filter."""
        self.open_filters_popover()
        cb = self.h.wait_for_element_visible(self._filter_checkbox_locator("product", value))
        cb.scroll_into_view_if_needed()
        cb.click(force=True)
        self.page.wait_for_timeout(1500)

    def is_product_filter_checked(self, value):
        cb = self.h.wait_for_element_visible(self._filter_checkbox_locator("product", value))
        return cb.is_checked()

    def toggle_source_filter(self, value):
        """value: one of SOURCE_FILTER_VALUES ('Campaign' | 'API' | 'Flow').
        CONFIRMED live DOM: checkbox multiselect, only 3 values (no
        "Incoming" option, unlike RCS Error Code Analytics' Source
        filter)."""
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

    def _select_first_async_option(self, container_css):
        """Best-effort: same caveat as every async-select field built
        across this project — no populated option-item markup was
        captured (only the empty 'No results found' state)."""
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
        self._js_click(".async-select-filter-department")
        self.page.wait_for_timeout(500)
        box = self.h.wait_for_element_visible(self.FILTER_DEPARTMENT_INPUT)
        box.click()
        box.type(text)
        self.page.wait_for_timeout(1000)
        return self._select_first_async_option(".async-select-filter-department")

    def filter_by_user(self, text):
        self.open_filters_popover()
        self._js_click(".async-select-filter-user")
        self.page.wait_for_timeout(500)
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
        for _ in range(5):
            if self._is_visible(self.GROUP_BY_DROPDOWN, timeout=1000):
                return
            self._js_click(self.GROUP_BY_BUTTON, timeout=5000)
            self.page.wait_for_timeout(1000)

    def toggle_group_by_dimension(self, dim):
        """dim: 'product' | 'source' | 'department' | 'user'. CONFIRMED
        live DOM: FOUR dimensions here (unique among WhatsApp Analytics
        reports — every sibling has only 3: product/department/user).
        Also note NONE are pre-checked by default here (CONFIRMED
        wire:snapshot initialSelected = []), unlike every sibling report
        where "product" is pre-checked."""
        self.open_group_by_dropdown()
        cb = self.h.wait_for_element_visible(f"input[data-dimension='{dim}']")
        cb.scroll_into_view_if_needed()
        cb.click(force=True)
        self.page.wait_for_timeout(1000)

    def is_group_by_dimension_checked(self, dim):
        cb = self.h.wait_for_element_visible(f"input[data-dimension='{dim}']")
        return cb.is_checked()

    def get_group_by_label_text(self):
        el = self.h.wait_for_element_visible(self.GROUP_BY_LABEL)
        return el.inner_text().strip()

    # ── Date range (flatpickr) ───────────────────────────────────────────────

    def open_date_range_picker(self):
        for _ in range(5):
            self._js_click(self.DATE_RANGE_PICKER, timeout=5000)
            self.page.wait_for_timeout(1000)
            if self._is_visible(self._DAY_CELLS_CSS, timeout=1000):
                return

    def select_date_range(self, from_day_offset=10, to_day_offset=3):
        """Same flatpickr range-mode interaction as every other report in
        this project (CONFIRMED live DOM: div.flatpickr-calendar.rangeMode,
        mode: 'range', maxDate: 'today', dateFormat: 'd-m-Y'). Cells are
        restricted to same-month-only and re-queried fresh before each
        click.

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
        # get_attribute("value") reads the static HTML attribute, but this
        # field is a flatpickr input (confirmed real DOM: id
        # "whatsapp-product-date-range-picker", class
        # "...flatpickr-input active", readonly, no value="..." attribute
        # present at all even though the picker visibly shows a default
        # range) -- flatpickr sets the displayed text via the DOM .value
        # PROPERTY (input.value = ...), which never touches the HTML
        # attribute, so get_attribute("value") always returned None here.
        # input_value() reads the live property instead.
        el = self.h.wait_for_element_visible(self.DATE_RANGE_PICKER)
        return el.input_value()

    # ── Columns dropdown ─────────────────────────────────────────────────────

    def open_columns_dropdown(self):
        if self._is_visible(self.COLUMN_CHECKBOXES, timeout=1000):
            return
        self._js_click(self.COLUMNS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def uncheck_first_optional_column(self):
        """Returns the unchecked checkbox's `value` attribute on success,
        or None if there was nothing to uncheck."""
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
        Column visibility persists in sessionStorage across a plain
        navigate_to_report() (CONFIRMED live wire:snapshot:
        sessionStorageStatus.columnselect=true)."""
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
        el = self.h.wait_for_element_visible(self.PAGINATION_RESULTS_TEXT)
        return el.inner_text().strip()

    def click_next_page(self):
        # _js_click_first_visible, not _js_click -- see the identical fix
        # (and full rationale) in whatsapp_campaign_analytics_page.py's
        # click_next_page(): a real run showed this exact call timing out
        # with "element is not visible" despite a confirmed working Next
        # button, the signature of _js_click's `.first` locking onto a
        # hidden duplicate DOM match.
        self._js_click_first_visible(self.NEXT_PAGE_BTN, timeout=10000)
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
