"""constants/sms_sender_id_headers.py — single source of truth for the SMS
Sender ID list's expected CSV/Excel export header names, in the exact order
the downloaded file must contain them.

Do NOT duplicate this list inline in test files. Import
EXPECTED_SMS_SENDER_ID_HEADERS from here everywhere an SMS Sender ID export
file needs its headers validated:

    from constants.sms_sender_id_headers import EXPECTED_SMS_SENDER_ID_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_SMS_SENDER_ID_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below — do not "clean up" or reorder this list without
confirming the change against the real Sender ID export first.
"""

EXPECTED_SMS_SENDER_ID_HEADERS = [
    "Sender Id",
    "Department",
    "User",
    "Status",
    "Type",
    "Entity Id",
    "Country code",
    "Created At",
    "Updated At",
]
