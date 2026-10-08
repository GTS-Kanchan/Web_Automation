"""
reporting/fingerprint.py -- stable failure fingerprints (requirement #10).

A fingerprint identifies "the same failure happening again" across runs,
so it deliberately excludes anything that changes run-to-run even when
the underlying defect hasn't: timestamps, UUIDs, message IDs, phone
numbers, worker IDs, temp file paths, and any other long numeric run.
"""
import hashlib
import re

# Order matters only in that each pattern below is applied independently
# (non-overlapping concerns), not chained in a way where order changes
# the result.
_NORMALIZERS = [
    # UUID (message IDs, request IDs, ...)
    re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"),
    # ISO-ish timestamps: 2026-10-07T18:56:00(.123)(Z)
    re.compile(r"\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?\b"),
    # Compact timestamps used in filenames: 20261007_185600
    re.compile(r"\b\d{8}_\d{6}\b"),
    # xdist worker ids: gw0, gw12, ...
    re.compile(r"\bgw\d+\b"),
    # Temp file paths
    re.compile(r"(/tmp/|\\Temp\\)[^\s'\"]+"),
    # Phone numbers / long numeric IDs (message IDs, epoch millis, ...) --
    # intentionally broad (8+ consecutive digits) since this suite's own
    # SMS_PASTE_CONTACTS/epoch-ms filename convention (utils/parallel.py)
    # both fall in this range.
    re.compile(r"\b\d{8,}\b"),
]


def normalize_message(message) -> str:
    """Collapse whitespace and strip every dynamic value listed above.
    Never raises -- a non-string input is coerced via str()."""
    if not message:
        return ""
    text = str(message)
    for pattern in _NORMALIZERS:
        text = pattern.sub("<N>", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:500]


def _channel_and_feature_hint(nodeid: str):
    """Best-effort CHANNEL-FEATURE hint for a readable fingerprint prefix
    -- display only, never relied on for uniqueness (the hash suffix is
    what actually guarantees that)."""
    path = nodeid.split("::")[0].replace("\\", "/")
    parts = [p for p in path.split("/") if p]
    channel = parts[1].upper() if len(parts) > 1 and parts[0] == "tests" else "UNK"
    feature = parts[2].replace("_", "-").title().replace("-", "") if len(parts) > 2 else "General"
    return channel, feature


def fingerprint(nodeid: str, exc_type: str, message: str) -> str:
    """test nodeid + exception type + NORMALIZED error message -> a
    stable id. Never includes timestamps/random IDs/dynamic message IDs
    directly -- only their already-normalized ('<N>') replacement."""
    channel, feature = _channel_and_feature_hint(nodeid or "")
    normalized = normalize_message(message)
    raw = f"{nodeid}|{exc_type or ''}|{normalized}"
    digest = hashlib.sha1(raw.encode("utf-8", "replace")).hexdigest()[:8]
    hint = re.sub(r"(Error|Exception)$", "", exc_type or "") or "Fail"
    hint = re.sub(r"[^A-Za-z0-9]", "", hint) or "Fail"
    return f"{channel}-{feature}-{hint}-{digest}"
