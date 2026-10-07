"""
test_sms_template_send_dlr.py

Test Case: TC-02 -- Verify DLR for /api/sms/template/send
Send API: POST /api/sms/template/send
DLR API:  GET {dlr_base_url}/api/v1/dlr/{message_id}

Provided directly by the project owner as a test-case spec (steps and
explicit failure conditions). Confirmed response shape for
/api/sms/template/send (see test_template_send.py): a top-level `data`
list, each entry carrying its own `message_id` -- same shape as
/api/sms/send and /api/sms/campaign/send, so this test reuses the
shared utils/dlr_helpers.py extraction/poll logic.

test_data.yaml's template_send.valid_payload sends to TWO recipients
("to": [<num1>, <num2>]), so the send response's `data` list has two
entries. The spec's flow is singular ("the message_id"), so this test
follows the confirmed pattern already used elsewhere in this suite
(campaign/sms-send DLR tests) and takes data[0] -- the first recipient's
message_id -- as *the* identifier to correlate against the DLR API.
Flagging this rather than silently assuming it: if the DLR spec
actually intends per-recipient DLR verification for multi-recipient
sends, that would need a fresh instruction/spec to implement.

IMPORTANT, per the spec: this test deliberately does NOT assert on
`status`, `provider_status`, `status_code`, or any particular
delivery-status value anywhere in the DLR body. It only validates DLR
reception and correlation (received=true + message_id match). Do not
add a delivery-status assertion here without a fresh instruction to do
so -- that would directly contradict the spec's stated intent.
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
def test_dlr_received_after_template_send(api_client, test_data, record_property):
    # ── Step 1-2: send the templated SMS, capture message_id ────────────────
    payload = test_data["template_send"]["valid_payload"]
    send_response = api_client.send_template(payload)
    record_property("Response", send_response.text)

    record_property("Expected", "200")
    record_property("Actual", str(send_response.status_code))
    assert send_response.status_code == 200, (
        f"SMS template send API failed: expected 200, got "
        f"{send_response.status_code}. Body: {send_response.text}"
    )

    send_body = send_response.json()
    message_id = extract_message_id_from_send_response(send_body)
    assert message_id, (
        f"'message_id' missing/empty in the template send response's "
        f"data[0]. Got: {send_body}"
    )
    record_property("message_id", message_id)

    # ── Step 3-4: wait for + call the DLR API ────────────────────────────────
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

    # ── Step 7: DLR message_id matches the SMS message_id ───────────────────
    assert fields["message_id"] == message_id, (
        f"DLR message_id ({fields['message_id']!r}) does not match the SMS "
        f"send message_id ({message_id!r}). Body: {dlr_body}"
    )

    # ── Step 8: DLR is received and stored ───────────────────────────────────
    # No separate "stored" field was given in the spec -- a 200 response
    # with received=true and a matching message_id (steps 5-7) IS the
    # confirmation. Deliberately NOT asserting on status / provider_status /
    # status_code or any delivery-status value anywhere in dlr_body.

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
