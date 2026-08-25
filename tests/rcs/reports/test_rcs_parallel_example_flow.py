"""
tests/rcs/reports/test_rcs_parallel_example_flow.py

Reference example for TRUE test-case-level parallel execution on the RCS
channel (deliverable: "Example RCS parallel tests"). Same pattern as the
SMS/WhatsApp examples — see tests/sms/campaigns/test_sms_parallel_example_flow.py
for the full rationale. Read-only against RcsOverviewPage (unchanged); safe
to run repeatedly and in parallel:

    pytest tests/rcs -n 4 --dist loadscope
"""
import pytest

from channels.rcs_channel import RCSChannel
from pages.rcs.rcs_overview_page import RcsOverviewPage

pytestmark = [pytest.mark.rcs, pytest.mark.report]


@pytest.mark.smoke
def test_parallel_example_overview_report_loads(logged_in_page, correlation_id):
    rcs = RCSChannel(page=logged_in_page)
    overview = RcsOverviewPage(logged_in_page)
    overview.navigate_to_report()

    rcs.log.info("Checking RCS overview report loaded", correlation_id=correlation_id)
    assert overview.is_report_page(), "URL should contain the RCS overview report path"


@pytest.mark.smoke
def test_parallel_example_summary_cards_present(logged_in_page, correlation_id):
    rcs = RCSChannel(page=logged_in_page)
    overview = RcsOverviewPage(logged_in_page)
    overview.navigate_to_report()

    cards = overview.get_all_summary_card_values()
    rcs.log.info("Read summary cards", card_count=len(cards or {}), correlation_id=correlation_id)
    assert cards, "RCS overview should expose at least one summary card"
