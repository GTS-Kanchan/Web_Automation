"""
test_webengage_send.py

Tests for POST /api/v1/sms/webengage/send

MIGRATION NOTE: the unauthorized-token test previously used a raw
`import requests` call; it now uses `api_client.send_webengage(payload,
headers=...)`, which already merges header overrides — all requests go
through Playwright's APIRequestContext.
"""

import pytest

pytestmark = pytest.mark.sms


@pytest.mark.smoke
def test_send_webengage_valid_payload_returns_success(api_client, test_data, record_property):
    payload = test_data["webengage_send"]["valid_payload"]

    response = api_client.send_webengage(payload)

    record_property("Expected", "200")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Body: {response.text}"
    )

    body = response.json()
    assert body.get("status") == "sms_accepted"


@pytest.mark.regression
def test_send_webengage_response_time_within_timeout(api_client, test_data, env_config, record_property):
    payload = test_data["webengage_send"]["valid_payload"]
    response = api_client.send_webengage(payload)
    assert response.elapsed.total_seconds() < env_config.timeout_seconds


@pytest.mark.negative
def test_send_webengage_missing_sms_data(api_client, test_data, record_property):
    payload = test_data["webengage_send"]["missing_sms_data"]

    response = api_client.send_webengage(payload)

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

    record_property("Expected", "401")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 401, (
        f"Expected 401 for invalid token, got {response.status_code}. "
        f"Body: {response.text}"
    )
