"""
test_sms_json.py

Tests for POST /api/sms/json
Not in the v2.2 API doc. This endpoint takes a `root` object (default
from/text/to values) plus a `data` array of per-message entries. Entries
can omit fields to inherit them from `root` — that inheritance behavior
is the main thing worth verifying here, since a real sample payload
deliberately included partial entries (missing `from`, missing `to`,
missing `text`, and one fully-empty `{}` entry).

Assertions are intentionally tolerant where behavior is unconfirmed;
tighten them once responses are observed against the real instance.

MIGRATION NOTE: header-edge-case and malformed-body tests that previously
used a raw `import requests` call now use `api_client.send_json(payload,
headers=...)` / `api_client.post_raw(...)` — all requests go through
Playwright's APIRequestContext.
"""

import copy

import pytest

pytestmark = pytest.mark.sms


@pytest.mark.smoke
def test_send_json_real_sample_payload(api_client, test_data, record_property):
    """The exact payload structure provided, including the deliberately
    incomplete entries meant to exercise root inheritance."""
    payload = test_data["sms_json"]["real_sample_payload"]

    response = api_client.send_json(payload)

    record_property("Expected", "200")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Body: {response.text}"
    )
    body = response.json()
    assert body.get("status") == "success"

    # Total messages sent should match the number of `data` entries
    # (root itself isn't a separate message — it's just defaults).
    if isinstance(body.get("data"), list):
        assert len(body["data"]) == len(payload["data"]), (
            f"Expected {len(payload['data'])} results (one per data "
            f"entry), got {len(body.get('data', []))}. Body: {response.text}"
        )
        for entry in body["data"]:
            assert entry["status"] in ("queued", "submitted")
            assert "message_id" in entry


@pytest.mark.smoke
def test_send_json_minimal_valid_payload(api_client, test_data, record_property):
    payload = test_data["sms_json"]["minimal_valid_payload"]

    response = api_client.send_json(payload)

    record_property("Expected", "200")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Body: {response.text}"
    )

    body = response.json()
    assert body.get("status") == "success"
    if isinstance(body.get("data"), list):
        assert len(body["data"]) == len(payload["data"])
        for entry in body["data"]:
            assert entry["status"] in ("queued", "submitted")
            assert "message_id" in entry


@pytest.mark.regression
def test_send_json_response_time_within_timeout(api_client, test_data, env_config, record_property):
    payload = test_data["sms_json"]["minimal_valid_payload"]
    response = api_client.send_json(payload)
    assert response.elapsed.total_seconds() < env_config.timeout_seconds


@pytest.mark.regression
def test_send_json_missing_root(api_client, test_data, record_property):
    """API accepts a missing 'root' when data entries are self-contained
    (returns 200). Observed on dev — root is not enforced server-side."""
    payload = test_data["sms_json"]["missing_root_payload"]

    response = api_client.send_json(payload)

    record_property("Expected", "200")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 200, (
        f"Expected 200 for a missing 'root' object (self-contained data entry), got "
        f"{response.status_code}. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_json_missing_data_array(api_client, test_data, record_property):
    payload = test_data["sms_json"]["missing_data_payload"]

    response = api_client.send_json(payload)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 422 for a missing 'data' array, got "
        f"{response.status_code}. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_json_empty_data_array(api_client, test_data, record_property):
    payload = test_data["sms_json"]["empty_data_array_payload"]

    response = api_client.send_json(payload)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected a handled response for an empty 'data' array, got "
        f"{response.status_code}. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_json_root_missing_from(api_client, test_data, record_property):
    """If root itself is missing 'from' and the data entry doesn't supply
    one either, there's nothing to inherit — documents the failure mode."""
    payload = test_data["sms_json"]["root_missing_from"]

    response = api_client.send_json(payload)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected a handled response when root is missing 'from' with "
        f"no override, got {response.status_code} — possible unhandled "
        f"server error. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_json_root_missing_text(api_client, test_data, record_property):
    payload = test_data["sms_json"]["root_missing_text"]

    response = api_client.send_json(payload)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected a handled response when root is missing 'text' with "
        f"no override, got {response.status_code} — possible unhandled "
        f"server error. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_json_root_missing_to(api_client, test_data, record_property):
    payload = test_data["sms_json"]["root_missing_to"]

    response = api_client.send_json(payload)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected a handled response when root is missing 'to' with no "
        f"override, got {response.status_code} — possible unhandled "
        f"server error. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_json_entry_with_invalid_override_number(api_client, test_data, record_property):
    payload = test_data["sms_json"]["entry_invalid_number"]

    response = api_client.send_json(payload)

    record_property("Expected", "(200, 422)")
    record_property("Actual", str(response.status_code))
    assert response.status_code in (200, 422), (
        f"Expected 200 (partial success) or 422 (whole-batch reject) for "
        f"an invalid overridden number, got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_json_entry_with_invalid_type_value(api_client, test_data, record_property):
    payload = test_data["sms_json"]["entry_with_invalid_type_value"]

    response = api_client.send_json(payload)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected a handled response for an invalid 'type' override, "
        f"got {response.status_code}. Body: {response.text}"
    )


@pytest.mark.regression
def test_send_json_unicode_text_entry(api_client, test_data, record_property):
    """The real sample payload includes a Hindi-language entry — confirm
    it's accepted and processed like any other message."""
    payload = test_data["sms_json"]["real_sample_payload"]
    unicode_entry = payload["data"][0]
    assert "सुप्रभात" in unicode_entry["text"], (
        "Test fixture should contain the Unicode sample entry"
    )

    minimal_unicode_payload = {
        "root": payload["root"],
        "data": [unicode_entry],
    }

    response = api_client.send_json(minimal_unicode_payload)

    record_property("Expected", "200")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 200, (
        f"Expected 200 for a Unicode-text data entry, got "
        f"{response.status_code}. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_json_unauthorized_without_token(api_client, test_data, record_property):
    payload = test_data["sms_json"]["minimal_valid_payload"]
    bad_headers = dict(api_client.env.headers)
    bad_headers["Authorization"] = "Bearer invalid-token-for-testing"

    response = api_client.send_json(payload, headers=bad_headers)

    record_property("Expected", "401")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 401, (
        f"Expected 401 for invalid token, got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_json_missing_authorization_header_entirely(api_client, test_data, record_property):
    payload = test_data["sms_json"]["minimal_valid_payload"]
    headers_without_auth = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    response = api_client.send_json(payload, headers=headers_without_auth)

    record_property("Expected", "401")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 401, (
        f"Expected 401 when Authorization header is entirely absent, got "
        f"{response.status_code}. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_json_malformed_json_body(api_client, record_property):
    """Same expected behavior as the other JSON-body endpoints: malformed
    JSON is treated as an empty/partial body and validated field-by-field
    rather than rejected with a raw 400 parse error."""
    response = api_client.post_raw(
        api_client.env.sms_json_url,
        raw_body='{"root": {"from": "X", "data": []}',  # missing closing brace
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
