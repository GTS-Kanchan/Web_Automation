"""constants/sms_sender_report_ui_headers.py — single source of truth for the SMS Sender Report
list page's expected ON-SCREEN (UI) table column header labels, as given
directly by the project owner (explicit statement of real, current app
behavior -- these are the page's DEFAULT columns, not the CSV/Excel
export headers, which are a separate, already-existing constants list
where one exists for this page).

Do NOT duplicate this list inline in test files. Import
EXPECTED_SMS_SENDER_REPORT_UI_HEADERS from here everywhere the SMS Sender Report page's
visible table header labels need verifying:

    from constants.sms_sender_report_ui_headers import EXPECTED_SMS_SENDER_REPORT_UI_HEADERS

Header spelling and capitalization are part of the specification below
-- do not "clean up" this list without confirming the change against the
real, live page first.
"""

EXPECTED_SMS_SENDER_REPORT_UI_HEADERS = [
    "duration",
    "Sender",
    "Product",
    "Total Count",
    "Submitted Count",
    "Delivered Count",
    "Failed Count",
    "Rejected Count",
    "DLR Awaited Count",
    "Total Units",
    "Submitted Units",
    "Delivered Units",
    "Failed Units",
    "Rejected Units",
    "DLR Awaited Units",
    "Total Charges",
    "Delivery Charges",
    "Surcharge",
    "Delivery Surcharge",
    "Delivery %",
]
