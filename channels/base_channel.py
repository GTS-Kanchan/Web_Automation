
from abc import ABC
import os

from utils.config import Config
from utils.logger import TestLogger
from utils.parallel import unique_name


class BaseChannel(ABC):
    #: Short channel key used everywhere: unique-name prefixes, log tags,
    #: marker names, data subdirectory. Subclasses MUST override.
    NAME = "base"

    def __init__(self, page=None, env: str = None):
        """*page* is an already-authenticated Playwright Page (from
        module_logged_in_page / logged_in_page) — BaseChannel does not log
        in on its own; that stays centralized in conftest.py."""
        self.page = page
        self.env = env or os.getenv("ENV", "qa")
        self.config = Config
        self.log = TestLogger(channel=self.NAME, env=self.env)

    # ── Worker-safe unique naming ────────────────────────────────────────────

    def unique_campaign_name(self, suffix: str = "CAMPAIGN", max_len: int = None) -> str:
        return unique_name(f"{self.NAME.upper()}_{suffix}", max_len=max_len)

    def unique_template_name(self, suffix: str = "TEMPLATE", max_len: int = None) -> str:
        return unique_name(f"{self.NAME.upper()}_{suffix}", max_len=max_len)

    def unique(self, label: str, max_len: int = None) -> str:
        """General-purpose escape hatch for any other per-channel unique
        value (a contact, a sender ID, a temp filename, ...)."""
        return unique_name(f"{self.NAME.upper()}_{label}", max_len=max_len)

    # ── Test data ─────────────────────────────────────────────────────────

    @property
    def data_dir(self) -> str:
        """tests/test_data/<channel>/ — falls back to the shared
        tests/test_data/ root if no channel-specific subfolder exists yet,
        so this is safe to call before any channel has migrated its data
        files into a subfolder."""
        from utils.test_data_generator import DATA_DIR as SHARED_DATA_DIR
        channel_dir = os.path.join(SHARED_DATA_DIR, self.NAME)
        return channel_dir if os.path.isdir(channel_dir) else SHARED_DATA_DIR
