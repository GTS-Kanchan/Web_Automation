"""pages/common/documents_page.py — Page Object Model for the Documents page.
URL: /documents
"""
import os
import re
import time
from typing import List, Optional, Dict, Any

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from pages.common.base_page import BasePage
from constants.document_ui_headers import (
    EXPECTED_DOCUMENT_UI_HEADERS,
    ALL_DOCUMENT_COLUMNS,
    KNOWN_DEFAULT_DOCUMENTS,
)


class DocumentsPage(BasePage):
    DOCUMENTS_URL = "/documents"
    TABLE_NAME = "table"

    COLUMN_INDEX = {
        "actions": 0,
        "action": 0,
        "name": 1,
        "created_at": 2,
        "created-at": 2,
    }

    # ── Page Header & Navigation ─────────────────────────────────────────────
    BREADCRUMB = "xpath=//nav[@aria-label='Breadcrumb']"
    NAV_DOCUMENTS = (
        "xpath=//aside//a[contains(@href,'/documents') and contains(.,'Documents')]"
        " | //nav//a[contains(@href,'/documents')]"
    )

    # ── Table & Structure ────────────────────────────────────────────────────
    TABLE = "#table-table, table"
    TABLE_HEADERS = "#table-table thead th, table thead th"
    TABLE_ROWS = "#table-table tbody tr, table tbody tr"
    RESULTS_COUNT = (
        "xpath=//*[contains(@class,'total-pagination-results')]"
        " | //*[contains(text(),'Showing') and contains(text(),'result')]"
    )
    NO_RECORDS_MSG = (
        "xpath=//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no items found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no record') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no data') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no result') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'not found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'nothing found')]"
    )

    # ── Search ───────────────────────────────────────────────────────────────
    SEARCH_INPUT = "input[placeholder='Search By Name'], input[wire\\:model\\.live='search']"

    # ── Filters (Popover Layout) ─────────────────────────────────────────────
    BTN_FILTERS = "xpath=//button[contains(.,'Filters') and not(ancestor::table)]"
    FILTER_POPOVER = (
        "xpath=//div[@role='menu' and contains(@aria-labelledby,'filters-menu')]"
        " | div[x-show='filterPopoverOpen']"
    )
    FILTER_CREATED_FROM = "#table-filter-created_from"
    FILTER_CREATED_TO = "#table-filter-created_to"

    # ── Filter Pills & Clear ─────────────────────────────────────────────────
    FILTER_PILLS = "xpath=//div[contains(@wire:key,'table-filter-pill-')]"
    FILTER_PILL_FROM = "xpath=//div[contains(@wire:key,'table-filter-pill-created_from')]"
    FILTER_PILL_TO = "xpath=//div[contains(@wire:key,'table-filter-pill-created_to')]"
    BTN_REMOVE_PILL_FROM = "xpath=//div[contains(@wire:key,'table-filter-pill-created_from')]//button"
    BTN_REMOVE_PILL_TO = "xpath=//div[contains(@wire:key,'table-filter-pill-created_to')]//button"
    BTN_CLEAR_ALL_FILTERS = (
        "xpath=//button[contains(@x-on:click,'resetAllFilters')]"
        " | //small[contains(text(),'Applied Filters')]/following::button[contains(.,'Clear')][1]"
    )

    # ── Sorting ──────────────────────────────────────────────────────────────
    SORT_PILL_CREATED_AT = "xpath=//span[contains(@wire:key,'table-sorting-pill-created_at')]"
    SORT_PILL_NAME = "xpath=//span[contains(@wire:key,'table-sorting-pill-name')]"
    BTN_CLEAR_ALL_SORTS = (
        "xpath=//button[contains(@wire:click,'clearSorts')]"
        " | //small[contains(text(),'Applied Sorting')]/following::button[contains(.,'Clear')][1]"
    )
    BTN_CLEAR_SORT_CREATED_AT = "xpath=//span[contains(@wire:key,'table-sorting-pill-created_at')]//button"

    SORT_BTN_NAME = "xpath=//th[contains(.,'Name')]//button | //button[contains(@wire:click,\"sortBy('name')\")]"
    SORT_BTN_CREATED_AT = (
        "xpath=//th[contains(.,'Created At')]//button"
        " | //button[contains(@wire:click,\"sortBy('created_at')\")]"
    )

    # ── Columns Dropdown ─────────────────────────────────────────────────────
    BTN_COLUMNS = "xpath=//button[contains(.,'Columns') and not(ancestor::table)]"
    COLUMNS_DROPDOWN_MENU = (
        "xpath=//div[@role='menu' and contains(@aria-labelledby,'column-select-menu')]"
        " | //div[contains(@class,'ring-opacity-5') and .//input[@value='name']]"
    )
    CHECKBOX_ALL_COLUMNS = "xpath=//div[contains(@wire:key,'columnSelect-selectAll')]//input[@type='checkbox']"

    # ── Row View Action ──────────────────────────────────────────────────────
    ROW_VIEW_BTN = (
        "xpath=.//a[contains(@href,'download') and (contains(normalize-space(.),'View') or contains(@class,'bg-blue-600'))]"
        " | .//button[contains(normalize-space(.),'View')]"
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ─────────────────────────────────────────────────────────────────────────
    # Navigation & Page State
    # ─────────────────────────────────────────────────────────────────────────

    def navigate(self) -> "DocumentsPage":
        self.open(self.DOCUMENTS_URL)
        self.page.wait_for_timeout(1500)
        return self

    def navigate_via_sidebar(self) -> "DocumentsPage":
        nav_link = self.page.locator(self.NAV_DOCUMENTS).first
        if nav_link.is_visible():
            nav_link.click()
            self.page.wait_for_timeout(1500)
        else:
            self.navigate()
        return self

    def is_documents_page(self) -> bool:
        url = self.get_current_url()
        return "/documents" in url and "login" not in url.lower()

    def get_breadcrumb_text(self) -> str:
        el = self.page.locator(self.BREADCRUMB).first
        if el.is_visible():
            return el.inner_text().strip()
        return ""

    def wait_for_table_load(self, timeout: int = 15000):
        try:
            self.page.locator(self.TABLE).first.wait_for(state="attached", timeout=timeout)
        except Exception:
            pass
        self.page.wait_for_timeout(600)

    # ─────────────────────────────────────────────────────────────────────────
    # Table Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def get_table_headers(self) -> List[str]:
        return self._get_headers_safe(self.TABLE_HEADERS)

    def is_column_visible(self, column_name: str) -> bool:
        headers = self.get_table_headers()
        lowered = [h.lower() for h in headers]
        return any(column_name.lower() in h for h in lowered)

    def get_row_count(self) -> int:
        """Count rows that contain genuine document data."""
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            count = 0
            for i in range(rows.count()):
                txt = rows.nth(i).inner_text().strip()
                if txt and "no " not in txt.lower():
                    count += 1
            return count
        except Exception:
            return 0

    def is_no_records_visible(self) -> bool:
        return self.h.is_element_present(self.NO_RECORDS_MSG, timeout=3000)

    def get_result_count_text(self) -> str:
        el = self.page.locator(self.RESULTS_COUNT).first
        return el.inner_text().strip() if el.is_visible() else ""

    def get_all_document_names(self) -> List[str]:
        return self.get_all_column_values("name")

    def get_cell_text(self, row_idx: int, col_idx_or_name) -> str:
        if isinstance(col_idx_or_name, str):
            col_idx = self.COLUMN_INDEX.get(col_idx_or_name.lower().replace(" ", "-"), 1)
        else:
            col_idx = col_idx_or_name

        try:
            rows = self.page.locator(self.TABLE_ROWS)
            if row_idx >= rows.count():
                return ""
            cells = rows.nth(row_idx).locator("td")
            if col_idx >= cells.count():
                return ""
            return cells.nth(col_idx).inner_text().strip()
        except Exception:
            return ""

    def get_all_column_values(self, col_idx_or_name) -> List[str]:
        if isinstance(col_idx_or_name, str):
            col_idx = self.COLUMN_INDEX.get(col_idx_or_name.lower().replace(" ", "-"), 1)
        else:
            col_idx = col_idx_or_name

        values = []
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            for i in range(rows.count()):
                row = rows.nth(i)
                txt = row.inner_text().strip()
                if not txt or "no " in txt.lower():
                    continue
                cells = row.locator("td")
                if col_idx < cells.count():
                    values.append(cells.nth(col_idx).inner_text().strip())
        except Exception:
            pass
        return values

    # ─────────────────────────────────────────────────────────────────────────
    # View Action
    # ─────────────────────────────────────────────────────────────────────────

    def get_view_link_for_row(self, row_idx: int = 0):
        rows = self.page.locator(self.TABLE_ROWS)
        if rows.count() > row_idx:
            row = rows.nth(row_idx)
            return row.locator("td").first.locator("a, button").first
        return None

    def get_view_url(self, row_idx: int = 0) -> str:
        link = self.get_view_link_for_row(row_idx)
        if link and link.is_visible():
            return link.get_attribute("href") or ""
        return ""

    def get_view_url_by_name(self, doc_name: str) -> str:
        rows = self.page.locator(self.TABLE_ROWS)
        for i in range(rows.count()):
            row = rows.nth(i)
            if doc_name.lower() in row.inner_text().lower():
                link = row.locator("td").first.locator("a, button").first
                if link.is_visible():
                    return link.get_attribute("href") or ""
        return ""

    def click_view(self, row_idx_or_name=0):
        """Click View and handle the opened popup or return the target href."""
        if isinstance(row_idx_or_name, str):
            rows = self.page.locator(self.TABLE_ROWS)
            target_row = None
            for i in range(rows.count()):
                if row_idx_or_name.lower() in rows.nth(i).inner_text().lower():
                    target_row = rows.nth(i)
                    break
            if target_row:
                link = target_row.locator("td").first.locator("a, button").first
            else:
                return None, ""
        else:
            link = self.get_view_link_for_row(row_idx_or_name)

        if not link or not link.is_visible():
            return None, ""

        href = link.get_attribute("href") or ""
        popup = None
        try:
            with self.page.expect_popup(timeout=8000) as popup_info:
                link.click()
            popup = popup_info.value
            popup.wait_for_load_state("domcontentloaded")
        except Exception:
            pass

        return popup, href

    # ─────────────────────────────────────────────────────────────────────────
    # Search
    # ─────────────────────────────────────────────────────────────────────────

    def search(self, query: str):
        inp = self.h.wait_for_element_visible(self.SEARCH_INPUT, timeout=8000)
        inp.fill(query)
        self.page.wait_for_timeout(1500)  # Livewire live debounce

    def clear_search(self):
        inp = self.page.locator(self.SEARCH_INPUT).first
        if inp.is_visible():
            inp.fill("")
            self.page.wait_for_timeout(1500)

    def get_search_value(self) -> str:
        inp = self.page.locator(self.SEARCH_INPUT).first
        return inp.input_value() if inp.is_visible() else ""

    # ─────────────────────────────────────────────────────────────────────────
    # Filters
    # ─────────────────────────────────────────────────────────────────────────

    def click_filters_button(self):
        btn = self.h.wait_for_element_clickable(self.BTN_FILTERS, timeout=8000)
        btn.click()
        self.page.wait_for_timeout(500)

    def is_filters_popover_open(self) -> bool:
        popover = self.page.locator(self.FILTER_POPOVER).first
        return popover.is_visible()

    def open_filters_popover(self):
        if not self.is_filters_popover_open():
            self.click_filters_button()

    def close_filters_popover(self):
        if self.is_filters_popover_open():
            self.click_filters_button()

    def set_created_from(self, date_str: str):
        self.open_filters_popover()
        inp = self.page.locator(self.FILTER_CREATED_FROM).first
        inp.fill(date_str)
        inp.dispatch_event("change")
        self.page.wait_for_timeout(1200)

    def set_created_to(self, date_str: str):
        self.open_filters_popover()
        inp = self.page.locator(self.FILTER_CREATED_TO).first
        inp.fill(date_str)
        inp.dispatch_event("change")
        self.page.wait_for_timeout(1200)

    def get_applied_filter_chips(self) -> List[str]:
        pills = self.page.locator(self.FILTER_PILLS)
        results = []
        for i in range(pills.count()):
            txt = pills.nth(i).inner_text().strip()
            if txt:
                results.append(txt)
        return results

    def remove_filter_chip(self, filter_name: str = "created_from"):
        if "from" in filter_name.lower():
            btn = self.page.locator(self.BTN_REMOVE_PILL_FROM).first
        else:
            btn = self.page.locator(self.BTN_REMOVE_PILL_TO).first
        if btn.is_visible():
            btn.click()
            self.page.wait_for_timeout(1200)

    def clear_all_filters(self):
        btn = self.page.locator(self.BTN_CLEAR_ALL_FILTERS).first
        if btn.is_visible():
            btn.click()
            self.page.wait_for_timeout(1200)

    # ─────────────────────────────────────────────────────────────────────────
    # Sorting
    # ─────────────────────────────────────────────────────────────────────────

    def get_applied_sort_text(self) -> str:
        pill = self.page.locator(self.SORT_PILL_CREATED_AT).first
        if pill.is_visible():
            return pill.inner_text().strip()
        name_pill = self.page.locator(self.SORT_PILL_NAME).first
        if name_pill.is_visible():
            return name_pill.inner_text().strip()
        any_pill = self.page.locator("xpath=//span[contains(@wire:key,'table-sorting-pill-')]").first
        return any_pill.inner_text().strip() if any_pill.is_visible() else ""

    def click_sort_name(self):
        btn = self.page.locator(self.SORT_BTN_NAME).first
        if btn.is_visible():
            btn.click()
            self.page.wait_for_timeout(1200)

    def click_sort_created_at(self):
        btn = self.page.locator(self.SORT_BTN_CREATED_AT).first
        if btn.is_visible():
            btn.click()
            self.page.wait_for_timeout(1200)

    def clear_sorting(self):
        btn = self.page.locator(self.BTN_CLEAR_ALL_SORTS).first
        if btn.is_visible():
            btn.click()
            self.page.wait_for_timeout(1200)

    # ─────────────────────────────────────────────────────────────────────────
    # Columns Menu
    # ─────────────────────────────────────────────────────────────────────────

    def click_columns_button(self):
        btn = self.h.wait_for_element_clickable(self.BTN_COLUMNS, timeout=8000)
        btn.click()
        self.page.wait_for_timeout(500)

    def is_columns_menu_open(self) -> bool:
        menu = self.page.locator(self.COLUMNS_DROPDOWN_MENU).first
        return menu.is_visible()

    def toggle_column(self, col_value: str, select: Optional[bool] = None):
        if not self.is_columns_menu_open():
            self.click_columns_button()
        cb = self.page.locator(f"xpath=//input[@type='checkbox' and @value='{col_value}']").first
        if cb.is_visible():
            current = cb.is_checked()
            if select is None or select != current:
                cb.click()
                self.page.wait_for_timeout(1000)

    def select_all_columns(self):
        if not self.is_columns_menu_open():
            self.click_columns_button()
        cb = self.page.locator(self.CHECKBOX_ALL_COLUMNS).first
        if cb.is_visible():
            cb.click()
            self.page.wait_for_timeout(1000)
