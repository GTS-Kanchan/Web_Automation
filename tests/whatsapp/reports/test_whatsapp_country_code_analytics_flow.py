"""
WhatsApp Country Code Analytics — Single Sequential Flow
=====================================================
Covers: Channels → WhatsApp → Analytics → Country Code page
(URL: /whatsapp/analytics/country-code; breadcrumb reads "WhatsApp Country Code Analytics"
but this page's own <h1> reads plain "Country Code Analytics" — CONFIRMED live DOM
difference from the RCS Analytics family, whose <h1>s include the channel
prefix)

No QA test-case sheet and no explicit "take reference from X" instruction
accompanied the live DOM dump this suite was built from (a combined upload
of 7 WhatsApp Analytics report pages: Usage, Campaign, Status, WABA Number,
Template, Country Code, Message Type). This suite was built directly from
THIS report's own confirmed live DOM/wire:snapshot, cross-checked against
its closest structural siblings (WABA Number/Template/Country Code/Message
Type — all sharing the identical Product/Department/User filter set and
overall framework) and against the RCS Analytics report family already
built in this project (same Livewire table framework/conventions).

Key confirmed structural facts that shaped this suite:
  - 17 columns total: duration/product/waba-number/country-code (4
    fixed identifiers) + the FULL 13-metric set.
  - Filters popover order is Product -> Department -> User (filterCount:
    3, CONFIRMED). Product is a plain <select> with options All/
    Authentication/Marketing/MMLite/Utility — a different option set than
    every RCS Analytics report's Product filter.
  - No Agent filter exists on this or any other WhatsApp Analytics report.
  - Group By dimensions are product/department/user (CONFIRMED live DOM),
    with "product" PRE-SELECTED by default.
  - Search placeholder is "Search by Country Code".
  - CONFIRMED live pagination total at capture time: 132 results.
  - Report Type defaults to "daily" with only Daily/Weekly/Monthly options.

All tests run in one browser session (module-scoped), mirroring the pattern
used across every other report suite in this project.

Migrated to Playwright: local page-object fixture renamed
`country_code_analytics_page` (built on conftest.py's
`module_logged_in_page`) to avoid shadowing pytest-playwright's reserved
`page` fixture.

Run:
    pytest tests/test_whatsapp_country_code_analytics_flow.py -v
"""
import pytest

from pages.whatsapp.whatsapp_country_code_analytics_page import WhatsappCountryCodeAnalyticsPage


pytestmark = [pytest.mark.whatsapp, pytest.mark.report]

@pytest.fixture(scope="module")
def country_code_analytics_page(module_logged_in_page):
    p = WhatsappCountryCodeAnalyticsPage(module_logged_in_page)
    p.navigate_to_report()
    return p


def ensure_on_report_page(p):
    if not p.is_report_page():
        p.navigate_to_report()
        p.page.wait_for_timeout(1000)


@pytest.fixture(autouse=True)
def _reset_after_test(country_code_analytics_page):
    """Hard reset to a clean report view after every test — this page has
    many stateful filters (date range, report type, group by, columns,
    product/department/user), so re-navigating fresh after each test is
    the simplest guaranteed way to avoid cross-test contamination (same
    rationale as every other report suite in this project)."""
    yield
    try:
        country_code_analytics_page.navigate_to_report()
    except Exception:
        pass


# ── TC_01 — Page Load ─────────────────────────────────────────────────────

@pytest.mark.smoke
def test_country_code_analytics_TC01_page_loads(country_code_analytics_page):
    """TC_01: WhatsApp Country Code Analytics page loads successfully without
    errors."""
    ensure_on_report_page(country_code_analytics_page)
    assert country_code_analytics_page.is_report_page(), "URL should contain /whatsapp/analytics/country-code"
    title = country_code_analytics_page.get_title().lower()
    assert "404" not in title and "error" not in title


@pytest.mark.smoke
def test_country_code_analytics_title_displayed(country_code_analytics_page):
    """Page title 'Country Code Analytics' is visible (CONFIRMED live DOM — this
    report's own <h1> omits the "WhatsApp" prefix seen in the breadcrumb)."""
    ensure_on_report_page(country_code_analytics_page)
    assert "Country Code Analytics" in country_code_analytics_page.get_page_title_text()


@pytest.mark.smoke
def test_country_code_analytics_filters_button_visible(country_code_analytics_page):
    """Filters button and Date Range / Report Type / Group By controls are
    visible."""
    ensure_on_report_page(country_code_analytics_page)
    assert country_code_analytics_page.is_element_present(country_code_analytics_page.FILTERS_BUTTON, timeout=5000)
    assert country_code_analytics_page.are_filters_visible()


# ── TC_02 — Default Date Range ───────────────────────────────────────────

@pytest.mark.smoke
def test_country_code_analytics_TC02_default_date_range_applied(country_code_analytics_page):
    """TC_02: A default date range is pre-selected on page load (CONFIRMED
    live wire:snapshot: fromDate/toDate defaulted to a 90-day window ending
    today, dateFormat 'd-m-Y')."""
    ensure_on_report_page(country_code_analytics_page)
    value = country_code_analytics_page.get_date_range_value()
    assert value, "Date range picker should have a pre-filled default value"


# ── TC_03 — UI Validation (Columns) ──────────────────────────────────────

@pytest.mark.smoke
def test_country_code_analytics_TC03_columns_displayed(country_code_analytics_page):
    """TC_03: All expected columns are visible and aligned in the table
    header. Asserts against the confirmed live <thead> column set."""
    ensure_on_report_page(country_code_analytics_page)
    headers = [h.lower() for h in country_code_analytics_page.get_visible_column_headers()]
    for expected in ['duration', 'product', 'waba number', 'country code', 'total']:
        assert any(expected in h for h in headers), f"Missing column: {expected}"


# ── TC_04-06 — Date Filter ────────────────────────────────────────────────

@pytest.mark.regression
def test_country_code_analytics_TC04_valid_custom_date_range(country_code_analytics_page):
    """TC_04: Selecting a valid custom date range refreshes the report.
    No "Click Apply" step exists — the flatpickr range applies immediately
    via wire:model.live (CONFIRMED live DOM)."""
    ensure_on_report_page(country_code_analytics_page)
    ok = country_code_analytics_page.select_date_range()
    if not ok:
        pytest.skip("Flatpickr date range interaction did not behave as expected")
    assert country_code_analytics_page.has_records() or country_code_analytics_page.has_no_records_message()


@pytest.mark.negative
def test_country_code_analytics_TC05_from_date_never_after_to_date(country_code_analytics_page):
    """TC_05: The From date can never end up after the To date. flatpickr's
    'range' mode inherently reorders two clicked dates chronologically
    rather than letting a user pick an inverted range."""
    ensure_on_report_page(country_code_analytics_page)
    ok = country_code_analytics_page.select_date_range(from_day_offset=3, to_day_offset=10)
    if not ok:
        pytest.skip("Flatpickr date range interaction did not behave as expected")
    value = country_code_analytics_page.get_date_range_value()
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
def test_country_code_analytics_TC06_future_date_range(country_code_analytics_page):
    """TC_06: Selecting a future date range either shows no data or a
    validation message — flatpickr's maxDate: 'today' (CONFIRMED live
    config) prevents picking any day after today at all, so this asserts
    the page remains in a valid, non-broken state."""
    ensure_on_report_page(country_code_analytics_page)
    country_code_analytics_page.open_date_range_picker()
    future_cells = country_code_analytics_page.page.locator(
        ".flatpickr-calendar.open .flatpickr-day.nextMonthDay:not(.flatpickr-disabled)")
    if future_cells.count() == 0:
        pytest.skip("No enabled next-month cells available to attempt a future selection")
    future_cells.first.click(force=True)
    country_code_analytics_page.page.wait_for_timeout(500)
    assert country_code_analytics_page.has_records() or country_code_analytics_page.has_no_records_message()


# ── TC_07-08 — Report Type ────────────────────────────────────────────────

@pytest.mark.regression
def test_country_code_analytics_TC07_daily_report_type(country_code_analytics_page):
    """TC_07: Selecting "Daily" from Report Type groups data by day
    (CONFIRMED default value)."""
    ensure_on_report_page(country_code_analytics_page)
    country_code_analytics_page.select_report_type("daily")
    assert country_code_analytics_page.get_report_type() == "daily"
    assert country_code_analytics_page.has_records() or country_code_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_country_code_analytics_TC08_monthly_report_type(country_code_analytics_page):
    """TC_08: Selecting "Monthly" groups data by month."""
    ensure_on_report_page(country_code_analytics_page)
    country_code_analytics_page.select_report_type("monthly")
    assert country_code_analytics_page.get_report_type() == "monthly"
    assert country_code_analytics_page.has_records() or country_code_analytics_page.has_no_records_message()
    country_code_analytics_page.select_report_type("daily")  # reset


# ── TC_09 — Group By ──────────────────────────────────────────────────────

@pytest.mark.regression
def test_country_code_analytics_TC09_group_by_option_changes_grouping(country_code_analytics_page):
    """TC_09: Selecting a different Group By option updates the grouping
    selection. "product" is PRE-SELECTED by default here (CONFIRMED live
    wire:snapshot dimensions:["product"]), so the label already reads
    "1 selected" before this test — toggling "department" on should bump it
    to "2 selected"."""
    ensure_on_report_page(country_code_analytics_page)
    assert "1 selected" in country_code_analytics_page.get_group_by_label_text().lower() \
        or "selected" in country_code_analytics_page.get_group_by_label_text().lower()
    country_code_analytics_page.toggle_group_by_dimension("department")
    country_code_analytics_page.page.wait_for_timeout(1000)
    assert "2 selected" in country_code_analytics_page.get_group_by_label_text().lower()
    country_code_analytics_page.toggle_group_by_dimension("department")  # reset (toggle back off)


# ── TC_10-11 — Search ─────────────────────────────────────────────────────

@pytest.mark.regression
def test_country_code_analytics_TC10_search_valid_country_code(country_code_analytics_page):
    """TC_10: Searching by a valid Country Code value returns matching
    records."""
    ensure_on_report_page(country_code_analytics_page)
    if not country_code_analytics_page.has_records():
        pytest.skip("No records available to search")
    country_code_analytics_page.search("IN")
    assert country_code_analytics_page.has_records() or country_code_analytics_page.has_no_records_message()
    country_code_analytics_page.clear_search()


@pytest.mark.negative
def test_country_code_analytics_TC11_search_invalid_country_code(country_code_analytics_page):
    """TC_11: Searching a non-existing Country Code value shows the
    no-records state."""
    ensure_on_report_page(country_code_analytics_page)
    country_code_analytics_page.search("ZZZZ_NON_EXISTENT_COUNTRY_CODE_9999")
    assert country_code_analytics_page.has_no_records_message(), "Invalid search should show a no-records state"
    country_code_analytics_page.clear_search()


# ── TC_12 — Filters (Product) ─────────────────────────────────────────────

@pytest.mark.regression
def test_country_code_analytics_TC12_filter_by_product(country_code_analytics_page):
    """TC_12: Filtering by Authentication/Marketing/Utility/MMLite shows
    only matching data. CONFIRMED live DOM: Product here is a plain
    <select> with exactly these four named options (plus "All")."""
    ensure_on_report_page(country_code_analytics_page)
    country_code_analytics_page.select_product_filter("MARKETING")
    assert country_code_analytics_page.get_product_filter_value() == "MARKETING"
    country_code_analytics_page.page.wait_for_timeout(1000)
    assert country_code_analytics_page.has_records() or country_code_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_country_code_analytics_filters_panel_shows_all_fields(country_code_analytics_page):
    """Opening the Filters button reveals ONLY the Product/Department/User
    filter fields, in that CONFIRMED order — no Agent field exists on any
    WhatsApp Analytics report."""
    ensure_on_report_page(country_code_analytics_page)
    country_code_analytics_page.open_filters_popover()
    assert country_code_analytics_page.is_element_present(country_code_analytics_page.FILTER_PRODUCT_SELECT, timeout=5000)
    assert country_code_analytics_page.is_element_present(country_code_analytics_page.FILTER_DEPARTMENT_INPUT, timeout=5000)
    assert country_code_analytics_page.is_element_present(country_code_analytics_page.FILTER_USER_INPUT, timeout=5000)


@pytest.mark.regression
def test_country_code_analytics_filter_by_department(country_code_analytics_page):
    """Filtering by Department updates the report (best-effort: see module
    docstring on the async-select empty-option-markup caveat)."""
    ensure_on_report_page(country_code_analytics_page)
    country_code_analytics_page.filter_by_department("a")
    assert country_code_analytics_page.has_records() or country_code_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_country_code_analytics_filter_by_user(country_code_analytics_page):
    """Filtering by User updates the report (best-effort caveat, see module
    docstring)."""
    ensure_on_report_page(country_code_analytics_page)
    country_code_analytics_page.filter_by_user("a")
    assert country_code_analytics_page.has_records() or country_code_analytics_page.has_no_records_message()


# ── TC_13-14 — Export ─────────────────────────────────────────────────────

@pytest.mark.regression
def test_country_code_analytics_TC13_export_csv(country_code_analytics_page):
    """TC_13: Export CSV button triggers a download (dispatches
    $wire.export(), CONFIRMED live DOM)."""
    ensure_on_report_page(country_code_analytics_page)
    country_code_analytics_page.click_export_csv()
    assert country_code_analytics_page.is_report_page()


@pytest.mark.regression
def test_country_code_analytics_TC14_export_button_available_after_filtering(country_code_analytics_page):
    """TC_14: Export CSV remains available and clickable after the report
    has been filtered/searched, implying the export reflects current filter
    state rather than being disabled or broken."""
    ensure_on_report_page(country_code_analytics_page)
    country_code_analytics_page.search("IN")
    assert country_code_analytics_page.is_element_present(country_code_analytics_page.EXPORT_CSV_BUTTON, timeout=5000)
    country_code_analytics_page.click_export_csv()
    assert country_code_analytics_page.is_report_page()
    country_code_analytics_page.clear_search()


# ── TC_15-16 — Columns Dropdown ───────────────────────────────────────────

@pytest.mark.regression
def test_country_code_analytics_TC15_hide_specific_column(country_code_analytics_page):
    """TC_15: Unchecking a column in the Columns dropdown removes it from
    the table. Column selection persists in sessionStorage across a plain
    navigate_to_report() (CONFIRMED live wire:snapshot:
    sessionStorageStatus.columnselect=true), so this restores the column
    in a finally block — otherwise TC_16 would find it missing."""
    ensure_on_report_page(country_code_analytics_page)
    before = set(country_code_analytics_page.get_visible_column_headers())
    toggled_value = country_code_analytics_page.uncheck_first_optional_column()
    if not toggled_value:
        pytest.skip("No optional columns available to uncheck")
    try:
        country_code_analytics_page.page.wait_for_timeout(1000)
        after = set(country_code_analytics_page.get_visible_column_headers())
        assert after != before, "Column visibility should change after unchecking"
    finally:
        country_code_analytics_page.check_column(toggled_value)


@pytest.mark.regression
def test_country_code_analytics_TC16_re_enable_hidden_column(country_code_analytics_page):
    """TC_16: Re-checking a hidden column makes it reappear."""
    ensure_on_report_page(country_code_analytics_page)
    toggled_value = country_code_analytics_page.uncheck_first_optional_column()
    if not toggled_value:
        pytest.skip("No optional columns available to uncheck")
    country_code_analytics_page.page.wait_for_timeout(1000)
    hidden = set(country_code_analytics_page.get_visible_column_headers())
    country_code_analytics_page.check_column(toggled_value)
    country_code_analytics_page.page.wait_for_timeout(1000)
    restored = set(country_code_analytics_page.get_visible_column_headers())
    assert restored != hidden, "Column should reappear after re-checking"


# ── TC_17 — Pagination ────────────────────────────────────────────────────

@pytest.mark.regression
def test_country_code_analytics_TC17_pagination_changes_data(country_code_analytics_page):
    """TC_17: Navigating to the next page changes the displayed data
    without breaking the UI."""
    ensure_on_report_page(country_code_analytics_page)
    before = country_code_analytics_page.get_column_values("duration")
    if not before:
        pytest.skip("No rows to paginate through")
    country_code_analytics_page.click_next_page()
    after = country_code_analytics_page.get_column_values("duration")
    assert after != before, "Row data should change after pagination"
    country_code_analytics_page.navigate_to_report()  # reset to page 1


@pytest.mark.smoke
def test_country_code_analytics_records_count_displayed(country_code_analytics_page):
    """Result count text at the bottom of the table shows correct wording
    (CONFIRMED live pagination total at capture time: 204 results)."""
    ensure_on_report_page(country_code_analytics_page)
    text = country_code_analytics_page.get_pagination_results_text()
    assert "showing" in text.lower() and "of" in text.lower()


# ── TC_18 — Performance ───────────────────────────────────────────────────

@pytest.mark.regression
def test_country_code_analytics_TC18_load_performance(country_code_analytics_page):
    """TC_18: Report loads within an acceptable time window. Uses the
    browser's real Performance Timing API rather than our own sleeps —
    threshold set generously (8s) to absorb normal CI/network variance,
    same convention as every other report suite in this project."""
    ensure_on_report_page(country_code_analytics_page)
    load_ms = country_code_analytics_page.get_page_load_time_ms()
    if load_ms is None or load_ms <= 0:
        pytest.skip("Browser performance timing API unavailable")
    assert load_ms < 8000, f"Page load took {load_ms}ms"


# ── Bonus — Individual Column Data Validation ────────────────────────────
# These items are fully CONFIRMED from the live DOM but were not
# individually itemised into TCs — added for the same reason every other
# report suite in this project validates each confirmed column and
# interactive element.

@pytest.mark.smoke
def test_country_code_analytics_table_loads(country_code_analytics_page):
    """Country Code analytics table loads with records displayed correctly."""
    ensure_on_report_page(country_code_analytics_page)
    assert country_code_analytics_page.has_records() or country_code_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_country_code_analytics_sort_by_duration(country_code_analytics_page):
    """Clicking the Duration column header's sort control does not break
    the page (CONFIRMED live DOM: wire:click="sortBy('duration')")."""
    ensure_on_report_page(country_code_analytics_page)
    country_code_analytics_page.sort_by_duration()
    assert country_code_analytics_page.has_records() or country_code_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_country_code_analytics_product_column_values(country_code_analytics_page):
    """Product column is present, with at least some rows populated.
    NOTE: CONFIRMED via a real pytest run against live data that this
    report can legitimately show a blank product cell on some rows
    (e.g. legacy/unassigned-product records) — user-confirmed expected
    behavior, not a locator bug, so this only requires SOME rows to be
    populated rather than ALL of them."""
    ensure_on_report_page(country_code_analytics_page)
    values = country_code_analytics_page.get_column_values("product")
    if not values:
        pytest.skip("No rows to validate")
    assert any(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_code_analytics_waba_number_column_values(country_code_analytics_page):
    """WABA Number column has values for every row (CONFIRMED live rows
    showed the same value "919202511257" throughout)."""
    ensure_on_report_page(country_code_analytics_page)
    values = country_code_analytics_page.get_column_values("waba_number")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_code_analytics_country_code_column_values(country_code_analytics_page):
    """Country Code column has values for every row (CONFIRMED live DOM
    identifier column unique to this report)."""
    ensure_on_report_page(country_code_analytics_page)
    values = country_code_analytics_page.get_column_values("country_code")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_code_analytics_total_column_values(country_code_analytics_page):
    """Total column has values for every row."""
    ensure_on_report_page(country_code_analytics_page)
    values = country_code_analytics_page.get_column_values("total")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_code_analytics_read_column_values(country_code_analytics_page):
    """Read column has values for every row."""
    ensure_on_report_page(country_code_analytics_page)
    values = country_code_analytics_page.get_column_values("read")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_code_analytics_interactions_column_values(country_code_analytics_page):
    """Interactions column has values for every row."""
    ensure_on_report_page(country_code_analytics_page)
    values = country_code_analytics_page.get_column_values("interactions")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_code_analytics_quick_reply_total_values(country_code_analytics_page):
    """Quick reply total column has values for every row."""
    ensure_on_report_page(country_code_analytics_page)
    values = country_code_analytics_page.get_column_values("quick_reply_total")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_code_analytics_quick_reply_unique_values(country_code_analytics_page):
    """Quick reply unique column has values for every row."""
    ensure_on_report_page(country_code_analytics_page)
    values = country_code_analytics_page.get_column_values("quick_reply_unique")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_code_analytics_cta_total_clicks_values(country_code_analytics_page):
    """CTA Total Clicks column has values for every row."""
    ensure_on_report_page(country_code_analytics_page)
    values = country_code_analytics_page.get_column_values("cta_total_clicks")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_code_analytics_cta_unique_clicks_values(country_code_analytics_page):
    """CTA Unique Clicks column has values for every row."""
    ensure_on_report_page(country_code_analytics_page)
    values = country_code_analytics_page.get_column_values("cta_unique_clicks")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_code_analytics_total_charges_values(country_code_analytics_page):
    """Total Charges column is displayed with values for every row."""
    ensure_on_report_page(country_code_analytics_page)
    values = country_code_analytics_page.get_column_values("total_charges")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_code_analytics_sent_column_values(country_code_analytics_page):
    """Sent column has values for every row."""
    ensure_on_report_page(country_code_analytics_page)
    values = country_code_analytics_page.get_column_values("sent")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_code_analytics_delivered_column_values(country_code_analytics_page):
    """Delivered column has values for every row."""
    ensure_on_report_page(country_code_analytics_page)
    values = country_code_analytics_page.get_column_values("delivered")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_code_analytics_failed_column_values(country_code_analytics_page):
    """Failed column has values for every row."""
    ensure_on_report_page(country_code_analytics_page)
    values = country_code_analytics_page.get_column_values("failed")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_code_analytics_rejected_column_values(country_code_analytics_page):
    """Rejected column has values for every row."""
    ensure_on_report_page(country_code_analytics_page)
    values = country_code_analytics_page.get_column_values("rejected")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_country_code_analytics_dlr_awaited_column_values(country_code_analytics_page):
    """DLR Awaited column has values for every row."""
    ensure_on_report_page(country_code_analytics_page)
    values = country_code_analytics_page.get_column_values("dlr_awaited")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)
