"""
TEMPORARY debug test -- diagnoses why is_card_clickable() finds no
onclick on the grandparent of the "Total Messages" label <p>. Delete
this file once the real cause is confirmed and fixed; it is not part of
the permanent suite.

Run:
    pytest tests/sms/campaigns/test_debug_card_dom.py -v -s
"""
import pytest

from pages.sms.sms_campaign_page import SMSCampaignPage
from pages.sms.sms_campaign_message_report_page import SmsCampaignMessageReportPage


pytestmark = [pytest.mark.sms]


def test_debug_card_dom(module_logged_in_page):
    listing = SMSCampaignPage(module_logged_in_page)
    listing.open_campaign_list()
    navigated = listing.click_reports_link_on_first_row()
    assert navigated, "Could not open the report page from the listing"

    p = SmsCampaignMessageReportPage(module_logged_in_page)
    p.wait_for_table_load(timeout=15000)

    page = p.page
    label_xpath = "xpath=//div[p[normalize-space(text())='Total Messages']]"
    matches = page.locator(label_xpath)
    count = matches.count()
    print(f"\n\n=== MATCH COUNT for label wrapper div: {count} ===")

    for i in range(count):
        el = matches.nth(i)
        print(f"\n--- match {i} ---")
        try:
            print("is_visible:", el.is_visible())
        except Exception as e:
            print("is_visible ERROR:", e)
        try:
            print("outerHTML:\n", el.evaluate("e => e.outerHTML"))
        except Exception as e:
            print("outerHTML ERROR:", e)
        try:
            grandparent_html = el.evaluate("e => e.parentElement && e.parentElement.parentElement ? e.parentElement.parentElement.outerHTML : null")
            print("grandparent outerHTML:\n", grandparent_html)
        except Exception as e:
            print("grandparent ERROR:", e)

    # Also directly test the /../.. locator used by the page object.
    resolved_xpath = "xpath=//div[p[normalize-space(text())='Total Messages']]/../.."
    resolved = page.locator(resolved_xpath)
    resolved_count = resolved.count()
    print(f"\n=== /../.. RESOLVED COUNT: {resolved_count} ===")
    for i in range(resolved_count):
        el = resolved.nth(i)
        print(f"\n--- resolved match {i} ---")
        try:
            print("is_visible:", el.is_visible())
            print("onclick attr:", el.get_attribute("onclick"))
            print("class attr:", el.get_attribute("class"))
        except Exception as e:
            print("ERROR:", e)

    assert True  # diagnostic only -- never fails on its own
