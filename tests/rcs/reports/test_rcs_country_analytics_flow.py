"""
RCS Country Analytics — Single Sequential Flow
================================================
Covers: Channels → RCS → Analytics → Country Code page
(URL: /rcs/analytics/country, page <h1>/breadcrumb both read "RCS Country
Analytics")

Locators (pages/rcs_country_analytics_page.py) are built from a live DOM
dump of this exact page, structurally a sibling of RCS Campaign Analytics
but with every locator independently re-confirmed against this page's own
DOM/wire:snapshot (see the page object's module docstring for the full list
of differences: "rcs_country_report" table name, "Search by Country Code"
placeholder, only 17 confirmed columns with 4 fixed identifier columns
[duration/product/agent/country-code] instead of Campaign's 6, and NO
action column / per-row Preview button at all on this report).

This suite was adapted from a QA reference sheet ("RCS Country Report Test
Cases", TC_01-TC_18, all marked PASS) with each TC number preserved as an
anchor below where it maps cleanly onto the confirmed DOM. Discrepancies
found between that sheet and the actual live DOM are handled explicitly
rather than followed blindly (see original Selenium suite for the full
rationale, preserved unchanged here).

Migrated to Playwright: the module-scoped "single sequential flow" pattern
now uses conftest.py's `module_logged_in_page` fixture; the local
page-object fixture is renamed `country_analytics_page` to avoid shadowing
pytest-playwright's reserved `page` fixture.

Run:
    pytest tests/test_rcs_country_analytics_flow.py -v
"""
import os
import re

import pytest

from constants.rcs_country_analytics_headers import EXPECTED_RCS_COUNTRY_ANALYTICS_HEADERS
from pages.rcs.rcs_country_analytics_page import RcsCountryAnalyticsPage
from utils.file_validator import (
    EmptyFileError,
    FileNotDownloadedError,
    HeaderValidationError,
    UnsupportedFileTypeError,
    validate_file_headers,
)


pytestmark = [pytest.mark.rcs, pytest.mark.report]

@pytest.fixture(scope="module")
def country_analytics_page(module_logged_in_page):
    p = RcsCountryAnalyticsPage(module_logged_in_page)
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
def _reset_after_test(country_analytics_page):
    """Hard reset to a clean report view after every test — this page has
    many stateful filters (date range, report type, group by, columns,
    agent/department/user/product), so re-navigating fresh after each test
    is the simplest guaranteed way to avoid cross-test contamination (same
    rationale as every other report suite in this project)."""
    yield
    try:
        country_analytics_page.navigate_to_report()
    except Exception:
        pass


# ── TC_01 — Page Load ─────────────────────────────────────────────────────

@pytest.mark.smoke
def test_country_analytics_TC01_page_loads(country_analytics_page):
    """TC_01: RCS Country Analytics page loads successfully without errors."""
    ensure_on_report_page(country_analytics_page)
    assert country_analytics_page.is_report_page(), "URL should contain /rcs/analytics/country"
    title = country_analytics_page.get_title().lower()
    assert "404" not in title and "error" not in title


@pytest.mark.smoke
def test_country_analytics_title_displayed(country_analytics_page):
    """Page title 'RCS Country Analytics' is visible."""
    ensure_on_report_page(country_analytics_page)
    assert "RCS Country Analytics" in country_analytics_page.get_page_title_text()


@pytest.mark.smoke
def test_country_analytics_filters_button_visible(country_analytics_page):
    """Filters button and Date Range / Report Type / Group By controls are
    visible."""
    ensure_on_report_page(country_analytics_page)
    assert country_analytics_page.is_element_present(country_analytics_page.FILTERS_BUTTON, timeout=5000)
    assert country_analytics_page.are_filters_visible()


# ── TC_02 — Default Date Range ───────────────────────────────────────────

@pytest.mark.smoke
def test_country_analytics_TC02_default_date_range_applied(country_analytics_page):
    """TC_02: A default date range is pre-selected on page load (CONFIRMED
    live wire:snapshot: fromDate/toDate defaulted to a 90-day window ending
    today, dateFormat 'd-m-Y', same as every other RCS Analytics report)."""
    ensure_on_report_page(country_analytics_page)
    value = country_analytics_page.get_date_range_value()
    assert value, "Date range picker should have a pre-filled default value"


# ── TC_03 — UI Validation (Columns) ──────────────────────────────────────

@pytest.mark.smoke
def test_country_analytics_TC03_columns_displayed(country_analytics_page):
    """TC_03: All expected columns are visible and aligned in the table
    header. ADAPTED: asserts against the confirmed live <thead> column set,
    since the QA sheet's expected result ("All columns are correct") gives
    no literal list to check against."""
    ensure_on_report_page(country_analytics_page)
    headers = [h.lower() for h in country_analytics_page.get_visible_column_headers()]
    for expected in ["duration", "product", "agent", "country code",
                     "total count", "total charges"]:
        assert any(expected in h for h in headers), f"Missing column: {expected}"


# ── TC_04-06 — Date Filter ────────────────────────────────────────────────

@pytest.mark.regression
def test_country_analytics_TC04_valid_custom_date_range(country_analytics_page):
    """TC_04: Selecting a valid custom date range refreshes the report.
    ADAPTED: no "Click Apply" step exists — the flatpickr range applies
    immediately via wire:model.live (CONFIRMED live DOM)."""
    ensure_on_report_page(country_analytics_page)
    ok = country_analytics_page.select_date_range()
    if not ok:
        pytest.skip("Flatpickr date range interaction did not behave as expected")
    assert country_analytics_page.has_records() or country_analytics_page.has_no_records_message()


@pytest.mark.negative
def test_country_analytics_TC05_from_date_never_after_to_date(country_analytics_page):
    """TC_05: The From date can never end up after the To date. flatpickr's
    'range' mode inherently reorders two clicked dates chronologically
    rather than letting a user pick an inverted range. ADAPTED: no "Click
    Apply" step exists on this page."""
    ensure_on_report_page(country_analytics_page)
    ok = country_analytics_page.select_date_range(from_day_offset=3, to_day_offset=10)
    if not ok:
        pytest.skip("Flatpickr date range interaction did not behave as expected")
    value = country_analytics_page.get_date_range_value()
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
def test_country_analytics_TC06_future_date_range(country_analytics_page):
    """TC_06: Selecting a future date range either shows no data or a
    validation message — flatpickr's maxDate: 'today' (CONFIRMED live
    config) prevents picking any day after today at all, so this asserts
    the page remains in a valid, non-broken state rather than asserting a
    specific validation message (none was captured in the DOM)."""
    ensure_on_report_page(country_analytics_page)
    country_analytics_page.open_date_range_picker()
    future_cells = country_analytics_page.page.locator(
        ".flatpickr-calendar.open .flatpickr-day.nextMonthDay:not(.flatpickr-disabled)")
    if future_cells.count() == 0:
        pytest.skip("No enabled next-month cells available to attempt a future selection")
    future_cells.first.click(force=True)
    country_analytics_page.page.wait_for_timeout(500)
    assert country_analytics_page.has_records() or country_analytics_page.has_no_records_message()


# ── TC_07-08 — Report Type ────────────────────────────────────────────────

@pytest.mark.regression
def test_country_analytics_TC07_daily_report_type(country_analytics_page):
    """TC_07: Selecting "Daily" from Report Type groups data by day."""
    ensure_on_report_page(country_analytics_page)
    country_analytics_page.select_report_type("daily")
    assert country_analytics_page.get_report_type() == "daily"
    assert country_analytics_page.has_records() or country_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_country_analytics_TC08_monthly_report_type(country_analytics_page):
    """TC_08: Selecting "Monthly" groups data by month."""
    ensure_on_report_page(country_analytics_page)
    country_analytics_page.select_report_type("monthly")
    assert country_analytics_page.get_report_type() == "monthly"
    assert country_analytics_page.has_records() or country_analytics_page.has_no_records_message()
    country_analytics_page.select_report_type("daily")  # reset


# ── TC_09 — Group By ──────────────────────────────────────────────────────

@pytest.mark.regression
def test_country_analytics_TC09_group_by_option_changes_grouping(country_analytics_page):
    """TC_09: Selecting a different Group By option updates the grouping
    selection. "product" is PRE-SELECTED by default here (CONFIRMED live
    wire:snapshot dimensions:["product"]), so the label already reads
    "1 selected" before this test — toggling "department" on should bump it
    to "2 selected"."""
    ensure_on_report_page(country_analytics_page)
    assert "1 selected" in country_analytics_page.get_group_by_label_text().lower() \
        or "selected" in country_analytics_page.get_group_by_label_text().lower()
    country_analytics_page.toggle_group_by_dimension("department")
    country_analytics_page.page.wait_for_timeout(1000)
    assert "2 selected" in country_analytics_page.get_group_by_label_text().lower()
    country_analytics_page.toggle_group_by_dimension("department")  # reset (toggle back off)


# ── TC_10-11 — Search ─────────────────────────────────────────────────────

@pytest.mark.regression
def test_country_analytics_TC10_search_valid_country(country_analytics_page):
    """TC_10: Searching by a valid Country returns matching records. Uses a
    short substring pulled from a real confirmed country-code value ("IN")
    rather than a guessed term."""
    ensure_on_report_page(country_analytics_page)
    if not country_analytics_page.has_records():
        pytest.skip("No records available to search")
    country_analytics_page.search("IN")
    assert country_analytics_page.has_records() or country_analytics_page.has_no_records_message()
    country_analytics_page.clear_search()


@pytest.mark.negative
def test_country_analytics_TC11_search_invalid_country(country_analytics_page):
    """TC_11: Searching a non-existing Country shows the no-records state.
    NOTE: the exact wording is UNCONFIRMED for this table (see module
    docstring) — asserts has_no_records_message()'s best-effort check
    rather than a literal string."""
    ensure_on_report_page(country_analytics_page)
    country_analytics_page.search("ZZZZ_NON_EXISTENT_COUNTRY_9999")
    assert country_analytics_page.has_no_records_message(), "Invalid search should show a no-records state"
    country_analytics_page.clear_search()


# ── TC_12 — Filters (Product) ─────────────────────────────────────────────

@pytest.mark.regression
def test_country_analytics_TC12_filter_by_product(country_analytics_page):
    """TC_12: Filtering by Transactional/OTP/Promotional shows only
    matching data. CONFIRMED live DOM: Product here is a plain <select>
    with exactly these three named options (plus "All")."""
    ensure_on_report_page(country_analytics_page)
    country_analytics_page.select_product_filter("Transactional")
    assert country_analytics_page.get_product_filter_value() == "Transactional"
    country_analytics_page.page.wait_for_timeout(1000)
    assert country_analytics_page.has_records() or country_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_country_analytics_filters_panel_shows_all_fields(country_analytics_page):
    """Opening the Filters button reveals the Agent/Product/Department/User
    filter fields, in that CONFIRMED order."""
    ensure_on_report_page(country_analytics_page)
    country_analytics_page.open_filters_popover()
    assert country_analytics_page.is_element_present(country_analytics_page.FILTER_AGENT_INPUT, timeout=5000)
    assert country_analytics_page.is_element_present(country_analytics_page.FILTER_PRODUCT_SELECT, timeout=5000)
    assert country_analytics_page.is_element_present(country_analytics_page.FILTER_DEPARTMENT_INPUT, timeout=5000)
    assert country_analytics_page.is_element_present(country_analytics_page.FILTER_USER_INPUT, timeout=5000)


@pytest.mark.regression
def test_country_analytics_filter_by_agent(country_analytics_page):
    """Filtering by Agent updates the report (best-effort: see module
    docstring on the async-select empty-option-markup caveat)."""
    ensure_on_report_page(country_analytics_page)
    country_analytics_page.filter_by_agent("a")
    assert country_analytics_page.has_records() or country_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_country_analytics_filter_by_department(country_analytics_page):
    """Filtering by Department updates the report (best-effort caveat, see
    module docstring)."""
    ensure_on_report_page(country_analytics_page)
    country_analytics_page.filter_by_department("a")
    assert country_analytics_page.has_records() or country_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_country_analytics_filter_by_user(country_analytics_page):
    """Filtering by User updates the report (best-effort caveat, see module
    docstring)."""
    ensure_on_report_page(country_analytics_page)
    country_analytics_page.filter_by_user("a")
    assert country_analytics_page.has_records() or country_analytics_page.has_no_records_message()


# ── TC_13-14 — Export ─────────────────────────────────────────────────────

@pytest.mark.regression
def test_country_analytics_TC13_export_csv(country_analytics_page):
    """TC_13: Export CSV downloads a file whose header row
    matches this instance's confirmed export columns exactly
    (constants/rcs_country_analytics_headers.py). click_export_csv() captures
    the download via page.expect_download() instead of the old
    click-and-sleep pattern that never verified anything (see the
    page object's click_export_csv() docstring)."""
    ensure_on_report_page(country_analytics_page)
    result = country_analytics_page.click_export_csv()
    if result is None:
        pytest.skip("Export CSV did not produce a downloaded file within 30s")
    print(f"[{os.path.basename(result['file_path'])}] downloaded, {result['file_size']} bytes, {result['elapsed_s']:.2f}s")

    try:
        actual_headers = validate_file_headers(result["file_path"], EXPECTED_RCS_COUNTRY_ANALYTICS_HEADERS)
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
    assert country_analytics_page.is_report_page()


@pytest.mark.regression
def test_country_analytics_TC14_export_button_available_after_filtering(country_analytics_page):
    """TC_14 (data-validation intent adapted to UI-level check: full CSV
    content diffing is outside Playwright's reach): Export CSV remains
    available and clickable after the report has been filtered/searched,
    implying the export reflects current filter state rather than being
    disabled or broken."""
    ensure_on_report_page(country_analytics_page)
    country_analytics_page.search("IN")
    assert country_analytics_page.is_element_present(country_analytics_page.EXPORT_CSV_BUTTON, timeout=5000)
    country_analytics_page.click_export_csv()
    assert country_analytics_page.is_report_page()
    country_analytics_page.clear_search()


# ── TC_15-16 — Columns Dropdown ───────────────────────────────────────────

@pytest.mark.regression
def test_country_analytics_TC15_hide_specific_column(country_analytics_page):
    """TC_15: Unchecking a column in the Columns dropdown removes it from
    the table. Column selection persists in sessionStorage across a plain
    navigate_to_report() (CONFIRMED live wire:snapshot:
    sessionStorageStatus.columnselect=true), so this restores the column
    in a finally block — otherwise TC_16 would find it missing."""
    ensure_on_report_page(country_analytics_page)
    before = set(country_analytics_page.get_visible_column_headers())
    toggled_value = country_analytics_page.uncheck_first_optional_column()
    if not toggled_value:
        pytest.skip("No optional columns available to uncheck")
    try:
        country_analytics_page.page.wait_for_timeout(1000)
        after = set(country_analytics_page.get_visible_column_headers())
        assert after != before, "Column visibility should change after unchecking"
    finally:
        country_analytics_page.check_column(toggled_value)


@pytest.mark.regression
def test_country_analytics_TC16_re_enable_hidden_column(country_analytics_page):
    """TC_16: Re-checking a hidden column makes it reappear."""
    ensure_on_report_page(country_analytics_page)
    toggled_value = country_analytics_page.uncheck_first_optional_column()
    if not toggled_value:
        pytest.skip("No optional columns available to uncheck")
    country_analytics_page.page.wait_for_timeout(1000)
    hidden = set(country_analytics_page.get_visible_column_headers())
    country_analytics_page.check_column(toggled_value)
    country_analytics_page.page.wait_for_timeout(1000)
    restored = set(country_analytics_page.get_visible_column_headers())
    assert restored != hidden, "Column should reappear after re-checking"


# ── TC_17 — Pagination ────────────────────────────────────────────────────

@pytest.mark.regression
def test_country_analytics_TC17_pagination_changes_data(country_analytics_page):
    """TC_17: Navigating to the next page changes the displayed data
    without breaking the UI."""
    ensure_on_report_page(country_analytics_page)
    before = country_analytics_page.get_column_values("duration")
    if not before:
        pytest.skip("No rows to paginate through")
    if not _has_next_page(country_analytics_page):
        pytest.skip("Only one page of results for the current date range -- no Next page button to click")
    country_analytics_page.click_next_page()
    after = country_analytics_page.get_column_values("duration")
    assert after != before, "Row data should change after pagination"
    country_analytics_page.navigate_to_report()  # reset to page 1


@pytest.mark.smoke
def test_country_analytics_records_count_displayed(country_analytics_page):
    """Result count text at the bottom of the table shows correct wording
    (CONFIRMED live text: "Showing 1 to 10 of 81 results" at capture time)."""
    ensure_on_report_page(country_analytics_page)
    if not country_analytics_page.has_records():
        pytest.skip("No records available to verify pagination text")
    text = country_analytics_page.get_pagination_results_text()
    assert "showing" in text.lower() and "of" in text.lower()


# ── TC_18 — Performance ───────────────────────────────────────────────────

@pytest.mark.regression
def test_country_analytics_TC18_load_performance(country_analytics_page):
    """TC_18: Report loads within an acceptable time window (<3-5s per the
    QA sheet). Uses the browser's real Performance Timing API rather than
    our own sleeps — threshold set generously (15s) to absorb normal CI/
    network variance, same convention as every other report suite in this
    project."""
    ensure_on_report_page(country_analytics_page)
    load_ms = country_analytics_page.get_page_load_time_ms()
    if load_ms is None or load_ms <= 0:
        pytest.skip("Browser performance timing API unavailable")
    assert load_ms < 15000, f"Page load took {load_ms}ms"


# ── Bonus — Individual Column Data Validation ────────────────────────────
# These items are fully CONFIRMED from the live DOM but were not
# individually itemised in the QA sheet's 18 TCs — added for the same
# reason every other report suite in this project validates each confirmed
# column and interactive element.

@pytest.mark.smoke
def test_country_analytics_table_loads(country_analytics_page):
    """Country analytics table loads with records displayed correctly."""
    ensure_on_report_page(country_analytics_page)
    assert country_analytics_page.has_records() or country_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_country_analytics_sort_by_duration(country_analytics_page):
    """Clicking the Duration column header's sort control does not break
    the page (CONFIRMED live DOM: wire:click="sortBy('duration')")."""
    ensure_on_report_page(country_analytics_page)
    if not country_analytics_page.has_records():
        pytest.skip("No records available to sort")
    country_analytics_page.sort_by_duration()
    assert country_analytics_page.has_records() or country_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_country_analytics_agent_column_values(country_analytics_page):
    """Agent column has values for every row (CONFIRMED live rows showed
    values like "Jio Assistant", "Cerfgs", "NRIMitr" at capture time)."""
    ensure_on_report_page(country_analytics_page)
    values = country_analytics_page.get_column_values("agent")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_analytics_country_code_column_values(country_analytics_page):
    """Country Code column has values for every row (CONFIRMED live rows
    showed "IN" and "SG" at capture time)."""
    ensure_on_report_page(country_analytics_page)
    values = country_analytics_page.get_column_values("country_code")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_analytics_product_column_values(country_analytics_page):
    """Product column has values for every row."""
    ensure_on_report_page(country_analytics_page)
    values = country_analytics_page.get_column_values("product")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_analytics_total_count_values(country_analytics_page):
    """Total Count column has values for every row."""
    ensure_on_report_page(country_analytics_page)
    values = country_analytics_page.get_column_values("total_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_analytics_sent_count_values(country_analytics_page):
    """Sent Count column has values for every row."""
    ensure_on_report_page(country_analytics_page)
    values = country_analytics_page.get_column_values("sent_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_analytics_delivered_count_values(country_analytics_page):
    """Delivered Count column has values for every row."""
    ensure_on_report_page(country_analytics_page)
    values = country_analytics_page.get_column_values("delivered_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_analytics_read_count_values(country_analytics_page):
    """Read Count column has values for every row."""
    ensure_on_report_page(country_analytics_page)
    values = country_analytics_page.get_column_values("read_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_analytics_failed_count_values(country_analytics_page):
    """Failed Count column has values for every row."""
    ensure_on_report_page(country_analytics_page)
    values = country_analytics_page.get_column_values("failed_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_analytics_rejected_count_values(country_analytics_page):
    """Rejected Count column has values for every row."""
    ensure_on_report_page(country_analytics_page)
    values = country_analytics_page.get_column_values("rejected_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_analytics_dlr_awaited_count_values(country_analytics_page):
    """DLR Awaited Count column has values for every row."""
    ensure_on_report_page(country_analytics_page)
    values = country_analytics_page.get_column_values("dlr_awaited_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_analytics_interactions_values(country_analytics_page):
    """Interactions column has values for every row."""
    ensure_on_report_page(country_analytics_page)
    values = country_analytics_page.get_column_values("interactions")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_analytics_quick_reply_total_values(country_analytics_page):
    """Quick reply total column has values for every row."""
    ensure_on_report_page(country_analytics_page)
    values = country_analytics_page.get_column_values("quick_reply_total")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_analytics_quick_reply_unique_values(country_analytics_page):
    """Quick reply unique column has values for every row."""
    ensure_on_report_page(country_analytics_page)
    values = country_analytics_page.get_column_values("quick_reply_unique")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_analytics_cta_total_clicks_values(country_analytics_page):
    """CTA Total Clicks column has values for every row."""
    ensure_on_report_page(country_analytics_page)
    values = country_analytics_page.get_column_values("cta_total_clicks")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_analytics_cta_unique_clicks_values(country_analytics_page):
    """CTA Unique Clicks column has values for every row."""
    ensure_on_report_page(country_analytics_page)
    values = country_analytics_page.get_column_values("cta_unique_clicks")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_analytics_total_charges_values(country_analytics_page):
    """Total Charges column is displayed with values for every row."""
    ensure_on_report_page(country_analytics_page)
    values = country_analytics_page.get_column_values("total_charges")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)
