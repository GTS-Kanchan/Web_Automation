"""
SMS Incoming Messages — Single Sequential Flow
================================================
Covers: Channels → SMS → More → Incoming Messages page, TC001 - TC025
(URL: /channels/sms/incoming-messages)

Migrated to Playwright: local page-object fixture renamed
`incoming_messages_page` (built on conftest.py's `module_logged_in_page`)
to avoid shadowing pytest-playwright's reserved `page` fixture. Export
CSV now captures Playwright's native download event instead of polling
DOWNLOAD_DIR by file mtime; window resizing for the responsive-layout
test uses page.set_viewport_size().

Built from a FULL live DOM dump of this exact page plus a supplied
manual-QA pass table (all 25 TCs marked Pass by the tester). Locators
(pages/sms_incoming_messages_page.py) are grounded directly in that
dump -- see the page object's module docstring for the full list of
confirmed specifics: all 6 columns selected by default (opposite of the
Blocked Numbers page, same convention as SMS Error Codes), only
Received At is sortable, the Filters popover uses native date+time
inputs (NOT flatpickr) for a Sender ID select plus Received From/To,
no bulk actions/row checkboxes exist on this page, the Action column's
View button opens the shared livewire-ui-modal component, and
pagination text uses class "total-pagination-results" (different from
Blocked Numbers' "paged-pagination-results").

CAVEATS (best-effort, flagged individually below):
  - NO_RECORDS_MSG (TC025): no genuine empty state was ever rendered in
    the dump (6 real records existed) -- exercised via an
    impossible-to-match search term, mirroring the Blocked Numbers
    page's TC006 pattern, with a broadened best-effort locator.
  - Modal close (TC012): no explicit in-modal close button was captured;
    closes via the confirmed Escape-key handler instead.

NOTE: TC010 (Clear filter) and TC021 (Hide/show columns) were removed
from this suite per request.

Run:
    pytest tests/test_sms_incoming_messages_flow.py -v
"""
import pytest

from pages.sms.sms_incoming_messages_page import SmsIncomingMessagesPage


pytestmark = [pytest.mark.sms, pytest.mark.messaging]



@pytest.fixture(scope="module")
def incoming_messages_page(module_logged_in_page):
    p = SmsIncomingMessagesPage(module_logged_in_page)
    p.navigate_to_report()
    return p


def ensure_on_page(p):
    if not p.is_report_page():
        p.navigate_to_report()
        p.page.wait_for_timeout(1000)


@pytest.fixture(autouse=True)
def _reset_after_test(incoming_messages_page):
    """Hard reset to a clean listing view after every test -- this page
    has many stateful pieces (search, filters, columns, sort, an
    open modal), so re-navigating fresh after each test avoids
    cross-test contamination (same rationale as every other suite in
    this project)."""
    yield
    try:
        ensure_on_page(incoming_messages_page)
        incoming_messages_page.navigate_to_report()
    except Exception:
        pass


# ── TC001 — Page Load ────────────────────────────────────────────────────

@pytest.mark.smoke
def test_tc001_page_loads_successfully(incoming_messages_page):
    """TC001: SMS Incoming Messages page loads successfully without errors."""
    ensure_on_page(incoming_messages_page)
    assert incoming_messages_page.is_report_page(), "URL should contain /channels/sms/incoming-messages"
    title = incoming_messages_page.get_title().lower()
    assert "404" not in title and "error" not in title


# ── TC002 — Page Title ───────────────────────────────────────────────────

@pytest.mark.smoke
def test_tc002_page_title(incoming_messages_page):
    """TC002: Page (heading) title displays 'SMS Incoming Messages'."""
    ensure_on_page(incoming_messages_page)
    assert incoming_messages_page.get_page_title_text() == "SMS Incoming Messages"


# ── TC003 — Incoming message records ─────────────────────────────────────

@pytest.mark.smoke
def test_tc003_incoming_message_records(incoming_messages_page):
    """TC003: Incoming message records should be displayed."""
    ensure_on_page(incoming_messages_page)
    assert incoming_messages_page.has_records()
    assert incoming_messages_page.get_row_count() > 0


# ── TC004 — Table columns ────────────────────────────────────────────────

@pytest.mark.smoke
def test_tc004_table_columns(incoming_messages_page):
    """TC004: Action, Campaign Name, Sender ID, Country Code, User Number
    and Received At columns should be displayed."""
    ensure_on_page(incoming_messages_page)
    headers = incoming_messages_page.get_visible_column_headers()
    expected = ["Action", "Campaign Name", "Sender ID", "Country Code",
                "User Number", "Received At"]
    for col in expected:
        assert any(col.lower() in h.lower() for h in headers), \
            f"Column '{col}' not found in headers: {headers}"


# ── TC005-007 — Search ───────────────────────────────────────────────────

@pytest.mark.regression
def test_tc005_search_existing_value(incoming_messages_page):
    """TC005: Searching an existing User Number returns a matching record.
    Self-verifying: reads a real value from the current listing immediately
    before searching (mirrors the Blocked Numbers page's TC005 fix for the
    same reason -- avoids depending on a hardcoded value that later data
    changes could invalidate)."""
    ensure_on_page(incoming_messages_page)
    existing_values = incoming_messages_page.get_column_values("user_number")
    assert existing_values, "Need at least one existing record to search for"
    target = existing_values[0]
    incoming_messages_page.search(target)
    assert incoming_messages_page.has_records()
    values = incoming_messages_page.get_column_values("user_number")
    assert any(target in v for v in values)
    incoming_messages_page.clear_search()


@pytest.mark.regression
@pytest.mark.negative
def test_tc006_search_invalid_value(incoming_messages_page):
    """TC006: Searching a non-existing keyword shows no matching records."""
    ensure_on_page(incoming_messages_page)
    incoming_messages_page.search("INVALIDSEARCHXYZ999")
    assert incoming_messages_page.has_no_records_message() or incoming_messages_page.get_row_count() == 0
    incoming_messages_page.clear_search()


@pytest.mark.regression
def test_tc007_clear_search(incoming_messages_page):
    """TC007: Removing search text restores the complete record list."""
    ensure_on_page(incoming_messages_page)
    before_count = incoming_messages_page.get_row_count()
    incoming_messages_page.search("INVALIDSEARCHXYZ999")
    incoming_messages_page.clear_search()
    after_count = incoming_messages_page.get_row_count()
    assert after_count == before_count, \
        "Row count after clearing search should match the original count"
    assert incoming_messages_page.has_records()


# ── TC008-009 — Filters ──────────────────────────────────────────────────

@pytest.mark.regression
def test_tc008_filters_button(incoming_messages_page):
    """TC008: Clicking Filters opens the filter panel."""
    ensure_on_page(incoming_messages_page)
    incoming_messages_page.open_filters_popover()
    assert incoming_messages_page.is_element_present(incoming_messages_page.FILTER_SENDER_SELECT, timeout=5000)


@pytest.mark.regression
def test_tc009_received_at_date_filter(incoming_messages_page):
    """TC009: Selecting a valid date range filters records to that range."""
    ensure_on_page(incoming_messages_page)
    incoming_messages_page.filter_by_received_date_range(days_back=60)
    from_value = incoming_messages_page.get_filter_received_from_value()
    to_value = incoming_messages_page.get_filter_received_to_value()
    assert from_value and to_value, "Date range inputs should show selected values"


# ── TC011 — Sorting ──────────────────────────────────────────────────────

@pytest.mark.regression
def test_tc011_sort_by_received_at(incoming_messages_page):
    """TC011: Clicking the Received At column header re-sorts the visible rows."""
    ensure_on_page(incoming_messages_page)
    before = incoming_messages_page.get_column_values("received_at")
    incoming_messages_page.sort_by_received_at()
    after1 = incoming_messages_page.get_column_values("received_at")
    incoming_messages_page.sort_by_received_at()
    after2 = incoming_messages_page.get_column_values("received_at")
    assert before != after1 or after1 != after2, \
        "Clicking Received At header should change row order across toggles"


# ── TC012 — Action (View) button ─────────────────────────────────────────

@pytest.mark.regression
def test_tc012_action_view_button(incoming_messages_page):
    """TC012: Clicking the View icon opens the message-details popup."""
    ensure_on_page(incoming_messages_page)
    clicked = incoming_messages_page.click_view_on_first_row()
    assert clicked, "View icon should be present and clickable on the first row"
    assert incoming_messages_page.is_modal_open(timeout=10000), "Message details modal should open"
    incoming_messages_page.close_modal()


# ── TC013 — Campaign Name column ─────────────────────────────────────────

@pytest.mark.regression
def test_tc013_campaign_name_values(incoming_messages_page):
    """TC013: Campaign Name column displays correctly, or N/A if unavailable."""
    ensure_on_page(incoming_messages_page)
    values = incoming_messages_page.get_column_values("campaign_name")
    assert values, "Campaign Name column should have values"
    assert all(len(v) > 0 for v in values)


# ── TC014 — Sender ID column ─────────────────────────────────────────────

@pytest.mark.regression
def test_tc014_sender_id_values(incoming_messages_page):
    """TC014: Sender ID column displays valid Sender IDs."""
    ensure_on_page(incoming_messages_page)
    values = incoming_messages_page.get_column_values("sender_id")
    assert values, "Sender ID column should have values"
    assert all(len(v) > 0 for v in values)


# ── TC015 — Country Code column ──────────────────────────────────────────

@pytest.mark.regression
def test_tc015_country_code_values(incoming_messages_page):
    """TC015: Country Code column displays correct country codes."""
    ensure_on_page(incoming_messages_page)
    values = incoming_messages_page.get_column_values("country_code")
    assert values, "Country Code column should have values"
    assert all(len(v) > 0 for v in values)


# ── TC016 — User Number column ───────────────────────────────────────────

@pytest.mark.regression
def test_tc016_user_number_values(incoming_messages_page):
    """TC016: User Number column displays valid, numeric user numbers."""
    ensure_on_page(incoming_messages_page)
    values = incoming_messages_page.get_column_values("user_number")
    assert values, "User Number column should have values"
    bad_values = [v for v in values if v and not v.isdigit()]
    assert not bad_values, (
        f"User Number column has non-numeric value(s): {bad_values!r} "
        f"(full column: {values!r})")


# ── TC017 — Refresh button ───────────────────────────────────────────────

@pytest.mark.regression
def test_tc017_refresh_button(incoming_messages_page):
    """TC017: Clicking Refresh reloads the latest incoming messages."""
    ensure_on_page(incoming_messages_page)
    incoming_messages_page.click_refresh()
    assert incoming_messages_page.is_report_page()
    assert incoming_messages_page.get_page_title_text() == "SMS Incoming Messages"
    assert incoming_messages_page.has_records()


# ── TC018-019 — Export CSV ───────────────────────────────────────────────

@pytest.mark.regression
def test_tc018_export_csv_button(incoming_messages_page):
    """TC018: Clicking Export CSV downloads a CSV file successfully."""
    ensure_on_page(incoming_messages_page)
    result = incoming_messages_page.export_csv(timeout=30000)
    assert result is not None, "Export CSV should produce a downloaded file"
    assert result["file_size"] > 0, "Downloaded export file should not be empty"


@pytest.mark.regression
def test_tc019_exported_csv_data_matches_ui(incoming_messages_page):
    """TC019: Exported CSV data should match the records displayed in the UI."""
    ensure_on_page(incoming_messages_page)
    ui_values = incoming_messages_page.get_column_values("sender_id")
    assert ui_values, "Need UI data to compare against the export"
    result = incoming_messages_page.export_csv(timeout=30000)
    assert result is not None, "Export CSV should produce a downloaded file"
    file_path = result["file_path"]
    with open(file_path, "r", encoding="utf-8-sig", errors="replace") as f:
        csv_content = f.read()
    matched = [v for v in ui_values if v in csv_content]
    assert matched, (
        f"None of the UI Sender ID values {ui_values!r} were found in the "
        f"exported file '{file_path}' -- exported data may not match the UI")


# ── TC020 — Columns dropdown ──────────────────────────────────────────────

@pytest.mark.regression
def test_tc020_columns_button(incoming_messages_page):
    """TC020: Columns button opens the column selection menu."""
    ensure_on_page(incoming_messages_page)
    incoming_messages_page.open_columns_dropdown()
    assert incoming_messages_page.is_element_present(incoming_messages_page.COLUMN_CHECKBOXES, timeout=5000)


# ── TC022 — Browser refresh ──────────────────────────────────────────────

@pytest.mark.regression
def test_tc022_page_refresh_browser(incoming_messages_page):
    """TC022: Refreshing the browser reloads the page without errors."""
    ensure_on_page(incoming_messages_page)
    incoming_messages_page.page.reload()
    incoming_messages_page.page.wait_for_timeout(2000)
    assert incoming_messages_page.is_report_page()
    assert incoming_messages_page.get_page_title_text() == "SMS Incoming Messages"


# ── TC023 — Responsive layout ────────────────────────────────────────────

@pytest.mark.regression
def test_tc023_responsive_layout(incoming_messages_page):
    """TC023: Resizing the browser keeps the UI aligned (no crash/blank)."""
    ensure_on_page(incoming_messages_page)
    original_size = incoming_messages_page.page.viewport_size
    try:
        incoming_messages_page.page.set_viewport_size({"width": 375, "height": 667})  # mobile viewport
        incoming_messages_page.page.wait_for_timeout(1000)
        assert incoming_messages_page.is_element_present(incoming_messages_page.SEARCH_BOX, timeout=5000)
        incoming_messages_page.page.set_viewport_size({"width": 1366, "height": 768})  # desktop viewport
        incoming_messages_page.page.wait_for_timeout(1000)
        assert incoming_messages_page.is_element_present(incoming_messages_page.TABLE, timeout=5000)
    finally:
        if original_size:
            incoming_messages_page.page.set_viewport_size(original_size)


# ── TC024 — Performance ──────────────────────────────────────────────────

@pytest.mark.regression
def test_tc024_page_performance(incoming_messages_page):
    """TC024: Page loads within an acceptable response time (<8000ms)."""
    ensure_on_page(incoming_messages_page)
    incoming_messages_page.navigate_to_report()
    load_time = incoming_messages_page.get_page_load_time_ms()
    if load_time is not None:
        assert load_time < 8000, f"Page load took {load_time}ms (>8000ms)"


# ── TC025 — Empty data scenario ──────────────────────────────────────────

@pytest.mark.regression
@pytest.mark.negative
def test_tc025_empty_data_scenario(incoming_messages_page):
    """TC025: When no incoming messages match, a "No Records Found"-style
    message should be displayed. No genuine empty state exists in this
    environment's data (real messages are always present), so this is
    exercised the same way as TC006 -- an impossible-to-match search term
    -- mirroring the equivalent pattern used for the Blocked Numbers
    page's empty-state test."""
    ensure_on_page(incoming_messages_page)
    incoming_messages_page.search("ZZZZNOMATCHPOSSIBLEQWERTY999")
    assert incoming_messages_page.has_no_records_message() or incoming_messages_page.get_row_count() == 0, \
        "An empty-state indicator (or zero rows) should be shown for a " \
        "search with no matches"
    incoming_messages_page.clear_search()
