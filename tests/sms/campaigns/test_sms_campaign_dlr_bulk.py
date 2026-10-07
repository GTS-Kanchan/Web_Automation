"""
test_sms_campaign_dlr_bulk.py

Test Case: Verify DLR for SMS UI Campaign
Objective: Verify that DLRs are received for all SMS messages sent
through an SMS UI campaign.
DLR Verification API: POST {dlr_base_url}/api/v1/dlr/verify

Provided directly by the project owner as a test-case spec (steps,
expected-result table, and explicit failure conditions). This is the
"bulk" counterpart of test_sms_json_dlr.py (also POST /api/v1/dlr/
verify), but the message_ids here come from a real UI campaign instead
of an API response's `data` array.

Lives under tests/sms/campaigns/ (moved here from tests/sms/api/, where
it was first placed) since this is fundamentally a UI-driven campaign
test (steps 1-10: create/launch a real campaign, read its report, walk
the Messages page for each recipient) that only calls the API for the
final bulk DLR check (steps 11-15) -- it belongs alongside
test_campaign_creation.py and test_sms_campaign_message_report_flow.py,
not the API-only suite.

This directory's own conftest.py (tests/sms/campaigns/conftest.py) was
added specifically for this test: it mirrors tests/sms/api/conftest.py's
env_config/test_data/api_request_context/api_client fixtures (same
underlying utils.sms_api_client.SmsApiClient / utils.sms_api_config_loader
code, no logic duplicated) since pytest only loads a conftest's fixtures
for paths on the actual collection path -- a conftest under tests/sms/api
is never loaded for tests collected under tests/sms/campaigns, same
reasoning already documented for the sibling test_sms_webengage_dlr.py
(a first version of THAT file, placed under tests/sms/messaging, failed
at fixture setup with "fixture 'api_client' not found" for exactly this
reason). Unlike tests/sms/api/conftest.py, this directory's conftest.py
does NOT re-register the --env CLI flag (that would conflict when both
directories are collected in the same run) -- see its own docstring.

Building blocks, all reused from already-confirmed, already-passing
code in this suite -- nothing here is a new/unconfirmed locator:

  1. Campaign creation + launch (steps 1-2): reuses SMSCampaignPage
     (pages/sms/sms_campaign_page.py) exactly the way
     tests/sms/campaigns/test_campaign_creation.py's
     test_TC_C021_launch_campaign does -- name -> Sender ID -> paste
     contacts -> Send Now -> Preview -> Launch Campaign -> poll for a
     success signal (redirect to list / success toast). The recipient
     numbers come from Config.SMS_PASTE_CONTACTS (the same confirmed
     test data TC_C021 itself launches with), not invented here.
  2. Campaign search + Reports (steps 3-7): SMSCampaignPage.search() +
     click_reports_link_on_first_row() -- confirmed real Reports icon
     (data-tooltip-target='tooltip-reports-<id>'), landing on
     SmsCampaignMessageReportPage (pages/sms/sms_campaign_message_report_
     page.py), whose default "total" metric table is CONFIRMED (see
     tests/sms/campaigns/test_sms_campaign_message_report_flow.py) to
     have a CONTACT column.
  3. Collecting recipients (step 8): reads the CONTACT column of every
     row on that report page via the newly added
     SmsCampaignMessageReportPage.get_cell_text() (same row/column
     convention as SMSMessagePage.get_cell_text(), just not previously
     needed on this page object).
  4. Extracting each message_id (step 9): the per-campaign report page
     itself has NO confirmed per-row "View" + message-details popup
     anywhere in this codebase (no such locator exists in
     sms_campaign_message_report_page.py, and no test in this suite
     exercises one) -- so, per this project's standing rule against
     fabricating a locator that was never confirmed, this does NOT
     invent a View button on the report page. Instead it reuses the ONE
     place in this codebase where a real, confirmed "View -> message
     details popup -> message_id" interaction exists and is proven
     working: the SMS Channel -> Messages page (pages/sms/
     sms_message_page.py; get_popup_message_id() is already relied on by
     the passing tests/sms/messaging/test_sms_message_flow.py::
     test_TC050_popup_shows_message_id, and by
     tests/sms/api/test_sms_webengage_dlr.py). This is exactly
     what SMSMessagePage.SOURCE_VAL_CAMPAIGN = "U" (a confirmed, real
     filter value on that same page) exists for: campaign-originated
     messages are confirmed to be visible there too, filterable by
     Source = Campaign. For each recipient number collected from the
     report, this searches the Messages page (filtered to Source =
     Campaign) for that number and picks the best-matching row via
     utils/ui_dlr_helpers.find_latest_matching_row() -- the same
     best-effort "Submitted At"/"Received At" disambiguation already
     used by test_sms_webengage_dlr.py, and flagged there and here as
     unconfirmed-format/best-effort, never a silent guess.
  5. Bulk DLR verification (steps 11-15): utils/dlr_helpers.poll_bulk_dlr(),
     the exact same helper already built and used by test_sms_json_dlr.py
     for the other bulk-DLR test case -- called ONCE with the full
     message_ids list, per the spec's explicit closing instruction
     ("perform DLR verification once in bulk ... rather than calling
     the DLR verification API separately for every recipient").

IMPORTANT, per the spec: this test deliberately does NOT assert on DLR
`status`, `provider_status`, or `status_code` anywhere in the response.
Message IDs are never hard-coded -- they are built dynamically from the
report page's own recipients and the Messages page's own popups.
"""

import time

import pytest

from pages.sms.sms_campaign_page import SMSCampaignPage
from pages.sms.sms_campaign_message_report_page import SmsCampaignMessageReportPage
from pages.sms.sms_message_page import SMSMessagePage
from utils.config import Config
from utils.dlr_format_validator import (
    aggregate_bulk_dlr_validation,
    build_bulk_dlr_validation_report,
)
from utils.dlr_helpers import DLR_POLL_TIMEOUT_SECONDS, poll_bulk_dlr
from utils.ui_dlr_helpers import find_latest_matching_row

pytestmark = pytest.mark.sms

VALID_SENDER_ID = Config.SMS_SENDER_ID
VALID_TEMPLATE = Config.SMS_TEMPLATE_NAME
PASTE_CONTACTS = Config.SMS_PASTE_CONTACTS.replace("\\n", "\n")

# How long to wait for a per-recipient message to be findable/viewable on
# the Messages page after the campaign launched -- not given a concrete
# number by the spec ("Continue until the message_id for every recipient
# has been collected" has no attached timeout), so this bounds what would
# otherwise be an unbounded search per recipient.
PER_RECIPIENT_SEARCH_TIMEOUT_SECONDS = 60
PER_RECIPIENT_SEARCH_INTERVAL_SECONDS = 3


def _create_and_launch_send_now_campaign(campaign_page, name_suffix):
    """Name -> Sender ID -> Template (best-effort) -> paste contacts ->
    Send Now -> Preview -> Launch Campaign -> wait for a success signal.
    Identical sequence to
    test_campaign_creation.py::test_TC_C021_launch_campaign -- kept local
    (not imported from that test module) since test modules aren't meant
    to be imported as shared libraries in this suite; every step below
    calls only already-confirmed SMSCampaignPage methods.

    Returns the generated campaign name. Raises AssertionError if launch
    never produces a success signal (redirect to list / success toast).
    """
    if not campaign_page.is_campaign_list_page():
        campaign_page.open_campaign_list()
    campaign_page.click_create_campaign()
    campaign_page.page.wait_for_timeout(1000)
    name = f"AutoCamp_DLR_{int(campaign_page.page.evaluate('() => Date.now()') / 1000)}"
    campaign_page.enter_campaign_name(name)

    campaign_page.select_sender_id(VALID_SENDER_ID)
    try:
        campaign_page.select_template(VALID_TEMPLATE)
    except Exception:
        pass  # template is best-effort, same as TC_C021

    campaign_page.click_import_contact()
    campaign_page.paste_contacts(PASTE_CONTACTS)
    campaign_page.click_import_confirm()
    campaign_page.page.wait_for_timeout(1000)

    if campaign_page.is_campaign_list_page():
        return name  # auto-redirected after import = launched

    campaign_page.select_send_now()
    campaign_page.page.wait_for_timeout(1000)

    if campaign_page.is_campaign_list_page():
        return name  # auto-redirected after Send Now = launched

    campaign_page.click_preview()
    assert campaign_page.is_preview_open(), (
        f"Preview modal did not open for campaign '{name}' -- cannot launch."
    )
    campaign_page.page.wait_for_timeout(2000)

    campaign_page.click_launch_campaign()

    deadline = time.time() + 20
    launched = False
    while time.time() < deadline:
        campaign_page.confirm_swal(timeout=1000)
        if campaign_page.is_campaign_list_page():
            launched = True
            break
        if campaign_page.is_element_present(campaign_page.TOAST_SUCCESS, timeout=1000):
            launched = True
            break
        campaign_page.page.wait_for_timeout(500)

    assert launched, (
        f"Campaign '{name}' did not produce a success signal after Launch. "
        f"URL: {campaign_page.get_current_url()}"
    )
    return name


@pytest.mark.smoke
def test_dlr_bulk_verification_for_sms_ui_campaign(api_client, logged_in_page, record_property):
    campaign_page = SMSCampaignPage(logged_in_page)

    # ── Steps 1-2: create and execute an SMS campaign, capture its name ─────
    campaign_page.open_campaign_list()
    campaign_name = _create_and_launch_send_now_campaign(campaign_page, "DLR")
    record_property("campaign_name", campaign_name)

    # ── Steps 3-5: back on the Campaigns list, search for it, find the row ──
    if not campaign_page.is_campaign_list_page():
        campaign_page.open_campaign_list()
    campaign_page.search(campaign_name)
    found = campaign_page.is_campaign_name_in_list(campaign_name, timeout=15000)
    assert found, f"Campaign '{campaign_name}' could not be found in the Campaigns list after search."

    # ── Step 6-7: click Reports, land on the campaign message report page ───
    opened = campaign_page.click_reports_link_on_first_row()
    assert opened, f"Reports link could not be opened for campaign '{campaign_name}'."

    report_page = SmsCampaignMessageReportPage(logged_in_page)
    assert report_page.is_report_page(), (
        f"Did not land on the campaign message report page for "
        f"'{campaign_name}'. URL: {report_page.get_current_url()}"
    )
    report_page.wait_for_table_load()

    # ── Step 8: collect recipient/mobile numbers from the CONTACT column ────
    headers = report_page.get_visible_column_headers()
    contact_col_idx = None
    for i, h in enumerate(headers):
        if h.strip().lower() == "contact":
            contact_col_idx = i
            break
    assert contact_col_idx is not None, (
        f"Could not find a 'Contact' column on the campaign report page. "
        f"Headers: {headers!r}"
    )

    row_count = report_page.get_row_count()
    assert row_count > 0, (
        f"Recipient list could not be loaded -- no rows on the report page "
        f"for campaign '{campaign_name}'."
    )

    recipients = [
        report_page.get_cell_text(i, contact_col_idx) for i in range(row_count)
    ]
    recipients = [r for r in recipients if r]  # drop any unreadable/empty cells
    record_property("Recipients collected", str(len(recipients)))
    record_property("recipients", ", ".join(recipients))

    # ── Step 9-10: for each recipient, View its message on the Messages page
    #               (Source = Campaign) and capture message_id -- see the
    #               module docstring for why the Messages page, not this
    #               report page, is where View/message_id actually exist ────
    message_page = SMSMessagePage(logged_in_page)
    message_page.navigate()
    message_page.open_filter_panel()
    message_page.set_filter_source("campaign")
    message_page.apply_filter()

    message_ids = []
    unresolved_recipients = []

    for recipient in recipients:
        deadline = time.time() + PER_RECIPIENT_SEARCH_TIMEOUT_SECONDS
        row_count_for_recipient = 0
        while time.time() < deadline:
            message_page.search(recipient)
            message_page.wait_for_table_load()
            row_count_for_recipient = message_page.get_row_count()
            if row_count_for_recipient > 0:
                break
            time.sleep(PER_RECIPIENT_SEARCH_INTERVAL_SECONDS)

        if row_count_for_recipient == 0:
            unresolved_recipients.append(recipient)
            continue

        row_index = find_latest_matching_row(message_page, record_property, label=recipient)
        message_page.click_view_icon(row_index)
        if not message_page.is_popup_open():
            unresolved_recipients.append(recipient)
            continue

        message_id = message_page.get_popup_message_id()
        message_page.close_popup()

        if not message_id:
            unresolved_recipients.append(recipient)
            continue

        message_ids.append(message_id)
        record_property(f"message_id[{recipient}]", message_id)

    record_property("Message IDs collected", str(len(message_ids)))

    assert not unresolved_recipients, (
        f"Could not obtain a message_id for {len(unresolved_recipients)} of "
        f"{len(recipients)} recipient(s): {unresolved_recipients}."
    )
    assert len(message_ids) == len(recipients), (
        f"Expected {len(recipients)} message_ids (one per recipient), got "
        f"{len(message_ids)}."
    )

    # ── Step 11-12: build the DLR verification request dynamically and call
    #                POST /api/v1/dlr/verify ONCE, in bulk -- never per
    #                recipient, per the spec's explicit closing instruction ──
    # require_billing is intentionally left out (defaults to None) --
    # by default this environment only generates a STATUS DLR for a
    # message, not a separate billing DLR, so requiring one here made
    # bulk-verify wait for/expect a DLR that never arrives.
    verify_response, verify_body, results = poll_bulk_dlr(
        api_client, message_ids
    )

    assert verify_response is not None, (
        "DLR verification API was never called -- unexpected internal state."
    )
    record_property("Response", verify_response.text)

    record_property("Expected", "200")
    record_property("Actual", str(verify_response.status_code))
    assert verify_response.status_code == 200, (
        f"DLR verification API failed for message_ids={message_ids} within "
        f"{DLR_POLL_TIMEOUT_SECONDS}s. Got {verify_response.status_code}. "
        f"Body: {verify_response.text}"
    )
    assert verify_body is not None, (
        f"DLR verification API returned 200 but the body wasn't valid JSON. "
        f"Body: {verify_response.text}"
    )
    assert results is not None, (
        f"Could not recognize the DLR verification response's shape to "
        f"extract per-message_id results from. Full body: {verify_body}"
    )

    # ── Step 13: response contains all submitted message IDs ────────────────
    missing_ids = [mid for mid in message_ids if mid not in results]
    record_property("Missing DLRs", str(len(missing_ids)))
    assert not missing_ids, (
        f"{len(missing_ids)} of {len(message_ids)} submitted message_id(s) "
        f"are missing from the DLR verification response entirely: "
        f"{missing_ids}. Full body: {verify_body}"
    )

    # ── Step 14: every submitted message has a received DLR ─────────────────
    not_received = [mid for mid in message_ids if not results[mid].get("received")]
    received_count = len(message_ids) - len(not_received)
    record_property("Expected DLRs", str(len(message_ids)))
    record_property("Received DLRs", str(received_count))
    assert not not_received, (
        f"{len(not_received)} of {len(message_ids)} submitted message_id(s) "
        f"were not marked received=true within {DLR_POLL_TIMEOUT_SECONDS}s: "
        f"{not_received}. Full body: {verify_body}"
    )

    # ── Step 15: no missing DLRs (already proven by steps 13-14 above) ──────
    # Bonus check from the spec's own Expected Result table ("Unmatched
    # DLRs 0"): DLR entries returned for an id that was never submitted.
    # Not in the spec's explicit Failure Conditions list, so this is
    # recorded for visibility; loosen if a real bulk-verify response is
    # confirmed to legitimately include extra correlated entries.
    unmatched_ids = [mid for mid in results if mid not in message_ids]
    record_property("Unmatched DLRs", str(len(unmatched_ids)))
    assert not unmatched_ids, (
        f"DLR verification response contains {len(unmatched_ids)} entry/"
        f"entries not among the submitted message_ids: {unmatched_ids}. "
        f"Full body: {verify_body}"
    )

    # Deliberately NOT asserting on status / provider_status / status_code
    # anywhere in the DLR verification body, per the spec's explicit
    # instruction -- this test is scoped to bulk DLR reception and
    # correlation only.

    # ── DLR Format/Schema Verification for every received DLR (generic
    #               test -- status/code are only checked to EXIST, never
    #               compared to a specific value). message_ids and
    #               recipients are the SAME order/length (enforced by the
    #               asserts above), so zipping them gives a real, dynamic
    #               message_id -> recipient map for mobile correlation,
    #               never a hard-coded one ──────────────────────────────
    expected_mobiles = dict(zip(message_ids, recipients))
    counts, failures = aggregate_bulk_dlr_validation(message_ids, results, expected_mobiles=expected_mobiles)
    bulk_report = build_bulk_dlr_validation_report(counts)
    record_property("DLR Bulk Validation Report", bulk_report)
    print("\n" + bulk_report)
    assert counts["invalid_format"] == 0, (
        f"{counts['invalid_format']} of {len(message_ids)} DLR(s) failed "
        f"format/schema validation.\n{bulk_report}\nFailures: {failures}"
    )
    assert counts["message_id_mismatches"] == 0, (
        f"{counts['message_id_mismatches']} DLR(s) had a message_id "
        f"correlation mismatch.\n{bulk_report}\nFailures: {failures}"
    )
    assert counts["mobile_mismatches"] == 0, (
        f"{counts['mobile_mismatches']} DLR(s) had a recipient/mobile "
        f"correlation mismatch.\n{bulk_report}\nFailures: {failures}"
    )
    assert counts["duplicate_dlrs"] == 0, (
        f"{counts['duplicate_dlrs']} duplicate DLR entry/entries found.\n"
        f"{bulk_report}\nFailures: {failures}"
    )
