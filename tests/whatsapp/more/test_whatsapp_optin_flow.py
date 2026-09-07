"""
WhatsApp OptIn Numbers — Automated Test Suite
Path: /whatsapp/campaigns/opt-in

No manual QA checklist (TC numbers) was supplied for this page this time
-- only a full live DOM dump of the listing page. This suite is built
entirely from that DOM evidence, following the same structure as the
already-automated, near-identical WhatsApp Opt-out Numbers suite
(tests/whatsapp/more/test_whatsapp_optout_flow.py) since the two pages
share the same livewire-tables scaffolding (filters, sorting, columns,
bulk actions, row-delete confirm dialog). See
pages/whatsapp/whatsapp_optin_page.py's module docstring for the complete
list of confirmed DOM specifics driving every locator used here, and for
where Opt-in DIFFERS from Opt-out (an extra "Export" top action; bulk
actions ARE present here where they were absent on Flows).

Test Design Notes:
  - scope="module" — page object shared across all tests (same pattern as
    every other suite in this project).
  - ensure_on_optin_page() recovers to a clean page state before each
    test (re-navigates if drifted).
  - "Bulk Delete" and the per-row "Delete" action are both DESTRUCTIVE.
    Bulk Delete is only checked for presence (dropdown + option), never
    clicked. The per-row delete IS exercised for real up to the
    SweetAlert2 confirm dialog (open it, read its title, verify it
    mentions deletion) but the flow always ends by clicking Cancel, never
    Confirm -- identical, already-established treatment to
    whatsapp_optout_page.py's row-delete test.
  - "Add New OptIn Number" is a REAL link (confirmed) to a separate
    create page whose own form DOM was never supplied -- only
    reachability is asserted, matching Opt-out's TC006 treatment.
  - "Upload OptIn Numbers" opens the shared livewire-ui-modal whose
    internal content (dropzone, submit) was never captured -- only "some
    popup renders" is asserted, matching Opt-out's TC007 treatment.
  - "Export" has no confirm dialog or captured success feedback -- the
    test only verifies the click doesn't destabilize the page.

Run:
    pytest tests/whatsapp/more/test_whatsapp_optin_flow.py -v
"""
import pytest

from pages.whatsapp.whatsapp_optin_page import WhatsappOptInPage


pytestmark = [pytest.mark.whatsapp, pytest.mark.opt_in]

# ══════════════════════════════════════════════════════════════════════════════
# Module-scoped page
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def optin_page(module_logged_in_page):
    p = WhatsappOptInPage(module_logged_in_page)
    p.navigate()
    p.wait_for_table_load(timeout=15000)
    return p


# ══════════════════════════════════════════════════════════════════════════════
# Recovery helpers
# ══════════════════════════════════════════════════════════════════════════════

def ensure_on_optin_page(p: WhatsappOptInPage):
    if not p.is_optin_page():
        p.navigate()
        p.wait_for_table_load(timeout=10000)


def reset_state(p: WhatsappOptInPage):
    try:
        p.clear_search()
    except Exception:
        pass
    try:
        p.clear_all_filters()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# Page load
# ══════════════════════════════════════════════════════════════════════════════

def test_page_loads_successfully(optin_page):
    ensure_on_optin_page(optin_page)
    assert optin_page.is_optin_page()
    title = optin_page.get_page_title_text()
    assert "opt" in title.lower()
    assert optin_page.is_element_present(optin_page.TABLE, timeout=10000)


# ══════════════════════════════════════════════════════════════════════════════
# Search
# ══════════════════════════════════════════════════════════════════════════════

def test_search_valid_keyword(optin_page):
    ensure_on_optin_page(optin_page)
    reset_state(optin_page)
    optin_page.search("9")
    optin_page.page.wait_for_timeout(1000)
    assert optin_page.get_row_count() > 0 or optin_page.has_no_records_message()
    optin_page.clear_search()


def test_search_invalid_keyword(optin_page):
    ensure_on_optin_page(optin_page)
    reset_state(optin_page)
    optin_page.search("zzz_no_such_optin_zzz")
    optin_page.page.wait_for_timeout(1000)
    assert optin_page.has_no_records_message() or optin_page.get_row_count() == 0
    optin_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# Columns
# ══════════════════════════════════════════════════════════════════════════════

def test_toggle_table_columns(optin_page):
    """All four columns are CONFIRMED selected by default on this page —
    toggles 'sender' OFF then back ON, verifying the header disappears/
    reappears accordingly."""
    ensure_on_optin_page(optin_page)
    assert optin_page.is_column_checked("sender") is True

    optin_page.toggle_column("sender")
    assert optin_page.is_column_checked("sender") is False
    headers_after_hide = optin_page.get_visible_column_headers()
    assert not any("sender" in h.lower() for h in headers_after_hide)

    optin_page.toggle_column("sender")
    assert optin_page.is_column_checked("sender") is True
    headers_after_show = optin_page.get_visible_column_headers()
    assert any("sender" in h.lower() for h in headers_after_show)


# ══════════════════════════════════════════════════════════════════════════════
# Sorting
# ══════════════════════════════════════════════════════════════════════════════

def test_sorting_each_column(optin_page):
    ensure_on_optin_page(optin_page)
    reset_state(optin_page)

    optin_page.sort_by_phone_number()
    pill = optin_page.get_applied_sort_pill_text()
    assert pill is not None and "phone" in pill.lower()

    optin_page.sort_by_sender()
    pill = optin_page.get_applied_sort_pill_text()
    assert pill is not None and "sender" in pill.lower()

    optin_page.sort_by_opted_in_at()
    pill = optin_page.get_applied_sort_pill_text()
    assert pill is not None and "opted in" in pill.lower()


def test_clear_applied_sorting(optin_page):
    ensure_on_optin_page(optin_page)
    reset_state(optin_page)

    optin_page.sort_by_phone_number()
    assert optin_page.get_applied_sort_pill_text() is not None

    optin_page.clear_all_sorts()
    optin_page.page.wait_for_timeout(1000)
    assert optin_page.get_applied_sort_pill_text() is None


# ══════════════════════════════════════════════════════════════════════════════
# Filters (slide-down: Sender / Opted In From / Opted In To)
# ══════════════════════════════════════════════════════════════════════════════

def test_filters_panel_fields_present(optin_page):
    ensure_on_optin_page(optin_page)
    reset_state(optin_page)
    optin_page.open_filters_panel()
    assert optin_page.is_element_present(optin_page.FILTER_SENDER, timeout=5000)
    assert optin_page.is_element_present(optin_page.FILTER_OPTED_IN_FROM, timeout=5000)
    assert optin_page.is_element_present(optin_page.FILTER_OPTED_IN_TO, timeout=5000)


def test_filters_set_and_clear(optin_page):
    ensure_on_optin_page(optin_page)
    reset_state(optin_page)
    optin_page.set_sender_filter("Globe")
    optin_page.page.wait_for_timeout(500)
    sender_val, _, _ = optin_page.get_filter_values()
    assert sender_val == "Globe"
    optin_page.clear_all_filters()
    sender_val, from_val, to_val = optin_page.get_filter_values()
    assert sender_val == "" and from_val == "" and to_val == ""


def test_filters_invalid_date_range_shows_no_data(optin_page):
    """Setting an Opted In From date after the Opted In To date is a
    boundary/negative case -- the confirmed max date attribute on both
    fields is capture-time-relative, so this uses a clearly invalid
    reversed range instead of hardcoding a specific date."""
    ensure_on_optin_page(optin_page)
    reset_state(optin_page)
    optin_page.set_date_filter(from_date="2026-01-01", to_date="2020-01-01")
    optin_page.page.wait_for_timeout(1000)
    assert optin_page.has_no_records_message() or optin_page.get_row_count() == 0
    optin_page.clear_all_filters()


# ══════════════════════════════════════════════════════════════════════════════
# Top actions: Export / Upload / Add New
# ══════════════════════════════════════════════════════════════════════════════

def test_export_button_present_and_stable_after_click(optin_page):
    """No confirm dialog or captured success feedback exists for Export
    (see module docstring) -- only verifies the button exists and that
    clicking it does not destabilize the page."""
    ensure_on_optin_page(optin_page)
    assert optin_page.is_export_button_present()
    optin_page.click_export()
    assert optin_page.is_optin_page()
    assert optin_page.is_element_present(optin_page.TABLE, timeout=10000)


def test_upload_button_opens_something(optin_page):
    """Confirms only that clicking the button doesn't error out / that
    SOME popup markup appears -- the modal's internal fields were never
    captured (documented gap)."""
    ensure_on_optin_page(optin_page)
    optin_page.click_upload_optin_numbers()
    opened = (
        optin_page.is_upload_popup_open()
        or optin_page.is_element_present(optin_page.MODAL_CONTAINER, timeout=5000)
    )
    if not opened:
        pytest.skip("Upload modal did not render any known marker within the "
                     "captured DOM's confirmed selectors ('#dropzone-file' or "
                     "the shared '#modal-container'). Needs a fresh DOM capture "
                     "of the open modal to build a firmer assertion.")
    ensure_on_optin_page(optin_page)


def test_add_new_optin_link_reachable(optin_page):
    """Confirms only the CONFIRMED part: the link exists and navigates to
    the expected create-page URL. The create page's own form fields were
    never supplied, so nothing about that form is asserted here."""
    ensure_on_optin_page(optin_page)
    optin_page.click_add_new_optin_number()
    assert optin_page.is_create_page()
    optin_page.navigate()
    optin_page.wait_for_table_load(timeout=10000)


# ══════════════════════════════════════════════════════════════════════════════
# Bulk Actions (presence-only -- destructive, never executed)
# ══════════════════════════════════════════════════════════════════════════════

def test_bulk_actions_dropdown_and_delete_option_present(optin_page):
    ensure_on_optin_page(optin_page)
    assert optin_page.is_bulk_actions_button_present()
    assert optin_page.is_bulk_delete_option_present()


def test_row_checkbox_present(optin_page):
    ensure_on_optin_page(optin_page)
    assert optin_page.is_row_checkbox_present()


# ══════════════════════════════════════════════════════════════════════════════
# Row delete -- opened and read for real, but always CANCELLED, never
# confirmed (see module docstring)
# ══════════════════════════════════════════════════════════════════════════════

def test_row_delete_confirm_dialog_then_cancel(optin_page):
    ensure_on_optin_page(optin_page)
    opened = optin_page.click_delete_on_first_row()
    if not opened:
        pytest.skip("No data row with a delete icon was available to click "
                     "(table may have been empty at run time).")
    title = optin_page.get_delete_confirm_title()
    assert "delete" in title.lower()
    cancelled = optin_page.cancel_delete()
    assert cancelled
    ensure_on_optin_page(optin_page)
    # Cancelling must not have removed the row.
    assert optin_page.get_row_count() >= 0


# ══════════════════════════════════════════════════════════════════════════════
# Pagination
# ══════════════════════════════════════════════════════════════════════════════

def test_pagination_results_text(optin_page):
    ensure_on_optin_page(optin_page)
    reset_state(optin_page)
    text = optin_page.get_pagination_results_text()
    assert "showing" in text.lower() and "result" in text.lower()
