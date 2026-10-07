"""
utils/dlr_format_validator.py

Shared DLR format/schema validator, reused by EVERY SMS DLR verification
test in this suite (single-message and bulk alike) on top of the
existing presence/correlation checks already provided by
utils/dlr_helpers.py and utils/campaign_dlr.py. This module does not
replace either of those -- it adds a second, independent layer:

    DLR presence/correlation (dlr_helpers.py / campaign_dlr.py)
        + DLR format/schema verification (THIS module)
        = the combined check every DLR test now runs.

Baseline DLR payload shapes, given directly by the project owner as the
two reference formats this validator is built from:

  SMS Default -- REJECTED DLR:
    {"message_id": "...", "service": "T", "sender": "...", "mobile": "...",
     "status": "REJECTED", "code": "456", "submit_at": "dd-mm-yyyy hh:mm:ss",
     "dlr_received_at": "dd-mm-yyyy hh:mm:ss", "entity_id": "...",
     "template_id": "...", "units": "1", "correlation_id": null}

  SMS Default -- DELIVERED DLR:
    {"message_id": "...", "service": "T", "sender": "...", "mobile": "...",
     "status": "DELIVRD", "code": "000", "submit_at": "dd-mm-yyyy hh:mm:ss",
     "dlr_received_at": "dd-mm-yyyy hh:mm:ss", "entity_id": "...",
     "template_id": "...", "units": "...", "correlation_id": "..."}

Required fields (ALL_DLR_FIELDS below): message_id, service, sender,
mobile, status, code, submit_at, dlr_received_at, entity_id,
template_id, units, correlation_id.

Status DLR vs billing DLR: confirmed real behavior (project owner) --
"in default dlr we only receive status dlr not billing". By default
this environment only generates/receives the STATUS DLR for a message;
`units` is BILLING information and is NOT part of that default DLR, so
it is NOT in _REQUIRED_NON_EMPTY_FIELDS -- missing/blank `units` on a
default DLR passes format validation (see _BILLING_FIELDS,
validate_dlr_format()'s require_billing parameter). This mirrors the
SAME status-vs-billing distinction utils/dlr_helpers.py::poll_bulk_dlr()
already makes via its own require_billing parameter (also None/False by
default), so a test only has to opt INTO billing-field validation
(require_billing=True) for a test that specifically targets billing-DLR
verification -- never the other way around. Both of the baseline
payloads above DO show a `units` value, but that is what the schema
looks like WHEN billing info is present, not proof that every default
DLR carries it.

Per the project owner's explicit "Important Existing DLR Rule": keep the
EXISTING distinction between format validation and business-status
validation.

  - Generic DLR presence/correlation tests (the majority of this suite,
    e.g. test_sms_campaign_dlr.py, test_sms_send_dlr.py, every
    campaign DLR test routed through utils/campaign_dlr.py):
    status/code are verified to EXIST, never compared against a
    specific expected value -- call validate_dlr_format() with
    expected_status=None, expected_code=None (the default). This keeps
    the pre-existing rule (see dlr_helpers.py's own module docstring)
    that no generic test fails merely because status/provider_status/
    status_code differs.

  - Status-specific tests (an explicit DELIVRD or REJECTED scenario):
    pass the concrete expected_status/expected_code
    (DELIVERED_STATUS/DELIVERED_CODE or REJECTED_STATUS/REJECTED_CODE
    below) so a mismatch DOES fail that specific test.

Timestamp format: CORRECTED AGAIN, this time from a real live
/dlr/{id} response (GET http://140.245.230.67:8080/api/v1/dlr/
1522ff82-2818-4670-b24e-306f0cf9266b/json) the project owner pasted and
then explicitly confirmed as correct: submit_at/dlr_received_at are
"2026-10-06 15:29:58" -- ISO "yyyy-mm-dd hh:mm:ss" (WITH a space
separator, same shape utils/datetime_verification.py's
accept_iso_datetime already models for a different, unrelated field --
see that module's own "Generated at"/"Completed at" note), NOT the
"dd-mm-yyyy hh:mm:ss" this module assumed after an earlier, now-reversed
correction ("for dlrs date format is DD MM YYYY and time same as
platform"). is_valid_dlr_timestamp() now passes accept_iso_datetime=True
into validate_date_format() so BOTH shapes are accepted (dd-mm-yyyy
hh:mm:ss OR yyyy-mm-dd hh:mm:ss) rather than hard-switching and risking
a third reversal -- DLR_TIMESTAMP_FORMAT is kept as the ISO shape since
that is the one confirmed by a real, live API call (as opposed to a
verbal description), and is only used for a human-readable format name
in failure details, not for parsing itself (is_valid_dlr_timestamp()
delegates all real parsing to validate_date_format()).

template_id: CONFIRMED real behavior (project owner, from the SAME live
REJECTED DLR evidence above, code "807", template_id: null) -- a
REJECTED DLR can have a null template_id (plausibly: rejected before a
template was ever assigned to the message). template_id is therefore
required non-empty ONLY when the DLR's own `status` is NOT
REJECTED_STATUS; a null/blank template_id on a REJECTED DLR passes
format validation the same way a null/blank `units` does on a
default/status DLR (see _BILLING_FIELDS above) -- see the dedicated
"template_id" branch in validate_dlr_format() below.

Dynamic correlation: never hard-code message_id/mobile/sender/
entity_id/template_id/correlation_id anywhere a test uses this module --
every expected value passed into validate_dlr_correlation() must come
from the actual API/campaign/export data the test itself captured.

Bulk POST /dlr/verify has a DIFFERENT, CONFIRMED REAL response shape --
confirmed via two consecutive live pytest failures (identical
failed-fields fingerprint across two different campaigns/tests) plus
the project owner pasting the actual raw response body. A per-entry
bulk-verify result looks like:

    {"message_id": "...:1", "received": true, "status": "DELIVERED",
     "provider_status": "DELIVRD", "status_code": "000",
     "source": "DEFAULT_SMS", "billed": false, "clicked": false,
     "matched": true}

This is NOT the single-DLR schema above -- it has no service/sender/
mobile/entity_id/template_id/submit_at/dlr_received_at/units/
correlation_id at all, so forcing ALL_DLR_FIELDS onto it fails every
bulk-verify entry 100% of the time (observed: failed_fields always
['code', 'dlr_received_at', 'entity_id', 'mobile', 'sender', 'service',
'submit_at', 'template_id'], plus a spurious mobile mismatch since this
shape has no mobile field to correlate against). `provider_status`
(abbreviated, e.g. "DELIVRD") and `status_code` (e.g. "000") are the
bulk-shape's real counterparts of the single-DLR schema's `status`/
`code` fields; the bulk shape's OWN `status` field is a separate,
full-word value (e.g. "DELIVERED") and is only checked for presence,
never compared, since no confirmed full-word vocabulary was given.
`billed`/`clicked`/`matched`/`received` are booleans and are format-
checked as such. See ALL_BULK_VERIFY_FIELDS, extract_bulk_verify_fields(),
validate_bulk_verify_format(), and validate_bulk_verify_correlation()
below -- aggregate_bulk_dlr_validation() (every bulk call site's single
shared entry point) now routes through these, not validate_dlr_format()/
validate_dlr_correlation(). Mobile correlation is structurally
impossible against this shape (no mobile field at all) and is never
attempted for bulk results, consistent with other documented gaps in
this suite (see utils/dlr_helpers.py, utils/sms_dlr_dynamic_recipient.py).
The single-DLR schema/validators above are UNCHANGED and remain correct
for the single-message GET /dlr/{id} call sites
(utils/dlr_helpers.py::verify_and_validate_dlr()).
"""

from __future__ import annotations

from typing import Any, Optional

from utils.datetime_verification import validate_date_format

# ---------------------------------------------------------------------------
# Schema constants
# ---------------------------------------------------------------------------

# The DLR payload's timestamp format -- confirmed by a real, live
# /dlr/{id} response (project owner, see module docstring) to be ISO
# "yyyy-mm-dd hh:mm:ss" (WITH a space separator), reversing an earlier
# verbal "dd-mm-yyyy" assumption. is_valid_dlr_timestamp() below accepts
# BOTH this format and the platform's usual dd-mm-yyyy hh:mm:ss, so a
# DLR entry in either shape still passes. Kept as its own named
# constant here for DLR call sites/error messages, without duplicating
# the parsing logic -- see is_valid_dlr_timestamp() below.
DLR_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

# Every field the two baseline DLR payloads (REJECTED / DELIVERED) carry.
ALL_DLR_FIELDS = (
    "message_id",
    "service",
    "sender",
    "mobile",
    "status",
    "code",
    "submit_at",
    "dlr_received_at",
    "entity_id",
    "template_id",
    "units",
    "correlation_id",
)

# Fields that must always be a non-empty value (never just "present").
_REQUIRED_NON_EMPTY_FIELDS = (
    "message_id",
    "service",
    "sender",
    "mobile",
)
_TIMESTAMP_FIELDS = ("submit_at", "dlr_received_at")

# Required non-empty UNLESS the DLR's own status is REJECTED_STATUS --
# CONFIRMED real behavior (project owner, real live REJECTED DLR,
# code "807", template_id: null -- see module docstring): a rejection
# can happen before a template is ever assigned, so template_id is only
# required on a non-REJECTED DLR (see the dedicated "template_id"
# branch in validate_dlr_format() below).
#
# entity_id moved OUT of _REQUIRED_NON_EMPTY_FIELDS (project owner,
# live run 2026-10, test_send_json_real_sample_payload): NONE of that
# payload's 6 entries supply an entity_id at all (config/sms_api/
# test_data.yaml -- sms_json.real_sample_payload), yet 3 of the 6 real
# DLRs still came back with entity_id populated anyway (apparently
# auto-attached per-sender/account registration) while the other 3 came
# back blank -- both are real, both DELIVERED. entity_id is therefore
# NOT something a DLR always carries; it depends on whether the
# sender/account has one registered, which this validator has no way
# to know from the DLR body alone. Per project-owner decision, it is
# now optional everywhere (see the dedicated "entity_id" branch in
# validate_dlr_format() below) -- never required, whatever value is
# present is still reported for visibility.
_CONDITIONALLY_REQUIRED_FIELDS = ("template_id",)

# Billing-only fields -- confirmed real behavior (project owner): by
# default this environment only generates/receives the STATUS DLR for a
# message, not a separate billing DLR (same distinction already
# documented on utils/dlr_helpers.py::poll_bulk_dlr()'s require_billing
# parameter). `units` is billing information, so it is NOT required on
# a default/status DLR -- missing/blank is expected and does not fail
# format validation. Pass require_billing=True to validate_dlr_format()
# only for a test that specifically targets billing-DLR verification,
# where units must then be present and numeric.
_BILLING_FIELDS = ("units",)

# Status-specific baselines (used only by tests that explicitly target
# one of these two scenarios -- never applied to a generic presence/
# correlation test).
DELIVERED_STATUS = "DELIVRD"
DELIVERED_CODE = "000"
REJECTED_STATUS = "REJECTED"
REJECTED_CODE = "456"

# Human-readable labels, in the exact order the Final DLR Validation
# Report must print them.
_REPORT_FIELD_ORDER = (
    ("message_id", "Message ID"),
    ("mobile", "Mobile"),
    ("service", "Service"),
    ("sender", "Sender"),
    ("status", "Status"),
    ("code", "Code"),
    ("submit_at", "Submit At"),
    ("dlr_received_at", "DLR Received At"),
    ("entity_id", "Entity ID"),
    ("template_id", "Template ID"),
    ("units", "Units"),
    ("correlation_id", "Correlation ID"),
)


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def is_valid_dlr_timestamp(value: Any) -> bool:
    """True iff value is a real date-time in EITHER confirmed DLR
    shape: ISO "yyyy-mm-dd hh:mm:ss" (DLR_TIMESTAMP_FORMAT -- confirmed
    by a real live /dlr/{id} response, see module docstring) or the
    platform's usual "dd-mm-yyyy hh:mm:ss" (DATE_FORMATS). Reuses the
    project's already-confirmed date-time validator (utils/
    datetime_verification.py::validate_date_format(), field_kind=
    "date-time", accept_iso_datetime=True) rather than a second,
    independent strptime check that could drift out of sync with
    either convention."""
    ok, _parsed, _kind = validate_date_format(
        value, field_kind="date-time", accept_iso_datetime=True
    )
    return ok


def _is_numeric_value(value: Any) -> bool:
    """True iff value is numeric or a string that parses as a number --
    units is confirmed in the baseline payloads as either "1" (string)
    or a plain numeric value, so both are accepted."""
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return True
    try:
        float(str(value).strip())
        return True
    except (ValueError, TypeError):
        return False


def extract_full_dlr_fields(dlr_body: Any) -> dict:
    """Returns a dict with every key in ALL_DLR_FIELDS from a DLR API
    response body (or a single bulk-verify result entry), checking the
    top level first, then a nested "dlr" object, then a nested "data"
    object -- the same checked-shape pattern already used by
    utils/dlr_helpers.py::extract_dlr_fields(), just extended to the
    full baseline schema instead of only
    received/message_id/correlation_id. Any field not found is None --
    nothing here is guessed beyond what the body actually contains.

    The nested "dlr" object is CONFIRMED real (project owner, live GET
    {dlr_base_url}/api/v1/dlr/{message_id} response, no /json suffix):
    the top level of that response is an enriched summary (source/
    received/provider_status/status/status_code/received_at/billing{}/
    clicks{}/event_count/etc.) that does NOT itself carry
    service/entity_id and uses different names/formats for a few
    fields (status_code not code, received_at not dlr_received_at, ISO
    "yyyy-mm-ddThh:mm:ss" timestamps) -- the classic schema this
    validator is built from lives one level down, under "dlr". "data"
    is kept as a second, lower-priority fallback for any other shape
    that happens to nest it there instead; checked only for whatever
    the top level and "dlr" didn't already fill in."""
    result = {key: None for key in ALL_DLR_FIELDS}
    if not isinstance(dlr_body, dict):
        return result

    def _fill_from(obj: dict) -> None:
        for key in result:
            if result[key] is None and key in obj:
                result[key] = obj[key]

    # Nested "dlr" wins over the top level when BOTH carry the same key
    # (confirmed real: a message can have identically-named top-level
    # AND nested-"dlr" fields -- e.g. "submit_at" -- in two DIFFERENT
    # formats; "dlr" is the classic-schema record this validator is
    # built from, the top level is just an enriched summary, so "dlr"
    # is checked FIRST). "data" is a lower-priority fallback.
    nested_dlr = dlr_body.get("dlr")
    if isinstance(nested_dlr, dict):
        _fill_from(nested_dlr)
    _fill_from(dlr_body)
    nested_data = dlr_body.get("data")
    if isinstance(nested_data, dict):
        _fill_from(nested_data)
    return result


# ---------------------------------------------------------------------------
# Per-DLR format/schema validation
# ---------------------------------------------------------------------------

def validate_dlr_format(
    dlr_fields: dict,
    expected_status: Optional[str] = None,
    expected_code: Optional[str] = None,
    correlation_id_required: Optional[bool] = None,
    require_billing: Optional[bool] = None,
) -> dict:
    """Validates one DLR's fields against the baseline schema.

    expected_status/expected_code: leave both None for a GENERIC
    presence/correlation test -- status/code are then only checked to
    EXIST, never compared to a value, preserving this suite's existing
    rule that a generic DLR test must not fail merely because status/
    provider_status/status_code differs (see module docstring). Pass
    the concrete DELIVERED_STATUS/DELIVERED_CODE or
    REJECTED_STATUS/REJECTED_CODE only for a test that explicitly
    targets that scenario.

    correlation_id_required: True  -> correlation_id must be a non-empty
                                       value (the DELIVERED baseline).
                              False -> null is explicitly allowed (the
                                       REJECTED baseline).
                              None  -> generic test: null is allowed,
                                       same as False, since no baseline
                                       was specified either way.

    require_billing: False/None (default) -> this is a default STATUS
                                       DLR -- `units` (billing info) is
                                       NOT required; missing/blank is
                                       expected and passes, same as
                                       poll_bulk_dlr()'s own
                                       require_billing default. If
                                       `units` IS present anyway, it
                                       must still be numeric.
                      True  -> this test specifically targets a BILLING
                                       DLR -- `units` must be present
                                       and numeric, same as the old
                                       always-required behavior.

    Returns {"fields": {name: {"status": "PASS"/"FAIL", "value": ...,
    "detail": str}}, "passed": bool, "failed_fields": [name, ...]}.
    """
    fields = {}
    failed = []

    for key in ALL_DLR_FIELDS:
        value = dlr_fields.get(key)

        if key in _BILLING_FIELDS:
            if require_billing:
                ok = not _is_blank(value) and _is_numeric_value(value)
                detail = "PASS" if ok else f"missing/non-numeric units value: {value!r}"
            else:
                # Default status DLR: billing info is not expected --
                # missing/blank passes; a present-but-non-numeric value
                # still fails (a real value that doesn't make sense).
                ok = _is_blank(value) or _is_numeric_value(value)
                detail = "PASS" if _is_blank(value) else ("PASS" if ok else f"present but non-numeric units value: {value!r}")
                if _is_blank(value):
                    detail = "Not Applicable (status DLR)"
        elif key == "template_id":
            if dlr_fields.get("status") == REJECTED_STATUS:
                # A REJECTED DLR may have no template_id at all
                # (confirmed real evidence) -- missing/blank passes;
                # a present value is still reported.
                ok = True
                detail = "PASS" if not _is_blank(value) else "Not Applicable (REJECTED DLR)"
            else:
                ok = not _is_blank(value)
                detail = "PASS" if ok else "missing/empty template_id"
        elif key == "entity_id":
            # Optional everywhere (project owner decision, 2026-10 --
            # see the comment above _REQUIRED_NON_EMPTY_FIELDS): whether
            # a DLR carries an entity_id depends on sender/account
            # registration, not on anything this validator can derive
            # from the DLR body -- missing/blank always passes, a
            # present value is still reported for visibility.
            ok = True
            detail = "PASS" if not _is_blank(value) else "Not Applicable (no entity_id attached)"
        elif key in _REQUIRED_NON_EMPTY_FIELDS:
            ok = not _is_blank(value)
            detail = "PASS" if ok else f"missing/empty {key}"
        elif key in _TIMESTAMP_FIELDS:
            ok = is_valid_dlr_timestamp(value)
            detail = "PASS" if ok else (
                f"{key}={value!r} does not match the DLR timestamp format "
                f"'{DLR_TIMESTAMP_FORMAT}' (dd-mm-yyyy hh:mm:ss, same as the platform)"
            )
        elif key == "status":
            if expected_status is None:
                ok = not _is_blank(value)
                detail = "PASS" if ok else "missing/empty status"
            else:
                ok = value == expected_status
                detail = "PASS" if ok else f"expected status={expected_status!r}, got {value!r}"
        elif key == "code":
            if expected_code is None:
                ok = not _is_blank(value)
                detail = "PASS" if ok else "missing/empty code"
            else:
                ok = value == expected_code
                detail = "PASS" if ok else f"expected code={expected_code!r}, got {value!r}"
        elif key == "correlation_id":
            if correlation_id_required:
                ok = not _is_blank(value)
                detail = "PASS" if ok else "correlation_id is required for this scenario but missing/empty"
            else:
                ok = True  # null is explicitly allowed (generic + REJECTED baseline)
                detail = "PASS" if not _is_blank(value) else "NULL Allowed"
        else:  # pragma: no cover - defensive, ALL_DLR_FIELDS is exhaustive above
            ok = not _is_blank(value)
            detail = "PASS" if ok else f"missing/empty {key}"

        # Type check -- every field in the two confirmed baseline DLR
        # payloads (module docstring) is a JSON STRING whenever it's
        # present at all, including the numeric-looking ones (code
        # "000"/"456", units "1") -- never a bare number or boolean.
        # Whatever the field-specific check above decided, a non-blank
        # value that isn't a str is still a format defect and fails
        # here, even if that check itself passed (e.g. units="1" vs
        # units=1 -- both numeric, only the first is a valid DLR
        # value).
        if ok and not _is_blank(value) and not isinstance(value, str):
            ok = False
            detail = f"{key}={value!r} is not a string (type={type(value).__name__})"

        fields[key] = {"status": "PASS" if ok else "FAIL", "value": value, "detail": detail}
        if not ok:
            failed.append(key)

    return {"fields": fields, "passed": not failed, "failed_fields": failed}


# ---------------------------------------------------------------------------
# Correlation (message_id / mobile)
# ---------------------------------------------------------------------------

def validate_dlr_correlation(
    dlr_fields: dict,
    expected_message_id: Optional[str] = None,
    expected_mobile: Optional[str] = None,
) -> dict:
    """Checks the DLR's message_id (always) and mobile (only if
    expected_mobile is given -- many call sites don't have a confirmed
    recipient/phone field to compare against, see dlr_helpers.py's own
    documented gap) against the values the TEST ITSELF captured
    dynamically from the API/campaign/export data -- never hard-coded.

    Returns {"message_id_match": bool, "mobile_match": bool|None (None =
    not checked), "passed": bool, "detail": str}.
    """
    message_id_match = True
    detail_parts = []

    if expected_message_id is not None:
        actual = dlr_fields.get("message_id")
        message_id_match = actual == expected_message_id
        if not message_id_match:
            detail_parts.append(
                f"message_id mismatch: DLR={actual!r}, expected={expected_message_id!r}"
            )

    mobile_match = None
    if expected_mobile is not None:
        actual_mobile = dlr_fields.get("mobile")
        mobile_match = str(actual_mobile or "").strip() == str(expected_mobile).strip()
        if not mobile_match:
            detail_parts.append(
                f"mobile mismatch: DLR={actual_mobile!r}, expected={expected_mobile!r}"
            )

    passed = message_id_match and (mobile_match is None or mobile_match)
    return {
        "message_id_match": message_id_match,
        "mobile_match": mobile_match,
        "passed": passed,
        "detail": "; ".join(detail_parts) if detail_parts else "PASS",
    }


# ---------------------------------------------------------------------------
# Final DLR Validation Report (single DLR)
# ---------------------------------------------------------------------------

def build_dlr_validation_report(format_result: dict, correlation_result: dict) -> str:
    """Builds the EXACT 'Final DLR Validation Report' text block the
    project owner specified, for one DLR."""
    lines = ["DLR Verification", ""]
    width = max(len(label) for _, label in _REPORT_FIELD_ORDER)
    for key, label in _REPORT_FIELD_ORDER:
        field = format_result["fields"][key]
        if key == "correlation_id" and field["status"] == "PASS" and field["detail"] == "NULL Allowed":
            value_text = "PASS / NULL Allowed"
        elif key == "units" and field["status"] == "PASS" and field["detail"] == "Not Applicable (status DLR)":
            value_text = "PASS / N/A (status DLR)"
        elif key == "template_id" and field["status"] == "PASS" and field["detail"] == "Not Applicable (REJECTED DLR)":
            value_text = "PASS / N/A (REJECTED DLR)"
        elif key == "entity_id" and field["status"] == "PASS" and field["detail"] == "Not Applicable (no entity_id attached)":
            value_text = "PASS / N/A (no entity_id attached)"
        else:
            value_text = field["status"]
        lines.append(f"{label.ljust(width)} : {value_text}")

    overall_passed = format_result["passed"] and correlation_result["passed"]
    lines.append("")
    lines.append(f"{'DLR Format'.ljust(width)} : {'PASS' if format_result['passed'] else 'FAIL'}")
    lines.append(f"{'Correlation'.ljust(width)} : {'PASS' if correlation_result['passed'] else 'FAIL'}")
    lines.append("")
    lines.append(f"{'RESULT'.ljust(width)} : {'PASS' if overall_passed else 'FAIL'}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Bulk POST /dlr/verify format/schema validation -- CONFIRMED REAL SHAPE
# ---------------------------------------------------------------------------
#
# Real per-entry shape of a bulk /dlr/verify result, re-confirmed across
# 10+ independent live runs (2026-10) spanning click-tracking, OTP,
# transactional and promotional campaigns -- every single one, INCLUDING
# the dedicated short-URL-click test (test_sms_campaign_short_url_click_
# dlr.py), came back as:
#
#   {"message_id": "...:1", "received": true, "status": "DELIVERED",
#    "provider_status": "DELIVRD", "status_code": "000",
#    "source": "DEFAULT_SMS", "billed": false, "clicked": false,
#    "dlr": {... classic single-DLR schema, same shape/nesting as the
#            single-message GET /dlr/{id} endpoint's own "dlr" object ...}}
#
# CORRECTED (2026-10): an earlier version of this module claimed
# "matched": true was also part of this confirmed shape. It never once
# appeared in any of the 10+ real responses above -- not even on the
# click-specific test, where a real click-correlation flag would most
# plausibly show up. Keeping it required made EVERY bulk-verify-based
# DLR test in the suite fail on "matched" alone (format/schema otherwise
# fully valid). "matched" is now optional everywhere (see the dedicated
# "matched" branch in validate_bulk_verify_format() below) -- never
# required, whatever value is present (if ever) is still reported.
#
# Also newly observed (not previously documented, and not yet validated
# by this module): each real entry now nests a "dlr" object carrying the
# classic single-DLR schema, just like the single-message GET /dlr/{id}
# endpoint. This validator still only checks the FLAT fields below --
# nothing here currently reads bulk_fields["dlr"] -- call out for a
# follow-up if that nested object ever needs its own check here too.
#
# This is a DIFFERENT, FLAT (at this level) shape from the single-DLR
# schema above -- none of service/sender/mobile/entity_id/template_id/
# submit_at/dlr_received_at/units/correlation_id exist at the TOP level
# here (they live one level down, inside "dlr", unused by this module).

ALL_BULK_VERIFY_FIELDS = (
    "message_id",
    "received",
    "status",
    "provider_status",
    "status_code",
    "source",
    "billed",
    "clicked",
    "matched",
)

# message_id/status/provider_status/status_code/source must always be a
# non-empty value on a real bulk-verify entry.
_BULK_VERIFY_REQUIRED_NON_EMPTY_FIELDS = (
    "message_id",
    "status",
    "provider_status",
    "status_code",
    "source",
)

# received/billed/clicked are booleans in the real response -- format-
# checked for type, not for a specific value (billed/clicked are
# business-outcome flags, not format defects, except see require_billing
# below). "matched" is deliberately NOT in this tuple -- see the
# dedicated "matched" branch in validate_bulk_verify_format(), which
# treats it as optional (2026-10 correction, module docstring above).
_BULK_VERIFY_BOOLEAN_FIELDS = ("received", "billed", "clicked")

_BULK_VERIFY_REPORT_FIELD_ORDER = (
    ("message_id", "Message ID"),
    ("received", "Received"),
    ("status", "Status"),
    ("provider_status", "Provider Status"),
    ("status_code", "Status Code"),
    ("source", "Source"),
    ("billed", "Billed"),
    ("clicked", "Clicked"),
    ("matched", "Matched"),
)


def extract_bulk_verify_fields(entry: Any) -> dict:
    """Returns a dict with every key in ALL_BULK_VERIFY_FIELDS from one
    bulk /dlr/verify result entry. Confirmed real shape is FLAT (no
    nested "data" object, unlike the single-DLR GET /dlr/{id} shape),
    so this is a straight top-level extraction -- nothing here is
    guessed beyond what the entry actually contains."""
    result = {key: None for key in ALL_BULK_VERIFY_FIELDS}
    if not isinstance(entry, dict):
        return result
    for key in result:
        if key in entry:
            result[key] = entry[key]
    return result


def validate_bulk_verify_format(
    bulk_fields: dict,
    expected_status: Optional[str] = None,
    expected_code: Optional[str] = None,
    require_billing: Optional[bool] = None,
    require_click_match: Optional[bool] = None,
) -> dict:
    """Validates one bulk-verify entry's fields against the CONFIRMED
    REAL bulk schema (see module docstring) -- NOT the single-DLR
    schema validate_dlr_format() uses.

    expected_status/expected_code are compared against `provider_status`/
    `status_code` -- the bulk shape's real counterparts of the
    single-DLR schema's `status`/`code` fields (both abbreviated,
    DLR-style values, e.g. "DELIVRD"/"000"). Leave both None for a
    GENERIC presence/correlation test, preserving the same "a generic
    DLR test must not fail merely because status/provider_status/
    status_code differs" rule as validate_dlr_format(). Pass
    DELIVERED_STATUS/DELIVERED_CODE or REJECTED_STATUS/REJECTED_CODE
    only for a test that explicitly targets that scenario.

    The bulk shape's OWN `status` field is a separate, full-word value
    (e.g. "DELIVERED") -- it is only checked for presence here, never
    compared to expected_status, since no confirmed full-word
    vocabulary was given by the project owner.

    require_billing: the bulk shape has no numeric billing field (no
    `units`) -- `billed` is a boolean outcome flag. False/None
    (default, status DLR) only checks `billed` is a real boolean,
    whatever its value. True (a test specifically targeting billing)
    additionally requires billed is True.

    require_click_match: `matched` is OPTIONAL (2026-10 correction,
    module docstring above) -- it never appeared in any of 10+ real
    bulk-verify responses, including the dedicated short-URL-click test.
    False/None (default) means missing/blank passes; a present value is
    still type-checked as a boolean. True (a test specifically targeting
    click-correlation, once/if a real `matched: true` response is ever
    actually observed) additionally requires it be present and True.

    Returns the same shape as validate_dlr_format(): {"fields": {...},
    "passed": bool, "failed_fields": [...]}.
    """
    fields = {}
    failed = []

    for key in ALL_BULK_VERIFY_FIELDS:
        value = bulk_fields.get(key)

        if key == "provider_status":
            if expected_status is None:
                ok = not _is_blank(value)
                detail = "PASS" if ok else "missing/empty provider_status"
            else:
                ok = value == expected_status
                detail = "PASS" if ok else f"expected provider_status={expected_status!r}, got {value!r}"
        elif key == "status_code":
            if expected_code is None:
                ok = not _is_blank(value)
                detail = "PASS" if ok else "missing/empty status_code"
            else:
                ok = value == expected_code
                detail = "PASS" if ok else f"expected status_code={expected_code!r}, got {value!r}"
        elif key == "billed":
            ok = isinstance(value, bool)
            if ok and require_billing:
                ok = value is True
                detail = "PASS" if ok else f"require_billing=True but billed={value!r}"
            else:
                detail = "PASS" if ok else f"billed is not a boolean: {value!r}"
        elif key == "matched":
            # Optional everywhere by default -- see module docstring and
            # this function's own docstring (2026-10 correction): never
            # once observed in a real bulk-verify response. Missing/blank
            # passes; a present value is still type-checked as a boolean.
            if require_click_match:
                ok = isinstance(value, bool) and value is True
                detail = "PASS" if ok else f"require_click_match=True but matched={value!r}"
            elif _is_blank(value):
                ok = True
                detail = "Not Applicable (not returned by this endpoint)"
            else:
                ok = isinstance(value, bool)
                detail = "PASS" if ok else f"matched is not a boolean: {value!r}"
        elif key in _BULK_VERIFY_BOOLEAN_FIELDS:
            ok = isinstance(value, bool)
            detail = "PASS" if ok else f"{key} is not a boolean: {value!r}"
        elif key in _BULK_VERIFY_REQUIRED_NON_EMPTY_FIELDS:
            ok = not _is_blank(value)
            detail = "PASS" if ok else f"missing/empty {key}"
        else:  # pragma: no cover - defensive, ALL_BULK_VERIFY_FIELDS is exhaustive above
            ok = not _is_blank(value)
            detail = "PASS" if ok else f"missing/empty {key}"

        # Type check -- same rule as validate_dlr_format(): every
        # NON-boolean field in the confirmed real bulk-verify shape
        # (message_id/status/provider_status/status_code/source) is a
        # JSON string whenever present. received/billed/clicked/matched
        # are excluded -- those are confirmed real booleans and are
        # already type-checked above as booleans, not strings.
        if ok and key not in _BULK_VERIFY_BOOLEAN_FIELDS and key != "matched" and not _is_blank(value) and not isinstance(value, str):
            ok = False
            detail = f"{key}={value!r} is not a string (type={type(value).__name__})"

        fields[key] = {"status": "PASS" if ok else "FAIL", "value": value, "detail": detail}
        if not ok:
            failed.append(key)

    return {"fields": fields, "passed": not failed, "failed_fields": failed}


def validate_bulk_verify_correlation(
    bulk_fields: dict,
    expected_message_id: Optional[str] = None,
) -> dict:
    """Checks the bulk-verify entry's message_id (only if
    expected_message_id is given) against the value the TEST ITSELF
    captured dynamically -- never hard-coded.

    Mobile correlation is NEVER attempted here: the confirmed real bulk
    /dlr/verify shape has no mobile field at all, so comparing against
    an expected recipient is structurally impossible (not a defect to
    report) -- this mirrors the documented gap already used elsewhere
    in this suite (e.g. utils/sms_dlr_dynamic_recipient.py). Returns
    mobile_match=None (not checked) always.

    Returns the same shape as validate_dlr_correlation():
    {"message_id_match": bool, "mobile_match": None, "passed": bool,
    "detail": str}.
    """
    message_id_match = True
    detail_parts = []

    if expected_message_id is not None:
        actual = bulk_fields.get("message_id")
        message_id_match = actual == expected_message_id
        if not message_id_match:
            detail_parts.append(
                f"message_id mismatch: DLR={actual!r}, expected={expected_message_id!r}"
            )

    return {
        "message_id_match": message_id_match,
        "mobile_match": None,
        "passed": message_id_match,
        "detail": "; ".join(detail_parts) if detail_parts else "PASS",
    }


# ---------------------------------------------------------------------------
# Bulk aggregate validation (10K-flooding-style tests)
# ---------------------------------------------------------------------------

def aggregate_bulk_dlr_validation(
    message_ids,
    results: dict,
    expected_mobiles: Optional[dict] = None,
    expected_status: Optional[str] = None,
    expected_code: Optional[str] = None,
    correlation_id_required: Optional[bool] = None,
    require_billing: Optional[bool] = None,
    require_click_match: Optional[bool] = None,
):
    """Runs format + correlation validation for EVERY message_id in
    message_ids against its entry in results (a {message_id: <raw
    bulk-verify record dict>} mapping, e.g. from
    utils/dlr_helpers.py::extract_bulk_dlr_results()/poll_bulk_dlr()),
    and returns aggregate counts + a list of per-message failure rows.

    This validates against the CONFIRMED REAL bulk POST /dlr/verify
    schema (validate_bulk_verify_format()/validate_bulk_verify_correlation(),
    see module docstring) -- NOT the single-DLR GET /dlr/{id} schema
    (validate_dlr_format()/validate_dlr_correlation(), still used
    unchanged by utils/dlr_helpers.py::verify_and_validate_dlr() for
    single-message call sites). Every bulk call site in this suite
    (utils/campaign_dlr.py, test_sms_campaign_dlr_bulk.py,
    test_sms_json_dlr.py, test_sms_campaign_dlr_dynamic_recipient_file.py,
    utils/dlr_helpers.py::verify_and_validate_dlrs_bulk()) routes
    through this one function, so fixing it here fixes all of them.

    expected_mobiles: accepted for backward compatibility with existing
    call sites and still used for the recipient shown in a failure row,
    but NEVER used to fail a bulk result -- the confirmed real bulk
    /dlr/verify shape has no mobile field at all, so mobile correlation
    is structurally impossible here (mobile_mismatches always stays 0
    for this path; see validate_bulk_verify_correlation()).

    correlation_id_required is accepted for backward compatibility but
    unused -- the bulk shape has no correlation_id field either
    (missing_correlation_id always stays 0 for this path).

    Returns (counts: dict, failures: list[(message_id, recipient, reason)]).
    """
    expected_mobiles = expected_mobiles or {}
    counts = {
        "total_expected": len(message_ids),
        "total_received": 0,
        "valid_format": 0,
        "invalid_format": 0,
        "missing_required_fields": 0,
        "invalid_timestamps": 0,
        "message_id_mismatches": 0,
        "mobile_mismatches": 0,
        "invalid_status": 0,
        "invalid_code": 0,
        "missing_correlation_id": 0,
        "duplicate_dlrs": 0,
        "missing_dlrs": 0,
    }
    failures = []
    seen_keys = set()

    for mid in message_ids:
        recipient = expected_mobiles.get(mid, "")
        entry = results.get(mid) if isinstance(results, dict) else None

        if not isinstance(entry, dict):
            counts["missing_dlrs"] += 1
            failures.append((mid, recipient, "DLR entry missing entirely"))
            continue

        if not entry.get("received"):
            counts["missing_dlrs"] += 1
            failures.append((mid, recipient, "DLR entry present but received=false"))
            continue

        counts["total_received"] += 1

        dedup_key = entry.get("message_id") or mid
        if dedup_key in seen_keys:
            counts["duplicate_dlrs"] += 1
            failures.append((mid, recipient, "duplicate DLR entry for this message_id"))
        seen_keys.add(dedup_key)

        bulk_fields = extract_bulk_verify_fields(entry)
        fmt = validate_bulk_verify_format(
            bulk_fields,
            expected_status=expected_status,
            expected_code=expected_code,
            require_billing=require_billing,
            require_click_match=require_click_match,
        )
        corr = validate_bulk_verify_correlation(bulk_fields, expected_message_id=mid)

        if fmt["passed"]:
            counts["valid_format"] += 1
        else:
            counts["invalid_format"] += 1
            failed = set(fmt["failed_fields"])
            if failed & set(_BULK_VERIFY_REQUIRED_NON_EMPTY_FIELDS):
                counts["missing_required_fields"] += 1
            if "provider_status" in failed:
                counts["invalid_status"] += 1
            if "status_code" in failed:
                counts["invalid_code"] += 1
            # No timestamp or correlation_id fields exist in the bulk
            # /dlr/verify shape -- invalid_timestamps/missing_correlation_id
            # stay 0 for this path, they are not fabricated as failures.
            failures.append((mid, recipient, f"DLR format failed: {sorted(failed)}"))

        if not corr["message_id_match"]:
            counts["message_id_mismatches"] += 1
            failures.append((mid, recipient, corr["detail"]))
        # Mobile correlation is structurally impossible against the bulk
        # /dlr/verify shape (no mobile field at all) -- never attempted,
        # so mobile_mismatches always stays 0 for this path.

    return counts, failures


_BULK_REPORT_FIELD_ORDER = (
    ("total_expected", "Total Expected DLRs"),
    ("total_received", "Total Received DLRs"),
    ("valid_format", "Valid DLR Format"),
    ("invalid_format", "Invalid DLR Format"),
    ("missing_required_fields", "Missing Required Fields"),
    ("invalid_timestamps", "Invalid Timestamps"),
    ("message_id_mismatches", "Message ID Mismatches"),
    ("mobile_mismatches", "Mobile Mismatches"),
    ("invalid_status", "Invalid Status"),
    ("invalid_code", "Invalid Code"),
    ("missing_correlation_id", "Missing Correlation ID"),
    ("duplicate_dlrs", "Duplicate DLRs"),
    ("missing_dlrs", "Missing DLRs"),
)


def build_bulk_dlr_validation_report(counts: dict) -> str:
    """Builds the exact aggregate DLR validation report block for bulk/
    flooding-style tests (e.g. the 10K recipient-file DLR test)."""
    width = max(len(label) for _, label in _BULK_REPORT_FIELD_ORDER)
    lines = [f"{label.ljust(width)} : {counts[key]}" for key, label in _BULK_REPORT_FIELD_ORDER]
    return "\n".join(lines)


def bulk_validation_passed(counts: dict) -> bool:
    """True iff the aggregate has zero of every failure-category count.
    A caller combining this with its own business-status assertions
    should still apply the 'generic test ignores status/code differences
    unless explicitly expected' rule by passing expected_status=None/
    expected_code=None into aggregate_bulk_dlr_validation() -- in that
    case invalid_status/invalid_code can only be non-zero if the field
    was missing outright, not merely a different value."""
    return all(
        counts[key] == 0
        for key in (
            "invalid_format",
            "missing_required_fields",
            "invalid_timestamps",
            "message_id_mismatches",
            "mobile_mismatches",
            "invalid_status",
            "invalid_code",
            "missing_correlation_id",
            "duplicate_dlrs",
            "missing_dlrs",
        )
    )


# ---------------------------------------------------------------------------
# Short URL click-event format/schema validation
# ---------------------------------------------------------------------------
#
# Baseline click-event payload, given directly by the project owner as
# real evidence of what the DLR Receiver returns for a message_id AFTER
# its short URL has been clicked (a DIFFERENT shape from the plain SMS
# DLR body validated above -- no top-level `received` field at all):
#
#   {"event": "short_link", "url_type": "dynamic",
#    "received_at": "dd-mm-yyyy hh:mm:ss",
#    "data": {"visited_count": "2", "url_type": "dynamic",
#              "contact": "...", "url_key": "...", "short_url": "...",
#              "destination_url": "...", "channel": "sms",
#              "ip_address": "...", "operating_system": "...",
#              "operating_system_version": "...", "browser": "...",
#              "browser_version": "...", "device_type": "...",
#              "clicked_at": "dd-mm-yyyy hh:mm:ss",
#              "message_id": "...", "correlation_id": ""}}
#
# correlation_id is confirmed real as an empty STRING ("") here, not
# null like the plain DLR baseline -- is_click_correlation_id_blank()
# below treats both the same way (blank is allowed by default).

CLICK_EXPECTED_EVENT = "short_link"

# Required non-empty fields -- event/url_type/received_at come from the
# top level, everything else from the nested `data` object; both are
# flattened into one dict by extract_click_fields() below.
_CLICK_REQUIRED_NON_EMPTY_FIELDS = (
    "event",
    "url_type",
    "contact",
    "url_key",
    "short_url",
    "destination_url",
    "channel",
    "ip_address",
    "operating_system",
    "operating_system_version",
    "browser",
    "browser_version",
    "device_type",
    "message_id",
)
_CLICK_NUMERIC_FIELDS = ("visited_count",)
_CLICK_TIMESTAMP_FIELDS = ("received_at", "clicked_at")

ALL_CLICK_FIELDS = (
    "event",
    "url_type",
    "received_at",
    "visited_count",
    "contact",
    "url_key",
    "short_url",
    "destination_url",
    "channel",
    "ip_address",
    "operating_system",
    "operating_system_version",
    "browser",
    "browser_version",
    "device_type",
    "clicked_at",
    "message_id",
    "correlation_id",
)

_CLICK_REPORT_FIELD_ORDER = (
    ("event", "Event"),
    ("url_type", "URL Type"),
    ("contact", "Contact"),
    ("message_id", "Message ID"),
    ("short_url", "Short URL"),
    ("destination_url", "Destination URL"),
    ("channel", "Channel"),
    ("ip_address", "IP Address"),
    ("operating_system", "Operating System"),
    ("operating_system_version", "OS Version"),
    ("browser", "Browser"),
    ("browser_version", "Browser Version"),
    ("device_type", "Device Type"),
    ("visited_count", "Visited Count"),
    ("clicked_at", "Clicked At"),
    ("received_at", "Received At"),
    ("correlation_id", "Correlation ID"),
)


def is_click_event_body(body: Any) -> bool:
    """True iff `body` matches the click-event shape (top-level
    event == "short_link") rather than the plain SMS DLR shape --
    confirmed real evidence: after a short URL is clicked, a DLR
    Receiver lookup for that message_id returns THIS shape instead of
    the plain DLR body, so callers must branch on this before deciding
    which validator (validate_dlr_format vs validate_click_format)
    actually applies to what they got back."""
    return isinstance(body, dict) and str(body.get("event") or "").strip().lower() == CLICK_EXPECTED_EVENT


def extract_click_fields(click_body: Any) -> dict:
    """Flattens a click-event body into one dict with every key in
    ALL_CLICK_FIELDS: event/url_type/received_at from the top level,
    everything else from the nested `data` object. Any field not found
    is None -- nothing here is guessed beyond what the body actually
    contains. If both the top level and `data` carry url_type (as the
    real sample does), the top-level value wins and data's is only used
    as a fallback."""
    result = {key: None for key in ALL_CLICK_FIELDS}
    if not isinstance(click_body, dict):
        return result

    result["event"] = click_body.get("event")
    result["url_type"] = click_body.get("url_type")
    result["received_at"] = click_body.get("received_at")

    data = click_body.get("data")
    if isinstance(data, dict):
        for key in ALL_CLICK_FIELDS:
            if key in ("event", "received_at"):
                continue
            if result.get(key) is None and key in data:
                result[key] = data[key]
    return result


def validate_click_format(
    click_fields: dict,
    expected_event: Optional[str] = CLICK_EXPECTED_EVENT,
    expected_channel: Optional[str] = None,
    correlation_id_required: Optional[bool] = None,
) -> dict:
    """Validates one click-event body's fields against the baseline
    short-URL-click schema. Mirrors validate_dlr_format()'s shape and
    rules:

    expected_event: pass None to only check `event` exists (generic);
    the default CLICK_EXPECTED_EVENT ("short_link") asserts the exact
    confirmed value, since every real sample of this event carries it.

    expected_channel: leave None to only check `channel` exists --
    this project's own sample is "sms", but a generic click-format
    check shouldn't assume every channel this ever fires for.

    correlation_id_required: True -> correlation_id must be non-blank.
                              False/None -> blank ("" or null) is
                              explicitly allowed, matching the real
                              sample's own correlation_id: "".

    Returns the same shape as validate_dlr_format(): {"fields": {...},
    "passed": bool, "failed_fields": [...]}.
    """
    fields = {}
    failed = []

    for key in ALL_CLICK_FIELDS:
        value = click_fields.get(key)

        if key == "event":
            if expected_event is None:
                ok = not _is_blank(value)
                detail = "PASS" if ok else "missing/empty event"
            else:
                ok = value == expected_event
                detail = "PASS" if ok else f"expected event={expected_event!r}, got {value!r}"
        elif key == "channel":
            if expected_channel is None:
                ok = not _is_blank(value)
                detail = "PASS" if ok else "missing/empty channel"
            else:
                ok = value == expected_channel
                detail = "PASS" if ok else f"expected channel={expected_channel!r}, got {value!r}"
        elif key in _CLICK_NUMERIC_FIELDS:
            ok = not _is_blank(value) and _is_numeric_value(value)
            detail = "PASS" if ok else f"missing/non-numeric {key} value: {value!r}"
        elif key in _CLICK_TIMESTAMP_FIELDS:
            ok = is_valid_dlr_timestamp(value)
            detail = "PASS" if ok else (
                f"{key}={value!r} does not match the platform timestamp format "
                f"'{DLR_TIMESTAMP_FORMAT}' (dd-mm-yyyy hh:mm:ss)"
            )
        elif key == "correlation_id":
            if correlation_id_required:
                ok = not _is_blank(value)
                detail = "PASS" if ok else "correlation_id is required for this scenario but missing/empty"
            else:
                ok = True  # blank ("" or null) is explicitly allowed
                detail = "PASS" if not _is_blank(value) else "Blank Allowed"
        elif key in _CLICK_REQUIRED_NON_EMPTY_FIELDS:
            ok = not _is_blank(value)
            detail = "PASS" if ok else f"missing/empty {key}"
        elif key == "url_type":
            ok = not _is_blank(value)
            detail = "PASS" if ok else "missing/empty url_type"
        else:  # pragma: no cover - defensive, ALL_CLICK_FIELDS is exhaustive above
            ok = not _is_blank(value)
            detail = "PASS" if ok else f"missing/empty {key}"

        fields[key] = {"status": "PASS" if ok else "FAIL", "value": value, "detail": detail}
        if not ok:
            failed.append(key)

    return {"fields": fields, "passed": not failed, "failed_fields": failed}


def validate_click_correlation(
    click_fields: dict,
    expected_message_id: Optional[str] = None,
    expected_contact: Optional[str] = None,
    expected_short_url: Optional[str] = None,
) -> dict:
    """Checks the click event's message_id (always, if given), contact
    (the clicking recipient's number) and short_url (the exact link that
    was clicked) against values the TEST ITSELF captured dynamically --
    never hard-coded. Mirrors validate_dlr_correlation()'s shape.

    Returns {"message_id_match": bool, "contact_match": bool|None,
    "short_url_match": bool|None, "passed": bool, "detail": str}.
    """
    message_id_match = True
    contact_match = None
    short_url_match = None
    detail_parts = []

    if expected_message_id is not None:
        actual = click_fields.get("message_id")
        message_id_match = actual == expected_message_id
        if not message_id_match:
            detail_parts.append(
                f"message_id mismatch: click event={actual!r}, expected={expected_message_id!r}"
            )

    if expected_contact is not None:
        actual_contact = click_fields.get("contact")
        contact_match = str(actual_contact or "").strip() == str(expected_contact).strip()
        if not contact_match:
            detail_parts.append(
                f"contact mismatch: click event={actual_contact!r}, expected={expected_contact!r}"
            )

    if expected_short_url is not None:
        actual_short_url = str(click_fields.get("short_url") or "").strip()
        short_url_match = actual_short_url == str(expected_short_url).strip()
        if not short_url_match:
            detail_parts.append(
                f"short_url mismatch: click event={actual_short_url!r}, expected={expected_short_url!r}"
            )

    passed = (
        message_id_match
        and (contact_match is None or contact_match)
        and (short_url_match is None or short_url_match)
    )
    return {
        "message_id_match": message_id_match,
        "contact_match": contact_match,
        "short_url_match": short_url_match,
        "passed": passed,
        "detail": "; ".join(detail_parts) if detail_parts else "PASS",
    }


def build_click_validation_report(format_result: dict, correlation_result: dict) -> str:
    """Builds a 'Short URL Click Verification' report block, mirroring
    build_dlr_validation_report()'s layout/convention for the click-event
    schema."""
    lines = ["Short URL Click Verification", ""]
    width = max(len(label) for _, label in _CLICK_REPORT_FIELD_ORDER)
    for key, label in _CLICK_REPORT_FIELD_ORDER:
        field = format_result["fields"][key]
        if key == "correlation_id" and field["status"] == "PASS" and field["detail"] == "Blank Allowed":
            value_text = "PASS / Blank Allowed"
        else:
            value_text = field["status"]
        lines.append(f"{label.ljust(width)} : {value_text}")

    overall_passed = format_result["passed"] and correlation_result["passed"]
    lines.append("")
    lines.append(f"{'Click Format'.ljust(width)} : {'PASS' if format_result['passed'] else 'FAIL'}")
    lines.append(f"{'Correlation'.ljust(width)} : {'PASS' if correlation_result['passed'] else 'FAIL'}")
    lines.append("")
    lines.append(f"{'RESULT'.ljust(width)} : {'PASS' if overall_passed else 'FAIL'}")
    return "\n".join(lines)
