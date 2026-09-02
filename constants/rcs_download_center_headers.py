"""constants/rcs_download_center_headers.py — single source of truth for
the RCS Download Center's async report export header names, in the exact
order the downloaded file must contain them.

Confirmed directly from a real completed-job download on this instance,
supplied by the user (2026-09-02). The file's *shape* (bare .csv/.xlsx/
.xls, or a .zip wrapping one of those, the way SMS's Download Center
export is confirmed to be) was not independently re-confirmed alongside
this header list -- utils/file_validator.py's read_file_headers() (used
by RcsDownloadCenterPage.get_csv_headers()) dispatches on file extension
automatically, so this constant works regardless of which shape a given
export happens to be.

Do NOT duplicate this list inline in test files. Import
EXPECTED_RCS_DOWNLOAD_CENTER_HEADERS from here everywhere an RCS Download
Center export file needs its headers validated:

    from constants.rcs_download_center_headers import EXPECTED_RCS_DOWNLOAD_CENTER_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_RCS_DOWNLOAD_CENTER_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below -- do not "clean up" or reorder this list without
confirming the change against a real RCS Download Center export first.
Note "Corelation Id" (not "Correlation Id") is the real, verbatim
spelling on this instance -- preserved exactly, not a typo to fix.
"""

EXPECTED_RCS_DOWNLOAD_CENTER_HEADERS = [
    "Phone Number",
    "Campaign Name",
    "Template Name",
    "Message Type",
    "Source",
    "Sub Source",
    "Status",
    "Submitted At",
    "Delivered At",
    "Read At",
    "Failed At",
    "Failure Reason",
    "Received At",
    "Total Clicks",
    "All Button Types",
    "All Button Values",
    "All Clicked Urls",
    "All Clicked At",
    "Created At",
    "Corelation Id",
]
