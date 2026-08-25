"""
api/common/base_client.py — API client scaffold.

Honesty note: this suite is 100% UI (Playwright) automation today. There is
no existing HTTP client code anywhere in the project, and this file does
NOT invent one against endpoints nobody has confirmed — that would be
actively misleading (dead code implying capabilities the suite doesn't
have). What this DOES provide is the pattern to wire in a real client when
one is needed (e.g. asserting a message's delivery status via the CPaaS
API instead of/alongside the UI, or seeding test data faster than a UI
flow), built on Playwright's own `APIRequestContext` — already a
dependency, no new package needed.

Usage once real endpoints are confirmed (see api/sms/sms_client.py's
docstring for the concrete next step):

    from playwright.sync_api import sync_playwright
    from api.common.base_client import BaseApiClient

    with sync_playwright() as p:
        request_ctx = p.request.new_context(base_url=Config.API_URL)
        client = SmsClient(request_ctx)
        resp = client.get_message_status(message_id)
"""
from utils.config import Config
from utils.logger import TestLogger


class BaseApiClient:
    """Wraps a Playwright APIRequestContext (`playwright.sync_api.APIRequestContext`,
    e.g. from the `request` fixture pytest-playwright already provides, or
    `playwright.request.new_context()`), pre-tagged with a channel name for
    logging/correlation."""

    CHANNEL = "common"

    def __init__(self, request_context, base_url: str = None):
        self.request = request_context
        self.base_url = base_url or Config.API_URL
        self.log = TestLogger(channel=self.CHANNEL, env=Config.ENV)

    def get(self, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        self.log.debug("GET", url=url)
        return self.request.get(url, **kwargs)

    def post(self, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        self.log.debug("POST", url=url)
        return self.request.post(url, **kwargs)
