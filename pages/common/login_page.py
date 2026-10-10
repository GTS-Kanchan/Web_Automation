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

    # Fields are bound to the Livewire component via wire:model, which only
    # starts listening once Livewire's own JS has hydrated the page.
    # navigate() -> BasePage.open() uses wait_until="domcontentloaded", which
    # fires as soon as the HTML is parsed -- before that hydration completes.
    # Under normal single-worker load there's usually enough incidental delay
    # between navigate() and login() for hydration to finish, but under
    # PLAYWRIGHT_WORKERS-driven CPU/network contention (seen in a real
    # mid-run re-authentication) fill() can land in that race window: the
    # DOM shows the typed value for a moment, but Livewire's component never
    # saw an input event, so the server receives an empty field. The app
    # correctly reports "Invalid credentials" for that empty submission and
    # Livewire's re-render then wipes the DOM back to its (empty) bound
    # state -- which is exactly what a real failure screenshot showed, with
    # both fields empty under an "Invalid credentials." message.
    #
    # Fix: verify each field's actual DOM value after fill() and retry a
    # bounded number of times before giving up, instead of trusting a single
    # fill() call blindly. This closes the race without guessing a fixed
    # hydration delay, and is a no-op cost-wise when hydration already
    # finished (the common case) since the value matches on the first try.
    _FIELD_FILL_RETRIES = 3
    _FIELD_FILL_RETRY_WAIT_MS = 500

    # ── Actions ────────────────────────────────────────────────────────────────

    def navigate(self):
        self.open("/login")
        return self

    def _fill_and_verify(self, locator, value):
        """Fill `locator` with `value` and confirm the DOM actually holds it,
        retrying the fill if a race (e.g. Livewire not yet hydrated) left the
        field empty or stale. Raises AssertionError if it never sticks."""
        loc = self.page.locator(locator).first
        last_seen = None
        for attempt in range(1, self._FIELD_FILL_RETRIES + 1):
            self.h.clear_and_type(locator, value)
            last_seen = loc.input_value()
            if last_seen == value:
                return loc
            self.page.wait_for_timeout(self._FIELD_FILL_RETRY_WAIT_MS)
        raise AssertionError(
            f"Field {locator!r} did not retain the typed value after "
            f"{self._FIELD_FILL_RETRIES} attempts (expected non-empty value, "
            f"last seen={last_seen!r}). Likely a page-hydration race."
        )

    def enter_email(self, email):
        self._fill_and_verify(self.EMAIL_INPUT, email)
        return self

    def enter_password(self, password):
        self._fill_and_verify(self.PASSWORD_INPUT, password)
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
