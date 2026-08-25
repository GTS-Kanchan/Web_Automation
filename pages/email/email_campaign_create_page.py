import os
import time

from pages.common.base_page import BasePage
from utils.config import Config, DOWNLOAD_DIR


class EmailCampaignCreatePage(BasePage):

    CREATE_URL = "/campaigns/email/create"
    LIST_URL = "/campaigns/email"

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h2[contains(normalize-space(),'Email Campaign')]"
    BREADCRUMB_CURRENT = (
        "xpath=//nav[@aria-label='Breadcrumb']//span[contains(normalize-space(.),'Email Campaign')]"
    )

    # ── Step indicator (Name / Template / Contacts) ──────────────────────────
    # Uses 'ancestor-or-self' so minor nesting variations in the live DOM
    # don't break the locator.
    STEP_CIRCLE_XPATH = (
        "xpath=//span[normalize-space()='{label}']/ancestor::div[1]//*[contains(@class,'rounded-full')]"
    )

    # ── Campaign details fields ──────────────────────────────────────────────
    CAMPAIGN_NAME_INPUT = "#name"
    EMAIL_SERVICE_SELECT = "#email_service"
    TEMPLATE_SELECT = "#template_id"
    SUBJECT_INPUT = "#subject"
    REPLY_TO_INPUT = "#reply_to_email"
    CC_EMAIL_TEXTAREA = "#cc_email"
    BCC_EMAIL_TEXTAREA = "#bcc_email"

    # Option value/text for each native select pulled from Config / .env
    EMAIL_SERVICE_OPTION_VALUE = Config.EMAIL_SERVICE
    TEMPLATE_OPTION_VALUE = Config.EMAIL_TEMPLATE_NAME

    # ── Contacts card ─────────────────────────────────────────────────────────
    CONTACTS_EMPTY_TEXT = "xpath=//p[normalize-space()='No emails imported']"
    IMPORT_CONTACTS_BTN = "xpath=//button[@*[name()='wire:click']='openContactsModal']"

    # ── Attachments ──────────────────────────────────────────────────────────
    ATTACHMENT_FILE_INPUT = "input[type='file'][wire\\:model='attachments']"
    ATTACHMENT_MAX_SIZE_TEXT = "xpath=//p[contains(normalize-space(.),'Max file size: 5MB')]"

    # ── Scheduling ───────────────────────────────────────────────────────────
    SEND_NOW_RADIO = "#send_now"
    SCHEDULE_LATER_RADIO = "#schedule_later"

    # ── Footer actions ───────────────────────────────────────────────────────
    CANCEL_LINK = (
        "xpath=//a[contains(@href,'/campaigns/email') and not(contains(@href,'/create')) "
        "and contains(normalize-space(.),'Cancel')]"
    )
    TEST_CAMPAIGN_BTN = "xpath=//button[@*[name()='wire:click']='openTestCampaignModal']"
    PREVIEW_CAMPAIGN_BTN = "xpath=//button[@*[name()='wire:click']='openPreviewModal']"

    # ── Import Contacts modal (shared global #modal-container) ──────────────
    MODAL_CONTAINER = "#modal-container"
    IMPORT_MODAL_TITLE = "xpath=//h2[normalize-space()='Import Contacts']"
    IMPORT_MODAL_CLOSE_X_BTN = (
        "xpath=//h2[normalize-space()='Import Contacts']/following-sibling::button"
        "[@*[name()='wire:click']='handleCancel']"
    )
    IMPORT_MODAL_FOOTER_CANCEL_BTN = (
        "xpath=//button[@*[name()='wire:click']='handleCancel' and contains(normalize-space(.),'Cancel')]"
    )
    IMPORT_MODAL_CONTINUE_BTN = (
        "xpath=//button[@*[name()='wire:click']='submit' and contains(normalize-space(.),'Continue')]"
    )

    # ── Import modal tabs ─────────────────────────────────────────────────────
    TAB_COPY_PASTE = "xpath=//a[contains(normalize-space(.),'Copy Paste Emails')]"
    TAB_FILE_UPLOAD = "xpath=//a[contains(normalize-space(.),'File Upload')]"
    TAB_CONTACT_MANAGEMENT = "xpath=//a[contains(normalize-space(.),'Contact Management')]"

    # ── Duplicate Email Handling toggle ───────────────────────────────────────
    KEEP_DUPLICATES_CHECKBOX = "#keep_duplicates"
    DUPLICATE_HANDLING_BADGE = (
        "xpath=//label[normalize-space()='Duplicate Email Handling']/following-sibling::span[1]"
    )

    # ── Copy Paste tab ────────────────────────────────────────────────────────
    CP_CONTACTS_TEXTAREA = "#cp_contacts"
    CP_HELPER_TEXT = "xpath=//p[contains(normalize-space(.),'Enter up to 50,000 email addresses')]"

    # ── File Upload tab ───────────────────────────────────────────────────────
    FILE_UPLOAD_INPUT = "#dropzone-file"
    DOWNLOAD_SAMPLE_CSV_BTN = "xpath=//button[@*[name()='wire:click']=\"export('csv')\"]"

    # ── Contact Management tab ───────────────────────────────────────────────
    CONTACT_IMPORT_SOURCE_SELECT = "#contactImportSource"
    # data-name attribute was in the original DOM dump but may not be
    # present on all builds — locate by for='ct_contacts' alone.
    CT_CONTACTS_CONTAINER = "label[for='ct_contacts']"
    CT_CONTACTS_SEARCH_INPUT = "input#search[type='search']"

    # ── Navigation / page state ─────────────────────────────────────────────

    def navigate(self):
        """Navigate to the create-campaign form and wait until the page is
        genuinely loaded: URL must contain '/create' AND the campaign-name
        input must be present in the DOM."""
        self.open(self.CREATE_URL)
        # Wait for the URL to settle on the create page (guards against
        # mid-navigation redirects, e.g. session expiry -> /login).
        try:
            self.page.wait_for_url("**/campaigns/email/create**", timeout=15000)
        except Exception:
            pass
        # Wait for the campaign-name input to be present — this is the
        # earliest reliable signal that Livewire has mounted.
        try:
            self.page.locator(self.CAMPAIGN_NAME_INPUT).first.wait_for(state="attached", timeout=15000)
        except Exception:
            self.page.wait_for_timeout(3000)  # fallback: give the page 3 s to settle
        return self

    def is_create_page(self):
        url = self.get_current_url()
        return "/campaigns/email/create" in url and "login" not in url.lower()

    def get_page_title_text(self):
        el = self.h.wait_for_element_visible(self.PAGE_TITLE)
        return el.inner_text().strip()

    def _is_visible(self, locator, timeout=5000):
        try:
            loc = self.page.locator(locator)
            for i in range(loc.count()):
                if loc.nth(i).is_visible():
                    return True
            return False
        except Exception:
            return False

    # ── Step indicator ───────────────────────────────────────────────────────

    def get_step_circle_class(self, label):
        """label: 'Name' | 'Template' | 'Contacts'"""
        xpath = self.STEP_CIRCLE_XPATH.format(label=label)
        el = self.h.wait_for_element_visible(xpath)
        return el.get_attribute("class")

    def is_step_indicator_visible(self):
        return (self._is_visible(self.STEP_CIRCLE_XPATH.format(label="Name"))
                and self._is_visible(self.STEP_CIRCLE_XPATH.format(label="Template"))
                and self._is_visible(self.STEP_CIRCLE_XPATH.format(label="Contacts")))

    # ── Campaign details fields ──────────────────────────────────────────────

    def get_campaign_name_value(self):
        return self.h.wait_for_element_visible(self.CAMPAIGN_NAME_INPUT).get_attribute("value")

    def set_campaign_name(self, value):
        self.h.clear_and_type(self.CAMPAIGN_NAME_INPUT, value)
        self.page.wait_for_timeout(300)

    def select_email_service(self, value=None):
        """Selects by visible text (the .env value is the human-readable
        service name, not the internal numeric id stored in the value attr)."""
        text = value or self.EMAIL_SERVICE_OPTION_VALUE
        self.h.wait_for_element_visible(self.EMAIL_SERVICE_SELECT)
        self.h.select_option(self.EMAIL_SERVICE_SELECT, label=text)
        self.page.wait_for_timeout(1200)

    def get_email_service_value(self):
        """Returns the visible text of the selected option (matches .env)."""
        el = self.h.wait_for_element_visible(self.EMAIL_SERVICE_SELECT)
        return el.locator("option:checked").inner_text().strip()

    def select_template(self, value=None):
        """Selects by visible text (the .env value is the template name,
        not the UUID stored in the value attr)."""
        text = value or self.TEMPLATE_OPTION_VALUE
        self.h.wait_for_element_visible(self.TEMPLATE_SELECT)
        self.h.select_option(self.TEMPLATE_SELECT, label=text)
        self.page.wait_for_timeout(1200)

    def get_template_value(self):
        """Returns the visible text of the selected option (matches .env)."""
        el = self.h.wait_for_element_visible(self.TEMPLATE_SELECT)
        return el.locator("option:checked").inner_text().strip()

    def select_service_and_template(self):
        """Selects a real, confirmed Email Service + Template pair — the
        precondition that flips Import/Test Campaign buttons enabled."""
        self.select_email_service()
        self.select_template()

    def set_subject(self, text):
        self.h.clear_and_type(self.SUBJECT_INPUT, text)
        self.page.wait_for_timeout(300)

    def get_subject_value(self):
        return self.h.wait_for_element_visible(self.SUBJECT_INPUT).get_attribute("value")

    def set_reply_to(self, text):
        self.h.clear_and_type(self.REPLY_TO_INPUT, text)
        self.page.wait_for_timeout(300)

    def get_reply_to_value(self):
        return self.h.wait_for_element_visible(self.REPLY_TO_INPUT).get_attribute("value")

    def set_cc_email(self, text):
        self.h.clear_and_type(self.CC_EMAIL_TEXTAREA, text)
        self.page.wait_for_timeout(300)

    def get_cc_email_value(self):
        return self.h.wait_for_element_visible(self.CC_EMAIL_TEXTAREA).get_attribute("value")

    def set_bcc_email(self, text):
        self.h.clear_and_type(self.BCC_EMAIL_TEXTAREA, text)
        self.page.wait_for_timeout(300)

    def get_bcc_email_value(self):
        return self.h.wait_for_element_visible(self.BCC_EMAIL_TEXTAREA).get_attribute("value")

    # ── Contacts card ─────────────────────────────────────────────────────────

    def is_contacts_empty_state_visible(self):
        return self._is_visible(self.CONTACTS_EMPTY_TEXT)

    def is_import_contacts_button_enabled(self):
        el = self.h.wait_for_element_visible(self.IMPORT_CONTACTS_BTN)
        return el.get_attribute("disabled") is None

    def click_import_contacts(self):
        self._js_click(self.IMPORT_CONTACTS_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    # ── Attachments ──────────────────────────────────────────────────────────

    def is_attachment_input_present(self):
        return self.is_element_present(self.ATTACHMENT_FILE_INPUT, timeout=5000)

    def upload_attachment(self, file_path):
        el = self.page.locator(self.ATTACHMENT_FILE_INPUT).first
        el.wait_for(state="attached", timeout=10000)
        # The input is visually hidden (class="hidden") behind a styled
        # <label> — set_input_files() works regardless of CSS visibility,
        # but we defensively unhide it first for parity with the original
        # Selenium behaviour (some stricter driver/browser combos need it
        # visible before send_keys equivalents will register the change).
        el.evaluate(
            "(elm) => { elm.classList.remove('hidden'); elm.style.display = 'block'; }"
        )
        el.set_input_files(file_path)
        self.page.wait_for_timeout(1000)

    # ── Scheduling ───────────────────────────────────────────────────────────

    def select_send_now(self):
        self._js_click(self.SEND_NOW_RADIO, timeout=10000)
        self.page.wait_for_timeout(500)

    def select_schedule_later(self):
        self._js_click(self.SCHEDULE_LATER_RADIO, timeout=10000)
        self.page.wait_for_timeout(500)

    def is_send_now_selected(self):
        return self.h.wait_for_element_visible(self.SEND_NOW_RADIO).is_checked()

    def is_schedule_later_selected(self):
        return self.h.wait_for_element_visible(self.SCHEDULE_LATER_RADIO).is_checked()

    # ── Footer actions ───────────────────────────────────────────────────────

    def click_cancel(self):
        self._js_click(self.CANCEL_LINK, timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_test_campaign_button_enabled(self):
        el = self.h.wait_for_element_visible(self.TEST_CAMPAIGN_BTN)
        return el.get_attribute("disabled") is None

    def click_test_campaign(self):
        self._js_click(self.TEST_CAMPAIGN_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_preview_campaign_button_enabled(self):
        el = self.h.wait_for_element_visible(self.PREVIEW_CAMPAIGN_BTN)
        return el.get_attribute("disabled") is None

    def click_preview_campaign(self):
        self._js_click(self.PREVIEW_CAMPAIGN_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    # ── Import Contacts modal ────────────────────────────────────────────────

    def is_import_modal_open(self):
        return self.is_element_present(self.IMPORT_MODAL_TITLE, timeout=8000)

    def close_import_modal_via_x(self):
        self._js_click(self.IMPORT_MODAL_CLOSE_X_BTN, timeout=10000)
        self.page.wait_for_timeout(1000)

    def close_import_modal_via_footer_cancel(self):
        self._js_click(self.IMPORT_MODAL_FOOTER_CANCEL_BTN, timeout=10000)
        self.page.wait_for_timeout(1000)

    def click_import_modal_continue(self):
        self._js_click(self.IMPORT_MODAL_CONTINUE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    # ── Import modal tabs ─────────────────────────────────────────────────────

    def switch_to_copy_paste_tab(self):
        self._js_click(self.TAB_COPY_PASTE, timeout=10000)
        self.page.wait_for_timeout(500)

    def switch_to_file_upload_tab(self):
        self._js_click(self.TAB_FILE_UPLOAD, timeout=10000)
        self.page.wait_for_timeout(500)

    def switch_to_contact_management_tab(self):
        self._js_click(self.TAB_CONTACT_MANAGEMENT, timeout=10000)
        self.page.wait_for_timeout(500)

    def is_tab_active(self, locator):
        el = self.h.wait_for_element_visible(locator)
        return "active" in (el.get_attribute("class") or "")

    # ── Duplicate Email Handling toggle ───────────────────────────────────────

    def toggle_keep_duplicates(self):
        self._js_click(self.KEEP_DUPLICATES_CHECKBOX, timeout=10000)
        self.page.wait_for_timeout(500)

    def is_keep_duplicates_checked(self):
        return self.h.wait_for_element_visible(self.KEEP_DUPLICATES_CHECKBOX).is_checked()

    def get_duplicate_badge_text(self):
        return self.h.wait_for_element_visible(self.DUPLICATE_HANDLING_BADGE).inner_text().strip()

    # ── Copy Paste tab ────────────────────────────────────────────────────────

    def set_cp_contacts(self, text):
        self.h.clear_and_type(self.CP_CONTACTS_TEXTAREA, text)
        self.page.wait_for_timeout(300)

    def get_cp_contacts_value(self):
        return self.h.wait_for_element_visible(self.CP_CONTACTS_TEXTAREA).get_attribute("value")

    # ── File Upload tab ───────────────────────────────────────────────────────

    def is_file_upload_input_present(self):
        return self.is_element_present(self.FILE_UPLOAD_INPUT, timeout=5000)

    def upload_contacts_file(self, file_path):
        el = self.h.wait_for_element_visible(self.FILE_UPLOAD_INPUT)
        el.set_input_files(file_path)
        self.page.wait_for_timeout(1000)

    def click_download_sample_csv(self):
        self._js_click(self.DOWNLOAD_SAMPLE_CSV_BTN, timeout=10000)
        self.page.wait_for_timeout(1000)

    def download_sample_csv(self, timeout=20000):
        """Captures the download via Playwright's native download event
        (replaces the Selenium version's DOWNLOAD_DIR mtime-based folder
        polling — same migration already confirmed working in
        whatsapp_overview_page.py / email_overview_page.py export_chart())."""
        try:
            with self.page.expect_download(timeout=timeout) as dl_info:
                self.click_download_sample_csv()
            download = dl_info.value
            filename = download.suggested_filename or f"sample_contacts_{int(time.time() * 1000)}.csv"
            dest = os.path.join(DOWNLOAD_DIR, filename)
            download.save_as(dest)
            return {"file_path": dest, "file_size": os.path.getsize(dest)}
        except Exception:
            return None

    # ── Contact Management tab ───────────────────────────────────────────────

    def select_contact_import_source(self, value):
        """value: 'tags' | 'segments'"""
        el = self.h.wait_for_element_visible(self.CONTACT_IMPORT_SOURCE_SELECT)
        el.select_option(value=value)
        self.page.wait_for_timeout(1000)

    def get_contact_import_source_value(self):
        el = self.h.wait_for_element_visible(self.CONTACT_IMPORT_SOURCE_SELECT)
        return el.input_value()

    def open_ct_contacts_picker(self):
        self._js_click(self.CT_CONTACTS_CONTAINER, timeout=10000)
        self.page.wait_for_timeout(500)

    def is_ct_contacts_picker_present(self):
        return self.is_element_present(self.CT_CONTACTS_CONTAINER, timeout=5000)

    # ── Performance ──────────────────────────────────────────────────────────

    def get_page_load_time_ms(self):
        try:
            return self.page.evaluate(
                "() => window.performance.timing.loadEventEnd - "
                "window.performance.timing.navigationStart"
            )
        except Exception:
            return None
