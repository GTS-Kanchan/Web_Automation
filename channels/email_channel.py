"""channels/email_channel.py — Email channel composition."""
from channels.base_channel import BaseChannel
from utils.config import Config


class EmailChannel(BaseChannel):
    NAME = "email"

    @property
    def service(self) -> str:
        return Config.EMAIL_SERVICE

    @property
    def template_name(self) -> str:
        return Config.EMAIL_TEMPLATE_NAME

    @property
    def template_with_vars(self) -> str:
        return Config.EMAIL_TEMPLATE_WITH_VARS

    @property
    def paste_contacts(self) -> str:
        return Config.EMAIL_PASTE_CONTACTS

    @property
    def campaign_prefix(self) -> str:
        return Config.EMAIL_CAMPAIGN_PREFIX

    @property
    def subject(self) -> str:
        return Config.EMAIL_SUBJECT
