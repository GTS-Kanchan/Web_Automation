from pages.common.base_page import BasePage


class RcsErrorCodesPage(BasePage):

    REPORT_URL = "/rcs/error-codes"
    TABLE_NAME = "smpp_error_codes"

    # Confirmed column order (same as SMS equivalent)
    COLUMN_INDEX = {"name": 0, "code": 1, "description": 2}

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'RCS Error Codes')]"
    BREADCRUMB = "nav[aria-label='Breadcrumb']"

    # ── Search ───────────────────────────────────────────────────────────────
    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search']"

    # ── Sorting ──────────────────────────────────────────────────────────────
    # Use @*[name()='wire:click'] to avoid Chrome's XPath namespace error
    SORT_NAME_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('name')\")]"
    SORT_CODE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('code')\")]"
    # CONFIRMED absent — description column has no sort control at all
    SORT_DESCRIPTION_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('description')\")]"

    # ── Columns dropdown ─────────────────────────────────────────────────────
    COLUMNS_BUTTON = "xpath=//button[contains(normalize-space(.),'Columns')]"
    COLUMN_CHECKBOXES = (
        "xpath=//div[contains(@*[name()='wire:key'],'smpp_error_codes-columnSelect-') and "
        "not(contains(@*[name()='wire:key'],'columnSelect-selectAll'))]//input[@type='checkbox']"
    )
    SELECT_ALL_COLUMNS_CHECKBOX = (
        "xpath=//div[contains(@*[name()='wire:key'],'smpp_error_codes-columnSelect-selectAll-')]//input[@type='checkbox']"
    )

    # ── Table ────────────────────────────────────────────────────────────────
    TABLE = "#table-smpp_error_codes"
    TABLE_HEADERS = "#table-smpp_error_codes thead th"
    TABLE_ROWS = "#table-smpp_error_codes tbody tr"
    NO_RECORDS_MSG = (
        "xpath=//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no items found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no record') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no data') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no result')]"
    )

    # ── Pagination ───────────────────────────────────────────────────────────
    PAGINATION_RESULTS_TEXT = ".paged-pagination-results"
    NEXT_PAGE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"nextPage('page')\")]"

    # ── User menu / logout ──────────────────────────────────────────────────
    USER_MENU_BUTTON = "xpath=//button[contains(@class,'rounded-full') and .//img]"
    LOGOUT_LINK = "xpath=//a[@title='Log out']"

    # ── Navigation / page state ─────────────────────────────────────────────

    def navigate_to_report(self):
        self.open(self.REPORT_URL)
        self.page.wait_for_timeout(2000)
        return self

    def is_report_page(self):
        url = self.get_current_url()
        return "/rcs/error-codes" in url and "login" not in url.lower()

    def get_page_title_text(self):
        return self.h.wait_for_element_visible(self.PAGE_TITLE).inner_text().strip()

    def get_breadcrumb_text(self):
        return " ".join(self.h.wait_for_element_visible(self.BREADCRUMB).inner_text().split())

    def _is_visible(self, locator, timeout=1000):
        try:
            return self.page.locator(locator).first.is_visible()
        except Exception:
            return False

    # ── Search ───────────────────────────────────────────────────────────────

    def _wait_for_search_to_settle(self, timeout_ms=8000):
        """Poll (row_count, no_records_message_present) until two consecutive
        reads agree — same fix as sms_error_codes_page.py to guard against
        the Livewire wire:model.live per-keystroke race."""
        last_state = [None]

        def _stable():
            current = self.get_row_count()
            no_msg = self.is_element_present(self.NO_RECORDS_MSG, timeout=500)
            state = (current, no_msg)
            if state == last_state[0]:
                return True
            last_state[0] = state
            return False

        self.h.wait_until(_stable, timeout_ms=timeout_ms, interval_ms=600)

    def search(self, value):
        """Sets the full value in one fill() call — same intent as the
        Selenium suite's single JS-driven 'input' dispatch (avoid
        out-of-order responses from wire:model.live per-keystroke
        requests); Playwright's fill() already sets the value and dispatches
        input/change events in one native action rather than per-keystroke."""
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.fill(value)
        self.page.wait_for_timeout(500)
        self._wait_for_search_to_settle()
        self.page.wait_for_timeout(300)

    def clear_search(self):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.fill("")
        self.page.wait_for_timeout(500)
        self._wait_for_search_to_settle()
        self.page.wait_for_timeout(300)
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
        rows = self.page.locator(self.TABLE_ROWS)
        count = 0
        for i in range(rows.count()):
            tds = rows.nth(i).locator("td")
            if tds.count() == 0:
                continue
            if any(t.strip() for t in tds.all_inner_texts()):
                count += 1
        return count

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

    def sort_by_name(self):
        self._js_click(self.SORT_NAME_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_code(self):
        self._js_click(self.SORT_CODE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def has_description_sort_control(self):
        """CONFIRMED absent from the live DOM — Description is not sortable.
        Returns False. Kept as a method so the test documents *why* it is
        checking for absence (same pattern as sms_error_codes_page.py)."""
        return self.is_element_present(self.SORT_DESCRIPTION_BTN, timeout=2000)

    # ── Columns dropdown ─────────────────────────────────────────────────────

    def open_columns_dropdown(self):
        if self._is_visible(self.COLUMN_CHECKBOXES, timeout=1000):
            return
        self._js_click(self.COLUMNS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def toggle_column(self, value):
        """value: 'name' | 'code' | 'description'

        Polls get_visible_column_headers() until the header actually flips
        to the expected state before returning — same timing hardening as
        sms_error_codes_page.py to avoid reading the stale header list
        during Livewire's async re-render."""
        self.open_columns_dropdown()
        cb = self.h.wait_for_element_visible(f"input[type='checkbox'][value='{value}']")
        was_checked = cb.is_checked()
        cb.scroll_into_view_if_needed()
        cb.click(force=True)

        expect_present = not was_checked

        def _flipped():
            headers = [h.lower() for h in self.get_visible_column_headers()]
            return (value in headers) == expect_present

        if not self.h.wait_until(_flipped, timeout_ms=6000, interval_ms=300):
            self.page.wait_for_timeout(500)

    def is_column_checked(self, value):
        self.open_columns_dropdown()
        try:
            return self.page.locator(f"input[type='checkbox'][value='{value}']").first.is_checked()
        except Exception:
            return None

    def restore_all_columns(self):
        """Ensures name/code/description are all checked — used in test
        teardown after hide-column tests. Waits for each header to actually
        reappear rather than using a fixed sleep (same fix as
        sms_error_codes_page.py)."""
        for value in ("name", "code", "description"):
            self.open_columns_dropdown()
            try:
                cb = self.page.locator(f"input[type='checkbox'][value='{value}']").first
                cb.wait_for(state="attached", timeout=3000)
            except Exception:
                continue
            if not cb.is_checked():
                cb.scroll_into_view_if_needed()
                cb.click(force=True)

                def _restored(value=value):
                    headers = [h.lower() for h in self.get_visible_column_headers()]
                    return value in headers

                if not self.h.wait_until(_restored, timeout_ms=6000, interval_ms=300):
                    self.page.wait_for_timeout(500)

    # ── Pagination ───────────────────────────────────────────────────────────

    def get_pagination_results_text(self):
        return self.h.wait_for_element_visible(self.PAGINATION_RESULTS_TEXT).inner_text().strip()

    def click_next_page(self):
        self._js_click(self.NEXT_PAGE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    # ── Security helpers ──────────────────────────────────────────────────────

    def search_expect_no_dialog(self, value):
        """Search for `value` while watching for a native alert/confirm/
        prompt dialog (used by the XSS-safety test). Returns the dialog's
        message if a script somehow triggered one, or None if the payload
        was safely treated as plain text — see Helpers.expect_no_dialog for
        why this replaces Selenium's reactive switch_to.alert check."""
        return self.h.expect_no_dialog(lambda: self.search(value))

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
                "() => window.performance.timing.loadEventEnd - window.performance.timing.navigationStart"
            )
        except Exception:
            return None
