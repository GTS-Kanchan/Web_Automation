"""
Test Suite: Login Page
Covers: UI elements, valid login, invalid credentials, empty fields, forgot password navigation.
"""
import pytest
from utils.config import Config
from pages.common.login_page import LoginPage
from pages.common.forgot_password_page import ForgotPasswordPage


pytestmark = [pytest.mark.common]

class TestLoginPageUI:
    """Verify login page renders correctly."""

    @pytest.mark.smoke
    def test_login_page_title(self, login_page):
        assert "CPaaS" in login_page.get_title(), "Page title should contain 'CPaaS'"

    @pytest.mark.smoke
    def test_logo_is_displayed(self, login_page):
        assert login_page.is_logo_displayed(), "Logo should be visible on login page"

    @pytest.mark.smoke
    def test_email_field_present(self, login_page):
        assert login_page.is_email_field_present(), "Email input should be present"

    @pytest.mark.smoke
    def test_password_field_present(self, login_page):
        assert login_page.is_password_field_present(), "Password input should be present"

    @pytest.mark.smoke
    def test_login_button_present(self, login_page):
        assert login_page.is_login_button_present(), "Login button should be present"

    @pytest.mark.smoke
    def test_forgot_password_link_present(self, login_page):
        assert login_page.is_element_present(LoginPage.FORGOT_LINK), \
            "Forgot Password link should be present"

    def test_login_page_url(self, login_page):
        assert login_page.is_login_page(), "URL should contain 'login'"


class TestValidLogin:
    """Test successful authentication."""

    @pytest.mark.smoke
    def test_valid_credentials_redirect(self, login_page):
        login_page.login(Config.VALID_EMAIL, Config.VALID_PASSWORD)
        login_page.h.wait_for_url_contains("/", timeout=15000)
        assert "login" not in login_page.get_current_url(), \
            "Should redirect away from login page after successful login"

    @pytest.mark.smoke
    def test_valid_login_no_error(self, login_page):
        login_page.login(Config.VALID_EMAIL, Config.VALID_PASSWORD)
        # Give page a moment to process
        login_page.page.wait_for_timeout(2000)
        # If still on login, check for error
        if login_page.is_login_page():
            error = login_page.get_error_message()
            assert not error, f"Unexpected error on valid login: {error}"


class TestInvalidLogin:
    """Test authentication failure scenarios."""

    @pytest.mark.regression
    @pytest.mark.negative
    def test_wrong_password(self, login_page):
        login_page.login(Config.VALID_EMAIL, "WrongPassword123!")
        login_page.page.wait_for_timeout(2000)
        assert login_page.is_login_page() or login_page.get_error_message(), \
            "Should stay on login or show error for wrong password"

    @pytest.mark.regression
    @pytest.mark.negative
    def test_wrong_email(self, login_page):
        login_page.login("notauser@example.com", Config.VALID_PASSWORD)
        login_page.page.wait_for_timeout(2000)
        assert login_page.is_login_page() or login_page.get_error_message(), \
            "Should stay on login or show error for wrong email"

    @pytest.mark.regression
    @pytest.mark.negative
    def test_empty_email(self, login_page):
        login_page.enter_password(Config.VALID_PASSWORD)
        login_page.click_login()
        login_page.page.wait_for_timeout(1000)
        # Should stay on login page — browser validation or server error
        assert "login" in login_page.get_current_url(), \
            "Should not proceed with empty email"

    @pytest.mark.regression
    @pytest.mark.negative
    def test_empty_password(self, login_page):
        login_page.enter_email(Config.VALID_EMAIL)
        login_page.click_login()
        login_page.page.wait_for_timeout(1000)
        assert "login" in login_page.get_current_url(), \
            "Should not proceed with empty password"

    @pytest.mark.regression
    @pytest.mark.negative
    def test_both_fields_empty(self, login_page):
        login_page.click_login()
        login_page.page.wait_for_timeout(1000)
        assert "login" in login_page.get_current_url(), \
            "Should not proceed with empty credentials"

    @pytest.mark.regression
    @pytest.mark.negative
    def test_invalid_email_format(self, login_page):
        login_page.enter_email("not-an-email")
        login_page.enter_password(Config.VALID_PASSWORD)
        login_page.click_login()
        login_page.page.wait_for_timeout(1000)
        assert "login" in login_page.get_current_url(), \
            "Should not accept malformed email"

    @pytest.mark.regression
    @pytest.mark.negative
    def test_sql_injection_in_email(self, login_page):
        login_page.login("' OR '1'='1", "password")
        login_page.page.wait_for_timeout(2000)
        assert login_page.is_login_page() or login_page.get_error_message(), \
            "SQL injection attempt should not succeed"

    @pytest.mark.regression
    @pytest.mark.negative
    def test_xss_in_email(self, login_page):
        login_page.login("<script>alert('xss')</script>@test.com", "password")
        login_page.page.wait_for_timeout(2000)
        assert login_page.is_login_page() or login_page.get_error_message(), \
            "XSS attempt should be safely handled"


class TestForgotPasswordNavigation:
    """Navigate to and from forgot-password page."""

    @pytest.mark.regression
    def test_forgot_password_link_navigates(self, login_page):
        login_page.click_forgot_password()
        login_page.h.wait_for_url_contains("forgot-password")
        assert "forgot-password" in login_page.get_current_url(), \
            "Should navigate to forgot-password page"

    @pytest.mark.regression
    def test_back_to_login_from_forgot(self, page):
        fp_page = ForgotPasswordPage(page)
        fp_page.navigate()
        assert fp_page.is_forgot_password_page()
        fp_page.click_login_link()
        fp_page.h.wait_for_url_contains("login")
        assert "login" in fp_page.get_current_url(), \
            "Should navigate back to login from forgot-password"
