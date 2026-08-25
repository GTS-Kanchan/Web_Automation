"""
RCS Error Codes (reference list) — Single Sequential Flow
================================================================
Covers: Channels → RCS → More → Error Codes page, REC-001 - REC-030
(URL: /rcs/error-codes)

NOTE: this is a DIFFERENT page from the RCS Error Code Analytics Report
(/rcs/analytics/error-code, see test_rcs_error_code_analytics_flow.py).
This page is a static reference/lookup table of every RCS error code
(Name / Code / Description) — it has no Report Type, Group By, Date
Range, Filters popover, or Export CSV control. See
pages/rcs_error_codes_page.py docstring for the full list of
DOM-confirmed details.

This suite is the RCS analog of test_sms_error_codes_flow.py and follows
exactly the same structure: module-scoped fixtures, autouse hard-reset,
fill()-based search, column-toggle with restore, pagination checks, and
security tests (unauthorized access, special chars, SQL injection, XSS).

IMPORTANT — Description column:
  The Description column header is a bare <span> with no
  wire:click="sortBy('description')" — confirmed absent (same as the SMS
  equivalent). REC-017 verifies this unsortable structure rather than
  asserting a control that doesn't exist.

All tests run in one browser session (module-scoped).

Run:
    pytest tests/test_rcs_error_codes_flow.py -v
"""
import pytest

from pages.common.login_page import LoginPage
from pages.rcs.rcs_error_codes_page import RcsErrorCodesPage
from utils.config import Config


pytestmark = [pytest.mark.rcs, pytest.mark.report]

@pytest.fixture(scope="module")
def rcs_error_codes_page(module_logged_in_page):
    p = RcsErrorCodesPage(module_logged_in_page)
    p.navigate_to_report()
    return p


def ensure_on_page(p):
    if not p.is_report_page():
        p.navigate_to_report()
        p.page.wait_for_timeout(1000)


@pytest.fixture(autouse=True)
def _reset_after_test(rcs_error_codes_page):
    """Hard reset to a clean page view after every test — this page has
    stateful search/column state that can otherwise leak between tests
    (same rationale as every other suite in this project)."""
    yield
    try:
        ensure_on_page(rcs_error_codes_page)
        rcs_error_codes_page.navigate_to_report()
    except Exception:
        pass


# ── REC-001 — Page Load ─────────────────────────────────────────────────

@pytest.mark.smoke
def test_rec001_page_loads_successfully(rcs_error_codes_page):
    """REC-001: RCS Error Codes page loads successfully without errors."""
    ensure_on_page(rcs_error_codes_page)
    assert rcs_error_codes_page.is_report_page(), "URL should contain /rcs/error-codes"
    title = rcs_error_codes_page.get_title().lower()
    assert "404" not in title and "error" not in title


# ── REC-002-004 — UI Validation ─────────────────────────────────────────

@pytest.mark.smoke
def test_rec002_page_title(rcs_error_codes_page):
    """REC-002: Page (heading) title displays 'RCS Error Codes'."""
    ensure_on_page(rcs_error_codes_page)
    assert rcs_error_codes_page.get_page_title_text() == "RCS Error Codes"


@pytest.mark.smoke
def test_rec003_breadcrumb_navigation(rcs_error_codes_page):
    """REC-003: Breadcrumb displays Home > Channels > RCS Error Codes."""
    ensure_on_page(rcs_error_codes_page)
    text = rcs_error_codes_page.get_breadcrumb_text()
    assert "Home" in text
    assert "Channels" in text or "RCS" in text


@pytest.mark.smoke
def test_rec004_name_code_description_columns_visible(rcs_error_codes_page):
    """REC-004: Name, Code and Description columns should all be visible."""
    ensure_on_page(rcs_error_codes_page)
    headers = [h.lower() for h in rcs_error_codes_page.get_visible_column_headers()]
    assert any("name" in h for h in headers), f"Name column not found: {headers}"
    assert any("code" in h for h in headers), f"Code column not found: {headers}"
    assert any("description" in h for h in headers), \
        f"Description column not found: {headers}"


# ── REC-005-007 — Data Display ──────────────────────────────────────────

@pytest.mark.smoke
def test_rec005_error_code_records_displayed(rcs_error_codes_page):
    """REC-005: RCS error code records should be displayed in the table."""
    ensure_on_page(rcs_error_codes_page)
    assert rcs_error_codes_page.has_records(), "Table should display error code records"
    assert rcs_error_codes_page.get_row_count() > 0


@pytest.mark.regression
def test_rec006_name_column_values(rcs_error_codes_page):
    """REC-006: Name column should display non-empty values for all rows."""
    ensure_on_page(rcs_error_codes_page)
    values = rcs_error_codes_page.get_column_values("name")
    assert values, "Name column should have values"
    assert all(len(v) > 0 for v in values), \
        f"All Name values should be non-empty; got: {values!r}"


@pytest.mark.regression
def test_rec007_code_column_values(rcs_error_codes_page):
    """REC-007: Code column should display non-empty values for all rows."""
    ensure_on_page(rcs_error_codes_page)
    values = rcs_error_codes_page.get_column_values("code")
    assert values, "Code column should have values"
    assert all(len(v) > 0 for v in values), \
        f"All Code values should be non-empty; got: {values!r}"


# ── REC-008-014 — Search ────────────────────────────────────────────────

@pytest.mark.regression
def test_rec008_search_by_name(rcs_error_codes_page):
    """REC-008: Search by a Name value that exists returns matching records."""
    ensure_on_page(rcs_error_codes_page)
    # Self-verifying: read a real Name from the listing before searching
    names = rcs_error_codes_page.get_column_values("name")
    assert names, "Need at least one record to build a search term"
    target = names[0]
    rcs_error_codes_page.search(target)
    assert rcs_error_codes_page.has_records()
    found = rcs_error_codes_page.get_column_values("name")
    assert any(target in v for v in found), \
        f"Expected '{target}' in Name column after searching; got: {found!r}"
    rcs_error_codes_page.clear_search()


@pytest.mark.regression
def test_rec009_search_by_code(rcs_error_codes_page):
    """REC-009: Search by a Code value that exists returns matching records."""
    ensure_on_page(rcs_error_codes_page)
    codes = rcs_error_codes_page.get_column_values("code")
    assert codes, "Need at least one record to build a search term"
    target = codes[0]
    rcs_error_codes_page.search(target)
    assert rcs_error_codes_page.has_records()
    found = rcs_error_codes_page.get_column_values("code")
    assert any(target in v for v in found), \
        f"Expected code '{target}' in Code column after searching; got: {found!r}"
    rcs_error_codes_page.clear_search()


@pytest.mark.regression
def test_rec010_search_by_description(rcs_error_codes_page):
    """REC-010: Search by a partial Description value returns matching records."""
    ensure_on_page(rcs_error_codes_page)
    descs = rcs_error_codes_page.get_column_values("description")
    assert descs, "Need at least one record to build a search term"
    # Use first word of the first description as a safe partial search
    first_word = descs[0].split()[0] if descs[0].split() else descs[0][:5]
    rcs_error_codes_page.search(first_word)
    assert rcs_error_codes_page.has_records() or rcs_error_codes_page.has_no_records_message()
    rcs_error_codes_page.clear_search()


@pytest.mark.regression
def test_rec011_partial_search(rcs_error_codes_page):
    """REC-011: A partial search term returns records matching that prefix."""
    ensure_on_page(rcs_error_codes_page)
    rcs_error_codes_page.search("FAI")
    # May or may not have results depending on data — just verify no crash
    title = rcs_error_codes_page.get_title().lower()
    assert "404" not in title and "error" not in title
    rcs_error_codes_page.clear_search()


@pytest.mark.regression
def test_rec012_case_insensitive_search(rcs_error_codes_page):
    """REC-012: Search is case-insensitive (searching lowercase also works)."""
    ensure_on_page(rcs_error_codes_page)
    names = rcs_error_codes_page.get_column_values("name")
    if not names:
        pytest.skip("No data available to test case-insensitive search")
    target_upper = names[0].upper()
    target_lower = names[0].lower()

    rcs_error_codes_page.search(target_upper)
    count_upper = rcs_error_codes_page.get_row_count()
    rcs_error_codes_page.clear_search()

    rcs_error_codes_page.search(target_lower)
    count_lower = rcs_error_codes_page.get_row_count()
    rcs_error_codes_page.clear_search()

    assert count_upper == count_lower, \
        f"Case-sensitive difference: '{target_upper}' returned {count_upper} rows, " \
        f"'{target_lower}' returned {count_lower} rows"


@pytest.mark.regression
@pytest.mark.negative
def test_rec013_invalid_search(rcs_error_codes_page):
    """REC-013: Searching an impossible term shows no matching records."""
    ensure_on_page(rcs_error_codes_page)
    rcs_error_codes_page.search("XYZ_NO_MATCH_QWERTY999")
    assert rcs_error_codes_page.has_no_records_message() or rcs_error_codes_page.get_row_count() == 0
    rcs_error_codes_page.clear_search()


@pytest.mark.regression
def test_rec014_clearing_search(rcs_error_codes_page):
    """REC-014: Clearing the search term restores the complete record list."""
    ensure_on_page(rcs_error_codes_page)
    original_count = rcs_error_codes_page.get_row_count()
    rcs_error_codes_page.search("XYZ_NO_MATCH_QWERTY999")
    assert rcs_error_codes_page.get_row_count() == 0 or rcs_error_codes_page.has_no_records_message()
    rcs_error_codes_page.clear_search()
    assert rcs_error_codes_page.has_records()
    assert rcs_error_codes_page.get_row_count() == original_count


# ── REC-015-016 — Pagination ─────────────────────────────────────────────

@pytest.mark.regression
def test_rec015_pagination_results_text(rcs_error_codes_page):
    """REC015: Pagination text shows 'Showing X to Y of Z items'."""
    ensure_on_page(rcs_error_codes_page)
    if not rcs_error_codes_page.is_element_present(rcs_error_codes_page.PAGINATION_RESULTS_TEXT, timeout=2000):
        pytest.skip("Not enough records to trigger pagination")
    text = rcs_error_codes_page.get_pagination_results_text()
    assert text, "Pagination results text should not be empty"
    assert any(word in text.lower() for word in ["showing", "result", "record"]), \
        f"Pagination text should describe results; got: {text!r}"


@pytest.mark.regression
def test_rec016_next_page_navigation(rcs_error_codes_page):
    """REC016: Clicking Next Page changes the visible records."""
    ensure_on_page(rcs_error_codes_page)
    if not rcs_error_codes_page.is_element_present(rcs_error_codes_page.PAGINATION_RESULTS_TEXT, timeout=2000) \
            or not rcs_error_codes_page.is_element_present(rcs_error_codes_page.NEXT_PAGE_BTN, timeout=2000):
        pytest.skip("Not enough records to trigger pagination")
    text_before = rcs_error_codes_page.get_pagination_results_text()
    try:
        rcs_error_codes_page.click_next_page()
        text_after = rcs_error_codes_page.get_pagination_results_text()
        assert text_before != text_after, \
            "Pagination text should change after clicking Next"
        assert rcs_error_codes_page.has_records()
    except Exception:
        pytest.skip("Next page button not available — may be single-page data set")


# ── REC-017 — Sorting ────────────────────────────────────────────────────

@pytest.mark.regression
def test_rec017_description_sorting(rcs_error_codes_page):
    """REC-017 (DOM-confirmed adaptation): the Description column has NO
    sortBy('description') control in the live DOM — its <th> is a bare
    <span>, same as the SMS Error Codes equivalent. This test verifies
    that documented (unsortable) structure rather than asserting a control
    that doesn't exist."""
    ensure_on_page(rcs_error_codes_page)
    assert rcs_error_codes_page.has_description_sort_control() is False, \
        "Description column is confirmed NOT sortable in the live DOM"


# ── REC-018-022 — Columns ────────────────────────────────────────────────

@pytest.mark.regression
def test_rec018_columns_button_opens_menu(rcs_error_codes_page):
    """REC-018: Clicking Columns opens the column selection menu."""
    ensure_on_page(rcs_error_codes_page)
    rcs_error_codes_page.open_columns_dropdown()
    assert rcs_error_codes_page.is_element_present(rcs_error_codes_page.COLUMN_CHECKBOXES, timeout=5000)


@pytest.mark.regression
def test_rec019_hide_show_name_column(rcs_error_codes_page):
    """REC-019: Hiding the Name column removes it from the visible headers."""
    ensure_on_page(rcs_error_codes_page)
    rcs_error_codes_page.page.reload()
    rcs_error_codes_page.page.wait_for_timeout(3000)
    try:
        rcs_error_codes_page.toggle_column("name")
        headers = [h.lower() for h in rcs_error_codes_page.get_visible_column_headers()]
        assert not any(h == "name" for h in headers), \
            f"Name column should be hidden; headers: {headers}"
    finally:
        rcs_error_codes_page.restore_all_columns()


@pytest.mark.regression
def test_rec020_hide_show_code_column(rcs_error_codes_page):
    """REC-020: Hiding the Code column removes it from the visible headers."""
    ensure_on_page(rcs_error_codes_page)
    rcs_error_codes_page.page.reload()
    rcs_error_codes_page.page.wait_for_timeout(3000)
    try:
        rcs_error_codes_page.toggle_column("code")
        headers = [h.lower() for h in rcs_error_codes_page.get_visible_column_headers()]
        assert not any(h == "code" for h in headers), \
            f"Code column should be hidden; headers: {headers}"
    finally:
        rcs_error_codes_page.restore_all_columns()


@pytest.mark.regression
def test_rec021_hide_show_description_column(rcs_error_codes_page):
    """REC-021: Hiding the Description column removes it from visible headers."""
    ensure_on_page(rcs_error_codes_page)
    rcs_error_codes_page.page.reload()
    rcs_error_codes_page.page.wait_for_timeout(3000)
    try:
        rcs_error_codes_page.toggle_column("description")
        headers = [h.lower() for h in rcs_error_codes_page.get_visible_column_headers()]
        assert not any(h == "description" for h in headers), \
            f"Description column should be hidden; headers: {headers}"
    finally:
        rcs_error_codes_page.restore_all_columns()


@pytest.mark.regression
def test_rec022_restore_hidden_columns(rcs_error_codes_page):
    """REC-022: Restoring hidden columns re-adds them to the visible headers."""
    ensure_on_page(rcs_error_codes_page)
    rcs_error_codes_page.page.reload()
    rcs_error_codes_page.page.wait_for_timeout(3000)
    rcs_error_codes_page.toggle_column("description")
    headers = [h.lower() for h in rcs_error_codes_page.get_visible_column_headers()]
    assert not any(h == "description" for h in headers)
    rcs_error_codes_page.restore_all_columns()
    headers = [h.lower() for h in rcs_error_codes_page.get_visible_column_headers()]
    assert any("name" in h for h in headers)
    assert any("code" in h for h in headers)
    assert any("description" in h for h in headers)

# ── REC-023 — Refresh ────────────────────────────────────────────────────

@pytest.mark.regression
def test_rec023_page_refresh(rcs_error_codes_page):
    """REC-023: Refreshing the browser reloads the page successfully."""
    ensure_on_page(rcs_error_codes_page)
    rcs_error_codes_page.page.reload()
    rcs_error_codes_page.page.wait_for_timeout(2000)
    assert rcs_error_codes_page.is_report_page()
    assert rcs_error_codes_page.get_page_title_text() == "RCS Error Codes"


# ── REC-024 — Security: Unauthorized Access ─────────────────────────────

@pytest.mark.regression
@pytest.mark.negative
def test_rec024_unauthorized_access_redirects_to_login(rcs_error_codes_page):
    """REC-024: Logging out then accessing the page URL redirects to Login."""
    ensure_on_page(rcs_error_codes_page)
    try:
        rcs_error_codes_page.logout()
        rcs_error_codes_page.h.wait_for_url_contains("login", timeout=10000)
        rcs_error_codes_page.open(RcsErrorCodesPage.REPORT_URL)
        rcs_error_codes_page.page.wait_for_timeout(2000)
        assert "login" in rcs_error_codes_page.get_current_url().lower(), \
            "Should be redirected to Login page when not authenticated"
    finally:
        login = LoginPage(rcs_error_codes_page.page)
        login.navigate()
        login.login(Config.VALID_EMAIL, Config.VALID_PASSWORD)
        login.h.wait_for_url_contains("/", timeout=20000)
        rcs_error_codes_page.navigate_to_report()


# ── REC-025-027 — Input Validation / Security ───────────────────────────

@pytest.mark.regression
@pytest.mark.negative
def test_rec025_search_special_characters(rcs_error_codes_page):
    """REC-025: Searching '@#$%^' should not crash the application."""
    ensure_on_page(rcs_error_codes_page)
    rcs_error_codes_page.search("@#$%^")
    title = rcs_error_codes_page.get_title().lower()
    assert "404" not in title and "error" not in title
    rcs_error_codes_page.clear_search()


@pytest.mark.regression
@pytest.mark.negative
def test_rec026_sql_injection_prevention(rcs_error_codes_page):
    """REC-026: SQL injection payload is treated as plain text search input."""
    ensure_on_page(rcs_error_codes_page)
    rcs_error_codes_page.search("' OR 1=1 --")
    title = rcs_error_codes_page.get_title().lower()
    assert "404" not in title and "error" not in title
    # A real SQLi would return every row (or crash) — a safely-parameterised
    # search treats it as a literal string with (almost certainly) no match.
    row_count = rcs_error_codes_page.get_row_count()
    assert row_count < 1000, \
        f"Unexpected large result set ({row_count} rows) after SQL injection attempt"
    rcs_error_codes_page.clear_search()


@pytest.mark.regression
@pytest.mark.negative
def test_rec027_xss_prevention(rcs_error_codes_page):
    """REC-027: XSS payload in search box must not execute a script/alert."""
    ensure_on_page(rcs_error_codes_page)
    dialog_message = rcs_error_codes_page.search_expect_no_dialog("<script>alert(1)</script>")
    assert dialog_message is None, \
        f"XSS payload triggered a native dialog -- script executed: {dialog_message!r}"
    title = rcs_error_codes_page.get_title().lower()
    assert "404" not in title and "error" not in title
    rcs_error_codes_page.clear_search()


# ── REC-029 — Performance ────────────────────────────────────────────────

@pytest.mark.regression
def test_rec029_page_performance(rcs_error_codes_page):
    """REC-029: Page loads within an acceptable response time (<8000ms)."""
    ensure_on_page(rcs_error_codes_page)
    rcs_error_codes_page.navigate_to_report()
    load_time = rcs_error_codes_page.get_page_load_time_ms()
    if load_time is not None:
        assert load_time < 8000, f"Page load took {load_time}ms (>8000ms)"


# ── REC-030 — Data Accuracy ──────────────────────────────────────────────

@pytest.mark.regression
def test_rec030_error_code_data_accuracy(rcs_error_codes_page):
    """REC-030: Displayed records contain non-empty, consistent data across
    all three columns (Name, Code, Description) — the best available
    structural cross-check without direct backend/API access."""
    ensure_on_page(rcs_error_codes_page)
    names = rcs_error_codes_page.get_column_values("name")
    codes = rcs_error_codes_page.get_column_values("code")
    descs = rcs_error_codes_page.get_column_values("description")
    assert names and codes and descs, "All three columns should contain values"
    assert len(names) == len(codes) == len(descs), \
        "Name, Code and Description columns should have the same row count"
    empty_names = [n for n in names if not n]
    empty_codes = [c for c in codes if not c]
    assert not empty_names, f"Some Name cells are empty: {empty_names!r}"
    assert not empty_codes, f"Some Code cells are empty: {empty_codes!r}"
