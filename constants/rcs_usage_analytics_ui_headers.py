"""constants/rcs_usage_analytics_ui_headers.py — single source of truth for the RCS Usage Analytics
list page's expected ON-SCREEN (UI) table column header labels, as given
directly by the project owner (explicit statement of real, current app
behavior -- these are the page's DEFAULT columns, not the CSV/Excel
export headers, which are a separate, already-existing constants list
where one exists for this page).

Do NOT duplicate this list inline in test files. Import
EXPECTED_RCS_USAGE_ANALYTICS_UI_HEADERS from here everywhere the RCS Usage Analytics page's
visible table header labels need verifying:

    from constants.rcs_usage_analytics_ui_headers import EXPECTED_RCS_USAGE_ANALYTICS_UI_HEADERS

Header spelling and capitalization are part of the specification below
-- do not "clean up" this list without confirming the change against the
real, live page first.
"""

EXPECTED_RCS_USAGE_ANALYTICS_UI_HEADERS = [
    "duration",
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
