"""
RCS Agent Analytics — Single Sequential Flow
==============================================
Migrated to Playwright: local page-object fixture renamed
`agent_analytics_page` (built on conftest.py's `module_logged_in_page`) to
avoid shadowing pytest-playwright's reserved `page` fixture.

Run:
    pytest tests/test_rcs_agent_analytics_flow.py -v
"""
import os
import re

import pytest

from constants.rcs_agent_analytics_headers import EXPECTED_RCS_AGENT_ANALYTICS_HEADERS
from pages.rcs.rcs_agent_analytics_page import RcsAgentAnalyticsPage
from utils.file_validator import (
    EmptyFileError,
    FileNotDownloadedError,
    HeaderValidationError,
    UnsupportedFileTypeError,
    validate_file_headers,
)


pytestmark = [pytest.mark.rcs, pytest.mark.report]

@pytest.fixture(scope="module")
def agent_analytics_page(module_logged_in_page):
    p = RcsAgentAnalyticsPage(module_logged_in_page)
    p.navigate_to_report()
    return p


def ensure_on_report_page(p):
    if not p.is_report_page():
        p.navigate_to_report()
        p.page.wait_for_timeout(1000)
    # Even when no navigation was needed, the table can still be mid-render
    # from whatever the previous test in this module-scoped fixture just
    # did (a filter/sort/pagination click, etc.) -- especially under
    # parallel (-n) execution where the shared staging backend is under
    # more load. Confirmed live: has_records() (waits up to 5s for a row to
    # attach) and has_no_records_message() (up to 3s) each individually
    # timed out -- neither state was true yet -- even though the table was
    # genuinely just still loading, not broken. Give the table one more
    # chance to settle into either terminal state before handing back
    # control, so a caller's own short-timeout checks aren't racing a
    # still-loading table. Best-effort: swallow a timeout here so a table
    # that's genuinely broken (not just slow) still surfaces truthfully
    # through the real assertion that follows.
    try:
        p.h.wait_until(lambda: p.has_records() or p.has_no_records_message(),
                        timeout_ms=15000, interval_ms=500)
    except Exception:
        pass


def _has_next_page(p):
    """Whether more results exist beyond the current page.

    Determined from the pagination results text (e.g. "Showing 1 to 10
    of 81 results", read via .paged-pagination-results -- a plain CSS
    class selector, not dependent on this table's Livewire component
    name) rather than the Next button's own visibility state.

    Confirmed more reliable from a real conflict: is_element_visible()
    on NEXT_PAGE_BTN reported "not visible" and caused a false skip on
    several of these reports, even though a live manual check of the
    same screen showed a fully populated, clickable pagination bar
    (page 1..N plus a working Next button) -- most likely a timing gap
    between the report's row data finishing its refresh and this
    specific control settling into its final state. Comparing the
    "shown up to" number against the "of TOTAL" number sidesteps that
    control entirely and reads the same fact the pagination component
    itself uses to decide whether Next should work.

    Falls back to True (attempt the click rather than skip) if the text
    doesn't match the expected "X to Y of Z" shape, since a parsing
    miss should not silently hide a real pagination bug."""
    text = p.get_pagination_results_text() or ""
    match = re.search(r"(\d+)\s+to\s+(\d+)\s+of\s+(\d+)", text, re.IGNORECASE)
    if not match:
        return True
    _, shown_to, total = (int(g) for g in match.groups())
    return total > shown_to


@pytest.fixture(autouse=True)
def _reset_after_test(agent_analytics_page):
    yield
    try:
        agent_analytics_page.navigate_to_report()
    except Exception:
        pass


# ── TC_01 — Page Load ─────────────────────────────────────────────────────

@pytest.mark.smoke
def test_agent_analytics_TC01_page_loads(agent_analytics_page):
    """TC_01: RCS Agent Analytics page loads successfully without errors."""
    ensure_on_report_page(agent_analytics_page)
    assert agent_analytics_page.is_report_page(), "URL should contain /rcs/analytics/agent"
    title = agent_analytics_page.get_title().lower()
    assert "404" not in title and "error" not in title


@pytest.mark.smoke
def test_agent_analytics_title_displayed(agent_analytics_page):
    """Page title 'RCS Agent Analytics' is visible."""
    ensure_on_report_page(agent_analytics_page)
    assert "RCS Agent Analytics" in agent_analytics_page.get_page_title_text()


@pytest.mark.smoke
def test_agent_analytics_filters_button_visible(agent_analytics_page):
    """Filters button and Date Range / Report Type / Group By controls are
    visible."""
    ensure_on_report_page(agent_analytics_page)
    assert agent_analytics_page.is_element_present(agent_analytics_page.FILTERS_BUTTON, timeout=5000)
    assert agent_analytics_page.are_filters_visible()


# ── TC_02 — Default Date Range ───────────────────────────────────────────

@pytest.mark.smoke
def test_agent_analytics_TC02_default_date_range_applied(agent_analytics_page):
    """TC_02: A default date range is pre-selected on page load."""
    ensure_on_report_page(agent_analytics_page)
    value = agent_analytics_page.get_date_range_value()
    assert value, "Date range picker should have a pre-filled default value"


# ── TC_03 — UI Validation (Columns) ──────────────────────────────────────

@pytest.mark.smoke
def test_agent_analytics_TC03_columns_displayed(agent_analytics_page):
    """TC_03: All expected columns are visible and aligned in the table
    header."""
    ensure_on_report_page(agent_analytics_page)
    headers = [h.lower() for h in agent_analytics_page.get_visible_column_headers()]
    for expected in ["duration", "product", "agent",
                     "total count", "total charges"]:
        assert any(expected in h for h in headers), f"Missing column: {expected}"


# ── TC_04-06 — Date Filter ────────────────────────────────────────────────

@pytest.mark.regression
def test_agent_analytics_TC04_valid_custom_date_range(agent_analytics_page):
    """TC_04: Selecting a valid custom date range refreshes the report."""
    ensure_on_report_page(agent_analytics_page)
    ok = agent_analytics_page.select_date_range()
    if not ok:
        pytest.skip("Flatpickr date range interaction did not behave as expected")
    assert agent_analytics_page.has_records() or agent_analytics_page.has_no_records_message()


@pytest.mark.negative
def test_agent_analytics_TC05_from_date_never_after_to_date(agent_analytics_page):
    """TC_05: The From date can never end up after the To date."""
    ensure_on_report_page(agent_analytics_page)
    ok = agent_analytics_page.select_date_range(from_day_offset=3, to_day_offset=10)
    if not ok:
        pytest.skip("Flatpickr date range interaction did not behave as expected")
    value = agent_analytics_page.get_date_range_value()
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
def test_agent_analytics_TC06_future_date_range(agent_analytics_page):
    """TC_06: Selecting a future date range either shows no data or a
    validation message."""
    ensure_on_report_page(agent_analytics_page)
    agent_analytics_page.open_date_range_picker()
    future_cells = agent_analytics_page.page.locator(
        ".flatpickr-calendar.open .flatpickr-day.nextMonthDay:not(.flatpickr-disabled)")
    if future_cells.count() == 0:
        pytest.skip("No enabled next-month cells available to attempt a future selection")
    future_cells.first.click(force=True)
    agent_analytics_page.page.wait_for_timeout(500)
    assert agent_analytics_page.has_records() or agent_analytics_page.has_no_records_message()


# ── TC_07-08 — Report Type ────────────────────────────────────────────────

@pytest.mark.regression
def test_agent_analytics_TC07_daily_report_type(agent_analytics_page):
    """TC_07: Selecting "Daily" from Report Type groups data by day."""
    ensure_on_report_page(agent_analytics_page)
    agent_analytics_page.select_report_type("daily")
    assert agent_analytics_page.get_report_type() == "daily"
    assert agent_analytics_page.has_records() or agent_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_agent_analytics_TC08_monthly_report_type(agent_analytics_page):
    """TC_08: Selecting "Monthly" groups data by month."""
    ensure_on_report_page(agent_analytics_page)
    agent_analytics_page.select_report_type("monthly")
    assert agent_analytics_page.get_report_type() == "monthly"
    assert agent_analytics_page.has_records() or agent_analytics_page.has_no_records_message()
    agent_analytics_page.select_report_type("daily")  # reset


# ── TC_09 — Group By ──────────────────────────────────────────────────────

@pytest.mark.regression
def test_agent_analytics_TC09_group_by_option_changes_grouping(agent_analytics_page):
    """TC_09: Selecting a different Group By option updates the grouping
    selection."""
    ensure_on_report_page(agent_analytics_page)
    assert "1 selected" in agent_analytics_page.get_group_by_label_text().lower() \
        or "selected" in agent_analytics_page.get_group_by_label_text().lower()
    agent_analytics_page.toggle_group_by_dimension("department")
    agent_analytics_page.page.wait_for_timeout(1000)
    assert "2 selected" in agent_analytics_page.get_group_by_label_text().lower()
    agent_analytics_page.toggle_group_by_dimension("department")  # reset (toggle back off)


# ── TC_10-11 — Search ─────────────────────────────────────────────────────

@pytest.mark.regression
def test_agent_analytics_TC10_search_valid_agent(agent_analytics_page):
    """TC_10: Searching by a valid Agent name returns matching records."""
    ensure_on_report_page(agent_analytics_page)
    if not agent_analytics_page.has_records():
        pytest.skip("No records available to search")
    agent_analytics_page.search("Jio")
    assert agent_analytics_page.has_records() or agent_analytics_page.has_no_records_message()
    agent_analytics_page.clear_search()


@pytest.mark.negative
def test_agent_analytics_TC11_search_invalid_agent(agent_analytics_page):
    """TC_11: Searching a non-existing Agent shows the no-records state."""
    ensure_on_report_page(agent_analytics_page)
    agent_analytics_page.search("ZZZZ_NON_EXISTENT_AGENT_9999")
    assert agent_analytics_page.has_no_records_message(), "Invalid search should show a no-records state"
    agent_analytics_page.clear_search()


# ── TC_12 — Filters (Product) ─────────────────────────────────────────────

@pytest.mark.regression
def test_agent_analytics_TC12_filter_by_product(agent_analytics_page):
    """TC_12: Filtering by Transactional/OTP/Promotional shows only
    matching data."""
    ensure_on_report_page(agent_analytics_page)
    agent_analytics_page.select_product_filter("Transactional")
    assert agent_analytics_page.get_product_filter_value() == "Transactional"
    agent_analytics_page.page.wait_for_timeout(1000)
    assert agent_analytics_page.has_records() or agent_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_agent_analytics_filters_panel_shows_all_fields(agent_analytics_page):
    """Opening the Filters button reveals the Product/Department/User
    filter fields (NO Agent filter — see module docstring)."""
    ensure_on_report_page(agent_analytics_page)
    agent_analytics_page.open_filters_popover()
    assert agent_analytics_page.is_element_present(agent_analytics_page.FILTER_PRODUCT_SELECT, timeout=5000)
    assert agent_analytics_page.is_element_present(agent_analytics_page.FILTER_DEPARTMENT_INPUT, timeout=5000)
    assert agent_analytics_page.is_element_present(agent_analytics_page.FILTER_USER_INPUT, timeout=5000)


@pytest.mark.regression
def test_agent_analytics_filter_by_department(agent_analytics_page):
    """Filtering by Department updates the report (best-effort caveat)."""
    ensure_on_report_page(agent_analytics_page)
    agent_analytics_page.filter_by_department("a")
    assert agent_analytics_page.has_records() or agent_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_agent_analytics_filter_by_user(agent_analytics_page):
    """Filtering by User updates the report (best-effort caveat)."""
    ensure_on_report_page(agent_analytics_page)
    agent_analytics_page.filter_by_user("a")
    assert agent_analytics_page.has_records() or agent_analytics_page.has_no_records_message()


# ── TC_13-14 — Export ─────────────────────────────────────────────────────

@pytest.mark.regression
def test_agent_analytics_TC13_export_csv(agent_analytics_page):
    """TC_13: Export CSV downloads a file whose header row
    matches this instance's confirmed export columns exactly
    (constants/rcs_agent_analytics_headers.py). click_export_csv() captures
    the download via page.expect_download() instead of the old
    click-and-sleep pattern that never verified anything (see the
    page object's click_export_csv() docstring)."""
    ensure_on_report_page(agent_analytics_page)
    result = agent_analytics_page.click_export_csv()
    if result is None:
        pytest.skip("Export CSV did not produce a downloaded file within 30s")
    print(f"[{os.path.basename(result['file_path'])}] downloaded, {result['file_size']} bytes, {result['elapsed_s']:.2f}s")

    try:
        actual_headers = validate_file_headers(result["file_path"], EXPECTED_RCS_AGENT_ANALYTICS_HEADERS)
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
    assert agent_analytics_page.is_report_page()


@pytest.mark.regression
def test_agent_analytics_TC14_export_button_available_after_filtering(agent_analytics_page):
    """TC_14: Export CSV remains available and clickable after the report
    has been filtered/searched."""
    ensure_on_report_page(agent_analytics_page)
    agent_analytics_page.search("Jio")
    assert agent_analytics_page.is_element_present(agent_analytics_page.EXPORT_CSV_BUTTON, timeout=5000)
    agent_analytics_page.click_export_csv()
    assert agent_analytics_page.is_report_page()
    agent_analytics_page.clear_search()


# ── TC_15-16 — Columns Dropdown ───────────────────────────────────────────

@pytest.mark.regression
def test_agent_analytics_TC15_hide_specific_column(agent_analytics_page):
    """TC_15: Unchecking a column in the Columns dropdown removes it from
    the table."""
    ensure_on_report_page(agent_analytics_page)
    before = set(agent_analytics_page.get_visible_column_headers())
    toggled_value = agent_analytics_page.uncheck_first_optional_column()
    if not toggled_value:
        pytest.skip("No optional columns available to uncheck")
    try:
        agent_analytics_page.page.wait_for_timeout(1000)
        after = set(agent_analytics_page.get_visible_column_headers())
        assert after != before, "Column visibility should change after unchecking"
    finally:
        agent_analytics_page.check_column(toggled_value)


@pytest.mark.regression
def test_agent_analytics_TC16_re_enable_hidden_column(agent_analytics_page):
    """TC_16: Re-checking a hidden column makes it reappear."""
    ensure_on_report_page(agent_analytics_page)
    toggled_value = agent_analytics_page.uncheck_first_optional_column()
    if not toggled_value:
        pytest.skip("No optional columns available to uncheck")
    agent_analytics_page.page.wait_for_timeout(1000)
    hidden = set(agent_analytics_page.get_visible_column_headers())
    agent_analytics_page.check_column(toggled_value)
    agent_analytics_page.page.wait_for_timeout(1000)
    restored = set(agent_analytics_page.get_visible_column_headers())
    assert restored != hidden, "Column should reappear after re-checking"


# ── TC_17 — Pagination ────────────────────────────────────────────────────

@pytest.mark.regression
def test_agent_analytics_TC17_pagination_changes_data(agent_analytics_page):
    """TC_17: Navigating to the next page changes the displayed data
    without breaking the UI."""
    ensure_on_report_page(agent_analytics_page)
    before = agent_analytics_page.get_column_values("duration")
    if not before:
        pytest.skip("No rows to paginate through")
    if not _has_next_page(agent_analytics_page):
        pytest.skip("Only one page of results for the current date range -- no Next page button to click")
    agent_analytics_page.click_next_page()
    after = agent_analytics_page.get_column_values("duration")
    assert after != before, "Row data should change after pagination"
    agent_analytics_page.navigate_to_report()  # reset to page 1


@pytest.mark.smoke
def test_agent_analytics_records_count_displayed(agent_analytics_page):
    """Result count text at the bottom of the table shows correct wording."""
    ensure_on_report_page(agent_analytics_page)
    text = agent_analytics_page.get_pagination_results_text()
    assert "showing" in text.lower() and "of" in text.lower()


# ── TC_18 — Performance ───────────────────────────────────────────────────

@pytest.mark.regression
def test_agent_analytics_TC18_load_performance(agent_analytics_page):
    """TC_18: Report loads within an acceptable time window."""
    ensure_on_report_page(agent_analytics_page)
    load_ms = agent_analytics_page.get_page_load_time_ms()
    if load_ms is None or load_ms <= 0:
        pytest.skip("Browser performance timing API unavailable")
    assert load_ms < 8000, f"Page load took {load_ms}ms"


# ── Bonus — Individual Column Data Validation ────────────────────────────

@pytest.mark.smoke
def test_agent_analytics_table_loads(agent_analytics_page):
    """Agent analytics table loads with records displayed correctly."""
    ensure_on_report_page(agent_analytics_page)
    assert agent_analytics_page.has_records() or agent_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_agent_analytics_sort_by_duration(agent_analytics_page):
    """Clicking the Duration column header's sort control does not break
    the page."""
    ensure_on_report_page(agent_analytics_page)
    agent_analytics_page.sort_by_duration()
    assert agent_analytics_page.has_records() or agent_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_agent_analytics_agent_column_values(agent_analytics_page):
    """Agent column has values for every row."""
    ensure_on_report_page(agent_analytics_page)
    values = agent_analytics_page.get_column_values("agent")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_agent_analytics_product_column_values(agent_analytics_page):
    """Product column has values for every row."""
    ensure_on_report_page(agent_analytics_page)
    values = agent_analytics_page.get_column_values("product")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_agent_analytics_total_count_values(agent_analytics_page):
    """Total Count column has values for every row."""
    ensure_on_report_page(agent_analytics_page)
    values = agent_analytics_page.get_column_values("total_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_agent_analytics_sent_count_values(agent_analytics_page):
    """Sent Count column has values for every row."""
    ensure_on_report_page(agent_analytics_page)
    values = agent_analytics_page.get_column_values("sent_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_agent_analytics_delivered_count_values(agent_analytics_page):
    """Delivered Count column has values for every row."""
    ensure_on_report_page(agent_analytics_page)
    values = agent_analytics_page.get_column_values("delivered_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_agent_analytics_read_count_values(agent_analytics_page):
    """Read Count column has values for every row."""
    ensure_on_report_page(agent_analytics_page)
    values = agent_analytics_page.get_column_values("read_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_agent_analytics_failed_count_values(agent_analytics_page):
    """Failed Count column has values for every row."""
    ensure_on_report_page(agent_analytics_page)
    values = agent_analytics_page.get_column_values("failed_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_agent_analytics_rejected_count_values(agent_analytics_page):
    """Rejected Count column has values for every row."""
    ensure_on_report_page(agent_analytics_page)
    values = agent_analytics_page.get_column_values("rejected_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_agent_analytics_dlr_awaited_count_values(agent_analytics_page):
    """DLR Awaited Count column has values for every row."""
    ensure_on_report_page(agent_analytics_page)
    values = agent_analytics_page.get_column_values("dlr_awaited_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_agent_analytics_interactions_values(agent_analytics_page):
    """Interactions column has values for every row."""
    ensure_on_report_page(agent_analytics_page)
    values = agent_analytics_page.get_column_values("interactions")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_agent_analytics_quick_reply_total_values(agent_analytics_page):
    """Quick reply total column has values for every row."""
    ensure_on_report_page(agent_analytics_page)
    values = agent_analytics_page.get_column_values("quick_reply_total")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_agent_analytics_quick_reply_unique_values(agent_analytics_page):
    """Quick reply unique column has values for every row."""
    ensure_on_report_page(agent_analytics_page)
    values = agent_analytics_page.get_column_values("quick_reply_unique")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_agent_analytics_cta_total_clicks_values(agent_analytics_page):
    """CTA Total Clicks column has values for every row."""
    ensure_on_report_page(agent_analytics_page)
    values = agent_analytics_page.get_column_values("cta_total_clicks")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_agent_analytics_cta_unique_clicks_values(agent_analytics_page):
    """CTA Unique Clicks column has values for every row."""
    ensure_on_report_page(agent_analytics_page)
    values = agent_analytics_page.get_column_values("cta_unique_clicks")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_agent_analytics_total_charges_values(agent_analytics_page):
    """Total Charges column is displayed with values for every row."""
    ensure_on_report_page(agent_analytics_page)
    values = agent_analytics_page.get_column_values("total_charges")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)
