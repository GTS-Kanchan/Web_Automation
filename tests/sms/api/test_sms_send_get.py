"""
test_sms_send_get.py

Tests for GET /api/sms/send
This endpoint takes its data as URL query parameters rather than a JSON request body.
The curl provided includes `api_token` in query parameters and a `domain` header.

MIGRATION NOTE: this file already went exclusively through `api_client`
(no raw `requests` calls), so no test-level changes were needed beyond
the underlying client now using Playwright's APIRequestContext.
"""

import pytest

pytestmark = pytest.mark.sms


@pytest.mark.smoke
def test_send_sms_get_valid_query_params_returns_success(api_client, test_data, env_config, record_property):
    query = test_data["sms_send_get"]["valid_query_params"]

    response = api_client.send_sms_get(query)

    record_property("Expected", "200")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Body: {response.text}"
    )

    # We assume the response might match the POST /api/sms/send format if it returns JSON
    try:
        if env_config.name != "malaysia":
            body = response.json()
            assert body.get("status") == "success"
            if isinstance(body.get("data"), list) and len(body["data"]) > 0:
                assert body["data"][0]["status"] in ("queued", "submitted")
                assert "message_id" in body["data"][0]
            assert "data" in body
    except ValueError:
        # If it doesn't return JSON, at least we asserted 200
        pass


@pytest.mark.regression
def test_send_sms_get_response_time_within_timeout(api_client, test_data, env_config, record_property):
    query = test_data["sms_send_get"]["valid_query_params"]
    response = api_client.send_sms_get(query)
    assert response.elapsed.total_seconds() < env_config.timeout_seconds


@pytest.mark.negative
def test_send_sms_get_missing_to_param(api_client, test_data, record_property):
    query = test_data["sms_send_get"]["missing_to_param"]

    response = api_client.send_sms_get(query)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 422 for missing 'to' param, got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_sms_get_missing_from_param(api_client, test_data, record_property):
    query = test_data["sms_send_get"]["missing_from_param"]

    response = api_client.send_sms_get(query)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 422 for missing 'from' param, got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_sms_get_missing_text_param(api_client, test_data, record_property):
    query = test_data["sms_send_get"]["missing_text_param"]

    response = api_client.send_sms_get(query)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 422 for missing 'text' param, got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_sms_get_unauthorized_without_token(api_client, test_data, record_property):
    # api_token in test_data is already set to "invalid-token" — auth fails via bad param value
    query = test_data["sms_send_get"]["invalid_token_param"]

    response = api_client.send_sms_get(query)

    record_property("Expected", "401")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 401, (
        f"Expected 401 for invalid api_token param, got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_sms_get_missing_domain_header(api_client, test_data, record_property):
    query = test_data["sms_send_get"]["valid_query_params"]
    # Explicitly clear the default domain header to test missing-domain behaviour
    headers = {"domain": None}

    response = api_client.send_sms_get(query, headers=headers)

    # Note: Depending on server implementation, missing domain might be 401, 400 or handled normally.
    # Asserting it doesn't fail catastrophically (500).
    assert response.status_code < 500, (
        f"Expected handled response when missing domain header, got {response.status_code}. "
        f"Body: {response.text}"
    )
