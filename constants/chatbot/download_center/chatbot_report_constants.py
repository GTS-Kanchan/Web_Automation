"""
Constants for Chatbot -> Download Center -> Create Request Report page.
"""

# Expected Page Headings & Breadcrumbs
EXPECTED_PAGE_HEADING = "Request a Report"
EXPECTED_PAGE_SUBHEADING = "Generate a chatbot detailed report for download"
EXPECTED_BREADCRUMB_ITEMS = ["Home", "Download Center", "Create Request Report"]

# Field Placeholders & Limits
EXPECTED_REPORT_NAME_PLACEHOLDER = "e.g., Weekly Chatbot Report"
REPORT_NAME_MAX_LENGTH = 100

# Bot Types
EXPECTED_BOT_TYPES = [
    "All Types",
    "Web",
    "WhatsApp",
    "Telegram",
    "RCS",
    "Facebook",
]

BOT_TYPE_OPTIONS_MAP = {
    "All Types": "",
    "Web": "web",
    "WhatsApp": "whatsapp",
    "Telegram": "telegram",
    "RCS": "rcs",
    "Facebook": "facebook",
}

# Date Restrictions & Helper Texts
FROM_DATE_HELPER_TEXT = "Maximum 90 days ago"
TO_DATE_HELPER_TEXT = "Maximum yesterday"
MAX_HISTORICAL_DAYS = 90
