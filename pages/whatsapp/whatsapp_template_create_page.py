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
    The lowercase/digit/underscore restriction is a SERVER-side behavior
    (wire:model.live.debounce, not a client regex/pattern attribute) --
    CONFIRMED via a real run: typing disallowed characters does NOT
    transform/strip the live value (it stays exactly as typed), and
    instead the app renders a real WireUI validation error label
    (`<label class="text-sm text-negative-600 mt-2" for="name">The name
    field format is invalid.</label>` -- same "negative-600" convention as
    FORM_VALIDATION_ERROR below). TC020 asserts on that error message, not
    on value normalization.
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

19. Cross-checked via three FRESH, independent full-page wire:snapshot
    captures (sub_category = multi_product_message, lto, and
    product_carousel respectively -- each decoded programmatically via
    html.unescape()+json.loads(), not eyeballed), two assumptions baked
    into points 15-18 above are corrected:
      - sub_category's REAL backend values (not just its display
        labels) are now confirmed straight from data.sub_category in
        each snapshot: "custom_message", "carousel", "catalog_message",
        "multi_product_message", "lto", "product_carousel", "spm",
        "order_details".
      - headerOptions and typeOptions are STATE-DEPENDENT, not fixed
        constants (an earlier assumption baked into point 8/13 is
        wrong): headerOptions is the full 4-value [None, Text, Media,
        Location] list for multi_product_message AND product_carousel,
        but narrows to ONLY [Media] for lto. typeOptions is
        [Image, Video, Document] (3 values) for multi_product_message,
        [Image, Video] (2 values) for lto, and empty ([]) for
        product_carousel (matching the earlier-confirmed empty state
        for catalog_message). The mechanism driving this is NOT known
        (do not assume a simple "gated by sub_category" rule beyond
        what's listed here) -- only these exact three additional
        snapshot-confirmed states are asserted anywhere in this suite.
      - otp_lengheader_textth:6 and allowedCategories:{"MARKETING":
        true,"UTILITY":true,"AUTHENTICATION":true} (CONVERSATION still
        absent) are reconfirmed identically across all three of these
        new captures, on top of the earlier captures -- these are
        stable, real backend fields/values, not paste artifacts.
      - mpm_sections is a genuinely empty-shaped placeholder array
        (one section containing one product_items entry, both with
        blank string fields) in EVERY capture regardless of
        sub_category, i.e. it is always initialized server-side, not
        something that only appears once multi_product_message is
        selected -- only its DOM rendering is gated by sub_category.

20. Marketing sub_category = Multi-Product Message (multi_product_message)
    reveals a Sections/Products sub-form, confirmed via the
    multi_product_message capture above (its own wire:id
    "yM78pITiQu63Fk0Z2mCG" is the SAME component instance the rest of
    this capture's fields decode to): a "Section 1" block with
    id="mpm_sections.0.title" (plain input,
    wire:model.live.debounce.200ms, placeholder "e.g. Popular
    Bundles") and, inside it, id="mpm_sections.0.product_items.0.product_retailer_id"
    (plain input, wire:model.live.debounce.200ms, placeholder "e.g.
    2lc20305pt"). Real, confirmed action buttons: "Add Section"
    (wire:click="addMpmSection"), "+ Add Product"
    (wire:click="addMpmProduct(0)"), "Remove Section"
    (wire:click="removeMpmSection(0)"), and a bare "Remove"
    (wire:click="removeMpmProduct(0, 0)"). Only this single
    section/product pair was ever captured populated -- multi-section/
    multi-product indexing beyond .0 is inferred solely from the
    addMpmSection/addMpmProduct naming convention, never itself
    captured, so tests here only exercise index 0.

21. Marketing sub_category = Limited Time Offer (lto) reveals, on top
    of the already-narrower headerOptions/typeOptions in point 19: a
    confirmed "Add button" trigger -- an Alpine dropdown
    (<button @click="open = !open">...<span>Add button</span></button>)
    that reveals 5 items, each a
    <button wire:click="showLTOdiv('<Label>')"> for the literal labels
    'Quick Reply', 'URL', 'Phone Number', 'Copy Offer Code', 'Flow'.
    CAUTION (as of this capture, since corrected -- see points 24/25): this
    trigger's method name (showLTOdiv) and its exclusive appearance in
    this lto-sub_category capture (absent from the multi_product_message
    and product_carousel captures checked alongside it) was originally
    treated as LTO-specific plumbing ONLY. Point 24 below, from a later
    CONVERSATION/cta_url_button capture, confirms the SAME showLTOdiv(...)
    click handler and Alpine dropdown also render there (with a single
    disabled 'URL' item); point 25 further confirms it under
    UTILITY/custom_message with all 5 items present -- so this is a
    shared "Add button" mechanism across at least three category/
    sub_category combinations, not LTO-exclusive. lto_title and enable_lto_expiry
    exist as real top-level component properties (confirmed via the
    snapshot) but were never seen populated or their own input DOM
    captured, so they remain undocumented beyond their existence.

22. Marketing sub_category = Product Card Carousel (product_carousel)
    reveals: form-wrapper="product_carousel_button_type" (WireUI
    searchable single-select, label "Button Type", placeholder "Select
    Button Type") with a confirmed 2-option list: "Single Product
    (SPM)" (SPM) / "URL Link" (URL). Per-card fields (index i, 0-based):
    a "Load Catalogs for This Card" button
    (wire:click="fetchCatalogsForCard(i)"), a native (non-WireUI)
    <select disabled><option>Load catalogs first</option></select>
    labeled "Select Catalog" that stays disabled until catalogs are
    fetched, an "Enter Catalog ID Manually" plain input
    (wire:model.live.debounce.200ms="carousel_products.{i}.catalogid",
    placeholder "e.g., 194836987003835"), and an "Enter Content ID
    Manually" plain input
    (wire:model.live.debounce.200ms="carousel_products.{i}.productretailerid",
    placeholder "e.g., vrpj01fvwp"). New cards are added via
    wire:click="addProductCard" ("Add Another Product Card" button).
    The catalog-fetch/dropdown-populate behavior itself (what "Select
    Catalog" looks like once real catalogs load) was never captured,
    so only the pre-fetch structural state above is built/asserted.

23. Category = AUTHENTICATION reveals a dedicated sub-form, confirmed via
    a genuine capture (memo.id "dpIvlQFBhc3F3AwarAf9", the SAME
    whatsapp.meta.create instance as points 15-18/19-22's capture --
    programmatically decoded via html.unescape()+json.loads(), not
    eyeballed) with category="AUTHENTICATION" and showAuthentication:true:
      - An OTP type radio group (real backend field "childcat", 3
        confirmed real values wire:model.live.debounce.200ms="childcat"):
        id="copycode" value="copycode" label "Copy Code" (default
        selected in this capture), id="autofill" value="autofill" label
        "AutoFill", id="zerotap" value="zerotap" label "Zero-Tap" -- each
        with its own confirmed descriptive helper text.
      - A "Message Content" section whose body text ({{1}} is your
        verification code.) is stated as non-editable ("Content for
        authentication templates can't be edited") and offers only two
        checkboxes, both sharing wire:model.live.debounce.200ms=
        "custom_add" (a multi-value array field) with different
        `value` attributes: id="custom-add-one" value="add_security"
        label "Add Security recommendation", and id="custom-add-two"
        value="add_expire" label "Add expiration time for code" (with
        confirmed helper text "After the code expires, Autofill button
        will be disabled.").
      - A "Buttons text" section with exactly one visible field in this
        capture: wire:model.live.debounce.200ms="auth_copy_code_button_text",
        placeholder "Copy Code", and a confirmed `disabled` attribute
        present on the element in this "Copy Code" OTP-type capture (not
        yet confirmed whether it un-disables for the AutoFill/Zero-Tap
        OTP types -- that would need its own fresh capture, not assumed
        here).
      - The Preview panel IS populated for real in this capture: a chat
        bubble showing the literal body text, plus a separate
        button-preview card showing "Copy code" (mdi-content-copy icon).
      - security_note ("For your security, do not share this code.") and
        code_expiration (60) are confirmed as real top-level component
        properties in the snapshot, but no corresponding visible input
        element for either was found in this capture -- they are NOT
        built as editable locators here, only noted as existing.
    TC037-TC041 is still left as a documented skip below because the
    Autofill/Zero-Tap OTP-type sub-behaviors (e.g. whether the button
    text field un-disables, App Setup/package name fields mentioned in
    the original checklist) were not captured; only the Copy-Code-default
    state above is solid.

24. Category = CONVERSATION, sub_category = cta_url_button reveals a
    populated state, confirmed via a genuine capture (memo.id
    "BJZjCv1X5MX01EgXSNgA", the SAME whatsapp.meta.create component type
    via memo.name/path -- programmatically decoded via
    html.unescape()+json.loads(), not eyeballed) with category=
    "CONVERSATION", sub_category="cta_url_button", conversation_enabled:
    true, showHeader:true, showFooter:true, showAddButton:true,
    showURL:true, urlButtonCount:1, totalButtonCount:1:
      - headerOptions is [Text, Media] (2 values -- a SIXTH distinct
        headerOptions/typeOptions state on top of the four already
        catalogued in point 19, never [None, Location] here) and
        typeOptions is [Image, Video, Document] (3 values, the same set
        already seen for multi_product_message). The mechanism is still
        not known; only this exact additional state is asserted.
      - allowedCategories is identical to every earlier capture
        ({"MARKETING": true, "UTILITY": true, "AUTHENTICATION": true}) --
        CONVERSATION itself is still absent from this dict even in a
        capture where category IS actively set to CONVERSATION, which
        confirms this omission is not state- or sub_category-dependent;
        it appears CONVERSATION is reachable but never offered as a
        fresh category choice via this dict-driven list.
      - The "Add button" Alpine dropdown documented in point 21 for
        sub_category=lto is CONFIRMED to also render here, but with only
        ONE menu item ("URL") instead of five, and that item carries a
        real `disabled=""` attribute plus `opacity-50 cursor-not-allowed`
        classes -- i.e. the same wire:click="showLTOdiv('URL')" handler
        is reused, just disabled. This corrects point 21's earlier
        "LTO-specific" caution: showLTOdiv is a shared "Add button" menu
        item handler, not exclusive to LTO (point 25 below further
        confirms it, with Copy Offer Code specifically disabled, under
        UTILITY/custom_message).
      - The URL button fields themselves reuse the exact same ids already
        documented in point 18: id="url_buttons_title.0" and
        id="url_buttons_value.0", plus a form-wrapper="url_button_type.0"
        WireUI select (readonly:true, aria-disabled="true", single option
        URL->URL) matching point 18's shape exactly -- no new locators
        needed, this capture just confirms that structure generalizes to
        this sub_category too. A confirmed helper text: "You must add
        exactly 1 URL button for CTA URL Button templates."
      - The Body EasyMDE container's wire:key is confirmed PER-CATEGORY
        rather than a single fixed value: wire:key="editor-CONVERSATION"
        in this capture (no other category's wire:key value has been
        captured for comparison) -- BODY_EDITOR_CONTAINER's existing
        prefix-selector (`[wire\\:key^='editor-']`) already tolerates any
        suffix and needs no change.
      - A real "Add Variable" button is confirmed for the first time:
        wire:click="insertVariable('body')" -- this is the actual
        clickable UI trigger that presumably invokes the already-
        documented insertVariableAtCursor JS handler (point 9); only the
        JS-level handler was previously documented, not this button.
    No other new fields were found in this capture; sub_category=
    cta_url_button otherwise reuses the point 18/21 structures as-is.

25. Category = UTILITY, sub_category = custom_message reveals a state
    confirmed via a genuine capture (memo.id "awrbrHP7LcMUWXlPKD0H",
    the SAME whatsapp.meta.create component type via memo.name/path --
    programmatically decoded via html.unescape()+json.loads(), not
    eyeballed) with category="UTILITY", sub_category="custom_message":
      - headerOptions is the full 4-value [None, Text, Media, Location]
        list and typeOptions is [Image, Video, Document] (3 values) --
        the SAME "full" state already seen for multi_product_message/
        product_carousel in point 19, not a new/narrower state.
      - allowedCategories is identical to every earlier capture
        ({"MARKETING": true, "UTILITY": true, "AUTHENTICATION": true}).
      - The "Add button" Alpine dropdown documented in point 21 (and
        extended to CONVERSATION/cta_url_button in point 24) is
        CONFIRMED here too, with all 5 menu items present (Quick Reply,
        URL, Phone Number, Copy Offer Code, Flow), and "Copy Offer Code"
        specifically carries the same real `disabled=""` attribute plus
        `opacity-50 cursor-not-allowed bg-gray-100` classes already seen
        under MARKETING/lto and CONVERSATION/cta_url_button -- this
        corrects point 21's original caution and point 24's restatement
        of it ("still unconfirmed for Custom Message specifically"):
        the "Add button" mechanism, and Copy Offer Code being disabled
        specifically, are now confirmed across THREE independent
        category/sub_category combinations, not LTO- or CONVERSATION-
        exclusive.
      - The UTILITY sub_category select's own x-ref="json" option blob
        decodes (again, byte-for-byte matching point 15's MARKETING
        capture's discovery of the same pattern under a different
        select) to exactly 3 real values: Custom Message
        (custom_message), Order Details (order_details), Order Status
        (order_status) -- confirming order_status IS a real, selectable
        value, though its own rendered form has still never been
        captured (see point 26 below).

26. Category = UTILITY, sub_category = order_details reveals a state
    confirmed via two independent genuine captures taken moments apart
    (both decoded programmatically; their Livewire snapshot `checksum`
    fields are BYTE-IDENTICAL --
    "2c19686b51f05f6663d31875db1923a2f42de8c3f1560a2178fa287d3eb2de6b"
    on both -- proving they are the exact same component state, not two
    different sub_category selections, even though the second was
    supplied labeled "order status"):
      - headerOptions narrows to ONLY [Media] (1 value) and typeOptions
        narrows to ONLY [Image] (1 value) -- a state strictly narrower
        than every other sub_category captured so far (point 19's lto
        state was [Media]/[Image, Video]; this is the first single-
        value typeOptions state seen for any UTILITY/MARKETING
        sub_category).
      - A "Button" section is fixed/non-editable: helper text reads
        "Only one button is supported for this type of template. The
        button text is not editable." followed by a bordered panel
        containing a disabled `<select disabled><option selected="">Open
        order details</option></select>` labeled "Type of Action", and a
        disabled/readonly `<input type="text" value="Review and Pay"
        readonly>` labeled "Button Text". Neither element carries
        wire:model, id, or name -- purely static/hardcoded markup, so
        the locators below anchor off the adjacent label text rather
        than any data attribute.
      - The Preview panel renders a REAL, additive button-preview block
        below the message bubble showing "Review and Pay" as a
        clickable-styled label -- confirmed structurally (same
        <div class="mt-2 rounded-md shadow-lg">...</div> wrapper shape
        already used for Authentication's button preview in point 23),
        not just present in the underlying snapshot data.
    CAUTION: despite the sub_category select's option list (point 25)
    confirming "Order Status" (order_status) is a real, independently
    selectable value, NO genuine capture of order_status's own rendered
    form has ever been obtained -- TWO separate capture attempts
    explicitly intended to select it both produced this exact
    order_details state instead (proven via the matching checksums
    above, not merely visual similarity). No order_status-specific
    locators, methods, or tests are built anywhere in this suite; a
    third, genuinely order_status-selected capture would be needed
    before that gap can be closed.

27. Real E2E (fill-and-submit-to-success) coverage, added for one
    confirmed category/sub_category combination at a time, reuses every
    locator/method above rather than inventing new ones, plus three new
    pieces of shared infra:
      - generate_unique_template_name()/fill_required_base_fields(): a
        real submit against a real account requires a genuinely UNIQUE
        Template Name each run (the checklist's own uniqueness
        constraint), so these generate a timestamp-suffixed,
        checklist-compliant (lowercase/digit/underscore) name rather
        than a fixed literal.
      - wait_for_save_result(): this page's own real post-submit DOM
        (success or validation-failure) has NEVER been captured, so no
        page-specific "success" locator is guessed here. Instead this
        polls for the FIRST of two signals: (a) the URL navigating away
        from this Create page, or (b) the already-confirmed, app-global
        toast/SweetAlert2 feedback (TOAST_NOTIFICATION_TEXT/SWAL_TITLE/
        SWAL_HTML_CONTAINER above) becoming visible with real text.
        Real E2E tests assert only that ONE of these generic signals
        appeared (i.e. the app responded at all to Save) -- they do NOT
        assert a specific "success" string, since what that string
        actually says has never been observed for this page. Whoever
        runs these tests should report back what wait_for_save_result()
        actually returns so a real "point 28" can document the
        confirmed success/failure text and this can be tightened.
      - Carousel/Product Card Carousel per-card media: WhatsApp Carousel
        templates require real header media per card
        (input[type='file'][wire:model='carousel_file.{i}'], already
        confirmed present). No test asset existed anywhere in this repo
        for this, so a small real, valid JPEG
        (tests/test_data/whatsapp_carousel_sample.jpg) was added
        following this repo's own existing tests/test_data/ convention
        (already used for CSV/XLSX/PDF fixtures elsewhere) -- this is
        supplying real binary test data through an already-confirmed
        file-input locator, not guessing a locator.

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
import time

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
    # CONFIRMED cross-file evidence: reused verbatim from
    # pages/common/contacts_page.py's FORM_VALIDATION_ERROR (same WireUI
    # "negative-600" convention used identically across this whole app,
    # and already reused once before in whatsapp_campaign_create_page.py).
    # Now directly confirmed on THIS page too, via a real rendered label
    # after typing an invalid name: <label class="text-sm text-negative-600
    # mt-2" for="name">The name field format is invalid.</label>.
    FORM_VALIDATION_ERROR = "label.text-negative-600, .text-negative-600"

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

    # "Add Variable" button for the body field (module docstring point 24
    # -- confirmed real wire:click trigger, distinct from the low-level
    # insertVariableAtCursor JS handler)
    ADD_VARIABLE_BODY_BTN = "[wire\\:click=\"insertVariable('body')\"]"

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

    # sub_category=multi_product_message: Sections/Products sub-form
    # (module docstring point 20)
    MPM_SECTION_TITLE_INPUT = "[id='mpm_sections.0.title']"
    MPM_PRODUCT_RETAILER_ID_INPUT = "[id='mpm_sections.0.product_items.0.product_retailer_id']"
    ADD_MPM_SECTION_BTN = "xpath=//button[normalize-space()='Add Section']"

    # "Add button" trigger (module docstring point 21; module docstring
    # point 24 confirms this same Alpine dropdown + showLTOdiv(...) click
    # handler is ALSO used for sub_category=cta_url_button -- so this is a
    # shared mechanism, not LTO-exclusive as first assumed)
    LTO_ADD_BUTTON_TRIGGER = "xpath=//button[.//span[normalize-space()='Add button']]"

    # sub_category=product_carousel: Product Card Carousel sub-form
    # (module docstring point 22)
    PRODUCT_CAROUSEL_BUTTON_TYPE_WRAPPER = "[form-wrapper='product_carousel_button_type']"
    ADD_PRODUCT_CARD_BTN = "xpath=//button[normalize-space()='Add Another Product Card']"

    # category=UTILITY, sub_category=order_details: fixed/non-editable
    # single-button block (module docstring point 26). Neither element
    # carries wire:model/id/name -- purely static markup, anchored here
    # via the adjacent, confirmed label text.
    ORDER_DETAILS_ACTION_SELECT = "xpath=//label[normalize-space()='Type of Action']/following-sibling::select"
    ORDER_DETAILS_BUTTON_TEXT_INPUT = "xpath=//label[normalize-space()='Button Text']/following-sibling::div//input"

    # category=AUTHENTICATION sub-form (module docstring point 23)
    AUTH_OTP_TYPE_COPYCODE_RADIO = "#copycode"
    AUTH_OTP_TYPE_AUTOFILL_RADIO = "#autofill"
    AUTH_OTP_TYPE_ZEROTAP_RADIO = "#zerotap"
    AUTH_ADD_SECURITY_CHECKBOX = "#custom-add-one"
    AUTH_ADD_EXPIRE_CHECKBOX = "#custom-add-two"
    AUTH_COPY_CODE_BUTTON_TEXT_INPUT = "[wire\\:model\\.live\\.debounce\\.200ms='auth_copy_code_button_text']"

    # Preview panel (presence-only, see module docstring point 13)
    PREVIEW_HEADER = "xpath=//h1[normalize-space()='Preview']"

    # Footer actions
    CANCEL_LINK = "xpath=//a[normalize-space()='Cancel']"
    SAVE_BTN = "button[type='submit']"

    # Global WireUI notification toast + SweetAlert2 (module docstring
    # point 27). This exact locator shape is NOT independently captured
    # for this specific page -- it is reused, per this project's
    # "already-confirmed identical pattern elsewhere in this codebase"
    # exception to the never-guess-a-locator rule, from
    # pages/rcs/rcs_campaign_create_page.py's NOTIFICATION_TITLE/
    # TOAST_NOTIFICATION_TEXT/SWAL_TITLE/SWAL_HTML_CONTAINER, which is
    # itself explicitly documented there as reused from
    # pages/sms/sms_campaign_page.py -- both call out that this WireUI
    # notification component (x-data="wireui_notifications") is
    # app-global, not per-channel/per-page, and SweetAlert2 is confirmed
    # to be a globally-loaded library on this page too (see this page's
    # own earlier captures showing "SweetAlert"/"Swal.fire" script tags).
    TOAST_NOTIFICATION_TEXT = (
        "xpath=//div[@x-data='wireui_notifications']"
        "//p[(@x-show='notification.title' or @x-show='notification.description') "
        "and normalize-space(text())!='']"
    )
    SWAL_TITLE = "#swal2-title"
    SWAL_HTML_CONTAINER = "#swal2-html-container"

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
        # The trigger click TOGGLES the popover (x-show="positionable.state")
        # rather than just opening it -- confirmed by a real run of
        # test_language_searchable_and_selectable: search_language() opens
        # the popover and leaves it open, then select_language() (which
        # also calls _open_select) clicked the trigger a SECOND time and
        # closed it again, so the subsequent popover.wait_for(state=
        # "visible") timed out on a popover that had just been toggled
        # hidden. Make this idempotent -- only click if not already open --
        # so callers can freely chain search_language()/select_language()
        # (or any other combination) without tracking open/closed state
        # themselves.
        popover = self.page.locator(wrapper_selector).locator("[x-ref='optionsContainer']").first
        if popover.is_visible():
            return
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
        # Selecting an option fires a Livewire wire:model.live update, which
        # can re-render/replace nearby DOM (e.g. a newly-revealed dependent
        # select) shortly after this click returns. Confirmed by a real run
        # selecting sub_category="Catalog" then immediately trying to open
        # the newly-revealed Catalog Type select: its container kept
        # getting "detached from the DOM, retrying" until Playwright's
        # click() gave up after 30s. Every other live-model-triggering
        # interaction in this file (set_name, select_category, etc.)
        # already settles with a short wait after firing -- this was the
        # one missing it.
        self.page.wait_for_timeout(400)

    def _search_in_select(self, wrapper_selector, text):
        self._open_select(wrapper_selector)
        search_input = self.page.locator(wrapper_selector).locator("input[type='search']").first
        search_input.fill(text)

    def _get_selected_display_text(self, wrapper_selector):
        # Alpine's client-side hydration of a WireUI select's server-set
        # initial value (e.g. Language's Livewire snapshot state
        # "language":"en" -> displayed "English", see module docstring
        # point 6) can still be in flight when navigate()'s
        # wait_for_load_state("domcontentloaded") returns -- confirmed by a
        # real run where test_language_defaults_to_english, the first test
        # in the file to read any WireUI select right after navigate(),
        # read back the raw un-hydrated placeholder ("Select Language")
        # instead of the confirmed default. Poll briefly and return once
        # two consecutive reads agree, rather than trusting a single
        # immediate read.
        locator = self.page.locator(wrapper_selector).locator("button span").first
        previous = None
        for _ in range(6):
            current = locator.inner_text().strip()
            if current == previous:
                return current
            previous = current
            self.page.wait_for_timeout(300)
        return previous

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

    def get_validation_errors(self):
        try:
            return [
                t for t in self.page.locator(self.FORM_VALIDATION_ERROR).all_inner_texts()
                if t.strip()
            ]
        except Exception:
            return []

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

    def is_add_variable_body_button_present(self):
        return self.is_element_present(self.ADD_VARIABLE_BODY_BTN, timeout=5000)

    def click_add_variable_body(self):
        self.page.locator(self.ADD_VARIABLE_BODY_BTN).click()
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
    # sub_category=multi_product_message: Sections/Products sub-form
    # (module docstring point 20). Only index .0/.0 was ever captured;
    # other helpers below are parametrized for completeness but only
    # index 0 is exercised by real tests.
    # ══════════════════════════════════════════════════════════════════

    def is_mpm_section_title_present(self):
        return self.is_element_present(self.MPM_SECTION_TITLE_INPUT, timeout=5000)

    def set_mpm_section_title(self, text, section_index=0):
        loc = self.page.locator(f"[id='mpm_sections.{section_index}.title']")
        loc.fill("")
        if text:
            loc.fill(text)
        loc.blur()
        self.page.wait_for_timeout(400)

    def get_mpm_section_title_value(self, section_index=0):
        return self.page.locator(f"[id='mpm_sections.{section_index}.title']").input_value()

    def is_mpm_product_retailer_id_present(self, section_index=0, product_index=0):
        return self.is_element_present(
            f"[id='mpm_sections.{section_index}.product_items.{product_index}.product_retailer_id']",
            timeout=5000,
        )

    def set_mpm_product_retailer_id(self, text, section_index=0, product_index=0):
        loc = self.page.locator(
            f"[id='mpm_sections.{section_index}.product_items.{product_index}.product_retailer_id']"
        )
        loc.fill("")
        if text:
            loc.fill(text)
        loc.blur()
        self.page.wait_for_timeout(400)

    def click_add_mpm_section(self):
        self.page.locator(self.ADD_MPM_SECTION_BTN).click()
        self.page.wait_for_timeout(400)

    def click_add_mpm_product(self, section_index=0):
        self.page.locator(f"[wire\\:click=\"addMpmProduct({section_index})\"]").click()
        self.page.wait_for_timeout(400)

    def remove_mpm_section(self, section_index=0):
        self.page.locator(f"[wire\\:click=\"removeMpmSection({section_index})\"]").click()
        self.page.wait_for_timeout(400)

    def remove_mpm_product(self, section_index=0, product_index=0):
        self.page.locator(
            f"[wire\\:click=\"removeMpmProduct({section_index}, {product_index})\"]"
        ).click()
        self.page.wait_for_timeout(400)

    # ══════════════════════════════════════════════════════════════════
    # "Add button" trigger (module docstring point 21, corrected/extended
    # by points 24 and 25): confirmed present for sub_category=lto (5
    # enabled menu items), sub_category=cta_url_button (1 disabled menu
    # item), AND category=UTILITY/sub_category=custom_message (5 menu
    # items, with Copy Offer Code specifically disabled there too) --
    # a shared mechanism across three independent category/sub_category
    # combinations, not exclusive to any one of them.
    # ══════════════════════════════════════════════════════════════════

    def is_lto_add_button_trigger_present(self):
        return self.is_element_present(self.LTO_ADD_BUTTON_TRIGGER, timeout=5000)

    def open_lto_add_button_menu(self):
        self.page.locator(self.LTO_ADD_BUTTON_TRIGGER).click()
        self.page.wait_for_timeout(300)

    def select_lto_add_button_type(self, label):
        """label must be one of the 5 confirmed literal showLTOdiv(...)
        arguments: 'Quick Reply', 'URL', 'Phone Number',
        'Copy Offer Code', 'Flow'. All 5 are confirmed present for
        sub_category=lto and UTILITY/custom_message; only 'URL' is
        confirmed present (and disabled) for sub_category=cta_url_button
        -- the other 4 labels were never captured there and may not
        exist in that context."""
        self.open_lto_add_button_menu()
        self.page.locator(f"[wire\\:click=\"showLTOdiv('{label}')\"]").click()
        self.page.wait_for_timeout(400)

    def is_lto_add_button_menu_item_disabled(self, label):
        return self.page.locator(
            f"[wire\\:click=\"showLTOdiv('{label}')\"]"
        ).is_disabled()

    # ══════════════════════════════════════════════════════════════════
    # sub_category=product_carousel: Product Card Carousel sub-form
    # (module docstring point 22)
    # ══════════════════════════════════════════════════════════════════

    def is_product_carousel_button_type_select_present(self):
        return self.is_element_present(self.PRODUCT_CAROUSEL_BUTTON_TYPE_WRAPPER, timeout=5000)

    def get_product_carousel_button_type_options(self):
        return self._decoded_options(self.PRODUCT_CAROUSEL_BUTTON_TYPE_WRAPPER)

    def select_product_carousel_button_type(self, option_text):
        self._select_option_by_text(self.PRODUCT_CAROUSEL_BUTTON_TYPE_WRAPPER, option_text)

    def click_load_catalogs_for_card(self, card_index=0):
        self.page.locator(f"[wire\\:click=\"fetchCatalogsForCard({card_index})\"]").click()
        self.page.wait_for_timeout(400)

    def is_carousel_product_catalog_id_input_present(self, card_index=0):
        return self.is_element_present(
            f"[wire\\:model\\.live\\.debounce\\.200ms='carousel_products.{card_index}.catalogid']",
            timeout=5000,
        )

    def set_carousel_product_catalog_id(self, text, card_index=0):
        loc = self.page.locator(
            f"[wire\\:model\\.live\\.debounce\\.200ms='carousel_products.{card_index}.catalogid']"
        )
        loc.fill("")
        if text:
            loc.fill(text)
        loc.blur()
        self.page.wait_for_timeout(400)

    def set_carousel_product_content_id(self, text, card_index=0):
        loc = self.page.locator(
            f"[wire\\:model\\.live\\.debounce\\.200ms='carousel_products.{card_index}.productretailerid']"
        )
        loc.fill("")
        if text:
            loc.fill(text)
        loc.blur()
        self.page.wait_for_timeout(400)

    def click_add_product_card(self):
        self.page.locator(self.ADD_PRODUCT_CARD_BTN).click()
        self.page.wait_for_timeout(400)

    # ══════════════════════════════════════════════════════════════════
    # category=UTILITY, sub_category=order_details: fixed/non-editable
    # single-button block (module docstring point 26). sub_category=
    # order_status remains UNCONFIRMED -- do not reuse these for it
    # without a genuine capture of its own (see point 26's caution).
    # ══════════════════════════════════════════════════════════════════

    def is_order_details_action_select_present(self):
        return self.is_element_present(self.ORDER_DETAILS_ACTION_SELECT, timeout=5000)

    def get_order_details_action_select_value(self):
        return self.page.locator(self.ORDER_DETAILS_ACTION_SELECT).input_value()

    def is_order_details_action_select_disabled(self):
        return self.page.locator(self.ORDER_DETAILS_ACTION_SELECT).is_disabled()

    def is_order_details_button_text_input_present(self):
        return self.is_element_present(self.ORDER_DETAILS_BUTTON_TEXT_INPUT, timeout=5000)

    def get_order_details_button_text_value(self):
        return self.page.locator(self.ORDER_DETAILS_BUTTON_TEXT_INPUT).input_value()

    def is_order_details_button_text_readonly(self):
        return self.page.locator(self.ORDER_DETAILS_BUTTON_TEXT_INPUT).get_attribute("readonly") is not None

    # ══════════════════════════════════════════════════════════════════
    # category=AUTHENTICATION sub-form (module docstring point 23)
    # ══════════════════════════════════════════════════════════════════

    _AUTH_OTP_TYPE_RADIOS = {
        "copycode": AUTH_OTP_TYPE_COPYCODE_RADIO,
        "autofill": AUTH_OTP_TYPE_AUTOFILL_RADIO,
        "zerotap": AUTH_OTP_TYPE_ZEROTAP_RADIO,
    }

    def is_auth_otp_type_radios_present(self):
        return self.is_element_present(self.AUTH_OTP_TYPE_COPYCODE_RADIO, timeout=5000)

    def select_auth_otp_type(self, value):
        """value must be one of the 3 confirmed real childcat values:
        'copycode', 'autofill', 'zerotap'."""
        locator = self._AUTH_OTP_TYPE_RADIOS[value]
        self.page.locator(locator).check(force=True)
        self.page.wait_for_timeout(400)

    def get_selected_auth_otp_type(self):
        for value, locator in self._AUTH_OTP_TYPE_RADIOS.items():
            if self.page.locator(locator).is_checked():
                return value
        return None

    def is_auth_add_security_checkbox_present(self):
        return self.is_element_present(self.AUTH_ADD_SECURITY_CHECKBOX, timeout=5000)

    def check_auth_add_security(self):
        self.page.locator(self.AUTH_ADD_SECURITY_CHECKBOX).check(force=True)
        self.page.wait_for_timeout(400)

    def is_auth_add_security_checked(self):
        return self.page.locator(self.AUTH_ADD_SECURITY_CHECKBOX).is_checked()

    def is_auth_add_expire_checkbox_present(self):
        return self.is_element_present(self.AUTH_ADD_EXPIRE_CHECKBOX, timeout=5000)

    def check_auth_add_expire(self):
        self.page.locator(self.AUTH_ADD_EXPIRE_CHECKBOX).check(force=True)
        self.page.wait_for_timeout(400)

    def is_auth_add_expire_checked(self):
        return self.page.locator(self.AUTH_ADD_EXPIRE_CHECKBOX).is_checked()

    def is_auth_copy_code_button_text_input_present(self):
        return self.is_element_present(self.AUTH_COPY_CODE_BUTTON_TEXT_INPUT, timeout=5000)

    def get_auth_copy_code_button_text_value(self):
        return self.page.locator(self.AUTH_COPY_CODE_BUTTON_TEXT_INPUT).input_value()

    def is_auth_copy_code_button_text_disabled(self):
        return self.page.locator(self.AUTH_COPY_CODE_BUTTON_TEXT_INPUT).is_disabled()

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

    # ══════════════════════════════════════════════════════════════════
    # Real E2E (fill-and-submit) shared infra (module docstring point 27)
    # ══════════════════════════════════════════════════════════════════

    def generate_unique_template_name(self, prefix="e2e_test"):
        """Timestamp-suffixed, checklist-compliant (lowercase/digit/
        underscore only) name -- Template Name must be unique per real
        account, and these E2E tests perform REAL submits."""
        return f"{prefix}_{int(time.time() * 1000)}"

    def fill_required_base_fields(self, name=None, body_text=None):
        """Fills the fields common to every real E2E submit: Sender ID
        (the only field structurally gating Save, point 11), Template
        Name (unique, checklist-compliant), and Body (not client-gated,
        but filled anyway since a real template needs real content).
        Language/Header/Footer are deliberately left at their defaults
        (English / none selected / blank) -- Header is skipped
        everywhere in this E2E suite specifically to avoid a media-
        upload dependency for sub_categories where it isn't otherwise
        confirmed mandatory. Returns the actual name used."""
        senders = self.get_sender_id_options()
        if not senders:
            raise AssertionError(
                "No real Sender ID options available -- cannot perform a "
                "real E2E submit without one"
            )
        label = senders[0].get("label")
        self.select_sender_id(label)
        name = name or self.generate_unique_template_name()
        self.set_name(name)
        self.set_body_text(
            body_text or "Hello, this is an automated end-to-end test message."
        )
        return name

    def set_carousel_card_file(self, card_index, filepath):
        """filepath must point to a real, existing file -- see module
        docstring point 27 for why tests/test_data/
        whatsapp_carousel_sample.jpg was added to this repo."""
        self._carousel_file_input(card_index).set_input_files(filepath)
        self.page.wait_for_timeout(600)

    def get_toast_or_swal_text(self):
        """Single-shot check of the confirmed app-global WireUI toast and
        SweetAlert2 title/html-container (see TOAST_NOTIFICATION_TEXT/
        SWAL_TITLE/SWAL_HTML_CONTAINER above). Returns the first
        non-empty, visible text found, or None."""
        for locator in (
            self.TOAST_NOTIFICATION_TEXT,
            self.SWAL_TITLE,
            self.SWAL_HTML_CONTAINER,
        ):
            try:
                els = self.page.locator(locator)
                for i in range(els.count()):
                    el = els.nth(i)
                    if el.is_visible():
                        text = el.inner_text().strip()
                        if text:
                            return text
            except Exception:
                continue
        return None

    def wait_for_save_result(self, timeout_s=15):
        """Call AFTER click_save(). This page's own real post-submit DOM
        has never been captured, so no page-specific "success" locator
        is guessed here -- polls for up to timeout_s for the FIRST of
        two generic, already-confirmed-elsewhere signals: the URL
        navigating away from this Create page, or the app-global toast/
        SweetAlert2 feedback becoming visible. Returns a dict:
        {"outcome": "url_changed" | "toast_or_swal" | "none_detected",
         "url": <current url>, "text": <toast/swal text, if any>}."""
        start_url = self.get_current_url()
        end_time = time.time() + timeout_s
        while time.time() < end_time:
            current_url = self.get_current_url()
            if current_url != start_url:
                return {"outcome": "url_changed", "url": current_url, "text": None}
            text = self.get_toast_or_swal_text()
            if text:
                return {"outcome": "toast_or_swal", "url": current_url, "text": text}
            self.page.wait_for_timeout(300)
        return {"outcome": "none_detected", "url": self.get_current_url(), "text": None}
