from pages.common.base_page import BasePage


class ForgotPasswordPage(BasePage):
    # ── Locators ───────────────────────────────────────────────────────────────
    EMAIL_INPUT   = "input[type='email'], input[name='email']"
    SEND_BUTTON   = "button[type='submit'], input[type='submit']"
    LOGIN_LINK    = "a:text-is('or Login')"
    SUCCESS_MSG   = ".alert-success, [class*='success']"
    ERROR_MSG     = ".alert-danger, [class*='error']"

    # ── Actions ────────────────────────────────────────────────────────────────

    def navigate(self):
        self.open("/forgot-password")
        return self

    def enter_email(self, email):
        self.h.clear_and_type(self.EMAIL_INPUT, email)
        return self

    def click_send_link(self):
        self.h.wait_for_element_clickable(self.SEND_BUTTON).click()
        return self

    def submit_email(self, email):
        self.enter_email(email)
        self.click_send_link()
        return self

    def click_login_link(self):
        self.h.wait_for_element_clickable(self.LOGIN_LINK).click()

    # ── Assertions ─────────────────────────────────────────────────────────────

    def is_forgot_password_page(self):
        return "forgot-password" in self.get_current_url()

    def get_success_message(self):
        if self.is_element_present(self.SUCCESS_MSG, timeout=5000):
            return self.h.wait_for_element_visible(self.SUCCESS_MSG).inner_text()
        return None

    def get_error_message(self):
        if self.is_element_present(self.ERROR_MSG, timeout=5000):
            return self.h.wait_for_element_visible(self.ERROR_MSG).inner_text()
        return None
