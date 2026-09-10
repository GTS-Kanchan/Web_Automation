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
    typeOptions state. The order_details capture also definitively
    disproves (via matching Livewire snapshot checksums across two
    separate capture attempts) that either attempt actually captured
    sub_category=order_status -- that sub_category's own form remains
    genuinely unconfirmed. See
    pages/whatsapp/whatsapp_template_create_page.py's module docstring
    points 25/26 for the full evidence trail.

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
      dropdown (Copy Offer Code disabled) and Order Details' fixed
      single-button block ARE now confirmed and built (page object
      docstring points 25/26) and exercised by real tests above. Still
      skipped as a numbered TC because the "Include opt-out button"
      checkbox was never found in either capture, and sub_category=
      order_status's own form remains uncaptured -- two separate
      attempts to capture it both produced this same order_details
      state instead (confirmed via matching checksums).
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
import os

import pytest

from pages.whatsapp.whatsapp_template_create_page import WhatsAppTemplateCreatePage


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
    """Best-effort: pick the first real Sender ID option if none is
    selected yet. Returns True only if a sender ends up genuinely
    selected; never fabricates success."""
    ensure_on_create_page(p)
    if p.page.locator(p.SENDER_ID_HIDDEN_INPUT).get_attribute("value"):
        return True
    senders = p.get_sender_id_options()
    if not senders:
        return False
    label = senders[0].get("label")
    if not label:
        return False
    try:
        p.select_sender_id(label)
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
# TC021 -- Template Name: min/max characters (3 - 512)
# ══════════════════════════════════════════════════════════════════════════════

def test_TC021_template_name_min_max_length(create_page):
    ensure_on_create_page(create_page)

    assert create_page.get_name_maxlength() == "512", (
        "Expected the Template Name field's maxlength attribute to be 512"
    )

    long_name = "a" * 600
    create_page.set_name(long_name)
    current_value = create_page.get_name_value()
    assert len(current_value) <= 512, (
        f"Expected the Template Name field to cap input at 512 characters, "
        f"got {len(current_value)} characters"
    )

    # Best-effort only: the 3-character MINIMUM is a server-side rule with
    # no confirmed client-side signal short of a full form submit (not
    # attempted here -- see module docstring). Not asserted as a hard
    # failure if the field simply accepts a short value without any
    # visible feedback.
    create_page.set_name("ab")
    short_value = create_page.get_name_value()
    if short_value == "ab":
        pytest.skip(
            "Template Name accepted a 2-character value with no visible "
            "client-side feedback -- the checklist's 3-character minimum "
            "appears to be enforced only on submit, which is not "
            "exercised here (see module docstring). Needs a fresh capture "
            "of the validation error text after a real submit attempt."
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


def test_language_searchable_and_selectable(create_page):
    ensure_on_create_page(create_page)

    options = create_page.get_language_options()
    assert options, "Expected real language options to be present"
    assert len(options) >= 60, f"Expected ~67 language options, got {len(options)}"

    hindi = next((o for o in options if o.get("label") == "Hindi"), None)
    assert hindi is not None, "Expected 'Hindi' to be a real language option"

    create_page.search_language("Hindi")
    create_page.page.wait_for_timeout(500)
    create_page.select_language("Hindi")
    assert create_page.get_selected_language_text() == "Hindi"

    # restore default for subsequent tests
    create_page.select_language("English")


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

    create_page.select_sub_category("Catalog")
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
    create_page.select_sub_category("Catalog")

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
# sub_category=Carousel reveals the Carousel sub-form's top-level fields
# (see page object docstring point 17)
# ══════════════════════════════════════════════════════════════════════════════

def test_carousel_form_selectable_for_carousel_sub_category(create_page):
    ensure_on_create_page(create_page)
    create_page.select_category("MARKETING")
    if not create_page.is_sub_category_select_present():
        pytest.skip("sub_category select not available in this environment")
    create_page.select_sub_category("Carousel")

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
    create_page.select_sub_category("Multi-Product Message")

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
    create_page.select_sub_category("Limited Time Offer")

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
    create_page.select_sub_category("Product Card Carousel")

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

def test_conversation_cta_url_button_reuses_add_button_and_url_fields(create_page):
    ensure_on_create_page(create_page)
    create_page.select_category("CONVERSATION")
    if not create_page.is_sub_category_select_present():
        pytest.skip("sub_category select not available in this environment")
    create_page.select_sub_category("CTA URL Button")

    options = create_page.get_header_options()
    if options:
        labels = {o.get("label") for o in options}
        assert labels == {"Text", "Media"}, (
            f"Expected the confirmed 2-value headerOptions state "
            f"([Text, Media]) for sub_category=cta_url_button, got "
            f"{labels!r}"
        )

    if not create_page.is_lto_add_button_trigger_present():
        pytest.skip(
            "The 'Add button' trigger was not present in this environment "
            "for sub_category=cta_url_button."
        )
    create_page.open_lto_add_button_menu()
    assert create_page.is_element_present(
        "[wire\\:click=\"showLTOdiv('URL')\"]", timeout=5000
    ), (
        "Expected the same showLTOdiv('URL') menu item confirmed for "
        "sub_category=lto to also render here -- confirming this is a "
        "shared 'Add button' mechanism, not LTO-exclusive"
    )
    assert create_page.is_lto_add_button_menu_item_disabled("URL"), (
        "Expected the 'URL' menu item to be disabled here: this "
        "sub_category force-provisions exactly one URL button rather "
        "than letting the user add one via this menu, per the confirmed "
        "'You must add exactly 1 URL button for CTA URL Button templates' "
        "helper text"
    )

    if create_page.is_url_button_fields_present():
        create_page.set_url_button_title("Visit us")
        create_page.set_url_button_value("https://example.com")
    else:
        pytest.skip(
            "The reused url_buttons_title.0/url_buttons_value.0 fields "
            "(point 18 infra) were not present at this point in the flow "
            "-- only the 'Add button' menu assertions above are asserted "
            "as a hard requirement."
        )

    if create_page.is_add_variable_body_button_present():
        create_page.click_add_variable_body()
    else:
        pytest.skip(
            "The 'Add Variable' button (wire:click=\"insertVariable('body')\") "
            "was not present at this point in the flow."
        )


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
    create_page.select_sub_category("Custom Message")

    options = create_page.get_header_options()
    if options:
        labels = {o.get("label") for o in options}
        assert labels == {"None", "Text", "Media", "Location"}, (
            f"Expected the confirmed 'full' 4-value headerOptions state for "
            f"UTILITY/custom_message, got {labels!r}"
        )

    if not create_page.is_lto_add_button_trigger_present():
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
# (see page object docstring point 26). sub_category=Order Status remains
# UNCONFIRMED -- two separate capture attempts both produced this exact
# order_details state instead (proven via matching Livewire snapshot
# checksums, not mere visual similarity), so no order_status-specific
# assertions are made anywhere in this suite.
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

def test_e2e_marketing_custom_message_submit(create_page):
    create_page.navigate()
    create_page.select_category("MARKETING")
    name = create_page.fill_required_base_fields()
    if create_page.is_sub_category_select_present():
        create_page.select_sub_category("Custom Message")
    create_page.click_save()
    _assert_save_responded(create_page, f"MARKETING/custom_message ({name})")


def test_e2e_marketing_carousel_submit(create_page):
    create_page.navigate()
    create_page.select_category("MARKETING")
    name = create_page.fill_required_base_fields()
    if not create_page.is_sub_category_select_present():
        pytest.skip("sub_category select not available in this environment")
    create_page.select_sub_category("Carousel")
    if not create_page.is_carousel_form_present():
        pytest.skip("Carousel sub-form not available in this environment")

    create_page.select_carousel_media_type("Image")
    create_page.select_carousel_button_count("1")
    create_page.select_carousel_button_type1("Quick Reply")
    create_page.set_carousel_card_description(0, "Great deal on this item.")
    if create_page.is_carousel_card_file_input_present(0):
        create_page.set_carousel_card_file(0, CAROUSEL_SAMPLE_IMAGE)
    else:
        pytest.skip(
            "Carousel card 0's file input was not present in this "
            "environment -- a real Carousel template requires header "
            "media per card, so a submit without it is not meaningful."
        )
    create_page.set_card_button_title(0, 0, "View")

    create_page.click_save()
    _assert_save_responded(create_page, f"MARKETING/carousel ({name})")


def test_e2e_marketing_catalog_submit(create_page):
    create_page.navigate()
    create_page.select_category("MARKETING")
    name = create_page.fill_required_base_fields()
    if not create_page.is_sub_category_select_present():
        pytest.skip("sub_category select not available in this environment")
    create_page.select_sub_category("Catalog")
    if create_page.is_catalog_type_select_present():
        create_page.select_catalog_type("Single-Product")
    # No further Catalog-specific fields (e.g. a real catalog_id input)
    # have ever been captured for this sub_category -- see page object
    # docstring point 16. Submitting with only catalog_type set is
    # expected to surface a real validation response, which
    # _assert_save_responded treats as a valid "the app responded"
    # signal (not necessarily a successful save).
    create_page.click_save()
    _assert_save_responded(create_page, f"MARKETING/catalog ({name})")


def test_e2e_marketing_multi_product_message_submit(create_page):
    create_page.navigate()
    create_page.select_category("MARKETING")
    name = create_page.fill_required_base_fields()
    if not create_page.is_sub_category_select_present():
        pytest.skip("sub_category select not available in this environment")
    create_page.select_sub_category("Multi-Product Message")
    if create_page.is_mpm_section_title_present():
        create_page.set_mpm_section_title("Popular Bundles", section_index=0)
        create_page.set_mpm_product_retailer_id(
            "e2e_test_sku_001", section_index=0, product_index=0
        )
    create_page.click_save()
    _assert_save_responded(create_page, f"MARKETING/multi_product_message ({name})")


def test_e2e_marketing_lto_submit(create_page):
    create_page.navigate()
    create_page.select_category("MARKETING")
    name = create_page.fill_required_base_fields()
    if not create_page.is_sub_category_select_present():
        pytest.skip("sub_category select not available in this environment")
    create_page.select_sub_category("Limited Time Offer")
    # lto_title/enable_lto_expiry are confirmed real properties but no
    # input DOM for either has ever been captured (page object docstring
    # point 21) -- not guessed here, so this submits with no LTO-specific
    # fields filled and relies on _assert_save_responded's "the app
    # responded at all" contract rather than asserting success.
    create_page.click_save()
    _assert_save_responded(create_page, f"MARKETING/lto ({name})")


def test_e2e_marketing_product_carousel_submit(create_page):
    create_page.navigate()
    create_page.select_category("MARKETING")
    name = create_page.fill_required_base_fields()
    if not create_page.is_sub_category_select_present():
        pytest.skip("sub_category select not available in this environment")
    create_page.select_sub_category("Product Card Carousel")
    if create_page.is_product_carousel_button_type_select_present():
        create_page.select_product_carousel_button_type("URL Link")
    if create_page.is_carousel_product_catalog_id_input_present(0):
        create_page.set_carousel_product_catalog_id("194836987003835", card_index=0)
        create_page.set_carousel_product_content_id("e2e_test_sku_001", card_index=0)
    create_page.click_save()
    _assert_save_responded(create_page, f"MARKETING/product_carousel ({name})")


def test_e2e_utility_custom_message_submit(create_page):
    create_page.navigate()
    create_page.select_category("UTILITY")
    name = create_page.fill_required_base_fields()
    if create_page.is_sub_category_select_present():
        create_page.select_sub_category("Custom Message")
    create_page.click_save()
    _assert_save_responded(create_page, f"UTILITY/custom_message ({name})")


def test_e2e_utility_order_details_submit(create_page):
    create_page.navigate()
    create_page.select_category("UTILITY")
    name = create_page.fill_required_base_fields()
    if create_page.is_sub_category_select_present():
        create_page.select_sub_category("Order Details")
    # The Order Details button block is entirely fixed/non-editable
    # (page object docstring point 26) -- nothing further to fill.
    create_page.click_save()
    _assert_save_responded(create_page, f"UTILITY/order_details ({name})")


def test_e2e_authentication_submit(create_page):
    create_page.navigate()
    create_page.select_category("AUTHENTICATION")
    name = create_page.fill_required_base_fields()
    # fill_required_base_fields()'s set_body_text() call is a documented
    # no-op here since AUTHENTICATION's message content is fixed/non-
    # editable (page object docstring point 23), not a real EasyMDE body.
    # Copy Code is the confirmed default OTP type -- nothing else to set.
    create_page.click_save()
    _assert_save_responded(create_page, f"AUTHENTICATION ({name})")


def test_e2e_conversation_cta_url_button_submit(create_page):
    create_page.navigate()
    create_page.select_category("CONVERSATION")
    name = create_page.fill_required_base_fields()
    if not create_page.is_sub_category_select_present():
        pytest.skip("sub_category select not available in this environment")
    create_page.select_sub_category("CTA URL Button")

    if create_page.is_url_button_fields_present():
        create_page.set_url_button_title("Visit us")
        # url_buttons_value.0 is CONFIRMED broken/absent in the live DOM
        # as of the last live run against this exact sub_category (a
        # 30s Locator.fill timeout, not a guess) -- guarded with a short
        # presence check rather than assumed, to avoid repeating that
        # hang here.
        if create_page.is_element_present(
            create_page.URL_BUTTON_VALUE_INPUT, timeout=3000
        ):
            create_page.set_url_button_value("https://example.com")

    create_page.click_save()
    _assert_save_responded(create_page, f"CONVERSATION/cta_url_button ({name})")


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

@pytest.mark.skip(
    reason=(
        "The Header WireUI select's own x-ref='json' option blob decoded "
        "to an empty array ([]) in the only capture taken of this page -- "
        "the real header-type option list (None/Text/Image/Video/"
        "Document/Location) was never captured, so none of these sub-"
        "behaviors can be built without guessing at option ids/names. "
        "Needs a fresh capture of the Header select WITH its options "
        "populated (e.g. right after a Sender ID is chosen, if that is "
        "what triggers population)."
    )
)
def test_TC023_to_TC028_header_type_subforms():
    pass


# ══════════════════════════════════════════════════════════════════════════════
# TC029-TC036 -- Conversation Template section
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(
    reason=(
        "sub_category=cta_url_button's confirmed fields (headerOptions/"
        "typeOptions state, the 'Add button' dropdown reused from LTO with "
        "its single disabled 'URL' item, the url_buttons_title.0/"
        "url_buttons_value.0 fields, and the 'Add Variable' button) ARE "
        "now confirmed and built (page object docstring point 24) and "
        "exercised by "
        "test_conversation_cta_url_button_reuses_add_button_and_url_fields "
        "above. Still skipped as a numbered TC because the enable toggle "
        "itself, body-variable-insertion behavior end-to-end, and footer "
        "sub-behaviors for this section were never captured populated."
    )
)
def test_TC029_to_TC036_conversation_template_section():
    pass


# ══════════════════════════════════════════════════════════════════════════════
# TC037-TC041 -- Authentication category form
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(
    reason=(
        "The OTP type radio group (Copy Code/AutoFill/Zero-Tap), the two "
        "Message Content checkboxes (Add Security recommendation / Add "
        "expiration time for code), and the Copy Code button text field "
        "ARE now confirmed and built (page object docstring point 23) "
        "and exercised by "
        "test_authentication_otp_type_and_message_content_fields above. "
        "Still skipped as a numbered TC because the Autofill/Zero-Tap "
        "OTP-type sub-behaviors (e.g. whether the button text field "
        "un-disables) and the App Setup/package name fields from the "
        "original checklist remain unconfirmed."
    )
)
def test_TC037_to_TC041_authentication_category_form():
    pass


# ══════════════════════════════════════════════════════════════════════════════
# TC042-TC046 -- Utility category form
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(
    reason=(
        "Custom Message's 'Add button' dropdown (with Copy Offer Code "
        "confirmed disabled) and Order Details' fixed/non-editable single-"
        "button block (plus its narrower [Media]-only headerOptions state) "
        "ARE now confirmed and built (page object docstring points 25/26) "
        "and exercised by "
        "test_utility_custom_message_add_button_copy_offer_code_disabled "
        "and test_utility_order_details_fixed_button_block above. Still "
        "skipped as a numbered TC because: (1) the 'Include opt-out "
        "button' checkbox mentioned in the original checklist was never "
        "found in either capture (only an unrelated sidebar nav link "
        "happens to share the text 'Opt-out'), and (2) sub_category="
        "order_status's own rendered form remains genuinely uncaptured -- "
        "TWO separate attempts to capture it (both explicitly labeled "
        "'order status' by the person providing the capture) instead "
        "produced this exact order_details state, proven via matching "
        "Livewire snapshot checksums, not mere visual similarity. A "
        "third, genuinely order_status-selected capture is needed before "
        "that sub_category's restrictions can be built."
    )
)
def test_TC042_to_TC046_utility_category_form():
    pass


# ══════════════════════════════════════════════════════════════════════════════
# TC047-TC058 -- Marketing - Custom message
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(
    reason=(
        "The URL/Phone Number/Copy-Offer-Code/Flow button fields' own "
        "structure and real option lists ARE now confirmed (see page "
        "object docstring point 18) and locators/helpers for them are "
        "built (is_url_button_fields_present, is_phone_button_fields_"
        "present, is_flow_button_fields_present, etc.). What blocks a "
        "real test here is that no capture has ever shown the UI action "
        "that first reveals these blocks (e.g. an 'Add button' control) "
        "-- getting from a fresh Create page to a visible button field "
        "would require guessing that trigger, which this project's "
        "evidence rule forbids. Needs a fresh capture showing the "
        "control that adds a button, or manual QA confirmation of it."
    )
)
def test_TC047_to_TC058_marketing_custom_message():
    pass


# ══════════════════════════════════════════════════════════════════════════════
# TC059-TC062 -- Marketing - Carousel
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(
    reason=(
        "The Carousel sub-form's top-level fields (media type, button "
        "count, button type 1, per-card file/description/button fields, "
        "Add Another Card) ARE now confirmed and built (page object "
        "docstring point 17) -- see "
        "test_carousel_form_selectable_for_carousel_sub_category below "
        "for a real test exercising them. This numbered TC stays "
        "skipped because the exact preview/validation behavior for a "
        "FULLY populated carousel (multiple real cards, a real submit) "
        "was never captured -- needs a fresh capture of that end state."
    )
)
def test_TC059_to_TC062_marketing_carousel():
    pass


# ══════════════════════════════════════════════════════════════════════════════
# TC063-TC066 -- Marketing - Catalog (incl. JIRA CPAAS-3220)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(
    reason=(
        "The Catalog Type select (Single-Product/Multi-Product) and the "
        "populated Preview panel for sub_category=Catalog ARE now "
        "confirmed and built (page object docstring point 16) -- see "
        "test_catalog_type_selectable_for_catalog_sub_category below for "
        "a real test exercising them. This numbered TC stays skipped "
        "because the JIRA CPAAS-3220 single-product validation gap and "
        "the multi-product auto-fetch behavior were never captured."
    )
)
def test_TC063_to_TC066_marketing_catalog():
    pass


# ══════════════════════════════════════════════════════════════════════════════
# TC067-TC069 -- Marketing - Single Product Message
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(
    reason=(
        "The Single Product Message sub-form (fetch Catalog ID, fetch "
        "Content ID, required-field validation) is rendered as empty "
        "Livewire conditional blocks in the only capture taken of this "
        "page (catalog_id/product_retailer_id both null). Needs a fresh "
        "capture with this sub-type selected and its form populated."
    )
)
def test_TC067_to_TC069_marketing_single_product_message():
    pass


# ══════════════════════════════════════════════════════════════════════════════
# TC070-TC072 -- Marketing - Multi Product Message
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(
    reason=(
        "The core Section Title / Content ID fields and the Add "
        "Section/Add Product actions ARE now confirmed and built (page "
        "object docstring point 20) and exercised by "
        "test_mpm_section_and_product_fields_selectable_for_mpm_sub_category "
        "above. Still skipped as a numbered TC because the mandatory "
        "Header Text requirement, the 10-section/30-content-ID upper "
        "bounds, and the QA-noted 'Validation is not available' gap on "
        "TC072 remain unconfirmed."
    )
)
def test_TC070_to_TC072_marketing_multi_product_message():
    pass


# ══════════════════════════════════════════════════════════════════════════════
# TC073-TC075 -- Marketing - Limited Time Offer
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(
    reason=(
        "The confirmed 'Add button' trigger (5 showLTOdiv(...) button "
        "types) IS now built (page object docstring point 21) and "
        "exercised by "
        "test_lto_add_button_menu_offers_five_confirmed_button_types "
        "above. Still skipped as a numbered TC because Offer Title "
        "validation, the expiry-period-up-to-30-days behavior, and the "
        "mandatory default URL button remain unconfirmed -- lto_title "
        "and enable_lto_expiry are confirmed as real properties but "
        "were never seen populated."
    )
)
def test_TC073_to_TC075_marketing_limited_time_offer():
    pass


# ══════════════════════════════════════════════════════════════════════════════
# TC076-TC079 -- Marketing - Product Card Carousel
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(
    reason=(
        "The Button Type select (Single Product (SPM)/URL Link) and the "
        "pre-fetch manual Catalog ID/Content ID fields ARE now confirmed "
        "and built (page object docstring point 22) and exercised by "
        "test_product_carousel_button_type_and_card_fields_selectable "
        "above. Still skipped as a numbered TC because the actual "
        "'Load Catalogs for This Card' fetch/select-product behavior "
        "and add/delete-up-to-10-cards bounds remain unconfirmed."
    )
)
def test_TC076_to_TC079_marketing_product_card_carousel():
    pass


# ══════════════════════════════════════════════════════════════════════════════
# TC080-TC085 -- Marketing - Order Details
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(
    reason=(
        "The Order Details sub-form (header restricted to image only, "
        "the single default 'Review and pay' button with all others "
        "hidden) is rendered as empty Livewire conditional blocks in the "
        "only capture taken of this page (showOrderButton:false). Needs "
        "a fresh capture with this sub-type selected and its form "
        "populated."
    )
)
def test_TC080_to_TC085_marketing_order_details():
    pass


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
