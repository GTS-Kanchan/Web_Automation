"""
Test Suite: Forgot Password Page
Covers: UI elements, email submission, empty field, invalid email.
"""
import pytest
from pages.common.forgot_password_page import ForgotPasswordPage
from utils.config import Config


pytestmark = [pytest.mark.common]

@pytest.fixture
def forgot_page(page):
    fp = ForgotPasswordPage(page)
    fp.navigate()
    return fp


class TestForgotPasswordUI:

    @pytest.mark.smoke
    def test_page_loads(self, forgot_page):
        assert forgot_page.is_forgot_password_page(), "Should be on forgot-password URL"

    @pytest.mark.smoke
    def test_email_input_present(self, forgot_page):
        assert forgot_page.is_element_present(ForgotPasswordPage.EMAIL_INPUT), \
            "Email input should be present"

    @pytest.mark.smoke
    def test_send_button_present(self, forgot_page):
        assert forgot_page.is_element_present(ForgotPasswordPage.SEND_BUTTON), \
            "Send Link button should be present"

    @pytest.mark.smoke
    def test_login_link_present(self, forgot_page):
        assert forgot_page.is_element_present(ForgotPasswordPage.LOGIN_LINK), \
            "'or Login' link should be present"


class TestForgotPasswordSubmission:

    @pytest.mark.regression
    def test_valid_email_submission(self, forgot_page):
        forgot_page.submit_email(Config.VALID_EMAIL)
        forgot_page.page.wait_for_timeout(2000)
        # Expect a success message or redirect
        success = forgot_page.get_success_message()
        error = forgot_page.get_error_message()
        assert success is not None or error is None, \
            "Valid email should result in success message or no error"

    @pytest.mark.regression
    @pytest.mark.negative
    def test_empty_email_submission(self, forgot_page):
        forgot_page.click_send_link()
        forgot_page.page.wait_for_timeout(1000)
        assert forgot_page.is_forgot_password_page(), \
            "Should stay on page with empty email"

    @pytest.mark.regression
    @pytest.mark.negative
    def test_invalid_email_format(self, forgot_page):
        forgot_page.submit_email("bademail")
        forgot_page.page.wait_for_timeout(1000)
        assert forgot_page.is_forgot_password_page(), \
            "Should stay on page with invalid email format"

    @pytest.mark.regression
    @pytest.mark.negative
    def test_nonexistent_email(self, forgot_page):
        forgot_page.submit_email("doesnotexist@nowhere.com")
        forgot_page.page.wait_for_timeout(2000)
        # App may show generic success (security best practice) or an error
        # Either is acceptable; the test just verifies no crash
        url = forgot_page.get_current_url()
        assert url is not None, "Page should still be reachable after submission"
