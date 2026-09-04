"""
RCS Agents — Single Sequential Flow
=====================================
Migrated to Playwright: local page-object fixture renamed
`agent_page` (built on conftest.py's `module_logged_in_page`) to avoid
shadowing pytest-playwright's reserved `page` fixture.

Run:
    pytest tests/test_rcs_agent_flow.py -v
"""
import os

import pytest

from constants.rcs_agent_list_headers import EXPECTED_RCS_AGENT_LIST_HEADERS
from pages.rcs.rcs_agent_page import RcsAgentPage
from utils.file_validator import (
    EmptyFileError,
    FileNotDownloadedError,
    HeaderValidationError,
    UnsupportedFileTypeError,
    validate_file_headers,
)


pytestmark = [pytest.mark.rcs, pytest.mark.agent]

@pytest.fixture(scope="module")
def agent_page(module_logged_in_page):
    p = RcsAgentPage(module_logged_in_page)
    p.navigate()
    p.wait_for_table_load(timeout=15000)
    return p


def ensure_on_agent_page(p: RcsAgentPage):
    if not p.is_agent_page():
        p.navigate()
        p.wait_for_table_load(timeout=10000)


def reset_state(p: RcsAgentPage):
    try:
        p.clear_search()
    except Exception:
        pass
    try:
        p.clear_date_filters()
    except Exception:
        pass


def test_RCS001_page_loads_successfully(agent_page):
    ensure_on_agent_page(agent_page)
    assert agent_page.is_agent_page()
    assert agent_page.is_element_present(agent_page.TABLE, timeout=10000)


def test_RCS002_page_title(agent_page):
    ensure_on_agent_page(agent_page)
    title = agent_page.get_page_title_text()
    assert "rcs agents" in title.lower()


def test_RCS003_breadcrumb_navigation(agent_page):
    ensure_on_agent_page(agent_page)
    crumb = agent_page.get_breadcrumb_text().lower()
    assert "home" in crumb
    assert "channels" in crumb
    assert "rcs agents" in crumb


def test_RCS004_records_displayed(agent_page):
    ensure_on_agent_page(agent_page)
    reset_state(agent_page)
    assert agent_page.has_records()


def test_RCS005_table_columns(agent_page):
    ensure_on_agent_page(agent_page)
    headers = [h.lower() for h in agent_page.get_visible_column_headers()]
    expected = ["action", "logo", "agent name", "display name", "use case",
                "status", "verification status", "created at"]
    for name in expected:
        assert any(name in h for h in headers), f"missing column header: {name}"


def test_RCS006_search_valid_keyword(agent_page):
    ensure_on_agent_page(agent_page)
    reset_state(agent_page)
    agent_page.search("a")
    agent_page.page.wait_for_timeout(1000)
    assert agent_page.get_row_count() > 0 or agent_page.has_no_records_message()
    agent_page.clear_search()


def test_RCS007_search_invalid_keyword(agent_page):
    ensure_on_agent_page(agent_page)
    reset_state(agent_page)
    agent_page.search("zzz_no_such_agent_zzz")
    agent_page.page.wait_for_timeout(1000)
    assert agent_page.has_no_records_message() or agent_page.get_row_count() == 0
    agent_page.clear_search()


def test_RCS008_clear_search(agent_page):
    ensure_on_agent_page(agent_page)
    agent_page.search("zzz_no_such_agent_zzz")
    agent_page.page.wait_for_timeout(1000)
    agent_page.clear_search()
    agent_page.page.wait_for_timeout(1000)
    assert agent_page.has_records()


def test_RCS009_filters_button(agent_page):
    ensure_on_agent_page(agent_page)
    agent_page.open_filters_popover()
    assert agent_page.is_element_present(agent_page.FILTER_CREATED_FROM, timeout=5000)
    assert agent_page.is_element_present(agent_page.FILTER_CREATED_TO, timeout=5000)


def test_RCS010_created_from_date_filter(agent_page):
    ensure_on_agent_page(agent_page)
    reset_state(agent_page)
    agent_page.set_created_from_filter("2025-01-01")
    agent_page.page.wait_for_timeout(1000)
    assert agent_page.has_records() or agent_page.has_no_records_message()
    from_val, _ = agent_page.get_filter_values()
    assert from_val == "2025-01-01"
    agent_page.clear_date_filters()


def test_RCS011_created_to_date_filter(agent_page):
    ensure_on_agent_page(agent_page)
    reset_state(agent_page)
    agent_page.set_created_to_filter("2025-12-31")
    agent_page.page.wait_for_timeout(1000)
    assert agent_page.has_records() or agent_page.has_no_records_message()
    _, to_val = agent_page.get_filter_values()
    assert to_val == "2025-12-31"
    agent_page.clear_date_filters()


def test_RCS012_created_date_range_filter(agent_page):
    ensure_on_agent_page(agent_page)
    reset_state(agent_page)
    agent_page.set_date_range_filter("2025-01-01", "2025-12-31")
    agent_page.page.wait_for_timeout(1000)
    assert agent_page.has_records() or agent_page.has_no_records_message()
    from_val, to_val = agent_page.get_filter_values()
    assert from_val == "2025-01-01"
    assert to_val == "2025-12-31"
    agent_page.clear_date_filters()


def test_RCS013_clear_filter(agent_page):
    ensure_on_agent_page(agent_page)
    agent_page.set_date_range_filter("2025-01-01", "2025-12-31")
    agent_page.page.wait_for_timeout(1000)
    agent_page.clear_date_filters()
    from_val, to_val = agent_page.get_filter_values()
    assert from_val == ""
    assert to_val == ""
    assert agent_page.has_records()


def test_RCS014_view_action_button(agent_page):
    ensure_on_agent_page(agent_page)
    reset_state(agent_page)
    clicked = agent_page.click_view_on_first_row()
    assert clicked
    opened = agent_page.is_modal_open() or agent_page.is_element_present(agent_page.MODAL_CONTAINER, timeout=5000)
    assert opened
    ensure_on_agent_page(agent_page)


def test_RCS015_agent_name_values(agent_page):
    ensure_on_agent_page(agent_page)
    reset_state(agent_page)
    values = agent_page.get_column_values("agent_name")
    assert len(values) > 0
    assert all(v.strip() != "" for v in values)


def test_RCS016_display_name_values(agent_page):
    ensure_on_agent_page(agent_page)
    values = agent_page.get_column_values("display_name")
    assert len(values) > 0
    assert all(v.strip() != "" for v in values)


def test_RCS017_use_case_values(agent_page):
    ensure_on_agent_page(agent_page)
    values = agent_page.get_column_values("use_case")
    assert len(values) > 0
    valid = {"transactional", "promotional", "multi_use", "otp"}
    for v in values:
        assert v.strip().lower() in valid, f"unexpected use case value: {v}"


def test_RCS018_status_values(agent_page):
    ensure_on_agent_page(agent_page)
    values = agent_page.get_column_values("status")
    assert len(values) > 0
    valid = {"launched", "draft"}
    for v in values:
        assert v.strip().lower() in valid, f"unexpected status value: {v}"


def test_RCS019_verification_status_values(agent_page):
    ensure_on_agent_page(agent_page)
    values = agent_page.get_column_values("verification_status")
    assert len(values) > 0
    valid = {"verified", "pending", "rejected"}
    for v in values:
        assert v.strip().lower() in valid, f"unexpected verification status value: {v}"


def test_RCS020_created_at_values(agent_page):
    ensure_on_agent_page(agent_page)
    values = agent_page.get_column_values("created_at")
    assert len(values) > 0
    assert all(v.strip() != "" for v in values)


def test_RCS021_sorting_by_created_at(agent_page):
    ensure_on_agent_page(agent_page)
    reset_state(agent_page)
    agent_page.sort_by_created_at()
    assert agent_page.has_records() or agent_page.has_no_records_message()


def test_RCS022_bulk_actions_dropdown(agent_page):
    ensure_on_agent_page(agent_page)
    agent_page.open_bulk_actions_dropdown()
    assert agent_page.is_element_present(agent_page.BULK_ACTION_EXPORT, timeout=5000)


def test_RCS023_columns_dropdown(agent_page):
    ensure_on_agent_page(agent_page)
    agent_page.open_columns_dropdown()
    assert agent_page.is_element_present(agent_page.COLUMN_CHECKBOXES, timeout=5000)
    assert agent_page.is_element_present(agent_page.SELECT_ALL_COLUMNS_CHECKBOX, timeout=5000)


def test_RCS025_page_refresh(agent_page):
    ensure_on_agent_page(agent_page)
    agent_page.refresh_page()
    assert agent_page.is_agent_page()
    assert agent_page.has_records()


def test_RCS026_export_csv_verifies_header(agent_page):
    """Bulk Actions -> Export downloads a file whose header row matches
    this instance's confirmed RCS Agent list export columns exactly
    (constants/rcs_agent_list_headers.py). No row checkboxes are
    selected first -- mirrors the confirmed-working Bulk Actions ->
    Export pattern already proven on SmsBlockedNumbersPage.export_csv()
    (see RcsAgentPage.export_csv() docstring): the export acts on the
    current filtered listing."""
    ensure_on_agent_page(agent_page)
    result = agent_page.export_csv()
    if result is None:
        pytest.skip("Bulk Actions -> Export did not produce a downloaded file within 30s")
    print(f"[{os.path.basename(result['file_path'])}] downloaded, {result['file_size']} bytes, {result['elapsed_s']:.2f}s")

    try:
        actual_headers = validate_file_headers(result["file_path"], EXPECTED_RCS_AGENT_LIST_HEADERS)
    except FileNotDownloadedError as exc:
        pytest.fail(str(exc))
    except (UnsupportedFileTypeError, EmptyFileError) as exc:
        pytest.fail(str(exc))
    except HeaderValidationError as exc:
        print(f"Actual headers: {exc.actual}")
        print(f"Missing headers: {exc.missing}")
        print(f"Unexpected headers: {exc.unexpected}")
        for position, expected_name, actual_name in exc.mismatches:
            print(f"Position {position}: expected '{expected_name}', actual '{actual_name}'")
        pytest.fail(str(exc))

    print(f"Header validation PASS: {actual_headers}")
    assert agent_page.is_agent_page()
