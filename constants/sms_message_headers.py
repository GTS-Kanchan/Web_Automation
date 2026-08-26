"""constants/sms_message_headers.py — single source of truth for the SMS
Messages (message log) list's expected CSV/Excel export header names, in
the exact order the downloaded file must contain them.

Do NOT duplicate this list inline in test files. Import
EXPECTED_SMS_MESSAGE_HEADERS from here everywhere an SMS Messages export
file needs its headers validated:

    from constants.sms_message_headers import EXPECTED_SMS_MESSAGE_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_SMS_MESSAGE_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below — do not "clean up" or reorder this list without
confirming the change against the real SMS Messages export first.
"""

EXPECTED_SMS_MESSAGE_HEADERS = [
    "Mobile Number",
    "Country Code",
    "Sender ID",
    "DLT Template ID",
    "Entity ID",
    "Status",
    "Correlation ID",
    "Message Id",
    "SMS Count",
    "Source",
    "Sub-Source",
    "Type",
    "Product",
    "Received At",
    "Submitted At",
    "DLR Received At",
    "Message Content",
    "Status Description",
]
