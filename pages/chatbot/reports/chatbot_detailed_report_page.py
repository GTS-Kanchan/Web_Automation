"""
Page Object for Chatbot -> Reports -> Detailed (Chatbot Flow Detailed Report).
Page URL: /chatbot/reports/detailed
"""

import time
import re
from typing import List, Dict, Optional, Any
from playwright.sync_api import Page, Locator

from pages.common.base_page import BasePage
from utils.config import Config
from constants.chatbot_detailed_constants import (
    EXPECTED_PAGE_HEADING,
    EXPECTED_CHART_TITLE,
    EXPECTED_DETAILED_UI_HEADERS,
    ALL_DETAILED_COLUMNS,
    EXPECTED_BOT_TYPES,
    BOT_TYPE_VALUE_MAP,
    COLUMN_KEYS,
)


class ChatbotDetailedReportPage(BasePage):
    """
    Page Object Model for the Chatbot Flow Detailed Report.
    """

    PATH = "/chatbot/reports/detailed"

    def __init__(self, page: Page):
        super().__init__(page)

        # Heading & Section Titles
        self.heading = page.locator("h1:has-text('Chatbot Flow detailed Report')")
        self.chart_title = page.locator("h3:has-text('Total conversations by Date')")

        # Top Filters (Bot Type, From Date, To Date)
        self.bot_type_select = page.locator("#botType, select[wire\\:model\\.live='botType']")
        self.from_date_input = page.locator("input[wire\\:model\\.live='from_date']")
        self.to_date_input = page.locator("input[wire\\:model\\.live='to_date']")

        # Chart Controls & ApexChart Canvas
        self.refresh_button = page.locator("button[wire\\:click='refreshData']")
        self.bar_toggle_button = page.locator("button[wire\\:click=\"toggleChart1Type('bar')\"]")
        self.line_toggle_button = page.locator("button[wire\\:click=\"toggleChart1Type('line')\"]")
        self.chart_container = page.locator("#chart-day")
        self.chart_canvas = page.locator("#chart-day .apexcharts-canvas")
        self.chart_yaxis_title = page.locator("#chart-day .apexcharts-yaxis-title-text")
        self.chart_yaxis_labels = page.locator("#chart-day .apexcharts-yaxis-label")
        self.chart_xaxis_labels = page.locator("#chart-day .apexcharts-xaxis-label, #chart-day .apexcharts-xaxis-texts-g text")
        self.chart_bars = page.locator("#chart-day path.apexcharts-bar-area")
        self.chart_lines = page.locator("#chart-day path.apexcharts-line")

        # Table & Containers
        self.table = page.locator("table").last
        self.thead_headers = page.locator("table thead th")
        self.table_rows = page.locator("table tbody tr:not([wire\\:key*='bulk-select-message'])")

        # Search
        self.search_input = page.locator("input[wire\\:model\\.live='search'], input[placeholder*='Search' i]")

        # Columns Visibility Dropdown
        self.columns_button = page.locator("button:has-text('Columns')")
        self.columns_menu = page.locator("div[role='menu'][aria-labelledby='column-select-menu'], div[x-show*='open'], div.columns-dropdown")

        # Selection & Bulk Actions
        self.header_checkbox = page.locator("th input[type='checkbox']").first
        self.bulk_actions_button = page.locator("button:has-text('Bulk Actions'), [id*='bulkActionsDropdown']")
        self.bulk_actions_menu = page.locator("div[role='menu']:has(button), div:has(button[wire\\:click='export'])")

        # Pagination
        self.pagination_nav = page.locator("nav[role='navigation'], ul.pagination, div.pagination")
        self.prev_page_button = page.locator("button[rel='prev'], a[rel='prev'], button:has-text('Previous'), [aria-label*='Previous' i]")
        self.next_page_button = page.locator("button[rel='next'], a[rel='next'], button:has-text('Next'), [aria-label*='Next' i]")
        self.first_page_button = page.locator("button:has-text('First'), a:has-text('First'), button:has-text('1'), a:has-text('1')").first
        self.page_number_buttons = page.locator("button[wire\\:click*='gotoPage'], a[wire\\:click*='gotoPage'], nav[role='navigation'] button, nav[role='navigation'] a")
        self.results_count_text = page.locator("p.text-sm:has-text('Showing'), div:has-text('Showing')")

    # ─────────────────────────────────────────────────────────────────────────
    # Navigation
    # ─────────────────────────────────────────────────────────────────────────

    def navigate(self):
        """Navigate directly to Chatbot Flow Detailed Report page."""
        url = f"{Config.BASE_URL}{self.PATH}"
        self.page.goto(url)
        self.wait_for_page_load()

    def wait_for_page_load(self, timeout: int = 15000):
        """Wait for page heading and chart/controls to be visible."""
        self.heading.wait_for(state="visible", timeout=timeout)
        self.chart_title.wait_for(state="visible", timeout=timeout)
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(500)

    def is_detailed_report_page(self) -> bool:
        """Verify currently on Chatbot Flow Detailed Report page."""
        url_match = "/chatbot/reports/detailed" in self.page.url
        heading_visible = self.heading.count() > 0 and self.heading.is_visible()
        return url_match or heading_visible

    def get_heading_text(self) -> str:
        """Return the heading text."""
        if self.heading.is_visible():
            return self.heading.inner_text().strip()
        return ""

    # ─────────────────────────────────────────────────────────────────────────
    # Top Filters (Bot Type, Date Range)
    # ─────────────────────────────────────────────────────────────────────────

    def get_available_bot_types(self) -> List[str]:
        """Return list of text labels from Bot Type dropdown."""
        options = self.bot_type_select.locator("option")
        count = options.count()
        return [options.nth(i).inner_text().strip() for i in range(count)]

    def get_selected_bot_type(self) -> str:
        """Return selected option text from Bot Type dropdown."""
        val = self.bot_type_select.input_value()
        # Find matching option text
        option = self.bot_type_select.locator(f"option[value='{val}']")
        if option.count() > 0:
            return option.inner_text().strip()
        return val

    def select_bot_type(self, bot_type_name_or_val: str):
        """Select a Bot Type by name (e.g. 'Web', 'WhatsApp', 'All Types') or value."""
        # Find value from map or match text
        val = BOT_TYPE_VALUE_MAP.get(bot_type_name_or_val.lower())
        if val is not None:
            self.bot_type_select.select_option(value=val)
        else:
            try:
                self.bot_type_select.select_option(label=bot_type_name_or_val)
            except Exception:
                self.bot_type_select.select_option(value=bot_type_name_or_val)
        self.bot_type_select.dispatch_event("change")
        self.page.wait_for_timeout(800)

    def get_from_date(self) -> str:
        """Return From Date input value."""
        return self.from_date_input.input_value()

    def get_to_date(self) -> str:
        """Return To Date input value."""
        return self.to_date_input.input_value()

    def set_from_date(self, date_str: str):
        """Set From Date input and trigger change."""
        self.from_date_input.fill(date_str)
        self.from_date_input.dispatch_event("input")
        self.from_date_input.dispatch_event("change")
        self.page.wait_for_timeout(800)

    def set_to_date(self, date_str: str):
        """Set To Date input and trigger change."""
        self.to_date_input.fill(date_str)
        self.to_date_input.dispatch_event("input")
        self.to_date_input.dispatch_event("change")
        self.page.wait_for_timeout(800)

    def set_date_range(self, from_date: str, to_date: str):
        """Set both From and To dates."""
        self.set_from_date(from_date)
        self.set_to_date(to_date)
        self.page.wait_for_timeout(800)

    def get_from_date_max_attribute(self) -> Optional[str]:
        """Return max attribute of From Date input."""
        return self.from_date_input.get_attribute("max")

    def get_to_date_max_attribute(self) -> Optional[str]:
        """Return max attribute of To Date input."""
        return self.to_date_input.get_attribute("max")

    # ─────────────────────────────────────────────────────────────────────────
    # Chart Controls & ApexCharts
    # ─────────────────────────────────────────────────────────────────────────

    def get_chart_title_text(self) -> str:
        """Return chart section title text."""
        if self.chart_title.is_visible():
            return self.chart_title.inner_text().strip()
        return ""

    def is_chart_visible(self) -> bool:
        """Return True if ApexCharts canvas or container is visible."""
        return (
            (self.chart_container.count() > 0 and self.chart_container.is_visible())
            or (self.chart_canvas.count() > 0 and self.chart_canvas.is_visible())
        )

    def get_chart_yaxis_title_text(self) -> str:
        """Return text of chart Y-axis title."""
        if self.chart_yaxis_title.count() > 0:
            return self.chart_yaxis_title.first.inner_text().strip()
        return ""

    def get_chart_xaxis_labels(self) -> List[str]:
        """Return list of X-axis date labels from chart."""
        count = self.chart_xaxis_labels.count()
        labels = []
        for i in range(count):
            txt = self.chart_xaxis_labels.nth(i).inner_text().strip()
            if txt and txt not in labels:
                labels.append(txt)
        return labels

    def get_chart_bars_count(self) -> int:
        """Return count of bar elements in chart."""
        return self.chart_bars.count()

    def get_chart_bars_values(self) -> List[int]:
        """Return list of values extracted from chart bars attributes or data points."""
        values = []
        count = self.chart_bars.count()
        for i in range(count):
            val_attr = self.chart_bars.nth(i).get_attribute("val")
            if val_attr is not None:
                try:
                    values.append(int(float(val_attr)))
                except ValueError:
                    pass
        return values

    def get_active_chart_type(self) -> str:
        """Return currently active chart type: 'bar' or 'line'."""
        bar_classes = self.bar_toggle_button.get_attribute("class") or ""
        if "bg-primary-600" in bar_classes or "text-white" in bar_classes:
            return "bar"
        line_classes = self.line_toggle_button.get_attribute("class") or ""
        if "bg-primary-600" in line_classes or "text-white" in line_classes:
            return "line"
        return "bar"

    def select_bar_view(self):
        """Click Bar view toggle button."""
        self.bar_toggle_button.click()
        self.page.wait_for_timeout(600)

    def select_line_view(self):
        """Click Line view toggle button."""
        self.line_toggle_button.click()
        self.page.wait_for_timeout(600)

    def refresh_chart(self):
        """Click chart refresh button."""
        self.refresh_button.click()
        self.page.wait_for_timeout(800)

    def get_chart_total_sessions_count(self) -> int:
        """Calculate the total session count from chart bars or displayed total."""
        values = self.get_chart_bars_values()
        if values:
            return sum(values)
        # Fallback: check if total text is displayed below chart
        total_text_elem = self.page.locator("div:has-text('Total conversations'), div:has-text('Total sessions')")
        if total_text_elem.count() > 0:
            match = re.search(r'\d+', total_text_elem.first.inner_text())
            if match:
                return int(match.group())
        return 0

    # ─────────────────────────────────────────────────────────────────────────
    # Table & Records
    # ─────────────────────────────────────────────────────────────────────────

    def is_table_visible(self) -> bool:
        """Check if detailed table is visible."""
        return self.table.count() > 0 and self.table.is_visible()

    def get_column_headers(self) -> List[str]:
        """Return list of column header texts excluding the checkbox column."""
        headers = []
        count = self.thead_headers.count()
        for i in range(count):
            th = self.thead_headers.nth(i)
            # Skip checkbox header
            if th.locator("input[type='checkbox']").count() > 0:
                continue
            text = th.inner_text().strip()
            clean_text = text.split("\n")[0].strip()
            if clean_text:
                headers.append(clean_text)
        return headers

    def get_row_count(self) -> int:
        """Return count of visible data rows in table."""
        self.page.wait_for_timeout(300)
        return self.table_rows.count()

    def is_empty_state_displayed(self) -> bool:
        """Return True if table displays empty state or 0 rows."""
        if self.get_row_count() == 0:
            return True
        first_row_text = self.table_rows.first.inner_text()
        return (
            "No items found" in first_row_text
            or "No matching records" in first_row_text
            or "No records found" in first_row_text
            or "No data available" in first_row_text
        )

    def get_cell_value(self, row_index: int, column_name: str) -> str:
        """
        Get text of a cell by 0-based row index and column name.
        e.g., 'User Name', 'Mobile Number', 'Session ID', 'Bot Type', etc.
        """
        row = self.table_rows.nth(row_index)
        headers = self.get_column_headers()
        target_idx = -1
        for idx, h in enumerate(headers):
            if column_name.lower() in h.lower():
                target_idx = idx
                break

        if target_idx != -1:
            # Check for leading checkbox td (+1 if present)
            has_chk = row.locator("td input[type='checkbox']").count() > 0
            nth = target_idx + 2 if has_chk else target_idx + 1
            cell = row.locator(f"td:nth-child({nth})")
            if cell.count() > 0:
                return cell.inner_text().strip()

        return ""

    def get_column_values(self, column_name: str) -> List[str]:
        """Get all visible cell values for a given column name."""
        count = self.get_row_count()
        return [self.get_cell_value(i, column_name) for i in range(count)]

    def get_all_rows_data(self) -> List[Dict[str, str]]:
        """Get list of dictionaries representing all visible rows."""
        data = []
        count = self.get_row_count()
        headers = self.get_column_headers()
        for i in range(count):
            row_dict = {}
            for h in headers:
                row_dict[h] = self.get_cell_value(i, h)
            data.append(row_dict)
        return data

    # ─────────────────────────────────────────────────────────────────────────
    # Search Functionality
    # ─────────────────────────────────────────────────────────────────────────

    def search(self, query: str):
        """Type query into search input and wait for Livewire debounce."""
        self.search_input.fill(query)
        self.search_input.dispatch_event("input")
        self.page.wait_for_timeout(700)

    def clear_search(self):
        """Clear search input and wait for Livewire debounce."""
        self.search_input.fill("")
        self.search_input.dispatch_event("input")
        self.page.wait_for_timeout(700)

    def get_search_value(self) -> str:
        """Return current value of search input."""
        return self.search_input.input_value()

    # ─────────────────────────────────────────────────────────────────────────
    # Sorting
    # ─────────────────────────────────────────────────────────────────────────

    def sort_by_column(self, column_name: str):
        """Click on the sort button or header for a specific column."""
        # Check for button inside th matching column_name
        th = self.thead_headers.filter(has_text=re.compile(rf"^{column_name}", re.I))
        if th.count() > 0:
            sort_btn = th.locator("button")
            if sort_btn.count() > 0:
                sort_btn.first.click()
            else:
                th.first.click()
            self.page.wait_for_timeout(600)
            return

        # Fallback: find any sort button with wire:click containing column key
        key = column_name.lower().replace(" ", "_")
        btn = self.page.locator(f"button[wire\\:click*=\"sortBy('{key}')\"]")
        if btn.count() > 0:
            btn.click()
            self.page.wait_for_timeout(600)

    # ─────────────────────────────────────────────────────────────────────────
    # Columns Visibility
    # ─────────────────────────────────────────────────────────────────────────

    def open_columns_dropdown(self):
        """Open Columns visibility menu."""
        if not self.is_columns_dropdown_open():
            self.columns_button.click()
            self.page.wait_for_timeout(300)

    def close_columns_dropdown(self):
        """Close Columns visibility menu."""
        if self.is_columns_dropdown_open():
            self.columns_button.click()
            self.page.wait_for_timeout(300)

    def is_columns_dropdown_open(self) -> bool:
        """Check if Columns visibility menu is open."""
        return self.columns_menu.count() > 0 and self.columns_menu.is_visible()

    def is_column_visible(self, column_name: str) -> bool:
        """Check if column is currently visible in table headers."""
        headers = self.get_column_headers()
        return any(column_name.lower() in h.lower() for h in headers)

    def toggle_column(self, column_name: str):
        """Toggle column checkbox in Columns menu."""
        self.open_columns_dropdown()
        # Find checkbox by label or value
        chk = self.columns_menu.locator(f"label:has-text('{column_name}') input[type='checkbox']")
        if chk.count() == 0:
            chk = self.columns_menu.locator(f"input[type='checkbox'][value*='{column_name.lower().replace(' ', '-')}']")
        if chk.count() > 0:
            chk.first.click()
            self.page.wait_for_timeout(600)
        self.close_columns_dropdown()

    def hide_column(self, column_name: str):
        """Hide column if currently visible."""
        if self.is_column_visible(column_name):
            self.toggle_column(column_name)

    def show_column(self, column_name: str):
        """Show column if currently hidden."""
        if not self.is_column_visible(column_name):
            self.toggle_column(column_name)

    def restore_all_columns(self):
        """Ensure all columns are selected / visible."""
        self.open_columns_dropdown()
        chks = self.columns_menu.locator("input[type='checkbox']")
        count = chks.count()
        for i in range(count):
            chk = chks.nth(i)
            if not chk.is_checked():
                chk.click()
                self.page.wait_for_timeout(150)
        self.close_columns_dropdown()

    # ─────────────────────────────────────────────────────────────────────────
    # Selection & Bulk Actions
    # ─────────────────────────────────────────────────────────────────────────

    def click_header_checkbox(self):
        """Click header select-all checkbox."""
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

    def get_selected_rows_count(self) -> int:
        """Return count of checked row checkboxes."""
        count = 0
        total = self.get_row_count()
        for i in range(total):
            if self.is_row_checkbox_checked(i):
                count += 1
        return count

    def open_bulk_actions(self):
        """Click Bulk Actions dropdown."""
        if self.bulk_actions_button.count() > 0 and self.bulk_actions_button.is_visible():
            self.bulk_actions_button.click()
            self.page.wait_for_timeout(300)

    def is_bulk_actions_enabled(self) -> bool:
        """Check if Bulk Actions button is enabled (not disabled)."""
        if self.bulk_actions_button.count() > 0:
            return not self.bulk_actions_button.is_disabled()
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # Pagination
    # ─────────────────────────────────────────────────────────────────────────

    def is_pagination_visible(self) -> bool:
        """Check if pagination controls are visible."""
        return (
            (self.pagination_nav.count() > 0 and self.pagination_nav.is_visible())
            or (self.next_page_button.count() > 0 and self.next_page_button.is_visible())
            or (self.results_count_text.count() > 0 and self.results_count_text.is_visible())
        )

    def click_next_page(self):
        """Click Next page button."""
        if self.next_page_button.count() > 0 and self.next_page_button.is_visible():
            self.next_page_button.click()
            self.page.wait_for_timeout(700)

    def click_prev_page(self):
        """Click Previous page button."""
        if self.prev_page_button.count() > 0 and self.prev_page_button.is_visible():
            self.prev_page_button.click()
            self.page.wait_for_timeout(700)

    def click_first_page(self):
        """Click First / Page 1 button."""
        p1 = self.page.locator("button:has-text('1'), a:has-text('1')").first
        if p1.count() > 0 and p1.is_visible():
            p1.click()
            self.page.wait_for_timeout(700)

    def click_last_page(self):
        """Click Last page button if available."""
        # Find last numeric button in pagination
        btns = self.page.locator("nav[role='navigation'] button, ul.pagination button, ul.pagination a")
        count = btns.count()
        last_numeric = None
        for i in range(count):
            txt = btns.nth(i).inner_text().strip()
            if txt.isdigit():
                last_numeric = btns.nth(i)
        if last_numeric is not None:
            last_numeric.click()
            self.page.wait_for_timeout(700)

    def get_total_records_count(self) -> Optional[int]:
        """Parse total records count from results summary text (e.g. 'Showing 1 to 10 of 542 results')."""
        if self.results_count_text.count() > 0:
            text = self.results_count_text.first.inner_text().strip()
            # Match "of <N> results" or "of <N>"
            match = re.search(r'of\s+([0-9,]+)', text, re.I)
            if match:
                num_str = match.group(1).replace(",", "")
                return int(num_str)
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # Data & Security Helpers (Masking, Tenant Isolation)
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def is_masked_value(val: str) -> bool:
        """Check if a value contains asterisk or masking characters."""
        return "*" in val or "•" in val or "X" in val or "x" in val

    def get_all_session_ids(self) -> List[str]:
        """Get all visible session ID strings."""
        return [s for s in self.get_column_values("Session ID") if s]

    def are_session_ids_unique(self) -> bool:
        """Return True if all displayed session IDs are unique."""
        session_ids = self.get_all_session_ids()
        if not session_ids:
            return True
        return len(session_ids) == len(set(session_ids))
