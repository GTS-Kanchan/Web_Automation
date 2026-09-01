import os
import re
import time

from pages.common.base_page import BasePage


class RcsCampaignCreatePage(BasePage):
    """RCS Campaign Create page object.

    RCS Campaign coverage update (functional-coverage pass): this app is
    built on the same stack across every channel (Laravel Livewire +
    WireUI + Tailwind + SweetAlert2 -- see docs/ARCHITECTURE.md, "SMS is
    the reference channel; RCS, WhatsApp, and Email followed the
    identical pattern"). tests/sms/campaigns/test_campaign_creation.py +
    pages/sms/sms_campaign_page.py is the ALREADY-VALIDATED reference
    implementation for this exact screen shape on SMS (do not modify
    those two files -- they are locked per the project's test-
    independence migration). Everything below that is genuinely new on
    this page (Duplicate Phone Handling, Contact Management search/
    select, template-variable autofill, validation/toast helpers, the
    WireUI combobox fallback for Agent/Template) is ported from that
    confirmed SMS implementation and adapted to RCS's own field names
    (agent instead of sender_id). Where RCS has NO confirmed DOM
    evidence at all (the opt-out "skip validation" checkbox, a
    stand-alone "Test Campaign" feature distinct from Preview+Launch),
    locators are best-effort text/attribute matches and the methods
    return None/False rather than raising, so tests built on them can
    skip with a clear reason instead of asserting against a guess.
    """

    CREATE_URL = "/rcs/campaign/create"
    LIST_URL   = "/rcs/campaign"

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_HEADING = (
        "xpath=//h1[contains(normalize-space(.),'Campaign')] | "
        "//h2[contains(normalize-space(.),'Campaign')] | "
        "//h3[contains(normalize-space(.),'Create')]"
    )

    BREADCRUMB = (
        "xpath=//nav[contains(@class,'breadcrumb') or @aria-label='Breadcrumb' "
        "or @aria-label='breadcrumb'] | "
        "//ol[contains(@class,'breadcrumb')] | "
        "//div[contains(@class,'breadcrumb')]"
    )

    # ── Section headings — best-effort text match (section 1, items 3-6 of
    # the coverage spec). This app's create forms are typically a single
    # Livewire component rendered as stacked <h2>/<h3>/<label> "step"
    # headings rather than distinct routed pages -- confirmed structurally
    # on the SMS reference (STEP 1..4 banners in test_campaign_creation.py
    # map to on-page section headings there). Matched case-insensitively
    # so exact heading-level markup doesn't matter. ──────────────────────
    def _section_heading_locator(self, *phrases):
        conds = " or ".join(
            f"contains(translate(normalize-space(.),"
            f"'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{p.lower()}')"
            for p in phrases
        )
        return f"xpath=//*[self::h1 or self::h2 or self::h3 or self::h4 or self::legend][{conds}]"

    # ── Global WireUI notification toast ────────────────────────────────────
    NOTIFICATION_TITLE = (
        "xpath=//div[@x-data='wireui_notifications']//p[@x-show='notification.title'] | "
        "//*[contains(@class,'wireui') and contains(@class,'notification')] | "
        "//*[@x-data='wireui_notifications']//*[contains(@class,'title')]"
    )
    # Same confirmed WireUI toast container as pages/sms/sms_campaign_page.py
    # (TOAST_NOTIFICATION_TEXT there) -- this component is app-global, not
    # per-channel, so the identical locator applies here.
    TOAST_NOTIFICATION_TEXT = (
        "xpath=//div[@x-data='wireui_notifications']"
        "//p[(@x-show='notification.title' or @x-show='notification.description') "
        "and normalize-space(text())!='']"
    )
    SWAL_TITLE = "#swal2-title"
    SWAL_HTML_CONTAINER = "#swal2-html-container"

    # Generic validation-error styling. 'text-negative' added after live
    # testing confirmed the RCS Campaign create form's actual
    # required-field error markup:
    # <label class="text-sm text-negative-600 mt-2" for="name">The
    # Campaign Name field is required.</label> -- this is WireUI's own
    # error-state color utility, distinct from the Tailwind
    # text-red-*/border-red-* set this locator originally guessed from
    # other pages in this app. Kept the original classes too since they
    # may still apply to non-WireUI-rendered errors elsewhere on this page.
    VALIDATION_ERROR = (
        "xpath=//*["
        "  contains(@class,'text-red') or contains(@class,'invalid-feedback')"
        "  or contains(@class,'error-message') or contains(@class,'text-danger')"
        "  or contains(@class,'border-red') or contains(@class,'has-error')"
        "  or contains(@class,'text-negative')"
        "][normalize-space()][not(ancestor::*[contains(@style,'display: none')])]"
    )

    # ── Form fields — Campaign Name ──────────────────────────────────────────
    CAMPAIGN_NAME_INPUT = (
        "xpath=//input[@id='name'] | "
        "//input[@id='campaign_name'] | "
        "//input[@*[name()='wire:model.defer' and contains(.,'campaign_name')]] | "
        "//input[@*[name()='wire:model' and contains(.,'campaign_name')]] | "
        "//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
        "'abcdefghijklmnopqrstuvwxyz'),'campaign name')]"
    )

    # Confirmed via live testing: the required-field error for Campaign
    # Name is a <label for="name" class="text-sm text-negative-600 mt-2">
    # reading "The Campaign Name field is required." -- matches the
    # input's id='name' above (a <label for="..."> targets that id).
    CAMPAIGN_NAME_REQUIRED_ERROR = (
        "xpath=//label[@for='name' and "
        "contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
        "'abcdefghijklmnopqrstuvwxyz'), 'required')]"
    )

    # ── Form fields — RCS Agent select ──────────────────────────────────────
    # Two candidate mechanisms are supported: a native <select> (the
    # original assumption in this file) AND the WireUI searchable-combobox
    # pattern confirmed for Sender ID/Template on the SMS reference
    # (button trigger -> search input -> div[select-option] list). Which
    # one this page actually uses was never independently confirmed here,
    # so select_agent_by_visible_text()/select_agent_by_index() try the
    # native <select> first and fall back to the combobox rather than
    # assuming either.
    RCS_AGENT_SELECT = (
        "xpath=//select[@id='agent_id'] | "
        "//select[@id='rcs_agent_id'] | "
        "//select[@*[name()='wire:model.live' and contains(.,'rcs_agent_id')]] | "
        "//select[@*[name()='wire:model' and contains(.,'agent')]]"
    )
    DROPDOWN_AGENT = (
        "xpath=//button[.//span[contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'select agent') "
        "or contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'agent')]]"
    )
    AGENT_FIRST_MESSAGE = (
        "xpath=//*[contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
        "'select an agent first') or "
        "contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
        "'select agent first') or "
        "contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
        "'please select an agent')]"
    )

    # ── Form fields — Template select ───────────────────────────────────────
    TEMPLATE_SELECT = (
        "xpath=//select[@id='template_id'] | "
        "//select[@*[name()='wire:model.live' and contains(.,'template_id')]] | "
        "//select[@*[name()='wire:model' and contains(.,'template')]]"
    )
    DROPDOWN_TEMPLATE = (
        "xpath=//button[.//span[contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'select template')]]"
    )
    TEMPLATE_VAR_INPUTS = "xpath=//input[starts-with(@id,'columnMapping.')]"
    TEMPLATE_PREVIEW = (
        "xpath=//*[contains(@class,'template-preview') or contains(@class,'preview-bubble')] | "
        "//*[@id='template_preview'] | "
        "//*[contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'template preview')]"
    )
    NO_TEMPLATES_MESSAGE = (
        "xpath=//*[contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no template') "
        "or contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no templates available')]"
    )

    # ── Form fields — Send Type radios ───────────────────────────────────────
    RADIO_SEND_NOW = (
        "xpath=//input[@id='send_now' or (@type='radio' and @value='now')] | "
        "//input[@type='radio'][1]"
    )

    RADIO_SCHEDULE_LATER = (
        "xpath=//input[@id='schedule_later' or (@type='radio' and @value='schedule')] | "
        "//input[@type='radio'][2]"
    )

    # Labels for the two radios above -- added after live testing showed
    # a JS-forced click directly on RADIO_SEND_NOW/RADIO_SCHEDULE_LATER
    # can silently no-op (TC041/TC042/TC043 all failed to actually
    # register a Send-Type selection before submit). Same "the native
    # input is visually hidden/overlaid and a <label> drives the click"
    # pattern already confirmed for Duplicate Phone Handling
    # (DUPLICATE_LABEL/toggle_duplicate_handling) -- see
    # select_send_now()/select_schedule_later() below.
    SEND_NOW_LABEL = (
        "xpath=//label[@for='send_now'] | "
        "//label[contains(translate(normalize-space(.), "
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'send now')] | "
        "//*[@*[name()='wire:click' or name()='x-on:click'] and "
        "contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'send now')]"
    )
    SCHEDULE_LATER_LABEL = (
        "xpath=//label[@for='schedule_later'] | "
        "//label[contains(translate(normalize-space(.), "
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'schedule')] | "
        "//*[@*[name()='wire:click' or name()='x-on:click'] and "
        "contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'schedule')]"
    )

    # ── Form fields — Scheduled date/time (shown after Schedule Later) ──────
    SCHEDULE_DATETIME_INPUT = (
        "xpath=//input[@id='scheduled_at'] | "
        "//input[@type='datetime-local'] | "
        "//input[@type='date' and @*[name()='x-model' and contains(.,'date')]] | "
        "//input[@*[name()='wire:model.defer' and contains(.,'scheduled_at')]]"
    )

    # ── Contacts section ─────────────────────────────────────────────────────
    IMPORT_CONTACTS_BTN = (
        "xpath=//button[@*[name()='wire:click']='openContactsModal' or contains(normalize-space(.), 'Import Contacts')]"
    )

    CONTACTS_MODAL = (
        "xpath=//div[contains(@class, 'fixed') or @x-show='show']//h3[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'contact')] | "
        "//div[@x-data='modal' or contains(@class, 'modal')]"
    )
    MODAL_TITLE = (
        "xpath=//div[contains(@class,'fixed')]//h1[contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'import contact')] | "
        "//div[contains(@class,'fixed')]//h2[contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'import contact')] | "
        "//div[contains(@class,'fixed')]//h3[contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'import contact')]"
    )
    MODAL_CLOSE_X = (
        # Confirmed via live testing (TC149): the modal's X control is a
        # <button type="button" wire:click="$dispatch('closeModal')"> with
        # an inner X-shaped <svg> and no visible text -- matched directly
        # on wire:click first, with the prior aria-label/first-svg-button
        # guesses kept as fallbacks for other modals in the suite.
        "xpath=//button[@*[name()='wire:click' and contains(.,'closeModal')]] | "
        "//div[contains(@class,'fixed')]//button[@aria-label='Close'] | "
        "//div[contains(@class,'fixed')]//button[.//svg][not(contains(@class,'swal'))][1]"
    )
    MODAL_CANCEL_BTN = (
        "xpath=//div[contains(@class,'fixed') or @x-show='show']"
        "//button[contains(normalize-space(),'Cancel')]"
    )

    MODAL_CP_TEXTAREA = "xpath=//textarea[@*[name()='wire:model']='cp_contacts' or @id='cp_contacts']"

    MODAL_FILE_UPLOAD = (
        "xpath=//input[@type='file' and (@*[name()='wire:model']='contact_file' or @*[name()='wire:model']='fu_contacts')]"
    )
    BTN_DOWNLOAD_SAMPLE = (
        "xpath=//a[contains(.,'Download') and contains(.,'Sample')] | "
        "//button[contains(.,'Download Sample')]"
    )

    # ── Duplicate Phone Handling — best-effort. No confirmed RCS DOM for
    # this control; ported locator STRATEGY (not the literal id) from the
    # already-confirmed SMS reference (#keep_duplicates + its <label
    # for="keep_duplicates">), plus a channel-agnostic role="switch"
    # fallback, so this resolves correctly whichever id RCS actually uses.
    DUPLICATE_CHECKBOX = (
        "#keep_duplicates, input[type='checkbox'][id*='duplicate' i], "
        "input[type='checkbox'][wire\\:model*='duplicate' i]"
    )
    DUPLICATE_LABEL = (
        "xpath=//label[@for='keep_duplicates'] | "
        "//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'duplicate')]"
        "[.//input[@type='checkbox'] or @for]"
    )
    DUPLICATE_SWITCH = (
        "xpath=//button[@role='switch'][ancestor::*[contains(translate(.,"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'duplicate')]] | "
        "//div[@role='switch'][ancestor::*[contains(translate(.,"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'duplicate')]]"
    )

    # ── Opt-out "Send to all numbers (Skip opt-out validation)" — best-
    # effort, no confirmed RCS DOM. Matched purely by the visible copy
    # given in the coverage spec; a real DOM dump of this control (see
    # module docstring) would let this be tightened to a real id/wire:model.
    OPT_OUT_SKIP_CHECKBOX = (
        "input[type='checkbox'][id*='opt_out' i], input[type='checkbox'][id*='optout' i], "
        "input[type='checkbox'][wire\\:model*='skip' i][wire\\:model*='opt' i]"
    )
    OPT_OUT_SKIP_LABEL = (
        "xpath=//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
        "'skip opt-out') or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
        "'send to all numbers')]"
    )

    # ── Contact Management tab (search / select / pagination) — best-
    # effort, generic search-input + checkbox-list pattern already proven
    # for the analogous Tags/Segments picker on SMS (import_from_contact_
    # management() there); RCS's own Contact Management sub-structure was
    # not independently confirmed.
    CONTACT_MGMT_SEARCH = (
        "xpath=//div[contains(@class,'fixed')]//input[@type='search' or "
        "contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
        "'abcdefghijklmnopqrstuvwxyz'),'search')]"
    )
    CONTACT_MGMT_ITEM = (
        "xpath=//label[contains(@class,'checkbox')] | "
        "//li[contains(@class,'option') or contains(@class,'item')] | "
        "//div[contains(@class,'fixed')]//input[@type='checkbox']"
    )
    CONTACT_MGMT_SELECT_ALL = (
        "xpath=//div[contains(@class,'fixed')]//input[@type='checkbox']"
        "[contains(@id,'all') or contains(@wire:model,'all')] | "
        "//div[contains(@class,'fixed')]//label[contains(translate(.,"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'select all')]"
    )
    CONTACT_MGMT_NO_RESULTS = (
        "xpath=//div[contains(@class,'fixed')]//*[contains(translate(.,"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no contact') "
        "or contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no results')]"
    )
    CONTACT_COUNT_TEXT = (
        "xpath=//*[contains(text(),'contact') or contains(text(),'Contact')]"
    )

    # ── Import summary interstitial (confirmed live markup, TC125) ──────────
    # After upload_contact_file() sets the file input, the app shows an
    # "Import Completed" panel with a stats grid (Total Rows / Unique
    # Contacts / conditionally Duplicates / Invalid) and Cancel /
    # "Confirm & Continue" buttons -- the contacts are NOT added to the
    # form until Confirm & Continue (wire:click="confirmImport") is
    # clicked. Confirmed exact markup:
    #   <h3>Import Completed</h3>
    #   <p class="text-xs ...">Total Rows</p><p class="text-2xl ...">1</p>
    #   <p class="text-xs ...">Unique Contacts</p><p class="text-2xl ...">1</p>
    #   <button wire:click="cancelImport">Cancel</button>
    #   <button wire:click="confirmImport">Confirm & Continue</button>
    # A separate, simpler "<N> Contacts Imported" label was also
    # confirmed elsewhere (post-confirmation running count).
    IMPORT_SUMMARY_HEADING = (
        "xpath=//h3[contains(normalize-space(.),'Import Completed')]"
    )
    BTN_CONFIRM_IMPORT = "xpath=//button[@*[name()='wire:click']='confirmImport']"
    BTN_CANCEL_IMPORT_SUMMARY = "xpath=//button[@*[name()='wire:click']='cancelImport']"
    CONTACTS_IMPORTED_LABEL = (
        "xpath=//p[contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'contacts imported')]"
    )

    # ── Test Campaign — best-effort; existence not confirmed on this page.
    BTN_TEST_CAMPAIGN = (
        "xpath=//button[contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'test campaign') "
        "or contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'send test')]"
    )

    # ── Footer actions ────────────────────────────────────────────────────────
    CANCEL_LINK = (
        "xpath=//a[contains(@href,'/rcs/campaign') and "
        "not(contains(@href,'/create')) and "
        "(normalize-space()='Cancel' or contains(normalize-space(),'Cancel'))]"
    )

    SUBMIT_BTN = (
        "xpath=//button[@type='submit'] | "
        "//button[contains(normalize-space(.),'Submit') or "
        "contains(normalize-space(.),'Create') or "
        "contains(normalize-space(.),'Launch') or "
        "contains(normalize-space(.),'Send')]"
    )

    # ── Wait Indicators ───────────────────────────────────────────────────────
    SPINNER = (
        "xpath=//*[@*[name()='wire:loading']] | "
        "//*[contains(@class,'spinner') or contains(@class,'loading')] | "
        "//*[contains(@class,'animate-spin')]"
    )

    # ── "No records" / empty state ────────────────────────────────────────────
    NO_RECORDS_TEXT = (
        "xpath=//*[contains(text(),'No records') or contains(text(),'no records') "
        "or contains(text(),'No data') or contains(text(),'No campaigns') "
        "or contains(text(),'No results') or contains(text(),'Nothing found')]"
    )

    # ── Import confirm buttons (contacts modal) ──────────────────────────────
    IMPORT_CONFIRM_BTN = (
        "xpath=//div[contains(@class,'fixed') or @x-show='show']//button[contains(normalize-space(),'Continue') or contains(normalize-space(),'Import') or contains(normalize-space(),'Save')]"
    )

    # ══════════════════════════════════════════════════════════════════════════
    # Navigation helpers
    # ══════════════════════════════════════════════════════════════════════════

    def navigate(self):
        """Navigate to the RCS Campaign create page."""
        self.open(self.CREATE_URL)
        self.page.wait_for_timeout(2000)
        return self

    def is_create_page(self):
        return "/rcs/campaign/create" in self.get_current_url()

    def is_list_page(self):
        url = self.get_current_url()
        return "/rcs/campaign" in url and "/create" not in url

    def is_form_loaded(self, timeout=12000):
        """Return True if the Campaign Name field is present on the page."""
        return self.is_element_present(self.CAMPAIGN_NAME_INPUT, timeout=timeout)

    def get_page_heading_text(self):
        try:
            el = self.h.wait_for_element_visible(self.PAGE_HEADING)
            return el.inner_text().strip()
        except Exception:
            return ""

    def get_breadcrumb_text(self):
        try:
            el = self.h.wait_for_element_visible(self.BREADCRUMB)
            return " ".join(el.inner_text().split())
        except Exception:
            return ""

    def get_page_title(self):
        return self.page.title()

    def _wait_spinner_gone(self, timeout=15000):
        """Wait for any Livewire loading spinner to disappear."""
        try:
            spinner = self.page.locator(self.SPINNER).first
            spinner.wait_for(state="visible", timeout=2000)
            spinner.wait_for(state="hidden", timeout=timeout)
        except Exception:
            pass

    def has_section_heading(self, *phrases, timeout=5000):
        """True if any heading/legend on the page contains one of *phrases*
        (case-insensitive). Used to verify the Campaign Details / Template
        Configuration / Contacts / Campaign Scheduling section headings
        (coverage spec section 1, items 3-6)."""
        return self.is_element_present(self._section_heading_locator(*phrases), timeout=timeout)

    # ══════════════════════════════════════════════════════════════════════════
    # Campaign Name
    # ══════════════════════════════════════════════════════════════════════════

    def fill_campaign_name(self, value):
        el = self.h.wait_for_element_visible(self.CAMPAIGN_NAME_INPUT)
        el.fill("")
        el.fill(value)
        return self

    def get_campaign_name_value(self):
        try:
            el = self.h.wait_for_element_visible(self.CAMPAIGN_NAME_INPUT)
            return el.input_value() or ""
        except Exception:
            return ""

    def get_default_campaign_name(self):
        """Return whatever value the Campaign Name field is pre-populated
        with immediately after navigating to a fresh create page (spec
        section 1, item 7). Returns "" if the field starts empty (a
        legitimately possible "no default" outcome, not a locator
        failure) -- callers should not treat "" as an error on its own."""
        return self.get_campaign_name_value()

    def clear_campaign_name(self):
        try:
            el = self.h.wait_for_element_visible(self.CAMPAIGN_NAME_INPUT)
            el.fill("")
            el.evaluate("(elm) => elm.dispatchEvent(new Event('input',{bubbles:true}))")
        except Exception:
            pass
        return self

    def get_campaign_name_maxlength(self):
        try:
            el = self.page.locator(self.CAMPAIGN_NAME_INPUT).first
            return el.get_attribute("maxlength")
        except Exception:
            return None

    def is_campaign_name_required(self):
        try:
            el = self.page.locator(self.CAMPAIGN_NAME_INPUT).first
            return el.get_attribute("required") is not None
        except Exception:
            return False

    def is_campaign_name_required_error_shown(self, timeout=5000):
        """Confirmed via live testing -- see CAMPAIGN_NAME_REQUIRED_ERROR's
        docstring for the exact markup."""
        return self.is_element_present(self.CAMPAIGN_NAME_REQUIRED_ERROR, timeout=timeout)

    # ══════════════════════════════════════════════════════════════════════════
    # RCS Agent
    # ══════════════════════════════════════════════════════════════════════════

    def is_agent_select_present(self, timeout=8000):
        return (self.is_element_present(self.RCS_AGENT_SELECT, timeout=timeout)
                or self.is_element_present(self.DROPDOWN_AGENT, timeout=1500))

    def is_agent_first_message_shown(self, timeout=3000):
        """'Please select an agent first' pre-selection message (spec
        section 2, item 7) -- best-effort text match, see class docstring."""
        return self.is_element_present(self.AGENT_FIRST_MESSAGE, timeout=timeout)

    def _alpine_container(self, el):
        """Walk up DOM to the nearest ancestor with an x-data attribute.
        Ported from the confirmed SMS WireUI-combobox helper
        (pages/sms/sms_campaign_page.py) -- same Alpine.js convention."""
        try:
            handle = el.evaluate_handle("""
                (start) => {
                    var e = start;
                    while (e.parentElement) {
                        e = e.parentElement;
                        if (e.hasAttribute('x-data')) return e;
                    }
                    return null;
                }
            """)
            return handle.as_element()
        except Exception:
            return None

    def _is_rendered(self, el):
        try:
            return bool(el.evaluate(
                "(e) => { var r = e.getBoundingClientRect(); return r.height > 0 && r.width > 0; }"
            ))
        except Exception:
            return False

    def _wireui_select(self, trigger_locator, value, timeout=15000):
        """WireUI searchable-combobox selection, identical strategy to the
        confirmed SMS implementation's _wireui_select(): open the trigger
        button, type into its scoped search input, click the matching
        div[select-option]. Used as the FALLBACK mechanism for Agent/
        Template selection when the native <select> locator isn't
        present -- see class docstring for why both are supported."""
        btn = self.page.locator(trigger_locator).first
        btn.wait_for(state="visible", timeout=timeout)
        container = self._alpine_container(btn)

        btn.click()
        self.page.wait_for_timeout(500)

        if container is not None:
            inputs = container.query_selector_all("xpath=.//input[@type='search']")
        else:
            inputs = self.page.query_selector_all("xpath=//input[@type='search']")
        rendered_inputs = [i for i in inputs if self._is_rendered(i)]
        search = rendered_inputs[-1] if rendered_inputs else None

        if search:
            search.evaluate(
                "(el) => { el.focus(); el.value=''; "
                "el.dispatchEvent(new Event('input',{bubbles:true})); }"
            )
            search.type(value)
            self.page.wait_for_timeout(1000)

        def _query_opts():
            if container is not None:
                opts = container.query_selector_all("xpath=.//div[@select-option]")
            else:
                opts = self.page.query_selector_all("xpath=//div[@select-option]")
            return [o for o in opts if self._is_rendered(o)]

        rendered = _query_opts()
        matched = [o for o in rendered if value.lower() in (o.inner_text() or "").lower()]
        target = matched[0] if matched else None

        if target is None:
            if search:
                search.evaluate(
                    "(el) => { el.focus(); el.value=''; "
                    "el.dispatchEvent(new Event('input',{bubbles:true})); }"
                )
                self.page.wait_for_timeout(800)
            unfiltered = _query_opts()
            target = unfiltered[0] if unfiltered else None

        if not target:
            raise RuntimeError(f"Option '{value}' not found in WireUI select")

        target.evaluate("(el) => el.scrollIntoView({block:'center'})")
        target.evaluate("(el) => el.click()")
        self.page.wait_for_timeout(400)

    def get_agent_options(self):
        """Return list of non-empty visible option texts from the agent select."""
        try:
            el = self.h.wait_for_element_visible(self.RCS_AGENT_SELECT)
            opts = el.locator("option")
            return [opts.nth(i).inner_text().strip() for i in range(opts.count()) if opts.nth(i).inner_text().strip()]
        except Exception:
            return []

    def select_agent_by_index(self, index: int = 1):
        """Select the agent at the given option index (0 = placeholder).
        Native <select> only -- the WireUI combobox has no stable notion
        of "index N", so callers needing that mechanism should use
        select_agent_by_visible_text() instead."""
        try:
            el = self.h.wait_for_element_visible(self.RCS_AGENT_SELECT)
            el.select_option(index=index)
            self.page.wait_for_timeout(1000)
            self._wait_spinner_gone()
            return True
        except Exception:
            return False

    def select_agent_by_visible_text(self, text: str):
        """Try the native <select> first; fall back to the WireUI
        combobox (DROPDOWN_AGENT) if the select isn't present or the
        option isn't found there -- see class docstring."""
        try:
            el = self.h.wait_for_element_visible(self.RCS_AGENT_SELECT, timeout=4000)
            opts = el.locator("option")
            for i in range(opts.count()):
                option = opts.nth(i)
                option_text = option.inner_text().strip()
                if text.lower() in option_text.lower():
                    val = option.get_attribute("value")
                    el.select_option(value=val)
                    self.page.wait_for_timeout(1000)
                    self._wait_spinner_gone()
                    return True
        except Exception:
            pass
        try:
            self._wireui_select(self.DROPDOWN_AGENT, text)
            self._wait_spinner_gone()
            return True
        except Exception:
            return False

    def get_selected_agent(self):
        try:
            el = self.h.wait_for_element_visible(self.RCS_AGENT_SELECT)
            return el.locator("option:checked").inner_text().strip()
        except Exception:
            return ""

    # ══════════════════════════════════════════════════════════════════════════
    # Template
    # ══════════════════════════════════════════════════════════════════════════

    def is_template_select_present(self, timeout=8000):
        return (self.is_element_present(self.TEMPLATE_SELECT, timeout=timeout)
                or self.is_element_present(self.DROPDOWN_TEMPLATE, timeout=1500))

    def is_no_templates_message_shown(self, timeout=3000):
        return self.is_element_present(self.NO_TEMPLATES_MESSAGE, timeout=timeout)

    def get_template_options(self):
        try:
            el = self.h.wait_for_element_visible(self.TEMPLATE_SELECT)
            opts = el.locator("option")
            return [opts.nth(i).inner_text().strip() for i in range(opts.count()) if opts.nth(i).inner_text().strip()]
        except Exception:
            return []

    def select_template_by_index(self, index: int = 1):
        try:
            el = self.h.wait_for_element_visible(self.TEMPLATE_SELECT)
            el.select_option(index=index)
            self.page.wait_for_timeout(1000)
            self._wait_spinner_gone()
            return True
        except Exception:
            return False

    def select_template_by_visible_text(self, text: str):
        try:
            el = self.h.wait_for_element_visible(self.TEMPLATE_SELECT, timeout=4000)
            opts = el.locator("option")
            for i in range(opts.count()):
                option = opts.nth(i)
                option_text = option.inner_text().strip()
                if text.lower() in option_text.lower():
                    val = option.get_attribute("value")
                    el.select_option(value=val)
                    self.page.wait_for_timeout(1000)
                    self._wait_spinner_gone()
                    return True
        except Exception:
            pass
        try:
            self._wireui_select(self.DROPDOWN_TEMPLATE, text)
            self._wait_spinner_gone()
            return True
        except Exception:
            return False

    def get_selected_template(self):
        try:
            el = self.h.wait_for_element_visible(self.TEMPLATE_SELECT)
            return el.locator("option:checked").inner_text().strip()
        except Exception:
            return ""

    def is_template_preview_shown(self, timeout=5000):
        return self.is_element_present(self.TEMPLATE_PREVIEW, timeout=timeout)

    # ── Template variables — ported from the confirmed SMS implementation
    # (pages/sms/sms_campaign_page.py.fill_all_template_variables()); same
    # 'columnMapping.<var>' id convention, same app-wide component. ──────

    def get_template_variables(self):
        """Returns a plain list of Locators (supports len()/indexing)."""
        return self.page.locator(self.TEMPLATE_VAR_INPUTS).all()

    def fill_template_variable(self, index, value):
        inputs = self.page.locator(self.TEMPLATE_VAR_INPUTS).all()
        if inputs and index < len(inputs):
            inp = inputs[index]
            inp.scroll_into_view_if_needed()
            inp.fill(value)
            inp.evaluate(
                "(el) => { el.dispatchEvent(new Event('input',{bubbles:true})); "
                "el.dispatchEvent(new Event('change',{bubbles:true})); }"
            )

    def fill_all_template_variables(self):
        """Discover every template-variable input and fill each with a
        value derived from its own id/placeholder. Returns the number of
        fields filled. Identical value-generation heuristics to the SMS
        reference so RCS template-variable tests behave the same way."""
        ts = str(int(time.time()))[-5:]
        inputs = self.page.locator(self.TEMPLATE_VAR_INPUTS).all()
        for inp in inputs:
            field_id = inp.get_attribute("id") or ""
            placeholder = inp.get_attribute("placeholder") or ""
            field_name = (field_id.split(".")[-1] if "." in field_id
                          else placeholder or field_id or "var").strip()
            low = field_name.lower()
            if re.search(r'phone|mobile|number|num|mob', low):
                value = f"91987654{ts}"
            elif re.search(r'email', low):
                value = f"test_{ts}@example.com"
            elif re.search(r'otp|pin|code', low):
                value = ts
            elif re.search(r'amount|price|cost|fee', low):
                value = f"{ts[:3]}.00"
            elif re.search(r'date', low):
                value = "2026-01-01"
            elif re.search(r'time', low):
                value = "10:00"
            elif re.search(r'name|customer|user', low):
                value = f"User{ts}"
            else:
                value = f"Auto_{field_name}_{ts}"

            inp.scroll_into_view_if_needed()
            try:
                inp.evaluate("(el) => { el.value = ''; }")
            except Exception:
                pass
            inp.fill(value)
            inp.evaluate(
                "(el) => { el.dispatchEvent(new Event('input',{bubbles:true})); "
                "el.dispatchEvent(new Event('change',{bubbles:true})); }"
            )
            self.page.wait_for_timeout(300)
        return len(inputs)

    # ══════════════════════════════════════════════════════════════════════════
    # Send Type radios
    # ══════════════════════════════════════════════════════════════════════════

    def is_send_now_radio_present(self, timeout=5000):
        return self.is_element_present(self.RADIO_SEND_NOW, timeout=timeout)

    def is_schedule_later_radio_present(self, timeout=5000):
        return self.is_element_present(self.RADIO_SCHEDULE_LATER, timeout=timeout)

    def select_send_now(self):
        """Label-click first (see SEND_NOW_LABEL's docstring: the native
        radio can be visually hidden/overlaid, so a JS-forced click
        directly on it can silently no-op instead of raising -- this was
        confirmed live as the root cause of TC041/TC042/TC043 all
        failing to actually register a Send-Type selection before
        submit). Falls back to the direct radio click, then verifies via
        is_send_now_selected() before returning so callers get an
        honest True/False rather than "the click didn't raise"."""
        try:
            lbl = self.page.locator(self.SEND_NOW_LABEL).first
            lbl.wait_for(state="attached", timeout=3000)
            lbl.scroll_into_view_if_needed()
            lbl.click()
            self.page.wait_for_timeout(500)
            if self.is_send_now_selected():
                return True
        except Exception:
            pass
        try:
            self._js_click(self.RADIO_SEND_NOW)
            self.page.wait_for_timeout(500)
        except Exception:
            pass
        return self.is_send_now_selected()

    def select_schedule_later(self):
        """Same label-first-then-verify strategy as select_send_now()."""
        try:
            lbl = self.page.locator(self.SCHEDULE_LATER_LABEL).first
            lbl.wait_for(state="attached", timeout=3000)
            lbl.scroll_into_view_if_needed()
            lbl.click()
            self.page.wait_for_timeout(500)
            self._wait_spinner_gone()
            if self.is_schedule_later_selected():
                return True
        except Exception:
            pass
        try:
            self._js_click(self.RADIO_SCHEDULE_LATER)
            self.page.wait_for_timeout(500)
            self._wait_spinner_gone()
        except Exception:
            pass
        return self.is_schedule_later_selected()

    def is_send_now_selected(self):
        try:
            el = self.page.locator(self.RADIO_SEND_NOW).first
            return el.is_checked()
        except Exception:
            return False

    def is_schedule_later_selected(self):
        try:
            try:
                if self.page.locator(self.SCHEDULE_DATETIME_INPUT).first.is_visible():
                    return True
            except Exception:
                pass
            el = self.page.locator(self.RADIO_SCHEDULE_LATER).first
            return el.is_checked() or el.get_attribute("checked") == "true"
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════════════
    # Schedule date/time input
    # ══════════════════════════════════════════════════════════════════════════

    def is_schedule_datetime_visible(self, timeout=5000):
        try:
            self.page.locator(self.SCHEDULE_DATETIME_INPUT).first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def fill_schedule_datetime(self, value: str):
        """
        Set the datetime input value (format: YYYY-MM-DDTHH:MM).
        Handles both single datetime-local and separate date/time inputs.
        Timeout raised from 8s to 12s after live testing (TC042) showed
        an 8s wait sometimes wasn't enough for the Scheduling section to
        finish rendering after Contacts were imported and Send Type
        selected -- same staging-environment latency theme as
        ensure_agent_and_template_selected()'s widened timeouts.
        """
        try:
            el = self.page.locator(self.SCHEDULE_DATETIME_INPUT).first
            el.wait_for(state="visible", timeout=12000)

            is_date_only = el.get_attribute("type") == "date"
            if is_date_only and "T" in value:
                date_part, time_part = value.split("T")

                el.evaluate(
                    "(elm, v) => { elm.value = v; "
                    "elm.dispatchEvent(new Event('input',{bubbles:true})); "
                    "elm.dispatchEvent(new Event('change',{bubbles:true})); }",
                    date_part
                )

                time_select_xpath = "xpath=//select[@*[name()='x-model' and contains(.,'time')]]"
                time_el = self.page.locator(time_select_xpath).first
                time_el.evaluate(
                    "(elm, v) => { elm.value = v; "
                    "elm.dispatchEvent(new Event('input',{bubbles:true})); "
                    "elm.dispatchEvent(new Event('change',{bubbles:true})); }",
                    time_part
                )
            else:
                el.evaluate(
                    "(elm, v) => { elm.value = v; "
                    "elm.dispatchEvent(new Event('input',{bubbles:true})); "
                    "elm.dispatchEvent(new Event('change',{bubbles:true})); }",
                    value
                )
            self.page.wait_for_timeout(300)
            return True
        except Exception as e:
            print(f"Error in fill_schedule_datetime: {e}")
            return False

    def get_schedule_datetime_value(self):
        """Reads via input_value() (the live DOM property), not
        get_attribute("value") (the static HTML attribute) -- confirmed
        via live testing as a real bug: fill_schedule_datetime() sets
        the value via JS (elm.value = v), which updates the DOM
        property but never the HTML attribute, so get_attribute("value")
        always read back "" regardless of what was actually set. This
        was the root cause of TC022/TC139 failing to see a value that
        genuinely was there."""
        try:
            el = self.page.locator(self.SCHEDULE_DATETIME_INPUT).first
            el.wait_for(state="attached", timeout=5000)

            is_date_only = el.get_attribute("type") == "date"
            try:
                date_val = el.input_value() or ""
            except Exception:
                date_val = el.get_attribute("value") or ""

            if is_date_only and date_val:
                try:
                    time_select_xpath = "xpath=//select[@*[name()='x-model' and contains(.,'time')]]"
                    time_el = self.page.locator(time_select_xpath).first
                    try:
                        time_val = time_el.input_value() or ""
                    except Exception:
                        time_val = time_el.get_attribute("value") or ""
                    if time_val:
                        return f"{date_val}T{time_val}"
                except Exception:
                    pass
            return date_val
        except Exception:
            return ""

    def get_schedule_datetime_min(self):
        """Returns the 'min' attribute of the schedule datetime input (the
        native HTML5 lower-bound constraint). Confirmed via live testing:
        "past dates get disabled to click" in the picker -- i.e. the app
        restricts past-date selection client-side via this attribute
        rather than via a post-submit error message (the prior skip's
        now-known-wrong assumption)."""
        try:
            el = self.page.locator(self.SCHEDULE_DATETIME_INPUT).first
            el.wait_for(state="attached", timeout=5000)
            return el.get_attribute("min") or ""
        except Exception:
            return ""

    def is_schedule_datetime_valid(self):
        """Uses the browser's native constraint validation (checkValidity())
        to confirm whether the value currently in the schedule datetime
        input satisfies its min/max/type constraints. This is the correct
        way to detect that a past datetime is rejected client-side:
        fill_schedule_datetime() sets .value via JS (elm.value = v), which
        bypasses the picker UI itself but not the native constraint API,
        so checkValidity() still reports False for an out-of-range value."""
        try:
            el = self.page.locator(self.SCHEDULE_DATETIME_INPUT).first
            el.wait_for(state="attached", timeout=5000)
            return bool(el.evaluate("elm => elm.checkValidity()"))
        except Exception:
            return True

    # ══════════════════════════════════════════════════════════════════════════
    # Contacts Modal
    # ══════════════════════════════════════════════════════════════════════════

    def is_import_contacts_btn_present(self, timeout=5000):
        return self.is_element_present(self.IMPORT_CONTACTS_BTN, timeout=timeout)

    def is_import_contacts_btn_disabled(self):
        try:
            el = self.page.locator(self.IMPORT_CONTACTS_BTN).first
            return el.get_attribute("disabled") is not None
        except Exception:
            return True

    def _select_has_real_selection(self, locator):
        """True/False if *locator* is a native <select> with/without a
        real (non-placeholder, index>0) option chosen; None if the
        element isn't present at all (e.g. a WireUI combobox is in use
        instead -- see class docstring)."""
        try:
            el = self.page.locator(locator).first
            if el.count() == 0:
                return None
            return bool(el.evaluate("(e) => e.selectedIndex > 0 && e.value !== ''"))
        except Exception:
            return None

    def _wait_for_select_populated(self, locator, min_options=2, timeout_ms=15000):
        """Poll until *locator* (a native <select>) has more than just a
        placeholder option, or timeout elapses. Agent/Template options
        are commonly loaded via an async Livewire request slightly after
        initial page render -- calling select_option(index=1) before
        that request resolves is a silent no-op (it raises, which
        select_agent_by_index()/select_template_by_index() swallow and
        report as False), which was a real cause of Import-Contacts
        staying disabled downstream even after "selecting" an agent.
        15s (not the original 8s) after live testing against the actual
        staging environment showed the shorter window was sometimes not
        enough, contributing to intermittent (not 100%-reproducible)
        failures opening the Import Contacts modal."""
        try:
            return self.h.wait_until(
                lambda: self.page.locator(locator).locator("option").count() >= min_options,
                timeout_ms=timeout_ms,
                interval_ms=300,
            )
        except Exception:
            return False

    def ensure_agent_and_template_selected(self):
        """Confirmed via live testing: the Import Contacts button/modal
        (and by extension the whole Contacts section) is gated behind
        Agent + Template being selected first -- until then the button
        carries a real `disabled` attribute and a JS-forced click on it
        does not open the modal (browsers do not dispatch click events
        on disabled form controls). Centralizing the "select the first
        available agent, then the first available template, unless one
        is already chosen" prerequisite here -- rather than duplicating
        it across every test that needs the Contacts modal -- means
        click_import_contacts_btn() below (and everything built on it:
        click_tab_copy_paste/click_tab_file_upload/click_tab_contact_mgmt
        via _ensure_contacts_modal_open()) satisfies the prerequisite
        automatically. Never overrides a selection a test already made
        on purpose (e.g. a specific agent/template chosen by name).
        Waits for each <select>'s options to actually be populated
        before selecting index 1 -- see _wait_for_select_populated()'s
        docstring for why that wait matters, not just a presence check."""
        try:
            if self.is_element_present(self.RCS_AGENT_SELECT, timeout=5000):
                if self._select_has_real_selection(self.RCS_AGENT_SELECT) is False:
                    self._wait_for_select_populated(self.RCS_AGENT_SELECT)
                    self.select_agent_by_index(1)
                    self._wait_spinner_gone()
        except Exception:
            pass
        try:
            if self.is_element_present(self.TEMPLATE_SELECT, timeout=5000):
                if self._select_has_real_selection(self.TEMPLATE_SELECT) is False:
                    self._wait_for_select_populated(self.TEMPLATE_SELECT)
                    self.select_template_by_index(1)
                    self._wait_spinner_gone()
        except Exception:
            pass

    def click_import_contacts_btn(self):
        """Bounded retry loop (up to 3 attempts) rather than a single
        settle-and-retry pass: live testing against the real staging
        environment showed the modal opening intermittently rather than
        100% reliably or 100% never -- some tests in the same run opened
        it fine while others (immediately before/after, same code path)
        timed out, which points at real network/Livewire round-trip
        variance rather than a fixed, always-wrong locator. Verifies the
        modal actually opened at the end instead of assuming the click
        worked just because it didn't raise."""
        for attempt in range(3):
            try:
                self.ensure_agent_and_template_selected()
                if self.is_import_contacts_btn_disabled():
                    self.page.wait_for_timeout(1500)
                    self._wait_spinner_gone()
                    continue
                self._js_click(self.IMPORT_CONTACTS_BTN)
                self.page.wait_for_timeout(800)
                self._wait_spinner_gone()
                if (self.is_contacts_modal_present(timeout=3000)
                        or self.is_modal_cp_contacts_textarea_present(timeout=1500)):
                    return True
            except Exception:
                pass
            self.page.wait_for_timeout(1000)
        return False

    def click_import_confirm(self):
        try:
            btn = self.page.locator(self.IMPORT_CONFIRM_BTN).first
            btn.wait_for(state="attached", timeout=15000)
            self.h.wait_until(lambda: btn.is_enabled(), timeout_ms=10000, interval_ms=500)
            self._js_click(self.IMPORT_CONFIRM_BTN)
            self.page.wait_for_timeout(1500)

            confirm_and_continue = "xpath=//div[contains(@class,'fixed') or @x-show='show']//button[contains(normalize-space(),'Confirm')]"
            try:
                btn2 = self.page.locator(confirm_and_continue).first
                btn2.wait_for(state="visible", timeout=4000)
                self._js_click(confirm_and_continue)
                self.page.wait_for_timeout(1000)
            except Exception:
                pass

            try:
                self.page.locator(self.IMPORT_CONFIRM_BTN).first.wait_for(state="hidden", timeout=5000)
            except Exception:
                pass
            return True
        except Exception as e:
            print(f"Could not click import confirm: {e}")
            return False

    def is_contacts_modal_present(self, timeout=5000):
        return self.is_element_present(self.CONTACTS_MODAL, timeout=timeout)

    def is_import_modal_title_correct(self, timeout=5000):
        """Spec section 4, item 4: modal title should read 'Import
        Contacts'. Best-effort -- see class docstring."""
        return self.is_element_present(self.MODAL_TITLE, timeout=timeout)

    def click_modal_close_x(self):
        """Spec section 4, item 5: the X close control (distinct from the
        Cancel button). Rewritten with the same bounded-retry +
        verified-post-condition pattern already used by
        click_import_contacts_btn(): live testing (TC065) showed the X
        control not reliably closing the modal on the first click while
        the modal/Livewire component is still settling, rather than
        pointing to a wrong locator (the same MODAL_CLOSE_X locator
        opens/closes the modal successfully on other runs). Verifies the
        modal actually closed (Copy/Paste textarea gone) instead of just
        trusting that the click call didn't raise."""
        for attempt in range(3):
            try:
                self._js_click(self.MODAL_CLOSE_X, timeout=5000)
                self.page.wait_for_timeout(600)
                self._wait_spinner_gone()
                if not self.is_modal_cp_contacts_textarea_present(timeout=1500):
                    return True
            except Exception:
                pass
            self.page.wait_for_timeout(800)
        return False

    def click_modal_cancel(self):
        try:
            self._js_click(self.MODAL_CANCEL_BTN, timeout=5000)
            self.page.wait_for_timeout(500)
            return True
        except Exception:
            return False

    def is_modal_cp_contacts_textarea_present(self, timeout=5000):
        return self.is_element_present(self.MODAL_CP_TEXTAREA, timeout=timeout)

    def fill_modal_cp_contacts(self, numbers: str):
        """Confirmed via live testing (TC073 failing with the textarea
        never found): Copy/Paste is not reliably the already-active tab
        by the time this is called -- callers throughout this suite open
        the modal via click_import_contacts_btn() and fill straight
        away, without explicitly clicking the Copy/Paste tab first. This
        now does that itself (click_tab_copy_paste() is a no-op-safe,
        idempotent call: it only opens the modal if it isn't already
        open, and only (re)selects the tab), so every existing caller is
        fixed without needing to touch each test."""
        try:
            self.click_tab_copy_paste()
        except Exception:
            pass
        try:
            el = self.h.wait_for_element_visible(self.MODAL_CP_TEXTAREA)
            el.evaluate(
                "(elm, v) => { elm.value = v; "
                "elm.dispatchEvent(new Event('input',{bubbles:true})); "
                "elm.dispatchEvent(new Event('change',{bubbles:true})); }",
                numbers
            )
            self.page.wait_for_timeout(300)
            return True
        except Exception:
            return False

    def upload_contact_file(self, filepath: str):
        try:
            try:
                tab_xpath = (
                    "xpath=//*[(local-name()='button' or local-name()='a') and "
                    "contains(translate(normalize-space(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'file upload')]"
                )
                tab = self.page.locator(tab_xpath).first
                self._js_click(tab_xpath)
                self.page.wait_for_timeout(1000)
            except Exception as e:
                print(f"DEBUG: Failed to click file upload tab: {e}")

            try:
                el = self.page.locator(self.MODAL_FILE_UPLOAD).first
                el.wait_for(state="attached", timeout=5000)
            except Exception as e:
                with open("modal_dump.html", "w", encoding="utf-8") as f:
                    f.write(self.page.content())
                print("File upload element not found! Saved modal_dump.html")
                raise e

            el.set_input_files(os.path.abspath(filepath))
            self.page.wait_for_timeout(2000)

            try:
                self.page.locator(
                    "xpath=//div[@*[name()='wire:loading'] and @*[name()='wire:target']='fu_contacts']"
                ).first.wait_for(state="hidden", timeout=15000)
            except Exception:
                pass
            return True
        except Exception as e:
            print(f"Error in upload_contact_file: {e}")
            return False

    def click_download_sample(self):
        try:
            btn = self.page.locator(self.BTN_DOWNLOAD_SAMPLE).first
            btn.wait_for(state="visible", timeout=5000)
            btn.click()
            self.page.wait_for_timeout(2000)
            return True
        except Exception:
            return False

    def get_import_error(self):
        """Spec sections 5/7/9: a single-shot read of the inline
        validation-error styling near the import modal. Prefer
        wait_for_validation_error_or_toast() below when the error may
        arrive slightly after a fixed-timeout window (Livewire round
        trip, or a toast that auto-dismisses)."""
        if self.is_element_present(self.VALIDATION_ERROR, timeout=5000):
            return self.page.locator(self.VALIDATION_ERROR).first.inner_text()
        return None

    def get_validation_errors(self):
        els = self.page.locator(self.VALIDATION_ERROR)
        texts = [t.strip() for t in els.all_inner_texts()]
        return [t for t in texts if t]

    def get_toast_error(self):
        """Checks the confirmed WireUI toast container, then SweetAlert2's
        title/html-container -- same mechanisms already confirmed
        elsewhere in this project (sms_blocked_numbers_page.py,
        sms_campaign_page.py). Single-shot; see
        wait_for_validation_error_or_toast() for the polling version."""
        for locator in (self.TOAST_NOTIFICATION_TEXT, self.SWAL_TITLE, self.SWAL_HTML_CONTAINER):
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

    def wait_for_validation_error_or_toast(self, timeout_s=6):
        """Poll get_validation_errors() and get_toast_error() together for
        up to timeout_s -- avoids the single-check race documented on the
        SMS reference (a Livewire round trip or a toast's own auto-
        dismiss can land just outside a fixed-timeout single check)."""
        end_time = time.time() + timeout_s
        errors, toast_err = [], None
        while time.time() < end_time:
            errors = self.get_validation_errors()
            toast_err = self.get_toast_error()
            if errors or toast_err:
                return errors, toast_err
            self.page.wait_for_timeout(300)
        return errors, toast_err

    # ── Duplicate Phone Handling ──────────────────────────────────────────

    def is_duplicate_handling_enabled(self):
        try:
            cb = self.page.locator(self.DUPLICATE_CHECKBOX).first
            return cb.is_checked()
        except Exception:
            try:
                sw = self.page.locator(self.DUPLICATE_SWITCH).first
                if sw.get_attribute("aria-checked") == "true":
                    return True
                return sw.is_checked()
            except Exception:
                return False

    def is_duplicate_handling_control_present(self, timeout=5000):
        return (self.is_element_present(self.DUPLICATE_CHECKBOX, timeout=timeout)
                or self.is_element_present(self.DUPLICATE_LABEL, timeout=1500)
                or self.is_element_present(self.DUPLICATE_SWITCH, timeout=1500))

    def toggle_duplicate_handling(self):
        """Label-click first (the confirmed SMS mechanism: a hidden
        checkbox driven by its <label>), JS-click on the checkbox itself
        as fallback, role=switch as last resort."""
        try:
            lbl = self.page.locator(self.DUPLICATE_LABEL).first
            lbl.wait_for(state="attached", timeout=3000)
            lbl.scroll_into_view_if_needed()
            lbl.click()
            self.page.wait_for_timeout(300)
            return
        except Exception:
            pass
        try:
            cb = self.page.locator(self.DUPLICATE_CHECKBOX).first
            cb.evaluate("(el) => el.click()")
            self.page.wait_for_timeout(300)
            return
        except Exception:
            pass
        try:
            sw = self.page.locator(self.DUPLICATE_SWITCH).first
            sw.scroll_into_view_if_needed()
            sw.click()
            self.page.wait_for_timeout(300)
        except Exception:
            pass

    # ── Opt-out "Send to all numbers (Skip opt-out validation)" ──────────

    def is_opt_out_skip_control_present(self, timeout=5000):
        return (self.is_element_present(self.OPT_OUT_SKIP_CHECKBOX, timeout=timeout)
                or self.is_element_present(self.OPT_OUT_SKIP_LABEL, timeout=1500))

    def is_opt_out_skip_enabled(self):
        try:
            cb = self.page.locator(self.OPT_OUT_SKIP_CHECKBOX).first
            return cb.is_checked()
        except Exception:
            return False

    def toggle_opt_out_skip(self):
        try:
            lbl = self.page.locator(self.OPT_OUT_SKIP_LABEL).first
            lbl.wait_for(state="attached", timeout=3000)
            lbl.scroll_into_view_if_needed()
            lbl.click()
            self.page.wait_for_timeout(300)
            return True
        except Exception:
            pass
        try:
            cb = self.page.locator(self.OPT_OUT_SKIP_CHECKBOX).first
            cb.evaluate("(el) => el.click()")
            self.page.wait_for_timeout(300)
            return True
        except Exception:
            return False

    # ── Contact count ──────────────────────────────────────────────────────

    def is_import_summary_present(self, timeout=5000):
        """True if the confirmed 'Import Completed' stats panel (shown
        after upload_contact_file(), before Confirm & Continue is
        clicked) is visible."""
        return self.is_element_present(self.IMPORT_SUMMARY_HEADING, timeout=timeout)

    def get_import_summary_stat(self, label: str):
        """Read a stat value from the confirmed 'Import Completed' panel
        by its label text ('Total Rows', 'Unique Contacts', etc.) --
        the label and its bold numeric value are sibling <p> elements
        inside the same stat-card <div>. Returns None if the label or a
        numeric value isn't found (e.g. a conditional stat like
        Duplicates/Invalid that's only rendered when non-zero)."""
        try:
            card_xpath = (
                f"xpath=//div[.//p[contains(translate(normalize-space(.),"
                f"'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
                f"'{label.lower()}')]]"
            )
            cards = self.page.locator(card_xpath)
            for i in range(cards.count()):
                card = cards.nth(i)
                value_els = card.locator("xpath=.//p[contains(@class,'text-2xl')]")
                if value_els.count() > 0:
                    text = value_els.first.inner_text().strip()
                    m = re.search(r'\d+', text)
                    if m:
                        return int(m.group())
        except Exception:
            pass
        return None

    def get_import_total_rows_count(self):
        return self.get_import_summary_stat("Total Rows")

    def get_import_unique_contacts_count(self):
        return self.get_import_summary_stat("Unique Contacts")

    def click_confirm_import(self):
        """Clicks the 'Confirm & Continue' button (wire:click=
        'confirmImport') on the Import Completed summary panel,
        finalizing the import into the create form."""
        try:
            self._js_click(self.BTN_CONFIRM_IMPORT, timeout=5000)
            self.page.wait_for_timeout(1000)
            self._wait_spinner_gone()
            return True
        except Exception:
            return False

    def get_contacts_imported_count(self):
        """Parses the confirmed post-confirmation '<N> Contacts Imported'
        label. Returns None if not present (e.g. before Confirm &
        Continue is clicked, or on flows that don't show this label)."""
        try:
            els = self.page.locator(self.CONTACTS_IMPORTED_LABEL)
            for i in range(els.count()):
                text = els.nth(i).inner_text()
                m = re.search(r'\d+', text)
                if m:
                    return int(m.group())
        except Exception:
            pass
        return None

    def get_contact_count(self):
        """Parses the current contact count. Prefers the confirmed
        'Import Completed' summary panel's 'Unique Contacts' stat (see
        get_import_unique_contacts_count()) when it's on screen -- the
        precise, confirmed signal for a just-completed file upload --
        then the confirmed post-confirm '<N> Contacts Imported' label,
        falling back to the original best-effort '<N> contact(s)' text
        scan for flows (e.g. copy/paste) where neither confirmed panel
        is shown."""
        if self.is_import_summary_present(timeout=1500):
            count = self.get_import_unique_contacts_count()
            if count is not None:
                return count
        count = self.get_contacts_imported_count()
        if count is not None:
            return count
        try:
            els = self.page.locator(self.CONTACT_COUNT_TEXT)
            for i in range(els.count()):
                text = els.nth(i).inner_text()
                m = re.search(r'\d+', text)
                if m:
                    return int(m.group())
        except Exception:
            pass
        return 0

    # ══════════════════════════════════════════════════════════════════════════
    # Contacts modal tabs — RECONSTRUCTED, not defined in the original
    # Selenium page object even though the corresponding test file
    # (test_rcs_campaign_create_flow.py TC024-TC029) calls click_tab_
    # copy_paste()/is_cp_contacts_textarea_present()/fill_cp_contacts()/
    # get_cp_contacts_value()/click_tab_file_upload()/
    # is_file_upload_input_present()/click_tab_contact_mgmt() — none of
    # which exist on the Selenium RcsCampaignCreatePage, so those tests
    # would have raised AttributeError there too. Reconstructed here using
    # the same generic text-match tab-lookup pattern already proven in
    # upload_contact_file()'s "file upload" tab click, so the suite is at
    # least runnable; tests exercising these skip gracefully (or may fail)
    # if the live modal's actual tab markup differs — never asserted
    # against unconfirmed specifics beyond this best-effort lookup.
    # ══════════════════════════════════════════════════════════════════════════

    TAB_COPY_PASTE = (
        "xpath=//*[(local-name()='button' or local-name()='a') and "
        "contains(translate(normalize-space(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'copy') "
        "and contains(translate(normalize-space(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'paste')]"
    )
    TAB_FILE_UPLOAD = (
        "xpath=//*[(local-name()='button' or local-name()='a') and "
        "contains(translate(normalize-space(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'file upload')]"
    )
    TAB_CONTACT_MGMT = (
        "xpath=//*[(local-name()='button' or local-name()='a') and "
        "contains(translate(normalize-space(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'contact management')]"
    )

    def _ensure_contacts_modal_open(self):
        if not self.is_contacts_modal_present(timeout=1000) and not self.is_modal_cp_contacts_textarea_present(timeout=1000):
            self.click_import_contacts_btn()

    def click_tab_copy_paste(self):
        self._ensure_contacts_modal_open()
        try:
            self._js_click(self.TAB_COPY_PASTE, timeout=5000)
            self.page.wait_for_timeout(500)
        except Exception:
            pass

    def is_copy_paste_tab_default_selected(self, timeout=3000):
        """Spec section 4, item 10: Copy Paste Numbers should be the
        default selected tab. Best-effort: checks aria-selected="true" /
        a common 'active' class on the tab element, falling back to
        "the copy-paste textarea is already visible without clicking any
        tab" as the practical signal that it's the default."""
        try:
            tab = self.page.locator(self.TAB_COPY_PASTE).first
            tab.wait_for(state="attached", timeout=timeout)
            aria = tab.get_attribute("aria-selected")
            if aria is not None:
                return aria == "true"
            cls = tab.get_attribute("class") or ""
            if "active" in cls or "selected" in cls:
                return True
        except Exception:
            pass
        return self.is_modal_cp_contacts_textarea_present(timeout=timeout)

    def is_cp_contacts_textarea_present(self, timeout=5000):
        return self.is_modal_cp_contacts_textarea_present(timeout=timeout)

    def fill_cp_contacts(self, numbers):
        return self.fill_modal_cp_contacts(numbers)

    def get_cp_contacts_value(self):
        try:
            el = self.page.locator(self.MODAL_CP_TEXTAREA).first
            return el.input_value() or ""
        except Exception:
            return ""

    def click_tab_file_upload(self):
        self._ensure_contacts_modal_open()
        try:
            self._js_click(self.TAB_FILE_UPLOAD, timeout=5000)
            self.page.wait_for_timeout(500)
        except Exception:
            pass

    def is_file_upload_input_present(self, timeout=5000):
        return self.is_element_present(self.MODAL_FILE_UPLOAD, timeout=timeout)

    def click_tab_contact_mgmt(self):
        self._ensure_contacts_modal_open()
        try:
            self._js_click(self.TAB_CONTACT_MGMT, timeout=5000)
            self.page.wait_for_timeout(500)
        except Exception:
            pass

    # ── Contact Management — search / select / pagination ────────────────

    def search_contact_management(self, term):
        self.click_tab_contact_mgmt()
        try:
            inp = self.h.wait_for_element_visible(self.CONTACT_MGMT_SEARCH, timeout=5000)
            inp.fill(term)
            inp.evaluate(
                "(el) => { el.dispatchEvent(new Event('input',{bubbles:true})); }"
            )
            self.page.wait_for_timeout(1000)
            return True
        except Exception:
            return False

    def get_contact_management_item_count(self):
        try:
            return self.page.locator(self.CONTACT_MGMT_ITEM).count()
        except Exception:
            return 0

    def is_contact_management_no_results(self, timeout=3000):
        return self.is_element_present(self.CONTACT_MGMT_NO_RESULTS, timeout=timeout)

    def select_contact_management_item(self, index=0):
        try:
            items = self.page.locator(self.CONTACT_MGMT_ITEM)
            item = items.nth(index)
            item.scroll_into_view_if_needed()
            item.evaluate("(el) => el.click()")
            self.page.wait_for_timeout(400)
            return True
        except Exception:
            return False

    def select_all_contact_management_items(self):
        try:
            self._js_click(self.CONTACT_MGMT_SELECT_ALL, timeout=5000)
            self.page.wait_for_timeout(500)
            return True
        except Exception:
            return False

    def import_from_contact_management(self, method="tags"):
        """Import contacts via the Contact Management tab. method: 'tags'
        or 'segments'. Raises RuntimeError if the tab or items are not
        available -- ported strategy from the confirmed SMS
        implementation's import_from_contact_management()."""
        self.click_tab_contact_mgmt()

        method_cap = method.capitalize()
        type_locator = (
            f"xpath=//button[normalize-space()='{method_cap}']"
            f" | //option[contains(.,'{method_cap}')]"
            f" | //label[contains(.,'{method_cap}')]"
            f" | //input[@value='{method.lower()}']"
            f" | //div[contains(@class,'tab')][contains(.,'{method_cap}')]"
        )
        try:
            el = self.page.locator(type_locator).first
            el.wait_for(state="visible", timeout=8000)
            el.evaluate("(e) => e.click()")
            self.page.wait_for_timeout(600)
        except Exception:
            pass

        try:
            item = self.page.locator(self.CONTACT_MGMT_ITEM).first
            item.wait_for(state="visible", timeout=10000)
            item.scroll_into_view_if_needed()
            item.evaluate("(e) => e.click()")
            self.page.wait_for_timeout(500)
        except Exception:
            raise RuntimeError(
                f"Could not find any available item in Contact Management {method} tab"
            )

    # ══════════════════════════════════════════════════════════════════════════
    # Test Campaign — best-effort; existence not confirmed on this page
    # (no reference implementation on SMS either). Returns False rather
    # than raising so callers can skip with a clear reason instead of
    # asserting against a feature that may not exist.
    # ══════════════════════════════════════════════════════════════════════════

    def is_test_campaign_button_present(self, timeout=3000):
        return self.is_element_present(self.BTN_TEST_CAMPAIGN, timeout=timeout)

    def click_test_campaign(self):
        if not self.is_test_campaign_button_present(timeout=3000):
            return False
        try:
            self._js_click(self.BTN_TEST_CAMPAIGN, timeout=5000)
            self.page.wait_for_timeout(1000)
            return True
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════════════
    # Footer actions
    # ══════════════════════════════════════════════════════════════════════════

    def is_cancel_link_present(self, timeout=5000):
        return self.is_element_present(self.CANCEL_LINK, timeout=timeout)

    def click_cancel(self):
        self._js_click(self.CANCEL_LINK, timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_submit_button_present(self, timeout=5000):
        return self.is_element_present(self.SUBMIT_BTN, timeout=timeout)

    def is_submit_button_enabled(self):
        try:
            btn = self.page.locator(self.SUBMIT_BTN).first
            return btn.is_enabled() and btn.get_attribute("disabled") is None
        except Exception:
            return False

    def is_submit_button_disabled_immediately_after_click(self, settle_ms=150):
        """Spec section 13, item 20: the launch button should show a
        loading/disabled state during submission (guards against a
        double-launch from rapid repeated clicks). Reads the disabled
        state shortly AFTER click_submit() has already been called by the
        caller -- this method does not click, it only observes."""
        try:
            self.page.wait_for_timeout(settle_ms)
            btn = self.page.locator(self.SUBMIT_BTN).first
            return btn.get_attribute("disabled") is not None
        except Exception:
            return False

    def click_submit(self):
        self._js_click(self.SUBMIT_BTN, timeout=10000)
        self.page.wait_for_timeout(2000)

    def confirm_launch(self, timeout=5000):
        """Handle the sweet alert confirmation that appears after click_submit()."""
        try:
            proceed_btn = "xpath=//button[contains(normalize-space(),'Proceed') or contains(@class,'swal2-confirm')]"
            self.h.wait_for_element_clickable(proceed_btn, timeout=timeout)
            self._js_click(proceed_btn)
            self.page.wait_for_timeout(1000)
            return True
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════════════
    # Toast / success feedback
    # ══════════════════════════════════════════════════════════════════════════

    def is_success_toast_shown(self, timeout=8000):
        return self.is_element_present(self.NOTIFICATION_TITLE, timeout=timeout)

    # ══════════════════════════════════════════════════════════════════════════
    # Performance
    # ══════════════════════════════════════════════════════════════════════════

    def get_page_load_time_ms(self):
        try:
            return self.page.evaluate(
                "() => window.performance.timing.loadEventEnd - "
                "window.performance.timing.navigationStart"
            )
        except Exception:
            return None
