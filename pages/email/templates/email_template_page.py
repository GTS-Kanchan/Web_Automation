from pages.common.base_page import BasePage


class EmailTemplatePage(BasePage):

    LIST_URL = "/email/template"
    CREATE_URL = "/email/template/create"
    TABLE_NAME = "email_templates"

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'Email Template')]"
    BREADCRUMB = "xpath=//nav[@aria-label='Breadcrumb']"
    CREATE_NEW_TEMPLATE_BTN = (
        "xpath=//a[contains(@href,'/email/template/create') and contains(normalize-space(.),'Create New Template')]"
    )
    MODAL_CONTAINER = "#modal-container"

    # ── Global WireUI confirm dialog (shared across the whole app) ──────────
    WIREUI_DIALOG = "xpath=//div[@x-data=\"wireui_dialog({ id: 'dialog' })\"]"
    WIREUI_DIALOG_TITLE = "xpath=//div[@x-data=\"wireui_dialog({ id: 'dialog' })\"]//h3[@x-ref='title']"
    WIREUI_DIALOG_ACCEPT_BTN = "xpath=//div[@x-ref='accept']//button"
    WIREUI_DIALOG_REJECT_BTN = "xpath=//div[@x-ref='reject']//button"

    # ── Global WireUI notification toast (shared across the whole app) ──────
    NOTIFICATION_TITLE = "xpath=//div[@x-data='wireui_notifications']//p[@x-show='notification.title']"

    # ── Search ───────────────────────────────────────────────────────────────
    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search']"

    # ── Filters (slide-down layout, six confirmed fields) ───────────────────
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')]"
    FILTER_DEPARTMENT = "#email_templates-filter-department"
    FILTER_USER = "#email_templates-filter-user"
    FILTER_STATUS_SELECT = "#email_templates-filter-status"
    FILTER_TYPE_SELECT = "#email_templates-filter-type"
    FILTER_CREATED_FROM = "#email_templates-filter-created_at_from"
    FILTER_CREATED_TO = "#email_templates-filter-created_at_to"

    STATUS_VALUES = {
        "Approved": "3", "Archived": "9", "Deleted": "10", "Disabled": "8",
        "Failed": "6", "Hold": "5", "Paused": "7", "Pending": "1",
        "Processing": "2", "Rejected": "4",
    }
    TYPE_VALUES = {"All": "", "Transactional": "Transactional",
                   "Promotional": "Promotional", "OTP": "OTP"}

    # ── Sorting ──────────────────────────────────────────────────────────────
    SORT_NAME_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('name')\")]"
    SORT_TYPE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('type')\")]"
    SORT_DEPARTMENT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('team.display_name')\")]"
    SORT_USER_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('user.name')\")]"
    SORT_STATUS_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('status')\")]"
    SORT_CREATED_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('created_at')\")]"
    CLEAR_SORT_BTN = "xpath=//button[contains(@*[name()='wire:click'],'clearSort')]"
    CLEAR_ALL_SORTS_BTN = "xpath=//button[contains(@*[name()='wire:click'],'clearSort')]"
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

    # ── Row actions: View (modal) / Edit (link) / Delete (WireUI dialog) ────
    VIEW_BTN_IN_ROW = (
        "xpath=.//button[contains(@*[starts-with(name(), 'wire:click')], 'openModal') "
        "or contains(@*[starts-with(name(), 'wire:click')], 'view') "
        "or contains(normalize-space(.), 'Preview') or contains(normalize-space(.), 'View')]"
    )
    EDIT_LINK_IN_ROW = "xpath=.//a[contains(@href,'/email/template/') and contains(@href,'/edit')]"
    DELETE_BTN_IN_ROW = "xpath=.//button[contains(@data-tooltip-target,'tooltip-deleteOne-')]"

    # ── Export to XLSX (confirmation modal — identical markup to EmailCampaignPage) ─
    EXPORT_XLSX_BTN = "xpath=//button[contains(normalize-space(.),'Export to XLSX')]"
    EXPORT_CONFIRM_MODAL_TITLE = "xpath=//h2[normalize-space()='Export']"
    EXPORT_CONFIRM_YES_BTN = "xpath=//button[@*[name()='wire:click']='exportAll']"
    EXPORT_CONFIRM_NO_BTN = "xpath=//button[contains(normalize-space(.),'No') and not(@*[name()='wire:click'])]"

    # ── Pagination ───────────────────────────────────────────────────────────
    PAGINATION_RESULTS_TEXT = ".paged-pagination-results"
    NEXT_PAGE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"nextPage('email_templatesPage')\")]"

    # ── User menu / logout (global header) ───────────────────────────────────
    USER_MENU_BUTTON = "xpath=//button[contains(@class,'rounded-full') and .//img]"
    LOGOUT_LINK = "xpath=//a[@title='Log out']"

    # ── Navigation / page state ─────────────────────────────────────────────

    def navigate(self):
        self.open(self.LIST_URL)
        self.page.wait_for_timeout(2000)
        return self

    def is_template_list_page(self):
        url = self.get_current_url()
        return "/email/template" in url and "login" not in url.lower() and "/create" not in url and "/edit" not in url

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

    def click_create_new_template(self):
        self._js_click(self.CREATE_NEW_TEMPLATE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_create_page(self):
        return "/email/template/create" in self.get_current_url()

    # ── Search ───────────────────────────────────────────────────────────────

    def _wait_for_search_to_settle(self, timeout_ms=8000):
        end_time_ms = timeout_ms
        last_state = None
        elapsed = 0
        interval = 600
        while elapsed < end_time_ms:
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

    def get_first_data_row(self):
        return self._first_visible_data_row(f"#table-{self.TABLE_NAME} tbody tr")

    # ── Sorting ──────────────────────────────────────────────────────────────

    def sort_by_name(self):
        self._js_click(self.SORT_NAME_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_type(self):
        self._js_click(self.SORT_TYPE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_department(self):
        self._js_click(self.SORT_DEPARTMENT_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_user(self):
        self._js_click(self.SORT_USER_BTN, timeout=10000)
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

    def set_status_filter(self, name):
        """name: one of STATUS_VALUES keys, e.g. 'Approved'."""
        self.open_filters_panel()
        self.h.wait_for_element_visible(self.FILTER_STATUS_SELECT)
        self.h.select_option(self.FILTER_STATUS_SELECT, value=self.STATUS_VALUES[name])
        self.page.wait_for_timeout(1200)

    def set_type_filter(self, name):
        """name: one of TYPE_VALUES keys, e.g. 'Transactional' or 'All'."""
        self.open_filters_panel()
        self.h.wait_for_element_visible(self.FILTER_TYPE_SELECT)
        self.h.select_option(self.FILTER_TYPE_SELECT, value=self.TYPE_VALUES[name])
        self.page.wait_for_timeout(1200)

    def set_created_date_range(self, from_date, to_date):
        self.open_filters_panel()
        from_el = self.h.wait_for_element_visible(self.FILTER_CREATED_FROM)
        from_el.evaluate(
            "(elm, v) => { elm.value = v; "
            "elm.dispatchEvent(new Event('input', {bubbles: true})); "
            "elm.dispatchEvent(new Event('change', {bubbles: true})); }",
            from_date
        )
        self.page.wait_for_timeout(600)
        to_el = self.h.wait_for_element_visible(self.FILTER_CREATED_TO)
        to_el.evaluate(
            "(elm, v) => { elm.value = v; "
            "elm.dispatchEvent(new Event('input', {bubbles: true})); "
            "elm.dispatchEvent(new Event('change', {bubbles: true})); }",
            to_date
        )
        self.page.wait_for_timeout(1500)

    def get_filter_values(self):
        self.open_filters_panel()
        dept = self.h.wait_for_element_visible(self.FILTER_DEPARTMENT).get_attribute("value")
        user = self.h.wait_for_element_visible(self.FILTER_USER).get_attribute("value")
        return {"department": dept, "user": user}

    def clear_all_filters(self):
        """No dedicated 'Clear Filters' button was confirmed in the
        supplied DOM dump — resets the confirmed text inputs directly via
        JS, and the Status/Type selects back to their default option
        (same caveat as every other slide-down-layout page in this
        project)."""
        self.open_filters_panel()
        for locator in (self.FILTER_DEPARTMENT, self.FILTER_USER,
                        self.FILTER_CREATED_FROM, self.FILTER_CREATED_TO):
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
        try:
            self.set_type_filter("All")
        except Exception:
            pass
        self.page.wait_for_timeout(1000)

    # ── Columns dropdown ─────────────────────────────────────────────────────

    def open_columns_dropdown(self):
        if self._is_visible(self.COLUMN_CHECKBOXES, timeout=1000):
            return
        self._js_click(self.COLUMNS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def toggle_column(self, value):
        """value: 'action' | 'template-name' | 'type' | 'department' |
        'user' | 'status' | 'created-at'"""
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
        """Restores the CONFIRMED default column state: all seven columns
        checked (action/template-name/type/department/user/status/
        created-at)."""
        defaults = {"action": True, "template-name": True, "type": True,
                    "department": True, "user": True, "status": True,
                    "created-at": True}
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

    # ── Row actions: View (modal) ─────────────────────────────────────────────

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

    def close_modal_via_escape(self):
        """The livewire-ui-modal component listens for
        x-on:keydown.escape.window="show && closeModalOnEscape()" —
        CONFIRMED structurally (attribute present on the modal root) even
        though the modal's own internal content was never captured."""
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(800)

    # ── Row actions: Edit (link reachability only) ────────────────────────────

    def click_edit_on_first_row(self):
        row = self.get_first_data_row()
        if row is None:
            return False
        try:
            link = row.locator(self.EDIT_LINK_IN_ROW).first
            if link.count() == 0:
                return False
        except Exception:
            return False
        href = link.get_attribute("href")
        link.scroll_into_view_if_needed()
        link.click(force=True)
        self.page.wait_for_timeout(1500)
        return href

    def is_edit_page(self):
        return "/email/template/" in self.get_current_url() and self.get_current_url().endswith("/edit")

    # ── Row actions: Delete (global WireUI confirm dialog) ────────────────────

    def click_delete_on_row(self, row):
        """Click the Delete button WITHIN a specific row element (never
        picks an arbitrary row implicitly — callers must locate the exact
        row, e.g. via search_and_get_first_row(), to avoid touching
        unrelated fixture data)."""
        try:
            btn = row.locator(self.DELETE_BTN_IN_ROW).first
            if btn.count() == 0:
                return False
        except Exception:
            return False
        btn.scroll_into_view_if_needed()
        try:
            btn.click()
        except Exception:
            btn.click(force=True)
        self.page.wait_for_timeout(500)
        return True

    def is_delete_confirm_dialog_open(self):
        try:
            title = self.page.locator(self.WIREUI_DIALOG_TITLE).first
            title.wait_for(state="visible", timeout=8000)
            deadline_ms = 8000
            elapsed = 0
            while elapsed < deadline_ms:
                if "delete" in title.inner_text().strip().lower():
                    return True
                self.page.wait_for_timeout(300)
                elapsed += 300
            return False
        except Exception:
            return self.is_element_present(self.WIREUI_DIALOG_ACCEPT_BTN, timeout=3000)

    def confirm_delete(self):
        self._js_click(self.WIREUI_DIALOG_ACCEPT_BTN, timeout=10000)
        self.page.wait_for_timeout(2000)

    def reject_delete(self):
        self._js_click(self.WIREUI_DIALOG_REJECT_BTN, timeout=10000)
        self.page.wait_for_timeout(800)

    def search_and_get_first_row(self, name):
        """Search for an exact template name and return its (only) row
        element, or None if not found. Used to scope delete tests to a
        specific, known template rather than an arbitrary grid row."""
        self.search(name)
        return self.get_first_data_row()

    # ── Export to XLSX (confirmation modal) ───────────────────────────────────

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

    # ── Pagination ───────────────────────────────────────────────────────────

    def get_pagination_results_text(self):
        el = self.h.wait_for_element_visible(self.PAGINATION_RESULTS_TEXT)
        return el.inner_text().strip()

    def click_next_page(self):
        self._js_click(self.NEXT_PAGE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    # ── Toast (shared global WireUI notification component) ──────────────────

    def is_success_toast_shown(self, timeout=6000):
        return self.is_element_present(self.NOTIFICATION_TITLE, timeout=timeout)

    # ── Logout ───────────────────────────────────────────────────────────────

    def logout(self):
        self._js_click(self.USER_MENU_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)
        self._js_click(self.LOGOUT_LINK, timeout=10000)
        self.page.wait_for_timeout(1500)
