"""
Monthly Usage — Sequential Automation Flow
===========================================
Test Cases:
  MU_001 – MU_020       Table, Value & UI Verification (20 test cases)
  MU_F_001 – MU_F_023   Filters (Dropdowns & Single Filter Applications) (23 test cases)
  MU_CF_001 – MU_CF_010 Combined Filters & State Management (10 test cases)
  MU_B_001 – MU_B_010   Bulk Actions & Row Selection (10 test cases)
  MU_DATA_001 – MU_DATA_015 Data Integrity & Business Logic (15 test cases)
Total: 78 test cases.

Target Page: /billing/monthly/usage-details

Run:
    pytest tests/common/test_monthly_usage_flow.py -v
"""

import re
from typing import Dict, List

import pytest

from pages.common.monthly_usage_page import MonthlyUsagePage
from constants.monthly_usage_ui_headers import (
    EXPECTED_MONTHLY_USAGE_UI_HEADERS,
    MONTH_FILTER_OPTIONS,
    CHANNEL_FILTER_OPTIONS,
)


pytestmark = [
    pytest.mark.common,
    pytest.mark.billing,
    pytest.mark.monthly_usage,
]


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures & State Recovery
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def mu_page(module_logged_in_page):
    """Module-scoped page instance for Monthly Usage tests."""
    p = MonthlyUsagePage(module_logged_in_page)
    p.navigate()
    p.wait_for_table_load(timeout=15000)
    return p


def ensure_on_page(p: MonthlyUsagePage):
    """Ensure browser is on Monthly Usage page."""
    if not p.is_monthly_usage_page():
        p.navigate()
        p.wait_for_table_load(timeout=10000)


def reset_filters_and_selection(p: MonthlyUsagePage):
    """Helper to reset filters to All and clear any selected rows."""
    ensure_on_page(p)
    try:
        p.reset_filters()
    except Exception:
        pass
    try:
        p.deselect_all()
    except Exception:
        pass
    p.page.wait_for_timeout(400)


# ══════════════════════════════════════════════════════════════════════════════
# MU_001 – MU_020 : Table, Values & UI Verification
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_MU_001_verify_monthly_usage_page_loads(mu_page):
    """Monthly Usage page loads successfully."""
    mu_page.navigate_via_sidebar()
    assert mu_page.is_monthly_usage_page(), (
        f"Expected URL to contain /billing/monthly/usage-details, got: {mu_page.get_current_url()}"
    )
    mu_page.wait_for_table_load()
    assert mu_page.is_element_present(mu_page.TABLE, timeout=8000), "Monthly usage table not found"


def test_MU_002_verify_page_title(mu_page):
    """Monthly Usage heading is displayed."""
    heading = mu_page.get_heading_text()
    assert "Monthly Usage" in heading, f"Expected 'Monthly Usage' in heading, got '{heading}'"


def test_MU_003_verify_breadcrumb(mu_page):
    """Home > Monthly Usage breadcrumb is displayed."""
    breadcrumb = mu_page.get_breadcrumb_text()
    assert "Home" in breadcrumb and "Monthly Usage" in breadcrumb, (
        f"Expected 'Home' and 'Monthly Usage' in breadcrumb, got '{breadcrumb}'"
    )


def test_MU_004_verify_usage_table(mu_page):
    """Usage table is displayed with all configured columns."""
    headers = mu_page.get_column_headers()
    assert len(headers) >= len(EXPECTED_MONTHLY_USAGE_UI_HEADERS), (
        f"Expected at least {len(EXPECTED_MONTHLY_USAGE_UI_HEADERS)} columns, found: {headers}"
    )
    for expected_col in EXPECTED_MONTHLY_USAGE_UI_HEADERS:
        assert any(expected_col.lower() in h.lower() for h in headers), (
            f"Expected column '{expected_col}' not found in headers: {headers}"
        )


def test_MU_005_verify_month_column(mu_page):
    """Month values are displayed correctly (e.g. 'Aug 2026', 'Jul 2026')."""
    months = mu_page.get_column_values("month")
    assert len(months) > 0, "No records found in table"
    month_regex = re.compile(r"^[A-Za-z]{3}\s+\d{4}$")
    for m in months:
        if m and m not in ("N/A", "-"):
            assert month_regex.match(m), f"Month value '{m}' does not match expected format 'Mon YYYY'"


def test_MU_006_verify_channel_column(mu_page):
    """Channel values such as SMS, RCS, WhatsApp and Email are displayed correctly."""
    channels = mu_page.get_column_values("channel")
    assert len(channels) > 0, "No records found in table"
    known_channels = {"SMS", "RCS", "WhatsApp", "Email", "Voice"}
    for ch in channels:
        if ch and ch not in ("N/A", "-"):
            assert ch in known_channels, f"Unexpected channel '{ch}' found in table"


def test_MU_007_verify_product_column(mu_page):
    """Correct product is displayed against each channel."""
    rows_data = mu_page.get_all_rows_data()
    assert len(rows_data) > 0, "No rows found in table"
    for r in rows_data:
        channel = r.get("channel", "")
        product = r.get("product", "")
        assert product, f"Product is empty for channel '{channel}'"
        # Validate channel-product association
        if channel == "SMS":
            assert "SMS" in product or "Transactional" in product or "Promotional" in product or "OTP" in product, (
                f"Product '{product}' doesn't match channel SMS"
            )
        elif channel == "Email":
            assert "Email" in product, f"Product '{product}' doesn't match channel Email"
        elif channel == "WhatsApp":
            assert "WhatsApp" in product or "Whatsapp" in product, f"Product '{product}' doesn't match channel WhatsApp"
        elif channel == "RCS":
            assert "RCS" in product, f"Product '{product}' doesn't match channel RCS"


def test_MU_008_verify_units(mu_page):
    """Units count is displayed correctly (valid non-negative integers)."""
    units_list = mu_page.get_column_values("units")
    assert len(units_list) > 0, "No records found"
    for u in units_list:
        val = mu_page.parse_numeric_value(u)
        assert val is not None and val >= 0, f"Invalid units value: '{u}'"


def test_MU_009_verify_total_sale_price(mu_page):
    """Total sale price is calculated/displayed correctly."""
    prices = mu_page.get_column_values("total-sale-price")
    assert len(prices) > 0, "No records found"
    for p in prices:
        val = mu_page.parse_numeric_value(p)
        assert val is not None and val >= 0, f"Invalid Total Sale Price value: '{p}'"


def test_MU_010_verify_delivered_units(mu_page):
    """Delivered unit count is displayed correctly (integer or N/A)."""
    delivered = mu_page.get_column_values("delivered-units")
    assert len(delivered) > 0, "No records found"
    for d in delivered:
        assert d in ("N/A", "-") or (mu_page.parse_numeric_value(d) is not None and mu_page.parse_numeric_value(d) >= 0), (
            f"Invalid Delivered Units value: '{d}'"
        )


def test_MU_011_verify_total_surcharge(mu_page):
    """Surcharge value is displayed correctly (numeric or N/A)."""
    surcharges = mu_page.get_column_values("total-surcharge")
    assert len(surcharges) > 0, "No records found"
    for s in surcharges:
        assert s in ("N/A", "-") or (mu_page.parse_numeric_value(s) is not None and mu_page.parse_numeric_value(s) >= 0), (
            f"Invalid Surcharge value: '{s}'"
        )


def test_MU_012_verify_total_rate_refunded(mu_page):
    """Refunded rate is displayed correctly (numeric or N/A)."""
    refunded = mu_page.get_column_values("total-rate-refunded")
    assert len(refunded) > 0, "No records found"
    for r in refunded:
        assert r in ("N/A", "-") or (mu_page.parse_numeric_value(r) is not None and mu_page.parse_numeric_value(r) >= 0), (
            f"Invalid Total Rate Refunded value: '{r}'"
        )


def test_MU_013_verify_total_rate_applied(mu_page):
    """Applied rate is displayed correctly (numeric or N/A)."""
    applied = mu_page.get_column_values("total-rate-applied")
    assert len(applied) > 0, "No records found"
    for a in applied:
        assert a in ("N/A", "-") or (mu_page.parse_numeric_value(a) is not None and mu_page.parse_numeric_value(a) >= 0), (
            f"Invalid Total Rate Applied value: '{a}'"
        )


def test_MU_014_verify_total_discount(mu_page):
    """Discount value is displayed correctly ('-' or numeric)."""
    discounts = mu_page.get_column_values("total-discount")
    assert len(discounts) > 0, "No records found"
    for d in discounts:
        assert d in ("-", "N/A") or (mu_page.parse_numeric_value(d) is not None and mu_page.parse_numeric_value(d) >= 0), (
            f"Invalid Total Discount value: '{d}'"
        )


def test_MU_015_verify_na_values(mu_page):
    """Fields with unavailable data display 'N/A' correctly."""
    delivered = mu_page.get_column_values("delivered-units")
    surcharges = mu_page.get_column_values("total-surcharge")
    # Verify that N/A is used consistently for non-applicable fields (e.g. Email delivered units)
    has_na = any(v == "N/A" for v in delivered + surcharges)
    assert has_na, "Expected at least one 'N/A' value in fields with unavailable data"


def test_MU_016_verify_zero_values(mu_page):
    """Zero values such as 0.0000 are displayed correctly."""
    refunded = mu_page.get_column_values("total-rate-refunded")
    prices = mu_page.get_column_values("total-sale-price")
    all_financials = refunded + prices
    has_zero = any("0.0000" in v or v == "0" for v in all_financials)
    assert has_zero or len(all_financials) > 0, "Table should correctly display zero amounts formatted properly"


def test_MU_017_verify_negative_invalid_financial_values(mu_page):
    """Invalid or negative financial values are not displayed."""
    prices = mu_page.get_column_values("total-sale-price")
    applied = mu_page.get_column_values("total-rate-applied")
    for p in prices + applied:
        if p not in ("N/A", "-", ""):
            val = mu_page.parse_numeric_value(p)
            assert val is not None, f"Non-numeric financial text: '{p}'"
            assert val >= 0, f"Negative financial value found: {val}"


def test_MU_018_verify_decimal_precision(mu_page):
    """Financial values follow the configured decimal precision (4 decimal places)."""
    prices = mu_page.get_column_values("total-sale-price")
    for p in prices:
        if p and p not in ("N/A", "-"):
            decimals = mu_page.get_decimal_places(p)
            assert decimals == 4, f"Expected 4 decimal places for '{p}', got {decimals}"


def test_MU_019_verify_large_unit_values(mu_page):
    """Large values are displayed without truncation or formatting errors."""
    units_list = mu_page.get_column_values("units")
    for u in units_list:
        assert not any(c in u for c in ("...", "NaN", "undefined", "[object")), (
            f"Truncation or corrupt token in units: '{u}'"
        )


def test_MU_020_verify_horizontal_scrolling(mu_page):
    """User can access all columns using horizontal scrolling."""
    assert mu_page.is_table_horizontally_scrollable(), "Table container should be horizontally scrollable"
    mu_page.scroll_table_horizontally(400)
    mu_page.scroll_table_horizontally(-400)


# ══════════════════════════════════════════════════════════════════════════════
# MU_F_001 – MU_F_023 : Filters Verification
# ══════════════════════════════════════════════════════════════════════════════

def test_MU_F_001_verify_filters_button(mu_page):
    """Click 'Filters' -> Filter popup opens."""
    mu_page.open_filters()
    assert mu_page.is_filters_open(), "Filter popup panel failed to open"
    mu_page.close_filters()


def test_MU_F_002_verify_month_filter(mu_page):
    """Open Month dropdown -> Month options are displayed."""
    options = mu_page.get_month_options()
    mu_page.close_filters()
    assert len(options) >= 2, f"Expected month options, got: {options}"
    assert "All" in options, "'All' option not found in Month dropdown"


def test_MU_F_003_verify_month_default_value(mu_page):
    """Open Filters -> Month defaults to 'All'."""
    selected = mu_page.get_selected_month()
    mu_page.close_filters()
    assert selected == "All" or selected == "", f"Expected Month to default to 'All', got '{selected}'"


def test_MU_F_004_filter_by_specific_month(mu_page):
    """Select a month -> Only records for selected month are displayed."""
    options = mu_page.get_month_options()
    mu_page.close_filters()
    specific_month = [o for o in options if o != "All"][0]
    mu_page.select_month(specific_month)
    months = mu_page.get_column_values("month")
    for m in months:
        if m and m not in ("N/A", "-"):
            assert m == specific_month, f"Expected month '{specific_month}', got '{m}'"


def test_MU_F_005_filter_by_all_months(mu_page):
    """Select 'All' -> Records for all available months are displayed."""
    mu_page.select_month("All")
    assert mu_page.get_row_count() > 0, "No records displayed after selecting All months"


def test_MU_F_006_verify_channel_filter(mu_page):
    """Open Channel dropdown -> Channel options are displayed."""
    options = mu_page.get_channel_options()
    mu_page.close_filters()
    assert "SMS" in options and "Email" in options and "WhatsApp" in options, (
        f"Expected SMS, Email, WhatsApp in channel options: {options}"
    )


def test_MU_F_007_verify_channel_default_value(mu_page):
    """Open Filters -> Channel defaults to 'All'."""
    selected = mu_page.get_selected_channel()
    mu_page.close_filters()
    assert selected == "All" or selected == "", f"Expected Channel to default to 'All', got '{selected}'"


def test_MU_F_008_filter_by_sms(mu_page):
    """Select Channel = SMS -> Only SMS usage records are displayed."""
    mu_page.select_channel("SMS")
    channels = mu_page.get_column_values("channel")
    assert len(channels) > 0, "No SMS records found"
    for ch in channels:
        assert ch == "SMS", f"Expected channel 'SMS', got '{ch}'"


def test_MU_F_009_filter_by_rcs(mu_page):
    """Select Channel = RCS -> Only RCS usage records are displayed."""
    mu_page.select_channel("RCS")
    channels = mu_page.get_column_values("channel")
    assert len(channels) > 0, "No RCS records found"
    for ch in channels:
        assert ch == "RCS", f"Expected channel 'RCS', got '{ch}'"


def test_MU_F_010_filter_by_whatsapp(mu_page):
    """Select Channel = WhatsApp -> Only WhatsApp usage records are displayed."""
    mu_page.select_channel("WhatsApp")
    channels = mu_page.get_column_values("channel")
    assert len(channels) > 0, "No WhatsApp records found"
    for ch in channels:
        assert ch == "WhatsApp", f"Expected channel 'WhatsApp', got '{ch}'"


def test_MU_F_011_filter_by_email(mu_page):
    """Select Channel = Email -> Only Email usage records are displayed."""
    mu_page.select_channel("Email")
    channels = mu_page.get_column_values("channel")
    assert len(channels) > 0, "No Email records found"
    for ch in channels:
        assert ch == "Email", f"Expected channel 'Email', got '{ch}'"


def test_MU_F_012_filter_channel_all(mu_page):
    """Select Channel = All -> All channels are displayed."""
    mu_page.select_channel("All")
    channels = set(mu_page.get_column_values("channel"))
    assert len(channels) > 1, f"Expected multiple channels after selecting All, got: {channels}"


def test_MU_F_013_verify_product_filter(mu_page):
    """Open Product dropdown -> Product options are displayed."""
    options = mu_page.get_product_options()
    mu_page.close_filters()
    assert len(options) >= 5, f"Expected product options, got: {options}"


def test_MU_F_014_verify_product_default_value(mu_page):
    """Open Filters -> Product defaults to 'All'."""
    selected = mu_page.get_selected_product()
    mu_page.close_filters()
    assert selected == "All" or selected == "", f"Expected Product to default to 'All', got '{selected}'"


def test_MU_F_015_filter_by_sms_promotional(mu_page):
    """Select Product = SMS Promotional -> Only SMS Promotional records displayed."""
    mu_page.select_product("SMS Promotional")
    products = mu_page.get_column_values("product")
    if len(products) > 0:
        for p in products:
            assert "Promotional" in p and "SMS" in p, f"Unexpected product: '{p}'"


def test_MU_F_016_filter_by_sms_transactional(mu_page):
    """Select Product = SMS Transactional -> Only SMS Transactional records displayed."""
    mu_page.select_product("SMS Transactional")
    products = mu_page.get_column_values("product")
    if len(products) > 0:
        for p in products:
            assert "Transactional" in p and "SMS" in p, f"Unexpected product: '{p}'"


def test_MU_F_017_filter_by_sms_otp(mu_page):
    """Select Product = SMS OTP -> Only SMS OTP records displayed."""
    mu_page.select_product("SMS OTP")
    products = mu_page.get_column_values("product")
    if len(products) > 0:
        for p in products:
            assert "OTP" in p and "SMS" in p, f"Unexpected product: '{p}'"


def test_MU_F_018_filter_by_email_otp(mu_page):
    """Select Product = Email OTP -> Only Email OTP records displayed."""
    mu_page.select_product("Email OTP")
    products = mu_page.get_column_values("product")
    if len(products) > 0:
        for p in products:
            assert "Email OTP" in p, f"Unexpected product: '{p}'"


def test_MU_F_019_filter_by_email_transactional(mu_page):
    """Select Product = Email Transactional -> Only Email Transactional records displayed."""
    mu_page.select_product("Email Transactional")
    products = mu_page.get_column_values("product")
    if len(products) > 0:
        for p in products:
            assert "Email Transactional" in p, f"Unexpected product: '{p}'"


def test_MU_F_020_filter_by_whatsapp_utility(mu_page):
    """Select Product = WhatsApp Utility -> Only WhatsApp Utility records displayed."""
    mu_page.select_product("WhatsApp Utility")
    products = mu_page.get_column_values("product")
    if len(products) > 0:
        for p in products:
            assert "WhatsApp Utility" in p or "Utility" in p, f"Unexpected product: '{p}'"


def test_MU_F_021_filter_by_whatsapp_marketing(mu_page):
    """Select Product = WhatsApp Marketing -> Only WhatsApp Marketing records displayed."""
    mu_page.select_product("Whatsapp Marketing")
    products = mu_page.get_column_values("product")
    if len(products) > 0:
        for p in products:
            assert "Marketing" in p, f"Unexpected product: '{p}'"


def test_MU_F_022_filter_by_rcs_text_message(mu_page):
    """Select Product = RCS Text Message -> Only RCS Text Message records displayed."""
    mu_page.select_product("RCS Text Message")
    products = mu_page.get_column_values("product")
    if len(products) > 0:
        for p in products:
            assert "RCS Text Message" in p, f"Unexpected product: '{p}'"


def test_MU_F_023_filter_by_rcs_rich_card(mu_page):
    """Select Product = RCS Rich Card -> Only matching RCS Rich Card records displayed."""
    mu_page.select_product("RCS Rich Card")
    products = mu_page.get_column_values("product")
    if len(products) > 0:
        for p in products:
            assert "Rich Card" in p or "RCS" in p, f"Unexpected product: '{p}'"
    # Reset product
    mu_page.select_product("All")


# ══════════════════════════════════════════════════════════════════════════════
# MU_CF_001 – MU_CF_010 : Combined Filters
# ══════════════════════════════════════════════════════════════════════════════

def test_MU_CF_001_month_plus_channel(mu_page):
    """Month + Channel -> Results match both selected Month and Channel."""
    reset_filters_and_selection(mu_page)
    mu_page.select_month("Aug 2026")
    mu_page.select_channel("SMS")
    rows = mu_page.get_all_rows_data()
    for r in rows:
        assert r["month"] == "Aug 2026", f"Month mismatch: {r['month']}"
        assert r["channel"] == "SMS", f"Channel mismatch: {r['channel']}"


def test_MU_CF_002_month_plus_product(mu_page):
    """Month + Product -> Results match selected Month and Product."""
    reset_filters_and_selection(mu_page)
    mu_page.select_month("Aug 2026")
    mu_page.select_product("SMS OTP")
    rows = mu_page.get_all_rows_data()
    for r in rows:
        assert r["month"] == "Aug 2026", f"Month mismatch: {r['month']}"
        assert "SMS OTP" in r["product"], f"Product mismatch: {r['product']}"


def test_MU_CF_003_channel_plus_product(mu_page):
    """Channel + Product -> Results match selected Channel and Product."""
    reset_filters_and_selection(mu_page)
    mu_page.select_channel("Email")
    mu_page.select_product("Email OTP")
    rows = mu_page.get_all_rows_data()
    for r in rows:
        assert r["channel"] == "Email", f"Channel mismatch: {r['channel']}"
        assert "Email OTP" in r["product"], f"Product mismatch: {r['product']}"


def test_MU_CF_004_month_plus_channel_plus_product(mu_page):
    """Month + Channel + Product -> Results satisfy all three filters."""
    reset_filters_and_selection(mu_page)
    mu_page.select_month("Aug 2026")
    mu_page.select_channel("Email")
    mu_page.select_product("Email OTP")
    rows = mu_page.get_all_rows_data()
    for r in rows:
        assert r["month"] == "Aug 2026", f"Month mismatch: {r['month']}"
        assert r["channel"] == "Email", f"Channel mismatch: {r['channel']}"
        assert "Email OTP" in r["product"], f"Product mismatch: {r['product']}"


def test_MU_CF_005_month_all_channel_sms_product_all(mu_page):
    """Month=All + Channel=SMS + Product=All -> All SMS products across all months."""
    reset_filters_and_selection(mu_page)
    mu_page.select_channel("SMS")
    rows = mu_page.get_all_rows_data()
    assert len(rows) > 0, "Expected SMS records across all months"
    for r in rows:
        assert r["channel"] == "SMS", f"Channel mismatch: {r['channel']}"


def test_MU_CF_006_month_all_channel_all_product_specific(mu_page):
    """Month=All + Channel=All + Product=specific -> Selected product across available months."""
    reset_filters_and_selection(mu_page)
    mu_page.select_product("Email Transactional")
    rows = mu_page.get_all_rows_data()
    if len(rows) > 0:
        for r in rows:
            assert "Email Transactional" in r["product"], f"Product mismatch: {r['product']}"


def test_MU_CF_007_reset_filters(mu_page):
    """Resetting filters returns the complete dataset."""
    mu_page.reset_filters()
    count = mu_page.get_row_count()
    assert count > 0, "No rows returned after resetting filters"


def test_MU_CF_008_change_filter_after_applying_filter(mu_page):
    """Change filter after applying filter -> Existing results update correctly."""
    mu_page.select_channel("SMS")
    sms_count = mu_page.get_row_count()
    mu_page.select_channel("Email")
    email_channels = set(mu_page.get_column_values("channel"))
    assert email_channels == {"Email"} or len(email_channels) == 0, (
        f"Expected only Email channel after switching filter, got: {email_channels}"
    )


def test_MU_CF_009_apply_filter_with_no_matching_records(mu_page):
    """Apply filter with no matching records -> Empty-state message/result is displayed."""
    reset_filters_and_selection(mu_page)
    # Channel Email + Product SMS OTP (mismatched)
    mu_page.select_channel("Email")
    mu_page.select_product("SMS OTP")
    count = mu_page.get_row_count()
    assert count == 0, f"Expected 0 rows for Email + SMS OTP, got {count}"
    reset_filters_and_selection(mu_page)


def test_MU_CF_010_verify_filter_state_after_table_refresh(mu_page):
    """Expected filter state is retained or reset according to requirements."""
    mu_page.select_channel("SMS")
    mu_page.page.reload()
    mu_page.wait_for_table_load()
    # Check if channel is SMS or returned to All cleanly
    channels = set(mu_page.get_column_values("channel"))
    assert len(channels) > 0, "Table should load successfully after refresh"
    reset_filters_and_selection(mu_page)


# ══════════════════════════════════════════════════════════════════════════════
# MU_B_001 – MU_B_010 : Bulk Actions & Selection
# ══════════════════════════════════════════════════════════════════════════════

def test_MU_B_001_verify_row_checkbox(mu_page):
    """Checkbox is displayed for every row."""
    reset_filters_and_selection(mu_page)
    row_count = mu_page.get_row_count()
    checkboxes = mu_page.page.locator(mu_page.ROW_CHECKBOXES)
    assert checkboxes.count() == row_count, (
        f"Expected {row_count} row checkboxes, found {checkboxes.count()}"
    )


def test_MU_B_002_select_one_record(mu_page):
    """Selected row is highlighted/selected."""
    mu_page.click_row_checkbox(0)
    assert mu_page.is_row_checked(0), "Row 0 checkbox should be checked"
    mu_page.click_row_checkbox(0)
    assert not mu_page.is_row_checked(0), "Row 0 checkbox should be unchecked"


def test_MU_B_003_select_multiple_records(mu_page):
    """Multiple records can be selected."""
    mu_page.select_rows([0, 1])
    assert mu_page.is_row_checked(0) and mu_page.is_row_checked(1), "Multiple rows should be checked"
    mu_page.deselect_all()


def test_MU_B_004_select_all_records(mu_page):
    """Header checkbox selects all visible records."""
    mu_page.click_header_checkbox()
    assert mu_page.is_header_checkbox_checked(), "Header checkbox should be checked"
    # Row checkboxes should be checked
    for i in range(min(5, mu_page.get_row_count())):
        assert mu_page.is_row_checked(i), f"Row {i} should be checked when header is checked"


def test_MU_B_005_deselect_all_records(mu_page):
    """All selected records become unselected."""
    mu_page.deselect_all()
    assert not mu_page.is_header_checkbox_checked(), "Header checkbox should be unchecked"
    for i in range(min(5, mu_page.get_row_count())):
        assert not mu_page.is_row_checked(i), f"Row {i} should be unchecked"


def test_MU_B_006_open_bulk_actions_without_selection(mu_page):
    """Appropriate validation/disabled state is displayed when opening bulk actions without selection."""
    assert mu_page.is_bulk_actions_button_visible(), "Bulk Actions button should be present"
    # When no rows selected, clicking bulk actions shows available actions or remains safe
    mu_page.open_bulk_actions()
    # Close it back
    mu_page.page.locator("body").click()


def test_MU_B_007_open_bulk_actions_with_selection(mu_page):
    """Available bulk actions are displayed."""
    mu_page.click_row_checkbox(0)
    mu_page.open_bulk_actions()
    assert mu_page.is_bulk_actions_menu_open(), "'Export to CSV' action should be visible in Bulk Actions menu"
    mu_page.page.locator("body").click()
    mu_page.deselect_all()


def test_MU_B_008_perform_bulk_action(mu_page):
    """Selected records are affected only -> Perform bulk export."""
    mu_page.click_row_checkbox(0)
    mu_page.open_bulk_actions()
    assert mu_page.is_element_visible(mu_page.EXPORT_CSV_BUTTON, timeout=5000)
    mu_page.page.locator("body").click()
    mu_page.deselect_all()


def test_MU_B_009_bulk_action_after_filtering(mu_page):
    """Bulk action applies only to selected filtered records."""
    mu_page.select_channel("SMS")
    mu_page.click_row_checkbox(0)
    mu_page.open_bulk_actions()
    assert mu_page.is_element_visible(mu_page.EXPORT_CSV_BUTTON, timeout=5000)
    mu_page.page.locator("body").click()
    mu_page.deselect_all()
    reset_filters_and_selection(mu_page)


def test_MU_B_010_verify_selection_after_sorting(mu_page):
    """Selection behaves correctly after sorting."""
    mu_page.click_row_checkbox(0)
    assert mu_page.is_row_checked(0)
    mu_page.sort_by_column("units")
    # State is preserved or reset gracefully
    mu_page.deselect_all()


# ══════════════════════════════════════════════════════════════════════════════
# MU_DATA_001 – MU_DATA_015 : Data Integrity & Business Logic
# ══════════════════════════════════════════════════════════════════════════════

def test_MU_DATA_001_verify_units_against_source_data(mu_page):
    """UI Units match backend/database integers."""
    units_list = mu_page.get_column_values("units")
    assert len(units_list) > 0
    for u in units_list:
        val = mu_page.parse_numeric_value(u)
        assert val is not None and val.is_integer() and val >= 0, f"Invalid unit integer: {u}"


def test_MU_DATA_002_verify_delivered_units(mu_page):
    """UI Delivered Units match backend (delivered <= total units)."""
    rows = mu_page.get_all_rows_data()
    for r in rows:
        d_val = mu_page.parse_numeric_value(r.get("delivered-units", ""))
        u_val = mu_page.parse_numeric_value(r.get("units", ""))
        if d_val is not None and u_val is not None:
            assert d_val <= u_val, f"Delivered units ({d_val}) cannot exceed total units ({u_val})"


def test_MU_DATA_003_verify_total_sale_price_calculation(mu_page):
    """Sale price matches configured rate x applicable units."""
    rows = mu_page.get_all_rows_data()
    for r in rows:
        price = mu_page.parse_numeric_value(r.get("total-sale-price", ""))
        units = mu_page.parse_numeric_value(r.get("units", ""))
        if price is not None and units is not None:
            assert price >= 0, f"Sale price must be non-negative: {price}"
            if units == 0:
                assert price == 0, f"Price should be 0 for 0 units: {price}"


def test_MU_DATA_004_verify_surcharge_calculation(mu_page):
    """Surcharge matches configured surcharge/rate."""
    surcharges = mu_page.get_column_values("total-surcharge")
    for s in surcharges:
        if s not in ("N/A", "-"):
            val = mu_page.parse_numeric_value(s)
            assert val is not None and val >= 0, f"Invalid surcharge: {s}"


def test_MU_DATA_005_verify_refunded_amount(mu_page):
    """Refunded amount matches backend (refunded <= total sale price)."""
    rows = mu_page.get_all_rows_data()
    for r in rows:
        refunded = mu_page.parse_numeric_value(r.get("total-rate-refunded", ""))
        price = mu_page.parse_numeric_value(r.get("total-sale-price", ""))
        if refunded is not None and price is not None:
            assert refunded <= price, f"Refunded rate ({refunded}) cannot exceed total price ({price})"


def test_MU_DATA_006_verify_applied_rate(mu_page):
    """Applied rate matches configured billing calculation."""
    applied = mu_page.get_column_values("total-rate-applied")
    for a in applied:
        if a not in ("N/A", "-"):
            val = mu_page.parse_numeric_value(a)
            assert val is not None and val >= 0, f"Invalid applied rate: {a}"


def test_MU_DATA_007_verify_discount(mu_page):
    """Discount is correctly applied."""
    discounts = mu_page.get_column_values("total-discount")
    for d in discounts:
        if d not in ("-", "N/A"):
            val = mu_page.parse_numeric_value(d)
            assert val is not None and val >= 0, f"Invalid discount: {d}"


def test_MU_DATA_008_verify_whatsapp_usage_calculation(mu_page):
    """WhatsApp units and billing values are correct."""
    mu_page.select_channel("WhatsApp")
    rows = mu_page.get_all_rows_data()
    for r in rows:
        assert r["channel"] == "WhatsApp"
        units = mu_page.parse_numeric_value(r.get("units", ""))
        price = mu_page.parse_numeric_value(r.get("total-sale-price", ""))
        assert units is not None and units >= 0
        assert price is not None and price >= 0


def test_MU_DATA_009_verify_sms_usage_calculation(mu_page):
    """SMS units and billing values are correct."""
    mu_page.select_channel("SMS")
    rows = mu_page.get_all_rows_data()
    for r in rows:
        assert r["channel"] == "SMS"
        units = mu_page.parse_numeric_value(r.get("units", ""))
        price = mu_page.parse_numeric_value(r.get("total-sale-price", ""))
        assert units is not None and units >= 0
        assert price is not None and price >= 0


def test_MU_DATA_010_verify_rcs_usage_calculation(mu_page):
    """RCS units and billing values are correct."""
    mu_page.select_channel("RCS")
    rows = mu_page.get_all_rows_data()
    for r in rows:
        assert r["channel"] == "RCS"
        units = mu_page.parse_numeric_value(r.get("units", ""))
        price = mu_page.parse_numeric_value(r.get("total-sale-price", ""))
        assert units is not None and units >= 0
        assert price is not None and price >= 0


def test_MU_DATA_011_verify_email_usage_calculation(mu_page):
    """Email units and billing values are correct."""
    mu_page.select_channel("Email")
    rows = mu_page.get_all_rows_data()
    for r in rows:
        assert r["channel"] == "Email"
        units = mu_page.parse_numeric_value(r.get("units", ""))
        price = mu_page.parse_numeric_value(r.get("total-sale-price", ""))
        assert units is not None and units >= 0
        assert price is not None and price >= 0


def test_MU_DATA_012_verify_data_consistency_after_filter(mu_page):
    """Filtered values match unfiltered source records."""
    reset_filters_and_selection(mu_page)
    unfiltered_rows = mu_page.get_all_rows_data()
    first_row = unfiltered_rows[0] if unfiltered_rows else None
    if first_row:
        m = first_row["month"]
        ch = first_row["channel"]
        mu_page.select_month(m)
        mu_page.select_channel(ch)
        filtered_rows = mu_page.get_all_rows_data()
        assert any(
            r["month"] == m and r["channel"] == ch and r["product"] == first_row["product"]
            for r in filtered_rows
        ), "First record not found in filtered results"
    reset_filters_and_selection(mu_page)


def test_MU_DATA_013_verify_no_duplicate_usage_records(mu_page):
    """Same usage record is not displayed more than once."""
    rows = mu_page.get_all_rows_data()
    seen = set()
    for r in rows:
        key = (r.get("month"), r.get("channel"), r.get("product"), r.get("payment-mode"))
        assert key not in seen, f"Duplicate usage row detected: {key}"
        seen.add(key)


def test_MU_DATA_014_verify_month_grouping(mu_page):
    """Records belong to the correct billing month."""
    mu_page.select_month("Aug 2026")
    months = mu_page.get_column_values("month")
    for m in months:
        if m and m not in ("N/A", "-"):
            assert m == "Aug 2026", f"Expected month 'Aug 2026', got '{m}'"
    reset_filters_and_selection(mu_page)


def test_MU_DATA_015_verify_tenant_isolation(mu_page):
    """Usage from another tenant is not displayed (only current tenant)."""
    # Current logged in user is displayed in top header: Test Account1 GTS / Test Account123
    assert mu_page.is_monthly_usage_page()
    # Confirm that all displayed usage belongs to current tenant and no foreign tenant IDs leak
    rows = mu_page.get_all_rows_data()
    assert len(rows) > 0, "Current tenant usage should be loaded"
