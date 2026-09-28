"""
test_sms_campaign_transaction_template_dlr.py

Test Case: Verify DLR for Transaction SMS Template
DLR Verification API: POST {dlr_base_url}/api/v1/dlr/verify

The template comes ONLY from .env, so it can be changed without touching code:
    SMS_TRANSACTION_TEMPLATE=Template9_7WT8C8
    SMS_TRANSACTION_TEMPLATE_TYPE=TRANSACTIONAL   (reported, defaults to TRANSACTIONAL)

Steps:
  1. Load SMS_TRANSACTION_TEMPLATE from .env (fail if missing).
  2-3. Create an SMS UI campaign with that template (sender = SMS_SENDER_ID,
       contacts = SMS_PASTE_CONTACTS), Send Now, launch it.
  4-13. utils/campaign_dlr.verify_campaign_dlrs(): find the campaign, open its
       report, View every recipient -> message_id, ONE bulk /api/v1/dlr/verify,
       every id must have a correlated DLR, 0 missing.

DLR status / provider_status / status_code are NOT validated.
"""

import time

import pytest

from pages.sms.sms_campaign_page import SMSCampaignPage
from utils.campaign_dlr import verify_campaign_dlrs
from utils.config import Config

pytestmark = [pytest.mark.sms, pytest.mark.campaign]

TEMPLATE = Config.SMS_TRANSACTION_TEMPLATE
TEMPLATE_TYPE = Config.SMS_TRANSACTION_TEMPLATE_TYPE or "TRANSACTIONAL"
SENDER_ID = Config.SMS_SENDER_ID
PASTE_CONTACTS = Config.SMS_PASTE_CONTACTS.replace("\\n", "\n")


def _print_summary(record_property, rows):
    width = max(len(k) for k, _ in rows)
    for k, v in rows:
        record_property(k, v)
    print("\n" + "\n".join(f"{k.ljust(width)}   {v}" for k, v in rows))


def _create_and_launch(campaign_page, name, template):
    """Name -> sender -> template (required) -> paste contacts -> Send Now ->
    Preview -> Launch. Returns None on success, else the failure reason."""
    campaign_page.open_campaign_list()
    campaign_page.click_create_campaign()
    campaign_page.page.wait_for_timeout(1000)
    campaign_page.enter_campaign_name(name)

    try:
        campaign_page.select_sender_id(SENDER_ID)
    except Exception as exc:
        return f"sender ID '{SENDER_ID}' could not be selected: {exc}"
    try:
        campaign_page.select_template(template)
    except Exception as exc:
        return f"template '{template}' could not be selected: {exc}"

    campaign_page.click_import_contact()
    campaign_page.paste_contacts(PASTE_CONTACTS)
    campaign_page.click_import_confirm()
    campaign_page.page.wait_for_timeout(1000)
    if campaign_page.is_campaign_list_page():
        return None  # app auto-submitted after import

    campaign_page.select_send_now()
    campaign_page.page.wait_for_timeout(1000)
    if campaign_page.is_campaign_list_page():
        return None

    campaign_page.click_preview()
    campaign_page.page.wait_for_timeout(1000)
    if campaign_page.is_campaign_list_page():
        return None
    if not campaign_page.is_preview_open():
        return "preview did not open, campaign could not be launched"
    campaign_page.page.wait_for_timeout(2000)
    campaign_page.click_launch_campaign()

    deadline = time.time() + 20
    while time.time() < deadline:
        campaign_page.confirm_swal(timeout=1000)
        if campaign_page.is_campaign_list_page():
            return None
        if campaign_page.is_element_present(campaign_page.TOAST_SUCCESS, timeout=1000):
            return None
        campaign_page.page.wait_for_timeout(500)
    return f"no success signal after Launch (URL: {campaign_page.get_current_url()})"


@pytest.mark.smoke
def test_dlr_verification_for_transaction_template_campaign(api_client, logged_in_page, record_property):
    # Step 1: template from .env only
    if not TEMPLATE:
        _print_summary(record_property, [("Transaction Template", "<not set>"), ("Final Result", "FAIL")])
        pytest.fail("Transaction template is not available in .env: set SMS_TRANSACTION_TEMPLATE=<template name>")

    summary = [("Transaction Template", TEMPLATE), ("Template Type", TEMPLATE_TYPE)]

    # Steps 2-3: create + launch the campaign with that template
    campaign_page = SMSCampaignPage(logged_in_page)
    name = f"{Config.SMS_CAMPAIGN_PREFIX}_TXN_{int(time.time())}"
    error = _create_and_launch(campaign_page, name, TEMPLATE)
    if error:
        _print_summary(record_property, summary + [("Campaign", name), ("Campaign Created", "FAIL"),
                                                   ("Final Result", "FAIL")])
        pytest.fail(f"Campaign creation failed for '{name}' with template '{TEMPLATE}': {error}")
    summary.append(("Campaign Created", "PASS"))

    # Steps 4-13: report -> View each recipient -> message_id -> ONE bulk DLR verify
    expected = len([n for n in PASTE_CONTACTS.split("\n") if n.strip()])
    verify_campaign_dlrs(logged_in_page, api_client, name, record_property=record_property,
                         expected_recipients=expected, summary_prefix=summary)
