"""
tests/whatsapp/reports/test_whatsapp_parallel_example_flow.py

Reference example for TRUE test-case-level parallel execution on the
WhatsApp channel (deliverable: "Example WhatsApp parallel tests") — same
pattern as tests/sms/campaigns/test_sms_parallel_example_flow.py. Existing
WhatsApp coverage (tests/test_whatsapp_*.py) stays exactly where it is and
keeps its module-scoped "single sequential flow" style unchanged; this file
is new and additive.

Both tests below use their own function-scoped `logged_in_page` (own login,
own browser context) and only read the already-live WhatsApp Overview
report (WhatsappOverviewPage, unchanged) — no data is created or mutated,
so this file is safe to run repeatedly and in parallel with the rest of the
suite:

    pytest tests/whatsapp -n 4 --dist loadscope
"""
import pytest

from channels.whatsapp_channel import WhatsAppChannel
from pages.whatsapp.whatsapp_overview_page import WhatsappOverviewPage

pytestmark = [pytest.mark.whatsapp, pytest.mark.report]


@pytest.mark.smoke
def test_parallel_example_overview_report_loads(logged_in_page, correlation_id):
    whatsapp = WhatsAppChannel(page=logged_in_page)
    overview = WhatsappOverviewPage(logged_in_page)
    overview.navigate_to_report()

    whatsapp.log.info("Checking WhatsApp overview report loaded", correlation_id=correlation_id)
    assert overview.is_report_page(), "URL should contain /whatsapp/channels/overview"


@pytest.mark.smoke
def test_parallel_example_summary_cards_present(logged_in_page, correlation_id):
    whatsapp = WhatsAppChannel(page=logged_in_page)
    overview = WhatsappOverviewPage(logged_in_page)
    overview.navigate_to_report()

    cards = overview.get_all_summary_card_values()
    whatsapp.log.info("Read summary cards", card_count=len(cards or {}), correlation_id=correlation_id)
    assert cards, "WhatsApp overview should expose at least one summary card"
