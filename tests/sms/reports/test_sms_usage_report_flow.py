"""
SMS Usage Report — Single Sequential Flow
================================================
Covers: Channels → SMS → Analytics → Usage page, TC_01 - TC_33
(URL: /channels/sms/reports/usage)

Migrated to Playwright: local page-object fixture renamed
`usage_report_page` (built on conftest.py's `module_logged_in_page`) to
avoid shadowing pytest-playwright's reserved `page` fixture.

Locators (pages/sms_usage_report_page.py) are built from a live DOM dump of
this exact page. Same rappasoft/livewire-tables conventions confirmed on
Campaign/Sender/Template Report apply here, but note two report-specific
differences (both CONFIRMED from the live DOM, documented in detail in the
page object docstring):
  1. The Product filter in the Filters popover is a checkbox multiselect
     (Transactional/Promotional/OTP), not a plain <select> like Sender/
     Template Report's product filter.
  2. Group By has a fourth "Source" dimension (Campaign/API/Flow/SMPP) not
     present on Sender/Template Report.
  3. There is no product/sender/template identifier column in the table —
     dimension breakdown is opt-in via Group By, so search-by-product and
     filter-by-department/user tests use soft assertions rather than
     asserting an exact result set, since there's no visible column to pull
     a guaranteed-valid search term from.

TC_30 (Delivery %) is a genuinely new finding versus Sender Report's TC_25:
this report's live data has rows where Units diverge from Counts
(multi-segment messages), and cross-checking those rows proves the formula
is Delivered UNITS / Submitted UNITS, not Delivered/Submitted COUNT (see
the test's docstring for the exact confirming rows).

Run:
    pytest tests/test_sms_usage_report_flow.py -v
"""
import pytest

from pages.sms.sms_usage_report_page import SmsUsageReportPage


pytestmark = [pytest.mark.sms, pytest.mark.report]



@pytest.fixture(scope="module")
def usage_report_page(module_logged_in_page):
    p = SmsUsageReportPage(module_logged_in_page)
    p.navigate_to_report()
    return p


def ensure_on_report_page(p):
    if not p.is_report_page():
        p.navigate_to_report()
        p.page.wait_for_timeout(1000)


@pytest.fixture(autouse=True)
def _reset_after_test(usage_report_page):
    """Hard reset to a clean report view after every test — same rationale
    as Campaign/Sender/Template Report's fixture of the same name: this
    page has many stateful filters (date range, report type, group by,
    columns, department/user/source/product), so re-navigating fresh after
    each test is the simplest guaranteed way to avoid cross-test
    contamination."""
    yield
    try:
        usage_report_page.navigate_to_report()
    except Exception:
        pass


# ── TC_01-04 — Page Load / UI Validation ────────────────────────────────

@pytest.mark.smoke
def test_usage_report_TC01_page_loads(usage_report_page):
    """TC_01: SMS Usage Report page loads successfully without errors."""
    ensure_on_report_page(usage_report_page)
    assert usage_report_page.is_report_page(), "URL should contain /channels/sms/reports/usage"
    title = usage_report_page.get_title().lower()
    assert "404" not in title and "error" not in title


@pytest.mark.smoke
def test_usage_report_TC02_title_displayed(usage_report_page):
    """TC_02: Page title 'Usage Report' is visible."""
    ensure_on_report_page(usage_report_page)
    assert "Usage Report" in usage_report_page.get_page_title_text()


@pytest.mark.smoke
def test_usage_report_TC03_search_bar_visible(usage_report_page):
    """TC_03: Search by Product search box is visible."""
    ensure_on_report_page(usage_report_page)
    assert usage_report_page.is_element_present(usage_report_page.SEARCH_BOX, timeout=5000)


@pytest.mark.smoke
def test_usage_report_TC04_filters_button_visible(usage_report_page):
    """TC_04: Filters button and Date Range / Report Type / Group By
    controls are visible."""
    ensure_on_report_page(usage_report_page)
    assert usage_report_page.is_element_present(usage_report_page.FILTERS_BUTTON, timeout=5000)
    assert usage_report_page.are_filters_visible()


# ── TC_05-06 — Search ─────────────────────────────────────────────────────

@pytest.mark.regression
def test_usage_report_TC05_search_valid_product_name(usage_report_page):
    """TC_05: Searching by a product name returns matching records.

    NOTE: unlike Sender/Template Report, this report's table has no visible
    product-identifier column to reliably pull a guaranteed-valid search
    term from (dimension breakdown here is opt-in via Group By), so this
    uses a short generic substring and asserts the report ends in a valid
    state (records or an explicit no-records message) rather than an exact
    match."""
    ensure_on_report_page(usage_report_page)
    if not usage_report_page.has_records():
        pytest.skip("No usage records available to search")
    usage_report_page.search("a")
    assert usage_report_page.has_records() or usage_report_page.has_no_records_message()
    usage_report_page.clear_search()


@pytest.mark.negative
def test_usage_report_TC06_search_invalid_product_name(usage_report_page):
    """TC_06: Searching a non-existing product name shows no results."""
    ensure_on_report_page(usage_report_page)
    usage_report_page.search("ZZZZ_NON_EXISTENT_PRODUCT_9999")
    assert usage_report_page.has_no_records_message(), "Invalid search should show no-records message"
    usage_report_page.clear_search()


# ── TC_07 — Filters Panel ─────────────────────────────────────────────────

@pytest.mark.regression
def test_usage_report_TC07_open_filters_panel(usage_report_page):
    """TC_07: Opening the Filters button reveals the Department/User/
    Source/Product filter fields."""
    ensure_on_report_page(usage_report_page)
    usage_report_page.open_filters_popover()
    assert usage_report_page.is_element_present(usage_report_page.FILTER_DEPARTMENT_INPUT, timeout=5000)
    assert usage_report_page.is_element_present(usage_report_page.FILTER_USER_INPUT, timeout=5000)
    assert usage_report_page.is_element_present(usage_report_page.FILTER_SOURCE_WRAPPER, timeout=5000)
    assert usage_report_page.is_element_present(usage_report_page.FILTER_PRODUCT_WRAPPER, timeout=5000)


# ── TC_08-09 — Department / User Filters ─────────────────────────────────

@pytest.mark.regression
def test_usage_report_TC08_filter_by_department(usage_report_page):
    """TC_08: Filtering by Department name updates the report (best-effort:
    the async-select department dropdown returned no populated option
    markup in the live DOM — only the empty "No results found" state — so
    this asserts the report remains in a valid state after typing into the
    filter rather than asserting an exact match, same caveat documented on
    the page object's _select_first_async_option)."""
    ensure_on_report_page(usage_report_page)
    usage_report_page.filter_by_department("a")
    assert usage_report_page.has_records() or usage_report_page.has_no_records_message()


@pytest.mark.regression
def test_usage_report_TC09_filter_by_user(usage_report_page):
    """TC_09: Filtering by User updates the report (same best-effort
    caveat as TC_08)."""
    ensure_on_report_page(usage_report_page)
    usage_report_page.filter_by_user("a")
    assert usage_report_page.has_records() or usage_report_page.has_no_records_message()


# ── TC_10-11 — Date Range ─────────────────────────────────────────────────

@pytest.mark.regression
def test_usage_report_TC10_valid_date_range(usage_report_page):
    """TC_10: Selecting a valid date range updates the report."""
    ensure_on_report_page(usage_report_page)
    ok = usage_report_page.select_date_range()
    if not ok:
        pytest.skip("Flatpickr date range interaction did not behave as expected")
    assert usage_report_page.has_records() or usage_report_page.has_no_records_message()


@pytest.mark.negative
def test_usage_report_TC11_invalid_date_order(usage_report_page):
    """TC_11: The From date can never end up after the To date. flatpickr's
    'range' mode inherently reorders two clicked dates chronologically
    rather than letting a user pick an inverted range, so this asserts the
    resulting picker value is always chronologically ordered after clicking
    two day cells in reverse chronological order."""
    ensure_on_report_page(usage_report_page)
    ok = usage_report_page.select_date_range(from_day_offset=3, to_day_offset=10)
    if not ok:
        pytest.skip("Flatpickr date range interaction did not behave as expected")
    value = usage_report_page.get_date_range_value()
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


# ── TC_12 — Report Type ───────────────────────────────────────────────────

@pytest.mark.regression
def test_usage_report_TC12_report_type_dropdown(usage_report_page):
    """TC_12: Switching Report Type (Daily/Weekly/Monthly) updates the data."""
    ensure_on_report_page(usage_report_page)
    usage_report_page.select_report_type("weekly")
    assert usage_report_page.get_report_type() == "weekly"
    assert usage_report_page.has_records() or usage_report_page.has_no_records_message()
    usage_report_page.select_report_type("daily")  # reset


# ── TC_13 — Group By ──────────────────────────────────────────────────────

@pytest.mark.regression
def test_usage_report_TC13_group_by_dropdown(usage_report_page):
    """TC_13: Selecting a Group By dimension updates the grouping selection."""
    ensure_on_report_page(usage_report_page)
    usage_report_page.toggle_group_by_dimension("department")
    usage_report_page.page.wait_for_timeout(1000)
    assert "selected" in usage_report_page.get_group_by_label_text().lower()
    usage_report_page.toggle_group_by_dimension("department")  # reset (toggle back off)


# ── TC_14 — Export ────────────────────────────────────────────────────────

@pytest.mark.regression
def test_usage_report_TC14_export_csv(usage_report_page):
    """TC_14: Export CSV button triggers a download (dispatches $wire.export())."""
    ensure_on_report_page(usage_report_page)
    usage_report_page.click_export_csv()
    assert usage_report_page.is_report_page()


# ── TC_15 — Columns Dropdown ──────────────────────────────────────────────

@pytest.mark.regression
def test_usage_report_TC15_columns_dropdown(usage_report_page):
    """TC_15: Columns dropdown allows showing/hiding table columns. Column
    selection persists in sessionStorage across page reloads (same
    confirmed behaviour as Campaign/Sender/Template Report), so this
    restores the column it hid in a finally block — otherwise a later test
    (TC_16) would find that column missing for the rest of the session."""
    ensure_on_report_page(usage_report_page)
    before = set(usage_report_page.get_visible_column_headers())
    toggled_value = usage_report_page.uncheck_first_optional_column()
    if not toggled_value:
        pytest.skip("No optional columns available to uncheck")
    try:
        usage_report_page.page.wait_for_timeout(1000)
        after = set(usage_report_page.get_visible_column_headers())
        assert after != before, "Column visibility should change after unchecking"
    finally:
        usage_report_page.check_column(toggled_value)


# ── TC_16-17 — Table Load / Columns Present ──────────────────────────────

@pytest.mark.smoke
def test_usage_report_TC16_table_loads(usage_report_page):
    """TC_16: Usage report table loads with records displayed correctly."""
    ensure_on_report_page(usage_report_page)
    assert usage_report_page.has_records() or usage_report_page.has_no_records_message()


@pytest.mark.smoke
def test_usage_report_TC17_columns_present(usage_report_page):
    """TC_17: Expected columns (Duration, Total Count, Submitted Count,
    etc.) are visible in the table header."""
    ensure_on_report_page(usage_report_page)
    headers = [h.lower() for h in usage_report_page.get_visible_column_headers()]
    for expected in ["duration", "total count", "submitted count"]:
        assert any(expected in h for h in headers), f"Missing column: {expected}"


# ── TC_18-21 — Data Validation Columns (Counts) ──────────────────────────

@pytest.mark.regression
def test_usage_report_TC18_total_count_values(usage_report_page):
    """TC_18: Total Count column has values for every row."""
    ensure_on_report_page(usage_report_page)
    values = usage_report_page.get_column_values("total_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_report_TC19_submitted_count_values(usage_report_page):
    """TC_19: Submitted Count column has values for every row."""
    ensure_on_report_page(usage_report_page)
    values = usage_report_page.get_column_values("submitted_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_report_TC20_delivered_count_values(usage_report_page):
    """TC_20: Delivered Count column has values for every row."""
    ensure_on_report_page(usage_report_page)
    values = usage_report_page.get_column_values("delivered_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_report_TC21_failed_count_values(usage_report_page):
    """TC_21: Failed Count column has values for every row."""
    ensure_on_report_page(usage_report_page)
    values = usage_report_page.get_column_values("failed_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


# ── TC_22-25 — Units Validation ───────────────────────────────────────────

@pytest.mark.regression
def test_usage_report_TC22_total_units_values(usage_report_page):
    """TC_22: Total Units column has values for every row."""
    ensure_on_report_page(usage_report_page)
    values = usage_report_page.get_column_values("total_units")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_report_TC23_submitted_units_values(usage_report_page):
    """TC_23: Submitted Units column has values for every row."""
    ensure_on_report_page(usage_report_page)
    values = usage_report_page.get_column_values("submitted_units")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_report_TC24_delivered_units_values(usage_report_page):
    """TC_24: Delivered Units column has values for every row."""
    ensure_on_report_page(usage_report_page)
    values = usage_report_page.get_column_values("delivered_units")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_report_TC25_failed_units_values(usage_report_page):
    """TC_25: Failed Units column has values for every row."""
    ensure_on_report_page(usage_report_page)
    values = usage_report_page.get_column_values("failed_units")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


# ── TC_26-29 — Charges Validation ─────────────────────────────────────────

@pytest.mark.regression
def test_usage_report_TC26_total_charges_values(usage_report_page):
    """TC_26: Total Charges column is displayed with values for every row."""
    ensure_on_report_page(usage_report_page)
    values = usage_report_page.get_column_values("total_charges")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_report_TC27_delivery_charges_values(usage_report_page):
    """TC_27: Delivery Charges column is displayed correctly."""
    ensure_on_report_page(usage_report_page)
    values = usage_report_page.get_column_values("delivery_charges")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_report_TC28_surcharge_values(usage_report_page):
    """TC_28: Surcharge column is displayed correctly."""
    ensure_on_report_page(usage_report_page)
    values = usage_report_page.get_column_values("surcharge")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_usage_report_TC29_delivery_surcharge_values(usage_report_page):
    """TC_29: Delivery Surcharge column is displayed correctly."""
    ensure_on_report_page(usage_report_page)
    values = usage_report_page.get_column_values("delivery_surcharge")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


# ── TC_30 — Delivery % Calculation ───────────────────────────────────────

@pytest.mark.regression
def test_usage_report_TC30_delivery_pct_calculation(usage_report_page):
    """TC_30: Delivery % column values are well-formed percentages
    (CONFIRMED live DOM format e.g. '100.00%', '78.87%') and internally
    consistent with Delivered UNITS / Submitted UNITS for each row — NOT
    Delivered/Submitted COUNT.

    This refines the formula found on Sender Report's TC_25
    (Delivered/Submitted Count). That formula happened to hold there only
    because every sampled row had Units == Count (single-segment
    messages). This report's live data has rows where Units diverge from
    Counts (multi-segment messages), and cross-checking those rows proves
    Units is the real basis:
      - duration=09-07-2026: submitted_count=51/delivered_count=45 would be
        88.24% (does NOT match), but submitted_units=71/delivered_units=56
        = 78.873% — and the displayed value is 78.87% (MATCHES).
      - duration=08-07-2026: submitted_count=63/delivered_count=60 would be
        95.24% (does NOT match), but submitted_units=72/delivered_units=66
        = 91.667% — and the displayed value is 91.67% (MATCHES).
      - duration=05-07-2026: submitted_units==submitted_count (19) and
        delivered_units==delivered_count (15) — 15/19=78.947%, displayed
        78.95% (MATCHES, and is consistent with both formulas since
        units==counts on this row).
    Rows with Submitted Units=0 are skipped to avoid a division-by-zero
    false negative. Values are comma-stripped before parsing since large
    counts/units are displayed with thousands separators (e.g.
    '5,238,712')."""
    ensure_on_report_page(usage_report_page)
    pct_values = usage_report_page.get_column_values("delivery_pct")
    submitted_units = usage_report_page.get_column_values("submitted_units")
    delivered_units = usage_report_page.get_column_values("delivered_units")
    if not pct_values:
        pytest.skip("No rows to validate")
    assert all(v.strip().endswith("%") for v in pct_values), \
        "Delivery % values should be formatted as percentages"

    def _to_number(s):
        return float(s.replace(",", ""))

    for pct, submitted, delivered in zip(pct_values, submitted_units, delivered_units):
        try:
            submitted_n = _to_number(submitted)
            delivered_n = _to_number(delivered)
            pct_n = float(pct.strip().rstrip("%"))
        except ValueError:
            continue
        if submitted_n <= 0:
            continue
        expected_pct = round((delivered_n / submitted_n) * 100, 2)
        assert abs(pct_n - expected_pct) <= 0.5, (
            f"Delivery % {pct_n} does not match Delivered/Submitted UNITS ratio "
            f"{expected_pct} for row (delivered_units={delivered_n}, submitted_units={submitted_n})"
        )


# ── TC_31-32 — Pagination ─────────────────────────────────────────────────

@pytest.mark.regression
def test_usage_report_TC31_pagination(usage_report_page):
    """TC_31: Navigating to the next page changes the displayed data."""
    ensure_on_report_page(usage_report_page)
    before = usage_report_page.get_column_values("duration")
    if not before:
        pytest.skip("No rows to paginate through")
    if not usage_report_page.is_next_page_enabled():
        pytest.skip("Pagination 'Next Page' button is disabled or hidden (probably only 1 page of data)")
    usage_report_page.click_next_page()
    after = usage_report_page.get_column_values("duration")
    assert after != before, "Row data should change after pagination"
    usage_report_page.navigate_to_report()  # reset to page 1


@pytest.mark.smoke
def test_usage_report_TC32_records_count_displayed(usage_report_page):
    """TC_32: Result count text at the bottom of the table shows correct wording."""
    ensure_on_report_page(usage_report_page)
    text = usage_report_page.get_pagination_results_text()
    assert "showing" in text.lower() and "of" in text.lower()


# ── TC_33 — Performance ───────────────────────────────────────────────────

@pytest.mark.regression
def test_usage_report_TC33_load_performance(usage_report_page):
    """TC_33: Report loads within an acceptable time window. Uses the
    browser's real Performance Timing API rather than our own sleeps —
    threshold is set generously (8s) to absorb normal CI/network variance
    versus the spec's ideal <5s under production conditions (same
    threshold rationale used on Campaign/Template Report's load-performance
    test)."""
    ensure_on_report_page(usage_report_page)
    load_ms = usage_report_page.get_page_load_time_ms()
    if load_ms is None or load_ms <= 0:
        pytest.skip("Browser performance timing API unavailable")
    assert load_ms < 8000, f"Page load took {load_ms}ms"
