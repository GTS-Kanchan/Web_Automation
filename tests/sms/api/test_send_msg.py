"""
test_send_msg.py

Tests for POST /api/sms/send-msg
This endpoint isn't in the v2.2 API doc and is structurally different
from the other three: it takes its data entirely as URL query parameters
(campaign_id, phone, params) rather than a JSON request body — there's
no Content-Type: application/json on the request at all in the sample
curl command.

`params` is a JSON array encoded as a single query-string value, e.g.
params=["test","test2","test2","test2"].

Assertions here are intentionally tolerant where behavior is unconfirmed;
tighten them once responses are observed against the real instance.

MIGRATION NOTE: header-edge-case tests and the malformed-params test that
previously used a raw `import requests` call now go through
`api_client.send_msg(query, headers=...)`, which already exposes a
`headers` override — all requests go through Playwright's
APIRequestContext.
"""

import copy

import pytest

pytestmark = pytest.mark.sms


@pytest.mark.smoke
def test_send_msg_valid_query_params_returns_success(api_client, test_data, env_config, record_property):
    query = test_data["send_msg"]["valid_query_params"]

    response = api_client.send_msg(query)

    record_property("Expected", "200")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Body: {response.text}"
    )

    body = response.json()
    assert body.get("status", "").lower() in ("submitted", "queued")
    assert "ref_id" in body


@pytest.mark.regression
def test_send_msg_response_time_within_timeout(api_client, test_data, env_config, record_property):
    query = test_data["send_msg"]["valid_query_params"]
    response = api_client.send_msg(query)
    assert response.elapsed.total_seconds() < env_config.timeout_seconds


@pytest.mark.negative
def test_send_msg_missing_campaign_id(api_client, test_data, record_property):
    query = test_data["send_msg"]["missing_campaign_id"]

    response = api_client.send_msg(query)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 422 for missing 'campaign_id', got "
        f"{response.status_code}. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_msg_missing_phone(api_client, test_data, record_property):
    query = test_data["send_msg"]["missing_phone"]

    response = api_client.send_msg(query)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 422 for missing 'phone', got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_msg_missing_params(api_client, test_data, record_property):
    """Documents whether `params` is strictly required or optional
    (e.g. for a campaign whose template has no placeholders)."""
    query = test_data["send_msg"]["missing_params"]

    response = api_client.send_msg(query)

    record_property("Expected", "400, 422")
    record_property("Actual", str(response.status_code))
    assert response.status_code in (400, 422), (
        f"Expected a handled response for missing 'params', got "
        f"{response.status_code} — possible unhandled server error. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_msg_empty_params_array(api_client, test_data, record_property):
    query = test_data["send_msg"]["empty_params_array"]

    response = api_client.send_msg(query)

    record_property("Expected", "400, 422")
    record_property("Actual", str(response.status_code))
    assert response.status_code in (400, 422), (
        f"Expected a handled response for an empty 'params' array, got "
        f"{response.status_code}. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_msg_invalid_phone_format(api_client, test_data, record_property):
    query = test_data["send_msg"]["invalid_phone_format"]

    response = api_client.send_msg(query)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 422 for an invalid 'phone' value, got "
        f"{response.status_code}. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_msg_non_numeric_phone(api_client, test_data, record_property):
    query = test_data["send_msg"]["non_numeric_phone"]

    response = api_client.send_msg(query)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 422 for a non-numeric 'phone' value, got "
        f"{response.status_code}. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_msg_nonexistent_campaign_id(api_client, test_data, record_property):
    """A campaign_id that (almost certainly) doesn't exist on the account."""
    query = test_data["send_msg"]["nonexistent_campaign_id"]

    response = api_client.send_msg(query)

    record_property("Expected", "400, 404, 422")
    record_property("Actual", str(response.status_code))
    assert response.status_code in (400, 404, 422), (
        f"Expected an error response for a nonexistent campaign_id, got "
        f"{response.status_code}. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_msg_malformed_campaign_id_format(api_client, test_data, record_property):
    """campaign_id looks like a UUID in the sample curl; confirms
    behavior when a non-UUID string is sent instead."""
    query = test_data["send_msg"]["malformed_campaign_id_format"]

    response = api_client.send_msg(query)

    record_property("Expected", "400, 404, 422")
    record_property("Actual", str(response.status_code))
    assert response.status_code in (400, 404, 422), (
        f"Expected an error response for a malformed campaign_id, got "
        f"{response.status_code} — possible unhandled server error. "
        f"Body: {response.text}"
    )


@pytest.mark.regression
def test_send_msg_extra_unexpected_query_param(api_client, test_data, record_property):
    """Confirms an unknown query param is handled gracefully, not a 500."""
    query = test_data["send_msg"]["extra_unexpected_query_param"]

    response = api_client.send_msg(query)

    record_property("Expected", "400, 422")
    record_property("Actual", str(response.status_code))
    assert response.status_code in (400, 422), (
        f"Expected a handled response for an unexpected extra query "
        f"param, got {response.status_code} — possible unhandled server "
        f"error. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_msg_unauthorized_without_token(api_client, test_data, env_config, record_property):
    query = test_data["send_msg"]["valid_query_params"]
    bad_headers = {"Authorization": "Bearer invalid-token-for-testing"}

    response = api_client.send_msg(query, headers=bad_headers)

    record_property("Expected", "401")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 401, (
        f"Expected 401 for invalid token, got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_msg_missing_authorization_header_entirely(api_client, test_data, env_config, record_property):
    query = test_data["send_msg"]["valid_query_params"]

    response = api_client.send_msg(query, headers={})

    record_property("Expected", "401")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 401, (
        f"Expected 401 when Authorization header is entirely absent, got "
        f"{response.status_code}. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_msg_malformed_params_json_in_query_string(api_client, test_data, record_property):
    """
    Sends syntactically invalid JSON directly in the `params` query value
    (not run through the client's normal JSON encoding), to see how the
    API handles an unparseable params array.
    """
    base_query = test_data["send_msg"]["valid_query_params"]
    query = {
        "campaign_id": base_query["campaign_id"],
        "phone": base_query["phone"],
        "params": '["test", "test2",]',  # trailing comma = invalid JSON
    }

    # `query["params"]` is already a string (not a list), so
    # SmsApiClient.send_msg() passes it through untouched — matching the
    # previous raw-requests behavior exactly.
    response = api_client.send_msg(
        query, headers={"Authorization": f"Bearer {api_client.env.auth_token}"}
    )

    record_property("Expected", "400, 422")
    record_property("Actual", str(response.status_code))
    assert response.status_code in (400, 422), (
        f"Expected 422 for malformed 'params' JSON in the query "
        f"string, got {response.status_code}. Body: {response.text}"
    )
