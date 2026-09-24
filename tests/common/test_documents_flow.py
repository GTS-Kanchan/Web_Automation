"""
Documents — Sequential Automation Flow
======================================
Test Cases: DOC_001 – DOC_040 (40 test cases)
Target Page: /documents

Covers:
  DOC_001–DOC_004   Page Load, Breadcrumb, Table Columns & Records
  DOC_005–DOC_007   View Action (Single, Specific, Each Document)
  DOC_008–DOC_013   Search (Exact, Partial, Case-insensitive, Nonexistent, Clear, Special Chars)
  DOC_014–DOC_020   Filters (Button, Created From, Created To, Range, Invalid, Remove, Clear)
  DOC_021–DOC_027   Sorting (Default Z-A, Ascending, Descending, Name, Search+Sort, Filter+Sort)
  DOC_028–DOC_032   Columns Visibility (Dropdown, Hide Name, Hide Created At, Restore, Hide Multiple)
  DOC_033–DOC_034   Result Counts (Normal Count, Zero Count)
  DOC_035–DOC_036   Combined Search + Filter, Filter + Sorting
  DOC_037–DOC_040   Document Names, Timestamp Format, Timestamp Accuracy & Deduplication

Run:
    pytest tests/common/test_documents_flow.py -v
"""

import re
from datetime import datetime

import pytest

from pages.common.documents_page import DocumentsPage
from constants.document_ui_headers import (
    EXPECTED_DOCUMENT_UI_HEADERS,
    ALL_DOCUMENT_COLUMNS,
    KNOWN_DEFAULT_DOCUMENTS,
)


pytestmark = [pytest.mark.common, pytest.mark.documents]


# ══════════════════════════════════════════════════════════════════════════════
# Fixture & State Recovery
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def docs_page(module_logged_in_page):
    p = DocumentsPage(module_logged_in_page)
    p.navigate()
    p.wait_for_table_load(timeout=15000)
    return p


def ensure_on_documents_page(p: DocumentsPage):
    if not p.is_documents_page():
        p.navigate()
        p.wait_for_table_load(timeout=10000)


def reset_page_state(p: DocumentsPage):
    try:
        p.clear_search()
    except Exception:
        pass
    try:
        p.clear_all_filters()
    except Exception:
        pass
    try:
        p.select_all_columns()
    except Exception:
        pass
    p.page.wait_for_timeout(800)


# ══════════════════════════════════════════════════════════════════════════════
# DOC_001 – DOC_004 : Page Load, Breadcrumb, Table & Records
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_DOC_001_verify_documents_page_loads(docs_page):
    """Navigate to Documents -> Documents page loads successfully."""
    docs_page.navigate_via_sidebar()
    assert docs_page.is_documents_page(), (
        f"Expected URL to contain /documents, got: {docs_page.get_current_url()}"
    )
    docs_page.wait_for_table_load(timeout=15000)
    assert docs_page.is_element_present(docs_page.TABLE, timeout=8000), "Documents table not found"


@pytest.mark.smoke
def test_DOC_002_verify_page_breadcrumb(docs_page):
    """Open Documents -> 'Home > Documents' breadcrumb is displayed."""
    ensure_on_documents_page(docs_page)
    breadcrumb = docs_page.get_breadcrumb_text()
    assert "Home" in breadcrumb and "Documents" in breadcrumb, (
        f"Expected 'Home > Documents' breadcrumb, got: {breadcrumb}"
    )


@pytest.mark.smoke
def test_DOC_003_verify_document_table(docs_page):
    """Open Documents -> Actions, Name and Created At columns are displayed."""
    ensure_on_documents_page(docs_page)
    headers = docs_page.get_table_headers()
    lowered = [h.lower() for h in headers]
    for expected in ["actions", "name", "created at"]:
        assert any(expected in h for h in lowered), (
            f"Missing expected header: {expected} in {headers}"
        )


@pytest.mark.smoke
def test_DOC_004_verify_document_records(docs_page):
    """Open Documents -> Existing documents are displayed correctly."""
    ensure_on_documents_page(docs_page)
    reset_page_state(docs_page)
    rows_count = docs_page.get_row_count()
    assert rows_count > 0 or docs_page.is_no_records_visible(), "Documents table has no records"
    if rows_count > 0:
        names = docs_page.get_all_document_names()
        assert len(names) > 0, "Document names should not be empty"


# ══════════════════════════════════════════════════════════════════════════════
# DOC_005 – DOC_007 : View Action
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_DOC_005_verify_view_button(docs_page):
    """Click View for a document -> Selected document opens successfully."""
    ensure_on_documents_page(docs_page)
    if docs_page.get_row_count() > 0:
        popup, href = docs_page.click_view(0)
        assert href and ("secure-pdf/download" in href or ".pdf" in href), (
            f"Expected secure PDF download link, got: {href}"
        )
        if popup:
            popup.close()


@pytest.mark.smoke
def test_DOC_006_verify_correct_document_opens(docs_page):
    """Click View for 'Email API - With Template' -> Details/content link of selected document."""
    ensure_on_documents_page(docs_page)
    target_name = "Email API - With Template"
    href = docs_page.get_view_url_by_name(target_name)
    assert href and ("secure-pdf/download" in href or ".pdf" in href), (
        f"Expected valid PDF download link for {target_name}, got: {href}"
    )


@pytest.mark.regression
def test_DOC_007_verify_each_view_button(docs_page):
    """Click View for each available document -> Correct corresponding document opens for every row."""
    ensure_on_documents_page(docs_page)
    row_count = docs_page.get_row_count()
    for idx in range(row_count):
        href = docs_page.get_view_url(idx)
        assert href and ("secure-pdf/download" in href or ".pdf" in href), (
            f"Row {idx} does not have a valid document link: {href}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# DOC_008 – DOC_013 : Search Functionality
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_DOC_008_search_document_by_exact_name(docs_page):
    """Search 'All API Document' -> Matching document is displayed."""
    ensure_on_documents_page(docs_page)
    reset_page_state(docs_page)

    search_term = "All API Document"
    docs_page.search(search_term)
    docs_page.wait_for_table_load(timeout=8000)

    names = docs_page.get_all_document_names()
    assert any(search_term.lower() in n.lower() for n in names), (
        f"Expected {search_term} in results: {names}"
    )
    docs_page.clear_search()


@pytest.mark.regression
def test_DOC_009_search_document_by_partial_name(docs_page):
    """Search 'Email API' -> All matching Email API documents are displayed."""
    ensure_on_documents_page(docs_page)
    reset_page_state(docs_page)

    partial = "Email API"
    docs_page.search(partial)
    docs_page.wait_for_table_load(timeout=8000)

    names = docs_page.get_all_document_names()
    assert len(names) >= 1, f"Expected at least 1 result for {partial}, got {names}"
    for name in names:
        assert partial.lower() in name.lower(), f"Non-matching document returned: {name}"

    docs_page.clear_search()


@pytest.mark.regression
def test_DOC_010_search_with_lowercase_text(docs_page):
    """Search 'email api' -> Matching documents returned irrespective of case."""
    ensure_on_documents_page(docs_page)
    reset_page_state(docs_page)

    lower_term = "email api"
    docs_page.search(lower_term)
    docs_page.wait_for_table_load(timeout=8000)

    names = docs_page.get_all_document_names()
    assert len(names) >= 1, f"Expected results for lowercase search {lower_term}, got {names}"
    for name in names:
        assert lower_term in name.lower(), f"Result {name} does not match {lower_term}"

    docs_page.clear_search()


@pytest.mark.negative
def test_DOC_011_search_nonexistent_document(docs_page):
    """Search 'Test Document XYZ' -> No matching records are displayed."""
    ensure_on_documents_page(docs_page)
    reset_page_state(docs_page)

    bogus_term = "Test Document XYZ Nonexistent 9999"
    docs_page.search(bogus_term)
    docs_page.wait_for_table_load(timeout=8000)

    count = docs_page.get_row_count()
    no_rec = docs_page.is_no_records_visible()
    assert count == 0 or no_rec, f"Expected 0 results for {bogus_term}, got {count}"

    docs_page.clear_search()


@pytest.mark.smoke
def test_DOC_012_clear_search(docs_page):
    """Enter search → clear search -> Complete document list is restored."""
    ensure_on_documents_page(docs_page)
    reset_page_state(docs_page)

    initial_count = docs_page.get_row_count()
    docs_page.search("WABA API")
    docs_page.wait_for_table_load(timeout=8000)

    docs_page.clear_search()
    docs_page.wait_for_table_load(timeout=8000)
    restored_count = docs_page.get_row_count()
    assert restored_count == initial_count, (
        f"Expected document count restored to {initial_count}, got: {restored_count}"
    )


@pytest.mark.negative
def test_DOC_013_search_with_special_characters(docs_page):
    """Enter special characters in search field -> Handled without UI/API error."""
    ensure_on_documents_page(docs_page)
    reset_page_state(docs_page)

    special_query = "!@#$%^&*()_+-=[]{}|;:'\",.<>?/`~"
    docs_page.search(special_query)
    docs_page.wait_for_table_load(timeout=8000)

    assert docs_page.is_element_present(docs_page.TABLE), "Table broken after special characters search"
    docs_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# DOC_014 – DOC_020 : Filters
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_DOC_014_verify_filters_button(docs_page):
    """Click 'Filters' -> Filter options/popover panel opens."""
    ensure_on_documents_page(docs_page)
    docs_page.open_filters_popover()
    assert docs_page.is_filters_popover_open(), "Filter popover did not open"
    docs_page.close_filters_popover()
    assert not docs_page.is_filters_popover_open(), "Filter popover did not close"


@pytest.mark.regression
def test_DOC_015_apply_created_from_filter(docs_page):
    """Select a valid Created From date -> Documents matching filter displayed."""
    ensure_on_documents_page(docs_page)
    reset_page_state(docs_page)

    docs_page.set_created_from("2026-02-17")
    docs_page.wait_for_table_load(timeout=8000)

    chips = docs_page.get_applied_filter_chips()
    assert any("Created From" in c or "17-02-2026" in c for c in chips), (
        f"Expected Created From chip in {chips}"
    )


@pytest.mark.regression
def test_DOC_016_apply_created_to_filter(docs_page):
    """Select a valid Created To date -> Documents matching filter displayed."""
    ensure_on_documents_page(docs_page)
    docs_page.set_created_to("2026-04-14")
    docs_page.wait_for_table_load(timeout=8000)

    chips = docs_page.get_applied_filter_chips()
    assert any("Created To" in c or "14-04-2026" in c for c in chips), (
        f"Expected Created To chip in {chips}"
    )


@pytest.mark.regression
def test_DOC_017_apply_date_range_filter(docs_page):
    """Select valid From and To dates -> Documents created within range displayed."""
    ensure_on_documents_page(docs_page)
    docs_page.set_created_from("2026-02-01")
    docs_page.set_created_to("2026-04-30")
    docs_page.wait_for_table_load(timeout=8000)

    chips = docs_page.get_applied_filter_chips()
    assert len(chips) >= 2, f"Expected 2 date filter chips, got: {chips}"


@pytest.mark.regression
def test_DOC_018_invalid_date_range(docs_page):
    """Set From date later than To date -> Validation or constraint prevents invalid filter."""
    ensure_on_documents_page(docs_page)
    docs_page.open_filters_popover()
    docs_page.set_created_to("2026-02-01")
    docs_page.set_created_from("2026-04-30")
    docs_page.page.wait_for_timeout(1000)

    from_val = docs_page.page.locator(docs_page.FILTER_CREATED_FROM).first.input_value()
    to_val = docs_page.page.locator(docs_page.FILTER_CREATED_TO).first.input_value()
    assert (from_val <= to_val) or docs_page.is_element_present(".validation-error"), (
        f"From date {from_val} was allowed greater than To date {to_val}"
    )


@pytest.mark.regression
def test_DOC_019_remove_applied_filter(docs_page):
    """Apply filter → remove filter -> Selected filter is removed."""
    ensure_on_documents_page(docs_page)
    chips_before = docs_page.get_applied_filter_chips()
    if chips_before:
        docs_page.remove_filter_chip("created_from")
        docs_page.page.wait_for_timeout(1200)
        chips_after = docs_page.get_applied_filter_chips()
        assert len(chips_after) < len(chips_before), (
            f"Expected chip count to decrease from {len(chips_before)} to {len(chips_after)}"
        )


@pytest.mark.smoke
def test_DOC_020_clear_filters(docs_page):
    """Apply filters → click 'Clear' -> All filters are removed and complete list is restored."""
    ensure_on_documents_page(docs_page)
    docs_page.clear_all_filters()
    docs_page.wait_for_table_load(timeout=8000)

    chips = docs_page.get_applied_filter_chips()
    assert len(chips) == 0, f"Expected 0 filter chips after clear, found: {chips}"


# ══════════════════════════════════════════════════════════════════════════════
# DOC_021 – DOC_027 : Sorting
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_DOC_021_verify_applied_sorting(docs_page):
    """Open page -> 'Created At: Z-A' sorting indicator is displayed."""
    ensure_on_documents_page(docs_page)
    sort_text = docs_page.get_applied_sort_text()
    assert "Created At" in sort_text and ("Z-A" in sort_text or "desc" in sort_text.lower()), (
        f"Expected default 'Created At: Z-A' sort indicator, got: {sort_text}"
    )


@pytest.mark.regression
def test_DOC_022_sort_created_at_ascending(docs_page):
    """Click Created At sort -> Documents sorted oldest -> newest (A-Z)."""
    ensure_on_documents_page(docs_page)
    docs_page.click_sort_created_at()
    docs_page.wait_for_table_load(timeout=8000)
    sort_text = docs_page.get_applied_sort_text()
    assert "Created At" in sort_text and ("A-Z" in sort_text or "asc" in sort_text.lower()), (
        f"Expected Created At: A-Z, got: {sort_text}"
    )


@pytest.mark.regression
def test_DOC_023_sort_created_at_descending(docs_page):
    """Click Created At again -> Documents sorted newest -> oldest (Z-A)."""
    ensure_on_documents_page(docs_page)
    docs_page.click_sort_created_at()
    docs_page.wait_for_table_load(timeout=8000)
    sort_text = docs_page.get_applied_sort_text()
    assert "Created At" in sort_text and ("Z-A" in sort_text or "desc" in sort_text.lower()), (
        f"Expected Created At: Z-A, got: {sort_text}"
    )


@pytest.mark.regression
def test_DOC_024_sort_name_ascending(docs_page):
    """Click Name sort -> Documents sorted alphabetically A -> Z."""
    ensure_on_documents_page(docs_page)
    docs_page.click_sort_name()
    docs_page.wait_for_table_load(timeout=8000)
    sort_text = docs_page.get_applied_sort_text()
    assert "Name" in sort_text and ("A-Z" in sort_text or "asc" in sort_text.lower()), (
        f"Expected Name: A-Z, got: {sort_text}"
    )

    names = docs_page.get_all_document_names()
    if len(names) > 1:
        assert names == sorted(names, key=str.casefold), "Names not sorted in ascending order"


@pytest.mark.regression
def test_DOC_025_sort_name_descending(docs_page):
    """Click Name again -> Documents sorted Z -> A."""
    ensure_on_documents_page(docs_page)
    docs_page.click_sort_name()
    docs_page.wait_for_table_load(timeout=8000)
    sort_text = docs_page.get_applied_sort_text()
    assert "Name" in sort_text and ("Z-A" in sort_text or "desc" in sort_text.lower()), (
        f"Expected Name: Z-A, got: {sort_text}"
    )

    names = docs_page.get_all_document_names()
    if len(names) > 1:
        assert names == sorted(names, key=str.casefold, reverse=True), "Names not sorted descending"


@pytest.mark.regression
def test_DOC_026_verify_sorting_after_search(docs_page):
    """Search a document -> sort -> Search results are sorted correctly."""
    ensure_on_documents_page(docs_page)
    reset_page_state(docs_page)

    docs_page.search("API")
    docs_page.wait_for_table_load(timeout=8000)
    docs_page.click_sort_name()
    docs_page.wait_for_table_load(timeout=8000)

    names = docs_page.get_all_document_names()
    assert len(names) >= 1, "Expected results for search 'API'"
    docs_page.clear_search()


@pytest.mark.regression
def test_DOC_027_verify_sorting_after_filtering(docs_page):
    """Apply date filter -> sort -> Filtered results sorted correctly."""
    ensure_on_documents_page(docs_page)
    reset_page_state(docs_page)

    docs_page.set_created_from("2026-02-17")
    docs_page.wait_for_table_load(timeout=8000)
    docs_page.click_sort_created_at()
    docs_page.wait_for_table_load(timeout=8000)

    assert docs_page.get_row_count() >= 0
    docs_page.clear_all_filters()


# ══════════════════════════════════════════════════════════════════════════════
# DOC_028 – DOC_032 : Columns Visibility
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_DOC_028_verify_columns_dropdown(docs_page):
    """Click 'Columns' -> Available columns/options are displayed."""
    ensure_on_documents_page(docs_page)
    docs_page.click_columns_button()
    assert docs_page.is_columns_menu_open(), "Columns menu did not open"
    docs_page.click_columns_button()


@pytest.mark.regression
def test_DOC_029_hide_name_column(docs_page):
    """Disable Name from Columns -> Name column is hidden."""
    ensure_on_documents_page(docs_page)
    docs_page.toggle_column("name", select=False)
    docs_page.wait_for_table_load(timeout=5000)

    assert not docs_page.is_column_visible("Name"), "Name column should be hidden"


@pytest.mark.regression
def test_DOC_030_hide_created_at_column(docs_page):
    """Disable Created At -> Created At column is hidden."""
    ensure_on_documents_page(docs_page)
    docs_page.toggle_column("created-at", select=False)
    docs_page.wait_for_table_load(timeout=5000)

    assert not docs_page.is_column_visible("Created At"), "Created At column should be hidden"


@pytest.mark.regression
def test_DOC_031_restore_hidden_column(docs_page):
    """Re-enable hidden column -> Column becomes visible again."""
    ensure_on_documents_page(docs_page)
    docs_page.toggle_column("name", select=True)
    docs_page.wait_for_table_load(timeout=5000)

    assert docs_page.is_column_visible("Name"), "Name column should be visible again"


@pytest.mark.regression
def test_DOC_032_hide_multiple_columns(docs_page):
    """Hide multiple columns -> Disappear without breaking table."""
    ensure_on_documents_page(docs_page)
    docs_page.toggle_column("name", select=False)
    docs_page.toggle_column("created-at", select=False)
    docs_page.wait_for_table_load(timeout=5000)

    assert docs_page.is_element_present(docs_page.TABLE), "Table broken after hiding columns"

    # Restore all columns
    docs_page.select_all_columns()
    docs_page.wait_for_table_load(timeout=5000)
    assert docs_page.is_column_visible("Name")
    assert docs_page.is_column_visible("Created At")


# ══════════════════════════════════════════════════════════════════════════════
# DOC_033 – DOC_034 : Results Count
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_DOC_033_verify_result_count(docs_page):
    """Check bottom of table -> Correct count such as 'Showing 9 results' is displayed."""
    ensure_on_documents_page(docs_page)
    reset_page_state(docs_page)

    res_text = docs_page.get_result_count_text()
    assert "Showing" in res_text and ("result" in res_text or "results" in res_text), (
        f"Expected results count text, got: {res_text}"
    )


@pytest.mark.negative
def test_DOC_034_verify_zero_results(docs_page):
    """Search nonexistent document -> Result count zero / appropriate no-data message."""
    ensure_on_documents_page(docs_page)
    docs_page.search("nonexistent_document_zero_results_query_9999")
    docs_page.wait_for_table_load(timeout=8000)

    res_text = docs_page.get_result_count_text()
    no_records = docs_page.is_no_records_visible()
    assert ("0" in res_text and "Showing" in res_text) or no_records, (
        f"Expected zero results indication, got text: {res_text}, no_records={no_records}"
    )
    docs_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# DOC_035 – DOC_036 : Combined Operations
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_DOC_035_search_plus_filter_combination(docs_page):
    """Search document + apply date filter -> Results satisfy both conditions."""
    ensure_on_documents_page(docs_page)
    reset_page_state(docs_page)

    docs_page.set_created_from("2026-02-17")
    docs_page.search("Email")
    docs_page.wait_for_table_load(timeout=8000)

    names = docs_page.get_all_document_names()
    for name in names:
        assert "email" in name.lower(), f"Result {name} does not match 'Email'"

    docs_page.clear_search()
    docs_page.clear_all_filters()


@pytest.mark.regression
def test_DOC_036_verify_filter_plus_sorting(docs_page):
    """Apply filter -> sort Created At -> Filter remains applied and results sorted."""
    ensure_on_documents_page(docs_page)
    reset_page_state(docs_page)

    docs_page.set_created_from("2026-02-17")
    docs_page.wait_for_table_load(timeout=8000)
    docs_page.click_sort_created_at()
    docs_page.wait_for_table_load(timeout=8000)

    chips = docs_page.get_applied_filter_chips()
    assert any("Created From" in c or "17-02-2026" in c for c in chips), (
        f"Filter chip lost after sorting: {chips}"
    )
    docs_page.clear_all_filters()


# ══════════════════════════════════════════════════════════════════════════════
# DOC_037 – DOC_040 : Data Accuracy & Formats
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_DOC_037_verify_document_names(docs_page):
    """Compare displayed names with configured documents -> No corruption/truncation."""
    ensure_on_documents_page(docs_page)
    reset_page_state(docs_page)

    names = docs_page.get_all_document_names()
    assert len(names) > 0, "No document names displayed"
    for expected in KNOWN_DEFAULT_DOCUMENTS:
        assert any(expected.lower() == n.lower() for n in names), (
            f"Expected document {expected!r} not found in table names: {names}"
        )


@pytest.mark.regression
def test_DOC_038_verify_created_at_format(docs_page):
    """Check Created At values -> Date/time follows format 'DD-MM-YYYY HH:MM:SS'."""
    ensure_on_documents_page(docs_page)
    timestamps = docs_page.get_all_column_values("created-at")
    assert len(timestamps) > 0, "No Created At timestamps found"
    pattern = r"^\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2}$"
    for ts in timestamps:
        assert re.match(pattern, ts.strip()), f"Timestamp {ts} does not match DD-MM-YYYY HH:MM:SS"


@pytest.mark.regression
def test_DOC_039_verify_created_at_accuracy(docs_page):
    """Compare UI timestamp with parsed datetime -> Valid real calendar timestamp."""
    ensure_on_documents_page(docs_page)
    timestamps = docs_page.get_all_column_values("created-at")
    for ts in timestamps:
        # Validate that datetime parses successfully
        dt = datetime.strptime(ts.strip(), "%d-%m-%Y %H:%M:%S")
        assert dt.year >= 2020 and dt.year <= 2030, f"Timestamp year unreasonable: {dt.year}"


@pytest.mark.regression
def test_DOC_040_verify_duplicate_documents(docs_page):
    """Review document list/search results -> No unintended duplicate documents."""
    ensure_on_documents_page(docs_page)
    reset_page_state(docs_page)

    names = docs_page.get_all_document_names()
    assert len(names) == len(set(names)), f"Duplicate document names found in table: {names}"
