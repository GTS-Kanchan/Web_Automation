"""
channels/base_channel.py — the Channel abstraction.

    BaseChannel
        |
        +-- SMSChannel
        +-- WhatsAppChannel
        +-- RCSChannel
        +-- EmailChannel
        +-- <FutureChannel>

What this is (and isn't)
-------------------------
This suite is 100% UI (Playwright) automation today — there is no existing
HTTP API client layer for it to wrap. BaseChannel is therefore a
COMPOSITION point, not a network abstraction: it centralizes the handful of
things every channel test genuinely needs and would otherwise duplicate --

  * channel-scoped config (credentials, base URL, channel-specific test data
    like sender IDs / template names, pulled from the single Config class)
  * worker-safe unique naming, prefixed per-channel (SMS_CAMPAIGN_...,
    WHATSAPP_CAMPAIGN_..., ...) so two channels' parallel workers can never
    produce a colliding name even if they happened to use the same prefix
  * a structured logger pre-tagged with this channel's name
  * the channel's test-data directory

It does NOT reimplement authentication, waiting, retry, or Playwright
context handling — those already live in utils/helpers.py (the `Helpers`
class every page object composes via `self.h`) and conftest.py's
`module_logged_in_page` / `logged_in_page` fixtures, and BaseChannel does
not duplicate them. A channel object is handed a Playwright `Page` (already
logged in) by a fixture; it does not create its own.

Adding a new channel = subclass BaseChannel, set NAME/DATA_SUBDIR, add any
channel-specific config accessors it needs. See channels/sms_channel.py for
the reference implementation, and docs/ADDING_A_CHANNEL.md for the full
walkthrough.
"""
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
