"""constants/whatsapp_sender_id_headers.py — single source of truth for the WhatsApp Number (Sender ID)
list's expected CSV/Excel export header names, in the exact order the
downloaded file must contain them.

Confirmed directly from two real downloaded/parsed WhatsApp Number exports (Whatsapp_SenderId_Summary.csv / Whatsapp_SenderId_Summary_1.csv, identical headers) on 2026-09-30. Real UI-vs-export naming differences: export "Name" vs UI "App Name", export "Number" vs UI "WABA Number", export "MM Lite API" (singular) vs UI "MM Lite APIs" (plural). Export also carries "Department"/"User" (deselected by default in the UI, so absent there) and "Updated At" (no corresponding confirmed UI column).

Do NOT duplicate this list inline in test files. Import
EXPECTED_WHATSAPP_SENDER_ID_HEADERS from here everywhere a WhatsApp Number (Sender ID) export
file needs its headers validated:

    from constants.whatsapp.sender_id.whatsapp_sender_id_headers import EXPECTED_WHATSAPP_SENDER_ID_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_WHATSAPP_SENDER_ID_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below -- do not "clean up" or reorder this list without
confirming the change against a real WhatsApp Number (Sender ID) export first.
"""

EXPECTED_WHATSAPP_SENDER_ID_HEADERS = [
    "ID",
    "Name",
    "Number",
    "Department",
    "User",
    "Status",
    "Quality",
    "Message Limit",
    "MM Lite API",
    "Created At",
    "Updated At",
]
