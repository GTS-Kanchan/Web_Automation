"""fixtures/rcs_fixtures.py — RCS-channel pytest fixtures."""
import pytest

from channels.rcs_channel import RCSChannel


@pytest.fixture
def rcs_channel(logged_in_page) -> RCSChannel:
    return RCSChannel(page=logged_in_page)
