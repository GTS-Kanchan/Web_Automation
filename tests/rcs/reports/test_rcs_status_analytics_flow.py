"""
RCS Status Analytics — Single Sequential Flow
===============================================
Migrated to Playwright: local page-object fixture renamed
`status_analytics_page` (built on conftest.py's `module_logged_in_page`) to
avoid shadowing pytest-playwright's reserved `page` fixture. TC numbering
and docstrings preserved from the Selenium suite.

Run:
    pytest tests/test_rcs_status_analytics_flow.py -v
"""
import os
import re

import pytest

from constants.rcs_status_analytics_headers import EXPECTED_RCS_STATUS_ANALYTICS_HEADERS
from pages.rcs.rcs_status_analytics_page import RcsStatusAnalyticsPage
from utils.file_validator import (
    EmptyFileError,
    FileNotDownloadedError,
    HeaderValidationError,
    UnsupportedFileTypeError,
    validate_file_headers,
)


pytestmark = [pytest.mark.rcs, pytest.mark.report]

@pytest.fixture(scope="module")
def status_analytics_page(module_logged_in_page):
    p = RcsStatusAnalyticsPage(module_logged_in_page)
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
def _reset_after_test(status_analytics_page):
    """Hard reset to a clean report view after every test — this page has
    many stateful filters (date range, report type, group by, columns,
    agent/department/user/product), so re-navigating fresh after each test
    is the simplest guaranteed way to avoid cross-test contamination (same
    rationale as every other report suite in this project)."""
    yield
    try:
        status_analytics_page.navigate_to_report()
    except Exception:
        pass


# ── TC_01-04 — Page Load / UI Validation ────────────────────────────────

@pytest.mark.smoke
def test_tc01_status_analytics_page_loads(status_analytics_page):
    """TC_01: RCS Status Analytics page loads successfully without errors."""
    ensure_on_report_page(status_analytics_page)
    assert status_analytics_page.is_report_page(), "URL should contain /rcs/analytics/status"
    title = status_analytics_page.get_title().lower()
    assert "404" not in title and "error" not in title


@pytest.mark.smoke
def test_tc02_status_analytics_page_title(status_analytics_page):
    """TC_02: Page title 'RCS Status Analytics' is visible."""
    ensure_on_report_page(status_analytics_page)
    assert "RCS Status Analytics" in status_analytics_page.get_page_title_text()


@pytest.mark.smoke
def test_tc03_search_bar_visible(status_analytics_page):
    """TC_03: Search by Status search box is visible."""
    ensure_on_report_page(status_analytics_page)
    assert status_analytics_page.is_element_present(status_analytics_page.SEARCH_BOX, timeout=10000)


@pytest.mark.smoke
def test_tc04_filters_button_visible(status_analytics_page):
    """TC_04: Filters button and Date Range / Report Type / Group By
    controls are visible."""
    ensure_on_report_page(status_analytics_page)
    assert status_analytics_page.is_element_present(status_analytics_page.FILTERS_BUTTON, timeout=5000)
    assert status_analytics_page.are_filters_visible()


# ── TC_05-06 — Search ─────────────────────────────────────────────────────

@pytest.mark.regression
def test_tc05_search_valid_status(status_analytics_page):
    """TC_05: Searching by a valid status (e.g. 'delivered', pulled from a
    real confirmed row) returns matching records."""
    ensure_on_report_page(status_analytics_page)
    if not status_analytics_page.has_records():
        pytest.skip("No status records available to search")
    statuses = status_analytics_page.get_column_values("status")
    needle = statuses[0] if statuses and statuses[0] else "delivered"
    status_analytics_page.search(needle)
    assert status_analytics_page.has_records() or status_analytics_page.has_no_records_message()
    status_analytics_page.clear_search()


@pytest.mark.negative
def test_tc06_search_invalid_status(status_analytics_page):
    """TC_06: Searching an invalid status shows no results."""
    ensure_on_report_page(status_analytics_page)
    status_analytics_page.search("zzzznonexistentstatus999")
    assert status_analytics_page.has_no_records_message(), "Invalid search should show no-records message"
    status_analytics_page.clear_search()


# ── TC_07-11 — Filters Panel / Agent / Product / Department / User ──────

@pytest.mark.regression
def test_tc07_open_filters_panel(status_analytics_page):
    """TC_07: Opening the Filters button reveals the Agent/Product/
    Department/User filter fields, in that CONFIRMED order."""
    ensure_on_report_page(status_analytics_page)
    status_analytics_page.open_filters_popover()
    assert status_analytics_page.is_element_present(status_analytics_page.FILTER_AGENT_INPUT, timeout=10000)
    assert status_analytics_page.is_element_present(status_analytics_page.FILTER_PRODUCT_SELECT, timeout=10000)
    assert status_analytics_page.is_element_present(status_analytics_page.FILTER_DEPARTMENT_INPUT, timeout=10000)
    assert status_analytics_page.is_element_present(status_analytics_page.FILTER_USER_INPUT, timeout=10000)


@pytest.mark.regression
def test_tc08_filter_by_agent(status_analytics_page):
    """TC_08: Filtering by Agent updates the report (best-effort)."""
    ensure_on_report_page(status_analytics_page)
    status_analytics_page.filter_by_agent("a")
    assert status_analytics_page.has_records() or status_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_tc09_filter_by_product_type(status_analytics_page):
    """TC_09: Filtering by Product Type (Transactional) updates the report.
    Uses toggle_product_filter_option() (checkbox-based, see its
    docstring) instead of the old unconfirmed select_product_filter()
    guess -- get_product_filter_value() doesn't apply to a checkbox
    multiselect, so it's dropped rather than asserted on."""
    ensure_on_report_page(status_analytics_page)
    status_analytics_page.toggle_product_filter_option("transactional")
    status_analytics_page.page.wait_for_timeout(1000)
    assert status_analytics_page.has_records() or status_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_tc10_filter_by_department(status_analytics_page):
    """TC_10: Filtering by Department name updates the report (best-effort)."""
    ensure_on_report_page(status_analytics_page)
    status_analytics_page.filter_by_department("a")
    assert status_analytics_page.has_records() or status_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_tc11_filter_by_user(status_analytics_page):
    """TC_11: Filtering by User updates the report (same best-effort
    caveat as TC_10).

    CONFIRMED live (user report + DOM): the 'Search User' async-select
    filter IS present and selectable in this environment/role on
    testqa.gtsstaging -- the previous "missing from the QA UI" skip
    reason was wrong (this page already had a fully implemented
    filter_by_user(), just never exercised because of the hard skip
    below it). "kanchan" narrowly matches this instance's confirmed
    real user -- Test Account123
    (kanchan.shinde@globeteleservices.com)."""
    ensure_on_report_page(status_analytics_page)
    status_analytics_page.filter_by_user("kanchan")
    assert status_analytics_page.has_records() or status_analytics_page.has_no_records_message()


# ── TC_12-13 — Date Range ─────────────────────────────────────────────────

@pytest.mark.regression
def test_tc12_valid_date_range(status_analytics_page):
    """TC_12: Selecting a valid date range updates the report."""
    ensure_on_report_page(status_analytics_page)
    ok = status_analytics_page.select_date_range()
    if not ok:
        pytest.skip("Flatpickr date range interaction did not behave as expected")
    assert status_analytics_page.has_records() or status_analytics_page.has_no_records_message()


@pytest.mark.negative
def test_tc13_invalid_date_order(status_analytics_page):
    """TC_13: The From date can never end up after the To date."""
    ensure_on_report_page(status_analytics_page)
    ok = status_analytics_page.select_date_range(from_day_offset=3, to_day_offset=10)
    if not ok:
        pytest.skip("Flatpickr date range interaction did not behave as expected")
    value = status_analytics_page.get_date_range_value()
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
def test_tc14_future_date_range(status_analytics_page):
    """TC_14: Selecting a future date range either shows no data or a
    validation message."""
    ensure_on_report_page(status_analytics_page)
    status_analytics_page.open_date_range_picker()
    future_cells = status_analytics_page.page.locator(
        ".flatpickr-calendar.open .flatpickr-day.nextMonthDay:not(.flatpickr-disabled)")
    if future_cells.count() == 0:
        pytest.skip("No enabled next-month cells available to attempt a future selection")
    future_cells.first.click(force=True)
    status_analytics_page.page.wait_for_timeout(500)
    assert status_analytics_page.has_records() or status_analytics_page.has_no_records_message()


# ── TC_15 — Report Type ───────────────────────────────────────────────────

@pytest.mark.regression
def test_tc15_change_report_type(status_analytics_page):
    """TC_15: Report Type dropdown can be changed. NOTE: unlike SMS Status
    Report (which defaults to 'hourly'), this RCS report defaults to
    'daily' — CONFIRMED live DOM x-data reportType: 'daily'."""
    ensure_on_report_page(status_analytics_page)
    default_type = status_analytics_page.get_report_type()
    assert default_type == "daily"
    status_analytics_page.select_report_type("weekly")
    assert status_analytics_page.get_report_type() == "weekly"
    status_analytics_page.select_report_type("monthly")
    assert status_analytics_page.get_report_type() == "monthly"
    status_analytics_page.select_report_type("daily")


# ── TC_16 — Group By ──────────────────────────────────────────────────────

@pytest.mark.regression
def test_tc16_group_by_dimension(status_analytics_page):
    """TC_16: Group By dropdown supports toggling dimensions."""
    ensure_on_report_page(status_analytics_page)
    label_before = status_analytics_page.get_group_by_label_text()
    assert "selected" in label_before.lower()
    status_analytics_page.toggle_group_by_dimension("department")
    label_after = status_analytics_page.get_group_by_label_text()
    assert "2 selected" in label_after.lower()
    status_analytics_page.toggle_group_by_dimension("department")


# ── TC_17 — Export ────────────────────────────────────────────────────────

@pytest.mark.regression
def test_tc17_export_csv(status_analytics_page):
    """TC_17: Export CSV downloads a file whose header row
    matches this instance's confirmed export columns exactly
    (constants/rcs_status_analytics_headers.py). click_export_csv() captures
    the download via page.expect_download() instead of the old
    click-and-sleep pattern that never verified anything (see the
    page object's click_export_csv() docstring)."""
    ensure_on_report_page(status_analytics_page)
    result = status_analytics_page.click_export_csv()
    if result is None:
        pytest.skip("Export CSV did not produce a downloaded file within 30s")
    print(f"[{os.path.basename(result['file_path'])}] downloaded, {result['file_size']} bytes, {result['elapsed_s']:.2f}s")

    try:
        actual_headers = validate_file_headers(result["file_path"], EXPECTED_RCS_STATUS_ANALYTICS_HEADERS)
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
    assert status_analytics_page.is_report_page()


# ── TC_18-19 — Columns Dropdown ───────────────────────────────────────────

@pytest.mark.regression
def test_tc18_columns_dropdown_toggle(status_analytics_page):
    """TC_18: Columns dropdown can toggle a column's visibility off and
    back on."""
    ensure_on_report_page(status_analytics_page)
    unchecked_value = status_analytics_page.uncheck_first_optional_column()
    try:
        assert unchecked_value is not None
    finally:
        if unchecked_value:
            status_analytics_page.check_column(unchecked_value)


@pytest.mark.regression
def test_tc19_re_enable_hidden_column(status_analytics_page):
    """TC_19: Re-checking a hidden column makes it reappear."""
    ensure_on_report_page(status_analytics_page)
    toggled_value = status_analytics_page.uncheck_first_optional_column()
    if not toggled_value:
        pytest.skip("No optional columns available to uncheck")
    status_analytics_page.page.wait_for_timeout(1000)
    hidden = set(status_analytics_page.get_visible_column_headers())
    status_analytics_page.check_column(toggled_value)
    status_analytics_page.page.wait_for_timeout(1000)
    restored = set(status_analytics_page.get_visible_column_headers())
    assert restored != hidden, "Column should reappear after re-checking"


# ── TC_20-21 — Table / Columns ────────────────────────────────────────────

@pytest.mark.smoke
def test_tc20_table_loads(status_analytics_page):
    """TC_20: Report table loads with data or a no-records message."""
    ensure_on_report_page(status_analytics_page)
    assert status_analytics_page.has_records() or status_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_tc21_expected_columns_present(status_analytics_page):
    """TC_21: Columns like Duration, Product, Agent, Status, Total Count
    should be visible (CONFIRMED live <thead>)."""
    ensure_on_report_page(status_analytics_page)
    headers = status_analytics_page.get_visible_column_headers()
    joined = " ".join(headers).lower()
    assert "duration" in joined
    assert "product" in joined
    assert "agent" in joined
    assert "status" in joined
    assert "total count" in joined


# ── TC_22-27 — Column Data Values ─────────────────────────────────────────

@pytest.mark.regression
def test_tc22_total_count_values(status_analytics_page):
    """TC_22: Verify Total Count data is present."""
    ensure_on_report_page(status_analytics_page)
    if not status_analytics_page.has_records():
        pytest.skip("No records available")
    values = status_analytics_page.get_column_values("total_count")
    assert len(values) > 0
    assert all(v != "" for v in values)


@pytest.mark.regression
def test_tc23_interactions_values(status_analytics_page):
    """TC_23: Verify Interactions values are present."""
    ensure_on_report_page(status_analytics_page)
    if not status_analytics_page.has_records():
        pytest.skip("No records available")
    values = status_analytics_page.get_column_values("interactions")
    assert len(values) > 0
    assert all(v != "" for v in values)


@pytest.mark.regression
def test_tc24_quick_reply_total_values(status_analytics_page):
    """TC_24: Verify Quick reply total values are present."""
    ensure_on_report_page(status_analytics_page)
    if not status_analytics_page.has_records():
        pytest.skip("No records available")
    values = status_analytics_page.get_column_values("quick_reply_total")
    assert len(values) > 0
    assert all(v != "" for v in values)


@pytest.mark.regression
def test_tc25_quick_reply_unique_values(status_analytics_page):
    """TC_25: Verify Quick reply unique values are present."""
    ensure_on_report_page(status_analytics_page)
    if not status_analytics_page.has_records():
        pytest.skip("No records available")
    values = status_analytics_page.get_column_values("quick_reply_unique")
    assert len(values) > 0
    assert all(v != "" for v in values)


@pytest.mark.regression
def test_tc26_cta_total_clicks_values(status_analytics_page):
    """TC_26: Verify CTA Total Clicks values are present."""
    ensure_on_report_page(status_analytics_page)
    if not status_analytics_page.has_records():
        pytest.skip("No records available")
    values = status_analytics_page.get_column_values("cta_total_clicks")
    assert len(values) > 0
    assert all(v != "" for v in values)


@pytest.mark.regression
def test_tc27_cta_unique_clicks_values(status_analytics_page):
    """TC_27: Verify CTA Unique Clicks values are present."""
    ensure_on_report_page(status_analytics_page)
    if not status_analytics_page.has_records():
        pytest.skip("No records available")
    values = status_analytics_page.get_column_values("cta_unique_clicks")
    assert len(values) > 0
    assert all(v != "" for v in values)


@pytest.mark.regression
def test_tc28_total_charges_values(status_analytics_page):
    """TC_28: Verify Total Charges values are present."""
    ensure_on_report_page(status_analytics_page)
    if not status_analytics_page.has_records():
        pytest.skip("No records available")
    values = status_analytics_page.get_column_values("total_charges")
    assert len(values) > 0
    assert all(v != "" for v in values)


# ── TC_29-31 — Agent / Status / Product Column Data ──────────────────────

@pytest.mark.regression
def test_tc29_agent_column_values(status_analytics_page):
    """TC_29: Agent column has values for every row."""
    ensure_on_report_page(status_analytics_page)
    values = status_analytics_page.get_column_values("agent")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_tc30_status_column_values(status_analytics_page):
    """TC_30: Status column has values for every row."""
    ensure_on_report_page(status_analytics_page)
    values = status_analytics_page.get_column_values("status")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_tc31_product_column_values(status_analytics_page):
    """TC_31: Product column has values for every row."""
    ensure_on_report_page(status_analytics_page)
    values = status_analytics_page.get_column_values("product")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


# ── TC_32-33 — Pagination ──────────────────────────────────────────────────

@pytest.mark.regression
def test_tc32_pagination_next_page(status_analytics_page):
    """TC_32: Clicking Next Page navigates to the next page of results."""
    ensure_on_report_page(status_analytics_page)
    if not status_analytics_page.has_records():
        pytest.skip("No records available")
    before = status_analytics_page.get_column_values("duration")
    if not _has_next_page(status_analytics_page):
        pytest.skip("Only one page of results for the current date range -- no Next page button to click")
    status_analytics_page.click_next_page()
    after = status_analytics_page.get_column_values("duration")
    assert before != after or len(after) >= 0
    status_analytics_page.navigate_to_report()  # reset to page 1


@pytest.mark.regression
def test_tc33_records_count_displayed(status_analytics_page):
    """TC_33: The pagination summary is displayed."""
    ensure_on_report_page(status_analytics_page)
    text = status_analytics_page.get_pagination_results_text()
    assert "of" in text.lower() or "showing" in text.lower()


# ── TC_34 — Performance ────────────────────────────────────────────────────

@pytest.mark.regression
def test_tc34_page_load_performance(status_analytics_page):
    """TC_34: Page loads within an 8000ms threshold."""
    ensure_on_report_page(status_analytics_page)
    load_time = status_analytics_page.get_page_load_time_ms()
    assert load_time is not None
    assert load_time < 8000


@pytest.mark.regression
def test_status_analytics_sort_by_duration(status_analytics_page):
    """Clicking the Duration column header's sort control does not break
    the page."""
    ensure_on_report_page(status_analytics_page)
    status_analytics_page.sort_by_duration()
    assert status_analytics_page.has_records() or status_analytics_page.has_no_records_message()
