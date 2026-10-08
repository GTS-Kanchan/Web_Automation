"""constants/sms_download_headers.py — single source of truth for the SMS
Download Center's expected CSV/Excel export header names, in the exact
order the downloaded file must contain them.

Do NOT duplicate this list inline in test files. Import
EXPECTED_SMS_DOWNLOAD_HEADERS from here everywhere an SMS Download Center
file needs its headers validated:

    from constants.sms_download_headers import EXPECTED_SMS_DOWNLOAD_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_SMS_DOWNLOAD_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below — do not "clean up" or reorder this list without
confirming the change against the real Download Center export first.

Phase 1 scope: SMS only. RCS/WhatsApp/Email header lists (e.g.
EXPECTED_RCS_HEADERS, EXPECTED_EMAIL_HEADERS) are out of scope for now and
belong in their own constants module alongside this one when implemented,
following the same single-source-of-truth pattern.
"""

EXPECTED_SMS_DOWNLOAD_HEADERS = [
    "Phone Number",
    "Message Id",
    "Correlation Id",
    "Campaign Name",
    "Dlt Template Id",
    "Units",
    "Sender Name",
    "Entity Id",
    "Is Unicode",
    "Product Type",
    "Source",
    "Sub Source",
    "Status",
    "Created At",
    "Submitted At",
    "Dlr Received At",
    "Status Description",
    "Total Clicks",
    "Clicked Url",
    "Clicked At",
]
