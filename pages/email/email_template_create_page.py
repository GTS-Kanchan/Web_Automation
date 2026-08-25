from pages.common.base_page import BasePage


class EmailTemplateCreatePage(BasePage):

    CREATE_URL = "/email/template/create"
    LIST_URL = "/email/template"

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_HEADING = "xpath=//h2[normalize-space()='Create Email Template']"

    # ── Global WireUI notification toast (shared across the whole app) ──────
    NOTIFICATION_TITLE = "xpath=//div[@x-data='wireui_notifications']//p[@x-show='notification.title']"

    # ── Form fields ──────────────────────────────────────────────────────────
    NAME_INPUT = "#name"
    TYPE_SELECT = "#type"
    CONTENT_TEXTAREA = "#email_template"
    CONTENT_TINYMCE_IFRAME = "#email_template_ifr"

    TYPE_OPTIONS = ["Select type", "Transactional", "Promotional", "OTP"]

    # ── Footer actions ───────────────────────────────────────────────────────
    CANCEL_LINK = "xpath=//a[contains(@href,'/email/template') and normalize-space()='Cancel']"
    SAVE_BTN = "xpath=//button[@type='submit' and contains(normalize-space(.),'Save Template')]"

    # ── Navigation / page state ─────────────────────────────────────────────

    def navigate(self):
        self.open(self.CREATE_URL)
        self.page.wait_for_timeout(2000)
        return self

    def is_create_page(self):
        return "/email/template/create" in self.get_current_url()

    def is_form_loaded(self):
        return (self.is_element_present(self.NAME_INPUT, timeout=10000)
                and self.is_element_present(self.TYPE_SELECT, timeout=5000)
                and self.is_element_present(self.CONTENT_TEXTAREA, timeout=5000))

    # ── Field getters/setters ────────────────────────────────────────────────

    def fill_name(self, value):
        el = self.h.wait_for_element_visible(self.NAME_INPUT)
        el.fill("")
        el.fill(value)

    def get_name_value(self):
        return self.h.wait_for_element_visible(self.NAME_INPUT).get_attribute("value")

    def get_type_options(self):
        el = self.h.wait_for_element_visible(self.TYPE_SELECT)
        return [o.strip() for o in el.locator("option").all_inner_texts()]

    def select_type(self, visible_text):
        el = self.h.wait_for_element_visible(self.TYPE_SELECT)
        el.select_option(label=visible_text)
        self.page.wait_for_timeout(500)

    def get_selected_type(self):
        el = self.h.wait_for_element_visible(self.TYPE_SELECT)
        return el.locator("option:checked").inner_text().strip()

    def wait_for_tinymce_ready(self, timeout=20000):
        """TinyMCE replaces the hidden textarea with an iframe editor
        asynchronously after tinymce.init() runs — wait for the global
        `tinymce.get('email_template')` instance to exist before
        interacting with it."""
        self.page.wait_for_function(
            "() => !!(window.tinymce && tinymce.get('email_template'))",
            timeout=timeout
        )

    def set_content(self, html):
        """Sets the TinyMCE editor's content via its own documented JS
        API, then calls .save() so the underlying hidden <textarea>
        (which wire:model.defer reads from at form-submit time) reflects
        the new value — CONFIRMED mechanism from the exact
        editor.on('init change', () => editor.save()) handler captured
        in this page's DOM."""
        self.wait_for_tinymce_ready()
        self.page.evaluate(
            "(html) => { var ed = tinymce.get('email_template'); "
            "ed.setContent(html); "
            "ed.save(); }",
            html
        )
        self.page.wait_for_timeout(500)

    def get_content(self):
        self.wait_for_tinymce_ready()
        return self.page.evaluate("() => tinymce.get('email_template').getContent()")

    # ── Footer actions ───────────────────────────────────────────────────────

    def click_cancel(self):
        self._js_click(self.CANCEL_LINK, timeout=10000)
        self.page.wait_for_timeout(1000)

    def is_save_button_enabled(self):
        try:
            btn = self.page.locator(self.SAVE_BTN).first
            return btn.is_enabled() and btn.get_attribute("disabled") is None
        except Exception:
            return False

    def click_save(self):
        self._js_click(self.SAVE_BTN, timeout=10000)
        self.page.wait_for_timeout(2000)

    # ── Toast (shared global WireUI notification component) ──────────────────

    def is_success_toast_shown(self, timeout=6000):
        return self.is_element_present(self.NOTIFICATION_TITLE, timeout=timeout)

    def is_list_page(self):
        url = self.get_current_url()
        return "/email/template" in url and "/create" not in url

    # ── Convenience: full valid submission ───────────────────────────────────

    def create_template(self, name, type_text=None, content_html=None):
        """Fills all three fields (Type/Content optional) and clicks
        Save. Returns the name used, for callers that need to search for
        the resulting row afterwards."""
        self.fill_name(name)
        if type_text:
            self.select_type(type_text)
        if content_html:
            self.set_content(content_html)
        self.click_save()
        return name
