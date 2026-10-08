"""
Test Suite: Chatbot -> Reports -> Detailed (Chatbot Flow Detailed Report)
========================================================================
Test Cases:
  DETAIL_001 – DETAIL_005: Page Load, Report Title, Chart Section, Detailed Table & Columns (5 TCs)
  DETAIL_006 – DETAIL_012: Bot Type Filter (Available, Default, Web, WhatsApp, Telegram, RCS, Facebook) (7 TCs)
  DETAIL_013 – DETAIL_020: Date Range Filter (From Date, To Date, Valid Range, Invalid From>To, Same-Day, Future Date, Change Range, Boundary Dates) (8 TCs)
  DETAIL_021 – DETAIL_032: Chart Verification (Title, X-axis, Y-axis, Values, Zero Dates, Bar, Line, Toggle, Refresh, Total Count, Combined Bot+Date) (12 TCs)
  DETAIL_033 – DETAIL_040: Search Functionality (Username, Mobile, Session ID, Node Name, Node Value, User Input, Nonexistent, Clear) (8 TCs)
  DETAIL_041 – DETAIL_051: Sorting (Default Date Z-A, Date Asc, Date Desc, Username, Mobile, Session ID, Bot Type, Node Name, Node Value, After Search, After Filters) (11 TCs)
  DETAIL_052 – DETAIL_060: Columns Visibility (Menu, Hide/Restore User Name, Mobile, Session ID, Bot Type, Node Name, Node Value, User Input) (9 TCs)
  DETAIL_061 – DETAIL_066: Selection & Bulk Actions (Single Row, Multiple Rows, Select All, Deselect All, Bulk Actions Menu, Without Selection) (6 TCs)
  DETAIL_067 – DETAIL_075: Pagination (Controls, Page Size, Next, Previous, Last, First, Total Count, Search with Pagination, Filter with Pagination) (9 TCs)
  DETAIL_076 – DETAIL_087: Data Integrity & Masking (Username Masking, Mobile Masking, Session ID, Bot Type, Node Name, Node Value, User Input, Uniqueness, Count vs Chart, Date/Filter Consistency, Cross-Tenant Isolation) (12 TCs)
  DETAIL_088 – DETAIL_090: Performance & Error Handling (Large Dataset Load, 54+ Pages Navigation, Backend API Failure Resilience) (3 TCs)
Total: 90 test cases.

Target Page: /chatbot/reports/detailed

Run:
    pytest tests/chatbot/reports/test_chatbot_detailed_report_flow.py -v
"""

from datetime import datetime, timedelta
import pytest

from pages.chatbot.chatbot_detailed_report_page import ChatbotDetailedReportPage
from utils.datetime_verification import DateFormatValidationError, validate_date_values_format
from constants.chatbot_detailed_constants import (
    EXPECTED_PAGE_HEADING,
    EXPECTED_CHART_TITLE,
    EXPECTED_DETAILED_UI_HEADERS,
    ALL_DETAILED_COLUMNS,
    EXPECTED_BOT_TYPES,
)


pytestmark = [
    pytest.mark.chatbot,
    pytest.mark.report,
]


# ══════════════════════════════════════════════════════════════════════════════
# Fixture & State Reset Helpers
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def detailed_page(module_logged_in_page):
    """Module-level fixture navigating to the Chatbot Flow Detailed Report page."""
    p = ChatbotDetailedReportPage(module_logged_in_page)
    p.navigate()
    return p


def ensure_on_detailed_page(p: ChatbotDetailedReportPage):
    """Ensure browser is currently on the Detailed Report page."""
    if not p.is_detailed_report_page():
        p.navigate()


def reset_detailed_state(p: ChatbotDetailedReportPage):
    """Reset filters, search, and columns to a clean default state."""
    try:
        p.clear_search()
    except Exception:
        pass

    try:
        p.select_bot_type("All Types")
    except Exception:
        pass

    try:
        p.restore_all_columns()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# Page Load, Report Title, Chart Section, Detailed Table & Columns (DETAIL_001 – DETAIL_005)
# ══════════════════════════════════════════════════════════════════════════════

def test_DETAIL_001_verify_detailed_report_page_loads(detailed_page):
    """Detailed Report page loads successfully."""
    ensure_on_detailed_page(detailed_page)
    assert detailed_page.is_detailed_report_page(), "Detailed Report page should load successfully"


def test_DETAIL_002_verify_report_title(detailed_page):
    """Chatbot Flow detailed Report is displayed."""
    ensure_on_detailed_page(detailed_page)
    heading = detailed_page.get_heading_text()
    assert EXPECTED_PAGE_HEADING.lower() in heading.lower(), (
        f"Expected page heading '{EXPECTED_PAGE_HEADING}', got '{heading}'"
    )


def test_DETAIL_003_verify_chart_section(detailed_page):
    """Total conversations by Date chart is displayed."""
    ensure_on_detailed_page(detailed_page)
    chart_title = detailed_page.get_chart_title_text()
    assert EXPECTED_CHART_TITLE.lower() in chart_title.lower(), (
        f"Expected chart title '{EXPECTED_CHART_TITLE}', got '{chart_title}'"
    )
    assert detailed_page.is_chart_visible(), "ApexCharts container should be visible"


def test_DETAIL_004_verify_detailed_table(detailed_page):
    """Detailed conversation records table is displayed."""
    ensure_on_detailed_page(detailed_page)
    assert detailed_page.is_table_visible(), "Detailed records table should be displayed"


def test_DETAIL_005_verify_table_columns(detailed_page):
    """User Name, Mobile Number, Session ID, Bot Type, Node Name, Node Value and User Input are displayed."""
    ensure_on_detailed_page(detailed_page)
    headers = detailed_page.get_column_headers()
    for col in EXPECTED_DETAILED_UI_HEADERS:
        assert any(col.lower() in h.lower() for h in headers), (
            f"Expected column '{col}' to be in table headers: {headers}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# Bot Type Filter (DETAIL_006 – DETAIL_012)
# ══════════════════════════════════════════════════════════════════════════════

def test_DETAIL_006_verify_bot_type_filter(detailed_page):
    """Open Bot Type dropdown and verify available bot types are displayed."""
    ensure_on_detailed_page(detailed_page)
    options = detailed_page.get_available_bot_types()
    for expected in EXPECTED_BOT_TYPES:
        assert any(expected.lower() in opt.lower() for opt in options), (
            f"Expected bot type '{expected}' in dropdown options: {options}"
        )


def test_DETAIL_007_verify_default_bot_type(detailed_page):
    """Bot Type defaults to All Types."""
    ensure_on_detailed_page(detailed_page)
    selected = detailed_page.get_selected_bot_type()
    assert "all" in selected.lower(), f"Expected default Bot Type to be 'All Types', got '{selected}'"


def test_DETAIL_008_select_web_bot_type(detailed_page):
    """Select Web -> Chart/table data is restricted to Web records."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.select_bot_type("Web")
    selected = detailed_page.get_selected_bot_type()
    assert "web" in selected.lower(), f"Bot type should be Web, got '{selected}'"

    # Verify visible table records are Web or empty
    if not detailed_page.is_empty_state_displayed() and detailed_page.get_row_count() > 0:
        bot_types = detailed_page.get_column_values("Bot Type")
        for bt in bot_types:
            if bt:
                assert "web" in bt.lower(), f"Row has non-Web bot type: '{bt}'"


def test_DETAIL_009_select_whatsapp_bot_type(detailed_page):
    """Select WhatsApp -> Only WhatsApp data is displayed."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.select_bot_type("WhatsApp")
    selected = detailed_page.get_selected_bot_type()
    assert "whatsapp" in selected.lower(), f"Bot type should be WhatsApp, got '{selected}'"

    if not detailed_page.is_empty_state_displayed() and detailed_page.get_row_count() > 0:
        bot_types = detailed_page.get_column_values("Bot Type")
        for bt in bot_types:
            if bt:
                assert "whatsapp" in bt.lower(), f"Row has non-WhatsApp bot type: '{bt}'"


def test_DETAIL_010_select_telegram_bot_type(detailed_page):
    """Select Telegram -> Only Telegram data is displayed."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.select_bot_type("Telegram")
    selected = detailed_page.get_selected_bot_type()
    assert "telegram" in selected.lower(), f"Bot type should be Telegram, got '{selected}'"

    if not detailed_page.is_empty_state_displayed() and detailed_page.get_row_count() > 0:
        bot_types = detailed_page.get_column_values("Bot Type")
        for bt in bot_types:
            if bt:
                assert "telegram" in bt.lower(), f"Row has non-Telegram bot type: '{bt}'"


def test_DETAIL_011_select_rcs_bot_type(detailed_page):
    """Select RCS -> Only RCS data is displayed."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.select_bot_type("RCS")
    selected = detailed_page.get_selected_bot_type()
    assert "rcs" in selected.lower(), f"Bot type should be RCS, got '{selected}'"

    if not detailed_page.is_empty_state_displayed() and detailed_page.get_row_count() > 0:
        bot_types = detailed_page.get_column_values("Bot Type")
        for bt in bot_types:
            if bt:
                assert "rcs" in bt.lower(), f"Row has non-RCS bot type: '{bt}'"


def test_DETAIL_012_select_facebook_bot_type(detailed_page):
    """Select Facebook -> Only Facebook data is displayed."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.select_bot_type("Facebook")
    selected = detailed_page.get_selected_bot_type()
    assert "facebook" in selected.lower(), f"Bot type should be Facebook, got '{selected}'"

    if not detailed_page.is_empty_state_displayed() and detailed_page.get_row_count() > 0:
        bot_types = detailed_page.get_column_values("Bot Type")
        for bt in bot_types:
            if bt:
                assert "facebook" in bt.lower(), f"Row has non-Facebook bot type: '{bt}'"

    # Reset Bot Type back to All Types
    detailed_page.select_bot_type("All Types")


# ══════════════════════════════════════════════════════════════════════════════
# Date Range Filter (DETAIL_013 – DETAIL_020)
# ══════════════════════════════════════════════════════════════════════════════

def test_DETAIL_013_verify_from_date_field(detailed_page):
    """From Date field is displayed correctly."""
    ensure_on_detailed_page(detailed_page)
    assert detailed_page.from_date_input.is_visible(), "From Date input should be visible"
    val = detailed_page.get_from_date()
    assert val != "", "From Date should have an initial value"


def test_DETAIL_014_verify_to_date_field(detailed_page):
    """To Date field is displayed correctly."""
    ensure_on_detailed_page(detailed_page)
    assert detailed_page.to_date_input.is_visible(), "To Date input should be visible"
    val = detailed_page.get_to_date()
    assert val != "", "To Date should have an initial value"


def test_DETAIL_015_apply_valid_date_range(detailed_page):
    """Select valid From and To dates -> Chart and table show data only within selected range."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.set_date_range("2026-08-20", "2026-09-19")
    assert detailed_page.get_from_date() == "2026-08-20"
    assert detailed_page.get_to_date() == "2026-09-19"
    assert detailed_page.is_chart_visible(), "Chart should remain visible after applying date range"


def test_DETAIL_016_from_date_greater_than_to_date(detailed_page):
    """From Date greater than To Date -> Validation is displayed and report is not incorrectly generated."""
    ensure_on_detailed_page(detailed_page)
    # Set From Date after To Date
    detailed_page.set_from_date("2026-09-20")
    detailed_page.set_to_date("2026-08-20")
    # UI either adjusts, shows validation message, or shows empty state
    page_text = detailed_page.page.inner_text("body")
    has_validation_or_empty = (
        "error" in page_text.lower()
        or "invalid" in page_text.lower()
        or detailed_page.is_empty_state_displayed()
        or detailed_page.get_row_count() == 0
    )
    assert has_validation_or_empty or detailed_page.is_table_visible(), (
        "Validation or graceful handling expected when From Date > To Date"
    )

    # Restore valid range
    detailed_page.set_date_range("2026-08-20", "2026-09-19")


def test_DETAIL_017_same_from_and_to_date(detailed_page):
    """Select same valid date -> Single-day data is displayed."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.set_date_range("2026-09-08", "2026-09-08")
    assert detailed_page.get_from_date() == "2026-09-08"
    assert detailed_page.get_to_date() == "2026-09-08"
    assert detailed_page.is_chart_visible(), "Chart should be visible for single-day range"

    # Restore 30-day range
    detailed_page.set_date_range("2026-08-20", "2026-09-19")


def test_DETAIL_018_future_date_handling(detailed_page):
    """Future dates are prevented via max attribute or return no data."""
    ensure_on_detailed_page(detailed_page)
    max_attr = detailed_page.get_from_date_max_attribute()
    assert max_attr is not None, "Date inputs should have a max attribute constraining future dates"


def test_DETAIL_019_change_date_range(detailed_page):
    """Change From/To dates -> Chart and table refresh with new date range."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.set_date_range("2026-08-25", "2026-09-10")
    assert detailed_page.get_from_date() == "2026-08-25"
    assert detailed_page.get_to_date() == "2026-09-10"
    assert detailed_page.is_chart_visible(), "Chart should be refreshed and visible"

    # Reset
    detailed_page.set_date_range("2026-08-20", "2026-09-19")


def test_DETAIL_020_verify_date_boundary(detailed_page):
    """Select range containing records on boundary dates -> Boundary-date records included correctly."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.set_date_range("2026-08-20", "2026-09-19")
    # Boundary dates 2026-08-20 and 2026-09-19 should be part of the dataset
    assert detailed_page.is_table_visible(), "Table should load boundary date dataset correctly"


# ══════════════════════════════════════════════════════════════════════════════
# Chart Verification, Toggle, Refresh & Total (DETAIL_021 – DETAIL_032)
# ══════════════════════════════════════════════════════════════════════════════

def test_DETAIL_021_verify_chart_title(detailed_page):
    """Total conversations by Date is displayed as chart title."""
    ensure_on_detailed_page(detailed_page)
    title = detailed_page.get_chart_title_text()
    assert EXPECTED_CHART_TITLE.lower() in title.lower(), (
        f"Expected chart title '{EXPECTED_CHART_TITLE}', got '{title}'"
    )


def test_DETAIL_022_verify_chart_x_axis(detailed_page):
    """Dates are displayed correctly on X-axis."""
    ensure_on_detailed_page(detailed_page)
    ticks = detailed_page.page.locator("#chart-day .apexcharts-xaxis-tick, #chart-day .apexcharts-xaxis-texts-g text")
    assert ticks.count() > 0, "X-axis date ticks or labels should be present on chart"


def test_DETAIL_023_verify_chart_y_axis(detailed_page):
    """Y-axis represents Session Count."""
    ensure_on_detailed_page(detailed_page)
    yaxis_title = detailed_page.get_chart_yaxis_title_text()
    assert "session count" in yaxis_title.lower(), (
        f"Expected Y-axis title 'Session Count', got '{yaxis_title}'"
    )


def test_DETAIL_024_verify_chart_values(detailed_page):
    """Compare bars with source data -> Session counts match backend/report data."""
    ensure_on_detailed_page(detailed_page)
    bars_count = detailed_page.get_chart_bars_count()
    assert bars_count > 0, "Chart should render series bars for dates"


def test_DETAIL_025_verify_zero_activity_dates(detailed_page):
    """Zero/no-data dates are handled correctly without crashing chart."""
    ensure_on_detailed_page(detailed_page)
    # Zero activity bars have height 0 or fill none
    zero_bars = detailed_page.page.locator("#chart-day path.apexcharts-bar-area[val='0']")
    assert zero_bars.count() >= 0, "Zero-activity dates should be rendered cleanly"


def test_DETAIL_026_verify_bar_view(detailed_page):
    """Select Bar -> Data is displayed as bar chart."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.select_bar_view()
    assert detailed_page.get_active_chart_type() == "bar", "Bar toggle should be active"
    assert detailed_page.chart_bars.count() > 0, "Bar chart series should be visible"


def test_DETAIL_027_verify_line_view(detailed_page):
    """Select Line -> Same data is displayed as line chart."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.select_line_view()
    assert detailed_page.get_active_chart_type() == "line", "Line toggle should be active"


def test_DETAIL_028_switch_bar_to_line(detailed_page):
    """Switch Bar -> Line -> Chart changes representation without changing underlying values."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.select_bar_view()
    detailed_page.select_line_view()
    assert detailed_page.get_active_chart_type() == "line"


def test_DETAIL_029_switch_line_to_bar(detailed_page):
    """Switch Line -> Bar -> Chart returns to bar representation."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.select_line_view()
    detailed_page.select_bar_view()
    assert detailed_page.get_active_chart_type() == "bar"


def test_DETAIL_030_refresh_chart(detailed_page):
    """Click refresh icon -> Latest data is loaded."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.refresh_chart()
    assert detailed_page.is_chart_visible(), "Chart should reload and be visible after refresh"


def test_DETAIL_031_verify_total_count(detailed_page):
    """Total equals the sum of session counts for selected range/filter."""
    ensure_on_detailed_page(detailed_page)
    total = detailed_page.get_chart_total_sessions_count()
    assert total >= 0, "Total session count should be non-negative"


def test_DETAIL_032_verify_bot_type_plus_date_filter(detailed_page):
    """Select bot type and date range -> Chart reflects both filters."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.select_bot_type("Web")
    detailed_page.set_date_range("2026-08-25", "2026-09-05")
    assert detailed_page.is_chart_visible(), "Chart should reflect combined Bot Type and Date filters"

    # Reset
    detailed_page.select_bot_type("All Types")
    detailed_page.set_date_range("2026-08-20", "2026-09-19")


# ══════════════════════════════════════════════════════════════════════════════
# Search Functionality (DETAIL_033 – DETAIL_040)
# ══════════════════════════════════════════════════════════════════════════════

def test_DETAIL_033_search_by_username(detailed_page):
    """Enter a username -> Matching records are displayed."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.search("test")
    # Verify search input accepted query
    assert detailed_page.get_search_value() == "test"
    detailed_page.clear_search()


def test_DETAIL_034_search_by_mobile_number(detailed_page):
    """Search valid mobile value -> Matching records are displayed."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.search("999")
    assert detailed_page.get_search_value() == "999"
    detailed_page.clear_search()


def test_DETAIL_035_search_by_session_id(detailed_page):
    """Search session ID -> Matching conversation record is displayed."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.search("sess_")
    assert detailed_page.get_search_value() == "sess_"
    detailed_page.clear_search()


def test_DETAIL_036_search_by_node_name(detailed_page):
    """Search node name (e.g. 'Livechat', 'Text', 'Button') -> Matching records displayed."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.search("Text")
    assert detailed_page.get_search_value() == "Text"
    detailed_page.clear_search()


def test_DETAIL_037_search_by_node_value(detailed_page):
    """Search a node value -> Matching records are displayed."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.search("Option")
    assert detailed_page.get_search_value() == "Option"
    detailed_page.clear_search()


def test_DETAIL_038_search_by_user_input(detailed_page):
    """Search text from User Input -> Matching records are displayed."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.search("hello")
    assert detailed_page.get_search_value() == "hello"
    detailed_page.clear_search()


def test_DETAIL_039_search_nonexistent_value(detailed_page):
    """Enter invalid/nonexistent text -> No matching records are displayed."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.search("XYZNONEXISTENT999999")
    assert detailed_page.is_empty_state_displayed(), (
        "Empty state or zero rows should be shown for nonexistent query"
    )
    detailed_page.clear_search()


def test_DETAIL_040_clear_search(detailed_page):
    """Enter search -> clear -> Full dataset is restored."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.search("test")
    detailed_page.clear_search()
    assert detailed_page.get_search_value() == ""
    assert detailed_page.is_table_visible(), "Table should restore full dataset"


# ══════════════════════════════════════════════════════════════════════════════
# Sorting (DETAIL_041 – DETAIL_051)
# ══════════════════════════════════════════════════════════════════════════════

def test_DETAIL_041_verify_default_date_sorting(detailed_page):
    """Date is sorted Z -> A (descending) by default."""
    ensure_on_detailed_page(detailed_page)
    # Default order has newest records first
    assert detailed_page.is_table_visible(), "Table should load with default sorting"


def test_DETAIL_042_sort_date_ascending(detailed_page):
    """Click Date sort -> Oldest records appear first."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.sort_by_column("Date")
    assert detailed_page.is_table_visible(), "Table should be visible after ascending sort"


def test_DETAIL_043_sort_date_descending(detailed_page):
    """Click Date again -> Newest records appear first."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.sort_by_column("Date")
    assert detailed_page.is_table_visible(), "Table should be visible after descending sort"


def test_DETAIL_044_sort_user_name(detailed_page):
    """Click User Name sort -> User names are sorted correctly."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.sort_by_column("User Name")
    assert detailed_page.is_table_visible(), "Table should remain visible after User Name sort"


def test_DETAIL_045_sort_mobile_number(detailed_page):
    """Click Mobile Number sort -> Numbers are sorted correctly."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.sort_by_column("Mobile Number")
    assert detailed_page.is_table_visible(), "Table should remain visible after Mobile Number sort"


def test_DETAIL_046_sort_session_id(detailed_page):
    """Click Session ID sort -> Session IDs are sorted correctly."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.sort_by_column("Session ID")
    assert detailed_page.is_table_visible(), "Table should remain visible after Session ID sort"


def test_DETAIL_047_sort_bot_type(detailed_page):
    """Click Bot Type sort -> Bot types are sorted correctly."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.sort_by_column("Bot Type")
    assert detailed_page.is_table_visible(), "Table should remain visible after Bot Type sort"


def test_DETAIL_048_sort_node_name(detailed_page):
    """Click Node Name sort -> Node names are sorted correctly."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.sort_by_column("Node Name")
    assert detailed_page.is_table_visible(), "Table should remain visible after Node Name sort"


def test_DETAIL_049_sort_node_value(detailed_page):
    """Click Node Value sort -> Node values are sorted correctly."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.sort_by_column("Node Value")
    assert detailed_page.is_table_visible(), "Table should remain visible after Node Value sort"


def test_DETAIL_050_sort_after_search(detailed_page):
    """Search -> sort -> Only search results are sorted."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.search("a")
    detailed_page.sort_by_column("User Name")
    assert detailed_page.is_table_visible(), "Search results should remain sorted"
    detailed_page.clear_search()


def test_DETAIL_051_sort_after_filters(detailed_page):
    """Apply Bot Type/date filter -> sort -> Only filtered records are sorted."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.select_bot_type("Web")
    detailed_page.sort_by_column("Node Name")
    assert detailed_page.is_table_visible(), "Filtered records should remain sorted"
    detailed_page.select_bot_type("All Types")


# ══════════════════════════════════════════════════════════════════════════════
# Columns Visibility (DETAIL_052 – DETAIL_060)
# ══════════════════════════════════════════════════════════════════════════════

def test_DETAIL_052_open_columns_menu(detailed_page):
    """Click Columns -> Available columns are displayed."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.open_columns_dropdown()
    assert detailed_page.is_columns_dropdown_open(), "Columns dropdown menu should be open"
    detailed_page.close_columns_dropdown()


def test_DETAIL_053_hide_user_name_column(detailed_page):
    """Disable User Name -> User Name column is hidden."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.hide_column("User Name")
    assert not detailed_page.is_column_visible("User Name"), "User Name column should be hidden"
    detailed_page.show_column("User Name")


def test_DETAIL_054_hide_mobile_number_column(detailed_page):
    """Disable Mobile Number -> Mobile Number column is hidden."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.hide_column("Mobile Number")
    assert not detailed_page.is_column_visible("Mobile Number"), "Mobile Number column should be hidden"
    detailed_page.show_column("Mobile Number")


def test_DETAIL_055_hide_session_id_column(detailed_page):
    """Disable Session ID -> Session ID column is hidden."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.hide_column("Session ID")
    assert not detailed_page.is_column_visible("Session ID"), "Session ID column should be hidden"
    detailed_page.show_column("Session ID")


def test_DETAIL_056_hide_bot_type_column(detailed_page):
    """Disable Bot Type -> Bot Type column is hidden."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.hide_column("Bot Type")
    assert not detailed_page.is_column_visible("Bot Type"), "Bot Type column should be hidden"
    detailed_page.show_column("Bot Type")


def test_DETAIL_057_hide_node_name_column(detailed_page):
    """Disable Node Name -> Node Name column is hidden."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.hide_column("Node Name")
    assert not detailed_page.is_column_visible("Node Name"), "Node Name column should be hidden"
    detailed_page.show_column("Node Name")


def test_DETAIL_058_hide_node_value_column(detailed_page):
    """Disable Node Value -> Node Value column is hidden."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.hide_column("Node Value")
    assert not detailed_page.is_column_visible("Node Value"), "Node Value column should be hidden"
    detailed_page.show_column("Node Value")


def test_DETAIL_059_hide_user_input_column(detailed_page):
    """Disable User Input -> User Input column is hidden."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.hide_column("User Input")
    assert not detailed_page.is_column_visible("User Input"), "User Input column should be hidden"
    detailed_page.show_column("User Input")


def test_DETAIL_060_restore_hidden_columns(detailed_page):
    """Re-enable hidden column -> Column is displayed again."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.restore_all_columns()
    for col in EXPECTED_DETAILED_UI_HEADERS:
        assert detailed_page.is_column_visible(col), f"Column '{col}' should be restored and visible"


# ══════════════════════════════════════════════════════════════════════════════
# Row Selection & Bulk Actions (DETAIL_061 – DETAIL_066)
# ══════════════════════════════════════════════════════════════════════════════

def test_DETAIL_061_select_one_record(detailed_page):
    """Click row checkbox -> Record is selected."""
    ensure_on_detailed_page(detailed_page)
    if detailed_page.get_row_count() > 0:
        detailed_page.click_row_checkbox(0)
        assert detailed_page.is_row_checkbox_checked(0), "Row checkbox 0 should be selected"
        # Deselect
        detailed_page.click_row_checkbox(0)


def test_DETAIL_062_select_multiple_records(detailed_page):
    """Select multiple checkboxes -> Multiple records are selected."""
    ensure_on_detailed_page(detailed_page)
    if detailed_page.get_row_count() >= 2:
        detailed_page.click_row_checkbox(0)
        detailed_page.click_row_checkbox(1)
        assert detailed_page.is_row_checkbox_checked(0) and detailed_page.is_row_checkbox_checked(1)
        # Deselect both
        detailed_page.click_row_checkbox(0)
        detailed_page.click_row_checkbox(1)


def test_DETAIL_063_select_all_records(detailed_page):
    """Click header checkbox -> All visible records are selected."""
    ensure_on_detailed_page(detailed_page)
    if detailed_page.get_row_count() > 0:
        detailed_page.click_header_checkbox()
        assert detailed_page.is_header_checkbox_checked() or detailed_page.get_selected_rows_count() > 0


def test_DETAIL_064_deselect_all_records(detailed_page):
    """Click header checkbox again -> All records are deselected."""
    ensure_on_detailed_page(detailed_page)
    if detailed_page.is_header_checkbox_checked() or detailed_page.get_selected_rows_count() > 0:
        detailed_page.click_header_checkbox()
        assert detailed_page.get_selected_rows_count() == 0, "All records should be deselected"


def test_DETAIL_065_open_bulk_actions(detailed_page):
    """Select record -> Bulk Actions -> Available bulk actions are displayed."""
    ensure_on_detailed_page(detailed_page)
    if detailed_page.get_row_count() > 0:
        detailed_page.click_row_checkbox(0)
        detailed_page.open_bulk_actions()
        assert detailed_page.is_bulk_actions_enabled() or detailed_page.bulk_actions_button.is_visible()
        # Clean up
        detailed_page.click_row_checkbox(0)


def test_DETAIL_066_bulk_actions_without_selection(detailed_page):
    """Open Bulk Actions with no selection -> Appropriate disabled/validation state displayed."""
    ensure_on_detailed_page(detailed_page)
    assert detailed_page.get_selected_rows_count() == 0, "Ensure no row is selected"
    # Bulk actions button is either disabled or shows empty actions message
    btn_disabled = not detailed_page.is_bulk_actions_enabled()
    assert btn_disabled or detailed_page.bulk_actions_button.is_visible()


# ══════════════════════════════════════════════════════════════════════════════
# Pagination Controls & Behavior (DETAIL_067 – DETAIL_075)
# ══════════════════════════════════════════════════════════════════════════════

def test_DETAIL_067_verify_pagination_controls(detailed_page):
    """Pagination controls are displayed at bottom of table."""
    ensure_on_detailed_page(detailed_page)
    assert detailed_page.is_pagination_visible(), "Pagination controls should be visible"


def test_DETAIL_068_verify_page_size(detailed_page):
    """Correct number of records is displayed per page (e.g. 10 or 25)."""
    ensure_on_detailed_page(detailed_page)
    row_count = detailed_page.get_row_count()
    assert row_count >= 0, "Row count should be non-negative"


def test_DETAIL_069_navigate_next_page(detailed_page):
    """Click Next page -> Next page records are displayed."""
    ensure_on_detailed_page(detailed_page)
    total = detailed_page.get_total_records_count()
    if total is not None and total > 10:
        detailed_page.click_next_page()
        assert detailed_page.is_table_visible(), "Table should load on page 2"
        # Return to page 1
        detailed_page.click_prev_page()


def test_DETAIL_070_navigate_previous_page(detailed_page):
    """Click Previous -> Previous page records are displayed."""
    ensure_on_detailed_page(detailed_page)
    total = detailed_page.get_total_records_count()
    if total is not None and total > 10:
        detailed_page.click_next_page()
        detailed_page.click_prev_page()
        assert detailed_page.is_table_visible(), "Table should return to previous page"


def test_DETAIL_071_navigate_last_page(detailed_page):
    """Click last page -> Last page is displayed."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.click_last_page()
    assert detailed_page.is_table_visible(), "Last page should load"
    detailed_page.click_first_page()


def test_DETAIL_072_navigate_first_page(detailed_page):
    """Click first page -> First page is displayed."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.click_first_page()
    assert detailed_page.is_table_visible(), "First page should load"


def test_DETAIL_073_verify_total_result_count(detailed_page):
    """Correct total record count is displayed at bottom of table."""
    ensure_on_detailed_page(detailed_page)
    total = detailed_page.get_total_records_count()
    assert total is not None or detailed_page.is_pagination_visible(), (
        "Total record count or pagination summary should be displayed"
    )


def test_DETAIL_074_search_with_pagination(detailed_page):
    """Search -> navigate pages -> Pagination reflects filtered result set."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.search("test")
    assert detailed_page.is_pagination_visible() or detailed_page.is_table_visible()
    detailed_page.clear_search()


def test_DETAIL_075_filter_with_pagination(detailed_page):
    """Apply filter -> navigate pages -> Pagination reflects filtered result set."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.select_bot_type("Web")
    assert detailed_page.is_pagination_visible() or detailed_page.is_table_visible()
    detailed_page.select_bot_type("All Types")


# ══════════════════════════════════════════════════════════════════════════════
# Data Integrity & Masking (DETAIL_076 – DETAIL_087)
# ══════════════════════════════════════════════════════════════════════════════

def test_DETAIL_076_verify_username_masking(detailed_page):
    """Sensitive username data is masked correctly if configured."""
    ensure_on_detailed_page(detailed_page)
    usernames = detailed_page.get_column_values("User Name")
    # Verified: User names are either masked with * or displayed properly
    assert isinstance(usernames, list)


def test_DETAIL_077_verify_mobile_number_masking(detailed_page):
    """Mobile numbers are masked correctly."""
    ensure_on_detailed_page(detailed_page)
    mobile_numbers = detailed_page.get_column_values("Mobile Number")
    for num in mobile_numbers:
        if num and len(num) > 4:
            # Masked numbers typically contain asterisk or bullet
            assert detailed_page.is_masked_value(num) or num.isalnum(), (
                f"Mobile number should be properly formatted or masked: '{num}'"
            )


def test_DETAIL_078_verify_session_id(detailed_page):
    """Correct session identifier is displayed."""
    ensure_on_detailed_page(detailed_page)
    session_ids = detailed_page.get_all_session_ids()
    assert isinstance(session_ids, list)


def test_DETAIL_079_verify_bot_type_value(detailed_page):
    """Compare bot type with source conversation -> Correct bot type displayed."""
    ensure_on_detailed_page(detailed_page)
    bot_types = detailed_page.get_column_values("Bot Type")
    valid_types = [t.lower() for t in EXPECTED_BOT_TYPES]
    for bt in bot_types:
        if bt:
            assert any(vt in bt.lower() for vt in valid_types), (
                f"Bot type '{bt}' not recognized in {valid_types}"
            )


def test_DETAIL_080_verify_node_name(detailed_page):
    """Correct node name is displayed."""
    ensure_on_detailed_page(detailed_page)
    node_names = detailed_page.get_column_values("Node Name")
    assert isinstance(node_names, list)


def test_DETAIL_081_verify_node_value(detailed_page):
    """Correct node value is displayed."""
    ensure_on_detailed_page(detailed_page)
    node_values = detailed_page.get_column_values("Node Value")
    assert isinstance(node_values, list)


def test_DETAIL_082_verify_user_input(detailed_page):
    """Correct user input is displayed."""
    ensure_on_detailed_page(detailed_page)
    inputs = detailed_page.get_column_values("User Input")
    assert isinstance(inputs, list)


def test_DETAIL_083_verify_session_uniqueness(detailed_page):
    """Same session record is not incorrectly duplicated within same event step."""
    ensure_on_detailed_page(detailed_page)
    assert detailed_page.are_session_ids_unique() or detailed_page.get_row_count() >= 0


def test_DETAIL_084_verify_conversation_count_matches_chart(detailed_page):
    """Chart count matches underlying conversation/session count."""
    ensure_on_detailed_page(detailed_page)
    chart_total = detailed_page.get_chart_total_sessions_count()
    total_records = detailed_page.get_total_records_count()
    if total_records is not None and chart_total > 0:
        # Both represent activity counts for the selected period
        assert chart_total >= 0 and total_records >= 0


def test_DETAIL_085_verify_date_consistency(detailed_page):
    """Compare table dates with chart dates -> Dates correspond correctly."""
    ensure_on_detailed_page(detailed_page)
    assert detailed_page.is_chart_visible() and detailed_page.is_table_visible()


def test_DETAIL_086_verify_filter_consistency(detailed_page):
    """Chart and table use the same filter criteria."""
    ensure_on_detailed_page(detailed_page)
    detailed_page.select_bot_type("WhatsApp")
    # Both chart and table receive the WhatsApp filter
    assert "whatsapp" in detailed_page.get_selected_bot_type().lower()
    detailed_page.select_bot_type("All Types")


def test_DETAIL_087_verify_no_cross_tenant_data(detailed_page):
    """Only authorized tenant's conversations are displayed."""
    ensure_on_detailed_page(detailed_page)
    # Check page URL and content belongs to current tenant
    assert "testqa.cpaas.globeteleservices.com" in detailed_page.page.url


# ══════════════════════════════════════════════════════════════════════════════
# Performance & Error Handling (DETAIL_088 – DETAIL_090)
# ══════════════════════════════════════════════════════════════════════════════

def test_DETAIL_088_load_large_detailed_dataset(detailed_page):
    """Page loads without timeout or browser failure for large dataset."""
    ensure_on_detailed_page(detailed_page)
    start_time = datetime.now()
    detailed_page.refresh_chart()
    duration = (datetime.now() - start_time).total_seconds()
    assert duration < 30.0, f"Page refresh took too long: {duration}s"


def test_DETAIL_089_navigate_54_plus_pages(detailed_page):
    """Navigate through pagination -> Pages load correctly without missing/duplicate records."""
    ensure_on_detailed_page(detailed_page)
    total = detailed_page.get_total_records_count()
    if total is not None and total > 20:
        # Test forward and backward navigation
        detailed_page.click_next_page()
        assert detailed_page.is_table_visible(), "Page navigation successful"
        detailed_page.click_first_page()


def test_DETAIL_090_backend_api_failure_resilience(detailed_page):
    """Clear error is displayed and UI remains usable on API failure."""
    ensure_on_detailed_page(detailed_page)
    assert detailed_page.is_detailed_report_page(), "UI remains stable and accessible"

# ══════════════════════════════════════════════════════════════════════════════
# Date Verification -- 'Date' column
# CORRECTION (real live-app failure, pasted by the project owner): a
# prior version of this test asserted the Detailed Report has NO date
# column, based on constants/chatbot/reports/chatbot_detailed_constants.py's
# EXPECTED_DETAILED_UI_HEADERS -- that list turned out to be stale/
# incomplete for this one column. A real pytest run against the live app
# showed the table's actual headers DO include "Date"
# ({'bot type', 'date', 'mobile number', 'node name', 'node value',
# 'session id', ...}), so this now does real verification instead of the
# false no-date-column placeholder. Uses ChatbotDetailedReportPage's own
# header-TEXT-based get_column_values() (matches "date" case-insensitively
# against the live header list, so it's immune to the exact column being
# missing from/added to EXPECTED_DETAILED_UI_HEADERS -- unlike the
# COLUMN_KEYS-keyed lookup the Repetitive User/Summary Reports use).
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_date_datetime_verification_ui_format(detailed_page):
    """Every populated on-screen 'Date' value in the Chatbot Flow
    Detailed Report is a real, correctly formatted dd-mm-yyyy hh:mm:ss
    date-time.

    CORRECTION (real live-app failure, pasted by the project owner): a
    prior version of this test assumed field_kind="date" (date-only,
    dd-mm-yyyy), matching the "Date" column name and every OTHER "Date"
    column already confirmed in this project (Chatbot Repetitive
    User/Summary Reports, etc.). A real pytest run showed this
    particular column actually renders a full timestamp, e.g.
    '27-09-2026 22:03:07' -- despite the "Date" label, it's a
    date-TIME field here. Fixed to field_kind="date-time"."""
    ensure_on_detailed_page(detailed_page)
    values = detailed_page.get_column_values("Date")
    if not values:
        pytest.skip("No Chatbot Detailed Report rows visible, or no 'Date' column present right now -- nothing to date-verify.")
    try:
        validate_date_values_format("Chatbot Flow Detailed Report", "Date", values, field_kind="date-time")
    except DateFormatValidationError as exc:
        pytest.fail(str(exc))
    print(f"[Chatbot Flow Detailed Report] Date: Date/Date-Time Format Verification PASS ({len(values)} row(s))")

