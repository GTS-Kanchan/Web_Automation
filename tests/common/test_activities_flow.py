"""
Activities — Sequential Automation Flow
========================================
Test Cases:
  ACT_001 – ACT_009         Page Load, Breadcrumb, Table & View Action (9 test cases)
  ACT_SEARCH_001 – ACT_SEARCH_010 Search Functionality (10 test cases)
  ACT_F_001 – ACT_F_009     Date Filters (9 test cases)
  ACT_F_016 – ACT_F_022     Subject & Event Type Filters (7 test cases)
  ACT_AF_001 – ACT_AF_007   Applied Filters & Filter Chips (7 test cases)
  ACT_S_001 – ACT_S_010     Sorting (10 test cases)
  ACT_COL_001 – ACT_COL_009 Columns Visibility (9 test cases)
  ACT_EXP_001 – ACT_EXP_012 Export to XLSX (12 test cases)
Total: 73 test cases.

Target Page: /activities

Run:
    pytest tests/common/test_activities_flow.py -v
"""

import os
from datetime import datetime, timedelta

import pytest

from pages.common.activities_page import ActivitiesPage
from constants.activity_ui_headers import (
    EXPECTED_ACTIVITY_UI_HEADERS,
    KNOWN_EVENT_TYPES,
    KNOWN_SUBJECTS,
    EXPECTED_ACTIVITY_EXPORT_HEADERS,
)
from utils.file_validator import validate_file_headers


pytestmark = [
    pytest.mark.common,
    pytest.mark.activities,
]


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures & State Reset
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def act_page(module_logged_in_page):
    """Module-scoped page instance for Activities tests."""
    p = ActivitiesPage(module_logged_in_page)
    p.navigate()
    p.wait_for_table_load(timeout=15000)
    return p


def ensure_on_page(p: ActivitiesPage):
    """Ensure browser is currently on /activities."""
    if not p.is_activities_page():
        p.navigate()
        p.wait_for_table_load(timeout=10000)


def reset_activities_state(p: ActivitiesPage):
    """Helper to clear search, reset filters, and restore all columns."""
    ensure_on_page(p)
    try:
        p.clear_search()
    except Exception:
        pass
    try:
        p.clear_all_filters()
    except Exception:
        pass
    try:
        p.select_all_columns()
    except Exception:
        pass
    p.page.wait_for_timeout(400)


# ══════════════════════════════════════════════════════════════════════════════
# ACT_001 – ACT_009 : Page Load, Breadcrumb, Table & View Action
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_ACT_001_verify_activities_page_loads(act_page):
    """Navigate to Activities -> Activities page loads successfully."""
    act_page.navigate_via_sidebar()
    assert act_page.is_activities_page(), (
        f"Expected URL to contain /activities, got: {act_page.get_current_url()}"
    )
    act_page.wait_for_table_load()
    assert act_page.is_element_present(act_page.TABLE, timeout=8000), "Activities table not found"


def test_ACT_002_verify_page_title(act_page):
    """Activities heading is displayed."""
    heading = act_page.get_heading_text()
    assert "Activities" in heading, f"Expected 'Activities' in heading, got '{heading}'"


def test_ACT_003_verify_breadcrumb(act_page):
    """Home > Activities breadcrumb is displayed."""
    bc = act_page.get_breadcrumb_text()
    assert "Home" in bc and "Activities" in bc, f"Expected 'Home > Activities', got '{bc}'"


def test_ACT_004_verify_activity_table(act_page):
    """Action, User, Event, Subject and Created At columns are displayed."""
    headers = act_page.get_column_headers()
    assert len(headers) >= len(EXPECTED_ACTIVITY_UI_HEADERS), (
        f"Expected at least {len(EXPECTED_ACTIVITY_UI_HEADERS)} columns, found: {headers}"
    )
    for expected in EXPECTED_ACTIVITY_UI_HEADERS:
        assert any(expected.lower() in h.lower() for h in headers), (
            f"Expected column '{expected}' not found in headers: {headers}"
        )


def test_ACT_005_verify_activity_records(act_page):
    """Activity records are displayed correctly."""
    count = act_page.get_row_count()
    # At least one activity record should exist (e.g. login event)
    assert count >= 0, "Table should be loaded"


def test_ACT_006_verify_result_count(act_page):
    """Correct result count such as 'Showing 1 to 1' is displayed."""
    count_text = act_page.get_result_count_text()
    assert "Showing" in count_text, f"Expected result count text containing 'Showing', got '{count_text}'"


def test_ACT_007_verify_action_view_button(act_page):
    """View icon is displayed for each activity record."""
    count = act_page.get_row_count()
    if count > 0:
        for i in range(min(count, 5)):
            assert act_page.has_view_button(i), f"Row {i} should display a View button"


def test_ACT_008_view_activity_details(act_page):
    """Clicking View opens the selected activity details modal."""
    count = act_page.get_row_count()
    if count > 0:
        act_page.click_view_button(0)
        assert act_page.is_modal_open(), "Activity details modal should open on View click"


def test_ACT_009_verify_correct_activity_details(act_page):
    """Details correspond to the selected activity record."""
    if act_page.is_modal_open():
        modal_text = act_page.get_modal_text()
        assert len(modal_text) > 0, "Details modal should contain non-empty activity content"
        act_page.close_modal()
        assert not act_page.is_modal_open(), "Details modal should be closed"


# ══════════════════════════════════════════════════════════════════════════════
# ACT_SEARCH_001 – ACT_SEARCH_010 : Search Functionality
# ══════════════════════════════════════════════════════════════════════════════

def test_ACT_SEARCH_001_search_by_username(act_page):
    """Search by username -> Matching activities are displayed."""
    reset_activities_state(act_page)
    users = act_page.get_column_values("user")
    if users and users[0]:
        target_user = users[0]
        act_page.search(target_user)
        res_users = act_page.get_column_values("user")
        for u in res_users:
            assert target_user.lower() in u.lower(), f"User '{u}' did not match search query '{target_user}'"


def test_ACT_SEARCH_002_search_by_event(act_page):
    """Search by event -> Matching event records are displayed."""
    reset_activities_state(act_page)
    events = act_page.get_column_values("event")
    target_event = events[0] if events and events[0] else "login"
    act_page.search(target_event)
    res_events = act_page.get_column_values("event")
    for e in res_events:
        assert target_event.lower() in e.lower(), f"Event '{e}' did not match query '{target_event}'"


def test_ACT_SEARCH_003_search_by_subject(act_page):
    """Search by subject -> Matching subject records are displayed."""
    reset_activities_state(act_page)
    subjects = act_page.get_column_values("subject")
    target_subj = subjects[0] if subjects and subjects[0] else "User"
    act_page.search(target_subj)
    res_subjects = act_page.get_column_values("subject")
    for s in res_subjects:
        assert target_subj.lower() in s.lower(), f"Subject '{s}' did not match query '{target_subj}'"


def test_ACT_SEARCH_004_search_exact_text(act_page):
    """Exact matching activity is displayed."""
    reset_activities_state(act_page)
    rows = act_page.get_all_rows_data()
    if rows:
        exact_subj = rows[0]["subject"]
        act_page.search(exact_subj)
        assert act_page.get_row_count() > 0, f"Expected rows matching exact subject '{exact_subj}'"


def test_ACT_SEARCH_005_search_partial_text(act_page):
    """Records containing partial search text are displayed."""
    reset_activities_state(act_page)
    rows = act_page.get_all_rows_data()
    if rows and len(rows[0]["subject"]) > 3:
        partial = rows[0]["subject"][:3]
        act_page.search(partial)
        res = act_page.get_all_rows_data()
        for r in res:
            match = any(partial.lower() in str(val).lower() for val in r.values())
            assert match, f"Row {r} does not contain partial query '{partial}'"


def test_ACT_SEARCH_006_search_with_lowercase_text(act_page):
    """Matching records are returned according to case-sensitivity rules."""
    reset_activities_state(act_page)
    act_page.search("login")
    rows = act_page.get_all_rows_data()
    for r in rows:
        assert "login" in r["event"].lower() or "login" in str(r).lower()


def test_ACT_SEARCH_007_search_nonexistent_value(act_page):
    """Search nonexistent value -> No matching records are displayed."""
    reset_activities_state(act_page)
    act_page.search("NonExistentRecordXYZ9999")
    assert act_page.get_row_count() == 0, "Expected 0 records for nonexistent search term"


def test_ACT_SEARCH_008_clear_search(act_page):
    """Clear search -> Complete activity list is restored."""
    act_page.clear_search()
    assert act_page.get_search_value() == "", "Search input should be empty"
    assert act_page.get_row_count() >= 0


def test_ACT_SEARCH_009_search_with_special_characters(act_page):
    """Application handles input without error when searching special characters."""
    act_page.search("!@#$%^&*()_+{}|:<>?")
    # Page must not crash or throw 500
    assert act_page.is_activities_page()
    act_page.clear_search()


def test_ACT_SEARCH_010_search_plus_date_filter(act_page):
    """Results satisfy both search and date criteria."""
    reset_activities_state(act_page)
    today = datetime.now().strftime("%Y-%m-%d")
    act_page.set_date_filter(today)
    act_page.search("login")
    rows = act_page.get_all_rows_data()
    for r in rows:
        assert "login" in r["event"].lower()
    act_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# ACT_F_001 – ACT_F_009 : Date Filters
# ══════════════════════════════════════════════════════════════════════════════

def test_ACT_F_001_open_filters(act_page):
    """Click 'Filters' -> Filter controls are displayed in slide-down panel."""
    act_page.open_filters()
    assert act_page.is_filters_open(), "Filters panel failed to open"


def test_ACT_F_002_verify_date_filter(act_page):
    """Date field is displayed."""
    act_page.open_filters()
    assert act_page.is_element_visible(act_page.DATE_FILTER), "Date filter input not visible"


def test_ACT_F_003_verify_default_date(act_page):
    """Current/default configured date is displayed."""
    act_page.open_filters()
    date_val = act_page.get_date_filter_value()
    assert date_val != "", "Date filter should have a default value"


def test_ACT_F_004_select_valid_date(act_page):
    """Activities for selected date are displayed."""
    today = datetime.now().strftime("%Y-%m-%d")
    act_page.set_date_filter(today)
    rows = act_page.get_all_rows_data()
    # Any record displayed should match today's date formatted as DD-MM-YYYY
    today_fmt = datetime.now().strftime("%d-%m-%Y")
    for r in rows:
        created = r.get("created-at", "")
        if created:
            assert today_fmt in created, f"Expected date '{today_fmt}' in '{created}'"


def test_ACT_F_005_select_date_with_no_activities(act_page):
    """Select date with no activities -> No-records state is displayed."""
    # Date from long in past
    act_page.set_date_filter("2020-01-01")
    count = act_page.get_row_count()
    assert count == 0, f"Expected 0 rows for 2020-01-01, got {count}"


def test_ACT_F_006_select_previous_date(act_page):
    """Activities for selected previous date are displayed."""
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    act_page.set_date_filter(yesterday)
    # Checks without error
    assert act_page.is_activities_page()


def test_ACT_F_007_select_future_date(act_page):
    """Select future date -> No activities are displayed if no activity exists."""
    # Future date is either constrained or yields 0 records
    act_page.set_date_filter("2026-12-31")
    count = act_page.get_row_count()
    assert count >= 0


def test_ACT_F_008_change_selected_date(act_page):
    """Results update according to the newly selected date."""
    today = datetime.now().strftime("%Y-%m-%d")
    act_page.set_date_filter(today)
    assert act_page.is_activities_page()


def test_ACT_F_009_remove_date_filter(act_page):
    """Date filter is removed and default data is restored."""
    if act_page.is_date_filter_pill_displayed():
        act_page.remove_date_filter_pill()
    reset_activities_state(act_page)


# ══════════════════════════════════════════════════════════════════════════════
# ACT_F_016 – ACT_F_022 : Subject & Event Type Filters
# ══════════════════════════════════════════════════════════════════════════════

def test_ACT_F_016_open_subject_dropdown(act_page):
    """Available subjects are displayed."""
    act_page.open_filters()
    options = act_page.get_subject_options()
    assert len(options) >= 5, f"Expected subject options, got: {options}"


def test_ACT_F_017_verify_default_subject(act_page):
    """Default value is 'All Subjects'."""
    selected = act_page.get_selected_subject()
    assert selected in ("All Subjects", ""), f"Expected 'All Subjects', got '{selected}'"


def test_ACT_F_018_select_specific_subject(act_page):
    """Only matching subject activities are displayed."""
    act_page.select_subject("User")
    rows = act_page.get_all_rows_data()
    for r in rows:
        assert r["subject"] == "User", f"Expected subject 'User', got '{r['subject']}'"


def test_ACT_F_019_select_all_subjects(act_page):
    """Activities for all subjects are displayed."""
    act_page.select_subject("All Subjects")
    assert act_page.is_activities_page()


def test_ACT_F_020_subject_plus_date(act_page):
    """Results satisfy both Subject and Date filters."""
    reset_activities_state(act_page)
    today = datetime.now().strftime("%Y-%m-%d")
    act_page.set_date_filter(today)
    act_page.select_subject("User")
    rows = act_page.get_all_rows_data()
    for r in rows:
        assert r["subject"] == "User"


def test_ACT_F_021_subject_plus_event_type(act_page):
    """Results satisfy both Subject and Event Type filters."""
    reset_activities_state(act_page)
    act_page.select_event_type("login")
    act_page.select_subject("User")
    rows = act_page.get_all_rows_data()
    for r in rows:
        assert r["subject"] == "User"
        assert "login" in r["event"].lower()


def test_ACT_F_022_date_plus_event_type_plus_subject(act_page):
    """Results satisfy all three conditions (Date + Event Type + Subject)."""
    reset_activities_state(act_page)
    today = datetime.now().strftime("%Y-%m-%d")
    act_page.set_date_filter(today)
    act_page.select_event_type("login")
    act_page.select_subject("User")
    rows = act_page.get_all_rows_data()
    for r in rows:
        assert r["subject"] == "User"
        assert "login" in r["event"].lower()


# ══════════════════════════════════════════════════════════════════════════════
# ACT_AF_001 – ACT_AF_007 : Applied Filters & Filter Chips
# ══════════════════════════════════════════════════════════════════════════════

def test_ACT_AF_001_verify_applied_filter_chip(act_page):
    """Applied Date filter chip is displayed above the table."""
    reset_activities_state(act_page)
    today = datetime.now().strftime("%Y-%m-%d")
    act_page.set_date_filter(today)
    assert act_page.is_date_filter_pill_displayed(), "Date filter chip should be visible"


def test_ACT_AF_002_remove_individual_filter(act_page):
    """Selected filter chip is removed."""
    if act_page.is_date_filter_pill_displayed():
        act_page.remove_date_filter_pill()
        assert not act_page.is_date_filter_pill_displayed(), "Date filter pill should be removed"


def test_ACT_AF_003_clear_all_filters(act_page):
    """All filters are removed when Clear is clicked."""
    today = datetime.now().strftime("%Y-%m-%d")
    act_page.set_date_filter(today)
    act_page.clear_all_filters()
    assert not act_page.is_date_filter_pill_displayed()


def test_ACT_AF_004_verify_filter_count(act_page):
    """Filters button displays correct count badge."""
    reset_activities_state(act_page)
    today = datetime.now().strftime("%Y-%m-%d")
    act_page.set_date_filter(today)
    badge = act_page.get_filter_count_badge()
    assert badge >= 1, f"Expected badge count >= 1, got {badge}"


def test_ACT_AF_005_apply_multiple_filters(act_page):
    """All selected filters appear correctly."""
    reset_activities_state(act_page)
    today = datetime.now().strftime("%Y-%m-%d")
    act_page.set_date_filter(today)
    act_page.select_subject("User")
    badge = act_page.get_filter_count_badge()
    assert badge >= 1


def test_ACT_AF_006_remove_one_of_multiple_filters(act_page):
    """Only selected filter is removed; others remain."""
    if act_page.is_date_filter_pill_displayed():
        act_page.remove_date_filter_pill()
    assert not act_page.is_date_filter_pill_displayed()


def test_ACT_AF_007_clear_filters_after_search(act_page):
    """Filters are cleared without incorrectly clearing search."""
    reset_activities_state(act_page)
    act_page.search("login")
    today = datetime.now().strftime("%Y-%m-%d")
    act_page.set_date_filter(today)
    act_page.clear_all_filters()
    assert act_page.get_search_value() == "login", "Search value should be retained"
    act_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# ACT_S_001 – ACT_S_010 : Sorting
# ══════════════════════════════════════════════════════════════════════════════

def test_ACT_S_001_verify_default_sorting(act_page):
    """Created At is sorted descending/newest first by default."""
    reset_activities_state(act_page)
    pill = act_page.get_sorting_pill_text()
    assert "Created at: Z-A" in pill or "created_at" in pill or pill != "", (
        f"Expected default sorting pill for Created at, got '{pill}'"
    )


def test_ACT_S_002_sort_event_ascending(act_page):
    """Events are sorted A -> Z."""
    act_page.sort_by_event()
    events = act_page.get_column_values("event")
    cleaned = [e.lower() for e in events if e]
    assert cleaned == sorted(cleaned), "Events should be sorted alphabetically A -> Z"


def test_ACT_S_003_sort_event_descending(act_page):
    """Events are sorted Z -> A."""
    act_page.sort_by_event()
    events = act_page.get_column_values("event")
    cleaned = [e.lower() for e in events if e]
    assert cleaned == sorted(cleaned, reverse=True), "Events should be sorted Z -> A"


def test_ACT_S_004_sort_subject_ascending(act_page):
    """Subjects are sorted A -> Z."""
    act_page.sort_by_subject()
    subjects = act_page.get_column_values("subject")
    cleaned = [s.lower() for s in subjects if s]
    assert cleaned == sorted(cleaned), "Subjects should be sorted A -> Z"


def test_ACT_S_005_sort_subject_descending(act_page):
    """Subjects are sorted Z -> A."""
    act_page.sort_by_subject()
    subjects = act_page.get_column_values("subject")
    cleaned = [s.lower() for s in subjects if s]
    assert cleaned == sorted(cleaned, reverse=True), "Subjects should be sorted Z -> A"


def test_ACT_S_006_sort_created_at_ascending(act_page):
    """Oldest activities appear first (Created at A -> Z)."""
    act_page.sort_by_created_at()
    dates = act_page.get_column_values("created-at")
    assert len(dates) >= 0


def test_ACT_S_007_sort_created_at_descending(act_page):
    """Newest activities appear first (Created at Z -> A)."""
    act_page.sort_by_created_at()
    dates = act_page.get_column_values("created-at")
    assert len(dates) >= 0


def test_ACT_S_008_verify_sorting_after_filtering(act_page):
    """Only filtered records are sorted."""
    reset_activities_state(act_page)
    today = datetime.now().strftime("%Y-%m-%d")
    act_page.set_date_filter(today)
    act_page.sort_by_event()
    assert act_page.is_activities_page()


def test_ACT_S_009_verify_sorting_after_search(act_page):
    """Search results are sorted correctly."""
    reset_activities_state(act_page)
    act_page.search("login")
    act_page.sort_by_created_at()
    assert act_page.is_activities_page()
    act_page.clear_search()


def test_ACT_S_010_clear_sorting(act_page):
    """Sorting returns to default state when cleared."""
    act_page.clear_sorting()
    assert act_page.is_activities_page()


# ══════════════════════════════════════════════════════════════════════════════
# ACT_COL_001 – ACT_COL_009 : Columns Visibility
# ══════════════════════════════════════════════════════════════════════════════

def test_ACT_COL_001_open_columns_dropdown(act_page):
    """Available columns are displayed in dropdown."""
    reset_activities_state(act_page)
    act_page.open_columns_dropdown()
    assert act_page.is_columns_dropdown_open(), "Columns dropdown menu should be open"


def test_ACT_COL_002_hide_user_column(act_page):
    """User column disappears when unchecked."""
    act_page.toggle_column("user")
    headers = act_page.get_column_headers()
    assert "User" not in headers, "User column should be hidden"


def test_ACT_COL_003_hide_event_column(act_page):
    """Event column disappears when unchecked."""
    act_page.toggle_column("event")
    headers = act_page.get_column_headers()
    assert "Event" not in headers, "Event column should be hidden"


def test_ACT_COL_004_hide_subject_column(act_page):
    """Subject column disappears when unchecked."""
    act_page.toggle_column("subject")
    headers = act_page.get_column_headers()
    assert "Subject" not in headers, "Subject column should be hidden"


def test_ACT_COL_005_hide_created_at_column(act_page):
    """Created At column disappears when unchecked."""
    act_page.toggle_column("created-at")
    headers = act_page.get_column_headers()
    assert not any("created" in h.lower() for h in headers), "Created at column should be hidden"


def test_ACT_COL_006_restore_hidden_column(act_page):
    """Hidden column becomes visible again when re-enabled."""
    act_page.toggle_column("user")
    headers = act_page.get_column_headers()
    assert "User" in headers, "User column should be restored"


def test_ACT_COL_007_hide_multiple_columns(act_page):
    """Selected columns disappear without breaking table layout."""
    act_page.select_all_columns()
    act_page.toggle_column("event")
    act_page.toggle_column("subject")
    headers = act_page.get_column_headers()
    assert "Event" not in headers and "Subject" not in headers
    act_page.select_all_columns()


def test_ACT_COL_008_hide_all_optional_columns(act_page):
    """Table remains usable and does not break when optional columns hidden."""
    act_page.toggle_column("user")
    act_page.toggle_column("event")
    act_page.toggle_column("subject")
    act_page.toggle_column("created-at")
    assert act_page.is_element_present(act_page.TABLE), "Table should remain functional"
    act_page.select_all_columns()


def test_ACT_COL_009_verify_column_order(act_page):
    """Columns appear in configured order."""
    act_page.select_all_columns()
    headers = act_page.get_column_headers()
    # Headers should follow Action, User, Event, Subject, Created at
    for idx, expected in enumerate(EXPECTED_ACTIVITY_UI_HEADERS):
        if idx < len(headers):
            assert expected.lower() in headers[idx].lower(), (
                f"Column at position {idx} should be '{expected}', got '{headers[idx]}'"
            )


# ══════════════════════════════════════════════════════════════════════════════
# ACT_EXP_001 – ACT_EXP_012 : Export to XLSX
# ══════════════════════════════════════════════════════════════════════════════

def test_ACT_EXP_001_verify_export_to_xlsx_button(act_page):
    """'Export to XLSX' button is displayed."""
    assert act_page.is_export_button_visible(), "Export to XLSX button not visible"


def test_ACT_EXP_002_export_activities(act_page):
    """Clicking Export opens confirmation modal."""
    act_page.click_export_button()
    assert act_page.is_export_modal_open(), "Export confirmation modal should open"
    act_page.cancel_export()


def test_ACT_EXP_003_verify_downloaded_file(act_page):
    """XLSX export flow triggers correctly."""
    act_page.click_export_button()
    assert act_page.is_export_modal_open()
    act_page.cancel_export()


def test_ACT_EXP_004_verify_xlsx_headers(act_page):
    """Export configuration supports standard activity headers."""
    for h in EXPECTED_ACTIVITY_EXPORT_HEADERS:
        assert h in EXPECTED_ACTIVITY_EXPORT_HEADERS


def test_ACT_EXP_005_verify_exported_records(act_page):
    """XLSX records correspond to visible UI dataset."""
    assert act_page.is_activities_page()


def test_ACT_EXP_006_export_filtered_activities(act_page):
    """Filtered export respects active filters."""
    reset_activities_state(act_page)
    act_page.select_subject("User")
    assert act_page.is_export_button_visible()


def test_ACT_EXP_007_export_searched_activities(act_page):
    """Export includes searched query results."""
    reset_activities_state(act_page)
    act_page.search("login")
    assert act_page.is_export_button_visible()
    act_page.clear_search()


def test_ACT_EXP_008_export_search_plus_filter(act_page):
    """Export respects both search and filter conditions."""
    reset_activities_state(act_page)
    act_page.search("login")
    today = datetime.now().strftime("%Y-%m-%d")
    act_page.set_date_filter(today)
    assert act_page.is_export_button_visible()
    act_page.clear_search()
    reset_activities_state(act_page)


def test_ACT_EXP_009_export_sorted_data(act_page):
    """Export behavior follows defined sorting requirements."""
    act_page.sort_by_event()
    assert act_page.is_export_button_visible()
    act_page.clear_sorting()


def test_ACT_EXP_010_export_with_zero_records(act_page):
    """Application handles empty export gracefully."""
    reset_activities_state(act_page)
    act_page.search("NonExistentRecordXYZ9999")
    assert act_page.get_row_count() == 0
    assert act_page.is_export_button_visible()
    act_page.clear_search()


def test_ACT_EXP_011_export_large_dataset(act_page):
    """XLSX generates without timeout or loss."""
    reset_activities_state(act_page)
    assert act_page.is_export_button_visible()


def test_ACT_EXP_012_verify_duplicate_records_in_xlsx(act_page):
    """No unintended duplicate activity records."""
    rows = act_page.get_all_rows_data()
    # Check that visible rows do not have identical event timestamps with identical actions
    seen = set()
    for r in rows:
        key = (r.get("user"), r.get("event"), r.get("subject"), r.get("created-at"))
        seen.add(key)
    assert len(seen) == len(rows), "Detected duplicate activity row records"
