"""constants/sms_campaign_report_headers.py — single source of truth for
the SMS Campaign Report's expected CSV/Excel export header names, in the
exact order the downloaded file must contain them.

Do NOT duplicate this list inline in test files. Import
EXPECTED_SMS_CAMPAIGN_REPORT_HEADERS from here everywhere an SMS Campaign
Report export file needs its headers validated:

    from constants.sms_campaign_report_headers import EXPECTED_SMS_CAMPAIGN_REPORT_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_SMS_CAMPAIGN_REPORT_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below — do not "clean up" or reorder this list without
confirming the change against the real Campaign Report export first.
"""

EXPECTED_SMS_CAMPAIGN_REPORT_HEADERS = [
    "Duration",
    "Campaign Name",
    "Sender",
    "Product",
    "Total Count",
    "Submitted Count",
    "Delivered Count",
    "Failed Count",
    "Rejected Count",
    "DLR Awaited Count",
    "Total Units",
    "Submitted Units",
    "Delivered Units",
    "Failed Units",
    "Rejected Units",
    "DLR Awaited Units",
    "Total Charges",
    "Delivery Charges",
    "Surcharge",
    "Delivery Surcharge",
    "Delivery %",
]
