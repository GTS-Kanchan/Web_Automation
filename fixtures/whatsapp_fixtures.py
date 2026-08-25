"""fixtures/whatsapp_fixtures.py — WhatsApp-channel pytest fixtures."""
import pytest

from channels.whatsapp_channel import WhatsAppChannel


@pytest.fixture
def whatsapp_channel(logged_in_page) -> WhatsAppChannel:
    return WhatsAppChannel(page=logged_in_page)
