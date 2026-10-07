"""
test_sms_json_dlr.py

Test Case: Verify DLR for /api/sms/json (bulk)
Send API:            POST /api/sms/json
DLR Verification API: POST {dlr_base_url}/api/v1/dlr/verify

Provided directly by the project owner as a test-case spec (steps,
example request/response shapes, expected-result table, and explicit
failure conditions). Unlike the single-message DLR tests
(test_sms_campaign_dlr.py, test_sms_send_dlr.py,
test_sms_template_send_dlr.py, test_sms_send_msg_dlr.py), this one
submits a batch of messages in one /api/sms/json call and verifies all
of their DLRs in a single bulk /api/v1/dlr/verify call.

Per the spec's own explicit "Important" section: this test must NOT
hard-code any message_id. Every message_id sent to /api/v1/dlr/verify
is extracted dynamically from the real /api/sms/json response's `data`
array (confirmed shape -- see test_sms_json.py's
test_send_json_real_sample_payload: top-level `data` list, each entry
carrying its own `message_id`).

Uses test_data.yaml's sms_json.real_sample_payload (already used and
confirmed working by test_sms_json.py) rather than a new payload, since
it already produces multiple `data` entries with real message_ids --
exactly what this bulk test needs, and avoids inventing a new payload
that hasn't been run against the real instance.

The bulk verify response's shape was never confirmed (only the request
body's shape was given, via the spec's own example) -- see
utils/dlr_helpers.py's extract_bulk_dlr_results()/poll_bulk_dlr() for
how that's handled: several plausible shapes are tried, and this test
fails loudly with the full raw body attached if none of them match,
rather than guessing further.

IMPORTANT, per the spec: this test deliberately does NOT assert on
`status`, `provider_status`, or `status_code` anywhere in the DLR
verification response. It only validates bulk DLR reception and
correlation.
"""

import pytest

from utils.dlr_format_validator import (
    aggregate_bulk_dlr_validation,
    build_bulk_dlr_validation_report,
)
from utils.dlr_helpers import (
    DLR_POLL_TIMEOUT_SECONDS,
    poll_bulk_dlr,
)

pytestmark = pytest.mark.sms


@pytest.mark.smoke
def test_bulk_dlr_received_after_sms_json_send(api_client, test_data, record_property):
    # ── Steps 1-2: send the batch via /api/sms/json, verify success ─────────
    payload = test_data["sms_json"]["real_sample_payload"]
    send_response = api_client.send_json(payload)
    record_property("Response", send_response.text)

    record_property("Expected", "200")
    record_property("Actual", str(send_response.status_code))
    assert send_response.status_code == 200, (
        f"SMS JSON API failed: expected 200, got "
        f"{send_response.status_code}. Body: {send_response.text}"
    )

    send_body = send_response.json()
    assert send_body.get("status") == "success", (
        f"Expected /api/sms/json response 'status' to be 'success'. "
        f"Body: {send_body}"
    )

    # ── Step 3-4: read `data`, extract message_id from every entry ──────────
    data = send_body.get("data")
    assert isinstance(data, list) and len(data) > 0, (
        f"Expected a non-empty 'data' list in the /api/sms/json response "
        f"to extract message_ids from. Got: {send_body}"
    )

    for i, entry in enumerate(data):
        assert isinstance(entry, dict) and entry.get("message_id"), (
            f"data[{i}] is missing 'message_id' -- a submitted SMS must "
            f"carry one. Entry: {entry}. Full body: {send_body}"
        )

    # ── Step 5: build the message_ids list dynamically (never hard-coded) ───
    message_ids = [entry["message_id"] for entry in data]
    submitted_count = len(message_ids)
    record_property("Submitted messages", str(submitted_count))
    record_property("message_ids", ", ".join(message_ids))

    # ── Step 6: call POST {dlr_base_url}/api/v1/dlr/verify with the
    #            dynamically-built message_ids list. DLR generation is
    #            asynchronous, so this polls with a bounded timeout the
    #            same way every other DLR test in this suite does --
    #            see poll_bulk_dlr()'s docstring for why, given the spec's
    #            own steps don't include an explicit wait step here ──────────
    # require_billing is intentionally left out (defaults to None) --
    # by default this environment only generates a STATUS DLR for a
    # message, not a separate billing DLR, so requiring one here made
    # bulk-verify wait for/expect a DLR that never arrives.
    verify_response, verify_body, results = poll_bulk_dlr(
        api_client, message_ids
    )

    assert verify_response is not None, (
        "DLR verification API was never called -- unexpected internal state."
    )
    record_property("Response", verify_response.text)

    record_property("Expected", "200")
    record_property("Actual", str(verify_response.status_code))
    assert verify_response.status_code == 200, (
        f"DLR verification API failed for message_ids={message_ids} "
        f"within {DLR_POLL_TIMEOUT_SECONDS}s. Got "
        f"{verify_response.status_code}. Body: {verify_response.text}"
    )

    assert verify_body is not None, (
        f"DLR verification API returned 200 but the body wasn't valid "
        f"JSON. Body: {verify_response.text}"
    )

    assert results is not None, (
        f"Could not recognize the DLR verification response's shape to "
        f"extract per-message_id results from (tried a top-level list, "
        f"'results'/'data'/'dlrs' list, and a dict keyed by message_id -- "
        f"see extract_bulk_dlr_results()). Full body: {verify_body}"
    )

    # ── Step 7: results present for every submitted message_id ──────────────
    missing_ids = [mid for mid in message_ids if mid not in results]
    assert not missing_ids, (
        f"{len(missing_ids)} of {submitted_count} submitted message_id(s) "
        f"are missing from the DLR verification response entirely: "
        f"{missing_ids}. Full body: {verify_body}"
    )

    # ── Step 8: every submitted message_id is received/correlated ───────────
    not_received = [
        mid for mid in message_ids if not results[mid].get("received")
    ]
    record_property("DLRs received", str(submitted_count - len(not_received)))
    record_property("Missing DLRs", str(len(not_received)))
    assert not not_received, (
        f"{len(not_received)} of {submitted_count} submitted message_id(s) "
        f"were not marked received=true by DLR verification within "
        f"{DLR_POLL_TIMEOUT_SECONDS}s: {not_received}. Full body: {verify_body}"
    )

    # ── Step 9: number of DLRs received matches number of submitted SMS ─────
    received_count = sum(1 for mid in message_ids if results[mid].get("received"))
    assert received_count == submitted_count, (
        f"Expected {submitted_count} DLRs received (one per submitted "
        f"message), got {received_count}. Full body: {verify_body}"
    )

    # Deliberately NOT asserting on status / provider_status / status_code
    # anywhere in the DLR verification body, per the spec's explicit
    # instruction -- this test is scoped to bulk DLR reception and
    # correlation only.

    # ── DLR Format/Schema Verification for every received DLR (generic
    #               test -- status/code are only checked to EXIST, never
    #               compared to a specific value) ─────────────────────────
    counts, failures = aggregate_bulk_dlr_validation(message_ids, results)
    bulk_report = build_bulk_dlr_validation_report(counts)
    record_property("DLR Bulk Validation Report", bulk_report)
    print("\n" + bulk_report)
    assert counts["invalid_format"] == 0, (
        f"{counts['invalid_format']} of {submitted_count} DLR(s) failed "
        f"format/schema validation.\n{bulk_report}\nFailures: {failures}"
    )
    assert counts["message_id_mismatches"] == 0, (
        f"{counts['message_id_mismatches']} DLR(s) had a message_id "
        f"correlation mismatch.\n{bulk_report}\nFailures: {failures}"
    )
    assert counts["duplicate_dlrs"] == 0, (
        f"{counts['duplicate_dlrs']} duplicate DLR entry/entries found.\n"
        f"{bulk_report}\nFailures: {failures}"
    )
