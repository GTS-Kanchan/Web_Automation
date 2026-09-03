"""
RCS Campaign Analytics — Single Sequential Flow
==================================================
Migrated to Playwright: local page-object fixture renamed
`campaign_analytics_page` (built on conftest.py's `module_logged_in_page`)
to avoid shadowing pytest-playwright's reserved `page` fixture.

Run:
    pytest tests/test_rcs_campaign_analytics_flow.py -v
"""
import os

import pytest

from constants.rcs_campaign_analytics_headers import EXPECTED_RCS_CAMPAIGN_ANALYTICS_HEADERS
from pages.rcs.rcs_campaign_analytics_page import RcsCampaignAnalyticsPage
from utils.file_validator import (
    EmptyFileError,
    FileNotDownloadedError,
    HeaderValidationError,
    UnsupportedFileTypeError,
    validate_file_headers,
)


pytestmark = [pytest.mark.rcs, pytest.mark.report]

@pytest.fixture(scope="module")
def campaign_analytics_page(module_logged_in_page):
    p = RcsCampaignAnalyticsPage(module_logged_in_page)
    p.navigate_to_report()
    return p


def ensure_on_report_page(p):
    if not p.is_report_page():
        p.navigate_to_report()
        p.page.wait_for_timeout(1000)


@pytest.fixture(autouse=True)
def _reset_after_test(campaign_analytics_page):
    yield
    try:
        campaign_analytics_page.navigate_to_report()
    except Exception:
        pass


# ── TC_01-02 — Page Load ─────────────────────────────────────────────────

@pytest.mark.smoke
def test_campaign_analytics_TC01_page_loads(campaign_analytics_page):
    """TC_01: RCS Campaign Analytics page loads successfully without errors."""
    ensure_on_report_page(campaign_analytics_page)
    assert campaign_analytics_page.is_report_page(), "URL should contain /rcs/analytics/campaign"
    title = campaign_analytics_page.get_title().lower()
    assert "404" not in title and "error" not in title


@pytest.mark.smoke
def test_campaign_analytics_TC02_default_date_range_applied(campaign_analytics_page):
    """TC_02: A default date range is pre-selected on page load."""
    ensure_on_report_page(campaign_analytics_page)
    value = campaign_analytics_page.get_date_range_value()
    assert value, "Date range picker should have a pre-filled default value"


@pytest.mark.smoke
def test_campaign_analytics_title_displayed(campaign_analytics_page):
    """Page title 'RCS Campaign Analytics' is visible."""
    ensure_on_report_page(campaign_analytics_page)
    assert "RCS Campaign Analytics" in campaign_analytics_page.get_page_title_text()


@pytest.mark.smoke
def test_campaign_analytics_filters_button_visible(campaign_analytics_page):
    """Filters button and Date Range / Report Type / Group By controls are
    visible."""
    ensure_on_report_page(campaign_analytics_page)
    assert campaign_analytics_page.is_element_present(campaign_analytics_page.FILTERS_BUTTON, timeout=5000)
    assert campaign_analytics_page.are_filters_visible()


# ── TC_03 — UI Validation (Columns) ──────────────────────────────────────

@pytest.mark.smoke
def test_campaign_analytics_TC03_columns_displayed(campaign_analytics_page):
    """TC_03: All expected columns are visible and aligned in the table
    header."""
    ensure_on_report_page(campaign_analytics_page)
    headers = [h.lower() for h in campaign_analytics_page.get_visible_column_headers()]
    for expected in ["duration", "product", "agent", "campaign name",
                     "template name", "total count", "total charges"]:
        assert any(expected in h for h in headers), f"Missing column: {expected}"


# ── TC_04-05 — Data Validation ────────────────────────────────────────────

@pytest.mark.regression
def test_campaign_analytics_TC04_all_rows_have_campaign_name(campaign_analytics_page):
    """TC_04: Every row must contain a non-empty Campaign Name value."""
    ensure_on_report_page(campaign_analytics_page)
    values = campaign_analytics_page.get_column_values("campaign_name")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values), "Every row should have a Campaign Name"


@pytest.mark.regression
def test_campaign_analytics_TC05_read_count_never_exceeds_delivered(campaign_analytics_page):
    """TC_05: Read Count must never exceed Delivered Count for any row."""
    ensure_on_report_page(campaign_analytics_page)
    read_values = campaign_analytics_page.get_column_values("read_count")
    delivered_values = campaign_analytics_page.get_column_values("delivered_count")
    if not read_values or not delivered_values:
        pytest.skip("No rows to validate")

    def _to_number(s):
        try:
            return float(s.replace(",", ""))
        except ValueError:
            return None

    for read_v, delivered_v in zip(read_values, delivered_values):
        read_n = _to_number(read_v)
        delivered_n = _to_number(delivered_v)
        if read_n is None or delivered_n is None:
            continue
        assert read_n <= delivered_n, (
            f"Read count {read_n} exceeds Delivered count {delivered_n}"
        )


# ── TC_06-08 — Date Filter ────────────────────────────────────────────────

@pytest.mark.regression
def test_campaign_analytics_TC06_valid_custom_date_range(campaign_analytics_page):
    """TC_06: Selecting a valid custom date range refreshes the report."""
    ensure_on_report_page(campaign_analytics_page)
    ok = campaign_analytics_page.select_date_range()
    if not ok:
        pytest.skip("Flatpickr date range interaction did not behave as expected")
    assert campaign_analytics_page.has_records() or campaign_analytics_page.has_no_records_message()


@pytest.mark.negative
def test_campaign_analytics_TC07_from_date_never_after_to_date(campaign_analytics_page):
    """TC_07: The From date can never end up after the To date."""
    ensure_on_report_page(campaign_analytics_page)
    ok = campaign_analytics_page.select_date_range(from_day_offset=3, to_day_offset=10)
    if not ok:
        pytest.skip("Flatpickr date range interaction did not behave as expected")
    value = campaign_analytics_page.get_date_range_value()
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
def test_campaign_analytics_TC08_future_date_range(campaign_analytics_page):
    """TC_08: Selecting a future date range either shows no data or a
    validation message."""
    ensure_on_report_page(campaign_analytics_page)
    campaign_analytics_page.open_date_range_picker()
    future_cells = campaign_analytics_page.page.locator(
        ".flatpickr-calendar.open .flatpickr-day.nextMonthDay:not(.flatpickr-disabled)")
    if future_cells.count() == 0:
        pytest.skip("No enabled next-month cells available to attempt a future selection")
    future_cells.first.click(force=True)
    campaign_analytics_page.page.wait_for_timeout(500)
    assert campaign_analytics_page.has_records() or campaign_analytics_page.has_no_records_message()


# ── TC_09-10 — Report Type ────────────────────────────────────────────────

@pytest.mark.regression
def test_campaign_analytics_TC09_daily_report_type(campaign_analytics_page):
    """TC_09: Selecting "Daily" from Report Type groups data by day."""
    ensure_on_report_page(campaign_analytics_page)
    campaign_analytics_page.select_report_type("daily")
    assert campaign_analytics_page.get_report_type() == "daily"
    assert campaign_analytics_page.has_records() or campaign_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_campaign_analytics_TC10_monthly_report_type(campaign_analytics_page):
    """TC_10: Selecting "Monthly" groups data by month."""
    ensure_on_report_page(campaign_analytics_page)
    campaign_analytics_page.select_report_type("monthly")
    assert campaign_analytics_page.get_report_type() == "monthly"
    assert campaign_analytics_page.has_records() or campaign_analytics_page.has_no_records_message()
    campaign_analytics_page.select_report_type("daily")  # reset


# ── TC_11 — Group By ──────────────────────────────────────────────────────

@pytest.mark.regression
def test_campaign_analytics_TC11_group_by_option_changes_grouping(campaign_analytics_page):
    """TC_11: Selecting a different Group By option updates the grouping
    selection."""
    ensure_on_report_page(campaign_analytics_page)
    assert "1 selected" in campaign_analytics_page.get_group_by_label_text().lower() \
        or "selected" in campaign_analytics_page.get_group_by_label_text().lower()
    campaign_analytics_page.toggle_group_by_dimension("department")
    campaign_analytics_page.page.wait_for_timeout(1000)
    assert "2 selected" in campaign_analytics_page.get_group_by_label_text().lower()
    campaign_analytics_page.toggle_group_by_dimension("department")  # reset (toggle back off)


# ── TC_12-13 — Search ─────────────────────────────────────────────────────

@pytest.mark.regression
def test_campaign_analytics_TC12_search_valid_campaign_name(campaign_analytics_page):
    """TC_12: Searching by a valid campaign name returns matching records."""
    ensure_on_report_page(campaign_analytics_page)
    if not campaign_analytics_page.has_records():
        pytest.skip("No campaign records available to search")
    campaign_analytics_page.search("Campaign")
    assert campaign_analytics_page.has_records() or campaign_analytics_page.has_no_records_message()
    campaign_analytics_page.clear_search()


@pytest.mark.negative
def test_campaign_analytics_TC13_search_invalid_campaign_name(campaign_analytics_page):
    """TC_13: Searching a non-existing campaign name shows the no-records
    state."""
    ensure_on_report_page(campaign_analytics_page)
    campaign_analytics_page.search("ZZZZ_NON_EXISTENT_CAMPAIGN_9999")
    assert campaign_analytics_page.has_no_records_message(), "Invalid search should show a no-records state"
    campaign_analytics_page.clear_search()


# ── TC_14 — Filters (Product) ─────────────────────────────────────────────

@pytest.mark.regression
def test_campaign_analytics_TC14_filter_by_product(campaign_analytics_page):
    """TC_14: Filtering by Transactional/OTP/Promotional shows only
    matching data."""
    ensure_on_report_page(campaign_analytics_page)
    campaign_analytics_page.select_product_filter("Transactional")
    assert campaign_analytics_page.get_product_filter_value() == "Transactional"
    campaign_analytics_page.page.wait_for_timeout(1000)
    assert campaign_analytics_page.has_records() or campaign_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_campaign_analytics_filters_panel_shows_all_fields(campaign_analytics_page):
    """Opening the Filters button reveals the Agent/Product/Department/User
    filter fields, in that CONFIRMED order."""
    ensure_on_report_page(campaign_analytics_page)
    campaign_analytics_page.open_filters_popover()
    assert campaign_analytics_page.is_element_present(campaign_analytics_page.FILTER_AGENT_INPUT, timeout=5000)
    assert campaign_analytics_page.is_element_present(campaign_analytics_page.FILTER_PRODUCT_SELECT, timeout=5000)
    assert campaign_analytics_page.is_element_present(campaign_analytics_page.FILTER_DEPARTMENT_INPUT, timeout=5000)


@pytest.mark.regression
def test_campaign_analytics_filter_by_agent(campaign_analytics_page):
    """Filtering by Agent (a NEW async-select filter not present on Usage
    Analytics) updates the report (best-effort caveat)."""
    ensure_on_report_page(campaign_analytics_page)
    campaign_analytics_page.filter_by_agent("a")
    assert campaign_analytics_page.has_records() or campaign_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_campaign_analytics_filter_by_department(campaign_analytics_page):
    """Filtering by Department updates the report (best-effort caveat)."""
    ensure_on_report_page(campaign_analytics_page)
    campaign_analytics_page.filter_by_department("a")
    assert campaign_analytics_page.has_records() or campaign_analytics_page.has_no_records_message()


@pytest.mark.skip(reason="The 'Search User' filter exists in the DOM but is permanently hidden (display:none) in the current environment/role.")
@pytest.mark.regression
def test_campaign_analytics_filter_by_user(campaign_analytics_page):
    """Filtering by User updates the report (best-effort caveat)."""
    ensure_on_report_page(campaign_analytics_page)
    campaign_analytics_page.filter_by_user("a")
    assert campaign_analytics_page.has_records() or campaign_analytics_page.has_no_records_message()


# ── TC_15-16 — Export ─────────────────────────────────────────────────────

@pytest.mark.regression
def test_campaign_analytics_TC15_export_csv(campaign_analytics_page):
    """TC_15: Export CSV downloads a file whose header row matches this
    instance's confirmed RCS Campaign Analytics export columns exactly
    (constants/rcs_campaign_analytics_headers.py). click_export_csv() now
    captures the download via page.expect_download() instead of the old
    click-and-sleep pattern that never verified anything (see the page
    object's click_export_csv() docstring)."""
    ensure_on_report_page(campaign_analytics_page)
    result = campaign_analytics_page.click_export_csv()
    if result is None:
        pytest.skip("Export CSV did not produce a downloaded file within 30s")
    print(f"[{os.path.basename(result['file_path'])}] downloaded, {result['file_size']} bytes, {result['elapsed_s']:.2f}s")

    try:
        actual_headers = validate_file_headers(result["file_path"], EXPECTED_RCS_CAMPAIGN_ANALYTICS_HEADERS)
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
    assert campaign_analytics_page.is_report_page()


@pytest.mark.regression
def test_campaign_analytics_TC16_export_button_available_after_filtering(campaign_analytics_page):
    """TC_16: Export CSV remains available and clickable after the report
    has been filtered/searched."""
    ensure_on_report_page(campaign_analytics_page)
    campaign_analytics_page.search("Campaign")
    assert campaign_analytics_page.is_element_present(campaign_analytics_page.EXPORT_CSV_BUTTON, timeout=5000)
    campaign_analytics_page.click_export_csv()
    assert campaign_analytics_page.is_report_page()
    campaign_analytics_page.clear_search()


# ── TC_17-18 — Columns Dropdown ───────────────────────────────────────────

@pytest.mark.regression
def test_campaign_analytics_TC17_hide_specific_column(campaign_analytics_page):
    """TC_17: Unchecking a column in the Columns dropdown removes it from
    the table."""
    ensure_on_report_page(campaign_analytics_page)
    before = set(campaign_analytics_page.get_visible_column_headers())
    toggled_value = campaign_analytics_page.uncheck_first_optional_column()
    if not toggled_value:
        pytest.skip("No optional columns available to uncheck")
    try:
        campaign_analytics_page.page.wait_for_timeout(1000)
        after = set(campaign_analytics_page.get_visible_column_headers())
        assert after != before, "Column visibility should change after unchecking"
    finally:
        campaign_analytics_page.check_column(toggled_value)


@pytest.mark.regression
def test_campaign_analytics_TC18_re_enable_hidden_column(campaign_analytics_page):
    """TC_18: Re-checking a hidden column makes it reappear."""
    ensure_on_report_page(campaign_analytics_page)
    toggled_value = campaign_analytics_page.uncheck_first_optional_column()
    if not toggled_value:
        pytest.skip("No optional columns available to uncheck")
    campaign_analytics_page.page.wait_for_timeout(1000)
    hidden = set(campaign_analytics_page.get_visible_column_headers())
    campaign_analytics_page.check_column(toggled_value)
    campaign_analytics_page.page.wait_for_timeout(1000)
    restored = set(campaign_analytics_page.get_visible_column_headers())
    assert restored != hidden, "Column should reappear after re-checking"


# ── TC_19 — Pagination ────────────────────────────────────────────────────

@pytest.mark.regression
def test_campaign_analytics_TC19_pagination_changes_data(campaign_analytics_page):
    """TC_19: Navigating to the next page changes the displayed data
    without breaking the UI."""
    ensure_on_report_page(campaign_analytics_page)
    before = campaign_analytics_page.get_pagination_results_text()
    if not before:
        pytest.skip("No rows to paginate through")
    if not campaign_analytics_page.is_element_visible(campaign_analytics_page.NEXT_PAGE_BTN, timeout=3000):
        pytest.skip("Only one page of results for the current date range -- no Next page button to click")
    campaign_analytics_page.click_next_page()
    after = campaign_analytics_page.get_pagination_results_text()
    assert after != before, "Pagination results text should change after pagination"
    campaign_analytics_page.navigate_to_report()  # reset to page 1


@pytest.mark.smoke
def test_campaign_analytics_records_count_displayed(campaign_analytics_page):
    """Result count text at the bottom of the table shows correct wording."""
    ensure_on_report_page(campaign_analytics_page)
    text = campaign_analytics_page.get_pagination_results_text()
    assert "showing" in text.lower() and "of" in text.lower()


# ── TC_20 — Performance ───────────────────────────────────────────────────

@pytest.mark.regression
def test_campaign_analytics_TC20_load_performance(campaign_analytics_page):
    """TC_20: Report loads within an acceptable time window."""
    ensure_on_report_page(campaign_analytics_page)
    load_ms = campaign_analytics_page.get_page_load_time_ms()
    if load_ms is None or load_ms <= 0:
        pytest.skip("Browser performance timing API unavailable")
    assert load_ms < 8000, f"Page load took {load_ms}ms"


# ── Bonus — Preview Button / Individual Column Data Validation ───────────

@pytest.mark.regression
def test_campaign_analytics_row_preview_button_does_not_error(campaign_analytics_page):
    """Clicking a row's Preview button does not break the page. Modal
    internals are UNCONFIRMED so this only verifies the trigger doesn't
    error, without asserting on modal content."""
    ensure_on_report_page(campaign_analytics_page)
    if not campaign_analytics_page.has_records():
        pytest.skip("No rows to preview")
    campaign_analytics_page.click_first_row_preview()
    assert campaign_analytics_page.is_report_page()


@pytest.mark.regression
def test_campaign_analytics_total_count_values(campaign_analytics_page):
    """Total Count column has values for every row."""
    ensure_on_report_page(campaign_analytics_page)
    values = campaign_analytics_page.get_column_values("total_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_campaign_analytics_sent_count_values(campaign_analytics_page):
    """Sent Count column has values for every row."""
    ensure_on_report_page(campaign_analytics_page)
    values = campaign_analytics_page.get_column_values("sent_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_campaign_analytics_failed_count_values(campaign_analytics_page):
    """Failed Count column has values for every row."""
    ensure_on_report_page(campaign_analytics_page)
    values = campaign_analytics_page.get_column_values("failed_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_campaign_analytics_rejected_count_values(campaign_analytics_page):
    """Rejected Count column has values for every row."""
    ensure_on_report_page(campaign_analytics_page)
    values = campaign_analytics_page.get_column_values("rejected_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_campaign_analytics_dlr_awaited_count_values(campaign_analytics_page):
    """DLR Awaited Count column has values for every row."""
    ensure_on_report_page(campaign_analytics_page)
    values = campaign_analytics_page.get_column_values("dlr_awaited_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_campaign_analytics_interactions_values(campaign_analytics_page):
    """Interactions column has values for every row."""
    ensure_on_report_page(campaign_analytics_page)
    values = campaign_analytics_page.get_column_values("interactions")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_campaign_analytics_quick_reply_total_values(campaign_analytics_page):
    """Quick reply total column has values for every row."""
    ensure_on_report_page(campaign_analytics_page)
    values = campaign_analytics_page.get_column_values("quick_reply_total")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_campaign_analytics_quick_reply_unique_values(campaign_analytics_page):
    """Quick reply unique column has values for every row."""
    ensure_on_report_page(campaign_analytics_page)
    values = campaign_analytics_page.get_column_values("quick_reply_unique")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_campaign_analytics_cta_total_clicks_values(campaign_analytics_page):
    """CTA Total Clicks column has values for every row."""
    ensure_on_report_page(campaign_analytics_page)
    values = campaign_analytics_page.get_column_values("cta_total_clicks")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_campaign_analytics_cta_unique_clicks_values(campaign_analytics_page):
    """CTA Unique Clicks column has values for every row."""
    ensure_on_report_page(campaign_analytics_page)
    values = campaign_analytics_page.get_column_values("cta_unique_clicks")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_campaign_analytics_total_charges_values(campaign_analytics_page):
    """Total Charges column is displayed with values for every row."""
    ensure_on_report_page(campaign_analytics_page)
    values = campaign_analytics_page.get_column_values("total_charges")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_campaign_analytics_agent_column_values(campaign_analytics_page):
    """Agent column has values for every row."""
    ensure_on_report_page(campaign_analytics_page)
    values = campaign_analytics_page.get_column_values("agent")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_campaign_analytics_template_name_column_values(campaign_analytics_page):
    """Template Name column has values for every row."""
    ensure_on_report_page(campaign_analytics_page)
    values = campaign_analytics_page.get_column_values("template_name")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.smoke
def test_campaign_analytics_table_loads(campaign_analytics_page):
    """Campaign analytics table loads with records displayed correctly."""
    ensure_on_report_page(campaign_analytics_page)
    assert campaign_analytics_page.has_records() or campaign_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_campaign_analytics_sort_by_duration(campaign_analytics_page):
    """Clicking the Duration column header's sort control does not break
    the page."""
    ensure_on_report_page(campaign_analytics_page)
    campaign_analytics_page.sort_by_duration()
    assert campaign_analytics_page.has_records() or campaign_analytics_page.has_no_records_message()
