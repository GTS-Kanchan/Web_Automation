"""constants/rcs_incoming_messages_headers.py — single source of truth for
the RCS Incoming Messages page's expected CSV/Excel export header names,
in the exact order the downloaded file must contain them.

Confirmed directly from a real "Export CSV" download on this instance,
supplied by the user (2026-09-02).

Do NOT duplicate this list inline in test files. Import
EXPECTED_RCS_INCOMING_MESSAGES_HEADERS from here everywhere an RCS
Incoming Messages export file needs its headers validated:

    from constants.rcs_incoming_messages_headers import EXPECTED_RCS_INCOMING_MESSAGES_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_RCS_INCOMING_MESSAGES_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below -- do not "clean up" or reorder this list without
confirming the change against a real RCS Incoming Messages export first.
Note "Corelation ID" here is capitalized differently from RCS Messages'
and RCS Download Center's "Corelation Id" -- both verbatim, confirmed
separately, not normalized to match each other.
"""

EXPECTED_RCS_INCOMING_MESSAGES_HEADERS = [
    "Campaign Name",
    "Agent",
    "Country Code",
    "User Number",
    "Type",
    "Message",
    "Corelation ID",
    "Received At",
    "Created At",
]
