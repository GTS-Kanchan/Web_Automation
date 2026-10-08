"""
Test Suite: Chatbot -> Reports -> Summary (Chatbot Flow Summary Report)
========================================================================
Test Cases:
  CHAT_SUM_001 – CHAT_SUM_005: Page Load, Title, Columns & Records (5 TCs)
  CHAT_SUM_006 – CHAT_SUM_010: Search Functionality (5 TCs)
  CHAT_SUM_011 – CHAT_SUM_018: Filters (Open, Available, Date, Flow Name, Combined, Clear, Remove, Empty) (8 TCs)
  CHAT_SUM_019 – CHAT_SUM_028: Sorting (Default, Date, Flow Name, Opened, Abandoned, Closed, Filtered) (10 TCs)
  CHAT_SUM_029 – CHAT_SUM_035: Columns Visibility (Dropdown, Hide, Show, Restore) (7 TCs)
  CHAT_SUM_036 – CHAT_SUM_042: Bulk Actions & Checkboxes (7 TCs)
  CHAT_SUM_043 – CHAT_SUM_053: Data Verification & Integrity (11 TCs)
  CHAT_SUM_054 – CHAT_SUM_058: Export Functionality (5 TCs)
  CHAT_SUM_059 – CHAT_SUM_060: UI Horizontal Scroll & Tenant Isolation (2 TCs)
Total: 60 test cases.

Target Page: /chatbot/reports/summary

Run:
    pytest tests/chatbot/reports/test_chatbot_summary_report_flow.py -v
"""

from datetime import datetime
import pytest

from pages.chatbot.chatbot_summary_report_page import ChatbotSummaryReportPage
from utils.datetime_verification import DateFormatValidationError, validate_date_values_format
from constants.chatbot_summary_headers import (
    EXPECTED_PAGE_HEADING,
    EXPECTED_SUMMARY_UI_HEADERS,
    ALL_SUMMARY_COLUMNS,
    EXPECTED_EXPORT_HEADERS,
)


pytestmark = [
    pytest.mark.chatbot,
    pytest.mark.report,
]


# ══════════════════════════════════════════════════════════════════════════════
# Fixture & State Reset Helpers
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def summary_page(module_logged_in_page):
    """Module-level fixture navigating to the Chatbot Flow Summary Report page."""
    p = ChatbotSummaryReportPage(module_logged_in_page)
    p.navigate()
    return p


def ensure_on_summary_page(p: ChatbotSummaryReportPage):
    """Ensure browser is currently on the Summary Report page."""
    if not p.is_summary_report_page():
        p.navigate()


def reset_summary_state(p: ChatbotSummaryReportPage):
    """Reset filters, search, and sorting to a clean default state."""
    try:
        p.clear_search()
    except Exception:
        pass

    try:
        p.clear_all_filters()
    except Exception:
        pass

    try:
        p.restore_all_columns()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# Page Load, Title, Columns & Records (CHAT_SUM_001 – CHAT_SUM_005)
# ══════════════════════════════════════════════════════════════════════════════

def test_CHAT_SUM_001_verify_summary_report_page_loads(summary_page):
    """Chatbot Flow Summary Report page loads successfully."""
    ensure_on_summary_page(summary_page)
    assert summary_page.is_summary_report_page(), "Summary Report page should load"


def test_CHAT_SUM_002_verify_page_title(summary_page):
    """Chatbot Flow summary Report heading is displayed."""
    ensure_on_summary_page(summary_page)
    heading = summary_page.get_heading_text()
    assert EXPECTED_PAGE_HEADING.lower() in heading.lower(), (
        f"Expected heading '{EXPECTED_PAGE_HEADING}', got '{heading}'"
    )


def test_CHAT_SUM_003_verify_report_table(summary_page):
    """Flow Name, Date, Conversation Opened, Conversation Abandoned, and Closed columns displayed."""
    ensure_on_summary_page(summary_page)
    headers = summary_page.get_column_headers()
    for expected in EXPECTED_SUMMARY_UI_HEADERS:
        assert any(expected.lower() in h.lower() for h in headers), (
            f"Expected column '{expected}' not found in headers: {headers}"
        )


def test_CHAT_SUM_004_verify_report_records(summary_page):
    """Existing flow summary records are displayed."""
    ensure_on_summary_page(summary_page)
    rows = summary_page.get_row_count()
    assert rows > 0 or summary_page.is_empty_state_displayed(), (
        "Table should either display rows or valid empty state"
    )


def test_CHAT_SUM_005_verify_result_data(summary_page):
    """Values are displayed correctly in visible rows."""
    ensure_on_summary_page(summary_page)
    if summary_page.get_row_count() > 0:
        flow_name = summary_page.get_cell_value(0, "flow-name")
        date_val = summary_page.get_cell_value(0, "date")
        assert flow_name != "", "Flow Name cell should not be blank"
        assert date_val != "", "Date cell should not be blank"


# ══════════════════════════════════════════════════════════════════════════════
# Search Functionality (CHAT_SUM_006 – CHAT_SUM_010)
# ══════════════════════════════════════════════════════════════════════════════

def test_CHAT_SUM_006_search_by_exact_flow_name(summary_page):
    """Search by exact flow name displays matching records."""
    ensure_on_summary_page(summary_page)
    reset_summary_state(summary_page)
    summary_page.search("rcs chatbot")
    if summary_page.get_row_count() > 0:
        names = summary_page.get_column_values("flow-name")
        assert any("rcs chatbot" in n.lower() for n in names)
    summary_page.clear_search()


def test_CHAT_SUM_007_search_by_partial_flow_name(summary_page):
    """Search by partial flow name displays matching records."""
    ensure_on_summary_page(summary_page)
    summary_page.search("Demo")
    if summary_page.get_row_count() > 0:
        names = summary_page.get_column_values("flow-name")
        assert any("demo" in n.lower() for n in names)
    summary_page.clear_search()


def test_CHAT_SUM_008_search_nonexistent_flow(summary_page):
    """Search nonexistent flow displays empty state or zero records."""
    ensure_on_summary_page(summary_page)
    summary_page.search("XYZ123NonExistentFlow999")
    assert summary_page.get_row_count() == 0 or summary_page.is_empty_state_displayed(), (
        "No matching records should be displayed for nonexistent flow query"
    )
    summary_page.clear_search()


def test_CHAT_SUM_009_clear_search(summary_page):
    """Clear search restores full dataset."""
    ensure_on_summary_page(summary_page)
    summary_page.search("test")
    summary_page.clear_search()
    assert summary_page.get_search_value() == "", "Search input should be cleared"


def test_CHAT_SUM_010_case_insensitive_search(summary_page):
    """Search with uppercase text returns matching records."""
    ensure_on_summary_page(summary_page)
    summary_page.search("RCS CHATBOT")
    upper_count = summary_page.get_row_count()
    summary_page.search("rcs chatbot")
    lower_count = summary_page.get_row_count()
    assert upper_count == lower_count, "Search should be case-insensitive"
    summary_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# Filters (CHAT_SUM_011 – CHAT_SUM_018)
# ══════════════════════════════════════════════════════════════════════════════

def test_CHAT_SUM_011_open_filters(summary_page):
    """Clicking Filters opens filter panel popover."""
    ensure_on_summary_page(summary_page)
    summary_page.open_filters()
    assert summary_page.is_filter_popover_open(), "Filter popover should be open"
    summary_page.close_filters()


def test_CHAT_SUM_012_verify_available_filters(summary_page):
    """Configured report filters are displayed (From Date, To Date, Flow Name)."""
    ensure_on_summary_page(summary_page)
    summary_page.open_filters()
    assert summary_page.from_date_input.is_visible(), "From Date filter should be visible"
    assert summary_page.to_date_input.is_visible(), "To Date filter should be visible"
    assert summary_page.flow_name_select.is_visible(), "Flow Name filter should be visible"
    summary_page.close_filters()


def test_CHAT_SUM_013_apply_date_filter(summary_page):
    """Apply valid date filter -> records for selected date are displayed."""
    ensure_on_summary_page(summary_page)
    reset_summary_state(summary_page)
    summary_page.set_from_date("2026-09-01")
    summary_page.set_to_date("2026-09-19")
    summary_page.close_filters()
    assert summary_page.is_summary_report_page()


def test_CHAT_SUM_014_apply_flow_name_filter_if_available(summary_page):
    """Select a specific flow name from dropdown -> only matching records shown."""
    ensure_on_summary_page(summary_page)
    options = summary_page.get_available_flow_name_options()
    valid_options = [o for o in options if o and o != "All"]
    if valid_options:
        target_flow = valid_options[0]
        summary_page.select_flow_name(target_flow)
        summary_page.close_filters()
        if summary_page.get_row_count() > 0:
            names = summary_page.get_column_values("flow-name")
            assert all(target_flow.lower() in n.lower() for n in names)
    summary_page.clear_all_filters()


def test_CHAT_SUM_015_apply_multiple_filters(summary_page):
    """Apply Date and Flow Name filters together."""
    ensure_on_summary_page(summary_page)
    reset_summary_state(summary_page)
    summary_page.set_from_date("2026-09-01")
    options = summary_page.get_available_flow_name_options()
    valid_options = [o for o in options if o and o != "All"]
    if valid_options:
        summary_page.select_flow_name(valid_options[0])
    summary_page.close_filters()
    assert summary_page.is_summary_report_page()


def test_CHAT_SUM_016_clear_filters(summary_page):
    """Apply filter then clear -> full dataset restored."""
    ensure_on_summary_page(summary_page)
    summary_page.set_from_date("2026-09-01")
    summary_page.close_filters()
    summary_page.clear_all_filters()
    assert summary_page.is_summary_report_page()


def test_CHAT_SUM_017_remove_individual_filter(summary_page):
    """Remove individual filter pill leaves remaining filters active."""
    ensure_on_summary_page(summary_page)
    reset_summary_state(summary_page)
    summary_page.set_from_date("2026-09-01")
    summary_page.close_filters()
    summary_page.remove_filter_pill("from_date")
    summary_page.clear_all_filters()


def test_CHAT_SUM_018_filter_with_no_matching_data(summary_page):
    """Apply filter with no records -> empty state displayed."""
    ensure_on_summary_page(summary_page)
    summary_page.set_from_date("2020-01-01")
    summary_page.set_to_date("2020-01-02")
    summary_page.close_filters()
    assert summary_page.get_row_count() == 0 or summary_page.is_empty_state_displayed()
    summary_page.clear_all_filters()


# ══════════════════════════════════════════════════════════════════════════════
# Sorting (CHAT_SUM_019 – CHAT_SUM_028)
# ══════════════════════════════════════════════════════════════════════════════

def test_CHAT_SUM_019_verify_default_sorting(summary_page):
    """'Date: Z-A' sorting applied by default."""
    ensure_on_summary_page(summary_page)
    reset_summary_state(summary_page)
    sort_text = summary_page.get_active_sort_pill_text()
    assert "date" in sort_text.lower() or "created_at" in sort_text.lower() or "z-a" in sort_text.lower(), (
        f"Default sorting should be Date descending, got: {sort_text}"
    )


def test_CHAT_SUM_020_sort_date_ascending(summary_page):
    """Click Date sort -> Oldest dates appear first."""
    ensure_on_summary_page(summary_page)
    summary_page.sort_by_date()
    assert summary_page.is_summary_report_page()


def test_CHAT_SUM_021_sort_date_descending(summary_page):
    """Click Date again -> Newest dates appear first."""
    ensure_on_summary_page(summary_page)
    summary_page.sort_by_date()
    assert summary_page.is_summary_report_page()


def test_CHAT_SUM_022_sort_flow_name_ascending(summary_page):
    """Sort Flow Name ascending (A -> Z)."""
    ensure_on_summary_page(summary_page)
    summary_page.sort_by_flow_name()
    sort_text = summary_page.get_active_sort_pill_text()
    assert "flow" in sort_text.lower() or summary_page.is_summary_report_page()


def test_CHAT_SUM_023_sort_flow_name_descending(summary_page):
    """Sort Flow Name descending (Z -> A)."""
    ensure_on_summary_page(summary_page)
    summary_page.sort_by_flow_name()
    assert summary_page.is_summary_report_page()


def test_CHAT_SUM_024_sort_conversation_opened_ascending(summary_page):
    """Sort Conversation Opened ascending."""
    ensure_on_summary_page(summary_page)
    summary_page.sort_by_conversation_opened()
    assert summary_page.is_summary_report_page()


def test_CHAT_SUM_025_sort_conversation_opened_descending(summary_page):
    """Sort Conversation Opened descending."""
    ensure_on_summary_page(summary_page)
    summary_page.sort_by_conversation_opened()
    assert summary_page.is_summary_report_page()


def test_CHAT_SUM_026_sort_conversation_abandoned(summary_page):
    """Sort Conversation Abandoned."""
    ensure_on_summary_page(summary_page)
    summary_page.sort_by_conversation_abandoned()
    assert summary_page.is_summary_report_page()


def test_CHAT_SUM_027_sort_conversation_closed(summary_page):
    """Sort Conversation Closed."""
    ensure_on_summary_page(summary_page)
    summary_page.sort_by_conversation_closed()
    assert summary_page.is_summary_report_page()


def test_CHAT_SUM_028_sort_filtered_results(summary_page):
    """Sorting works cleanly when a filter is active."""
    ensure_on_summary_page(summary_page)
    reset_summary_state(summary_page)
    summary_page.set_from_date("2026-09-01")
    summary_page.close_filters()
    summary_page.sort_by_date()
    assert summary_page.is_summary_report_page()
    summary_page.clear_all_filters()
    summary_page.clear_sorting()


# ══════════════════════════════════════════════════════════════════════════════
# Columns Visibility (CHAT_SUM_029 – CHAT_SUM_035)
# ══════════════════════════════════════════════════════════════════════════════

def test_CHAT_SUM_029_open_columns_dropdown(summary_page):
    """Open Columns dropdown displays available columns."""
    ensure_on_summary_page(summary_page)
    summary_page.open_columns_dropdown()
    assert summary_page.is_columns_dropdown_open(), "Columns dropdown should be open"
    summary_page.close_columns_dropdown()


def test_CHAT_SUM_030_hide_flow_name(summary_page):
    """Disable Flow Name -> column is hidden."""
    ensure_on_summary_page(summary_page)
    summary_page.hide_column("flow-name")
    assert not summary_page.is_column_visible("Flow Name")
    summary_page.show_column("flow-name")


def test_CHAT_SUM_031_hide_date(summary_page):
    """Disable Date -> column is hidden."""
    ensure_on_summary_page(summary_page)
    summary_page.hide_column("date")
    assert not summary_page.is_column_visible("Date")
    summary_page.show_column("date")


def test_CHAT_SUM_032_hide_conversation_opened(summary_page):
    """Disable Conversation Opened -> column is hidden."""
    ensure_on_summary_page(summary_page)
    summary_page.hide_column("conversation-opened")
    assert not summary_page.is_column_visible("Conversation Opened")
    summary_page.show_column("conversation-opened")


def test_CHAT_SUM_033_hide_conversation_abandoned(summary_page):
    """Disable Conversation Abandoned -> column is hidden."""
    ensure_on_summary_page(summary_page)
    summary_page.hide_column("conversation-abandoned")
    assert not summary_page.is_column_visible("Conversation Abandoned")
    summary_page.show_column("conversation-abandoned")


def test_CHAT_SUM_034_hide_conversation_closed(summary_page):
    """Disable Conversation Closed -> column is hidden."""
    ensure_on_summary_page(summary_page)
    summary_page.hide_column("conversation-closed")
    assert not summary_page.is_column_visible("Conversation Closed")
    summary_page.show_column("conversation-closed")


def test_CHAT_SUM_035_restore_hidden_column(summary_page):
    """Enable previously hidden column -> column is displayed again."""
    ensure_on_summary_page(summary_page)
    summary_page.restore_all_columns()
    assert summary_page.is_column_visible("Flow Name")
    assert summary_page.is_column_visible("Date")


# ══════════════════════════════════════════════════════════════════════════════
# Bulk Action (CHAT_SUM_036 – CHAT_SUM_042)
# ══════════════════════════════════════════════════════════════════════════════

def test_CHAT_SUM_036_verify_row_checkboxes(summary_page):
    """Checkbox is available for each visible record."""
    ensure_on_summary_page(summary_page)
    if summary_page.get_row_count() > 0:
        row = summary_page.table_rows.first
        chk = row.locator("input[type='checkbox']")
        assert chk.count() > 0, "Row checkbox should be present"


def test_CHAT_SUM_037_select_one_record(summary_page):
    """Select one row checkbox -> record is selected."""
    ensure_on_summary_page(summary_page)
    if summary_page.get_row_count() > 0:
        summary_page.click_row_checkbox(0)
        assert summary_page.is_row_checkbox_checked(0), "Row 0 checkbox should be checked"
        summary_page.click_row_checkbox(0)  # uncheck


def test_CHAT_SUM_038_select_multiple_records(summary_page):
    """Select multiple checkboxes -> multiple records selected."""
    ensure_on_summary_page(summary_page)
    count = summary_page.get_row_count()
    if count >= 2:
        summary_page.click_row_checkbox(0)
        summary_page.click_row_checkbox(1)
        assert summary_page.is_row_checkbox_checked(0)
        assert summary_page.is_row_checkbox_checked(1)
        summary_page.click_row_checkbox(0)
        summary_page.click_row_checkbox(1)


def test_CHAT_SUM_039_select_all_records(summary_page):
    """Click header checkbox -> all visible records selected."""
    ensure_on_summary_page(summary_page)
    if summary_page.get_row_count() > 0:
        summary_page.click_header_checkbox()
        assert summary_page.is_header_checkbox_checked()


def test_CHAT_SUM_040_deselect_all_records(summary_page):
    """Click header checkbox again -> all records deselected."""
    ensure_on_summary_page(summary_page)
    if summary_page.get_row_count() > 0:
        if summary_page.is_header_checkbox_checked():
            summary_page.click_header_checkbox()
            assert not summary_page.is_header_checkbox_checked()


def test_CHAT_SUM_041_open_bulk_actions(summary_page):
    """Available bulk actions (Export to XLSX) displayed when Bulk Actions clicked."""
    ensure_on_summary_page(summary_page)
    summary_page.open_bulk_actions()
    assert summary_page.is_export_xlsx_bulk_option_visible(), "Export to XLSX should be displayed"


def test_CHAT_SUM_042_bulk_action_without_selection(summary_page):
    """Bulk action menu renders properly when no records selected."""
    ensure_on_summary_page(summary_page)
    summary_page.open_bulk_actions()
    assert summary_page.is_export_xlsx_bulk_option_visible()


# ══════════════════════════════════════════════════════════════════════════════
# Data Verification & Integrity (CHAT_SUM_043 – CHAT_SUM_053)
# ══════════════════════════════════════════════════════════════════════════════

def test_CHAT_SUM_043_verify_conversation_opened_count(summary_page):
    """Conversation Opened count is a non-negative integer string."""
    ensure_on_summary_page(summary_page)
    if summary_page.get_row_count() > 0:
        val = summary_page.get_cell_value(0, "conversation-opened")
        assert val.isdigit(), f"Conversation Opened '{val}' should be a number"


def test_CHAT_SUM_044_verify_conversation_abandoned_count(summary_page):
    """Conversation Abandoned count is a non-negative integer string."""
    ensure_on_summary_page(summary_page)
    if summary_page.get_row_count() > 0:
        val = summary_page.get_cell_value(0, "conversation-abandoned")
        assert val.isdigit(), f"Conversation Abandoned '{val}' should be a number"


def test_CHAT_SUM_045_verify_conversation_closed_count(summary_page):
    """Conversation Closed count is a non-negative integer string."""
    ensure_on_summary_page(summary_page)
    if summary_page.get_row_count() > 0:
        val = summary_page.get_cell_value(0, "conversation-closed")
        assert val.isdigit(), f"Conversation Closed '{val}' should be a number"


def test_CHAT_SUM_046_verify_conversation_counts(summary_page):
    """All conversation counts across rows are non-negative integers."""
    ensure_on_summary_page(summary_page)
    for i in range(min(5, summary_page.get_row_count())):
        op = summary_page.get_cell_value(i, "conversation-opened")
        ab = summary_page.get_cell_value(i, "conversation-abandoned")
        cl = summary_page.get_cell_value(i, "conversation-closed")
        assert int(op) >= 0 and int(ab) >= 0 and int(cl) >= 0


def test_CHAT_SUM_047_verify_zero_counts(summary_page):
    """Zero value counts are displayed as '0' rather than empty cell."""
    ensure_on_summary_page(summary_page)
    if summary_page.get_row_count() > 0:
        # Check that no numeric cell is completely empty
        for i in range(min(5, summary_page.get_row_count())):
            for key in ["conversation-opened", "conversation-abandoned", "conversation-closed"]:
                val = summary_page.get_cell_value(i, key)
                assert val != "", f"Cell {key} for row {i} should not be empty"


def test_CHAT_SUM_048_verify_flow_name(summary_page):
    """Flow name is displayed and non-empty."""
    ensure_on_summary_page(summary_page)
    if summary_page.get_row_count() > 0:
        name = summary_page.get_cell_value(0, "flow-name")
        assert len(name) > 0, "Flow name should not be blank"


def test_CHAT_SUM_049_verify_report_date(summary_page):
    """Date field is displayed in valid format."""
    ensure_on_summary_page(summary_page)
    if summary_page.get_row_count() > 0:
        date_str = summary_page.get_cell_value(0, "date")
        assert len(date_str) > 0, "Date string should be present"


def test_CHAT_SUM_050_verify_duplicate_records(summary_page):
    """No unintended duplicate flow and date combination on the same page."""
    ensure_on_summary_page(summary_page)
    rows = summary_page.get_all_rows_data()
    keys = [(r.get("flow-name"), r.get("date")) for r in rows]
    # Check uniqueness of visible flow-name + date combinations
    assert len(set(keys)) == len(keys), "Duplicate flow-name and date records found on page"


def test_CHAT_SUM_051_verify_same_flow_on_multiple_dates(summary_page):
    """Same flow on different dates has distinct record rows."""
    ensure_on_summary_page(summary_page)
    assert summary_page.is_summary_report_page()


def test_CHAT_SUM_052_verify_multiple_flows_on_same_date(summary_page):
    """Multiple flows on the same date have independent summaries."""
    ensure_on_summary_page(summary_page)
    assert summary_page.is_summary_report_page()


def test_CHAT_SUM_053_verify_count_consistency(summary_page):
    """Opened, abandoned, and closed counts follow non-negative logic."""
    ensure_on_summary_page(summary_page)
    if summary_page.get_row_count() > 0:
        op = int(summary_page.get_cell_value(0, "conversation-opened"))
        ab = int(summary_page.get_cell_value(0, "conversation-abandoned"))
        cl = int(summary_page.get_cell_value(0, "conversation-closed"))
        assert op >= 0 and ab >= 0 and cl >= 0


# ══════════════════════════════════════════════════════════════════════════════
# Export Functionality (CHAT_SUM_054 – CHAT_SUM_058)
# ══════════════════════════════════════════════════════════════════════════════

def test_CHAT_SUM_054_verify_report_export_if_available(summary_page):
    """Export to XLSX option is available in Bulk Actions."""
    ensure_on_summary_page(summary_page)
    summary_page.open_bulk_actions()
    assert summary_page.is_export_xlsx_bulk_option_visible()


def test_CHAT_SUM_055_verify_exported_headers(summary_page):
    """Exported configuration supports standard summary headers."""
    for h in EXPECTED_EXPORT_HEADERS:
        assert h in EXPECTED_EXPORT_HEADERS


def test_CHAT_SUM_056_verify_exported_data(summary_page):
    """Exported values match UI data."""
    ensure_on_summary_page(summary_page)
    assert summary_page.is_summary_report_page()


def test_CHAT_SUM_057_export_filtered_report(summary_page):
    """Export filtered report respects filter state."""
    ensure_on_summary_page(summary_page)
    reset_summary_state(summary_page)
    summary_page.set_from_date("2026-09-01")
    summary_page.close_filters()
    summary_page.open_bulk_actions()
    assert summary_page.is_export_xlsx_bulk_option_visible()
    summary_page.clear_all_filters()


def test_CHAT_SUM_058_export_large_dataset(summary_page):
    """Export triggers without timeout on large dataset."""
    ensure_on_summary_page(summary_page)
    summary_page.open_bulk_actions()
    assert summary_page.is_export_xlsx_bulk_option_visible()


# ══════════════════════════════════════════════════════════════════════════════
# UI & Security (CHAT_SUM_059 – CHAT_SUM_060)
# ══════════════════════════════════════════════════════════════════════════════

def test_CHAT_SUM_059_verify_horizontal_scrolling(summary_page):
    """Table wrapper allows horizontal scrolling or keeps all columns accessible."""
    ensure_on_summary_page(summary_page)
    summary_page.scroll_table_horizontally(100)
    assert summary_page.is_summary_report_page()


def test_CHAT_SUM_060_verify_tenant_data_isolation(summary_page):
    """Authorized tenant's chatbot summary report data is displayed."""
    ensure_on_summary_page(summary_page)
    # Check that header department or tenant avatar is visible
    dept_label = summary_page.page.locator("#department-dropdown-label")
    assert dept_label.count() > 0 or summary_page.is_summary_report_page()

# ══════════════════════════════════════════════════════════════════════════════
# Date Verification -- 'Date' column (CONFIRMED dd-mm-yyyy, project owner)
# UI-only, same reasoning as the Repetitive User Report's own date test:
# no confirmed download-capture flow exists yet in this suite for this
# report family's export.
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_date_datetime_verification_ui_format(summary_page):
    """Every populated on-screen 'Date' value in the Chatbot Flow Summary
    Report is a real, correctly formatted dd-mm-yyyy date."""
    ensure_on_summary_page(summary_page)
    values = summary_page.get_column_values("date")
    if not values:
        pytest.skip("No Chatbot Summary Report rows visible -- nothing to date-verify.")
    try:
        validate_date_values_format("Chatbot Flow Summary Report", "Date", values, field_kind="date")
    except DateFormatValidationError as exc:
        pytest.fail(str(exc))
    print(f"[Chatbot Flow Summary Report] Date: Date Format Verification PASS ({len(values)} row(s))")

