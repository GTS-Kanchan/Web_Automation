"""constants/sms_incoming_messages_headers.py — single source of truth for
the SMS Incoming Messages export's expected CSV header names, in the exact
order the downloaded file must contain them.

Do NOT duplicate this list inline in test files. Import
EXPECTED_SMS_INCOMING_MESSAGES_HEADERS from here everywhere an SMS Incoming
Messages export file needs its headers validated:

    from constants.sms_incoming_messages_headers import EXPECTED_SMS_INCOMING_MESSAGES_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_SMS_INCOMING_MESSAGES_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below — do not "clean up" or reorder this list without
confirming the change against the real Incoming Messages export first.

Note: the exported file's columns are a superset of the 6 columns shown in
the on-screen table (Action, Campaign Name, Sender ID, Country Code, User
Number, Received At) — the export additionally includes Message ID and
Status, which are not rendered as visible table columns.
"""

EXPECTED_SMS_INCOMING_MESSAGES_HEADERS = [
    "Campaign Name",
    "Sender ID",
    "Country Code",
    "User Number",
    "Message ID",
    "Status",
    "Received At",
]
