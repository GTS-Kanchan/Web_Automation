from pages.common.base_page import BasePage


class WhatsAppMessageReportPage(BasePage):

    REPORT_URL = "/whatsapp/campaigns/msg-report"
    TABLE_NAME = "wa_messages"

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'Messages Report')]"
    BREADCRUMB = "xpath=//nav[@aria-label='Breadcrumb']"

    MODAL_CONTAINER = "#modal-container"

    # ── "View" popup internals (component 'whatsapp.campaign.message.view')
    # confirmed from a real captured DOM dump of the OPEN popup (message
    # id 129644 / "91720*****07" row) -- see module docstring update. Every
    # field row in the popup follows the identical "<label>: <value>"
    # pattern (a text-gray-500 label element immediately followed by a
    # sibling value element), grouped under a section <h4> heading, so
    # fields are located by (section heading text, label text) rather than
    # by index or class name, which is otherwise unstable (WireUI classes
    # like bg-green-100/text-green-800 vary per value/state).
    MODAL_TITLE = "xpath=//h3[normalize-space(.)='Message Details']"
    MODAL_CLOSE_BUTTON = "xpath=//button[contains(@*[name()='wire:click'],'closeModal')]"
    MODAL_CURRENT_STATUS = "xpath=//p[normalize-space(.)='Current Status']/preceding-sibling::h4[1]"
    MODAL_CONTACT_NUMBER = "xpath=//p[normalize-space(.)='Contact Number']/following-sibling::p[1]"
    MODAL_CATEGORY_TYPE = "xpath=//p[normalize-space(.)='Category Type']/following-sibling::span[1]"
    MODAL_MESSAGE_CONTENT = (
        "xpath=//h4[contains(normalize-space(.),'Message Content')]/parent::div"
        "//p[contains(@class,'whitespace-pre-wrap')]"
    )

    # Section headings used to scope the generic (label -> value) lookups
    # below -- several labels (e.g. "Status:", "Campaign Name:") repeat
    # across multiple sections with different meanings, so every lookup
    # must be scoped to its own section's heading, never done globally.
    MODAL_SECTION_BASIC_INFO = "Basic Information"
    MODAL_SECTION_WABA_INFO = "WABA Information"
    MODAL_SECTION_TEMPLATE_DETAILS = "Template Details"
    MODAL_SECTION_CAMPAIGN_INFO = "Campaign Information"
    MODAL_SECTION_TIMELINE = "Timeline"

    # ── Search ───────────────────────────────────────────────────────────────
    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search Mobile Number']"

    # ── Filters (slide-down panel, not a popover — see module docstring #1) ─
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')]"
    FILTER_STATUS = f"#{TABLE_NAME}-filter-status"
    FILTER_SOURCE = f"#{TABLE_NAME}-filter-source"
    FILTER_SUB_SOURCE = f"#{TABLE_NAME}-filter-sub-_source"
    FILTER_CREATED_FROM_WRAPPER = f"#{TABLE_NAME}-filter-created_from-wrapper"
    FILTER_CREATED_TO_WRAPPER = f"#{TABLE_NAME}-filter-created_to-wrapper"
    CLEAR_ALL_FILTERS_BTN = (
        "xpath=//button[contains(@*[name()='x-on:click.prevent'],'resetAllFilters')] "
        "| //button[contains(normalize-space(.),'Clear')]"
    )

    # ── Export (plain anchor, no bulk dropdown — see module docstring #4) ───
    EXPORT_CSV_LINK = (
        "xpath=//a[contains(@href,'/whatsapp/messages/export') and contains(normalize-space(.),'Export CSV')]"
    )

    # ── Sorting (8 sortable columns) ──────────────────────────────────────────
    SORT_TO_NUMBER_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('number')\")]"
    SORT_SOURCE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('source')\")]"
    SORT_SUB_SOURCE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('external_source')\")]"
    SORT_TEMPLATE_CATEGORY_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('template_category')\")]"
    SORT_CREATED_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('created_at')\")]"
    SORT_SUBMITTED_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('sent_at')\")]"
    SORT_DELIVERED_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('delivered_at')\")]"
    SORT_READ_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('read_at')\")]"
    SORT_FAILED_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('failed_at')\")]"
    CLEAR_ALL_SORTS_BTN = "xpath=//button[contains(@*[name()='wire:click'],'clearSorts')]"
    APPLIED_SORT_PILL = f"xpath=//span[contains(@*[name()='wire:key'],'{TABLE_NAME}-sorting-pill-')]"

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
        "xpath=//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no items found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no record') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no data') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no result') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'not found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'nothing found')]"
    )

    # ── Row action: View only (opens shared modal; internal content
    # UNCONFIRMED — see module docstring caveat #8) ─────────────────────────
    VIEW_ICON_IN_ROW = "xpath=.//*[contains(@data-tooltip-target,'tooltip-view-')]"

    # ── Pagination ───────────────────────────────────────────────────────────
    PAGINATION_RESULTS_TEXT = ".paged-pagination-results"
    NEXT_PAGE_BTN = f"xpath=//button[contains(@*[name()='wire:click'],\"nextPage('{TABLE_NAME}Page')\")]"
    # INFERRED from package convention — see module docstring caveat #9.
    PREV_PAGE_BTN = f"xpath=//button[contains(@*[name()='wire:click'],\"previousPage('{TABLE_NAME}Page')\")]"

    # ── User menu / logout (global header, confirmed identical to every
    # other page in this app). ──────────────────────────────────────────────
    USER_MENU_BUTTON = "xpath=//button[contains(@class,'rounded-full') and .//img]"
    LOGOUT_LINK = "xpath=//a[@title='Log out']"

    # ── Navigation / page state ─────────────────────────────────────────────

    def navigate(self):
        self.open(self.REPORT_URL)
        self.page.wait_for_timeout(2000)
        return self

    navigate_to_report = navigate

    def is_message_report_page(self):
        url = self.get_current_url()
        return "/whatsapp/campaigns/msg-report" in url and "login" not in url.lower()

    def get_page_title_text(self):
        el = self.h.wait_for_element_visible(self.PAGE_TITLE)
        return el.inner_text().strip()

    def get_breadcrumb_text(self):
        el = self.h.wait_for_element_visible(self.BREADCRUMB)
        return el.inner_text().strip()

    def wait_for_table_load(self, timeout=15000):
        self.page.locator(self.TABLE).wait_for(state="attached", timeout=timeout)
        self.page.wait_for_timeout(1000)

    def _is_visible(self, locator, timeout=1000):
        try:
            loc = self.page.locator(locator)
            for i in range(loc.count()):
                if loc.nth(i).is_visible():
                    return True
            return False
        except Exception:
            return False

    def _set_input_value(self, locator_or_element, value, event="input"):
        el = locator_or_element if hasattr(locator_or_element, "evaluate") else self.page.locator(locator_or_element).first
        el.evaluate(
            "(elm, args) => { elm.value = args[0];"
            "elm.dispatchEvent(new Event(args[1], {bubbles: true})); }",
            [value, event]
        )

    # ── Search ───────────────────────────────────────────────────────────────

    def _wait_for_search_to_settle(self, timeout_ms=8000):
        end_time = self.page.evaluate("() => Date.now()") + timeout_ms
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
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        self._set_input_value(box, value, "input")
        box.evaluate("el => el.dispatchEvent(new Event('change', {bubbles: true}))")
        self.page.wait_for_timeout(500)
        self._wait_for_search_to_settle()
        self.page.wait_for_timeout(300)

    def clear_search(self):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        self._set_input_value(box, "", "input")
        box.evaluate("el => el.dispatchEvent(new Event('change', {bubbles: true}))")
        self.page.wait_for_timeout(500)
        self._wait_for_search_to_settle()
        self.page.wait_for_timeout(300)

    # ── Table / rows ─────────────────────────────────────────────────────────

    def has_records(self):
        return self.is_element_present(self.TABLE_ROWS, timeout=5000) and self.get_row_count() > 0

    @staticmethod
    def _is_empty_state_row(tds):
        return tds.count() == 1 and tds.nth(0).get_attribute("colspan")

    def has_no_records_message(self):
        if self.is_element_present(self.NO_RECORDS_MSG, timeout=3000):
            return True
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            if rows.count() == 1:
                tds = rows.nth(0).locator("td")
                if self._is_empty_state_row(tds):
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
                if self._is_empty_state_row(tds):
                    continue
                if any(t.strip() for t in tds.all_inner_texts()):
                    count += 1
            return count
        except Exception:
            return 0

    def get_visible_column_headers(self):
        return self._get_headers_safe(self.TABLE_HEADERS)

    def get_column_values(self, header_substring):
        """Finds the column index dynamically by matching header text
        (case-insensitive substring), rather than a hardcoded index dict —
        this table has 16-18 possibly-toggled columns with no leading
        bulk-checkbox <th>, so headers align 1:1 with <td> cells and a
        dynamic lookup is safer than a fixed mapping tied to one specific
        column-selection state."""
        headers = self.get_visible_column_headers()
        idx = None
        for i, h in enumerate(headers):
            if header_substring.lower() in h.lower():
                idx = i
                break
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

    # ── Sorting ──────────────────────────────────────────────────────────────

    def sort_by_to_number(self):
        self._js_click(self.SORT_TO_NUMBER_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_source(self):
        self._js_click(self.SORT_SOURCE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_sub_source(self):
        self._js_click(self.SORT_SUB_SOURCE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_template_category(self):
        self._js_click(self.SORT_TEMPLATE_CATEGORY_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_created_at(self):
        self._js_click(self.SORT_CREATED_AT_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_submitted_at(self):
        self._js_click(self.SORT_SUBMITTED_AT_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_delivered_at(self):
        self._js_click(self.SORT_DELIVERED_AT_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_read_at(self):
        self._js_click(self.SORT_READ_AT_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_failed_at(self):
        self._js_click(self.SORT_FAILED_AT_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def get_applied_sort_pill_text(self):
        if self.is_element_present(self.APPLIED_SORT_PILL, timeout=3000):
            return self.h.wait_for_element_visible(self.APPLIED_SORT_PILL).inner_text().strip()
        return None

    def clear_all_sorts(self):
        self._js_click(self.CLEAR_ALL_SORTS_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    # ── Filters (slide-down panel) ───────────────────────────────────────────

    def open_filters_panel(self):
        if self._is_visible(self.FILTER_STATUS, timeout=1000):
            return
        self._js_click(self.FILTERS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def set_status_filter(self, value):
        """value: '' | 'pending' | 'sent' | 'delivered' | 'read' | 'failed' | 'rejected'"""
        self.open_filters_panel()
        self.h.wait_for_element_visible(self.FILTER_STATUS)
        self.h.select_option(self.FILTER_STATUS, value=value)
        self.page.wait_for_timeout(1200)

    def set_source_filter(self, value):
        """value: '' | 'u' (Campaign) | 'a' (API) | 'f' (Flow)"""
        self.open_filters_panel()
        self.h.wait_for_element_visible(self.FILTER_SOURCE)
        self.h.select_option(self.FILTER_SOURCE, value=value)
        self.page.wait_for_timeout(1200)

    def _date_input_in_wrapper(self, wrapper_locator):
        wrapper = self.h.wait_for_element_visible(wrapper_locator)
        return wrapper.locator("input[type='date']").first

    def _time_select_in_wrapper(self, wrapper_locator):
        wrapper = self.h.wait_for_element_visible(wrapper_locator)
        return wrapper.locator("select").first

    def set_created_from_filter(self, date_value, time_value=None):
        """date_input/time_select have NO stable ids of their own — located
        relative to the confirmed stable wrapper id instead (see module
        docstring caveat #2)."""
        self.open_filters_panel()
        date_el = self._date_input_in_wrapper(self.FILTER_CREATED_FROM_WRAPPER)
        self._set_input_value(date_el, date_value, "input")
        self.page.wait_for_timeout(300)
        if time_value:
            time_el = self._time_select_in_wrapper(self.FILTER_CREATED_FROM_WRAPPER)
            time_el.select_option(value=time_value)
        else:
            date_el.evaluate("el => el.dispatchEvent(new Event('change', {bubbles: true}))")
        self.page.wait_for_timeout(1200)

    def set_created_to_filter(self, date_value, time_value=None):
        self.open_filters_panel()
        date_el = self._date_input_in_wrapper(self.FILTER_CREATED_TO_WRAPPER)
        self._set_input_value(date_el, date_value, "input")
        self.page.wait_for_timeout(300)
        if time_value:
            time_el = self._time_select_in_wrapper(self.FILTER_CREATED_TO_WRAPPER)
            time_el.select_option(value=time_value)
        else:
            date_el.evaluate("el => el.dispatchEvent(new Event('change', {bubbles: true}))")
        self.page.wait_for_timeout(1200)

    def set_date_range_filter(self, from_date, to_date, from_time=None, to_time=None):
        self.set_created_from_filter(from_date, from_time)
        self.set_created_to_filter(to_date, to_time)

    def get_filter_date_values(self):
        # input_value(), not get_attribute("value") -- these fields are set
        # via _set_input_value()'s elm.value = ... (a live DOM PROPERTY
        # assignment), which never touches the static HTML value attribute.
        # Confirmed by a real run of test_TC004_date_filter_valid_range:
        # get_attribute("value") returned None right after
        # set_date_range_filter() set a real date. Same proven fix already
        # used on the WhatsApp Incoming Messages page and the RCS Opt-out
        # page's get_filter_values().
        self.open_filters_panel()
        from_el = self._date_input_in_wrapper(self.FILTER_CREATED_FROM_WRAPPER)
        to_el = self._date_input_in_wrapper(self.FILTER_CREATED_TO_WRAPPER)
        return from_el.input_value(), to_el.input_value()

    def clear_all_filters(self):
        if self.is_element_present(self.CLEAR_ALL_FILTERS_BTN, timeout=3000):
            self._js_click(self.CLEAR_ALL_FILTERS_BTN, timeout=5000)
            self.page.wait_for_timeout(1200)

    # ── Export ───────────────────────────────────────────────────────────────

    def get_export_csv_href(self):
        el = self.h.wait_for_element_visible(self.EXPORT_CSV_LINK)
        return el.get_attribute("href")

    # ── Columns dropdown ─────────────────────────────────────────────────────

    def open_columns_dropdown(self):
        if self._is_visible(self.COLUMN_CHECKBOXES, timeout=1000):
            return
        self._js_click(self.COLUMNS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def toggle_column(self, value):
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

    # ── Row action: View ─────────────────────────────────────────────────────

    def click_view_on_first_row(self):
        row = self.get_first_data_row()
        if row is None:
            return False
        try:
            btn = row.locator(self.VIEW_ICON_IN_ROW).first
            if btn.count() == 0:
                return False
        except Exception:
            return False
        btn.scroll_into_view_if_needed()
        btn.click(force=True)
        self.page.wait_for_timeout(1500)
        return True

    def is_modal_open(self):
        try:
            return self.page.locator(self.MODAL_CONTAINER).first.is_visible()
        except Exception:
            return False

    def is_message_view_popup_open(self):
        return self.is_element_present(self.MODAL_TITLE, timeout=5000)

    def close_message_view_popup(self):
        self._js_click(self.MODAL_CLOSE_BUTTON, timeout=5000)
        self.page.wait_for_timeout(500)

    def get_modal_current_status(self):
        el = self.h.wait_for_element_visible(self.MODAL_CURRENT_STATUS, timeout=8000)
        return el.inner_text().strip()

    def get_modal_contact_number(self):
        el = self.h.wait_for_element_visible(self.MODAL_CONTACT_NUMBER, timeout=8000)
        return el.inner_text().strip()

    def get_modal_category_type(self):
        el = self.h.wait_for_element_visible(self.MODAL_CATEGORY_TYPE, timeout=8000)
        return el.inner_text().strip()

    def get_modal_message_content(self):
        el = self.h.wait_for_element_visible(self.MODAL_MESSAGE_CONTENT, timeout=8000)
        return el.inner_text().strip()

    def _modal_section_field(self, section_heading, label, timeout=8000):
        # Generic (section heading, "label:") -> value lookup shared by
        # every multi-field section of the popup (Basic Information, WABA
        # Information, Template Details, Campaign Information).
        xpath = (
            f"xpath=//h4[contains(normalize-space(.),'{section_heading}')]/parent::div"
            f"//span[normalize-space(text())='{label}:']/following-sibling::span[1]"
        )
        el = self.h.wait_for_element_visible(xpath, timeout=timeout)
        return el.inner_text().strip()

    def get_modal_basic_info_field(self, label):
        return self._modal_section_field(self.MODAL_SECTION_BASIC_INFO, label)

    def get_modal_waba_field(self, label):
        return self._modal_section_field(self.MODAL_SECTION_WABA_INFO, label)

    def get_modal_template_field(self, label):
        return self._modal_section_field(self.MODAL_SECTION_TEMPLATE_DETAILS, label)

    def get_modal_campaign_info_field(self, label):
        return self._modal_section_field(self.MODAL_SECTION_CAMPAIGN_INFO, label)

    def get_modal_timeline_field(self, label, timeout=3000):
        # Timeline rows (Created/Sent/Delivered/Read) are EACH individually
        # conditional on the message having reached that status -- confirmed
        # in the captured DOM via per-row Blade if-blocks. Returns None when
        # this popup doesn't render that row (rather than raising), so
        # callers can treat "no such timestamp yet" as a real, expected
        # outcome instead of a locator failure.
        xpath = (
            f"xpath=//h4[contains(normalize-space(.),'{self.MODAL_SECTION_TIMELINE}')]/parent::div"
            f"//span[normalize-space(text())='{label}:']/following-sibling::span[1]"
        )
        if not self.is_element_present(xpath, timeout=timeout):
            return None
        return self.page.locator(xpath).first.inner_text().strip()

    def has_button_click_section(self):
        return self.is_element_present(
            "xpath=//h4[contains(normalize-space(.),'Button Click')]", timeout=3000
        )

    def has_error_section(self):
        return self.is_element_present(
            "xpath=//h4[contains(normalize-space(.),'Error')]", timeout=3000
        )

    # ── Pagination ───────────────────────────────────────────────────────────

    def get_pagination_results_text(self):
        el = self.h.wait_for_element_visible(self.PAGINATION_RESULTS_TEXT)
        return el.inner_text().strip()

    def click_next_page(self):
        self._js_click(self.NEXT_PAGE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_prev_page_enabled(self):
        try:
            return self.page.locator(self.PREV_PAGE_BTN).first.count() > 0
        except Exception:
            return False

    def click_prev_page(self):
        self._js_click(self.PREV_PAGE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    # ── Logout ───────────────────────────────────────────────────────────────

    def logout(self):
        self._js_click(self.USER_MENU_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)
        self._js_click(self.LOGOUT_LINK, timeout=10000)
        self.page.wait_for_timeout(1500)
