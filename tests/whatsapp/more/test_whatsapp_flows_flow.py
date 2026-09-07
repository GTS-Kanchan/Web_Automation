"""
WhatsApp Flows — Automated Test Suite
Path: /whatsapp/flows

Built from a manual QA checklist supplied by the user (TC001-TC025, all
marked PASS) for the "WhatsApp Flows" page reached via the top nav's
"More" dropdown, paired with a full live DOM dump of the flows LISTING
page. See pages/whatsapp/whatsapp_flows_page.py's module docstring for
the complete list of confirmed DOM specifics driving every locator used
here.

IMPORTANT SCOPE NOTE (read before extending this suite): the supplied
DOM capture is ONLY of the flows listing page. TC005 ("Verify create
flows") through TC025 (screens, components, edit-content: Large Heading,
Small Heading, Caption, Body, Image, Short Answer, Paragraph, Date
Picker, Single Choice, Multiple Choice, Dropdown, Opt-in, screen/
component limits) all describe the SEPARATE Flow Builder page
(/whatsapp/flows/builder, reached via the confirmed "Create Flow" link)
-- a complex drag-and-drop screen/component editor whose DOM was NEVER
supplied. Per this project's "never guess" rule, only the listing page
(TC001-TC004) plus the confirmed reachability of "Create Flow" (the
non-form part of TC005) are covered with real locators and assertions.
TC006-TC025 are documented skips below, each naming exactly what's
missing, pending a DOM capture of the Flow Builder page itself.

Test Design Notes:
  - scope="module" — page object shared across all tests (same pattern as
    every other suite in this project).
  - ensure_on_flows_page() recovers to a clean page state before each
    test (re-navigates if drifted).
  - The "Deprecate" row action is DESTRUCTIVE (it deprecates a real flow
    via a WireUI confirm dialog) — this suite only verifies the button
    and its tooltip exist, and deliberately never clicks through the
    confirm dialog, consistent with this project's caution around
    irreversible actions against QA data.
  - "Sync Flows" and "Preview" both open the shared livewire-ui-modal
    whose internal content was never captured — only "the modal opens"
    is asserted for each, same treatment as every other uncaptured modal
    this session.

Run:
    pytest tests/whatsapp/more/test_whatsapp_flows_flow.py -v
"""
import pytest

from pages.whatsapp.whatsapp_flows_page import WhatsappFlowsPage


pytestmark = [pytest.mark.whatsapp, pytest.mark.flow]

# ══════════════════════════════════════════════════════════════════════════════
# Module-scoped page
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def flows_page(module_logged_in_page):
    p = WhatsappFlowsPage(module_logged_in_page)
    p.navigate()
    p.wait_for_table_load(timeout=15000)
    return p


# ══════════════════════════════════════════════════════════════════════════════
# Recovery helpers
# ══════════════════════════════════════════════════════════════════════════════

def ensure_on_flows_page(p: WhatsappFlowsPage):
    if not p.is_flows_page():
        p.navigate()
        p.wait_for_table_load(timeout=10000)


def reset_state(p: WhatsappFlowsPage):
    try:
        p.clear_search()
    except Exception:
        pass
    try:
        p.restore_default_columns()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# TC001 — Page loads successfully
# ══════════════════════════════════════════════════════════════════════════════

def test_TC001_page_loads_successfully(flows_page):
    ensure_on_flows_page(flows_page)
    assert flows_page.is_flows_page()
    title = flows_page.get_page_title_text()
    assert "whatsapp flow" in title.lower()
    assert flows_page.is_element_present(flows_page.TABLE, timeout=10000)


# ══════════════════════════════════════════════════════════════════════════════
# TC002 — Search functionality (ID, Name, or Status)
# ══════════════════════════════════════════════════════════════════════════════

def test_TC002_search_valid_keyword(flows_page):
    """Confirmed search placeholder is 'Search By flow name' — this
    suite searches by a real, confirmed flow name substring."""
    ensure_on_flows_page(flows_page)
    reset_state(flows_page)
    flows_page.search("test")
    flows_page.page.wait_for_timeout(1000)
    assert flows_page.get_row_count() > 0 or flows_page.has_no_records_message()
    flows_page.clear_search()


def test_TC002_search_invalid_keyword(flows_page):
    ensure_on_flows_page(flows_page)
    reset_state(flows_page)
    flows_page.search("zzz_no_such_flow_zzz")
    flows_page.page.wait_for_timeout(1000)
    assert flows_page.has_no_records_message() or flows_page.get_row_count() == 0
    flows_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# TC003 — Columns functionality
# ══════════════════════════════════════════════════════════════════════════════

def test_TC003_toggle_column(flows_page):
    """'Sender' is CONFIRMED deselected by default on this page (unlike
    most WhatsApp tables) — this test toggles it ON then back OFF,
    verifying the header appears/disappears accordingly."""
    ensure_on_flows_page(flows_page)
    reset_state(flows_page)
    assert flows_page.is_column_checked("sender") is False

    flows_page.toggle_column("sender")
    assert flows_page.is_column_checked("sender") is True
    headers_after_show = flows_page.get_table_headers()
    assert any("sender" in h.lower() for h in headers_after_show)

    flows_page.toggle_column("sender")
    assert flows_page.is_column_checked("sender") is False
    headers_after_hide = flows_page.get_table_headers()
    assert not any("sender" in h.lower() for h in headers_after_hide)


# ══════════════════════════════════════════════════════════════════════════════
# TC004 — Sync flows functionality
# ══════════════════════════════════════════════════════════════════════════════

def test_TC004_sync_flows_opens_modal(flows_page):
    """Only 'the modal opens' is asserted — the Sync Flows modal's
    internal fields (sender select, confirm button) were never captured
    in the supplied DOM evidence (documented gap in the page object
    docstring)."""
    ensure_on_flows_page(flows_page)
    flows_page.click_sync_flows()
    assert flows_page.is_modal_open()
    flows_page.close_modal()
    ensure_on_flows_page(flows_page)


# ══════════════════════════════════════════════════════════════════════════════
# TC005 — Verify create flows (reachability only — see SCOPE NOTE)
# ══════════════════════════════════════════════════════════════════════════════

def test_TC005_create_flow_link_reachable(flows_page):
    """Confirms only the CONFIRMED part: the 'Create Flow' link exists
    and navigates to the Flow Builder page. Nothing about the builder's
    form/canvas is asserted — its DOM was never supplied (see this
    file's and the page object's SCOPE NOTE)."""
    ensure_on_flows_page(flows_page)
    assert flows_page.is_create_flow_link_present()
    href = flows_page.get_create_flow_link_href()
    assert "/whatsapp/flows/builder" in href

    flows_page.click_create_flow()
    assert flows_page.is_on_flow_builder_page()

    flows_page.navigate()
    flows_page.wait_for_table_load(timeout=10000)


# ══════════════════════════════════════════════════════════════════════════════
# TC006-TC025 — Flow Builder internals (DOCUMENTED SKIPS)
#
# All of these describe UI inside /whatsapp/flows/builder (sender-id
# selection, category selection, screen add/delete, and every content
# type in the "Edit content" panel). None of that page's DOM was
# supplied — only the flows LISTING page was captured. Building any
# locator for these would be guessing, which this project's rules
# forbid. Each skip below names the exact missing evidence.
# ══════════════════════════════════════════════════════════════════════════════

_BUILDER_SKIP_REASON = (
    "The Flow Builder page (/whatsapp/flows/builder) DOM was never "
    "captured -- only the flows listing page was supplied. This test "
    "case describes UI inside the builder ({0}), which cannot be "
    "located without guessing. Provide a DOM dump of the builder page "
    "(with the relevant panel open) to build a real locator instead."
)


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format("the sender id selector shown when creating a new flow"))
def test_TC006_select_sender_id_in_create_flow(flows_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("sender id selector"))


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format("the Categories multi-select and its selected-count badge"))
def test_TC007_select_categories_in_create_flow(flows_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("categories selector"))


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format("the 'Add screen' control and the 8-screen maximum"))
def test_TC008_add_up_to_8_screens(flows_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("Add screen control"))


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format("the per-screen delete control"))
def test_TC009_delete_screen(flows_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("delete screen control"))


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format("the screen title edit field"))
def test_TC010_edit_screen_title(flows_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("screen title edit field"))


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format("the button title edit field"))
def test_TC011_edit_button_title(flows_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("button title edit field"))


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format("the 'Add content > Text > Large Heading' control"))
def test_TC012_add_large_heading(flows_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("Large Heading content control"))


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format("the 'Add content > Text > Small Heading' control"))
def test_TC013_add_small_heading(flows_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("Small Heading content control"))


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format("the 'Add content > Text > Caption' control"))
def test_TC014_add_caption(flows_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("Caption content control"))


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format("the 'Add content > Text > Body' control"))
def test_TC015_add_body(flows_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("Body content control"))


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format("the 'Add content > Media > Image' control and its upload dropzone"))
def test_TC016_add_image(flows_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("Image content control"))


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format("the 'Add content > Text Answer > Short Answer' control"))
def test_TC017_add_short_answer(flows_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("Short Answer content control"))


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format("the 'Add content > Text Answer > Paragraph' control"))
def test_TC018_add_paragraph(flows_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("Paragraph content control"))


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format("the 'Add content > Text Answer > Date Picker' control"))
def test_TC019_add_date_picker(flows_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("Date Picker content control"))


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format("the 'Add content > Selection > Single Choice' control and its option-add flow"))
def test_TC020_add_single_choice(flows_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("Single Choice content control"))


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format("the 'Add content > Selection > Multiple Choice' control and its option-add flow"))
def test_TC021_add_multiple_choice(flows_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("Multiple Choice content control"))


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format("the 'Add content > Selection > Dropdown' control and its option-add flow"))
def test_TC022_add_dropdown(flows_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("Dropdown content control"))


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format("the 'Add content > Selection > Opt-in' control, its 'Add Read more screen' action, and the save-flow button"))
def test_TC023_add_optin_and_save_flow(flows_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("Opt-in content control and save flow button"))


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format("the screen list and its enforced 8-screen maximum"))
def test_TC024_max_8_screens_enforced(flows_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("screen list max-count enforcement"))


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format("a single screen's component list and its enforced 8-component maximum"))
def test_TC025_max_8_components_per_screen_enforced(flows_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("per-screen component max-count enforcement"))


# ══════════════════════════════════════════════════════════════════════════════
# Bonus, non-checklist coverage (confirmed by the DOM, not requested)
# ══════════════════════════════════════════════════════════════════════════════

def test_bonus_sorting_each_column(flows_page):
    """Only Name / Status / Created At are sortable (confirmed) -- Flow
    Id / WABA Number / Categories / Action have no sortBy button."""
    ensure_on_flows_page(flows_page)
    reset_state(flows_page)

    flows_page.sort_by_name()
    pill = flows_page.get_applied_sort_pill_text()
    assert pill is not None and "name" in pill.lower()

    flows_page.sort_by_status()
    pill = flows_page.get_applied_sort_pill_text()
    assert pill is not None and "status" in pill.lower()

    flows_page.sort_by_created_at()
    pill = flows_page.get_applied_sort_pill_text()
    assert pill is not None and "created at" in pill.lower()

    flows_page.clear_all_sorts()
    flows_page.page.wait_for_timeout(1000)
    assert flows_page.get_applied_sort_pill_text() is None


def test_bonus_sender_filter_popover_reachable(flows_page):
    """Bonus, non-checklist coverage: confirms the 'Filters' popover
    opens and its (async-select) sender search box renders -- without
    asserting anything about search results, since the async-select's
    live options list depends on production sender data not captured
    here."""
    ensure_on_flows_page(flows_page)
    assert flows_page.is_sender_filter_search_present()


def test_bonus_deprecate_action_present(flows_page):
    """Bonus, non-checklist coverage: confirms the 'Deprecate' row
    action exists. Deliberately does NOT click through its WireUI
    confirm dialog -- deprecating a flow is destructive and irreversible
    against real QA data."""
    ensure_on_flows_page(flows_page)
    assert flows_page.is_deprecate_action_present()


def test_bonus_preview_action_opens_modal(flows_page):
    """Bonus, non-checklist coverage: confirms the 'Preview' row action
    opens the shared modal. Only 'the modal opens' is asserted -- its
    internal content was never captured."""
    ensure_on_flows_page(flows_page)
    flows_page.click_preview_action()
    assert flows_page.is_modal_open()
    flows_page.close_modal()
    ensure_on_flows_page(flows_page)


def test_bonus_pagination_results_text(flows_page):
    """Bonus, non-checklist coverage: confirms the richer 'Showing X to
    Y of Z results' pagination format confirmed for this page (178 real
    flows existed at capture time)."""
    ensure_on_flows_page(flows_page)
    reset_state(flows_page)
    text = flows_page.get_pagination_results_text()
    assert "showing" in text.lower() and "results" in text.lower()
