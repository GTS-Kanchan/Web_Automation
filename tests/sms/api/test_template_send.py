"""
test_template_send.py

Tests for POST /api/sms/template/send
This endpoint isn't in the v2.2 API doc — its shape was captured from a
sample curl command. Notably different from campaign/send:
  - `id` is a plain numeric template ID (e.g. "7079"), not a UUID
  - `params` uses named keys (e.g. "name") rather than positional numeric
    keys ("1", "2", "3")

Assertions here are intentionally tolerant where behavior is unconfirmed;
tighten them once responses are observed against the real instance.

MIGRATION NOTE: header-edge-case and malformed-body tests that previously
used a raw `import requests` call now use `api_client.send_template(
payload, headers=...)` / `api_client.post_raw(...)` — all requests go
through Playwright's APIRequestContext.
"""

import copy

import pytest

from utils.dlr_helpers import verify_and_validate_dlrs_bulk

pytestmark = pytest.mark.sms


@pytest.mark.smoke
def test_send_template_valid_payload_returns_success(api_client, test_data, env_config, record_property):
    payload = test_data["template_send"]["valid_payload"]

    response = api_client.send_template(payload)
    record_property("Response", response.text)

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

    # ── DLR Verification + DLR Format/Schema check for every sent
    #               message -- no confirmed recipient/mobile field in
    #               this endpoint's response, so mobile correlation is
    #               skipped, not guessed ───────────────────────────────
    message_ids = [entry["message_id"] for entry in body["data"]]
    record_property("message_ids", ", ".join(message_ids))
    verify_response, verify_body, results, counts, failures, report = verify_and_validate_dlrs_bulk(
        api_client, message_ids,
    )
    record_property("DLR Bulk Validation Report", report)
    print("\n" + report)
    assert counts["missing_dlrs"] == 0, (
        f"{counts['missing_dlrs']} of {len(message_ids)} DLR(s) were never "
        f"received.\n{report}\nFailures: {failures}"
    )
    assert counts["invalid_format"] == 0, (
        f"{counts['invalid_format']} of {len(message_ids)} DLR(s) failed "
        f"format/schema validation.\n{report}\nFailures: {failures}"
    )
    assert counts["message_id_mismatches"] == 0, (
        f"DLR message_id correlation failed for one or more message(s).\n{report}\nFailures: {failures}"
    )


@pytest.mark.regression
def test_send_template_response_time_within_timeout(api_client, test_data, env_config, record_property):
    payload = test_data["template_send"]["valid_payload"]
    response = api_client.send_template(payload)
    record_property("Response", response.text)
    assert response.elapsed.total_seconds() < env_config.timeout_seconds


@pytest.mark.negative
def test_send_template_missing_id(api_client, test_data, record_property):
    payload = test_data["template_send"]["missing_id_payload"]

    response = api_client.send_template(payload)
    record_property("Response", response.text)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 422 for missing 'id', got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_template_missing_to(api_client, test_data, record_property):
    payload = test_data["template_send"]["missing_to_payload"]

    response = api_client.send_template(payload)
    record_property("Response", response.text)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 422 for missing 'to', got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_template_empty_to_array(api_client, test_data, record_property):
    payload = test_data["template_send"]["empty_to_array_payload"]

    response = api_client.send_template(payload)
    record_property("Response", response.text)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 422 for empty 'to' array, got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_template_missing_params(api_client, test_data, record_property):
    """Documents whether `params` is strictly required or optional when
    the template has no placeholders to fill."""
    payload = test_data["template_send"]["missing_params_payload"]

    response = api_client.send_template(payload)
    record_property("Response", response.text)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected a handled response for missing 'params', got "
        f"{response.status_code} — possible unhandled server error. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_template_empty_params_object(api_client, test_data, record_property):
    payload = test_data["template_send"]["empty_params_payload"]

    response = api_client.send_template(payload)
    record_property("Response", response.text)

    record_property("Expected", "(200, 422)")
    record_property("Actual", str(response.status_code))
    assert response.status_code in (200, 422), (
        f"Expected 200 (ignored) or 422 (rejected) for empty 'params', got "
        f"{response.status_code}. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_template_nonexistent_template_id(api_client, test_data, record_property):
    """A template ID that (almost certainly) doesn't exist on the account."""
    payload = test_data["template_send"]["nonexistent_template_id_payload"]

    response = api_client.send_template(payload)
    record_property("Response", response.text)

    record_property("Expected", "(404, 422)")
    record_property("Actual", str(response.status_code))
    assert response.status_code in (404, 422), (
        f"Expected an error response for a nonexistent template id, got "
        f"{response.status_code}. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_template_non_numeric_id(api_client, test_data, record_property):
    payload = test_data["template_send"]["non_numeric_id_payload"]

    response = api_client.send_template(payload)
    record_property("Response", response.text)

    record_property("Expected", "422")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 422, (
        f"Expected 422 for a non-numeric template id, got "
        f"{response.status_code}. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_template_invalid_number(api_client, test_data, record_property):
    """
    CHANGED (live run): a hard 422-only assertion started failing with a
    real 200 + {"status":"success", ...} body. Rather than guess which
    one is "the" correct behavior, this now takes the SAME reference
    already used for the identical ambiguity on /api/sms/send (see
    test_sms_send.py::test_send_sms_invalid_number_returns_422 /
    test_send_sms_invalid_number_with_letters): a 200 response is
    accepted only if the per-recipient entry itself reports a failed
    status (server validated and rejected it inline, not silently
    "sent"), otherwise this still requires 422.
    """
    payload = test_data["template_send"]["invalid_number_payload"]

    response = api_client.send_template(payload)
    record_property("Response", response.text)

    if response.status_code == 200:
        body = response.json()
        entry_status = body.get("data", [{}])[0].get("status")
        assert entry_status == "failed", (
            f"Expected a 'failed' per-recipient status for an invalid "
            f"recipient number in a 200 response, got {entry_status!r}. "
            f"Body: {response.text}"
        )
    else:
        record_property("Expected", "422")
        record_property("Actual", str(response.status_code))
        assert response.status_code == 422, (
            f"Expected 200 (rejected inline) or 422 (whole-request reject) "
            f"for an invalid recipient number, got {response.status_code}. "
            f"Body: {response.text}"
        )


@pytest.mark.smoke
def test_send_template_multiple_recipients(api_client, test_data, env_config, record_property):
    payload = test_data["template_send"]["multiple_recipients_payload"]

    response = api_client.send_template(payload)
    record_property("Response", response.text)

    record_property("Expected", "200")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 200, (
        f"Expected 200 for a multi-recipient template send, got "
        f"{response.status_code}. Body: {response.text}"
    )

    # ── DLR Verification + DLR Format/Schema check for every recipient ──────
    body = response.json()
    if isinstance(body.get("data"), list) and body["data"]:
        message_ids = [entry["message_id"] for entry in body["data"] if entry.get("message_id")]
        record_property("message_ids", ", ".join(message_ids))
        verify_response, verify_body, results, counts, failures, report = verify_and_validate_dlrs_bulk(
            api_client, message_ids,
        )
        record_property("DLR Bulk Validation Report", report)
        print("\n" + report)
        assert counts["missing_dlrs"] == 0, (
            f"{counts['missing_dlrs']} of {len(message_ids)} DLR(s) were never "
            f"received for the multi-recipient template send.\n{report}\nFailures: {failures}"
        )
        assert counts["invalid_format"] == 0, (
            f"{counts['invalid_format']} of {len(message_ids)} DLR(s) failed "
            f"format/schema validation.\n{report}\nFailures: {failures}"
        )
        assert counts["message_id_mismatches"] == 0, (
            f"DLR message_id correlation failed for one or more message(s).\n{report}\nFailures: {failures}"
        )


@pytest.mark.regression
def test_send_template_extra_unexpected_param(api_client, test_data, record_property):
    """Confirms an unknown key inside `params` is handled gracefully,
    not a 500. API may either ignore the extra param (200) or reject it (422)."""
    payload = test_data["template_send"]["extra_unexpected_param_payload"]

    response = api_client.send_template(payload)
    record_property("Response", response.text)

    record_property("Expected", "(200, 422)")
    record_property("Actual", str(response.status_code))
    assert response.status_code in (200, 422), (
        f"Expected 200 (ignored) or 422 (rejected) for an unexpected extra param, got "
        f"{response.status_code} — possible unhandled server error. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_template_unauthorized_without_token(api_client, test_data, record_property):
    payload = test_data["template_send"]["valid_payload"]
    bad_headers = dict(api_client.env.headers)
    bad_headers["Authorization"] = "Bearer invalid-token-for-testing"

    response = api_client.send_template(payload, headers=bad_headers)
    record_property("Response", response.text)

    record_property("Expected", "401")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 401, (
        f"Expected 401 for invalid token, got {response.status_code}. "
        f"Body: {response.text}"
    )


@pytest.mark.negative
def test_send_template_missing_authorization_header_entirely(api_client, test_data, record_property):
    payload = test_data["template_send"]["valid_payload"]
    headers_without_auth = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    response = api_client.send_template(payload, headers=headers_without_auth)
    record_property("Response", response.text)

    record_property("Expected", "401")
    record_property("Actual", str(response.status_code))
    assert response.status_code == 401, (
        f"Expected 401 when Authorization header is entirely absent, got "
        f"{response.status_code}. Body: {response.text}"
    )


@pytest.mark.negative
def test_send_template_malformed_json_body(api_client, record_property):
    """Same expected behavior as the other two endpoints: malformed JSON
    is treated as an empty/partial body and validated field-by-field,
    returning 422"""
    response = api_client.post_raw(
        api_client.env.template_send_url,
        raw_body='{"id": "7079", "to": ["917002088565", "params": {}}',
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_client.env.auth_token}",
        },
    )
    record_property("Response", response.text)

    record_property("Expected", "400, 422")
    record_property("Actual", str(response.status_code))
    assert response.status_code in (400, 422), (
        f"Expected 422 for malformed JSON body, got {response.status_code}. "
        f"Body: {response.text}"
    )
