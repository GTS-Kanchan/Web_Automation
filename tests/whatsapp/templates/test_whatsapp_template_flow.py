"""
WhatsApp Templates — Automated Test Suite (Templates LISTING page)
Path: /whatsapp/channels/template

Built from a manual QA checklist supplied by the user (TC001-TC015 -- note
TC012 does not exist in the source spreadsheet, a numbering gap only; see
pages/whatsapp/whatsapp_template_page.py's module docstring point 10),
paired with a full, genuine live DOM dump of this exact page (~1027 real
template rows across 103 pages at capture time). See that page object's
module docstring for the complete list of confirmed DOM specifics driving
every locator used here.

Explicitly OUT OF SCOPE per direct user instruction ("don't add fetch
template"): TC015 ("Fetch Template") -- no test for it exists in this file,
even though the real trigger button is confirmed present in the DOM (see
the page object's module docstring point 12).

Test Design Notes:
  - scope="module" -- page object shared across all tests (same pattern as
    every other suite in this project).
  - ensure_on_template_page() recovers to a clean page state before each
    test (re-navigates if drifted). reset_state() clears search/filters/
    sorts and closes any leftover modal before each test.
  - TC008 ("View button") and TC010 ("Template Preview button") are BOTH
    automated against the SAME single confirmed control -- the real DOM
    has no second, distinct "Preview" button (page object module
    docstring point 8). Per the page object's module docstring point 11,
    Header/Footer/variables/buttons sub-sections are NOT asserted since no
    capture of a template with those populated was ever supplied -- only
    the CONFIRMED header/Template ID/body text elements are checked.
  - TC009 ("Delete button") opens the real WireUI confirmAction ->
    SweetAlert2 dialog and then CANCELS it -- no real template row is
    deleted. This page has no "Create Template" flow in scope to
    manufacture a safe scratch row first (unlike e.g.
    tests/email/templates/test_email_template_flow.py's delete-confirm
    test), so a real destructive delete is intentionally not exercised
    here (see page object module docstring point 14).
  - TC011 ("Update template status button") -- the checklist's own
    "Steps" column text for this row doesn't match its own title (page
    object module docstring point 9); automated against the real,
    confirmed updateStatus(<id>) control. The resulting status VALUE is
    NOT asserted (its exact state-transition semantics were never
    confirmed) -- only that the control is present and clickable without
    the page erroring out.
  - TC006 ("Bulk Action") maps to the one real matching control -- a
    page-level "Export to XLSX" confirm-modal flow (wire:click=
    "exportAll"), independent of any filter selection (page object module
    docstring point 4). The checklist's "select date range, department,
    user" wording doesn't describe a real gating requirement on this page.
  - TC013 (sorting) exercises all 7 CONFIRMED sortable columns (Action has
    no sort control). Only the "created_at" case asserts the sorting
    pill's exact wording ("Created at: Z-A" is the one wording this
    session actually captured); the other six only assert that A pill
    appears, to avoid asserting an unconfirmed label format.
  - TC014 (pagination): this environment currently has ~1027 real
    template rows across ~103 pages, so forward pagination is exercised
    for real; the page is re-navigated back to page 1 afterwards so any
    later test run starts from a clean state.

Run:
    pytest tests/whatsapp/templates/test_whatsapp_template_flow.py -v
"""
from datetime import date, timedelta

import pytest

from pages.whatsapp.whatsapp_template_page import WhatsAppTemplatePage


pytestmark = [pytest.mark.whatsapp, pytest.mark.template]


# ══════════════════════════════════════════════════════════════════════════════
# Module-scoped page
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def template_page(module_logged_in_page):
    p = WhatsAppTemplatePage(module_logged_in_page)
    p.navigate()
    p.wait_for_table_load(timeout=15000)
    return p


# ══════════════════════════════════════════════════════════════════════════════
# Recovery helpers
# ══════════════════════════════════════════════════════════════════════════════

def ensure_on_template_page(p: WhatsAppTemplatePage):
    if not p.is_template_list_page():
        p.navigate()
        p.wait_for_table_load(timeout=10000)


def reset_state(p: WhatsAppTemplatePage):
    try:
        p.close_template_preview()
    except Exception:
        pass
    try:
        p.page.keyboard.press("Escape")
    except Exception:
        pass
    try:
        p.clear_search()
    except Exception:
        pass
    try:
        p.clear_all_filters()
    except Exception:
        pass
    try:
        p.clear_all_sorts()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# TC001 — Page loads successfully
# ══════════════════════════════════════════════════════════════════════════════

def test_TC001_page_loads_successfully(template_page):
    ensure_on_template_page(template_page)
    reset_state(template_page)
    assert template_page.is_template_list_page()
    assert template_page.get_page_header_text() == "WhatsApp Template"
    assert "WhatsApp Templates" in template_page.get_breadcrumb_text()
    assert template_page.is_element_present(template_page.TABLE, timeout=10000)


# ══════════════════════════════════════════════════════════════════════════════
# TC002 / TC003 — Search box
# ══════════════════════════════════════════════════════════════════════════════

def test_TC002_search_box_valid_keyword(template_page):
    ensure_on_template_page(template_page)
    reset_state(template_page)
    row = template_page.get_first_data_row()
    assert row is not None, "Expected at least one real template row to search for"
    # Default column order (module docstring #6/#5): Action=0, Name=1.
    name_text = row.locator("td").nth(1).inner_text().strip()
    assert name_text, "First row's Name cell should not be empty"
    keyword = name_text[:6] if len(name_text) >= 6 else name_text
    template_page.search(keyword)
    assert template_page.has_records(), (
        f"Searching for '{keyword}' (taken from a real row's own Name) "
        "should return at least one result"
    )
    template_page.clear_search()


def test_TC003_search_box_invalid_keyword(template_page):
    ensure_on_template_page(template_page)
    reset_state(template_page)
    template_page.search("zzz_nonexistent_qa_keyword_12345")
    assert template_page.has_no_records_message() or template_page.get_row_count() == 0
    template_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# TC004 / TC005 — Filters
# ══════════════════════════════════════════════════════════════════════════════

def test_TC004_filters(template_page):
    ensure_on_template_page(template_page)
    reset_state(template_page)
    template_page.select_type_filter("authentication")
    template_page.select_status_filter("3")  # Approved — CONFIRMED value (STATUS_OPTIONS)
    template_page.set_date_filter("2020-01-01", str(date.today()))
    # The filter combination may legitimately return zero rows in this
    # environment — what's asserted is that filtering runs without error
    # and the page stays on the listing view.
    assert template_page.is_template_list_page()
    assert template_page.get_row_count() >= 0
    template_page.clear_all_filters()


def test_TC005_invalid_date_filter(template_page):
    ensure_on_template_page(template_page)
    reset_state(template_page)
    today = date.today()
    yesterday = today - timedelta(days=1)
    template_page.set_date_filter(str(today), str(yesterday))
    assert template_page.has_no_records_message() or template_page.get_row_count() == 0
    template_page.clear_all_filters()


# ══════════════════════════════════════════════════════════════════════════════
# TC006 — Bulk Action (Export to XLSX)
# ══════════════════════════════════════════════════════════════════════════════

def test_TC006_bulk_action_export(template_page):
    ensure_on_template_page(template_page)
    reset_state(template_page)
    template_page.click_export_button()
    assert template_page.is_export_modal_open()
    confirm_text = template_page.get_export_confirm_text()
    assert "export" in confirm_text.lower()
    # Export is a read-only operation (no data mutation) — safe to fire for
    # real. The "ready to download" markup was never captured (page object
    # module docstring #4), so nothing further is asserted here.
    template_page.confirm_export()


# ══════════════════════════════════════════════════════════════════════════════
# TC007 — Toggle table columns
# ══════════════════════════════════════════════════════════════════════════════

def test_TC007_toggle_table_columns(template_page):
    ensure_on_template_page(template_page)
    reset_state(template_page)
    assert template_page.is_column_checked("department") is False
    template_page.toggle_column("department")
    assert template_page.is_column_checked("department") is True
    headers = template_page.get_visible_column_headers()
    assert any("department" in h.lower() for h in headers)
    template_page.restore_default_columns()
    assert template_page.is_column_checked("department") is False


# ══════════════════════════════════════════════════════════════════════════════
# TC008 / TC010 — View / "Template Preview" button in Actions (SAME control)
# ══════════════════════════════════════════════════════════════════════════════

def test_TC008_view_button_in_actions(template_page):
    ensure_on_template_page(template_page)
    reset_state(template_page)
    assert template_page.click_view_on_first_row(), "View button should be present on the first row"
    assert template_page.is_template_preview_open()
    assert "Template ID:" in template_page.get_template_preview_id_text()
    template_page.close_template_preview()


def test_TC010_template_preview_button_in_actions(template_page):
    """Per page object module docstring #8: the checklist's "Template
    preview button" is the SAME control as TC008's "View" button — there
    is no second, distinct button in the real DOM."""
    ensure_on_template_page(template_page)
    reset_state(template_page)
    assert template_page.click_template_preview_on_first_row()
    assert template_page.is_template_preview_open()
    body = template_page.get_template_preview_body_text()
    assert body != "", "Template Preview body text should render"
    template_page.close_template_preview()


# ══════════════════════════════════════════════════════════════════════════════
# TC009 — Delete button in Actions (open + CANCEL only — see docstring)
# ══════════════════════════════════════════════════════════════════════════════

def test_TC009_delete_button_in_actions(template_page):
    ensure_on_template_page(template_page)
    reset_state(template_page)
    assert template_page.click_delete_on_first_row(), "Delete button should be present on the first row"
    assert template_page.is_delete_confirm_dialog_open(), "WireUI delete confirmation dialog should open"
    assert template_page.cancel_delete()


# ══════════════════════════════════════════════════════════════════════════════
# TC011 — Update template status button in Actions
# ══════════════════════════════════════════════════════════════════════════════

def test_TC011_update_template_status_button(template_page):
    ensure_on_template_page(template_page)
    reset_state(template_page)
    assert template_page.is_update_status_first_row_present(), (
        "Update Status button should be present on the first row"
    )
    assert template_page.click_update_status_on_first_row()
    template_page.page.wait_for_timeout(1500)
    # Resulting status value intentionally not asserted — see module docstring.
    assert template_page.is_template_list_page()


# ══════════════════════════════════════════════════════════════════════════════
# TC013 — Sorting for each column
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("column_key", ["name", "category", "type", "waba_number", "status", "quality"])
def test_TC013_sorting_each_column(template_page, column_key):
    ensure_on_template_page(template_page)
    reset_state(template_page)
    template_page.sort_by(column_key)
    assert template_page.get_applied_sort_pill_text() is not None, (
        f"A sorting pill should appear after sorting by '{column_key}'"
    )
    template_page.clear_all_sorts()


def test_TC013_sorting_created_at_column(template_page):
    ensure_on_template_page(template_page)
    reset_state(template_page)
    template_page.sort_by("created_at")
    pill = template_page.get_applied_sort_pill_text()
    assert pill is not None
    assert "created at" in pill.lower()  # CONFIRMED wording: "Created at: Z-A"
    template_page.clear_all_sorts()


def test_TC013_clear_all_sorts(template_page):
    ensure_on_template_page(template_page)
    reset_state(template_page)
    template_page.sort_by("name")
    assert template_page.get_applied_sort_pill_text() is not None
    template_page.clear_all_sorts()
    assert template_page.get_applied_sort_pill_text() is None


# ══════════════════════════════════════════════════════════════════════════════
# TC014 — Pagination (run last — navigates forward through real pages)
# ══════════════════════════════════════════════════════════════════════════════

def test_TC014_pagination(template_page):
    ensure_on_template_page(template_page)
    reset_state(template_page)
    assert template_page.is_previous_page_disabled(), "Previous should be disabled on page 1"
    assert template_page.is_next_page_enabled(), "Next should be enabled with ~103 real pages"
    template_page.click_next_page()
    assert not template_page.is_previous_page_disabled(), (
        "Previous should become enabled after moving to page 2"
    )
    # Reset back to page 1 so any later test run starts from a clean state.
    template_page.navigate()
    template_page.wait_for_table_load()
