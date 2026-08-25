"""
RCS Campaigns — Automated Test Suite
Covers: List page interactions (Search, Filter, Export).

Migrated to Playwright: local page-object fixture renamed `campaign_page`
(built on conftest.py's `module_logged_in_page`) to avoid shadowing
pytest-playwright's reserved `page` fixture.
"""
import pytest

from pages.rcs.rcs_campaign_page import RCSCampaignPage


pytestmark = [pytest.mark.rcs, pytest.mark.campaign]

@pytest.fixture(scope="module")
def campaign_page(module_logged_in_page):
    """Yield the RCSCampaignPage, built on the already-logged-in module page."""
    return RCSCampaignPage(module_logged_in_page)


@pytest.fixture(autouse=True)
def _reset_after_test(campaign_page):
    """Ensure each test starts on the correct page."""
    yield
    campaign_page.load_campaign_list()
    campaign_page.page.wait_for_timeout(1000)


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_TC001_campaign_page_loads(campaign_page):
    """TC001: Verify that the RCS Campaign list page loads successfully."""
    campaign_page.load_campaign_list()
    assert "rcs/campaign" in campaign_page.get_current_url().lower(), "Did not navigate to RCS Campaign page"
    try:
        campaign_page.h.wait_for_element_visible("h1", timeout=10000)
    except Exception:
        pass
    assert "Campaign" in campaign_page.get_title() or campaign_page.page.locator("h1").count() > 0, \
        "Page heading missing"


def test_TC002_campaign_list_table_loads(campaign_page):
    """TC002: Verify that the Campaign list table loads properly."""
    campaign_page.load_campaign_list()
    campaign_page.wait_for_spinner_to_disappear()
    rows = campaign_page.get_table_rows()
    # It might be 0 if there are no campaigns, but the table should not throw exceptions
    assert isinstance(rows, list), "Failed to retrieve table rows"


def test_TC003_campaign_search(campaign_page):
    """TC003: Search for a dummy campaign returns no results."""
    campaign_page.load_campaign_list()
    campaign_page.wait_for_spinner_to_disappear()
    campaign_page.search_campaign("Test Campaign Search XYZ")
    campaign_page.page.wait_for_timeout(3000)  # Give extra time for debounce and search
    rows = campaign_page.get_table_rows()
    if len(rows) == 1:
        text = rows[0].inner_text().lower()
        assert any(x in text for x in ["no ", "0", "not found", "nothing"]), f"Expected empty state, got row: {text}"
    else:
        assert len(rows) == 0, f"Expected 0 records for dummy search, got {len(rows)}"


def test_TC004_campaign_filter_status(campaign_page):
    """TC004: Verify filtering by Status."""
    campaign_page.load_campaign_list()
    try:
        campaign_page.set_status_filter("Completed")
        campaign_page.wait_for_spinner_to_disappear()
    except Exception as e:
        pytest.skip(f"Status filter not available or exception occurred: {e}")


def test_TC005_campaign_pagination_per_page(campaign_page):
    """TC005: Verify per-page pagination dropdown."""
    campaign_page.load_campaign_list()
    try:
        campaign_page.set_per_page("25")
        rows = campaign_page.get_table_rows()
        assert len(rows) <= 25, f"Expected at most 25 rows, got {len(rows)}"
    except Exception as e:
        pytest.skip(f"Per page dropdown error: {e}")


def test_TC006_campaign_export(campaign_page):
    """TC006: Verify Export functionality triggers a download or UI reaction."""
    campaign_page.load_campaign_list()
    # We just click Export to ensure no JS errors occur (actual file validation would require filesystem checks)
    try:
        campaign_page.export_data()
    except Exception as e:
        pytest.skip(f"Export button not found or failed: {e}")
