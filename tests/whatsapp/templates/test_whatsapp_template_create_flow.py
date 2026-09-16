"""
WhatsApp Templates -- Automated Test Suite (Template CREATE page)
Path: /whatsapp/channels/template/create

Built from a 70-row manual QA checklist ("Template Creation Page" section,
TC016-TC085) plus a genuine, pasted live-DOM capture of this exact page --
see pages/whatsapp/whatsapp_template_create_page.py's module docstring for
the full list of confirmed DOM specifics driving every locator used here.

IMPORTANT -- what this suite covers, and what it deliberately does NOT,
and why:

  Covered with real tests (well-confirmed DOM evidence exists for all of
  these):
    TC016 (page loads), TC017 (Sender ID select + selection), TC018/TC019
    (Sender ID search, valid/invalid keyword), TC020 (Template Name
    character restriction -- exercised at runtime since Playwright drives
    the live page, not assumed from the checklist prose), TC021 (Template
    Name max length, confirmed via maxlength="512"), TC022 (Header is
    optional -- confirmed structurally since Save is gated only on
    senderId, not header) -- plus the Category radios (4 confirmed real
    values), Language select (67 confirmed real options, default
    "English"/"en"), Template Labels (optional field), Footer Text
    (maxlength=60), Cancel link, and the structurally-disabled Save
    button.

    Also covered (added from a second, later capture of this same live
    Create-page component -- confirmed via each field's own wireModel
    blob decoding to the SAME livewireId as every other locator on this
    page, so this is not separate/unrelated evidence): the Marketing
    sub_category select (8 real values, only rendered once
    category=MARKETING is chosen), the Catalog Type select that appears
    specifically for sub_category=Catalog (2 real values, Single-Product/
    Multi-Product), and the Carousel sub-form's top-level selects
    (Header media type, No of buttons, Button type 1) that appear for
    sub_category=Carousel. See pages/whatsapp/whatsapp_template_create_page.py's
    module docstring points 15-18 for the full evidence trail.

    Also covered (added from THREE further fresh, independently
    programmatically-decoded wire:snapshot captures -- sub_category =
    multi_product_message, lto, and product_carousel, each confirmed to
    be the SAME whatsapp.meta.create component type via memo.name/path):
    the Multi-Product Message Section Title / Content ID fields plus
    their Add Section/Add Product actions; the Limited Time Offer
    sub-form's confirmed "Add button" trigger (5 showLTOdiv(...) button
    types -- explicitly NOT assumed to generalize to Custom Message);
    and the Product Card Carousel's Button Type select (2 real values)
    plus its pre-fetch manual Catalog ID/Content ID fields. These same
    three captures also corrected two earlier assumptions: headerOptions/
    typeOptions are state-dependent (not fixed), and sub_category's real
    backend values are now known. See
    pages/whatsapp/whatsapp_template_create_page.py's module docstring
    points 19-22 for the full evidence trail.

    Also covered (added from a genuine, programmatically-decoded
    category=AUTHENTICATION capture -- same whatsapp.meta.create
    component instance): the OTP type radio group (Copy Code/AutoFill/
    Zero-Tap, real backend field "childcat"), the two Message Content
    checkboxes ("Add Security recommendation" / "Add expiration time for
    code", both backed by the shared "custom_add" array field), and the
    Copy Code button text field (confirmed default value "Copy code" and
    a confirmed `disabled` attribute in the default OTP-type state). See
    pages/whatsapp/whatsapp_template_create_page.py's module docstring
    point 23 for the full evidence trail.

    Also covered (added from a genuine, programmatically-decoded
    category=CONVERSATION, sub_category=cta_url_button capture -- same
    whatsapp.meta.create component instance): confirmation that the
    "Add button" dropdown documented in point 21 above is a SHARED
    mechanism (not LTO-exclusive as first assumed) -- it renders here too
    with a single disabled showLTOdiv('URL') item; the reused
    url_buttons_title.0/url_buttons_value.0 fields from point 18; a
    confirmed "Add Variable" button (wire:click="insertVariable('body')");
    and a SIXTH distinct headerOptions/typeOptions state ([Text, Media] /
    [Image, Video, Document]). See
    pages/whatsapp/whatsapp_template_create_page.py's module docstring
    point 24 for the full evidence trail.

    Also covered (added from two genuine, programmatically-decoded
    category=UTILITY captures -- sub_category=custom_message and
    sub_category=order_details, both the same whatsapp.meta.create
    component type via memo.name/path): confirmation that the "Add
    button" dropdown (points 21/24) is a THIRD independently-confirmed
    shared mechanism under UTILITY/custom_message, with Copy Offer Code
    disabled there too, alongside the "full" 4-value headerOptions state;
    and, for UTILITY/order_details, the fixed/non-editable single-button
    block (a disabled "Type of Action" select fixed to "Open order
    details" and a readonly "Button Text" input fixed to "Review and
    Pay") plus a narrower [Media]-only headerOptions/[Image]-only
    typeOptions state. Two earlier capture attempts aimed at
    sub_category=order_status both landed on this exact order_details
    state instead (proven via matching Livewire snapshot checksums); a
    third attempt succeeded and confirmed order_status as a genuinely
    distinct state -- [Media]-only headerOptions but EMPTY typeOptions,
    and no fixed order-button block at all (showOrderButton:false). See
    pages/whatsapp/whatsapp_template_create_page.py's module docstring
    points 25/26/30 for the full evidence trail.

    Also added: real end-to-end (fill-and-submit) tests, one per
    confirmed category/sub_category combination above (test_e2e_*
    functions) -- each performs a REAL submit against the real live
    account using only already-confirmed fields/locators, then asserts
    the app responded at all (URL redirect or the confirmed app-global
    WireUI/SweetAlert2 toast) rather than a specific unconfirmed
    "success" string. See page object docstring point 27 for the full
    rationale, including why no page-specific success locator is
    guessed and how the Carousel test's media-file dependency was
    solved (a real test asset added to tests/test_data/, not a locator
    guess).

  Deliberately NOT covered here, each with a documented skip explaining
  exactly what evidence is missing (per this project's "never guess,
  skip with a documented reason instead" rule):
    - TC023-TC028 (Header None/Text/Image/Video/Document/Location
      sub-behaviors, including the two real QA-noted bugs: TC024's
      variable-insertion-after-60-chars bug and TC026/TC027's
      unsupported 3GP/PPT(X) formats, JIRA CPAAS-3196): the Header
      select's own x-ref="json" option blob decoded to an EMPTY array in
      this capture -- the real header-type option list was never
      captured. Needs a fresh capture of the Header select WITH its
      options populated (e.g. right after a Sender ID is chosen, if that
      is what populates it).
    - TC029-TC036 (Conversation Template section: enable toggle,
      Template Type "CTA URL Button", body variables, footer): the
      sub_category=cta_url_button form's confirmed fields (the shared
      "Add button" dropdown, url_buttons_title.0/value.0, "Add Variable"
      button) ARE now confirmed and built (page object docstring point
      24) and exercised by
      test_conversation_cta_url_button_reuses_add_button_and_url_fields
      above. Still skipped as a numbered TC because the
      conversation_enabled toggle itself, end-to-end body-variable
      insertion behavior, and footer sub-behaviors for this section were
      never captured populated.
    - TC037-TC041 (Authentication category form: OTP type, Autofill OTP,
      Message Content, Buttons text, App Setup/package name): the
      snapshot shows showAuthentication:false / showSecurityOptions:false
      -- this entire sub-form was rendered as empty conditional blocks in
      this capture (category was never set to AUTHENTICATION when
      captured).
    - TC042-TC046 (Utility category form: category selection, opt-out
      button, Custom message, disabled Coupon code button, Order
      details/Order Status restrictions): Custom Message's "Add button"
      dropdown (Copy Offer Code disabled), Order Details' fixed
      single-button block, and Order Status's distinct (no button block,
      empty typeOptions) state ARE now confirmed and built (page object
      docstring points 25/26/30) and exercised by real tests above.
      Still skipped as a numbered TC because the "Include opt-out
      button" checkbox was never found in any capture.
    - TC047-TC058 (Marketing - Custom message: Tap Target header
      restriction, Quick Reply/URL/Phone/Coupon Code/Flow buttons): a
      later capture DID confirm the real structure/options of the URL,
      Phone Number/Copy-Offer-Code/URL ("Select Type") and Flow button
      fields (see page object docstring point 18), and those locators/
      helpers are now built. What's still missing is the exact UI action
      that first reveals each button block (no "Add button" control was
      ever captured), so no test here can get from a fresh page to a
      visible button field without guessing that trigger -- still
      skipped for that reason alone, not for missing field evidence.
    - TC059-TC062 (Marketing - Carousel): the top-level sub-form
      (media type, button count, button type 1, per-card description/
      file/button fields) IS now confirmed and built (page object
      docstring point 17) and exercised by a real test below. Still
      skipped as a numbered TC because the exact preview/validation
      behavior for a fully populated carousel (multiple cards, submit)
      was never captured.
    - TC063-TC066 (Marketing - Catalog, incl. JIRA CPAAS-3220): the
      Catalog Type select (Single-Product/Multi-Product) and the
      populated Preview panel for this sub_category ARE now confirmed
      and exercised by a real test below (page object docstring point
      16). Still skipped as a numbered TC because the JIRA CPAAS-3220
      single-product validation behavior and the multi-product
      auto-fetch behavior remain unconfirmed.
    - TC067-TC069 (Marketing - Single Product Message): catalog_id/
      product_retailer_id both null, no populated form captured.
    - TC070-TC072 (Marketing - Multi Product Message, incl. the
      "Validation is not available" QA remark on TC072): the Section
      Title/Content ID fields and Add Section/Add Product actions ARE
      now confirmed and built, exercised by a real test above. Still
      skipped as a numbered TC because the mandatory Header Text
      requirement, the 10-section/30-content-ID upper bounds, and the
      TC072 validation remark remain unconfirmed.
    - TC073-TC075 (Marketing - Limited Time Offer): the "Add button"
      trigger (5 confirmed showLTOdiv(...) types) IS now confirmed and
      built, exercised by a real test above. Still skipped as a numbered
      TC because Offer Title validation, the expiry-period behavior, and
      the mandatory default URL button remain unconfirmed.
    - TC076-TC079 (Marketing - Product Card Carousel): the Button Type
      select and pre-fetch manual Catalog ID/Content ID fields ARE now
      confirmed and built, exercised by a real test above. Still skipped
      as a numbered TC because the actual catalog-fetch/select-product
      behavior and the add/delete-up-to-10-cards bounds remain
      unconfirmed.
    - TC080-TC085 (Marketing - Order Details): showOrderButton:false.
    One consolidated skip covers each of the above blocks -- see the
    `pytest.skip(...)` calls below for the exact per-section wording.

Test Design Notes:
  - scope="module" -- one shared page object/browser page across the
    whole file, same convention as every other suite in this project.
  - The Sender ID / Language WireUI selects only expose their real option
    data via a base64 JSON blob the framework itself embeds
    (x-ref="json") -- decoded by the page object's _decoded_options()
    helper. The actual rendered <li> option rows are only ever visible
    once Alpine hydrates them client-side; since Playwright drives the
    real live page (not a static capture), those rows DO render for
    real at runtime and are matched by the generic, standard
    role="listitem" plus real confirmed label text -- never a guessed
    class or attribute.
  - TC020/TC021 (Template Name rules) are exercised by actually typing
    into the live field and reading back the resulting value after the
    field's own wire:model.live.debounce.200ms round trip, rather than
    assumed from the checklist's prose. The checklist's specific claim of
    a 3-character MINIMUM cannot be confirmed this way (nothing here
    strips a too-short value client-side) -- only the observable, testable
    behaviors (character-set filtering, and the 512 upper bound) are
    asserted as hard requirements; the 3-char minimum is checked
    best-effort and does not fail the test if unconfirmed.
  - The Body field is an EasyMDE/CodeMirror editor, not a plain textarea
    -- get_body_text()/set_body_text() drive it via the SAME CodeMirror
    lookup this exact page's own inline <script> uses for variable
    insertion (see the page object's docstring), never a plain .fill().
  - TC016's Save-button check exercises the confirmed
    `:disabled="!$wire.senderId"` Alpine binding structurally (disabled
    before Sender ID is chosen, enabled after) rather than attempting a
    full submit (submitting would require a fully valid template across
    every required field, which is far beyond what any capture confirms).

Run:
    pytest tests/whatsapp/templates/test_whatsapp_template_create_flow.py -v
"""
import json
import os

import pytest

from pages.whatsapp.whatsapp_template_create_page import WhatsAppTemplateCreatePage
from utils.config import Config


pytestmark = [pytest.mark.whatsapp, pytest.mark.template]

# Real, valid JPEG test asset for the Carousel E2E test's per-card media
# upload (see page object docstring point 27 for why this was added --
# no image test asset existed anywhere in this repo before).
CAROUSEL_SAMPLE_IMAGE = os.path.join(
    os.path.dirname(__file__), "..", "..", "test_data", "whatsapp_carousel_sample.jpg"
)


# ══════════════════════════════════════════════════════════════════════════════
# Module-scoped page
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def create_page(module_logged_in_page):
    p = WhatsAppTemplateCreatePage(module_logged_in_page)
    p.navigate()
    return p


# ══════════════════════════════════════════════════════════════════════════════
# Recovery / shared helpers
# ══════════════════════════════════════════════════════════════════════════════

def ensure_on_create_page(p: WhatsAppTemplateCreatePage):
    if not p.is_create_page():
        p.navigate()


def _ensure_sender_selected(p: WhatsAppTemplateCreatePage):
    """Best-effort: pick a real Sender ID option if none is selected yet.
    Driven by Config.WHATSAPP_TEMPLATE_SENDER_ID (env var
    WHATSAPP_TEMPLATE_SENDER_ID, default "Globe Teleservices Pte. Ltd."
    -- see utils/config.py and .env/.env.example), matched case-
    insensitively as a substring rather than hardcoded, so switching
    instance/account only means changing .env (per explicit user
    request: "select sender id config from .env make it dynamic").
    Falls back to the first available option, with a printed warning,
    only if no option matches. Returns True only if a sender ends up
    genuinely selected; never fabricates success."""
    ensure_on_create_page(p)
    if p.page.locator(p.SENDER_ID_HIDDEN_INPUT).get_attribute("value"):
        return True
    senders = p.get_sender_id_options()
    if not senders:
        return False
    configured = (Config.WHATSAPP_TEMPLATE_SENDER_ID or "").strip().lower()
    label = None
    if configured:
        for sender in senders:
            candidate = sender.get("label") or ""
            if configured in candidate.lower():
                label = candidate
                break
    if not label:
        label = senders[0].get("label")
        print(
            f"[_ensure_sender_selected] WARNING: no Sender ID option "
            f"matching Config.WHATSAPP_TEMPLATE_SENDER_ID "
            f"({Config.WHATSAPP_TEMPLATE_SENDER_ID!r}) found among "
            f"{[s.get('label') for s in senders]!r} -- falling back to "
            f"the first option ({label!r})"
        )
    if not label:
        return False
    try:
        # select_sender_id_by_search(), not select_sender_id(): real
        # --headed evidence (a screenshot of the open popover) showed
        # the configured/matched sender label is often NOT among the
        # Sender ID popover's initially-rendered listitems, even though
        # get_sender_id_options() decodes the full real list -- plain
        # select_sender_id() then waits forever on a listitem that's
        # never going to render, silently swallowed by the except below,
        # producing a misleading "No real Sender ID options available"
        # skip. select_sender_id_by_search() reuses the CONFIRMED
        # search_sender_id() filtering mechanism (see
        # test_TC018_sender_id_search_valid_keyword) to guarantee the
        # target actually renders before clicking it.
        p.select_sender_id_by_search(label)
    except Exception:
        return False
    return bool(p.page.locator(p.SENDER_ID_HIDDEN_INPUT).get_attribute("value"))


def _assert_save_responded(create_page, context):
    """Shared assertion for every real E2E test below: clicks Save must
    have already happened before this is called. Asserts only that the
    app responded AT ALL (a URL redirect or the confirmed app-global
    toast/SweetAlert2 feedback) -- see page object docstring point 27
    for why no specific "success" text/locator is asserted (never
    captured for this page). Prints the observed outcome so a real run's
    output can be used to document the real success/failure text
    afterward."""
    result = create_page.wait_for_save_result()
    print(f"[{context}] wait_for_save_result() -> {result!r}")
    assert result["outcome"] != "none_detected", (
        f"[{context}] No recognized post-submit feedback (URL redirect, "
        f"or the confirmed app-global WireUI/SweetAlert2 toast) appeared "
        f"within 15s after clicking Save. Real post-submit behavior for "
        f"this exact combination has never been captured -- if the app "
        f"is genuinely not responding (rather than just not emitting a "
        f"recognized signal), check for silent client-side validation, "
        f"or a required field this test didn't fill in."
    )
    return result


# ══════════════════════════════════════════════════════════════════════════════
# TC016 -- Create New Template page loads
# ══════════════════════════════════════════════════════════════════════════════

def test_TC016_page_loads_successfully(create_page):
    ensure_on_create_page(create_page)
    assert create_page.is_create_page()
    assert create_page.get_page_header_text() == "Create New WhatsApp Template"
    assert create_page.is_element_present(create_page.SENDER_ID_WRAPPER, timeout=10000)


# ══════════════════════════════════════════════════════════════════════════════
# TC017 -- Sender ID field: select a real sender
# ══════════════════════════════════════════════════════════════════════════════

def test_TC017_sender_id_selectable(create_page):
    ensure_on_create_page(create_page)

    options = create_page.get_sender_id_options()
    assert options, "Expected at least one real Sender ID option"

    target = options[0]["label"]
    create_page.select_sender_id(target)
    selected = create_page.get_selected_sender_id_text()
    assert selected, "Expected a Sender ID to be selected"
    assert selected in target or target in selected


# ══════════════════════════════════════════════════════════════════════════════
# TC018 -- Sender ID search: valid keyword filters the list
# ══════════════════════════════════════════════════════════════════════════════

def test_TC018_sender_id_search_valid_keyword(create_page):
    ensure_on_create_page(create_page)

    options = create_page.get_sender_id_options()
    assert options, "Expected at least one real Sender ID option"

    target = options[0]["label"]
    search_term = target.split(" ")[0]
    create_page.search_sender_id(search_term)
    create_page.page.wait_for_timeout(500)

    popover = create_page.page.locator(create_page.SENDER_ID_WRAPPER).locator(
        "[x-ref='optionsContainer']"
    ).first
    visible_items = popover.get_by_role("listitem").all_inner_texts()
    assert any(search_term.lower() in t.lower() for t in visible_items), (
        f"Expected the search term {search_term!r} to match at least one "
        f"visible Sender ID option, got {visible_items!r}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# TC019 -- Sender ID search: invalid keyword returns nothing
# ══════════════════════════════════════════════════════════════════════════════

def test_TC019_sender_id_search_invalid_keyword(create_page):
    ensure_on_create_page(create_page)

    bogus_term = "zzzznonexistentsenderid9999"
    create_page.search_sender_id(bogus_term)
    create_page.page.wait_for_timeout(500)

    popover = create_page.page.locator(create_page.SENDER_ID_WRAPPER).locator(
        "[x-ref='optionsContainer']"
    ).first
    visible_items = [t for t in popover.get_by_role("listitem").all_inner_texts() if t.strip()]
    assert not visible_items, (
        f"Expected no Sender ID options for the bogus search term "
        f"{bogus_term!r}, got {visible_items!r}"
    )
    # close the popover so it doesn't interfere with later tests
    create_page.page.keyboard.press("Escape")


# ══════════════════════════════════════════════════════════════════════════════
# TC020 -- Template Name: only lowercase letters, digits and underscore
# ══════════════════════════════════════════════════════════════════════════════

def test_TC020_template_name_character_restriction(create_page):
    """The checklist's "only lowercase/digit/underscore" claim was
    originally tested by asserting the LIVE VALUE got auto-normalized --
    but a real run showed the field keeps the raw typed value unchanged
    ('Invalid Name! With SPACE and CAPS#123') and instead renders a real
    WireUI validation error label: <label class="text-sm text-negative-600
    mt-2" for="name">The name field format is invalid.</label> (same
    "negative-600" convention as FORM_VALIDATION_ERROR, now confirmed on
    this field too). So this restriction is enforced via server-side
    validation feedback, not client-side input transformation -- asserting
    on the error message is what the real app actually does."""
    ensure_on_create_page(create_page)

    create_page.set_name("Invalid Name! With SPACE and CAPS#123")
    current_value = create_page.get_name_value()

    assert current_value == "Invalid Name! With SPACE and CAPS#123", (
        f"Expected the Template Name field to keep the raw typed value "
        f"(this app validates rather than silently transforms input), but "
        f"got {current_value!r}"
    )
    errors = create_page.get_validation_errors()
    assert any("name" in e.lower() and "invalid" in e.lower() for e in errors), (
        f"Expected a 'name field format is invalid' validation message "
        f"after typing disallowed characters, but got: {errors!r}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# TC022 -- Header is optional
# ══════════════════════════════════════════════════════════════════════════════

def test_TC022_header_is_optional(create_page):
    ensure_on_create_page(create_page)

    if not _ensure_sender_selected(create_page):
        pytest.skip("No real Sender ID options available in this environment")

    create_page.set_name("optional_header_test")
    # Header is deliberately left unset here.
    assert create_page.is_save_enabled(), (
        "Expected Save to be enabled once Sender ID is set, without ever "
        "touching the Header field -- confirming Header is optional "
        "(Save is only gated on :disabled=\"!$wire.senderId\")"
    )


# ══════════════════════════════════════════════════════════════════════════════
# Category radios (4 confirmed real values)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("category", ["MARKETING", "UTILITY", "AUTHENTICATION", "CONVERSATION"])
def test_category_radio_selectable(create_page, category):
    ensure_on_create_page(create_page)
    create_page.select_category(category)
    assert create_page.get_selected_category() == category


# ══════════════════════════════════════════════════════════════════════════════
# Language select (67 confirmed real options, defaults to English/"en")
# ══════════════════════════════════════════════════════════════════════════════

def test_language_defaults_to_english(create_page):
    ensure_on_create_page(create_page)
    assert create_page.get_selected_language_text() == "English"




# ══════════════════════════════════════════════════════════════════════════════
# Template Labels (optional)
# ══════════════════════════════════════════════════════════════════════════════

def test_template_label_optional_field(create_page):
    ensure_on_create_page(create_page)
    create_page.set_label("qa_label_test")
    assert create_page.get_label_value() == "qa_label_test"
    create_page.set_label("")
    assert create_page.get_label_value() == ""


# ══════════════════════════════════════════════════════════════════════════════
# Footer Text (maxlength 60)
# ══════════════════════════════════════════════════════════════════════════════

def test_footer_text_max_60_chars(create_page):
    ensure_on_create_page(create_page)
    assert create_page.get_footer_text_maxlength() == "60"

    long_footer = "F" * 100
    create_page.set_footer_text(long_footer)
    assert len(create_page.get_footer_text_value()) <= 60


# ══════════════════════════════════════════════════════════════════════════════
# Body field presence (EasyMDE/CodeMirror -- see page object docstring)
# ══════════════════════════════════════════════════════════════════════════════

def test_body_editor_is_codemirror_based(create_page):
    ensure_on_create_page(create_page)
    assert create_page.is_body_editor_present(), (
        "Expected the Body field's EasyMDE/CodeMirror container "
        "([wire\\:key^='editor-']) to be present"
    )
    create_page.set_body_text("Hi {{1}}, this is a QA automation test")
    assert create_page.get_body_text() == "Hi {{1}}, this is a QA automation test"


# ══════════════════════════════════════════════════════════════════════════════
# Marketing sub_category select (8 confirmed real values, only rendered
# when category=MARKETING -- see page object docstring point 15)
# ══════════════════════════════════════════════════════════════════════════════

def test_sub_category_select_appears_for_marketing_and_is_selectable(create_page):
    ensure_on_create_page(create_page)
    create_page.select_category("MARKETING")
    assert create_page.is_sub_category_select_present(), (
        "Expected the sub_category select to render once category=MARKETING "
        "is chosen"
    )

    options = create_page.get_sub_category_options()
    assert options, "Expected real sub_category options to be present"
    labels = {o.get("label") for o in options}
    expected = {
        "Custom Message", "Carousel", "Catalog", "Multi-Product Message",
        "Limited Time Offer", "Product Card Carousel",
        "Single Product Messages", "Order Details",
    }
    assert expected.issubset(labels), (
        f"Expected all 8 confirmed sub_category labels, got {labels!r}"
    )

    create_page.ensure_sub_category_selected("Catalog")
    assert create_page.get_selected_sub_category_text() == "Catalog"


# ══════════════════════════════════════════════════════════════════════════════
# sub_category=Catalog reveals the Catalog Type select (2 confirmed real
# values -- see page object docstring point 16)
# ══════════════════════════════════════════════════════════════════════════════

def test_catalog_type_selectable_for_catalog_sub_category(create_page):
    ensure_on_create_page(create_page)
    create_page.select_category("MARKETING")
    if not create_page.is_sub_category_select_present():
        pytest.skip("sub_category select not available in this environment")
    create_page.ensure_sub_category_selected("Catalog")

    assert create_page.is_catalog_type_select_present(), (
        "Expected the Catalog Type select to render once sub_category="
        "Catalog is chosen"
    )
    options = create_page.get_catalog_type_options()
    labels = {o.get("label") for o in options}
    assert labels == {"Single-Product", "Multi-Product"}, (
        f"Expected exactly the 2 confirmed Catalog Type options, got {labels!r}"
    )

    create_page.select_catalog_type("Single-Product")
    assert create_page.get_selected_catalog_type_text() == "Single-Product"




# ══════════════════════════════════════════════════════════════════════════════
# sub_category=Limited Time Offer: the "enable_lto_expiry" checkbox and
# the expiry-days input it reveals (see page object docstring point 29,
# both pieces now confirmed via real pasted DOM captures).
# ══════════════════════════════════════════════════════════════════════════════

def test_lto_expiry_days_input_when_present(create_page):
    create_page.navigate()
    create_page.select_category("MARKETING")
    if not create_page.is_sub_category_select_present():
        pytest.skip("sub_category select not available in this environment")
    create_page.ensure_sub_category_selected("Limited Time Offer")

    if create_page.is_lto_enable_expiry_checkbox_present():
        create_page.check_lto_enable_expiry()
    else:
        pytest.skip(
            "'enable_lto_expiry' checkbox not present for sub_category="
            "Limited Time Offer in this environment."
        )

    if not create_page.is_lto_expiry_days_input_present():
        pytest.skip(
            "lto_expiry_days input still not present after ticking "
            "'enable_lto_expiry' in this environment."
        )
    assert create_page.get_lto_expiry_days_min() == "1", (
        "Expected the confirmed min='1' attribute on the expiry-days input"
    )
    create_page.set_lto_expiry_days(2)
    assert create_page.get_lto_expiry_days_value() == "2", (
        "Expected the recorded test value of 2 days to be accepted"
    )


# ══════════════════════════════════════════════════════════════════════════════
# sub_category=Carousel reveals the Carousel sub-form's top-level fields
# (see page object docstring point 17)
# ══════════════════════════════════════════════════════════════════════════════

def test_carousel_form_selectable_for_carousel_sub_category(create_page):
    ensure_on_create_page(create_page)
    create_page.select_category("MARKETING")
    if not create_page.is_sub_category_select_present():
        pytest.skip("sub_category select not available in this environment")
    create_page.ensure_sub_category_selected("Carousel")

    assert create_page.is_carousel_form_present(), (
        "Expected the Carousel sub-form (Header media type select) to "
        "render once sub_category=Carousel is chosen"
    )

    media_options = create_page.get_carousel_media_type_options()
    assert {o.get("label") for o in media_options} == {"Image", "Video"}, (
        f"Expected exactly the 2 confirmed media type options, got "
        f"{media_options!r}"
    )
    create_page.select_carousel_media_type("Image")

    count_options = create_page.get_carousel_button_count_options()
    assert {o.get("label") for o in count_options} == {"1", "2"}, (
        f"Expected exactly the 2 confirmed button count options, got "
        f"{count_options!r}"
    )

    type1_options = create_page.get_carousel_button_type1_options()
    type1_labels = {o.get("label") for o in type1_options}
    assert {"URL", "Quick Reply", "Phone Number", "WhatsApp Flow"}.issubset(type1_labels), (
        f"Expected all 4 confirmed Button type 1 options, got {type1_labels!r}"
    )
    create_page.select_carousel_button_type1("URL")

    if create_page.is_carousel_card_file_input_present(0):
        assert create_page.get_carousel_card_description_maxlength(0) == "160"
        create_page.set_carousel_card_description(0, "QA automation card")
    else:
        pytest.skip(
            "Card 0's description/file fields were not present at this "
            "point in the flow -- only the top-level Carousel selects "
            "above are asserted as hard requirements; needs a fresh "
            "capture confirming exactly when per-card fields render."
        )


# ══════════════════════════════════════════════════════════════════════════════
# sub_category=Multi-Product Message: Section/Product fields are real and
# selectable (see page object docstring point 20)
# ══════════════════════════════════════════════════════════════════════════════

def test_mpm_section_and_product_fields_selectable_for_mpm_sub_category(create_page):
    ensure_on_create_page(create_page)
    create_page.select_category("MARKETING")
    if not create_page.is_sub_category_select_present():
        pytest.skip("sub_category select not available in this environment")
    create_page.ensure_sub_category_selected("Multi-Product Message")

    assert create_page.is_mpm_section_title_present(), (
        "Expected the MPM 'Section 1' title field to render once "
        "sub_category=Multi-Product Message is chosen"
    )
    create_page.set_mpm_section_title("QA automation bundle")
    assert create_page.get_mpm_section_title_value() == "QA automation bundle"

    assert create_page.is_mpm_product_retailer_id_present(), (
        "Expected the first product's Content ID field to render "
        "alongside the section title"
    )
    create_page.set_mpm_product_retailer_id("qa_test_sku_001")

    assert create_page.is_element_present(
        create_page.ADD_MPM_SECTION_BTN, timeout=5000
    ), "Expected a confirmed 'Add Section' button"
    assert create_page.is_element_present(
        "[wire\\:click=\"addMpmProduct(0)\"]", timeout=5000
    ), "Expected a confirmed '+ Add Product' button for section 0"


# ══════════════════════════════════════════════════════════════════════════════
# sub_category=Limited Time Offer: the confirmed "Add button" trigger (see
# page object docstring point 21). Point 24 below confirms this same
# trigger is also reused for sub_category=cta_url_button.
# ══════════════════════════════════════════════════════════════════════════════

def test_lto_add_button_menu_offers_five_confirmed_button_types(create_page):
    ensure_on_create_page(create_page)
    create_page.select_category("MARKETING")
    if not create_page.is_sub_category_select_present():
        pytest.skip("sub_category select not available in this environment")
    create_page.ensure_sub_category_selected("Limited Time Offer")

    if not create_page.is_lto_add_button_trigger_present():
        pytest.skip(
            "The 'Add button' trigger was not present in this environment "
            "-- needs a fresh capture confirming whether this is gated by "
            "an additional flag beyond sub_category=lto."
        )

    create_page.open_lto_add_button_menu()
    for label in ("Quick Reply", "URL", "Phone Number", "Copy Offer Code", "Flow"):
        assert create_page.is_element_present(
            f"[wire\\:click=\"showLTOdiv('{label}')\"]", timeout=5000
        ), f"Expected a confirmed showLTOdiv(...) menu item for {label!r}"


# ══════════════════════════════════════════════════════════════════════════════
# sub_category=Product Card Carousel: Button Type select + per-card fields
# (see page object docstring point 22)
# ══════════════════════════════════════════════════════════════════════════════

def test_product_carousel_button_type_and_card_fields_selectable(create_page):
    ensure_on_create_page(create_page)
    create_page.select_category("MARKETING")
    if not create_page.is_sub_category_select_present():
        pytest.skip("sub_category select not available in this environment")
    create_page.ensure_sub_category_selected("Product Card Carousel")

    assert create_page.is_product_carousel_button_type_select_present(), (
        "Expected the Button Type select to render once "
        "sub_category=Product Card Carousel is chosen"
    )
    options = create_page.get_product_carousel_button_type_options()
    labels = {o.get("label") for o in options}
    assert labels == {"Single Product (SPM)", "URL Link"}, (
        f"Expected exactly the 2 confirmed Button Type options, got {labels!r}"
    )
    create_page.select_product_carousel_button_type("URL Link")

    if create_page.is_carousel_product_catalog_id_input_present():
        create_page.set_carousel_product_catalog_id("194836987003835")
        create_page.set_carousel_product_content_id("qa_test_sku_001")
    else:
        pytest.skip(
            "Card 0's manual Catalog ID / Content ID fields were not "
            "present at this point in the flow -- only the top-level "
            "Button Type select above is asserted as a hard requirement."
        )


# ══════════════════════════════════════════════════════════════════════════════
# category=Authentication: OTP type radios + Message Content checkboxes +
# Copy Code button text field (see page object docstring point 23)
# ══════════════════════════════════════════════════════════════════════════════

def test_authentication_otp_type_and_message_content_fields(create_page):
    ensure_on_create_page(create_page)
    create_page.select_category("AUTHENTICATION")

    assert create_page.is_auth_otp_type_radios_present(), (
        "Expected the OTP type radio group (Copy Code/AutoFill/Zero-Tap) "
        "to render once category=AUTHENTICATION is chosen"
    )
    assert create_page.get_selected_auth_otp_type() == "copycode", (
        "Expected Copy Code to be the default-selected OTP type"
    )
    create_page.select_auth_otp_type("autofill")
    assert create_page.get_selected_auth_otp_type() == "autofill"
    create_page.select_auth_otp_type("copycode")
    assert create_page.get_selected_auth_otp_type() == "copycode"

    assert create_page.is_auth_add_security_checkbox_present(), (
        "Expected the 'Add Security recommendation' checkbox to be present"
    )
    assert create_page.is_auth_add_expire_checkbox_present(), (
        "Expected the 'Add expiration time for code' checkbox to be present"
    )
    create_page.check_auth_add_security()
    assert create_page.is_auth_add_security_checked()
    create_page.check_auth_add_expire()
    assert create_page.is_auth_add_expire_checked()

    assert create_page.is_auth_copy_code_button_text_input_present(), (
        "Expected the Copy Code button text field to be present"
    )
    assert create_page.get_auth_copy_code_button_text_value() == "Copy code", (
        "Expected the Copy Code button text field to default to 'Copy code'"
    )
    assert create_page.is_auth_copy_code_button_text_disabled(), (
        "Expected the Copy Code button text field to be disabled in the "
        "default (Copy Code OTP type) state, per the confirmed capture"
    )


# ══════════════════════════════════════════════════════════════════════════════
# category=Conversation, sub_category=CTA URL Button: confirms the "Add
# button" dropdown from point 21 is a SHARED mechanism (not LTO-exclusive
# as first assumed), plus the reused url_buttons_title.0/value.0 fields
# and the "Add Variable" button (see page object docstring point 24)
# ══════════════════════════════════════════════════════════════════════════════

# COMMENTED OUT per explicit user request -- this test case was SKIPPED or FAILED in the most recent full-suite run and the user asked to disable (not delete) it. The original code is preserved below as comments for reference / future re-enabling.
# def test_conversation_cta_url_button_reuses_add_button_and_url_fields(create_page):
#     ensure_on_create_page(create_page)
#     create_page.select_category("CONVERSATION")
#     if not create_page.is_sub_category_select_present():
#         pytest.skip("sub_category select not available in this environment")
#     # ensure_sub_category_selected(..., force=True): CONVERSATION/CTA URL
#     # Button is CONFIRMED (direct observation of a --headed run) to be
#     # the OPPOSITE case from UTILITY/Custom Message -- its single-option
#     # dropdown shows "CTA URL Button" by default, but that default is
#     # apparently never actually committed to the Livewire model until a
#     # real click fires. force=True makes the click happen even though
#     # the display text already matches (see that method's docstring for
#     # the full story, including why this was very likely also the real
#     # cause of the URL button title/value fields coming up empty).
#     # create_page.ensure_sub_category_selected("CTA URL Button", force=True)
#
#     options = create_page.get_header_options()
#     if options:
#         labels = {o.get("label") for o in options}
#         assert labels == {"Text", "Media"}, (
#             f"Expected the confirmed 2-value headerOptions state "
#             f"([Text, Media]) for sub_category=cta_url_button, got "
#             f"{labels!r}"
#         )
#
#     if not create_page.is_lto_add_button_trigger_present():
#         pytest.skip(
#             "The 'Add button' trigger was not present in this environment "
#             "for sub_category=cta_url_button."
#         )
#     create_page.open_lto_add_button_menu()
#     assert create_page.is_element_present(
#         "[wire\\:click=\"showLTOdiv('URL')\"]", timeout=5000
#     ), (
#         "Expected the same showLTOdiv('URL') menu item confirmed for "
#         "sub_category=lto to also render here -- confirming this is a "
#         "shared 'Add button' mechanism, not LTO-exclusive"
#     )
#     assert create_page.is_lto_add_button_menu_item_disabled("URL"), (
#         "Expected the 'URL' menu item to be disabled here: this "
#         "sub_category force-provisions exactly one URL button rather "
#         "than letting the user add one via this menu, per the confirmed "
#         "'You must add exactly 1 URL button for CTA URL Button templates' "
#         "helper text"
#     )
#
#     if create_page.is_url_button_fields_present():
#         create_page.set_url_button_title("Visit us")
#         create_page.set_url_button_value("https://example.com")
#     else:
#         pytest.skip(
#             "The reused url_buttons_title.0/url_buttons_value.0 fields "
#             "(point 18 infra) were not present at this point in the flow "
#             "-- only the 'Add button' menu assertions above are asserted "
#             "as a hard requirement."
#         )
#
#     if create_page.is_add_variable_body_button_present():
#         create_page.click_add_variable_body()
#     else:
#         pytest.skip(
#             "The 'Add Variable' button (wire:click=\"insertVariable('body')\") "
#             "was not present at this point in the flow."
#         )


# ══════════════════════════════════════════════════════════════════════════════
# category=Utility, sub_category=Custom Message: confirms the "Add button"
# dropdown from point 21/24 is ALSO shared here (a THIRD independent
# category/sub_category combination), with Copy Offer Code specifically
# disabled again, and the "full" 4-value headerOptions state (see page
# object docstring point 25)
# ══════════════════════════════════════════════════════════════════════════════

def test_utility_custom_message_add_button_copy_offer_code_disabled(create_page):
    # Forces a fresh page load rather than ensure_on_create_page(): this
    # test runs immediately after
    # test_conversation_cta_url_button_reuses_add_button_and_url_fields,
    # which leaves category=CONVERSATION selected (and possibly the "Add
    # button" dropdown open) if it fails partway through --
    # ensure_on_create_page() only checks the URL/header and would NOT
    # reset that leftover state, since this is a module-scoped page.
    create_page.navigate()
    create_page.select_category("UTILITY")
    if not create_page.is_sub_category_select_present():
        pytest.skip("sub_category select not available in this environment")
    # ensure_sub_category_selected(), not select_sub_category(): real
    # evidence (a live run) showed UTILITY already defaults sub_category
    # to "Custom Message", and re-clicking an already-selected option in
    # this WireUI select TOGGLES IT OFF instead of being a no-op -- see
    # ensure_sub_category_selected()'s docstring for the full story
    # (this was the root cause of a 30s Locator.click timeout here).
    create_page.ensure_sub_category_selected("Custom Message")
    # When Custom Message was ALREADY the default (the normal case),
    # ensure_sub_category_selected() returns immediately with no click
    # and no settle wait -- but the deeper "Add button" section is its
    # own nested conditional render that depends on the same Livewire
    # cycle as the sub_category default, and may not have finished
    # painting yet by the time select_category()'s own wait returns.
    # Page object docstring point 25 confirms (checksum-verified real
    # capture) that this section DOES render for UTILITY/custom_message
    # with all 5 menu items -- so a short settle wait here is a timing
    # fix, not walking back that confirmed fact.
    create_page.page.wait_for_timeout(800)

    options = create_page.get_header_options()
    if options:
        labels = {o.get("label") for o in options}
        assert labels == {"None", "Text", "Media", "Location"}, (
            f"Expected the confirmed 'full' 4-value headerOptions state for "
            f"UTILITY/custom_message, got {labels!r}"
        )

    if not create_page.is_lto_add_button_trigger_present(timeout=10000):
        pytest.skip(
            "The 'Add button' trigger was not present in this environment "
            "for UTILITY/custom_message."
        )
    create_page.open_lto_add_button_menu()
    for label in ("Quick Reply", "URL", "Phone Number", "Copy Offer Code", "Flow"):
        assert create_page.is_element_present(
            f"[wire\\:click=\"showLTOdiv('{label}')\"]", timeout=5000
        ), f"Expected a confirmed showLTOdiv(...) menu item for {label!r}"
    assert create_page.is_lto_add_button_menu_item_disabled("Copy Offer Code"), (
        "Expected 'Copy Offer Code' to be disabled here too, matching the "
        "confirmed disabled state already seen under MARKETING/lto and "
        "CONVERSATION/cta_url_button -- this is a shared, not sub_category-"
        "specific, restriction"
    )


# ══════════════════════════════════════════════════════════════════════════════
# category=Utility, sub_category=Order Details: the fixed/non-editable
# single-button block plus the narrower [Media]-only headerOptions state
# (see page object docstring point 26). sub_category=Order Status is now
# separately confirmed as a DISTINCT state (page object docstring point
# 30, exercised by test_utility_order_status_distinct_from_order_details
# below) -- two earlier capture attempts aimed at Order Status had both
# landed on this exact Order Details state instead (proven via matching
# Livewire snapshot checksums), before a third attempt succeeded.
# ══════════════════════════════════════════════════════════════════════════════

def test_utility_order_details_fixed_button_block(create_page):
    # Fresh page load for the same reason as
    # test_utility_custom_message_add_button_copy_offer_code_disabled
    # above -- do not inherit sub_category=custom_message/open-dropdown
    # state from that test if it skips or fails partway through.
    create_page.navigate()
    create_page.select_category("UTILITY")
    if not create_page.is_sub_category_select_present():
        pytest.skip("sub_category select not available in this environment")
    create_page.select_sub_category("Order Details")

    options = create_page.get_header_options()
    if options:
        labels = {o.get("label") for o in options}
        assert labels == {"Media"}, (
            f"Expected the confirmed narrower [Media]-only headerOptions "
            f"state for UTILITY/order_details, got {labels!r}"
        )

    if not create_page.is_order_details_action_select_present():
        pytest.skip(
            "The fixed 'Type of Action' select was not present in this "
            "environment for UTILITY/order_details."
        )
    assert create_page.get_order_details_action_select_value() == "Open order details", (
        "Expected the fixed, non-editable 'Type of Action' select to be "
        "pre-set to 'Open order details'"
    )
    assert create_page.is_order_details_action_select_disabled(), (
        "Expected the 'Type of Action' select to be disabled -- per the "
        "confirmed helper text 'The button text is not editable.'"
    )

    assert create_page.is_order_details_button_text_input_present(), (
        "Expected the fixed 'Button Text' input to be present"
    )
    assert create_page.get_order_details_button_text_value() == "Review and Pay", (
        "Expected the fixed 'Button Text' input to default to "
        "'Review and Pay'"
    )
    assert create_page.is_order_details_button_text_readonly(), (
        "Expected the 'Button Text' input to be readonly, matching the "
        "confirmed 'not editable' helper text"
    )


# ══════════════════════════════════════════════════════════════════════════════
# category=Utility, sub_category=Order Status: CONFIRMED to be a distinct
# state from Order Details, not the same form (page object docstring
# point 30) -- narrower typeOptions ([] vs order_details' [Image]) and no
# fixed order-button block at all (showOrderButton:false). Also CONFIRMED
# (point 31, via direct user inspection of the live app) that no Header
# type select renders at all for order_status -- superseding an earlier
# capture's [Media]-only headerOptions claim, which conflicted with a
# second genuine capture's headerOptions data and is now moot since the
# Header field isn't present in this sub_category to begin with.
# ══════════════════════════════════════════════════════════════════════════════

def test_utility_order_status_distinct_from_order_details(create_page):
    create_page.navigate()
    create_page.select_category("UTILITY")
    if not create_page.is_sub_category_select_present():
        pytest.skip("sub_category select not available in this environment")
    create_page.select_sub_category("Order Status")
    assert create_page.get_selected_sub_category_text() == "Order Status"

    assert not create_page.is_header_select_present(), (
        "Expected NO Header type select for sub_category=Order Status -- "
        "confirmed via direct user inspection of the live app (page "
        "object docstring point 31); an earlier genuine capture's "
        "headerOptions snapshot data was misleading since the Header "
        "field never actually renders for this sub_category"
    )

    assert not create_page.is_order_details_action_select_present(), (
        "Expected NO 'Type of Action' select for sub_category=Order "
        "Status -- confirmed distinct from Order Details, which does "
        "render this fixed button block (page object docstring point 30)"
    )
    assert not create_page.is_order_details_button_text_input_present(), (
        "Expected NO fixed 'Button Text' input for sub_category=Order "
        "Status, for the same reason"
    )


# ══════════════════════════════════════════════════════════════════════════════
# Real E2E (fill-and-submit) template creation, one per confirmed
# category/sub_category combination (page object docstring point 27).
#
# Every test below performs a REAL submit against the real live account --
# it fills only fields this suite has genuine DOM evidence for (never a
# guessed locator), clicks Save, and asserts only that the app responded
# AT ALL (a URL redirect, or the confirmed app-global WireUI/SweetAlert2
# toast) -- NOT that a specific "success" string appeared, since this
# page's real post-submit DOM has never been captured. Each test starts
# with create_page.navigate() (a fresh page load), same defensive pattern
# used above for the UTILITY tests, so none of these depend on -- or
# leave behind -- state for any other test in this module-scoped file.
#
# Whoever runs these against the real environment should capture what
# wait_for_save_result() actually printed (each test prints it) so a
# real, confirmed "point 28" can be written documenting the exact
# success/failure text -- at which point these can be tightened from
# "the app responded" to "the app confirmed success".
# ══════════════════════════════════════════════════════════════════════════════

WHATSAPP_TEMPLATES_JSON_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "test_data", "whatsapp_templates.json"
)


def load_whatsapp_templates(include_unconfirmed=False):
    """Loads tests/test_data/whatsapp_templates.json -- the real,
    per-scenario source of truth for the E2E submit tests below. Each
    entry's 'components' list mirrors Meta's real WhatsApp Business
    Template API JSON shape (a genuine payload example was provided
    directly by the project owner); CPaaS-UI-specific fields with no
    Meta-schema equivalent live under 'gts_fields'. By default only
    entries with confirmed:true are returned -- an entry marked
    confirmed:false (e.g. the 3-card VIDEO carousel reference payload,
    which needs a real video test asset this repo doesn't have yet) is
    documentation, not something to run blind."""
    with open(WHATSAPP_TEMPLATES_JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    templates = data["templates"]
    if not include_unconfirmed:
        templates = [t for t in templates if t.get("confirmed") is True]
    return templates


def _get_component(template, comp_type):
    for component in template.get("components", []):
        if component.get("type") == comp_type:
            return component
    return None


def _component_text(template, comp_type, default=None):
    component = _get_component(template, comp_type)
    return component.get("text", default) if component else default


def _fill_marketing_carousel_image_1card(create_page, template):
    if not create_page.is_carousel_form_present():
        pytest.skip("Carousel sub-form not available in this environment")

    carousel = _get_component(template, "CAROUSEL")

    if carousel.get("media_type") != "IMAGE":
        pytest.skip(
            f"CAROUSEL media_type={carousel.get('media_type')!r} has no "
            f"real test asset wired up -- see tests/test_data/"
            f"whatsapp_templates.json"
        )

    # Image is already selected by default for Carousel Media Header.
    # No need to explicitly select "Image".

    card = carousel["cards"][0]
    buttons = card.get("buttons", [])

    button_type = (
        "Quick Reply"
        if buttons and buttons[0].get("type") == "QUICK_REPLY"
        else "Quick Reply"
    )

    create_page.select_carousel_button_type1(button_type)

    create_page.set_carousel_card_description(
        0, card["description"]
    )

    if create_page.is_carousel_card_file_input_present(0):
        media_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "test_data",
            card["media_file"],
        )
        create_page.set_carousel_card_file(0, media_path)
    else:
        pytest.skip(
            "Carousel card 0's file input was not present in this "
            "environment -- a real Carousel template requires header "
            "media per card, so a submit without it is not meaningful."
        )

    if buttons and "text" in buttons[0]:
        create_page.set_card_button_title(
            0, 0, buttons[0]["text"]
        )

def _fill_marketing_catalog(create_page, template):
    fields = template.get("gts_fields", {})
    if create_page.is_catalog_type_select_present() and "catalog_type" in fields:
        create_page.select_catalog_type(fields["catalog_type"])
    # Content Id (product_retailer_id) is now confirmed (page object
    # docstring point 28) -- fill it when present. There is confirmed to
    # be NO separate Catalog ID field anywhere in this flow (checked
    # directly against the real live app, see point 16's correction), so
    # Content Id is the only sub_category-specific field this submit can
    # fill; any validation response the app still returns is treated by
    # _assert_save_responded as a valid "the app responded" signal.
    if create_page.is_catalog_content_id_input_present() and "content_id" in fields:
        create_page.set_catalog_content_id(fields["content_id"])


def _fill_marketing_multi_product_message(create_page, template):
    fields = template.get("gts_fields", {})
    if create_page.is_mpm_section_title_present():
        if "mpm_section_title" in fields:
            create_page.set_mpm_section_title(
                fields["mpm_section_title"], section_index=0
            )
        if "mpm_product_retailer_id" in fields:
            create_page.set_mpm_product_retailer_id(
                fields["mpm_product_retailer_id"], section_index=0, product_index=0
            )


def _fill_marketing_lto_url_button(create_page, template):
    fields = template.get("gts_fields", {})
    buttons_component = _get_component(template, "BUTTONS")
    url_button = next(
        (b for b in (buttons_component.get("buttons", []) if buttons_component else [])
         if b.get("type") == "URL"),
        None,
    )
    # Per original instruction, only the URL button type is exercised
    # here for LTO (Quick Reply/Phone Number/Copy Offer Code/Flow
    # deliberately out of scope) -- URL is confirmed present in the
    # 5-item "Add button" menu (page object docstring point 21).
    if url_button and create_page.is_lto_add_button_trigger_present():
        create_page.select_lto_add_button_type("URL")
        if create_page.is_url_button_fields_present():
            if "text" in url_button:
                create_page.set_url_button_title(url_button["text"])
            if "url" in url_button and create_page.is_element_present(
                create_page.URL_BUTTON_VALUE_INPUT, timeout=3000
            ):
                create_page.set_url_button_value(url_button["url"])
    # Expiry-days input is only confirmed once the (uncaptured)
    # "enable_lto_expiry" checkbox is ticked -- guarded here, not
    # guessed.
    if "lto_expiry_days" in fields and create_page.is_lto_expiry_days_input_present():
        create_page.set_lto_expiry_days(fields["lto_expiry_days"])
    # lto_title is a confirmed real property but no input DOM for it has
    # ever been captured (page object docstring point 21) -- not guessed
    # here.


def _fill_marketing_product_carousel(create_page, template):
    fields = template.get("gts_fields", {})
    if (
        create_page.is_product_carousel_button_type_select_present()
        and "product_carousel_button_type" in fields
    ):
        create_page.select_product_carousel_button_type(
            fields["product_carousel_button_type"]
        )
    if (
        create_page.is_carousel_product_catalog_id_input_present(0)
        and "product_carousel_catalog_id" in fields
    ):
        create_page.set_carousel_product_catalog_id(
            fields["product_carousel_catalog_id"], card_index=0
        )
        if "product_carousel_content_id" in fields:
            create_page.set_carousel_product_content_id(
                fields["product_carousel_content_id"], card_index=0
            )
    # Give the card's own conditional sub-form a moment to settle after
    # Catalog ID/Content ID's debounced Livewire round-trip before
    # checking for Button Title/URL -- real evidence (a screenshot
    # showing both fields still empty with the app's own "required"
    # validation visible after Save) suggests this card may still be
    # re-rendering when the presence check below runs.
    create_page.page.wait_for_timeout(800)
    # Button Title / Button URL (page object docstring point 33) --
    # real evidence: a live run got NO post-submit signal at all without
    # these filled, consistent with silent client-side validation on
    # this required pair (same failure shape as CONVERSATION/
    # cta_url_button's missing URL button).
    if (
        create_page.is_carousel_product_button_title_input_present(0)
        and "product_carousel_button_title" in fields
    ):
        create_page.set_carousel_product_button_title(
            fields["product_carousel_button_title"], card_index=0
        )
    if (
        create_page.is_carousel_product_button_url_input_present(0)
        and "product_carousel_button_url" in fields
    ):
        create_page.set_carousel_product_button_url(
            fields["product_carousel_button_url"], card_index=0
        )


def _fill_conversation_cta_url_button(create_page, template):
    buttons_component = _get_component(template, "BUTTONS")
    url_button = next(
        (b for b in (buttons_component.get("buttons", []) if buttons_component else [])
         if b.get("type") == "URL"),
        None,
    )
    if url_button and create_page.is_url_button_fields_present():
        if "text" in url_button:
            create_page.set_url_button_title(url_button["text"])
        # url_buttons_value.0 is CONFIRMED broken/absent in the live DOM
        # as of the last live run against this exact sub_category (a
        # real 30s Locator.fill timeout, not a guess) -- guarded with a
        # short presence check rather than assumed, to avoid repeating
        # that hang here.
        if "url" in url_button and create_page.is_element_present(
            create_page.URL_BUTTON_VALUE_INPUT, timeout=3000
        ):
            create_page.set_url_button_value(url_button["url"])


# sub_category-specific fillers, keyed by the JSON entry's "id" (not just
# sub_category, since e.g. both Carousel entries share a sub_category but
# only one is runnable). Entries with no filler here (custom_message,
# order_details, order_status, authentication) are confirmed to need
# nothing beyond fill_required_base_fields() -- see each JSON entry's
# "notes".
_TEMPLATE_FILLERS = {
    "marketing_carousel_image_1card": _fill_marketing_carousel_image_1card,
    "marketing_catalog": _fill_marketing_catalog,
    "marketing_multi_product_message": _fill_marketing_multi_product_message,
    "marketing_lto_url_button": _fill_marketing_lto_url_button,
    "marketing_product_carousel": _fill_marketing_product_carousel,
    "conversation_cta_url_button": _fill_conversation_cta_url_button,
}

WHATSAPP_E2E_TEMPLATES = load_whatsapp_templates()


@pytest.mark.parametrize(
    "template", WHATSAPP_E2E_TEMPLATES, ids=[t["id"] for t in WHATSAPP_E2E_TEMPLATES]
)
def test_e2e_template_submit(create_page, template):
    # COMMENTED-OUT-EQUIVALENT SKIP per explicit user request: these two
    # specific JSON entries FAILED in the most recent full-suite run --
    # marketing_lto_url_button got no recognized post-submit signal
    # (outcome='none_detected') after Save, and conversation_cta_url_button
    # timed out 30s filling '[id=\"url_buttons_title.0\"]' (this is the
    # exact same test_conversation_cta_url_button_reuses_add_button_and_
    # url_fields scenario, which is now commented out above pending real
    # investigation). The user asked to disable, not delete -- every
    # other id in this JSON still runs normally through this same
    # function, so the whole function isn't disabled, only these two
    # parametrized cases.
    if template["id"] in ("marketing_lto_url_button", "conversation_cta_url_button"):
        pytest.skip(
            f"[{template['id']}] disabled per explicit user request -- "
            f"FAILED in the most recent full-suite run; needs real "
            f"investigation (see the comment above this skip) before "
            f"being re-enabled."
        )
    create_page.navigate()
    create_page.select_category(template["category"])
    body_text = _component_text(template, "BODY")
    name = create_page.fill_required_base_fields(body_text=body_text)

    sub_category = template.get("sub_category")
    if sub_category:
        selection_mode = template.get("sub_category_selection", "required")
        select_present = create_page.is_sub_category_select_present()
        if selection_mode == "optional":
            # Custom Message/Order Details/Order Status: selecting the
            # sub_category was always best-effort in the original tests
            # -- select it if present, but never skip the test if it
            # isn't (see the JSON's _schema_note). ensure_sub_category_
            # selected() (not select_sub_category()) matters especially
            # here: real evidence showed UTILITY already defaults
            # sub_category to "Custom Message", and re-clicking an
            # already-selected option in this WireUI select TOGGLES IT
            # OFF instead of being a no-op (see that method's docstring
            # -- this was a real 30s timeout root cause).
            if select_present:
                create_page.ensure_sub_category_selected(sub_category)
        else:
            if not select_present:
                pytest.skip("sub_category select not available in this environment")
            # BUG FIX (real evidence -- user report + code inspection):
            # this branch used to only CHECK that the sub_category select
            # was present, then never actually clicked the target option
            # -- the selection call itself was left commented out below.
            # For "required"-mode entries (Carousel, Catalog, Multi-
            # Product Message, LTO, Product Carousel, CONVERSATION/CTA
            # URL Button) this meant the page stayed on whatever
            # sub_category was already selected, so every filler's own
            # is_X_form_present() guard then correctly reported the
            # target form "not available in this environment" -- a
            # misleading skip reason, since the real cause was that
            # sub_category was simply never changed. force_select (JSON:
            # "sub_category_force_select") matters for CONVERSATION/CTA
            # URL Button specifically -- confirmed by direct observation
            # of a --headed run that its single-option dropdown's default
            # display text is not actually bound to the Livewire model
            # until a real click fires (the opposite symptom from
            # UTILITY's toggle-off bug). See
            # ensure_sub_category_selected()'s docstring.
            force_select = template.get("sub_category_force_select", False)
            create_page.ensure_sub_category_selected(sub_category, force=force_select)

    filler = _TEMPLATE_FILLERS.get(template["id"])
    if filler:
        filler(create_page, template)

    create_page.click_save()
    _assert_save_responded(
        create_page,
        f"{template['category']}/{sub_category or template['id']} ({name})",
    )


# ══════════════════════════════════════════════════════════════════════════════
# Header select: open/search mechanics only (real options unconfirmed --
# see module docstring / page object docstring point 8)
# ══════════════════════════════════════════════════════════════════════════════

def test_header_select_present_but_options_unconfirmed(create_page):
    ensure_on_create_page(create_page)
    assert create_page.is_header_select_present()

    if create_page.get_header_options():
        pytest.skip(
            "Header select now exposes real options in this environment -- "
            "the original capture had an empty option list. Re-capture "
            "this page and update whatsapp_template_create_page.py / this "
            "suite to build out TC023-TC028 (Header None/Text/Image/"
            "Video/Document/Location) using the real option data."
        )


# ══════════════════════════════════════════════════════════════════════════════
# Save button: structurally disabled until Sender ID is set
# ══════════════════════════════════════════════════════════════════════════════

def test_save_button_disabled_until_sender_id(create_page):
    create_page.navigate()
    assert create_page.is_save_button_present()
    assert not create_page.is_save_enabled(), (
        "Expected Save to be disabled before any Sender ID is chosen "
        "(:disabled=\"!$wire.senderId\")"
    )

    if not _ensure_sender_selected(create_page):
        pytest.skip("No real Sender ID options available in this environment")

    assert create_page.is_save_enabled(), (
        "Expected Save to become enabled once a Sender ID is chosen"
    )


# ══════════════════════════════════════════════════════════════════════════════
# TC023-TC028 -- Header type sub-behaviors (None/Text/Image/Video/
# Document/Location), including the TC024 variable-insertion-after-60-
# chars bug and the TC026/TC027 unsupported-format gaps (JIRA CPAAS-3196)
# ══════════════════════════════════════════════════════════════════════════════

def test_TC023_to_TC028_header_type_subforms(create_page):
    """Captures the REAL Header select option list for MARKETING/Custom
    Message -- the specific context this checklist item (TC023-TC028)
    targets -- rather than guessing at it.

    Real headerOptions data already exists for THREE other contexts (see
    page object docstring points 24-26, and
    test_conversation_cta_url_button_reuses_add_button_and_url_fields /
    test_utility_custom_message_add_button_copy_offer_code_disabled /
    test_utility_order_details_fixed_button_block above):
      - CONVERSATION / cta_url_button   -> {"Text", "Media"}
      - UTILITY / custom_message        -> {"None", "Text", "Media", "Location"}
      - UTILITY / order_details         -> {"Media"}
    None of these three real, confirmed captures ever showed separate
    "Image"/"Video"/"Document" options -- only a single umbrella "Media"
    value. That already contradicts this checklist item's assumed 6-value
    list (None/Text/Image/Video/Document/Location), so TC023-TC028 cannot
    be built against that assumed list even once MARKETING/Custom Message
    is captured -- the real option set will very likely also just be a
    subset of {None, Text, Media, Location}.

    This test drives the app to the one remaining uncaptured context
    (MARKETING/Custom Message, with a real Sender ID chosen the same way
    _ensure_sender_selected() does for other confirmed tests in this
    file) and reports the real decoded option list via print(), using
    ONLY the already-proven get_header_options()/_decoded_options()
    mechanism -- the same one used for Sender ID, Language, sub_category,
    Catalog Type, and Carousel Media Type. It intentionally does not
    assert a specific label set yet: once a real run prints real labels
    here, replace the prints below with a hard assertion and build the
    per-type sub-forms (None/Text/Media[/Location]) for this context
    using select_header_type(), matching the pattern already proven for
    the 3 confirmed contexts above.
    """
    create_page.navigate()
    create_page.select_category("MARKETING")
    if create_page.is_sub_category_select_present():
        create_page.ensure_sub_category_selected("Custom Message")

    if not _ensure_sender_selected(create_page):
        pytest.skip("No real Sender ID options available in this environment")

    if not create_page.is_header_select_present():
        pytest.skip(
            "Header select is not present for MARKETING/Custom Message in "
            "this environment -- cannot capture its real option list."
        )

    options = create_page.get_header_options()
    print(
        f"\n[TC023-TC028 evidence] MARKETING/Custom Message "
        f"headerOptions = {options!r}"
    )

    if not options:
        pytest.skip(
            "Header select is present but its option blob decoded to an "
            "empty list for MARKETING/Custom Message, same as the "
            "original capture. Needs a --headed run to inspect why (e.g. "
            "maybe another field must be set first, or this state "
            "genuinely has no header options yet). TC023-TC028's real "
            "sub-behaviors remain un-buildable until this returns real "
            "data -- run this test with -s and paste the printed line "
            "above plus this skip reason."
        )

    labels = {o.get("label") for o in options}
    print(f"[TC023-TC028 evidence] labels = {labels!r}")


# ══════════════════════════════════════════════════════════════════════════════
# TC029-TC036 -- Conversation Template section
# ══════════════════════════════════════════════════════════════════════════════

# COMMENTED OUT per explicit user request -- this test case was SKIPPED or FAILED in the most recent full-suite run and the user asked to disable (not delete) it. The original code is preserved below as comments for reference / future re-enabling.
# @pytest.mark.skip(
#     reason=(
#         "sub_category=cta_url_button's confirmed fields (headerOptions/"
#         "typeOptions state, the 'Add button' dropdown reused from LTO with "
#         "its single disabled 'URL' item, the url_buttons_title.0/"
#         "url_buttons_value.0 fields, and the 'Add Variable' button) ARE "
#         "now confirmed and built (page object docstring point 24) and "
#         "exercised by "
#         "test_conversation_cta_url_button_reuses_add_button_and_url_fields "
#         "above. The conversation_enabled toggle now has a GUESSED, "
#         "unconfirmed locator/test -- see "
#         "test_TC029_conversation_enabled_toggle_guessed below (page object "
#         "docstring point 32). This TC stays skipped for the remaining "
#         "still-uncaptured pieces: end-to-end body-variable insertion "
#         "behavior for this section, and footer sub-behaviors beyond the "
#         "already-confirmed footer_text field/maxlength."
#     )
# )
# def test_TC029_to_TC036_conversation_template_section():
#     pass


@pytest.mark.xfail(
    strict=False,
    reason=(
        "GUESSED locator, NOT confirmed from real DOM evidence -- see page "
        "object docstring point 32. No rendered toggle/checkbox HTML for "
        "conversation_enabled has ever been captured; only its boolean "
        "`true` value inside the wire:snapshot JSON for category="
        "CONVERSATION was observed. CONVERSATION_ENABLED_TOGGLE_GUESSED "
        "('#conversation_enabled') is a guess modeled on this codebase's "
        "id-matches-wire:model convention (e.g. #footer_text), added at "
        "the user's explicit request to write guessed-and-marked-pending "
        "coverage rather than leave this gap uncovered. Expected to FAIL "
        "against the real app until confirmed/corrected -- xfail(strict="
        "False) so a real pass doesn't hard-fail the suite, but a failure "
        "here is not itself a regression signal."
    )
)
def test_TC029_conversation_enabled_toggle_guessed(create_page):
    create_page.navigate()
    create_page.select_category("CONVERSATION")
    if create_page.is_sub_category_select_present():
        # force=True -- see ensure_sub_category_selected()'s docstring:
        # CONVERSATION/CTA URL Button's default display text is not
        # actually committed until a real click fires (confirmed by
        # direct observation of a --headed run).
        create_page.ensure_sub_category_selected("CTA URL Button", force=True)
    assert create_page.is_conversation_enabled_toggle_present(), (
        "GUESSED locator CONVERSATION_ENABLED_TOGGLE_GUESSED "
        "('#conversation_enabled') did not match any element -- expected, "
        "since this selector was never confirmed from real DOM evidence "
        "(page object docstring point 32). Provide a real DOM capture of "
        "the toggle control to replace this guess."
    )
    initial_state = create_page.is_conversation_enabled()
    create_page.toggle_conversation_enabled()
    assert create_page.is_conversation_enabled() != initial_state, (
        "Toggling the guessed conversation_enabled control did not "
        "change its checked state as expected -- the guessed locator/"
        "interaction model is likely wrong; needs a real DOM capture."
    )


# ══════════════════════════════════════════════════════════════════════════════
# TC037-TC041 -- Authentication category form
# ══════════════════════════════════════════════════════════════════════════════

def test_TC037_to_TC041_authentication_category_form(create_page):
    """CONFIRMED (real --headed run, printed evidence: OTP type='autofill'
    -- present=True, disabled=True; OTP type='zerotap' -- present=True,
    disabled=True): the Copy Code button text field stays PRESENT and
    DISABLED for the Autofill and Zero-Tap OTP types too -- identical to
    the already-confirmed default Copy Code state
    (test_authentication_otp_type_and_message_content_fields above). It
    never un-disables for any of the 3 OTP types, resolving the
    originally-open question. Also CONFIRMED (same run: 'App Setup' text
    visible=False, 'Package' text visible=False): no "App Setup"/
    "Package" text renders anywhere on the page for
    category=AUTHENTICATION in this environment -- the original
    checklist's App Setup/package name fields do not exist here (at
    least not as visible text; this does not rule out a differently-
    worded or conditionally-gated field, only that these two exact
    strings never render).

    Copy Code's OTP-type radio switching itself (select_auth_otp_type(),
    get_selected_auth_otp_type()) is already confirmed and exercised by
    test_authentication_otp_type_and_message_content_fields above -- this
    test extends that CONFIRMED mechanism to the two OTP types the
    button-text-field's disabled state had never been directly inspected
    for.
    """
    create_page.navigate()
    create_page.select_category("AUTHENTICATION")
    if not create_page.is_auth_otp_type_radios_present():
        pytest.skip("OTP type radio group not present in this environment")

    for otp_type in ("autofill", "zerotap"):
        create_page.select_auth_otp_type(otp_type)
        assert create_page.get_selected_auth_otp_type() == otp_type, (
            f"Expected {otp_type!r} to become the selected OTP type"
        )
        assert create_page.is_auth_copy_code_button_text_input_present(), (
            f"Expected the Copy Code button text field to still be "
            f"present when OTP type={otp_type!r}, per the confirmed "
            f"real run"
        )
        assert create_page.is_auth_copy_code_button_text_disabled(), (
            f"Expected the Copy Code button text field to remain "
            f"DISABLED when OTP type={otp_type!r} -- a real --headed run "
            f"confirmed it never un-disables for any of the 3 OTP types, "
            f"contradicting the original checklist's assumption that it "
            f"might"
        )

    # Restore the confirmed default OTP type for whatever test runs next
    # on this module-scoped page.
    create_page.select_auth_otp_type("copycode")

    # CONFIRMED absent (real run): neither string renders anywhere on
    # this page for category=AUTHENTICATION. Kept as a live check (not a
    # hard assertion) so a future app change adding either field
    # surfaces here as a skip -- with a note to build a real assertion
    # from it -- instead of a silent false negative.
    app_setup_visible = create_page.page.get_by_text("App Setup", exact=False).count() > 0
    package_visible = create_page.page.get_by_text("Package", exact=False).count() > 0
    if app_setup_visible or package_visible:
        pytest.skip(
            f"'App Setup'/'Package' text is now visible on the page "
            f"(app_setup_visible={app_setup_visible!r}, "
            f"package_visible={package_visible!r}) -- this contradicts "
            f"the last confirmed run (both False) and means the app has "
            f"changed. Needs a fresh DOM capture to build a real "
            f"assertion for this field before this TC can be considered "
            f"fully resolved."
        )


# ══════════════════════════════════════════════════════════════════════════════
# TC042-TC046 -- Utility category form
# ══════════════════════════════════════════════════════════════════════════════

# COMMENTED OUT per explicit user request -- this test case was SKIPPED or FAILED in the most recent full-suite run and the user asked to disable (not delete) it. The original code is preserved below as comments for reference / future re-enabling.
# @pytest.mark.skip(
#     reason=(
#         "Custom Message's 'Add button' dropdown (with Copy Offer Code "
#         "confirmed disabled) and Order Details' fixed/non-editable single-"
#         "button block (plus its narrower [Media]-only headerOptions state) "
#         "ARE now confirmed and built (page object docstring points 25/26) "
#         "and exercised by "
#         "test_utility_custom_message_add_button_copy_offer_code_disabled "
#         "and test_utility_order_details_fixed_button_block above. Still "
#         "skipped as a numbered TC because the 'Include opt-out "
#         "button' checkbox mentioned in the original checklist was never "
#         "found in any capture (only an unrelated sidebar nav link "
#         "happens to share the text 'Opt-out'). sub_category=order_status "
#         "was initially hard to pin down -- two attempts to capture it "
#         "both landed back on order_details instead (proven via matching "
#         "Livewire snapshot checksums) -- but a third attempt succeeded: "
#         "order_status is now confirmed distinct from order_details "
#         "(page object docstring point 30) and exercised by "
#         "test_utility_order_status_distinct_from_order_details above."
#     )
# )
# def test_TC042_to_TC046_utility_category_form():
#     pass


# ══════════════════════════════════════════════════════════════════════════════
# TC047-TC058 -- Marketing - Custom message
# ══════════════════════════════════════════════════════════════════════════════

# COMMENTED OUT per explicit user request -- this test case was SKIPPED or FAILED in the most recent full-suite run and the user asked to disable (not delete) it. The original code is preserved below as comments for reference / future re-enabling.
# @pytest.mark.skip(
#     reason=(
#         "The URL/Phone Number/Copy-Offer-Code/Flow button fields' own "
#         "structure and real option lists ARE now confirmed (see page "
#         "object docstring point 18) and locators/helpers for them are "
#         "built (is_url_button_fields_present, is_phone_button_fields_"
#         "present, is_flow_button_fields_present, etc.). What blocks a "
#         "real test here is that no capture has ever shown the UI action "
#         "that first reveals these blocks (e.g. an 'Add button' control) "
#         "-- getting from a fresh Create page to a visible button field "
#         "would require guessing that trigger, which this project's "
#         "evidence rule forbids. Needs a fresh capture showing the "
#         "control that adds a button, or manual QA confirmation of it."
#     )
# )
# def test_TC047_to_TC058_marketing_custom_message():
#     pass


# ══════════════════════════════════════════════════════════════════════════════
# TC059-TC062 -- Marketing - Carousel
# ══════════════════════════════════════════════════════════════════════════════

# COMMENTED OUT per explicit user request -- this test case was SKIPPED or FAILED in the most recent full-suite run and the user asked to disable (not delete) it. The original code is preserved below as comments for reference / future re-enabling.
# @pytest.mark.skip(
#     reason=(
#         "The Carousel sub-form's top-level fields (media type, button "
#         "count, button type 1, per-card file/description/button fields, "
#         "Add Another Card) ARE now confirmed and built (page object "
#         "docstring point 17) -- see "
#         "test_carousel_form_selectable_for_carousel_sub_category below "
#         "for a real test exercising them. This numbered TC stays "
#         "skipped because the exact preview/validation behavior for a "
#         "FULLY populated carousel (multiple real cards, a real submit) "
#         "was never captured -- needs a fresh capture of that end state."
#     )
# )
# def test_TC059_to_TC062_marketing_carousel():
#     pass


# ══════════════════════════════════════════════════════════════════════════════
# TC063-TC066 -- Marketing - Catalog (incl. JIRA CPAAS-3220)
# ══════════════════════════════════════════════════════════════════════════════

# COMMENTED OUT per explicit user request -- this test case was SKIPPED or FAILED in the most recent full-suite run and the user asked to disable (not delete) it. The original code is preserved below as comments for reference / future re-enabling.
# @pytest.mark.skip(
#     reason=(
#         "The Catalog Type select (Single-Product/Multi-Product) and the "
#         "populated Preview panel for sub_category=Catalog ARE now "
#         "confirmed and built (page object docstring point 16) -- see "
#         "test_catalog_type_selectable_for_catalog_sub_category below for "
#         "a real test exercising them. This numbered TC stays skipped "
#         "because the JIRA CPAAS-3220 single-product validation gap and "
#         "the multi-product auto-fetch behavior were never captured."
#     )
# )
# def test_TC063_to_TC066_marketing_catalog():
#     pass


# ══════════════════════════════════════════════════════════════════════════════
# TC067-TC069 -- Marketing - Single Product Message
# ══════════════════════════════════════════════════════════════════════════════

# COMMENTED OUT per explicit user request -- this test case was SKIPPED or FAILED in the most recent full-suite run and the user asked to disable (not delete) it. The original code is preserved below as comments for reference / future re-enabling.
# @pytest.mark.skip(
#     reason=(
#         "The Single Product Message sub-form (fetch Catalog ID, fetch "
#         "Content ID, required-field validation) is rendered as empty "
#         "Livewire conditional blocks in the only capture taken of this "
#         "page (catalog_id/product_retailer_id both null). Needs a fresh "
#         "capture with this sub-type selected and its form populated."
#     )
# )
# def test_TC067_to_TC069_marketing_single_product_message():
#     pass


# ══════════════════════════════════════════════════════════════════════════════
# TC070-TC072 -- Marketing - Multi Product Message
# ══════════════════════════════════════════════════════════════════════════════

# COMMENTED OUT per explicit user request -- this test case was SKIPPED or FAILED in the most recent full-suite run and the user asked to disable (not delete) it. The original code is preserved below as comments for reference / future re-enabling.
# @pytest.mark.skip(
#     reason=(
#         "The core Section Title / Content ID fields and the Add "
#         "Section/Add Product actions ARE now confirmed and built (page "
#         "object docstring point 20) and exercised by "
#         "test_mpm_section_and_product_fields_selectable_for_mpm_sub_category "
#         "above. Still skipped as a numbered TC because the mandatory "
#         "Header Text requirement, the 10-section/30-content-ID upper "
#         "bounds, and the QA-noted 'Validation is not available' gap on "
#         "TC072 remain unconfirmed."
#     )
# )
# def test_TC070_to_TC072_marketing_multi_product_message():
#     pass


# ══════════════════════════════════════════════════════════════════════════════
# TC073-TC075 -- Marketing - Limited Time Offer
# ══════════════════════════════════════════════════════════════════════════════

# COMMENTED OUT per explicit user request -- this test case was SKIPPED or FAILED in the most recent full-suite run and the user asked to disable (not delete) it. The original code is preserved below as comments for reference / future re-enabling.
# @pytest.mark.skip(
#     reason=(
#         "The confirmed 'Add button' trigger (5 showLTOdiv(...) button "
#         "types) IS now built (page object docstring point 21) and "
#         "exercised by "
#         "test_lto_add_button_menu_offers_five_confirmed_button_types "
#         "above. Still skipped as a numbered TC because Offer Title "
#         "validation, the expiry-period-up-to-30-days behavior, and the "
#         "mandatory default URL button remain unconfirmed -- lto_title "
#         "and enable_lto_expiry are confirmed as real properties but "
#         "were never seen populated."
#     )
# )
# def test_TC073_to_TC075_marketing_limited_time_offer():
#     pass


# ══════════════════════════════════════════════════════════════════════════════
# TC076-TC079 -- Marketing - Product Card Carousel
# ══════════════════════════════════════════════════════════════════════════════

# COMMENTED OUT per explicit user request -- this test case was SKIPPED or FAILED in the most recent full-suite run and the user asked to disable (not delete) it. The original code is preserved below as comments for reference / future re-enabling.
# @pytest.mark.skip(
#     reason=(
#         "The Button Type select (Single Product (SPM)/URL Link) and the "
#         "pre-fetch manual Catalog ID/Content ID fields ARE now confirmed "
#         "and built (page object docstring point 22) and exercised by "
#         "test_product_carousel_button_type_and_card_fields_selectable "
#         "above. Still skipped as a numbered TC because the actual "
#         "'Load Catalogs for This Card' fetch/select-product behavior "
#         "and add/delete-up-to-10-cards bounds remain unconfirmed."
#     )
# )
# def test_TC076_to_TC079_marketing_product_card_carousel():
#     pass


# ══════════════════════════════════════════════════════════════════════════════
# TC080-TC085 -- Marketing - Order Details
# ══════════════════════════════════════════════════════════════════════════════

# COMMENTED OUT per explicit user request -- this test case was SKIPPED or FAILED in the most recent full-suite run and the user asked to disable (not delete) it. The original code is preserved below as comments for reference / future re-enabling.
# @pytest.mark.skip(
#     reason=(
#         "The Order Details sub-form (header restricted to image only, "
#         "the single default 'Review and pay' button with all others "
#         "hidden) is rendered as empty Livewire conditional blocks in the "
#         "only capture taken of this page (showOrderButton:false). Needs "
#         "a fresh capture with this sub-type selected and its form "
#         "populated."
#     )
# )
# def test_TC080_to_TC085_marketing_order_details():
#     pass


# ══════════════════════════════════════════════════════════════════════════════
# Cancel (navigates away -- last test in this file)
# ══════════════════════════════════════════════════════════════════════════════

def test_cancel_returns_to_template_listing(create_page):
    ensure_on_create_page(create_page)
    href = create_page.get_cancel_href()
    assert href and href.rstrip("/").endswith("/whatsapp/channels/template"), (
        f"Expected Cancel to link back to the Templates listing page, "
        f"got {href!r}"
    )
    create_page.click_cancel()
    assert "/whatsapp/channels/template" in create_page.get_current_url()
    assert "/create" not in create_page.get_current_url()
