import os

from pages.common.base_page import BasePage


class RcsCampaignCreatePage(BasePage):

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

    # ── Global WireUI notification toast ────────────────────────────────────
    NOTIFICATION_TITLE = (
        "xpath=//div[@x-data='wireui_notifications']//p[@x-show='notification.title'] | "
        "//*[contains(@class,'wireui') and contains(@class,'notification')] | "
        "//*[@x-data='wireui_notifications']//*[contains(@class,'title')]"
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

    # ── Form fields — RCS Agent select ──────────────────────────────────────
    RCS_AGENT_SELECT = (
        "xpath=//select[@id='agent_id'] | "
        "//select[@id='rcs_agent_id'] | "
        "//select[@*[name()='wire:model.live' and contains(.,'rcs_agent_id')]] | "
        "//select[@*[name()='wire:model' and contains(.,'agent')]]"
    )

    # ── Form fields — Template select ───────────────────────────────────────
    TEMPLATE_SELECT = (
        "xpath=//select[@id='template_id'] | "
        "//select[@*[name()='wire:model.live' and contains(.,'template_id')]] | "
        "//select[@*[name()='wire:model' and contains(.,'template')]]"
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

    MODAL_CP_TEXTAREA = "xpath=//textarea[@*[name()='wire:model']='cp_contacts' or @id='cp_contacts']"

    MODAL_FILE_UPLOAD = (
        "xpath=//input[@type='file' and (@*[name()='wire:model']='contact_file' or @*[name()='wire:model']='fu_contacts')]"
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

    # ══════════════════════════════════════════════════════════════════════════
    # RCS Agent
    # ══════════════════════════════════════════════════════════════════════════

    def is_agent_select_present(self, timeout=8000):
        return self.is_element_present(self.RCS_AGENT_SELECT, timeout=timeout)

    def get_agent_options(self):
        """Return list of non-empty visible option texts from the agent select."""
        try:
            el = self.h.wait_for_element_visible(self.RCS_AGENT_SELECT)
            opts = el.locator("option")
            return [opts.nth(i).inner_text().strip() for i in range(opts.count()) if opts.nth(i).inner_text().strip()]
        except Exception:
            return []

    def select_agent_by_index(self, index: int = 1):
        """Select the agent at the given option index (0 = placeholder)."""
        try:
            el = self.h.wait_for_element_visible(self.RCS_AGENT_SELECT)
            el.select_option(index=index)
            self.page.wait_for_timeout(1000)
            self._wait_spinner_gone()
            return True
        except Exception:
            return False

    def select_agent_by_visible_text(self, text: str):
        el = self.h.wait_for_element_visible(self.RCS_AGENT_SELECT)
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
        return self.is_element_present(self.TEMPLATE_SELECT, timeout=timeout)

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
            el = self.h.wait_for_element_visible(self.TEMPLATE_SELECT)
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
            return False
        except Exception:
            return False

    def get_selected_template(self):
        try:
            el = self.h.wait_for_element_visible(self.TEMPLATE_SELECT)
            return el.locator("option:checked").inner_text().strip()
        except Exception:
            return ""

    # ══════════════════════════════════════════════════════════════════════════
    # Send Type radios
    # ══════════════════════════════════════════════════════════════════════════

    def is_send_now_radio_present(self, timeout=5000):
        return self.is_element_present(self.RADIO_SEND_NOW, timeout=timeout)

    def is_schedule_later_radio_present(self, timeout=5000):
        return self.is_element_present(self.RADIO_SCHEDULE_LATER, timeout=timeout)

    def select_send_now(self):
        try:
            self._js_click(self.RADIO_SEND_NOW)
            self.page.wait_for_timeout(500)
            return True
        except Exception:
            return False

    def select_schedule_later(self):
        try:
            self._js_click(self.RADIO_SCHEDULE_LATER)
            self.page.wait_for_timeout(500)
            self._wait_spinner_gone()
            return True
        except Exception:
            return False

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
        """
        try:
            el = self.page.locator(self.SCHEDULE_DATETIME_INPUT).first
            el.wait_for(state="visible", timeout=8000)

            is_date_only = el.get_attribute("type") == "date"
            if is_date_only and "T" in value:
                date_part, time_part = value.split("T")

                # Fill date part
                el.evaluate(
                    "(elm, v) => { elm.value = v; "
                    "elm.dispatchEvent(new Event('input',{bubbles:true})); "
                    "elm.dispatchEvent(new Event('change',{bubbles:true})); }",
                    date_part
                )

                # Fill time part
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
        try:
            el = self.page.locator(self.SCHEDULE_DATETIME_INPUT).first
            el.wait_for(state="attached", timeout=5000)

            is_date_only = el.get_attribute("type") == "date"
            date_val = el.get_attribute("value") or ""

            if is_date_only and date_val:
                try:
                    time_select_xpath = "xpath=//select[@*[name()='x-model' and contains(.,'time')]]"
                    time_el = self.page.locator(time_select_xpath).first
                    time_val = time_el.get_attribute("value") or ""
                    if time_val:
                        return f"{date_val}T{time_val}"
                except Exception:
                    pass
            return date_val
        except Exception:
            return ""

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

    def click_import_contacts_btn(self):
        try:
            self._js_click(self.IMPORT_CONTACTS_BTN)
            self.page.wait_for_timeout(500)
            self._wait_spinner_gone()
            return True
        except Exception:
            return False

    def click_import_confirm(self):
        try:
            # First click 'Continue' or 'Import'
            btn = self.page.locator(self.IMPORT_CONFIRM_BTN).first
            btn.wait_for(state="attached", timeout=15000)
            self.h.wait_until(lambda: btn.is_enabled(), timeout_ms=10000, interval_ms=500)
            self._js_click(self.IMPORT_CONFIRM_BTN)
            self.page.wait_for_timeout(1500)

            # Second step: 'Confirm & Continue' might appear after backend processes contacts
            confirm_and_continue = "xpath=//div[contains(@class,'fixed') or @x-show='show']//button[contains(normalize-space(),'Confirm')]"
            try:
                btn2 = self.page.locator(confirm_and_continue).first
                btn2.wait_for(state="visible", timeout=4000)
                self._js_click(confirm_and_continue)
                self.page.wait_for_timeout(1000)
            except Exception:
                pass  # Not a two step modal, or didn't load

            # Wait for modal to close
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

    def is_modal_cp_contacts_textarea_present(self, timeout=5000):
        return self.is_element_present(self.MODAL_CP_TEXTAREA, timeout=timeout)

    def fill_modal_cp_contacts(self, numbers: str):
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
            # Click File Upload tab if present
            try:
                tab_xpath = (
                    "xpath=//*[(local-name()='button' or local-name()='a') and "
                    "contains(translate(normalize-space(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'file upload')]"
                )
                tab = self.page.locator(tab_xpath).first
                print(f"DEBUG: Found tab element. is_visible={tab.is_visible()}")
                self._js_click(tab_xpath)
                self.page.wait_for_timeout(1000)
            except Exception as e:
                print(f"DEBUG: Failed to click file upload tab: {e}")

            try:
                el = self.page.locator(self.MODAL_FILE_UPLOAD).first
                el.wait_for(state="attached", timeout=5000)
            except Exception as e:
                # dump html for debugging
                with open("modal_dump.html", "w", encoding="utf-8") as f:
                    f.write(self.page.content())
                print("File upload element not found! Saved modal_dump.html")
                raise e

            el.set_input_files(os.path.abspath(filepath))
            self.page.wait_for_timeout(2000)

            # Wait for processing loader if any
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

    def click_submit(self):
        self._js_click(self.SUBMIT_BTN, timeout=10000)
        self.page.wait_for_timeout(2000)

    def confirm_launch(self, timeout=5000):
        """Handle the sweet alert confirmation that appears after click_submit()."""
        try:
            proceed_btn = "xpath=//button[contains(normalize-space(),'Proceed') or contains(@class,'swal2-confirm')]"
            btn = self.h.wait_for_element_clickable(proceed_btn, timeout=timeout)
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
