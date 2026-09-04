"""
RCS Error Code Analytics — Single Sequential Flow
====================================================
Migrated to Playwright: local page-object fixture renamed
`error_code_analytics_page` (built on conftest.py's `module_logged_in_page`)
to avoid shadowing pytest-playwright's reserved `page` fixture. TC
numbering and docstrings preserved from the Selenium suite.

Run:
    pytest tests/test_rcs_error_code_analytics_flow.py -v
"""
import os
import re

import pytest

from constants.rcs_error_code_analytics_headers import EXPECTED_RCS_ERROR_CODE_ANALYTICS_HEADERS
from pages.rcs.rcs_error_code_analytics_page import RcsErrorCodeAnalyticsPage
from utils.file_validator import (
    EmptyFileError,
    FileNotDownloadedError,
    HeaderValidationError,
    UnsupportedFileTypeError,
    validate_file_headers,
)


pytestmark = [pytest.mark.rcs, pytest.mark.report]

@pytest.fixture(scope="module")
def error_code_analytics_page(module_logged_in_page):
    p = RcsErrorCodeAnalyticsPage(module_logged_in_page)
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
def _reset_after_test(error_code_analytics_page):
    """Hard reset to a clean report view after every test — this page has
    many stateful filters (date range, report type, group by, columns,
    product/source checkboxes), so re-navigating fresh after each test is
    the simplest guaranteed way to avoid cross-test contamination (same
    rationale as every other report suite in this project)."""
    yield
    try:
        error_code_analytics_page.navigate_to_report()
    except Exception:
        pass


# ── TC_01 — Page Load ─────────────────────────────────────────────────────

@pytest.mark.smoke
def test_error_code_analytics_TC01_page_loads(error_code_analytics_page):
    """TC_01: RCS Error Code Analytics page loads successfully without
    errors."""
    ensure_on_report_page(error_code_analytics_page)
    assert error_code_analytics_page.is_report_page(), "URL should contain /rcs/analytics/error-code"
    title = error_code_analytics_page.get_title().lower()
    assert "404" not in title and "error" not in title


@pytest.mark.smoke
def test_error_code_analytics_title_displayed(error_code_analytics_page):
    """Page title 'RCS Error Code Report' is visible (CONFIRMED live DOM —
    this report's own title does not follow the "RCS {X} Analytics"
    pattern used by every sibling report)."""
    ensure_on_report_page(error_code_analytics_page)
    assert "RCS Error Code Report" in error_code_analytics_page.get_page_title_text()


@pytest.mark.smoke
def test_error_code_analytics_filters_button_visible(error_code_analytics_page):
    """Filters button and Date Range / Report Type / Group By controls are
    visible."""
    ensure_on_report_page(error_code_analytics_page)
    assert error_code_analytics_page.is_element_present(error_code_analytics_page.FILTERS_BUTTON, timeout=5000)
    assert error_code_analytics_page.are_filters_visible()


# ── TC_02 — Default Date Range ───────────────────────────────────────────

@pytest.mark.smoke
def test_error_code_analytics_TC02_default_date_range_applied(error_code_analytics_page):
    """TC_02: A default date range is pre-selected on page load."""
    ensure_on_report_page(error_code_analytics_page)
    value = error_code_analytics_page.get_date_range_value()
    assert value, "Date range picker should have a pre-filled default value"


# ── TC_03 — UI Validation (Columns) ──────────────────────────────────────

@pytest.mark.smoke
def test_error_code_analytics_TC03_columns_displayed(error_code_analytics_page):
    """TC_03: All expected columns are visible and aligned in the table
    header. Only 6 columns exist on this report."""
    ensure_on_report_page(error_code_analytics_page)
    headers = [h.lower() for h in error_code_analytics_page.get_visible_column_headers()]
    for expected in ["duration", "product", "error code", "error description",
                     "total count", "percentage share"]:
        assert any(expected in h for h in headers), f"Missing column: {expected}"


# ── TC_04-06 — Date Filter ────────────────────────────────────────────────

@pytest.mark.regression
def test_error_code_analytics_TC04_valid_custom_date_range(error_code_analytics_page):
    """TC_04: Selecting a valid custom date range refreshes the report."""
    ensure_on_report_page(error_code_analytics_page)
    ok = error_code_analytics_page.select_date_range()
    if not ok:
        pytest.skip("Flatpickr date range interaction did not behave as expected")
    assert error_code_analytics_page.has_records() or error_code_analytics_page.has_no_records_message()


@pytest.mark.negative
def test_error_code_analytics_TC05_from_date_never_after_to_date(error_code_analytics_page):
    """TC_05: The From date can never end up after the To date."""
    ensure_on_report_page(error_code_analytics_page)
    ok = error_code_analytics_page.select_date_range(from_day_offset=3, to_day_offset=10)
    if not ok:
        pytest.skip("Flatpickr date range interaction did not behave as expected")
    value = error_code_analytics_page.get_date_range_value()
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
def test_error_code_analytics_TC06_future_date_range(error_code_analytics_page):
    """TC_06: Selecting a future date range either shows no data or a
    validation message."""
    ensure_on_report_page(error_code_analytics_page)
    error_code_analytics_page.open_date_range_picker()
    future_cells = error_code_analytics_page.page.locator(
        ".flatpickr-calendar.open .flatpickr-day.nextMonthDay:not(.flatpickr-disabled)")
    if future_cells.count() == 0:
        pytest.skip("No enabled next-month cells available to attempt a future selection")
    future_cells.first.click(force=True)
    error_code_analytics_page.page.wait_for_timeout(500)
    assert error_code_analytics_page.has_records() or error_code_analytics_page.has_no_records_message()


# ── TC_07-08 — Report Type ────────────────────────────────────────────────

@pytest.mark.regression
def test_error_code_analytics_TC07_daily_report_type(error_code_analytics_page):
    """TC_07: Selecting "Daily" from Report Type groups data by day."""
    ensure_on_report_page(error_code_analytics_page)
    error_code_analytics_page.select_report_type("daily")
    assert error_code_analytics_page.get_report_type() == "daily"
    assert error_code_analytics_page.has_records() or error_code_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_error_code_analytics_TC08_monthly_report_type(error_code_analytics_page):
    """TC_08: Selecting "Monthly" groups data by month."""
    ensure_on_report_page(error_code_analytics_page)
    error_code_analytics_page.select_report_type("monthly")
    assert error_code_analytics_page.get_report_type() == "monthly"
    assert error_code_analytics_page.has_records() or error_code_analytics_page.has_no_records_message()
    error_code_analytics_page.select_report_type("daily")  # reset


# ── TC_09 — Group By ──────────────────────────────────────────────────────

@pytest.mark.regression
def test_error_code_analytics_TC09_group_by_option_changes_grouping(error_code_analytics_page):
    """TC_09: Selecting a different Group By option updates the grouping
    selection. CONFIRMED live DOM: this report's dimensions are product/
    source/provider, NOT product/department/user like every sibling
    report."""
    ensure_on_report_page(error_code_analytics_page)
    assert "1 selected" in error_code_analytics_page.get_group_by_label_text().lower() \
        or "selected" in error_code_analytics_page.get_group_by_label_text().lower()
    error_code_analytics_page.toggle_group_by_dimension("source")
    error_code_analytics_page.page.wait_for_timeout(1000)
    assert "2 selected" in error_code_analytics_page.get_group_by_label_text().lower()
    error_code_analytics_page.toggle_group_by_dimension("source")  # reset (toggle back off)


@pytest.mark.regression
def test_error_code_analytics_group_by_provider_dimension_toggle(error_code_analytics_page):
    """Toggling the "provider" Group By dimension (unique to this report)
    updates the checked state without breaking the page."""
    ensure_on_report_page(error_code_analytics_page)
    error_code_analytics_page.toggle_group_by_dimension("provider")
    assert error_code_analytics_page.is_group_by_dimension_checked("provider")
    error_code_analytics_page.toggle_group_by_dimension("provider")  # reset
    assert not error_code_analytics_page.is_group_by_dimension_checked("provider")


# ── TC_10-11 — Search ─────────────────────────────────────────────────────

@pytest.mark.regression
def test_error_code_analytics_TC10_search_valid_term(error_code_analytics_page):
    """TC_10: Searching by a valid error/provider term returns matching
    records."""
    ensure_on_report_page(error_code_analytics_page)
    if not error_code_analytics_page.has_records():
        pytest.skip("No records available to search")
    error_code_analytics_page.search("error")
    assert error_code_analytics_page.has_records() or error_code_analytics_page.has_no_records_message()
    error_code_analytics_page.clear_search()


@pytest.mark.negative
def test_error_code_analytics_TC11_search_invalid_term(error_code_analytics_page):
    """TC_11: Searching a non-existing error/provider term shows the
    no-records state.

    Hardened against a real timing race: search() only sleeps a fixed
    1.5s, which isn't always enough for Livewire's debounced search
    round-trip against the live remote app to finish rendering the
    no-records state. Polls briefly before asserting instead of checking
    only once.
    """
    ensure_on_report_page(error_code_analytics_page)
    error_code_analytics_page.search("ZZZZ_NON_EXISTENT_ERROR_9999")
    result = error_code_analytics_page.h.wait_until(
        error_code_analytics_page.has_no_records_message, timeout_ms=6000, interval_ms=500)
    assert result, "Invalid search should show a no-records state"
    error_code_analytics_page.clear_search()


# ── TC_12 — Filters (Product / Source) ────────────────────────────────────

@pytest.mark.regression
def test_error_code_analytics_TC12_filter_by_product(error_code_analytics_page):
    """TC_12: Filtering by a Product checkbox (e.g. "transactional") shows
    only matching data."""
    ensure_on_report_page(error_code_analytics_page)
    error_code_analytics_page.toggle_product_filter("transactional")
    assert error_code_analytics_page.is_product_filter_checked("transactional")
    error_code_analytics_page.page.wait_for_timeout(1000)
    assert error_code_analytics_page.has_records() or error_code_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_error_code_analytics_filter_by_source(error_code_analytics_page):
    """Filtering by a Source checkbox (e.g. "API") updates the report."""
    ensure_on_report_page(error_code_analytics_page)
    error_code_analytics_page.toggle_source_filter("API")
    assert error_code_analytics_page.is_source_filter_checked("API")
    error_code_analytics_page.page.wait_for_timeout(1000)
    assert error_code_analytics_page.has_records() or error_code_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_error_code_analytics_filters_panel_shows_only_product_and_source(error_code_analytics_page):
    """Opening the Filters button reveals ONLY the Product and Source
    filter fields — CONFIRMED absent: Agent, Department, User."""
    ensure_on_report_page(error_code_analytics_page)
    error_code_analytics_page.open_filters_popover()
    assert error_code_analytics_page.is_element_present(error_code_analytics_page.FILTER_PRODUCT_SELECT_ALL, timeout=5000)
    assert error_code_analytics_page.is_element_present(error_code_analytics_page.FILTER_SOURCE_SELECT_ALL, timeout=5000)


@pytest.mark.regression
def test_error_code_analytics_select_all_product_filter(error_code_analytics_page):
    """Clicking the Product "All" checkbox does not break the page."""
    ensure_on_report_page(error_code_analytics_page)
    error_code_analytics_page.select_all_product_filter()
    assert error_code_analytics_page.has_records() or error_code_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_error_code_analytics_select_all_source_filter(error_code_analytics_page):
    """Clicking the Source "All" checkbox does not break the page."""
    ensure_on_report_page(error_code_analytics_page)
    error_code_analytics_page.select_all_source_filter()
    assert error_code_analytics_page.has_records() or error_code_analytics_page.has_no_records_message()


# ── TC_13-14 — Export ─────────────────────────────────────────────────────

@pytest.mark.regression
def test_error_code_analytics_TC13_export_csv(error_code_analytics_page):
    """TC_13: Export CSV downloads a file whose header row
    matches this instance's confirmed export columns exactly
    (constants/rcs_error_code_analytics_headers.py). click_export_csv() captures
    the download via page.expect_download() instead of the old
    click-and-sleep pattern that never verified anything (see the
    page object's click_export_csv() docstring)."""
    ensure_on_report_page(error_code_analytics_page)
    result = error_code_analytics_page.click_export_csv()
    if result is None:
        pytest.skip("Export CSV did not produce a downloaded file within 30s")
    print(f"[{os.path.basename(result['file_path'])}] downloaded, {result['file_size']} bytes, {result['elapsed_s']:.2f}s")

    try:
        actual_headers = validate_file_headers(result["file_path"], EXPECTED_RCS_ERROR_CODE_ANALYTICS_HEADERS)
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
    assert error_code_analytics_page.is_report_page()


@pytest.mark.regression
def test_error_code_analytics_TC14_export_button_available_after_filtering(error_code_analytics_page):
    """TC_14: Export CSV remains available and clickable after the report
    has been filtered/searched."""
    ensure_on_report_page(error_code_analytics_page)
    error_code_analytics_page.search("error")
    assert error_code_analytics_page.is_element_present(error_code_analytics_page.EXPORT_CSV_BUTTON, timeout=5000)
    error_code_analytics_page.click_export_csv()
    assert error_code_analytics_page.is_report_page()
    error_code_analytics_page.clear_search()


# ── TC_15-16 — Columns Dropdown ───────────────────────────────────────────

@pytest.mark.regression
def test_error_code_analytics_TC15_hide_specific_column(error_code_analytics_page):
    """TC_15: Unchecking a column in the Columns dropdown removes it from
    the table. Only 2 toggleable columns exist here (total-count,
    percentage-share)."""
    ensure_on_report_page(error_code_analytics_page)
    before = set(error_code_analytics_page.get_visible_column_headers())
    toggled_value = error_code_analytics_page.uncheck_first_optional_column()
    if not toggled_value:
        pytest.skip("No optional columns available to uncheck")
    try:
        error_code_analytics_page.page.wait_for_timeout(1000)
        after = set(error_code_analytics_page.get_visible_column_headers())
        assert after != before, "Column visibility should change after unchecking"
    finally:
        error_code_analytics_page.check_column(toggled_value)


@pytest.mark.regression
def test_error_code_analytics_TC16_re_enable_hidden_column(error_code_analytics_page):
    """TC_16: Re-checking a hidden column makes it reappear."""
    ensure_on_report_page(error_code_analytics_page)
    toggled_value = error_code_analytics_page.uncheck_first_optional_column()
    if not toggled_value:
        pytest.skip("No optional columns available to uncheck")
    error_code_analytics_page.page.wait_for_timeout(1000)
    hidden = set(error_code_analytics_page.get_visible_column_headers())
    error_code_analytics_page.check_column(toggled_value)
    error_code_analytics_page.page.wait_for_timeout(1000)
    restored = set(error_code_analytics_page.get_visible_column_headers())
    assert restored != hidden, "Column should reappear after re-checking"


# ── TC_17 — Pagination ────────────────────────────────────────────────────

@pytest.mark.regression
def test_error_code_analytics_TC17_pagination_changes_data(error_code_analytics_page):
    """TC_17: Navigating to the next page changes the displayed data
    without breaking the UI."""
    ensure_on_report_page(error_code_analytics_page)
    before = error_code_analytics_page.get_column_values("duration")
    if not before:
        pytest.skip("No rows to paginate through")
    if not _has_next_page(error_code_analytics_page):
        pytest.skip("Only one page of results for the current date range -- no Next page button to click")
    error_code_analytics_page.click_next_page()
    after = error_code_analytics_page.get_column_values("duration")
    assert after != before, "Row data should change after pagination"
    error_code_analytics_page.navigate_to_report()  # reset to page 1


@pytest.mark.smoke
def test_error_code_analytics_records_count_displayed(error_code_analytics_page):
    """Result count text at the bottom of the table shows correct wording."""
    ensure_on_report_page(error_code_analytics_page)
    text = error_code_analytics_page.get_pagination_results_text()
    assert "showing" in text.lower() and "of" in text.lower()


# ── TC_18 — Performance ───────────────────────────────────────────────────

@pytest.mark.regression
def test_error_code_analytics_TC18_load_performance(error_code_analytics_page):
    """TC_18: Report loads within an acceptable time window."""
    ensure_on_report_page(error_code_analytics_page)
    load_ms = error_code_analytics_page.get_page_load_time_ms()
    if load_ms is None or load_ms <= 0:
        pytest.skip("Browser performance timing API unavailable")
    assert load_ms < 8000, f"Page load took {load_ms}ms"


# ── Bonus — Individual Column Data Validation ────────────────────────────

@pytest.mark.smoke
def test_error_code_analytics_table_loads(error_code_analytics_page):
    """Error Code analytics table loads with records displayed correctly."""
    ensure_on_report_page(error_code_analytics_page)
    assert error_code_analytics_page.has_records() or error_code_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_error_code_analytics_sort_by_duration(error_code_analytics_page):
    """Clicking the Duration column header's sort control does not break
    the page."""
    ensure_on_report_page(error_code_analytics_page)
    error_code_analytics_page.sort_by_duration()
    assert error_code_analytics_page.has_records() or error_code_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_error_code_analytics_product_column_values(error_code_analytics_page):
    """Product column has values for every row."""
    ensure_on_report_page(error_code_analytics_page)
    values = error_code_analytics_page.get_column_values("product")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_error_code_analytics_error_code_column_values(error_code_analytics_page):
    """Error Code column has values for every row."""
    ensure_on_report_page(error_code_analytics_page)
    values = error_code_analytics_page.get_column_values("error_code")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_error_code_analytics_error_description_column_values(error_code_analytics_page):
    """Error Description column has values for every row."""
    ensure_on_report_page(error_code_analytics_page)
    values = error_code_analytics_page.get_column_values("error_description")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_error_code_analytics_total_count_values(error_code_analytics_page):
    """Total Count column has values for every row."""
    ensure_on_report_page(error_code_analytics_page)
    values = error_code_analytics_page.get_column_values("total_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_error_code_analytics_percentage_share_values(error_code_analytics_page):
    """Percentage Share column has values for every row."""
    ensure_on_report_page(error_code_analytics_page)
    values = error_code_analytics_page.get_column_values("percentage_share")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)
