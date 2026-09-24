"""
Page Object for Chatbot -> Download Center -> Create Request Report.
Page URL: /chatbot/download/center/create
"""

import time
from typing import List, Optional
from playwright.sync_api import Page, Locator

from pages.common.base_page import BasePage
from utils.config import Config


class ChatbotRequestReportPage(BasePage):
    """
    Page Object Model for the Chatbot Request a Report page.
    """

    PATH = "/chatbot/download/center/create"

    def __init__(self, page: Page):
        super().__init__(page)

        # Main headers & containers
        self.heading = page.locator("h2:has-text('Request a Report')")
        self.subheading = page.locator("p:has-text('Generate a chatbot detailed report for download')")
        self.breadcrumb_nav = page.locator("nav[aria-label='Breadcrumb']")
        self.breadcrumb_items = page.locator("nav[aria-label='Breadcrumb'] ol li")

        # Form fields
        self.report_name_input = page.locator('input[wire\\:model="name"]')
        self.report_name_label = page.locator("label:has-text('Report Name')")

        self.bot_type_select = page.locator('select[wire\\:model="bot_type"]')
        self.bot_type_label = page.locator("label:has-text('Bot Type')")

        self.from_date_input = page.locator('input[wire\\:model="from_date"]')
        self.from_date_label = page.locator("label:has-text('From Date')")
        self.from_date_helper = page.locator("p:has-text('Maximum 90 days ago')")

        self.to_date_input = page.locator('input[wire\\:model="to_date"]')
        self.to_date_label = page.locator("label:has-text('To Date')")
        self.to_date_helper = page.locator("p:has-text('Maximum yesterday')")

        # Action buttons
        self.generate_report_button = page.locator('button[type="submit"]')
        self.cancel_button = page.locator('a:has-text("Cancel")')

        # Generic validation / alerts
        self.validation_errors = page.locator("span.text-red-500, p.text-red-500, div.text-red-500")

    # ─────────────────────────────────────────────────────────────────────────
    # Navigation
    # ─────────────────────────────────────────────────────────────────────────

    def navigate(self):
        """Navigate directly to the Request Report page."""
        url = f"{Config.BASE_URL}{self.PATH}"
        self.page.goto(url)
        self.wait_for_load(timeout=15000)

    def navigate_via_sidebar(self):
        """Navigate via sidebar Chatbot link then Download Center tab."""
        chatbot_link = self.page.locator("aside nav a[href*='/chatbot/settings']")
        if chatbot_link.count() > 0 and chatbot_link.is_visible():
            chatbot_link.click()
            self.page.wait_for_load_state("domcontentloaded")

        dl_center_tab = self.page.locator("a[href*='/chatbot/download/center']")
        if dl_center_tab.count() > 0:
            dl_center_tab.first.click()
            self.page.wait_for_load_state("domcontentloaded")

        # Now go to create report if button exists or navigate direct
        create_btn = self.page.locator("a[href*='/chatbot/download/center/create']")
        if create_btn.count() > 0 and create_btn.first.is_visible():
            create_btn.first.click()
            self.page.wait_for_load_state("domcontentloaded")
        else:
            self.navigate()

    def wait_for_load(self, timeout: int = 10000):
        """Wait for page heading and form container to appear."""
        self.heading.wait_for(state="visible", timeout=timeout)

    def is_request_report_page(self) -> bool:
        """Check if currently on the Request a Report page."""
        url_match = "/chatbot/download/center/create" in self.page.url
        heading_visible = self.heading.count() > 0 and self.heading.is_visible()
        return url_match or heading_visible

    # ─────────────────────────────────────────────────────────────────────────
    # Headings & Breadcrumbs
    # ─────────────────────────────────────────────────────────────────────────

    def get_heading_text(self) -> str:
        """Return the text of the page heading."""
        if self.heading.is_visible():
            return self.heading.inner_text().strip()
        return ""

    def get_subheading_text(self) -> str:
        """Return the text of the page subheading."""
        if self.subheading.is_visible():
            return self.subheading.inner_text().strip()
        return ""

    def get_breadcrumb_text(self) -> str:
        """Return the full breadcrumb text."""
        if self.breadcrumb_nav.is_visible():
            return self.breadcrumb_nav.inner_text().strip()
        return ""

    def get_breadcrumb_items(self) -> List[str]:
        """Return individual breadcrumb link/text items."""
        items = []
        count = self.breadcrumb_items.count()
        for i in range(count):
            text = self.breadcrumb_items.nth(i).inner_text().strip()
            # Clean up empty strings or separator characters
            text = text.replace(">", "").strip()
            if text:
                items.append(text)
        return items

    # ─────────────────────────────────────────────────────────────────────────
    # Report Name Field
    # ─────────────────────────────────────────────────────────────────────────

    def is_report_name_visible(self) -> bool:
        """Check if Report Name input is visible."""
        return self.report_name_input.is_visible()

    def is_report_name_mandatory(self) -> bool:
        """Check if Report Name label has the mandatory indicator (* or red asterisk)."""
        if self.report_name_label.count() > 0:
            label_text = self.report_name_label.inner_text()
            has_asterisk = "*" in label_text
            red_span = self.report_name_label.locator("span.text-red-500")
            return has_asterisk or red_span.count() > 0
        return False

    def get_report_name_placeholder(self) -> str:
        """Get placeholder attribute of Report Name input."""
        return self.report_name_input.get_attribute("placeholder") or ""

    def get_report_name_maxlength(self) -> Optional[int]:
        """Get maxlength attribute of Report Name input."""
        val = self.report_name_input.get_attribute("maxlength")
        return int(val) if val and val.isdigit() else None

    def enter_report_name(self, name: str):
        """Enter value into Report Name input."""
        self.report_name_input.fill(name)
        # Trigger Livewire model update
        self.report_name_input.dispatch_event("input")
        self.report_name_input.dispatch_event("change")

    def clear_report_name(self):
        """Clear the Report Name input."""
        self.report_name_input.fill("")
        self.report_name_input.dispatch_event("input")
        self.report_name_input.dispatch_event("change")

    def get_report_name_value(self) -> str:
        """Get current value of Report Name input."""
        return self.report_name_input.input_value()

    # ─────────────────────────────────────────────────────────────────────────
    # Bot Type Dropdown
    # ─────────────────────────────────────────────────────────────────────────

    def is_bot_type_dropdown_visible(self) -> bool:
        """Check if Bot Type dropdown is visible."""
        return self.bot_type_select.is_visible()

    def get_bot_type_options(self) -> List[str]:
        """Get all visible option texts from Bot Type dropdown."""
        options = self.bot_type_select.locator("option")
        count = options.count()
        return [options.nth(i).inner_text().strip() for i in range(count)]

    def get_selected_bot_type(self) -> str:
        """Get visible text of currently selected option in Bot Type."""
        return self.bot_type_select.evaluate(
            "el => el.options[el.selectedIndex] ? el.options[el.selectedIndex].text.trim() : ''"
        )

    def get_selected_bot_type_value(self) -> str:
        """Get value attribute of currently selected option in Bot Type."""
        return self.bot_type_select.input_value()

    def select_bot_type(self, label_or_value: str):
        """Select an option in Bot Type dropdown by label or value."""
        # Try by label first
        try:
            self.bot_type_select.select_option(label=label_or_value)
        except Exception:
            self.bot_type_select.select_option(value=label_or_value)
        self.bot_type_select.dispatch_event("change")

    # ─────────────────────────────────────────────────────────────────────────
    # From Date Field
    # ─────────────────────────────────────────────────────────────────────────

    def is_from_date_visible(self) -> bool:
        """Check if From Date input is visible."""
        return self.from_date_input.is_visible()

    def is_from_date_mandatory(self) -> bool:
        """Check if From Date is marked mandatory."""
        if self.from_date_label.count() > 0:
            label_text = self.from_date_label.inner_text()
            has_asterisk = "*" in label_text
            red_span = self.from_date_label.locator("span.text-red-500")
            return has_asterisk or red_span.count() > 0
        return False

    def get_from_date_value(self) -> str:
        """Get current value of From Date."""
        return self.from_date_input.input_value()

    def get_from_date_min(self) -> str:
        """Get min attribute of From Date."""
        return self.from_date_input.get_attribute("min") or ""

    def get_from_date_max(self) -> str:
        """Get max attribute of From Date."""
        return self.from_date_input.get_attribute("max") or ""

    def get_from_date_helper_text(self) -> str:
        """Get helper text under From Date."""
        if self.from_date_helper.is_visible():
            return self.from_date_helper.inner_text().strip()
        return ""

    def enter_from_date(self, date_str: str):
        """Enter a date into From Date."""
        self.from_date_input.fill(date_str)
        self.from_date_input.dispatch_event("input")
        self.from_date_input.dispatch_event("change")

    # ─────────────────────────────────────────────────────────────────────────
    # To Date Field
    # ─────────────────────────────────────────────────────────────────────────

    def is_to_date_visible(self) -> bool:
        """Check if To Date input is visible."""
        return self.to_date_input.is_visible()

    def is_to_date_mandatory(self) -> bool:
        """Check if To Date is marked mandatory."""
        if self.to_date_label.count() > 0:
            label_text = self.to_date_label.inner_text()
            has_asterisk = "*" in label_text
            red_span = self.to_date_label.locator("span.text-red-500")
            return has_asterisk or red_span.count() > 0
        return False

    def get_to_date_value(self) -> str:
        """Get current value of To Date."""
        return self.to_date_input.input_value()

    def get_to_date_max(self) -> str:
        """Get max attribute of To Date."""
        return self.to_date_input.get_attribute("max") or ""

    def get_to_date_helper_text(self) -> str:
        """Get helper text under To Date."""
        if self.to_date_helper.is_visible():
            return self.to_date_helper.inner_text().strip()
        return ""

    def enter_to_date(self, date_str: str):
        """Enter a date into To Date."""
        self.to_date_input.fill(date_str)
        self.to_date_input.dispatch_event("input")
        self.to_date_input.dispatch_event("change")

    # ─────────────────────────────────────────────────────────────────────────
    # Actions & Validation
    # ─────────────────────────────────────────────────────────────────────────

    def click_generate_report(self):
        """Click the 'Generate Report' submit button."""
        self.generate_report_button.click()
        self.page.wait_for_timeout(500)

    def click_cancel(self):
        """Click the 'Cancel' button."""
        self.cancel_button.click()
        self.page.wait_for_load_state("domcontentloaded")

    def get_validation_errors(self) -> List[str]:
        """Collect visible validation error texts on the page."""
        errors = []
        # Check input error spans
        err_loc = self.page.locator("span.text-red-500, p.text-red-500, div.text-red-500, .text-danger")
        count = err_loc.count()
        for i in range(count):
            item = err_loc.nth(i)
            if item.is_visible():
                txt = item.inner_text().strip()
                if txt and txt != "*":
                    errors.append(txt)

        # Check WireUI notifications or alerts
        wireui_notification = self.page.locator("[x-data='wireui_notifications'] p")
        count_notif = wireui_notification.count()
        for i in range(count_notif):
            item = wireui_notification.nth(i)
            if item.is_visible():
                txt = item.inner_text().strip()
                if txt:
                    errors.append(txt)

        return errors

    def is_validation_error_displayed(self) -> bool:
        """Check if any validation error is displayed."""
        errors = self.get_validation_errors()
        return len(errors) > 0

    def check_input_validity(self, locator: Locator) -> bool:
        """Check HTML5 validity for a specific input."""
        return locator.evaluate("el => el.checkValidity()")
