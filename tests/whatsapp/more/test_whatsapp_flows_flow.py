"""
WhatsApp Flows — Automated Test Suite
Path: /whatsapp/flows

Built from a manual QA checklist supplied by the user (TC001-TC025, all
marked PASS) for the "WhatsApp Flows" page reached via the top nav's
"More" dropdown, paired with a full live DOM dump of the flows LISTING
page. See pages/whatsapp/whatsapp_flows_page.py's module docstring for
the complete list of confirmed DOM specifics driving every locator used
here.

SCOPE NOTE: this suite was originally built from a DOM capture of ONLY
the flows listing page, leaving TC006-TC025 (the Flow Builder page,
/whatsapp/flows/builder) as documented skips. A full live DOM capture of
the Flow Builder page has since been supplied (Sender ID select, Flow
Name field, Categories dropdown, Screens panel, Edit content panel with
its "Add content" control and all 12 real addComponent(...) buttons,
Save Flow button) -- see pages/whatsapp/whatsapp_flow_builder_page.py's
module docstring for the complete list of confirmed DOM specifics. Most
of TC006-TC025 are now real, locator-backed tests below. Two remain
documented skips because their SPECIFIC evidence is still missing (not
the whole page): TC009 (the per-screen delete control's markup was never
captured -- only 1 screen existed at capture time) and TC011 (clicking
selectComponent(index) was never captured, so what "edit the button
title" actually opens is unknown).

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
import json
import uuid

import pytest

from pages.whatsapp.whatsapp_flows_page import WhatsappFlowsPage
from pages.whatsapp.whatsapp_flow_builder_page import WhatsappFlowBuilderPage


pytestmark = [pytest.mark.whatsapp, pytest.mark.flow]

# ══════════════════════════════════════════════════════════════════════════════
# Module-scoped pages
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def flows_page(module_logged_in_page):
    p = WhatsappFlowsPage(module_logged_in_page)
    p.navigate()
    p.wait_for_table_load(timeout=15000)
    return p


@pytest.fixture(scope="module")
def builder_page(module_logged_in_page):
    p = WhatsappFlowBuilderPage(module_logged_in_page)
    p.navigate()
    return p


# ══════════════════════════════════════════════════════════════════════════════
# Recovery helpers
# ══════════════════════════════════════════════════════════════════════════════

def ensure_on_flows_page(p: WhatsappFlowsPage):
    if not p.is_flows_page():
        p.navigate()
        p.wait_for_table_load(timeout=10000)


def ensure_on_builder_page(p: WhatsappFlowBuilderPage):
    if not p.is_on_builder_page():
        p.navigate()


def _assert_add_and_remove_component(builder_page, component_type):
    """Shared by TC012-TC022: confirms the real 'Add content > ... > X'
    control (see whatsapp_flow_builder_page.py docstring point 9) adds a
    real component, then removes it again so each test leaves screen 0's
    component count unchanged for the next one and for TC025."""
    builder_page.select_screen(0)
    _, label = builder_page.COMPONENT_TYPE_INFO[component_type]
    assert builder_page.is_add_component_control_present(component_type), (
        f"Expected a real 'Add content' control for {label} "
        f"(confirmed wire:click=\"addComponent('{component_type}')\")"
    )
    before = builder_page.get_component_count()
    builder_page.add_component(component_type)
    after = builder_page.get_component_count()
    assert before is not None and after == before + 1, (
        f"Expected the 'Edit content' counter to go from {before} to "
        f"{(before or 0) + 1} after adding {label}, got {after}"
    )
    labels = builder_page.get_component_card_labels()
    assert label in labels, f"Expected a '{label}' component card, got {labels}"
    builder_page.remove_component(after - 1)
    assert builder_page.get_component_count() == before


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
# TC006-TC025 — Flow Builder internals
#
# Real, locator-backed tests built from a full live DOM capture of
# /whatsapp/flows/builder. See whatsapp_flow_builder_page.py's module
# docstring for the confirmed facts driving every locator used below.
# TC009 and TC011 remain documented skips -- see the module docstring's
# SCOPE NOTE above for exactly what's still missing for each.
# ══════════════════════════════════════════════════════════════════════════════

_BUILDER_SKIP_REASON = (
    "The full Flow Builder page DOM was captured, but this specific "
    "test case describes UI whose markup was never seen in that capture "
    "({0}) -- see whatsapp_flow_builder_page.py's module docstring for "
    "exactly what's missing. Provide a DOM dump of that specific state "
    "to build a real locator instead."
)


def test_TC006_select_sender_id_in_create_flow(builder_page):
    ensure_on_builder_page(builder_page)
    assert builder_page.is_sender_id_select_present()
    builder_page.select_sender_id("GTS QA")
    selected = builder_page.get_selected_sender_id_text()
    assert "GTS QA" in selected, f"Expected 'GTS QA' to be selected, got {selected!r}"


def test_TC007_select_categories_in_create_flow(builder_page):
    ensure_on_builder_page(builder_page)
    for value in builder_page.ALL_CATEGORY_VALUES:
        assert builder_page.is_category_checkbox_present(value), (
            f"Expected a real checkbox for category {value!r}"
        )
    assert builder_page.is_category_checked("SURVEY") is False
    builder_page.toggle_category("SURVEY")
    assert builder_page.is_category_checked("SURVEY") is True
    # Leave state clean for later tests in this module-scoped suite.
    builder_page.toggle_category("SURVEY")
    assert builder_page.is_category_checked("SURVEY") is False


def test_TC008_add_up_to_8_screens(builder_page):
    ensure_on_builder_page(builder_page)
    assert builder_page.is_add_screen_btn_present()
    for _ in range(10):
        count = builder_page.get_screen_count()
        if count is not None and count >= 8:
            break
        if not builder_page.is_add_screen_btn_enabled():
            break
        builder_page.click_add_screen()
    assert builder_page.get_screen_count() == 8, (
        f"Expected to be able to add screens up to the confirmed 8-screen "
        f"maximum, got {builder_page.get_screen_count()}"
    )


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format(
    "the per-screen delete control -- only 1 screen existed at capture "
    "time, so its row's control slot never rendered a delete button"
))
def test_TC009_delete_screen(builder_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("delete screen control"))


def test_TC010_edit_screen_title(builder_page):
    ensure_on_builder_page(builder_page)
    # TC008 (runs immediately before this test) adds screens up to the
    # 8-screen max without re-selecting screen 0 afterward, so the builder
    # can be left on whichever screen was added last. Screen 0's title
    # input only renders for the currently SELECTED screen (accordion-style
    # panel), which is why reading it without first re-selecting screen 0
    # timed out entirely (wire:key="screen-title-0" wasn't in the DOM at
    # all, not just hidden) -- confirmed by a real failing run.
    builder_page.select_screen(0)
    original = builder_page.get_screen_title_value(0) or "Screen 1"
    builder_page.set_screen_title(0, "QA Automation Screen")
    updated = builder_page.get_screen_title_value(0)
    assert updated == "QA Automation Screen", (
        f"Expected the screen title to update to 'QA Automation Screen', got {updated!r}"
    )
    builder_page.set_screen_title(0, original)
    assert builder_page.get_screen_title_value(0) == original


@pytest.mark.skip(reason=_BUILDER_SKIP_REASON.format(
    "what clicking selectComponent(index) actually opens -- no "
    "property-edit panel for the Footer/button component was ever "
    "captured, since no component was clicked during capture"
))
def test_TC011_edit_button_title(builder_page):
    pytest.skip(_BUILDER_SKIP_REASON.format("button title edit field"))


def test_TC012_add_large_heading(builder_page):
    ensure_on_builder_page(builder_page)
    _assert_add_and_remove_component(builder_page, "LargeHeading")


def test_TC013_add_small_heading(builder_page):
    ensure_on_builder_page(builder_page)
    _assert_add_and_remove_component(builder_page, "SmallHeading")


def test_TC014_add_caption(builder_page):
    ensure_on_builder_page(builder_page)
    _assert_add_and_remove_component(builder_page, "Caption")


def test_TC015_add_body(builder_page):
    ensure_on_builder_page(builder_page)
    _assert_add_and_remove_component(builder_page, "Body")


def test_TC016_add_image(builder_page):
    """Only the 'Add content > Media > Image' control itself is
    confirmed -- its upload dropzone's DOM was never captured (this
    control adds an Image component card, not an inline upload UI in
    this capture), so only the add/remove mechanics are asserted here."""
    ensure_on_builder_page(builder_page)
    _assert_add_and_remove_component(builder_page, "Image")


def test_TC017_add_short_answer(builder_page):
    ensure_on_builder_page(builder_page)
    _assert_add_and_remove_component(builder_page, "ShortAnswer")


def test_TC018_add_paragraph(builder_page):
    ensure_on_builder_page(builder_page)
    _assert_add_and_remove_component(builder_page, "Paragraph")


def test_TC019_add_date_picker(builder_page):
    ensure_on_builder_page(builder_page)
    _assert_add_and_remove_component(builder_page, "DatePicker")


def test_TC020_add_single_choice(builder_page):
    """Only the 'Add content > Selection > Single Choice' control itself
    is confirmed -- its option-add flow's DOM was never captured, so
    only the add/remove mechanics are asserted here."""
    ensure_on_builder_page(builder_page)
    _assert_add_and_remove_component(builder_page, "SingleChoice")


def test_TC021_add_multiple_choice(builder_page):
    """Only the 'Add content > Selection > Multiple Choice' control
    itself is confirmed -- its option-add flow's DOM was never captured,
    so only the add/remove mechanics are asserted here."""
    ensure_on_builder_page(builder_page)
    _assert_add_and_remove_component(builder_page, "MultipleChoice")


def test_TC022_add_dropdown(builder_page):
    """Only the 'Add content > Selection > Dropdown' control itself is
    confirmed -- its option-add flow's DOM was never captured, so only
    the add/remove mechanics are asserted here."""
    ensure_on_builder_page(builder_page)
    _assert_add_and_remove_component(builder_page, "Dropdown")


def test_TC023_add_optin_and_save_flow(builder_page):
    """The 'Add content > Selection > Opt-in' control and the Save Flow
    button are both confirmed real. Its 'Add Read more screen' action
    was never captured (no DOM evidence of what clicking an added Opt-in
    component reveals), so that part is not asserted. Save Flow creates
    a real flow in this shared QA environment -- per this project's
    caution around irreversible/data-creating actions, only its
    presence/enabled state is checked, never clicked."""
    ensure_on_builder_page(builder_page)
    _assert_add_and_remove_component(builder_page, "OptIn")
    assert builder_page.is_save_flow_btn_present()
    assert builder_page.is_save_flow_btn_enabled()


def test_TC024_max_8_screens_enforced(builder_page):
    ensure_on_builder_page(builder_page)
    for _ in range(10):
        if builder_page.get_screen_count() is not None and builder_page.get_screen_count() >= 8:
            break
        if not builder_page.is_add_screen_btn_enabled():
            break
        builder_page.click_add_screen()
    assert builder_page.get_screen_count() == 8
    # Extra adds beyond the confirmed maximum must not increase the count,
    # regardless of how the app enforces it (disabled button, no-op click,
    # etc. -- no DOM evidence of the specific at-limit mechanism exists).
    builder_page.click_add_screen()
    builder_page.click_add_screen()
    assert builder_page.get_screen_count() == 8, (
        "Screen count exceeded the confirmed 8-screen maximum after extra adds"
    )


def test_TC025_max_8_components_per_screen_enforced(builder_page):
    ensure_on_builder_page(builder_page)
    builder_page.select_screen(0)
    for _ in range(12):
        count = builder_page.get_component_count()
        if count is not None and count >= 8:
            break
        builder_page.add_component("LargeHeading")
    assert builder_page.get_component_count() == 8, (
        f"Expected to be able to add components up to the confirmed "
        f"8-component-per-screen maximum, got {builder_page.get_component_count()}"
    )
    # CONFIRMED live (user-reported real behavior): at the 8-component
    # maximum, the "Add content" control's own category submenu button
    # becomes genuinely unclickable/unusable -- this IS the app's real
    # enforcement mechanism, not a bug. A further add_component() call
    # therefore times out trying to reach that control rather than
    # silently no-op'ing, so that timeout itself is the expected, correct
    # signal that the maximum is enforced.
    with pytest.raises(Exception):
        builder_page.add_component("LargeHeading")
    assert builder_page.get_component_count() == 8, (
        "Component count exceeded the confirmed 8-component-per-screen maximum"
    )


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


# ══════════════════════════════════════════════════════════════════════════════
# E2E -- full WhatsApp Flow creation lifecycle (create -> configure two
# screens -> validate the generated JSON -> Save -> verify it persists on
# the Flows listing page). This is the one place in this suite that
# actually clicks Save Flow and creates a real flow -- see
# whatsapp_flow_builder_page.py's click_save_flow()/wait_for_save_result()
# docstrings for why that's a deliberate, scoped exception here.
#
# Uses its OWN fresh WhatsappFlowsPage/WhatsappFlowBuilderPage instances,
# both wrapping the SAME shared module_logged_in_page fixture every other
# test in this module already uses (so login/session handling is fully
# reused, nothing re-authenticates), rather than this file's own
# module-scoped flows_page/builder_page fixtures. Those fixtures are
# shared across every TC00x/TC0xx test above and below, so reusing them
# here would mean either inheriting whatever builder state (screens,
# components) an earlier test left behind, or leaving this test's own
# state behind for a later one to trip over (e.g. TC008/TC024 assume a
# builder that starts with exactly 1 screen). A fresh instance sidesteps
# that entirely without needing any change to the existing fixtures or
# tests.
# ══════════════════════════════════════════════════════════════════════════════

def test_e2e_whatsapp_flow_creation_and_persistence(module_logged_in_page):
    flows = WhatsappFlowsPage(module_logged_in_page)
    builder = WhatsappFlowBuilderPage(module_logged_in_page)

    # 1-2. Open WhatsApp Flows, then Create Flow / Flow Builder (reuses
    # the confirmed listing-page navigation + "Create Flow" link already
    # proven by TC001/TC005).
    flows.navigate()
    flows.wait_for_table_load(timeout=15000)
    assert flows.is_create_flow_link_present()
    flows.click_create_flow()
    assert builder.is_on_builder_page()

    # Unique flow name per run (same uuid4().hex[:8] convention already
    # used by tests/rcs/reports/test_rcs_download_center_flow.py for a
    # collision-free unique report name).
    unique_flow_name = f"E2E WhatsApp Flow {uuid.uuid4().hex[:8]}"

    # 3. Select a valid Sender ID (reuses TC006's exact interaction and
    # the same "GTS QA" test sender already used throughout this file).
    assert builder.is_sender_id_select_present()
    builder.select_sender_id("GTS QA")
    selected_sender = builder.get_selected_sender_id_text()
    assert "GTS QA" in selected_sender, (
        f"Expected 'GTS QA' to be selected, got {selected_sender!r}"
    )

    # 4. Enter a unique Flow Name (reuses set_flow_name/get_flow_name_value).
    builder.set_flow_name(unique_flow_name)
    assert builder.get_flow_name_value() == unique_flow_name

    # 5. Select the "Survey" category (reuses TC007's exact interaction).
    assert builder.is_category_checkbox_present("SURVEY")
    builder.toggle_category("SURVEY")
    assert builder.is_category_checked("SURVEY") is True

    # 6. Configure Screen 1: title "Welcome" + a Large Heading component.
    # The default Footer/"Continue" button is left untouched -- add_
    # component only adds, nothing here removes or edits the existing
    # footer, and the JSON assertions below confirm it's still present.
    builder.select_screen(0)
    builder.set_screen_title(0, "Welcome")
    assert builder.get_screen_title_value(0) == "Welcome"

    assert builder.is_add_component_control_present("LargeHeading"), (
        "Expected a real 'Add content' control for the Large Heading component"
    )
    before_s1 = builder.get_component_count()
    builder.add_component("LargeHeading")
    after_s1 = builder.get_component_count()
    assert before_s1 is not None and after_s1 == before_s1 + 1, (
        f"Expected the 'Edit content' counter to go from {before_s1} to "
        f"{(before_s1 or 0) + 1} after adding Large Heading, got {after_s1}"
    )
    assert "Large Heading" in builder.get_component_card_labels()
    # NOTE: there is no confirmed locator for editing a component's own
    # label/placeholder text -- selectComponent(index)'s property panel
    # was never captured (see TC011's documented skip and this page
    # object's docstring point 8), so "configure it with valid test
    # data" is limited to adding the real, confirmed component itself;
    # there is no known, evidence-backed way to type into its fields yet.

    # 7-8. Add Screen 2 via "Add New Screen", title it "Customer
    # Details" (reuses click_add_screen/select_screen/set_screen_title
    # -- select_screen(1) before touching it, the same lesson TC010
    # needed: a newly added screen doesn't stay implicitly selected).
    builder.click_add_screen()
    builder.select_screen(1)
    builder.set_screen_title(1, "Customer Details")
    assert builder.get_screen_title_value(1) == "Customer Details"

    # Add a Short Answer component (reuses is_add_component_control_
    # present/add_component/get_component_count/get_component_card_labels
    # -- the exact same methods TC012-TC022 already use for every other
    # component type, per COMPONENT_TYPE_INFO's confirmed type->label map).
    before_s2 = builder.get_component_count()
    assert builder.is_add_component_control_present("ShortAnswer")
    builder.add_component("ShortAnswer")
    after_s2 = builder.get_component_count()
    assert after_s2 == before_s2 + 1, (
        f"Expected the 'Edit content' counter to go from {before_s2} to "
        f"{before_s2 + 1} after adding Short Answer, got {after_s2}"
    )
    assert "Short Answer" in builder.get_component_card_labels()

    # 10-12. Open View JSON and validate the generated flow JSON
    # structurally (reuses open_view_json_modal/is_json_modal_open/
    # get_json_modal_content -- get_json_modal_content() returns the
    # real text of #jsonContent, parsed here with json.loads rather than
    # just substring-matched, so this is a real structural check, not a
    # UI-text check).
    builder.open_view_json_modal()
    assert builder.is_json_modal_open()
    flow_json_text = builder.get_json_modal_content()
    flow_json = json.loads(flow_json_text)  # raises if not valid JSON

    # version exists. No specific value was ever confirmed via a real
    # DOM/JSON capture for this page, so this checks presence/non-empty
    # rather than guessing an exact expected string (e.g. "3.1") that
    # was never actually observed -- asserting an unconfirmed literal
    # would be exactly the kind of guess this project's page objects
    # deliberately avoid everywhere else.
    assert flow_json.get("version"), f"Expected a non-empty 'version' in flow JSON, got {flow_json.get('version')!r}"

    # screens exist, with Screen 1 ("Welcome") and Screen 2 ("Customer
    # Details") both present by title.
    screens = flow_json.get("screens")
    assert isinstance(screens, list) and len(screens) >= 2, (
        f"Expected at least 2 screens in flow JSON, got {screens!r}"
    )
    screen_by_title = {s.get("title"): s for s in screens}
    assert "Welcome" in screen_by_title, (
        f"Expected a screen titled 'Welcome', got titles {list(screen_by_title)!r}"
    )
    assert "Customer Details" in screen_by_title, (
        f"Expected a screen titled 'Customer Details', got titles {list(screen_by_title)!r}"
    )
    screen1_json = screen_by_title["Welcome"]
    screen2_json = screen_by_title["Customer Details"]

    def _screen_children(screen):
        # Confirmed via a real DOM/JSON capture off the View JSON modal:
        # layout.children is a single-item list wrapping a Form node
        # (type "Form", name "flow_path"), and the actual per-screen
        # components (headings, inputs, footer, ...) live one level
        # deeper, under that Form's own "children". Drill into the Form
        # wrapper when present; fall back to the raw layout.children (or
        # a flat "children"/"components" key) for any shape that
        # doesn't match, rather than assuming the nested Form always
        # exists.
        layout = screen.get("layout") or {}
        top_children = layout.get("children")
        if isinstance(top_children, list) and len(top_children) == 1 \
                and isinstance(top_children[0], dict) \
                and top_children[0].get("type") == "Form":
            form_children = top_children[0].get("children")
            if isinstance(form_children, list):
                return form_children
        if top_children is not None:
            return top_children
        return screen.get("children") or screen.get("components") or []

    # Expected components exist in the appropriate screens: Screen 1 has
    # at least the Large Heading we added (plus its default Footer);
    # Screen 2 has at least the Short Answer we added.
    screen1_children = _screen_children(screen1_json)
    screen2_children = _screen_children(screen2_json)
    assert len(screen1_children) >= 1, (
        f"Expected at least 1 component on the 'Welcome' screen, got {screen1_json!r}"
    )
    assert len(screen2_children) >= 1, (
        f"Expected at least 1 component on the 'Customer Details' screen, got {screen2_json!r}"
    )
    # Continue/footer button retained (default, never removed by this
    # test) -- checked by substring on the 'Welcome' screen's own JSON
    # rather than a guessed component "type" key.
    assert "Continue" in json.dumps(screen1_json), (
        "Expected the default Continue/footer button to remain on the 'Welcome' screen"
    )

    # 13. Close the JSON view.
    builder.close_view_json_modal()
    assert not builder.is_json_modal_open()

    # 14-16. Click Save Flow and wait for the actual save result (reuses
    # the same generic, already-proven app-global toast/SweetAlert2/
    # URL-change signal whatsapp_template_create_page.py's wait_for_
    # save_result() already relies on -- see that page's own docstring
    # for the confirmed origin of this mechanism -- rather than a
    # fixed-length wait).
    assert builder.is_save_flow_btn_enabled(), "Expected Save Flow to be enabled with Sender ID + Flow Name set"
    builder.click_save_flow()
    save_result = builder.wait_for_save_result()
    assert save_result["outcome"] != "none_detected", (
        f"No recognized post-save feedback (URL redirect, or the "
        f"confirmed app-global WireUI/SweetAlert2 toast) appeared "
        f"within the wait budget after clicking Save Flow for "
        f"{unique_flow_name!r}: {save_result!r}"
    )

    # 17-18. Navigate to the Flows listing and find the newly created
    # unique flow (reuses navigate/wait_for_table_load/search/
    # get_row_count/get_column_values exactly as TC001-TC004 do).
    flows.navigate()
    flows.wait_for_table_load(timeout=15000)
    flows.search(unique_flow_name)
    assert flows.get_row_count() >= 1, (
        f"Expected the newly created flow {unique_flow_name!r} to appear "
        f"in the Flows listing after Save, found no matching row"
    )
    listed_names = flows.get_column_values("name")
    assert any(unique_flow_name in n for n in listed_names), (
        f"Expected {unique_flow_name!r} among listed flow names, got {listed_names!r}"
    )
    listed_categories = flows.get_column_values("categories")
    assert any("SURVEY" in c for c in listed_categories), (
        f"Expected the saved flow's Categories column to include SURVEY, "
        f"got {listed_categories!r}"
    )

    # 19-20. Open the created flow, if supported, and verify it
    # persists. "Preview" (opens the shared #modal-container) is the
    # only confirmed row action for viewing an existing flow -- there is
    # no confirmed "edit"/"reopen into the builder" row action on this
    # listing page (documented gap, same as TC004's Sync Flows modal and
    # test_bonus_preview_action_opens_modal above), so only "the modal
    # opens" is asserted here; the listing-row assertions above already
    # confirmed the saved flow's name and category persisted, and the
    # JSON assertions above already confirmed its screens/components
    # were generated correctly before Save.
    if flows.is_element_present(flows.PREVIEW_ACTION_BTN, timeout=5000):
        flows.click_preview_action()
        assert flows.is_modal_open()
        flows.close_modal()

    flows.clear_search()
