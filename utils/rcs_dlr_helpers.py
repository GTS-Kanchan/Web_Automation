"""
utils/rcs_dlr_helpers.py

DLR (webhook event) verification for the RCS simulator, used by the RCS
E2E campaign test (tests/rcs/campaigns/test_rcs_campaign_create_flow.py
::test_e2ecopypastenumber_send_now) via utils/rcs_campaign_dlr.py.

Retrieval mechanism (CONFIRMED by the project owner, 2026-10-10):

    GET {dlr_base_url}/api/v1/dlr/{message_id}

This is the EXACT SAME endpoint/host already configured for SMS DLR
retrieval (config/sms_api/environments.yaml's `dlr_base_url`, e.g.
"http://140.245.230.67:8080" -- confirmed identical across every
environment block in that file) -- so this module reuses
utils.sms_api_client.SmsApiClient.get_dlr() for the raw HTTP call
rather than building a second client. Only the RESPONSE SHAPE differs
from the SMS DLR response: for RCS it is an RCS simulator webhook event
object (see below), not SMS's {"received":..., "message_id":...,
"correlation_id":...} shape, so all the parsing/validation here is new.

Response shape (CONFIRMED, project owner pasted 3 real payloads,
2026-10-10): a SINGLE event object reflecting the message's current/
latest state (not a list/array) -- it updates in place as the message
progresses through Submitted -> sent -> delivered. Real examples:

  message_dispatch / Submitted:
    {"agent": {"id":..., "name":"agentsim", "provider":"Simulator"},
     "status": "Submitted",
     "message": {"id":..., "type":"text", "number":"917973059161",
                 "content": {...}, "agent_id":..., "direction":"outbound",
                 "campaign_id":...},
     "timestamp": "2026-10-10T11:19:48.608472Z",
     "event_type": "message_dispatch",
     "message_id": "4c1c7b1b-...",
     "corelation_id": null,            <- CONFIRMED spelling (not "correlation_id")
     "rcs_message_id": null,
     "additional_data": {"provider": "dotgo-rcs",
                          "provider_response": {"status": "sent", "message_id": "SIMXHQNLZ5CS7K8"}},
     "external_message_id": "SIMXHQNLZ5CS7K8"}

  message_dispatch / sent (same shape, "status": "sent", "additional_data"
  has provider_name/provider_type instead of provider_response -- both
  additional_data shapes are provider-reported detail, never asserted on).

  message_delivery / delivered:
    {"agent": {"id":..., "name":"agentsim", "provider":"Simulator",
               "provider_type":"dotgo"},
     "status": "delivered",
     "message": {"id":..., "type":"text", "number":"917973059161",
                 "payload": {...},   <- NOTE: "payload" here, not "content"
                 "agent_id":..., "direction":"outbound", "campaign_id":...},
     "timestamp": "2026-10-10T11:19:49.803163Z",
     "event_type": "message_delivery",
     "message_id": "4c1c7b1b-...",
     "corelation_id": null,
     "delivery_info": {
         "read_at": null, "sent_at": "2026-10-10T11:19:48.000000Z",
         "attempts": 0, "failed_at": null,
         "delivered_at": "2026-10-10T11:19:49.000000Z",
         "error_message": null, "failure_reason": null,
         "delivery_status": {
             "status": "delivered",
             "sent_at": "2026-10-10T11:19:48.592171Z",
             "provider": "dotgo-rcs",
             "api_response": {...},
             "last_webhook_at": "2026-10-10T11:19:49.770466Z",
             "last_webhook_event": "DELIVERED"}},
     "rcs_message_id": null,
     "additional_data": {...},
     "external_message_id": "SIMXHQNLZ5CS7K8"}

Per the project owner's explicit spec:
  - Do NOT require `rcs_message_id` to be populated (it is legitimately
    null in every real sample -- external_message_id is the real
    provider correlation id here).
  - Do NOT require `read_at` to be populated (null on a delivered, unread
    event).
  - `external_message_id` is the provider id; match it against a prior
    dispatch event's own `external_message_id` when both are available,
    never require it to equal anything captured before dispatch (it
    does not exist until the simulator assigns it).
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Optional


# ── Configuration (env-overridable; "Keep polling intervals and timeout
# configurable" per spec) ────────────────────────────────────────────────
import os

RCS_DLR_POLL_TIMEOUT_SECONDS = int(os.getenv("RCS_DLR_POLL_TIMEOUT_SECONDS", "120"))
RCS_DLR_POLL_INTERVAL_SECONDS = int(os.getenv("RCS_DLR_POLL_INTERVAL_SECONDS", "5"))

EVENT_TYPE_DISPATCH = "message_dispatch"
EVENT_TYPE_DELIVERY = "message_delivery"
STATUS_DELIVERED = "delivered"


class RcsDlrSchemaError(AssertionError):
    """Raised with a human-readable list of what's wrong with an event's
    structure; `missing_fields`/`invalid_fields` carry the machine-
    readable detail for a failure report."""

    def __init__(self, message, missing_fields=None, invalid_fields=None):
        super().__init__(message)
        self.missing_fields = missing_fields or []
        self.invalid_fields = invalid_fields or []


def _get_path(obj: Any, path: str):
    """Reads a dotted path ("message.id", "delivery_info.delivered_at")
    out of a nested dict. Returns (found, value): found=False if any
    segment along the path is missing (never raises, never confuses
    "present but null" with "missing" -- found=True, value=None for an
    explicitly-null field like rcs_message_id)."""
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return False, None
        cur = cur[part]
    return True, cur


def is_valid_iso8601_utc(value: Any) -> bool:
    """True if `value` parses as an ISO-8601 timestamp. The real samples
    use a trailing "Z" (UTC) with up to microsecond precision
    ("2026-10-10T11:19:49.803163Z") -- Python's fromisoformat() (3.11+)
    accepts "Z" directly; for older runtimes this normalizes "Z" to
    "+00:00" first. Does not require UTC specifically (a webhook replay
    from a different TZ would still be a valid, parseable timestamp) --
    callers that specifically need "the required timestamps are present,
    parseable, and valid" (per spec section 6) are satisfied by this
    alone."""
    if not isinstance(value, str) or not value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


# ── Schema validation ────────────────────────────────────────────────────
#
# Field lists below are the EXACT fields given in the task spec
# (section 5), cross-checked against the 3 real pasted payloads above.
# "Required" here means: the path must be PRESENT in the dict (even if
# its value is legitimately null, e.g. corelation_id/rcs_message_id/
# read_at) -- this module never requires a specific non-null value for
# those three fields, per the spec's explicit exceptions.

DISPATCH_REQUIRED_FIELDS = [
    "agent.id", "agent.name", "agent.provider",
    "status",
    "message.id", "message.type", "message.number", "message.agent_id",
    "message.direction", "message.campaign_id",
    "timestamp", "event_type", "message_id", "external_message_id",
]

DELIVERY_REQUIRED_FIELDS = [
    "agent", "status", "message", "timestamp", "event_type", "message_id",
    "delivery_info", "delivery_info.sent_at", "delivery_info.delivered_at",
    "delivery_info.delivery_status", "external_message_id",
]

# Fields legitimately null in every confirmed sample -- presence is
# checked, a null VALUE is never treated as a failure for these.
NULLABLE_OK_FIELDS = {"corelation_id", "rcs_message_id", "delivery_info.read_at"}

DISPATCH_TIMESTAMP_FIELDS = ["timestamp"]
DELIVERY_TIMESTAMP_FIELDS = [
    "timestamp", "delivery_info.sent_at", "delivery_info.delivered_at",
    "delivery_info.delivery_status.sent_at", "delivery_info.delivery_status.last_webhook_at",
]


def validate_event_schema(event: dict) -> tuple[bool, list, list]:
    """Validates `event` against the schema for its OWN event_type
    (message_dispatch vs message_delivery) -- never requires a
    delivery-only field on a dispatch event or vice versa, per the
    spec's explicit "fields that legitimately differ... must not be
    incorrectly required in both" instruction.

    Returns (is_valid, missing_fields, invalid_timestamps).
    """
    if not isinstance(event, dict):
        return False, ["<entire event body is not a JSON object>"], []

    event_type = event.get("event_type")
    if event_type == EVENT_TYPE_DISPATCH:
        required = DISPATCH_REQUIRED_FIELDS
        ts_fields = DISPATCH_TIMESTAMP_FIELDS
    elif event_type == EVENT_TYPE_DELIVERY:
        required = DELIVERY_REQUIRED_FIELDS
        ts_fields = DELIVERY_TIMESTAMP_FIELDS
    else:
        return False, [f"unrecognized event_type: {event_type!r}"], []

    missing = []
    for path in required:
        found, _ = _get_path(event, path)
        if not found:
            missing.append(path)

    invalid_timestamps = []
    for path in ts_fields:
        found, value = _get_path(event, path)
        if not found:
            continue  # already reported (or optional) above
        if not is_valid_iso8601_utc(value):
            invalid_timestamps.append((path, value))

    return (not missing and not invalid_timestamps), missing, invalid_timestamps


# ── Correlation ──────────────────────────────────────────────────────────

def correlate_event(event: dict, expected_message_id: str,
                     expected_number: Optional[str] = None,
                     expected_campaign_id: Optional[str] = None,
                     expected_external_message_id: Optional[str] = None) -> dict:
    """Checks that `event` genuinely belongs to the message the test
    sent: internal message id always; recipient number and campaign id
    when the caller has them (both live under `message.*` in every
    confirmed sample); external_message_id only when the caller already
    captured one from an earlier dispatch event for this same message
    (it doesn't exist before the simulator assigns it).

    Returns a dict of individual pass/fail checks, never raises --
    callers decide pass/fail and build the section-8 failure report from
    this.
    """
    result = {
        "internal_message_id_match": None,
        "recipient_match": None,
        "campaign_id_match": None,
        "external_message_id_match": None,
    }
    if not isinstance(event, dict):
        return result

    actual_internal_id = event.get("message_id") or _get_path(event, "message.id")[1]
    result["internal_message_id_match"] = (
        expected_message_id is not None and actual_internal_id == expected_message_id
    )

    if expected_number is not None:
        _, actual_number = _get_path(event, "message.number")
        result["recipient_match"] = actual_number == expected_number

    if expected_campaign_id is not None:
        _, actual_campaign_id = _get_path(event, "message.campaign_id")
        result["campaign_id_match"] = actual_campaign_id == expected_campaign_id

    if expected_external_message_id is not None:
        result["external_message_id_match"] = (
            event.get("external_message_id") == expected_external_message_id
        )

    return result


# ── Delivery-info verification (spec section 7) ─────────────────────────

def validate_delivery_info(event: dict) -> tuple[bool, list]:
    """For a message_delivery event, checks the delivery_info block per
    spec section 7. Returns (is_valid, problems)."""
    problems = []
    found, delivery_info = _get_path(event, "delivery_info")
    if not found or not isinstance(delivery_info, dict):
        return False, ["delivery_info missing or not an object"]

    found, delivered_at = _get_path(event, "delivery_info.delivered_at")
    if not found or not delivered_at:
        problems.append("delivery_info.delivered_at is not populated")

    found, status = _get_path(event, "delivery_info.delivery_status.status")
    if not found or status != STATUS_DELIVERED:
        problems.append(f"delivery_info.delivery_status.status is {status!r}, expected 'delivered'")

    # last_webhook_event, when present, should be consistent with a
    # delivered event ("DELIVERED" in the confirmed real sample) --
    # informational only (never fails the test on its own) since no
    # exhaustive enum of acceptable values was given.
    found, last_event = _get_path(event, "delivery_info.delivery_status.last_webhook_event")
    if found and last_event and "delivered" not in str(last_event).lower():
        problems.append(
            f"delivery_info.delivery_status.last_webhook_event is {last_event!r}, "
            f"which doesn't look consistent with a delivered event"
        )

    return (not problems), problems


# ── Polling ──────────────────────────────────────────────────────────────

def poll_for_rcs_delivery(api_client, message_id: str,
                           timeout_seconds: int = RCS_DLR_POLL_TIMEOUT_SECONDS,
                           interval_seconds: int = RCS_DLR_POLL_INTERVAL_SECONDS):
    """Polls GET {dlr_base_url}/api/v1/dlr/{message_id} (via
    SmsApiClient.get_dlr(), the same endpoint/client SMS DLR tests
    already use) until a message_delivery event with status=='delivered'
    is observed, or the timeout elapses.

    Returns (last_response, last_body, events_seen) where events_seen is
    the list of every DISTINCT event_type/status combination observed
    during polling (e.g. [("message_dispatch","Submitted"),
    ("message_dispatch","sent"), ("message_delivery","delivered")]) --
    informational evidence that the message actually progressed through
    the expected lifecycle, not just evidence of the final state. Never
    raises -- a timeout still returns the last response/body/events_seen
    so the caller can build a precise failure report (spec section 8)
    rather than a generic timeout error.
    """
    last_response = None
    last_body = None
    events_seen = []
    seen_keys = set()

    deadline = time.time() + timeout_seconds
    while True:
        last_response = api_client.get_dlr(message_id)
        if last_response is not None and last_response.status_code == 200:
            try:
                last_body = last_response.json()
            except Exception:
                last_body = None
            if isinstance(last_body, dict):
                key = (last_body.get("event_type"), last_body.get("status"))
                if key not in seen_keys:
                    seen_keys.add(key)
                    events_seen.append(key)
                if (last_body.get("event_type") == EVENT_TYPE_DELIVERY
                        and last_body.get("status") == STATUS_DELIVERED):
                    return last_response, last_body, events_seen
        if time.time() >= deadline:
            return last_response, last_body, events_seen
        time.sleep(interval_seconds)


# ── Failure report (spec section 8, exact field order) ──────────────────

def build_failure_report(*, campaign_id, internal_message_id, external_message_id,
                          recipient, actual_event, actual_status, dlr_received,
                          schema_validation, correlation_validation, failure_reason) -> str:
    def _yn(b):
        if b is None:
            return "N/A"
        return "YES" if b else "NO"

    def _pf(b):
        if b is None:
            return "N/A"
        return "PASS" if b else "FAIL"

    lines = [
        f"Campaign ID: {campaign_id}",
        f"Internal Message ID: {internal_message_id}",
        f"External Message ID: {external_message_id}",
        f"Recipient: {recipient}",
        f"Expected Event: {EVENT_TYPE_DELIVERY}",
        f"Expected Status: {STATUS_DELIVERED}",
        f"Actual Event: {actual_event}",
        f"Actual Status: {actual_status}",
        f"DLR Received: {_yn(dlr_received)}",
        f"Schema Validation: {_pf(schema_validation)}",
        f"Correlation Validation: {_pf(correlation_validation)}",
        f"Failure Reason: {failure_reason}",
    ]
    return "\n".join(lines)
