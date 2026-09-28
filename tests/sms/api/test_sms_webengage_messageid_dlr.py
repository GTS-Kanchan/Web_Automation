"""
test_sms_webengage_messageid_dlr.py

Test Case: Verify WebEngage SMS DLR using messageId
Send API: POST /api/v1/sms/webengage/send
DLR API:  GET {dlr_base_url}/api/v1/dlr/{message_id}

Provided directly by the project owner as a test-case spec. Unlike the
sibling "Verify WebEngage SMS DLR" test (test_sms_webengage_dlr.py in
this same directory), this one explicitly does NOT read the message_id
off the SMS Channel -> Messages UI -- the spec's own closing line says
so: "Do not search the Messages tab or obtain the message ID from the
UI." Instead, a messageId is generated locally, sent as
metadata.messageId in the WebEngage request, and that exact same value
is used directly as the DLR lookup identifier. This makes the test pure
API, no browser needed.

metadata.messageId is a real, already-confirmed field in this
endpoint's payload shape (see test_data.yaml's
webengage_send.valid_payload, previously a fixed dummy value
"111112222333334444555" there) -- generating a fresh one per run is a
legitimate use of that same field, not a new/unconfirmed one.

Generated ID format: the spec's own example ("11111222233333447982")
is a purely numeric string, matching the existing fixed test-data
value's shape -- so the generated ID here is built the same way
(digits only). No exact required length/format was confirmed beyond
that example, so this doesn't try to match its length precisely; it
only mirrors "numeric string" to stay consistent with the one real
sample given.

IMPORTANT, per the spec: this test deliberately does NOT assert on
`status`, `provider_status`, or `status_code` anywhere in the DLR body.
"""

import copy
import random
import string
import time

import pytest

from utils.dlr_helpers import DLR_POLL_TIMEOUT_SECONDS, poll_for_dlr

pytestmark = pytest.mark.sms


def _generate_numeric_message_id() -> str:
    """Numeric-only ID, mirroring the shape of the spec's own example
    ("11111222233333447982") and the existing fixed test-data value
    ("111112222333334444555") -- timestamp prefix (for rough uniqueness/
    traceability) + random digits, no exact length/format was confirmed
    beyond "numeric string"."""
    return str(int(time.time())) + "".join(random.choices(string.digits, k=8))


@pytest.mark.smoke
def test_dlr_received_after_webengage_send_using_message_id(api_client, test_data, record_property):
    # ── Step 1-2: generate a unique messageId, add it to the request ────────
    message_id = _generate_numeric_message_id()
    assert message_id, "Failed to generate a messageId for this test run."
    record_property("Generated messageId", message_id)

    payload = copy.deepcopy(test_data["webengage_send"]["valid_payload"])
    payload["metadata"]["messageId"] = message_id

    # ── Step 3-4: send via /api/v1/sms/webengage/send, verify response ──────
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

    # ── Step 5-6: wait for + call the DLR Receiver using the SAME
    #              metadata.messageId that was sent -- never the UI ─────────
    dlr_response, dlr_body, fields = poll_for_dlr(api_client, message_id)

    assert dlr_response is not None, (
        "DLR API was never called -- unexpected internal state."
    )
    record_property("Response", dlr_response.text)

    # ── Step 7: DLR API returns a successful response ────────────────────────
    record_property("Expected", "200")
    record_property("Actual", str(dlr_response.status_code))
    assert dlr_response.status_code == 200, (
        f"DLR Receiver API could not be accessed / did not return a "
        f"successful response for message_id={message_id} within "
        f"{DLR_POLL_TIMEOUT_SECONDS}s. Got {dlr_response.status_code}. "
        f"Body: {dlr_response.text}"
    )
    assert dlr_body is not None, (
        f"DLR API returned 200 but the body wasn't valid JSON. "
        f"Body: {dlr_response.text}"
    )

    # ── Step 8: received = true ──────────────────────────────────────────────
    assert fields["received"] is True, (
        f"DLR was not received within {DLR_POLL_TIMEOUT_SECONDS}s for "
        f"message_id={message_id} (received={fields['received']!r}). "
        f"Body: {dlr_body}"
    )

    # ── Step 9: DLR message_id matches the generated metadata.messageId ─────
    assert fields["message_id"] == message_id, (
        f"DLR message_id ({fields['message_id']!r}) does not match the "
        f"generated metadata.messageId sent in the WebEngage request "
        f"({message_id!r}). Body: {dlr_body}"
    )

    # DLR received + correlated + a 200 response (steps 7-9 above) IS the
    # confirmation the DLR was received and stored -- no separate "stored"
    # field was given in the spec. Deliberately NOT asserting on
    # status / provider_status / status_code anywhere in dlr_body.
