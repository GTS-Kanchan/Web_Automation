"""
WhatsApp Blocked Users — Automated Test Suite
Path: /whatsapp/blocked-users (reached via the top nav's "More" dropdown ->
"Blocked Users" -- the manual QA checklist calls this "sender id page" /
"Blocked users tab"). This is a DIFFERENT feature from WhatsApp OptOut
Numbers (test_whatsapp_optout_flow.py, /whatsapp/campaigns/opt-out) even
though both live in this same "more" folder because both sit under the
app's "More" nav dropdown.

Built from a manual QA checklist supplied by the user (TC001-TC012, all
marked PASS) plus a full live DOM dump of this exact page. See
pages/whatsapp/whatsapp_blocked_users_page.py's module docstring for the
complete list of confirmed DOM specifics driving every locator used here
(tableName "whatsapp_blocked_users", the three plain-onclick modal-trigger
buttons, the confirmed 2-of-4-sortable-columns rule, the Bulk Actions
dropdown's single "Unblock Selected" option, and the genuinely-captured
empty-state text).

Test Design Notes / flagged gaps (per this project's "never guess" rule):
  - The supplied DOM dump captured this page with ZERO rows
    (paginationTotalItemCount: 0) -- a genuine, directly-observed empty
    state, unlike every other page object built this session. This means
    no row-level "Unblock" action button in the Actions column was ever
    captured, and no individual row checkbox's exact markup was directly
    observed either (only the header "select all" checkbox was). Tests
    that need real row data are written to self-verify against whatever
    data exists when the suite actually runs, and skip gracefully with a
    clear reason when the environment is empty at run time -- never
    against a fabricated locator.
  - TC005 (Bulk Action: select contacts, Unblock Selected) is split in
    two: the Bulk Actions dropdown opening and showing "Unblock Selected"
    IS asserted for real (confirmed DOM). The end-to-end
    select-a-row-then-unblock flow is a DOCUMENTED SKIP: the per-row
    checkbox locator used by the page object is reused from an
    already-confirmed IDENTICAL pattern on sibling pages in this same
    codebase (sms_blocked_numbers_page.py / rcs_optout_page.py /
    whatsapp_optout_page.py / rcs_agent_page.py), not from this page's
    own captured DOM (which had no rows) -- and exercising it for real
    would permanently unblock a real contact in the QA environment, so
    it is deliberately not run automatically without the user confirming
    both the exact row markup and that this is safe to execute in this
    environment.
  - TC006 (row-level "Unblock" action in the Actions column) is a
    DOCUMENTED SKIP outright: with zero rows captured, no locator for
    this button exists at all -- not even an inferred one.
  - TC008 (Sync from API), TC009/TC010 (Block Users via CSV / manual
    entry), and TC011/TC012 (Unblock Users via CSV / manual entry) each
    share one of two confirmed trigger buttons ("Sync from API" /
    "Block Users" / "Unblock Users"). Each trigger opening the shared
    livewire-ui-modal IS asserted for real. The modal's INTERNAL content
    for all three (the sender-id select, the "Sync blocked users"
    button, the CSV/manual-entry mode, the upload dropzone, the contact
    input fields) was never captured -- `<div id="modal-container">` was
    present but empty at capture time -- so those are DOCUMENTED SKIPS,
    same treatment as every other uncaptured modal in this session.

Run:
    pytest tests/whatsapp/more/test_whatsapp_blocked_users_flow.py -v
"""
import pytest

from pages.whatsapp.whatsapp_blocked_users_page import WhatsappBlockedUsersPage


pytestmark = [pytest.mark.whatsapp, pytest.mark.opt_out]


# ══════════════════════════════════════════════════════════════════════════════
# Module-scoped page
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def blocked_users_page(module_logged_in_page):
    p = WhatsappBlockedUsersPage(module_logged_in_page)
    p.navigate()
    p.wait_for_table_load(timeout=15000)
    return p


def ensure_on_page(p: WhatsappBlockedUsersPage):
    if not p.is_blocked_users_page():
        p.navigate()
        p.wait_for_table_load(timeout=10000)


def reset_state(p: WhatsappBlockedUsersPage):
    try:
        p.clear_search()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _reset_after_test(blocked_users_page):
    """Hard reset to a clean listing view after every test -- this page
    has several stateful pieces (search, sort, an open modal), so
    re-navigating fresh after each test avoids cross-test contamination
    (same rationale as every other suite in this project)."""
    yield
    try:
        ensure_on_page(blocked_users_page)
        blocked_users_page.navigate()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# TC001 — Verify sender id page (Blocked Users page loads)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_TC001_page_loads_successfully(blocked_users_page):
    """TC001: Blocked users page should open without any error."""
    ensure_on_page(blocked_users_page)
    assert blocked_users_page.is_blocked_users_page()
    assert blocked_users_page.get_page_title_text() == "WhatsApp Blocked Users"
    assert blocked_users_page.is_element_present(blocked_users_page.TABLE, timeout=10000)


# ══════════════════════════════════════════════════════════════════════════════
# TC002 — Search box with a valid keyword
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC002_search_box_valid_keyword(blocked_users_page):
    """TC002: Searching a WABA number or sender id name should display
    data based on the search keyword. Self-verifying where possible:
    reads a real Phone Number value from the current listing first; if
    the environment has no blocked users at run time (the supplied DOM
    dump itself captured a genuinely empty table), falls back to
    asserting the search mechanism itself doesn't error."""
    ensure_on_page(blocked_users_page)
    reset_state(blocked_users_page)
    existing_values = blocked_users_page.get_column_values("phone_number")
    if existing_values:
        target = existing_values[0]
        blocked_users_page.search(target)
        assert blocked_users_page.has_records()
        values = blocked_users_page.get_column_values("phone_number")
        assert any(target in v for v in values)
    else:
        blocked_users_page.search("9")
        assert blocked_users_page.get_row_count() > 0 or blocked_users_page.has_no_records_message()
    blocked_users_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# TC003 — Search box with an invalid keyword
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
@pytest.mark.negative
def test_TC003_search_box_invalid_keyword(blocked_users_page):
    """TC003: Searching an invalid/non-existent keyword shows no data.
    The confirmed real empty-state text ("No items found, try to broaden
    your search") makes this assertion precise rather than a broadened
    guess."""
    ensure_on_page(blocked_users_page)
    reset_state(blocked_users_page)
    blocked_users_page.search("zzz_no_such_blocked_user_zzz")
    blocked_users_page.page.wait_for_timeout(1000)
    assert blocked_users_page.has_no_records_message() or blocked_users_page.get_row_count() == 0
    blocked_users_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# TC004 — Sorting for each sortable column
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC004_sorting_each_column(blocked_users_page):
    """TC004: Clicking a sortable column header should re-sort the data.
    Only Phone Number and Blocked At are confirmed sortable on this page
    (Sender ID and Actions are plain, non-sortable headers)."""
    ensure_on_page(blocked_users_page)
    reset_state(blocked_users_page)

    blocked_users_page.sort_by_phone_number()
    pill = blocked_users_page.get_applied_sort_pill_text()
    assert pill is not None and "phone" in pill.lower()

    blocked_users_page.sort_by_blocked_at()
    pill = blocked_users_page.get_applied_sort_pill_text()
    assert pill is not None and "block" in pill.lower()

    blocked_users_page.clear_all_sorts()


# ══════════════════════════════════════════════════════════════════════════════
# TC005 — Bulk Action (Unblock Selected)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC005_bulk_actions_dropdown_shows_unblock_option(blocked_users_page):
    """Confirmed part of TC005: the Bulk Actions dropdown opens and shows
    the "Unblock Selected" option."""
    ensure_on_page(blocked_users_page)
    blocked_users_page.open_bulk_actions_dropdown()
    assert blocked_users_page.is_element_present(blocked_users_page.BULK_ACTION_UNBLOCK, timeout=5000)


@pytest.mark.skip(reason="No row was ever captured in the supplied DOM dump (the "
                          "table had 0 items at capture time), so this page's own "
                          "per-row checkbox markup was never directly observed -- "
                          "the page object's ROW_CHECKBOX locator is reused from an "
                          "already-confirmed identical pattern on sibling pages "
                          "(sms_blocked_numbers_page.py / rcs_optout_page.py / "
                          "whatsapp_optout_page.py), not from this page's own DOM. "
                          "Exercising it for real would also permanently unblock a "
                          "real contact in this QA environment. Needs the user to "
                          "confirm both the exact row markup and that this is safe "
                          "to run automatically before this is asserted for real.")
def test_TC005_bulk_unblock_selected_contacts(blocked_users_page):
    ensure_on_page(blocked_users_page)
    assert blocked_users_page.has_records(), "Need at least one existing blocked user to select"
    blocked_users_page.select_first_row_checkbox()
    blocked_users_page.click_bulk_unblock()


# ══════════════════════════════════════════════════════════════════════════════
# TC006 — Verify actions (row-level Unblock) — DOCUMENTED SKIP
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(reason="No row was ever captured in the supplied DOM dump (the "
                          "table had 0 items at capture time), so no row-level "
                          "'Unblock' action button locator exists in the page "
                          "object at all -- not even an inferred one. Needs a DOM "
                          "capture of the Actions column with at least one real "
                          "blocked user row present.")
def test_TC006_row_level_unblock_action(blocked_users_page):
    ensure_on_page(blocked_users_page)
    pytest.fail("No row-level Unblock locator exists -- see skip reason above.")


# ══════════════════════════════════════════════════════════════════════════════
# TC007 — Toggle table columns
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC007_toggle_table_columns(blocked_users_page):
    """TC007: Columns hide/show correctly. All four columns are confirmed
    selected by default -- toggles Sender ID off then back on, verifying
    the header disappears/reappears accordingly."""
    ensure_on_page(blocked_users_page)
    assert blocked_users_page.get_column_checkbox_state("sender-id") is True

    blocked_users_page.toggle_column("sender-id")
    assert blocked_users_page.get_column_checkbox_state("sender-id") is False
    headers_after_hide = blocked_users_page.get_table_headers()
    assert not any("sender" in h.lower() for h in headers_after_hide)

    blocked_users_page.toggle_column("sender-id")
    assert blocked_users_page.get_column_checkbox_state("sender-id") is True
    headers_after_show = blocked_users_page.get_table_headers()
    assert any("sender" in h.lower() for h in headers_after_show)


# ══════════════════════════════════════════════════════════════════════════════
# TC008 — Sync from API
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC008_sync_from_api_opens_modal(blocked_users_page):
    """Confirmed part of TC008: clicking "Sync from API" opens the
    shared livewire-ui-modal."""
    ensure_on_page(blocked_users_page)
    blocked_users_page.click_sync_from_api()
    assert blocked_users_page.is_modal_open(timeout=10000)
    blocked_users_page.close_modal()


@pytest.mark.skip(reason="The modal's internal content for 'Sync from API' "
                          "(component 'whatsapp.blocked-users.sync-blocked-users' "
                          "-- the sender id select and the 'Sync blocked users' "
                          "button) was never captured; only the trigger button and "
                          "the fact that the shared modal opens are confirmed. "
                          "Needs a DOM capture of the open modal to build real "
                          "field-level assertions.")
def test_TC008_sync_from_api_select_sender_and_sync(blocked_users_page):
    ensure_on_page(blocked_users_page)
    pytest.fail("Modal internals for Sync from API were never captured -- see skip reason above.")


# ══════════════════════════════════════════════════════════════════════════════
# TC009 / TC010 — Block users through CSV/Excel file or manual entry
# (both share the same confirmed "Block Users" trigger button; the
# CSV-vs-manual choice happens INSIDE the uncaptured modal)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC009_TC010_block_users_button_opens_modal(blocked_users_page):
    """Confirmed shared part of TC009/TC010: clicking "Block Users" opens
    the shared livewire-ui-modal (dispatched with arguments
    {action: 'block'})."""
    ensure_on_page(blocked_users_page)
    blocked_users_page.click_block_users()
    assert blocked_users_page.is_modal_open(timeout=10000)
    blocked_users_page.close_modal()


@pytest.mark.skip(reason="The Block Users modal's internal content (component "
                          "'whatsapp.blocked-users.import-users' with the "
                          "CSV/Excel upload dropzone vs. manual-entry mode, sender "
                          "id select, and submit button) was never captured; only "
                          "the trigger button and the fact that the shared modal "
                          "opens are confirmed. Needs a DOM capture of the open "
                          "modal (both the file-upload and manual-entry modes) to "
                          "build real field-level assertions for TC009 (CSV) and "
                          "TC010 (manual entry) separately.")
def test_TC009_TC010_block_users_via_csv_or_manual(blocked_users_page):
    ensure_on_page(blocked_users_page)
    pytest.fail("Block Users modal internals were never captured -- see skip reason above.")


# ══════════════════════════════════════════════════════════════════════════════
# TC011 / TC012 — Unblock users through CSV/Excel file or manual entry
# (both share the same confirmed "Unblock Users" trigger button; the
# CSV-vs-manual choice happens INSIDE the uncaptured modal)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC011_TC012_unblock_users_button_opens_modal(blocked_users_page):
    """Confirmed shared part of TC011/TC012: clicking "Unblock Users"
    opens the shared livewire-ui-modal (dispatched with arguments
    {action: 'unblock'})."""
    ensure_on_page(blocked_users_page)
    blocked_users_page.click_unblock_users()
    assert blocked_users_page.is_modal_open(timeout=10000)
    blocked_users_page.close_modal()


@pytest.mark.skip(reason="The Unblock Users modal's internal content (component "
                          "'whatsapp.blocked-users.import-users' with the "
                          "CSV/Excel upload dropzone vs. manual-entry mode, sender "
                          "id select, and submit button) was never captured; only "
                          "the trigger button and the fact that the shared modal "
                          "opens are confirmed. Needs a DOM capture of the open "
                          "modal (both the file-upload and manual-entry modes) to "
                          "build real field-level assertions for TC011 (CSV) and "
                          "TC012 (manual entry) separately.")
def test_TC011_TC012_unblock_users_via_csv_or_manual(blocked_users_page):
    ensure_on_page(blocked_users_page)
    pytest.fail("Unblock Users modal internals were never captured -- see skip reason above.")


# ══════════════════════════════════════════════════════════════════════════════
# Bonus — genuinely-captured empty state
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
@pytest.mark.negative
def test_bonus_empty_state_exact_text(blocked_users_page):
    """Unlike every other page object built this session, this page's
    empty state was GENUINELY captured (0 rows at capture time), giving
    an exact confirmed message rather than a guessed fallback."""
    ensure_on_page(blocked_users_page)
    reset_state(blocked_users_page)
    blocked_users_page.search("zzz_guaranteed_no_match_zzz")
    blocked_users_page.page.wait_for_timeout(1000)
    assert blocked_users_page.is_element_present(blocked_users_page.NO_RECORDS_MSG, timeout=5000)
    blocked_users_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# Bonus — pagination results text
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_bonus_pagination_results_text(blocked_users_page):
    """Confirmed convention (same as WhatsApp OptOut Numbers): a
    single-count "Showing N results" format."""
    ensure_on_page(blocked_users_page)
    text = blocked_users_page.get_pagination_results_text()
    assert text, "Pagination results text should be present"
    assert "showing" in text.lower()
