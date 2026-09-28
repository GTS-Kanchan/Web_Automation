"""
utils/ui_dlr_helpers.py

Shared UI-correlation logic for DLR tests that have to read a message_id
off a browser page rather than an API response (tests/sms/api/
test_sms_webengage_dlr.py, tests/sms/api/test_sms_campaign_dlr_bulk.py).

Factored out of a first version of test_sms_webengage_dlr.py, which
defined _parse_timestamp_best_effort()/_find_latest_row_index() locally
-- moved here once a second test needed the exact same "pick the row
most likely to be the one this test just created" logic, so both tests
share one implementation instead of two copies that could drift apart.

Disambiguating "the latest/correct matching row" is a recurring problem
across every UI-based DLR test in this suite: a Messages-page search by
mobile number can return more than one row for that number (retests,
earlier runs, other campaigns), and neither test-case spec that needed
this ever supplied a confirmed sample of the 'Submitted At'/'Received
At' column's on-screen text format. So this stays best-effort: it tries
several plausible timestamp formats and falls back to row 0 (visibly
flagged via record_property, never a silent guess) if none of them
parse. See find_latest_matching_row()'s own docstring.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

# Candidate formats for the Messages table's 'Submitted At'/'Received At'
# cell text. UNCONFIRMED -- no real sample was ever given for this
# column's exact rendering. Extend this list (or replace it with the
# real confirmed format) once a live run shows what the column actually
# renders.
_CANDIDATE_TIMESTAMP_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%d-%m-%Y %H:%M:%S",
    "%d-%m-%Y %H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%b %d, %Y %I:%M %p",
    "%d %b %Y, %I:%M %p",
    "%Y-%m-%dT%H:%M:%S",
]


def parse_timestamp_best_effort(text: str) -> Optional[datetime]:
    text = (text or "").strip()
    if not text:
        return None
    for fmt in _CANDIDATE_TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def find_latest_matching_row(message_page, record_property, label: str = "") -> int:
    """Returns the index of the row on the (already searched/filtered)
    SMS Messages page most likely to be the latest matching message.

    Tries the 'Submitted At'/'Received At' column (whichever is present)
    and picks the row with the max parseable timestamp. If neither
    column exists, or none of its values parse with a known format
    (see module docstring -- never confirmed against the real app),
    this falls back to row 0 and records that fallback via
    record_property (visible in the HTML report) as a flagged
    assumption rather than a silent guess. `label` (e.g. the recipient
    number being searched) is included in the recorded property name so
    multiple calls in the same test (one per recipient) don't overwrite
    each other's diagnostic entry."""
    prefix = f"latest_row_selection[{label}]" if label else "latest_row_selection"

    headers = message_page.get_table_headers()
    col_idx = None
    for i, h in enumerate(headers):
        if h.strip().lower() in ("submitted at", "received at"):
            col_idx = i
            break

    row_count = message_page.get_row_count()
    if col_idx is None or row_count <= 1:
        if col_idx is None:
            record_property(
                prefix,
                "No 'Submitted At'/'Received At' column found -- defaulted to row 0.",
            )
        return 0

    best_index = 0
    best_ts = None
    any_parsed = False
    for i in range(row_count):
        cell_text = message_page.get_cell_text(i, col_idx)
        ts = parse_timestamp_best_effort(cell_text)
        if ts is not None:
            any_parsed = True
            if best_ts is None or ts > best_ts:
                best_ts = ts
                best_index = i

    if not any_parsed:
        record_property(
            prefix,
            f"Could not parse any row's '{headers[col_idx]}' value with a "
            f"known format -- defaulted to row 0. Sample value: "
            f"{message_page.get_cell_text(0, col_idx)!r}",
        )
        return 0

    record_property(
        prefix,
        f"Selected row {best_index} by max parsed '{headers[col_idx]}' "
        f"value ({best_ts}).",
    )
    return best_index
