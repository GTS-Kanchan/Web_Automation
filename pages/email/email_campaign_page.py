import os
import time

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR


class EmailCampaignPage(BasePage):

    REPORT_URL = "/campaigns/email"
    CREATE_URL = "/campaigns/email/create"
    TABLE_NAME = "email_campaigns"

    # Confirmed column order for the DEFAULT (9-column) visible state only.
    COLUMN_INDEX = {"action": 0, "campaign_name": 1, "type": 2, "subject": 3,
                     "email_service": 4, "template": 5, "status": 6,
                     "scheduled_at": 7, "created_at": 8}

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'Email Campaigns')]"
    BREADCRUMB = "xpath=//nav[@aria-label='Breadcrumb']"

    # ── Top action buttons ───────────────────────────────────────────────────
    REFRESH_BTN = (
        "xpath=//a[contains(@href,'/campaigns/email') and not(contains(@href,'/create')) "
        "and contains(normalize-space(.),'Refresh')]"
    )
    CREATE_NEW_CAMPAIGN_BTN = (
        "xpath=//a[contains(@href,'/campaigns/email/create') and contains(normalize-space(.),'Create New Campaign')]"
    )
    MODAL_CONTAINER = "#modal-container"

    # ── Search ───────────────────────────────────────────────────────────────
    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search']"

    # ── Filters (slide-down layout, seven confirmed fields) ─────────────────
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')]"
    FILTER_DEPARTMENT = "#email_campaigns-filter-department"
    FILTER_USER = "#email_campaigns-filter-user"
    FILTER_SCHEDULED_FROM = "#email_campaigns-filter-scheduled_from"
    FILTER_SCHEDULED_TO = "#email_campaigns-filter-scheduled_to"
    FILTER_TYPE_SELECT = "#email_campaigns-filter-type"

    FILTER_STATUS_WRAPPER = "#email_campaigns-filter-status-wrapper"
    FILTER_SERVICE_WRAPPER = "#email_campaigns-filter-service-wrapper"

    # ── Sorting ──────────────────────────────────────────────────────────────
    SORT_CAMPAIGN_NAME_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('name')\")]"
    SORT_TYPE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('contact_type')\")]"
    SORT_EMAIL_SERVICE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('email_service_id')\")]"
    SORT_TEMPLATE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('template_id')\")]"
    SORT_STATUS_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('status_id')\")]"
    SORT_SCHEDULED_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('scheduled_at')\")]"
    SORT_CREATED_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('created_at')\")]"
    CLEAR_SORT_BTN = "xpath=//button[contains(@*[name()='wire:click'],'clearSort')]"
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

    # ── Row actions: View (modal) + Reports (link) ───────────────────────────
    VIEW_BTN_IN_ROW = "xpath=.//button[contains(@*[starts-with(name(),'wire:click')],\"'mail.campaign.view'\")]"
    REPORTS_LINK_IN_ROW = "xpath=.//a[contains(@href,'/campaigns/email/report/')]"

    # ── Export to XLSX (confirmation modal) ──────────────────────────────────
    EXPORT_XLSX_BTN = "xpath=//button[contains(normalize-space(.),'Export to XLSX')]"
    EXPORT_CONFIRM_MODAL_TITLE = "xpath=//h2[normalize-space()='Export']"
    EXPORT_CONFIRM_YES_BTN = "xpath=//button[@*[name()='wire:click']='exportAll']"
    EXPORT_CONFIRM_NO_BTN = "xpath=//button[contains(normalize-space(.),'No') and not(@*[name()='wire:click'])]"

    # ── Pagination ───────────────────────────────────────────────────────────
    PAGINATION_RESULTS_TEXT = ".paged-pagination-results"
    NEXT_PAGE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"nextPage('email_campaignsPage')\")]"

    # ── User menu / logout (global header, confirmed identical to every
    # other page in this app). ──────────────────────────────────────────────
    USER_MENU_BUTTON = "xpath=//button[contains(@class,'rounded-full') and .//img]"
    LOGOUT_LINK = "xpath=//a[@title='Log out']"

    # -------------------------------------------------------------------------
    # Init — registers a page-level download listener (same pattern as
    # rcs_download_center_page.py): every completed download gets saved
    # into DOWNLOAD_DIR and appended to self._downloaded_paths, which
    # wait_for_xlsx_download() below consumes -- replaces the Selenium
    # version's mtime-based folder polling.
    # -------------------------------------------------------------------------

    def __init__(self, page):
        super().__init__(page)
        self._downloaded_paths = []
        self.page.on("download", self._on_download)

    def _on_download(self, download):
        try:
            filename = download.suggested_filename or f"email_campaigns_export_{int(time.time() * 1000)}.xlsx"
            dest = os.path.join(DOWNLOAD_DIR, filename)
            download.save_as(dest)
            self._downloaded_paths.append(dest)
        except Exception:
            pass

    # ── Navigation / page state ─────────────────────────────────────────────

    def navigate(self):
        self.open(self.REPORT_URL)
        self.page.wait_for_timeout(2000)
        return self

    navigate_to_report = navigate

    def is_campaign_page(self):
        url = self.get_current_url()
        return "/campaigns/email" in url and "login" not in url.lower() and "/create" not in url

    def get_page_title_text(self):
        el = self.h.wait_for_element_visible(self.PAGE_TITLE)
        return el.inner_text().strip()

    def wait_for_table_load(self, timeout=15000):
        self.page.locator(self.TABLE).first.wait_for(state="attached", timeout=timeout)
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

    # ── Top action buttons ───────────────────────────────────────────────────

    def click_refresh(self):
        self._js_click(self.REFRESH_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def click_create_new_campaign(self):
        self._js_click(self.CREATE_NEW_CAMPAIGN_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_create_page(self):
        return "/campaigns/email/create" in self.get_current_url()

    # ── Search ───────────────────────────────────────────────────────────────

    def _wait_for_search_to_settle(self, timeout_ms=8000):
        last_state = None
        elapsed = 0
        interval = 600
        while elapsed < timeout_ms:
            current = self.get_row_count()
            no_msg = self.is_element_present(self.NO_RECORDS_MSG, timeout=500)
            state = (current, no_msg)
            if state == last_state:
                return
            last_state = state
            self.page.wait_for_timeout(interval)
            elapsed += interval

    def search(self, value):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.evaluate(
            "(elm, v) => { elm.value = v; "
            "elm.dispatchEvent(new Event('input', {bubbles: true})); "
            "elm.dispatchEvent(new Event('change', {bubbles: true})); }",
            value
        )
        self.page.wait_for_timeout(500)
        self._wait_for_search_to_settle()
        self.page.wait_for_timeout(300)

    def clear_search(self):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.evaluate(
            "(elm) => { elm.value = ''; "
            "elm.dispatchEvent(new Event('input', {bubbles: true})); "
            "elm.dispatchEvent(new Event('change', {bubbles: true})); }"
        )
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
                td_count = tds.count()
                if td_count == 0:
                    continue
                if self._is_empty_state_row(tds):
                    continue
                has_text = False
                for j in range(td_count):
                    if tds.nth(j).inner_text().strip():
                        has_text = True
                        break
                if has_text:
                    count += 1
            return count
        except Exception:
            return 0

    def get_visible_column_headers(self):
        return self._get_headers_safe(self.TABLE_HEADERS)

    def get_column_values(self, header_substring):
        """Dynamic header-index lookup (this table has togglable columns,
        so a fixed index dict is only safe for the default state) — finds
        the column index by matching header text at call-time, same
        pattern as whatsapp_message_report_page.py's get_column_values()."""
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

    def sort_by_campaign_name(self):
        self._js_click(self.SORT_CAMPAIGN_NAME_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_type(self):
        self._js_click(self.SORT_TYPE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_email_service(self):
        self._js_click(self.SORT_EMAIL_SERVICE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_template(self):
        self._js_click(self.SORT_TEMPLATE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_status(self):
        self._js_click(self.SORT_STATUS_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_scheduled_at(self):
        self._js_click(self.SORT_SCHEDULED_AT_BTN, timeout=10000)
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

    # ── Filters (slide-down) ─────────────────────────────────────────────────

    def open_filters_panel(self):
        if self._is_visible(self.FILTER_DEPARTMENT, timeout=1000):
            return
        self._js_click(self.FILTERS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def set_department_filter(self, value):
        self.open_filters_panel()
        el = self.h.wait_for_element_visible(self.FILTER_DEPARTMENT)
        el.evaluate(
            "(elm, v) => { elm.value = v; "
            "elm.dispatchEvent(new Event('input', {bubbles: true})); "
            "elm.dispatchEvent(new Event('change', {bubbles: true})); }",
            value
        )
        self.page.wait_for_timeout(1200)

    def set_user_filter(self, value):
        self.open_filters_panel()
        el = self.h.wait_for_element_visible(self.FILTER_USER)
        el.evaluate(
            "(elm, v) => { elm.value = v; "
            "elm.dispatchEvent(new Event('input', {bubbles: true})); "
            "elm.dispatchEvent(new Event('change', {bubbles: true})); }",
            value
        )
        self.page.wait_for_timeout(1200)

    def set_scheduled_date_range(self, from_date, to_date):
        self.open_filters_panel()
        from_el = self.h.wait_for_element_visible(self.FILTER_SCHEDULED_FROM)
        from_el.evaluate(
            "(elm, v) => { elm.value = v; "
            "elm.dispatchEvent(new Event('input', {bubbles: true})); "
            "elm.dispatchEvent(new Event('change', {bubbles: true})); }",
            from_date
        )
        self.page.wait_for_timeout(600)
        to_el = self.h.wait_for_element_visible(self.FILTER_SCHEDULED_TO)
        to_el.evaluate(
            "(elm, v) => { elm.value = v; "
            "elm.dispatchEvent(new Event('input', {bubbles: true})); "
            "elm.dispatchEvent(new Event('change', {bubbles: true})); }",
            to_date
        )
        self.page.wait_for_timeout(1500)

    def set_type_filter(self, value):
        """value: '' (All) | 'flow_numbers' (Flow) | 'campaign' (Campaign)"""
        self.open_filters_panel()
        self.h.wait_for_element_visible(self.FILTER_TYPE_SELECT)
        self.h.select_option(self.FILTER_TYPE_SELECT, value=value)
        self.page.wait_for_timeout(1200)

    def get_filter_values(self):
        self.open_filters_panel()
        dept = self.h.wait_for_element_visible(self.FILTER_DEPARTMENT).get_attribute("value")
        user = self.h.wait_for_element_visible(self.FILTER_USER).get_attribute("value")
        sched_from = self.h.wait_for_element_visible(self.FILTER_SCHEDULED_FROM).get_attribute("value")
        sched_to = self.h.wait_for_element_visible(self.FILTER_SCHEDULED_TO).get_attribute("value")
        return {"department": dept, "user": user,
                "scheduled_from": sched_from, "scheduled_to": sched_to}

    def clear_all_filters(self):
        """No dedicated 'Clear Filters' button was confirmed in the
        supplied DOM dump — resets the confirmed text/date inputs
        directly via JS (same caveat as every other slide-down-layout
        page in this project). The Status/Service multiselects and Type
        select are left untouched here (they default to empty/"All" on
        a fresh page load, which reset_state() handles via re-navigate)."""
        self.open_filters_panel()
        for locator in (self.FILTER_DEPARTMENT, self.FILTER_USER,
                        self.FILTER_SCHEDULED_FROM, self.FILTER_SCHEDULED_TO):
            try:
                el = self.h.wait_for_element_visible(locator)
                el.evaluate(
                    "(elm) => { elm.value = ''; "
                    "elm.dispatchEvent(new Event('input', {bubbles: true})); "
                    "elm.dispatchEvent(new Event('change', {bubbles: true})); }"
                )
                self.page.wait_for_timeout(500)
            except Exception:
                pass
        self.page.wait_for_timeout(1000)

    # ── Status / Service custom Alpine multiselect filters ───────────────────

    def _open_multiselect(self, wrapper_locator):
        self.open_filters_panel()
        wrapper = self.h.wait_for_element_visible(wrapper_locator)
        toggle_btn = wrapper.locator("button").first
        toggle_btn.scroll_into_view_if_needed()
        toggle_btn.click(force=True)
        self.page.wait_for_timeout(500)
        return wrapper

    def select_status_option(self, name):
        """name: one of Cancelled, Draft, Failed, Paused, Pending, Scheduled, Sending, Sent"""
        wrapper = self._open_multiselect(self.FILTER_STATUS_WRAPPER)
        label = wrapper.locator(f"xpath=.//label[.//span[normalize-space()='{name}']]").first
        cb = label.locator("input").first
        cb.click(force=True)
        self.page.wait_for_timeout(1000)

    def select_service_option(self, name):
        wrapper = self._open_multiselect(self.FILTER_SERVICE_WRAPPER)
        label = wrapper.locator(f"xpath=.//label[.//span[normalize-space()='{name}']]").first
        cb = label.locator("input").first
        cb.click(force=True)
        self.page.wait_for_timeout(1000)

    def get_status_filter_count_text(self):
        self.open_filters_panel()
        wrapper = self.h.wait_for_element_visible(self.FILTER_STATUS_WRAPPER)
        btn = wrapper.locator("button").first
        return btn.inner_text().strip()

    def get_service_filter_count_text(self):
        self.open_filters_panel()
        wrapper = self.h.wait_for_element_visible(self.FILTER_SERVICE_WRAPPER)
        btn = wrapper.locator("button").first
        return btn.inner_text().strip()

    # ── Bulk Actions ─────────────────────────────────────────────────────────
    # NOT built here -- confirmed absent from this page's DOM (see module
    # docstring caveat #6): no Bulk Actions dropdown, no row checkboxes.

    # ── Columns dropdown ─────────────────────────────────────────────────────

    def open_columns_dropdown(self):
        if self._is_visible(self.COLUMN_CHECKBOXES, timeout=1000):
            return
        self._js_click(self.COLUMNS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def toggle_column(self, value):
        """value: 'action' | 'campaign-name' | 'type' | 'subject' |
        'department' | 'user' | 'email-service' | 'template' | 'status' |
        'scheduled-at' | 'created-at'"""
        self.open_columns_dropdown()
        cb = self.h.wait_for_element_visible(f"input[type='checkbox'][value*='{value}']")
        cb.scroll_into_view_if_needed()
        cb.click(force=True)
        self.page.wait_for_timeout(800)

    def is_column_checked(self, value):
        self.open_columns_dropdown()
        try:
            cb = self.page.locator(f"input[type='checkbox'][value*='{value}']").first
            return cb.is_checked()
        except Exception:
            return None

    def restore_default_columns(self):
        """Restores the CONFIRMED default column state: action/
        campaign-name/type/subject/email-service/template/status/
        scheduled-at/created-at checked, department/user unchecked."""
        defaults = {"action": True, "campaign-name": True, "type": True,
                    "subject": True, "department": False, "user": False,
                    "email-service": True, "template": True, "status": True,
                    "scheduled-at": True, "created-at": True}
        for value, should_be_checked in defaults.items():
            self.open_columns_dropdown()
            try:
                cb = self.page.locator(f"input[type='checkbox'][value='{value}']").first
                if cb.count() == 0:
                    continue
            except Exception:
                continue
            if cb.is_checked() != should_be_checked:
                cb.scroll_into_view_if_needed()
                cb.click(force=True)
                self.page.wait_for_timeout(500)

    # ── Row actions: View (modal) + Reports (link) ───────────────────────────

    def click_view_on_first_row(self):
        row = self.get_first_data_row()
        if row is None:
            return False
        try:
            btn = row.locator(self.VIEW_BTN_IN_ROW).first
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
            modal = self.page.locator(self.MODAL_CONTAINER).first
            if modal.count() == 0:
                return False
            style = modal.get_attribute("style")
            return modal.is_visible() or style != "display: none;"
        except Exception:
            return False

    def click_reports_on_first_row(self):
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
        link.click(force=True)
        self.page.wait_for_timeout(1500)
        return True

    def is_campaign_report_page(self):
        return "/campaigns/email/report/" in self.get_current_url()

    # ── Export to XLSX (confirmation modal) ──────────────────────────────────

    def click_export_to_xlsx(self):
        self._js_click(self.EXPORT_XLSX_BTN, timeout=10000)
        self.page.wait_for_timeout(1000)

    def is_export_confirm_modal_open(self):
        return self.is_element_present(self.EXPORT_CONFIRM_MODAL_TITLE, timeout=5000)

    def click_export_confirm_yes(self):
        self._js_click(self.EXPORT_CONFIRM_YES_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def click_export_confirm_no(self):
        self._js_click(self.EXPORT_CONFIRM_NO_BTN, timeout=10000)
        self.page.wait_for_timeout(1000)

    def wait_for_xlsx_download(self, timeout=30000):
        """Waits for the page-level download event registered in
        __init__ to fire (replaces the Selenium version's DOWNLOAD_DIR
        mtime-based folder polling — Playwright captures the download
        directly as an event, with no folder polling or filename
        collisions to worry about)."""
        deadline = time.time() + timeout / 1000
        start_count = len(self._downloaded_paths)
        while time.time() < deadline:
            if len(self._downloaded_paths) > start_count:
                dest = self._downloaded_paths[-1]
                return {"file_path": dest, "file_size": os.path.getsize(dest)}
            self.page.wait_for_timeout(500)
        return None

    # ── Pagination ───────────────────────────────────────────────────────────

    def get_pagination_results_text(self):
        el = self.h.wait_for_element_visible(self.PAGINATION_RESULTS_TEXT)
        return el.inner_text().strip()

    def click_next_page(self):
        self._js_click(self.NEXT_PAGE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    # ── Performance ──────────────────────────────────────────────────────────

    def get_page_load_time_ms(self):
        try:
            return self.page.evaluate(
                "() => window.performance.timing.loadEventEnd - "
                "window.performance.timing.navigationStart"
            )
        except Exception:
            return None

    # ── Logout ───────────────────────────────────────────────────────────────

    def logout(self):
        self._js_click(self.USER_MENU_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)
        self._js_click(self.LOGOUT_LINK, timeout=10000)
        self.page.wait_for_timeout(1500)
