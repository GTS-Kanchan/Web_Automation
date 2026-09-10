from pages.common.base_page import BasePage


class WhatsAppOptOutPage(BasePage):

    REPORT_URL = "/whatsapp/campaigns/opt-out"
    CREATE_URL = "/whatsapp/campaigns/opt-out/create"
    TABLE_NAME = "opt_out_numbers"

    # Confirmed column order for the DEFAULT (all-selected) column state only.
    COLUMN_INDEX = {"bulk_checkbox": 0, "action": 1, "phone_number": 2,
                     "sender": 3, "opted_out_at": 4}

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'WhatsApp OptOut Numbers')]"
    BREADCRUMB = "xpath=//nav[@aria-label='Breadcrumb']"

    # ── Top action buttons (confirmed) ──────────────────────────────────────
    ADD_NEW_BTN = (
        "xpath=//a[contains(@href,'/whatsapp/campaigns/opt-out/create') and "
        "contains(normalize-space(.),'Add New OptOut Number')]"
    )
    UPLOAD_BTN = "xpath=//button[@title='Upload OptOut Numbers from Excel/CSV file']"
    MODAL_CONTAINER = "#modal-container"

    # ── Search ───────────────────────────────────────────────────────────────
    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search by phone number or sender...']"

    # ── Filters (slide-down layout, three confirmed fields) ─────────────────
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')]"
    FILTER_SENDER = "#opt_out_numbers-filter-sender"
    FILTER_OPTED_OUT_FROM = "#opt_out_numbers-filter-opted_out_from"
    FILTER_OPTED_OUT_TO = "#opt_out_numbers-filter-opted_out_to"

    # ── Bulk Actions ─────────────────────────────────────────────────────────
    BULK_ACTIONS_BUTTON = "#opt_out_numbers-bulkActionsDropdown"
    BULK_ACTION_DELETE = (
        "xpath=//button[@*[name()='wire:click']='bulkDelete' and contains(@*[name()='wire:key'],'bulk-action-bulkDelete')]"
    )
    ROW_CHECKBOX = "input[type='checkbox'][wire\\:key^='opt_out_numbersselectedItems-']"

    # ── Sorting ──────────────────────────────────────────────────────────────
    SORT_PHONE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('phone_number')\")]"
    SORT_SENDER_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('sender_id')\")]"
    SORT_OPTED_OUT_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('opted_out_at')\")]"
    CLEAR_SORT_BTN = "xpath=//button[contains(@*[name()='wire:click'],'clearSort')]"
    # wire:click.prevent, not wire:click -- confirmed via real DOM after a
    # live test_TC008_clear_applied_sorting timeout: <button
    # wire:click.prevent="clearSorts">...Clear...</button>. Same bug, same
    # fix as whatsapp_template_page.py's CLEAR_ALL_SORTS_BTN: XPath's
    # name()='wire:click' only matches an attribute named exactly that
    # string, not 'wire:click.prevent', so the old locator could never
    # match this button. (This is NOT the same situation as RCS's
    # rcs_optout_page.py, whose own clear_all_sorts() comment says that
    # page has no clearSorts button at all -- WhatsApp's opt-out page does
    # have one, confirmed here, it was just unreachable via the wrong
    # attribute name.)
    CLEAR_ALL_SORTS_BTN = "xpath=//button[contains(@*[name()='wire:click.prevent'],'clearSorts')]"
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

    # ── Delete (row) — $wireui.confirmAction -> SweetAlert2 ─────────────────
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
    PAGINATION_RESULTS_TEXT = ".total-pagination-results"

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

    def is_optout_page(self):
        url = self.get_current_url()
        return "/whatsapp/campaigns/opt-out" in url and "login" not in url.lower()

    def get_page_title_text(self):
        el = self.h.wait_for_element_visible(self.PAGE_TITLE)
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

    # ── Top action buttons ───────────────────────────────────────────────────

    def click_add_new_optout_number(self):
        self._js_click(self.ADD_NEW_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def click_upload_optout_numbers(self):
        self._js_click(self.UPLOAD_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_upload_popup_open(self):
        return (self.is_element_present("#dropzone-file", timeout=8000)
                or self.is_element_present(self.MODAL_CONTAINER, timeout=3000))

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

    def sort_by_sender(self):
        self._js_click(self.SORT_SENDER_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_opted_out_at(self):
        self._js_click(self.SORT_OPTED_OUT_AT_BTN, timeout=10000)
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
        if self._is_visible(self.FILTER_SENDER, timeout=1000):
            return
        self._js_click(self.FILTERS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def set_sender_filter(self, value):
        self.open_filters_panel()
        el = self.h.wait_for_element_visible(self.FILTER_SENDER)
        el.evaluate(
            "(elm, v) => { elm.value = v; "
            "elm.dispatchEvent(new Event('input', {bubbles: true})); "
            "elm.dispatchEvent(new Event('change', {bubbles: true})); }",
            value
        )
        self.page.wait_for_timeout(1200)

    def set_date_filter(self, from_date, to_date):
        self.open_filters_panel()
        from_el = self.h.wait_for_element_visible(self.FILTER_OPTED_OUT_FROM)
        from_el.evaluate(
            "(elm, v) => { elm.value = v; "
            "elm.dispatchEvent(new Event('input', {bubbles: true})); "
            "elm.dispatchEvent(new Event('change', {bubbles: true})); }",
            from_date
        )
        self.page.wait_for_timeout(600)
        to_el = self.h.wait_for_element_visible(self.FILTER_OPTED_OUT_TO)
        to_el.evaluate(
            "(elm, v) => { elm.value = v; "
            "elm.dispatchEvent(new Event('input', {bubbles: true})); "
            "elm.dispatchEvent(new Event('change', {bubbles: true})); }",
            to_date
        )
        self.page.wait_for_timeout(1500)

    def get_filter_values(self):
        # input_value(), not get_attribute("value") -- set_sender_filter()
        # and the opted-out-from/to date setters all assign via
        # elm.value = ... (a live DOM PROPERTY), which never touches the
        # static HTML value attribute. Same proven fix already used on the
        # WhatsApp Incoming Messages page and the RCS Opt-out page's own
        # get_filter_values() (this page's WhatsApp counterpart was the
        # one still using the broken get_attribute("value") form).
        self.open_filters_panel()
        sender_el = self.h.wait_for_element_visible(self.FILTER_SENDER)
        from_el = self.h.wait_for_element_visible(self.FILTER_OPTED_OUT_FROM)
        to_el = self.h.wait_for_element_visible(self.FILTER_OPTED_OUT_TO)
        return (sender_el.input_value(), from_el.input_value(),
                to_el.input_value())

    def clear_all_filters(self):
        """No dedicated 'Clear Filters' button was confirmed in the supplied
        DOM dump (see module docstring caveat #4) — resets all three
        confirmed filter inputs directly via JS instead of guessing a
        hidden button locator."""
        self.open_filters_panel()
        for locator in (self.FILTER_SENDER, self.FILTER_OPTED_OUT_FROM, self.FILTER_OPTED_OUT_TO):
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
        """value: 'action' | 'phone-number' | 'sender' | 'opted-out-at'"""
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
        """Restores the CONFIRMED default column state: ALL FOUR columns
        (action/phone-number/sender/opted-out-at) checked — unlike
        rcs_optout_page.py, there is no deselected-by-default column here."""
        defaults = {"action": True, "phone-number": True, "sender": True, "opted-out-at": True}
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
        btn.scroll_into_view_if_needed()
        btn.click(force=True)
        self.page.wait_for_timeout(1000)
        return True

    def cancel_delete(self):
        try:
            btn = self.page.locator(self.CANCEL_DELETE_BTN).first
            btn.wait_for(state="visible", timeout=10000)
        except Exception:
            return False
        btn.click()
        self.page.wait_for_timeout(1000)
        return True

    # ── Pagination ───────────────────────────────────────────────────────────

    def get_pagination_results_text(self):
        el = self.h.wait_for_element_visible(self.PAGINATION_RESULTS_TEXT)
        return el.inner_text().strip()

    # ── Add OptOut Number (create page) — best-effort, see module
    # docstring caveat #8. Not asserted against; flagged/skipped in tests. ──

    def is_create_page(self):
        return "/whatsapp/campaigns/opt-out/create" in self.get_current_url()

    # ── Logout ───────────────────────────────────────────────────────────────

    def logout(self):
        self._js_click(self.USER_MENU_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)
        self._js_click(self.LOGOUT_LINK, timeout=10000)
        self.page.wait_for_timeout(1500)
