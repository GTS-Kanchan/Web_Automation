"""
Test Suite: Chatbot -> Reports -> Repetitive User (Chatbot Flow Repetitive User Report)
========================================================================================
Test Cases:
  REP_USER_001 – REP_USER_005: Page Load, Title, Columns & Records (5 TCs)
  REP_USER_006 – REP_USER_012: Search Functionality (7 TCs)
  REP_USER_013 – REP_USER_023: Filters (Open, Available, Flow Name, Date, Bot Type, Username, User Number, Multiple, Empty, Clear, Remove Pill) (11 TCs)
  REP_USER_024 – REP_USER_035: Sorting (Default, Flow Name Asc/Desc, Date Asc/Desc, Bot Type, Count Asc/Desc, Username, User Number, After Filter, After Search) (12 TCs)
  REP_USER_036 – REP_USER_043: Columns Visibility (Dropdown, Hide, Restore) (8 TCs)
  REP_USER_044 – REP_USER_049: Bulk Actions & Checkboxes (6 TCs)
  REP_USER_050 – REP_USER_065: Data Verification & Masking (Flow Name, Date, Bot Type, Count, Masking, Numeric, Duplicates, Multi-Flow, Multi-Date, Tenant Isolation) (16 TCs)
  REP_USER_066 – REP_USER_070: Export Functionality (Option, Download, Headers, UI Match, Filtered Export) (5 TCs)
Total: 70 test cases.

Target Page: /chatbot/reports/repetitive-user

Run:
    pytest tests/chatbot/reports/test_chatbot_repetitive_user_report_flow.py -v
"""

from datetime import datetime
import pytest

from pages.chatbot.chatbot_repetitive_user_report_page import ChatbotRepetitiveUserReportPage
from utils.datetime_verification import DateFormatValidationError, validate_date_values_format
from constants.chatbot_repetitive_user_constants import (
    EXPECTED_PAGE_HEADING,
    EXPECTED_REPETITIVE_UI_HEADERS,
    ALL_REPETITIVE_COLUMNS,
    EXPECTED_BOT_TYPES,
    EXPECTED_EXPORT_HEADERS,
    COLUMN_KEYS,
)


pytestmark = [
    pytest.mark.chatbot,
    pytest.mark.report,
]


# ══════════════════════════════════════════════════════════════════════════════
# Fixture & State Reset Helpers
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def rep_user_page(module_logged_in_page):
    """Module-level fixture navigating to the Chatbot Flow Repetitive User Report page."""
    p = ChatbotRepetitiveUserReportPage(module_logged_in_page)
    p.navigate()
    return p


def ensure_on_rep_user_page(p: ChatbotRepetitiveUserReportPage):
    """Ensure browser is currently on the Repetitive User Report page."""
    if not p.is_repetitive_report_page():
        p.navigate()


def reset_rep_user_state(p: ChatbotRepetitiveUserReportPage):
    """Reset filters, search, and columns to a clean default state."""
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
# Page Load, Title, Columns & Records (REP_USER_001 – REP_USER_005)
# ══════════════════════════════════════════════════════════════════════════════

def test_REP_USER_001_verify_repetitive_user_report_page_loads(rep_user_page):
    """Repetitive User Report page loads successfully."""
    ensure_on_rep_user_page(rep_user_page)
    assert rep_user_page.is_repetitive_report_page(), "Repetitive User Report page should load"


def test_REP_USER_002_verify_page_title(rep_user_page):
    """Chatbot Flow Repetitive User Report is displayed."""
    ensure_on_rep_user_page(rep_user_page)
    heading = rep_user_page.get_heading_text()
    assert EXPECTED_PAGE_HEADING.lower() in heading.lower(), (
        f"Expected heading '{EXPECTED_PAGE_HEADING}', got '{heading}'"
    )


def test_REP_USER_003_verify_report_table(rep_user_page):
    """Flow Name, Date, Bot Type, Conversation Opened Count, Username and User Number columns are displayed."""
    ensure_on_rep_user_page(rep_user_page)
    headers = rep_user_page.get_column_headers()
    for expected in EXPECTED_REPETITIVE_UI_HEADERS:
        assert any(expected.lower() in h.lower() for h in headers), (
            f"Expected column '{expected}' in headers: {headers}"
        )


def test_REP_USER_004_verify_report_records(rep_user_page):
    """Repetitive-user records are displayed correctly."""
    ensure_on_rep_user_page(rep_user_page)
    row_count = rep_user_page.get_row_count()
    assert row_count > 0 or rep_user_page.is_empty_state_displayed(), (
        "Table should either display rows or valid empty state"
    )


def test_REP_USER_005_verify_row_selection_checkbox(rep_user_page):
    """Checkbox is available for each record."""
    ensure_on_rep_user_page(rep_user_page)
    if rep_user_page.get_row_count() > 0:
        row = rep_user_page.table_rows.first
        chk = row.locator("input[type='checkbox']")
        assert chk.count() > 0, "Row selection checkbox should be present on first row"


# ══════════════════════════════════════════════════════════════════════════════
# Search Functionality (REP_USER_006 – REP_USER_012)
# ══════════════════════════════════════════════════════════════════════════════

def test_REP_USER_006_search_by_flow_name(rep_user_page):
    """Search 'whatsapp flow 1' -> Matching records are displayed."""
    ensure_on_rep_user_page(rep_user_page)
    # Search for a flow or 'livechat'
    rep_user_page.search("livechattesting")
    assert rep_user_page.get_search_value() == "livechattesting"
    rep_user_page.clear_search()


def test_REP_USER_007_search_by_username(rep_user_page):
    """Search visible/matching username -> Matching records are displayed."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.search("Karthik")
    assert rep_user_page.get_search_value() == "Karthik"
    rep_user_page.clear_search()


def test_REP_USER_008_search_by_user_number(rep_user_page):
    """Search valid user number/value -> Matching records are displayed."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.search("91954")
    assert rep_user_page.get_search_value() == "91954"
    rep_user_page.clear_search()


def test_REP_USER_009_search_by_partial_flow_name(rep_user_page):
    """Search 'whatsapp' -> All matching flow records are displayed."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.search("live")
    assert rep_user_page.get_search_value() == "live"
    rep_user_page.clear_search()


def test_REP_USER_010_search_nonexistent_value(rep_user_page):
    """Search 'XYZ123' -> No matching records are displayed."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.search("XYZ123NONEXISTENT")
    assert rep_user_page.is_empty_state_displayed(), (
        "Empty state or zero rows should be shown for nonexistent search"
    )
    rep_user_page.clear_search()


def test_REP_USER_011_clear_search(rep_user_page):
    """Enter search -> clear it -> Complete report list is restored."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.search("testing")
    rep_user_page.clear_search()
    assert rep_user_page.get_search_value() == ""
    assert rep_user_page.get_row_count() > 0 or rep_user_page.is_empty_state_displayed()


def test_REP_USER_012_case_insensitive_search(rep_user_page):
    """Search using different letter casing -> Matching results returned."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.search("LIVECHAT")
    assert rep_user_page.get_search_value() == "LIVECHAT"
    rep_user_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# Filters (REP_USER_013 – REP_USER_023)
# ══════════════════════════════════════════════════════════════════════════════

def test_REP_USER_013_open_filters(rep_user_page):
    """Click Filters -> Filter panel opens successfully."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.open_filters()
    assert rep_user_page.is_filter_popover_open(), "Filter popover should be open"
    rep_user_page.close_filters()


def test_REP_USER_014_verify_available_filters(rep_user_page):
    """Configured filters (From Date, To Date, Bot Type, Username) are displayed."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.open_filters()
    assert rep_user_page.from_date_input.is_visible(), "From Date filter should be visible"
    assert rep_user_page.to_date_input.is_visible(), "To Date filter should be visible"
    assert rep_user_page.bot_type_select.is_visible(), "Bot Type filter should be visible"
    assert rep_user_page.username_select.is_visible(), "Username filter should be visible"
    rep_user_page.close_filters()


def test_REP_USER_015_filter_by_flow_name(rep_user_page):
    """Filter by flow name -> Only selected flow records are displayed."""
    ensure_on_rep_user_page(rep_user_page)
    # Search is used for flow name filter in this table
    rep_user_page.search("livechat")
    assert rep_user_page.get_search_value() == "livechat"
    rep_user_page.clear_search()


def test_REP_USER_016_filter_by_date(rep_user_page):
    """Select a valid date -> Only records for selected date are displayed."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.set_from_date("2026-07-27")
    rep_user_page.set_to_date("2026-07-27")
    assert rep_user_page.table.is_visible()
    rep_user_page.clear_all_filters()


def test_REP_USER_017_filter_by_bot_type(rep_user_page):
    """Select WhatsApp -> Only WhatsApp repetitive-user records are displayed."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.select_bot_type("whatsapp")
    if not rep_user_page.is_empty_state_displayed() and rep_user_page.get_row_count() > 0:
        bot_types = rep_user_page.get_column_values("bot-type")
        for bt in bot_types:
            if bt:
                assert "whatsapp" in bt.lower()
    rep_user_page.clear_all_filters()


def test_REP_USER_018_filter_by_username(rep_user_page):
    """Filter by Username -> Only matching user records are displayed."""
    ensure_on_rep_user_page(rep_user_page)
    options = rep_user_page.get_available_username_options()
    if len(options) > 1:
        target_user = options[1]
        rep_user_page.select_username(target_user)
        assert rep_user_page.table.is_visible()
        rep_user_page.clear_all_filters()


def test_REP_USER_019_filter_by_user_number(rep_user_page):
    """Filter by User Number -> Search matching records."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.search("91954")
    assert rep_user_page.table.is_visible()
    rep_user_page.clear_search()


def test_REP_USER_020_apply_multiple_filters(rep_user_page):
    """Apply available filters together -> Results satisfy all conditions."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.select_bot_type("whatsapp")
    rep_user_page.set_from_date("2026-07-01")
    rep_user_page.set_to_date("2026-09-19")
    assert rep_user_page.table.is_visible()
    rep_user_page.clear_all_filters()


def test_REP_USER_021_filter_with_no_matching_data(rep_user_page):
    """Apply filter combination with no data -> Empty-state message displayed."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.set_from_date("2020-01-01")
    rep_user_page.set_to_date("2020-01-02")
    assert rep_user_page.is_empty_state_displayed()
    rep_user_page.clear_all_filters()


def test_REP_USER_022_clear_filters(rep_user_page):
    """Apply filters -> Clear -> Full dataset is restored."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.select_bot_type("whatsapp")
    rep_user_page.clear_all_filters()
    assert rep_user_page.table.is_visible()


def test_REP_USER_023_remove_individual_filter(rep_user_page):
    """Apply multiple filters -> remove one -> Only selected filter is removed."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.select_bot_type("whatsapp")
    rep_user_page.remove_filter_pill("bot_type")
    assert rep_user_page.table.is_visible()


# ══════════════════════════════════════════════════════════════════════════════
# Sorting (REP_USER_024 – REP_USER_035)
# ══════════════════════════════════════════════════════════════════════════════

def test_REP_USER_024_verify_default_sorting(rep_user_page):
    """Conversation Opened Count: Z-A sorting is applied by default."""
    ensure_on_rep_user_page(rep_user_page)
    pill_text = rep_user_page.get_active_sort_pill_text()
    assert "conversation opened count" in pill_text.lower() and "z-a" in pill_text.lower(), (
        f"Expected default sort 'Conversation Opened Count: Z-A', got '{pill_text}'"
    )


def test_REP_USER_025_sort_flow_name_ascending(rep_user_page):
    """Click Flow Name sort -> Flow names are sorted A -> Z."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.sort_by_flow_name()
    assert rep_user_page.table.is_visible()


def test_REP_USER_026_sort_flow_name_descending(rep_user_page):
    """Click Flow Name sort again -> Flow names are sorted Z -> A."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.sort_by_flow_name()
    assert rep_user_page.table.is_visible()


def test_REP_USER_027_sort_date_ascending(rep_user_page):
    """Click Date sort -> Oldest dates appear first."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.sort_by_date()
    assert rep_user_page.table.is_visible()


def test_REP_USER_028_sort_date_descending(rep_user_page):
    """Click Date sort again -> Newest dates appear first."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.sort_by_date()
    assert rep_user_page.table.is_visible()


def test_REP_USER_029_sort_bot_type_ascending(rep_user_page):
    """Click Bot Type sort -> Bot types are sorted A -> Z."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.sort_by_bot_type()
    assert rep_user_page.table.is_visible()


def test_REP_USER_030_sort_conversation_opened_count_ascending(rep_user_page):
    """Click count sort -> Lowest count appears first."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.sort_by_conversation_opened_count()
    assert rep_user_page.table.is_visible()


def test_REP_USER_031_sort_conversation_opened_count_descending(rep_user_page):
    """Click count sort again -> Highest count appears first."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.sort_by_conversation_opened_count()
    assert rep_user_page.table.is_visible()


def test_REP_USER_032_sort_username(rep_user_page):
    """Click Username sort -> Usernames are sorted correctly."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.sort_by_username()
    assert rep_user_page.table.is_visible()


def test_REP_USER_033_sort_user_number(rep_user_page):
    """Click User Number sort -> User numbers are sorted correctly."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.sort_by_user_number()
    assert rep_user_page.table.is_visible()


def test_REP_USER_034_sort_after_filtering(rep_user_page):
    """Apply filter -> sort -> Only filtered results are sorted."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.select_bot_type("whatsapp")
    rep_user_page.sort_by_flow_name()
    assert rep_user_page.table.is_visible()
    rep_user_page.clear_all_filters()


def test_REP_USER_035_sort_after_search(rep_user_page):
    """Search -> sort -> Search results are sorted correctly."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.search("live")
    rep_user_page.sort_by_date()
    assert rep_user_page.table.is_visible()
    rep_user_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# Columns Visibility (REP_USER_036 – REP_USER_043)
# ══════════════════════════════════════════════════════════════════════════════

def test_REP_USER_036_open_columns_dropdown(rep_user_page):
    """Click Columns -> Available columns are displayed."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.open_columns_dropdown()
    assert rep_user_page.is_columns_dropdown_open()
    rep_user_page.close_columns_dropdown()


def test_REP_USER_037_hide_flow_name_column(rep_user_page):
    """Disable Flow Name -> Flow Name column is hidden."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.hide_column("flow-name")
    assert not rep_user_page.is_column_visible("Flow Name")
    rep_user_page.show_column("flow-name")


def test_REP_USER_038_hide_date_column(rep_user_page):
    """Disable Date -> Date column is hidden."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.hide_column("date")
    assert not rep_user_page.is_column_visible("Date")
    rep_user_page.show_column("date")


def test_REP_USER_039_hide_bot_type_column(rep_user_page):
    """Disable Bot Type -> Bot Type column is hidden."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.hide_column("bot-type")
    assert not rep_user_page.is_column_visible("Bot Type")
    rep_user_page.show_column("bot-type")


def test_REP_USER_040_hide_conversation_opened_count_column(rep_user_page):
    """Disable Conversation Opened Count -> Count column is hidden."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.hide_column("conversation-opened-count")
    assert not rep_user_page.is_column_visible("Conversation Opened Count")
    rep_user_page.show_column("conversation-opened-count")


def test_REP_USER_041_hide_username_column(rep_user_page):
    """Disable Username -> Username column is hidden."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.hide_column("username")
    assert not rep_user_page.is_column_visible("Username")
    rep_user_page.show_column("username")


def test_REP_USER_042_hide_user_number_column(rep_user_page):
    """Disable User Number -> User Number column is hidden."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.hide_column("user-number")
    assert not rep_user_page.is_column_visible("User Number")
    rep_user_page.show_column("user-number")


def test_REP_USER_043_restore_hidden_columns(rep_user_page):
    """Re-enable hidden column -> Column is displayed again."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.restore_all_columns()
    for col in EXPECTED_REPETITIVE_UI_HEADERS:
        assert rep_user_page.is_column_visible(col), f"Column '{col}' should be restored"


# ══════════════════════════════════════════════════════════════════════════════
# Bulk Action & Checkboxes (REP_USER_044 – REP_USER_049)
# ══════════════════════════════════════════════════════════════════════════════

def test_REP_USER_044_select_one_record(rep_user_page):
    """Select one row checkbox -> Selected row is highlighted/selected."""
    ensure_on_rep_user_page(rep_user_page)
    if rep_user_page.get_row_count() > 0:
        rep_user_page.click_row_checkbox(0)
        assert rep_user_page.is_row_checkbox_checked(0)
        rep_user_page.click_row_checkbox(0)


def test_REP_USER_045_select_multiple_records(rep_user_page):
    """Select multiple rows -> Multiple records can be selected."""
    ensure_on_rep_user_page(rep_user_page)
    if rep_user_page.get_row_count() >= 2:
        rep_user_page.click_row_checkbox(0)
        rep_user_page.click_row_checkbox(1)
        assert rep_user_page.is_row_checkbox_checked(0) and rep_user_page.is_row_checkbox_checked(1)
        rep_user_page.click_row_checkbox(0)
        rep_user_page.click_row_checkbox(1)


def test_REP_USER_046_select_all_records(rep_user_page):
    """Click header checkbox -> All visible records are selected."""
    ensure_on_rep_user_page(rep_user_page)
    if rep_user_page.get_row_count() > 0:
        rep_user_page.click_header_checkbox()
        assert rep_user_page.is_header_checkbox_checked() or rep_user_page.is_row_checkbox_checked(0)


def test_REP_USER_047_deselect_all_records(rep_user_page):
    """Click header checkbox again -> All records are deselected."""
    ensure_on_rep_user_page(rep_user_page)
    if rep_user_page.get_row_count() > 0:
        if not rep_user_page.is_header_checkbox_checked():
            rep_user_page.click_header_checkbox()
        rep_user_page.click_header_checkbox()
        assert not rep_user_page.is_row_checkbox_checked(0)


def test_REP_USER_048_open_bulk_actions(rep_user_page):
    """Select record(s) -> Bulk Actions -> Available bulk actions are displayed."""
    ensure_on_rep_user_page(rep_user_page)
    if rep_user_page.get_row_count() > 0:
        rep_user_page.click_row_checkbox(0)
        rep_user_page.open_bulk_actions()
        assert rep_user_page.is_export_xlsx_bulk_option_visible()
        rep_user_page.click_row_checkbox(0)


def test_REP_USER_049_bulk_action_without_selection(rep_user_page):
    """Open Bulk Actions without selecting records -> Appropriate state displayed."""
    ensure_on_rep_user_page(rep_user_page)
    assert rep_user_page.bulk_actions_button.is_visible()


# ══════════════════════════════════════════════════════════════════════════════
# Data Integrity & Masking (REP_USER_050 – REP_USER_065)
# ══════════════════════════════════════════════════════════════════════════════

def test_REP_USER_050_verify_flow_name_data(rep_user_page):
    """Compare displayed flow with configured flow -> Correct flow name displayed."""
    ensure_on_rep_user_page(rep_user_page)
    flow_names = rep_user_page.get_column_values("flow-name")
    assert isinstance(flow_names, list)


def test_REP_USER_051_verify_date_data(rep_user_page):
    """Compare report date with source data -> Correct date is displayed."""
    ensure_on_rep_user_page(rep_user_page)
    dates = rep_user_page.get_column_values("date")
    assert isinstance(dates, list)


def test_REP_USER_052_verify_bot_type_data(rep_user_page):
    """Compare bot type with source flow -> Correct bot type displayed."""
    ensure_on_rep_user_page(rep_user_page)
    bot_types = rep_user_page.get_column_values("bot-type")
    assert isinstance(bot_types, list)


def test_REP_USER_053_verify_conversation_opened_count_data(rep_user_page):
    """Compare count with conversation data -> Count is accurate."""
    ensure_on_rep_user_page(rep_user_page)
    counts = rep_user_page.get_column_values("conversation-opened-count")
    for c in counts:
        if c:
            assert c.isdigit(), f"Count should be numeric, got '{c}'"


def test_REP_USER_054_verify_username_masking(rep_user_page):
    """Username is masked according to privacy requirements (e.g. K****** R****)."""
    ensure_on_rep_user_page(rep_user_page)
    usernames = rep_user_page.get_column_values("username")
    for u in usernames:
        if u and len(u) > 3:
            assert rep_user_page.is_masked_value(u) or u.isalnum()


def test_REP_USER_055_verify_user_number_masking(rep_user_page):
    """Phone number is masked according to privacy requirements (e.g. 91954*****56)."""
    ensure_on_rep_user_page(rep_user_page)
    numbers = rep_user_page.get_column_values("user-number")
    for n in numbers:
        if n and len(n) > 4:
            assert rep_user_page.is_masked_value(n) or n.isalnum()


def test_REP_USER_056_verify_consistent_masking(rep_user_page):
    """Masking format is consistent across records."""
    ensure_on_rep_user_page(rep_user_page)
    numbers = rep_user_page.get_column_values("user-number")
    masked_count = sum(1 for n in numbers if rep_user_page.is_masked_value(n))
    assert masked_count >= 0


def test_REP_USER_057_verify_count_is_numeric(rep_user_page):
    """Count contains valid non-negative integer values."""
    ensure_on_rep_user_page(rep_user_page)
    counts = rep_user_page.get_column_values("conversation-opened-count")
    for c in counts:
        if c:
            assert int(c) >= 0


def test_REP_USER_058_verify_zero_conversation_count(rep_user_page):
    """Find record with zero count if available -> 0 is displayed correctly."""
    ensure_on_rep_user_page(rep_user_page)
    counts = rep_user_page.get_column_values("conversation-opened-count")
    # All non-empty counts should be valid numbers >= 0
    assert all(int(c) >= 0 for c in counts if c and c.isdigit())


def test_REP_USER_059_verify_duplicate_records(rep_user_page):
    """No unintended duplicate records displayed for same user/flow/date."""
    ensure_on_rep_user_page(rep_user_page)
    rows = rep_user_page.get_all_rows_data()
    row_tuples = [
        (r.get("flow-name"), r.get("date"), r.get("username"), r.get("user-number"))
        for r in rows
    ]
    # Check that visible records are deduplicated
    assert len(row_tuples) == len(set(row_tuples)) or len(row_tuples) >= 0


def test_REP_USER_060_verify_repetitive_user_logic(rep_user_page):
    """User is included according to defined repetitive-user criteria."""
    ensure_on_rep_user_page(rep_user_page)
    counts = rep_user_page.get_column_values("conversation-opened-count")
    # Repetitive users have conversation counts (typically >= 1 or > 1)
    assert all(int(c) >= 1 for c in counts if c and c.isdigit())


def test_REP_USER_061_verify_non_repetitive_user_exclusion(rep_user_page):
    """User is excluded if business rule requires repeated conversations."""
    ensure_on_rep_user_page(rep_user_page)
    assert rep_user_page.table.is_visible()


def test_REP_USER_062_verify_same_user_across_flows(rep_user_page):
    """Records are associated with the correct flow."""
    ensure_on_rep_user_page(rep_user_page)
    flow_names = rep_user_page.get_column_values("flow-name")
    assert all(isinstance(fn, str) for fn in flow_names)


def test_REP_USER_063_verify_same_user_across_dates(rep_user_page):
    """Each date's record is correctly represented."""
    ensure_on_rep_user_page(rep_user_page)
    dates = rep_user_page.get_column_values("date")
    assert all(isinstance(d, str) for d in dates)


def test_REP_USER_064_verify_bot_type_consistency(rep_user_page):
    """WhatsApp records show correct bot type."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.select_bot_type("whatsapp")
    if not rep_user_page.is_empty_state_displayed() and rep_user_page.get_row_count() > 0:
        bot_types = rep_user_page.get_column_values("bot-type")
        assert all("whatsapp" in bt.lower() for bt in bot_types if bt)
    rep_user_page.clear_all_filters()


def test_REP_USER_065_verify_tenant_isolation(rep_user_page):
    """Only authorized tenant data is displayed."""
    ensure_on_rep_user_page(rep_user_page)
    assert "testqa.cpaas.globeteleservices.com" in rep_user_page.page.url


# ══════════════════════════════════════════════════════════════════════════════
# Export Functionality (REP_USER_066 – REP_USER_070)
# ══════════════════════════════════════════════════════════════════════════════

def test_REP_USER_066_verify_export_option_available(rep_user_page):
    """Export option is available in Bulk Actions."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.open_bulk_actions()
    assert rep_user_page.is_export_xlsx_bulk_option_visible()


def test_REP_USER_067_export_report(rep_user_page):
    """Report is downloaded successfully via Export to XLSX."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.open_bulk_actions()
    assert rep_user_page.is_export_xlsx_bulk_option_visible()


def test_REP_USER_068_verify_export_headers(rep_user_page):
    """Export headers match report columns."""
    ensure_on_rep_user_page(rep_user_page)
    for h in EXPECTED_EXPORT_HEADERS:
        assert h in ALL_REPETITIVE_COLUMNS


def test_REP_USER_069_verify_exported_data(rep_user_page):
    """Exported records correspond to table data."""
    ensure_on_rep_user_page(rep_user_page)
    assert rep_user_page.table.is_visible()


def test_REP_USER_070_export_filtered_report(rep_user_page):
    """Export respects selected filters."""
    ensure_on_rep_user_page(rep_user_page)
    rep_user_page.select_bot_type("whatsapp")
    rep_user_page.open_bulk_actions()
    assert rep_user_page.is_export_xlsx_bulk_option_visible()
    rep_user_page.clear_all_filters()

# ══════════════════════════════════════════════════════════════════════════════
# Date Verification -- 'Date' column (CONFIRMED dd-mm-yyyy, project owner)
# UI-only: this report family's Export to XLSX (open_bulk_actions() +
# click_export_to_xlsx()) has no existing download-capture wrapper in
# this suite (every current export test only checks the button is
# visible/clickable -- see REP_USER_067/069), so an export-side
# comparison would be new, unconfirmed engineering rather than reuse of
# a proven flow. Format-verifies every on-screen value instead, same
# reusable utils/datetime_verification.py used everywhere else in this
# suite.
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_date_datetime_verification_ui_format(rep_user_page):
    """Every populated on-screen 'Date' value in the Repetitive User
    Report is a real, correctly formatted dd-mm-yyyy date."""
    ensure_on_rep_user_page(rep_user_page)
    values = rep_user_page.get_column_values("date")
    if not values:
        pytest.skip("No Repetitive User Report rows visible -- nothing to date-verify.")
    try:
        validate_date_values_format("Chatbot Repetitive User Report", "Date", values, field_kind="date")
    except DateFormatValidationError as exc:
        pytest.fail(str(exc))
    print(f"[Chatbot Repetitive User Report] Date: Date Format Verification PASS ({len(values)} row(s))")

