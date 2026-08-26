import os
import time

from pages.common.base_page import BasePage


class SmsBlockedNumbersPage(BasePage):

    REPORT_URL = "/channels/sms/blocked-numbers"
    CREATE_URL = "/channels/sms/blocked-numbers/create"
    TABLE_NAME = "sms_optouts"

    # Confirmed column order for the DEFAULT column selection only
    # (action/phone-number/created-at). If department/user get toggled
    # on, these indices shift — column-visibility tests below check
    # header text presence/absence rather than depending on index
    # stability once toggled.
    COLUMN_INDEX = {"bulk_checkbox": 0, "action": 1, "phone_number": 2, "created_at": 3}

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'SMS Blocked Numbers')]"
    BREADCRUMB = "nav[aria-label='Breadcrumb']"

    # ── Top action buttons (confirmed) ──────────────────────────────────────
    ADD_NEW_BTN = (
        "xpath=//a[contains(@href,'/blocked-numbers/create')] | //button[contains(.,'Add') and contains(.,'Blocked Number')] | //a[contains(.,'Add New')]"
    )
    UPLOAD_BTN = "xpath=//button[@title='Upload Blocked Numbers from Excel/CSV file']"
    MODAL_CONTAINER = "#modal-container"

    # ── Search ───────────────────────────────────────────────────────────────
    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search']"

    # ── Filters popover (confirmed: only a Created date-range filter) ──────
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')]"
    FILTER_CREATED_AT_INPUT = "#sms_optouts-filter-dateRange-created_at"

    # ── Bulk Actions ─────────────────────────────────────────────────────────
    BULK_ACTIONS_BUTTON = "#sms_optouts-bulkActionsDropdown"
    BULK_ACTION_EXPORT = (
        "xpath=//button[@*[name()='wire:click']='export' and contains(@*[name()='wire:key'],'bulk-action-export')]"
    )
    BULK_ACTION_DELETE = (
        "xpath=//button[@*[name()='wire:click']='bulkDelete' and contains(@*[name()='wire:key'],'bulk-action-bulkDelete')]"
    )
    ROW_CHECKBOX = "input[type='checkbox'][wire\\:key^='sms_optoutsselectedItems-']"

    # ── Sorting ──────────────────────────────────────────────────────────────
    SORT_PHONE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('phone_number')\")]"
    SORT_CREATED_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('created_at')\")]"
    CLEAR_SORT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"clearSort\")]"
    CLEAR_ALL_SORTS_BTN = "xpath=//button[contains(@*[name()='wire:click'],'clearSorts')]"

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
    # Broadened + made case-insensitive (via translate()) after a live run
    # showed a search with zero real matches was NOT being detected: the
    # empty-state text this table actually renders doesn't match the
    # exact-case "No records"/"No data"/"No results" substrings used
    # elsewhere in this project (e.g. on the Error Codes page).
    NO_RECORDS_MSG = (
        "xpath=//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no items found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no record') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no data') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no result') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'not found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'nothing found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no blocked')]"
    )

    # ── Delete (row) — same $wireui.confirmAction -> SweetAlert2 convention
    # already confirmed/used on contacts_page.py and tags_page.py. ─────────
    DELETE_ICON_IN_ROW = (
        "xpath=.//*[contains(@data-tooltip-target,'tooltip-deleteOne') or contains(@data-tooltip-target,'deleteOne')]"
    )
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
    PAGINATION_RESULTS_TEXT = ".paged-pagination-results"
    NEXT_PAGE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"nextPage('sms_optoutsPage')\")]"

    # ── Add Blocked Number form — CONFIRMED from a live DOM dump of
    # /channels/sms/blocked-numbers/create (Livewire component
    # "sms.optout.create", wire:submit.prevent="save"):
    #   <input wire:model="phone_number" type="text" id="phone_number"
    #          placeholder="Enter phone number with country code (e.g.,
    #          +1234567890)" ...>
    #   <button type="submit">Add Blocked Number</button>
    #   <a href=".../blocked-numbers">Cancel</a>
    # The previous ADD_PHONE_INPUT locator used a raw @wire:model XPath
    # attribute, which Chrome's XPath evaluator throws a NamespaceError
    # on (the same "unresolvable namespace" bug documented elsewhere in
    # this project for @wire:key / @wire:click) — this is what caused
    # TC016-TC019 to fail with InvalidSelectorException. Fixed by
    # targeting the confirmed id instead. ─────────────────────────────────
    ADD_PHONE_INPUT = "#phone_number"
    ADD_SUBMIT_BTN = (
        "xpath=//button[@type='submit' and contains(normalize-space(.),'Add Blocked Number')] "
        "| //button[@type='submit']"
    )
    ADD_CANCEL_BTN = (
        "xpath=//a[contains(@href,'/blocked-numbers') and not(contains(@href,'/create')) "
        "and normalize-space()='Cancel'] | //a[normalize-space()='Cancel']"
    )
    # Validation error message: the live DOM shows an empty
    # <!--[if BLOCK]><![endif]--> Blade conditional block immediately
    # after the phone_number input and before its helper paragraph —
    # this is a compiled @error('phone_number') @enderror directive with
    # no error currently rendered (form was never submitted in the
    # captured dump), so its exact markup/classes are still unconfirmed.
    # Scoped near the phone_number field to reduce false positives from
    # the "*" required-marker span (which also carries text-red-500).
    VALIDATION_ERROR_MSG = (
        "xpath=//label[@for='phone_number']/ancestor::div[contains(@class,'md:col-span-2')]"
        "//*[(contains(@class,'text-red-500') or contains(@class,'text-red-600')) "
        "and normalize-space(text())!='*' and normalize-space(text())!='']"
    )
    # CONFIRMED container from the full page DOM captured earlier for this
    # exact create page: WireUI's global toast-notification component.
    # User confirmed behaviorally that submitting a duplicate blocked
    # number shows "an error pop up" rather than an inline field error --
    # this is that mechanism (a dispatched wireui:notification toast, the
    # same one already used for success notifications elsewhere in this
    # app), not the inline @error('phone_number') block. Checked as a
    # fallback in get_validation_error_text() below.
    TOAST_NOTIFICATION_TEXT = (
        "xpath=//div[@x-data='wireui_notifications']"
        "//p[(@x-show='notification.title' or @x-show='notification.description') "
        "and normalize-space(text())!='']"
    )
    # CONFIRMED from the popup's COMPLETE real DOM — the message lives in
    # the <h2 id="swal2-title"> element, NOT in .swal2-html-container
    # (which is empty/hidden here).
    SWAL_ERROR_TITLE = "#swal2-title"
    # Kept as a secondary fallback (matches on the confirmed rendered
    # text itself) in case a future variant of this popup doesn't reuse
    # the #swal2-title id.
    DUPLICATE_POPUP_TEXT = "text=This phone number is already in the blocked numbers list"

    # ── Upload popup — several pieces now CONFIRMED from pasted DOM
    # snippets; the modal's initial (no-file-selected) full-container
    # markup is still not captured, so FILE_INPUT/UPLOAD_POPUP remain
    # best-effort (reusing the "dropzone-file" id convention confirmed
    # working on the Sender ID upload modal elsewhere in this app). ────────
    FILE_INPUT = "#dropzone-file"
    UPLOAD_POPUP = "xpath=//div[contains(@class,'fixed') and .//input[@id='dropzone-file']]"
    BTN_DOWNLOAD_SAMPLE = (
        "xpath=//button[@*[name()='wire:click']='export' and "
        "contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'sample')] "
        "| //a[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'sample')]"
    )
    BTN_UPLOAD_CONFIRM = (
        "xpath=//button[normalize-space()='Yes, Import' or normalize-space()='Import' "
        "or normalize-space()='Upload' or normalize-space()='Submit']"
    )
    # TC027 ("Cancel closes the upload popup", tested against the popup's
    # INITIAL state) — BTN_CANCEL_UPLOAD targets the confirmed
    # $dispatch('closeModal') Cancel control present as soon as the popup
    # opens, before any file is selected. BTN_CANCEL_IMPORT_CONFIRM is the
    # separate post-file-selection confirm-step Cancel, kept for parity
    # but not currently exercised by any test.
    BTN_CANCEL_UPLOAD = "xpath=//div[contains(@*[name()='wire:click'],\"closeModal\") and normalize-space()='Cancel']"
    BTN_CANCEL_IMPORT_CONFIRM = "xpath=//button[@*[name()='wire:click']='cancelImport']"
    UPLOAD_LOADER = (
        "xpath=//div[contains(@class,'animate-pulse') or contains(@class,'animate-spin')] "
        "| //svg[contains(@class,'animate-spin')]"
    )
    # CONFIRMED from a pasted DOM snippet -- the real rejection message for
    # an invalid file type.
    UPLOAD_ERROR_MSG = (
        "xpath=//p[contains(@class,'text-red-700') or contains(@class,'text-red-600') "
        "or contains(@class,'text-red-500')]"
        "[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'error')]"
    )
    UPLOAD_SUCCESS_MSG = "[class*='success'], [class*='alert-success']"

    # ── User menu / logout (global header, confirmed identical to every
    # other page in this app). ──────────────────────────────────────────────
    USER_MENU_BUTTON = "xpath=//button[contains(@class,'rounded-full') and .//img]"
    LOGOUT_LINK = "xpath=//a[@title='Log out']"

    # ── Navigation / page state ─────────────────────────────────────────────

    def navigate_to_report(self):
        self.open(self.REPORT_URL)
        self.page.wait_for_timeout(2000)
        return self

    def is_report_page(self):
        url = self.get_current_url()
        return "/channels/sms/blocked-numbers" in url and "login" not in url.lower()

    def get_page_title_text(self):
        el = self.h.wait_for_element_visible(self.PAGE_TITLE)
        return el.inner_text().strip()

    def get_breadcrumb_text(self):
        el = self.h.wait_for_element_visible(self.BREADCRUMB)
        return " ".join(el.inner_text().split())

    def _js_click(self, locator, timeout=10000):
        return self.h.js_click(locator, timeout=timeout)

    def _is_visible(self, locator, timeout=1000):
        try:
            el = self.page.locator(locator).first
            el.wait_for(state="attached", timeout=timeout)
            return el.is_visible()
        except Exception:
            return False

    # ── Top action buttons ───────────────────────────────────────────────────

    def click_add_new_blocked_number(self):
        self._js_click(self.ADD_NEW_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def click_upload_blocked_numbers(self):
        self._js_click(self.UPLOAD_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_upload_popup_open(self):
        return self.is_element_present(self.FILE_INPUT, timeout=8000) or \
               self.is_element_present(self.UPLOAD_POPUP, timeout=3000)

    # ── Search ───────────────────────────────────────────────────────────────

    def _wait_for_search_to_settle(self, timeout=8000):
        # We need to wait for a period of stability, not just exit immediately
        # if the state hasn't changed once. Livewire might clear the table
        # during loading, which drops row count to 0 temporarily.
        end_time = self.page.evaluate("() => Date.now()") + timeout
        stable_count = 0
        last_state = None
        while self.page.evaluate("() => Date.now()") < end_time:
            current = self.get_row_count()
            no_msg = self.is_element_present(self.NO_RECORDS, timeout=200)
            state = (current, no_msg)
            if state == last_state and current >= 0:
                stable_count += 1
                if stable_count >= 3:  # Must be stable for ~1.5s
                    return
            else:
                stable_count = 0
            last_state = state
            self.page.wait_for_timeout(500)

    def search(self, value):
        """Sets the full value via a single JS-driven 'input' dispatch
        (not fill()/type character-by-character) to avoid a race condition
        with wire:model.live's per-keystroke requests — same fix applied
        on the SMS Error Codes page after a live run exposed it there."""
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.evaluate(
            """(el, val) => {
                el.value = val;
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
            }""",
            value
        )
        box.focus()
        box.press("Enter")
        box.blur()
        self.page.wait_for_timeout(500)
        self._wait_for_search_to_settle()
        self.page.wait_for_timeout(300)

    def clear_search(self):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.evaluate(
            """(el) => {
                el.value = '';
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
            }"""
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
        <td colspan="N">...</td> (the "no records" placeholder), not real
        data. Detected structurally via colspan so it doesn't depend on
        guessing the exact empty-state wording."""
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
        """Playwright locators auto-re-resolve, so the staleness race the
        Selenium version retried against is structurally gone here; the
        retry loop is kept defensively for transient errors during a
        Livewire morph."""
        for attempt in range(4):
            try:
                rows = self.page.locator(self.TABLE_ROWS)
                count = 0
                for i in range(rows.count()):
                    row = rows.nth(i)
                    tds = row.locator("td")
                    if tds.count() == 0:
                        continue
                    if self._is_empty_state_row(tds):
                        continue
                    if any(t.strip() for t in tds.all_inner_texts()):
                        count += 1
                return count
            except Exception:
                if attempt == 3:
                    raise
                self.page.wait_for_timeout(300)
        return 0

    def get_visible_column_headers(self):
        return self._get_headers_safe(self.TABLE_HEADERS)

    def get_column_values(self, column_name):
        idx = self.COLUMN_INDEX.get(column_name)
        if idx is None:
            return []
        for attempt in range(4):
            try:
                rows = self.page.locator(self.TABLE_ROWS)
                values = []
                for i in range(rows.count()):
                    row = rows.nth(i)
                    tds = row.locator("td")
                    if tds.count() > idx:
                        values.append(tds.nth(idx).inner_text().strip())
                return values
            except Exception:
                if attempt == 3:
                    raise
                self.page.wait_for_timeout(300)
        return []

    def get_first_data_row(self):
        return self._first_visible_data_row(f"#table-{self.TABLE_NAME} tbody tr")

    def sort_by_phone_number(self):
        self._js_click(self.SORT_PHONE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_created_at(self):
        self._js_click(self.SORT_CREATED_AT_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    # ── Filters popover ──────────────────────────────────────────────────────

    def open_filters_popover(self):
        if self._is_visible(self.FILTER_CREATED_AT_INPUT, timeout=1000):
            return
        self._js_click(self.FILTERS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    _DAY_CELLS_CSS = (".flatpickr-calendar.open .flatpickr-day:not(.flatpickr-disabled)"
                       ":not(.prevMonthDay):not(.nextMonthDay)")

    def filter_by_created_date_range(self, from_day_offset=10, to_day_offset=3):
        """TC007: since this is a "Created At" filter, flatpickr disables
        dates after today, so the CURRENT month can have too few enabled
        days to satisfy both offsets (worst case early in a month). Per
        the user's suggestion, this navigates back to the previous
        (fully-elapsed, so entirely-enabled) month first via flatpickr's
        standard "previous month" navigation arrow -- this is a stable
        flatpickr library convention (same as the .flatpickr-day/
        .prevMonthDay/.nextMonthDay classes _DAY_CELLS_CSS already relies
        on above), not app-specific markup that needed to be pasted."""
        self.open_filters_popover()
        el = self.h.wait_for_element_visible(self.FILTER_CREATED_AT_INPUT)
        el.scroll_into_view_if_needed()
        el.click(force=True)
        self.page.wait_for_timeout(500)

        try:
            prev_month_btn = self.page.locator(".flatpickr-calendar.open .flatpickr-prev-month").first
            prev_month_btn.click(force=True)
            self.page.wait_for_timeout(400)
        except Exception:
            pass

        def _click_cell(offset_from_end):
            days = self.page.locator(self._DAY_CELLS_CSS)
            count = days.count()
            if count <= offset_from_end:
                return False
            cell = days.nth(count - offset_from_end - 1)
            try:
                cell.click(force=True)
            except Exception:
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

    def get_filter_created_at_value(self):
        el = self.h.wait_for_element_visible(self.FILTER_CREATED_AT_INPUT)
        return el.get_attribute("value")

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
        """value: 'action' | 'phone-number' | 'department' | 'user' | 'created-at'"""
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
        """Restores the CONFIRMED default column state: action/phone-number/
        created-at checked, department/user unchecked. sessionStorage
        persists column visibility across a plain reload (same gotcha as
        every other Livewire-tables page in this project)."""
        defaults = {"action": True, "phone-number": True, "department": False,
                    "user": False, "created-at": True}
        for value, should_be_checked in defaults.items():
            self.open_columns_dropdown()
            try:
                cb = self.page.locator(f"input[type='checkbox'][value='{value}']").first
            except Exception:
                continue
            try:
                is_checked = cb.is_checked()
            except Exception:
                continue
            if is_checked != should_be_checked:
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
            btn.wait_for(state="attached", timeout=3000)
        except Exception:
            return False
        btn.scroll_into_view_if_needed()
        btn.click(force=True)
        self.page.wait_for_timeout(1000)
        return True

    def confirm_delete(self):
        try:
            btn = self.page.locator(self.CONFIRM_DELETE_BTN).first
            btn.wait_for(state="visible", timeout=10000)
        except Exception:
            return False
        btn.click()
        self.page.wait_for_timeout(1500)
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

    def click_next_page(self):
        self._js_click(self.NEXT_PAGE_BTN + " >> visible=true", timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_next_page_enabled(self):
        """Returns True if the Next Page button exists, is visible, and is not disabled."""
        locators = self.page.locator(self.NEXT_PAGE_BTN).all()
        for loc in locators:
            if loc.is_visible():
                return loc.get_attribute("disabled") is None
        return False

    def is_prev_page_enabled(self):
        """Returns True if the Previous Page button exists, is visible, and is not disabled."""
        locators = self.page.locator(self.PREV_PAGE_BTN).all()
        for loc in locators:
            if loc.is_visible():
                return loc.get_attribute("disabled") is None
        return False


    # ── Add Blocked Number (create page) — best-effort, see module
    # docstring caveat. ──────────────────────────────────────────────────────

    def is_create_page(self):
        return "/blocked-numbers/create" in self.get_current_url()

    def add_blocked_number(self, phone_number):
        self.h.clear_and_type(self.ADD_PHONE_INPUT, phone_number)
        self._js_click(self.ADD_SUBMIT_BTN, timeout=10000)
        # Kept short on purpose: a screen recording of a live TC019 run
        # showed the duplicate-number case's SweetAlert2 error dialog
        # auto-dismisses itself only ~2-3s after appearing, so
        # get_validation_error_text() needs as much of that window left
        # as possible when its polling loop starts. This just gives the
        # request a beat to land before that loop takes over the waiting.
        self.page.wait_for_timeout(300)

    def get_validation_error_text(self):
        """Checks four independent mechanisms this app uses for form
        errors: (1) the inline @error('phone_number') block near the
        field, (2) a WireUI toast notification dispatched via
        wireui:notification, and (3)/(4) a SweetAlert2 error dialog used
        specifically for the duplicate-number case.

        Confirmed via screen recording that the duplicate-number case
        renders via mechanism (3)/(4) -- SweetAlert2, with
        <html class="swal2-shown ..."> and the message text visible --
        but that dialog auto-dismisses itself only ~2-3s after
        appearing. The previous version checked each mechanism in turn
        with its own long timeout (5s, then 4s, then 6s for the
        html-container) before ever confirming the SweetAlert2 dialog,
        so by the time it got there the dialog had already closed
        itself and the run returned None despite the error genuinely
        having fired. Polling all four mechanisms together in one short
        loop instead means whichever one the app actually used gets
        caught while it's still on screen, regardless of order."""
        candidates = (
            self.VALIDATION_ERROR_MSG,
            self.TOAST_NOTIFICATION_TEXT,
            "#swal2-html-container",
            self.SWAL_ERROR_TITLE,
            self.DUPLICATE_POPUP_TEXT,
        )
        end_time = time.time() + 6
        while time.time() < end_time:
            for locator in candidates:
                try:
                    els = self.page.locator(locator)
                    for i in range(els.count()):
                        el = els.nth(i)
                        if el.is_visible():
                            text = el.inner_text().strip()
                            if text:
                                return text
                except Exception:
                    continue
            self.page.wait_for_timeout(200)
            
        # Ultimate fallback for WireUI popups where .first might grab a hidden template
        try:
            body_text = self.page.locator("body").inner_text()
            if "already in the blocked numbers list" in body_text.lower():
                return "This phone number is already in the blocked numbers list."
        except Exception:
            pass
            
        return None

    def click_cancel_on_create_page(self):
        self._js_click(self.ADD_CANCEL_BTN, timeout=10000)
        self.page.wait_for_timeout(1000)

    # ── Upload popup — best-effort, see module docstring caveat. ────────────

    def upload_file(self, file_path):
        file_input = self.page.locator(self.FILE_INPUT).first
        file_input.wait_for(state="attached", timeout=20000)
        self.page.evaluate(
            "(el) => { el.style.display = 'block'; }",
            file_input.element_handle()
        )
        file_input.set_input_files(os.path.abspath(file_path))
        try:
            self.page.locator(self.UPLOAD_LOADER).first.wait_for(state="hidden", timeout=30000)
        except Exception:
            self.page.wait_for_timeout(2000)

    def click_download_sample(self):
        self.h.wait_for_element_clickable(self.BTN_DOWNLOAD_SAMPLE).click()
        self.page.wait_for_timeout(2000)

    def click_upload_confirm(self):
        btn = self.page.locator(self.BTN_UPLOAD_CONFIRM).first
        btn.wait_for(state="visible", timeout=20000)
        btn.click(force=True)
        self.page.wait_for_timeout(2000)

    def click_cancel_upload(self):
        """Uses a JS-driven force click (like _js_click elsewhere in this
        page object) rather than a plain click() -- this Cancel control is
        a <div>, not a native <button>, and a native click risks landing
        on an intercepting overlay/backdrop element instead."""
        self._js_click(self.BTN_CANCEL_UPLOAD, timeout=10000)
        self.page.wait_for_timeout(500)

    def get_upload_error(self):
        if self.is_element_present(self.UPLOAD_ERROR_MSG, timeout=5000):
            return self.h.wait_for_element_visible(self.UPLOAD_ERROR_MSG).inner_text()
        return None

    def get_upload_success(self):
        if self.is_element_present(self.UPLOAD_SUCCESS_MSG, timeout=5000):
            return self.h.wait_for_element_visible(self.UPLOAD_SUCCESS_MSG).inner_text()
        return None

    # ── Logout ───────────────────────────────────────────────────────────────

    def logout(self):
        self._js_click(self.USER_MENU_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)
        self._js_click(self.LOGOUT_LINK, timeout=10000)
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
