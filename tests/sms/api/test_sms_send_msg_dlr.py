"""
test_sms_send_msg_dlr.py

Test Case: TC-03 -- Verify DLR for /api/sms/send-msg
Send API: POST /api/sms/send-msg  (query params, no JSON body)
DLR API:  GET {dlr_base_url}/api/v1/dlr/{ref_id}

Provided directly by the project owner as a test-case spec, including
an example request showing `correlation_id` as an addable query param:

    /api/sms/send-msg?campaign_id=...&phone=...&correlation_id=...

CONFIRMED response shape (see test_send_msg.py's
test_send_msg_valid_query_params_returns_success): only `status` and
`ref_id` at the top level -- there is no `message_id` field at all.

IDENTIFIER, per real evidence from the project owner (run against the
actual staging instance): `ref_id` IS the platform's message_id for
this endpoint -- not a locally-generated `correlation_id`. A first
version of this test generated its own `correlation_id` and polled the
DLR API with that string; the DLR API accepted it (200 OK) but simply
echoed it straight back as `message_id` in an empty/pending record
(`{"message_id": "dlrtest-...", "received": false, "status":
"PENDING"}`) that never resolved, because the real DLR the platform
generates for the SMS is keyed by `ref_id`, not by the invented
correlation_id. Confirmed fix, from the project owner directly: "ref_id
is messageid in platform." So this test now polls the DLR API using
`ref_id`, treating it as this endpoint's message_id.

`correlation_id` is still generated and sent as a query param, since
the spec's example request includes it -- but it is no longer used as
the DLR lookup identifier. If a real `correlation_id` field is ever
confirmed to appear in the DLR body too, step 10's correlation check
below still verifies it when present; it just isn't relied on as the
primary identifier anymore.

IMPORTANT, per the spec: this test deliberately does NOT assert on
`status`, `provider_status`, `status_code`, or any particular
delivery-status value anywhere in the DLR body. It only validates DLR
reception and correlation. Do not add a delivery-status assertion here
without a fresh instruction to do so -- that would directly contradict
the spec's stated intent.
"""

import uuid

import pytest

from utils.dlr_helpers import (
    DLR_POLL_TIMEOUT_SECONDS,
    poll_for_dlr,
)

pytestmark = pytest.mark.sms


@pytest.mark.smoke
def test_dlr_received_after_send_msg(api_client, test_data, record_property):
    # ── Step 1: send via /api/sms/send-msg. A correlation_id is generated
    #            and sent as a query param (per the spec's example request)
    #            but, per confirmed platform behavior, is NOT the DLR
    #            lookup identifier -- ref_id is (see module docstring) ──────
    base_query = test_data["send_msg"]["valid_query_params"]
    correlation_id = f"dlrtest-{uuid.uuid4().hex}"
    query = dict(base_query)
    query["correlation_id"] = correlation_id
    record_property("correlation_id (sent)", correlation_id)

    send_response = api_client.send_msg(query)
    record_property("Response", send_response.text)

    record_property("Expected", "200")
    record_property("Actual", str(send_response.status_code))
    assert send_response.status_code == 200, (
        f"SMS send-msg API failed: expected 200, got "
        f"{send_response.status_code}. Body: {send_response.text}"
    )

    send_body = send_response.json()

    # ── Step 2-3: capture the identifier. This endpoint never returns
    #              message_id (confirmed) -- ref_id is the platform's
    #              message_id equivalent here, confirmed directly against
    #              the real DLR API, so it's what's used to poll DLR ──────
    message_id = None
    ref_id = None
    if isinstance(send_body, dict):
        message_id = send_body.get("message_id")
        if not message_id:
            data = send_body.get("data")
            if isinstance(data, list) and data:
                message_id = data[0].get("message_id")
        ref_id = send_body.get("ref_id")

    identifier = message_id or ref_id
    used_correlation_id = False
    if not identifier:
        # Neither message_id nor ref_id available -- last-resort fallback
        # to the correlation_id this test sent, per the spec's step 3.
        # Not expected to trigger given current confirmed behavior.
        identifier = correlation_id
        used_correlation_id = True

    assert identifier, (
        f"None of message_id, ref_id, or correlation_id could be used to "
        f"identify this SMS for DLR lookup. Send body: {send_body}"
    )
    record_property("message_id", message_id if message_id else "(not returned)")
    record_property("ref_id", ref_id if ref_id else "(not returned)")
    record_property("identifier used for DLR lookup", identifier)

    # ── Step 4-5: wait for + call the DLR API ────────────────────────────────
    dlr_response, dlr_body, fields = poll_for_dlr(api_client, identifier)

    assert dlr_response is not None, (
        "DLR API was never called -- unexpected internal state."
    )
    record_property("Response", dlr_response.text)

    # ── Step 6: DLR API returns a successful response ────────────────────────
    record_property("Expected", "200")
    record_property("Actual", str(dlr_response.status_code))
    assert dlr_response.status_code == 200, (
        f"DLR API could not be accessed / did not return a successful "
        f"response for identifier={identifier} within "
        f"{DLR_POLL_TIMEOUT_SECONDS}s. Got {dlr_response.status_code}. "
        f"Body: {dlr_response.text}"
    )

    assert dlr_body is not None, (
        f"DLR API returned 200 but the body wasn't valid JSON. "
        f"Body: {dlr_response.text}"
    )

    # ── Step 7: received = true ────────────────────────────────────────────
    assert fields["received"] is True, (
        f"DLR was not received within {DLR_POLL_TIMEOUT_SECONDS}s for "
        f"identifier={identifier} (received={fields['received']!r}). "
        f"Body: {dlr_body}"
    )

    # ── Step 8: DLR belongs to the SMS submitted by this test ────────────────
    # Established by successfully looking it up via the identifier this
    # test itself captured and sent/received (steps 1-6 above).

    # ── Step 9: DLR message_id matches the submitted SMS identifier
    #            (ref_id, treated as this endpoint's message_id), when
    #            available ───────────────────────────────────────────────────
    if not used_correlation_id:
        assert fields["message_id"] == identifier, (
            f"DLR message_id ({fields['message_id']!r}) does not match the "
            f"send-msg identifier used for lookup ({identifier!r} -- "
            f"ref_id={ref_id!r}, message_id={message_id!r}). "
            f"Body: {dlr_body}"
        )

    # ── Step 10: if correlation was performed using correlation_id (only
    #             the last-resort fallback path), verify the DLR
    #             correlation ID matches the request correlation ID ─────────
    if used_correlation_id:
        assert fields["correlation_id"] == correlation_id, (
            f"DLR correlation_id ({fields['correlation_id']!r}) does not "
            f"match the correlation_id sent with the request "
            f"({correlation_id!r}). Body: {dlr_body}"
        )
