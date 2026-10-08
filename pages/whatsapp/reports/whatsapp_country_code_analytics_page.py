import os
import time

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR


class WhatsappCountryCodeAnalyticsPage(BasePage):

    REPORT_URL = "/whatsapp/analytics/country-code"
    TABLE_NAME = "whatsapp_country_code_report"

    COLUMN_INDEX = {
        "duration": 0, "product": 1, "waba_number": 2, "country_code": 3,
        "total": 4, "sent": 5, "delivered": 6, "read": 7, "failed": 8,
        "rejected": 9, "dlr_awaited": 10, "interactions": 11,
        "quick_reply_total": 12, "quick_reply_unique": 13,
        "cta_total_clicks": 14, "cta_unique_clicks": 15, "total_charges": 16,
    }

    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'Country Code Analytics')]"

    DATE_RANGE_PICKER = "#whatsapp-country-code-date-range-picker"
    REPORT_TYPE_SELECT = "#whatsapp-country-code-report-type-select"
    GROUP_BY_LABEL = "#whatsapp-country-code-dimension-multiselect-label"
    GROUP_BY_BUTTON = (
        "xpath=//span[@id='whatsapp-country-code-dimension-multiselect-label']/ancestor::button[1]"
    )
    GROUP_BY_DROPDOWN = "#whatsapp-country-code-dimension-multiselect-dropdown"

    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search by Country Code']"

    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')]"
    FILTER_PRODUCT_SELECT = f"#{TABLE_NAME}-filter-product"
    FILTER_DEPARTMENT_INPUT = ".async-select-filter-department input[placeholder='Search Department']"
    FILTER_USER_INPUT = ".async-select-filter-user input[placeholder='Search User']"

    COLUMNS_BUTTON = "xpath=//button[contains(normalize-space(.),'Columns')]"
    COLUMN_CHECKBOXES = (
        f"xpath=//div[contains(@*[name()='wire:key'],'{TABLE_NAME}-columnSelect-') and "
        f"not(contains(@*[name()='wire:key'],'columnSelect-selectAll'))]//input[@type='checkbox']"
    )

    EXPORT_CSV_BUTTON = "xpath=//button[contains(normalize-space(.),'Export CSV')]"

    TABLE = f"#table-{TABLE_NAME}"
    TABLE_HEADERS = f"#table-{TABLE_NAME} thead th"
    TABLE_ROWS = f"#table-{TABLE_NAME} tbody tr"
    DURATION_SORT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('duration')\")]"
    NO_RECORDS_MSG = (
        "xpath=//*[contains(text(),'No records') or contains(text(),'No data') "
        "or contains(text(),'No results')]"
    )

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
        return "/whatsapp/analytics/country-code" in url and "login" not in url.lower()

    def get_page_title_text(self):
        el = self.h.wait_for_element_visible(self.PAGE_TITLE)
        return el.inner_text().strip()

    def are_filters_visible(self):
        return (self.is_element_present(self.DATE_RANGE_PICKER, timeout=5000)
                and self.is_element_present(self.REPORT_TYPE_SELECT, timeout=5000)
                and self.is_element_present(self.GROUP_BY_LABEL, timeout=5000))

    def _is_visible(self, locator, timeout=1000):
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
        # Livewire re-render race this guards against.
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
        for _ in range(5):
            if self._is_visible(self.FILTER_PRODUCT_SELECT, timeout=1000):
                return
            self._js_click(self.FILTERS_BUTTON, timeout=5000)
            self.page.wait_for_timeout(1000)

    def _select_first_async_option(self, container_css):
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

    def select_product_filter(self, value):
        self.open_filters_popover()
        self.h.select_option(self.FILTER_PRODUCT_SELECT, value=value)
        self.page.wait_for_timeout(1500)

    def get_product_filter_value(self):
        return self.h.wait_for_element_visible(self.FILTER_PRODUCT_SELECT).input_value()

    def select_report_type(self, value):
        self.h.select_option(self.REPORT_TYPE_SELECT, value=value)
        self.page.wait_for_timeout(1500)

    def get_report_type(self):
        return self.h.wait_for_element_visible(self.REPORT_TYPE_SELECT).input_value()

    def open_group_by_dropdown(self):
        for _ in range(5):
            if self._is_visible(self.GROUP_BY_DROPDOWN, timeout=1000):
                return
            self._js_click(self.GROUP_BY_BUTTON, timeout=5000)
            self.page.wait_for_timeout(1000)

    def toggle_group_by_dimension(self, dim):
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

    def open_date_range_picker(self):
        for _ in range(5):
            self._js_click(self.DATE_RANGE_PICKER, timeout=5000)
            self.page.wait_for_timeout(1000)
            if self._is_visible(self._DAY_CELLS_CSS, timeout=1000):
                return

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
        # get_attribute("value") reads the static HTML attribute, but this
        # field is a flatpickr input (confirmed real DOM on the sibling
        # Usage Analytics page: class "...flatpickr-input active", readonly,
        # no value="..." attribute present at all even though the picker
        # visibly shows a default range) -- flatpickr sets the displayed
        # text via the DOM .value PROPERTY (input.value = ...), which never
        # touches the HTML attribute, so get_attribute("value") always
        # returned None here. input_value() reads the live property instead.
        el = self.h.wait_for_element_visible(self.DATE_RANGE_PICKER)
        return el.input_value()

    def open_columns_dropdown(self):
        if self._is_visible(self.COLUMN_CHECKBOXES, timeout=1000):
            return
        self._js_click(self.COLUMNS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def uncheck_first_optional_column(self):
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

    def get_column_toggles(self):
        """Return list of (label_text, checkbox_locator, is_checked) for
        every checkbox in the Columns panel, scoped to this table's own
        `{TABLE_NAME}-columnSelect-*` wire:key wrappers (so the select-all
        toggle and any other page's checkboxes are never included).

        Label text is resolved the same way as the other report pages'
        column-toggle readers: `for=` attribute on a sibling <label>, an
        enclosing <label>, a following sibling span/label, and finally
        the checkbox's own `value` attribute as a last resort -- never
        assumes a checkbox has no usable label.
        """
        self.open_columns_dropdown()
        result = []
        try:
            checkboxes = self.page.locator(self.COLUMN_CHECKBOXES)
            count = checkboxes.count()
        except Exception:
            return result
        for i in range(count):
            cb = checkboxes.nth(i)
            label_text = ""
            try:
                cb_id = cb.get_attribute("id") or ""
                if cb_id:
                    lbl = self.page.locator(f"label[for='{cb_id}']").first
                    if lbl.count() > 0:
                        label_text = lbl.inner_text().strip()
            except Exception:
                pass
            if not label_text:
                try:
                    lbl = cb.locator("xpath=ancestor::label[1]").first
                    label_text = lbl.inner_text().strip()
                except Exception:
                    pass
            if not label_text:
                try:
                    lbl = cb.locator(
                        "xpath=following-sibling::span[1] | following-sibling::label[1]"
                    ).first
                    label_text = lbl.inner_text().strip()
                except Exception:
                    pass
            if not label_text:
                val = cb.get_attribute("value") or ""
                label_text = val.replace("_", " ").replace("-", " ").title()
            try:
                is_checked = cb.is_checked()
            except Exception:
                is_checked = False
            result.append((label_text, cb, is_checked))
        return result

    def ensure_columns_checked(self, labels):
        """Make sure each column named in `labels` (case-insensitive,
        substring match against the Columns panel's label text) is
        checked, checking it if it is currently unchecked.

        This exists so report-content assertions don't depend on
        whatever column-visibility state another test left behind in
        this account's session (sessionStorage-backed, so it survives a
        plain navigate_to_report() -- see check_column()). Returns the
        list of requested labels that could not be found/checked, so
        callers can surface a clear failure instead of asserting blind.

        A label with no matching checkbox at all (a mandatory/always-on
        column with no toggle) is NOT reported as not-found -- only a
        checkbox that was found unchecked but could not be clicked is.
        """
        wanted = [(label, label.strip().lower()) for label in labels]
        not_found = []
        for original_label, needle in wanted:
            toggles = self.get_column_toggles()
            match = None
            for label_text, cb, is_checked in toggles:
                if needle in label_text.strip().lower():
                    match = (cb, is_checked)
                    break
            if match is None:
                # No checkbox for this label at all -- it's either a
                # mandatory/always-visible column (no toggle exists for
                # it) or a naming mismatch. Either way this method's job
                # is only to make sure TOGGLEABLE columns are turned on;
                # whether the column actually appears in the table is
                # for the caller's own header assertion to decide, so
                # this is not treated as a failure here.
                continue
            cb, is_checked = match
            if not is_checked:
                try:
                    cb.scroll_into_view_if_needed()
                    cb.click(force=True)
                    self.page.wait_for_timeout(800)
                except Exception:
                    not_found.append(original_label)
        return not_found

    def click_export_csv(self, timeout_ms=30000):
        """Clicks Export CSV, capturing the resulting download via
        page.expect_download() -- previously just clicked and slept,
        never actually capturing a file, which silently produced no
        downloaded export for every WhatsApp analytics report (confirmed
        via a real pytest run: all 7 export-side date-verification tests
        skipped with "export did not produce a downloaded file").

        Returns {"elapsed_s", "file_path", "file_size"} on success, or
        None on failure (timeout / no download triggered) -- matches the
        RCS analytics family's confirmed-working click_export_csv() contract.
        """
        try:
            btn = self.h.wait_for_element_clickable(self.EXPORT_CSV_BUTTON, timeout=10000)
            btn.scroll_into_view_if_needed()
            start = time.time()
            with self.page.expect_download(timeout=timeout_ms) as dl_info:
                self._js_click(self.EXPORT_CSV_BUTTON, timeout=10000)
            download = dl_info.value
            filename = download.suggested_filename or "whatsapp_country_code_report_export.csv"
            dest = os.path.join(DOWNLOAD_DIR, filename)
            download.save_as(dest)
            return {
                "elapsed_s": time.time() - start,
                "file_path": dest,
                "file_size": os.path.getsize(dest),
            }
        except Exception:
            return None

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

    def get_page_load_time_ms(self):
        try:
            return self.page.evaluate(
                "() => window.performance.timing.loadEventEnd - "
                "window.performance.timing.navigationStart"
            )
        except Exception:
            return None
