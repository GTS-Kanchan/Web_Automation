"""constants/whatsapp_campaign_headers.py — single source of truth for the WhatsApp Campaign List
list's expected CSV/Excel export header names, in the exact order the
downloaded file must contain them.

Confirmed directly from a real downloaded/parsed Campaign List export (Whatsapp_Campaign_Summary_1.csv) on 2026-09-30. Note two real UI-vs-export naming differences: export "Campaign Name" vs UI "Name", and export "Template Name" vs UI "Template" -- same underlying fields, different labels each side.

Do NOT duplicate this list inline in test files. Import
EXPECTED_WHATSAPP_CAMPAIGN_HEADERS from here everywhere a WhatsApp Campaign List export
file needs its headers validated:

    from constants.whatsapp.campaigns.whatsapp_campaign_headers import EXPECTED_WHATSAPP_CAMPAIGN_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_WHATSAPP_CAMPAIGN_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below -- do not "clean up" or reorder this list without
confirming the change against a real WhatsApp Campaign List export first.
"""

EXPECTED_WHATSAPP_CAMPAIGN_HEADERS = [
    "ID",
    "Campaign Name",
    "Type",
    "Template Name",
    "WABA Number",
    "Status",
    "Total Messages",
    "Created At",
    "Scheduled At",
]
