"""
test_sms_webengage_dlr.py

Test Case: Verify WebEngage SMS DLR
Send API: POST /api/v1/sms/webengage/send
DLR API:  GET {dlr_base_url}/api/v1/dlr/{message_id}

Provided directly by the project owner as a test-case spec (steps and
explicit failure conditions). Unlike every other DLR test in this suite,
/api/v1/sms/webengage/send's own response never carries a message_id
(confirmed shape -- see test_webengage_send.py's
test_send_webengage_valid_payload_returns_success: only
{"status": "sms_accepted"}). Per the spec's own steps 4-9, the
message_id instead has to be read off the SMS Channel -> Messages UI
page (pages/sms/sms_message_page.py, the same page object and locators
already exercised and passing in
tests/sms/messaging/test_sms_message_flow.py -- e.g. its TC050 already
confirms get_popup_message_id() reliably returns a real Message ID from
that same popup). So this test mixes the API suite's `api_client`
fixture with the UI suite's `logged_in_page` fixture in one test -- both
are independent fixture trees (session-scoped API client, a fresh
function-scoped authenticated browser context) and compose without
conflict.

Lives under tests/sms/api/ (not tests/sms/messaging/, where a first
version of this file was placed) specifically so it picks up this
directory's conftest.py -- api_client/test_data/env_config and the
--env CLI flag are only registered for tests collected under
tests/sms/api (pytest only loads a conftest's fixtures/options for
paths on the actual collection path); a real run against the first
version, placed under tests/sms/messaging, failed at fixture setup with
"fixture 'api_client' not found" for exactly this reason, and --env
wasn't recognized either. Only pages.sms.sms_message_page/logged_in_page
(root conftest.py, loaded everywhere) are used for the UI portion.

Recipient number: reuses test_data.yaml's webengage_send.valid_payload
toNumber ("918074318217") -- the only recipient number ever confirmed
usable against this environment. The spec's step 1 ("Generate/store the
test recipient phone number") is implemented as capturing/recording
that confirmed number for reuse in the Messages search, rather than
inventing an unconfirmed one that might not be deliverable here.

Disambiguating "the latest matching message" (per the spec's own
"Important" section -- do not just take the first search result):
  1. The Messages table is searched for the recipient number and its
     row count is captured BEFORE sending, as a baseline. After sending,
     the same search is re-run (bounded poll) until the row count goes
     ABOVE that baseline -- i.e. a genuinely NEW row appeared, not a
     coincidental pre-existing message for the same number.
  2. Among the (possibly still >1) matching rows, the one with the
     latest value in the 'Submitted At'/'Received At' column (whichever
     is present -- see constants/sms_message_ui_headers.py) is selected.
     NOTE: the real on-screen rendering format of that column's text was
     never confirmed by any sample -- no such sample was given, and no
     other test in this suite reads that column's cell values (only
     date-range *filter inputs* elsewhere use a confirmed 'DD-MM-YYYY'
     format, which is a different UI element). Parsing here is therefore
     best-effort across several plausible formats; if none of them parse
     for any row, this test falls back to row 0 and explicitly records
     that fallback via record_property (visible in the HTML report) as a
     flagged assumption rather than a silent guess -- see
     utils/ui_dlr_helpers.py's find_latest_matching_row(), shared with
     tests/sms/api/test_sms_campaign_dlr_bulk.py which needs the exact
     same disambiguation logic.

IMPORTANT, per the spec: this test deliberately does NOT assert on
`status`, `provider_status`, or `status_code` anywhere in the DLR body.
It only validates DLR reception and message correlation.
"""

import copy
import time
import uuid

import pytest

from pages.sms.sms_message_page import SMSMessagePage
from utils.dlr_helpers import DLR_POLL_TIMEOUT_SECONDS, poll_for_dlr
from utils.ui_dlr_helpers import find_latest_matching_row

pytestmark = pytest.mark.sms

# Not specified as a concrete number by the spec ("wait for the latest
# message record to appear" has no attached timeout/interval) -- same
# reasoning as DLR_POLL_TIMEOUT_SECONDS/DLR_POLL_INTERVAL_SECONDS in
# utils/dlr_helpers.py. Tighten once real UI indexing latency is
# confirmed for this instance.
MESSAGES_SEARCH_TIMEOUT_SECONDS = 60
MESSAGES_SEARCH_INTERVAL_SECONDS = 3


@pytest.mark.smoke
def test_dlr_received_after_webengage_send(api_client, test_data, logged_in_page, record_property):
    # ── Step 1: recipient phone number -- confirmed real test number,
    #            stored for reuse in the Messages search below ─────────────
    payload = copy.deepcopy(test_data["webengage_send"]["valid_payload"])
    recipient_number = payload["smsData"]["toNumber"]
    record_property("recipient_number", recipient_number)

    # A fresh, unique metadata.messageId per run -- a real field already in
    # the confirmed payload shape (previously a fixed dummy value in
    # test_data.yaml). Recorded for diagnostics only; the message_id
    # actually used for DLR lookup always comes from the Messages UI
    # (step 9), never assumed to equal this value.
    run_marker = f"dlrtest-{uuid.uuid4().hex}"
    payload["metadata"]["messageId"] = run_marker
    record_property("run_marker (metadata.messageId sent)", run_marker)

    message_page = SMSMessagePage(logged_in_page)

    # ── Baseline (supports steps 4-6): open Messages, search the recipient
    #            number BEFORE sending, to know the row count beforehand ──
    message_page.navigate()
    message_page.search(recipient_number)
    message_page.wait_for_table_load()
    baseline_count = message_page.get_row_count()
    record_property("baseline row count (before send)", str(baseline_count))

    # ── Step 2-3: send via /api/v1/sms/webengage/send, verify response ──────
    send_response = api_client.send_webengage(payload)
    record_property("Response", send_response.text)

    record_property("Expected", "sms_accepted")
    send_body = send_response.json() if send_response.status_code == 200 else {}
    record_property("Actual", str(send_body.get("status")))
    assert send_response.status_code == 200, (
        f"WebEngage SMS API failed: expected 200, got "
        f"{send_response.status_code}. Body: {send_response.text}"
    )
    assert send_body.get("status") == "sms_accepted", (
        f"Expected response 'status' to be 'sms_accepted'. "
        f"Body: {send_response.text}"
    )

    # ── Steps 4-6: back on Messages, search again, wait (bounded poll) for
    #              a NEW row past the baseline to appear ──────────────────
    deadline = time.time() + MESSAGES_SEARCH_TIMEOUT_SECONDS
    row_count = baseline_count
    while time.time() < deadline:
        message_page.search(recipient_number)
        message_page.wait_for_table_load()
        row_count = message_page.get_row_count()
        if row_count > baseline_count:
            break
        time.sleep(MESSAGES_SEARCH_INTERVAL_SECONDS)

    assert row_count > baseline_count, (
        f"No new message record appeared in SMS Channel -> Messages for "
        f"recipient {recipient_number} within "
        f"{MESSAGES_SEARCH_TIMEOUT_SECONDS}s (baseline row count was "
        f"{baseline_count}, still {row_count})."
    )

    # ── Step 7: identify the latest matching message (not just the first
    #            search result) -- see find_latest_matching_row() ──────────
    row_index = find_latest_matching_row(message_page, record_property, label=recipient_number)

    # ── Step 8: click View for that message ──────────────────────────────
    message_page.click_view_icon(row_index)
    assert message_page.is_popup_open(), (
        f"View button/popup did not open for row {row_index} "
        f"(recipient {recipient_number})."
    )

    # ── Step 9: extract message_id from the message details ─────────────
    message_id = message_page.get_popup_message_id()
    message_page.close_popup()

    assert message_id, (
        f"Could not extract a 'message_id' from the message details popup "
        f"for row {row_index} (recipient {recipient_number})."
    )
    record_property("message_id", message_id)

    # ── Step 10-11: call the DLR Receiver, verify success ────────────────
    dlr_response, dlr_body, fields = poll_for_dlr(api_client, message_id)

    assert dlr_response is not None, (
        "DLR API was never called -- unexpected internal state."
    )
    record_property("Response", dlr_response.text)

    record_property("Expected", "200")
    record_property("Actual", str(dlr_response.status_code))
    assert dlr_response.status_code == 200, (
        f"DLR API could not be accessed / did not return a successful "
        f"response for message_id={message_id} within "
        f"{DLR_POLL_TIMEOUT_SECONDS}s. Got {dlr_response.status_code}. "
        f"Body: {dlr_response.text}"
    )
    assert dlr_body is not None, (
        f"DLR API returned 200 but the body wasn't valid JSON. "
        f"Body: {dlr_response.text}"
    )

    # ── Step 12: received = true ──────────────────────────────────────────
    assert fields["received"] is True, (
        f"DLR was not received within {DLR_POLL_TIMEOUT_SECONDS}s for "
        f"message_id={message_id} (received={fields['received']!r}). "
        f"Body: {dlr_body}"
    )

    # ── Step 13: DLR message_id matches the Messages-page message_id ────
    assert fields["message_id"] == message_id, (
        f"DLR message_id ({fields['message_id']!r}) does not match the "
        f"message_id obtained from the Messages page ({message_id!r}). "
        f"Body: {dlr_body}"
    )

    # ── Step 14: PASS ──────────────────────────────────────────────────────
    # All assertions above passed -- reception + correlation confirmed.
    # Deliberately NOT asserting on status / provider_status / status_code
    # anywhere in the DLR body, per the spec's explicit instruction.
