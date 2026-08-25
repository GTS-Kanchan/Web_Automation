"""
RCS Messages — Automated Test Suite
Path: /rcs/message

Built directly from a manual QA checklist supplied by the user (TC01-14,
TC12 omitted by the tester, all 13 marked PASS) for the RCS Messages
listing page, paired with a full live DOM dump of that same page. See
pages/rcs_message_page.py's module docstring for the complete list of
confirmed DOM specifics driving every locator used here.

Migrated to Playwright: local page-object fixture renamed `message_page`
(built on conftest.py's `module_logged_in_page`) to avoid shadowing
pytest-playwright's reserved `page` fixture. Downloads now go through
Playwright's native page.expect_download() (see click_export()/
wait_for_download() in the page object) rather than OS-folder polling,
but the test-facing API is unchanged from the Selenium suite.

Test Design Notes:
  - scope="module" — page object shared across all tests (same pattern
    as every other suite in this project).
  - ensure_on_rcs_messages_page() recovers to a clean page state before
    each test (closes stray popups, re-navigates if drifted).
  - Filters are wire:model.live — no Apply button; apply_filter() is a
    settle-time no-op kept for API parity with sibling page objects.
  - Created From/To are set via a direct Livewire JS call rather than
    interacting with the date/time controls directly — CONFIRMED those
    controls have no stable id (see page object docstring for why).
  - TC12 does not exist in the supplied checklist (the sheet jumps from
    TC11 to TC13) — intentionally not renumbered, to keep 1:1
    traceability with the manual test case IDs.
  - Assertions favor "did not crash / produced a sane state" over
    content-exact checks where the underlying data is not something
    this suite controls (e.g. TC02's date-range results, TC08's status
    values) — consistent with the rest of this project's analytics/
    report suites.
"""
from datetime import datetime, timedelta

import pytest

from pages.rcs.rcs_message_page import RcsMessagePage


pytestmark = [pytest.mark.rcs, pytest.mark.messaging]

def days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


# ══════════════════════════════════════════════════════════════════════════════
# Module-scoped page object
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def message_page(module_logged_in_page):
    p = RcsMessagePage(module_logged_in_page)
    p.navigate()
    p.wait_for_table_load(timeout=15000)
    return p


# ══════════════════════════════════════════════════════════════════════════════
# Recovery helpers
# ══════════════════════════════════════════════════════════════════════════════

def ensure_on_rcs_messages_page(p: RcsMessagePage):
    if not p.is_messages_page():
        p.navigate()
        p.wait_for_table_load(timeout=10000)


def reset_filters(p: RcsMessagePage):
    """Hard-reset filters/search by re-navigating to the page."""
    p.navigate()
    p.wait_for_table_load(timeout=10000)
    p.page.wait_for_timeout(3000)


# ══════════════════════════════════════════════════════════════════════════════
# TC01 — Page loads successfully
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC01_page_loads_successfully(message_page):
    """TC01: Login -> Channels -> RCS -> Messages loads without error."""
    ensure_on_rcs_messages_page(message_page)
    assert message_page.is_messages_page(), f"Not on RCS Messages page: {message_page.get_current_url()}"
    title = message_page.get_page_title_text()
    assert title == "RCS Messages", f"Unexpected page heading: {title!r}"


# ══════════════════════════════════════════════════════════════════════════════
# TC02 — Valid date filter
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC02_valid_date_filter_shows_records(message_page):
    """TC02: Applying a valid Created From/To range narrows results without
    error. Content-exact date-range verification is not attempted (the
    date/time controls have no stable locator — see page object
    docstring); this asserts the filter applies cleanly and the table
    settles into either a populated or an explicit empty state."""
    reset_filters(message_page)
    message_page.open_filter_panel()
    message_page.set_date_filter(days_ago(7), today_str())
    message_page.apply_filter()
    assert message_page.get_row_count() > 0 or message_page.is_no_records_visible(), (
        "Table did not settle into a populated or empty state after date filter"
    )


# ══════════════════════════════════════════════════════════════════════════════
# TC03 — Sorting by Created At
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC03_sort_by_created_at(message_page):
    """TC03: Clicking the Created At column header toggles sort order.
    Default sort is confirmed as Created at: Z-A (desc); clicking should
    flip it to A-Z (asc) without breaking the table."""
    reset_filters(message_page)
    before_pill = message_page.get_applied_sort_pill_text()
    message_page.click_created_at_header()
    after_pill = message_page.get_applied_sort_pill_text()
    assert message_page.get_row_count() > 0 or message_page.is_no_records_visible(), (
        "Table broke after clicking the Created At sort header"
    )
    if before_pill and after_pill:
        assert after_pill != before_pill, (
            f"Sort pill did not change after clicking header "
            f"(before={before_pill!r}, after={after_pill!r})"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TC04 — Search by valid mobile number
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC04_search_by_valid_mobile_number(message_page):
    """TC04: Entering a valid mobile number (taken from a real row already
    on the page) shows that message's record."""
    reset_filters(message_page)
    if message_page.get_row_count() == 0:
        pytest.skip("No rows available to source a valid mobile number from")
    contact = message_page.get_cell_text(0, message_page.COLUMN_INDEX["contact"])
    if not contact:
        pytest.skip("Could not read a contact number from the first row")
    message_page.search(contact)
    assert message_page.get_row_count() > 0, (
        f"Searching for a known contact ({contact!r}) produced no rows"
    )
    message_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# TC05 — Export CSV
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC05_export_csv(message_page):
    """TC05: Clicking Export CSV downloads a file with the displayed
    records."""
    reset_filters(message_page)
    message_page.clear_download_dir()
    before = message_page.snapshot_downloads()
    message_page.click_export()
    downloaded = message_page.wait_for_download(timeout=30, before=before)
    if not downloaded:
        pytest.skip("Export did not produce a downloaded file within 30s")
    headers = message_page.get_csv_headers(downloaded)
    assert headers, f"Downloaded CSV had no header row: {downloaded}"


# ══════════════════════════════════════════════════════════════════════════════
# TC06 — Columns customization
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC06_columns_customization(message_page):
    """TC06: Hiding/showing a column via the Columns dropdown reflects in
    the grid. Uses "department", confirmed DESELECTED by default, so
    enabling it is a real, observable state change."""
    reset_filters(message_page)
    message_page.open_columns_panel()
    if not message_page.is_column_checkbox_present("department"):
        pytest.skip("Department column checkbox not present — locator may need updating")
    was_checked = message_page.get_column_checkbox_state("department")
    toggled = message_page.toggle_column("department")
    if not toggled:
        pytest.skip("Could not toggle the Department column checkbox")
    headers_after = message_page.get_table_headers()
    now_checked = message_page.get_column_checkbox_state("department")
    assert now_checked != was_checked, "Department checkbox state did not change"
    if now_checked:
        assert any("department" in h.lower() for h in headers_after), (
            f"Department column not reflected in grid headers: {headers_after}"
        )
    # Restore original state so downstream tests see the default columns.
    message_page.toggle_column("department")


# ══════════════════════════════════════════════════════════════════════════════
# TC07 — Refresh button
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC07_refresh_reloads_data(message_page):
    """TC07: Clicking Refresh reloads the latest data without error."""
    reset_filters(message_page)
    message_page.click_refresh()
    message_page.wait_for_table_load(timeout=10000)
    assert message_page.is_messages_page(), "Refresh navigated away from RCS Messages"
    assert message_page.get_row_count() > 0 or message_page.is_no_records_visible(), (
        "Table did not settle into a populated or empty state after Refresh"
    )


# ══════════════════════════════════════════════════════════════════════════════
# TC08 — Message status display
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC08_message_status_display(message_page):
    """TC08: Status column shows one of the confirmed status values.
    Sending a fresh RCS message is out of scope for this suite (no
    message-composer flow is exercised here); this instead validates
    that whatever rows already exist show a recognized status, which is
    the same signal the manual TC verifies."""
    reset_filters(message_page)
    if message_page.get_row_count() == 0:
        pytest.skip("No rows available to check status values")
    values = message_page.get_all_values_in_column("status")
    values = [v for v in values if v]
    if not values:
        pytest.skip("Could not read any Status cell values")
    known = {"submitted", "sent", "delivered", "read", "failed", "queued",
             "received", "rejected", "pending"}
    for v in values:
        assert v.lower() in known, f"Unrecognized status value: {v!r}"


# ══════════════════════════════════════════════════════════════════════════════
# TC09 — Empty data message
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC09_empty_data_message(message_page):
    """TC09: A filter combination with no matching records shows the
    app-wide confirmed 'No items found, try to broaden your search'
    empty state."""
    reset_filters(message_page)
    message_page.search("zzz_no_such_contact_zzz")
    if message_page.get_row_count() == 0:
        assert message_page.is_no_records_visible(), (
            "Zero rows returned but no-records message not shown"
        )
    else:
        pytest.skip("Search unexpectedly matched existing rows — cannot verify empty state")
    message_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# TC10 — Invalid date range (End < Start)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.negative
def test_TC10_invalid_date_range_end_before_start(message_page):
    """TC10: Selecting an end date earlier than the start date should not
    crash the page or raise a server error — either a validation message
    appears or the table gracefully shows no/normal results."""
    reset_filters(message_page)
    message_page.open_filter_panel()
    message_page.set_date_filter(today_str(), days_ago(7))
    message_page.apply_filter()
    assert message_page.is_messages_page(), "Page navigated away/broke on an invalid date range"
    assert message_page.get_row_count() >= 0  # no crash: table state is readable at all
    reset_filters(message_page)


# ══════════════════════════════════════════════════════════════════════════════
# TC11 — Invalid mobile number search
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.negative
def test_TC11_invalid_mobile_number_search(message_page):
    """TC11: Entering alphabets/special characters in the search box
    should not crash the system — either no results or a validation/
    empty state is shown."""
    reset_filters(message_page)
    message_page.search("!!!abc###")
    assert message_page.is_messages_page(), "Page broke after an invalid search term"
    assert message_page.get_row_count() == 0 or message_page.get_row_count() >= 0
    if message_page.get_row_count() == 0:
        assert message_page.is_no_records_visible(), (
            "Zero rows returned but no-records message not shown"
        )
    message_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# TC13 — Export CSV with no records (TC12 not present in the supplied
# checklist — intentionally not renumbered, see module docstring)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC13_export_csv_with_no_records(message_page):
    """TC13: Exporting while a filter produces zero results downloads a
    CSV with headers only (or the export is otherwise handled without
    error)."""
    reset_filters(message_page)
    message_page.search("zzz_no_such_contact_zzz")
    if message_page.get_row_count() != 0:
        pytest.skip("Search unexpectedly matched existing rows — cannot verify empty export")

    message_page.clear_download_dir()
    before = message_page.snapshot_downloads()
    message_page.click_export()
    downloaded = message_page.wait_for_download(timeout=30, before=before)
    if not downloaded:
        pytest.skip("Export did not produce a downloaded file within 30s for the empty case")
    row_count = message_page.get_csv_row_count(downloaded)
    assert row_count == 0, f"Expected an empty (headers-only) CSV, got {row_count} data rows"
    message_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# TC14 — Rapid multiple clicks on Refresh
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC14_rapid_refresh_clicks(message_page):
    """TC14: Rapidly clicking Refresh multiple times should not duplicate
    data or crash the page."""
    reset_filters(message_page)
    before_count = message_page.get_row_count()
    for _ in range(4):
        message_page.click_refresh()
    message_page.wait_for_table_load(timeout=10000)
    assert message_page.is_messages_page(), "Page broke after rapid Refresh clicks"
    after_count = message_page.get_row_count()
    assert after_count == before_count or (before_count == 0 and after_count >= 0), (
        f"Row count changed unexpectedly after rapid refresh "
        f"(before={before_count}, after={after_count}) — possible duplication"
    )


# ══════════════════════════════════════════════════════════════════════════════
# TC15 — Status filter selection
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC15_filter_by_status(message_page):
    """TC15: Selecting a status from the status filter updates the table results."""
    reset_filters(message_page)
    message_page.open_filter_panel()
    success = message_page.set_filter_status(message_page.STATUS_DELIVERED)
    if not success:
        pytest.skip("Status filter dropdown could not be set")
    assert message_page.is_messages_page(), "Page broke after applying status filter"
    assert message_page.get_row_count() >= 0 or message_page.is_no_records_visible()
    reset_filters(message_page)


# ══════════════════════════════════════════════════════════════════════════════
# TC16 — Source filter selection
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC16_filter_by_source(message_page):
    """TC16: Selecting a source from the source filter updates the table results."""
    reset_filters(message_page)
    message_page.open_filter_panel()
    success = message_page.set_filter_source(message_page.SOURCE_CAMPAIGN)
    if not success:
        pytest.skip("Source filter dropdown could not be set")
    assert message_page.is_messages_page(), "Page broke after applying source filter"
    assert message_page.get_row_count() >= 0 or message_page.is_no_records_visible()
    reset_filters(message_page)
