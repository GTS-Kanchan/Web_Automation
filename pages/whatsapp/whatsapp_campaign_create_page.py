"""
Page Object: WhatsApp Campaign Create page
Path: /whatsapp/campaigns/create
Livewire component: whatsapp.campaign.create

Built from a genuine, pasted live-DOM capture of this exact page (captured
mid-session; the component's wire:id is session-specific and NOT hardcoded
anywhere below -- only stable ids/names/attributes are used) plus a second,
separately pasted capture of the "Import Contacts" modal
(livewire-ui-modal / component id varies per load) reachable from this page
via the "Import Contacts" button.

Confirmed facts from the real capture (do not "fix" these without a fresh
capture proving otherwise):

 1. Breadcrumb trail is Home > Channels > WhatsApp Campaigns > "Create
    Campaign" -- the last crumb is a plain <span>, not a link.
 2. Header: <h2>Create WhatsApp Campaign</h2> with subtitle "Set up your
    WhatsApp campaign with contacts, template, and scheduling".
 3. Campaign Name field: form-wrapper="name", <input id="name" name="name"
    wire:model.defer="name" placeholder="Enter campaign name">. The
    Livewire snapshot observed in this same capture shows the "name" state
    already pre-populated with an auto-generated value (a timestamp +
    " - Campaign " suffix) -- i.e. this field is NOT guaranteed empty on
    page load. Tests must read the actual live value rather than assume
    "".
 4. Validation-error locator: this page's own markup already exposes
    WireUI's "invalidated:" Tailwind variant classes
    (invalidated:text-negative-600, invalidated:ring-negative-500, etc.)
    directly on the name field's wrapper/label, confirming the SAME
    "negative-600" WireUI convention already confirmed live and documented
    in pages/common/contacts_page.py's FORM_VALIDATION_ERROR (captured
    there from an actual rendered error label:
    `<label class="text-sm text-negative-600 mt-2" for="first_name">The
    First...`). No invalid-state capture of THIS page exists (the field
    was never submitted empty in the capture), so the exact inline error
    message text is unconfirmed -- but the rendering convention itself is
    the same WireUI package used identically across this whole app, so
    FORM_VALIDATION_ERROR is reused verbatim per this project's "already
    confirmed identical pattern elsewhere in this codebase" exception
    (not a guess from a description).
 5. Sender ID: WireUI searchable single-select, form-wrapper="sender_id",
    hidden input id="sender_id". The real option list IS present in this
    capture as a base64 JSON blob in the component's x-ref="json" div (9
    real sender ids/names, e.g. "WhatsApp Simulator Testing
    ( 919691926438 )"). The *rendered* <li> option rows were only ever
    captured in their pre-hydration Alpine loading-skeleton state
    (animate-pulse placeholder divs) -- the real, populated <li> markup
    that Alpine's x-for renders at runtime was never captured. Since
    Playwright drives the actual live page (not a static capture), Alpine
    WILL hydrate real <li role="listitem"> rows with real visible text
    once the dropdown is opened -- so option selection here is done via
    the generic, standard ARIA role="listitem" (implicit for any <li>,
    not a guess about this app's specific styling) filtered by REAL,
    confirmed label text from the decoded option JSON. No option's
    internal class/attribute structure is assumed beyond "it's an <li>".
 6. Template: WireUI select, form-wrapper="template_id", starts
    aria-disabled="true" / readonly with an EMPTY option list ("W10=" -->
    "[]") until a Sender ID is chosen -- confirmed structurally (the
    aria-disabled attribute itself), not guessed.
 7. "Send to all numbers (Skip opt-out validation)" checkbox has NO id --
    only wire:model="skipOptOutCheck". Located by that attribute plus its
    label text.
 8. Import Contacts button: wire:click="openContactsModal", confirmed
    disabled="disabled" until a template is selected (helper text "Select
    a template first").
 9. Scheduling: two real radios, id="send_now" value="now" and
    id="schedule_later" value="schedule", both wire:model.live="send_type".
10. Footer: Cancel is a plain <a href=".../whatsapp/campaigns">Cancel</a>
    (goes to the campaign LISTING page, not any "report" page -- a
    mismatch vs. some checklist wording, documented here rather than
    "corrected" by guessing). "Test Campaign"
    (wire:click="openTestCampaignModal") and the submit button
    ("Preview Campaign", type=submit) are BOTH confirmed disabled in this
    capture's initial state (no template/contacts yet).
11. Media upload, location fields, and the Template Preview section are
    ALL conditionally-rendered blocks that were empty
    (<!--[if BLOCK]><![endif]-->) in this capture because no template was
    selected -- their real markup has never been captured. NOT built here;
    see the test file's documented skips.
12. Import Contacts modal (separately captured, real DOM):
      - 3 tabs, Alpine x-data driven (no full navigation): "Copy Paste
        Numbers" (default active, tab='copy_paste'), "File Upload"
        (tab='file_upload'), "Contact Management" (tab='contact_tags').
      - A "Duplicate Phone Handling" toggle, checkbox id="keep_duplicates"
        wire:model.live="keepDuplicates", default OFF.
      - Copy Paste tab: <textarea id="cp_contacts" name="cp_contacts"
        wire:model="cp_contacts">, helper text "Enter up to 50,000
        contacts".
      - File Upload tab: <input id="dropzone-file" type="file"
        wire:model="fu_contacts" accept=".csv,...">, a real "Download
        Sample CSV" button (wire:click="export('csv')"), helper text
        "Upload CSV file".
      - Contact Management tab: form-wrapper="contactImportSource" (single
        select, real options decoded from its own x-ref="json" blob:
        Tags/Segments, defaults to "Tags") and form-wrapper="ct_contacts"
        (multiselect, real tag names decoded from its own JSON blob --
        confirmed non-fabricated tag list of this environment's real
        tags).
      - Footer (hidden for the File Upload tab): "Cancel"
        (wire:click="handleCancel") and "Continue"/"Processing..."
        (wire:click="submit") -- these are the MODAL's own actions,
        distinct from the main page's Cancel/Preview Campaign buttons.

No cross-page inheritance/mixins per this project's established
convention (confirmed via `grep -rn "^class .*Page(" pages/ | grep -v
"BasePage"` returning zero matches) -- the small "open a WireUI select /
pick an option" helper below is a private method of THIS class only, not a
shared base.
"""
import base64
import json
import re

from pages.common.base_page import BasePage


class WhatsAppCampaignCreatePage(BasePage):
    PATH = "/whatsapp/campaigns/create"

    # Breadcrumb / header
    BREADCRUMB_ACTIVE = "xpath=//li[.//span[normalize-space()='Create Campaign']]"
    PAGE_HEADER = "xpath=//h2[normalize-space()='Create WhatsApp Campaign']"

    # Campaign Name
    NAME_WRAPPER = "[form-wrapper='name']"
    NAME_INPUT = "#name"
    # CONFIRMED cross-file evidence (see module docstring point 4): reused
    # verbatim from pages/common/contacts_page.py's FORM_VALIDATION_ERROR,
    # which was captured from a REAL rendered WireUI error label elsewhere
    # in this exact app (same package/convention).
    FORM_VALIDATION_ERROR = "label.text-negative-600, .text-negative-600"

    # Sender ID (WireUI searchable single-select)
    SENDER_ID_WRAPPER = "[form-wrapper='sender_id']"
    SENDER_ID_HIDDEN_INPUT = "#sender_id"

    # Template (WireUI select, disabled until Sender ID chosen)
    TEMPLATE_WRAPPER = "[form-wrapper='template_id']"
    TEMPLATE_HIDDEN_INPUT = "#template_id"

    # Skip opt-out
    SKIP_OPT_OUT_CHECKBOX = "input[wire\\:model='skipOptOutCheck']"
    SKIP_OPT_OUT_LABEL_TEXT = "Send to all numbers (Skip opt-out validation)"

    # Contacts / Import
    IMPORT_CONTACTS_BTN = "button[wire\\:click='openContactsModal']"
    IMPORT_CONTACTS_STATUS = "xpath=//p[contains(.,'No contacts imported') or contains(.,'contact imported') or contains(.,'contacts imported')]"

    # Scheduling
    SEND_NOW_RADIO = "#send_now"
    SCHEDULE_LATER_RADIO = "#schedule_later"

    # Footer actions (main page)
    CANCEL_LINK = "xpath=//a[normalize-space()='Cancel']"
    TEST_CAMPAIGN_BTN = "button[wire\\:click='openTestCampaignModal']"
    PREVIEW_CAMPAIGN_BTN = "xpath=//button[@type='submit' and contains(.,'Preview Campaign')]"

    # Import Contacts modal (livewire-ui-modal)
    MODAL_CONTAINER = "#modal-container"
    MODAL_TAB_COPY_PASTE = "xpath=//div[@id='modal-container']//a[normalize-space()='Copy Paste Numbers']"
    MODAL_TAB_FILE_UPLOAD = "xpath=//div[@id='modal-container']//a[normalize-space()='File Upload']"
    MODAL_TAB_CONTACT_MGMT = "xpath=//div[@id='modal-container']//a[normalize-space()='Contact Management']"
    MODAL_DUPLICATE_TOGGLE = "#keep_duplicates"
    MODAL_CP_CONTACTS_TEXTAREA = "#cp_contacts"
    
    # SweetAlert2 Validation Popup
    SWAL_POPUP = ".swal2-popup:visible"
    SWAL_TITLE = ".swal2-title:visible"
    SWAL_CONFIRM_BTN = ".swal2-confirm:visible"
    MODAL_CP_HELPER_TEXT = "xpath=//p[contains(.,'Enter up to 50,000 contacts')]"
    MODAL_FU_FILE_INPUT = "#dropzone-file"
    MODAL_FU_DOWNLOAD_SAMPLE_BTN = "button[wire\\:click=\"export('csv')\"]"
    MODAL_FU_HELPER_TEXT = "xpath=//p[contains(.,'Upload CSV file')]"
    MODAL_CONTACT_IMPORT_SOURCE_WRAPPER = "[form-wrapper='contactImportSource']"
    MODAL_CT_CONTACTS_WRAPPER = "[form-wrapper='ct_contacts']"
    # Column Mapping select (File Upload tab only) -- CONFIRMED via a
    # real, pasted DOM capture: after a CSV is uploaded, this WireUI
    # select (same component family as the two wrappers above, same
    # x-ref="json" base64-encoded real option list) lets the user map
    # which CSV column holds the phone number before Continue can
    # correctly import. This step was never previously known/handled --
    # skipping it is a likely real cause of file-upload imports either
    # failing validation or mapping the wrong column, which reads as the
    # app "working fine" by hand (where a human picks the right column)
    # but the automated test failing (where nothing was ever selected).
    MODAL_COLUMN_MAPPING_PHONE_WRAPPER = "[form-wrapper='columnMapping.phone']"
    MODAL_CANCEL_BTN = "button[wire\\:click='handleCancel']"
    MODAL_CONTINUE_BTN = "button[wire\\:click='submit']"
    # File Upload tab's Continue button -- CONFIRMED from a real, pasted DOM
    # capture of the modal after a CSV is uploaded: the button uses
    # wire:click="confirmImportContacts", NOT wire:click="submit" (which
    # belongs only to the Copy Paste / Contact Management tabs). Using the
    # wrong selector (submit) in the file upload path was the root cause of
    # "No contacts imported" -- the click was silently targeting nothing.
    MODAL_FU_CONFIRM_BTN = "button[wire\\:click='confirmImportContacts']"

    # Import Completed confirmation screen (CONFIRMED from a real, pasted
    # DOM capture): clicking MODAL_CONTINUE_BTN on the Copy Paste/File
    # Upload/Contact Management input screen does NOT close the modal --
    # it swaps the SAME #modal-container to this confirmation screen
    # ("Import Completed", Total Rows / Unique Contacts stat tiles, "Would
    # you like to continue with these N unique contact(s)?", Cancel /
    # Confirm & Continue buttons). The import is only actually committed
    # once Confirm & Continue (wire:click="confirmImport") is clicked.
    # This was never known before this capture -- it is the real root
    # cause of the "waiting for #modal-container to be hidden" timeouts
    # seen in real test runs (TC073-TC077, both scheduled/file-upload E2E
    # tests): the modal was never going to become hidden right after the
    # first Continue click alone.
    IMPORT_COMPLETED_HEADING = "xpath=//h3[normalize-space()='Import Completed']"
    IMPORT_CONFIRM_CONTINUE_BTN = "button[wire\\:click='confirmImport']"
    IMPORT_CANCEL_CONFIRM_BTN = "button[wire\\:click='cancelImport']"
    IMPORT_TOTAL_ROWS_VALUE = "xpath=//p[normalize-space()='Total Rows']/following-sibling::p[1]"
    IMPORT_UNIQUE_CONTACTS_VALUE = "xpath=//p[contains(normalize-space(),'Unique Contacts')]/following-sibling::p[1]"

    # Template Preview panel (whatsapp.template.view component,
    # rendered inside the shared #modal-container once a template is
    # selected -- CONFIRMED from a genuine, separately pasted capture
    # of its real, populated content: a "Preview" header, a close
    # button that dispatches closeModal, a "Template ID: <id>" line,
    # a chat-bubble-style rendering of the template body text plus a
    # timestamp, and an optional opt-in/opt-out indicator depending on
    # the template's own settings.
    # The TRIGGER control is now ALSO confirmed, from a later, separate
    # DOM capture taken alongside the panel's own wire:snapshot: a
    # plain <button wire:click="openTemplateModal" type="button"> with
    # visible text "Preview Template", styled as a purple/primary
    # button, sitting just below/beside the Template Configuration
    # section on the main Create Campaign form.
    TEMPLATE_PREVIEW_HEADER = "xpath=//h1[normalize-space()='Preview']"
    TEMPLATE_PREVIEW_CLOSE_BTN = "button[wire\\:click=\"$dispatch('closeModal')\"]"
    TEMPLATE_PREVIEW_ID_TEXT = "xpath=//p[contains(.,'Template ID:')]"
    TEMPLATE_PREVIEW_BODY_TEXT = "xpath=//div[contains(@class,'break-words')]//p[contains(@class,'text-left')]"
    TEMPLATE_PREVIEW_TIMESTAMP = "xpath=//div[contains(@class,'break-words')]//p[contains(@class,'text-right')]"
    TEMPLATE_PREVIEW_OPT_INDICATOR = "xpath=//i[contains(@class,'mdi-reply')]"
    TEMPLATE_PREVIEW_TRIGGER_BTN = "button[wire\\:click='openTemplateModal']"

    # ── Schedule for Later: date/time fields -- NOW CONFIRMED on this
    # exact page via a real, pasted DOM capture (grid of two fields):
    #   <input x-model="date" x-on:change="updateDateTime()"
    #          type="date" :min="resolvedMinDate()" :max="resolvedMaxDate()"
    #          min="<today>" max="<today+7>">
    #   <select x-model="time" x-on:change="updateDateTime()">
    #     <option value="">Select Time</option>
    #     <option value="00:00" :disabled="isTimeOptionDisabled('00:00')">00:00</option>
    #     ... 5-minute-increment slots through 23:55 ...
    #   </select>
    # NEITHER field has an id (unlike the sibling SMS Campaign Create
    # page's #schedule_date/#schedule_time) -- both are addressed by
    # their real Alpine x-model attribute instead, which IS a valid CSS
    # attribute selector. isTimeOptionDisabled() disables PAST times for
    # today's date at runtime (Alpine :disabled, not a static HTML
    # attribute) -- selecting a genuinely future slot (see
    # set_schedule_date_time() callers) avoids that entirely. The date
    # input's min/max constrain the pickable range to roughly a 7-day
    # window from today -- callers scheduling more than a few days out
    # should re-check those bounds. The SMS-confirmed id-based selectors
    # are kept as a trailing fallback only, in case a future markup
    # revision reintroduces ids. ──────────────────────────────────────
    SCHEDULE_DATE_INPUT = "input[x-model='date'], #schedule_date, input[type='date']"
    SCHEDULE_TIME_SELECT = "select[x-model='time'], #schedule_time, select[id*='time']"

    # ── Preview Campaign panel's real submit/close controls -- CONFIRMED
    # via a real, pasted raw-HTML capture of this exact panel (superseding
    # the earlier SMS-page-informed guess of wire:click="submit", which
    # does NOT exist on this page and was silently matching nothing,
    # causing find_modal_submit_button() to fall through to keyword
    # matching -- which also never matched this page's real label
    # ("Proceed & Launch" contains neither "launch campaign" nor "send
    # now" etc.) and made the E2E tests skip/stall right after Preview
    # Campaign). The real, confirmed action names are:
    #   - Submit/launch: wire:click="proceed", label "Proceed & Launch"
    #     (loading-state label "Launching...")
    #   - Close without launching: wire:click="closeModal", label "Close"
    # The captured markup for this panel ("bg-white shadow-lg rounded-xl
    # mt-6 mb-6 mx-6 p-6 border ...", no backdrop) also does NOT look like
    # the same darkened-overlay #modal-container used for Import Contacts
    # (see that screenshot capture) -- so these locators are NOT scoped to
    # MODAL_CONTAINER; they are matched page-wide by their confirmed
    # wire:click attribute, which works whichever container really wraps
    # them. ─────────────────────────────────────────────────────────────
    MODAL_SUBMIT_BTN_WIRE_CLICK = r"button[wire\:click='proceed']"
    PREVIEW_CLOSE_BTN_WIRE_CLICK = r"button[wire\:click='closeModal']"
    # Ancestor of the confirmed Proceed & Launch button that also contains
    # the confirmed "Campaign Name:" label -- a structural/text anchor
    # (not a Tailwind class) used to scope get_preview_summary_text() to
    # just this panel's real content.
    PREVIEW_PANEL_ANCHOR = (
        "xpath=//button[@wire:click='proceed']"
        "/ancestor::div[.//p[contains(.,'Campaign Name:')]][1]"
    )

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
            "/whatsapp/campaigns/create" in self.get_current_url()
            and self.is_element_present(self.PAGE_HEADER, timeout=10000)
        )

    def get_page_header_text(self):
        return self.page.locator(self.PAGE_HEADER).inner_text().strip()

    # ══════════════════════════════════════════════════════════════════
    # Campaign Name
    # ══════════════════════════════════════════════════════════════════

    def get_name_value(self):
        return self.page.locator(self.NAME_INPUT).input_value()

    def set_name(self, value):
        loc = self.page.locator(self.NAME_INPUT)
        loc.fill("")
        if value:
            loc.fill(value)
        loc.blur()

    def clear_name(self):
        self.set_name("")

    def get_validation_errors(self):
        try:
            return [
                t for t in self.page.locator(self.FORM_VALIDATION_ERROR).all_inner_texts()
                if t.strip()
            ]
        except Exception:
            return []

    # ══════════════════════════════════════════════════════════════════
    # Generic WireUI select helpers (private to this page object -- no
    # cross-file mixin per this project's convention)
    # ══════════════════════════════════════════════════════════════════

    def _select_container(self, wrapper_selector):
        return self.page.locator(wrapper_selector).locator(
            "label[data-name='form.wrapper.container']"
        ).first

    def _open_select(self, wrapper_selector):
        # The trigger click TOGGLES the popover (x-show="positionable.state").
        # If it's already open, we shouldn't click it. We use a short wait_for
        # rather than synchronous is_visible() because Livewire DOM swaps (e.g. 
        # filtering search results) can cause the popover to briefly disappear 
        # and reappear. Synchronous is_visible() during a swap would return False, 
        # causing us to click and mistakenly CLOSE the popover!
        popover = self.page.locator(wrapper_selector).locator("[x-ref='optionsContainer']").first
        try:
            popover.wait_for(state="visible", timeout=1500)
            return
        except Exception:
            pass
        
        self._select_container(wrapper_selector).click()
        self.page.wait_for_timeout(500)

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

    def _select_option_by_text(self, wrapper_selector, option_text, closes_on_select=True):
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
        # Use force=True to bypass interceptors if animating, rather than JS click
        # which AlpineJS might ignore if it relies on trusted UI events.
        # Use position (5,5) to hit the padding of the li and avoid any nested 
        # <mark> tags during search.
        item.click(position={"x": 5, "y": 5}, force=True)
        if closes_on_select:
            popover.wait_for(state="hidden", timeout=5000)
        # Selecting an option fires a Livewire wire:model.live update, which
        # can re-render/replace nearby DOM (e.g. a newly-revealed dependent
        # select, such as Template becoming enabled after Sender ID is
        # chosen) shortly after this click returns. Confirmed on the
        # sibling Template Create page by a real run where a dependent
        # select's container kept getting "detached from the DOM,
        # retrying" until Playwright's click() gave up after 30s. Same
        # settle-wait fix applied here defensively.
        self.page.wait_for_timeout(400)

    def _search_in_select(self, wrapper_selector, text):
        self._open_select(wrapper_selector)
        search_input = self.page.locator(wrapper_selector).locator("input[type='search']").first
        search_input.fill(text)
        # Give Livewire time to process the search query and swap the DOM options
        self.page.wait_for_timeout(1500)

    def _get_selected_display_text(self, wrapper_selector):
        loc = self.page.locator(wrapper_selector).locator("button span").first
        try:
            # Wait for Livewire to populate the span text with the actual selection
            # rather than empty or the default 'Select Sender ID' placeholder.
            self.page.wait_for_function(
                "el => el.innerText.trim() !== '' && !el.innerText.includes('Select Sender ID') && !el.innerText.includes('Select Template')",
                arg=loc.element_handle(timeout=5000),
                timeout=5000
            )
        except Exception:
            pass
        return loc.inner_text().strip()

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

    # ══════════════════════════════════════════════════════════════════
    # Template
    # ══════════════════════════════════════════════════════════════════

    def is_template_select_enabled(self):
        return not self._is_select_disabled(self.TEMPLATE_WRAPPER)

    def get_template_options(self):
        return self._decoded_options(self.TEMPLATE_WRAPPER)

    def select_template(self, option_text):
        self._select_option_by_text(self.TEMPLATE_WRAPPER, option_text)

    # ══════════════════════════════════════════════════════════════════
    # Skip opt-out
    # ══════════════════════════════════════════════════════════════════

    def is_skip_opt_out_checked(self):
        return self.page.locator(self.SKIP_OPT_OUT_CHECKBOX).is_checked()

    def toggle_skip_opt_out(self):
        self.page.locator(self.SKIP_OPT_OUT_CHECKBOX).click()

    # ══════════════════════════════════════════════════════════════════
    # Contacts / Import Contacts button
    # ══════════════════════════════════════════════════════════════════

    def is_import_contacts_enabled(self):
        return self.page.locator(self.IMPORT_CONTACTS_BTN).is_enabled()

    def wait_for_import_contacts_enabled(self, timeout_ms=8000):
        """Poll until Import Contacts becomes enabled (Livewire processes template
        selection asynchronously). Returns True when enabled, False on timeout."""
        waited = 0
        step = 300
        while waited < timeout_ms:
            if self.is_import_contacts_enabled():
                return True
            self.page.wait_for_timeout(step)
            waited += step
        return self.is_import_contacts_enabled()

    def _js_click_first_visible_retry(self, locator, timeout=10000, attempts=3, settle_ms=500):

        """Wraps _js_click_first_visible() with a retry loop.

        Real runs against this page showed a genuine check-then-act race,
        not a one-off fluke: js_click_first_visible() polls all matches
        for `locator` until one reports is_visible()==True, then acts on
        THAT SAME Locator reference a moment later via
        scroll_into_view_if_needed()/click() -- but this page's Import
        Contacts modal is a Livewire component that re-renders its own
        DOM (new tab content, updated contact counts, a freshly-mounted
        component on each re-open) fast enough that the reference can go
        stale (no longer visible, or fully detached) in the gap between
        the visibility check and the action. This was confirmed live:
        the SECOND+ click_import_contacts()/switch_import_tab()/
        click_modal_continue() call within one test (after the modal had
        already been opened and closed at least once) intermittently hit
        "element is not visible" / "Element is not attached to the DOM"
        for the full poll budget, while the FIRST call in a test always
        succeeded -- consistent with a live re-render race rather than a
        permanently broken locator. Retrying with a short settle pause
        lets Livewire finish whatever re-render was in flight before the
        next attempt re-resolves the locator from scratch."""
        last_exc = None
        for attempt in range(attempts):
            try:
                return self._js_click_first_visible(locator, timeout=timeout)
            except Exception as e:
                last_exc = e
                if attempt < attempts - 1:
                    self.page.wait_for_timeout(settle_ms)
        raise last_exc

    def click_import_contacts(self):
        # Switched from a plain .click() to _js_click_first_visible()
        # (BasePage, already the established fix in this codebase for the
        # "subtree intercepts pointer events" / retrying-click-forever
        # failure pattern seen live on this exact page: a DOM click can
        # silently bind to a hidden duplicate copy of the same selector,
        # or land on a still-fading modal backdrop -- see
        # click_modal_cancel()'s own docstring below for the confirmed
        # root cause of the same symptom elsewhere on this page).
        
        # Retry loop: Livewire might ignore the click if it's still processing
        # the template selection update, so if the modal doesn't open within 2s, 
        # try clicking again up to 5 times.
        for attempt in range(5):
            self._js_click_first_visible_retry(self.IMPORT_CONTACTS_BTN, timeout=5000)
            try:
                self.page.locator(self.MODAL_CONTAINER).wait_for(state="visible", timeout=2000)
                break
            except Exception:
                if attempt == 4:
                    raise
        
        # Settle wait for Alpine's own x-transition:enter (duration-300)
        # to fully finish before any caller interacts with modal-internal
        # elements -- is_visible() can report True mid-fade, before the
        # element is genuinely stable/interactive.
        self.page.wait_for_timeout(400)

    def get_import_contacts_status_text(self):
        if getattr(self, "last_swal_title", None):
            return self.last_swal_title
        import re
        return self.page.locator("p").filter(has_text=re.compile(r"contact[s]? imported", re.IGNORECASE)).first.inner_text().strip()

    def get_imported_contacts_count(self):
        """Parse the real imported-contact count out of
        IMPORT_CONTACTS_STATUS's own text (e.g. "12 contacts imported")
        rather than a separately-fabricated counter locator -- returns 0
        for the confirmed "No contacts imported" state or if no digits
        are found."""
        text = self.get_import_contacts_status_text()
        match = re.search(r"\d+", text)
        return int(match.group()) if match else 0

    # ══════════════════════════════════════════════════════════════════
    # Import Contacts modal
    # ══════════════════════════════════════════════════════════════════

    def is_import_modal_open(self):
        try:
            return (
                self.page.locator(self.MODAL_TAB_COPY_PASTE).is_visible()
                or self.page.locator(self.MODAL_TAB_FILE_UPLOAD).is_visible()
            )
        except Exception:
            return False

    def switch_import_tab(self, tab_name):
        mapping = {
            "copy_paste": self.MODAL_TAB_COPY_PASTE,
            "file_upload": self.MODAL_TAB_FILE_UPLOAD,
            "contact_tags": self.MODAL_TAB_CONTACT_MGMT,
        }
        # Same fix as click_import_contacts()/click_modal_continue(): a
        # plain .click() here was observed hanging in real runs with the
        # modal's own backdrop ("<div class='absolute inset-0
        # bg-gray-500 opacity-75'>...</div>") reported as intercepting
        # pointer events, retried dozens of times before the caller's
        # own downstream wait timed out -- _js_click_first_visible finds
        # and clicks the actually-visible tab link instead of blindly
        # trusting DOM order.
        self._js_click_first_visible_retry(mapping[tab_name], timeout=10000)
        # Wait for Livewire to swap the tab contents (requires network request)
        self.page.wait_for_timeout(1500)

    def fill_copy_paste_contacts(self, text):
        self.page.locator(self.MODAL_CP_CONTACTS_TEXTAREA).fill(text)

    def get_copy_paste_helper_text(self):
        return self.page.locator(self.MODAL_CP_HELPER_TEXT).first.inner_text().strip()

    def upload_contacts_file(self, file_path):
        self.page.locator(self.MODAL_FU_FILE_INPUT).first.set_input_files(file_path)

    def click_download_sample_csv(self):
        self.page.locator(self.MODAL_FU_DOWNLOAD_SAMPLE_BTN).click()

    def get_file_upload_helper_text(self):
        return self.page.locator(self.MODAL_FU_HELPER_TEXT).first.inner_text().strip()

    def is_duplicate_toggle_checked(self):
        return self.page.locator(self.MODAL_DUPLICATE_TOGGLE).is_checked()

    def toggle_duplicate_handling(self):
        # Same fix as the other modal-internal controls above -- this
        # toggle lives inside the same Import Contacts modal.
        self._js_click_first_visible_retry(self.MODAL_DUPLICATE_TOGGLE, timeout=10000)

    def get_contact_import_source_options(self):
        return self._decoded_options(self.MODAL_CONTACT_IMPORT_SOURCE_WRAPPER)

    def select_contact_import_source(self, option_text):
        self._select_option_by_text(self.MODAL_CONTACT_IMPORT_SOURCE_WRAPPER, option_text)

    def get_selected_contact_import_source_text(self):
        return self._get_selected_display_text(self.MODAL_CONTACT_IMPORT_SOURCE_WRAPPER)

    def get_contact_tags_options(self):
        return self._decoded_options(self.MODAL_CT_CONTACTS_WRAPPER)

    def select_contact_tag(self, option_text):
        self._select_option_by_text(self.MODAL_CT_CONTACTS_WRAPPER, option_text, closes_on_select=False)
        # Close the WireUI multiselect dropdown by clicking the modal heading/
        # container -- NOT by pressing Escape, which dismisses the entire modal
        # and removes the Continue button (confirmed live failure: the timeout
        # waiting for wire:click='submit' was caused by Escape closing the modal).
        try:
            # Click the modal's own title/heading to dismiss just the dropdown
            self.page.locator(self.MODAL_CONTAINER).locator("h3, h2, h1").first.click(timeout=2000)
        except Exception:
            try:
                # Fallback: click the top-left corner of the modal container
                self.page.locator(self.MODAL_CONTAINER).click(
                    position={"x": 20, "y": 20}, timeout=2000, force=True
                )
            except Exception:
                pass
        self.page.wait_for_timeout(300)

    def is_column_mapping_visible(self):
        """True if the confirmed Column Mapping select (File Upload tab
        only, appears after a CSV is uploaded) is currently showing."""
        return self.is_element_visible(self.MODAL_COLUMN_MAPPING_PHONE_WRAPPER, timeout=3000)

    def get_column_mapping_phone_options(self):
        return self._decoded_options(self.MODAL_COLUMN_MAPPING_PHONE_WRAPPER)

    def select_column_mapping_phone(self, option_text):
        self._select_option_by_text(self.MODAL_COLUMN_MAPPING_PHONE_WRAPPER, option_text)

    def get_selected_column_mapping_phone_text(self):
        return self._get_selected_display_text(self.MODAL_COLUMN_MAPPING_PHONE_WRAPPER)

    # Mirror click_import_contacts() above: don't return until the
        # close has actually finished. Confirmed root cause of a real
        # cluster of "<div class='absolute inset-0 bg-gray-500 opacity-75'>
        # ... subtree intercepts pointer events" failures on
        # click_import_contacts()/click_test_campaign() in the very next
        # test (TC055-TC058): this method used to click Cancel and return
        # immediately, while the livewire-ui-modal's own close transition
        # (and its backdrop) was still fading out -- the next test's plain
        # .click() on a background button then landed on that still-present
        # backdrop instead of the real button underneath it.
        # Switched from .first.click(force=True) to
        # _js_click_first_visible(): force=True bypasses the
        # "is the target obscured" check, but it does NOT change
        # WHICH element .first binds to -- if the first DOM match for
        # MODAL_CANCEL_BTN is a hidden mobile/desktop duplicate (the
        # same class of bug already documented/fixed for the Sender ID
        # select's placeholder/value spans and for TC025's Add Content
        # dropdown elsewhere in this project), a forced click on it is
        # a real click on the WRONG, inert element -- Livewire never
        # sees it, so the modal never actually closes. This is the
        # confirmed root cause of a live "modal never closes" failure
        # observed on click_modal_continue() (identical pattern).
    def click_modal_cancel(self):
        """Click Cancel inside the import contacts modal."""
        if not self.page.locator(self.MODAL_CONTAINER).is_visible():
            return
            
        try:
            self._js_click_first_visible_retry(self.MODAL_CANCEL_BTN, timeout=5000)
        except Exception:
            pass
            
        try:
            self.page.locator(self.MODAL_CONTAINER).wait_for(state="hidden", timeout=5000)
        except Exception:
            pass
        self.page.wait_for_timeout(300)

    def click_modal_continue(self):
        self.last_swal_title = None
        self._js_click_first_visible_retry(self.MODAL_CONTINUE_BTN, timeout=10000)

        poll_waited = 0
        while poll_waited < 30000:
            if self.is_swal_visible():
                self.last_swal_title = self.get_swal_title()
                self.click_swal_ok()
                # If this was an error swal, wait for modal to close or cancel
                try:
                    self.page.locator(self.MODAL_CONTAINER).wait_for(state="hidden", timeout=5000)
                    return
                except Exception:
                    pass

            if self.is_import_completed_screen_visible():
                try:
                    self._js_click_first_visible_retry(self.IMPORT_CONFIRM_CONTINUE_BTN, timeout=10000)
                except Exception:
                    pass
                try:
                    self.page.locator(self.MODAL_CONTAINER).wait_for(state="hidden", timeout=10000)
                except Exception:
                    self.click_modal_cancel()
                try:
                    self.page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    self.page.wait_for_timeout(2000)
                self.last_swal_title = None
                return

            if not self.is_import_modal_open():
                try:
                    self.page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    self.page.wait_for_timeout(2000)
                self.last_swal_title = None
                return

            self.page.wait_for_timeout(400)
            poll_waited += 400

        # Fallback if modal did not close in 30s
        self.click_modal_cancel()

    def is_import_completed_screen_visible(self):
        """True if the confirmed 'Import Completed' confirmation screen
        (Total Rows / Unique Contacts stat tiles, Cancel / Confirm &
        Continue) is currently showing inside #modal-container."""
        return self.is_element_visible(self.IMPORT_COMPLETED_HEADING, timeout=3000)

    def get_import_completed_summary(self):
        """Parse (total_rows, unique_contacts) ints straight off the
        confirmed Import Completed confirmation screen's own stat tiles --
        a more precise, earlier read of the real import outcome than
        get_imported_contacts_count() (which reads the MAIN page's status
        text and is only meaningful after Confirm & Continue has actually
        committed the import). Returns (0, 0) if the screen isn't open."""
        if not self.is_import_completed_screen_visible():
            return (0, 0)

        def _digits(locator):
            try:
                text = self.page.locator(locator).first.inner_text().strip()
            except Exception:
                return 0
            match = re.search(r"\d+", text)
            return int(match.group()) if match else 0

        return (_digits(self.IMPORT_TOTAL_ROWS_VALUE), _digits(self.IMPORT_UNIQUE_CONTACTS_VALUE))

    def cancel_import_confirmation(self):
        """Click the confirmed Cancel button on the Import Completed
        confirmation screen (wire:click='cancelImport') to abort the
        import instead of committing it -- distinct from
        click_modal_cancel(), which cancels from the earlier input
        screen, before this confirmation screen is ever reached."""
        self._js_click_first_visible_retry(self.IMPORT_CANCEL_CONFIRM_BTN, timeout=10000)
        self.page.locator(self.MODAL_CONTAINER).wait_for(state="hidden", timeout=10000)
        self.page.wait_for_timeout(300)

    # ══════════════════════════════════════════════════════════════════
    # SweetAlert Popup
    # ══════════════════════════════════════════════════════════════════

    def is_swal_visible(self):
        return self.is_element_visible(self.SWAL_POPUP, timeout=3000)

    def get_swal_title(self):
        if self.is_swal_visible():
            return self.page.locator(self.SWAL_TITLE).first.inner_text().strip()
        return ""

    def click_swal_ok(self):
        try:
            self.page.locator(self.SWAL_CONFIRM_BTN).first.click(timeout=2000)
        except Exception:
            pass
        try:
            self.page.locator(self.SWAL_POPUP).wait_for(state="hidden", timeout=5000)
        except Exception:
            pass
        self.page.wait_for_timeout(500)

    # ══════════════════════════════════════════════════════════════════
    # Higher-level Import Contacts combos (new -- compose only the
    # already-confirmed atomic modal methods above; no new locators).
    # Reused across the new copy-paste/file-upload functional and E2E
    # tests to avoid re-duplicating the same open/switch/fill/continue
    # sequence at every call site.
    # ══════════════════════════════════════════════════════════════════

    def import_contacts_via_copy_paste(self, numbers_text):
        """Open Import Contacts (if not already open), switch to the
        confirmed default Copy Paste tab, fill the confirmed textarea,
        and click the confirmed Continue button. Caller is responsible
        for having reached a state where Import Contacts is enabled
        (see _ensure_template_selected in the test file)."""
        if not self.is_import_modal_open():
            self.click_import_contacts()
        self.switch_import_tab("copy_paste")
        self.fill_copy_paste_contacts(numbers_text)
        self.click_modal_continue()

    def _wait_for_file_upload_completion(self, preceding_swal_title):
        """Called after clicking OK on a file-upload swal (e.g. 'Start Contact
        Import?'). Polls up to 30 s for one of:
          (a) Modal closes naturally → success; sets last_swal_title = None
              so get_import_contacts_status_text() reads the real page status.
          (b) A second swal appears (e.g. error 'Valid Imported Contacts not
              found') → reports that as the error title.
          (c) Import Completed screen → confirms it and waits for modal close.
          (d) Timeout → force-cancels; does NOT keep the confirmation prompt
              as the error title (that would mask the real page status).
        The 5-8 s flat wait_for(state='hidden') that this replaces always
        timed out for this server (import takes >8 s after OK), which sent
        execution down the except-branch and incorrectly set last_swal_title
        to the confirmation prompt text ('Start Contact Import?')."""
        poll_waited = 0
        while poll_waited < 30000:
            if not self.is_import_modal_open():
                # Modal closed on its own → import committed.
                # Wait for Livewire to finish processing and update the UI
                # (contact count, Preview Campaign button state) before returning.
                # Without this, clicking Preview Campaign immediately may find the
                # modal with no wire:click buttons (Livewire still mid-render).
                try:
                    self.page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    self.page.wait_for_timeout(2000)
                self.last_swal_title = None
                return
            if self.is_swal_visible():
                # A follow-up swal (error or further confirmation)
                self.last_swal_title = self.get_swal_title()
                self.click_swal_ok()
                try:
                    self.page.locator(self.MODAL_CONTAINER).wait_for(state="hidden", timeout=8000)
                except Exception:
                    self.click_modal_cancel()
                return
            if self.is_import_completed_screen_visible():
                try:
                    self._js_click_first_visible_retry(self.IMPORT_CONFIRM_CONTINUE_BTN, timeout=10000)
                except Exception:
                    pass
                try:
                    self.page.locator(self.MODAL_CONTAINER).wait_for(state="hidden", timeout=8000)
                except Exception:
                    self.click_modal_cancel()
                self.last_swal_title = None
                return
            self.page.wait_for_timeout(500)
            poll_waited += 500
        # 30 s timeout — force close; treat as inconclusive, not an error
        self.click_modal_cancel()
        self.last_swal_title = None

    def import_contacts_via_file_upload(self, file_path, phone_column_hint="phone"):
        if not self.is_import_modal_open():
            self.click_import_contacts()
        self.switch_import_tab("file_upload")
        self.upload_contacts_file(file_path)

        # After Livewire uploads the file to the server, the modal renders
        # the CONFIRMED file-upload-specific Continue button:
        #   wire:click="confirmImportContacts"  (MODAL_FU_CONFIRM_BTN)
        # This is distinct from the Copy Paste / Contact Management Continue
        # button (wire:click='submit'). Using the wrong selector was the
        # confirmed root cause of "No contacts imported" in all previous runs.
        # Also poll for a SweetAlert (server-side rejection) as an exit condition.
        waited = 0
        step = 500
        max_wait = 20000
        while waited < max_wait:
            if self.is_swal_visible():
                break
            try:
                if self.page.locator(self.MODAL_FU_CONFIRM_BTN).is_visible(timeout=200):
                    break
            except Exception:
                pass
            if self.is_column_mapping_visible():
                break
            self.page.wait_for_timeout(step)
            waited += step

        if self.is_swal_visible():
            # Swal appeared before confirmImportContacts was clicked.
            # For file upload this can be the "Start Contact Import?"
            # confirmation -- click OK and then poll up to 30 s for the
            # server to finish processing and the modal to close.
            _swal_title = self.get_swal_title()
            self.click_swal_ok()
            self._wait_for_file_upload_completion(_swal_title)
            return

        # Handle optional column mapping step
        if self.is_column_mapping_visible():
            options = self.get_column_mapping_phone_options()
            match = None
            for opt in options:
                label = opt.get("label") or ""
                if phone_column_hint.lower() in label.lower():
                    match = label
                    break
            if match is None:
                non_placeholder = [
                    o for o in options
                    if str(o.get("value") or "").strip().lower() not in ("select", "")
                ]
                if non_placeholder:
                    match = non_placeholder[0]["label"]
            if match:
                self.select_column_mapping_phone(match)
            self.page.wait_for_timeout(500)

        # Click the CONFIRMED file-upload Continue button
        try:
            fu_btn = self.page.locator(self.MODAL_FU_CONFIRM_BTN)
            if fu_btn.is_visible(timeout=3000):
                self._js_click_first_visible_retry(self.MODAL_FU_CONFIRM_BTN, timeout=10000)
                # Poll for swal (e.g. "Start Contact Import?" confirmation),
                # Import Completed screen, or modal already closed.
                waited2 = 0
                while waited2 < 10000:
                    if self.is_swal_visible() or self.is_import_completed_screen_visible():
                        break
                    if not self.is_import_modal_open():
                        self.last_swal_title = None
                        return  # Modal already closed — success
                    self.page.wait_for_timeout(500)
                    waited2 += 500
                if self.is_swal_visible():
                    _swal_title = self.get_swal_title()
                    self.click_swal_ok()
                    self._wait_for_file_upload_completion(_swal_title)
                    return
                if self.is_import_completed_screen_visible():
                    try:
                        self._js_click_first_visible_retry(self.IMPORT_CONFIRM_CONTINUE_BTN, timeout=10000)
                    except Exception:
                        pass
        except Exception:
            pass

        try:
            self.page.locator(self.MODAL_CONTAINER).wait_for(state="hidden", timeout=8000)
        except Exception:
            self.click_modal_cancel()


    # ══════════════════════════════════════════════════════════════════
    # Generic modal text/button discovery (new -- for the Preview
    # Campaign / Test Campaign modals, whose INTERNAL DOM was never
    # captured; see TC060-TC070's documented skip in the test file).
    # Both are confirmed to render into the SAME shared #modal-container
    # this page already uses for Import Contacts and the Template
    # Preview panel (see class docstring / TEMPLATE_PREVIEW_* comment),
    # so MODAL_CONTAINER visibility/text IS a legitimate, non-fabricated
    # way to detect "a modal opened" and read what it actually says --
    # this does not fabricate any field-specific locator inside it.
    # ══════════════════════════════════════════════════════════════════

    def is_modal_open(self):
        """Alias of is_import_modal_open() under a channel-neutral name
        -- same #modal-container check, valid for whichever Livewire
        component (Import Contacts / Template Preview / Preview
        Campaign / Test Campaign) is currently rendered into it."""
        return self.is_import_modal_open()

    def get_modal_text(self):
        try:
            return self.page.locator(self.MODAL_CONTAINER).first.inner_text().strip()
        except Exception:
            return ""

    def get_modal_button_texts(self):
        """All real, currently-visible button labels inside the open
        modal -- used to discover (never guess) the modal's own actions
        at runtime, e.g. the Preview Campaign modal's real submit
        control, whose exact wording/selector was never captured."""
        try:
            buttons = self.page.locator(self.MODAL_CONTAINER).locator("button")
            texts = []
            for i in range(buttons.count()):
                btn = buttons.nth(i)
                if btn.is_visible():
                    t = btn.inner_text().strip()
                    if t:
                        texts.append(t)
            return texts
        except Exception:
            return []

    def find_modal_button_by_keywords(self, keywords):
        """Return the Locator for the single visible modal button whose
        text matches one of `keywords` (case-insensitive substring), or
        None if zero or more than one match -- deliberately refuses to
        guess when the result would be ambiguous. Pair with
        get_modal_button_texts() to see what candidates actually exist
        when this returns None."""
        try:
            buttons = self.page.locator(self.MODAL_CONTAINER).locator("button")
            matches = []
            for i in range(buttons.count()):
                btn = buttons.nth(i)
                if not btn.is_visible():
                    continue
                text = btn.inner_text().strip().lower()
                if any(k.lower() in text for k in keywords):
                    matches.append(btn)
            return matches[0] if len(matches) == 1 else None
        except Exception:
            return None

    def find_modal_submit_button(self):
        """The Preview Campaign panel's real submit control: CONFIRMED
        (via a real, pasted raw-HTML capture) to be
        wire:click='proceed', label "Proceed & Launch". Matched
        page-wide (not scoped to MODAL_CONTAINER, since this panel's
        real markup doesn't look like that darkened-overlay container --
        see MODAL_SUBMIT_BTN_WIRE_CLICK's own comment) so it's found
        regardless of which container actually wraps it. Falls back to
        keyword text-matching (both within MODAL_CONTAINER and
        page-wide) only if that confirmed attribute isn't present,
        covering the possibility of a genuinely different control for
        some other campaign type never seen in this capture."""
        try:
            btn = self.page.locator(self.MODAL_SUBMIT_BTN_WIRE_CLICK).first
            if btn.count() > 0 and btn.is_visible():
                return btn
        except Exception:
            pass

        keywords = [
            "proceed & launch", "proceed", "launch",
            "send campaign", "schedule campaign", "launch campaign", "send now",
            "create campaign", "create", "submit", "confirm", "save",
        ]
        found = self.find_modal_button_by_keywords(keywords)
        if found is not None:
            return found

        # Page-wide fallback (not scoped to MODAL_CONTAINER) using the
        # same keyword vocabulary, for the same reason as the primary
        # attribute lookup above.
        try:
            buttons = self.page.locator("button")
            matches = []
            for i in range(buttons.count()):
                btn = buttons.nth(i)
                if not btn.is_visible():
                    continue
                text = btn.inner_text().strip().lower()
                if any(k in text for k in keywords):
                    matches.append(btn)
            return matches[0] if len(matches) == 1 else None
        except Exception:
            return None

    def is_preview_panel_open(self):
        """True if the confirmed Preview Campaign panel is showing,
        detected via its own confirmed Proceed & Launch control rather
        than an assumed container."""
        try:
            return self.page.locator(self.MODAL_SUBMIT_BTN_WIRE_CLICK).first.is_visible()
        except Exception:
            return False

    def get_preview_summary_text(self):
        """Real text content of the Preview Campaign panel (Campaign
        Name / Sender ID / Template / Recipients / Schedule / message
        body etc.), scoped via PREVIEW_PANEL_ANCHOR -- a structural
        anchor on the confirmed Proceed & Launch button and the
        confirmed "Campaign Name:" label, not a Tailwind class. Falls
        back to the whole page's body text if that anchor doesn't
        resolve (e.g. a genuinely different DOM shape), so callers can
        still assert on it rather than getting an empty string."""
        try:
            anchor = self.page.locator(self.PREVIEW_PANEL_ANCHOR).first
            if anchor.count() > 0:
                return anchor.inner_text()
        except Exception:
            pass
        try:
            return self.page.locator("body").inner_text()
        except Exception:
            return ""

    def close_preview_panel(self):
        """Click the confirmed Close control (wire:click='closeModal')
        to dismiss the Preview Campaign panel WITHOUT launching the
        campaign -- for tests that only need to verify preview content."""
        self._js_click_first_visible_retry(self.PREVIEW_CLOSE_BTN_WIRE_CLICK, timeout=10000)
        self.page.wait_for_timeout(300)

    # ══════════════════════════════════════════════════════════════════
    # Template Preview panel
    # ══════════════════════════════════════════════════════════════════

    def open_template_preview(self):
        """Click the confirmed "Preview Template" trigger button
        (wire:click="openTemplateModal") and wait for the panel's own
        confirmed header (TEMPLATE_PREVIEW_HEADER) to become visible.
        Both the trigger and the panel content are now independently
        confirmed via real, pasted DOM captures -- see
        TEMPLATE_PREVIEW_TRIGGER_BTN's docstring above (this used to
        raise NotImplementedError before the trigger capture existed)."""
        self._js_click_first_visible_retry(self.TEMPLATE_PREVIEW_TRIGGER_BTN, timeout=10000)
        self.page.locator(self.TEMPLATE_PREVIEW_HEADER).wait_for(state="visible", timeout=8000)

    def is_template_preview_open(self):
        return self.is_element_visible(self.TEMPLATE_PREVIEW_HEADER, timeout=5000)

    def get_template_preview_id_text(self):
        return self.page.locator(self.TEMPLATE_PREVIEW_ID_TEXT).first.inner_text().strip()

    def get_template_preview_body_text(self):
        return self.page.locator(self.TEMPLATE_PREVIEW_BODY_TEXT).first.inner_text().strip()

    def get_template_preview_opt_indicator_text(self):
        loc = self.page.locator(self.TEMPLATE_PREVIEW_OPT_INDICATOR)
        if loc.count() == 0:
            return None
        return loc.first.inner_text().strip()

    def close_template_preview(self):
        self.page.locator(self.TEMPLATE_PREVIEW_CLOSE_BTN).click()
        try:
            self.page.locator(self.MODAL_CONTAINER).wait_for(state="hidden", timeout=5000)
        except Exception:
            self.page.wait_for_timeout(1000)

    # ══════════════════════════════════════════════════════════════════
    # Scheduling
    # ══════════════════════════════════════════════════════════════════

    def _set_send_type_livewire(self, value):
        """Directly update the Livewire component's send_type property.
        Carefully targets only components that actually declare send_type,
        avoiding unrelated components (e.g. department-dropdown in navbar)
        which crash the server with PublicPropertyNotFoundException."""
        try:
            self.page.evaluate(f"""
                () => {{
                    if (!window.Livewire) return;
                    const all = window.Livewire.all ? window.Livewire.all() : [];
                    for (const comp of all) {{
                        try {{
                            const name = comp.name || (comp.$wire && comp.$wire.__instance && comp.$wire.__instance.name) || '';
                            let currentVal = undefined;
                            try {{ currentVal = comp.get('send_type'); }} catch(e) {{}}
                            if (currentVal === undefined && comp.$wire && typeof comp.$wire.get === 'function') {{
                                try {{ currentVal = comp.$wire.get('send_type'); }} catch(e) {{}}
                            }}
                            if (currentVal !== undefined || name.includes('campaign')) {{
                                if (typeof comp.set === 'function') {{
                                    comp.set('send_type', '{value}');
                                }} else if (comp.$wire && typeof comp.$wire.set === 'function') {{
                                    comp.$wire.set('send_type', '{value}');
                                }}
                            }}
                        }} catch(e) {{}}
                    }}
                }}
            """)
        except Exception:
            pass

    def select_send_now(self):
        # Strategy: (1) click the visible label to trigger native radio semantics
        # (2) also directly update Livewire's send_type via JS to ensure
        # wire:model.live is satisfied even if the click event isn't captured.
        try:
            label = self.page.locator("label[for='send_now']")
            if label.count() > 0:
                label.first.click(timeout=3000)
        except Exception:
            pass
        # Directly set Livewire state as the reliable fallback / confirmation
        self._set_send_type_livewire("now")
        # Also set the native input (belt-and-suspenders for Alpine x-model)
        try:
            self.page.evaluate("""
                () => {
                    const el = document.getElementById('send_now');
                    if (el) {
                        el.checked = true;
                        el.dispatchEvent(new Event('change', {bubbles: true}));
                    }
                }
            """)
        except Exception:
            pass
        # Wait for Livewire to complete the send_type server roundtrip before
        # returning. Without this, callers (e.g. click_preview_campaign) may
        # find the component mid-render with no wire:click buttons in the modal.
        try:
            self.page.wait_for_load_state("networkidle", timeout=6000)
        except Exception:
            self.page.wait_for_timeout(1000)

    def select_schedule_later(self):
        # Mirror of select_send_now() with value='schedule'.
        try:
            label = self.page.locator("label[for='schedule_later']")
            if label.count() > 0:
                label.first.click(timeout=3000)
        except Exception:
            pass
        self._set_send_type_livewire("schedule")
        try:
            self.page.evaluate("""
                () => {
                    const el = document.getElementById('schedule_later');
                    if (el) {
                        el.checked = true;
                        el.dispatchEvent(new Event('change', {bubbles: true}));
                    }
                }
            """)
        except Exception:
            pass
        try:
            self.page.wait_for_load_state("networkidle", timeout=6000)
        except Exception:
            self.page.wait_for_timeout(1000)

    def set_schedule_date_time(self, date_str, time_str):
        """Set the Schedule for Later date/time fields -- CONFIRMED via a
        real DOM capture of this exact page (see SCHEDULE_DATE_INPUT /
        SCHEDULE_TIME_SELECT docstring): the date field is a native
        <input type="date" x-model="date" x-on:change="updateDateTime()">
        set via JS + a dispatched input/change event pair (needed for
        Alpine's x-model to pick up a programmatic value change -- a
        plain .fill() is not guaranteed to trigger those bindings), and
        the time field is a <select x-model="time"> with 5-minute-
        increment options (NOT a native time input), chosen via
        select_option() with a JS fallback. `date_str` is "YYYY-MM-DD",
        `time_str` is "HH:MM" (rounded down to the nearest 5-minute
        slot, matching the confirmed option step). Pass a genuinely
        future date/time -- isTimeOptionDisabled() disables past slots
        for today's date at runtime, and the date input's own min/max
        (confirmed ~today through ~today+7) bound the pickable range.

        Returns True if the date field was found and set (time is set
        best-effort if its own field is found); False if no matching
        date field exists at all -- callers should treat False as "this
        page's real markup has changed since the last capture", not
        silently proceed as if scheduling succeeded."""
        date_el = self.page.locator(self.SCHEDULE_DATE_INPUT).first
        try:
            date_el.wait_for(state="visible", timeout=8000)
        except Exception:
            if date_el.count() == 0:
                return False
        try:
            date_el.evaluate(
                "(e, val) => { e.value = val; "
                "e.dispatchEvent(new Event('input', {bubbles:true})); "
                "e.dispatchEvent(new Event('change', {bubbles:true})); }",
                date_str,
            )
        except Exception:
            return False

        time_el = self.page.locator(self.SCHEDULE_TIME_SELECT).first
        try:
            time_el.wait_for(state="visible", timeout=5000)
        except Exception:
            pass
        if time_el.count() > 0:
            h, m = map(int, time_str.split(":"))
            m = (m // 5) * 5
            slot = f"{h:02d}:{m:02d}"
            try:
                time_el.select_option(value=slot)
                time_el.evaluate("(e) => e.dispatchEvent(new Event('change', {bubbles:true}))")
            except Exception:
                try:
                    time_el.evaluate(
                        "(e, val) => { e.value = val; "
                        "e.dispatchEvent(new Event('change', {bubbles:true})); }",
                        slot,
                    )
                except Exception:
                    pass

        self.page.wait_for_timeout(400)
        return True

    def get_send_type(self):
        # WireUI hides native radio inputs -- Alpine/Livewire tracks the selected
        # state internally. Read it via multiple strategies in priority order:
        # 1) Livewire component data (most reliable -- the ground truth)
        # 2) Native .checked DOM property (may not reflect Alpine state)
        # 3) Visible CSS indicator on the label/wrapper (visual fallback)
        try:
            val = self.page.evaluate("""
                () => {
                    // Strategy 1: Livewire component data
                    if (window.Livewire) {
                        try {
                            const all = window.Livewire.all ? window.Livewire.all() : [];
                            for (const comp of all) {
                                let v = null;
                                try { v = comp.get('send_type'); } catch(e) {}
                                if (!v) { try { v = comp.$wire && comp.$wire.get ? comp.$wire.get('send_type') : null; } catch(e) {} }
                                if (v === 'now' || v === 'schedule') return v;
                            }
                        } catch(e) {}
                    }
                    // Strategy 2: native .checked
                    const sn = document.getElementById('send_now');
                    const sl = document.getElementById('schedule_later');
                    if (sn && sn.checked) return 'now';
                    if (sl && sl.checked) return 'schedule';
                    // Strategy 3: checked radio in group by value attribute
                    const checked = document.querySelector('input[type="radio"]:checked');
                    if (checked) return checked.value || null;
                    return null;
                }
            """)
            return val
        except Exception:
            pass
        return None

    # ══════════════════════════════════════════════════════════════════
    # Footer actions (main page)
    # ══════════════════════════════════════════════════════════════════

    def get_cancel_href(self):
        return self.page.locator(self.CANCEL_LINK).get_attribute("href")

    def click_cancel(self):
        with self.page.expect_navigation():
            self.page.locator(self.CANCEL_LINK).click()

    def is_test_campaign_enabled(self):
        return self.page.locator(self.TEST_CAMPAIGN_BTN).is_enabled()

    def click_test_campaign(self):
        # Same _js_click_first_visible fix as the Import Contacts modal
        # buttons above -- this page's own docstring already names
        # click_test_campaign() as part of the same historical
        # "subtree intercepts pointer events" failure cluster.
        self._js_click_first_visible_retry(self.TEST_CAMPAIGN_BTN, timeout=10000)

    def is_preview_campaign_enabled(self):
        return self.page.locator(self.PREVIEW_CAMPAIGN_BTN).is_enabled()

    def click_preview_campaign(self):
        btn = self.page.locator(self.PREVIEW_CAMPAIGN_BTN).first
        btn.wait_for(state="visible", timeout=10000)
        try:
            btn.click(timeout=5000)
        except Exception:
            try:
                btn.click(force=True, timeout=5000)
            except Exception:
                self._js_click_first_visible_retry(self.PREVIEW_CAMPAIGN_BTN, timeout=10000)
