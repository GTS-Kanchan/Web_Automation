"""constants/activity_ui_headers.py — Column headers, filter options, and metadata
for the Activities page (/activities).
"""

EXPECTED_ACTIVITY_UI_HEADERS = [
    "Action",
    "User",
    "Event",
    "Subject",
    "Created at",
]

ALL_ACTIVITY_COLUMNS = [
    "Action",
    "User",
    "Event",
    "Subject",
    "Created at",
]

# Selectable column keys in Columns dropdown
COLUMN_KEYS = [
    "action",
    "user",
    "event",
    "subject",
    "created-at",
]

KNOWN_EVENT_TYPES = [
    "All Events",
    "created",
    "deleted",
    "login",
    "logout",
    "otp_resent",
    "otp_verification_failed",
    "updated",
]

KNOWN_SUBJECTS = [
    "All Subjects",
    "CallPermission",
    "CallPermissionHistory",
    "Campaign",
    "ChatbotSetting",
    "ClientWebhook",
    "Contact",
    "CustomContact",
    "Flow",
    "FlowSchedule",
    "OptOut",
    "OptOutKeyword",
    "PersonalAccessToken",
    "PersonalAccessTokens",
    "Role",
    "SecurityGroup",
    "SenderId",
    "ShortUrl",
    "Template",
    "Tenant",
    "User",
    "WhatsappOrderInterest",
]

EXPECTED_ACTIVITY_EXPORT_HEADERS = [
    "User",
    "Event",
    "Subject",
    "Created at",
]
