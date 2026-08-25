from pages.common.base_page import BasePage


class RcsOptOutPage(BasePage):

    REPORT_URL = "/rcs/optout"
    CREATE_URL = "/rcs/optout/create"
    TABLE_NAME = "rcs_optouts"

    # Confirmed column order for the DEFAULT column selection only
    # (action/phone-number/opted-out-at). If reason/created-at get
    # toggled on, indices shift — tests check header text presence/
    # absence rather than depending on index stability once toggled.
    COLUMN_INDEX = {"bulk_checkbox": 0, "action": 1, "phone_number": 2, "opted_out_at": 3}

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'RCS OptOut Numbers')]"
    BREADCRUMB = "xpath=//nav[@aria-label='Breadcrumb']"

    # ── Top action buttons (confirmed) ──────────────────────────────────────
    ADD_NEW_BTN = (
        "xpath=//a[contains(@href,'/rcs/optout/create') and contains(normalize-space(.),'Add New OptOut Number')]"
    )
    UPLOAD_BTN = "xpath=//button[@title='Upload OptOut Numbers from Excel/CSV file']"
    MODAL_CONTAINER = "#modal-container"

    # ── Search ───────────────────────────────────────────────────────────────
    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search by phone number...']"

    # ── Filters popover (confirmed: two plain native date inputs) ───────────
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')]"
    FILTER_OPTED_OUT_FROM = "#rcs_optouts-filter-opted_out_from"
    FILTER_OPTED_OUT_TO = "#rcs_optouts-filter-opted_out_to"

    # ── Bulk Actions ─────────────────────────────────────────────────────────
    BULK_ACTIONS_BUTTON = "#rcs_optouts-bulkActionsDropdown"
    BULK_ACTION_EXPORT = (
        "xpath=//button[@*[name()='wire:click']='export' and contains(@*[name()='wire:key'],'bulk-action-export')]"
    )
    BULK_ACTION_DELETE = (
        "xpath=//button[@*[name()='wire:click']='bulkDelete' and contains(@*[name()='wire:key'],'bulk-action-bulkDelete')]"
    )
    ROW_CHECKBOX = "input[type='checkbox'][wire\\:key^='rcs_optoutsselectedItems-']"

    # ── Sorting ──────────────────────────────────────────────────────────────
    SORT_PHONE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('phone_number')\")]"
    SORT_OPTED_OUT_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('opted_out_at')\")]"
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

    # ── Delete (row) — $wireui.confirmAction -> SweetAlert2, note the
    # "tooltip-delete-" prefix (not "tooltip-deleteOne-" like SMS). ─────────
    DELETE_ICON_IN_ROW = "xpath=.//*[contains(@data-tooltip-target,'tooltip-delete-')]"
    CONFIRM_DELETE_BTN = (
        "xpath=//button[contains(@class,'swal2-confirm')] "
        "| //div[contains(@class,'swal2-actions')]//button[not(contains(@class,'swal2-cancel')) "
        "and not(contains(@class,'swal2-deny'))] "
        "| //button[normalize-space()='Confirm' or normalize-space()='Yes' "
        "or normalize-space()='Yes, delete it!' or normalize-space()='OK' "
        "or normalize-space()='Delete' or normalize-space()='Accept']"
    )
    CANCEL_DELETE_BTN = (
        "xpath=//button[contains(@class,'swal2-cancel')] "
        "| //button[normalize-space()='Cancel' or normalize-space()='No']"
    )

    # ── Pagination ───────────────────────────────────────────────────────────
    PAGINATION_RESULTS_TEXT = ".total-pagination-results, .paged-pagination-results"
    NEXT_PAGE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"nextPage('rcs_optoutsPage')\")]"
    PREV_PAGE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"previousPage('rcs_optoutsPage')\")]"

    # ── Add OptOut Number (create page) — UNCONFIRMED, see module docstring
    # caveat #8. Best-effort only; not asserted against in the test suite. ──
    ADD_PHONE_INPUT = "#phone_number"
    ADD_SUBMIT_BTN = (
        "xpath=//button[@type='submit' and contains(normalize-space(.),'Add OptOut Number')] "
        "| //button[@type='submit']"
    )

    # ── Upload popup — UNCONFIRMED, see module docstring caveat #9. ─────────
    FILE_INPUT = "#dropzone-file"
    UPLOAD_POPUP = "xpath=//div[contains(@class,'fixed') and .//input[@id='dropzone-file']]"

    # ── User menu / logout (global header, confirmed identical to every
    # other page in this app). ──────────────────────────────────────────────
    USER_MENU_BUTTON = "xpath=//button[contains(@class,'rounded-full') and .//img]"
    LOGOUT_LINK = "xpath=//a[@title='Log out']"

    # ── Navigation / page state ─────────────────────────────────────────────

    def navigate(self):
        self.open(self.REPORT_URL)
        self.page.wait_for_timeout(4000)
        return self

    # kept as an alias for parity with the naming used elsewhere
    navigate_to_report = navigate

    def is_optout_page(self):
        url = self.get_current_url()
        return "/rcs/optout" in url and "login" not in url.lower()

    def get_page_title_text(self):
        el = self.h.wait_for_element_visible(self.PAGE_TITLE)
        return el.inner_text().strip()

    def wait_for_table_load(self, timeout=15000):
        self.page.locator(self.TABLE).first.wait_for(state="attached", timeout=timeout)
        self.page.wait_for_timeout(1000)

    def _is_visible(self, locator, timeout=1000):
        try:
            return self.page.locator(locator).first.is_visible()
        except Exception:
            return False

    # ── Top action buttons ───────────────────────────────────────────────────

    def click_add_new_optout_number(self):
        self._js_click(self.ADD_NEW_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def click_upload_optout_numbers(self):
        self._js_click(self.UPLOAD_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_upload_popup_open(self):
        return self.is_element_present(self.FILE_INPUT, timeout=8000) or \
               self.is_element_present(self.UPLOAD_POPUP, timeout=3000)

    # ── Search ───────────────────────────────────────────────────────────────

    def _wait_for_search_to_settle(self, timeout=8000):
        end_time = self.page.evaluate("() => Date.now()") + timeout
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
        """Sets the full value via a single JS-driven 'input' dispatch to
        avoid a race condition with wire:model.live's per-keystroke
        requests — same fix applied on other Livewire-tables pages in this
        project."""
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.evaluate(
            "(el, v) => { el.value = v; "
            "el.dispatchEvent(new Event('input', {bubbles: true})); "
            "el.dispatchEvent(new Event('change', {bubbles: true})); }",
            value
        )
        self.page.wait_for_timeout(500)
        self._wait_for_search_to_settle()
        self.page.wait_for_timeout(300)

    def clear_search(self):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.evaluate(
            "(el) => { el.value = ''; "
            "el.dispatchEvent(new Event('input', {bubbles: true})); "
            "el.dispatchEvent(new Event('change', {bubbles: true})); }"
        )
        self.page.wait_for_timeout(500)
        self._wait_for_search_to_settle()
        self.page.wait_for_timeout(300)

    # ── Table / rows ─────────────────────────────────────────────────────────

    def has_records(self):
        return self.is_element_present(self.TABLE_ROWS, timeout=5000) and self.get_row_count() > 0

    @staticmethod
    def _is_empty_state_row(tds):
        """rappasoft/laravel-livewire-tables renders a genuinely empty
        result set as a single <tr> containing exactly one
        <td colspan="N">...</td> placeholder — detected structurally via
        colspan so it doesn't depend on guessing the exact empty-state
        wording."""
        return len(tds) == 1 and tds[0].get_attribute("colspan")

    def has_no_records_message(self):
        if self.is_element_present(self.NO_RECORDS_MSG, timeout=3000):
            return True
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            if rows.count() == 1:
                tds = rows.nth(0).locator("td")
                td_list = [tds.nth(i) for i in range(tds.count())]
                if self._is_empty_state_row(td_list):
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
                td_list = [tds.nth(j) for j in range(n)]
                if self._is_empty_state_row(td_list):
                    continue
                if any(td.inner_text().strip() for td in td_list):
                    count += 1
            return count
        except Exception:
            return 0

    def get_visible_column_headers(self):
        return self._get_headers_safe(self.TABLE_HEADERS)

    def get_column_values(self, column_name):
        idx = self.COLUMN_INDEX.get(column_name)
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

    def sort_by_phone_number(self):
        self._js_click(self.SORT_PHONE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_opted_out_at(self):
        self._js_click(self.SORT_OPTED_OUT_AT_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def get_applied_sort_pill_text(self):
        if self.is_element_present(self.APPLIED_SORT_PILL, timeout=3000):
            return self.h.wait_for_element_visible(self.APPLIED_SORT_PILL).inner_text().strip()
        return None

    def clear_all_sorts(self):
        try:
            # The Opt-out page doesn't have a clearSorts button.
            # We must click the 'x' on the active pill itself.
            remove_btns = self.page.locator("xpath=//button[contains(@*[name()='wire:click'], 'clearSort(')]")
            for i in range(remove_btns.count()):
                btn = remove_btns.nth(i)
                btn.scroll_into_view_if_needed()
                btn.click(force=True)
                self.page.wait_for_timeout(1000)
        except Exception:
            pass

    # ── Filters popover ──────────────────────────────────────────────────────

    def open_filters_popover(self):
        if self._is_visible(self.FILTER_OPTED_OUT_FROM, timeout=1000):
            return
        self._js_click(self.FILTERS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def set_date_filter(self, from_date, to_date):
        """Both filter fields are plain native <input type="date"> with
        stable ids and wire:model.live bindings — CONFIRMED from the DOM
        (no Alpine no-stable-id combo pattern here, unlike several other
        pages in this project), so a direct JS value-set + input/change
        event dispatch is sufficient without any Livewire-JS workaround."""
        self.open_filters_popover()
        from_el = self.h.wait_for_element_visible(self.FILTER_OPTED_OUT_FROM)
        from_el.evaluate(
            "(el, v) => { el.value = v; "
            "el.dispatchEvent(new Event('input', {bubbles: true})); "
            "el.dispatchEvent(new Event('change', {bubbles: true})); }",
            from_date
        )
        self.page.wait_for_timeout(600)
        to_el = self.h.wait_for_element_visible(self.FILTER_OPTED_OUT_TO)
        to_el.evaluate(
            "(el, v) => { el.value = v; "
            "el.dispatchEvent(new Event('input', {bubbles: true})); "
            "el.dispatchEvent(new Event('change', {bubbles: true})); }",
            to_date
        )
        self.page.wait_for_timeout(1500)

    def get_filter_values(self):
        self.open_filters_popover()
        from_el = self.h.wait_for_element_visible(self.FILTER_OPTED_OUT_FROM)
        to_el = self.h.wait_for_element_visible(self.FILTER_OPTED_OUT_TO)
        return from_el.get_attribute("value"), to_el.get_attribute("value")

    # ── Bulk Actions ─────────────────────────────────────────────────────────

    def open_bulk_actions_dropdown(self):
        self._js_click(self.BULK_ACTIONS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def select_first_row_checkbox(self):
        cb = self.h.wait_for_element_visible(self.ROW_CHECKBOX)
        cb.scroll_into_view_if_needed()
        cb.click(force=True)
        self.page.wait_for_timeout(500)

    # ── Columns dropdown ─────────────────────────────────────────────────────

    def open_columns_dropdown(self):
        if self._is_visible(self.COLUMN_CHECKBOXES, timeout=1000):
            return
        self._js_click(self.COLUMNS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def toggle_column(self, value):
        """value: 'action' | 'phone-number' | 'reason' | 'opted-out-at' | 'created-at'"""
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
        """Restores the CONFIRMED default column state: action/
        phone-number/opted-out-at checked, reason/created-at unchecked."""
        defaults = {"action": True, "phone-number": True, "reason": False,
                    "opted-out-at": True, "created-at": False}
        for value, should_be_checked in defaults.items():
            self.open_columns_dropdown()
            try:
                cb = self.page.locator(f"input[type='checkbox'][value='{value}']").first
                if cb.count() == 0:
                    continue
                if cb.is_checked() != should_be_checked:
                    cb.scroll_into_view_if_needed()
                    cb.click(force=True)
                    self.page.wait_for_timeout(500)
            except Exception:
                continue

    # ── Delete (row) ─────────────────────────────────────────────────────────

    def click_delete_on_first_row(self):
        row = self.get_first_data_row()
        if row is None:
            return False
        try:
            btn = row.locator(self.DELETE_ICON_IN_ROW).first
            if btn.count() == 0:
                return False
        except Exception:
            return False
        try:
            btn.scroll_into_view_if_needed()
            btn.click(force=True)
        except Exception:
            return False
        self.page.wait_for_timeout(1000)
        return True

    def cancel_delete(self):
        try:
            btn = self.page.locator(self.CANCEL_DELETE_BTN).first
            btn.wait_for(state="visible", timeout=10000)
            btn.click()
        except Exception:
            return False
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
        """Previous renders as a disabled <span> on page 1 (confirmed from
        the DOM: aria-disabled='true' wrapping a plain <span>, no
        wire:click) — only a real clickable <button> counts as enabled,
        same convention as rcs_message_page.py."""
        try:
            return self.page.locator(self.PREV_PAGE_BTN).count() > 0
        except Exception:
            return False

    # ── Add OptOut Number (create page) — best-effort, see module
    # docstring caveat #8. Not asserted against; flagged/skipped in tests. ──

    def is_create_page(self):
        return "/rcs/optout/create" in self.get_current_url()

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
