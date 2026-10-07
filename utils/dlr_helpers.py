"""
utils/dlr_helpers.py

Shared logic for every "Verify DLR is received/correlated after sending
SMS" test case (tests/sms/api/test_sms_campaign_dlr.py,
test_sms_send_dlr.py, test_sms_template_send_dlr.py,
test_sms_send_msg_dlr.py) -- all four were given as separate test-case
specs by the project owner but describe the exact same single-message
DLR-verification flow against the same endpoint:

    GET {dlr_base_url}/api/v1/dlr/{identifier}

Also has the bulk equivalent used by test_sms_json_dlr.py ("Verify DLR
for /api/sms/json"), which submits many messages in one call and
verifies all of their DLRs in one call:

    POST {dlr_base_url}/api/v1/dlr/verify

Centralized here so the poll-loop/timeout, and the "which fields does
the DLR response body actually expose" extraction, are defined ONCE and
stay consistent across all five tests -- rather than five copies that
could quietly drift out of sync with each other.

CONFIRMED evidence for DLR response fields, from the project owner's own
test-case specs: `received` and `message_id` (the "Verify DLR for
/api/sms/send-msg" spec additionally implies a `correlation_id` field,
via step 10: "verify the DLR correlation ID matches the request
correlation ID"). No wrapper-object shape was ever given, so
`extract_dlr_fields` below checks both the top level and a nested `data`
object (the shape every other endpoint in this API uses), and returns
None for anything not found rather than guessing -- callers always
attach the full raw body to their assertion failure message so a wrong
guess here is visible and fixable, not silently masked.

For bulk verification, NO response shape was ever given for
POST {dlr_base_url}/api/v1/dlr/verify -- only the *request* body's shape
(see the "Verify DLR for /api/sms/json" spec's own example:
{"message_ids": [...], "expected_status": ..., "require_billing": ...}).
`extract_bulk_dlr_results` below tries the response shapes already used
elsewhere in this module/API for a list of per-message records (a
`results`/`data`/`dlrs` list, the body itself being such a list, or a
dict keyed directly by message_id) and returns None if nothing matches,
so the caller fails loudly with the full raw body attached instead of a
further guess.

Per every one of these specs' own "Note"/"Failure conditions" section:
none of this suite's DLR tests may assert on `status`, `provider_status`,
or `status_code` anywhere in the DLR body. That constraint lives in each
test file (nothing here reads those fields for pass/fail), but is
repeated here as a reminder for anyone adding another DLR test on top of
this module.
"""

from __future__ import annotations

import time
from typing import Any, Optional


# Not specified as a concrete number in any of the DLR test-case specs
# ("wait for the DLR to be generated" has no attached timeout/interval) --
# tighten once a real expected DLR-generation latency is confirmed for
# the instance under test.
DLR_POLL_TIMEOUT_SECONDS = 60
DLR_POLL_INTERVAL_SECONDS = 3


def extract_message_id_from_send_response(send_response_body: dict) -> Optional[str]:
    """Pulls message_id out of a JSON-body SMS send response.

    Confirmed shape -- shared by /api/sms/send, /api/sms/campaign/send,
    and /api/sms/template/send (see each endpoint's own
    test_..._valid_payload_returns_success test): a top-level `data`
    list, each entry carrying its own `message_id`. Returns None (never
    raises) if the shape doesn't match, so callers can produce their own
    context-specific assertion message with the full body attached."""
    if not isinstance(send_response_body, dict):
        return None
    data = send_response_body.get("data")
    if not isinstance(data, list) or not data:
        return None
    return data[0].get("message_id")


def extract_dlr_fields(dlr_body: Any) -> dict:
    """Returns {"received": ..., "message_id": ..., "correlation_id": ...}
    from a DLR API response body, checking the top level first, then a
    nested "dlr" object, then a nested "data" object. Any field not
    found is None -- see this module's docstring for why nothing here
    is guessed beyond what was explicitly confirmed.

    The nested "dlr" object is CONFIRMED real (project owner, live GET
    {dlr_base_url}/api/v1/dlr/{message_id} response -- see utils/
    dlr_format_validator.py::extract_full_dlr_fields()'s matching
    note): correlation_id in particular sometimes only lives under
    "dlr" rather than at the top level."""
    result = {"received": None, "message_id": None, "correlation_id": None}
    if not isinstance(dlr_body, dict):
        return result

    def _fill_from(obj: dict) -> None:
        for key in result:
            if result[key] is None and key in obj:
                result[key] = obj[key]

    # Nested "dlr" wins over the top level for correlation_id when both
    # are present (same priority as utils/dlr_format_validator.py::
    # extract_full_dlr_fields() -- see its docstring); "received" only
    # ever lives at the top level, so order doesn't affect it. "data"
    # is a lower-priority fallback.
    nested_dlr = dlr_body.get("dlr")
    if isinstance(nested_dlr, dict):
        _fill_from(nested_dlr)
    _fill_from(dlr_body)
    nested_data = dlr_body.get("data")
    if isinstance(nested_data, dict):
        _fill_from(nested_data)
    return result


def poll_for_dlr(
    api_client,
    identifier: str,
    timeout_seconds: int = DLR_POLL_TIMEOUT_SECONDS,
    interval_seconds: int = DLR_POLL_INTERVAL_SECONDS,
):
    """Polls GET {dlr_base_url}/api/v1/dlr/{identifier} until the DLR
    shows received=true or the timeout elapses.

    Returns (dlr_response, dlr_body, fields) from the LAST attempt made
    (whether or not it succeeded) -- callers assert on this triple, so a
    timeout still produces a real response/body/fields to build a
    precise failure message from, rather than None."""
    dlr_response = None
    dlr_body = None
    fields = {"received": None, "message_id": None, "correlation_id": None}

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        dlr_response = api_client.get_dlr(identifier)
        if dlr_response.status_code == 200:
            try:
                dlr_body = dlr_response.json()
            except Exception:
                dlr_body = None
            if dlr_body is not None:
                fields = extract_dlr_fields(dlr_body)
                if fields["received"]:
                    break
        time.sleep(interval_seconds)

    return dlr_response, dlr_body, fields


# ─────────────────────────── Bulk DLR verification ──────────────────────────

def extract_bulk_dlr_results(body: Any, message_ids: list) -> Optional[dict]:
    """
    Best-effort extraction of a per-message_id result from a bulk
    POST {dlr_base_url}/api/v1/dlr/verify response body.

    No response shape was ever confirmed for this endpoint (see module
    docstring), so this tries, in order:
      1. The body itself being a list of per-message records.
      2. A `results` / `data` / `dlrs` list under those keys.
      3. The body being a dict keyed directly by message_id.

    Returns {message_id: <record dict>} for whichever of `message_ids`
    could be found, or None if the body's shape couldn't be recognized
    at all -- callers must then fail with the full raw body attached
    rather than assume anything further.
    """
    if body is None:
        return None

    records = None
    if isinstance(body, list):
        records = body
    elif isinstance(body, dict):
        for key in ("results", "data", "dlrs"):
            candidate = body.get(key)
            if isinstance(candidate, list):
                records = candidate
                break
        if records is None and any(mid in body for mid in message_ids):
            # Body keyed directly by message_id, e.g. {"<id>": {...}, ...}
            return {mid: body[mid] for mid in message_ids if mid in body}

    if records is None:
        return None

    result = {}
    for entry in records:
        if not isinstance(entry, dict):
            continue
        mid = entry.get("message_id") or entry.get("id")
        if mid:
            result[mid] = entry
    return result


def poll_bulk_dlr(
    api_client,
    message_ids: list,
    expected_status: Optional[str] = "DELIVERED",
    require_billing: Optional[bool] = None,
    timeout_seconds: int = DLR_POLL_TIMEOUT_SECONDS,
    interval_seconds: int = DLR_POLL_INTERVAL_SECONDS,
):
    """
    Polls POST {dlr_base_url}/api/v1/dlr/verify with the full
    `message_ids` list until every one of them shows received=true (or
    the timeout elapses).

    require_billing defaults to None (left out of the request body) --
    confirmed real behavior (project owner): by default this environment
    only generates/receives the STATUS DLR for a message, not a separate
    billing DLR, so requiring one (require_billing=True) made bulk-verify
    wait for/expect a DLR that never arrives. Pass True explicitly only
    for a test that specifically targets billing-DLR verification.

    The bulk-verify test-case spec's own step list doesn't include an
    explicit "wait for the DLR to be generated" step the way the
    single-message DLR specs do (they all have one) -- DLR generation is
    still asynchronous relative to the send call, so a single immediate
    call would very likely find nothing yet. This applies the same
    bounded poll-with-timeout pattern already used by poll_for_dlr()
    above (and every other DLR test in this suite) rather than
    introducing a new idiom or silently assuming a single call suffices.

    Returns (verify_response, verify_body, results) from the LAST
    attempt made -- `results` is either the dict from
    extract_bulk_dlr_results() (possibly with some message_ids still
    missing/not received) or None if the response body's shape was
    never recognized at all.
    """
    verify_response = None
    verify_body = None
    results: Optional[dict] = None

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        verify_response = api_client.verify_dlr_bulk(
            message_ids,
            expected_status=expected_status,
            require_billing=require_billing,
        )
        if verify_response.status_code == 200:
            try:
                verify_body = verify_response.json()
            except Exception:
                verify_body = None
            if verify_body is not None:
                results = extract_bulk_dlr_results(verify_body, message_ids)
                if results is not None and all(
                    isinstance(results.get(mid), dict) and results[mid].get("received")
                    for mid in message_ids
                ):
                    break
        time.sleep(interval_seconds)

    return verify_response, verify_body, results


# ─────────────────────────────────────────────────────────────────────────
# DLR verification + format/schema check, shared by every "success" send
# test in this suite (added on top of each endpoint's existing status-
# code/response-shape assertions, per the project owner's instruction to
# add DLR verification + DLR format checking to every success API test,
# not just the dedicated *_dlr.py test files) -- as well as reused
# internally by this module's own callers. Both helpers run the SAME
# generic (no expected_status/expected_code) format check as the
# dedicated DLR tests, preserving the existing "don't fail a DLR test
# merely because status/provider_status/status_code differs" rule.
# ─────────────────────────────────────────────────────────────────────────

def verify_and_validate_dlr(
    api_client,
    identifier: str,
    expected_mobile: Optional[str] = None,
    timeout_seconds: int = DLR_POLL_TIMEOUT_SECONDS,
    interval_seconds: int = DLR_POLL_INTERVAL_SECONDS,
):
    """Single-message DLR presence + format/schema verification: polls
    GET {dlr_base_url}/api/v1/dlr/{identifier} (poll_for_dlr(), unchanged)
    then runs utils.dlr_format_validator's generic format + correlation
    check against the real response body.

    Returns (dlr_response, dlr_body, fields, format_result,
    correlation_result, report) -- `fields` is poll_for_dlr()'s own
    received/message_id/correlation_id triple (unchanged, for callers
    that still want the original received=true check), the rest are the
    new format/schema layer's results.
    """
    from utils.dlr_format_validator import (
        build_dlr_validation_report,
        extract_full_dlr_fields,
        validate_dlr_correlation,
        validate_dlr_format,
    )

    dlr_response, dlr_body, fields = poll_for_dlr(
        api_client, identifier, timeout_seconds=timeout_seconds, interval_seconds=interval_seconds,
    )
    dlr_fields_full = extract_full_dlr_fields(dlr_body)
    format_result = validate_dlr_format(dlr_fields_full)
    correlation_result = validate_dlr_correlation(
        dlr_fields_full, expected_message_id=identifier, expected_mobile=expected_mobile,
    )
    report = build_dlr_validation_report(format_result, correlation_result)
    return dlr_response, dlr_body, fields, format_result, correlation_result, report


def verify_and_validate_dlrs_bulk(
    api_client,
    message_ids: list,
    expected_mobiles: Optional[dict] = None,
    timeout_seconds: int = DLR_POLL_TIMEOUT_SECONDS,
    interval_seconds: int = DLR_POLL_INTERVAL_SECONDS,
):
    """Bulk DLR presence + format/schema verification for every id in
    `message_ids`: polls POST {dlr_base_url}/api/v1/dlr/verify
    (poll_bulk_dlr(), unchanged) then runs utils.dlr_format_validator's
    aggregate_bulk_dlr_validation() over every result.

    expected_mobiles: optional {message_id: recipient} map for mobile
    correlation -- only pass keys for ids whose recipient field the
    test actually confirmed (e.g. a real "number"/"mobile" field in the
    send response), never a guessed one.

    Returns (verify_response, verify_body, results, counts, failures,
    report).
    """
    from utils.dlr_format_validator import (
        aggregate_bulk_dlr_validation,
        build_bulk_dlr_validation_report,
    )

    verify_response, verify_body, results = poll_bulk_dlr(
        api_client, message_ids, expected_status=None, require_billing=None,
        timeout_seconds=timeout_seconds, interval_seconds=interval_seconds,
    )
    results = results or {}
    counts, failures = aggregate_bulk_dlr_validation(
        message_ids, results, expected_mobiles=expected_mobiles,
    )
    report = build_bulk_dlr_validation_report(counts)
    return verify_response, verify_body, results, counts, failures, report
