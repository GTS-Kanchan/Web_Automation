"""constants/rcs_campaign_headers.py — single source of truth for the RCS
Campaign list page's expected CSV/Excel export header names, in the exact
order the downloaded file must contain them.

Confirmed directly from a real "Export CSV" download on this instance
(the export is actually an .xlsx file named "Table Export.xlsx" despite
the button being labeled "Export CSV" -- utils/file_validator.py's
read_file_headers() dispatches on file extension automatically, so this
constant works regardless of which format a given export happens to be).

Do NOT duplicate this list inline in test files. Import
EXPECTED_RCS_CAMPAIGN_HEADERS from here everywhere an RCS Campaign list
export file needs its headers validated:

    from constants.rcs_campaign_headers import EXPECTED_RCS_CAMPAIGN_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_RCS_CAMPAIGN_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below -- do not "clean up" or reorder this list without
confirming the change against a real RCS Campaign export first.
"""

EXPECTED_RCS_CAMPAIGN_HEADERS = [
    "ID",
    "Campaign Name",
    "Type",
    "Department",
    "User",
    "Template",
    "Agent",
    "Status",
    "Total Messages",
    "Sent Count",
    "Delivered Count",
    "Read Count",
    "Interactions",
    "Failed Count",
    "Created At",
    "Scheduled At",
    "Send Type",
    "Started At",
    "Completed At",
    "Message Content",
    "Updated At",
]
