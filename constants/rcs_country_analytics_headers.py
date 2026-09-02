"""constants/rcs_country_analytics_headers.py — single source of truth for the
RCS Country Analytics report's expected CSV/Excel export header names, in the exact order the
downloaded file must contain them.

Confirmed directly from a real "Export" download on this instance,
supplied by the user (2026-09-02) -- grouped by Country Code rather than by agent/template/status/message-type.

Do NOT duplicate this list inline in test files. Import
EXPECTED_RCS_COUNTRY_ANALYTICS_HEADERS from here everywhere an
RCS Country Analytics report export file needs its headers validated:

    from constants.rcs_country_analytics_headers import EXPECTED_RCS_COUNTRY_ANALYTICS_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_RCS_COUNTRY_ANALYTICS_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below -- do not "clean up" or reorder this list without
confirming the change against a real RCS Country Analytics report export first.
"""

EXPECTED_RCS_COUNTRY_ANALYTICS_HEADERS = [
    "Duration",
    "Product",
    "Agent",
    "Country Code",
    "Total Count",
    "Sent Count",
    "Delivered Count",
    "Read Count",
    "Failed Count",
    "Rejected Count",
    "DLR Awaited Count",
    "Interactions",
    "Quick reply total",
    "Quick reply unique",
    "CTA Total Clicks",
    "CTA Unique Clicks",
    "Total Charges",
]
