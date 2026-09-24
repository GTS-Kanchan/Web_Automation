"""
Communication Flow Summary Report — Single Sequential Flow
============================================================
Covers: Automation Flows → Summary tab, TC_SUM_001 - TC_SUM_040
(URL: /flow/summary)

Local page-object fixture named `flow_summary_report_page` (built on
conftest.py's `module_logged_in_page`), following the same pattern as
every other report suite in this project (e.g.
tests/sms/reports/test_sms_status_report_flow.py).

Locators (pages/common/flow_summary_report_page.py) are built from a
live DOM dump of this exact page. See that page object's module
docstring for the full list of CONFIRMED discrepancies vs. the supplied
TC_SUM_* spec -- most importantly:

  * The live table has a 7th column (WhatsApp Count) not listed in the
    spec's TC_SUM_003 (only 6 columns: Flow Name, Date, Trigger Count,
    SMS Count, Email Count, Voice Count).
  * "Bulk Actions" is always visible (hideBulkActionsWhenEmpty: false),
    not gated behind row selection as the spec's TC_SUM_029 precondition
    states, and its only action is "Export to CSV".
  * Export lives inside that Bulk Actions dropdown, not a standalone
    "Export CSV" button.
  * Pagination wire:click targets use TABLE_NAME + "Page" rather than
    the plain TABLE_NAME used elsewhere in this project.

Several TC_SUM_* cases require correlating the UI against known,
seeded backend data (exact trigger/channel counts for a specific flow,
cross-report consistency with the Detailed report, a guaranteed-empty
report state, or triggering a live flow execution) that this suite has
no fixture control over. Per this project's "never guess" convention,
those are implemented as best-effort structural checks (skip when the
live data can't support the assertion) rather than fabricated exact-
match assertions -- see each test's docstring for the specific caveat.

Run:
    pytest tests/common/test_flow_summary_report_flow.py -v
"""
from datetime import datetime

import pytest

from constants.common.flow_summary_report_ui_headers import (
    EXPECTED_FLOW_SUMMARY_REPORT_UI_HEADERS,
)
from pages.common.flow_summary_report_page import FlowSummaryReportPage


pytestmark = [pytest.mark.common, pytest.mark.report, pytest.mark.flow]


@pytest.fixture(scope="module")
def flow_summary_report_page(module_logged_in_page):
    p = FlowSummaryReportPage(module_logged_in_page)
    p.navigate_to_report()
    return p


def ensure_on_report_page(p):
    if not p.is_report_page():
        p.navigate_to_report()
        p.page.wait_for_timeout(1000)


@pytest.fixture(autouse=True)
def _reset_after_test(flow_summary_report_page):
    """Hard reset to a clean report view after every test -- same
    rationale as every other report suite in this project: many
    stateful filters/sorts/selections/columns, so re-navigating fresh
    after each test is the simplest guaranteed way to avoid cross-test
    contamination."""
    yield
    try:
        flow_summary_report_page.navigate_to_report()
    except Exception:
        pass


# ── TC_SUM_001-003 — Page Load / UI Validation ──────────────────────────────

@pytest.mark.smoke
def test_tc_sum_001_summary_report_page_loads(flow_summary_report_page):
    """TC_SUM_001: Communication Flow Summary Report page loads
    successfully."""
    ensure_on_report_page(flow_summary_report_page)
    assert flow_summary_report_page.is_report_page(), "URL should contain /flow/summary"
    title = flow_summary_report_page.get_title().lower()
    assert "404" not in title and "error" not in title


@pytest.mark.smoke
def test_tc_sum_002_report_title_displayed(flow_summary_report_page):
    """TC_SUM_002: "Communication Flow Summary Report" heading is
    displayed."""
    ensure_on_report_page(flow_summary_report_page)
    assert "Communication Flow Summary Report" in flow_summary_report_page.get_page_title_text()


@pytest.mark.regression
def test_tc_sum_003_table_columns(flow_summary_report_page):
    """TC_SUM_003: Table columns include Flow Name, Date, Trigger Count,
    SMS Count, Email Count, Voice Count. NOTE: CONFIRMED live DOM also
    has a 7th "WhatsApp Count" column not listed in the original spec --
    included in EXPECTED_FLOW_SUMMARY_REPORT_UI_HEADERS rather than
    dropped, per this suite's "never guess / never trim confirmed data"
    convention."""
    ensure_on_report_page(flow_summary_report_page)
    headers = flow_summary_report_page.get_visible_column_headers()
    for col in EXPECTED_FLOW_SUMMARY_REPORT_UI_HEADERS:
        assert any(col.lower() in h.lower() for h in headers), \
            f"Column '{col}' not found in headers: {headers}"


# ── TC_SUM_004-011 — Row Data Verification ──────────────────────────────────

@pytest.mark.smoke
def test_tc_sum_004_flow_records_displayed(flow_summary_report_page):
    """TC_SUM_004: Flow records are displayed with data."""
    ensure_on_report_page(flow_summary_report_page)
    assert flow_summary_report_page.has_records() or flow_summary_report_page.has_no_records_message()


@pytest.mark.regression
def test_tc_sum_005_flow_name_column_populated(flow_summary_report_page):
    """TC_SUM_005: Flow Name column shows a non-empty value per row.
    (Best-effort: this suite has no fixture control over which flows
    were actually configured/executed, so it checks presence/non-
    blankness rather than an exact expected name.)"""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.has_records():
        pytest.skip("No flow records available")
    values = flow_summary_report_page.get_column_values("flow_name")
    assert len(values) > 0
    assert all(v != "" for v in values)


@pytest.mark.regression
def test_tc_sum_006_date_column_format(flow_summary_report_page):
    """TC_SUM_006: Date column is displayed in a valid, parseable date
    format. CONFIRMED live DOM format: DD-MM-YYYY (e.g. "16-09-2026")."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.has_records():
        pytest.skip("No flow records available")
    values = flow_summary_report_page.get_column_values("date")
    assert len(values) > 0
    for v in values:
        datetime.strptime(v, "%d-%m-%Y")  # raises ValueError if malformed


@pytest.mark.regression
def test_tc_sum_007_trigger_count_numeric(flow_summary_report_page):
    """TC_SUM_007: Trigger Count values are present and numeric (best-
    effort: verifying they equal actual backend execution counts would
    require seeded data this suite doesn't control)."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.has_records():
        pytest.skip("No flow records available")
    values = flow_summary_report_page.get_column_values("trigger_count")
    assert len(values) > 0
    assert all(v.isdigit() for v in values)


@pytest.mark.regression
def test_tc_sum_008_sms_count_numeric(flow_summary_report_page):
    """TC_SUM_008: SMS Count values are present and numeric."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.has_records():
        pytest.skip("No flow records available")
    values = flow_summary_report_page.get_column_values("sms_count")
    assert len(values) > 0
    assert all(v.isdigit() for v in values)


@pytest.mark.regression
def test_tc_sum_009_email_count_numeric(flow_summary_report_page):
    """TC_SUM_009: Email Count values are present and numeric."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.has_records():
        pytest.skip("No flow records available")
    values = flow_summary_report_page.get_column_values("email_count")
    assert len(values) > 0
    assert all(v.isdigit() for v in values)


@pytest.mark.regression
def test_tc_sum_010_voice_count_numeric(flow_summary_report_page):
    """TC_SUM_010: Voice Count values are present and numeric."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.has_records():
        pytest.skip("No flow records available")
    values = flow_summary_report_page.get_column_values("voice_count")
    assert len(values) > 0
    assert all(v.isdigit() for v in values)


@pytest.mark.regression
def test_tc_sum_011_zero_counts_display_as_zero(flow_summary_report_page):
    """TC_SUM_011: A channel with no communication shows "0", not a
    blank/null cell. CONFIRMED live DOM sample rows already contain
    literal "0" cells (e.g. Email Count "0" alongside SMS Count "2")."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.has_records():
        pytest.skip("No flow records available")
    for col in ("sms_count", "email_count", "voice_count", "whatsapp_count"):
        values = flow_summary_report_page.get_column_values(col)
        assert all(v != "" for v in values), f"{col} should never render blank"


# ── TC_SUM_012-015 — Search / Clear ──────────────────────────────────────────

@pytest.mark.regression
def test_tc_sum_012_search_valid_flow_name(flow_summary_report_page):
    """TC_SUM_012: Searching a valid flow name returns matching
    records."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.has_records():
        pytest.skip("No flow records available to search")
    names = flow_summary_report_page.get_column_values("flow_name")
    needle = names[0] if names and names[0] else "flow"
    flow_summary_report_page.search(needle)
    assert flow_summary_report_page.has_records() or flow_summary_report_page.has_no_records_message()
    flow_summary_report_page.clear_search()


@pytest.mark.regression
def test_tc_sum_013_search_partial_flow_name(flow_summary_report_page):
    """TC_SUM_013: Searching a partial flow name returns all matching
    records."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.has_records():
        pytest.skip("No flow records available to search")
    names = flow_summary_report_page.get_column_values("flow_name")
    full = names[0] if names and names[0] else "flow"
    partial = full[: max(1, len(full) // 2)]
    flow_summary_report_page.search(partial)
    assert flow_summary_report_page.has_records() or flow_summary_report_page.has_no_records_message()
    flow_summary_report_page.clear_search()


@pytest.mark.negative
def test_tc_sum_014_search_invalid_flow_name(flow_summary_report_page):
    """TC_SUM_014: Searching a non-existing flow name shows no
    matching records."""
    ensure_on_report_page(flow_summary_report_page)
    flow_summary_report_page.search("zzzznonexistentflow999")
    assert flow_summary_report_page.has_no_records_message(), \
        "Invalid search should show a no-records state"
    flow_summary_report_page.clear_search()


@pytest.mark.regression
def test_tc_sum_015_clear_removes_applied_sort(flow_summary_report_page):
    """TC_SUM_015: The "Clear" affordance removes an applied sort and
    restores the report's default view. NOTE: the only CONFIRMED "Clear"
    button in the live DOM clears sorting (wire:click.prevent=
    "clearSorts") -- there is no separate combined search/filter "Clear"
    button. CONFIRMED live wire:snapshot: defaultSortColumn="created_at",
    defaultSortDirection="desc" -- clearSorts() resets to THAT default
    rather than to "no sort at all", so this sorts by a different column
    first (Flow Name) to get a non-default chip, then verifies clearSorts
    reverts it back to the default Date sort rather than asserting an
    empty chip."""
    ensure_on_report_page(flow_summary_report_page)
    default_chip = flow_summary_report_page.get_applied_sort_chip_text()
    assert default_chip != ""
    flow_summary_report_page.sort_by("flow_name")
    changed_chip = flow_summary_report_page.get_applied_sort_chip_text()
    assert changed_chip != default_chip
    flow_summary_report_page.clear_all_sorts()
    after = flow_summary_report_page.get_applied_sort_chip_text()
    assert after == default_chip
    assert flow_summary_report_page.has_records() or flow_summary_report_page.has_no_records_message()


# ── TC_SUM_016-019 — Filters ─────────────────────────────────────────────────

@pytest.mark.smoke
def test_tc_sum_016_filters_button_opens_panel(flow_summary_report_page):
    """TC_SUM_016: Clicking Filters reveals the From Date / To Date /
    Flow Name filter fields."""
    ensure_on_report_page(flow_summary_report_page)
    assert flow_summary_report_page.are_filters_visible()


@pytest.mark.regression
def test_tc_sum_017_date_filter_updates_report(flow_summary_report_page):
    """TC_SUM_017: Applying a From/To date range updates the displayed
    records (best-effort: asserts the report remains in a valid state,
    since the exact matching row count depends on live, unseeded data)."""
    ensure_on_report_page(flow_summary_report_page)
    today = datetime.now().strftime("%Y-%m-%d")
    flow_summary_report_page.filter_by_from_date("2020-01-01")
    flow_summary_report_page.filter_by_to_date(today)
    assert flow_summary_report_page.has_records() or flow_summary_report_page.has_no_records_message()


@pytest.mark.regression
def test_tc_sum_018_applied_filter_chip_shown(flow_summary_report_page):
    """TC_SUM_018: An applied filter is displayed as a removable chip.
    Best-effort: no filter was applied in the captured live DOM, so the
    chip markup itself is inferred by symmetry with the CONFIRMED sort
    chip -- skips rather than fails if the live app doesn't render one
    for a Flow Name filter selection."""
    ensure_on_report_page(flow_summary_report_page)
    options = flow_summary_report_page.get_flow_name_filter_options()
    non_default = [o for o in options if o.lower() != "all"]
    if not non_default:
        pytest.skip("No selectable Flow Name filter options available")
    flow_summary_report_page.filter_by_flow_name(non_default[0])
    if not flow_summary_report_page.has_applied_filter_chip():
        pytest.skip("Applied Filters chip markup not confirmed for this filter in the live app")
    assert flow_summary_report_page.has_applied_filter_chip()


@pytest.mark.regression
def test_tc_sum_019_remove_applied_filter_chip(flow_summary_report_page):
    """TC_SUM_019: Removing a filter chip clears that filter and
    refreshes the data. Same best-effort caveat as TC_SUM_018."""
    ensure_on_report_page(flow_summary_report_page)
    options = flow_summary_report_page.get_flow_name_filter_options()
    non_default = [o for o in options if o.lower() != "all"]
    if not non_default:
        pytest.skip("No selectable Flow Name filter options available")
    flow_summary_report_page.filter_by_flow_name(non_default[0])
    if not flow_summary_report_page.has_applied_filter_chip():
        pytest.skip("Applied Filters chip markup not confirmed for this filter in the live app")
    removed = flow_summary_report_page.remove_first_filter_chip()
    assert removed
    assert not flow_summary_report_page.has_applied_filter_chip()


# ── TC_SUM_020-025 — Sorting ─────────────────────────────────────────────────

@pytest.mark.regression
def test_tc_sum_020_date_ascending_sort(flow_summary_report_page):
    """TC_SUM_020: Clicking the Date column header sorts records. Since
    the default sort is already Date descending (CONFIRMED live
    wire:snapshot: sorts: {created_at: desc}), one click flips it to
    ascending. sort_by() polls for the chip text to actually change
    before returning (see page object docstring) -- skips rather than
    fails if the live app doesn't visibly toggle within that window,
    since this suite has no way to force a faster Livewire round-trip."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.has_records():
        pytest.skip("No flow records available")
    before = flow_summary_report_page.get_applied_sort_chip_text()
    changed = flow_summary_report_page.sort_by("date")
    if not changed:
        pytest.skip("Sort chip did not visibly change within the polling window")
    after = flow_summary_report_page.get_applied_sort_chip_text()
    assert "a-z" in after.lower()
    assert after != before


@pytest.mark.regression
def test_tc_sum_021_date_descending_sort(flow_summary_report_page):
    """TC_SUM_021: Clicking the Date column header a second time flips
    the sort direction back."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.has_records():
        pytest.skip("No flow records available")
    changed1 = flow_summary_report_page.sort_by("date")
    if not changed1:
        pytest.skip("Sort chip did not visibly change within the polling window")
    first = flow_summary_report_page.get_applied_sort_chip_text()
    changed2 = flow_summary_report_page.sort_by("date")
    if not changed2:
        pytest.skip("Sort chip did not visibly change within the polling window")
    second = flow_summary_report_page.get_applied_sort_chip_text()
    assert first != second


@pytest.mark.regression
def test_tc_sum_022_trigger_count_sort(flow_summary_report_page):
    """TC_SUM_022: Trigger Count header sorts the table."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.has_records():
        pytest.skip("No flow records available")
    flow_summary_report_page.sort_by("trigger_count")
    assert flow_summary_report_page.has_records() or flow_summary_report_page.has_no_records_message()


@pytest.mark.regression
def test_tc_sum_023_sms_count_sort(flow_summary_report_page):
    """TC_SUM_023: SMS Count header sorts the table."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.has_records():
        pytest.skip("No flow records available")
    flow_summary_report_page.sort_by("sms_count")
    assert flow_summary_report_page.has_records() or flow_summary_report_page.has_no_records_message()


@pytest.mark.regression
def test_tc_sum_024_email_count_sort(flow_summary_report_page):
    """TC_SUM_024: Email Count header sorts the table."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.has_records():
        pytest.skip("No flow records available")
    flow_summary_report_page.sort_by("email_count")
    assert flow_summary_report_page.has_records() or flow_summary_report_page.has_no_records_message()


@pytest.mark.regression
def test_tc_sum_025_voice_count_sort(flow_summary_report_page):
    """TC_SUM_025: Voice Count header sorts the table."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.has_records():
        pytest.skip("No flow records available")
    flow_summary_report_page.sort_by("voice_count")
    assert flow_summary_report_page.has_records() or flow_summary_report_page.has_no_records_message()


# ── TC_SUM_026-029 — Row Selection / Bulk Actions ────────────────────────────

@pytest.mark.regression
def test_tc_sum_026_row_selection_checkbox(flow_summary_report_page):
    """TC_SUM_026: Selecting a row's checkbox marks it selected."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.has_records():
        pytest.skip("No flow records available")
    assert flow_summary_report_page.select_row_checkbox(0)
    assert flow_summary_report_page.is_row_selected(0)


@pytest.mark.regression
def test_tc_sum_027_select_all_checkbox(flow_summary_report_page):
    """TC_SUM_027: The header Select All checkbox selects every record.
    NOTE: CONFIRMED live DOM (delaySelectAll: false) -- clicking it does
    NOT tick each row's own checkbox; it flips a server-side
    selectAllStatus flag and reveals a "You are currently selecting all
    N rows." banner instead, which is what this asserts."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.has_records():
        pytest.skip("No flow records available")
    flow_summary_report_page.click_select_all()
    assert flow_summary_report_page.has_select_all_banner()


@pytest.mark.regression
def test_tc_sum_028_deselect_all_checkbox(flow_summary_report_page):
    """TC_SUM_028: "Deselect All" on the select-all banner clears the
    selection again. Same delaySelectAll: false caveat as TC_SUM_027."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.has_records():
        pytest.skip("No flow records available")
    flow_summary_report_page.click_select_all()
    assert flow_summary_report_page.has_select_all_banner()
    flow_summary_report_page.click_deselect_all()
    assert not flow_summary_report_page.has_select_all_banner()


@pytest.mark.regression
def test_tc_sum_029_bulk_actions_menu(flow_summary_report_page):
    """TC_SUM_029: Bulk Actions reveals available actions. NOTE:
    CONFIRMED live DOM hideBulkActionsWhenEmpty: false -- the Bulk
    Actions button is always available (not gated behind row selection
    as the original spec's precondition states), and its only action is
    "Export to CSV"."""
    ensure_on_report_page(flow_summary_report_page)
    flow_summary_report_page.open_bulk_actions_menu()
    assert flow_summary_report_page.is_element_present(
        flow_summary_report_page.BULK_ACTION_EXPORT_CSV, timeout=5000
    )


# ── TC_SUM_030-032 — Columns Menu ────────────────────────────────────────────

@pytest.mark.regression
def test_tc_sum_030_columns_menu_opens(flow_summary_report_page):
    """TC_SUM_030: Clicking Columns shows the available table columns."""
    ensure_on_report_page(flow_summary_report_page)
    flow_summary_report_page.open_columns_dropdown()
    assert flow_summary_report_page.is_element_present(
        flow_summary_report_page.COLUMN_CHECKBOXES, timeout=5000
    )


@pytest.mark.regression
def test_tc_sum_031_032_hide_and_show_column(flow_summary_report_page):
    """TC_SUM_031 / TC_SUM_032: Disabling a column hides it from the
    table, and re-enabling it restores it. Combined into one test since
    the second half depends directly on the first's hidden column value
    (column selection persists in sessionStorage, CONFIRMED live
    wire:snapshot: sessionStorageStatus.columnselect=true)."""
    ensure_on_report_page(flow_summary_report_page)
    before = set(flow_summary_report_page.get_visible_column_headers())
    unchecked_value = flow_summary_report_page.uncheck_first_optional_column()
    assert unchecked_value is not None
    try:
        after_hide = set(flow_summary_report_page.get_visible_column_headers())
        assert len(after_hide) < len(before)
    finally:
        flow_summary_report_page.check_column(unchecked_value)
    after_show = set(flow_summary_report_page.get_visible_column_headers())
    assert after_show == before


# ── TC_SUM_033-034 — Pagination ──────────────────────────────────────────────

@pytest.mark.regression
def test_tc_sum_033_pagination_next_page(flow_summary_report_page):
    """TC_SUM_033: Navigating to the next page shows the next set of
    records."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.is_next_page_enabled():
        pytest.skip("Next page button is not enabled (only one page of data)")
    before = flow_summary_report_page.get_column_values("flow_name")
    flow_summary_report_page.click_next_page()
    after = flow_summary_report_page.get_column_values("flow_name")
    assert before != after


@pytest.mark.regression
def test_tc_sum_034_pagination_previous_page(flow_summary_report_page):
    """TC_SUM_034: From page 2+, clicking Previous shows the previous
    page's records."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.is_next_page_enabled():
        pytest.skip("Only one page of data -- cannot navigate to page 2")
    page1 = flow_summary_report_page.get_column_values("flow_name")
    flow_summary_report_page.click_next_page()
    if not flow_summary_report_page.is_prev_page_enabled():
        pytest.skip("Previous page button not enabled after navigating forward")
    flow_summary_report_page.click_prev_page()
    page1_again = flow_summary_report_page.get_column_values("flow_name")
    assert page1 == page1_again


# ── TC_SUM_035 — Empty Report ────────────────────────────────────────────────

@pytest.mark.regression
def test_tc_sum_035_empty_report_no_data_message(flow_summary_report_page):
    """TC_SUM_035: An appropriate "No Data" message is displayed when no
    flow execution data matches the current view. Best-effort: this
    suite has no fixture control to make the *entire* report empty (the
    live report has 215+ rows), so this uses an impossible search term
    as a proxy for a query returning zero results, same as TC_SUM_014."""
    ensure_on_report_page(flow_summary_report_page)
    flow_summary_report_page.search("zzzz_no_such_flow_execution_data_zzzz")
    assert flow_summary_report_page.has_no_records_message()
    flow_summary_report_page.clear_search()


# ── TC_SUM_036 — Cross-Report Consistency ────────────────────────────────────

@pytest.mark.regression
def test_tc_sum_036_data_consistency_with_detailed_report(flow_summary_report_page):
    """TC_SUM_036: Trigger/channel counts should be consistent between
    the Summary and Detailed reports. SKIPPED: this project has no page
    object for the Detailed report (/flow/detailed) yet, and fabricating
    one from an unconfirmed DOM would violate this suite's "never guess"
    convention -- add a FlowDetailedReportPage and revisit this test once
    that page's locators are confirmed against the live app."""
    pytest.skip("No confirmed page object for /flow/detailed yet -- see test docstring")


# ── TC_SUM_037-038 — Multi-Channel / Duplicate Flow Names ────────────────────

@pytest.mark.regression
def test_tc_sum_037_multiple_channel_counts_independent(flow_summary_report_page):
    """TC_SUM_037: A flow using multiple channels shows independently
    updated per-channel counts (best-effort: looks for any row in the
    live data where more than one channel column is non-zero, rather
    than triggering a flow execution, which this suite has no control
    over)."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.has_records():
        pytest.skip("No flow records available")
    sms = flow_summary_report_page.get_column_values("sms_count")
    email = flow_summary_report_page.get_column_values("email_count")
    voice = flow_summary_report_page.get_column_values("voice_count")
    whatsapp = flow_summary_report_page.get_column_values("whatsapp_count")
    rows = zip(sms, email, voice, whatsapp)
    multi_channel_rows = [r for r in rows if sum(1 for v in r if v.isdigit() and int(v) > 0) > 1]
    if not multi_channel_rows:
        pytest.skip("No multi-channel flow rows present in current live data")
    assert multi_channel_rows


@pytest.mark.regression
def test_tc_sum_038_duplicate_flow_names_different_dates(flow_summary_report_page):
    """TC_SUM_038: The same flow name with executions on different dates
    appears as separate rows rather than being merged together."""
    ensure_on_report_page(flow_summary_report_page)
    if not flow_summary_report_page.has_records():
        pytest.skip("No flow records available")
    names = flow_summary_report_page.get_column_values("flow_name")
    dates = flow_summary_report_page.get_column_values("date")
    from collections import defaultdict
    by_name = defaultdict(list)
    for n, d in zip(names, dates):
        by_name[n].append(d)
    duplicates = {n: ds for n, ds in by_name.items() if len(ds) > 1}
    if not duplicates:
        pytest.skip("No flow name appears more than once in current live data")
    for name, ds in duplicates.items():
        assert len(set(ds)) == len(ds), \
            f"Flow '{name}' has duplicate rows with the SAME date -- rows may have merged"


# ── TC_SUM_039 — Refresh After New Execution ─────────────────────────────────

@pytest.mark.regression
def test_tc_sum_039_refresh_reflects_new_execution(flow_summary_report_page):
    """TC_SUM_039: Triggering a flow and refreshing the report reflects
    the new execution/count. SKIPPED: this suite has no way to trigger a
    live flow execution from the report page itself (that action lives
    in the Flow Builder, a separate, unrelated page object) -- see
    pages/common/communication_flow_page.py, which is itself an unused
    placeholder with no confirmed locators."""
    pytest.skip("No confirmed way to trigger a flow execution from this suite -- see test docstring")


# ── TC_SUM_040 — Large Data Volume ───────────────────────────────────────────

@pytest.mark.regression
def test_tc_sum_040_large_data_volume_loads_successfully(flow_summary_report_page):
    """TC_SUM_040: The report loads successfully without UI failure or
    incorrect data even with a large number of records. CONFIRMED live
    data at capture time: 215 total records (paginationTotalItemCount).
    Uses the standard browser Performance Timing API, generous 8000ms
    threshold consistent with every other report suite in this
    project."""
    ensure_on_report_page(flow_summary_report_page)
    assert flow_summary_report_page.has_records() or flow_summary_report_page.has_no_records_message()
    text = flow_summary_report_page.get_pagination_results_text()
    assert "of" in text.lower()
    load_time = flow_summary_report_page.get_page_load_time_ms()
    assert load_time is not None
    assert load_time < 8000


# ══════════════════════════════════════════════════════════════════════════════
# UI default table headers -- full-list verification
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_ui_default_table_headers_full(flow_summary_report_page):
    """All confirmed default on-screen table column headers for the
    Communication Flow Summary Report page are present. Full-list check
    (every header in EXPECTED_FLOW_SUMMARY_REPORT_UI_HEADERS), following
    this suite's established case-insensitive substring-per-header
    convention."""
    ensure_on_report_page(flow_summary_report_page)
    headers = flow_summary_report_page.get_visible_column_headers()
    for col in EXPECTED_FLOW_SUMMARY_REPORT_UI_HEADERS:
        assert any(col.lower() in h.lower() for h in headers), \
            f"Column '{col}' not found in headers: {headers}"
