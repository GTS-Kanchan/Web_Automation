"""pages/email/email_messages_page.py — Page Object Model for the Email Messages page.
URL: /campaigns/email/messages
"""
import os
import time
import csv
from typing import List, Dict, Optional

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR
from constants.email_message_ui_headers import (
    EXPECTED_EMAIL_MESSAGE_UI_HEADERS,
    ALL_EMAIL_MESSAGE_COLUMNS,
)


class EmailMessagesPage(BasePage):
    MESSAGES_URL = "/campaigns/email/messages"
    CHANNELS_URL = "/channels"
    TABLE_NAME = "email_messages"

    # Confirmed default visible column index mapping
    COLUMN_INDEX = {
        "action": 0,
        "to-email-address": 1,
        "to_email_address": 1,
        "source": 2,
        "units": 3,
        "units-to-cc-bcc": 3,
        "status": 4,
        "sent-at": 5,
        "sent_at": 5,
        "delivered-at": 6,
        "delivered_at": 6,
        "opened-at": 7,
        "opened_at": 7,
        "clicked-at": 8,
        "clicked_at": 8,
        "bounced-at": 9,
        "bounced_at": 9,
        "failed-at": 10,
        "failed_at": 10,
        "created-at": 11,
        "created_at": 11,
    }

    # ── Page Header & Navigation ─────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'Email Messages')]"
    BREADCRUMB = "xpath=//nav[@aria-label='Breadcrumb']"
    NAV_CHANNELS = "xpath=//aside//a[contains(@href,'/channels')] | //header//a[contains(@href,'/channels')]"
    TAB_MESSAGES = "xpath=//a[contains(@href,'/campaigns/email/messages') and contains(.,'Messages')]"
    REFRESH_BTN = "xpath=//a[contains(@href,'/campaigns/email/messages') and contains(normalize-space(.),'Refresh')]"

    # ── Search ───────────────────────────────────────────────────────────────
    SEARCH_INPUT = "input[placeholder='Search by email'], input[wire\\:model\\.live='search']"

    # ── Filters Panel ────────────────────────────────────────────────────────
    BTN_FILTERS = "xpath=//button[contains(.,'Filters') and not(ancestor::table)]"
    FILTER_COUNT_BADGE = "xpath=//button[contains(.,'Filters')]//span[contains(@class,'rounded-full')]"
    FILTERS_PANEL = "div[x-show='filtersOpen']"

    FILTER_CREATED_FROM_WRAPPER = "#email_messages-filter-created_from-wrapper"
    FILTER_CREATED_FROM_DATE = "#email_messages-filter-created_from-wrapper input[type='date']"
    FILTER_CREATED_FROM_TIME = "#email_messages-filter-created_from-wrapper select"

    FILTER_CREATED_TO_WRAPPER = "#email_messages-filter-created_to-wrapper"
    FILTER_CREATED_TO_DATE = (
        "#email_messages-filter-created_to-wrapper input[type='date'], "
        "xpath=(//div[contains(@id,'filter') and contains(@id,'created')]//input[@type='date'])[2]"
    )
    FILTER_CREATED_TO_TIME = (
        "#email_messages-filter-created_to-wrapper select, "
        "xpath=(//div[contains(@id,'filter') and contains(@id,'created')]//select)[2]"
    )

    # ── Filter Pills & Clear ─────────────────────────────────────────────────
    FILTER_PILLS = "xpath=//div[contains(@wire:key,'email_messages-filter-pill-')]"
    FILTER_PILL_FROM = "xpath=//div[contains(@wire:key,'email_messages-filter-pill-created_from')]"
    FILTER_PILL_TO = "xpath=//div[contains(@wire:key,'email_messages-filter-pill-created_to')]"
    BTN_REMOVE_PILL_FROM = "xpath=//div[contains(@wire:key,'email_messages-filter-pill-created_from')]//button"
    BTN_REMOVE_PILL_TO = "xpath=//div[contains(@wire:key,'email_messages-filter-pill-created_to')]//button"
    BTN_CLEAR_ALL_FILTERS = (
        "xpath=//button[contains(@x-on:click,'resetAllFilters')]"
        " | //small[contains(text(),'Applied Filters')]/following::button[contains(.,'Clear')][1]"
    )

    # ── Sorting ──────────────────────────────────────────────────────────────
    SORT_PILL_CREATED_AT = "xpath=//span[contains(@wire:key,'email_messages-sorting-pill-created_at')]"
    BTN_CLEAR_SORT_CREATED_AT = "xpath=//span[contains(@wire:key,'email_messages-sorting-pill-created_at')]//button"
    BTN_CLEAR_ALL_SORTS = (
        "xpath=//button[contains(@wire:click,'clearSorts')]"
        " | //small[contains(text(),'Applied Sorting')]/following::button[contains(.,'Clear')][1]"
    )

    SORT_BTN_CREATED_AT = "xpath=//th[contains(.,'Created At')]//button | //button[contains(@wire:click,\"sortBy('created_at')\")]"
    SORT_BTN_TO_EMAIL = (
        "xpath=//th[contains(.,'To Email Address')]//button"
        " | //button[contains(@wire:click,\"sortBy('to_email_address')\") or contains(@wire:click,\"sortBy('to-email-address')\")]"
    )
    SORT_BTN_SOURCE = "xpath=//th[contains(.,'Source')]//button | //button[contains(@wire:click,\"sortBy('source')\")]"

    # ── Columns Dropdown ─────────────────────────────────────────────────────
    BTN_COLUMNS = "xpath=//button[contains(.,'Columns') and not(ancestor::table)]"
    COLUMNS_DROPDOWN_MENU = "xpath=//div[@role='menu' or contains(@aria-labelledby,'column-select-menu')]"
    CHECKBOX_ALL_COLUMNS = "xpath=//div[contains(@wire:key,'columnSelect-selectAll')]//input[@type='checkbox']"

    # ── Table & Records ──────────────────────────────────────────────────────
    TABLE = "#table-email_messages, table"
    TABLE_HEADERS = "#table-email_messages thead th, table thead th"
    TABLE_ROWS = "#table-email_messages tbody tr, table tbody tr"
    RESULTS_COUNT_TEXT = "xpath=//*[contains(text(),'Showing') and (contains(text(),'result') or contains(text(),'item'))]"
    NO_RECORDS_MSG = (
        "xpath=//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no items found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no record') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no data') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no result') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'not found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'nothing found')]"
    )

    # ── Export CSV ───────────────────────────────────────────────────────────
    BTN_EXPORT_CSV = (
        "xpath=//button[contains(normalize-space(.),'Export CSV') and not(ancestor::table)]"
        " | //button[contains(@wire:click,'confirmExport')]"
    )

    # ── Row View Action & Modal ──────────────────────────────────────────────
    ROW_VIEW_BTN = (
        "xpath=(//table//tbody//tr[not(contains(.,'No record') or contains(.,'no result') or contains(.,'No item'))]"
        "//td[1]//button)[1]"
        " | (//table//tbody//tr//button[contains(@data-tooltip-target,'tooltip-view-')])[1]"
    )
    MODAL_CONTAINER = (
        "#modal-container, div[role='dialog'], "
        "div[x-data*='wireui_dialog'], div.dialog-backdrop, div[x-data*='dialog']"
    )
    MODAL_CLOSE_BTN = (
        "xpath=//button[contains(@class,'dialog-button-close') or @aria-label='close' or @aria-label='Close']"
        " | //div[@role='dialog']//button[contains(.,'Close') or @aria-label='Close']"
        " | //div[@id='modal-container']//button[contains(.,'Close') or @aria-label='Close']"
    )

    def __init__(self, page: Page):
        super().__init__(page)
        self._downloaded_paths: List[str] = []
        self.page.on("download", self._on_download)

    def _on_download(self, download):
        try:
            filename = download.suggested_filename or f"email_messages_export_{int(time.time() * 1000)}.csv"
            dest = os.path.join(DOWNLOAD_DIR, filename)
            download.save_as(dest)
            self._downloaded_paths.append(dest)
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # Navigation
    # ─────────────────────────────────────────────────────────────────────────

    def navigate(self) -> "EmailMessagesPage":
        """Navigate directly to the Email Messages page."""
        self.open(self.MESSAGES_URL)
        self.page.wait_for_timeout(1500)
        return self

    def navigate_via_channels(self) -> "EmailMessagesPage":
        """Navigate via Channels -> Messages -> Email Messages as in TC EMAIL_MSG_001."""
        self.open(self.CHANNELS_URL)
        self.page.wait_for_timeout(1000)
        # Click Messages tab/link or Email Messages
        messages_tab = self.page.locator(self.TAB_MESSAGES).first
        if messages_tab.is_visible():
            messages_tab.click()
            self.page.wait_for_timeout(1500)
        else:
            self.navigate()
        return self

    def is_messages_page(self) -> bool:
        url = self.get_current_url()
        return "/campaigns/email/messages" in url and "login" not in url.lower()

    def get_page_title_text(self) -> str:
        try:
            el = self.h.wait_for_element_visible(self.PAGE_TITLE, timeout=8000)
            return el.inner_text().strip()
        except Exception:
            # Fallback to any h1
            h1 = self.page.locator("h1").first
            return h1.inner_text().strip() if h1.is_visible() else ""

    def wait_for_table_load(self, timeout: int = 15000):
        """Wait for the datatable or no-records message to settle."""
        try:
            self.page.locator(self.TABLE).first.wait_for(state="attached", timeout=timeout)
        except Exception:
            pass
        self.page.wait_for_timeout(800)

    # ─────────────────────────────────────────────────────────────────────────
    # Search
    # ─────────────────────────────────────────────────────────────────────────

    def search(self, query: str):
        inp = self.h.wait_for_element_visible(self.SEARCH_INPUT, timeout=8000)
        inp.fill(query)
        self.page.wait_for_timeout(1500)  # Livewire live search debounce

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
        self.page.wait_for_timeout(600)

    def is_filters_panel_open(self) -> bool:
        panel = self.page.locator(self.FILTERS_PANEL).first
        return panel.is_visible()

    def open_filters_panel(self):
        if not self.is_filters_panel_open():
            self.click_filters_button()

    def close_filters_panel(self):
        if self.is_filters_panel_open():
            self.click_filters_button()

    def get_filter_count(self) -> Optional[int]:
        badge = self.page.locator(self.FILTER_COUNT_BADGE).first
        if badge.is_visible():
            txt = badge.inner_text().strip()
            try:
                return int(txt)
            except ValueError:
                pass
        return None

    def set_created_from_date(self, date_str: str):
        """Set Created From date input (YYYY-MM-DD or DD-MM-YYYY)."""
        self.open_filters_panel()
        inp = self.page.locator(self.FILTER_CREATED_FROM_DATE).first
        inp.fill(date_str)
        inp.dispatch_event("change")
        self.page.wait_for_timeout(1000)

    def set_created_from_time(self, time_str: str):
        """Set Created From time select option (e.g. '00:00', '12:00')."""
        self.open_filters_panel()
        sel = self.page.locator(self.FILTER_CREATED_FROM_TIME).first
        sel.select_option(time_str)
        sel.dispatch_event("change")
        self.page.wait_for_timeout(1000)

    def set_created_to_date(self, date_str: str):
        """Set Created To date input."""
        self.open_filters_panel()
        inp = self.page.locator(self.FILTER_CREATED_TO_DATE).first
        inp.fill(date_str)
        inp.dispatch_event("change")
        self.page.wait_for_timeout(1000)

    def set_created_to_time(self, time_str: str):
        """Set Created To time select option."""
        self.open_filters_panel()
        sel = self.page.locator(self.FILTER_CREATED_TO_TIME).first
        sel.select_option(time_str)
        sel.dispatch_event("change")
        self.page.wait_for_timeout(1000)

    def get_applied_filter_chips(self) -> List[str]:
        pills = self.page.locator(self.FILTER_PILLS)
        results = []
        for i in range(pills.count()):
            txt = pills.nth(i).inner_text().strip()
            if txt:
                results.append(txt)
        return results

    def remove_filter_chip(self, filter_type: str = "created_from"):
        if "from" in filter_type.lower():
            btn = self.page.locator(self.BTN_REMOVE_PILL_FROM).first
        else:
            btn = self.page.locator(self.BTN_REMOVE_PILL_TO).first
        if btn.is_visible():
            btn.click()
            self.page.wait_for_timeout(1000)

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
        # Fallback to any sorting pill
        any_pill = self.page.locator("xpath=//span[contains(@wire:key,'-sorting-pill-')]").first
        return any_pill.inner_text().strip() if any_pill.is_visible() else ""

    def clear_sorting(self):
        btn = self.page.locator(self.BTN_CLEAR_ALL_SORTS).first
        if btn.is_visible():
            btn.click()
            self.page.wait_for_timeout(1000)
        else:
            single_clear = self.page.locator(self.BTN_CLEAR_SORT_CREATED_AT).first
            if single_clear.is_visible():
                single_clear.click()
                self.page.wait_for_timeout(1000)

    def click_sort_created_at(self):
        btn = self.page.locator(self.SORT_BTN_CREATED_AT).first
        if btn.is_visible():
            btn.click()
            self.page.wait_for_timeout(1200)

    def click_sort_to_email(self):
        btn = self.page.locator(self.SORT_BTN_TO_EMAIL).first
        if btn.is_visible():
            btn.click()
            self.page.wait_for_timeout(1200)

    def click_sort_source(self):
        btn = self.page.locator(self.SORT_BTN_SOURCE).first
        if btn.is_visible():
            btn.click()
            self.page.wait_for_timeout(1200)

    # ─────────────────────────────────────────────────────────────────────────
    # Columns Dropdown
    # ─────────────────────────────────────────────────────────────────────────

    def click_columns_button(self):
        btn = self.h.wait_for_element_clickable(self.BTN_COLUMNS, timeout=8000)
        btn.click()
        self.page.wait_for_timeout(500)

    def is_columns_menu_open(self) -> bool:
        menu = self.page.locator(self.COLUMNS_DROPDOWN_MENU).first
        return menu.is_visible()

    def get_column_checkbox(self, col_value: str):
        return self.page.locator(f"xpath=//input[@type='checkbox' and @value='{col_value}']").first

    def toggle_column_by_value(self, col_value: str, select: Optional[bool] = None):
        """Toggle or set checked state of a column by its checkbox value."""
        if not self.is_columns_menu_open():
            self.click_columns_button()
        cb = self.get_column_checkbox(col_value)
        if cb.is_visible():
            is_checked = cb.is_checked()
            if select is None or select != is_checked:
                cb.click()
                self.page.wait_for_timeout(1000)

    def select_all_columns(self):
        if not self.is_columns_menu_open():
            self.click_columns_button()
        all_cb = self.page.locator(self.CHECKBOX_ALL_COLUMNS).first
        if all_cb.is_visible():
            all_cb.click()
            self.page.wait_for_timeout(1000)

    # ─────────────────────────────────────────────────────────────────────────
    # Table & Data
    # ─────────────────────────────────────────────────────────────────────────

    def get_table_headers(self) -> List[str]:
        return self._get_headers_safe(self.TABLE_HEADERS)

    def is_column_visible(self, column_name: str) -> bool:
        headers = self.get_table_headers()
        lowered = [h.lower() for h in headers]
        return any(column_name.lower() in h for h in lowered)

    def get_row_count(self) -> int:
        """Return number of real data rows (skipping empty placeholder rows)."""
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
        el = self.page.locator(self.RESULTS_COUNT_TEXT).first
        if el.is_visible():
            return el.inner_text().strip()
        # Fallback to pagination text
        paged = self.page.locator(".paged-pagination-results").first
        return paged.inner_text().strip() if paged.is_visible() else ""

    def get_cell_text(self, row_index: int, col_index_or_name) -> str:
        if isinstance(col_index_or_name, str):
            col_index = self.COLUMN_INDEX.get(col_index_or_name.lower().replace(" ", "-"), 0)
        else:
            col_index = col_index_or_name

        try:
            rows = self.page.locator(self.TABLE_ROWS)
            if row_index >= rows.count():
                return ""
            cells = rows.nth(row_index).locator("td")
            if col_index >= cells.count():
                return ""
            return cells.nth(col_index).inner_text().strip()
        except Exception:
            return ""

    def get_all_column_values(self, col_index_or_name) -> List[str]:
        if isinstance(col_index_or_name, str):
            col_index = self.COLUMN_INDEX.get(col_index_or_name.lower().replace(" ", "-"), 0)
        else:
            col_index = col_index_or_name

        values = []
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            for i in range(rows.count()):
                row = rows.nth(i)
                txt = row.inner_text().strip()
                if not txt or "no " in txt.lower():
                    continue
                cells = row.locator("td")
                if col_index < cells.count():
                    values.append(cells.nth(col_index).inner_text().strip())
        except Exception:
            pass
        return values

    def click_refresh(self):
        btn = self.h.wait_for_element_clickable(self.REFRESH_BTN, timeout=8000)
        btn.click()
        self.page.wait_for_timeout(1500)

    # ─────────────────────────────────────────────────────────────────────────
    # Export CSV
    # ─────────────────────────────────────────────────────────────────────────

    def click_export_csv(self) -> Optional[str]:
        """Click Export CSV and wait for download to start/finish."""
        btn = self.h.wait_for_element_clickable(self.BTN_EXPORT_CSV, timeout=8000)
        try:
            with self.page.expect_download(timeout=15000) as download_info:
                btn.click()
            download = download_info.value
            filename = download.suggested_filename or f"email_messages_{int(time.time()*1000)}.csv"
            dest = os.path.join(DOWNLOAD_DIR, filename)
            download.save_as(dest)
            self._downloaded_paths.append(dest)
            return dest
        except Exception:
            # Fallback if download triggered asynchronously
            btn.click()
            self.page.wait_for_timeout(3000)
            if self._downloaded_paths:
                return self._downloaded_paths[-1]
            return None

    def get_latest_download(self) -> Optional[str]:
        return self._downloaded_paths[-1] if self._downloaded_paths else None

    # ─────────────────────────────────────────────────────────────────────────
    # View Action & Details Modal
    # ─────────────────────────────────────────────────────────────────────────

    def click_view_action(self, row_idx: int = 0):
        """Click the View (eye icon) action in the specified row."""
        rows = self.page.locator(self.TABLE_ROWS)
        if rows.count() > row_idx:
            row = rows.nth(row_idx)
            # Find action button inside row
            action_btn = row.locator("td").first.locator("button, a").first
            if action_btn.is_visible():
                action_btn.click()
                self.page.wait_for_timeout(1000)
                return True
        return False

    def is_details_modal_open(self) -> bool:
        modal = self.page.locator(self.MODAL_CONTAINER).first
        return modal.is_visible()

    def get_modal_text(self) -> str:
        modal = self.page.locator(self.MODAL_CONTAINER).first
        return modal.inner_text().strip() if modal.is_visible() else ""

    def close_details_modal(self):
        close_btn = self.page.locator(self.MODAL_CLOSE_BTN).first
        if close_btn.is_visible():
            close_btn.click()
            self.page.wait_for_timeout(800)
        else:
            # Press Escape
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(500)
