"""channels/sms_channel.py — SMS channel composition. Reference
implementation; copy this file's shape for a new channel."""
from channels.base_channel import BaseChannel
from utils.config import Config


class SMSChannel(BaseChannel):
    NAME = "sms"

    @property
    def sender_id(self) -> str:
        return Config.SMS_SENDER_ID

    @property
    def template_name(self) -> str:
        return Config.SMS_TEMPLATE_NAME

    @property
    def template_with_vars(self) -> str:
        return Config.SMS_TEMPLATE_WITH_VARS

    @property
    def paste_contacts(self) -> str:
        return Config.SMS_PASTE_CONTACTS

    @property
    def campaign_prefix(self) -> str:
        return Config.SMS_CAMPAIGN_PREFIX
