"""constants/sms_campaign_ui_headers.py — single source of truth for the SMS Campaigns
list page's expected ON-SCREEN (UI) table column header labels, as given
directly by the project owner (explicit statement of real, current app
behavior -- these are the page's DEFAULT columns, not the CSV/Excel
export headers, which are a separate, already-existing constants list
where one exists for this page).

Do NOT duplicate this list inline in test files. Import
EXPECTED_SMS_CAMPAIGN_UI_HEADERS from here everywhere the SMS Campaigns page's
visible table header labels need verifying:

    from constants.sms_campaign_ui_headers import EXPECTED_SMS_CAMPAIGN_UI_HEADERS

Header spelling and capitalization are part of the specification below
-- do not "clean up" this list without confirming the change against the
real, live page first.

KNOWN APP GAP (confirmed, not a test bug): a real --headed run against the
live SMS Campaigns list page rendered only 8 of these 9 headers --
"Total Units" was absent. The project owner explicitly confirmed
"Total Units" IS supposed to be a default column here, so this list is
kept as-is (the correct expected spec) and
tests/sms/campaigns/test_sms_campaign_flow.py::test_ui_default_table_headers_full
is expected to keep failing on this one column until the app renders it.
Do not remove "Total Units" from this list to make that test pass.
"""

EXPECTED_SMS_CAMPAIGN_UI_HEADERS = [
    "Action",
    "Campaign Name",
    "Source",
    "Sender id",
    "Template Name",
    "Status",
    "Total Units",
    "Created at",
    "Scheduled at",
]
