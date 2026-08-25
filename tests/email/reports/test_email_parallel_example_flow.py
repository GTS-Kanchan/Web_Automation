"""
tests/email/reports/test_email_parallel_example_flow.py

Reference example for TRUE test-case-level parallel execution on the Email
channel (deliverable: "Example Email parallel tests"). Same pattern as the
SMS/WhatsApp/RCS examples — see
tests/sms/campaigns/test_sms_parallel_example_flow.py for the full
rationale. Read-only against EmailOverviewPage (unchanged); safe to run
repeatedly and in parallel:

    pytest tests/email -n 4 --dist loadscope
"""
import pytest

from channels.email_channel import EmailChannel
from pages.email.email_overview_page import EmailOverviewPage

pytestmark = [pytest.mark.email, pytest.mark.report]


@pytest.mark.smoke
def test_parallel_example_overview_report_loads(logged_in_page, correlation_id):
    email = EmailChannel(page=logged_in_page)
    overview = EmailOverviewPage(logged_in_page)
    overview.navigate_to_report()

    email.log.info("Checking Email overview report loaded", correlation_id=correlation_id)
    assert overview.is_report_page(), "URL should contain the Email overview report path"


@pytest.mark.smoke
def test_parallel_example_summary_cards_present(logged_in_page, correlation_id):
    email = EmailChannel(page=logged_in_page)
    overview = EmailOverviewPage(logged_in_page)
    overview.navigate_to_report()

    cards = overview.get_all_card_values()
    email.log.info("Read summary cards", card_count=len(cards or {}), correlation_id=correlation_id)
    assert cards, "Email overview should expose at least one summary card"
