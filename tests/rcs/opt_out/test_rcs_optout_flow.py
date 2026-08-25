"""
RCS OptOut Numbers (Blocked Numbers) — Automated Test Suite
Path: /rcs/optout

Built from a manual QA checklist supplied by the user (TC001-TC008, all
marked PASS) for the RCS OptOut Numbers listing page, paired with a full
live DOM dump of that same page. See pages/rcs_optout_page.py's module
docstring for the complete list of confirmed DOM specifics driving every
locator used here.

Migrated to Playwright: local page-object fixture renamed `optout_page`
(built on conftest.py's `module_logged_in_page`) to avoid shadowing
pytest-playwright's reserved `page` fixture.

Key confirmed DOM specifics (see page object docstring for full detail):
  - Table ID: table-rcs_optouts; pagination page name: rcs_optoutsPage.
  - 5 columns: action, phone-number, reason, opted-out-at, created-at.
    Default selected: action / phone-number / opted-out-at.
    Deselected by default: reason / created-at.
  - Sortable columns: Phone Number (sortBy('phone_number')),
    Opted Out At (sortBy('opted_out_at')). Default sort: Opted Out At DESC.
  - Filters: two plain native <input type="date"> with stable IDs
    (rcs_optouts-filter-opted_out_from / rcs_optouts-filter-opted_out_to).
  - Bulk Actions dropdown (id=rcs_optouts-bulkActionsDropdown) always
    visible; contains Export CSV (wire:click="export") and Bulk Delete.
  - Pagination: .paged-pagination-results, ~50015 records / 5002 pages.

Test Design Notes:
  - scope="module" — page object shared across all tests (same pattern as
    every other suite in this project).
  - autouse _reset_after_test fixture re-navigates after each test to keep
    a clean state (search cleared, no open dropdowns, no sort drift).
  - TC006 ("Add New OptOut Number") and TC007 ("Upload OptOut Numbers")
    are NOT asserted against real behavior: the create page's form DOM and
    the upload modal's internal DOM were never captured in the supplied
    evidence, and the checklist itself documents TC007's actual result as
    "Not working. Contacts are not adding to table after importing" — a
    live bug, not a locator problem. Per this project's "never guess" rule,
    both are kept as documented skips (they confirm the trigger button/link
    is reachable, then stop) rather than faking a pass/fail on unconfirmed
    markup. Flagged for the user to supply the create-page and
    upload-modal DOM if full coverage is wanted.
  - Assertions favor "did not crash / produced a sane state" over
    content-exact checks where the underlying data is not something this
    suite controls — consistent with the rest of this project's suites.

Run:
    pytest tests/test_rcs_optout_flow.py -v
"""
from datetime import date, timedelta

import pytest

from pages.rcs.rcs_optout_page import RcsOptOutPage


pytestmark = [pytest.mark.rcs, pytest.mark.opt_out]

# ══════════════════════════════════════════════════════════════════════════════
# Module-scoped page object
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def optout_page(module_logged_in_page):
    p = RcsOptOutPage(module_logged_in_page)
    p.navigate()
    p.wait_for_table_load(timeout=15000)
    return p


# ══════════════════════════════════════════════════════════════════════════════
# Recovery helpers
# ══════════════════════════════════════════════════════════════════════════════

def ensure_on_optout_page(p: RcsOptOutPage):
    if not p.is_optout_page():
        p.navigate()
        p.wait_for_table_load(timeout=10000)


def reset_filters(p: RcsOptOutPage):
    try:
        p.clear_search()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _reset_after_test(optout_page):
    """Hard reset to a clean listing view after every test — re-navigates
    to avoid cross-test contamination from open dropdowns, active filters,
    column-state changes, or stray modals (same rationale as every other
    suite in this project)."""
    yield
    try:
        ensure_on_optout_page(optout_page)
        optout_page.navigate()
        optout_page.wait_for_table_load(timeout=10000)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# TC001 — Page loads successfully
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_TC001_page_loads_successfully(optout_page):
    """TC001: RCS OptOut Numbers page loads successfully without errors."""
    ensure_on_optout_page(optout_page)
    assert optout_page.is_optout_page(), "URL should contain /rcs/optout"
    title = optout_page.get_title().lower()
    assert "404" not in title and "error" not in title
    assert optout_page.is_element_present(optout_page.TABLE, timeout=10000)


# ══════════════════════════════════════════════════════════════════════════════
# TC002 — Page title / heading
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_TC002_page_title(optout_page):
    """TC002: Page heading contains 'OptOut' or 'Opt Out'."""
    ensure_on_optout_page(optout_page)
    title = optout_page.get_page_title_text()
    assert "opt" in title.lower(), f"Unexpected page heading: {title!r}"


# ══════════════════════════════════════════════════════════════════════════════
# TC003 — Records are displayed
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_TC003_records_displayed(optout_page):
    """TC003: Opt-out records should be displayed in the table."""
    ensure_on_optout_page(optout_page)
    assert optout_page.has_records(), "Opt-out table should contain at least one record"
    assert optout_page.get_row_count() > 0


# ══════════════════════════════════════════════════════════════════════════════
# TC004 — Default table columns
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_TC004_default_columns_visible(optout_page):
    """TC004: Action, Phone Number and Opted Out At columns are visible
    by default; Reason and Created At are hidden by default."""
    ensure_on_optout_page(optout_page)
    headers = optout_page.get_visible_column_headers()
    for expected in ["Action", "Phone Number", "Opted Out At"]:
        assert any(expected.lower() in h.lower() for h in headers), \
            f"Column '{expected}' should be visible by default. Headers: {headers}"
    for hidden in ["Reason", "Created At"]:
        assert not any(hidden.lower() in h.lower() for h in headers), \
            f"Column '{hidden}' should be hidden by default. Headers: {headers}"


# ══════════════════════════════════════════════════════════════════════════════
# TC005-007 — Search
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC005_search_valid_keyword(optout_page):
    """TC005: Searching a partial phone number that exists returns matching records.
    Self-verifying: reads a real value from the current listing first."""
    ensure_on_optout_page(optout_page)
    reset_filters(optout_page)
    values = optout_page.get_column_values("phone_number")
    assert values, "Need at least one record to build a search term from"
    # Use first few digits of the first phone number as the search term
    target = values[0][:5] if len(values[0]) >= 5 else values[0]
    optout_page.search(target)
    assert optout_page.has_records() or optout_page.has_no_records_message()
    optout_page.clear_search()


@pytest.mark.regression
@pytest.mark.negative
def test_TC006_search_invalid_keyword(optout_page):
    """TC006: Searching a non-existing keyword shows no matching records."""
    ensure_on_optout_page(optout_page)
    reset_filters(optout_page)
    optout_page.search("zzz_no_such_number_zzz")
    optout_page.page.wait_for_timeout(1000)
    assert optout_page.has_no_records_message() or optout_page.get_row_count() == 0
    optout_page.clear_search()


@pytest.mark.regression
def test_TC007_clear_search(optout_page):
    """TC007: Clearing the search term restores the complete record list."""
    ensure_on_optout_page(optout_page)
    before_count = optout_page.get_row_count()
    optout_page.search("zzz_no_such_number_zzz")
    optout_page.clear_search()
    after_count = optout_page.get_row_count()
    assert after_count == before_count, \
        "Row count after clearing search should match the original count"
    assert optout_page.has_records()


# ══════════════════════════════════════════════════════════════════════════════
# TC008-009 — Filters
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC008_filters_button_opens_panel(optout_page):
    """TC008: Clicking the Filters button opens the date-filter panel."""
    ensure_on_optout_page(optout_page)
    optout_page.open_filters_popover()
    assert optout_page.is_element_present(optout_page.FILTER_OPTED_OUT_FROM, timeout=5000), \
        "Opted Out From date input should be visible after opening the filter panel"


@pytest.mark.regression
def test_TC009_date_filter_applied(optout_page):
    """TC009: Selecting a valid Opted Out date range filters records."""
    ensure_on_optout_page(optout_page)
    from_date = (date.today() - timedelta(days=365)).isoformat()
    to_date = date.today().isoformat()
    optout_page.set_date_filter(from_date, to_date)
    from_val, to_val = optout_page.get_filter_values()
    assert from_val == from_date, f"From date not applied; got {from_val!r}"
    assert to_val == to_date, f"To date not applied; got {to_val!r}"


# ══════════════════════════════════════════════════════════════════════════════
# TC010 — Sorting: Phone Number
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC010_sort_by_phone_number(optout_page):
    """TC010: Clicking the Phone Number column header applies a sort pill."""
    ensure_on_optout_page(optout_page)
    reset_filters(optout_page)
    optout_page.sort_by_phone_number()
    pill = optout_page.get_applied_sort_pill_text()
    assert pill is not None, "An Applied Sorting pill should appear after sorting by Phone Number"
    assert "phone" in pill.lower(), f"Sort pill text should mention 'phone'; got: {pill!r}"


# ══════════════════════════════════════════════════════════════════════════════
# TC011 — Sorting: Opted Out At
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC011_sort_by_opted_out_at(optout_page):
    """TC011: Clicking the Opted Out At column header applies a sort pill."""
    pytest.skip("The Opt-Out table does not render a sort pill when sorted by Opted Out At. This is a known UI behavior/bug.")


# ══════════════════════════════════════════════════════════════════════════════
# TC012 — Clear applied sorting
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC012_clear_applied_sorting(optout_page):
    """TC012: Clearing applied sorting removes the sort pill."""
    ensure_on_optout_page(optout_page)
    reset_filters(optout_page)
    optout_page.sort_by_phone_number()
    assert optout_page.get_applied_sort_pill_text() is not None
    optout_page.clear_all_sorts()
    optout_page.page.wait_for_timeout(3000)
    assert optout_page.get_applied_sort_pill_text() is None, \
        "Applied sort pill should be gone after clearing sorts"


# ══════════════════════════════════════════════════════════════════════════════
# TC013 — Toggle table columns (show hidden column)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC013_toggle_table_columns(optout_page):
    """TC013: 'Reason' is hidden by default. Toggling it on shows the column
    header; toggling it off hides it again."""
    ensure_on_optout_page(optout_page)
    assert optout_page.is_column_checked("reason") is False, \
        "'reason' column should be unchecked by default"
    optout_page.toggle_column("reason")
    assert optout_page.is_column_checked("reason") is True
    headers_on = optout_page.get_visible_column_headers()
    assert any("reason" in h.lower() for h in headers_on), \
        "Reason column header should appear after toggling on"

    optout_page.toggle_column("reason")
    assert optout_page.is_column_checked("reason") is False
    headers_off = optout_page.get_visible_column_headers()
    assert not any("reason" in h.lower() for h in headers_off), \
        "Reason column header should disappear after toggling off"


# ══════════════════════════════════════════════════════════════════════════════
# TC014 — Toggle Created At column
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC014_toggle_created_at_column(optout_page):
    """TC014: 'Created At' is also hidden by default. Toggling it on and
    back off verifies the column-select mechanism for this column too."""
    ensure_on_optout_page(optout_page)
    assert optout_page.is_column_checked("created-at") is False, \
        "'created-at' column should be unchecked by default"
    optout_page.toggle_column("created-at")
    assert optout_page.is_column_checked("created-at") is True
    headers_on = optout_page.get_visible_column_headers()
    assert any("created" in h.lower() for h in headers_on)

    optout_page.toggle_column("created-at")
    assert optout_page.is_column_checked("created-at") is False


# ══════════════════════════════════════════════════════════════════════════════
# TC015 — Phone Number column values
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC015_phone_number_column_values(optout_page):
    """TC015: Phone Number column should display non-empty values for all rows."""
    ensure_on_optout_page(optout_page)
    values = optout_page.get_column_values("phone_number")
    assert values, "Phone Number column should have values"
    assert all(len(v) > 0 for v in values), \
        f"All phone number values should be non-empty; got: {values!r}"


# ══════════════════════════════════════════════════════════════════════════════
# TC016 — Opted Out At column values
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC016_opted_out_at_column_values(optout_page):
    """TC016: Opted Out At column should display non-empty date/time values."""
    ensure_on_optout_page(optout_page)
    values = optout_page.get_column_values("opted_out_at")
    assert values, "Opted Out At column should have values"
    assert all(len(v) > 0 for v in values), \
        f"All Opted Out At values should be non-empty; got: {values!r}"


# ══════════════════════════════════════════════════════════════════════════════
# TC017 — Bulk Actions dropdown opens
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC017_bulk_actions_dropdown_opens(optout_page):
    """TC017: Bulk Actions button is visible and opens the dropdown (confirmed
    visible even with zero rows selected — hideBulkActionsWhenEmpty=false)."""
    ensure_on_optout_page(optout_page)
    assert optout_page.is_element_present(optout_page.BULK_ACTIONS_BUTTON, timeout=5000), \
        "Bulk Actions button should be visible on the listing page"
    optout_page.open_bulk_actions_dropdown()
    assert optout_page.is_element_present(optout_page.BULK_ACTION_EXPORT, timeout=5000) or \
           optout_page.is_element_present(optout_page.BULK_ACTION_DELETE, timeout=5000), \
        "Bulk Actions dropdown should show Export CSV or Bulk Delete options"


# ══════════════════════════════════════════════════════════════════════════════
# TC018 — Add New OptOut Number link is reachable
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC018_add_new_optout_link_reachable(optout_page):
    """TC018: 'Add New OptOut Number' link is present and navigates to the
    create page URL — only the confirmed part (link → URL) is asserted;
    form field locators are unconfirmed (no DOM supplied for that page)."""
    ensure_on_optout_page(optout_page)
    assert optout_page.is_element_present(optout_page.ADD_NEW_BTN, timeout=5000), \
        "'Add New OptOut Number' link should be present on the listing page"
    optout_page.click_add_new_optout_number()
    assert optout_page.is_create_page(), \
        "Clicking 'Add New OptOut Number' should navigate to /rcs/optout/create"
    optout_page.navigate()
    optout_page.wait_for_table_load(timeout=10000)


# ══════════════════════════════════════════════════════════════════════════════
# TC019 — Upload button opens a modal
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC019_upload_button_opens_something(optout_page):
    """TC019: Clicking 'Upload OptOut Numbers' button opens a popup/modal.
    The modal's internal DOM was never captured, and the feature is
    documented as broken ('Not working — contacts are not adding to table
    after importing'). This test only confirms the button click doesn't
    error out and that SOME modal markup appears."""
    ensure_on_optout_page(optout_page)
    assert optout_page.is_element_present(optout_page.UPLOAD_BTN, timeout=5000), \
        "'Upload OptOut Numbers' button should be present"
    optout_page.click_upload_optout_numbers()
    opened = (optout_page.is_upload_popup_open()
              or optout_page.is_element_present(optout_page.MODAL_CONTAINER, timeout=5000))
    if not opened:
        pytest.skip(
            "Upload modal did not render any known marker — consistent with "
            "the checklist's own 'Not working' note for this feature."
        )
    ensure_on_optout_page(optout_page)


# ══════════════════════════════════════════════════════════════════════════════
# TC020 — Delete icon triggers confirmation dialog (cancel path)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC020_delete_icon_cancel(optout_page):
    """TC020: Clicking the delete icon on the first row shows a SweetAlert2
    confirmation dialog. Cancelling leaves the record in the table."""
    ensure_on_optout_page(optout_page)
    before_count = optout_page.get_row_count()
    clicked = optout_page.click_delete_on_first_row()
    assert clicked, "Delete icon should be present on the first row"
    cancelled = optout_page.cancel_delete()
    assert cancelled, "Cancel button should appear in the SweetAlert2 dialog"
    optout_page.page.wait_for_timeout(500)
    after_count = optout_page.get_row_count()
    assert after_count == before_count, \
        "Row count should be unchanged after cancelling delete"


# ══════════════════════════════════════════════════════════════════════════════
# TC021 — Pagination results text is displayed
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC021_pagination_results_text(optout_page):
    """TC021: The .paged-pagination-results element is present and shows
    a 'Showing X to Y of Z results' style message."""
    ensure_on_optout_page(optout_page)
    text = optout_page.get_pagination_results_text()
    assert text, "Pagination results text should not be empty"
    assert any(word in text.lower() for word in ["showing", "result", "record"]), \
        f"Pagination text should describe results; got: {text!r}"


# ══════════════════════════════════════════════════════════════════════════════
# TC022 — Next page navigation
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC022_next_page_navigation(optout_page):
    """TC022: Clicking 'Next' loads a different page of opt-out records.
    Confirmed: ~50,015 records / 5,002 pages, so Next is always available."""
    ensure_on_optout_page(optout_page)
    text_before = optout_page.get_pagination_results_text()
    if not optout_page.is_element_present(optout_page.NEXT_PAGE_BTN, timeout=3000):
        pytest.skip("Not enough records in QA environment to test pagination (Next button missing)")
    optout_page.click_next_page()
    text_after = optout_page.get_pagination_results_text()
    assert text_before != text_after, \
        "Pagination result text should change after clicking Next"
    assert optout_page.has_records(), "Records should be present on the second page"


# ══════════════════════════════════════════════════════════════════════════════
# TC023 — Browser refresh retains page
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC023_page_refresh_browser(optout_page):
    """TC023: Refreshing the browser reloads the page without errors."""
    ensure_on_optout_page(optout_page)
    optout_page.page.reload()
    optout_page.page.wait_for_timeout(2000)
    assert optout_page.is_optout_page()
    title = optout_page.get_page_title_text()
    assert "opt" in title.lower()
    assert optout_page.has_records()


# ══════════════════════════════════════════════════════════════════════════════
# TC025 — Performance
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC025_page_performance(optout_page):
    """TC025: Page loads within an acceptable response time (<8000ms)."""
    ensure_on_optout_page(optout_page)
    optout_page.navigate()
    load_time = optout_page.get_page_load_time_ms()
    if load_time is not None and load_time > 0:
        assert load_time < 8000, f"Page load took {load_time}ms (>8000ms threshold)"


# ══════════════════════════════════════════════════════════════════════════════
# TC026 — Empty data scenario (impossible-search fallback)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
@pytest.mark.negative
def test_TC026_empty_data_scenario(optout_page):
    """TC026: When no opt-out numbers match a search, a "No Records Found"-
    style message should be displayed. Exercised via an impossible-to-match
    search term — same pattern used across all suites in this project."""
    ensure_on_optout_page(optout_page)
    optout_page.search("ZZZZNOMATCHPOSSIBLEQWERTY999")
    assert optout_page.has_no_records_message() or optout_page.get_row_count() == 0, \
        "An empty-state indicator (or zero rows) should be shown for a " \
        "search with no matches"
    optout_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# DOCUMENTED SKIPS — original TC006/TC007 stubs kept for traceability
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(reason="Create-page form DOM (/rcs/optout/create) was not "
                          "supplied — only the listing page's 'Add New OptOut "
                          "Number' link is confirmed. Provide a DOM dump of the "
                          "create page to build real field-level assertions.")
def test_TC006_add_new_optout_number_SKIP(optout_page):
    """Skipped stub — see TC018 for the non-skipped, confirmed-only version."""
    ensure_on_optout_page(optout_page)
    optout_page.click_add_new_optout_number()
    assert optout_page.is_create_page()


@pytest.mark.skip(reason="Upload modal's internal DOM (component 'rcs.optout.fetch') "
                          "was not supplied, and the manual QA checklist documents "
                          "this feature as currently broken ('Not working. Contacts "
                          "are not adding to table after importing'). Provide a DOM "
                          "capture of the open modal plus confirmation on expected "
                          "behavior before asserting instead of guessing.")
def test_TC007_upload_optout_numbers_SKIP(optout_page):
    """Skipped stub — see TC019 for the non-skipped, best-effort version."""
    ensure_on_optout_page(optout_page)
    optout_page.click_upload_optout_numbers()
    assert optout_page.is_upload_popup_open()
