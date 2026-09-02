"""constants/rcs_error_code_analytics_headers.py — single source of truth for the
RCS Error Code report's expected CSV/Excel export header names, in the exact order the
downloaded file must contain them.

Confirmed directly from a real "Export" download on this instance,
supplied by the user (2026-09-02) -- a much shorter column set than the other Analytics exports -- error/failure
breakdown only, not a Sent/Delivered/Read/Failed metrics table.

Do NOT duplicate this list inline in test files. Import
EXPECTED_RCS_ERROR_CODE_ANALYTICS_HEADERS from here everywhere an
RCS Error Code report export file needs its headers validated:

    from constants.rcs_error_code_analytics_headers import EXPECTED_RCS_ERROR_CODE_ANALYTICS_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_RCS_ERROR_CODE_ANALYTICS_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below -- do not "clean up" or reorder this list without
confirming the change against a real RCS Error Code report export first.
"""

EXPECTED_RCS_ERROR_CODE_ANALYTICS_HEADERS = [
    "Duration",
    "Product",
    "ERROR CODE",
    "ERROR DESCRIPTION",
    "Total Count",
    "Percentage Share",
]
