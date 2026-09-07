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
    IMPORT_CONTACTS_STATUS = "xpath=//p[contains(.,'No contacts imported') or contains(.,'contacts imported')]"

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
    MODAL_CP_HELPER_TEXT = "xpath=//p[contains(.,'Enter up to 50,000 contacts')]"
    MODAL_FU_FILE_INPUT = "#dropzone-file"
    MODAL_FU_DOWNLOAD_SAMPLE_BTN = "button[wire\\:click=\"export('csv')\"]"
    MODAL_FU_HELPER_TEXT = "xpath=//p[contains(.,'Upload CSV file')]"
    MODAL_CONTACT_IMPORT_SOURCE_WRAPPER = "[form-wrapper='contactImportSource']"
    MODAL_CT_CONTACTS_WRAPPER = "[form-wrapper='ct_contacts']"
    MODAL_CANCEL_BTN = "button[wire\\:click='handleCancel']"
    MODAL_CONTINUE_BTN = "button[wire\\:click='submit']"

    # Template Preview panel (whatsapp.template.view component,
    # rendered inside the shared #modal-container once a template is
    # selected -- CONFIRMED from a genuine, separately pasted capture
    # of its real, populated content: a "Preview" header, a close
    # button that dispatches closeModal, a "Template ID: <id>" line,
    # a chat-bubble-style rendering of the template body text plus a
    # timestamp, and an optional opt-in/opt-out indicator depending on
    # the template's own settings. The exact control that TRIGGERS
    # opening this panel from the main Create Campaign form was NOT
    # part of that capture (only the panel's own content was), so it
    # is deliberately not guessed here -- see open_template_preview()
    # below and the test suite's TC053 for the resulting documented
    # gap.
    TEMPLATE_PREVIEW_HEADER = "xpath=//h1[normalize-space()='Preview']"
    TEMPLATE_PREVIEW_CLOSE_BTN = "button[wire\\:click=\"$dispatch('closeModal')\"]"
    TEMPLATE_PREVIEW_ID_TEXT = "xpath=//p[contains(.,'Template ID:')]"
    TEMPLATE_PREVIEW_BODY_TEXT = "xpath=//div[contains(@class,'break-words')]//p[contains(@class,'text-left')]"
    TEMPLATE_PREVIEW_TIMESTAMP = "xpath=//div[contains(@class,'break-words')]//p[contains(@class,'text-right')]"
    TEMPLATE_PREVIEW_OPT_INDICATOR = "xpath=//i[contains(@class,'mdi-reply')]"

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

    def click_import_contacts(self):
        self.page.locator(self.IMPORT_CONTACTS_BTN).click()
        self.page.locator(self.MODAL_CONTAINER).wait_for(state="visible", timeout=10000)

    def get_import_contacts_status_text(self):
        return self.page.locator(self.IMPORT_CONTACTS_STATUS).first.inner_text().strip()

    # ══════════════════════════════════════════════════════════════════
    # Import Contacts modal
    # ══════════════════════════════════════════════════════════════════

    def is_import_modal_open(self):
        return self.is_element_visible(self.MODAL_CONTAINER, timeout=5000)

    def switch_import_tab(self, tab_name):
        mapping = {
            "copy_paste": self.MODAL_TAB_COPY_PASTE,
            "file_upload": self.MODAL_TAB_FILE_UPLOAD,
            "contact_tags": self.MODAL_TAB_CONTACT_MGMT,
        }
        self.page.locator(mapping[tab_name]).click()
        self.page.wait_for_timeout(300)

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
        self.page.locator(self.MODAL_DUPLICATE_TOGGLE).click()

    def get_contact_import_source_options(self):
        return self._decoded_options(self.MODAL_CONTACT_IMPORT_SOURCE_WRAPPER)

    def select_contact_import_source(self, option_text):
        self._select_option_by_text(self.MODAL_CONTACT_IMPORT_SOURCE_WRAPPER, option_text)

    def get_selected_contact_import_source_text(self):
        return self._get_selected_display_text(self.MODAL_CONTACT_IMPORT_SOURCE_WRAPPER)

    def get_contact_tags_options(self):
        return self._decoded_options(self.MODAL_CT_CONTACTS_WRAPPER)

    def select_contact_tag(self, option_text):
        self._select_option_by_text(self.MODAL_CT_CONTACTS_WRAPPER, option_text)

    def click_modal_cancel(self):
        self.page.locator(self.MODAL_CANCEL_BTN).click()

    def click_modal_continue(self):
        self.page.locator(self.MODAL_CONTINUE_BTN).click()

    # ══════════════════════════════════════════════════════════════════
    # Template Preview panel
    # ══════════════════════════════════════════════════════════════════

    def open_template_preview(self):
        """NOT IMPLEMENTED: the trigger control for this panel was
        never captured (only the panel's own populated content was --
        see the class docstring / TEMPLATE_PREVIEW_* locators above).
        Raises NotImplementedError rather than guessing a click target,
        per this project's never-fabricate-a-locator rule. Once a
        capture of the real trigger element (e.g. a "Preview" link/icon
        in the Template Configuration section) is available, implement
        this to click it and then wait for TEMPLATE_PREVIEW_HEADER.
        """
        raise NotImplementedError(
            "Template Preview trigger control not yet confirmed from a "
            "live DOM capture -- see open_template_preview() docstring"
        )

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

    # ══════════════════════════════════════════════════════════════════
    # Scheduling
    # ══════════════════════════════════════════════════════════════════

    def select_send_now(self):
        self.page.locator(self.SEND_NOW_RADIO).check(force=True)

    def select_schedule_later(self):
        self.page.locator(self.SCHEDULE_LATER_RADIO).check(force=True)

    def get_send_type(self):
        if self.page.locator(self.SEND_NOW_RADIO).is_checked():
            return "now"
        if self.page.locator(self.SCHEDULE_LATER_RADIO).is_checked():
            return "schedule"
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
        self.page.locator(self.TEST_CAMPAIGN_BTN).click()

    def is_preview_campaign_enabled(self):
        return self.page.locator(self.PREVIEW_CAMPAIGN_BTN).is_enabled()

    def click_preview_campaign(self):
        self.page.locator(self.PREVIEW_CAMPAIGN_BTN).click()
