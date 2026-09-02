"""constants/rcs_agent_analytics_headers.py — single source of truth for
the RCS Agent Analytics report's expected CSV/Excel export header names,
in the exact order the downloaded file must contain them.

Confirmed directly from a real "Export" download on this instance,
supplied by the user (2026-09-02) -- distinct from
rcs_agent_list_headers.py's Agent LIST screen (agent catalog fields like
Display Name/Use Case/Verification Status, not usage metrics).

Do NOT duplicate this list inline in test files. Import
EXPECTED_RCS_AGENT_ANALYTICS_HEADERS from here everywhere an RCS Agent
Analytics export file needs its headers validated:

    from constants.rcs_agent_analytics_headers import EXPECTED_RCS_AGENT_ANALYTICS_HEADERS
    from utils.file_validator import validate_file_headers

    validate_file_headers(downloaded_file_path, EXPECTED_RCS_AGENT_ANALYTICS_HEADERS)

Header spelling, capitalization, spacing, and order are all part of the
specification below -- do not "clean up" or reorder this list without
confirming the change against a real RCS Agent Analytics export first.
Note "Quick reply total"/"Quick reply unique" use sentence case (not
Title Case like the surrounding columns) -- preserved exactly, not a
typo to fix.
"""

EXPECTED_RCS_AGENT_ANALYTICS_HEADERS = [
    "Duration",
    "Product",
    "Agent",
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
