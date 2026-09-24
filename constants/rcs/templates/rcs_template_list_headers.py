"""constants/rcs_template_list_headers.py — single source of truth for the
RCS Template LIST screen's (`/rcs/template`) expected CSV/Excel export
header names, in the exact order the downloaded file must contain them.

Confirmed directly from a real "Export" download on this instance,
supplied by the user (2026-09-02) -- distinct from
rcs_template_analytics_page.py's Template Analytics Report, whose
columns are usage/metric counts (duration, sent/delivered/read/failed
counts, interactions, ...), not this catalog-style listing. Same
screen-name-collision caveat already noted for SMS's
sms_template_report_headers.py vs sms_template_headers.py.

Do NOT duplicate this list inline in test files. Import
EXPECTED_RCS_TEMPLATE_LIST_HEADERS from here everywhere an RCS Template
list export file needs its headers validated:

    from constants.rcs_template_list_headers import EXPECTED_RCS_TEMPLATE_LIST_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_RCS_TEMPLATE_LIST_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below -- do not "clean up" or reorder this list without
confirming the change against a real RCS Template list export first.

Note: unlike the header row, the Export button's exact locator on this
screen was NOT independently confirmed against the live DOM --
RcsTemplateCreatePage.click_export_csv()'s BTN_EXPORT is a best-effort
guess mirrored from RCSCampaignPage's confirmed pattern. A test using
this constant should treat a None return from click_export_csv() as
"button not found -- skip", not a hard failure.
"""

EXPECTED_RCS_TEMPLATE_LIST_HEADERS = [
    "ID",
    "Name",
    "Message Type",
    "Agent",
    "Status",
    "Product",
    "Is Public",
    "Created At",
    "Department",
    "User",
    "Updated At",
]
