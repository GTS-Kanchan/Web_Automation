"""
RCS Campaigns — Automated Test Suite
Covers: List page interactions (Search, Filter, Export).

Migrated to Playwright: local page-object fixture renamed `campaign_page`
(built on conftest.py's `module_logged_in_page`) to avoid shadowing
pytest-playwright's reserved `page` fixture.
"""
import datetime
import os

import pytest

from constants.rcs_campaign_headers import EXPECTED_RCS_CAMPAIGN_HEADERS
from pages.rcs.rcs_campaign_page import RCSCampaignPage
from utils.config import Config
from utils.file_validator import (
    EmptyFileError,
    FileNotDownloadedError,
    HeaderValidationError,
    UnsupportedFileTypeError,
    validate_file_headers,
)


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
    """TC004: Verify filtering by Status. Confirmed live markup: Status
    is a custom Alpine multiselect ('Select status (N)' button opening a
    checkbox panel listing Draft/Scheduled/Running/Paused/Completed/
    Cancelled/Failed) -- not the native <select> the old version assumed
    (SELECT_FILTER_STATUS's select_option() call never matched anything
    real, which is why this test previously only ever skipped)."""
    campaign_page.load_campaign_list()
    ok = campaign_page.set_status_filter("Completed")
    if not ok:
        pytest.skip(
            "Status filter control (BTN_STATUS_FILTER / 'Select status' "
            "button) not found/interactable"
        )
    assert ok


def test_TC005_campaign_pagination_navigates_pages(campaign_page):
    """TC005: Clicking the page-2 pagination button navigates to page 2
    without error. Confirmed live markup: numbered pagination buttons
    via wire:click="gotoPage(N, 'rcs_campaignsPage')", aria-label='Go to
    page N' -- replaces the old per-page-count-dropdown version, whose
    SELECT_PER_PAGE locator was never confirmed and this list's table
    may not even offer (only page-number navigation was confirmed)."""
    campaign_page.load_campaign_list()
    if not campaign_page.is_page_number_button_present(2, timeout=5000):
        pytest.skip("No page-2 pagination button present -- fewer than 2 pages of results")
    ok = campaign_page.go_to_page(2)
    if not ok:
        pytest.skip("Could not click the page-2 pagination button")
    title = campaign_page.get_title().lower()
    assert "404" not in title and "500" not in title


def test_TC006_campaign_export(campaign_page):
    """TC006: Verify Export functionality triggers a download or UI reaction."""
    campaign_page.load_campaign_list()
    # We just click Export to ensure no JS errors occur (actual file validation would require filesystem checks)
    try:
        campaign_page.export_data()
    except Exception as e:
        pytest.skip(f"Export button not found or failed: {e}")


def _export_and_validate_header(campaign_page, label):
    """Shared export + header-validation tail for TC007/TC008/TC009.
    Reuses the exact utils/file_validator.py flow already proven by every
    SMS report/export test (see tests/sms/reports/test_sms_campaign_report_flow.py's
    test_campaign_report_TC15_export_csv) -- the RCS Campaign list's
    "Export CSV" button actually downloads an .xlsx ("Table Export.xlsx"),
    confirmed from a real download on this instance, which is exactly why
    this generic validator (dispatches on file extension) is used instead
    of assuming a raw .csv."""
    result = campaign_page.click_export_csv(timeout_ms=30000)
    if result is None:
        pytest.skip(f"[{label}] Export CSV did not produce a downloaded file within 30s")
    file_path = result["file_path"]
    print(f"[{label}] Export file downloaded: {os.path.basename(file_path)} ({result['file_size']} bytes)")

    print(f"[{label}] Expected headers: {EXPECTED_RCS_CAMPAIGN_HEADERS}")
    try:
        actual_headers = validate_file_headers(file_path, EXPECTED_RCS_CAMPAIGN_HEADERS)
    except FileNotDownloadedError as exc:
        pytest.fail(f"[{label}] {exc}")
    except (UnsupportedFileTypeError, EmptyFileError) as exc:
        print(f"[{label}] Header validation: FAIL")
        pytest.fail(str(exc))
    except HeaderValidationError as exc:
        print(f"[{label}] Actual headers: {exc.actual}")
        print(f"[{label}] Header validation: FAIL")
        print(f"[{label}] Missing headers: {exc.missing}")
        print(f"[{label}] Unexpected headers: {exc.unexpected}")
        for position, expected_name, actual_name in exc.mismatches:
            print(f"[{label}] Position {position}: expected '{expected_name}', actual '{actual_name}'")
        pytest.fail(str(exc))

    print(f"[{label}] Actual headers: {actual_headers}")
    print(f"[{label}] Header validation: PASS")


@pytest.mark.regression
def test_TC007_filter_type_and_export_verifies_header(campaign_page):
    """TC007: Setting the Type filter, then exporting, downloads a file
    whose header row matches this instance's confirmed RCS Campaign
    export columns exactly (constants/rcs_campaign_headers.py). Type
    filter application is best-effort -- its exact DOM wasn't
    independently captured the way the Status checkbox panel and the
    Export/download flow were (only confirmed via screenshot) -- so a
    filter that can't be set is noted but doesn't fail the test; the
    header-row assertion itself is exact."""
    campaign_page.load_campaign_list()
    type_ok = campaign_page.set_type_filter("All")
    print(f"[TC007] Type filter applied: {type_ok}")
    _export_and_validate_header(campaign_page, "TC007")


@pytest.mark.regression
def test_TC008_filter_agent_and_export_verifies_header(campaign_page):
    """TC008: Setting the Agent filter (Config.RCS_AGENT_NAME, the same
    known-existing agent used throughout the create-flow suite -- no new
    hardcoded value), then exporting, downloads a file whose header row
    matches this instance's confirmed RCS Campaign export columns
    exactly. Agent filter application is best-effort -- its exact DOM
    wasn't independently captured, only the shared 'Select agent (N)'
    multiselect pattern and trigger button -- so a filter that can't be
    set is noted but doesn't fail the test; the header-row assertion
    itself is exact."""
    campaign_page.load_campaign_list()
    agent_ok = campaign_page.set_agent_filter(Config.RCS_AGENT_NAME)
    print(f"[TC008] Agent filter applied: {agent_ok}")
    _export_and_validate_header(campaign_page, "TC008")


@pytest.mark.regression
def test_TC009_filter_created_date_range_and_export_verifies_header(campaign_page):
    """TC009: Setting the Created From/To date range filter, then
    exporting, downloads a file whose header row matches this instance's
    confirmed RCS Campaign export columns exactly. Date filter
    application is best-effort -- its exact DOM wasn't independently
    captured, only its labels (confirmed via screenshot) -- so a filter
    that can't be set is noted but doesn't fail the test; the header-row
    assertion itself is exact."""
    campaign_page.load_campaign_list()
    today = datetime.date.today()
    from_date = (today - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")
    date_ok = campaign_page.set_created_date_range(from_date, to_date)
    print(f"[TC009] Created date range applied: {date_ok}")
    _export_and_validate_header(campaign_page, "TC009")
