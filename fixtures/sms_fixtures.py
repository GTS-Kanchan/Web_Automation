"""fixtures/sms_fixtures.py — SMS-channel pytest fixtures, registered as a
plugin from conftest.py. Additive: existing tests/sms/*/test_*.py files
already define their own local page-object fixtures and keep using them
unchanged. New SMS tests can use `sms_channel` below instead."""
import pytest

from channels.sms_channel import SMSChannel


@pytest.fixture
def sms_channel(logged_in_page) -> SMSChannel:
    """Function-scoped: a fresh SMSChannel (fresh login, fresh browser
    context) per test — use for genuinely independent, parallel-safe SMS
    tests. For the existing single-sequential-flow style, build channel
    objects from module_logged_in_page directly instead (see
    tests/sms/campaigns/test_sms_parallel_example_flow.py for both
    patterns)."""
    return SMSChannel(page=logged_in_page)
