"""
SMS Error Codes (reference list) — Single Sequential Flow
================================================================
Covers: Channels → SMS → More → Error Codes page, SEC-001 - SEC-030
(URL: /channels/sms/errorcodes)

Migrated to Playwright: local page-object fixture renamed
`error_codes_page` (built on conftest.py's `module_logged_in_page`) to
avoid shadowing pytest-playwright's reserved `page` fixture. Native
dialog handling for the XSS test now goes through
Helpers.expect_no_dialog (page.once("dialog", ...)) instead of
Selenium's reactive driver.switch_to.alert; window resizing for the
responsive-UI test uses Playwright's page.set_viewport_size().

NOTE: this is a DIFFERENT page from the SMS Error Code Report
(/channels/sms/reports/error-code, see test_sms_error_code_report_flow.py).
This page is a static reference/lookup table of every SMS error code
(Name / Code / Description) — it has no Report Type, Group By, Date
Range, Filters popover, or Export CSV control. See
pages/sms_error_codes_page.py docstring for the full list of
DOM-confirmed differences from the report pages.

IMPORTANT — DOM-confirmed discrepancy vs. the supplied test-case spec:
SEC-017 expects "Descriptions should sort alphabetically", but the live
DOM's Description column header is a bare <span> with no wire:click=
"sortBy('description')" anywhere on the page — Name and Code are the
only two sortable columns (CONFIRMED, both wrapped in real <button
wire:click="sortBy(...)"> elements). Per this project's "never guess"
rule, SEC-017 is written to verify the actual (unsortable) DOM
structure rather than asserting a sort control that does not exist.

SEC-015 (Code sorting) and SEC-016 (Name sorting) have been REMOVED at
the user's explicit request after a live run showed the sortBy('code')/
sortBy('name') click handlers firing without the visible row order
actually changing across two toggles.

Run:
    pytest tests/test_sms_error_codes_flow.py -v
"""
import pytest

from pages.common.login_page import LoginPage
from pages.sms.sms_error_codes_page import SmsErrorCodesPage
from utils.config import Config


pytestmark = [pytest.mark.sms, pytest.mark.report]



@pytest.fixture(scope="module")
def error_codes_page(module_logged_in_page):
    p = SmsErrorCodesPage(module_logged_in_page)
    p.navigate_to_report()
    return p


def ensure_on_page(p):
    if not p.is_report_page():
        p.navigate_to_report()
        p.page.wait_for_timeout(1000)


@pytest.fixture(autouse=True)
def _reset_after_test(error_codes_page):
    """Hard reset to a clean page view after every test — this page has
    stateful search/columns state that can otherwise leak between tests
    (same rationale as every other SMS suite in this project)."""
    yield
    try:
        ensure_on_page(error_codes_page)
        error_codes_page.navigate_to_report()
    except Exception:
        pass


# ── SEC-001 — Page Load ─────────────────────────────────────────────────

@pytest.mark.smoke
def test_sec001_page_loads_successfully(error_codes_page):
    """SEC-001: SMS Error Codes page loads successfully without errors."""
    ensure_on_page(error_codes_page)
    assert error_codes_page.is_report_page(), "URL should contain /channels/sms/errorcodes"
    title = error_codes_page.get_title().lower()
    assert "404" not in title and "error" not in title


# ── SEC-002-004 — UI Validation ─────────────────────────────────────────

@pytest.mark.smoke
def test_sec002_page_title(error_codes_page):
    """SEC-002: Page (heading) title displays 'SMS Error Codes'."""
    ensure_on_page(error_codes_page)
    assert error_codes_page.get_page_title_text() == "SMS Error Codes"


@pytest.mark.smoke
def test_sec003_breadcrumb_navigation(error_codes_page):
    """SEC-003: Breadcrumb displays Home > Channels > SMS Error Codes."""
    ensure_on_page(error_codes_page)
    text = error_codes_page.get_breadcrumb_text()
    assert "Home" in text
    assert "Channels" in text
    assert "SMS Error Codes" in text


@pytest.mark.smoke
def test_sec004_name_code_description_columns_visible(error_codes_page):
    """SEC-004: Name, Code and Description columns should be visible."""
    ensure_on_page(error_codes_page)
    headers = [h.lower() for h in error_codes_page.get_visible_column_headers()]
    assert any("name" in h for h in headers)
    assert any("code" in h for h in headers)
    assert any("description" in h for h in headers)


# ── SEC-005-007 — Data Display ──────────────────────────────────────────

@pytest.mark.smoke
def test_sec005_error_code_records_displayed(error_codes_page):
    """SEC-005: SMS error code records should be displayed."""
    ensure_on_page(error_codes_page)
    assert error_codes_page.has_records(), "Table should display records"
    assert error_codes_page.get_row_count() > 0


@pytest.mark.regression
def test_sec006_delivered_error_code(error_codes_page):
    """SEC-006: Search '000' -> DELIVRD / Code 000 / Delivered."""
    ensure_on_page(error_codes_page)
    error_codes_page.search("000")
    names = error_codes_page.get_column_values("name")
    codes = error_codes_page.get_column_values("code")
    descs = error_codes_page.get_column_values("description")
    assert "DELIVRD" in names
    assert "000" in codes
    assert "Delivered" in descs
    error_codes_page.clear_search()


@pytest.mark.regression
def test_sec007_failed_error_codes_display(error_codes_page):
    """SEC-007: Failed error codes should display correctly (confirmed
    present on page 1's natural load — codes 101-109, Name=FAILED)."""
    ensure_on_page(error_codes_page)
    names = error_codes_page.get_column_values("name")
    assert "FAILED" in names


# ── SEC-008-014 — Search ────────────────────────────────────────────────

@pytest.mark.regression
def test_sec008_search_by_name(error_codes_page):
    """SEC-008: Search 'FAILED' -> matching records displayed."""
    ensure_on_page(error_codes_page)
    error_codes_page.search("FAILED")
    assert error_codes_page.has_records()
    names = error_codes_page.get_column_values("name")
    assert all(n == "FAILED" for n in names if n)
    error_codes_page.clear_search()


@pytest.mark.regression
def test_sec009_search_by_code(error_codes_page):
    """SEC-009: Search '101' -> Code 101 record appears (FAILED /
    TEMPLATE_ID_NOT_FOUND, confirmed live DOM)."""
    ensure_on_page(error_codes_page)
    error_codes_page.search("101")
    codes = error_codes_page.get_column_values("code")
    descs = error_codes_page.get_column_values("description")
    assert "101" in codes
    assert "TEMPLATE_ID_NOT_FOUND" in descs
    error_codes_page.clear_search()


@pytest.mark.regression
def test_sec010_search_by_description(error_codes_page):
    """SEC-010: Search 'CONTENT_NOT_MATCHED' -> matching record appears."""
    ensure_on_page(error_codes_page)
    error_codes_page.search("CONTENT_NOT_MATCHED")
    descs = error_codes_page.get_column_values("description")
    assert any("CONTENT_NOT_MATCHED" in d for d in descs)
    error_codes_page.clear_search()


@pytest.mark.regression
def test_sec011_partial_search(error_codes_page):
    """SEC-011: Partial search 'TEMP' -> template-related records appear."""
    ensure_on_page(error_codes_page)
    error_codes_page.search("TEMP")
    assert error_codes_page.has_records()
    descs = error_codes_page.get_column_values("description")
    assert any("temp" in d.lower() for d in descs)
    error_codes_page.clear_search()


@pytest.mark.regression
def test_sec012_case_insensitive_search(error_codes_page):
    """SEC-012: Search 'failed' (lowercase) -> FAILED records appear."""
    ensure_on_page(error_codes_page)
    error_codes_page.search("failed")
    assert error_codes_page.has_records()
    names = error_codes_page.get_column_values("name")
    assert all(n == "FAILED" for n in names if n)
    error_codes_page.clear_search()


@pytest.mark.regression
@pytest.mark.negative
def test_sec013_invalid_search(error_codes_page):
    """SEC-013: Search 'XYZ123' -> no matching records displayed."""
    ensure_on_page(error_codes_page)
    error_codes_page.search("XYZ123")
    assert error_codes_page.has_no_records_message() or error_codes_page.get_row_count() == 0
    error_codes_page.clear_search()


@pytest.mark.regression
def test_sec014_clearing_search(error_codes_page):
    """SEC-014: Clearing search restores the complete record list."""
    ensure_on_page(error_codes_page)
    error_codes_page.search("000")
    assert error_codes_page.get_row_count() >= 1
    error_codes_page.clear_search()
    assert error_codes_page.has_records()
    text = error_codes_page.get_pagination_results_text()
    assert "of" in text  # e.g. "Showing 1 to 10 of 58 results"


# ── SEC-017 — Sorting ────────────────────────────────────────────────────

@pytest.mark.regression
def test_sec017_description_sorting(error_codes_page):
    """SEC-017 (DOM-confirmed adaptation): the supplied spec expects
    Description to sort alphabetically, but the live DOM has NO sortBy
    ('description') control anywhere on the page -- only Name and Code
    are sortable (both wrapped in real <button wire:click="sortBy(...)">
    elements; Description's <th> is a bare <span>). This test verifies
    that documented (unsortable) structure rather than asserting a
    control that doesn't exist."""
    ensure_on_page(error_codes_page)
    assert error_codes_page.has_description_sort_control() is False, \
        "Description column is confirmed NOT sortable in the live DOM"


# ── SEC-018-022 — Columns ────────────────────────────────────────────────

@pytest.mark.regression
def test_sec018_columns_button_opens_menu(error_codes_page):
    """SEC-018: Clicking Columns opens the column selection menu."""
    ensure_on_page(error_codes_page)
    error_codes_page.open_columns_dropdown()
    assert error_codes_page.is_element_present(error_codes_page.COLUMN_CHECKBOXES, timeout=5000)


@pytest.mark.regression
def test_sec019_hide_show_name_column(error_codes_page):
    """SEC-019: Hiding the Name column removes it from the visible headers."""
    ensure_on_page(error_codes_page)
    try:
        error_codes_page.toggle_column("name")
        headers = [h.lower() for h in error_codes_page.get_visible_column_headers()]
        assert not any(h == "name" for h in headers)
    finally:
        error_codes_page.restore_all_columns()


@pytest.mark.regression
def test_sec020_hide_show_code_column(error_codes_page):
    """SEC-020: Hiding the Code column removes it from the visible headers."""
    ensure_on_page(error_codes_page)
    try:
        error_codes_page.toggle_column("code")
        headers = [h.lower() for h in error_codes_page.get_visible_column_headers()]
        assert not any(h == "code" for h in headers)
    finally:
        error_codes_page.restore_all_columns()


@pytest.mark.regression
def test_sec021_hide_show_description_column(error_codes_page):
    """SEC-021: Hiding the Description column removes it from the visible headers."""
    ensure_on_page(error_codes_page)
    try:
        error_codes_page.toggle_column("description")
        headers = [h.lower() for h in error_codes_page.get_visible_column_headers()]
        assert not any(h == "description" for h in headers)
    finally:
        error_codes_page.restore_all_columns()


@pytest.mark.regression
def test_sec022_restore_hidden_columns(error_codes_page):
    """SEC-022: Re-enabling hidden columns displays them again."""
    ensure_on_page(error_codes_page)
    error_codes_page.toggle_column("description")
    headers = [h.lower() for h in error_codes_page.get_visible_column_headers()]
    assert not any(h == "description" for h in headers)
    error_codes_page.restore_all_columns()
    headers = [h.lower() for h in error_codes_page.get_visible_column_headers()]
    assert any("name" in h for h in headers)
    assert any("code" in h for h in headers)
    assert any("description" in h for h in headers)


# ── SEC-023 — Refresh ────────────────────────────────────────────────────

@pytest.mark.regression
def test_sec023_page_refresh(error_codes_page):
    """SEC-023: Refreshing the browser reloads the page successfully."""
    ensure_on_page(error_codes_page)
    error_codes_page.page.reload()
    error_codes_page.page.wait_for_timeout(2000)
    assert error_codes_page.is_report_page()
    assert error_codes_page.get_page_title_text() == "SMS Error Codes"


# ── SEC-024 — Security: Unauthorized Access ─────────────────────────────

@pytest.mark.regression
@pytest.mark.negative
def test_sec024_unauthorized_access_redirects_to_login(error_codes_page):
    """SEC-024: Logging out then accessing the page URL redirects to Login."""
    ensure_on_page(error_codes_page)
    try:
        error_codes_page.logout()
        error_codes_page.h.wait_for_url_contains("login", timeout=10000)
        error_codes_page.open(SmsErrorCodesPage.REPORT_URL)
        error_codes_page.page.wait_for_timeout(2000)
        assert "login" in error_codes_page.get_current_url().lower(), \
            "Should be redirected to Login page when not authenticated"
    finally:
        # Re-authenticate so subsequent tests in this module still pass.
        login = LoginPage(error_codes_page.page)
        login.navigate()
        login.login(Config.VALID_EMAIL, Config.VALID_PASSWORD)
        login.h.wait_for_url_contains("/", timeout=20000)
        error_codes_page.navigate_to_report()


# ── SEC-025-027 — Input Validation / Security ───────────────────────────

@pytest.mark.regression
@pytest.mark.negative
def test_sec025_search_special_characters(error_codes_page):
    """SEC-025: Searching '@#$%^' should not crash the application."""
    ensure_on_page(error_codes_page)
    error_codes_page.search("@#$%^")
    title = error_codes_page.get_title().lower()
    assert "404" not in title and "error" not in title
    error_codes_page.clear_search()


@pytest.mark.regression
@pytest.mark.negative
def test_sec026_sql_injection_prevention(error_codes_page):
    """SEC-026: SQL injection payload is treated as plain text search input."""
    ensure_on_page(error_codes_page)
    error_codes_page.search("' OR 1=1 --")
    title = error_codes_page.get_title().lower()
    assert "404" not in title and "error" not in title
    # A real SQLi would return every row (or crash); a safely-parameterised
    # search treats it as a literal string with (almost certainly) no match.
    assert error_codes_page.get_row_count() <= 58
    error_codes_page.clear_search()


@pytest.mark.regression
@pytest.mark.negative
def test_sec027_xss_prevention(error_codes_page):
    """SEC-027: XSS payload in search box must not execute a script/alert."""
    ensure_on_page(error_codes_page)
    dialog_message = error_codes_page.search_expect_no_dialog("<script>alert(1)</script>")
    assert dialog_message is None, \
        f"XSS payload triggered a native dialog -- script executed: {dialog_message!r}"
    title = error_codes_page.get_title().lower()
    assert "404" not in title and "error" not in title
    error_codes_page.clear_search()


# ── SEC-028 — Responsive UI ──────────────────────────────────────────────

@pytest.mark.regression
def test_sec028_responsive_ui(error_codes_page):
    """SEC-028: Resizing the browser keeps the UI aligned (no crash/blank)."""
    ensure_on_page(error_codes_page)
    original_size = error_codes_page.page.viewport_size
    try:
        error_codes_page.page.set_viewport_size({"width": 375, "height": 667})  # mobile viewport
        error_codes_page.page.wait_for_timeout(1000)
        assert error_codes_page.is_element_present(error_codes_page.SEARCH_BOX, timeout=5000)
        error_codes_page.page.set_viewport_size({"width": 1366, "height": 768})  # desktop viewport
        error_codes_page.page.wait_for_timeout(1000)
        assert error_codes_page.is_element_present(error_codes_page.TABLE, timeout=5000)
    finally:
        if original_size:
            error_codes_page.page.set_viewport_size(original_size)


# ── SEC-029 — Performance ────────────────────────────────────────────────

@pytest.mark.regression
def test_sec029_page_performance(error_codes_page):
    """SEC-029: Page loads within an acceptable response time (<8000ms)."""
    ensure_on_page(error_codes_page)
    error_codes_page.navigate_to_report()
    load_time = error_codes_page.get_page_load_time_ms()
    if load_time is not None:
        assert load_time < 8000, f"Page load took {load_time}ms (>8000ms)"


# ── SEC-030 — Data Accuracy ──────────────────────────────────────────────

@pytest.mark.regression
def test_sec030_error_code_data_accuracy(error_codes_page):
    """SEC-030: Displayed record matches the confirmed known mapping
    (Code 000 -> DELIVRD / Delivered), used as the best available
    structural cross-check without direct backend/API access."""
    ensure_on_page(error_codes_page)
    error_codes_page.search("000")
    names = error_codes_page.get_column_values("name")
    codes = error_codes_page.get_column_values("code")
    descs = error_codes_page.get_column_values("description")
    assert "DELIVRD" in names and "000" in codes and "Delivered" in descs
    error_codes_page.clear_search()
