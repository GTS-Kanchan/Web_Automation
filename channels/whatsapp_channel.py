"""channels/whatsapp_channel.py — WhatsApp channel composition.

The suite's current WhatsApp coverage is read/analytics-focused (overview,
template analytics, message reports, opt-out, download center — see
tests/test_whatsapp_*.py), so Config has no WHATSAPP_* campaign-creation
constants yet the way SMS/Email do. Add them to utils/config.py the same
way SMS_SENDER_ID etc. are defined when WhatsApp campaign-creation tests
are added, then expose them here as properties (see SMSChannel)."""
from channels.base_channel import BaseChannel


class WhatsAppChannel(BaseChannel):
    NAME = "whatsapp"
