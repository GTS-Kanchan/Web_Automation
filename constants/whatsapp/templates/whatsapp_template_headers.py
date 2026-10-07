"""constants/whatsapp_template_headers.py — single source of truth for the WhatsApp Templates
list's expected CSV/Excel export header names, in the exact order the
downloaded file must contain them.

Confirmed directly from a real downloaded/parsed WhatsApp Template export (Whatsapp_Template_Summary_1.csv) on 2026-09-30. Matches the UI list closely (minus the UI-only "Action" column), same names both sides.

Do NOT duplicate this list inline in test files. Import
EXPECTED_WHATSAPP_TEMPLATE_HEADERS from here everywhere a WhatsApp Templates export
file needs its headers validated:

    from constants.whatsapp.templates.whatsapp_template_headers import EXPECTED_WHATSAPP_TEMPLATE_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_WHATSAPP_TEMPLATE_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below -- do not "clean up" or reorder this list without
confirming the change against a real WhatsApp Templates export first.
"""

EXPECTED_WHATSAPP_TEMPLATE_HEADERS = [
    "Name",
    "Category",
    "Type",
    "WABA Number",
    "Status",
    "Quality",
    "Created at",
]
