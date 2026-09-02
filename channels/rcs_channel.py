"""channels/rcs_channel.py — RCS channel composition."""
from channels.base_channel import BaseChannel
from utils.config import Config
from utils.parallel import short_unique_tag


class RCSChannel(BaseChannel):
    NAME = "rcs"

    @property
    def agent_name(self) -> str:
        return Config.RCS_AGENT_NAME

    def unique_campaign_name(self, prefix: str = "RCS_CAMP") -> str:
        """Worker-safe unique RCS campaign name, e.g. "RCS_CAMP_812219m7K"
        (< 30 chars).

        Deliberately overrides BaseChannel.unique_campaign_name() with a
        different signature (a single `prefix`, no `max_len`) and a
        different underlying primitive: the RCS Campaign Name field has a
        tight, hand-tuned character budget that BaseChannel's default
        (built on unique_name()'s longer epoch/worker/counter/random
        suffix) would exceed. short_unique_tag() is used instead -- its
        own docstring in utils/parallel.py names "the RCS template/
        campaign creation flows" as one of the exact call sites it exists
        for.

        This consolidates what used to be a local `_unique_name()` helper
        duplicated inside
        tests/rcs/campaigns/test_rcs_campaign_create_flow.py (identical
        output shape: f"{prefix[:8]}_{short_unique_tag()}") so RCS
        campaign-name generation lives in one place instead of being
        re-implemented per test file. Behavior is unchanged from that
        helper -- this is a dedup, not a new naming scheme.
        """
        return f"{prefix[:8]}_{short_unique_tag()}"
