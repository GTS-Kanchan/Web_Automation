"""constants/common/flow_summary_report_ui_headers.py — single source of
truth for the Communication Flow Summary Report page's expected
ON-SCREEN (UI) table column header labels.

CONFIRMED from a live DOM dump of /flow/summary (table-head-0 .. -6).
Note this is one column MORE than the originally supplied TC_SUM_003
test-case spec (which lists only Flow Name, Date, Trigger Count, SMS
Count, Email Count, Voice Count) -- the live page also has a WhatsApp
Count column. Per this project's "never guess" rule, the extra confirmed
column is included here rather than trimmed to match the spec.

Do NOT duplicate this list inline in test files. Import
EXPECTED_FLOW_SUMMARY_REPORT_UI_HEADERS from here everywhere the Flow
Summary Report page's visible table header labels need verifying:

    from constants.common.flow_summary_report_ui_headers import (
        EXPECTED_FLOW_SUMMARY_REPORT_UI_HEADERS,
    )
"""

EXPECTED_FLOW_SUMMARY_REPORT_UI_HEADERS = [
    "Flow Name",
    "Date",
    "Trigger Count",
    "SMS Count",
    "Email Count",
    "Voice Count",
    "WhatsApp Count",
]
