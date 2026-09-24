"""constants/rcs_agent_list_headers.py — single source of truth for the
RCS Agent LIST screen's expected CSV/Excel export header names, in the
exact order the downloaded file must contain them.

Confirmed directly from a real "Export" download on this instance,
supplied by the user (2026-09-02) -- distinct from
rcs_agent_analytics_page.py's Agent Analytics Report (a different screen
with usage/metric columns: duration, total/sent/delivered/read/failed
counts, etc., not agent catalog fields). Same screen-name-collision
caveat already noted for rcs_template_list_headers.py vs the Template
Analytics Report.

Do NOT duplicate this list inline in test files. Import
EXPECTED_RCS_AGENT_LIST_HEADERS from here everywhere an RCS Agent list
export file needs its headers validated:

    from constants.rcs_agent_list_headers import EXPECTED_RCS_AGENT_LIST_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_RCS_AGENT_LIST_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below -- do not "clean up" or reorder this list without
confirming the change against a real RCS Agent list export first.
"""

EXPECTED_RCS_AGENT_LIST_HEADERS = [
    "ID",
    "Agent Name",
    "Display Name",
    "Use Case",
    "Status",
    "Verification Status",
    "Billing Category",
    "Primary Phone",
    "Primary Email",
    "Created At",
    "Updated At",
]
