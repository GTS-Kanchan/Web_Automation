"""constants/rcs_message_headers.py — single source of truth for the RCS
Messages (outgoing message log) page's expected CSV/Excel export header
names, in the exact order the downloaded file must contain them.

Confirmed directly from a real "Export" download on this instance,
supplied by the user (2026-09-02).

Do NOT duplicate this list inline in test files. Import
EXPECTED_RCS_MESSAGE_HEADERS from here everywhere an RCS Messages export
file needs its headers validated:

    from constants.rcs_message_headers import EXPECTED_RCS_MESSAGE_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_RCS_MESSAGE_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below -- do not "clean up" or reorder this list without
confirming the change against a real RCS Messages export first. Note
"Corelation Id" (not "Correlation Id") is the real, verbatim spelling on
this instance -- preserved exactly, not a typo to fix.
"""

EXPECTED_RCS_MESSAGE_HEADERS = [
    "ID",
    "Contact Number",
    "Department",
    "User",
    "Status",
    "Direction",
    "Message Type",
    "Source",
    "Sub-Source",
    "Message Content",
    "Submitted At",
    "Delivered At",
    "Read At",
    "Failed At",
    "Failure Reason",
    "Corelation Id",
    "Created At",
    "Assistant ID",
    "Agent Name",
    "Agent Status",
    "Agent Sender Name",
    "Campaign Name",
]
