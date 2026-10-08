"""constants/sms_error_code_report_headers.py — single source of truth
for the SMS Error Code Report's expected CSV/Excel export header names, in
the exact order the downloaded file must contain them.

Do NOT duplicate this list inline in test files. Import
EXPECTED_SMS_ERROR_CODE_REPORT_HEADERS from here everywhere an SMS Error
Code Report export file needs its headers validated:

    from constants.sms_error_code_report_headers import EXPECTED_SMS_ERROR_CODE_REPORT_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_SMS_ERROR_CODE_REPORT_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below — do not "clean up" or reorder this list without
confirming the change against the real Error Code Report export first.
Note ERROR CODE / ERROR DESCRIPTION are all-caps in the real export, unlike
every other header in this module — preserved verbatim as given.
"""

EXPECTED_SMS_ERROR_CODE_REPORT_HEADERS = [
    "Duration",
    "Product",
    "ERROR CODE",
    "ERROR DESCRIPTION",
    "Total Count",
    "Total Units",
    "Percentage Share",
]
