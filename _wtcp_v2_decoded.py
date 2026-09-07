"""
Page Object: WhatsApp Template Create page
Path: /whatsapp/channels/template/create
Livewire component: whatsapp.meta.create

Built from a genuine, pasted live-DOM capture of this exact page (captured
mid-session; the component's wire:id is session-specific and NOT hardcoded
anywhere below -- only stable ids/names/attributes are used).

Confirmed facts from the real capture (do not "fix" these without a fresh
capture proving otherwise):

 1. Breadcrumb trail is Home > Channels > WhatsApp Templates > "WhatsApp
    Template Create" -- the last crumb is a plain <span>, not a link (same
    convention as the Campaign Create page).
 2. Header: <h1 class="text-md font-semibold whitespace-nowrap">Create New
    WhatsApp Template</h1>.
 3. Sender ID: WireUI searchable single-select, form-wrapper="senderId",
    hidden input id="senderId". The real option list IS present in this
    capture as a base64 JSON blob in the select's own x-ref="json" div: 9
    real sender ids/names (e.g. "WhatsApp Simulator Testing
    ( 919691926438 )"), each a {"label", "value"} pair. As with every
    other WireUI select already confirmed elsewhere in this codebase, the
    rendered <li> option rows only hydrate client-side via Alpine's x-for
    -- since Playwright drives the live page, real role="listitem" rows
    DO render at runtime and are matched by that generic ARIA role plus
    real, confirmed label text.
 4. Template Name: <input id="name" name="name"
    wire:model.live.debounce.200ms="name" maxlength="512">. The checklist
    (TC020/TC021) claims the live app only accepts lowercase letters,
    digits and underscore, and enforces a 3-512 character range. The
    upper bound (512) is directly confirmed via the maxlength attribute.
    The lowercase/digit/underscore restriction and the 3-character lower
    bound are SERVER-side behaviors (wire:model.live.debounce, not a
    client regex/pattern attribute) that are not visible in a static
    capture -- they are exercised at runtime in the test suite by typing
    disallowed input and reading back the live post-debounce value,
    rather than assumed from the checklist prose alone.
 5. Category: exactly 4 real, confirmed <input type="radio"
    name="category"> values -- id="marketing" value="MARKETING",
    id="utility" value="UTILITY", id="authentication"
    value="AUTHENTICATION", id="conversation" value="CONVERSATION" -- all
    wire:model.live.debounce.200ms="category".
 6. Language: WireUI searchable single-select, form-wrapper="language",
    optionValue='code'/optionLabel='name'. The real option list is a
    base64 JSON blob of 67 real language rows (Eloquent-model-shaped,
    each still exposing a plain {"label", "value"} pair, e.g.
    {"label": "English", "value": "en"}, {"label": "Hindi", "value":
    "hi"}). The Livewire snapshot's initial state already has
    "language":"en", and the select's own displayed text in this capture
    already shows "English" as pre-selected (getSelectedDisplayText() ->
    "<span>English</span>") -- i.e. Language defaults to English on page
    load, confirmed structurally, not guessed.
 7. Template Labels: <input id="label" name="label" wire:model="label"
    placeholder="Enter label">. No maxlength attribute observed on this
    field in the capture.
 8. Header: WireUI searchable single-select, form-wrapper="header",
    optionValue='id'/optionLabel='name', placeholder "Select Header
    Type". UNLIKE Sender ID and Language, this select's own x-ref="json"
    blob decoded to an EMPTY array ("W10=" -> []) in this single "nothing
    selected yet" capture -- the real header-type option list (None /
    Text / Image / Video / Document / Location, per the checklist) was
    never captured. Only the select's open/search mechanics (shared,
    already-confirmed WireUI plumbing) are built here; a fresh capture
    with real header options populated (or the values simply hard-coded
    with a manual QA confirmation) is needed before TC023-TC028 can be
    built.
 9. Body: NOT a plain <textarea>/<input> -- it's an EasyMDE/CodeMirror
    rich-text editor, wired via a custom Alpine component
    `easyMDEComponent(window.Livewire.find('<id>').entangle('body'),
    1024)` (the "1024" is the field's max length, passed as the second
    constructor arg). A confirmed inline <script> block on this exact
    page shows the app's OWN mechanism for inserting a variable into this
    field: it looks up the CodeMirror instance via
    `document.querySelector('[wire\\:key^="editor-"] .CodeMirror').CodeMirror`
    and calls `cm.replaceSelection(variable)` / `cm.setValue(...)` /
    `cm.getValue()`. get_body_text()/set_body_text() below reuse that
    EXACT confirmed selector and CodeMirror API rather than attempting a
    plain Playwright .fill() (which would not work against a CodeMirror
    instance backing a hidden source <textarea>).
10. Footer Text: <input id="footer_text" name="footer_text"
    wire:model.live.debounce.200ms="footer_text" maxlength="60"
    placeholder="Footer text">. maxlength=60 confirmed directly.
11. Save/Submit button: <button type="submit" wire:click.prevent="submit"
    :disabled="!$wire.senderId">Save</button> -- structurally, provably
    disabled until Sender ID is populated (Alpine binding, not a guess).
    There is exactly one type="submit" button on this page.
12. Cancel: a single <a href=".../whatsapp/channels/template">Cancel</a>
    (goes back to the Templates LISTING page) -- the only element on this
    entire page containing the literal text "Cancel", so a simple
    normalize-space() text match is unambiguous.
13. A "Preview" panel (<h1 class="p-4 ...">Preview</h1>, same heading
    text/style already confirmed on the Templates listing page's own
    Preview panel) sits alongside the form, but in this "nothing selected
    yet" capture its body is entirely empty conditional blocks
    (<!--[if BLOCK]><![endif]-->) -- no real populated content was ever
    captured for it here, so it is not built beyond a presence check.
14. ALL category-conditional sub-forms (Conversation Template enable
    toggle + CTA URL Button type; the entire Authentication category
    form; the entire Utility category form) correspond to Livewire
    boolean flags (showAuthentication, showUtility, conversation_enabled,
    etc.) that were still `false`/empty in every capture taken of this
    page, with their corresponding markup rendered as empty
    <!--[if BLOCK]><![endif]--><!--[if ENDBLOCK]><![endif]--> Livewire
    placeholders. None of that DOM has ever been captured for real, so
    NONE of it is built here -- see the test suite's module docstring for
    the full list of checklist items deliberately left as documented
    skips, and exactly what additional captures would unblock each one.

15. Marketing sub_category: a SECOND WireUI searchable single-select,
    form-wrapper="sub_category", placeholder "Select Template Type",
    optionValue='id'/optionLabel='name' -- same plumbing pattern as
    Sender ID/Language. Rendered only once category=MARKETING is
    selected. Its own x-ref="json" blob decoded (via a genuine capture
    with category=MARKETING active) to exactly 8 real values: Custom
    Message (custom_message), Carousel (carousel), Catalog
    (catalog_message), Multi-Product Message (multi_product_message),
    Limited Time Offer (lto), Product Card Carousel (product_carousel),
    Single Product Messages (spm), Order Details (order_details).
    Confirmed via this exact select's own wireModel blob decoding to
    {"name":"sub_category","livewireId":"dTL8ceOhB3LUbrB6lWrz"} -- i.e.
    this select provably belongs to the SAME whatsapp.meta.create
    component instance as every other locator in this file, not a
    separate/unrelated capture.

16. Marketing sub_category = Catalog (catalog_message) reveals a THIRD
    WireUI searchable single-select, form-wrapper="catalog_type",
    placeholder "Select Catalog Type", with a confirmed 2-option list:
    Single-Product (single_product), Multi-Product (multi_product). Its
    own wireModel blob likewise decodes to
    {"name":"catalog_type","livewireId":"dTL8ceOhB3LUbrB6lWrz"} --
    confirmed same component. This is the ONLY sub_category whose
    top-level select and Preview panel content have been captured
    populated for real (Preview shows a chat-bubble card headed "View
    {BIZ_NAME}'s Catalog on WhatsA....." with body text "Browse pictures
    and details of their offerings." plus a separate "View catalog"
    button-preview card) -- TC063-TC066 is still left as a documented
    skip below because the JIRA CPAAS-3220 single-product validation
    behavior and the multi-product auto-fetch behavior remain
    unconfirmed; only the select-and-preview mechanics above are solid.

17. Marketing sub_category = Carousel reveals a Carousel sub-form,
    confirmed via a genuine capture with sub_category=carousel active:
      - form-wrapper="carousel_media_type" (WireUI select, label
        "Header media type"): 2 real options, Image (IMAGE) / Video
        (VIDEO).
      - form-wrapper="carousel_button" (WireUI select, label "No of
        buttons"): 2 real options, "1" (1) / "2" (2) -- controls how
        many "Button type N" selects render below (only "Button type 1"
        renders when carousel_button=1, confirmed structurally).
      - form-wrapper="carousel_button_type1" (and, when
        carousel_button=2, a second "carousel_button_type2" -- NOT
        itself captured, only inferred from the "1"/"2" naming
        convention and the wire:snapshot's own carousel_button_type2
        key existing alongside carousel_button_type1): 4 real options,
        URL (URL) / Quick Reply ("Quick Reply") / Phone Number ("Phone
        Number") / WhatsApp Flow (FLOW).
      - Per card (index i, 0-based -- up to maxCardFieldCount=10 per the
        wire:snapshot): a file input (wire:model="carousel_file.{i}",
        accept="image/*"), a Description textarea
        (form-wrapper/id="carousel_description.{i}",
        wire:model.live.debounce.200ms, maxlength="160"), and per card
        one button block per cardFieldCount whose own fields are named
        card_buttons_type.{card}.{button} (readonly select mirroring
        the carousel_button_typeN choice), card_buttons_title.{card}.
        {button} (plain input, wire:model.live.debounce.200ms), an
        optional card_buttons_url_type.{card}.{button} select
        (Static/Dynamic, only relevant for URL-type buttons) and
        card_buttons_value.{card}.{button} (plain input, plain
        wire:model). New cards are added via
        wire:click="addCardCount" ("Add Another Card" button) and
        removed via wire:click="removeCard({i})".
    All of the above field names (carousel_media_type, carousel_button,
    carousel_button_type1/2, carousel_description, carousel_file,
    card_buttons_type/title/url_type/value, cardFieldCount,
    maxCardFieldCount) are independently corroborated as real top-level
    properties of the SAME whatsapp.meta.create component via its own
    wire:snapshot JSON dump (not just the fragment capture) -- see the
    test suite docstring. TC059-TC062 is still left as a documented skip
    below because the exact preview/validation behavior for a fully
    populated carousel was never captured; only presence + selection
    mechanics above are solid.

18. Marketing sub_category = Custom message reveals a set of "Call to
    action" / Quick-Reply button config fields, confirmed via a genuine
    capture that provably belongs to this SAME component (each field's
    own wireModel blob decodes to
    "livewireId":"dTL8ceOhB3LUbrB6lWrz"):
      - URL button (index i, 0-based): form-wrapper="url_button_type.{i}"
        (readonly select, single option URL->URL),
        id="url_buttons_title.{i}" (plain input,
        wire:model.live.debounce.200ms, maxlength="25"),
        id="url_buttons_value.{i}" (plain input,
        wire:model.live.debounce.200ms, no maxlength, placeholder
        "https://example.com"), removed via
        wire:click="removeUrl({i})".
      - A shared "phone_button_type" select (label literally "Select
        Type", NOT "Call to action" -- confirmed exact label text;
        readonly, searchable:true per its x-props even though
        readonly:true) offering 3 real values that together cover 3
        different button kinds: Copy Offer Code ("Copy offer code"),
        URL ("URL"), Phone Number ("PHONE_NUMBER"). Alongside it,
        id="phone_button_title" (maxlength="25") and
        id="phone_button_value" (maxlength="20"). Removed via
        wire:click="removeData('Phone Number')" (the literal string
        argument confirmed from the capture; the same removeData(...)
        call presumably takes the OTHER two labels for the other two
        button kinds this shared selector covers, but that has NOT been
        directly captured for "Copy Offer Code" or "URL" and is not
        assumed here).
      - Flow button: form-wrapper="flow_button_type" (readonly select,
        single option Flow->FLOW), id="flow_button_title" (maxlength=
        "25", placeholder "Enter button title"), and
        form-wrapper="flow_button_value" -- a DIFFERENT, non-readonly,
        searchable:true WireUI select (NOT a plain input) whose own
        x-ref="json" blob is empty ("W10=" == []) because it is a live
        async-search dropdown rather than a fixed enum; the account's
        REAL Flow records (90 real {id, name} rows, e.g. {"id": 376,
        "name": "template node"}) are exposed separately via this same
        component's wire:snapshot under the "quick_reply_flows" key --
        that is the authoritative ground truth for this field's real
        values, not its own (empty) x-ref blob. Removed via
        wire:click="removeData('Flow')".
    The capture that produced this evidence does NOT include a
    wire:snapshot of its own governing show* flags (showURL,
    showphoneNumber, showcopyOfferCode, showFlow), so the exact UI
    action that first reveals each of these blocks (e.g. an "Add
    button" control) was never captured and is NOT guessed at here --
    only the fields' own structure/options are built as locators/decode
    helpers, ready to use once that trigger is confirmed. See TC047-
    TC058's skip below.

No cross-page inheritance/mixins per this project's established
convention (confirmed via `grep -rn "^class .*Page(" pages/ | grep -v
"BasePage"` returning zero matches) -- the small "open a WireUI select /
pick an option" helper below is a private method of THIS class only
(deliberately duplicated from WhatsAppCampaignCreatePage rather than
shared, per that convention), not a shared base.
"""
import base64
import json
import re

from pages.common.base_page import BasePage


class WhatsAppTemplateCreatePage(BasePage):
    PATH = "/whatsapp/channels/template/create"

    # Breadcrumb / header
    BREADCRUMB_ACTIVE = "xpath=//li[.//span[normalize-space()='WhatsApp Template Create']]"
    PAGE_HEADER = "xpath=//h1[normalize-space()='Create New WhatsApp Template']"

    # Sender ID (WireUI searchable single-select)
    SENDER_ID_WRAPPER = "[form-wrapper='senderId']"
    SENDER_ID_HIDDEN_INPUT = "#senderId"

    # Template Name
    NAME_INPUT = "#name"

    # Category (plain radio group)
    CATEGORY_MARKETING_RADIO = "#marketing"
    CATEGORY_UTILITY_RADIO = "#utility"
    CATEGORY_AUTHENTICATION_RADIO = "#authentication"
    CATEGORY_CONVERSATION_RADIO = "#conversation"

    # Language (WireUI searchable single-select, defaults to English/"en")
    LANGUAGE_WRAPPER = "[form-wrapper='language']"

    # Template Labels (optional, plain text)
    LABEL_INPUT = "#label"

    # Header type (WireUI searchable single-select -- real options NOT yet
    # confirmed, see module docstring point 8)
    HEADER_WRAPPER = "[form-wrapper='header']"

    # Body (EasyMDE/CodeMirror -- see module docstring point 9)
    BODY_EDITOR_CONTAINER = "[wire\\:key^='editor-']"

    # Footer Text
    FOOTER_INPUT = "#footer_text"

    # Marketing sub_category (WireUI searchable single-select, only
    # rendered when category=MARKETING -- see module docstring point 15)
    SUB_CATEGORY_WRAPPER = "[form-wrapper='sub_category']"

    # sub_category=catalog_message reveals this select (module docstring
    # point 16)
    CATALOG_TYPE_WRAPPER = "[form-wrapper='catalog_type']"

    # sub_category=carousel reveals this sub-form (module docstring
    # point 17)
    CAROUSEL_MEDIA_TYPE_WRAPPER = "[form-wrapper='carousel_media_type']"
    CAROUSEL_BUTTON_COUNT_WRAPPER = "[form-wrapper='carousel_button']"
    CAROUSEL_BUTTON_TYPE1_WRAPPER = "[form-wrapper='carousel_button_type1']"
    CAROUSEL_BUTTON_TYPE2_WRAPPER = "[form-wrapper='carousel_button_type2']"
    ADD_ANOTHER_CARD_BTN = "xpath=//button[normalize-space()='Add Another Card']"

    # sub_category=custom_message button-config fields (module docstring
    # point 18)
    URL_BUTTON_TITLE_INPUT = "[id='url_buttons_title.0']"
    URL_BUTTON_VALUE_INPUT = "[id='url_buttons_value.0']"
    PHONE_BUTTON_TYPE_WRAPPER = "[form-wrapper='phone_button_type']"
    PHONE_BUTTON_TITLE_INPUT = "#phone_button_title"
    PHONE_BUTTON_VALUE_INPUT = "#phone_button_value"
    FLOW_BUTTON_TYPE_WRAPPER = "[form-wrapper='flow_button_type']"
    FLOW_BUTTON_TITLE_INPUT = "#flow_button_title"
    FLOW_BUTTON_VALUE_WRAPPER = "[form-wrapper='flow_button_value']"

    # Preview panel (presence-only, see module docstring point 13)
    PREVIEW_HEADER = "xpath=//h1[normalize-space()='Preview']"

    # Footer actions
    CANCEL_LINK = "xpath=//a[normalize-space()='Cancel']"
    SAVE_BTN = "button[type='submit']"

    def __init__(self, page):
        super().__init__(page)

    # ══════════════════════════════════════════════════════════════════
    # Navigation
    # ══════════════════════════════════════════════════════════════════

    def navigate(self):
        self.open(self.PATH)
        self.page.wait_for_load_state("domcontentloaded")

    def is_create_page(self):
        return (
            "/whatsapp/channels/template/create" in self.get_current_url()
            and self.is_element_present(self.PAGE_HEADER, timeout=10000)
        )

    def get_page_header_text(self):
        return self.page.locator(self.PAGE_HEADER).inner_text().strip()

    # ══════════════════════════════════════════════════════════════════
    # Generic WireUI select helpers (private to this page object -- no
    # cross-file mixin per this project's convention; duplicated from
    # WhatsAppCampaignCreatePage's already-confirmed identical pattern)
    # ══════════════════════════════════════════════════════════════════

    def _select_container(self, wrapper_selector):
        return self.page.locator(wrapper_selector).locator(
            "label[data-name='form.wrapper.container']"
        ).first

    def _open_select(self, wrapper_selector):
        self._select_container(wrapper_selector).click()
        self.page.wait_for_timeout(300)

    def _is_select_disabled(self, wrapper_selector):
        attr = self.page.locator(wrapper_selector).first.get_attribute("aria-disabled")
        return attr == "true"

    def _decoded_options(self, wrapper_selector):
        """Decode the real option list from the WireUI select's own
        base64 JSON blob (x-ref="json") -- confirmed genuine data
        embedded by the framework itself, not a guess."""
        try:
            raw = self.page.locator(wrapper_selector).locator("[x-ref='json']").first.inner_text()
            match = re.search(r"atob\('([^']+)'\)", raw)
            if not match:
                return []
            decoded = base64.b64decode(match.group(1)).decode("utf-8")
            return json.loads(decoded)
        except Exception:
            return []

    def _select_option_by_text(self, wrapper_selector, option_text):
        """Click a real, hydrated <li role="listitem"> inside the given
        select's popover, matched by its REAL visible text (from
        _decoded_options / server-confirmed labels) -- role="listitem" is
        the generic implicit ARIA role of any <li>, not a guessed
        app-specific class."""
        self._open_select(wrapper_selector)
        popover = self.page.locator(wrapper_selector).locator("[x-ref='optionsContainer']").first
        popover.wait_for(state="visible", timeout=5000)
        item = popover.get_by_role("listitem").filter(has_text=option_text).first
        item.wait_for(state="visible", timeout=5000)
        item.click()

    def _search_in_select(self, wrapper_selector, text):
        self._open_select(wrapper_selector)
        search_input = self.page.locator(wrapper_selector).locator("input[type='search']").first
        search_input.fill(text)

    def _get_selected_display_text(self, wrapper_selector):
        return self.page.locator(wrapper_selector).locator(
            "button span"
        ).first.inner_text().strip()

    # ══════════════════════════════════════════════════════════════════
    # Sender ID
    # ══════════════════════════════════════════════════════════════════

    def get_sender_id_options(self):
        return self._decoded_options(self.SENDER_ID_WRAPPER)

    def open_sender_id_select(self):
        self._open_select(self.SENDER_ID_WRAPPER)

    def search_sender_id(self, text):
        self._search_in_select(self.SENDER_ID_WRAPPER, text)

    def select_sender_id(self, option_text):
        self._select_option_by_text(self.SENDER_ID_WRAPPER, option_text)

    def get_selected_sender_id_text(self):
        return self._get_selected_display_text(self.SENDER_ID_WRAPPER)

    def is_save_enabled(self):
        return self.page.locator(self.SAVE_BTN).is_enabled()

    # ══════════════════════════════════════════════════════════════════
    # Template Name
    # ══════════════════════════════════════════════════════════════════

    def get_name_value(self):
        return self.page.locator(self.NAME_INPUT).input_value()

    def set_name(self, value):
        loc = self.page.locator(self.NAME_INPUT)
        loc.fill("")
        if value:
            loc.fill(value)
        loc.blur()
        # wire:model.live.debounce.200ms -- give the round trip time to land
        self.page.wait_for_timeout(400)

    def clear_name(self):
        self.set_name("")

    def get_name_maxlength(self):
        return self.page.locator(self.NAME_INPUT).get_attribute("maxlength")

    # ══════════════════════════════════════════════════════════════════
    # Category
    # ══════════════════════════════════════════════════════════════════

    _CATEGORY_RADIOS = {
        "MARKETING": CATEGORY_MARKETING_RADIO,
        "UTILITY": CATEGORY_UTILITY_RADIO,
        "AUTHENTICATION": CATEGORY_AUTHENTICATION_RADIO,
        "CONVERSATION": CATEGORY_CONVERSATION_RADIO,
    }

    def select_category(self, category):
        locator = self._CATEGORY_RADIOS[category]
        self.page.locator(locator).check(force=True)
        self.page.wait_for_timeout(400)

    def get_selected_category(self):
        for category, locator in self._CATEGORY_RADIOS.items():
            if self.page.locator(locator).is_checked():
                return category
        return None

    # ══════════════════════════════════════════════════════════════════
    # Language
    # ══════════════════════════════════════════════════════════════════

    def get_language_options(self):
        return self._decoded_options(self.LANGUAGE_WRAPPER)

    def open_language_select(self):
        self._open_select(self.LANGUAGE_WRAPPER)

    def search_language(self, text):
        self._search_in_select(self.LANGUAGE_WRAPPER, text)

    def select_language(self, option_text):
        self._select_option_by_text(self.LANGUAGE_WRAPPER, option_text)

    def get_selected_language_text(self):
        return self._get_selected_display_text(self.LANGUAGE_WRAPPER)

    # ══════════════════════════════════════════════════════════════════
    # Template Labels
    # ══════════════════════════════════════════════════════════════════

    def get_label_value(self):
        return self.page.locator(self.LABEL_INPUT).input_value()

    def set_label(self, value):
        loc = self.page.locator(self.LABEL_INPUT)
        loc.fill("")
        if value:
            loc.fill(value)
        loc.blur()

    # ══════════════════════════════════════════════════════════════════
    # Header type (open/search mechanics only -- see module docstring
    # point 8; real option list not yet confirmed)
    # ══════════════════════════════════════════════════════════════════

    def get_header_options(self):
        return self._decoded_options(self.HEADER_WRAPPER)

    def open_header_select(self):
        self._open_select(self.HEADER_WRAPPER)

    def is_header_select_present(self):
        return self.is_element_present(self.HEADER_WRAPPER, timeout=5000)

    # ══════════════════════════════════════════════════════════════════
    # Body (EasyMDE/CodeMirror -- see module docstring point 9). This
    # reuses the app's OWN confirmed CodeMirror lookup/selector, taken
    # verbatim from this page's own inline <script> (insertVariableAtCursor
    # handler), rather than a plain Playwright .fill().
    # ══════════════════════════════════════════════════════════════════

    def is_body_editor_present(self):
        return self.is_element_present(self.BODY_EDITOR_CONTAINER, timeout=5000)

    def get_body_text(self):
        return self.page.evaluate(
            r"""
            () => {
                const cmEl = document.querySelector('[wire\\:key^="editor-"] .CodeMirror');
                return (cmEl && cmEl.CodeMirror) ? cmEl.CodeMirror.getValue() : null;
            }
            """
        )

    def set_body_text(self, text):
        self.page.evaluate(
            r"""
            (value) => {
                const cmEl = document.querySelector('[wire\\:key^="editor-"] .CodeMirror');
                if (cmEl && cmEl.CodeMirror) {
                    cmEl.CodeMirror.setValue(value);
                    cmEl.CodeMirror.focus();
                }
            }
            """,
            text,
        )
        # Entangled to the Livewire "body" property -- give it a moment
        # to sync before any assertion reads the wire model back.
        self.page.wait_for_timeout(400)

    # ══════════════════════════════════════════════════════════════════
    # Footer Text
    # ══════════════════════════════════════════════════════════════════

    def get_footer_text_value(self):
        return self.page.locator(self.FOOTER_INPUT).input_value()

    def set_footer_text(self, value):
        loc = self.page.locator(self.FOOTER_INPUT)
        loc.fill("")
        if value:
            loc.fill(value)
        loc.blur()
        self.page.wait_for_timeout(400)

    def get_footer_text_maxlength(self):
        return self.page.locator(self.FOOTER_INPUT).get_attribute("maxlength")

    # ══════════════════════════════════════════════════════════════════
    # Marketing sub_category (see module docstring point 15). Same
    # generic WireUI select helpers as Sender ID/Language.
    # ══════════════════════════════════════════════════════════════════

    def is_sub_category_select_present(self):
        return self.is_element_present(self.SUB_CATEGORY_WRAPPER, timeout=5000)

    def get_sub_category_options(self):
        return self._decoded_options(self.SUB_CATEGORY_WRAPPER)

    def select_sub_category(self, option_text):
        self._select_option_by_text(self.SUB_CATEGORY_WRAPPER, option_text)

    def get_selected_sub_category_text(self):
        return self._get_selected_display_text(self.SUB_CATEGORY_WRAPPER)

    # ══════════════════════════════════════════════════════════════════
    # sub_category=catalog_message: Catalog Type select (module
    # docstring point 16)
    # ══════════════════════════════════════════════════════════════════

    def is_catalog_type_select_present(self):
        return self.is_element_present(self.CATALOG_TYPE_WRAPPER, timeout=5000)

    def get_catalog_type_options(self):
        return self._decoded_options(self.CATALOG_TYPE_WRAPPER)

    def select_catalog_type(self, option_text):
        self._select_option_by_text(self.CATALOG_TYPE_WRAPPER, option_text)

    def get_selected_catalog_type_text(self):
        return self._get_selected_display_text(self.CATALOG_TYPE_WRAPPER)

    # ══════════════════════════════════════════════════════════════════
    # sub_category=carousel: Carousel sub-form (module docstring point
    # 17). Card/button fields are parametrized by index since the app
    # supports up to maxCardFieldCount=10 cards.
    # ══════════════════════════════════════════════════════════════════

    def is_carousel_form_present(self):
        return self.is_element_present(self.CAROUSEL_MEDIA_TYPE_WRAPPER, timeout=5000)

    def get_carousel_media_type_options(self):
        return self._decoded_options(self.CAROUSEL_MEDIA_TYPE_WRAPPER)

    def select_carousel_media_type(self, option_text):
        self._select_option_by_text(self.CAROUSEL_MEDIA_TYPE_WRAPPER, option_text)

    def get_carousel_button_count_options(self):
        return self._decoded_options(self.CAROUSEL_BUTTON_COUNT_WRAPPER)

    def select_carousel_button_count(self, option_text):
        self._select_option_by_text(self.CAROUSEL_BUTTON_COUNT_WRAPPER, option_text)

    def get_carousel_button_type1_options(self):
        return self._decoded_options(self.CAROUSEL_BUTTON_TYPE1_WRAPPER)

    def select_carousel_button_type1(self, option_text):
        self._select_option_by_text(self.CAROUSEL_BUTTON_TYPE1_WRAPPER, option_text)

    def _carousel_description_input(self, card_index):
        return self.page.locator(f"[id='carousel_description.{card_index}']")

    def set_carousel_card_description(self, card_index, text):
        loc = self._carousel_description_input(card_index)
        loc.fill("")
        if text:
            loc.fill(text)
        loc.blur()
        self.page.wait_for_timeout(400)

    def get_carousel_card_description_maxlength(self, card_index):
        return self._carousel_description_input(card_index).get_attribute("maxlength")

    def _carousel_file_input(self, card_index):
        return self.page.locator(f"input[type='file'][wire\\:model='carousel_file.{card_index}']")

    def is_carousel_card_file_input_present(self, card_index):
        return self._carousel_file_input(card_index).count() > 0

    def click_add_another_card(self):
        self.page.locator(self.ADD_ANOTHER_CARD_BTN).click()
        self.page.wait_for_timeout(400)

    def remove_carousel_card(self, card_index):
        self.page.locator(f"[wire\\:click=\"removeCard({card_index})\"]").click()
        self.page.wait_for_timeout(400)

    def _card_button_type_input(self, card_index, button_index):
        return self.page.locator(f"[id='card_buttons_type.{card_index}.{button_index}']")

    def get_card_button_type_value(self, card_index, button_index):
        return self._card_button_type_input(card_index, button_index).get_attribute("value")

    def _card_button_title_input(self, card_index, button_index):
        return self.page.locator(
            f"[wire\\:model\\.live\\.debounce\\.200ms='card_buttons_title.{card_index}.{button_index}']"
        )

    def set_card_button_title(self, card_index, button_index, text):
        loc = self._card_button_title_input(card_index, button_index)
        loc.fill("")
        if text:
            loc.fill(text)
        loc.blur()
        self.page.wait_for_timeout(400)

    def _card_button_value_input(self, card_index, button_index):
        return self.page.locator(
            f"[wire\\:model='card_buttons_value.{card_index}.{button_index}']"
        )

    def set_card_button_value(self, card_index, button_index, text):
        loc = self._card_button_value_input(card_index, button_index)
        loc.fill("")
        if text:
            loc.fill(text)
        loc.blur()
        self.page.wait_for_timeout(400)

    # ══════════════════════════════════════════════════════════════════
    # sub_category=custom_message: button-config fields (module
    # docstring point 18). The exact UI trigger that first reveals these
    # blocks was never captured -- these locators/helpers operate on the
    # fields once visible, they do not themselves reveal the blocks.
    # ══════════════════════════════════════════════════════════════════

    def is_url_button_fields_present(self):
        return self.is_element_present(self.URL_BUTTON_TITLE_INPUT, timeout=5000)

    def set_url_button_title(self, text):
        loc = self.page.locator(self.URL_BUTTON_TITLE_INPUT)
        loc.fill("")
        if text:
            loc.fill(text)
        loc.blur()
        self.page.wait_for_timeout(400)

    def set_url_button_value(self, text):
        loc = self.page.locator(self.URL_BUTTON_VALUE_INPUT)
        loc.fill("")
        if text:
            loc.fill(text)
        loc.blur()
        self.page.wait_for_timeout(400)

    def remove_url_button(self, index=0):
        self.page.locator(f"[wire\\:click=\"removeUrl({index})\"]").click()
        self.page.wait_for_timeout(400)

    def is_phone_button_fields_present(self):
        return self.is_element_present(self.PHONE_BUTTON_TYPE_WRAPPER, timeout=5000)

    def get_phone_button_type_options(self):
        return self._decoded_options(self.PHONE_BUTTON_TYPE_WRAPPER)

    def set_phone_button_title(self, text):
        loc = self.page.locator(self.PHONE_BUTTON_TITLE_INPUT)
        loc.fill("")
        if text:
            loc.fill(text)
        loc.blur()
        self.page.wait_for_timeout(400)

    def set_phone_button_value(self, text):
        loc = self.page.locator(self.PHONE_BUTTON_VALUE_INPUT)
        loc.fill("")
        if text:
            loc.fill(text)
        loc.blur()
        self.page.wait_for_timeout(400)

    def remove_phone_button(self):
        """Removes the button using the ONE confirmed removeData(...)
        argument ('Phone Number') -- see module docstring point 18 for
        why the Copy-Offer-Code / URL variants of this shared selector
        are not covered here."""
        self.page.locator("[wire\\:click=\"removeData('Phone Number')\"]").click()
        self.page.wait_for_timeout(400)

    def is_flow_button_fields_present(self):
        return self.is_element_present(self.FLOW_BUTTON_TYPE_WRAPPER, timeout=5000)

    def set_flow_button_title(self, text):
        loc = self.page.locator(self.FLOW_BUTTON_TITLE_INPUT)
        loc.fill("")
        if text:
            loc.fill(text)
        loc.blur()
        self.page.wait_for_timeout(400)

    def open_flow_button_value_select(self):
        self._open_select(self.FLOW_BUTTON_VALUE_WRAPPER)

    def search_flow_button_value(self, text):
        self._search_in_select(self.FLOW_BUTTON_VALUE_WRAPPER, text)

    def select_flow_button_value(self, option_text):
        self._select_option_by_text(self.FLOW_BUTTON_VALUE_WRAPPER, option_text)

    def remove_flow_button(self):
        self.page.locator("[wire\\:click=\"removeData('Flow')\"]").click()
        self.page.wait_for_timeout(400)

    # ══════════════════════════════════════════════════════════════════
    # Preview panel (presence-only, see module docstring point 13)
    # ══════════════════════════════════════════════════════════════════

    def is_preview_panel_present(self):
        return self.is_element_present(self.PREVIEW_HEADER, timeout=5000)

    # ══════════════════════════════════════════════════════════════════
    # Footer actions
    # ══════════════════════════════════════════════════════════════════

    def get_cancel_href(self):
        return self.page.locator(self.CANCEL_LINK).get_attribute("href")

    def click_cancel(self):
        with self.page.expect_navigation():
            self.page.locator(self.CANCEL_LINK).click()

    def is_save_button_present(self):
        return self.is_element_present(self.SAVE_BTN, timeout=5000)

    def click_save(self):
        self.page.locator(self.SAVE_BTN).click()
