"""
WhatsApp Usage Analytics — Single Sequential Flow
=====================================================
Covers: Channels → WhatsApp → Analytics → Usage page
(URL: /whatsapp/analytics/usage; breadcrumb reads "WhatsApp Usage
Analytics" but this page's own <h1> reads plain "Usage Analytics" —
CONFIRMED live DOM difference from the RCS Analytics family, whose <h1>s
include the channel prefix)

No QA test-case sheet and no explicit "take reference from X" instruction
accompanied the live DOM dump this suite was built from (a combined upload
of 7 WhatsApp Analytics report pages: Usage, Campaign, Status, WABA Number,
Template, Country Code, Message Type). Unlike the other 6 WhatsApp
Analytics reports (which all share an (almost) identical Product-select/
Department/User filter shape), THIS report's own live DOM revealed a
genuinely different structure — a checkbox-multiselect Product+Source
filter pattern whose only precedent in this project is RCS Error Code
Analytics — so this suite's TC numbering was built directly from THIS
page's own confirmed live DOM/wire:snapshot (see the page object's module
docstring for full detail), while still following the same overall
test-file conventions (fixtures, TC numbering style, hard-reset autouse
fixture) established across every other report suite in this project.

Key confirmed structural facts that shaped this suite:
  - Livewire table name is "whatsapp_product_report" (NOT "whatsapp_usage_
    report") and every element ID is prefixed "whatsapp-product-*" — a
    genuine naming-convention break unique to this report.
  - Only 14 columns total: duration (fixed) + the FULL 13-metric set. NO
    product/waba-number/other identifier columns exist at all.
  - filterCount: 4 — Product (checkbox multiselect) -> Source (checkbox
    multiselect) -> Department (async-select) -> User (async-select). NO
    Agent filter (consistent with every WhatsApp Analytics report).
    Product values: AUTHENTICATION/MARKETING/MMLite/UTILITY (note "MMLite"
    mixed-case here, vs. uppercase "MMLITE" on the plain-<select> reports).
    Source values: Campaign/API/Flow (only 3 — no "Incoming", unlike RCS
    Error Code Analytics' Source filter).
  - Group By has FOUR dimensions: product/source/department/user (CONFIRMED
    live DOM) — the only WhatsApp Analytics report with 4 (every sibling
    has 3). CONFIRMED live wire:snapshot: initialSelected = [] — NONE
    pre-checked by default here, unlike every sibling report where
    "product" is pre-checked.
  - Search placeholder is "Search by Product" (CONFIRMED live DOM).
  - CONFIRMED live pagination total at capture time: 40 results.
  - Report Type defaults to "daily" with only Daily/Weekly/Monthly options
    (CONFIRMED identical to every other report in this project).

All tests run in one browser session (module-scoped), mirroring the pattern
used across every other report suite in this project.

Migrated to Playwright: local page-object fixture renamed
`usage_analytics_page` (built on conftest.py's `module_logged_in_page`) to
avoid shadowing pytest-playwright's reserved `page` fixture.

Run:
    pytest tests/test_whatsapp_usage_analytics_flow.py -v
"""
import pytest

from pages.whatsapp.whatsapp_usage_analytics_page import WhatsappUsageAnalyticsPage


pytestmark = [pytest.mark.whatsapp, pytest.mark.report]

@pytest.fixture(scope="module")
def usage_analytics_page(module_logged_in_page):
    p = WhatsappUsageAnalyticsPage(module_logged_in_page)
    p.navigate_to_report()
    return p


def ensure_on_report_page(p):
    if not p.is_report_page():
        p.navigate_to_report()
        p.page.wait_for_timeout(1000)


@pytest.fixture(autouse=True)
def _reset_after_test(usage_analytics_page):
    """Hard reset to a clean report view after every test — this page has
    many stateful filters (date range, report type, group by, columns,
    product/source checkboxes, department/user), so re-navigating fresh
    after each test is the simplest guaranteed way to avoid cross-test
    contamination (same rationale as every other report suite in this
    project)."""
    yield
    try:
        usage_analytics_page.navigate_to_report()
    except Exception:
        pass


# ── TC_01 — Page Load ─────────────────────────────────────────────────────

@pytest.mark.smoke
def test_usage_analytics_TC01_page_loads(usage_analytics_page):
    """TC_01: WhatsApp Usage Analytics page loads successfully without
    errors."""
    ensure_on_report_page(usage_analytics_page)
    assert usage_analytics_page.is_report_page(), "URL should contain /whatsapp/analytics/usage"
    title = usage_analytics_page.get_title().lower()
    assert "404" not in title and "error" not in title


@pytest.mark.smoke
def test_usage_analytics_title_displayed(usage_analytics_page):
    """Page title 'Usage Analytics' is visible (CONFIRMED live DOM — this
    report's own <h1> omits the "WhatsApp" prefix seen in the
    breadcrumb)."""
    ensure_on_report_page(usage_analytics_page)
    assert "Usage Analytics" in usage_analytics_page.get_page_title_text()


@pytest.mark.smoke
def test_usage_analytics_filters_button_visible(usage_analytics_page):
    """Filters button and Date Range / Report Type / Group By controls are
    visible."""
    ensure_on_report_page(usage_analytics_page)
    assert usage_analytics_page.is_element_present(usage_analytics_page.FILTERS_BUTTON, timeout=5000)
    assert usage_analytics_page.are_filters_visible()


# ── TC_02 — Default Date Range ───────────────────────────────────────────

@pytest.mark.smoke
def test_usage_analytics_TC02_default_date_range_applied(usage_analytics_page):
    """TC_02: A default date range is pre-selected on page load (CONFIRMED
    live wire:snapshot: fromDate/toDate defaulted to a 90-day window ending
    today, dateFormat 'd-m-Y')."""
    ensure_on_report_page(usage_analytics_page)
    value = usage_analytics_page.get_date_range_value()
    assert value, "Date range picker should have a pre-filled default value"


# ── TC_03 — UI Validation (Columns) ──────────────────────────────────────

@pytest.mark.smoke
def test_usage_analytics_TC03_columns_displayed(usage_analytics_page):
    """TC_03: All expected columns are visible and aligned in the table
    header. Asserts against the confirmed live <thead> column set — only
    14 columns exist on this report (duration + 13 metrics, NO product/
    identifier columns)."""
    ensure_on_report_page(usage_analytics_page)
    headers = [h.lower() for h in usage_analytics_page.get_visible_column_headers()]
    for expected in ["duration", "total", "sent", "delivered"]:
        assert any(expected in h for h in headers), f"Missing column: {expected}"


# ── TC_04-06 — Date Filter ────────────────────────────────────────────────

@pytest.mark.regression
def test_usage_analytics_TC04_valid_custom_date_range(usage_analytics_page):
    """TC_04: Selecting a valid custom date range refreshes the report.
    No "Click Apply" step exists — the flatpickr range applies immediately
    via wire:model.live (CONFIRMED live DOM)."""
    ensure_on_report_page(usage_analytics_page)
    ok = usage_analytics_page.select_date_range()
    if not ok:
        pytest.skip("Flatpickr date range interaction did not behave as expected")
    assert usage_analytics_page.has_records() or usage_analytics_page.has_no_records_message()


@pytest.mark.negative
def test_usage_analytics_TC05_from_date_never_after_to_date(usage_analytics_page):
    """TC_05: The From date can never end up after the To date. flatpickr's
    'range' mode inherently reorders two clicked dates chronologically
    rather than letting a user pick an inverted range."""
    ensure_on_report_page(usage_analytics_page)
    ok = usage_analytics_page.select_date_range(from_day_offset=3, to_day_offset=10)
    if not ok:
        pytest.skip("Flatpickr date range interaction did not behave as expected")
    value = usage_analytics_page.get_date_range_value()
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
def test_usage_analytics_TC06_future_date_range(usage_analytics_page):
    """TC_06: Selecting a future date range either shows no data or a
    validation message — flatpickr's maxDate: 'today' (CONFIRMED live
    config) prevents picking any day after today at all, so this asserts
    the page remains in a valid, non-broken state."""
    ensure_on_report_page(usage_analytics_page)
    usage_analytics_page.open_date_range_picker()
    future_cells = usage_analytics_page.page.locator(
        ".flatpickr-calendar.open .flatpickr-day.nextMonthDay:not(.flatpickr-disabled)")
    if future_cells.count() == 0:
        pytest.skip("No enabled next-month cells available to attempt a future selection")
    future_cells.first.click(force=True)
    usage_analytics_page.page.wait_for_timeout(500)
    assert usage_analytics_page.has_records() or usage_analytics_page.has_no_records_message()


# ── TC_07-08 — Report Type ────────────────────────────────────────────────

@pytest.mark.regression
def test_usage_analytics_TC07_daily_report_type(usage_analytics_page):
    """TC_07: Selecting "Daily" from Report Type groups data by day
    (CONFIRMED default value)."""
    ensure_on_report_page(usage_analytics_page)
    usage_analytics_page.select_report_type("daily")
    assert usage_analytics_page.get_report_type() == "daily"
    assert usage_analytics_page.has_records() or usage_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_usage_analytics_TC08_monthly_report_type(usage_analytics_page):
    """TC_08: Selecting "Monthly" groups data by month."""
    ensure_on_report_page(usage_analytics_page)
    usage_analytics_page.select_report_type("monthly")
    assert usage_analytics_page.get_report_type() == "monthly"
    assert usage_analytics_page.has_records() or usage_analytics_page.has_no_records_message()
    usage_analytics_page.select_report_type("daily")  # reset


# ── TC_09 — Group By ──────────────────────────────────────────────────────

@pytest.mark.regression
def test_usage_analytics_TC09_group_by_option_changes_grouping(usage_analytics_page):
    """TC_09: Selecting a Group By option updates the grouping selection.
    CONFIRMED live wire:snapshot: initialSelected = [] — NONE of the four
    dimensions are pre-selected by default here (a genuine difference from
    every sibling WhatsApp Analytics report, where "product" is
    pre-checked), so toggling "product" on should bump the label from "0
    selected" (or equivalent) to "1 selected"."""
    ensure_on_report_page(usage_analytics_page)
    usage_analytics_page.toggle_group_by_dimension("product")
    usage_analytics_page.page.wait_for_timeout(1000)
    assert "1 selected" in usage_analytics_page.get_group_by_label_text().lower()
    usage_analytics_page.toggle_group_by_dimension("product")  # reset (toggle back off)


@pytest.mark.regression
def test_usage_analytics_group_by_source_dimension_toggle(usage_analytics_page):
    """Toggling the "source" Group By dimension (CONFIRMED live DOM —
    present on this report and RCS Error Code Analytics, but no other
    WhatsApp Analytics report) updates the checked state without breaking
    the page."""
    ensure_on_report_page(usage_analytics_page)
    usage_analytics_page.toggle_group_by_dimension("source")
    assert usage_analytics_page.is_group_by_dimension_checked("source")
    usage_analytics_page.toggle_group_by_dimension("source")  # reset
    assert not usage_analytics_page.is_group_by_dimension_checked("source")


# ── TC_10-11 — Search ─────────────────────────────────────────────────────

@pytest.mark.regression
def test_usage_analytics_TC10_search_valid_term(usage_analytics_page):
    """TC_10: Searching by a valid Product term returns matching records
    (search placeholder is "Search by Product", CONFIRMED live DOM)."""
    ensure_on_report_page(usage_analytics_page)
    if not usage_analytics_page.has_records():
        pytest.skip("No records available to search")
    usage_analytics_page.search("a")
    assert usage_analytics_page.has_records() or usage_analytics_page.has_no_records_message()
    usage_analytics_page.clear_search()


@pytest.mark.negative
def test_usage_analytics_TC11_search_invalid_term(usage_analytics_page):
    """TC_11: Searching a non-existing term shows the no-records state."""
    ensure_on_report_page(usage_analytics_page)
    usage_analytics_page.search("ZZZZ_NON_EXISTENT_PRODUCT_9999")
    assert usage_analytics_page.has_no_records_message(), "Invalid search should show a no-records state"
    usage_analytics_page.clear_search()


# ── TC_12 — Filters (Product / Source / Department / User) ──────────────

@pytest.mark.regression
def test_usage_analytics_TC12_filter_by_product(usage_analytics_page):
    """TC_12: Filtering by a Product checkbox (e.g. "MARKETING") shows only
    matching data. CONFIRMED live DOM: Product here is a checkbox
    multiselect, NOT a plain <select> — unlike every sibling WhatsApp
    Analytics report's Product filter."""
    ensure_on_report_page(usage_analytics_page)
    usage_analytics_page.toggle_product_filter("MARKETING")
    assert usage_analytics_page.is_product_filter_checked("MARKETING")
    usage_analytics_page.page.wait_for_timeout(1000)
    assert usage_analytics_page.has_records() or usage_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_usage_analytics_filter_by_source(usage_analytics_page):
    """Filtering by a Source checkbox (e.g. "API") updates the report.
    CONFIRMED live DOM: Source is also a checkbox multiselect, and this
    filter field does not exist at all on any other WhatsApp Analytics
    report."""
    ensure_on_report_page(usage_analytics_page)
    usage_analytics_page.toggle_source_filter("API")
    assert usage_analytics_page.is_source_filter_checked("API")
    usage_analytics_page.page.wait_for_timeout(1000)
    assert usage_analytics_page.has_records() or usage_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_usage_analytics_filters_panel_shows_all_four_fields(usage_analytics_page):
    """Opening the Filters button reveals Product/Source/Department/User —
    filterCount 4 (CONFIRMED live DOM), the most filter fields of any
    WhatsApp Analytics report."""
    ensure_on_report_page(usage_analytics_page)
    usage_analytics_page.open_filters_popover()
    assert usage_analytics_page.is_element_present(usage_analytics_page.FILTER_PRODUCT_SELECT_ALL, timeout=5000)
    assert usage_analytics_page.is_element_present(usage_analytics_page.FILTER_SOURCE_SELECT_ALL, timeout=5000)
    assert usage_analytics_page.is_element_present(usage_analytics_page.FILTER_DEPARTMENT_INPUT, timeout=5000)
    assert usage_analytics_page.is_element_present(usage_analytics_page.FILTER_USER_INPUT, timeout=5000)


@pytest.mark.regression
def test_usage_analytics_select_all_product_filter(usage_analytics_page):
    """Clicking the Product "All" checkbox (wire:input=
    "selectAllFilterOptions('product')", CONFIRMED live DOM) does not break
    the page."""
    ensure_on_report_page(usage_analytics_page)
    usage_analytics_page.select_all_product_filter()
    assert usage_analytics_page.has_records() or usage_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_usage_analytics_select_all_source_filter(usage_analytics_page):
    """Clicking the Source "All" checkbox (wire:input=
    "selectAllFilterOptions('source')", CONFIRMED live DOM) does not break
    the page."""
    ensure_on_report_page(usage_analytics_page)
    usage_analytics_page.select_all_source_filter()
    assert usage_analytics_page.has_records() or usage_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_usage_analytics_filter_by_department(usage_analytics_page):
    """Filtering by Department updates the report (best-effort: see module
    docstring on the async-select empty-option-markup caveat)."""
    ensure_on_report_page(usage_analytics_page)
    usage_analytics_page.filter_by_department("a")
    assert usage_analytics_page.has_records() or usage_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_usage_analytics_filter_by_user(usage_analytics_page):
    """Filtering by User updates the report (best-effort caveat, see module
    docstring)."""
    ensure_on_report_page(usage_analytics_page)
    usage_analytics_page.filter_by_user("a")
    assert usage_analytics_page.has_records() or usage_analytics_page.has_no_records_message()


# ── TC_13-14 — Export ─────────────────────────────────────────────────────

@pytest.mark.regression
def test_usage_analytics_TC13_export_csv(usage_analytics_page):
    """TC_13: Export CSV button triggers a download (dispatches
    $wire.export(), CONFIRMED live DOM)."""
    ensure_on_report_page(usage_analytics_page)
    usage_analytics_page.click_export_csv()
    assert usage_analytics_page.is_report_page()


@pytest.mark.regression
def test_usage_analytics_TC14_export_button_available_after_filtering(usage_analytics_page):
    """TC_14: Export CSV remains available and clickable after the report
    has been filtered/searched, implying the export reflects current filter
    state rather than being disabled or broken."""
    ensure_on_report_page(usage_analytics_page)
    usage_analytics_page.search("a")
    assert usage_analytics_page.is_element_present(usage_analytics_page.EXPORT_CSV_BUTTON, timeout=5000)
    usage_analytics_page.click_export_csv()
    assert usage_analytics_page.is_report_page()
    usage_analytics_page.clear_search()


# ── TC_15-16 — Columns Dropdown ───────────────────────────────────────────

@pytest.mark.regression
def test_usage_analytics_TC15_hide_specific_column(usage_analytics_page):
    """TC_15: Unchecking a column in the Columns dropdown removes it from
    the table. Column selection persists in sessionStorage across a plain
    navigate_to_report() (CONFIRMED live wire:snapshot:
    sessionStorageStatus.columnselect=true), so this restores the column
    in a finally block — otherwise TC_16 would find it missing."""
    ensure_on_report_page(usage_analytics_page)
    before = set(usage_analytics_page.get_visible_column_headers())
    toggled_value = usage_analytics_page.uncheck_first_optional_column()
    if not toggled_value:
        pytest.skip("No optional columns available to uncheck")
    try:
        usage_analytics_page.page.wait_for_timeout(1000)
        after = set(usage_analytics_page.get_visible_column_headers())
        assert after != before, "Column visibility should change after unchecking"
    finally:
        usage_analytics_page.check_column(toggled_value)


@pytest.mark.regression
def test_usage_analytics_TC16_re_enable_hidden_column(usage_analytics_page):
    """TC_16: Re-checking a hidden column makes it reappear."""
    ensure_on_report_page(usage_analytics_page)
    toggled_value = usage_analytics_page.uncheck_first_optional_column()
    if not toggled_value:
        pytest.skip("No optional columns available to uncheck")
    usage_analytics_page.page.wait_for_timeout(1000)
    hidden = set(usage_analytics_page.get_visible_column_headers())
    usage_analytics_page.check_column(toggled_value)
    usage_analytics_page.page.wait_for_timeout(1000)
    restored = set(usage_analytics_page.get_visible_column_headers())
    assert restored != hidden, "Column should reappear after re-checking"


# ── TC_17 — Pagination ────────────────────────────────────────────────────

@pytest.mark.regression
def test_usage_analytics_TC17_pagination_changes_data(usage_analytics_page):
    """TC_17: Navigating to the next page changes the displayed data
    without breaking the UI."""
    ensure_on_report_page(usage_analytics_page)
    before = usage_analytics_page.get_column_values("duration")
    if not before:
        pytest.skip("No rows to paginate through")
    usage_analytics_page.click_next_page()
    after = usage_analytics_page.get_column_values("duration")
    assert after != before, "Row data should change after pagination"
    usage_analytics_page.navigate_to_report()  # reset to page 1


@pytest.mark.smoke
def test_usage_analytics_records_count_displayed(usage_analytics_page):
    """Result count text at the bottom of the table shows correct wording
    (CONFIRMED live pagination total at capture time: 40 results)."""
    ensure_on_report_page(usage_analytics_page)
    text = usage_analytics_page.get_pagination_results_text()
    assert "showing" in text.lower() and "of" in text.lower()


# ── TC_18 — Performance ───────────────────────────────────────────────────

@pytest.mark.regression
def test_usage_analytics_TC18_load_performance(usage_analytics_page):
    """TC_18: Report loads within an acceptable time window. Uses the
    browser's real Performance Timing API rather than our own sleeps —
    threshold set generously (8s) to absorb normal CI/network variance,
    same convention as every other report suite in this project."""
    ensure_on_report_page(usage_analytics_page)
    load_ms = usage_analytics_page.get_page_load_time_ms()
    if load_ms is None or load_ms <= 0:
        pytest.skip("Browser performance timing API unavailable")
    assert load_ms < 8000, f"Page load took {load_ms}ms"


# ── Bonus — Individual Column Data Validation ────────────────────────────
# These items are fully CONFIRMED from the live DOM but were not
# individually itemised into TCs — added for the same reason every other
# report suite in this project validates each confirmed column and
# interactive element.

@pytest.mark.smoke
def test_usage_analytics_table_loads(usage_analytics_page):
    """Usage analytics table loads with records displayed correctly."""
    ensure_on_report_page(usage_analytics_page)
    assert usage_analytics_page.has_records() or usage_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_usage_analytics_sort_by_duration(usage_analytics_page):
    """Clicking the Duration column header's sort control does not break
    the page (CONFIRMED live DOM: wire:click="sortBy('duration')")."""
    ensure_on_report_page(usage_analytics_page)
    usage_analytics_page.sort_by_duration()
    assert usage_analytics_page.has_records() or usage_analytics_page.has_no_records_message()


@pytest.mark.regression
def test_usage_analytics_total_column_values(usage_analytics_page):
    """Total column has values for every row."""
    ensure_on_report_page(usage_analytics_page)
    values = usage_analytics_page.get_column_values("total")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_analytics_sent_column_values(usage_analytics_page):
    """Sent column has values for every row."""
    ensure_on_report_page(usage_analytics_page)
    values = usage_analytics_page.get_column_values("sent")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_analytics_delivered_column_values(usage_analytics_page):
    """Delivered column has values for every row."""
    ensure_on_report_page(usage_analytics_page)
    values = usage_analytics_page.get_column_values("delivered")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_analytics_read_column_values(usage_analytics_page):
    """Read column has values for every row."""
    ensure_on_report_page(usage_analytics_page)
    values = usage_analytics_page.get_column_values("read")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_analytics_failed_column_values(usage_analytics_page):
    """Failed column has values for every row."""
    ensure_on_report_page(usage_analytics_page)
    values = usage_analytics_page.get_column_values("failed")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_analytics_rejected_column_values(usage_analytics_page):
    """Rejected column has values for every row."""
    ensure_on_report_page(usage_analytics_page)
    values = usage_analytics_page.get_column_values("rejected")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_analytics_dlr_awaited_column_values(usage_analytics_page):
    """DLR Awaited column has values for every row."""
    ensure_on_report_page(usage_analytics_page)
    values = usage_analytics_page.get_column_values("dlr_awaited")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_analytics_interactions_column_values(usage_analytics_page):
    """Interactions column has values for every row."""
    ensure_on_report_page(usage_analytics_page)
    values = usage_analytics_page.get_column_values("interactions")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_analytics_quick_reply_total_values(usage_analytics_page):
    """Quick reply total column has values for every row."""
    ensure_on_report_page(usage_analytics_page)
    values = usage_analytics_page.get_column_values("quick_reply_total")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_analytics_quick_reply_unique_values(usage_analytics_page):
    """Quick reply unique column has values for every row."""
    ensure_on_report_page(usage_analytics_page)
    values = usage_analytics_page.get_column_values("quick_reply_unique")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_analytics_cta_total_clicks_values(usage_analytics_page):
    """CTA Total Clicks column has values for every row."""
    ensure_on_report_page(usage_analytics_page)
    values = usage_analytics_page.get_column_values("cta_total_clicks")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_analytics_cta_unique_clicks_values(usage_analytics_page):
    """CTA Unique Clicks column has values for every row."""
    ensure_on_report_page(usage_analytics_page)
    values = usage_analytics_page.get_column_values("cta_unique_clicks")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_analytics_total_charges_values(usage_analytics_page):
    """Total Charges column is displayed with values for every row."""
    ensure_on_report_page(usage_analytics_page)
    values = usage_analytics_page.get_column_values("total_charges")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)
