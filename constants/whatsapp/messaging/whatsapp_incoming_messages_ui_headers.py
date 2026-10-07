"""constants/whatsapp_incoming_messages_ui_headers.py — single source of truth for the WhatsApp Incoming Messages
list page's expected ON-SCREEN (UI) table column header labels, as given
directly by the project owner (explicit statement of real, current app
behavior -- these are the page's DEFAULT columns, not the CSV/Excel
export headers, which are a separate, already-existing constants list
where one exists for this page).

Do NOT duplicate this list inline in test files. Import
EXPECTED_WHATSAPP_INCOMING_MESSAGES_UI_HEADERS from here everywhere the WhatsApp Incoming Messages page's
visible table header labels need verifying:

    from constants.whatsapp.messaging.whatsapp_incoming_messages_ui_headers import EXPECTED_WHATSAPP_INCOMING_MESSAGES_UI_HEADERS

Header spelling and capitalization are part of the specification below
-- do not "clean up" this list without confirming the change against the
real, live page first.
"""

EXPECTED_WHATSAPP_INCOMING_MESSAGES_UI_HEADERS = [
    "Action",
    "Campaign Name",
    "WABA Number",
    "Country Code",
    "User Number",
    "User Name",
    "Type",
    "Received At",
    "Created At",
]
