"""constants/sms_blocked_numbers_headers.py — single source of truth for
the SMS Blocked Numbers (opt-out) list's expected CSV/Excel export header
names, in the exact order the downloaded file must contain them.

Do NOT duplicate this list inline in test files. Import
EXPECTED_SMS_BLOCKED_NUMBERS_HEADERS from here everywhere an SMS Blocked
Numbers export file needs its headers validated:

    from constants.sms_blocked_numbers_headers import EXPECTED_SMS_BLOCKED_NUMBERS_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_SMS_BLOCKED_NUMBERS_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below — do not "clean up" or reorder this list without
confirming the change against the real Blocked Numbers export first.
"""

EXPECTED_SMS_BLOCKED_NUMBERS_HEADERS = [
    "ID",
    "Phone Number",
    "Department",
    "User",
    "Created At",
]
