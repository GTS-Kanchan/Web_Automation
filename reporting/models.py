"""
reporting/models.py -- shared constants / tiny structures used across the
reporting package. Deliberately NOT heavy dataclasses: every other module
passes plain dicts (so they serialize to JSON with zero translation step),
this module just documents the shape and the controlled vocabularies.
"""
import re

# Canonical test_record shape (see collector.build_record):
#   test, channel, feature, status, when, marker, worker, duration,
#   category, fingerprint, error, error_raw, stack_trace, screenshot, log

STATUS_PASSED  = "passed"
STATUS_FAILED  = "failed"
STATUS_SKIPPED = "skipped"
STATUS_XFAILED = "xfailed"
STATUS_XPASSED = "xpassed"

ALL_STATUSES = (STATUS_PASSED, STATUS_FAILED, STATUS_SKIPPED, STATUS_XFAILED, STATUS_XPASSED)

# Secret-shaped keys that must NEVER appear in any reporting JSON/HTML --
# matched the same way utils.config.is_secret_name already does, kept as
# an independent, explicit list here (reporting must stay safe even if
# that helper's rules ever change for an unrelated reason).
_SECRET_MARKERS = ("password", "token", "secret", "cookie", "auth", "storage_state", "key")


def looks_like_secret_key(name: str) -> bool:
    lowered = (name or "").lower()
    return any(marker in lowered for marker in _SECRET_MARKERS)

# Phone numbers (DLR recipients, in particular) must not be exposed in
# full in any report output (requirement #15/#38: "mask phone numbers
# where appropriate -- do not expose sensitive recipient information
# unnecessarily"). Matches a leading optional "+" followed by 7-15
# digits (optionally separated by spaces/dashes/dots/parens), which
# covers both E.164-style numbers and the loosely-formatted numbers
# that show up in SMS/DLR provider error text and stack traces.
_PHONE_RE = re.compile(r"(?<!\d)(\+?[\d][\d\-\.\s()]{5,17}\d)(?!\d)")


def _mask_one(match) -> str:
    digits = re.sub(r"\D", "", match.group(0))
    if len(digits) < 7:
        # Too short to confidently be a phone number -- leave untouched
        # rather than risk masking an unrelated short numeric token
        # (duration, HTTP status code, etc.).
        return match.group(0)
    prefix = "+" if match.group(0).strip().startswith("+") else ""
    visible = digits[-4:]
    masked_len = len(digits) - 4
    return f"{prefix}{'X' * masked_len}{visible}"


def mask_phone_numbers(text: str) -> str:
    """Replaces phone-number-shaped digit runs with the last 4 digits
    visible and the rest masked (e.g. "+15551234567" -> "+XXXXXXXX4567").
    Used for the DLR-specific report fields/sections, which otherwise
    show the recipient number raw for debugging purposes. Deliberately
    conservative: only touches runs that already look like a phone
    number (7+ digits), never a message ID, timestamp, or short code --
    those still go through fingerprint.py's own normalization, which is
    for STABLE FINGERPRINTING, not display masking, and is a separate
    concern from this one."""
    if not text:
        return text
    return _PHONE_RE.sub(_mask_one, text)
