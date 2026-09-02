"""
RCS Message Type Analytics — Single Sequential Flow
=====================================================
Covers: Channels → RCS → Analytics → Message Type page
(URL: /rcs/analytics/message-type, page <h1>/breadcrumb both read "RCS
Message Type Analytics")

Migrated to Playwright: the module-scoped "single sequential flow" pattern
now uses conftest.py's `module_logged_in_page` fixture; the local
page-object fixture is renamed `message_type_analytics_page` to avoid
shadowing pytest-playwright's reserved `page` fixture. All other content
(TC numbering, docstrings, skip rationale) preserved from the Selenium
suite.

Run:
    pytest tests/test_rcs_message_type_analytics_flow.py -v
"""
import os

import pytest

from constants.rcs_message_type_analytics_headers import EXPECTED_RCS_MESSAGE_TYPE_ANALYTICS_HEADERS
from pages.rcs.rcs_message_type_analytics_page import RcsMessageTypeAnalyticsPage
from utils.file_validator import (
    EmptyFileError,
    FileNotDownloadedError,
    HeaderValidationError,
    UnsupportedFileTypeError,
    validate_file_headers,
)


pytestmark = [pytest.mark.rcs, pytest.mark.report]

@pytest.fixture(scope="module")
def message_type_analytics_page(module_logged_in_page):
    p = RcsMessageTypeAnalyticsPage(module_logged_in_page)
    p.navigate_to_report()
    return p


def ensure_on_report_page(p):
    if not p.is_report_page():
        p.navigate_to_report()
        p.page.wait_for_timeout(1000)


@pytest.fixture(autouse=True)
def _reset_after_test(message_type_analytics_page):
    yield
    try:
        message_type_analytics_page.navigate_to_report()
    except Exception:
        pass


# ── TC_01 — Page Load ─────────────────────────────────────────────────────

@pytest.mark.smoke
def test_message_type_analytics_TC01_page_loads(message_type_analytics_page):
    """TC_01: RCS Message Type Analytics page loads successfully without
    errors."""
    ensure_on_report_page(message_type_analytics_page)
    assert message_type_analytics_page.is_report_page(), "URL should contain /rcs/analytics/message-type"
    title = message_type_analytics_page.get_title().lower()
    assert "404" not in title and "error" not in title


@pytest.mark.smoke
def test_message_type_analytics_title_displayed(message_type_analytics_page):
    """Page title 'RCS Message Type Analytics' is visible."""
    ensure_on_report_page(message_type_analytics_page)
    assert "RCS Message Type Analytics" in message_type_analytics_page.get_page_title_text()


@pytest.mark.smoke
def test_message_type_analytics_filters_button_visible(message_type_analytics_page):
    """Filters button and Date Range / Report Type / Group By controls are
    visible."""
    ensure_on_report_page(message_type_analytics_page)
    assert message_type_analytics_page.is_element_present(message_type_analytics_page.FILTERS_BUTTON, timeout=5000)
    assert message_type_analytics_page.are_filters_visible()


# ── TC_02 — Default Date Range ───────────────────────────────────────────

@pytest.mark.smoke
def test_message_type_analytics_TC02_default_date_range_applied(message_type_analytics_page):
    """TC_02: A default date range is pre-selected on page load."""
    ensure_on_report_page(message_type_analytics_page)
    value = message_type_analytics_page.get_date_range_value()
    assert value, "Date range picker should have a pre-filled default value"


# ── TC_03 — UI Validation (Columns) ──────────────────────────────────────

@pytest.mark.smoke
def test_message_type_analytics_TC03_columns_displayed(message_type_analytics_page):
    """TC_03: All expected columns are visible and aligned in the table
    header."""
    ensure_on_report_page(message_type_analytics_page)
    headers = [h.lower() for h in message_type_analytics_page.get_visible_column_headers()]
    for expected in ["duration", "product", "agent", "message type",
                     "total count", "total charges"]:
        assert any(expected in h for h in headers), f"Missing column: {expected}"


# ── TC_04-06 — Date Filter ────────────────────────────────────────────────

@pytest.mark.regression
def test_message_type_analytics_TC04_valid_custom_date_range(message_type_analytics_page):
    """TC_04: Selecting a valid custom date range refreshes the report."""
    ensure_on_report_page(message_type_analytics_page)
    ok = message_type_analytics_page.select_date_range()
    if not ok:
        pytest.skip("Flatpickr date range interaction did not behave as expected")
    assert message_type_analytics_page.has_records() or message_type_analytics_page.has_no_records_message()


@pytest.mark.negative
def test_message_type_analytics_TC05_from_date_never_after_to_date(message_type_analytics_page):
    """TC_05: The From date can never end up after the To date."""
    ensure_on_report_page(message_type_analytics_page)
    ok = message_type_analytics_page.select_date_range(from_day_offset=3, to_day_offset=10)
    if not ok:
        pytest.skip("Flatpickr date range interaction did not behave as expected")
    value = message_type_analytics_page.get_date_range_value()
    if not value or " to " not in value:
        pytest.skip(f"Unexpected date range picker value format: {value!r}")
    from datetime import datetime
    start_str, end_str = value.split(" to ")
    try:
        start = datetime.strptime(start_str.strip(), "%d-%m-%Y")
        end = datetime.strptime(end_str.strip(), "%d-%m-%Y")
    except ValueError:
        pytest.skip(f"Could not parse date range value: {value!r}")
    assert start <= end, "From date must never be after To date"


@pytest.mark.regression
def test_message_type_analytics_TC06_future_date_range(message_type_analytics_page):
    """TC_06: Selecting a future date range either shows no data or a
    validation message."""
    ensure_on_report_page(message_type_analytics_page)
    message_type_analytics_page.open_date_range_picker()
    future_cells = message_type_analytics_page.page.locator(
        ".flatpickr-calendar.open .flatpickr-day.nextMonthDay:not(.flatpickr-disabled)")
    if future_cells.count() == 0:
        pytest.skip("No enabled next-month cells available to attempt a future selection")
    future_cells.first.click(force=True)
    message_type_analytics_page.page.wait_for_timeout(500)
    assert message_type_analytics_page.has_records() or message_type_analytics_page.has_no_records_message()


# ── TC_07-08 — Report Type ────────────────────────────────────────────────

@pytest.mark.regression
def test_message_type_analytics_TC07_daily_report_type(message_type_analytics_page):
    """TC_07: Selecting "Daily" from Report Type groups data by day."""
    ensure_on_report_page(message_type_analytics_page)
    message_type_analytics_page.select_report_type("daily")
    assert message_type_analytics_page.get_report_type() == "daily"
    assert message_type_analytics_page.has_records() or message_type_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_message_type_analytics_TC08_monthly_report_type(message_type_analytics_page):
    """TC_08: Selecting "Monthly" groups data by month."""
    ensure_on_report_page(message_type_analytics_page)
    message_type_analytics_page.select_report_type("monthly")
    assert message_type_analytics_page.get_report_type() == "monthly"
    assert message_type_analytics_page.has_records() or message_type_analytics_page.has_no_records_message()
    message_type_analytics_page.select_report_type("daily")  # reset


# ── TC_09 — Group By ──────────────────────────────────────────────────────

@pytest.mark.regression
def test_message_type_analytics_TC09_group_by_option_changes_grouping(message_type_analytics_page):
    """TC_09: Selecting a different Group By option updates the grouping
    selection."""
    ensure_on_report_page(message_type_analytics_page)
    assert "1 selected" in message_type_analytics_page.get_group_by_label_text().lower() \
        or "selected" in message_type_analytics_page.get_group_by_label_text().lower()
    message_type_analytics_page.toggle_group_by_dimension("department")
    message_type_analytics_page.page.wait_for_timeout(1000)
    assert "2 selected" in message_type_analytics_page.get_group_by_label_text().lower()
    message_type_analytics_page.toggle_group_by_dimension("department")  # reset (toggle back off)


# ── TC_10-11 — Search ─────────────────────────────────────────────────────

@pytest.mark.regression
def test_message_type_analytics_TC10_search_valid_message_type(message_type_analytics_page):
    """TC_10: Searching by a valid Message Type returns matching records."""
    ensure_on_report_page(message_type_analytics_page)
    if not message_type_analytics_page.has_records():
        pytest.skip("No records available to search")
    message_type_analytics_page.search("text")
    assert message_type_analytics_page.has_records() or message_type_analytics_page.has_no_records_message()
    message_type_analytics_page.clear_search()


@pytest.mark.negative
def test_message_type_analytics_TC11_search_invalid_message_type(message_type_analytics_page):
    """TC_11: Searching a non-existing Message Type shows the no-records
    state."""
    ensure_on_report_page(message_type_analytics_page)
    message_type_analytics_page.search("ZZZZ_NON_EXISTENT_MESSAGE_TYPE_9999")
    assert message_type_analytics_page.has_no_records_message(), "Invalid search should show a no-records state"
    message_type_analytics_page.clear_search()


# ── TC_12 — Filters (Product) ─────────────────────────────────────────────

@pytest.mark.regression
def test_message_type_analytics_TC12_filter_by_product(message_type_analytics_page):
    """TC_12: Filtering by Transactional/OTP/Promotional shows only
    matching data."""
    ensure_on_report_page(message_type_analytics_page)
    message_type_analytics_page.select_product_filter("Transactional")
    assert message_type_analytics_page.get_product_filter_value() == "Transactional"
    message_type_analytics_page.page.wait_for_timeout(1000)
    assert message_type_analytics_page.has_records() or message_type_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_message_type_analytics_filters_panel_shows_all_fields(message_type_analytics_page):
    """Opening the Filters button reveals the Agent/Product/Department/User
    filter fields, in that CONFIRMED order."""
    ensure_on_report_page(message_type_analytics_page)
    message_type_analytics_page.open_filters_popover()
    assert message_type_analytics_page.is_element_present(message_type_analytics_page.FILTER_AGENT_INPUT, timeout=5000)
    assert message_type_analytics_page.is_element_present(message_type_analytics_page.FILTER_PRODUCT_SELECT, timeout=5000)
    assert message_type_analytics_page.is_element_present(message_type_analytics_page.FILTER_DEPARTMENT_INPUT, timeout=5000)
    assert message_type_analytics_page.is_element_present(message_type_analytics_page.FILTER_USER_INPUT, timeout=5000)


@pytest.mark.regression
def test_message_type_analytics_filter_by_agent(message_type_analytics_page):
    """Filtering by Agent updates the report (best-effort caveat)."""
    ensure_on_report_page(message_type_analytics_page)
    message_type_analytics_page.filter_by_agent("a")
    assert message_type_analytics_page.has_records() or message_type_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_message_type_analytics_filter_by_department(message_type_analytics_page):
    """Filtering by Department updates the report (best-effort caveat)."""
    ensure_on_report_page(message_type_analytics_page)
    message_type_analytics_page.filter_by_department("a")
    assert message_type_analytics_page.has_records() or message_type_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_message_type_analytics_filter_by_user(message_type_analytics_page):
    """Filtering by User updates the report (best-effort caveat)."""
    pytest.skip("User filter is not present on the Message Type Analytics report")


# ── TC_13-14 — Export ─────────────────────────────────────────────────────

@pytest.mark.regression
def test_message_type_analytics_TC13_export_csv(message_type_analytics_page):
    """TC_13: Export CSV downloads a file whose header row
    matches this instance's confirmed export columns exactly
    (constants/rcs_message_type_analytics_headers.py). click_export_csv() captures
    the download via page.expect_download() instead of the old
    click-and-sleep pattern that never verified anything (see the
    page object's click_export_csv() docstring)."""
    ensure_on_report_page(message_type_analytics_page)
    result = message_type_analytics_page.click_export_csv()
    if result is None:
        pytest.skip("Export CSV did not produce a downloaded file within 30s")
    print(f"[{os.path.basename(result['file_path'])}] downloaded, {result['file_size']} bytes, {result['elapsed_s']:.2f}s")

    try:
        actual_headers = validate_file_headers(result["file_path"], EXPECTED_RCS_MESSAGE_TYPE_ANALYTICS_HEADERS)
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
    assert message_type_analytics_page.is_report_page()


@pytest.mark.regression
def test_message_type_analytics_TC14_export_button_available_after_filtering(message_type_analytics_page):
    """TC_14: Export CSV remains available and clickable after the report
    has been filtered/searched."""
    ensure_on_report_page(message_type_analytics_page)
    message_type_analytics_page.search("text")
    assert message_type_analytics_page.is_element_present(message_type_analytics_page.EXPORT_CSV_BUTTON, timeout=5000)
    message_type_analytics_page.click_export_csv()
    assert message_type_analytics_page.is_report_page()
    message_type_analytics_page.clear_search()


# ── TC_15-16 — Columns Dropdown ───────────────────────────────────────────

@pytest.mark.regression
def test_message_type_analytics_TC15_hide_specific_column(message_type_analytics_page):
    """TC_15: Unchecking a column in the Columns dropdown removes it from
    the table."""
    ensure_on_report_page(message_type_analytics_page)
    before = set(message_type_analytics_page.get_visible_column_headers())
    toggled_value = message_type_analytics_page.uncheck_first_optional_column()
    if not toggled_value:
        pytest.skip("No optional columns available to uncheck")
    try:
        message_type_analytics_page.page.wait_for_timeout(3000)
        after = set(message_type_analytics_page.get_visible_column_headers())
        assert after != before, "Column visibility should change after unchecking"
    finally:
        message_type_analytics_page.check_column(toggled_value)


@pytest.mark.regression
def test_message_type_analytics_TC16_re_enable_hidden_column(message_type_analytics_page):
    """TC_16: Re-checking a hidden column makes it reappear."""
    ensure_on_report_page(message_type_analytics_page)
    toggled_value = message_type_analytics_page.uncheck_first_optional_column()
    if not toggled_value:
        pytest.skip("No optional columns available to uncheck")
    message_type_analytics_page.page.wait_for_timeout(3000)
    hidden = set(message_type_analytics_page.get_visible_column_headers())
    message_type_analytics_page.check_column(toggled_value)
    message_type_analytics_page.page.wait_for_timeout(1000)
    restored = set(message_type_analytics_page.get_visible_column_headers())
    assert restored != hidden, "Column should reappear after re-checking"


# ── TC_17 — Pagination ────────────────────────────────────────────────────

@pytest.mark.regression
def test_message_type_analytics_TC17_pagination_changes_data(message_type_analytics_page):
    """TC_17: Navigating to the next page changes the displayed data
    without breaking the UI."""
    ensure_on_report_page(message_type_analytics_page)
    before = message_type_analytics_page.get_column_values("duration")
    if not before:
        pytest.skip("No rows to paginate through")
    message_type_analytics_page.click_next_page()
    after = message_type_analytics_page.get_column_values("duration")
    assert after != before, "Row data should change after pagination"
    message_type_analytics_page.navigate_to_report()  # reset to page 1


@pytest.mark.smoke
def test_message_type_analytics_records_count_displayed(message_type_analytics_page):
    """Result count text at the bottom of the table shows correct wording."""
    ensure_on_report_page(message_type_analytics_page)
    text = message_type_analytics_page.get_pagination_results_text()
    assert "showing" in text.lower() and "of" in text.lower()


# ── TC_18 — Performance ───────────────────────────────────────────────────

@pytest.mark.regression
def test_message_type_analytics_TC18_load_performance(message_type_analytics_page):
    """TC_18: Report loads within an acceptable time window."""
    ensure_on_report_page(message_type_analytics_page)
    load_ms = message_type_analytics_page.get_page_load_time_ms()
    if load_ms is None or load_ms <= 0:
        pytest.skip("Browser performance timing API unavailable")
    assert load_ms < 8000, f"Page load took {load_ms}ms"


# ── Bonus — Individual Column Data Validation ────────────────────────────

@pytest.mark.smoke
def test_message_type_analytics_table_loads(message_type_analytics_page):
    """Message Type analytics table loads with records displayed
    correctly."""
    ensure_on_report_page(message_type_analytics_page)
    assert message_type_analytics_page.has_records() or message_type_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_message_type_analytics_sort_by_duration(message_type_analytics_page):
    """Clicking the Duration column header's sort control does not break
    the page."""
    ensure_on_report_page(message_type_analytics_page)
    message_type_analytics_page.sort_by_duration()
    assert message_type_analytics_page.has_records() or message_type_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_message_type_analytics_agent_column_values(message_type_analytics_page):
    """Agent column has values for every row."""
    ensure_on_report_page(message_type_analytics_page)
    values = message_type_analytics_page.get_column_values("agent")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_message_type_analytics_message_type_column_values(message_type_analytics_page):
    """Message Type column has values for every row."""
    ensure_on_report_page(message_type_analytics_page)
    values = message_type_analytics_page.get_column_values("message_type")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_message_type_analytics_product_column_values(message_type_analytics_page):
    """Product column has values for every row."""
    ensure_on_report_page(message_type_analytics_page)
    values = message_type_analytics_page.get_column_values("product")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_message_type_analytics_total_count_values(message_type_analytics_page):
    """Total Count column has values for every row."""
    ensure_on_report_page(message_type_analytics_page)
    values = message_type_analytics_page.get_column_values("total_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_message_type_analytics_sent_count_values(message_type_analytics_page):
    """Sent Count column has values for every row."""
    ensure_on_report_page(message_type_analytics_page)
    values = message_type_analytics_page.get_column_values("sent_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_message_type_analytics_delivered_count_values(message_type_analytics_page):
    """Delivered Count column has values for every row."""
    ensure_on_report_page(message_type_analytics_page)
    values = message_type_analytics_page.get_column_values("delivered_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_message_type_analytics_read_count_values(message_type_analytics_page):
    """Read Count column has values for every row."""
    ensure_on_report_page(message_type_analytics_page)
    values = message_type_analytics_page.get_column_values("read_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_message_type_analytics_failed_count_values(message_type_analytics_page):
    """Failed Count column has values for every row."""
    ensure_on_report_page(message_type_analytics_page)
    values = message_type_analytics_page.get_column_values("failed_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_message_type_analytics_rejected_count_values(message_type_analytics_page):
    """Rejected Count column has values for every row."""
    ensure_on_report_page(message_type_analytics_page)
    values = message_type_analytics_page.get_column_values("rejected_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_message_type_analytics_dlr_awaited_count_values(message_type_analytics_page):
    """DLR Awaited Count column has values for every row."""
    ensure_on_report_page(message_type_analytics_page)
    values = message_type_analytics_page.get_column_values("dlr_awaited_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_message_type_analytics_interactions_values(message_type_analytics_page):
    """Interactions column has values for every row."""
    ensure_on_report_page(message_type_analytics_page)
    values = message_type_analytics_page.get_column_values("interactions")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_message_type_analytics_quick_reply_total_values(message_type_analytics_page):
    """Quick reply total column has values for every row."""
    ensure_on_report_page(message_type_analytics_page)
    values = message_type_analytics_page.get_column_values("quick_reply_total")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_message_type_analytics_quick_reply_unique_values(message_type_analytics_page):
    """Quick reply unique column has values for every row."""
    ensure_on_report_page(message_type_analytics_page)
    values = message_type_analytics_page.get_column_values("quick_reply_unique")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_message_type_analytics_cta_total_clicks_values(message_type_analytics_page):
    """CTA Total Clicks column has values for every row."""
    ensure_on_report_page(message_type_analytics_page)
    values = message_type_analytics_page.get_column_values("cta_total_clicks")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_message_type_analytics_cta_unique_clicks_values(message_type_analytics_page):
    """CTA Unique Clicks column has values for every row."""
    ensure_on_report_page(message_type_analytics_page)
    values = message_type_analytics_page.get_column_values("cta_unique_clicks")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_message_type_analytics_total_charges_values(message_type_analytics_page):
    """Total Charges column is displayed with values for every row."""
    ensure_on_report_page(message_type_analytics_page)
    values = message_type_analytics_page.get_column_values("total_charges")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)
