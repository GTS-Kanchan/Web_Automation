import pytest
from pages.common.login_page import LoginPage
from pages.sms.sms_template_page import SMSTemplatePage

def test_dump_first_row(page):
    # Log in first!
    login_page = LoginPage(page)
    login_page.open()
    login_page.login("navjot", "Testing@123")
    page.wait_for_timeout(3000)

    template_page = SMSTemplatePage(page)
    template_page.open(template_page.TEMPLATE_LIST_URL)
    page.wait_for_timeout(4000)
    
    # Dump body to file
    body_html = page.evaluate("document.body.innerHTML")
    with open("page_dump_loggedin.html", "w", encoding="utf-8") as f:
        f.write(body_html)
