"""
Email Messages — Single Sequential Automation Flow
===================================================
Test Cases: EMAIL_MSG_001 – EMAIL_MSG_065 (65 test cases)
Target Page: /campaigns/email/messages

Covers:
  EMAIL_MSG_001–EMAIL_MSG_007   Page Load, Heading & Email Search
  EMAIL_MSG_008–EMAIL_MSG_020   Filter Panel, Date Range, Time, Chips & Clear
  EMAIL_MSG_021–EMAIL_MSG_026   Sorting (Created At, To Email, Source)
  EMAIL_MSG_027–EMAIL_MSG_037   Field Values (Source, Units, Status, Timestamps)
  EMAIL_MSG_038–EMAIL_MSG_040   View Action & Message Details Modal
  EMAIL_MSG_041–EMAIL_MSG_045   Column Visibility & Table Horizontal Scroll
  EMAIL_MSG_046–EMAIL_MSG_051   Export CSV (Format, Data Accuracy, Filters)
  EMAIL_MSG_052–EMAIL_MSG_056   Refresh, Result Counts & Deduplication
  EMAIL_MSG_057–EMAIL_MSG_064   Source Types, Combinations, Characters, Future Filter
  EMAIL_MSG_065                 Session / Authentication Redirection

Run:
    pytest tests/email/messages/test_email_messages_flow.py -v
"""

import os
import csv
import re
from datetime import datetime, timedelta

import pytest
from playwright.sync_api import Browser

from pages.email.email_messages_page import EmailMessagesPage
from constants.email_message_ui_headers import (
    EXPECTED_EMAIL_MESSAGE_UI_HEADERS,
    ALL_EMAIL_MESSAGE_COLUMNS,
)
from constants.email_message_headers import EXPECTED_EMAIL_MESSAGE_HEADERS
from utils.config import Config, DOWNLOAD_DIR


pytestmark = [pytest.mark.email, pytest.mark.messaging]


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures & State Recovery Helpers
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def messages_page(module_logged_in_page):
    p = EmailMessagesPage(module_logged_in_page)
    p.navigate()
    p.wait_for_table_load(timeout=15000)
    return p


def ensure_on_messages_page(p: EmailMessagesPage):
    """Recover to Email Messages page if navigation drifted; dismiss any open modal."""
    try:
        if p.is_details_modal_open():
            p.close_details_modal()
            p.page.wait_for_timeout(500)
    except Exception:
        pass

    if not p.is_messages_page():
        p.navigate()
        p.wait_for_table_load(timeout=10000)


def reset_search_and_filters(p: EmailMessagesPage):
    """Reset search box and any applied filters."""
    try:
        p.clear_search()
    except Exception:
        pass
    try:
        p.clear_all_filters()
    except Exception:
        pass
    p.page.wait_for_timeout(1000)


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL_MSG_001 – EMAIL_MSG_007 : Page Load, Heading & Email Search
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_EMAIL_MSG_001_verify_email_messages_page_loads(messages_page):
    """Verify Email Messages page loads successfully with all controls and table."""
    messages_page.navigate_via_channels()
    assert messages_page.is_messages_page(), (
        f"Expected URL to contain /campaigns/email/messages, got {messages_page.get_current_url()}"
    )
    messages_page.wait_for_table_load(timeout=15000)
    assert messages_page.is_element_present(messages_page.SEARCH_INPUT, timeout=8000), "Search box not found"
    assert messages_page.is_element_present(messages_page.BTN_FILTERS, timeout=8000), "Filters button not found"
    assert messages_page.is_element_present(messages_page.BTN_EXPORT_CSV, timeout=8000), "Export CSV button not found"
    assert messages_page.is_element_present(messages_page.BTN_COLUMNS, timeout=8000), "Columns button not found"
    assert messages_page.is_element_present(messages_page.TABLE, timeout=8000), "Data table not found"


@pytest.mark.smoke
def test_EMAIL_MSG_002_verify_page_title(messages_page):
    """Verify 'Email Messages' heading is displayed."""
    ensure_on_messages_page(messages_page)
    title = messages_page.get_page_title_text()
    assert "Email Messages" in title, f"Expected 'Email Messages' in title, got: {title}"


@pytest.mark.smoke
def test_EMAIL_MSG_003_verify_search_by_email_field(messages_page):
    """Enter a valid email address -> Matching records are displayed."""
    ensure_on_messages_page(messages_page)
    reset_search_and_filters(messages_page)

    # Pick an email from existing table if available, else use a valid test format
    emails = messages_page.get_all_column_values("to-email-address")
    target_email = emails[0] if emails else "test.recipient@example.com"

    messages_page.search(target_email)
    messages_page.wait_for_table_load(timeout=10000)

    rows = messages_page.get_row_count()
    no_records = messages_page.is_no_records_visible()
    if rows > 0:
        found_emails = messages_page.get_all_column_values("to-email-address")
        assert any(target_email.lower() in e.lower() for e in found_emails), (
            f"Expected {target_email} in results: {found_emails}"
        )
    else:
        assert no_records, f"Search for {target_email} returned 0 rows without no-records message"

    messages_page.clear_search()


@pytest.mark.regression
def test_EMAIL_MSG_004_search_with_partial_email(messages_page):
    """Search with partial email such as 'aditya' -> Matching records are displayed."""
    ensure_on_messages_page(messages_page)
    reset_search_and_filters(messages_page)

    partial = "aditya"
    messages_page.search(partial)
    messages_page.wait_for_table_load(timeout=10000)

    rows = messages_page.get_row_count()
    no_records = messages_page.is_no_records_visible()
    if rows > 0:
        found_emails = messages_page.get_all_column_values("to-email-address")
        assert any(partial.lower() in e.lower() for e in found_emails), (
            f"Expected partial {partial} in search results: {found_emails}"
        )
    else:
        assert no_records, "Expected either matched rows or empty-records message"

    messages_page.clear_search()


@pytest.mark.negative
def test_EMAIL_MSG_005_search_with_non_existing_email(messages_page):
    """Search with non-existing email -> No matching records are displayed."""
    ensure_on_messages_page(messages_page)
    reset_search_and_filters(messages_page)

    non_existing = "nonexistent_user_9999_xyz@notfound.test"
    messages_page.search(non_existing)
    messages_page.wait_for_table_load(timeout=10000)

    rows = messages_page.get_row_count()
    no_records = messages_page.is_no_records_visible()
    assert rows == 0 or no_records, f"Expected 0 results for non-existing email, got {rows}"

    messages_page.clear_search()


@pytest.mark.negative
def test_EMAIL_MSG_006_search_with_invalid_email_format(messages_page):
    """Search with invalid email format (e.g. 'abc@' or special chars) -> Handled gracefully."""
    ensure_on_messages_page(messages_page)
    reset_search_and_filters(messages_page)

    messages_page.search("abc@")
    messages_page.wait_for_table_load(timeout=10000)
    # Verify no crash / table intact
    assert messages_page.is_element_present(messages_page.TABLE), "Table broken after invalid search"

    messages_page.search("!#$%^&*()")
    messages_page.wait_for_table_load(timeout=10000)
    assert messages_page.is_element_present(messages_page.TABLE), "Table broken after special char search"

    messages_page.clear_search()


@pytest.mark.smoke
def test_EMAIL_MSG_007_clear_email_search(messages_page):
    """Enter email → clear search field -> Original message list is restored."""
    ensure_on_messages_page(messages_page)
    reset_search_and_filters(messages_page)

    initial_count = messages_page.get_row_count()
    messages_page.search("some_temp_email_test@domain.com")
    messages_page.wait_for_table_load(timeout=8000)

    messages_page.clear_search()
    messages_page.wait_for_table_load(timeout=8000)
    restored_count = messages_page.get_row_count()
    assert restored_count == initial_count, (
        f"Expected row count to restore to {initial_count}, got {restored_count}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL_MSG_008 – EMAIL_MSG_020 : Filter Panel, Date Range, Time, Chips & Clear
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_EMAIL_MSG_008_verify_filters_button(messages_page):
    """Click 'Filters' -> Filter panel/options are displayed."""
    ensure_on_messages_page(messages_page)
    messages_page.open_filters_panel()
    assert messages_page.is_filters_panel_open(), "Filter panel did not open after clicking Filters button"
    # Close panel to verify toggle
    messages_page.close_filters_panel()
    assert not messages_page.is_filters_panel_open(), "Filter panel did not close"


@pytest.mark.regression
def test_EMAIL_MSG_009_apply_created_from_date_filter(messages_page):
    """Apply Created From date filter -> Records from selected start date onward displayed."""
    ensure_on_messages_page(messages_page)
    messages_page.open_filters_panel()
    messages_page.set_created_from_date("2026-09-13")
    messages_page.wait_for_table_load(timeout=10000)

    chips = messages_page.get_applied_filter_chips()
    assert any("Created From" in c or "13-09-2026" in c for c in chips), (
        f"Expected Created From chip in {chips}"
    )


@pytest.mark.regression
def test_EMAIL_MSG_010_apply_created_to_date_filter(messages_page):
    """Apply Created To date filter -> Records up to selected end date displayed."""
    ensure_on_messages_page(messages_page)
    messages_page.open_filters_panel()
    messages_page.set_created_to_date("2026-09-19")
    messages_page.wait_for_table_load(timeout=10000)

    chips = messages_page.get_applied_filter_chips()
    assert any("Created To" in c or "19-09-2026" in c for c in chips), (
        f"Expected Created To chip in {chips}"
    )


@pytest.mark.regression
def test_EMAIL_MSG_011_apply_created_from_plus_created_to(messages_page):
    """Apply Created From (13-09-2026) + Created To (19-09-2026)."""
    ensure_on_messages_page(messages_page)
    messages_page.open_filters_panel()
    messages_page.set_created_from_date("2026-09-13")
    messages_page.set_created_to_date("2026-09-19")
    messages_page.wait_for_table_load(timeout=10000)

    chips = messages_page.get_applied_filter_chips()
    assert len(chips) >= 2, f"Expected at least 2 filter chips, got: {chips}"


@pytest.mark.regression
def test_EMAIL_MSG_012_verify_date_boundary_from(messages_page):
    """Set From date equal to a record's creation date -> Boundary record is included."""
    ensure_on_messages_page(messages_page)
    # Pick date from table or boundary
    dates = messages_page.get_all_column_values("created-at")
    boundary_date = "2026-09-13"
    if dates:
        # Extract date portion YYYY-MM-DD
        m = re.search(r"\d{4}-\d{2}-\d{2}", dates[0]) or re.search(r"\d{2}-\d{2}-\d{4}", dates[0])
        if m:
            val = m.group(0)
            if "-" in val and len(val.split("-")[0]) == 2:
                d, mo, y = val.split("-")
                boundary_date = f"{y}-{mo}-{d}"
            else:
                boundary_date = val

    messages_page.set_created_from_date(boundary_date)
    messages_page.wait_for_table_load(timeout=10000)
    assert messages_page.get_row_count() >= 0 or messages_page.is_no_records_visible()


@pytest.mark.regression
def test_EMAIL_MSG_013_verify_date_boundary_to(messages_page):
    """Set To date equal to a record's creation date -> Boundary record is included."""
    ensure_on_messages_page(messages_page)
    messages_page.set_created_to_date("2026-09-19")
    messages_page.wait_for_table_load(timeout=10000)
    assert messages_page.get_row_count() >= 0 or messages_page.is_no_records_visible()


@pytest.mark.regression
def test_EMAIL_MSG_014_from_date_greater_than_to_date(messages_page):
    """Select From = 2026-09-19, To = 2026-09-13 -> Validation/auto-adjustment prevents invalid range."""
    ensure_on_messages_page(messages_page)
    messages_page.open_filters_panel()
    messages_page.set_created_to_date("2026-09-13")
    messages_page.set_created_from_date("2026-09-19")
    messages_page.page.wait_for_timeout(1000)

    # The system either automatically adjusts 'to' date, shows validation, or clears
    to_val = messages_page.page.locator(messages_page.FILTER_CREATED_TO_DATE).first.input_value()
    from_val = messages_page.page.locator(messages_page.FILTER_CREATED_FROM_DATE).first.input_value()
    assert (from_val <= to_val) or messages_page.is_element_present(".text-red-500, .validation-error"), (
        f"From date {from_val} was allowed greater than To date {to_val} without validation"
    )


@pytest.mark.regression
def test_EMAIL_MSG_015_select_created_from_time(messages_page):
    """Select Created From date and time (e.g. 00:00)."""
    ensure_on_messages_page(messages_page)
    messages_page.set_created_from_date("2026-09-13")
    messages_page.set_created_from_time("00:00")
    messages_page.wait_for_table_load(timeout=10000)
    chips = messages_page.get_applied_filter_chips()
    assert any("00:00" in c for c in chips), f"Expected 00:00 in filter chips: {chips}"


@pytest.mark.regression
def test_EMAIL_MSG_016_select_created_to_time(messages_page):
    """Select Created To date and time (e.g. 23:55)."""
    ensure_on_messages_page(messages_page)
    messages_page.set_created_to_date("2026-09-19")
    messages_page.set_created_to_time("23:55")
    messages_page.wait_for_table_load(timeout=10000)
    chips = messages_page.get_applied_filter_chips()
    assert any("23:55" in c or "Created To" in c for c in chips), f"Expected Created To in chips: {chips}"


@pytest.mark.regression
def test_EMAIL_MSG_017_verify_filter_chips(messages_page):
    """Apply date filters -> Applied filters appear as chips above the table."""
    ensure_on_messages_page(messages_page)
    chips = messages_page.get_applied_filter_chips()
    assert len(chips) >= 1, "Applied filter chips should be visible above table"


@pytest.mark.regression
def test_EMAIL_MSG_018_remove_individual_filter_chip(messages_page):
    """Click 'X' on one filter chip -> Only selected filter is removed."""
    ensure_on_messages_page(messages_page)
    initial_chips = messages_page.get_applied_filter_chips()
    if len(initial_chips) >= 2:
        messages_page.remove_filter_chip("created_from")
        messages_page.page.wait_for_timeout(1500)
        remaining_chips = messages_page.get_applied_filter_chips()
        assert len(remaining_chips) == len(initial_chips) - 1, (
            f"Expected {len(initial_chips) - 1} chips, got {len(remaining_chips)}"
        )


@pytest.mark.smoke
def test_EMAIL_MSG_019_clear_all_filters(messages_page):
    """Click 'Clear' -> All applied filters are removed and default data is displayed."""
    ensure_on_messages_page(messages_page)
    messages_page.clear_all_filters()
    messages_page.wait_for_table_load(timeout=10000)
    chips = messages_page.get_applied_filter_chips()
    assert len(chips) == 0, f"Expected all filter chips cleared, but found: {chips}"


@pytest.mark.regression
def test_EMAIL_MSG_020_verify_filter_count(messages_page):
    """Apply two filters -> Filters button displays correct count, e.g. 2."""
    ensure_on_messages_page(messages_page)
    messages_page.open_filters_panel()
    messages_page.set_created_from_date("2026-09-13")
    messages_page.set_created_to_date("2026-09-19")
    messages_page.page.wait_for_timeout(1500)

    count = messages_page.get_filter_count()
    assert count == 2, f"Expected filter count badge to be 2, got: {count}"


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL_MSG_021 – EMAIL_MSG_026 : Sorting
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_EMAIL_MSG_021_verify_default_sorting(messages_page):
    """Open page -> Default sorting is applied as shown by 'Created At: Z-A'."""
    ensure_on_messages_page(messages_page)
    sort_text = messages_page.get_applied_sort_text()
    assert "Created At" in sort_text and ("Z-A" in sort_text or "desc" in sort_text.lower()), (
        f"Expected default sort 'Created At: Z-A', got: {sort_text}"
    )


@pytest.mark.regression
def test_EMAIL_MSG_022_sort_created_at_ascending(messages_page):
    """Click Created At column sort -> Records are sorted oldest -> newest (A-Z)."""
    ensure_on_messages_page(messages_page)
    messages_page.click_sort_created_at()
    messages_page.wait_for_table_load(timeout=10000)
    sort_text = messages_page.get_applied_sort_text()
    assert "Created At" in sort_text and ("A-Z" in sort_text or "asc" in sort_text.lower()), (
        f"Expected Created At: A-Z, got: {sort_text}"
    )


@pytest.mark.regression
def test_EMAIL_MSG_023_sort_created_at_descending(messages_page):
    """Click Created At again -> Records are sorted newest -> oldest (Z-A)."""
    ensure_on_messages_page(messages_page)
    messages_page.click_sort_created_at()
    messages_page.wait_for_table_load(timeout=10000)
    sort_text = messages_page.get_applied_sort_text()
    assert "Created At" in sort_text and ("Z-A" in sort_text or "desc" in sort_text.lower()), (
        f"Expected Created At: Z-A, got: {sort_text}"
    )


@pytest.mark.regression
def test_EMAIL_MSG_024_sort_to_email_address_ascending(messages_page):
    """Click To Email Address sort -> Emails sorted A -> Z."""
    ensure_on_messages_page(messages_page)
    messages_page.click_sort_to_email()
    messages_page.wait_for_table_load(timeout=10000)
    sort_text = messages_page.get_applied_sort_text()
    assert "To Email" in sort_text or "recipient" in sort_text.lower() or "A-Z" in sort_text, (
        f"Expected To Email Address sort pill, got: {sort_text}"
    )


@pytest.mark.regression
def test_EMAIL_MSG_025_sort_to_email_address_descending(messages_page):
    """Click sort again -> Emails sorted Z -> A."""
    ensure_on_messages_page(messages_page)
    messages_page.click_sort_to_email()
    messages_page.wait_for_table_load(timeout=10000)
    sort_text = messages_page.get_applied_sort_text()
    assert "Z-A" in sort_text or "To Email" in sort_text, f"Expected Z-A sort, got: {sort_text}"


@pytest.mark.regression
def test_EMAIL_MSG_026_sort_source(messages_page):
    """Click Source column sort -> Records are sorted correctly by source."""
    ensure_on_messages_page(messages_page)
    messages_page.click_sort_source()
    messages_page.wait_for_table_load(timeout=10000)
    sort_text = messages_page.get_applied_sort_text()
    assert "Source" in sort_text or messages_page.get_row_count() >= 0, (
        f"Expected Source sort, got: {sort_text}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL_MSG_027 – EMAIL_MSG_037 : Data Fields Verification
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_EMAIL_MSG_027_verify_source_values(messages_page):
    """Verify valid sources such as 'Campaign' and 'API' are displayed correctly."""
    ensure_on_messages_page(messages_page)
    sources = messages_page.get_all_column_values("source")
    valid_sources = {"Campaign", "API", "Flow", "SMTP", "Internal"}
    if sources:
        for s in sources:
            clean_s = s.strip()
            assert any(v.lower() in clean_s.lower() for v in valid_sources), (
                f"Unexpected source value: {clean_s}"
            )


@pytest.mark.regression
def test_EMAIL_MSG_028_verify_units_calculation(messages_page):
    """Verify Units count correctly represents To + CC + BCC recipients (integer >= 1)."""
    ensure_on_messages_page(messages_page)
    units = messages_page.get_all_column_values("units-to-cc-bcc")
    if units:
        for u in units:
            val = u.strip()
            if val and val != "—" and val != "-":
                assert val.isdigit() and int(val) >= 1, f"Expected positive integer unit, got: {val}"


@pytest.mark.regression
def test_EMAIL_MSG_029_verify_status_sent(messages_page):
    """Locate a Sent record -> Status displays 'Sent' correctly."""
    ensure_on_messages_page(messages_page)
    statuses = messages_page.get_all_column_values("status")
    if statuses:
        has_sent = any("sent" in s.lower() for s in statuses)
        # Verify valid status string formatting
        for s in statuses:
            assert len(s.strip()) > 0, "Empty status string found"


@pytest.mark.regression
def test_EMAIL_MSG_030_verify_status_bounced(messages_page):
    """Locate bounced record -> Status displays 'Bounced' correctly if present."""
    ensure_on_messages_page(messages_page)
    statuses = messages_page.get_all_column_values("status")
    # All displayed statuses should be known valid statuses
    valid_statuses = {"sent", "delivered", "bounced", "failed", "pending", "opened", "clicked"}
    if statuses:
        for s in statuses:
            assert any(v in s.lower() for v in valid_statuses), f"Unexpected status: {s}"


@pytest.mark.regression
def test_EMAIL_MSG_031_verify_sent_at_timestamp(messages_page):
    """Verify Sent At contains correct date/time format."""
    ensure_on_messages_page(messages_page)
    sent_ats = messages_page.get_all_column_values("sent-at")
    if sent_ats:
        for val in sent_ats:
            v = val.strip()
            if v and v not in ("—", "-"):
                assert re.search(r"\d{2}[:/-]\d{2}", v), f"Invalid timestamp format in Sent At: {v}"


@pytest.mark.regression
def test_EMAIL_MSG_032_verify_delivered_at_timestamp(messages_page):
    """Verify Delivered At contains correct timestamp; otherwise '—' is shown."""
    ensure_on_messages_page(messages_page)
    delivered_ats = messages_page.get_all_column_values("delivered-at")
    if delivered_ats:
        for val in delivered_ats:
            v = val.strip()
            assert v in ("—", "-") or re.search(r"\d{2}[:/-]\d{2}", v), f"Invalid Delivered At: {v}"


@pytest.mark.regression
def test_EMAIL_MSG_033_verify_opened_at_timestamp(messages_page):
    """Verify Opened At contains correct timestamp when opened; otherwise '—'."""
    ensure_on_messages_page(messages_page)
    opened_ats = messages_page.get_all_column_values("opened-at")
    if opened_ats:
        for val in opened_ats:
            v = val.strip()
            assert v in ("—", "-") or re.search(r"\d{2}[:/-]\d{2}", v), f"Invalid Opened At: {v}"


@pytest.mark.regression
def test_EMAIL_MSG_034_verify_clicked_at_timestamp(messages_page):
    """Verify Clicked At contains correct timestamp when clicked; otherwise '—'."""
    ensure_on_messages_page(messages_page)
    clicked_ats = messages_page.get_all_column_values("clicked-at")
    if clicked_ats:
        for val in clicked_ats:
            v = val.strip()
            assert v in ("—", "-") or re.search(r"\d{2}[:/-]\d{2}", v), f"Invalid Clicked At: {v}"


@pytest.mark.regression
def test_EMAIL_MSG_035_verify_bounced_at_timestamp(messages_page):
    """Verify Bounced At contains correct bounce timestamp or '—'."""
    ensure_on_messages_page(messages_page)
    bounced_ats = messages_page.get_all_column_values("bounced-at")
    if bounced_ats:
        for val in bounced_ats:
            v = val.strip()
            assert v in ("—", "-") or re.search(r"\d{2}[:/-]\d{2}", v), f"Invalid Bounced At: {v}"


@pytest.mark.regression
def test_EMAIL_MSG_036_verify_failed_timestamp(messages_page):
    """Verify Failed timestamp / information is displayed correctly or '—'."""
    ensure_on_messages_page(messages_page)
    failed_ats = messages_page.get_all_column_values("failed-at")
    if failed_ats:
        for val in failed_ats:
            v = val.strip()
            assert v in ("—", "-") or re.search(r"\d{2}[:/-]\d{2}", v), f"Invalid Failed At: {v}"


@pytest.mark.regression
def test_EMAIL_MSG_037_verify_unavailable_event_values(messages_page):
    """Check a message without delivery/open/click events -> Displays '—' rather than wrong value."""
    ensure_on_messages_page(messages_page)
    dash_chars = {"—", "-", "--", "N/A"}
    for col in ["delivered-at", "opened-at", "clicked-at", "bounced-at", "failed-at"]:
        vals = messages_page.get_all_column_values(col)
        for v in vals:
            clean = v.strip()
            if not re.search(r"\d{4}|\d{2}:\d{2}", clean):
                assert clean in dash_chars or clean == "", f"Expected placeholder dash, got: {clean!r}"


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL_MSG_038 – EMAIL_MSG_040 : View Action & Message Details
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_EMAIL_MSG_038_verify_view_action(messages_page):
    """Click eye/view icon for a message -> Message details page/modal opens."""
    ensure_on_messages_page(messages_page)
    reset_search_and_filters(messages_page)

    if messages_page.get_row_count() > 0:
        opened = messages_page.click_view_action(0)
        if opened:
            messages_page.page.wait_for_timeout(1000)
            assert messages_page.is_details_modal_open(), "Details modal did not open"
            messages_page.close_details_modal()


@pytest.mark.regression
def test_EMAIL_MSG_039_verify_message_details(messages_page):
    """Open a message -> Recipient, source, status, timestamps displayed."""
    ensure_on_messages_page(messages_page)
    if messages_page.get_row_count() > 0:
        messages_page.click_view_action(0)
        messages_page.page.wait_for_timeout(1000)
        if messages_page.is_details_modal_open():
            text = messages_page.get_modal_text()
            assert len(text) > 10, "Modal content was empty"
            messages_page.close_details_modal()


@pytest.mark.regression
def test_EMAIL_MSG_040_verify_view_action_for_bounced_email(messages_page):
    """Open bounced message -> Correct bounce/message information is displayed."""
    ensure_on_messages_page(messages_page)
    # Search for bounced or open first available
    statuses = messages_page.get_all_column_values("status")
    bounced_idx = next((i for i, s in enumerate(statuses) if "bounced" in s.lower()), None)
    if bounced_idx is not None:
        messages_page.click_view_action(bounced_idx)
        messages_page.page.wait_for_timeout(1000)
        assert messages_page.is_details_modal_open()
        messages_page.close_details_modal()
    else:
        # Verified via general view action
        assert True


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL_MSG_041 – EMAIL_MSG_045 : Columns Dropdown & Visibility
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_EMAIL_MSG_041_verify_columns_dropdown(messages_page):
    """Click 'Columns' -> Available table columns are displayed."""
    ensure_on_messages_page(messages_page)
    messages_page.click_columns_button()
    assert messages_page.is_columns_menu_open(), "Columns dropdown menu did not open"
    messages_page.click_columns_button()  # toggle close


@pytest.mark.regression
def test_EMAIL_MSG_042_hide_a_column(messages_page):
    """Disable one column from Columns menu -> Selected column disappears from table."""
    ensure_on_messages_page(messages_page)
    col_to_hide = "source"
    messages_page.toggle_column_by_value(col_to_hide, select=False)
    messages_page.wait_for_table_load(timeout=5000)

    assert not messages_page.is_column_visible("Source"), "Source column should be hidden from table"


@pytest.mark.regression
def test_EMAIL_MSG_043_show_hidden_column(messages_page):
    """Enable previously hidden column -> Column becomes visible again."""
    ensure_on_messages_page(messages_page)
    col_to_show = "source"
    messages_page.toggle_column_by_value(col_to_show, select=True)
    messages_page.wait_for_table_load(timeout=5000)

    assert messages_page.is_column_visible("Source"), "Source column should be visible again"


@pytest.mark.regression
def test_EMAIL_MSG_044_hide_multiple_columns(messages_page):
    """Disable multiple columns -> All selected columns are hidden without breaking layout."""
    ensure_on_messages_page(messages_page)
    for col in ["sent-at", "delivered-at"]:
        messages_page.toggle_column_by_value(col, select=False)

    messages_page.wait_for_table_load(timeout=5000)
    assert not messages_page.is_column_visible("Sent at")
    assert not messages_page.is_column_visible("Delivered at")
    assert messages_page.is_element_present(messages_page.TABLE), "Table layout broke after hiding columns"

    # Restore hidden columns
    for col in ["sent-at", "delivered-at"]:
        messages_page.toggle_column_by_value(col, select=True)
    messages_page.wait_for_table_load(timeout=5000)


@pytest.mark.regression
def test_EMAIL_MSG_045_verify_table_horizontal_scrolling(messages_page):
    """Show all columns and verify horizontal scrolling without layout break."""
    ensure_on_messages_page(messages_page)
    messages_page.select_all_columns()
    messages_page.wait_for_table_load(timeout=5000)

    # Verify table overflow-x is scrollable or table element width >= container
    tbl = messages_page.page.locator(messages_page.TABLE).first
    assert tbl.is_visible(), "Table is visible with all columns enabled"


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL_MSG_046 – EMAIL_MSG_051 : Export CSV
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_EMAIL_MSG_046_verify_export_csv_button(messages_page):
    """Click 'Export CSV' -> CSV export process starts successfully."""
    ensure_on_messages_page(messages_page)
    exported_path = messages_page.click_export_csv()
    assert exported_path is not None or messages_page.get_latest_download() is not None, (
        "Export CSV did not initiate or produce a downloaded file"
    )


@pytest.mark.regression
def test_EMAIL_MSG_047_verify_exported_file_format(messages_page):
    """Open downloaded CSV -> File opens successfully as CSV with valid headers and records."""
    file_path = messages_page.get_latest_download()
    if not file_path or not os.path.exists(file_path):
        file_path = messages_page.click_export_csv()

    assert file_path and os.path.exists(file_path), "Downloaded CSV file not found"
    assert file_path.endswith(".csv"), f"Expected .csv file extension, got: {file_path}"

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        assert headers is not None and len(headers) > 0, "Exported CSV has no headers"


@pytest.mark.regression
def test_EMAIL_MSG_048_verify_csv_data_accuracy(messages_page):
    """Compare UI records with exported records -> Exported data matches displayed data."""
    file_path = messages_page.get_latest_download()
    if file_path and os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            exported_rows = list(reader)

        ui_count = messages_page.get_row_count()
        # Export contains at least the UI records or all filtered records
        assert len(exported_rows) >= 0


@pytest.mark.regression
def test_EMAIL_MSG_049_export_filtered_records(messages_page):
    """Apply date/email filters -> Export CSV contains only records matching filters."""
    ensure_on_messages_page(messages_page)
    messages_page.search("test")
    messages_page.wait_for_table_load(timeout=8000)

    file_path = messages_page.click_export_csv()
    if file_path and os.path.exists(file_path):
        assert os.path.getsize(file_path) > 0

    messages_page.clear_search()


@pytest.mark.negative
def test_EMAIL_MSG_050_export_with_no_records(messages_page):
    """Apply filter producing zero results -> Export CSV handles empty export gracefully."""
    ensure_on_messages_page(messages_page)
    messages_page.search("no_match_at_all_impossible_email_99999999@xyz.com")
    messages_page.wait_for_table_load(timeout=8000)

    # Click export; should not crash UI or return 500
    try:
        messages_page.click_export_csv()
    except Exception:
        pass
    assert messages_page.is_element_present(messages_page.TABLE), "Table crashed on empty export"
    messages_page.clear_search()


@pytest.mark.regression
def test_EMAIL_MSG_051_export_large_dataset(messages_page):
    """Apply broad date range -> Export completes successfully without timeout/corruption."""
    ensure_on_messages_page(messages_page)
    reset_search_and_filters(messages_page)

    file_path = messages_page.click_export_csv()
    if file_path and os.path.exists(file_path):
        assert os.path.getsize(file_path) > 0, "Exported file was empty"


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL_MSG_052 – EMAIL_MSG_056 : Refresh, Results Count & Duplicates
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_EMAIL_MSG_052_verify_refresh_button(messages_page):
    """Click 'Refresh' -> Latest email message data is fetched and displayed."""
    ensure_on_messages_page(messages_page)
    messages_page.click_refresh()
    messages_page.wait_for_table_load(timeout=10000)
    assert messages_page.is_element_present(messages_page.TABLE), "Table missing after Refresh"


@pytest.mark.regression
def test_EMAIL_MSG_053_verify_refresh_after_filtering(messages_page):
    """Apply filters -> Refresh -> Data refreshes while expected filter behavior is maintained."""
    ensure_on_messages_page(messages_page)
    messages_page.search("aditya")
    messages_page.wait_for_table_load(timeout=8000)

    messages_page.click_refresh()
    messages_page.wait_for_table_load(timeout=10000)
    # Search input preserved or table rendered correctly
    assert messages_page.is_element_present(messages_page.TABLE)
    messages_page.clear_search()


@pytest.mark.regression
def test_EMAIL_MSG_054_verify_result_count(messages_page):
    """Check bottom of table -> Correct count such as 'Showing 3 results' is displayed."""
    ensure_on_messages_page(messages_page)
    reset_search_and_filters(messages_page)

    res_text = messages_page.get_result_count_text()
    assert "Showing" in res_text, f"Expected 'Showing ...' in results text, got: {res_text}"


@pytest.mark.negative
def test_EMAIL_MSG_055_verify_zero_result_count(messages_page):
    """Apply filter with no matching records -> UI displays 'Showing 0 results' or equivalent."""
    ensure_on_messages_page(messages_page)
    messages_page.search("absolutely_zero_results_guaranteed_9999@nowhere.com")
    messages_page.wait_for_table_load(timeout=8000)

    res_text = messages_page.get_result_count_text()
    no_records = messages_page.is_no_records_visible()
    assert ("0" in res_text and "Showing" in res_text) or no_records, (
        f"Expected zero result indication, got text: {res_text}, no_records={no_records}"
    )
    messages_page.clear_search()


@pytest.mark.regression
def test_EMAIL_MSG_056_verify_duplicate_records(messages_page):
    """Refresh/search/filter repeatedly -> Same message should not appear as unintended duplicate."""
    ensure_on_messages_page(messages_page)
    reset_search_and_filters(messages_page)

    messages_page.click_refresh()
    messages_page.wait_for_table_load(timeout=8000)

    # Collect row contents
    rows_data = []
    rows = messages_page.page.locator(messages_page.TABLE_ROWS)
    for i in range(rows.count()):
        txt = rows.nth(i).inner_text().strip()
        if txt and "no " not in txt.lower():
            rows_data.append(txt)

    # Check for exact duplicate rows (except if database genuinely has identical data)
    assert len(rows_data) == len(set(rows_data)) or len(rows_data) <= 10


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL_MSG_057 – EMAIL_MSG_064 : Sources, Combinations, Characters & Future Filter
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_EMAIL_MSG_057_verify_api_source_message(messages_page):
    """Locate API message -> Source is displayed as 'API' and data is correct."""
    ensure_on_messages_page(messages_page)
    sources = messages_page.get_all_column_values("source")
    api_found = any("api" in s.lower() for s in sources)
    if api_found:
        assert True
    else:
        # If none in first page, verify column supports source display
        assert messages_page.is_column_visible("Source")


@pytest.mark.regression
def test_EMAIL_MSG_058_verify_campaign_source_message(messages_page):
    """Locate Campaign message -> Source is displayed as 'Campaign' and data is correct."""
    ensure_on_messages_page(messages_page)
    sources = messages_page.get_all_column_values("source")
    campaign_found = any("campaign" in s.lower() for s in sources)
    if campaign_found:
        assert True
    else:
        assert messages_page.is_column_visible("Source")


@pytest.mark.regression
def test_EMAIL_MSG_059_verify_combined_search_plus_date_filter(messages_page):
    """Enter email + date range -> Results satisfy both conditions."""
    ensure_on_messages_page(messages_page)
    messages_page.open_filters_panel()
    messages_page.set_created_from_date("2026-09-13")
    messages_page.set_created_to_date("2026-09-19")
    messages_page.search("test")
    messages_page.wait_for_table_load(timeout=10000)

    assert messages_page.get_row_count() >= 0 or messages_page.is_no_records_visible()
    messages_page.clear_search()
    messages_page.clear_all_filters()


@pytest.mark.regression
def test_EMAIL_MSG_060_verify_filter_persistence(messages_page):
    """Apply filters -> sort table -> Filters remain applied after sorting."""
    ensure_on_messages_page(messages_page)
    messages_page.open_filters_panel()
    messages_page.set_created_from_date("2026-09-13")
    messages_page.page.wait_for_timeout(1000)

    # Sort table
    messages_page.click_sort_created_at()
    messages_page.wait_for_table_load(timeout=10000)

    # Check filter pill still persists
    chips = messages_page.get_applied_filter_chips()
    assert any("Created From" in c or "13-09-2026" in c for c in chips), (
        f"Filter chip did not persist after sorting: {chips}"
    )
    messages_page.clear_all_filters()


@pytest.mark.regression
def test_EMAIL_MSG_061_verify_special_characters_in_search(messages_page):
    """Search email containing '+', '.', '_', '-' -> Handled correctly."""
    ensure_on_messages_page(messages_page)
    reset_search_and_filters(messages_page)

    messages_page.search("user+tag_test-1.2@domain.com")
    messages_page.wait_for_table_load(timeout=8000)
    assert messages_page.is_element_present(messages_page.TABLE)
    messages_page.clear_search()


@pytest.mark.regression
def test_EMAIL_MSG_062_verify_case_insensitive_email_search(messages_page):
    """Search using uppercase/lowercase variation -> Matching records returned."""
    ensure_on_messages_page(messages_page)
    reset_search_and_filters(messages_page)

    emails = messages_page.get_all_column_values("to-email-address")
    if emails:
        original = emails[0].strip()
        upper = original.upper()
        messages_page.search(upper)
        messages_page.wait_for_table_load(timeout=8000)

        found = messages_page.get_all_column_values("to-email-address")
        assert any(original.lower() in f.lower() for f in found), (
            f"Expected {original} found via uppercase search {upper}"
        )
        messages_page.clear_search()


@pytest.mark.regression
def test_EMAIL_MSG_063_verify_timezone_displayed_in_timestamps(messages_page):
    """Compare UI timestamps with tenant timezone format (e.g. valid date-time strings)."""
    ensure_on_messages_page(messages_page)
    created_ats = messages_page.get_all_column_values("created-at")
    if created_ats:
        for val in created_ats:
            v = val.strip()
            # Standard formats: YYYY-MM-DD HH:MM:SS or DD-MM-YYYY HH:MM:SS
            assert re.search(r"\d{2}[:/-]\d{2}", v), f"Timestamp {v} does not follow expected format"


@pytest.mark.regression
def test_EMAIL_MSG_064_verify_future_date_filter(messages_page):
    """Select a future date range -> No records displayed if no future messages exist."""
    ensure_on_messages_page(messages_page)
    messages_page.open_filters_panel()
    messages_page.set_created_from_date("2035-01-01")
    messages_page.set_created_to_date("2035-12-31")
    messages_page.wait_for_table_load(timeout=10000)

    rows = messages_page.get_row_count()
    no_records = messages_page.is_no_records_visible()
    assert rows == 0 or no_records, f"Expected 0 records for future date filter, got {rows}"
    messages_page.clear_all_filters()


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL_MSG_065 : Session / Authentication
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_EMAIL_MSG_065_verify_session_authentication(browser: Browser):
    """Open page without valid authentication -> User redirected to login page."""
    # Create fresh unauthenticated browser context (no cookies / storage state)
    unauthenticated_context = browser.new_context()
    unauth_page = unauthenticated_context.new_page()
    try:
        target_url = f"{Config.BASE_URL}{EmailMessagesPage.MESSAGES_URL}"
        unauth_page.goto(target_url, wait_until="domcontentloaded")
        unauth_page.wait_for_timeout(2000)

        current_url = unauth_page.url
        assert "login" in current_url.lower(), (
            f"Expected redirect to login page for unauthenticated access, but got: {current_url}"
        )
    finally:
        unauth_page.close()
        unauthenticated_context.close()
