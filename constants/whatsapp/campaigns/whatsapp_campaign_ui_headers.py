"""constants/whatsapp_campaign_ui_headers.py — single source of truth for the WhatsApp Campaign List
list page's expected ON-SCREEN (UI) table column header labels, as given
directly by the project owner (explicit statement of real, current app
behavior -- these are the page's DEFAULT columns, not the CSV/Excel
export headers, which are a separate, already-existing constants list
where one exists for this page).

Do NOT duplicate this list inline in test files. Import
EXPECTED_WHATSAPP_CAMPAIGN_UI_HEADERS from here everywhere the WhatsApp Campaign List page's
visible table header labels need verifying:

    from constants.whatsapp.campaigns.whatsapp_campaign_ui_headers import EXPECTED_WHATSAPP_CAMPAIGN_UI_HEADERS

Header spelling and capitalization are part of the specification below
-- do not "clean up" this list without confirming the change against the
real, live page first.
"""

EXPECTED_WHATSAPP_CAMPAIGN_UI_HEADERS = [
    "Action",
    "Name",
    "Type",
    "Template",
    "WABA Number",
    "Status",
    "Total Messages",
    "Scheduled At",
    "Created At",
]
