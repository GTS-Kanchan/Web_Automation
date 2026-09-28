"""
test_sms_campaign_otp_test_dlr.py

Test Case: Verify DLR for `OTP_test` SMS Campaign
DLR Verification API: POST {dlr_base_url}/api/v1/dlr/verify

The OTP_test campaign is run beforehand from the UI; this test does NOT create
or launch anything. It searches the Campaigns list for OTP_test, opens the
Reports of the newest row named exactly "OTP_test", collects every recipient's
message_id via View, then verifies all DLRs with ONE bulk
/api/v1/dlr/verify call. The steps live in utils/campaign_dlr.py, which every
SMS campaign launch test also uses (see tests/sms/campaigns/conftest.py).

DLR status / provider_status / status_code are NOT validated.

Env: DLR_CAMPAIGN_NAME (default "OTP_test"), SMS_CAMPAIGN_DLR_TIMEOUT (default 180 s).
"""

import os

import pytest

from utils.campaign_dlr import verify_campaign_dlrs

pytestmark = pytest.mark.sms

CAMPAIGN_NAME = os.getenv("DLR_CAMPAIGN_NAME", "OTP_test")


@pytest.mark.smoke
def test_dlr_verification_for_otp_test_campaign(api_client, logged_in_page, record_property):
    # Existing campaign -> its report is already complete, no need to wait long for rows.
    verify_campaign_dlrs(logged_in_page, api_client, CAMPAIGN_NAME,
                         record_property=record_property, report_timeout=30)
