"""
test_sms_campaign_dlr.py

Test Case: Verify DLR is received after sending SMS campaign
Send API: POST /api/sms/campaign/send
DLR API:  GET {dlr_base_url}/api/v1/dlr/{message_id}

Provided directly by the project owner as a test-case spec (steps,
expected result table, and explicit failure conditions) -- not derived
from a documented DLR response schema, since none was supplied. The
only DLR response fields confirmed by that spec are `received` and
`message_id` (see steps 6-7 below); this test does NOT assume or check
any other field name. On an assertion failure the full raw DLR body is
always included in the message so a real, unconfirmed field can be
identified and the test tightened later -- not guessed at now.

IMPORTANT, per the spec's own "Note": this test deliberately does NOT
assert on `status`, `provider_status`, `status_code`, or any particular
delivery-status value anywhere in the DLR body. It only validates DLR
reception and correlation (received=true + message_id match). Do not
add a delivery-status assertion here without a fresh instruction to do
so -- that would directly contradict the spec's stated intent.

DLR generation is asynchronous relative to the campaign-send call, so
step 3 ("wait for the DLR to be generated") is implemented as a bounded
poll loop, not a fixed sleep -- see utils/dlr_helpers.py, shared with
the sibling DLR tests (test_sms_send_dlr.py, test_sms_template_send_dlr.py,
test_sms_send_msg_dlr.py) so the poll/extraction logic stays in one
place instead of four independent copies.
"""

import pytest

from utils.dlr_format_validator import (
    build_dlr_validation_report,
    extract_full_dlr_fields,
    validate_dlr_correlation,
    validate_dlr_format,
)
from utils.dlr_helpers import (
    DLR_POLL_TIMEOUT_SECONDS,
    extract_message_id_from_send_response,
    poll_for_dlr,
)

pytestmark = pytest.mark.sms


@pytest.mark.smoke
def test_dlr_received_after_campaign_send(api_client, test_data, record_property):
    # ── Step 1-2: send the campaign, capture message_id ─────────────────────
    payload = test_data["campaign_send"]["valid_payload"]
    send_response = api_client.send_campaign(payload)
    record_property("Response", send_response.text)

    record_property("Expected", "200")
    record_property("Actual", str(send_response.status_code))
    assert send_response.status_code == 200, (
        f"SMS send API failed: expected 200, got "
        f"{send_response.status_code}. Body: {send_response.text}"
    )

    send_body = send_response.json()
    message_id = extract_message_id_from_send_response(send_body)
    assert message_id, (
        f"'message_id' missing/empty in the campaign send response's "
        f"data[0]. Got: {send_body}"
    )
    record_property("message_id", message_id)

    # ── Step 3-4: poll the DLR API until it has a record for message_id ─────
    dlr_response, dlr_body, fields = poll_for_dlr(api_client, message_id)

    assert dlr_response is not None, (
        "DLR API was never called -- unexpected internal state."
    )
    record_property("Response", dlr_response.text)

    # ── Step 5: DLR API returns a successful response ────────────────────────
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

    # ── Step 6: received = true ──────────────────────────────────────────────
    assert fields["received"] is True, (
        f"DLR was not received within {DLR_POLL_TIMEOUT_SECONDS}s for "
        f"message_id={message_id} (received={fields['received']!r}). "
        f"Body: {dlr_body}"
    )

    # ── Step 7: DLR message_id matches the SMS send message_id ──────────────
    assert fields["message_id"] == message_id, (
        f"DLR message_id ({fields['message_id']!r}) does not match the SMS "
        f"send message_id ({message_id!r}). Body: {dlr_body}"
    )

    # ── Step 8: DLR successfully received and stored ────────────────────────
    # No separate "stored" field was given in the spec -- a 200 response
    # with received=true and a matching message_id (steps 5-7 above) IS
    # the confirmation that the DLR was received and is queryable/stored.
    # Deliberately NOT asserting on status / provider_status / status_code
    # or any delivery-status value anywhere in dlr_body, per the spec's
    # explicit "Note".

    # ── DLR Format/Schema Verification (generic test -- status/code are
    #               only checked to EXIST, never compared to a specific
    #               value, per the "Important Existing DLR Rule") ────────
    dlr_fields_full = extract_full_dlr_fields(dlr_body)
    format_result = validate_dlr_format(dlr_fields_full)
    correlation_result = validate_dlr_correlation(dlr_fields_full, expected_message_id=message_id)
    report = build_dlr_validation_report(format_result, correlation_result)
    record_property("DLR Validation Report", report)
    print("\n" + report)
    assert format_result["passed"], (
        f"DLR format/schema validation failed for message_id={message_id}: "
        f"{format_result['failed_fields']}.\n{report}\nBody: {dlr_body}"
    )
    assert correlation_result["passed"], (
        f"DLR correlation failed for message_id={message_id}: "
        f"{correlation_result['detail']}.\n{report}\nBody: {dlr_body}"
    )
