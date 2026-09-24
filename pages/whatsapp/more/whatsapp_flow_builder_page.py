import time

from pages.common.base_page import BasePage


class WhatsappFlowBuilderPage(BasePage):
    """
    WhatsApp Flow Builder — page object.

    Grounded in a full live DOM capture of
    https://.../whatsapp/flows/builder (reached via the Flows listing
    page's confirmed "Create Flow" link, see whatsapp_flows_page.py).
    This is the FIRST real DOM evidence of this page — every locator
    below is built directly from it. It replaces the documented
    "never guess" skips for TC006-TC025 in test_whatsapp_flows_flow.py
    (see that file's _BUILDER_SKIP_REASON block), except where noted.

    Confirmed facts driving every locator below:

    1. Livewire component: memo.name = "whatsapp.flow.flow-builder",
       memo.path = "whatsapp/flows/builder". Real wire:snapshot data
       confirms: flowName:"" , selectedSenderId:"", selectedCategories:[]
       (all empty defaults on a fresh builder), plus the full
       availableCategories and availableComponents maps used below.
    2. Header: `<h1 class="text-md font-semibold whitespace-nowrap">WhatsApp Flow Builder</h1>`
       (confirmed exact text — different from the listing page's singular
       "WhatsApp Flow"). "Back to Flows" is a real `<a href=".../whatsapp/flows">`.
    3. Sender ID: a WireUI searchable single-select
       (`form-wrapper="selectedSenderId"`, `x-data="wireui_select"`,
       placeholder "Select SenderId", searchable, clearable, NOT
       multiselect) — the SAME reusable Alpine/WireUI select component
       already modeled and proven on
       whatsapp_template_create_page.py/whatsapp_campaign_create_page.py
       (x-on:click="openIfClosed" trigger, x-ref="optionsContainer"/
       "listing" popover, real <li> options that carry the browser's
       native implicit ARIA "listitem" role). Real embedded sender
       options confirmed via the control's own x-ref="json" data (base64
       JSON decoded): CERF Solutions, GTS QA, Capture Moments, Globe
       Teleservices Pte. Ltd., Testing, Cerf Telin, Test Acccount 1,
       WhatsApp Simulator Testing — same wa_sender_ids table backing this
       page's counterpart on the Template Create page (`form-wrapper=
       "senderId"` there vs "selectedSenderId" here — different
       wire:model name, identical component).
    4. Flow Name: `<input type="text" wire:model="flowName" placeholder="Enter flow name">`
       — confirmed a PLAIN `wire:model` (no `.live`), unlike most other
       text inputs in this codebase — so it only syncs to the Livewire
       component on the next network round trip (e.g. clicking Save),
       not on every keystroke.
    5. Categories: confirmed a DIFFERENT mechanism from Sender ID — a
       plain Alpine dropdown (`x-data="{ open: false }"`, button text
       "Select categories") containing 8 real
       `<input type="checkbox" wire:model.live="selectedCategories" value="{CATEGORY}">`
       checkboxes, one per `wire:key="category-{CATEGORY}"` label — NOT
       a WireUI multiselect. Real confirmed category values (from
       wire:snapshot's availableCategories, matching the 8 rendered
       checkboxes exactly): SIGN_UP, SIGN_IN, APPOINTMENT_BOOKING,
       LEAD_GENERATION, CONTACT_US, CUSTOMER_SUPPORT, SURVEY, OTHER.
    6. Screens panel: a real "Screens" header with a live "N/8" counter
       (`<span class="text-sm text-gray-500">1/8</span>` at capture
       time, one default screen). Each screen row is
       `<div wire:click="selectScreen({index})">`; a real
       `<button wire:click="addScreen">Add New Screen</button>` exists.
       NOT confirmed: the per-screen delete control's markup — the
       capture only had 1 screen, so the row's control slot (present but
       empty at wire:click.stop="") never rendered a delete button.
       TC009 stays a documented skip for this reason.
    7. Screen title: a real
       `<input type="text" wire:change="updateCurrentScreenTitle($event.target.value)"
       wire:key="screen-title-{index}" maxlength="20">` — confirmed
       `wire:change` (fires on blur/Enter), not `wire:model.live`.
    8. Components ("Edit content" panel): mirrors the Screens panel's
       "N/8" counter convention (a real per-screen component-count cap).
       Each existing component renders as a
       `.border.border-gray-200.rounded-lg` card with
       `<button wire:click="selectComponent({index})">` (edit) and, for
       removable components, `<button wire:click="removeComponent({index})">`.
       The default Footer/"Continue" button component had NO remove
       control in the capture (still has a selectComponent button) —
       confirmed it's a fixed/required component. NOT confirmed: what
       selectComponent({index}) actually opens (no property-edit panel
       was captured, since no component was ever clicked during
       capture) — TC011 (edit button title) stays a documented skip for
       this reason.
    9. "Add content" control: a real Alpine dropdown
       (`@click="isOpen = !isOpen"`, text "Add content") containing 4
       real category toggles (Text / Media / Text Answer / Selection,
       each `@click="activeCategory = activeCategory === '{cat}' ? null : '{cat}'"`)
       whose submenus contain ALL 12 real, confirmed
       `wire:click="addComponent('{Type}'); closeDropdown()"` buttons —
       this directly and completely confirms TC012-TC022 (one control
       each) plus half of TC023 (the Opt-in control). Real type->label
       map (from wire:snapshot's availableComponents, matching every
       rendered button's visible text exactly): LargeHeading->"Large
       Heading", SmallHeading->"Small Heading", Caption->"Caption",
       Body->"Body" (Text category); Image->"Image" (Media category);
       ShortAnswer->"Short Answer", Paragraph->"Paragraph",
       DatePicker->"Date Picker" (Text Answer category); SingleChoice->
       "Single Choice", MultipleChoice->"Multiple Choice", Dropdown->
       "Dropdown", OptIn->"Opt-in" (Selection category). A newly-added
       component's card renders with the SAME label text as its
       availableComponents entry (confirmed: the pre-existing "Large
       Heading" card's span text matches this map's LargeHeading entry
       exactly).
    10. Save Flow: a real `<button wire:click="saveFlow">Save Flow</button>`
        in the header row (beside the Sender ID select) — this covers
        the other half of TC023. Per this project's caution around
        irreversible/data-creating actions in shared QA environments,
        every test in THIS FILE except the dedicated E2E creation test
        (test_e2e_whatsapp_flow_creation_and_persistence) only checks
        the button's presence/enabled state. click_save_flow() exists
        for that one real, explicitly-requested test; its real post-save
        DOM was never captured either, so wait_for_save_result() reuses
        the same generic, already-confirmed app-global toast/SweetAlert2/
        URL-change signal whatsapp_template_create_page.py relies on for
        the same reason (see that page's own doc comments for the reuse
        chain), rather than guessing a flow-specific one.
    11. "View JSON" button (`onclick="document.getElementById('jsonModal')...`,
        plain onclick, not wire:click) opens a real local modal
        (`#jsonModal`) with a `<pre id="jsonContent">` showing the live
        flow JSON — confirmed real, client-side only (no server round
        trip), safe to open/close freely.
    12. Preview panel (right half): a live, read-only rendering of the
        current screen's components inside a fixed 320x600 "device
        frame" — confirmed present but not modeled with specific
        per-component-type locators here (out of scope for TC012-TC022,
        which only test the ADD controls, not the resulting preview
        rendering).

    IMPORTANT SCOPE NOTE: TC009 (per-screen delete control) and TC011
    (edit button/footer title) remain documented skips — see points 6
    and 8 above for exactly what evidence is still missing. TC024/TC025
    (8-screen / 8-component maximum enforcement) are modeled here
    BEHAVIORALLY (add repeatedly and confirm the counter/row count never
    exceeds 8) rather than via a specific "limit reached" locator, since
    no DOM evidence of the at-limit state was ever captured — this
    avoids guessing what the enforcement UI looks like while still
    exercising the real, confirmed addScreen/addComponent mechanisms.
    """

    BUILDER_URL = "/whatsapp/flows/builder"

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[normalize-space()='WhatsApp Flow Builder']"
    BACK_TO_FLOWS_LINK = "xpath=//a[contains(normalize-space(.),'Back to Flows')]"

    # ── Sender ID (WireUI select — same component family as the Template/
    # Campaign Create pages' selects) ───────────────────────────────────────
    SENDER_ID_WRAPPER = "[form-wrapper='selectedSenderId']"

    # ── Flow Name (confirmed PLAIN wire:model, not .live) ───────────────────
    FLOW_NAME_INPUT = "input[wire\\:model='flowName']"

    # ── Categories (confirmed plain Alpine dropdown + real checkboxes,
    # NOT a WireUI select) ───────────────────────────────────────────────────
    CATEGORIES_BUTTON = (
        "xpath=//label[normalize-space()='Categories']"
        "/following-sibling::div//button[@type='button']"
    )
    CATEGORY_CHECKBOX_BY_VALUE = (
        "input[type='checkbox'][wire\\:model\\.live='selectedCategories'][value='{value}']"
    )
    ALL_CATEGORY_VALUES = [
        "SIGN_UP", "SIGN_IN", "APPOINTMENT_BOOKING", "LEAD_GENERATION",
        "CONTACT_US", "CUSTOMER_SUPPORT", "SURVEY", "OTHER",
    ]

    # ── Screens panel ────────────────────────────────────────────────────────
    SCREENS_HEADER = "xpath=//h3[normalize-space()='Screens']"
    SCREENS_COUNTER = "xpath=(//h3[normalize-space()='Screens']/following-sibling::span)[1]"
    ADD_SCREEN_BTN = "xpath=//button[@*[name()='wire:click']='addScreen']"
    SCREEN_ROW_BY_INDEX = "xpath=//div[@*[name()='wire:click']=\"selectScreen({index})\"]"
    SCREEN_TITLE_INPUT_BY_INDEX = "xpath=//input[@*[name()='wire:key']='screen-title-{index}']"

    # ── Edit content / components panel ─────────────────────────────────────
    EDIT_CONTENT_HEADER = "xpath=//h3[normalize-space()='Edit content']"
    EDIT_CONTENT_COUNTER = "xpath=(//h3[normalize-space()='Edit content']/following-sibling::span)[1]"
    COMPONENT_CARDS = ".border.border-gray-200.rounded-lg.p-3"
    SELECT_COMPONENT_BTN_BY_INDEX = "xpath=//button[@*[name()='wire:click']='selectComponent({index})']"
    REMOVE_COMPONENT_BTN_BY_INDEX = "xpath=//button[@*[name()='wire:click']='removeComponent({index})']"

    # ── "Add content" dropdown (confirmed 4 categories, 12 real
    # addComponent(...) buttons) ─────────────────────────────────────────────
    ADD_CONTENT_BTN = "xpath=//button[contains(normalize-space(.),'Add content')]"
    ADD_CONTENT_CATEGORY_BTN = {
        "text": "xpath=//button[.//span[normalize-space()='Text']]",
        "media": "xpath=//button[.//span[normalize-space()='Media']]",
        "textAnswer": "xpath=//button[.//span[normalize-space()='Text Answer']]",
        "selection": "xpath=//button[.//span[normalize-space()='Selection']]",
    }
    ADD_COMPONENT_BTN_BY_TYPE = (
        "xpath=//button[contains(@*[name()='wire:click'], \"addComponent('{type}')\")]"
    )
    # Real type -> submenu category -> displayed label, confirmed via
    # wire:snapshot's availableComponents map (see docstring point 9).
    COMPONENT_TYPE_INFO = {
        "LargeHeading":   ("text", "Large Heading"),
        "SmallHeading":   ("text", "Small Heading"),
        "Caption":        ("text", "Caption"),
        "Body":           ("text", "Body"),
        "Image":          ("media", "Image"),
        "ShortAnswer":    ("textAnswer", "Short Answer"),
        "Paragraph":      ("textAnswer", "Paragraph"),
        "DatePicker":     ("textAnswer", "Date Picker"),
        "SingleChoice":   ("selection", "Single Choice"),
        "MultipleChoice": ("selection", "Multiple Choice"),
        "Dropdown":       ("selection", "Dropdown"),
        "OptIn":          ("selection", "Opt-in"),
    }

    # ── Save Flow ────────────────────────────────────────────────────────────
    SAVE_FLOW_BTN = "xpath=//button[@*[name()='wire:click']='saveFlow']"

    # ── Post-save feedback (app-global, NOT specific to this page --
    # reused verbatim from the same confirmed WireUI notification /
    # SweetAlert2 selectors already relied on by
    # pages/whatsapp/whatsapp_template_create_page.py's wait_for_save_
    # result(), itself explicitly documented there as reused from
    # pages/rcs/rcs_campaign_create_page.py, itself reused from
    # pages/sms/sms_campaign_page.py. No flow-specific "success" locator
    # has ever been captured for THIS page, so this deliberately doesn't
    # invent one -- it relies on the same already-proven, app-global
    # signal every one of those pages already relies on.) ───────────────────
    TOAST_NOTIFICATION_TEXT = (
        "xpath=//div[@x-data='wireui_notifications']"
        "//p[(@x-show='notification.title' or @x-show='notification.description') "
        "and normalize-space(text())!='']"
    )
    SWAL_TITLE = "#swal2-title"
    SWAL_HTML_CONTAINER = "#swal2-html-container"

    # ── View JSON (confirmed plain onclick, local-only modal) ───────────────
    VIEW_JSON_BTN = "xpath=//button[contains(normalize-space(.),'View JSON')]"
    JSON_MODAL = "#jsonModal"
    JSON_MODAL_CONTENT = "#jsonContent"
    # NOTE: previously built as `f"{JSON_MODAL} xpath=..."` -- a bare
    # CSS selector concatenated with an xpath= fragment via a plain
    # space, which is NOT Playwright's ">>" chain syntax, so
    # page.locator() couldn't parse it. close_view_json_modal()'s own
    # try/except silently swallowed the resulting error, so the button
    # was never actually clicked and the modal never closed. Confirmed
    # via a real HTML dump: the close button is
    # `<button type="button" onclick="document.getElementById('jsonModal').classList.add('hidden')">`
    # -- rewritten as a single valid CSS selector (attribute-contains,
    # no engine-chaining needed) to fix that.
    JSON_MODAL_CLOSE_BTN = '#jsonModal button[onclick*="jsonModal"][onclick*="classList.add"]'


    # -------------------------------------------------------------------------
    # Navigation / page state
    # -------------------------------------------------------------------------

    def __init__(self, page):
        super().__init__(page)

    def navigate(self):
        self.open(self.BUILDER_URL)
        self.page.wait_for_timeout(2000)
        return self

    def is_on_builder_page(self):
        url = self.get_current_url()
        return "/whatsapp/flows/builder" in url and "login" not in url.lower()

    def get_page_title_text(self):
        try:
            el = self.page.locator(self.PAGE_TITLE).first
            el.wait_for(state="visible", timeout=8000)
            return el.inner_text().strip()
        except Exception:
            return ""

    def is_back_to_flows_link_present(self):
        return self.is_element_present(self.BACK_TO_FLOWS_LINK, timeout=5000)

    # -------------------------------------------------------------------------
    # Sender ID (reusing the proven generic WireUI-select pattern already
    # confirmed on whatsapp_template_create_page.py / whatsapp_campaign_
    # create_page.py -- same x-data="wireui_select" component)
    # -------------------------------------------------------------------------

    def _visible_wrapper(self, wrapper_selector, timeout_ms=3000):
        """Some pages in this app render more than one element matching
        the same generic selector -- a hidden duplicate/responsive-
        breakpoint copy, or a transient extra node during a Livewire
        DOM morph. Already a confirmed, live pattern on THIS page: see
        the ADD_CONTENT_BTN/ADD_CONTENT_CATEGORY_BTN fix (js_click_
        first_visible) above, which exists for exactly this reason.

        A blind `.first` can silently lock onto such a copy. That's the
        best explanation that fits everything observed on this select
        across two real runs: clicking "GTS QA" and reading the label
        back always returned the stale "Select SenderId" placeholder --
        even after widening the read's patience budget from 5s to a full
        20s made no difference -- while a screenshot taken moments after
        each failed assertion showed "GTS QA" correctly selected on the
        actual visible page. That's not "hasn't updated yet" (patience
        would have fixed that); it's "reading the wrong copy" (patience
        never can). Poll briefly for a VISIBLE match instead of trusting
        DOM order; falls back to plain `.first` if nothing is ever found
        visible, so a genuine "control never rendered" bug still surfaces
        as a real error instead of hanging silently."""
        matches = self.page.locator(wrapper_selector)
        end = time.time() + timeout_ms / 1000
        while time.time() < end:
            try:
                count = matches.count()
            except Exception:
                count = 0
            for i in range(count):
                cand = matches.nth(i)
                try:
                    if cand.is_visible():
                        return cand
                except Exception:
                    continue
            self.page.wait_for_timeout(150)
        return matches.first

    def _select_container(self, wrapper_selector):
        return self._visible_wrapper(wrapper_selector).locator(
            "label[data-name='form.wrapper.container']"
        ).first

    def _open_select(self, wrapper_selector):
        popover = self._visible_wrapper(wrapper_selector).locator("[x-ref='optionsContainer']").first
        if popover.is_visible():
            return
        self._select_container(wrapper_selector).click()
        self.page.wait_for_timeout(300)

    def _select_option_by_text(self, wrapper_selector, option_text):
        self._open_select(wrapper_selector)
        popover = self._visible_wrapper(wrapper_selector).locator("[x-ref='optionsContainer']").first
        popover.wait_for(state="visible", timeout=5000)
        item = popover.get_by_role("listitem").filter(has_text=option_text).first
        item.wait_for(state="visible", timeout=5000)
        item.click()
        self.page.wait_for_timeout(400)

    def _get_selected_display_text(self, wrapper_selector, placeholder=None, timeout_ms=20000):
        """Poll the select's trigger label until it stabilizes, re-
        resolving the VISIBLE wrapper copy (see _visible_wrapper) on
        every read -- not just once -- since a Livewire re-render after
        selection is exactly the kind of DOM morph that can shuffle which
        copy is "first". `placeholder`, when given, is the label's known
        pre-selection text (e.g. "Select SenderId"); a read that still
        equals it is treated as "hasn't updated yet" and kept polling
        rather than accepted as stable.

        Budget history, from real runs, because both a short AND a long
        window have failed at different times, for different reasons:
        5s wasn't enough (screenshot proved the real selection lands
        shortly after); 20s alone wasn't enough either on a run with no
        re-auth involved (which is what motivated _visible_wrapper: a
        stale/duplicate copy, not raw timing, looked like the better fit
        for THAT run); then, back down to 8s post-_visible_wrapper, it
        failed again on a run whose captured setup log showed a real
        mid-test re-authentication (session expired, full re-login) just
        before this ran -- a freshly logged-in, freshly navigated page is
        a cold start for Alpine/Livewire hydration, plausibly slower than
        an already-warmed session, and a screenshot again showed "GTS QA"
        correctly selected once the test had already failed. Both causes
        are real and not mutually exclusive, so this keeps BOTH fixes:
        _visible_wrapper's scan, and a generous 20s budget to cover a
        cold-start round trip.

        ROOT CAUSE FOUND (from a real HTML dump at failure time): the
        trigger button actually contains TWO sibling <span> elements at
        once -- a placeholder span (x-show="isEmpty()") and a
        selected-value span (x-show="!config.multiselect &&
        isNotEmpty()") -- both always present in the DOM, with Alpine
        toggling which one is shown via an inline style="display: none"
        rather than removing either from the DOM. The placeholder span
        is first in DOM order, so plain `.locator("button span").first`
        was consistently reading the HIDDEN placeholder span regardless
        of which one Alpine had actually made visible -- explaining why
        every timing/duplicate-wrapper fix above still failed. The fix
        is to target the visible span specifically via Playwright's
        `:visible` pseudo-class, instead of relying on DOM order."""
        end = time.time() + timeout_ms / 1000
        previous = None
        while time.time() < end:
            wrapper = self._visible_wrapper(wrapper_selector, timeout_ms=1000)
            visible_span = wrapper.locator("button span:visible").first
            try:
                if visible_span.count() > 0:
                    current = visible_span.inner_text().strip()
                else:
                    # Fallback: no span currently reads as visible (e.g. a
                    # mid-render blip) -- fall back to DOM order rather
                    # than raising, and let the next poll iteration retry.
                    current = wrapper.locator("button span").first.inner_text().strip()
            except Exception:
                current = previous or ""
            if placeholder is not None and current == placeholder:
                previous = current
                self.page.wait_for_timeout(300)
                continue
            if current == previous:
                return current
            previous = current
            self.page.wait_for_timeout(300)
        return previous

    def is_sender_id_select_present(self):
        return self.is_element_present(self.SENDER_ID_WRAPPER, timeout=8000)

    def open_sender_id_select(self):
        self._open_select(self.SENDER_ID_WRAPPER)

    def select_sender_id(self, option_text):
        self._select_option_by_text(self.SENDER_ID_WRAPPER, option_text)

    def get_selected_sender_id_text(self):
        return self._get_selected_display_text(
            self.SENDER_ID_WRAPPER, placeholder="Select SenderId"
        )

    # -------------------------------------------------------------------------
    # Flow Name
    # -------------------------------------------------------------------------

    def set_flow_name(self, value):
        el = self.h.wait_for_element_visible(self.FLOW_NAME_INPUT)
        el.fill(value)
        # Confirmed PLAIN wire:model (not .live) -- blur to force the sync
        # point the app itself relies on (docstring point 4).
        el.blur()
        self.page.wait_for_timeout(300)

    def get_flow_name_value(self):
        return self.h.wait_for_element_visible(self.FLOW_NAME_INPUT).input_value()

    # -------------------------------------------------------------------------
    # Categories
    # -------------------------------------------------------------------------

    def open_categories_dropdown(self):
        if self._is_visible(self.CATEGORY_CHECKBOX_BY_VALUE.format(value="SIGN_UP"), timeout=1000):
            return
        self._js_click(self.CATEGORIES_BUTTON, timeout=8000)
        self.page.wait_for_timeout(400)

    def _is_visible(self, locator, timeout=1000):
        try:
            return self.page.locator(locator).first.is_visible()
        except Exception:
            return False

    def is_category_checkbox_present(self, value):
        try:
            return self.page.locator(self.CATEGORY_CHECKBOX_BY_VALUE.format(value=value)).count() > 0
        except Exception:
            return False

    def toggle_category(self, value):
        self.open_categories_dropdown()
        cb = self.h.wait_for_element_visible(self.CATEGORY_CHECKBOX_BY_VALUE.format(value=value))
        cb.click(force=True)
        self.page.wait_for_timeout(600)

    def is_category_checked(self, value):
        self.open_categories_dropdown()
        try:
            return self.page.locator(self.CATEGORY_CHECKBOX_BY_VALUE.format(value=value)).first.is_checked()
        except Exception:
            return None

    # -------------------------------------------------------------------------
    # Screens
    # -------------------------------------------------------------------------

    def get_screens_counter_text(self):
        try:
            return self.page.locator(self.SCREENS_COUNTER).first.inner_text().strip()
        except Exception:
            return ""

    def get_screen_count(self):
        text = self.get_screens_counter_text()
        try:
            return int(text.split("/")[0].strip())
        except Exception:
            return None

    def is_add_screen_btn_present(self):
        return self.is_element_present(self.ADD_SCREEN_BTN, timeout=5000)

    def is_add_screen_btn_enabled(self):
        try:
            return self.page.locator(self.ADD_SCREEN_BTN).first.is_enabled()
        except Exception:
            return False

    def click_add_screen(self):
        self._js_click(self.ADD_SCREEN_BTN, timeout=8000)
        self.page.wait_for_timeout(800)

    def select_screen(self, index):
        self._js_click(self.SCREEN_ROW_BY_INDEX.format(index=index), timeout=8000)
        self.page.wait_for_timeout(500)

    def get_screen_title_value(self, index):
        return self.page.locator(self.SCREEN_TITLE_INPUT_BY_INDEX.format(index=index)).input_value()

    def set_screen_title(self, index, value):
        el = self.h.wait_for_element_visible(self.SCREEN_TITLE_INPUT_BY_INDEX.format(index=index))
        el.fill(value)
        el.blur()
        self.page.wait_for_timeout(600)

    # -------------------------------------------------------------------------
    # Edit content / components
    # -------------------------------------------------------------------------

    def get_edit_content_counter_text(self):
        try:
            return self.page.locator(self.EDIT_CONTENT_COUNTER).first.inner_text().strip()
        except Exception:
            return ""

    def get_component_count(self):
        text = self.get_edit_content_counter_text()
        try:
            return int(text.split("/")[0].strip())
        except Exception:
            return None

    def get_component_card_labels(self):
        try:
            cards = self.page.locator(self.COMPONENT_CARDS)
            labels = []
            for i in range(cards.count()):
                span = cards.nth(i).locator("span.text-sm.font-medium").first
                labels.append(span.inner_text().strip())
            return labels
        except Exception:
            return []

    # -------------------------------------------------------------------------
    # Add content
    # -------------------------------------------------------------------------

    def open_add_content_dropdown(self):
        if self._is_visible(self.ADD_CONTENT_CATEGORY_BTN["text"], timeout=1000):
            return
        # _js_click_first_visible, not _js_click: confirmed by a real
        # TC025 failure -- with several component cards already added,
        # plain _js_click's .first force-click on this button timed out
        # as "not visible" (18 scroll retries) even though the same
        # control had just worked for earlier additions on the same
        # screen. That signature matches this app's documented duplicate-
        # DOM-copy pattern (see Helpers.js_click_first_visible's
        # docstring) -- _js_click's blind .first can lock onto a hidden
        # copy once enough re-renders have happened, where scanning for
        # the actually-visible match does not.
        self._js_click_first_visible(self.ADD_CONTENT_BTN, timeout=8000)
        self.page.wait_for_timeout(400)

    def is_add_content_category_present(self, category):
        self.open_add_content_dropdown()
        return self.is_element_present(self.ADD_CONTENT_CATEGORY_BTN[category], timeout=5000)

    def _ensure_component_control_visible(self, component_type, category):
        # Each category toggle button TOGGLES its submenu open/closed
        # (Alpine: activeCategory === cat ? null : cat) -- a second click
        # on an already-open category would close it again. Make this
        # idempotent by checking whether the TARGET addComponent button
        # is already visible before clicking anything, so callers can
        # freely chain is_add_component_control_present() then
        # add_component() (or call either alone) without tracking
        # dropdown/submenu state themselves.
        btn = self.ADD_COMPONENT_BTN_BY_TYPE.format(type=component_type)
        if self._is_visible(btn, timeout=500):
            return
        self.open_add_content_dropdown()
        if self._is_visible(btn, timeout=500):
            return
        # Same duplicate-DOM-copy risk as open_add_content_dropdown()
        # above, for the category toggle itself.
        self._js_click_first_visible(self.ADD_CONTENT_CATEGORY_BTN[category], timeout=8000)
        self.page.wait_for_timeout(400)

    def is_add_component_control_present(self, component_type):
        category, _ = self.COMPONENT_TYPE_INFO[component_type]
        self._ensure_component_control_visible(component_type, category)
        return self.is_element_present(
            self.ADD_COMPONENT_BTN_BY_TYPE.format(type=component_type), timeout=5000
        )

    def add_component(self, component_type):
        """Adds a real component via the confirmed
        wire:click="addComponent('{type}'); closeDropdown()" button (see
        docstring point 9)."""
        category, _ = self.COMPONENT_TYPE_INFO[component_type]
        self._ensure_component_control_visible(component_type, category)
        self._js_click(self.ADD_COMPONENT_BTN_BY_TYPE.format(type=component_type), timeout=8000)
        self.page.wait_for_timeout(800)

    def remove_component(self, index):
        self._js_click(self.REMOVE_COMPONENT_BTN_BY_INDEX.format(index=index), timeout=8000)
        self.page.wait_for_timeout(600)

    # -------------------------------------------------------------------------
    # Save Flow
    # -------------------------------------------------------------------------

    def is_save_flow_btn_present(self):
        return self.is_element_present(self.SAVE_FLOW_BTN, timeout=8000)

    def is_save_flow_btn_enabled(self):
        try:
            return self.page.locator(self.SAVE_FLOW_BTN).first.is_enabled()
        except Exception:
            return False

    def click_save_flow(self):
        """The one deliberate exception to this page object's earlier
        presence/enabled-state-only stance on Save Flow (this project's
        documented caution around irreversible/data-creating actions
        against shared QA data) -- added specifically for the real,
        explicitly-requested E2E creation test in
        test_whatsapp_flows_flow.py (test_e2e_whatsapp_flow_creation_
        and_persistence). Matches the same click_save() convention
        already used for genuine Save actions elsewhere in this codebase
        (e.g. pages/sms/sms_sender_id_page.py,
        pages/whatsapp/whatsapp_template_create_page.py) -- a plain JS
        click, no guessed post-click behavior baked in here."""
        self._js_click(self.SAVE_FLOW_BTN, timeout=10000)
        self.page.wait_for_timeout(1000)

    def get_toast_or_swal_text(self):
        """Single-shot check of the confirmed app-global WireUI toast and
        SweetAlert2 title/html-container (see TOAST_NOTIFICATION_TEXT/
        SWAL_TITLE/SWAL_HTML_CONTAINER above). Returns the first
        non-empty, visible text found, or None. Identical in shape to
        whatsapp_template_create_page.py's method of the same name."""
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
        """Call AFTER click_save_flow(). This page's own real post-save
        DOM has never been captured, so no flow-specific "success"
        locator is guessed here -- polls for up to timeout_s for the
        FIRST of two generic, already-confirmed-elsewhere signals: the
        URL navigating away from the builder, or the app-global toast/
        SweetAlert2 feedback becoming visible. Returns a dict:
        {"outcome": "url_changed" | "toast_or_swal" | "none_detected",
         "url": <current url>, "text": <toast/swal text, if any>}.
        Identical in shape to whatsapp_template_create_page.py's method
        of the same name."""
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

    # -------------------------------------------------------------------------
    # View JSON (local-only modal, safe to open/close freely)
    # -------------------------------------------------------------------------

    def open_view_json_modal(self):
        self._js_click(self.VIEW_JSON_BTN, timeout=8000)
        self.page.wait_for_timeout(400)

    def is_json_modal_open(self):
        try:
            return self.page.locator(self.JSON_MODAL).first.is_visible()
        except Exception:
            return False

    def get_json_modal_content(self):
        try:
            return self.page.locator(self.JSON_MODAL_CONTENT).first.inner_text().strip()
        except Exception:
            return ""

    def close_view_json_modal(self):
        try:
            self._js_click(self.JSON_MODAL_CLOSE_BTN, timeout=5000)
        except Exception:
            pass
        self.page.wait_for_timeout(300)
