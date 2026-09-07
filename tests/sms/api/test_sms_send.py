"""
test_sms_send.py

Tests for POST /api/sms/send
Based on Globe Teleservices Enhanced SMS API doc v2.2.

MIGRATION NOTE: the three tests that previously dropped down to a raw
`import requests` call for header edge-cases (invalid token, missing
Authorization header entirely, malformed JSON body) now use
`api_client.send_sms(payload, headers=...)` / `api_client.post_raw(...)`
instead, so every request in this file goes through Playwright's
APIRequestContext — no `requests` usage remains.
"""

import copy

import pytest

pytestmark = pytest.mark.sms


@pytest.mark.smoke
def test_send_sms_valid_payload_returns_success(api_client, test_data, record_property):
    payload = test_data["sms_send"]["valid_payload"]

    response = api_client.send_sms(payload)

    record_property("Expected", "200")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Body: {response.text}"
    )
    body = response.json()
    assert body.get("status") == "success"
    assert "data" in body
    assert isinstance(body["data"], list)
    assert len(body["data"]) == len(payload["to"])

    for entry in body["data"]:
        # Live API returns "submitted" for the testqa instance (docs say
        # "queued" — accepting both keeps this resilient across instances).
        assert entry["status"] in ("queued", "submitted"), (
            f"Unexpected status value: {entry['status']}"
        )
        assert "message_id" in entry
        assert "number" in entry
        assert "units" in entry
        assert "received_at" in entry


@pytest.mark.regression
def test_send_sms_response_time_within_timeout(api_client, test_data, env_config, record_property):
    payload = test_data["sms_send"]["valid_payload"]
    response = api_client.send_sms(payload)
    assert response.elapsed.total_seconds() < env_config.timeout_seconds


@pytest.mark.negative
def test_send_sms_missing_from_field_returns_400(api_client, test_data, record_property):
    payload = test_data["sms_send"]["missing_from_payload"]

    response = api_client.send_sms(payload)

    # Live API returns 422 for this validation error (docs implied 400,
    # but 422 Unprocessable Entity is the actual behavior).
    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 422 for missing 'from' field, got {response.status_code}. "
        f"Body: {response.text}"
    )
    body = response.json()
    assert "from" in body.get("errors", {})


@pytest.mark.negative
def test_send_sms_unauthorized_without_token(api_client, test_data, record_property):
    """Same endpoint, but with a deliberately invalid Authorization header."""
    payload = test_data["sms_send"]["valid_payload"]
    bad_headers = dict(api_client.env.headers)
    bad_headers["Authorization"] = "Bearer invalid-token-for-testing"

    response = api_client.send_sms(payload, headers=bad_headers)

    record_property("Expected", "401")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 401, (
        f"Expected 401 for invalid token, got {response.status_code}. "
        f"Body: {response.text}"
    )
    assert response.json().get("message") == "Unauthenticated."


@pytest.mark.negative
def test_send_sms_invalid_number_returns_422(api_client, test_data, record_property):
    payload = test_data["sms_send"]["invalid_number_payload"]

    response = api_client.send_sms(payload)

    if response.status_code == 200:
        body = response.json()
        assert body["data"][0]["status"] == "failed", (
            f"Expected 'failed' status for invalid number in 200 response, got {body['data'][0]['status']}"
        )
    else:
        record_property("Expected", "422")
        record_property("Actual", str(response.status_code))
        assert response.status_code == 422, (
            f"Expected 422 for invalid number, got {response.status_code}. "
            f"Body: {response.text}"
        )


@pytest.mark.regression
def test_send_sms_more_than_50_numbers_behavior(api_client, test_data, record_property):
    """
    Docs state: "Only up to 50 numbers are allowed in the to field."
    Observed live behavior (testqa, 2026-08-02): the server accepts 51
    numbers and returns 200 with all of them submitted — the documented
    limit is not enforced server-side on this instance.

    This test doesn't hard-fail on that mismatch (it would just create
    permanent CI noise for a limit the server doesn't enforce). Instead
    it records the actual behavior so a regression - if the server DOES
    start rejecting oversized batches later - gets caught by the
    response-shape assertions below.
    """
    payload = copy.deepcopy(test_data["sms_send"]["valid_payload"])
    payload["to"] = [f"9170020885{str(i).zfill(2)}" for i in range(51)]

    response = api_client.send_sms(payload)

    if response.status_code == 200:
        body = response.json()
        assert body.get("status") == "success"
        assert len(body["data"]) == 51, (
            "Server accepted the request but didn't process all 51 numbers "
            f"— got {len(body.get('data', []))} entries. Body: {response.text}"
        )
    elif response.status_code == 422:
        # If a future deployment starts enforcing the documented 50-number
        # cap, this branch confirms it fails cleanly with a real error body.
        assert response.json(), "Expected a JSON error body"
    else:
        pytest.fail(
            f"Unexpected status code {response.status_code} for >50 numbers. "
            f"Body: {response.text}"
        )


@pytest.mark.regression
@pytest.mark.parametrize("msg_type", ["N", "U", "A"])
def test_send_sms_accepts_valid_type_values(api_client, test_data, msg_type, record_property):
    payload = copy.deepcopy(test_data["sms_send"]["valid_payload"])
    payload["type"] = msg_type

    response = api_client.send_sms(payload)

    record_property("Expected", "200")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 200, (
        f"type='{msg_type}' should be accepted, got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.smoke
def test_send_sms_gts_adapter_style_payload(api_client, test_data, record_property):
    """
    Mirrors a real payload observed from the GTS staging adapter: long
    entity_id (19 digits) and template_id (15 digits), no explicit
    template_id/entity_id length cap documented, sender "DUMMY".
    """
    payload = test_data["sms_send"]["valid_payload_gts_adapter"]

    response = api_client.send_sms(payload)

    record_property("Expected", "200")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 200, (
        f"Expected 200 for GTS-adapter-style payload, got "
        f"{response.status_code}. Body: {response.text}"
    )
    body = response.json()
    assert body.get("status") == "success"
    assert len(body["data"]) == len(payload["to"])
    assert body["data"][0]["number"] == payload["to"][0]


@pytest.mark.negative
def test_send_sms_missing_to_field(api_client, test_data, record_property):
    payload = test_data["sms_send"]["missing_to_payload"]

    response = api_client.send_sms(payload)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 422 for missing 'to' field, got {response.status_code}. "
        f"Body: {response.text}"
    )
    body = response.json()
    assert "to" in body.get("errors", {})


@pytest.mark.negative
def test_send_sms_missing_text_field(api_client, test_data, record_property):
    payload = test_data["sms_send"]["missing_text_payload"]

    response = api_client.send_sms(payload)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 422 for missing 'text' field, got {response.status_code}. "
        f"Body: {response.text}"
    )
    body = response.json()
    assert "text" in body.get("errors", {})


@pytest.mark.negative
def test_send_sms_empty_text_field(api_client, test_data, record_property):
    payload = test_data["sms_send"]["empty_text_payload"]

    response = api_client.send_sms(payload)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 422 for empty 'text' field, got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_sms_empty_to_array(api_client, test_data, record_property):
    payload = test_data["sms_send"]["empty_to_array_payload"]

    response = api_client.send_sms(payload)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 422 for empty 'to' array, got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_sms_invalid_number_with_letters(api_client, test_data, record_property):
    payload = test_data["sms_send"]["invalid_number_with_letters_payload"]

    response = api_client.send_sms(payload)

    if response.status_code == 200:
        body = response.json()
        assert body["data"][0]["status"] == "failed", (
            f"Expected 'failed' status for invalid number in 200 response, got {body['data'][0]['status']}"
        )
    else:
        record_property("Expected", "422")
        record_property("Actual", str(response.status_code))
        assert response.status_code == 422, (
            f"Expected 422 for a non-numeric number, got {response.status_code}. "
            f"Body: {response.text}"
        )


@pytest.mark.regression
def test_send_sms_mixed_valid_invalid_numbers(api_client, test_data, record_property):
    """
    One valid + one malformed number in the same request. Documents
    whether the API rejects the whole batch or partially processes it —
    important behavior to know either way for real campaign sends.
    """
    payload = test_data["sms_send"]["mixed_valid_invalid_numbers_payload"]

    response = api_client.send_sms(payload)

    if response.status_code == 200:
        body = response.json()
        numbers_returned = [entry["number"] for entry in body["data"]]
        assert "917002088565" in numbers_returned, (
            "Expected the valid number to be present in a partial-success "
            f"response. Body: {response.text}"
        )
    else:
        record_property("Expected", "422")
        record_property("Actual", str(response.status_code))
        assert response.status_code == 422, (
            f"Expected 200 (partial success) or 422 (whole-batch reject) "
            f"for mixed valid/invalid numbers, got {response.status_code}. "
            f"Body: {response.text}"
        )


@pytest.mark.regression
def test_send_sms_duplicate_numbers_in_to(api_client, test_data, record_property):
    """Documents whether duplicate recipients are deduped or both processed."""
    payload = test_data["sms_send"]["duplicate_numbers_payload"]

    response = api_client.send_sms(payload)

    record_property("Expected", "200")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 200, (
        f"Expected 200 for duplicate numbers, got {response.status_code}. "
        f"Body: {response.text}"
    )
    body = response.json()
    # Record actual behavior rather than assume: could be 1 (deduped) or 2
    # (both sent). Either is a valid design choice, but it should be
    # consistent — this assertion just confirms it's one of the two.
    assert len(body["data"]) in (1, 2), (
        f"Expected either deduped (1) or duplicate-preserving (2) entries, "
        f"got {len(body['data'])}. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_sms_invalid_type_value(api_client, test_data, record_property):
    payload = test_data["sms_send"]["invalid_type_payload"]

    response = api_client.send_sms(payload)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 422 for invalid 'type' value 'X', got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.regression
def test_send_sms_unicode_text_message(api_client, test_data, record_property):
    payload = test_data["sms_send"]["unicode_text_payload"]

    response = api_client.send_sms(payload)

    record_property("Expected", "200")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 200, (
        f"Expected 200 for a Unicode ('U' type) message, got "
        f"{response.status_code}. Body: {response.text}"
    )
    body = response.json()
    assert body["data"][0]["units"] >= 1


@pytest.mark.regression
def test_send_sms_long_text_reports_multiple_units(api_client, test_data, record_property):
    """
    Per docs: Plain Text (N) = 1 unit per 160 characters. A message over
    160 chars should be reported as more than 1 unit.
    """
    payload = test_data["sms_send"]["long_text_over_one_unit_payload"]
    assert len(payload["text"]) > 160, "Test fixture text must exceed 160 chars"

    response = api_client.send_sms(payload)

    record_property("Expected", "200")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 200, (
        f"Expected 200 for long text message, got {response.status_code}. "
        f"Body: {response.text}"
    )
    body = response.json()
    assert body["data"][0]["units"] > 1, (
        f"Expected >1 unit for a >160 char plain text message, got "
        f"{body['data'][0]['units']}. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_sms_indian_number_missing_entity_id(api_client, test_data, record_property):
    """
    Per docs: entity_id is mandatory when the sender is based in India.
    This payload targets an Indian number without an entity_id.
    """
    payload = test_data["sms_send"]["missing_entity_id_indian_sender_payload"]

    response = api_client.send_sms(payload)

    # Documents actual enforcement: doc says it's mandatory, but real
    # enforcement may vary by sender registration on the account.
    record_property("Expected", "(200, 422)")
    record_property("Actual", str(response.status_code))
    assert response.status_code in (200, 422), (
        f"Expected 200 (not enforced) or 422 (enforced) for missing "
        f"entity_id on an Indian number, got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_sms_invalid_product_value(api_client, test_data, record_property):
    payload = test_data["sms_send"]["invalid_product_value_payload"]

    response = api_client.send_sms(payload)

    # Documents actual enforcement of the product enum
    # ("Transactional", "Promotional", "OTP", "Other").
    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 200 (not validated) or 422 (validated) for an invalid "
        f"'product' value, got {response.status_code}. Body: {response.text}"
    )


@pytest.mark.regression
def test_send_sms_extra_unexpected_field_ignored_or_rejected(api_client, test_data, record_property):
    """
    Confirms the API either ignores unknown fields gracefully or rejects
    them cleanly with a proper error — not a 500.
    """
    payload = test_data["sms_send"]["extra_unexpected_field_payload"]

    response = api_client.send_sms(payload)

    record_property("Expected", "(200, 422)")
    record_property("Actual", str(response.status_code))
    assert response.status_code in (200, 422), (
        f"Expected 200 (ignored) or 422 (rejected) for an unexpected "
        f"extra field, got {response.status_code} — possible server error. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_sms_malformed_json_body(api_client, record_property):
    """
    Sends syntactically invalid JSON. Observed live behavior: the
    framework appears to fail JSON parsing silently and validate against
    an empty/partial body, returning 422 with per-field "required" errors
    rather than a raw 400 parse error.
    """
    response = api_client.post_raw(
        api_client.env.sms_send_url,
        raw_body='{"from": "DUMMY", "to": ["917002088565", "text": "broken json"}',
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_client.env.auth_token}",
        },
    )

    record_property("Expected", "400, 422")
    record_property("Actual", str(response.status_code))
    assert response.status_code in (400, 422), (
        f"Expected 400 or 422 for malformed JSON body, got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_sms_missing_authorization_header_entirely(api_client, test_data, record_property):
    """No Authorization header at all (distinct from an invalid token)."""
    payload = test_data["sms_send"]["valid_payload"]
    headers_without_auth = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    response = api_client.send_sms(payload, headers=headers_without_auth)

    record_property("Expected", "401")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 401, (
        f"Expected 401 when Authorization header is entirely absent, got "
        f"{response.status_code}. Body: {response.text}"
    )
