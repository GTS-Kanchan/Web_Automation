"""pages/common/monthly_usage_page.py — Page Object Model for the Monthly Usage
billing page (/billing/monthly/usage-details).
"""

import re
import time
from typing import Dict, List, Optional

from playwright.sync_api import Page, expect

from pages.common.base_page import BasePage
from utils.config import Config


class MonthlyUsagePage(BasePage):
    """Page Object for the Monthly Usage page under Billing."""

    PATH = "/billing/monthly/usage-details"

    # ── Locators ──
    SIDEBAR_LINK = "a[href*='/billing/monthly/usage-details']"
    PAGE_HEADING = "h1:has-text('Monthly Usage')"
    BREADCRUMB_NAV = "nav[aria-label='Breadcrumb']"

    # Table & Container
    TABLE = "#table-monthly_usage_reports"
    TABLE_BODY = "#monthly_usage_reports-tbody"
    TABLE_ROWS = "#monthly_usage_reports-tbody tr[rowpk]"
    HORIZONTAL_WRAPPER = "div[wire\\:key='monthly_usage_reports-twrap']"

    # Filters
    FILTERS_BUTTON = "button:has-text('Filters')"
    FILTERS_POPOVER = "div[x-show='filterPopoverOpen']"
    MONTH_SELECT = "#monthly_usage_reports-filter-month"
    CHANNEL_SELECT = "#monthly_usage_reports-filter-channel"
    PRODUCT_SELECT = "#monthly_usage_reports-filter-product"

    # Bulk Actions
    BULK_ACTIONS_BUTTON = "#monthly_usage_reports-bulkActionsDropdown"
    BULK_ACTIONS_MENU = "div[x-show='open']"
    EXPORT_CSV_BUTTON = "button:has-text('Export to CSV')"
    BULK_HEADER_CHECKBOX = "th[wire\\:key='monthly_usage_reports-thead-bulk-actions'] input[type='checkbox']"
    ROW_CHECKBOXES = "td[wire\\:key*='monthly_usage_reports-tbody-td-bulk-actions-td-'] input[type='checkbox']"
    BULK_SELECT_MESSAGE = "tr[wire\\:key='monthly_usage_reports-bulk-select-message']"

    # Columns mapping (column attribute name to td wire:key suffix)
    COLUMNS = [
        "month",
        "channel",
        "product",
        "units",
        "total-sale-price",
        "delivered-units",
        "total-surcharge",
        "total-rate-refunded",
        "total-rate-applied",
        "total-discount",
        "gross-sale-price",
        "payment-mode",
        "last-updated-at",
    ]

    def __init__(self, page: Page):
        super().__init__(page)

    # ══════════════════════════════════════════════════════════════════════════
    # Navigation & Verification
    # ══════════════════════════════════════════════════════════════════════════

    def navigate(self):
        """Directly open the Monthly Usage page."""
        self.open(self.PATH)
        self.wait_for_table_load()

    def navigate_via_sidebar(self):
        """Click the sidebar link for Monthly Usage."""
        link = self.page.locator(self.SIDEBAR_LINK).first
        link.wait_for(state="visible", timeout=10000)
        link.click()
        self.wait_for_table_load()

    def is_monthly_usage_page(self) -> bool:
        """Check if current page URL points to Monthly Usage."""
        return "/billing/monthly/usage-details" in self.get_current_url()

    def get_heading_text(self) -> str:
        """Get the h1 page heading text."""
        heading = self.page.locator(self.PAGE_HEADING).first
        heading.wait_for(state="visible", timeout=10000)
        return heading.inner_text().strip()

    def get_breadcrumb_text(self) -> str:
        """Get the full breadcrumb text (e.g. 'Home > Monthly Usage')."""
        breadcrumb = self.page.locator(self.BREADCRUMB_NAV).first
        breadcrumb.wait_for(state="visible", timeout=10000)
        return breadcrumb.inner_text().strip()

    def wait_for_table_load(self, timeout: int = 15000):
        """Wait for the table and ensure Livewire is idle."""
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
    # Table Header & Data Inspection
    # ══════════════════════════════════════════════════════════════════════════

    def get_column_headers(self) -> List[str]:
        """Get visible table column header text list, excluding bulk actions checkbox."""
        ths = self.page.locator(f"{self.TABLE} thead tr th")
        headers = []
        for i in range(ths.count()):
            th = ths.nth(i)
            # Skip bulk action checkbox header
            if "bulk-actions" in (th.get_attribute("wire:key") or ""):
                continue
            text = th.inner_text().strip()
            # Clean up sort indicators or whitespace
            cleaned = text.split("\n")[0].strip()
            if cleaned:
                headers.append(cleaned)
        return headers

    def get_row_count(self) -> int:
        """Return the number of data rows currently rendered."""
        rows = self.page.locator(self.TABLE_ROWS)
        return rows.count()

    def get_cell_value(self, row_index: int, col_name: str) -> str:
        """Get text value of a specific cell by row index (0-based) and column name.
        col_name can be hyphenated ('total-sale-price') or underscore ('total_sale_price').
        """
        normalized_col = col_name.lower().replace("_", "-")
        cell_locator = f"td[wire\\:key$='-{normalized_col}']"
        row = self.page.locator(self.TABLE_ROWS).nth(row_index)
        cell = row.locator(cell_locator)
        if cell.count() > 0:
            return cell.first.inner_text().strip()
        # Fallback to column index
        col_index = self._get_col_index(normalized_col)
        if col_index is not None:
            # +1 because index 0 is checkbox
            tds = row.locator("td")
            if tds.count() > col_index + 1:
                return tds.nth(col_index + 1).inner_text().strip()
        return ""

    def _get_col_index(self, normalized_col: str) -> Optional[int]:
        if normalized_col in self.COLUMNS:
            return self.COLUMNS.index(normalized_col)
        return None

    def get_column_values(self, col_name: str) -> List[str]:
        """Return all values for a column across all visible rows."""
        count = self.get_row_count()
        values = []
        for i in range(count):
            values.append(self.get_cell_value(i, col_name))
        return values

    def get_row_data(self, row_index: int) -> Dict[str, str]:
        """Return dictionary of all column values for a specific row."""
        data = {}
        for col in self.COLUMNS:
            data[col] = self.get_cell_value(row_index, col)
        return data

    def get_all_rows_data(self) -> List[Dict[str, str]]:
        """Return list of row data dictionaries for all visible rows."""
        count = self.get_row_count()
        return [self.get_row_data(i) for i in range(count)]

    # ══════════════════════════════════════════════════════════════════════════
    # Filters
    # ══════════════════════════════════════════════════════════════════════════

    def is_filters_open(self) -> bool:
        """Check if filter popover is currently visible."""
        popover = self.page.locator(self.FILTERS_POPOVER)
        return popover.is_visible()

    def open_filters(self):
        """Click Filters button to open popover if not already open."""
        if not self.is_filters_open():
            btn = self.page.locator(self.FILTERS_BUTTON).first
            btn.click()
            self.page.wait_for_selector(self.FILTERS_POPOVER, state="visible", timeout=5000)
            self.page.wait_for_timeout(300)

    def close_filters(self):
        """Close filter popover if currently open."""
        if self.is_filters_open():
            btn = self.page.locator(self.FILTERS_BUTTON).first
            btn.click()
            self.page.wait_for_timeout(300)

    def get_month_options(self) -> List[str]:
        """Return list of option texts from Month dropdown."""
        self.open_filters()
        select = self.page.locator(self.MONTH_SELECT)
        options = select.locator("option")
        return [options.nth(i).inner_text().strip() for i in range(options.count())]

    def get_selected_month(self) -> str:
        """Get currently selected option text in Month dropdown."""
        self.open_filters()
        select = self.page.locator(self.MONTH_SELECT)
        val = select.input_value()
        # Find option text matching this value
        option = select.locator(f"option[value='{val}']")
        if option.count() > 0:
            return option.first.inner_text().strip()
        return ""

    def select_month(self, month_text_or_val: str):
        """Select a month from the Month filter by label or value."""
        self.open_filters()
        select = self.page.locator(self.MONTH_SELECT)
        # Try label first, fallback to value
        try:
            select.select_option(label=month_text_or_val)
        except Exception:
            select.select_option(value=month_text_or_val)
        self.wait_for_livewire()
        self.close_filters()

    def get_channel_options(self) -> List[str]:
        """Return list of option texts from Channel dropdown."""
        self.open_filters()
        select = self.page.locator(self.CHANNEL_SELECT)
        options = select.locator("option")
        return [options.nth(i).inner_text().strip() for i in range(options.count())]

    def get_selected_channel(self) -> str:
        """Get currently selected option text in Channel dropdown."""
        self.open_filters()
        select = self.page.locator(self.CHANNEL_SELECT)
        val = select.input_value()
        option = select.locator(f"option[value='{val}']")
        if option.count() > 0:
            return option.first.inner_text().strip()
        return ""

    def select_channel(self, channel_text_or_val: str):
        """Select a channel from the Channel filter by label or value."""
        self.open_filters()
        select = self.page.locator(self.CHANNEL_SELECT)
        try:
            select.select_option(label=channel_text_or_val)
        except Exception:
            select.select_option(value=channel_text_or_val)
        self.wait_for_livewire()
        self.close_filters()

    def get_product_options(self) -> List[str]:
        """Return list of option texts from Product dropdown."""
        self.open_filters()
        select = self.page.locator(self.PRODUCT_SELECT)
        options = select.locator("option")
        return [options.nth(i).inner_text().strip() for i in range(options.count())]

    def get_selected_product(self) -> str:
        """Get currently selected option text in Product dropdown."""
        self.open_filters()
        select = self.page.locator(self.PRODUCT_SELECT)
        val = select.input_value()
        option = select.locator(f"option[value='{val}']")
        if option.count() > 0:
            return option.first.inner_text().strip()
        return ""

    def select_product(self, product_text_or_val: str):
        """Select a product from the Product filter by label or value."""
        self.open_filters()
        select = self.page.locator(self.PRODUCT_SELECT)
        # Check if partial or exact label matches
        options = select.locator("option")
        matched_val = None
        for i in range(options.count()):
            opt_text = options.nth(i).inner_text().strip()
            if product_text_or_val.lower() in opt_text.lower():
                matched_val = options.nth(i).get_attribute("value")
                break
        if matched_val is not None:
            select.select_option(value=matched_val)
        else:
            try:
                select.select_option(label=product_text_or_val)
            except Exception:
                select.select_option(value=product_text_or_val)
        self.wait_for_livewire()
        self.close_filters()

    def reset_filters(self):
        """Reset all three filters to 'All'."""
        self.open_filters()
        self.page.locator(self.MONTH_SELECT).select_option(value="")
        self.page.locator(self.CHANNEL_SELECT).select_option(value="")
        self.page.locator(self.PRODUCT_SELECT).select_option(value="")
        self.wait_for_livewire()
        self.close_filters()

    # ══════════════════════════════════════════════════════════════════════════
    # Bulk Actions & Row Checkboxes
    # ══════════════════════════════════════════════════════════════════════════

    def is_header_checkbox_checked(self) -> bool:
        """Check if bulk select all header checkbox is checked."""
        cb = self.page.locator(self.BULK_HEADER_CHECKBOX).first
        return cb.is_checked()

    def click_header_checkbox(self):
        """Toggle the bulk select all header checkbox."""
        cb = self.page.locator(self.BULK_HEADER_CHECKBOX).first
        cb.click()
        self.page.wait_for_timeout(300)

    def is_row_checked(self, row_index: int) -> bool:
        """Check if a specific row checkbox is checked."""
        cbs = self.page.locator(self.ROW_CHECKBOXES)
        if cbs.count() > row_index:
            return cbs.nth(row_index).is_checked()
        return False

    def click_row_checkbox(self, row_index: int):
        """Toggle a specific row checkbox."""
        cbs = self.page.locator(self.ROW_CHECKBOXES)
        if cbs.count() > row_index:
            cbs.nth(row_index).click()
            self.page.wait_for_timeout(300)

    def select_rows(self, indices: List[int]):
        """Select checkboxes for specified row indices."""
        for idx in indices:
            if not self.is_row_checked(idx):
                self.click_row_checkbox(idx)

    def deselect_all(self):
        """Click Deselect All button or uncheck header checkbox."""
        deselect_btn = self.page.locator("button:has-text('Deselect All')")
        if deselect_btn.is_visible():
            deselect_btn.first.click()
            self.page.wait_for_timeout(300)
        elif self.is_header_checkbox_checked():
            self.click_header_checkbox()

    def is_bulk_actions_button_visible(self) -> bool:
        """Check if Bulk Actions button is rendered."""
        btn = self.page.locator(self.BULK_ACTIONS_BUTTON)
        return btn.is_visible()

    def open_bulk_actions(self):
        """Click Bulk Actions button to open dropdown."""
        btn = self.page.locator(self.BULK_ACTIONS_BUTTON).first
        btn.click()
        self.page.wait_for_timeout(300)

    def is_bulk_actions_menu_open(self) -> bool:
        """Check if bulk actions menu dropdown is visible."""
        item = self.page.locator(self.EXPORT_CSV_BUTTON)
        return item.is_visible()

    def click_export_to_csv(self):
        """Click Export to CSV in Bulk Actions menu."""
        if not self.is_bulk_actions_menu_open():
            self.open_bulk_actions()
        export_btn = self.page.locator(self.EXPORT_CSV_BUTTON).first
        export_btn.click()
        self.wait_for_livewire()

    def export_csv_download(self):
        """Trigger Export to CSV and wait for download event."""
        if not self.is_bulk_actions_menu_open():
            self.open_bulk_actions()
        with self.page.expect_download(timeout=15000) as download_info:
            self.page.locator(self.EXPORT_CSV_BUTTON).first.click()
        download = download_info.value
        return download

    def get_bulk_select_message_text(self) -> str:
        """Get the text from the bulk selection message banner."""
        msg = self.page.locator(self.BULK_SELECT_MESSAGE)
        if msg.is_visible():
            return msg.inner_text().strip()
        return ""

    # ══════════════════════════════════════════════════════════════════════════
    # Sorting
    # ══════════════════════════════════════════════════════════════════════════

    def sort_by_column(self, col_key: str):
        """Click column sort button (e.g. 'created_at', 'units', 'total_sale_price')."""
        # Map friendly column name to wire:click sortBy pattern
        key_map = {
            "month": "created_at",
            "channel": "channel.name",
            "product": "product.name",
            "units": "units",
            "total_sale_price": "total_sale_price",
            "delivered_units": "delivered_units",
            "total_surcharge": "total_surcharge",
            "total_rate_refunded": "total_rate_refunded",
            "total_rate_applied": "total_rate_applied",
            "total_discount": "total_discount",
            "gross_sale_price": "gross_sale_price",
            "payment_mode": "payment_mode",
            "last_updated_at": "updated_at",
        }
        wire_target = key_map.get(col_key, col_key)
        btn = self.page.locator(f"button[wire\\:click=\"sortBy('{wire_target}')\"]").first
        btn.click()
        self.wait_for_livewire()

    # ══════════════════════════════════════════════════════════════════════════
    # Layout & Horizontal Scrolling
    # ══════════════════════════════════════════════════════════════════════════

    def is_table_horizontally_scrollable(self) -> bool:
        """Verify if table container has horizontal scrollable content."""
        wrapper = self.page.locator(self.HORIZONTAL_WRAPPER).first
        if not wrapper.is_visible():
            return False
        return self.page.evaluate(
            "(sel) => { const el = document.querySelector(sel); return el ? el.scrollWidth > el.clientWidth : false; }",
            self.HORIZONTAL_WRAPPER,
        )

    def scroll_table_horizontally(self, offset: int = 500):
        """Scroll the table horizontally by offset pixels."""
        self.page.evaluate(
            f"(sel) => {{ const el = document.querySelector(sel); if (el) el.scrollLeft += {offset}; }}",
            self.HORIZONTAL_WRAPPER,
        )
        self.page.wait_for_timeout(200)

    # ══════════════════════════════════════════════════════════════════════════
    # Data Validation Helpers
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def parse_numeric_value(val_str: str) -> Optional[float]:
        """Extract float value from formatted string, ignoring commas, or None if N/A / dash."""
        val_str = val_str.strip()
        if val_str in ("N/A", "-", "", "—"):
            return None
        cleaned = re.sub(r"[^\d.-]", "", val_str)
        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def get_decimal_places(val_str: str) -> Optional[int]:
        """Return number of decimal places in string, or None if not a decimal."""
        val_str = val_str.strip()
        if "." in val_str:
            parts = val_str.split(".")
            return len(parts[1])
        return None
