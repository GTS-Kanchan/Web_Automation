"""constants/sms_latency_report_headers.py — single source of truth for
the SMS Latency Report's expected CSV/Excel export header names, in the
exact order the downloaded file must contain them.

Do NOT duplicate this list inline in test files. Import
EXPECTED_SMS_LATENCY_REPORT_HEADERS from here everywhere an SMS Latency
Report export file needs its headers validated:

    from constants.sms_latency_report_headers import EXPECTED_SMS_LATENCY_REPORT_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_SMS_LATENCY_REPORT_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below — do not "clean up" or reorder this list without
confirming the change against the real Latency Report export first.
"""

EXPECTED_SMS_LATENCY_REPORT_HEADERS = [
    "Duration",
    "Product",
    "Delivered 0-5 sec",
    "Delivered 5-10 sec",
    "Delivered 10-15 sec",
    "Delivered 15-30 sec",
    "Delivered After 30 sec",
    "DLR Awaited Count",
    "DLR Awaited Units",
    "Rejected Count",
    "Rejected Units",
    "Failed Count",
    "Failed Units",
]
