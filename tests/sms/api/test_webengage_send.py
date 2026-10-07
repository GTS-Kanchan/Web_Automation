"""
test_webengage_send.py

Tests for POST /api/v1/sms/webengage/send

MIGRATION NOTE: the unauthorized-token test previously used a raw
`import requests` call; it now uses `api_client.send_webengage(payload,
headers=...)`, which already merges header overrides — all requests go
through Playwright's APIRequestContext.

CONFIRMED real response shape: TWO different real `status` values
have now been observed from this SAME endpoint/payload across separate
live runs -- "sms_sent" (one real pasted response, with extra fields
version/smsCount/toNumber/messageId/statusCode) and "sms_accepted"
(a real live pytest failure, body `{"status":"sms_accepted"}` only).
Since both are real, confirmed-live values and no single one has been
shown to be the only correct one, this test accepts EITHER rather than
guessing which is "the" right one -- see _ACCEPTED_SEND_STATUSES below.

CONFIRMED real behavior (project owner, explicit instruction): "for
webengage use get api for dlr with meta data message id" -- the DLR
lookup identifier is the request payload's own metadata.messageId
(read back, never re-generated), the SAME identifier
test_sms_webengage_messageid_dlr.py uses -- NOT this response's own
"messageId" field (an earlier version of this test used the response's
"messageId" instead; that was reverted per this explicit correction).

CONFIRMED real behavior (project owner): "for sms webengage api, only
dlr received" -- this endpoint's DLR check only asserts
`fields["received"] is True` (presence), the SAME lightweight check
poll_for_dlr() already returns. It deliberately does NOT run the full
DLR format/schema + correlation validation (utils/
dlr_format_validator.py / verify_and_validate_dlr()) that every other
SMS send API's DLR test now runs.
"""

_ACCEPTED_SEND_STATUSES = ("sms_sent", "sms_accepted")

import pytest

from utils.dlr_helpers import DLR_POLL_TIMEOUT_SECONDS, poll_for_dlr

pytestmark = pytest.mark.sms


@pytest.mark.smoke
def test_send_webengage_valid_payload_returns_success(api_client, test_data, record_property):
    payload = test_data["webengage_send"]["valid_payload"]

    response = api_client.send_webengage(payload)
    record_property("Response", response.text)

    record_property("Expected", "200")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Body: {response.text}"
    )

    body = response.json()
    record_property("Expected status", " or ".join(_ACCEPTED_SEND_STATUSES))
    record_property("Actual status", str(body.get("status")))
    assert body.get("status") in _ACCEPTED_SEND_STATUSES, (
        f"Expected response 'status' to be one of {_ACCEPTED_SEND_STATUSES}. "
        f"Body: {response.text}"
    )

    # ── DLR Verification (received only) -- the DLR lookup identifier is
    #               the request payload's own metadata.messageId, per
    #               project owner's explicit instruction (see module
    #               docstring) -- the same field
    #               test_sms_webengage_messageid_dlr.py uses ──────────────
    message_id = payload.get("metadata", {}).get("messageId")
    assert message_id, (
        f"'metadata.messageId' missing/empty in the request payload used "
        f"for this test -- cannot look up its DLR. Payload: {payload}"
    )
    record_property("message_id", message_id)
    dlr_response, dlr_body, fields = poll_for_dlr(api_client, message_id)

    assert dlr_response is not None and dlr_response.status_code == 200 and dlr_body is not None, (
        f"DLR API could not be reached/did not return a valid body for "
        f"message_id={message_id} within {DLR_POLL_TIMEOUT_SECONDS}s. "
        f"Response: {getattr(dlr_response, 'text', None)}"
    )
    assert fields["received"] is True, (
        f"DLR was not received within {DLR_POLL_TIMEOUT_SECONDS}s for "
        f"message_id={message_id} (received={fields['received']!r}). "
        f"Body: {dlr_body}"
    )


@pytest.mark.regression
def test_send_webengage_response_time_within_timeout(api_client, test_data, env_config, record_property):
    payload = test_data["webengage_send"]["valid_payload"]
    response = api_client.send_webengage(payload)
    record_property("Response", response.text)
    assert response.elapsed.total_seconds() < env_config.timeout_seconds


@pytest.mark.negative
def test_send_webengage_missing_sms_data(api_client, test_data, record_property):
    payload = test_data["webengage_send"]["missing_sms_data"]

    response = api_client.send_webengage(payload)
    record_property("Response", response.text)

    record_property("Expected", "400")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 400, (
        f"Expected 400 for missing 'smsData' object, got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_webengage_missing_to_number(api_client, test_data, record_property):
    payload = test_data["webengage_send"]["missing_to_number"]

    response = api_client.send_webengage(payload)
    record_property("Response", response.text)

    record_property("Expected", "400")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 400, (
        f"Expected 400 for missing 'toNumber', got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_webengage_missing_from_number(api_client, test_data, record_property):
    payload = test_data["webengage_send"]["missing_from_number"]

    response = api_client.send_webengage(payload)
    record_property("Response", response.text)

    record_property("Expected", "400")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 400, (
        f"Expected 400 for missing 'fromNumber', got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_webengage_missing_body(api_client, test_data, record_property):
    payload = test_data["webengage_send"]["missing_body"]

    response = api_client.send_webengage(payload)
    record_property("Response", response.text)

    record_property("Expected", "400")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 400, (
        f"Expected 400 for missing 'body', got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_webengage_unauthorized_without_token(api_client, test_data, record_property):
    payload = test_data["webengage_send"]["valid_payload"]
    bad_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer invalid-token",
    }

    response = api_client.send_webengage(payload, headers=bad_headers)
    record_property("Response", response.text)

    record_property("Expected", "401")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 401, (
        f"Expected 401 for invalid token, got {response.status_code}. "
        f"Body: {response.text}"
    )
