"""fixtures/email_fixtures.py — Email-channel pytest fixtures."""
import pytest

from channels.email_channel import EmailChannel


@pytest.fixture
def email_channel(logged_in_page) -> EmailChannel:
    return EmailChannel(page=logged_in_page)
