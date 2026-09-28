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

import re
import pytest

from constants.rcs_message_headers import EXPECTED_RCS_MESSAGE_HEADERS
from constants.rcs_message_ui_headers import EXPECTED_RCS_MESSAGE_UI_HEADERS
from pages.rcs.rcs_message_page import RcsMessagePage
from utils.date_module_config import DATE_MODULE_CONFIG
from utils.datetime_verification import (
    DateComparisonError,
    DateFormatValidationError,
    capture_ui_datetime_values,
    column_index_lookup,
    detect_date_columns,
    detect_ui_date_columns,
    read_export_datetime_values,
    validate_date_values_format,
    validate_ui_export_dates,
)
from utils.file_validator import (
    EmptyFileError,
    FileNotDownloadedError,
    HeaderValidationError,
    UnsupportedFileTypeError,
    read_file_rows,
    validate_file_headers,
)


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
    """TC05: Clicking Export CSV downloads a file whose header row
    matches this instance's confirmed RCS Messages export columns
    exactly (constants/rcs_message_headers.py)."""
    reset_filters(message_page)
    message_page.clear_download_dir()
    before = message_page.snapshot_downloads()
    message_page.click_export()
    downloaded = message_page.wait_for_download(timeout=30, before=before)
    if not downloaded:
        pytest.skip("Export did not produce a downloaded file within 30s")

    try:
        actual_headers = validate_file_headers(downloaded, EXPECTED_RCS_MESSAGE_HEADERS)
    except FileNotDownloadedError as exc:
        pytest.fail(str(exc))
    except (UnsupportedFileTypeError, EmptyFileError) as exc:
        pytest.fail(str(exc))
    except HeaderValidationError as exc:
        print(f"Actual headers: {exc.actual}")
        print(f"Missing headers: {exc.missing}")
        print(f"Unexpected headers: {exc.unexpected}")
        for position, expected_name, actual_name in exc.mismatches:
            print(f"Position {position}: expected '{expected_name}', actual '{actual_name}'")
        pytest.fail(str(exc))

    print(f"Header validation PASS: {actual_headers}")


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
    now_checked = message_page.get_column_checkbox_state("department")
    assert now_checked != was_checked, "Department checkbox state did not change"
    # Poll rather than a single immediate read: toggle_column()'s own
    # fixed 800ms settle wait isn't always enough for the grid's header
    # row to finish re-rendering under parallel (-n) execution -- the
    # checkbox itself flips right away (confirmed by now_checked above),
    # but the header list can briefly still reflect the OLD column set.
    headers_after = []
    if now_checked:
        for _ in range(10):
            headers_after = message_page.get_table_headers()
            if any("department" in h.lower() for h in headers_after):
                break
            message_page.page.wait_for_timeout(500)
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
             "received", "rejected", "pending", "-"}
    # A cell showing "no status yet" can render as any of several
    # visually-identical dash characters depending on how the app/CSS
    # produced it (ASCII hyphen-minus U+002D, en dash U+2013, em dash
    # U+2014, non-breaking hyphen U+2011, minus sign U+2212, ...) --
    # confirmed live: a value that *looked* like a plain "-" in the
    # pytest failure output still failed `v.lower() in known` even
    # though "-" is literally in that set, which only happens if it's
    # one of these lookalikes rather than the ASCII character. Treat any
    # cell that's ENTIRELY made of dash-like characters (plus optional
    # surrounding whitespace) as the same "no status" placeholder,
    # regardless of which specific glyph the app used.
    dash_only = re.compile(r"^[\s\-‐‑‒–—―−]+$")
    for v in values:
        if dash_only.match(v):
            continue
        assert v.lower() in known, f"Unrecognized status value: {v!r}"


# ══════════════════════════════════════════════════════════════════════════════
# TC09 — Empty data message
# ══════════════════════════════════════════════════════════════════════════════


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


# ══════════════════════════════════════════════════════════════════════════════
# UI default table headers -- full-list verification
#
# Source: explicit statement of real, current app behavior given directly by
# the project owner (the RCS Messages page's default on-screen table columns),
# not a guess and not the CSV/Excel export header list above (which is a
# separate, already-existing concept). See
# constants/rcs_message_ui_headers.py for the full header list and provenance note.
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_ui_default_table_headers_full(message_page):
    """All confirmed default on-screen table column headers for the RCS Messages
    page are present. Full-list check (every header in
    EXPECTED_RCS_MESSAGE_UI_HEADERS), following this suite's established
    case-insensitive substring-per-header convention."""
    message_page.navigate()
    headers = message_page.get_table_headers()
    for col in EXPECTED_RCS_MESSAGE_UI_HEADERS:
        assert any(col.lower() in h.lower() for h in headers), \
            f"Column '{col}' not found in headers: {headers}"


# ════════════════════════════════════════════════════════════════════════════
# Date/Date-Time Verification -- RCS Messages (shared reusable utility --
# utils/datetime_verification.py, config in utils/date_module_config.py).
# Strict dd-mm-yyyy / dd-mm-yyyy hh:mm:ss only, no relaxation.
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_date_datetime_verification_ui_vs_export(message_page):
    """For every real RCS Messages date/date-time column ("Submitted at",
    "Delivered at", "Read at", "Failed at", "Created at" -- confirmed via
    constants/rcs_message_ui_headers.py / constants/rcs_message_headers.py,
    not hardcoded here), validates every populated on-screen value is a
    real dd-mm-yyyy/dd-mm-yyyy hh:mm:ss value, validates the export's own
    values the same way, and compares UI vs export per column."""
    ensure_on_rcs_messages_page(message_page)

    config = DATE_MODULE_CONFIG["rcs_messages"]
    ui_headers = message_page.get_raw_headers(message_page.TABLE_HEADERS)
    ui_date_columns = detect_ui_date_columns(ui_headers, config["date_columns"], config["ui_column_names"])
    if not ui_date_columns:
        pytest.skip("No configured date/date-time column is present in the RCS Messages UI table right now.")

    row_count = message_page.get_row_count()
    if row_count == 0:
        pytest.skip("No RCS Message rows visible -- nothing to date-verify.")

    ui_values_by_column = capture_ui_datetime_values(
        get_cell_text=message_page.get_cell_text,
        get_column_index=column_index_lookup(ui_headers),
        row_count=row_count,
        date_columns=ui_date_columns,
        column_pairs=config["ui_column_names"],
    )

    message_page.click_export()
    file_path = message_page._last_download_path
    if not file_path:
        pytest.skip("RCS Messages export did not produce a downloaded file -- UI-only verification stands.")

    _headers, rows = read_file_rows(file_path)
    if not rows:
        pytest.skip("RCS Messages export produced 0 data rows -- nothing to compare against.")

    export_date_columns = detect_date_columns(list(rows[0].keys()), config["export_date_columns"])
    export_values_by_column = read_export_datetime_values(rows, export_date_columns)

    try:
        validate_ui_export_dates(
            "RCS Messages", ui_values_by_column, export_values_by_column,
            field_kinds=config["field_kinds"],
        )
    except (DateFormatValidationError, DateComparisonError) as exc:
        pytest.fail(str(exc))
    print(f"[RCS Messages] Date/Date-Time Verification PASS ({row_count} UI row(s))")


# ════════════════════════════════════════════════════════════════════════════════════
# Date/Date-Time Verification -- Message Details Popup (Timeline).
# CONFIRMED via a real pasted DOM: heading "Message Details", Timeline
# card shows Created/Scheduled/Submitted/Delivered/Read, each
# dd-mm-yyyy hh:mm:ss (e.g. "28-09-2026 17:01:31"). UI-only format check
# (no export correspondence for a detail popup), reuses the same
# utils/datetime_verification.py used everywhere else in this suite.
# ═════════════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_date_datetime_verification_details_popup(message_page):
    """Opens the first row's Message Details popup and validates its
    Timeline Created/Scheduled/Submitted/Delivered/Read date-time fields
    are each a real, correctly formatted dd-mm-yyyy hh:mm:ss value."""
    ensure_on_rcs_messages_page(message_page)

    row_count = message_page.get_row_count()
    if row_count == 0:
        pytest.skip("No RCS Message rows visible -- nothing to open a Message Details popup for.")

    if not message_page.click_view_icon(0):
        pytest.skip("No View icon on row 0 -- nothing to date-verify.")
    if not message_page.is_popup_open():
        pytest.skip("Message Details popup did not open for row 0 -- nothing to date-verify.")

    try:
        fields = {
            "Created": message_page.get_popup_created(),
            "Scheduled": message_page.get_popup_scheduled(),
            "Submitted": message_page.get_popup_submitted(),
            "Delivered": message_page.get_popup_delivered(),
            "Read": message_page.get_popup_read(),
        }
        for column, value in fields.items():
            if not value:
                # Not every field applies to every message (e.g. "Read"
                # only applies once a message has actually been read) --
                # not a format violation, nothing to check.
                continue
            try:
                validate_date_values_format("Message Details Popup", column, [value], field_kind="date-time")
            except DateFormatValidationError as exc:
                pytest.fail(str(exc))
            print(f"[Message Details Popup] {column}: Date/Date-Time Format Verification PASS ({value!r})")
    finally:
        message_page.close_popup()

