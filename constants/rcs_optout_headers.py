"""constants/rcs_optout_headers.py — single source of truth for the RCS
Opt-out / Blocked Numbers list's (`/rcs/optout`) expected CSV/Excel export
header names, in the exact order the downloaded file must contain them.

Confirmed directly from a real "Export" download on this instance,
supplied by the user (2026-09-02). Note the RCS version's columns
(ID, Phone Number, Reason, Opted Out At) differ from SMS's sibling export
(constants/sms_blocked_numbers_headers.py: ID, Phone Number, Department,
User, Created At) -- confirmed separately, not assumed to match.

Do NOT duplicate this list inline in test files. Import
EXPECTED_RCS_OPTOUT_HEADERS from here everywhere an RCS Opt-out export
file needs its headers validated:

    from constants.rcs_optout_headers import EXPECTED_RCS_OPTOUT_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_RCS_OPTOUT_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below -- do not "clean up" or reorder this list without
confirming the change against a real RCS Opt-out export first.
"""

EXPECTED_RCS_OPTOUT_HEADERS = [
    "ID",
    "Phone Number",
    "Reason",
    "Opted Out At",
]
