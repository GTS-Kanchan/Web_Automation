"""
tests/sms/campaigns/test_sms_parallel_example_flow.py

Reference example for TRUE test-case-level parallel execution (deliverable:
"Example SMS parallel tests"), contrasted with the rest of the SMS suite's
module-scoped "single sequential flow" style (see test_sms_campaign_flow.py
in this same directory) which trades per-test isolation for speed (one
login per file instead of per test) and is NOT safe to split across workers
mid-file.

These two tests are each fully independent:
  * function-scoped `logged_in_page` -> own browser context, own login, own
    Playwright page -- no shared state with each other or with any other
    test file.
  * every piece of test data is built with utils.parallel.unique_name /
    channels.SMSChannel.unique_campaign_name, so two workers (or this file
    and any other SMS test) can run at the exact same instant without ever
    producing the same campaign name.

Because of that, pytest-xdist is free to schedule these two tests onto
*different* workers simultaneously -- e.g.:

    pytest tests/sms -n 4 --dist loadscope

Run just this file in parallel:
    pytest tests/sms/campaigns/test_sms_parallel_example_flow.py -n 2

Neither test submits/launches the campaign (no real campaign is created in
the live app) — both are read/verify only, matching the same non-destructive
pattern already used by test_TC024_campaign_name_accepted in
test_sms_campaign_flow.py, so this file is safe to run repeatedly and in
parallel with the rest of the suite without leaving data behind.
"""
import pytest

from channels.sms_channel import SMSChannel
from pages.sms.sms_campaign_page import SMSCampaignPage

pytestmark = [pytest.mark.sms, pytest.mark.campaign]


@pytest.mark.smoke
def test_parallel_example_unique_campaign_name_roundtrips(logged_in_page, correlation_id):
    """Entering a worker-safe unique campaign name and reading it back
    demonstrates the naming mechanism end-to-end: two parallel runs of this
    same test (different workers) always produce different names."""
    sms = SMSChannel(page=logged_in_page)
    campaign_page = SMSCampaignPage(logged_in_page)
    campaign_page.open_campaign_list()

    name = sms.unique_campaign_name()
    sms.log.info("Entering unique campaign name", campaign_name=name, correlation_id=correlation_id)

    campaign_page.enter_campaign_name(name)
    entered = campaign_page.get_campaign_name()

    assert entered == name, (
        f"Campaign name field should hold the exact worker-safe unique value "
        f"entered ({name!r}), got {entered!r}"
    )


@pytest.mark.smoke
def test_parallel_example_two_unique_names_never_collide(logged_in_page, correlation_id):
    """Generating two names back-to-back within the same test (and the same
    worker) still never collides — the counter/random suffix in
    utils.parallel.unique_name covers same-worker, same-millisecond calls,
    not just cross-worker ones."""
    sms = SMSChannel(page=logged_in_page)
    name_a = sms.unique_campaign_name()
    name_b = sms.unique_campaign_name()

    sms.log.info("Generated two unique names", a=name_a, b=name_b, correlation_id=correlation_id)
    assert name_a != name_b, "Two unique_campaign_name() calls must never produce the same value"
    assert name_a.startswith("SMS_CAMPAIGN_")
    assert name_b.startswith("SMS_CAMPAIGN_")
