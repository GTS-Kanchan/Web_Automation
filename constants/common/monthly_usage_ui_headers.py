"""constants/monthly_usage_ui_headers.py — Column headers, filter options,
and metadata for the Monthly Usage billing page (/billing/monthly/usage-details).
"""

EXPECTED_MONTHLY_USAGE_UI_HEADERS = [
    "Month",
    "Channel",
    "Product",
    "Units",
    "Total Sale Price",
    "Delivered Units",
    "Total Surcharge",
    "Total Rate Refunded",
    "Total Rate Applied",
    "Total Discount",
    "Gross Sale Price",
    "Payment Mode",
    "Last Updated At",
]

MONTH_FILTER_OPTIONS = [
    "All",
    "Aug 2026",
    "Jul 2026",
    "May 2026",
    "Apr 2026",
    "Mar 2026",
    "Feb 2026",
    "Jan 2026",
    "Dec 2025",
    "Nov 2025",
]

CHANNEL_FILTER_OPTIONS = [
    "All",
    "Email",
    "RCS",
    "SMS",
    "Voice",
    "WhatsApp",
]

# Map channel names to Livewire option values
CHANNEL_VALUE_MAP = {
    "All": "",
    "Email": "9",
    "RCS": "11",
    "SMS": "1",
    "Voice": "6",
    "WhatsApp": "2",
}

# Map month display names to Livewire option values
MONTH_VALUE_MAP = {
    "All": "",
    "Aug 2026": "2026-08",
    "Jul 2026": "2026-07",
    "May 2026": "2026-05",
    "Apr 2026": "2026-04",
    "Mar 2026": "2026-03",
    "Feb 2026": "2026-02",
    "Jan 2026": "2026-01",
    "Dec 2025": "2025-12",
    "Nov 2025": "2025-11",
}

# Known product filter names and their Livewire option values
PRODUCT_VALUE_MAP = {
    "All": "",
    "Email OTP (Email)": "31",
    "Email Promotional (Email)": "33",
    "Email Transactional  (Email)": "32",
    "RCS Media with Suggestion (RCS)": "61",
    "RCS Multi Use (RCS)": "45",
    "RCS MultiUse (RCS)": "47",
    "RCS Promotional (RCS)": "41",
    "RCS Rich Card Carousel (RCS)": "51",
    "RCS Rich Card StandAlone (RCS)": "53",
    "RCS Rich Card Without Med (RCS)": "59",
    "RCS Rich Message (RCS)": "57",
    "RCS Text Message (RCS)": "49",
    "RCS Text Message with Doc (RCS)": "55",
    "RCS Transactional (RCS)": "40",
    "SMS OTP (SMS)": "10",
    "SMS Promotional (SMS)": "9",
    "SMS Transactional (SMS)": "8",
    "Transactional (Voice)": "26",
    "WhatsApp Authentication (WhatsApp)": "24",
    "Whatsapp Marketing (WhatsApp)": "23",
    "WhatsApp MMLite (WhatsApp)": "43",
    "WhatsApp Utility (WhatsApp)": "25",
}
