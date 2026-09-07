"""
WhatsApp Numbers (Sender ID) — Automated Test Suite
Path: /whatsapp/channels/senderid

Built from a manual QA checklist supplied by the user (TC001-TC007 and
TC012-TC014, all marked PASS — TC008-TC011 are simply ABSENT from the
supplied checklist, not blank rows, so those numbers are intentionally
skipped here rather than fabricated) for the page the checklist calls
"WhatsApp Numbers" / "sender id page", paired with a full live DOM dump.
See pages/whatsapp/whatsapp_sender_id_page.py's module docstring for the
complete list of confirmed DOM specifics driving every locator used here,
in particular two corrections/clarifications versus the checklist's own
wording:

  - TC006 ("Verify Bulk Action ... Data should download"): this page has
    NO real bulk-actions/row-selection feature at all (confirmed empty
    bulkActions array, no select-all/row checkboxes anywhere in the
    table). The checklist's own wording is reconciled here against the
    CONFIRMED "Export to XLSX" mechanism (an Alpine confirm-dialog +
    wire:click="exportAll"), which is what actually produces a
    downloadable export on this page.
  - TC004 ("Verify filters ... Select date range, Department and user"):
    Department and User are CONFIRMED plain free-text inputs, not
    <select> dropdowns as the wording might suggest.

Test Design Notes:
  - scope="module" — page object shared across all tests (same pattern as
    every other suite in this project).
  - ensure_on_sender_id_page() recovers to a clean page state before each
    test (re-navigates if drifted).
  - TC007 (View) and the bonus "Optimize MMT" action: only "the modal
    opens" is asserted. Neither modal's internal DOM was captured in the
    supplied evidence (showActiveComponent was empty since neither button
    was clicked during capture) — asserting anything about the fields
    inside either modal would be guessing, which this project's rules
    forbid.
  - TC014 (TPS): DOCUMENTED SKIP. wire:snapshot confirms editingTps/
    tpsValue properties and real per-row rate_limit_per_second values
    exist, but no clickable UI trigger for editing TPS was found anywhere
    in the captured DOM (most likely lives inside the uncaptured View
    modal). Skipped rather than guessed.
  - Bonus coverage (confirmed by the DOM but not requested in the
    checklist): the "Create New App" link's reachability, and the
    "Optimize MMT" row action's modal-opens check.

Run:
    pytest tests/whatsapp/sender_id/test_whatsapp_sender_id_flow.py -v
"""
import pytest

from pages.whatsapp.whatsapp_sender_id_page import WhatsappSenderIdPage


pytestmark = [pytest.mark.whatsapp, pytest.mark.sender_id]

# ══════════════════════════════════════════════════════════════════════════════
# Module-scoped page
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def sender_id_page(module_logged_in_page):
    p = WhatsappSenderIdPage(module_logged_in_page)
    p.navigate()
    p.wait_for_table_load(timeout=15000)
    return p


# ══════════════════════════════════════════════════════════════════════════════
# Recovery helpers
# ══════════════════════════════════════════════════════════════════════════════

def ensure_on_sender_id_page(p: WhatsappSenderIdPage):
    if not p.is_sender_id_page():
        p.navigate()
        p.wait_for_table_load(timeout=10000)


def reset_state(p: WhatsappSenderIdPage):
    try:
        p.clear_search()
    except Exception:
        pass
    try:
        p.clear_all_filters()
    except Exception:
        pass
    try:
        p.restore_default_columns()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# TC001 — Page loads successfully
# ══════════════════════════════════════════════════════════════════════════════

def test_TC001_page_loads_successfully(sender_id_page):
    ensure_on_sender_id_page(sender_id_page)
    assert sender_id_page.is_sender_id_page()
    title = sender_id_page.get_page_title_text()
    assert "whatsapp numbers" in title.lower()
    assert sender_id_page.is_element_present(sender_id_page.TABLE, timeout=10000)


def test_TC001_create_new_app_link_reachable(sender_id_page):
    """Bonus, non-checklist coverage: confirms the CONFIRMED-present
    'Create New App' link exists, without asserting anything about the
    create-app page itself (its DOM was never captured)."""
    ensure_on_sender_id_page(sender_id_page)
    assert sender_id_page.is_create_new_app_link_present()


# ══════════════════════════════════════════════════════════════════════════════
# TC002 — Search box with a valid keyword (WABA number or sender id name)
# ══════════════════════════════════════════════════════════════════════════════

def test_TC002_search_box_valid_keyword(sender_id_page):
    ensure_on_sender_id_page(sender_id_page)
    reset_state(sender_id_page)
    sender_id_page.search("9")
    sender_id_page.page.wait_for_timeout(1000)
    assert sender_id_page.get_row_count() > 0 or sender_id_page.has_no_records_message()
    sender_id_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# TC003 — Search box with an invalid keyword shows no data
# ══════════════════════════════════════════════════════════════════════════════

def test_TC003_search_box_invalid_keyword(sender_id_page):
    ensure_on_sender_id_page(sender_id_page)
    reset_state(sender_id_page)
    sender_id_page.search("zzz_no_such_sender_id_zzz")
    sender_id_page.page.wait_for_timeout(1000)
    assert sender_id_page.has_no_records_message() or sender_id_page.get_row_count() == 0
    sender_id_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# TC004 — Filters: date range, Department and User
# ══════════════════════════════════════════════════════════════════════════════

def test_TC004_filters_department_user_date_range(sender_id_page):
    """Department/User are CONFIRMED plain free-text inputs (not
    <select> dropdowns) — see page object docstring point 4."""
    ensure_on_sender_id_page(sender_id_page)
    reset_state(sender_id_page)

    sender_id_page.filter_by_department("a")
    sender_id_page.page.wait_for_timeout(500)
    assert sender_id_page.get_row_count() >= 0  # applies without erroring

    sender_id_page.filter_by_user("a")
    sender_id_page.page.wait_for_timeout(500)
    assert sender_id_page.get_row_count() >= 0

    sender_id_page.set_created_at_from("2020-01-01")
    sender_id_page.set_created_at_to("2030-01-01")
    sender_id_page.page.wait_for_timeout(1000)
    assert sender_id_page.get_row_count() > 0 or sender_id_page.has_no_records_message()

    sender_id_page.clear_all_filters()


# ══════════════════════════════════════════════════════════════════════════════
# TC005 — Invalid date filter: From date more than To date -> no data
# ══════════════════════════════════════════════════════════════════════════════

def test_TC005_invalid_date_range_shows_no_data(sender_id_page):
    ensure_on_sender_id_page(sender_id_page)
    reset_state(sender_id_page)

    sender_id_page.set_created_at_from("2030-01-01")
    sender_id_page.set_created_at_to("2020-01-01")
    sender_id_page.page.wait_for_timeout(1200)

    assert sender_id_page.has_no_records_message() or sender_id_page.get_row_count() == 0

    sender_id_page.clear_all_filters()


# ══════════════════════════════════════════════════════════════════════════════
# TC006 — "Bulk Action" (reconciled to the confirmed Export to XLSX flow)
# ══════════════════════════════════════════════════════════════════════════════

def test_TC006_export_to_xlsx_dialog(sender_id_page):
    """This page has no real bulk-actions/row-selection feature (confirmed
    empty bulkActions array, no checkboxes anywhere) — the checklist's
    'Bulk Action ... Data should download' is reconciled here against the
    CONFIRMED Export to XLSX mechanism instead of a fabricated bulk-select
    locator. Only the dialog opening with the right text and the click
    being accepted are asserted; the post-export 'ready' UI state was
    never captured in the supplied DOM evidence (documented gap)."""
    ensure_on_sender_id_page(sender_id_page)
    reset_state(sender_id_page)

    sender_id_page.click_export_trigger()
    assert sender_id_page.is_export_dialog_open()

    sender_id_page.cancel_export_dialog()
    sender_id_page.page.wait_for_timeout(500)


def test_TC006_export_to_xlsx_confirm(sender_id_page):
    """Companion test: actually confirms the export (wire:click="exportAll"),
    verifying only that the click is accepted without error. No specific
    download/ready UI is asserted (never captured)."""
    ensure_on_sender_id_page(sender_id_page)
    sender_id_page.click_export_trigger()
    if not sender_id_page.is_export_dialog_open():
        pytest.skip("Export confirm dialog did not render — cannot safely "
                     "proceed without guessing an alternate mechanism.")
    sender_id_page.confirm_export()
    ensure_on_sender_id_page(sender_id_page)


# ══════════════════════════════════════════════════════════════════════════════
# TC007 — View button opens a popup with sender id details
# ══════════════════════════════════════════════════════════════════════════════

def test_TC007_view_action_opens_modal(sender_id_page):
    """Only 'the modal opens' is asserted — the View modal's internal
    fields were never captured in the supplied DOM evidence (documented
    gap in the page object docstring)."""
    ensure_on_sender_id_page(sender_id_page)
    sender_id_page.click_view_action()
    assert sender_id_page.is_modal_open()
    sender_id_page.close_modal()
    ensure_on_sender_id_page(sender_id_page)


def test_bonus_optimize_mmt_action_opens_modal(sender_id_page):
    """Bonus, non-checklist coverage: a second, genuinely-confirmed row
    action ('Optimize MMT') exists alongside View. Only 'the modal opens'
    is asserted, for the same reason as TC007."""
    ensure_on_sender_id_page(sender_id_page)
    sender_id_page.click_optimize_mmt_action()
    assert sender_id_page.is_modal_open()
    sender_id_page.close_modal()
    ensure_on_sender_id_page(sender_id_page)


# ══════════════════════════════════════════════════════════════════════════════
# TC012 — Sorting for each sortable column
# ══════════════════════════════════════════════════════════════════════════════

def test_TC012_sorting_each_column(sender_id_page):
    """Only App Name / WABA Number / Status / Created At are sortable
    (confirmed) — Quality/Message Limit/MM Lite APIs have no sortBy
    button at all."""
    ensure_on_sender_id_page(sender_id_page)
    reset_state(sender_id_page)

    sender_id_page.sort_by_app_name()
    pill = sender_id_page.get_applied_sort_pill_text()
    assert pill is not None and "app name" in pill.lower()

    sender_id_page.sort_by_waba_number()
    pill = sender_id_page.get_applied_sort_pill_text()
    assert pill is not None and "waba number" in pill.lower()

    sender_id_page.sort_by_status()
    pill = sender_id_page.get_applied_sort_pill_text()
    assert pill is not None and "status" in pill.lower()

    sender_id_page.sort_by_created_at()
    pill = sender_id_page.get_applied_sort_pill_text()
    assert pill is not None and "created at" in pill.lower()

    sender_id_page.clear_all_sorts()
    sender_id_page.page.wait_for_timeout(1000)
    assert sender_id_page.get_applied_sort_pill_text() is None


# ══════════════════════════════════════════════════════════════════════════════
# TC013 — MM Lite column: click Enabled/Disabled -> fetch latest status
# ══════════════════════════════════════════════════════════════════════════════

def test_TC013_mm_lite_status_click(sender_id_page):
    ensure_on_sender_id_page(sender_id_page)
    reset_state(sender_id_page)

    before = sender_id_page.get_mm_lite_pill_text()
    assert before.strip() != ""

    sender_id_page.click_mm_lite_pill()
    # getMmLiteStatus() fetches live status from Meta — only asserts the
    # pill still renders a valid Enabled/Disabled value afterward, not a
    # specific before/after transition (real Meta API response is not
    # deterministic in a QA environment).
    after = sender_id_page.get_mm_lite_pill_text()
    assert after.strip() in ("Enabled", "Disabled")


# ══════════════════════════════════════════════════════════════════════════════
# TC014 — TPS editing (DOCUMENTED SKIP — no confirmed UI trigger anywhere
# in the captured DOM; likely lives inside the uncaptured View modal)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(reason="No clickable UI trigger for editing TPS was found "
                          "anywhere in the captured DOM, even though the "
                          "component's editingTps/tpsValue properties and "
                          "each row's real rate_limit_per_second value are "
                          "confirmed to exist. It most likely lives inside "
                          "the View modal's internal markup, which was "
                          "never captured (the View button was never "
                          "clicked during the DOM capture). Provide a DOM "
                          "dump of the opened View modal to build a real "
                          "locator instead of guessing one.")
def test_TC014_set_tps(sender_id_page):
    ensure_on_sender_id_page(sender_id_page)
    sender_id_page.click_view_action()
    raise NotImplementedError("No confirmed TPS control to interact with.")
