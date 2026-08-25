from pages.common.base_page import BasePage


class RcsTemplateCreatePage(BasePage):

    CREATE_URL = "/rcs/template/create"
    LIST_URL = "/rcs/template"

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_HEADING = (
        "xpath=//h1[contains(normalize-space(.),'Create') and "
        "contains(normalize-space(.),'Template')] | "
        "//h2[contains(normalize-space(.),'Create') and "
        "contains(normalize-space(.),'Template')]"
    )
    BREADCRUMB = "nav[aria-label='Breadcrumb']"

    # ── Global WireUI notification toast ────────────────────────────────────
    NOTIFICATION_TITLE = "xpath=//div[@x-data='wireui_notifications']//p[@x-show='notification.title']"

    # ── Form fields ──────────────────────────────────────────────────────────
    NAME_INPUT = "#name"
    TYPE_SELECT = "#type"
    # Plain <textarea> (NOT TinyMCE) — confirmed by emoji-picker in DOM
    BODY_TEXTAREA = (
        "xpath=//textarea[contains(@*[name()='wire:model.live'],'message_content') "
        "or contains(@*[name()='wire:model.defer'],'body') "
        "or contains(@*[name()='wire:model'],'body') "
        "or @id='message_content-input' or @name='message_content']"
    )
    # Emoji picker trigger button (confirmed by emoji-picker CSS in page)
    EMOJI_TRIGGER = (
        "xpath=//button[contains(@class,'emoji') or @data-emoji-trigger "
        "or contains(@class,'picker')] | "
        "//span[contains(@class,'emoji') and @role='button']"
    )
    CHAR_COUNTER = (
        "xpath=//*[contains(@class,'char') and contains(text(),'/')] | "
        "//*[contains(@x-text,'charCount') or contains(@x-text,'length')]"
    )

    # ── Agent select (used by create_template flow) ──────────────────────────
    AGENT_SELECT = (
        "xpath=//select[@id='agent_id'] | //select[@id='rcs_agent_id'] "
        "| //select[contains(@*[name()='wire:model'], 'agent')]"
    )

    # ── Footer actions ───────────────────────────────────────────────────────
    CANCEL_LINK = (
        "xpath=//a[contains(@href,'/rcs/template') and "
        "not(contains(@href,'/create')) and "
        "normalize-space()='Cancel']"
    )
    SAVE_BTN = (
        "xpath=//button[@type='submit'] | "
        "//button[contains(normalize-space(.),'Save') or "
        "contains(normalize-space(.),'Create') or "
        "contains(normalize-space(.),'Submit')]"
    )

    # ── Known type options (same taxonomy as every other RCS form) ───────────
    TYPE_OPTIONS_EXPECTED = ["Text Message", "Text Message with Document", "Rich Card Stand-alone", "Rich Card Carousel"]

    # ── Navigation / page state ─────────────────────────────────────────────

    def navigate(self):
        self.open(self.CREATE_URL)
        self.page.wait_for_timeout(2000)
        return self

    def is_create_page(self):
        return "/rcs/template/create" in self.get_current_url()

    def is_list_page(self):
        url = self.get_current_url()
        return "/rcs/template" in url and "/create" not in url

    def is_form_loaded(self):
        return (self.is_element_present(self.NAME_INPUT, timeout=10000)
                and self.is_element_present(self.TYPE_SELECT, timeout=5000))

    def get_page_heading_text(self):
        el = self.h.wait_for_element_visible(self.PAGE_HEADING)
        return el.inner_text().strip()

    def get_breadcrumb_text(self):
        el = self.h.wait_for_element_visible(self.BREADCRUMB)
        return " ".join(el.inner_text().split())

    # ── Field getters / setters ──────────────────────────────────────────────

    def fill_name(self, value):
        el = self.h.wait_for_element_visible(self.NAME_INPUT)
        el.fill("")
        el.fill(value)

    def get_name_value(self):
        return self.h.wait_for_element_visible(self.NAME_INPUT).input_value()

    def get_type_options(self):
        el = self.h.wait_for_element_visible(self.TYPE_SELECT)
        opts = el.locator("option")
        return [opts.nth(i).inner_text().strip() for i in range(opts.count()) if opts.nth(i).inner_text().strip()]

    def select_type(self, visible_text):
        el = self.h.wait_for_element_visible(self.TYPE_SELECT)
        self.h.select_option(self.TYPE_SELECT, label=visible_text)
        self.page.wait_for_timeout(500)

    def get_selected_type(self):
        el = self.h.wait_for_element_visible(self.TYPE_SELECT)
        return el.locator("option:checked").inner_text().strip()

    def select_agent(self, text_contains):
        el = self.h.wait_for_element_visible(self.AGENT_SELECT)
        opts = el.locator("option")
        # Try to find a matching option first
        for i in range(opts.count()):
            opt = opts.nth(i)
            text = opt.inner_text().strip()
            if text_contains.lower() in text.lower():
                self.h.select_option(self.AGENT_SELECT, label=text)
                self.page.wait_for_timeout(500)
                return
        # Fallback to the first non-empty option
        for i in range(opts.count()):
            opt = opts.nth(i)
            val = opt.get_attribute("value")
            text = opt.inner_text().strip()
            if val and text:
                self.h.select_option(self.AGENT_SELECT, label=text)
                self.page.wait_for_timeout(500)
                return

    def fill_body(self, value):
        """Sets the message body textarea value via standard Playwright fill
        so Livewire correctly registers the input."""
        try:
            el = self.h.wait_for_element_visible(self.BODY_TEXTAREA)
            el.fill("")
            el.fill(value)
            self.page.wait_for_timeout(300)
            return True
        except Exception as e:
            print(f"Error in fill_body: {e}")
            return False

    def get_body_value(self):
        try:
            el = self.h.wait_for_element_visible(self.BODY_TEXTAREA)
            return el.input_value() or ""
        except Exception:
            return ""

    def clear_body(self):
        try:
            el = self.h.wait_for_element_visible(self.BODY_TEXTAREA)
            el.evaluate(
                "(elm) => { elm.value = ''; "
                "elm.dispatchEvent(new Event('input', {bubbles: true})); }"
            )
            self.page.wait_for_timeout(300)
        except Exception:
            pass

    def has_emoji_trigger(self):
        return self.is_element_present(self.EMOJI_TRIGGER, timeout=3000)

    # ── Footer actions ───────────────────────────────────────────────────────

    def click_cancel(self):
        self._js_click(self.CANCEL_LINK, timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_save_button_present(self):
        return self.is_element_present(self.SAVE_BTN, timeout=5000)

    def is_save_button_enabled(self):
        try:
            btn = self.page.locator(self.SAVE_BTN).first
            return btn.is_enabled() and btn.get_attribute("disabled") is None
        except Exception:
            return False

    def click_save(self):
        self._js_click(self.SAVE_BTN, timeout=10000)
        self.page.wait_for_timeout(2000)

    # ── Toast / feedback ─────────────────────────────────────────────────────

    def is_success_toast_shown(self, timeout=6000):
        return self.is_element_present(self.NOTIFICATION_TITLE, timeout=timeout)

    # ── Convenience: full valid submission ───────────────────────────────────

    def create_template(self, name, type_text=None, body=None):
        """Fills all fields and clicks Save. Returns the name used."""
        self.navigate()
        self.fill_name(name)
        if type_text:
            self.select_type(type_text)
        if body:
            self.fill_body(body)
        self.click_save()
        return name

    # ── Performance ──────────────────────────────────────────────────────────

    def get_page_load_time_ms(self):
        try:
            return self.page.evaluate(
                "() => window.performance.timing.loadEventEnd - "
                "window.performance.timing.navigationStart"
            )
        except Exception:
            return None
