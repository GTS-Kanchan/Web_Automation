import time

from pages.common.base_page import BasePage


class SmsBlockedKeywordsPage(BasePage):
    """SMS → Blocked Keywords (opt-out keywords) page object.

    Modeled on pages/sms/sms_blocked_numbers_page.py (same Livewire
    listing-page conventions: laravel-livewire-tables, WireUI toasts,
    $wireui.confirmAction -> SweetAlert2 delete confirmation, a Filters
    popover, a Columns dropdown keyed by `{TABLE_NAME}-columnSelect-`).

    Confirmed from the live page (URL, screenshots, and full HTML dump of
    /channels/sms/blocked-keywords the user provided):
      - REPORT_URL, TABLE_NAME ("sms_optout_keywords")
      - Columns present: Action, Keyword, Status, Created at, Updated at
      - "Add Keyword" opens a MODAL in-place (Livewire.dispatch('openModal',
        {component: 'sms.optoutkeyword.create'})) -- unlike Blocked Numbers,
        which navigates to a separate /create page.
      - The Filters popover has a single Status <select> (wire:model.live on
        a `filterComponents.status`-style binding) with options
        All / Active / Inactive.
      - Row delete reuses the same $wireui.confirmAction -> SweetAlert2
        mechanism as every other listing page in this app (confirmed
        dispatch params reference OptOutKeyword's model class), so the
        generic DELETE_ICON_IN_ROW / CONFIRM_DELETE_BTN / CANCEL_DELETE_BTN
        locators already proven on Blocked Numbers/Sender ID/Contacts/Tags
        are reused as-is.

    NOT independently re-confirmed in this pass (best-effort, same caveat
    style as sms_blocked_numbers_page.py's Add/Upload sections): the exact
    modal field id/name for the Keyword input, and the exact validation-
    error markup for a duplicate/empty keyword. get_column_values() below
    resolves column position by HEADER TEXT rather than a hardcoded index,
    specifically so it does not depend on a guessed/confirmed column order.
    """

    REPORT_URL = "/channels/sms/blocked-keywords"
    TABLE_NAME = "sms_optout_keywords"

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'Blocked Keyword')]"

    # ── Top action button ───────────────────────────────────────────────────
    ADD_KEYWORD_BTN = (
        "xpath=//button[contains(normalize-space(.),'Add Keyword')] "
        "| //a[contains(normalize-space(.),'Add Keyword')]"
    )
    MODAL_CONTAINER = "#modal-container"

    # ── Search ───────────────────────────────────────────────────────────────
    SEARCH_BOX = "input[wire\\:model\\.live='search']"

    # ── Filters popover (Status: All / Active / Inactive) ──────────────────
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')]"
    STATUS_FILTER_SELECT = (
        "select[wire\\:model\\.live*='status'], select[wire\\:model*='status']"
    )

    # ── Columns dropdown ─────────────────────────────────────────────────────
    COLUMNS_BUTTON = "xpath=//button[contains(normalize-space(.),'Columns')]"
    COLUMN_CHECKBOXES = (
        f"xpath=//div[contains(@*[name()='wire:key'],'{TABLE_NAME}-columnSelect-') and "
        f"not(contains(@*[name()='wire:key'],'columnSelect-selectAll'))]//input[@type='checkbox']"
    )

    # ── Table ────────────────────────────────────────────────────────────────
    TABLE = f"#table-{TABLE_NAME}"
    TABLE_HEADERS = f"#table-{TABLE_NAME} thead th"
    TABLE_ROWS = f"#table-{TABLE_NAME} tbody tr"
    # Same case-insensitive-substring convention as sms_blocked_numbers_page.py
    # (that page's own comment documents this app's empty-state text does NOT
    # reliably match a single exact phrase across listing pages).
    NO_RECORDS_MSG = (
        "xpath=//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no items found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no record') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no data') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no result') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'not found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'nothing found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no keyword')]"
    )

    # ── Delete (row) — identical $wireui.confirmAction -> SweetAlert2
    # convention already used on blocked_numbers/contacts/tags. ──────────────
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

    # ── Add Keyword modal — best-effort (see module docstring caveat) ───────
    # Keyword input: try several plausible wire:model bindings/name/id/
    # placeholder combinations rather than a single guessed id, since this
    # field's exact markup was not independently re-confirmed.
    KEYWORD_INPUT = (
        "#keyword, input[wire\\:model='keyword'], input[wire\\:model\\.defer='keyword'], "
        "input[name='keyword']"
    )
    MODAL_SAVE_BTN = (
        "xpath=//div[@id='modal-container']//button[@type='submit'] "
        "| //div[@id='modal-container']//button[contains(normalize-space(.),'Save') "
        "or contains(normalize-space(.),'Add')]"
    )
    MODAL_CANCEL_BTN = (
        "xpath=//div[@id='modal-container']//button[contains(normalize-space(.),'Cancel')] "
        "| //div[@id='modal-container']//a[contains(normalize-space(.),'Cancel')]"
    )
    # Same multi-mechanism validation-error convention as
    # sms_blocked_numbers_page.py's get_validation_error_text(): an inline
    # @error() block, a WireUI toast, and a SweetAlert2 dialog are all
    # checked together in one short polling loop (order-independent),
    # scoped to the modal where possible to reduce false positives.
    VALIDATION_ERROR_MSG = (
        "xpath=//div[@id='modal-container']"
        "//*[(contains(@class,'text-red-500') or contains(@class,'text-red-600')) "
        "and normalize-space(text())!='*' and normalize-space(text())!='']"
    )
    TOAST_NOTIFICATION_TEXT = (
        "xpath=//div[@x-data='wireui_notifications']"
        "//p[(@x-show='notification.title' or @x-show='notification.description') "
        "and normalize-space(text())!='']"
    )
    SWAL_ERROR_TITLE = "#swal2-title"

    # ── User menu / logout (global header, confirmed identical app-wide) ────
    USER_MENU_BUTTON = "xpath=//button[contains(@class,'rounded-full') and .//img]"
    LOGOUT_LINK = "xpath=//a[@title='Log out']"

    # ── Navigation / page state ─────────────────────────────────────────────

    def navigate_to_report(self):
        self.open(self.REPORT_URL)
        self.page.wait_for_timeout(2000)
        return self

    def navigate(self):
        """Navigates to the SMS Blocked Keywords page."""
        self.open(self.REPORT_URL)
        self.page.wait_for_timeout(2000)
        return self

    def is_report_page(self):
        url = self.get_current_url()
        return "/channels/sms/blocked-keywords" in url and "login" not in url.lower()

    def get_page_title_text(self):
        el = self.h.wait_for_element_visible(self.PAGE_TITLE)
        return el.inner_text().strip()

    def _js_click(self, locator, timeout=10000):
        return self.h.js_click(locator, timeout=timeout)

    def _is_visible(self, locator, timeout=1000):
        try:
            el = self.page.locator(locator).first
            el.wait_for(state="attached", timeout=timeout)
            return el.is_visible()
        except Exception:
            return False

    # ── Search ───────────────────────────────────────────────────────────────

    def search(self, value):
        """Same JS-driven single 'input' dispatch as
        sms_blocked_numbers_page.py.search() -- avoids a race with
        wire:model.live's per-keystroke request that plain fill()/type()
        can trigger."""
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
        self.page.wait_for_timeout(1500)

    def clear_search(self):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.evaluate(
            """(el) => {
                el.value = '';
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
            }"""
        )
        self.page.wait_for_timeout(1500)

    # ── Table / rows ─────────────────────────────────────────────────────────

    @staticmethod
    def _is_empty_state_row(tds):
        """Same rappasoft/laravel-livewire-tables structural empty-state
        detection as sms_blocked_numbers_page.py: a genuinely empty result
        set renders as a single <tr> with one <td colspan="N">."""
        return tds.count() == 1 and tds.nth(0).get_attribute("colspan")

    def has_records(self):
        return self.is_element_present(self.TABLE_ROWS, timeout=5000) and self.get_row_count() > 0

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

    def _header_index(self, header_label):
        """Resolve a column's position by its HEADER TEXT (case-insensitive
        substring match) rather than a hardcoded index -- this page's
        column order was not independently re-confirmed, and toggling
        columns via the Columns dropdown shifts indices anyway (same
        caveat sms_blocked_numbers_page.py documents for COLUMN_INDEX)."""
        headers = self.get_visible_column_headers()
        target = header_label.strip().lower()
        for i, h in enumerate(headers):
            if target in h.strip().lower():
                return i
        return None

    def get_column_values(self, header_label):
        idx = self._header_index(header_label)
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

    def is_keyword_present_in_list(self, keyword: str) -> bool:
        """Exact <td> match, same strategy as
        SMSSenderIDPage.is_sender_id_present_in_list(): hard-return to the
        list, check the first page, then narrow via search and check
        again. Never falls back to has_records() (that would pass for ANY
        rows, not specifically this keyword)."""
        self.navigate_to_report()
        by_td = f"xpath=//td[normalize-space()='{keyword}']"
        if self.is_element_present(by_td, timeout=5000):
            return True
        try:
            self.search(keyword)
            found = self.is_element_present(by_td, timeout=5000)
            self.clear_search()
            return found
        except Exception:
            return False

    # ── Filters popover (Status) ────────────────────────────────────────────

    def open_filters_popover(self):
        if self._is_visible(self.STATUS_FILTER_SELECT, timeout=1000):
            return
        self._js_click(self.FILTERS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def filter_by_status(self, label):
        """label: 'All' | 'Active' | 'Inactive' (matched by visible option
        text, not by a guessed underlying value, so this is resilient to
        the select using e.g. '1'/'0' or 'active'/'inactive' as values)."""
        self.open_filters_popover()
        select = self.h.wait_for_element_visible(self.STATUS_FILTER_SELECT)
        select.select_option(label=label)
        self.page.wait_for_timeout(1500)

    # ── Columns dropdown ─────────────────────────────────────────────────────

    def open_columns_dropdown(self):
        if self._is_visible(self.COLUMN_CHECKBOXES, timeout=1000):
            return
        self._js_click(self.COLUMNS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    # ── Add Keyword (modal) ──────────────────────────────────────────────────

    def click_add_keyword(self):
        """Clicks the 'Add Keyword' button."""
        try:
            self._js_click(self.ADD_KEYWORD_BTN, timeout=10000)
        except Exception as e:
            with open("tc014_fail.html", "w", encoding="utf-8") as f:
                f.write(self.page.content())
            raise e
        self.page.wait_for_timeout(1000)

    def is_add_keyword_modal_open(self):
        return self.is_element_present(self.KEYWORD_INPUT, timeout=8000)

    def add_keyword(self, keyword):
        inp = self.h.clear_and_type(self.KEYWORD_INPUT, keyword)
        try:
            inp.evaluate("(el) => { el.dispatchEvent(new Event('input',{bubbles:true})); el.dispatchEvent(new Event('change',{bubbles:true})); }")
        except Exception:
            pass
        self.page.wait_for_timeout(1000)  # Wait for Livewire sync
        btn = self.page.locator(self.MODAL_SAVE_BTN).first
        btn.wait_for(state="visible", timeout=5000)
        btn.click(force=True)
        self.page.wait_for_timeout(3000)

    def click_cancel_on_add_modal(self):
        btn = self.page.locator(self.MODAL_CANCEL_BTN).first
        btn.wait_for(state="visible", timeout=5000)
        btn.click(force=True)
        self.page.wait_for_timeout(1000)

    def get_validation_error_text(self):
        """Polls the inline modal error / toast / SweetAlert2 mechanisms
        together in one short loop -- same rationale as
        sms_blocked_numbers_page.py.get_validation_error_text(): whichever
        mechanism the app actually used gets caught regardless of order or
        how quickly it auto-dismisses."""
        candidates = (
            self.VALIDATION_ERROR_MSG,
            self.TOAST_NOTIFICATION_TEXT,
            "#swal2-html-container",
            self.SWAL_ERROR_TITLE,
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
                            if text and "success" not in text.lower():
                                return text
                except Exception:
                    continue
            self.page.wait_for_timeout(500)
        return None

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

    def is_success_toast_shown(self):
        try:
            els = self.page.locator(self.TOAST_NOTIFICATION_TEXT)
            for i in range(els.count()):
                el = els.nth(i)
                if el.is_visible() and el.inner_text().strip():
                    return True
        except Exception:
            pass
        return False

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
