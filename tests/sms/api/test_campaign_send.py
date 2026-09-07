"""
test_campaign_send.py

Tests for POST /api/sms/campaign/send
(This endpoint isn't documented in the v2.2 PDF but was provided via the
sample curl command — assertions here are intentionally light/structural
and should be tightened once the endpoint is formally documented.)

MIGRATION NOTE: header-edge-case tests that previously used a raw
`import requests` call now use `api_client.send_campaign(payload,
headers=...)` / `api_client.post_raw(...)` — all requests go through
Playwright's APIRequestContext.
"""

import pytest

pytestmark = pytest.mark.sms


@pytest.mark.smoke
def test_send_campaign_valid_payload_returns_success(api_client, test_data, env_config, record_property):
    payload = test_data["campaign_send"]["valid_payload"]

    response = api_client.send_campaign(payload)

    record_property("Expected", "200")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Body: {response.text}"
    )

    body = response.json()
    assert body.get("status") == "success"
    assert "data" in body
    assert isinstance(body["data"], list)

    for entry in body["data"]:
        assert entry["status"] in ("queued", "submitted")
        assert "message_id" in entry


@pytest.mark.negative
def test_send_campaign_missing_id_returns_error(api_client, test_data, record_property):
    payload = test_data["campaign_send"]["missing_id_payload"]

    response = api_client.send_campaign(payload)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 422 for missing 'id', got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_campaign_missing_to_returns_error(api_client, test_data, record_property):
    payload = test_data["campaign_send"]["missing_to_payload"]

    response = api_client.send_campaign(payload)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 422 for missing 'to', got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_campaign_unauthorized_without_token(api_client, test_data, record_property):
    payload = test_data["campaign_send"]["valid_payload"]
    bad_headers = dict(api_client.env.headers)
    bad_headers["Authorization"] = "Bearer invalid-token-for-testing"

    response = api_client.send_campaign(payload, headers=bad_headers)

    record_property("Expected", "401")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 401, (
        f"Expected 401 for invalid token, got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_campaign_missing_authorization_header_entirely(api_client, test_data, record_property):
    payload = test_data["campaign_send"]["valid_payload"]
    headers_without_auth = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    response = api_client.send_campaign(payload, headers=headers_without_auth)

    record_property("Expected", "401")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 401, (
        f"Expected 401 when Authorization header is entirely absent, got "
        f"{response.status_code}. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_campaign_missing_params(api_client, test_data, record_property):
    payload = test_data["campaign_send"]["missing_params_payload"]

    response = api_client.send_campaign(payload)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected a handled response for missing 'params', got "
        f"{response.status_code}. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_campaign_empty_params(api_client, test_data, record_property):
    payload = test_data["campaign_send"]["empty_params_payload"]

    response = api_client.send_campaign(payload)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected a handled response for empty 'params', got "
        f"{response.status_code}. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_campaign_invalid_id_format(api_client, test_data, record_property):
    """id is expected to be a UUID based on the sample curl; confirms
    behavior when a non-UUID string is sent instead."""
    payload = test_data["campaign_send"]["invalid_id_format_payload"]

    response = api_client.send_campaign(payload)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected a handled response for a malformed 'id', got "
        f"{response.status_code} — possible unhandled server error. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_campaign_malformed_json_body(api_client, record_property):
    """Same behavior as the sms/send endpoint: malformed JSON is treated
    as an empty/partial body and validated field-by-field, returning 422."""
    response = api_client.post_raw(
        api_client.env.campaign_send_url,
        raw_body='{"id": "abc", "to": ["917002088565", "params": {}}',
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
