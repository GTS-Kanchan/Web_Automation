"""constants/whatsapp_incoming_messages_headers.py — single source of truth for the WhatsApp Incoming Messages
list's expected CSV/Excel export header names, in the exact order the
downloaded file must contain them.

Confirmed directly from a real downloaded/parsed WhatsApp Incoming Messages export (WhatsApp_Incoming_Messages_-_30-09-2026_104913.csv) on 2026-09-30. Matches the UI list closely (minus the UI-only "Action" column). Export also carries an extra "Message" column with no corresponding confirmed UI column -- export-only, not a problem.

Do NOT duplicate this list inline in test files. Import
EXPECTED_WHATSAPP_INCOMING_MESSAGES_HEADERS from here everywhere a WhatsApp Incoming Messages export
file needs its headers validated:

    from constants.whatsapp.messaging.whatsapp_incoming_messages_headers import EXPECTED_WHATSAPP_INCOMING_MESSAGES_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_WHATSAPP_INCOMING_MESSAGES_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below -- do not "clean up" or reorder this list without
confirming the change against a real WhatsApp Incoming Messages export first.
"""

EXPECTED_WHATSAPP_INCOMING_MESSAGES_HEADERS = [
    "Campaign Name",
    "WABA Number",
    "Country Code",
    "User Number",
    "User Name",
    "Type",
    "Message",
    "Received At",
    "Created At",
]
