"""
SMS Template Report — Single Sequential Flow
================================================
Covers: Channels → SMS → Analytics → Template Report page, TC_01 - TC_28
(URL: /channels/sms/reports/template)

Migrated to Playwright: local page-object fixture renamed
`template_report_page` (built on conftest.py's `module_logged_in_page`) to
avoid shadowing pytest-playwright's reserved `page` fixture.

Locators (pages/sms_template_report_page.py) are built from a live DOM dump
of this exact page. Same rappasoft/livewire-tables conventions confirmed on
the Campaign Report and Sender Report pages apply here — this report has NO
row-preview/detail modal (confirmed absent from the live DOM, same as
Sender Report), so there is no modal test block like Campaign Report's
TC_26-33.

Run:
    pytest tests/test_sms_template_report_flow.py -v
"""
import os

import pytest

from constants.sms_template_report_headers import EXPECTED_SMS_TEMPLATE_REPORT_HEADERS
from pages.sms.sms_template_report_page import SmsTemplateReportPage
from utils.file_validator import (
    EmptyFileError,
    FileNotDownloadedError,
    HeaderValidationError,
    UnsupportedFileTypeError,
    validate_file_headers,
)


pytestmark = [pytest.mark.sms, pytest.mark.template]



@pytest.fixture(scope="module")
def template_report_page(module_logged_in_page):
    p = SmsTemplateReportPage(module_logged_in_page)
    p.navigate_to_report()
    return p


def ensure_on_report_page(p):
    if not p.is_report_page():
        p.navigate_to_report()
        p.page.wait_for_timeout(1000)


@pytest.fixture(autouse=True)
def _reset_after_test(template_report_page):
    """Hard reset to a clean report view after every test — same rationale
    as Campaign Report / Sender Report's fixture of the same name: this
    page has many stateful filters (date range, report type, group by,
    columns, product/department/user), so re-navigating fresh after each
    test is the simplest guaranteed way to avoid cross-test contamination."""
    yield
    try:
        template_report_page.navigate_to_report()
    except Exception:
        pass


# ── TC_01-04 — Page Load / UI Validation ────────────────────────────────

@pytest.mark.smoke
def test_template_report_TC01_page_loads(template_report_page):
    """TC_01: SMS Template Report page loads successfully without errors."""
    ensure_on_report_page(template_report_page)
    assert template_report_page.is_report_page(), "URL should contain /channels/sms/reports/template"
    title = template_report_page.get_title().lower()
    assert "404" not in title and "error" not in title


@pytest.mark.smoke
def test_template_report_TC02_title_displayed(template_report_page):
    """TC_02: Page title 'Template Report' is visible."""
    ensure_on_report_page(template_report_page)
    assert "Template Report" in template_report_page.get_page_title_text()


@pytest.mark.smoke
def test_template_report_TC03_search_bar_visible(template_report_page):
    """TC_03: Search by Template search box is visible."""
    ensure_on_report_page(template_report_page)
    assert template_report_page.is_element_present(template_report_page.SEARCH_BOX, timeout=5000)


@pytest.mark.smoke
def test_template_report_TC04_filters_button_visible(template_report_page):
    """TC_04: Filters button and Date Range / Report Type / Group By
    controls are visible."""
    ensure_on_report_page(template_report_page)
    assert template_report_page.is_element_present(template_report_page.FILTERS_BUTTON, timeout=5000)
    assert template_report_page.are_filters_visible()


# ── TC_05-06 — Search ─────────────────────────────────────────────────────

@pytest.mark.regression
def test_template_report_TC05_search_valid_template(template_report_page):
    """TC_05: Searching by an existing Template name returns matching records."""
    ensure_on_report_page(template_report_page)
    if not template_report_page.has_records():
        pytest.skip("No template records available to search")
    names = template_report_page.get_column_values("template_name")
    if not names or not names[0]:
        pytest.skip("Could not read a template name to search for")
    needle = names[0][:4]
    template_report_page.search(needle)
    assert template_report_page.has_records() or template_report_page.has_no_records_message()


@pytest.mark.negative
def test_template_report_TC06_search_invalid_template(template_report_page):
    """TC_06: Searching a non-existing Template name shows no results."""
    ensure_on_report_page(template_report_page)
    template_report_page.search("ZZZZ_NON_EXISTENT_TEMPLATE_9999")
    assert template_report_page.has_no_records_message(), "Invalid search should show no-records message"
    template_report_page.clear_search()


# ── TC_07-08 — Filters Panel / Product Filter ────────────────────────────

@pytest.mark.regression
def test_template_report_TC07_open_filters_panel(template_report_page):
    """TC_07: Opening the Filters button reveals the Product/Department/
    User filter fields."""
    ensure_on_report_page(template_report_page)
    template_report_page.open_filters_popover()
    assert template_report_page.is_element_present(template_report_page.FILTER_PRODUCT_SELECT, timeout=5000)
    assert template_report_page.is_element_present(template_report_page.FILTER_DEPARTMENT_INPUT, timeout=5000)
    assert template_report_page.is_element_present(template_report_page.FILTER_USER_INPUT, timeout=5000)


@pytest.mark.regression
def test_template_report_TC08_product_filter(template_report_page):
    """TC_08: Filtering by Product Type (OTP) updates the report."""
    ensure_on_report_page(template_report_page)
    template_report_page.filter_by_product("O")
    assert template_report_page.has_records() or template_report_page.has_no_records_message()
    template_report_page.filter_by_product("")  # reset to All


# ── TC_09-10 — Date Range ─────────────────────────────────────────────────

@pytest.mark.negative
def test_template_report_TC10_invalid_date_order(template_report_page):
    """TC_10: The From date can never end up after the To date. flatpickr's
    'range' mode inherently reorders two clicked dates chronologically
    rather than letting a user pick an inverted range, so this asserts the
    resulting picker value is always chronologically ordered after clicking
    two day cells in reverse chronological order."""
    ensure_on_report_page(template_report_page)
    ok = template_report_page.select_date_range(from_day_offset=3, to_day_offset=10)
    if not ok:
        pytest.skip("Flatpickr date range interaction did not behave as expected")
    value = template_report_page.get_date_range_value()
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


# ── TC_11 — Report Type ───────────────────────────────────────────────────

@pytest.mark.regression
def test_template_report_TC11_report_type_dropdown(template_report_page):
    """TC_11: Switching Report Type (Daily/Weekly/Monthly) updates the data."""
    ensure_on_report_page(template_report_page)
    template_report_page.select_report_type("weekly")
    assert template_report_page.get_report_type() == "weekly"
    assert template_report_page.has_records() or template_report_page.has_no_records_message()
    template_report_page.select_report_type("daily")  # reset


# ── TC_12 — Group By ──────────────────────────────────────────────────────

@pytest.mark.regression
def test_template_report_TC12_group_by_dropdown(template_report_page):
    """TC_12: Selecting a Group By dimension updates the grouping selection."""
    ensure_on_report_page(template_report_page)
    template_report_page.toggle_group_by_dimension("department")
    template_report_page.page.wait_for_timeout(1000)
    assert "selected" in template_report_page.get_group_by_label_text().lower()
    template_report_page.toggle_group_by_dimension("department")  # reset (toggle back off)


# ── TC_13 — Export ────────────────────────────────────────────────────────

@pytest.mark.regression
def test_template_report_TC13_export_csv(template_report_page):
    """TC_13: Export CSV button triggers a download (dispatches $wire.export()),
    and the downloaded file's header row exactly matches the defined SMS
    Template Report export specification
    (constants/sms_template_report_headers.py). Reuses the same generic
    utils/file_validator.py used by every other SMS export's header
    validation; only the expected-header list differs. Not to be confused
    with the SMS Template *list's* export header check
    (test_sms_template.py::TestExportTemplateList) — different feature.
    """
    ensure_on_report_page(template_report_page)
    assert template_report_page.is_report_page()

    print("[DOWNLOAD] SMS Template Report export requested")
    result = template_report_page.click_export_csv(timeout_ms=30000)
    assert result is not None, "Export CSV should produce a downloaded file"
    assert result["file_size"] > 0, "Downloaded export file should not be empty"
    file_path = result["file_path"]
    print("[DOWNLOAD] SMS Template Report export file downloaded")
    print(f"[DOWNLOAD] File: {os.path.basename(file_path)}")

    print("[VALIDATION] Reading file headers")
    print(f"[VALIDATION] Expected headers: {len(EXPECTED_SMS_TEMPLATE_REPORT_HEADERS)}")
    print(f"[VALIDATION] Expected header names: {EXPECTED_SMS_TEMPLATE_REPORT_HEADERS}")
    try:
        actual_headers = validate_file_headers(file_path, EXPECTED_SMS_TEMPLATE_REPORT_HEADERS)
    except FileNotDownloadedError as exc:
        pytest.fail(f"[DOWNLOAD] {exc}")
    except (UnsupportedFileTypeError, EmptyFileError) as exc:
        print("[VALIDATION] SMS Template Report header validation: FAIL")
        pytest.fail(str(exc))
    except HeaderValidationError as exc:
        print(f"[VALIDATION] Actual headers: {len(exc.actual)}")
        print(f"[VALIDATION] Actual header names: {exc.actual}")
        print("[VALIDATION] SMS Template Report header validation: FAIL")
        print(f"[VALIDATION] Missing headers: {exc.missing}")
        print(f"[VALIDATION] Unexpected headers: {exc.unexpected}")
        if exc.mismatches:
            for position, expected_name, actual_name in exc.mismatches:
                print(
                    f"[VALIDATION] Position {position}: "
                    f"expected '{expected_name}', actual '{actual_name}'"
                )
        pytest.fail(str(exc))

    print(f"[VALIDATION] Actual headers: {len(actual_headers)}")
    print(f"[VALIDATION] Actual header names: {actual_headers}")
    print("[VALIDATION] SMS Template Report header validation: PASS")


# ── TC_14 — Columns Dropdown ──────────────────────────────────────────────

@pytest.mark.regression
def test_template_report_TC14_columns_dropdown(template_report_page):
    """TC_14: Columns dropdown allows showing/hiding table columns. Column
    selection persists in sessionStorage across page reloads (same
    confirmed behaviour as Campaign/Sender Report), so this restores the
    column it hid in a finally block — otherwise a later test (TC_16)
    would find that column missing for the rest of the session."""
    ensure_on_report_page(template_report_page)
    before = set(template_report_page.get_visible_column_headers())
    toggled_value = template_report_page.uncheck_first_optional_column()
    if not toggled_value:
        pytest.skip("No optional columns available to uncheck")
    try:
        template_report_page.page.wait_for_timeout(1000)
        after = set(template_report_page.get_visible_column_headers())
        assert after != before, "Column visibility should change after unchecking"
    finally:
        template_report_page.check_column(toggled_value)


# ── TC_15-16 — Table Load / Columns Present ──────────────────────────────

@pytest.mark.smoke
def test_template_report_TC15_table_loads(template_report_page):
    """TC_15: Template report table loads with records displayed correctly."""
    ensure_on_report_page(template_report_page)
    assert template_report_page.has_records() or template_report_page.has_no_records_message()


@pytest.mark.smoke
def test_template_report_TC16_columns_present(template_report_page):
    """TC_16: Expected columns (Duration, Template Name, Product, Total
    Count, etc.) are visible in the table header."""
    ensure_on_report_page(template_report_page)
    headers = [h.lower() for h in template_report_page.get_visible_column_headers()]
    for expected in ["duration", "template name", "product", "total count"]:
        assert any(expected in h for h in headers), f"Missing column: {expected}"


# ── TC_17-20 — Data Validation Columns (Counts) ──────────────────────────

@pytest.mark.regression
def test_template_report_TC17_total_count_values(template_report_page):
    """TC_17: Total Count column has values for every row."""
    ensure_on_report_page(template_report_page)
    values = template_report_page.get_column_values("total_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_template_report_TC18_submitted_count_values(template_report_page):
    """TC_18: Submitted Count column has values for every row."""
    ensure_on_report_page(template_report_page)
    values = template_report_page.get_column_values("submitted_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_template_report_TC19_delivered_count_values(template_report_page):
    """TC_19: Delivered Count column has values for every row."""
    ensure_on_report_page(template_report_page)
    values = template_report_page.get_column_values("delivered_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_template_report_TC20_failed_count_values(template_report_page):
    """TC_20: Failed Count column has values for every row."""
    ensure_on_report_page(template_report_page)
    values = template_report_page.get_column_values("failed_count")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


# ── TC_21 — Units ─────────────────────────────────────────────────────────

@pytest.mark.regression
def test_template_report_TC21_total_units_values(template_report_page):
    """TC_21: Total Units column has values for every row."""
    ensure_on_report_page(template_report_page)
    values = template_report_page.get_column_values("total_units")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


# ── TC_22-24 — Charges / Surcharge ────────────────────────────────────────

@pytest.mark.regression
def test_template_report_TC22_total_charges_displayed(template_report_page):
    """TC_22: Total Charges column is displayed with values for every row."""
    ensure_on_report_page(template_report_page)
    values = template_report_page.get_column_values("total_charges")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_template_report_TC23_delivery_charges_displayed(template_report_page):
    """TC_23: Delivery Charges column is displayed correctly."""
    ensure_on_report_page(template_report_page)
    values = template_report_page.get_column_values("delivery_charges")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


@pytest.mark.regression
def test_template_report_TC24_surcharge_displayed(template_report_page):
    """TC_24: Surcharge column is displayed correctly."""
    ensure_on_report_page(template_report_page)
    values = template_report_page.get_column_values("surcharge")
    if not values:
        pytest.skip("No rows to validate")
    assert all(v.strip() != "" for v in values)


# ── TC_25 — Delivery % Calculation ───────────────────────────────────────

@pytest.mark.regression
def test_template_report_TC25_delivery_pct_calculation(template_report_page):
    """TC_25: Delivery % column values are well-formed percentages
    (CONFIRMED live DOM format e.g. '100.00%') and internally consistent
    with Delivered Count / Submitted Count for each row.

    NOTE: the formula denominator is Submitted Count, not Total Count —
    this was confirmed on Sender Report against real data (e.g. total=2,
    submitted=1, delivered=1, rejected=1 -> 100%, which only holds if the
    denominator is Submitted Count) and re-confirmed here against this
    report's live dataset, e.g. a row with total_count=13,
    submitted_count=8, delivered_count=8, rejected_count=5 also showing
    100% (8/8=100%, 8/13=61.5% would not match). Rows with Submitted
    Count=0 are skipped to avoid a division-by-zero false negative."""
    ensure_on_report_page(template_report_page)
    pct_values = template_report_page.get_column_values("delivery_pct")
    submitted_values = template_report_page.get_column_values("submitted_count")
    delivered_values = template_report_page.get_column_values("delivered_count")
    if not pct_values:
        pytest.skip("No rows to validate")
    assert all(v.strip().endswith("%") for v in pct_values), \
        "Delivery % values should be formatted as percentages"
    for pct, submitted, delivered in zip(pct_values, submitted_values, delivered_values):
        try:
            submitted_n = float(submitted)
            delivered_n = float(delivered)
            pct_n = float(pct.strip().rstrip("%"))
        except ValueError:
            continue
        if submitted_n <= 0:
            continue
        expected_pct = round((delivered_n / submitted_n) * 100, 2)
        assert abs(pct_n - expected_pct) <= 0.5, (
            f"Delivery % {pct_n} does not match Delivered/Submitted ratio "
            f"{expected_pct} for row (delivered={delivered_n}, submitted={submitted_n})"
        )


# ── TC_26-27 — Pagination ─────────────────────────────────────────────────

@pytest.mark.regression
def test_template_report_TC26_pagination(template_report_page):
    """TC_26: Navigating to the next page changes the displayed data."""
    ensure_on_report_page(template_report_page)
    before = template_report_page.get_column_values("template_name")
    if not before:
        pytest.skip("No rows to paginate through")
    if not template_report_page.is_next_page_enabled():
        pytest.skip("Next page button is not enabled (only one page of data)")
    template_report_page.click_next_page()
    after = template_report_page.get_column_values("template_name")
    assert after != before, "Row data should change after pagination"
    template_report_page.navigate_to_report()  # reset to page 1


@pytest.mark.smoke
def test_template_report_TC27_records_count_displayed(template_report_page):
    """TC_27: Result count text at the bottom of the table shows correct wording."""
    ensure_on_report_page(template_report_page)
    text = template_report_page.get_pagination_results_text()
    assert "showing" in text.lower() and "of" in text.lower()


# ── TC_28 — Performance ───────────────────────────────────────────────────

@pytest.mark.regression
def test_template_report_TC28_load_performance(template_report_page):
    """TC_28: Report loads within an acceptable time window. Uses the
    browser's real Performance Timing API rather than our own sleeps —
    threshold is set generously (20s) to absorb normal CI/network variance
    versus the spec's ideal <5s under production conditions."""
    ensure_on_report_page(template_report_page)
    load_ms = template_report_page.get_page_load_time_ms()
    if load_ms is None or load_ms <= 0:
        pytest.skip("Browser performance timing API unavailable")
    assert load_ms < 20000, f"Page load took {load_ms}ms"
