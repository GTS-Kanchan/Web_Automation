"""pages/common/activities_page.py — Page Object Model for the Activities page (/activities).
"""

import time
from typing import Dict, List, Optional

from playwright.sync_api import Page, expect

from pages.common.base_page import BasePage
from utils.config import Config


class ActivitiesPage(BasePage):
    """Page Object for Activities log table and controls."""

    PATH = "/activities"

    # ── Navigation & Headings ──
    SIDEBAR_LINK = "a[href*='/activities']"
    PAGE_HEADING = "h1:has-text('Activities')"
    BREADCRUMB_NAV = "nav[aria-label='Breadcrumb']"

    # ── Table & Wrapper ──
    TABLE = "#table-activity_log"
    TABLE_BODY = "#activity_log-tbody"
    TABLE_ROWS = "#activity_log-tbody tr[rowpk]"
    HORIZONTAL_WRAPPER = "div[wire\\:key='activity_log-twrap']"

    # ── Search ──
    SEARCH_INPUT = "input[wire\\:model\\.live='search']"
    RESULT_COUNT = "p.paged-pagination-results, p.total-pagination-results"

    # ── View Details Modal ──
    VIEW_BUTTONS = "td[wire\\:key$='-action'] button"
    MODAL_CONTAINER = "#modal-container, div[x-show='show && showActiveComponent']"
    MODAL_CLOSE_BUTTON = "#modal-container button[aria-label='Close Modal'], button.dialog-button-close, #modal-container button:has-text('×')"

    # ── Filters (Slide-down) ──
    FILTERS_BUTTON = "button:has-text('Filters')"
    FILTERS_BADGE = "button:has-text('Filters') span"
    FILTERS_PANEL = "div[x-show='filtersOpen']"
    DATE_FILTER = "#activity_log-filter-date"
    EVENT_TYPE_FILTER = "#activity_log-filter-event_type"
    SUBJECT_FILTER = "#activity_log-filter-subject"

    # ── Applied Filter Pills ──
    FILTER_PILLS = "div[wire\\:key^='activity_log-filter-pill-']"
    DATE_FILTER_PILL = "div[wire\\:key='activity_log-filter-pill-date']"
    DATE_FILTER_PILL_REMOVE = "div[wire\\:key='activity_log-filter-pill-date'] button"
    CLEAR_FILTERS_BUTTON = "button[x-on\\:click\\.prevent='resetAllFilters']"

    # ── Sorting ──
    SORT_EVENT_BUTTON = "button[wire\\:click=\"sortBy('event')\"]"
    SORT_SUBJECT_BUTTON = "button[wire\\:click=\"sortBy('subject_type')\"]"
    SORT_CREATED_AT_BUTTON = "button[wire\\:click=\"sortBy('created_at')\"]"
    SORTING_PILL = "span[wire\\:key^='activity_log-sorting-pill-']"
    CLEAR_SORTS_BUTTON = "button[wire\\:click\\.prevent='clearSorts']"

    # ── Columns Dropdown ──
    COLUMNS_BUTTON = "div[wire\\:key='activity_log-column-select-button'] button"
    ALL_COLUMNS_CHECKBOX = "input[wire\\:click='deselectAllColumns']"
    COLUMN_CHECKBOX_TEMPLATE = "input[wire\\:model\\.live='selectedColumns'][value='{col_key}']"

    # ── Export to XLSX ──
    EXPORT_BUTTON = "button:has-text('Export to XLSX')"
    EXPORT_MODAL = "div[x-show='showModal']"
    EXPORT_CONFIRM_BUTTON = "button[wire\\:click='exportAll'], button:has-text('Yes, Export')"
    EXPORT_CANCEL_BUTTON = "button:has-text('No')"

    COLUMNS = [
        "action",
        "user",
        "event",
        "subject",
        "created-at",
    ]

    def __init__(self, page: Page):
        super().__init__(page)

    # ══════════════════════════════════════════════════════════════════════════
    # Navigation & Verification
    # ══════════════════════════════════════════════════════════════════════════

    def navigate(self):
        """Directly navigate to /activities."""
        self.open(self.PATH)
        self.wait_for_table_load()

    def navigate_via_sidebar(self):
        """Click the Activities link in the sidebar."""
        link = self.page.locator(self.SIDEBAR_LINK).first
        link.wait_for(state="visible", timeout=10000)
        link.click()
        self.wait_for_table_load()

    def is_activities_page(self) -> bool:
        """Check if current URL contains /activities."""
        return "/activities" in self.get_current_url()

    def get_heading_text(self) -> str:
        """Get the h1 heading text."""
        heading = self.page.locator(self.PAGE_HEADING).first
        heading.wait_for(state="visible", timeout=10000)
        return heading.inner_text().strip()

    def get_breadcrumb_text(self) -> str:
        """Get the full breadcrumb text."""
        bc = self.page.locator(self.BREADCRUMB_NAV).first
        bc.wait_for(state="visible", timeout=10000)
        return bc.inner_text().strip()

    def wait_for_table_load(self, timeout: int = 15000):
        """Wait for the activity table to be present and Livewire to settle."""
        self.page.wait_for_selector(self.TABLE, state="visible", timeout=timeout)
        self.wait_for_livewire(timeout=timeout)

    def wait_for_livewire(self, timeout: int = 10000):
        """Wait until Livewire background updates settle."""
        try:
            self.page.wait_for_function(
                "() => !window.Livewire || !window.Livewire.all().some(c => c.el && c.el.hasAttribute('wire:loading'))",
                timeout=timeout,
            )
        except Exception:
            pass
        self.page.wait_for_timeout(400)

    # ══════════════════════════════════════════════════════════════════════════
    # Table Inspection
    # ══════════════════════════════════════════════════════════════════════════

    def get_column_headers(self) -> List[str]:
        """Return list of visible column header texts in order."""
        ths = self.page.locator(f"{self.TABLE} thead tr th")
        headers = []
        for i in range(ths.count()):
            text = ths.nth(i).inner_text().strip()
            # Clean up multi-line or sort arrows
            cleaned = text.split("\n")[0].strip()
            if cleaned:
                headers.append(cleaned)
        return headers

    def get_row_count(self) -> int:
        """Return the number of data rows in table body."""
        return self.page.locator(self.TABLE_ROWS).count()

    def get_cell_value(self, row_index: int, col_name: str) -> str:
        """Get text value of a specific cell by row index and column name."""
        norm = col_name.lower().replace("_", "-")
        cell_locator = f"td[wire\\:key$='-{norm}']"
        row = self.page.locator(self.TABLE_ROWS).nth(row_index)
        cell = row.locator(cell_locator)
        if cell.count() > 0:
            return cell.first.inner_text().strip()
        # Fallback by column position
        if norm in self.COLUMNS:
            idx = self.COLUMNS.index(norm)
            tds = row.locator("td")
            if tds.count() > idx:
                return tds.nth(idx).inner_text().strip()
        return ""

    def get_column_values(self, col_name: str) -> List[str]:
        """Return list of values for a column across all visible rows."""
        count = self.get_row_count()
        return [self.get_cell_value(i, col_name) for i in range(count)]

    def get_all_rows_data(self) -> List[Dict[str, str]]:
        """Return list of dictionaries with all column data for visible rows."""
        count = self.get_row_count()
        data = []
        for i in range(count):
            row_dict = {}
            for col in self.COLUMNS:
                row_dict[col] = self.get_cell_value(i, col)
            data.append(row_dict)
        return data

    def get_result_count_text(self) -> str:
        """Return result count string (e.g. 'Showing 1 to 1')."""
        loc = self.page.locator(self.RESULT_COUNT)
        if loc.count() > 0:
            return loc.first.inner_text().strip()
        return ""

    # ══════════════════════════════════════════════════════════════════════════
    # View Details Action
    # ══════════════════════════════════════════════════════════════════════════

    def has_view_button(self, row_index: int) -> bool:
        """Check if View button is visible in specified row."""
        row = self.page.locator(self.TABLE_ROWS).nth(row_index)
        btn = row.locator("td[wire\\:key$='-action'] button")
        return btn.is_visible()

    def click_view_button(self, row_index: int):
        """Click the View icon button on specified row."""
        row = self.page.locator(self.TABLE_ROWS).nth(row_index)
        btn = row.locator("td[wire\\:key$='-action'] button").first
        btn.click()
        self.page.wait_for_timeout(500)

    def is_modal_open(self) -> bool:
        """Check if details modal is open."""
        modal = self.page.locator(self.MODAL_CONTAINER).first
        return modal.is_visible()

    def get_modal_text(self) -> str:
        """Get the text content inside the details modal."""
        modal = self.page.locator(self.MODAL_CONTAINER).first
        if modal.is_visible():
            return modal.inner_text().strip()
        return ""

    def close_modal(self):
        """Close the open details modal."""
        close_btn = self.page.locator(self.MODAL_CLOSE_BUTTON)
        if close_btn.count() > 0 and close_btn.first.is_visible():
            close_btn.first.click()
        else:
            self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(400)

    # ══════════════════════════════════════════════════════════════════════════
    # Search
    # ══════════════════════════════════════════════════════════════════════════

    def search(self, query: str):
        """Type search query into Search input and wait for results."""
        inp = self.page.locator(self.SEARCH_INPUT).first
        inp.fill(query)
        self.wait_for_livewire()

    def clear_search(self):
        """Clear search input."""
        inp = self.page.locator(self.SEARCH_INPUT).first
        inp.fill("")
        self.wait_for_livewire()

    def get_search_value(self) -> str:
        """Get currently typed search value."""
        inp = self.page.locator(self.SEARCH_INPUT).first
        return inp.input_value()

    # ══════════════════════════════════════════════════════════════════════════
    # Filters
    # ══════════════════════════════════════════════════════════════════════════

    def is_filters_open(self) -> bool:
        """Check if slide-down filters panel is open."""
        panel = self.page.locator(self.FILTERS_PANEL)
        return panel.is_visible()

    def open_filters(self):
        """Open slide-down filters panel if not open."""
        if not self.is_filters_open():
            self.page.locator(self.FILTERS_BUTTON).first.click()
            self.page.wait_for_selector(self.FILTERS_PANEL, state="visible", timeout=5000)
            self.page.wait_for_timeout(300)

    def close_filters(self):
        """Close slide-down filters panel if open."""
        if self.is_filters_open():
            self.page.locator(self.FILTERS_BUTTON).first.click()
            self.page.wait_for_timeout(300)

    def get_filter_count_badge(self) -> int:
        """Get the integer badge count on the Filters button, or 0 if none."""
        badge = self.page.locator(self.FILTERS_BADGE)
        if badge.is_visible():
            txt = badge.inner_text().strip()
            try:
                return int(txt)
            except ValueError:
                return 0
        return 0

    def get_date_filter_value(self) -> str:
        """Get value of Date filter input (YYYY-MM-DD)."""
        self.open_filters()
        val = self.page.locator(self.DATE_FILTER).input_value()
        return val

    def set_date_filter(self, date_str: str):
        """Set Date filter (format: YYYY-MM-DD)."""
        self.open_filters()
        inp = self.page.locator(self.DATE_FILTER)
        inp.fill(date_str)
        # Trigger change event for Alpine / Livewire
        inp.dispatch_event("change")
        self.wait_for_livewire()

    def get_event_type_options(self) -> List[str]:
        """Return option texts from Event Type select."""
        self.open_filters()
        select = self.page.locator(self.EVENT_TYPE_FILTER)
        options = select.locator("option")
        return [options.nth(i).inner_text().strip() for i in range(options.count())]

    def get_selected_event_type(self) -> str:
        """Get selected Event Type text."""
        self.open_filters()
        select = self.page.locator(self.EVENT_TYPE_FILTER)
        val = select.input_value()
        opt = select.locator(f"option[value='{val}']")
        if opt.count() > 0:
            return opt.first.inner_text().strip()
        return ""

    def select_event_type(self, event_text_or_val: str):
        """Select Event Type option."""
        self.open_filters()
        select = self.page.locator(self.EVENT_TYPE_FILTER)
        try:
            select.select_option(label=event_text_or_val)
        except Exception:
            select.select_option(value=event_text_or_val)
        self.wait_for_livewire()

    def get_subject_options(self) -> List[str]:
        """Return option texts from Subject select."""
        self.open_filters()
        select = self.page.locator(self.SUBJECT_FILTER)
        options = select.locator("option")
        return [options.nth(i).inner_text().strip() for i in range(options.count())]

    def get_selected_subject(self) -> str:
        """Get selected Subject text."""
        self.open_filters()
        select = self.page.locator(self.SUBJECT_FILTER)
        val = select.input_value()
        opt = select.locator(f"option[value='{val}']")
        if opt.count() > 0:
            return opt.first.inner_text().strip()
        return ""

    def select_subject(self, subject_text_or_val: str):
        """Select Subject option."""
        self.open_filters()
        select = self.page.locator(self.SUBJECT_FILTER)
        try:
            select.select_option(label=subject_text_or_val)
        except Exception:
            select.select_option(value=subject_text_or_val)
        self.wait_for_livewire()

    def is_date_filter_pill_displayed(self) -> bool:
        """Check if Date filter pill is visible."""
        return self.page.locator(self.DATE_FILTER_PILL).is_visible()

    def remove_date_filter_pill(self):
        """Click remove button on Date filter pill."""
        btn = self.page.locator(self.DATE_FILTER_PILL_REMOVE).first
        if btn.is_visible():
            btn.click()
            self.wait_for_livewire()

    def clear_all_filters(self):
        """Click 'Clear' button to remove all applied filters."""
        btn = self.page.locator(self.CLEAR_FILTERS_BUTTON).first
        if btn.is_visible():
            btn.click()
            self.wait_for_livewire()

    def get_applied_filter_pill_texts(self) -> List[str]:
        """Return list of texts from visible applied filter pills."""
        pills = self.page.locator(self.FILTER_PILLS)
        texts = []
        for i in range(pills.count()):
            if pills.nth(i).is_visible():
                texts.append(pills.nth(i).inner_text().strip())
        return texts

    # ══════════════════════════════════════════════════════════════════════════
    # Sorting
    # ══════════════════════════════════════════════════════════════════════════

    def sort_by_event(self):
        """Click sort button on Event column."""
        self.page.locator(self.SORT_EVENT_BUTTON).first.click()
        self.wait_for_livewire()

    def sort_by_subject(self):
        """Click sort button on Subject column."""
        self.page.locator(self.SORT_SUBJECT_BUTTON).first.click()
        self.wait_for_livewire()

    def sort_by_created_at(self):
        """Click sort button on Created at column."""
        self.page.locator(self.SORT_CREATED_AT_BUTTON).first.click()
        self.wait_for_livewire()

    def get_sorting_pill_text(self) -> str:
        """Get text of active sorting pill (e.g. 'Created at: Z-A')."""
        pill = self.page.locator(self.SORTING_PILL)
        if pill.is_visible():
            return pill.inner_text().strip()
        return ""

    def clear_sorting(self):
        """Click Clear button for applied sorting."""
        btn = self.page.locator(self.CLEAR_SORTS_BUTTON).first
        if btn.is_visible():
            btn.click()
            self.wait_for_livewire()

    # ══════════════════════════════════════════════════════════════════════════
    # Columns Select
    # ══════════════════════════════════════════════════════════════════════════

    def open_columns_dropdown(self):
        """Open Columns dropdown."""
        btn = self.page.locator(self.COLUMNS_BUTTON).first
        btn.click()
        self.page.wait_for_timeout(300)

    def is_columns_dropdown_open(self) -> bool:
        """Check if Columns dropdown menu is open."""
        return self.page.locator("div[role='menu'][aria-labelledby='column-select-menu']").is_visible()

    def toggle_column(self, col_key: str):
        """Toggle column checkbox by column key (e.g. 'user', 'event', 'subject', 'created-at')."""
        if not self.is_columns_dropdown_open():
            self.open_columns_dropdown()
        cb = self.page.locator(f"input[wire\\:model\\.live='selectedColumns'][value='{col_key}']").first
        cb.click()
        self.wait_for_livewire()

    def select_all_columns(self):
        """Check 'All Columns' checkbox."""
        if not self.is_columns_dropdown_open():
            self.open_columns_dropdown()
        cb = self.page.locator(self.ALL_COLUMNS_CHECKBOX).first
        if not cb.is_checked():
            cb.click()
            self.wait_for_livewire()

    # ══════════════════════════════════════════════════════════════════════════
    # Export to XLSX
    # ══════════════════════════════════════════════════════════════════════════

    def is_export_button_visible(self) -> bool:
        """Check if 'Export to XLSX' button is visible."""
        return self.page.locator(self.EXPORT_BUTTON).first.is_visible()

    def click_export_button(self):
        """Click 'Export to XLSX' to open confirm modal."""
        self.page.locator(self.EXPORT_BUTTON).first.click()
        self.page.wait_for_selector(self.EXPORT_MODAL, state="visible", timeout=5000)

    def is_export_modal_open(self) -> bool:
        """Check if Export confirm modal is open."""
        return self.page.locator(self.EXPORT_MODAL).is_visible()

    def confirm_export(self):
        """Click 'Yes, Export' inside modal."""
        self.page.locator(self.EXPORT_CONFIRM_BUTTON).first.click()
        self.wait_for_livewire()

    def cancel_export(self):
        """Click 'No' inside modal."""
        self.page.locator(self.EXPORT_CANCEL_BUTTON).first.click()
        self.page.wait_for_timeout(300)

    def trigger_export_and_download(self):
        """Handle full export flow and wait for download if triggered."""
        self.click_export_button()
        try:
            with self.page.expect_download(timeout=10000) as download_info:
                self.confirm_export()
            return download_info.value
        except Exception:
            # Livewire polling or direct download handler
            return None
