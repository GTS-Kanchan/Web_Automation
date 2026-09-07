"""
WhatsApp Campaigns -- Automated Test Suite (Campaign CREATE page)
Path: /whatsapp/campaigns/create

Built from a 27-row manual QA checklist ("Campaign Creation page" section,
TC045-TC071) plus a genuine, pasted live-DOM capture of this exact page and
a second, separately pasted capture of its "Import Contacts" modal -- see
pages/whatsapp/whatsapp_campaign_create_page.py's module docstring for the
full list of confirmed DOM specifics driving every locator used here.

IMPORTANT -- what this suite deliberately does NOT cover, and why:
  - TC051 (custom media upload) and TC052 (location details): both are
    conditionally-rendered sections that only appear once a matching
    template is selected. Neither capture ever showed one selected, so
    their real markup was never captured. Documented `@pytest.mark.skip`s
    below explain exactly what capture would unblock each one.
  - TC053 (Template Preview data): a later, genuine capture confirmed the
    PANEL'S OWN content (whatsapp.template.view component: a "Preview"
    header, "Template ID: <id>" line, the rendered template body text in
    a chat-bubble, a timestamp, and an optional opt-in/opt-out indicator)
    -- see WhatsAppCampaignCreatePage's TEMPLATE_PREVIEW_* locators. What
    was NOT captured is the control that TRIGGERS opening it from the
    main form, so TC053 below still skips, but only on that one missing
    piece (open_template_preview() raises NotImplementedError until a
    capture of the real trigger element is supplied).
  - TC057 (Test Campaign modal contents): the button itself and its
    enabled/disabled wiring ARE confirmed, so TC057 exercises opening +
    closing the modal generically (via the already-confirmed shared
    livewire-ui-modal container and its confirmed Escape-key close
    handler), but does NOT assert on any field inside it -- that modal's
    internal DOM was never captured.
  - TC059's actual date/time picker fields (shown only after picking
    "Schedule for Later"): not captured. The radio button itself IS
    covered.
  - TC060-TC070 (the entire "Preview Campaign" modal and its 10 field
    checks): NO capture of this modal exists at all -- it requires
    successfully submitting a fully-populated campaign first. One
    consolidated skip covers this whole block.

Test Design Notes:
  - scope="module" -- one shared page object/browser page across the
    whole file, same convention as every other suite in this project.
  - The Sender ID / Template WireUI selects only expose their real option
    data via a base64 JSON blob the framework itself embeds
    (x-ref="json") -- decoded by the page object's _decoded_options()
    helper. The actual rendered <li> option rows are only ever visible
    once Alpine hydrates them client-side; since Playwright drives the
    real live page (not a static capture), those rows DO render for
    real at runtime and are matched by the generic, standard
    role="listitem" plus real confirmed label text -- never a guessed
    class or attribute.
  - Whether templates actually populate for a chosen Sender ID, and
    whether any template in this environment has zero variables / is
    otherwise immediately submittable, is NOT something either capture
    could confirm (no capture was ever taken past the "Sender ID chosen"
    state). Every test that depends on a template actually becoming
    selectable therefore calls `_ensure_template_selected()` first and
    gracefully `pytest.skip()`s with a specific reason if the environment
    doesn't cooperate, rather than assuming success.
  - The Campaign Name field's own snapshot data shows it is
    PRE-POPULATED with an auto-generated name on page load (not empty) --
    tests read the actual live value rather than assume "".
  - The "required" / "max 63 chars" validations (TC046/TC047) can only be
    observed by actually submitting the form (the Campaign Name field
    uses wire:model.defer, so nothing is validated live on blur), and the
    submit ("Preview Campaign") button is confirmed disabled until a
    template + contacts are in place. Both tests attempt the real flow
    when reachable and `pytest.skip()` with a clear reason otherwise --
    consistent with this project's "never guess, skip with a documented
    reason instead" rule.
  - TC071 (Cancel) navigates away from the create page, so it is the
    last test in this file.

Run:
    pytest tests/whatsapp/campaigns/test_whatsapp_campaign_create_flow.py -v
"""
import pytest

from pages.whatsapp.whatsapp_campaign_create_page import WhatsAppCampaignCreatePage


pytestmark = [pytest.mark.whatsapp, pytest.mark.campaign]


# ══════════════════════════════════════════════════════════════════════════════
# Module-scoped page
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def create_page(module_logged_in_page):
    p = WhatsAppCampaignCreatePage(module_logged_in_page)
    p.navigate()
    return p


# ══════════════════════════════════════════════════════════════════════════════
# Recovery / shared helpers
# ══════════════════════════════════════════════════════════════════════════════

def ensure_on_create_page(p: WhatsAppCampaignCreatePage):
    if not p.is_create_page():
        p.navigate()


def _ensure_template_selected(p: WhatsAppCampaignCreatePage, timeout_ms=8000):
    """Best-effort: pick a real Sender ID, wait for the Template select to
    become enabled with real options, then pick one. Returns True only if
    a template ends up genuinely selected; never fabricates success."""
    ensure_on_create_page(p)

    if p.page.locator(p.TEMPLATE_HIDDEN_INPUT).get_attribute("value"):
        return True

    senders = p.get_sender_id_options()
    if not senders:
        return False
    sender_label = senders[0].get("label")
    if not sender_label:
        return False
    try:
        p.select_sender_id(sender_label)
    except Exception:
        return False

    waited = 0
    step = 500
    while waited < timeout_ms:
        if p.is_template_select_enabled():
            break
        p.page.wait_for_timeout(step)
        waited += step
    if not p.is_template_select_enabled():
        return False

    templates = p.get_template_options()
    if not templates:
        return False
    template_label = templates[0].get("label")
    if not template_label:
        return False
    try:
        p.select_template(template_label)
    except Exception:
        return False
    return bool(p.page.locator(p.TEMPLATE_HIDDEN_INPUT).get_attribute("value"))


# ══════════════════════════════════════════════════════════════════════════════
# TC045 -- Create Campaign page loads
# ══════════════════════════════════════════════════════════════════════════════

def test_TC045_page_loads_successfully(create_page):
    ensure_on_create_page(create_page)
    assert create_page.is_create_page()
    assert create_page.get_page_header_text() == "Create WhatsApp Campaign"
    assert create_page.is_element_present(create_page.NAME_INPUT, timeout=10000)


# ══════════════════════════════════════════════════════════════════════════════
# TC046 -- Campaign name is required
# ══════════════════════════════════════════════════════════════════════════════

def test_TC046_campaign_name_required(create_page):
    ensure_on_create_page(create_page)
    create_page.clear_name()

    if not create_page.is_preview_campaign_enabled():
        pytest.skip(
            "Preview Campaign (the only control that triggers server-side "
            "validation, since the Name field uses wire:model.defer) is "
            "confirmed disabled until a template + contacts are selected. "
            "No capture exists of this page in a submittable state, so the "
            "required-name validation message cannot be exercised without "
            "guessing. Needs: a fresh capture with a template + contacts "
            "already selected, or manual QA confirmation of the exact "
            "error text."
        )

    create_page.click_preview_campaign()
    create_page.page.wait_for_timeout(1000)
    errors = create_page.get_validation_errors()
    assert errors, "Expected a validation error for an empty Campaign Name"


# ══════════════════════════════════════════════════════════════════════════════
# TC047 -- Campaign name maximum 63 characters
# ══════════════════════════════════════════════════════════════════════════════

def test_TC047_campaign_name_max_63_chars(create_page):
    ensure_on_create_page(create_page)
    long_name = "A" * 70
    create_page.set_name(long_name)

    if not create_page.is_preview_campaign_enabled():
        pytest.skip(
            "Same gating as TC046: Preview Campaign is disabled until a "
            "template + contacts are selected in this environment, so the "
            "63-character-limit validation message cannot be exercised "
            "without guessing. Needs a fresh capture in a submittable "
            "state."
        )

    create_page.click_preview_campaign()
    create_page.page.wait_for_timeout(1000)
    current_value = create_page.get_name_value()
    errors = create_page.get_validation_errors()
    assert len(current_value) <= 63 or errors, (
        "Expected either the Name field to be capped at 63 characters or "
        "a validation error for exceeding it"
    )


# ══════════════════════════════════════════════════════════════════════════════
# TC048 -- Sender ID searchable dropdown
# ══════════════════════════════════════════════════════════════════════════════

def test_TC048_sender_id_searchable_dropdown(create_page):
    ensure_on_create_page(create_page)

    options = create_page.get_sender_id_options()
    assert options, "Expected at least one real Sender ID option"

    target = options[0]["label"]
    search_term = target.split(" ")[0]
    create_page.search_sender_id(search_term)
    create_page.page.wait_for_timeout(500)

    create_page.select_sender_id(target)
    selected = create_page.get_selected_sender_id_text()
    assert selected, "Expected a Sender ID to be selected"
    assert selected in target or target in selected


# ══════════════════════════════════════════════════════════════════════════════
# TC049 -- Template searchable dropdown (enabled only after Sender ID)
# ══════════════════════════════════════════════════════════════════════════════

def test_TC049_template_dropdown_enables_after_sender(create_page):
    ensure_on_create_page(create_page)

    if not create_page.page.locator(create_page.SENDER_ID_HIDDEN_INPUT).get_attribute("value"):
        senders = create_page.get_sender_id_options()
        if not senders:
            pytest.skip("No real Sender ID options available in this environment")
        create_page.select_sender_id(senders[0]["label"])

    waited = 0
    while waited < 8000 and not create_page.is_template_select_enabled():
        create_page.page.wait_for_timeout(500)
        waited += 500

    if not create_page.is_template_select_enabled():
        pytest.skip(
            "Template select stayed aria-disabled after choosing a Sender "
            "ID in this environment -- no capture confirms what unlocks "
            "it beyond Sender ID selection (e.g. an approved WABA/template "
            "sync delay). Needs a fresh capture taken a few seconds after "
            "Sender ID selection."
        )

    templates = create_page.get_template_options()
    if not templates:
        pytest.skip(
            "Template select is enabled but has zero real options for "
            "this Sender ID in this environment -- cannot select a "
            "template without fabricating one."
        )

    create_page.select_template(templates[0]["label"])
    assert create_page.page.locator(create_page.TEMPLATE_HIDDEN_INPUT).get_attribute("value")


# ══════════════════════════════════════════════════════════════════════════════
# TC050 -- Skip Opt-out numbers checkbox
# ══════════════════════════════════════════════════════════════════════════════

def test_TC050_skip_opt_out_checkbox(create_page):
    ensure_on_create_page(create_page)
    was_checked = create_page.is_skip_opt_out_checked()

    create_page.toggle_skip_opt_out()
    assert create_page.is_skip_opt_out_checked() != was_checked

    create_page.toggle_skip_opt_out()
    assert create_page.is_skip_opt_out_checked() == was_checked


# ══════════════════════════════════════════════════════════════════════════════
# TC051 -- Upload custom media (NOT CAPTURED)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(
    reason=(
        "Media upload UI is a conditionally-rendered block that only "
        "appears once a MEDIA-type template is selected. Both captures "
        "of this page were taken with no template selected, so this "
        "section's real markup was never captured. Needs a fresh capture "
        "of this page with a media template selected."
    )
)
def test_TC051_upload_custom_media():
    pass


# ══════════════════════════════════════════════════════════════════════════════
# TC052 -- Location details fields (NOT CAPTURED)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(
    reason=(
        "Location fields are a conditionally-rendered block that only "
        "appears once a LOCATION-header template is selected -- same gap "
        "as TC051. Needs a fresh capture with a location-header template "
        "selected."
    )
)
def test_TC052_location_details_fields():
    pass


# ══════════════════════════════════════════════════════════════════════════════
# TC053 -- Preview template data (NOT CAPTURED)
# ══════════════════════════════════════════════════════════════════════════════

def test_TC053_template_preview_data(create_page):
    ensure_on_create_page(create_page)
    if not _ensure_template_selected(create_page):
        pytest.skip("Could not reach a state with a template selected (see TC049)")

    try:
        create_page.open_template_preview()
    except NotImplementedError:
        pytest.skip(
            "The Template Preview panel's own content IS confirmed from a "
            "genuine capture (see TEMPLATE_PREVIEW_* locators), but the "
            "control that opens it from this form was never captured, so "
            "open_template_preview() deliberately isn't implemented yet. "
            "Needs a capture of that trigger element (e.g. a Preview "
            "link/icon in the Template Configuration section)."
        )

    assert create_page.is_template_preview_open()
    assert "Template ID:" in create_page.get_template_preview_id_text()
    assert create_page.get_template_preview_body_text()
    create_page.close_template_preview()


# ══════════════════════════════════════════════════════════════════════════════
# TC054 -- Import Contacts: Copy Paste tab
# ══════════════════════════════════════════════════════════════════════════════

def test_TC054_import_contacts_copy_paste_tab(create_page):
    ensure_on_create_page(create_page)
    if not _ensure_template_selected(create_page):
        pytest.skip(
            "Import Contacts requires a template to be selected first "
            "(confirmed via the component's disableImportContactsBtn / "
            "'Select a template first' helper text), but no template "
            "could be genuinely selected in this environment."
        )
    if not create_page.is_import_contacts_enabled():
        pytest.skip("Import Contacts button did not become enabled after selecting a template")

    create_page.click_import_contacts()
    assert create_page.is_import_modal_open()

    create_page.switch_import_tab("copy_paste")
    create_page.fill_copy_paste_contacts("919876543210,919988776655")
    assert "919876543210" in create_page.page.locator(
        create_page.MODAL_CP_CONTACTS_TEXTAREA
    ).input_value()
    assert "50,000" in create_page.get_copy_paste_helper_text()

    create_page.click_modal_cancel()


# ══════════════════════════════════════════════════════════════════════════════
# TC055 -- Import Contacts: File Upload tab
# ══════════════════════════════════════════════════════════════════════════════

def test_TC055_import_contacts_file_upload_tab(create_page):
    ensure_on_create_page(create_page)
    if not _ensure_template_selected(create_page):
        pytest.skip("Could not reach a state where Import Contacts is enabled (see TC054)")
    if not create_page.is_import_contacts_enabled():
        pytest.skip("Import Contacts button is not enabled in this environment")

    create_page.click_import_contacts()
    assert create_page.is_import_modal_open()

    create_page.switch_import_tab("file_upload")
    assert create_page.is_element_present(create_page.MODAL_FU_FILE_INPUT, timeout=5000)
    assert create_page.is_element_present(create_page.MODAL_FU_DOWNLOAD_SAMPLE_BTN, timeout=5000)
    assert "Upload CSV" in create_page.get_file_upload_helper_text()

    create_page.click_modal_cancel()


# ══════════════════════════════════════════════════════════════════════════════
# TC056 -- Import Contacts: Contact Management tab (tags/segments)
# ══════════════════════════════════════════════════════════════════════════════

def test_TC056_import_contacts_contact_management_tab(create_page):
    ensure_on_create_page(create_page)
    if not _ensure_template_selected(create_page):
        pytest.skip("Could not reach a state where Import Contacts is enabled (see TC054)")
    if not create_page.is_import_contacts_enabled():
        pytest.skip("Import Contacts button is not enabled in this environment")

    create_page.click_import_contacts()
    assert create_page.is_import_modal_open()

    create_page.switch_import_tab("contact_tags")

    source_options = create_page.get_contact_import_source_options()
    assert {o.get("label") for o in source_options} >= {"Tags", "Segments"}
    assert create_page.get_selected_contact_import_source_text() == "Tags"

    tag_options = create_page.get_contact_tags_options()
    assert tag_options, "Expected at least one real contact tag"
    create_page.select_contact_tag(tag_options[0]["label"])

    create_page.click_modal_cancel()


# ══════════════════════════════════════════════════════════════════════════════
# TC057 -- Test Campaign (modal opens; internal fields NOT CAPTURED)
# ══════════════════════════════════════════════════════════════════════════════

def test_TC057_test_campaign_modal_opens(create_page):
    ensure_on_create_page(create_page)
    if not _ensure_template_selected(create_page):
        pytest.skip("Test Campaign requires a template to be selected; could not reach that state")
    if not create_page.is_test_campaign_enabled():
        pytest.skip("Test Campaign button is not enabled in this environment")

    create_page.click_test_campaign()
    assert create_page.is_element_visible(create_page.MODAL_CONTAINER, timeout=10000), (
        "Expected the shared livewire-ui-modal container to open"
    )
    # No assertions on the modal's internal fields: that DOM was never
    # captured. Close via the confirmed Escape-key handler
    # (x-on:keydown.escape.window="show && closeModalOnEscape()").
    create_page.page.keyboard.press("Escape")


# ══════════════════════════════════════════════════════════════════════════════
# TC058 -- Send Now radio
# ══════════════════════════════════════════════════════════════════════════════

def test_TC058_send_now_radio(create_page):
    ensure_on_create_page(create_page)
    create_page.select_send_now()
    assert create_page.get_send_type() == "now"


# ══════════════════════════════════════════════════════════════════════════════
# TC059 -- Schedule for Later radio (date/time picker fields NOT CAPTURED)
# ══════════════════════════════════════════════════════════════════════════════

def test_TC059_schedule_later_radio(create_page):
    ensure_on_create_page(create_page)
    create_page.select_schedule_later()
    assert create_page.get_send_type() == "schedule"
    # The date/time picker fields shown after selecting this option were
    # never captured -- not asserted on here, per this project's
    # never-guess rule.

    create_page.select_send_now()
    assert create_page.get_send_type() == "now"


# ══════════════════════════════════════════════════════════════════════════════
# TC060-TC070 -- Preview Campaign modal and its 10 field checks (NOT CAPTURED)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(
    reason=(
        "The entire Preview Campaign modal (opened by the main page's "
        "'Preview Campaign' submit button once a campaign is fully "
        "populated) was never captured -- reaching it requires a "
        "successful submit, which needs a template + contacts already in "
        "place, and no such capture exists. This single skip covers "
        "checklist rows TC060 (modal opens) through TC070 (message body "
        "field), i.e. all 10 field checks (Campaign Name, Sender ID, "
        "Template, Template ID, Product, Message Type, Recipients, "
        "Schedule, Opt-out Check, message body). Needs a fresh capture of "
        "this modal opened with a real, fully-populated campaign."
    )
)
def test_TC060_to_TC070_preview_campaign_modal():
    pass


# ══════════════════════════════════════════════════════════════════════════════
# TC071 -- Cancel button (last test: navigates away from the create page)
# ══════════════════════════════════════════════════════════════════════════════

def test_TC071_cancel_button(create_page):
    ensure_on_create_page(create_page)
    href = create_page.get_cancel_href()
    assert href and href.rstrip("/").endswith("/whatsapp/campaigns"), (
        "Confirmed real href: Cancel goes to the campaign LISTING page "
        "(/whatsapp/campaigns), not a 'campaign report' page -- a "
        "mismatch vs. some checklist wording, documented rather than "
        "silently 'corrected'."
    )

    create_page.click_cancel()
    create_page.page.wait_for_timeout(1000)
    assert "/whatsapp/campaigns" in create_page.get_current_url()
    assert "/whatsapp/campaigns/create" not in create_page.get_current_url()
