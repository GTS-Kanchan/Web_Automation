from pages.common.base_page import BasePage


class WhatsAppCampaignPage(BasePage):
    """Page object for the WhatsApp Campaign listing page
    (/whatsapp/campaigns) -- the "Campaigns" tab of the WhatsApp channel.

    Built entirely from a genuine live DOM dump of this page (Livewire
    component 'whatsapp.campaign.table', wire:id 'xyHpTvNNO09NvtnHF7d4',
    table name 'wa_campaigns'). Two caveats carried over from that capture,
    both documented rather than guessed around:

    1. NO DATE FILTER IS PRESENT. The manual QA checklist (TC009/TC010)
       describes a "CreatedAt From / CreatedAt To" date filter, but the
       captured filter panel has exactly 5 fields -- department, user,
       status, type, sender_id (WABA number) -- matching the Livewire
       component's own `filterCount: 5` and `filterComponents` snapshot
       keys. No date-range control exists anywhere in the captured markup.
       Per this project's "never guess" rule, no locator is fabricated for
       it; TC009/TC010 are documented `@pytest.mark.skip`s instead.
    2. NO DEDICATED "CLEAR ALL FILTERS" BUTTON IS PRESENT (unlike the
       WhatsApp Messages Report page, which has one). `clear_all_filters()`
       here resets each real filter control individually instead of
       clicking a button that doesn't exist in this DOM.

    The Action column's two real controls are NOT the same thing:
      - the eye/"View" button dispatches an `openModal` event for a
        DIFFERENT Livewire component ('whatsapp.campaign.view') than the
        one used on the Messages Report page -- a quick-view popup for the
        campaign itself. Not covered by the current QA checklist, so no
        test asserts on its internal content.
      - the document/"Reports" icon is a plain anchor to
        `/whatsapp/campaigns/messages/<campaignId>` -- a full page navigation
        to the per-campaign "Campaign Report" page (QA checklist TC016 and
        the whole TC017-043 block describe THIS page, not the modal). That
        page's own DOM has not been captured, so its automation is a
        separate suite pending that evidence.
    """

    REPORT_URL = "/whatsapp/campaigns"
    TABLE_NAME = "wa_campaigns"

    # ── Page header / breadcrumb ─────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'WhatsApp Campaigns')]"
    BREADCRUMB = "xpath=//nav[@aria-label='Breadcrumb']"

    # ── Top actions ──────────────────────────────────────────────────────────
    REFRESH_LINK = "xpath=//a[contains(normalize-space(.),'Refresh')]"
    CREATE_CAMPAIGN_LINK = "xpath=//a[contains(normalize-space(.),'Create New Campaign')]"

    # ── Search (CONFIRMED placeholder is "Search Campaign Name" -- the QA
    # checklist's own TC002 description, "enter User number or Template
    # category", does not match the real placeholder text; same kind of
    # checklist/DOM mismatch seen on other pages in this project) ──────────
    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search Campaign Name']"

    # ── Filters (slide-down panel) -- 5 real fields only, see class
    # docstring caveat #1 ────────────────────────────────────────────────────
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')]"
    FILTER_DEPARTMENT = f"#{TABLE_NAME}-filter-department"
    FILTER_USER = f"#{TABLE_NAME}-filter-user"
    FILTER_TYPE = f"#{TABLE_NAME}-filter-type"
    FILTER_STATUS_WRAPPER = f"#{TABLE_NAME}-filter-status-wrapper"
    FILTER_WABA_NUMBER_WRAPPER = f"#{TABLE_NAME}-filter-sender_id-wrapper"

    # ── Export (a confirm-modal flow, not a bulk-action dropdown -- the QA
    # checklist calls this "Bulk Action" but the only real control is a
    # single "Export to XLSX" button that opens a Yes/No confirm dialog) ───
    EXPORT_BUTTON = "xpath=//button[contains(normalize-space(.),'Export to XLSX')]"
    EXPORT_CONFIRM_TEXT = (
        "xpath=//p[contains(normalize-space(.),'Are you sure you want to export')]"
    )
    EXPORT_CONFIRM_YES_BTN = "xpath=//button[contains(@*[name()='wire:click'],'exportAll')]"
    EXPORT_CONFIRM_NO_BTN = "xpath=//button[normalize-space(.)='No']"

    # ── Columns dropdown ─────────────────────────────────────────────────────
    COLUMNS_BUTTON = "xpath=//button[contains(normalize-space(.),'Columns')]"
    COLUMN_CHECKBOXES = (
        f"xpath=//div[contains(@*[name()='wire:key'],'{TABLE_NAME}-columnSelect-') and "
        f"not(contains(@*[name()='wire:key'],'columnSelect-selectAll'))]//input[@type='checkbox']"
    )
    SELECT_ALL_COLUMNS_CHECKBOX = (
        f"xpath=//div[contains(@*[name()='wire:key'],'{TABLE_NAME}-columnSelect-selectAll-')]//input[@type='checkbox']"
    )

    # ── Sorting (6 sortable columns; Action/Total Messages/Scheduled at are
    # CONFIRMED NOT sortable -- plain <span> headers, no wire:click button) ──
    SORT_CAMPAIGN_NAME_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('name')\")]"
    SORT_TYPE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('contact_type')\")]"
    SORT_TEMPLATE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('template_id')\")]"
    SORT_WABA_NUMBER_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('sender_id')\")]"
    SORT_STATUS_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('status_id')\")]"
    SORT_CREATED_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('created_at')\")]"
    CLEAR_ALL_SORTS_BTN = "xpath=//button[contains(@*[name()='wire:click.prevent'],'clearSorts')]"
    APPLIED_SORT_PILL = f"xpath=//span[contains(@*[name()='wire:key'],'{TABLE_NAME}-sorting-pill-')]"

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

    # ── Row actions (see class docstring for the View-vs-Reports distinction) ─
    VIEW_MODAL_ICON_IN_ROW = "xpath=.//*[contains(@data-tooltip-target,'tooltip-view-')]"
    REPORTS_LINK_IN_ROW = "xpath=.//*[contains(@data-tooltip-target,'tooltip-reports-')]"

    # ── Pagination ───────────────────────────────────────────────────────────
    PAGINATION_RESULTS_TEXT = ".paged-pagination-results"
    NEXT_PAGE_BTN = f"xpath=//button[contains(@*[name()='wire:click'],\"nextPage('{TABLE_NAME}Page')\")]"
    # INFERRED from the identical, already-confirmed pagination package
    # convention used on the Messages Report page -- not a direct DOM
    # observation, since every capture of this page so far has had only
    # one page's worth of "Previous" state (disabled).
    PREV_PAGE_BTN = f"xpath=//button[contains(@*[name()='wire:click'],\"previousPage('{TABLE_NAME}Page')\")]"

    # ── User menu / logout (global header, confirmed identical to every
    # other page in this app) ───────────────────────────────────────────────
    USER_MENU_BUTTON = "xpath=//button[contains(@class,'rounded-full') and .//img]"
    LOGOUT_LINK = "xpath=//a[@title='Log out']"

    # ── Navigation / page state ──────────────────────────────────────────────

    def navigate(self):
        self.open(self.REPORT_URL)
        self.page.wait_for_timeout(2000)
        return self

    navigate_to_report = navigate

    def is_campaign_page(self):
        url = self.get_current_url()
        return "/whatsapp/campaigns" in url and "login" not in url.lower() and "msg-report" not in url

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

    # ── Top actions ──────────────────────────────────────────────────────────

    def click_refresh(self):
        self._js_click(self.REFRESH_LINK, timeout=10000)
        self.page.wait_for_timeout(1500)

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

    def sort_by_campaign_name(self):
        self._js_click(self.SORT_CAMPAIGN_NAME_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_type(self):
        self._js_click(self.SORT_TYPE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_template(self):
        self._js_click(self.SORT_TEMPLATE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_waba_number(self):
        self._js_click(self.SORT_WABA_NUMBER_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_status(self):
        self._js_click(self.SORT_STATUS_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_created_at(self):
        self._js_click(self.SORT_CREATED_AT_BTN, timeout=10000)
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
        if self._is_visible(self.FILTER_DEPARTMENT, timeout=1000):
            return
        self._js_click(self.FILTERS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def set_department_filter(self, value):
        """value: '' | 'Admin' | 'Eshwar DEPT' | 'TESTQA_TEST_01' | 'User'
        (options CONFIRMED in the live <select>)."""
        self.open_filters_panel()
        self.h.wait_for_element_visible(self.FILTER_DEPARTMENT)
        self.h.select_option(self.FILTER_DEPARTMENT, value=value)
        self.page.wait_for_timeout(1200)

    def set_user_filter(self, value):
        """value: '' | 'Eshwar Chavan' | 'Karthik Reddy' | 'Om Patel' |
        'Test Account23' (options CONFIRMED in the live <select>)."""
        self.open_filters_panel()
        self.h.wait_for_element_visible(self.FILTER_USER)
        self.h.select_option(self.FILTER_USER, value=value)
        self.page.wait_for_timeout(1200)

    def set_type_filter(self, value):
        """value: '' | 'flow_numbers' (Flow) | 'campaign' (Campaign)."""
        self.open_filters_panel()
        self.h.wait_for_element_visible(self.FILTER_TYPE)
        self.h.select_option(self.FILTER_TYPE, value=value)
        self.page.wait_for_timeout(1200)

    def _open_custom_multiselect(self, wrapper_locator):
        """The Status and WABA Number filters are NOT native <select>s --
        each is a custom Alpine.js checkbox-list dropdown scoped to its own
        wrapper id. Opens it (idempotent) and returns the wrapper Locator."""
        wrapper = self.h.wait_for_element_visible(wrapper_locator)
        toggle_btn = wrapper.locator("button[type='button']").first
        options_visible = wrapper.locator("input[type='checkbox']").first.is_visible() if wrapper.locator("input[type='checkbox']").count() else False
        if not options_visible:
            toggle_btn.click(force=True)
            self.page.wait_for_timeout(400)
        return wrapper

    def toggle_status_filter_option(self, status_name):
        """status_name: one of the CONFIRMED live options -- 'Cancelled',
        'Draft', 'Failed', 'Paused', 'Pending', 'Scheduled', 'Sending',
        'Sent'."""
        wrapper = self._open_custom_multiselect(self.FILTER_STATUS_WRAPPER)
        option = wrapper.locator(
            f"xpath=.//label[.//span[normalize-space(text())='{status_name}']]//input[@type='checkbox']"
        ).first
        option.click(force=True)
        self.page.wait_for_timeout(1200)

    def toggle_waba_number_filter_option(self, waba_number):
        """waba_number: one of the CONFIRMED live options, e.g.
        '919691926438'."""
        wrapper = self._open_custom_multiselect(self.FILTER_WABA_NUMBER_WRAPPER)
        option = wrapper.locator(
            f"xpath=.//label[.//span[normalize-space(text())='{waba_number}']]//input[@type='checkbox']"
        ).first
        option.click(force=True)
        self.page.wait_for_timeout(1200)

    def clear_all_filters(self):
        """No dedicated "Clear all filters" button exists on this page
        (see class docstring caveat #2) -- resets each real control to its
        default/empty state individually instead."""
        self.open_filters_panel()
        try:
            self.h.select_option(self.FILTER_DEPARTMENT, value="")
        except Exception:
            pass
        try:
            self.h.select_option(self.FILTER_USER, value="")
        except Exception:
            pass
        try:
            self.h.select_option(self.FILTER_TYPE, value="")
        except Exception:
            pass
        self.page.wait_for_timeout(1200)

    # ── Export ───────────────────────────────────────────────────────────────

    def click_export(self):
        self._js_click(self.EXPORT_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def is_export_confirm_open(self):
        return self.is_element_present(self.EXPORT_CONFIRM_TEXT, timeout=5000)

    def confirm_export(self):
        self._js_click(self.EXPORT_CONFIRM_YES_BTN, timeout=10000)
        self.page.wait_for_timeout(1000)

    def cancel_export(self):
        self._js_click(self.EXPORT_CONFIRM_NO_BTN, timeout=10000)
        self.page.wait_for_timeout(500)

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

    # ── Row actions ──────────────────────────────────────────────────────────

    def click_view_modal_on_first_row(self):
        row = self.get_first_data_row()
        if row is None:
            return False
        try:
            btn = row.locator(self.VIEW_MODAL_ICON_IN_ROW).first
            if btn.count() == 0:
                return False
        except Exception:
            return False
        btn.scroll_into_view_if_needed()
        btn.click(force=True)
        self.page.wait_for_timeout(1500)
        return True

    def click_reports_link_on_first_row(self):
        row = self.get_first_data_row()
        if row is None:
            return False
        try:
            link = row.locator(self.REPORTS_LINK_IN_ROW).first
            if link.count() == 0:
                return False
        except Exception:
            return False
        link.scroll_into_view_if_needed()
        with self.page.expect_navigation(timeout=15000):
            link.click(force=True)
        self.page.wait_for_timeout(1000)
        return True

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
