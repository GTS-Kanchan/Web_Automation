"""channels/rcs_channel.py — RCS channel composition."""
from channels.base_channel import BaseChannel
from utils.config import Config


class RCSChannel(BaseChannel):
    NAME = "rcs"

    @property
    def agent_name(self) -> str:
        return Config.RCS_AGENT_NAME
