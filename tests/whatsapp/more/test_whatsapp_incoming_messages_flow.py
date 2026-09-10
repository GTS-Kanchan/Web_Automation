"""
WhatsApp Incoming Messages — Automated Test Suite
Path: /whatsapp/campaigns/incoming-messages (reached via the top nav's
"More" dropdown -> "Incoming Messages", not one of the main channel tabs).

Built from a manual QA checklist supplied by the user (TC001-TC005 plus 4
further unlabeled checklist rows: "View button in action", "Campaign name
column", "WABA number", and an incomplete row "Verify User number and user
name" whose Steps/Expected/Actual were left blank), paired with a full live
DOM dump of this exact page. See
pages/whatsapp/whatsapp_incoming_messages_page.py's module docstring for
the complete list of confirmed DOM specifics driving every locator used
here (tableName "wa_incoming_messages", the WABA Number filter's
phone-number-to-internal-id mapping, the 11 Type filter values, the native
date+time Received From/To filter mechanism, the 2-of-9-sortable-headers
rule, the masked User Number pattern, the Campaign Name "N/A"-or-"...-
Campaign" business rule, the livewire-ui-modal View popup, and the real
2603-item/261-page pagination).

Test Design Notes / flagged gaps (per this project's "never guess" rule):
  - TC005 in the user's checklist says "select CreatedAt From and CreatedAt
    To dates", but the DOM capture confirms the actual filter fields are
    named `received_from` / `received_to` (labelled "Received From" /
    "Received To" in the UI) -- there is no separate CreatedAt date filter
    on this page. This test exercises the CONFIRMED received_from/
    received_to fields and flags the naming discrepancy here rather than
    silently assuming they're interchangeable.
  - The unlabeled "View button in action" row asks that "all data related
    to that incoming message should be available" after clicking View.
    The supplied DOM dump only captured the page BEFORE the modal opens
    (`<div id="modal-container">` was present but empty at capture time,
    same situation already documented for the WhatsApp Messages Report
    page's TC009-027) -- so only "the modal opens" is asserted for real;
    the fields rendered *inside* the modal are an undocumented gap and are
    not asserted here to avoid fabricating locators.
  - The final unlabeled checklist row ("Verify User number and user name")
    had blank Steps/Expected/Actual in the source spreadsheet. It is
    implemented here using the two DOM-confirmed, unambiguous business
    rules available for those two columns: User Number values must match
    the confirmed masking pattern, and User Name values must be
    non-empty real text.
  - No genuine empty state was ever captured (all 10 sampled rows had real
    data), so NO_RECORDS_MSG is only exercised indirectly via an
    impossible-to-match search term, mirroring the same pattern already
    used for this identical situation on the SMS Incoming Messages suite.
  - Bonus coverage beyond the original checklist (consistent with this
    project's practice of also testing everything else genuinely
    confirmed by the DOM evidence): the Columns dropdown's 9 checkboxes,
    sorting on the two confirmed-sortable headers (Received At / Created
    At) plus their clear-sort/clear-all-sorts controls, the Export CSV
    link, and the real multi-page pagination (Next button, gotoPage,
    results text).

Run:
    pytest tests/whatsapp/more/test_whatsapp_incoming_messages_flow.py -v
"""
import pytest

from pages.whatsapp.whatsapp_incoming_messages_page import WhatsappIncomingMessagesPage


pytestmark = [pytest.mark.whatsapp, pytest.mark.messaging]


# ══════════════════════════════════════════════════════════════════════════════
# Module-scoped page
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def incoming_messages_page(module_logged_in_page):
    p = WhatsappIncomingMessagesPage(module_logged_in_page)
    p.navigate()
    p.wait_for_table_load(timeout=15000)
    return p


def ensure_on_page(p: WhatsappIncomingMessagesPage):
    if not p.is_incoming_messages_page():
        p.navigate()
        p.wait_for_table_load(timeout=10000)


@pytest.fixture(autouse=True)
def _reset_after_test(incoming_messages_page):
    """Hard reset to a clean listing view after every test -- this page has
    many stateful pieces (search, filters, columns, sort, an open modal),
    so re-navigating fresh after each test avoids cross-test contamination
    (same rationale as every other suite in this project)."""
    yield
    try:
        incoming_messages_page.navigate()
        incoming_messages_page.wait_for_table_load(timeout=10000)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# TC001 — Incoming Messages page loads
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_TC001_page_loads_successfully(incoming_messages_page):
    """TC001: Incoming Messages page should load without any error."""
    ensure_on_page(incoming_messages_page)
    assert incoming_messages_page.is_incoming_messages_page()
    assert incoming_messages_page.get_page_title_text() == "WhatsApp Incoming Messages"
    assert incoming_messages_page.is_element_present(incoming_messages_page.TABLE, timeout=10000)


# ══════════════════════════════════════════════════════════════════════════════
# TC002 — Search filter with a valid keyword
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC002_search_valid_keyword(incoming_messages_page):
    """TC002: Searching a valid keyword (User Name) should display data
    matching that keyword. User Name is used as the search target rather
    than the masked User Number or the sometimes-"N/A" Campaign Name,
    since it's the one confirmed column that's always plain, unmasked
    text -- self-verifying: reads a real value from the current listing
    immediately before searching, mirroring the SMS Incoming Messages
    suite's TC005 pattern."""
    ensure_on_page(incoming_messages_page)
    existing_values = incoming_messages_page.get_column_values("user_name")
    assert existing_values, "Need at least one existing record to search for"
    target = existing_values[0]
    incoming_messages_page.search(target)
    assert incoming_messages_page.has_records()
    values = incoming_messages_page.get_column_values("user_name")
    assert any(target in v for v in values)
    incoming_messages_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# TC003 — WABA number filter
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC003_waba_number_filter(incoming_messages_page):
    """TC003: Selecting a WABA number in the Filters panel should filter
    data to only that WABA number. Self-verifying: reads a real WABA
    Number value from the current listing, then filters by it (mapped
    through WABA_NUMBER_TO_ID, since the <select>'s real option values
    are internal sender ids, not the phone numbers themselves)."""
    ensure_on_page(incoming_messages_page)
    existing_values = incoming_messages_page.get_column_values("waba_number")
    assert existing_values, "Need at least one existing record to filter by"
    target = existing_values[0]
    assert target in incoming_messages_page.WABA_NUMBER_TO_ID, \
        f"WABA Number {target!r} is not one of the confirmed known senders {list(incoming_messages_page.WABA_NUMBER_TO_ID)!r}"
    incoming_messages_page.filter_by_waba_number(target)
    assert incoming_messages_page.has_records() or incoming_messages_page.has_no_records_message()
    if incoming_messages_page.has_records():
        values = incoming_messages_page.get_column_values("waba_number")
        assert all(v == target for v in values), \
            f"All rows should have WABA Number {target!r} after filtering, got {values!r}"
    incoming_messages_page.click_clear_all_filters()


# ══════════════════════════════════════════════════════════════════════════════
# TC004 — Type filter
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC004_type_filter(incoming_messages_page):
    """TC004: Selecting an incoming message Type in the Filters panel
    should filter data to only that message type. Self-verifying: reads a
    real Type value from the current listing, then filters by it."""
    ensure_on_page(incoming_messages_page)
    existing_values = incoming_messages_page.get_column_values("type")
    assert existing_values, "Need at least one existing record to filter by"
    target = existing_values[0]
    assert target in incoming_messages_page.TYPE_FILTER_VALUES, \
        f"Type {target!r} is not one of the confirmed Type filter values {incoming_messages_page.TYPE_FILTER_VALUES!r}"
    incoming_messages_page.filter_by_type(target)
    assert incoming_messages_page.has_records() or incoming_messages_page.has_no_records_message()
    if incoming_messages_page.has_records():
        values = incoming_messages_page.get_column_values("type")
        assert all(v == target for v in values), \
            f"All rows should have Type {target!r} after filtering, got {values!r}"
    incoming_messages_page.click_clear_all_filters()


# ══════════════════════════════════════════════════════════════════════════════
# TC005 — Date filter (Received From / Received To)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC005_date_filter(incoming_messages_page):
    """TC005: Selecting a From/To date range should display data based on
    the applied filter. NOTE: the user's checklist calls this
    "CreatedAt From/To", but the DOM-confirmed filter fields on this page
    are actually "Received From" / "Received To" (filterComponents.
    received_from / .received_to) -- there is no separate CreatedAt date
    filter here, so this test exercises the confirmed Received From/To
    fields instead."""
    ensure_on_page(incoming_messages_page)
    incoming_messages_page.set_received_from("2026-01-01", time_str="00:00")
    incoming_messages_page.set_received_to("2026-09-06", time_str="23:55")
    assert incoming_messages_page.has_records() or incoming_messages_page.has_no_records_message()
    from_value = incoming_messages_page.get_filter_received_from_value()
    to_value = incoming_messages_page.get_filter_received_to_value()
    assert from_value == "2026-01-01"
    assert to_value == "2026-09-06"
    incoming_messages_page.click_clear_all_filters()


# ══════════════════════════════════════════════════════════════════════════════
# View button in Action column
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_view_button_action_column(incoming_messages_page):
    """Verify View button in Action column: clicking it should open the
    incoming message's detail popup. Only "the modal opens" is asserted
    for real -- the DOM dump did not capture the modal's rendered inner
    content (undocumented gap, see module docstring), so specific field
    assertions inside the popup are intentionally not made here."""
    ensure_on_page(incoming_messages_page)
    clicked = incoming_messages_page.click_view_on_first_row()
    assert clicked, "View icon should be present and clickable on the first row"
    assert incoming_messages_page.is_modal_open(timeout=10000), "Incoming message details modal should open"
    incoming_messages_page.close_modal()


# ══════════════════════════════════════════════════════════════════════════════
# Campaign Name column
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_campaign_name_column(incoming_messages_page):
    """Verify Campaign Name column: should display only the latest
    campaign sent to that user (a label ending in "- Campaign"), or "N/A"
    when no campaign preceded the message."""
    ensure_on_page(incoming_messages_page)
    values = incoming_messages_page.get_column_values("campaign_name")
    assert values, "Campaign Name column should have values"
    bad_values = [v for v in values if not incoming_messages_page.is_valid_campaign_name_value(v)]
    assert not bad_values, (
        f"Campaign Name column has value(s) that are neither 'N/A' nor a "
        f"campaign label: {bad_values!r} (full column: {values!r})")


# ══════════════════════════════════════════════════════════════════════════════
# WABA number column
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_waba_number_column(incoming_messages_page):
    """Verify WABA number column: should display only the sender id
    (WABA number) the user is messaging -- one of the confirmed real
    sender numbers."""
    ensure_on_page(incoming_messages_page)
    values = incoming_messages_page.get_column_values("waba_number")
    assert values, "WABA Number column should have values"
    bad_values = [v for v in values if v not in incoming_messages_page.WABA_NUMBER_TO_ID]
    assert not bad_values, (
        f"WABA Number column has value(s) that are not a confirmed known "
        f"sender: {bad_values!r} (full column: {values!r})")


# ══════════════════════════════════════════════════════════════════════════════
# User number and user name columns
# (unlabeled/incomplete checklist row -- Steps/Expected/Actual were blank
# in the source spreadsheet; implemented using the two DOM-confirmed rules
# below since no other detail was supplied.)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_user_number_and_user_name_columns(incoming_messages_page):
    """Verify User Number and User Name columns. User Number: confirmed
    to always be partially masked (e.g. "91873*****03"), never a raw
    unmasked number. User Name: confirmed to always be non-empty real
    text."""
    ensure_on_page(incoming_messages_page)
    number_values = incoming_messages_page.get_column_values("user_number")
    assert number_values, "User Number column should have values"
    bad_numbers = [v for v in number_values if not incoming_messages_page.is_masked_user_number(v)]
    assert not bad_numbers, (
        f"User Number column has value(s) not matching the confirmed masked "
        f"pattern: {bad_numbers!r} (full column: {number_values!r})")

    name_values = incoming_messages_page.get_column_values("user_name")
    assert name_values, "User Name column should have values"
    assert all(len(v) > 0 for v in name_values), \
        f"User Name column should have no empty values, got {name_values!r}"


# ══════════════════════════════════════════════════════════════════════════════
# Bonus — search with no match (empty-state exercise)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
@pytest.mark.negative
def test_bonus_search_invalid_keyword(incoming_messages_page):
    """No genuine empty state was ever captured in the DOM dump, so this
    is exercised the same way as the SMS Incoming Messages suite's TC025
    -- an impossible-to-match search term."""
    ensure_on_page(incoming_messages_page)
    incoming_messages_page.search("ZZZZNOMATCHPOSSIBLEQWERTY999")
    assert incoming_messages_page.has_no_records_message() or incoming_messages_page.get_row_count() == 0
    incoming_messages_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# Bonus — Columns dropdown
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_bonus_columns_dropdown_all_present(incoming_messages_page):
    """The Columns dropdown should list all 9 confirmed real column
    checkboxes, all checked by default (per wire:snapshot's
    selectedColumns)."""
    ensure_on_page(incoming_messages_page)
    incoming_messages_page.open_columns_dropdown()
    for value in incoming_messages_page.ALL_COLUMN_VALUES:
        assert incoming_messages_page.is_column_checkbox_present(value), \
            f"Column checkbox {value!r} should be present in the Columns dropdown"
        assert incoming_messages_page.get_column_checkbox_state(value) is True, \
            f"Column checkbox {value!r} should be checked by default"


# ══════════════════════════════════════════════════════════════════════════════
# Bonus — Sorting (only Received At / Created At are sortable)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_bonus_sort_by_received_at(incoming_messages_page):
    """Clicking the Received At column header re-sorts the visible rows."""
    ensure_on_page(incoming_messages_page)
    before = incoming_messages_page.get_column_values("received_at")
    incoming_messages_page.sort_by_received_at()
    after1 = incoming_messages_page.get_column_values("received_at")
    incoming_messages_page.sort_by_received_at()
    after2 = incoming_messages_page.get_column_values("received_at")
    assert before != after1 or after1 != after2, \
        "Clicking Received At header should change row order across toggles"
    incoming_messages_page.clear_all_sorts()


@pytest.mark.regression
def test_bonus_sort_by_created_at(incoming_messages_page):
    """Clicking the Created At column header re-sorts the visible rows."""
    ensure_on_page(incoming_messages_page)
    before = incoming_messages_page.get_column_values("created_at")
    incoming_messages_page.sort_by_created_at()
    after1 = incoming_messages_page.get_column_values("created_at")
    incoming_messages_page.sort_by_created_at()
    after2 = incoming_messages_page.get_column_values("created_at")
    assert before != after1 or after1 != after2, \
        "Clicking Created At header should change row order across toggles"
    incoming_messages_page.clear_all_sorts()


@pytest.mark.regression
def test_bonus_clear_single_sort_pill(incoming_messages_page):
    """A single sort pill's own clear control (plain wire:click, no
    .prevent -- confirmed distinct from the clear-ALL control) should
    remove just that applied sort."""
    ensure_on_page(incoming_messages_page)
    incoming_messages_page.sort_by_received_at()
    assert incoming_messages_page.is_sort_applied("received_at")
    incoming_messages_page.clear_sort("received_at")
    assert not incoming_messages_page.is_sort_applied("received_at")


@pytest.mark.regression
def test_bonus_clear_all_sorts(incoming_messages_page):
    """The clear-ALL-sorts control (wire:click.prevent="clearSorts",
    WITH .prevent -- confirmed distinct from the single-pill form) should
    remove every applied sort."""
    ensure_on_page(incoming_messages_page)
    incoming_messages_page.sort_by_received_at()
    incoming_messages_page.sort_by_created_at()
    incoming_messages_page.clear_all_sorts()
    assert not incoming_messages_page.is_sort_applied("received_at")
    assert not incoming_messages_page.is_sort_applied("created_at")


# ══════════════════════════════════════════════════════════════════════════════
# Bonus — Export CSV
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_bonus_export_csv(incoming_messages_page):
    """Clicking Export CSV (a plain <a> link to a dedicated /export route,
    not a wire:click button) should download a non-empty CSV file."""
    ensure_on_page(incoming_messages_page)
    result = incoming_messages_page.export_csv(timeout=30000)
    assert result is not None, "Export CSV should produce a downloaded file"
    assert result["file_size"] > 0, "Downloaded export file should not be empty"


# ══════════════════════════════════════════════════════════════════════════════
# Bonus — Pagination (real, multi-page: confirmed 2603 items / 261 pages)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_bonus_pagination_results_text(incoming_messages_page):
    """Pagination results text should reflect the real multi-page dataset
    (e.g. "Showing 1 to 10 of 2603 results")."""
    ensure_on_page(incoming_messages_page)
    text = incoming_messages_page.get_pagination_results_text()
    assert text, "Pagination results text should be present"
    assert "of" in text.lower()


@pytest.mark.regression
def test_bonus_pagination_next_and_goto_page(incoming_messages_page):
    """Clicking Next should advance to page 2; goto_page(1) (the same
    templated gotoPage button confirmed for pages 2-10) returns to page 1."""
    ensure_on_page(incoming_messages_page)
    first_page_values = incoming_messages_page.get_column_values("user_name")
    advanced = incoming_messages_page.click_next_page()
    assert advanced, "Clicking Next should succeed"
    second_page_values = incoming_messages_page.get_column_values("user_name")
    assert first_page_values != second_page_values, \
        "Row content should differ after advancing to the next page"
    back = incoming_messages_page.goto_page(1)
    assert back, "goto_page(1) should succeed"
    # NOT asserting is_previous_page_disabled() here -- and the standalone
    # "Previous disabled on first page" test was removed entirely (not just
    # skipped): its premise was never confirmed from a real DOM capture (see
    # is_previous_page_disabled()'s own comment), and a real check of this
    # page's live pagination showed only numbered gotoPage(N, ...) buttons
    # ("Go to page N") -- no Previous/Next-labeled control exists to be
    # disabled. click_next_page() and goto_page() above are the real,
    # confirmed mechanics this test cares about, and both already succeeded
    # by this point.
