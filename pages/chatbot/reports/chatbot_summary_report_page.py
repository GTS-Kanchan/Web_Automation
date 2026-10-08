"""
Page Object for Chatbot -> Reports -> Summary (Chatbot Flow Summary Report).
Page URL: /chatbot/reports/summary
"""

import time
from typing import List, Dict, Optional
from playwright.sync_api import Page, Locator

from pages.common.base_page import BasePage
from utils.config import Config
from constants.chatbot_summary_headers import COLUMN_KEYS


class ChatbotSummaryReportPage(BasePage):
    """
    Page Object Model for the Chatbot Flow Summary Report.
    """

    PATH = "/chatbot/reports/summary"

    def __init__(self, page: Page):
        super().__init__(page)

        # Page Heading
        self.heading = page.locator("h1:has-text('Chatbot Flow summary Report')")

        # Table & Containers
        self.table_container = page.locator("#datatable-3aM1clxI8yRtvk5RLuiL, div[wire\\:key='bot_flow_summary_report-wrapper']")
        self.table = page.locator("#table-bot_flow_summary_report")
        self.thead_headers = page.locator("#table-bot_flow_summary_report thead th")
        self.table_rows = page.locator("#bot_flow_summary_report-tbody tr:not([wire\\:key='bot_flow_summary_report-bulk-select-message'])")

        # Search
        self.search_input = page.locator("input[wire\\:model\\.live='search']")

        # Filters Popover
        self.filters_button = page.locator("div[x-data*='filterPopoverOpen'] button:has-text('Filters')")
        self.filters_popover = page.locator("div[x-show='filterPopoverOpen']")
        self.from_date_input = page.locator("#bot_flow_summary_report-filter-from_date")
        self.to_date_input = page.locator("#bot_flow_summary_report-filter-to_date")
        self.flow_name_select = page.locator("#bot_flow_summary_report-filter-flow_name")

        # Applied Filters & Sorting Pills
        self.applied_sorting_pills = page.locator("span[wire\\:key^='bot_flow_summary_report-sorting-pill']")
        self.clear_sorting_button = page.locator("button[wire\\:click\\.prevent='clearSorts']")
        self.applied_filter_pills = page.locator("div[wire\\:key^='bot_flow_summary_report-filter-pill']")
        self.clear_filters_button = page.locator("button[x-on\\:click\\.prevent='resetAllFilters']")

        # Columns Visibility Dropdown
        self.columns_button = page.locator("button:has-text('Columns')")
        self.columns_menu = page.locator("div[role='menu'][aria-labelledby='column-select-menu']")

        # Bulk Actions
        self.header_checkbox = page.locator("th[wire\\:key='bot_flow_summary_report-thead-bulk-actions'] input[type='checkbox']")
        self.bulk_actions_button = page.locator("#bot_flow_summary_report-bulkActionsDropdown")
        self.export_xlsx_bulk_button = page.locator("button[wire\\:click='export']")

    # ─────────────────────────────────────────────────────────────────────────
    # Navigation
    # ─────────────────────────────────────────────────────────────────────────

    def navigate(self):
        """Navigate directly to Chatbot Flow Summary Report page."""
        url = f"{Config.BASE_URL}{self.PATH}"
        self.page.goto(url)
        self.wait_for_table_load()

    def wait_for_table_load(self, timeout: int = 15000):
        """Wait for page heading and table to be visible."""
        self.heading.wait_for(state="visible", timeout=timeout)
        self.table.wait_for(state="visible", timeout=timeout)
        self.page.wait_for_load_state("domcontentloaded")

    def is_summary_report_page(self) -> bool:
        """Verify currently on Chatbot Flow Summary Report page."""
        url_match = "/chatbot/reports/summary" in self.page.url
        heading_visible = self.heading.count() > 0 and self.heading.is_visible()
        return url_match or heading_visible

    def get_heading_text(self) -> str:
        """Return the heading text."""
        if self.heading.is_visible():
            return self.heading.inner_text().strip()
        return ""

    # ─────────────────────────────────────────────────────────────────────────
    # Table Inspection
    # ─────────────────────────────────────────────────────────────────────────

    def get_column_headers(self) -> List[str]:
        """Return visible header text list, excluding bulk action checkbox header."""
        headers = []
        count = self.thead_headers.count()
        for i in range(count):
            th = self.thead_headers.nth(i)
            # Skip bulk action checkbox header
            if "bulk-actions" in (th.get_attribute("wire:key") or ""):
                continue
            text = th.inner_text().strip()
            # Clean up newlines or sorting arrows
            clean_text = text.split("\n")[0].strip()
            if clean_text:
                headers.append(clean_text)
        return headers

    def get_row_count(self) -> int:
        """Return count of visible data rows in table."""
        self.page.wait_for_timeout(300)
        return self.table_rows.count()

    def is_empty_state_displayed(self) -> bool:
        """Check if empty state / no records row is visible."""
        if self.get_row_count() == 0:
            return True
        first_row_text = self.table_rows.first.inner_text()
        return "No items found" in first_row_text or "No matching records" in first_row_text

    def get_cell_value(self, row_index: int, column_key: str) -> str:
        """
        Get text of a cell by 0-based row index and column key.
        e.g., column_key: 'flow-name', 'date', 'conversation-opened', etc.
        """
        row = self.table_rows.nth(row_index)
        # Check td by wire:key suffix
        td = row.locator(f"td[wire\\:key*='-{column_key}']")
        if td.count() > 0:
            return td.first.inner_text().strip()
        # Fallback to order index
        col_names = list(COLUMN_KEYS.keys())
        if column_key in col_names:
            idx = col_names.index(column_key) + 1  # +1 for checkbox
            return row.locator(f"td:nth-child({idx + 1})").inner_text().strip()
        return ""

    def get_column_values(self, column_key: str) -> List[str]:
        """Get all visible cell values for a given column key."""
        count = self.get_row_count()
        return [self.get_cell_value(i, column_key) for i in range(count)]

    def get_all_rows_data(self) -> List[Dict[str, str]]:
        """Get list of dictionaries representing all rows."""
        data = []
        count = self.get_row_count()
        for i in range(count):
            row_dict = {}
            for k in COLUMN_KEYS.keys():
                row_dict[k] = self.get_cell_value(i, k)
            data.append(row_dict)
        return data

    # ─────────────────────────────────────────────────────────────────────────
    # Search Functionality
    # ─────────────────────────────────────────────────────────────────────────

    def search(self, query: str):
        """Type query into search input and wait for Livewire debounce."""
        self.search_input.fill(query)
        self.search_input.dispatch_event("input")
        self.page.wait_for_timeout(600)

    def clear_search(self):
        """Clear search input and wait for reload."""
        self.search_input.fill("")
        self.search_input.dispatch_event("input")
        self.page.wait_for_timeout(600)

    def get_search_value(self) -> str:
        """Return current value of search input."""
        return self.search_input.input_value()

    # ─────────────────────────────────────────────────────────────────────────
    # Filters Popover
    # ─────────────────────────────────────────────────────────────────────────

    def open_filters(self):
        """Open the filter popover menu if closed."""
        if not self.is_filter_popover_open():
            self.filters_button.click()
            self.filters_popover.wait_for(state="visible", timeout=5000)

    def close_filters(self):
        """Close the filter popover menu if open."""
        if self.is_filter_popover_open():
            self.filters_button.click()
            self.page.wait_for_timeout(300)

    def is_filter_popover_open(self) -> bool:
        """Check if filter popover is currently open."""
        return self.filters_popover.count() > 0 and self.filters_popover.is_visible()

    def set_from_date(self, date_str: str):
        """Set From Date filter."""
        self.open_filters()
        self.from_date_input.fill(date_str)
        self.from_date_input.dispatch_event("change")
        self.page.wait_for_timeout(500)

    def set_to_date(self, date_str: str):
        """Set To Date filter."""
        self.open_filters()
        self.to_date_input.fill(date_str)
        self.to_date_input.dispatch_event("change")
        self.page.wait_for_timeout(500)

    def select_flow_name(self, flow_name: str):
        """Select a flow name from the filter dropdown."""
        self.open_filters()
        self.flow_name_select.select_option(label=flow_name)
        self.flow_name_select.dispatch_event("change")
        self.page.wait_for_timeout(600)

    def get_available_flow_name_options(self) -> List[str]:
        """Get all options from the flow_name filter dropdown."""
        self.open_filters()
        options = self.flow_name_select.locator("option")
        count = options.count()
        return [options.nth(i).inner_text().strip() for i in range(count)]

    def get_filter_badge_count(self) -> Optional[int]:
        """Return badge count number on Filters button if present."""
        badge = self.filters_button.locator("span.rounded-full")
        if badge.count() > 0 and badge.is_visible():
            txt = badge.inner_text().strip()
            return int(txt) if txt.isdigit() else None
        return None

    def clear_all_filters(self):
        """Click the Clear button on applied filters if visible, or reset fields."""
        if self.clear_filters_button.count() > 0 and self.clear_filters_button.is_visible():
            self.clear_filters_button.click()
            self.page.wait_for_timeout(600)
        else:
            self.open_filters()
            try:
                self.from_date_input.fill("")
                self.from_date_input.dispatch_event("change")
            except Exception:
                pass
            try:
                self.to_date_input.fill("")
                self.to_date_input.dispatch_event("change")
            except Exception:
                pass
            try:
                self.flow_name_select.select_option(value="")
                self.flow_name_select.dispatch_event("change")
            except Exception:
                pass
            self.close_filters()
            self.page.wait_for_timeout(500)

    def get_applied_filter_pills_text(self) -> List[str]:
        """Return list of text from applied filter pills."""
        count = self.applied_filter_pills.count()
        return [self.applied_filter_pills.nth(i).inner_text().strip() for i in range(count)]

    def remove_filter_pill(self, filter_key: str):
        """Remove a specific applied filter pill by key or button."""
        pill = self.page.locator(f"div[wire\\:key='bot_flow_summary_report-filter-pill-{filter_key}'] button")
        if pill.count() > 0 and pill.is_visible():
            pill.click()
            self.page.wait_for_timeout(500)

    # ─────────────────────────────────────────────────────────────────────────
    # Sorting
    # ─────────────────────────────────────────────────────────────────────────

    def sort_by_flow_name(self):
        """Click sort on Flow Name column header."""
        btn = self.page.locator("button[wire\\:click=\"sortBy('flow_name')\"]")
        btn.click()
        self.page.wait_for_timeout(600)

    def sort_by_date(self):
        """Click sort on Date column header."""
        btn = self.page.locator("button[wire\\:click=\"sortBy('created_at')\"]")
        btn.click()
        self.page.wait_for_timeout(600)

    def sort_by_conversation_opened(self):
        """Click sort on Conversation Opened column header."""
        btn = self.page.locator("button[wire\\:click=\"sortBy('conversation_opened')\"]")
        btn.click()
        self.page.wait_for_timeout(600)

    def sort_by_conversation_abandoned(self):
        """Click sort on Conversation Abandoned column header."""
        btn = self.page.locator("button[wire\\:click=\"sortBy('conversation_abandoned')\"]")
        btn.click()
        self.page.wait_for_timeout(600)

    def sort_by_conversation_closed(self):
        """Click sort on Conversation Closed column header."""
        btn = self.page.locator("button[wire\\:click=\"sortBy('conversation_closed')\"]")
        btn.click()
        self.page.wait_for_timeout(600)

    def get_active_sort_pill_text(self) -> str:
        """Get text of active sorting pill (e.g. 'Date: Z-A')."""
        if self.applied_sorting_pills.count() > 0 and self.applied_sorting_pills.first.is_visible():
            return self.applied_sorting_pills.first.inner_text().strip()
        return ""

    def clear_sorting(self):
        """Click Clear on applied sorting."""
        if self.clear_sorting_button.count() > 0 and self.clear_sorting_button.is_visible():
            self.clear_sorting_button.click()
            self.page.wait_for_timeout(600)

    # ─────────────────────────────────────────────────────────────────────────
    # Columns Visibility
    # ─────────────────────────────────────────────────────────────────────────

    def open_columns_dropdown(self):
        """Open the Columns visibility dropdown menu."""
        if not self.is_columns_dropdown_open():
            self.columns_button.click()
            self.columns_menu.wait_for(state="visible", timeout=5000)

    def close_columns_dropdown(self):
        """Close the Columns dropdown."""
        if self.is_columns_dropdown_open():
            self.columns_button.click()
            self.page.wait_for_timeout(300)

    def is_columns_dropdown_open(self) -> bool:
        """Check if Columns dropdown is visible."""
        return self.columns_menu.count() > 0 and self.columns_menu.is_visible()

    def is_column_visible(self, column_name: str) -> bool:
        """Check if a column header is currently visible in the table."""
        headers = self.get_column_headers()
        return any(column_name.lower() in h.lower() for h in headers)

    def toggle_column(self, column_key: str):
        """Toggle column checkbox by key (e.g., 'flow-name', 'date')."""
        self.open_columns_dropdown()
        chk = self.page.locator(f"input[wire\\:model\\.live='selectedColumns'][value='{column_key}']")
        chk.click()
        self.page.wait_for_timeout(600)
        self.close_columns_dropdown()

    def hide_column(self, column_key: str):
        """Hide a column if it is currently visible."""
        self.open_columns_dropdown()
        chk = self.page.locator(f"input[wire\\:model\\.live='selectedColumns'][value='{column_key}']")
        if chk.is_checked():
            chk.click()
            self.page.wait_for_timeout(600)
        self.close_columns_dropdown()

    def show_column(self, column_key: str):
        """Show a column if it is currently hidden."""
        self.open_columns_dropdown()
        chk = self.page.locator(f"input[wire\\:model\\.live='selectedColumns'][value='{column_key}']")
        if not chk.is_checked():
            chk.click()
            self.page.wait_for_timeout(600)
        self.close_columns_dropdown()

    def restore_all_columns(self):
        """Re-check All Columns or select all column checkboxes."""
        self.open_columns_dropdown()
        for k in COLUMN_KEYS.keys():
            chk = self.page.locator(f"input[wire\\:model\\.live='selectedColumns'][value='{k}']")
            if chk.count() > 0 and not chk.is_checked():
                chk.click()
                self.page.wait_for_timeout(200)
        self.close_columns_dropdown()

    # ─────────────────────────────────────────────────────────────────────────
    # Bulk Actions & Row Checkboxes
    # ─────────────────────────────────────────────────────────────────────────

    def click_header_checkbox(self):
        """Click the header bulk select-all checkbox."""
        self.header_checkbox.click()
        self.page.wait_for_timeout(300)

    def is_header_checkbox_checked(self) -> bool:
        """Check if header checkbox is checked."""
        return self.header_checkbox.is_checked()

    def click_row_checkbox(self, row_index: int):
        """Click row selection checkbox by 0-based index."""
        row = self.table_rows.nth(row_index)
        chk = row.locator("input[type='checkbox']")
        chk.click()
        self.page.wait_for_timeout(300)

    def is_row_checkbox_checked(self, row_index: int) -> bool:
        """Check if a specific row checkbox is checked."""
        row = self.table_rows.nth(row_index)
        chk = row.locator("input[type='checkbox']")
        return chk.is_checked()

    def open_bulk_actions(self):
        """Click Bulk Actions dropdown."""
        self.bulk_actions_button.click()
        self.page.wait_for_timeout(300)

    def is_export_xlsx_bulk_option_visible(self) -> bool:
        """Check if Export to XLSX option is visible inside Bulk Actions."""
        return self.export_xlsx_bulk_button.count() > 0 and self.export_xlsx_bulk_button.is_visible()

    def click_export_to_xlsx(self):
        """Click 'Export to XLSX' in Bulk Actions."""
        self.export_xlsx_bulk_button.click()

    # ─────────────────────────────────────────────────────────────────────────
    # UI Layout Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def is_table_horizontally_scrollable(self) -> bool:
        """Check if the table wrapper has horizontal scroll capability."""
        wrapper = self.page.locator("div[wire\\:key='bot_flow_summary_report-twrap']")
        if wrapper.count() > 0:
            return wrapper.evaluate("el => el.scrollWidth > el.clientWidth")
        return False

    def scroll_table_horizontally(self, offset: int = 200):
        """Scroll table horizontally."""
        wrapper = self.page.locator("div[wire\\:key='bot_flow_summary_report-twrap']")
        if wrapper.count() > 0:
            wrapper.evaluate(f"el => el.scrollLeft += {offset}")
            self.page.wait_for_timeout(200)
