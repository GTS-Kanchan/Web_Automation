"""constants/sms_template_headers.py — single source of truth for the SMS
Template list's expected CSV/Excel export header names, in the exact order
the downloaded file must contain them.

Do NOT duplicate this list inline in test files. Import
EXPECTED_SMS_TEMPLATE_HEADERS from here everywhere an SMS Template export
file needs its headers validated:

    from constants.sms_template_headers import EXPECTED_SMS_TEMPLATE_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_SMS_TEMPLATE_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below — do not "clean up" or reorder this list without
confirming the change against the real Template export first.
"""

EXPECTED_SMS_TEMPLATE_HEADERS = [
    "DLT Template Id",
    "Template Name",
    "Sender Id",
    "Content",
    "Status",
    "Product",
    "Short URL",
    "Created At",
]
