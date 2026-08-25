import pytest
from pages.common.login_page import LoginPage
from pages.sms.sms_template_page import SMSTemplatePage

def test_dump_modal(page):
    from utils.config import Config
    
    login_page = LoginPage(page)
    login_page.open("/login")
    login_page.login("navjot", "Testing@123")
    page.wait_for_timeout(3000)

    template_page = SMSTemplatePage(page)
    template_page.open(template_page.TEMPLATE_LIST_URL)
    page.wait_for_timeout(4000)
    
    template_page.click_first_row_view()
    page.wait_for_timeout(3000)
    
    loc = page.locator(template_page.PREVIEW_POPUP).first
    print("INNER TEXT: ", repr(loc.inner_text()))
    print("TEXT CONTENT: ", repr(loc.text_content()))
