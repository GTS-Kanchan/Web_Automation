"""constants/whatsapp_message_headers.py — single source of truth for the WhatsApp Messages
list's expected CSV/Excel export header names, in the exact order the
downloaded file must contain them.

Confirmed directly from a real downloaded/parsed WhatsApp Messages Report export (WhatsApp_Messages_Report_-_2026-09-30_104704.csv) on 2026-09-30. Note the export's "Recipient Number" is the same real field as the UI's "To Number" -- different label, same column.

Do NOT duplicate this list inline in test files. Import
EXPECTED_WHATSAPP_MESSAGE_HEADERS from here everywhere a WhatsApp Messages export
file needs its headers validated:

    from constants.whatsapp.messaging.whatsapp_message_headers import EXPECTED_WHATSAPP_MESSAGE_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_WHATSAPP_MESSAGE_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below -- do not "clean up" or reorder this list without
confirming the change against a real WhatsApp Messages export first.
"""

EXPECTED_WHATSAPP_MESSAGE_HEADERS = [
    "ID",
    "Message ID",
    "Correlation ID",
    "Campaign Name",
    "Recipient Number",
    "Country Code",
    "Status",
    "Template Name",
    "Template Category",
    "Template Type",
    "WABA Number",
    "MM Lite Status",
    "Source",
    "Sub-Source",
    "Created At",
    "Submitted At",
    "Delivered At",
    "Read At",
    "Failed At",
    "Error Description",
]
