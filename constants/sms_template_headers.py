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

UPDATED (2026-09-08): the export gained a "Rejection Reason" column
between Status and Product — confirmed against the latest real export
header row: DLT Template Id, Template Name, Sender Id, Content, Status,
Rejection Reason, Product, Short URL, Created At. Same addition, same
position relative to Status, as the SMS Sender ID export's
"Rejection Reason" column (see constants/sms_sender_id_headers.py) —
consistent with both being DLT-approval-gated resources.
"""

EXPECTED_SMS_TEMPLATE_HEADERS = [
    "DLT Template Id",
    "Template Name",
    "Sender Id",
    "Content",
    "Status",
    "Rejection Reason",
    "Product",
    "Short URL",
    "Created At",
]
