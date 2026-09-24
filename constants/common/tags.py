"""constants/tags.py — single source of truth for marker/tag names, so
`-m` expressions and any tooling that reads/writes markers agree with what's
declared in pytest.ini. Keep this list in sync with pytest.ini's `markers =`
block when adding a new channel or feature area."""

CHANNELS = ("sms", "whatsapp", "rcs", "email")
FEATURES = ("campaign", "template", "sender_id", "messaging", "report", "opt_out", "agent")
LEVELS = ("smoke", "regression", "negative")
CROSS_CUTTING = ("common",)

ALL_MARKERS = CHANNELS + FEATURES + LEVELS + CROSS_CUTTING
