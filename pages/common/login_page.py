from pages.common.base_page import BasePage


class LoginPage(BasePage):
    # ── Locators (Playwright selector strings; "xpath=" prefix for XPath) ───────
    EMAIL_INPUT    = "input[type='email'], input[name='email'], input[placeholder*='mail' i]"
    PASSWORD_INPUT = "input[type='password']"
    LOGIN_BUTTON   = (
        "xpath=//button[@type='submit'] | //input[@type='submit'] "
        "| //button[contains(text(),'Login')] | //button[contains(text(),'Sign In')]"
    )
    FORGOT_LINK    = "a:text-is('Forgot Password?')"
    ERROR_MESSAGE  = ".alert-danger, .error, [class*='error'], [class*='alert']"
    LOGO           = "img[alt*='Logo' i], img[src*='logo' i]"

    # ── Actions ────────────────────────────────────────────────────────────────

    def navigate(self):
        self.open("/login")
        return self

    def enter_email(self, email):
        self.h.clear_and_type(self.EMAIL_INPUT, email)
        return self

    def enter_password(self, password):
        self.h.clear_and_type(self.PASSWORD_INPUT, password)
        return self

    def click_login(self):
        btn = self.h.wait_for_element_clickable(self.LOGIN_BUTTON)
        btn.click()
        return self

    def login(self, email, password):
        self.enter_email(email)
        self.enter_password(password)
        self.click_login()
        return self

    def click_forgot_password(self):
        self.h.wait_for_element_clickable(self.FORGOT_LINK).click()

    # ── Assertions ─────────────────────────────────────────────────────────────

    def is_login_page(self):
        return "login" in self.get_current_url()

    def get_error_message(self):
        if self.is_element_present(self.ERROR_MESSAGE, timeout=5000):
            # inner_text() (not text_content()) to match Selenium's .text
            # semantics: rendered, visible-only text.
            return self.h.wait_for_element_visible(self.ERROR_MESSAGE).inner_text()
        return None

    def is_logo_displayed(self):
        return self.is_element_present(self.LOGO)

    def is_email_field_present(self):
        return self.is_element_present(self.EMAIL_INPUT)

    def is_password_field_present(self):
        return self.is_element_present(self.PASSWORD_INPUT)

    def is_login_button_present(self):
        return self.is_element_present(self.LOGIN_BUTTON)
