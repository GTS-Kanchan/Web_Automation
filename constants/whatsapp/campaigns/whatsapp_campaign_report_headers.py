"""constants/whatsapp_campaign_report_headers.py — single source of truth for the WhatsApp Campaign Reports
list's expected CSV/Excel export header names, in the exact order the
downloaded file must contain them.

Confirmed directly from a real downloaded/parsed per-campaign report export (campaign_export_20260930_104719.csv) on 2026-09-30. Matches the UI list cleanly (minus the UI-only "Action" column), same names both sides.

Do NOT duplicate this list inline in test files. Import
EXPECTED_WHATSAPP_CAMPAIGN_REPORT_HEADERS from here everywhere a WhatsApp Campaign Reports export
file needs its headers validated:

    from constants.whatsapp.campaigns.whatsapp_campaign_report_headers import EXPECTED_WHATSAPP_CAMPAIGN_REPORT_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_WHATSAPP_CAMPAIGN_REPORT_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below -- do not "clean up" or reorder this list without
confirming the change against a real WhatsApp Campaign Reports export first.
"""

EXPECTED_WHATSAPP_CAMPAIGN_REPORT_HEADERS = [
    "Contact",
    "Country Code",
    "Status",
    "Is MM Lite Used",
    "Created At",
    "Sent At",
    "Delivered At",
    "Failed At",
    "Read At",
]
