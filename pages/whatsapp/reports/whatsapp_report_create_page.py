from pages.common.base_page import BasePage


class WhatsappReportCreatePage(BasePage):

    CREATE_PATH = "/whatsapp/channels/download/center/create"

    # Category constants (actual <option value="...">, confirmed)
    CATEGORY_ALL            = ""
    CATEGORY_MARKETING      = "marketing"
    CATEGORY_MM_LITE        = "mmlite"
    CATEGORY_UTILITY        = "utility"
    CATEGORY_AUTHENTICATION = "authentication"

    # Confirmed default "Select Columns for Export" values (18, all
    # checked by default)
    ALL_COLUMNS = [
        "phone_number", "message_id", "correlation_id", "campaign_name",
        "template_name", "waba_number", "category", "source", "status",
        "submitted_at", "delivered_at", "read_at", "failed_at",
        "failure_reason", "total_clicks", "all_button_types",
        "all_button_values", "all_clicked_at",
    ]

    # --- Form field locators ---

    FORM_TITLE = "xpath=//h2[normalize-space()='Create New Report']"

    # Report Name: unique placeholder
    REPORT_NAME_INPUT = "input[placeholder='e.g., Campaign Report']"

    # Category: the only <select> with an "All Categories" option
    CATEGORY_SELECT = "xpath=//select[.//option[normalize-space()='All Categories']]"

    # Dates: positional -- from_date is first date input, to_date is second
    # (same convention as the SMS/RCS references; do NOT rely on @min/@max
    # since to_date's own max is set but from_date's min could also shift).
    FROM_DATE_INPUT = "xpath=(//input[@type='date'])[1]"
    TO_DATE_INPUT   = "xpath=(//input[@type='date'])[2]"

    # Summary By checkboxes -- disambiguated from the export-columns
    # "status" checkbox via the confirmed ancestor div class ("flex-wrap").
    SUMMARY_BY_SENDER = (  # labeled "WABA Number" in the UI
        "xpath=//div[contains(@class,'flex-wrap')]//input[@type='checkbox' and @value='sender']"
    )
    SUMMARY_BY_STATUS = "xpath=//div[contains(@class,'flex-wrap')]//input[@type='checkbox' and @value='status']"

    # Notify email input + Add button (confirmed type="button", so it
    # cannot be confused with the type="submit" Generate button)
    EMAIL_INPUT   = "input[type='email'][placeholder='Enter email address']"
    BTN_ADD_EMAIL = "xpath=//button[@type='button' and normalize-space()='Add']"

    # Summary Only toggle (label click toggles the hidden checkbox)
    SUMMARY_ONLY_LABEL = "label[for='summary_only']"
    SUMMARY_ONLY_INPUT = "#summary_only"

    # Include Message Content toggle
    INCLUDE_MSG_LABEL = "label[for='exclude_message_data']"
    INCLUDE_MSG_INPUT = "#exclude_message_data"

    # Export-columns checkboxes -- disambiguated via the confirmed
    # "grid grid-cols-2" ancestor (the "status" value also exists under
    # Summary By above, hence the ancestor scoping).
    COLUMN_CHECKBOX_BY_VALUE_XPATH = (
        "xpath=//div[contains(@class,'grid-cols-2')]"
        "//input[@type='checkbox' and @value='{value}']"
    )

    # Generate / Cancel
    BTN_GENERATE = "xpath=//button[@type='submit']"
    BTN_CANCEL   = (
        "xpath=//a[contains(normalize-space(),'Cancel')]"
        "[contains(@href,'download/center')]"
    )

    # Success/error feedback (unconfirmed -- kept for parity with the SMS
    # reference; is_success() primarily relies on the URL redirect check)
    SUCCESS_INDICATOR = (
        "xpath=//*[contains(translate(.,'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),"
        "              'SUCCESS') or"
        "    contains(translate(.,'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),"
        "              'QUEUED') or"
        "    contains(translate(.,'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),"
        "              'CREATED')]"
    )

    # -------------------------------------------------------------------------
    # Navigation
    # -------------------------------------------------------------------------

    def navigate(self):
        self.open(self.CREATE_PATH)
        self.page.wait_for_timeout(1500)

    def is_create_page(self):
        return "create" in self.get_current_url().lower()

    def wait_for_form_load(self, timeout=15000):
        try:
            self.page.locator(self.BTN_GENERATE).first.wait_for(state="attached", timeout=timeout)
            self.page.wait_for_timeout(500)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Field setters
    # -------------------------------------------------------------------------

    def set_report_name(self, name):
        try:
            inp = self.h.wait_for_element_clickable(self.REPORT_NAME_INPUT, timeout=8000)
            inp.fill("")
            inp.fill(name)
        except Exception:
            pass

    def set_category(self, value):
        """value: '' | 'marketing' | 'mmlite' | 'utility' | 'authentication'"""
        try:
            self.h.wait_for_element_clickable(self.CATEGORY_SELECT, timeout=8000)
            self.h.select_option(self.CATEGORY_SELECT, value=value)
        except Exception:
            try:
                self.page.evaluate(
                    "(v) => { window.Livewire && window.Livewire.all().forEach(function(c) {"
                    "  try { c.set('category', v); } catch(e) {}"
                    "}); }",
                    value
                )
            except Exception:
                pass
        self.page.wait_for_timeout(300)

    def _set_date_input(self, locator, date_str, livewire_key):
        """
        Set a native <input type="date"> to date_str (YYYY-MM-DD).
        Same strategy as the SMS/RCS references: JS value-set + dispatch
        input/change events (locale-proof), then a Livewire JS API
        fallback.
        """
        try:
            inp = self.page.locator(locator).first
            inp.wait_for(state="attached", timeout=8000)
            inp.evaluate(
                "(el, v) => { el.value = v; "
                "el.dispatchEvent(new Event('input', {bubbles: true})); "
                "el.dispatchEvent(new Event('change', {bubbles: true})); }",
                date_str
            )
            self.page.wait_for_timeout(300)
        except Exception:
            pass

        try:
            self.page.evaluate(
                "([key, v]) => { if (window.Livewire) { "
                "window.Livewire.all().forEach(function(c) {"
                "  try { c.set(key, v); } catch(e) {}"
                "}); } }",
                [livewire_key, date_str]
            )
            self.page.wait_for_timeout(300)
        except Exception:
            pass

    def set_from_date(self, date_str):
        """date_str: 'YYYY-MM-DD'."""
        self._set_date_input(self.FROM_DATE_INPUT, date_str, "from_date")

    def set_to_date(self, date_str):
        """date_str: 'YYYY-MM-DD'."""
        self._set_date_input(self.TO_DATE_INPUT, date_str, "to_date")

    def set_summary_by(self, include_waba=True, include_status=True):
        """Set Summary By checkboxes ('WABA Number' [value=sender] / 'Status')."""
        for locator, should_check in [
            (self.SUMMARY_BY_SENDER, include_waba),
            (self.SUMMARY_BY_STATUS, include_status),
        ]:
            try:
                cb = self.page.locator(locator).first
                cb.wait_for(state="attached", timeout=5000)
                is_checked = cb.is_checked()
                if is_checked != should_check:
                    cb.click(force=True)
                    self.page.wait_for_timeout(200)
            except Exception:
                pass

    def add_notify_email(self, email):
        """Add one email to the notify list."""
        try:
            inp = self.h.wait_for_element_clickable(self.EMAIL_INPUT, timeout=5000)
            inp.fill("")
            inp.fill(email)
            btn = self.h.wait_for_element_clickable(self.BTN_ADD_EMAIL, timeout=5000)
            btn.click(force=True)
            self.page.wait_for_timeout(500)
        except Exception:
            pass

    def set_summary_only(self, enabled=True):
        """Toggle the Summary Only switch."""
        try:
            inp = self.page.locator(self.SUMMARY_ONLY_INPUT).first
            is_checked = inp.is_checked()
            if is_checked != enabled:
                lbl = self.h.wait_for_element_clickable(self.SUMMARY_ONLY_LABEL, timeout=5000)
                lbl.click(force=True)
                self.page.wait_for_timeout(500)
        except Exception:
            pass

    def set_include_message_content(self, enabled=True):
        """Toggle the Include Message Content switch."""
        try:
            inp = self.page.locator(self.INCLUDE_MSG_INPUT).first
            is_checked = inp.is_checked()
            if is_checked != enabled:
                lbl = self.h.wait_for_element_clickable(self.INCLUDE_MSG_LABEL, timeout=5000)
                lbl.click(force=True)
                self.page.wait_for_timeout(500)
        except Exception:
            pass

    def select_column(self, column_value):
        """Check a specific export column checkbox (by value attribute)."""
        try:
            xpath = self.COLUMN_CHECKBOX_BY_VALUE_XPATH.format(value=column_value)
            cb = self.page.locator(xpath).first
            if not cb.is_checked():
                cb.click(force=True)
                self.page.wait_for_timeout(100)
        except Exception:
            pass

    def deselect_all_columns(self):
        """Uncheck every export-column checkbox."""
        try:
            cbs = self.page.locator("xpath=//div[contains(@class,'grid-cols-2')]//input[@type='checkbox']")
            for i in range(cbs.count()):
                cb = cbs.nth(i)
                if cb.is_checked():
                    cb.click(force=True)
            self.page.wait_for_timeout(200)
        except Exception:
            pass

    def get_column_checkbox_state(self, column_value):
        """Return True if the export-columns checkbox for this value is checked."""
        try:
            xpath = self.COLUMN_CHECKBOX_BY_VALUE_XPATH.format(value=column_value)
            return self.page.locator(xpath).first.is_checked()
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # Submission
    # -------------------------------------------------------------------------

    def submit(self):
        """Click Generate Report."""
        try:
            self._js_click(self.BTN_GENERATE, timeout=10000)
            self.page.wait_for_timeout(2500)
        except Exception:
            pass

    def cancel(self):
        """Click Cancel link -- navigates back to Download Center."""
        try:
            self._js_click(self.BTN_CANCEL, timeout=8000)
            self.page.wait_for_timeout(1500)
        except Exception:
            pass

    def is_success(self):
        """Return True if a success notification / redirect back occurred."""
        url = self.get_current_url()
        if "download/center" in url and "create" not in url:
            return True
        try:
            els = self.page.locator(self.SUCCESS_INDICATOR)
            for i in range(els.count()):
                if els.nth(i).is_visible():
                    return True
            return False
        except Exception:
            return False

    def get_validation_errors(self):
        """Return list of visible validation error texts (unconfirmed
        locator pattern -- no error DOM was captured in this dump)."""
        try:
            errs = self.page.locator(
                "xpath=//*[contains(@class,'text-red') or contains(@class,'error')]"
                "[normalize-space()]"
            )
            result = []
            for i in range(errs.count()):
                text = errs.nth(i).inner_text().strip()
                if text:
                    result.append(text)
            return result
        except Exception:
            return []
