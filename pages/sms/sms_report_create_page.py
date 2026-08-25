from pages.common.base_page import BasePage


class SMSReportCreatePage(BasePage):

    CREATE_PATH = "/channels/sms/download/center/create"

    # Product type constants (actual <option value="...">)
    TYPE_ALL          = ""
    TYPE_PROMOTIONAL  = "P"
    TYPE_TRANSACTIONAL = "T"
    TYPE_OTP          = "O"

    # Available column values
    ALL_COLUMNS = [
        "phone_number", "message_id", "correlation_id", "campaign_name",
        "dlt_template_id", "units", "sender_name", "entity_id", "is_unicode",
        "product_type", "source", "status", "created_at", "submitted_at",
        "dlr_received_at", "status_description", "url_tracking",
    ]

    # --- Form field locators ---

    # Report Name: unique placeholder
    REPORT_NAME_INPUT = "input[placeholder='e.g., Report Name']"

    # Product Type: the only <select> that has an "All Types" option
    PRODUCT_TYPE_SELECT = (
        "xpath=//select[.//option[normalize-space()='All Types'] and"
        "         .//option[normalize-space()='Promotional']]"
    )

    # Dates: positional — from_date is first date input, to_date is second.
    # Do NOT use @min/@max to distinguish: to_date can also gain @min dynamically
    # after the user picks a from_date (Livewire sets it as a constraint).
    FROM_DATE_INPUT = "xpath=(//input[@type='date'])[1]"
    TO_DATE_INPUT   = "xpath=(//input[@type='date'])[2]"

    # Summary By checkboxes
    SUMMARY_BY_SENDER = "xpath=//input[@type='checkbox' and @value='sender']"
    SUMMARY_BY_STATUS = "xpath=//input[@type='checkbox' and @value='status']"

    # Notify email input + Add button
    EMAIL_INPUT   = "input[placeholder='Enter email address']"
    BTN_ADD_EMAIL = "xpath=//button[normalize-space()='Add'][not(ancestor::table)]"

    # Summary Only toggle (label clicks the hidden checkbox)
    SUMMARY_ONLY_LABEL   = "label[for='summary_only']"
    SUMMARY_ONLY_INPUT   = "#summary_only"

    # Include Message Content toggle
    INCLUDE_MSG_LABEL = "label[for='exclude_message_data']"
    INCLUDE_MSG_INPUT = "#exclude_message_data"

    # Generate / Cancel
    BTN_GENERATE = "xpath=//button[@type='submit' and contains(.,'Generate')]"
    BTN_CANCEL   = (
        "xpath=//a[contains(normalize-space(),'Cancel')]"
        "[contains(@href,'download/center')]"
    )

    # Success/error feedback
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

    def set_product_type(self, value):
        """value: '' | 'P' | 'T' | 'O'"""
        try:
            self.h.wait_for_element_clickable(self.PRODUCT_TYPE_SELECT, timeout=8000)
            self.h.select_option(self.PRODUCT_TYPE_SELECT, value=value)
        except Exception:
            try:
                self.page.evaluate(
                    "(v) => { window.Livewire && window.Livewire.all().forEach(function(c) {"
                    "  try { c.set('type', v); } catch(e) {}"
                    "}); }",
                    value
                )
            except Exception:
                pass
        self.page.wait_for_timeout(300)

    def _set_date_input(self, locator, date_str, livewire_key):
        """
        Set a native <input type="date"> to date_str (YYYY-MM-DD).

        Strategy (in priority order):
          1. JS: element.value = ISO string + dispatch input/change events.
             This bypasses locale-specific key-entry (DD-MM-YYYY on Indian locale
             turns typing "2026-07-04" into "20-02-0704").
          2. Livewire JS API fallback (c.set(key, value)) in case the field is
             fully controlled by Livewire and JS DOM events aren't enough.
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

        # Livewire API fallback
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
        """date_str: 'YYYY-MM-DD'.  Sets from_date field via JS to avoid locale issues."""
        self._set_date_input(self.FROM_DATE_INPUT, date_str, "from_date")

    def set_to_date(self, date_str):
        """date_str: 'YYYY-MM-DD'.  Sets to_date field via JS to avoid locale issues."""
        self._set_date_input(self.TO_DATE_INPUT, date_str, "to_date")

    def set_summary_by(self, include_sender=True, include_status=True):
        """Set Summary By checkboxes."""
        for locator, should_check in [
            (self.SUMMARY_BY_SENDER, include_sender),
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
            cb = self.page.locator(
                f"xpath=//input[@type='checkbox' and @value='{column_value}']"
                f"[ancestor::div[contains(@class,'grid')]]"
            ).first
            if not cb.is_checked():
                cb.click(force=True)
                self.page.wait_for_timeout(100)
        except Exception:
            pass

    def deselect_all_columns(self):
        """Uncheck every column checkbox."""
        try:
            cbs = self.page.locator(
                "xpath=//input[@type='checkbox']"
                "[ancestor::div[contains(@class,'grid')]]"
            )
            for i in range(cbs.count()):
                cb = cbs.nth(i)
                if cb.is_checked():
                    cb.click(force=True)
            self.page.wait_for_timeout(200)
        except Exception:
            pass

    def get_column_checkbox_state(self, column_value):
        """Return True if column checkbox is checked."""
        try:
            cb = self.page.locator(f"xpath=//input[@type='checkbox' and @value='{column_value}']").first
            return cb.is_checked()
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
        """Click Cancel link — navigates back to Download Center."""
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
        """Return list of visible validation error texts."""
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
