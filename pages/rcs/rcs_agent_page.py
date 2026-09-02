import os
import time

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR


class RcsAgentPage(BasePage):

    REPORT_URL = "/rcs/senderid"
    TABLE_NAME = "table"

    # Confirmed column order for the DEFAULT (all-8) column selection.
    COLUMN_INDEX = {
        "bulk_checkbox": 0, "action": 1, "logo": 2, "agent_name": 3,
        "display_name": 4, "use_case": 5, "status": 6,
        "verification_status": 7, "created_at": 8,
    }

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'RCS Agents')]"
    BREADCRUMB = "xpath=//nav[@aria-label='Breadcrumb']"

    MODAL_CONTAINER = "#modal-container"

    # ── Search ───────────────────────────────────────────────────────────────
    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search']"

    # ── Filters popover (confirmed: two plain native date inputs, no
    # dedicated Clear button — see module docstring caveat #5). ─────────────
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')]"
    FILTER_CREATED_FROM = "#table-filter-created_from"
    FILTER_CREATED_TO = "#table-filter-created_to"

    # ── Bulk Actions (Export to XLSX only — no bulk delete here) ────────────
    BULK_ACTIONS_BUTTON = "#table-bulkActionsDropdown"
    BULK_ACTION_EXPORT = (
        "xpath=//button[@*[name()='wire:click']='export' and contains(@*[name()='wire:key'],'bulk-action-export')]"
    )
    ROW_CHECKBOX = "input[type='checkbox'][wire\\:key^='tableselectedItems-']"

    # ── Sorting (6 sortable columns) ─────────────────────────────────────────
    SORT_AGENT_NAME_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('sender_name')\")]"
    SORT_DISPLAY_NAME_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('display_name')\")]"
    SORT_USE_CASE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('use_case')\")]"
    SORT_STATUS_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('status')\")]"
    SORT_VERIFICATION_STATUS_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('verification_status')\")]"
    SORT_CREATED_AT_BTN = "xpath=//button[contains(normalize-space(.), 'Created at')]"
    CLEAR_ALL_SORTS_BTN = "xpath=//button[contains(@*[name()='wire:click'],'clearSorts')]"
    APPLIED_SORT_PILL = f"xpath=//span[contains(@*[name()='wire:key'],'{TABLE_NAME}-sorting-pill-')]"

    # ── Columns dropdown (7 toggleable checkboxes; "Logo" is NOT one of
    # them — see module docstring caveat #2) ────────────────────────────────
    COLUMNS_BUTTON = "xpath=//button[contains(normalize-space(.),'Columns')]"
    COLUMN_CHECKBOXES = (
        f"xpath=//div[contains(@*[name()='wire:key'],'{TABLE_NAME}-columnSelect-') and "
        f"not(contains(@*[name()='wire:key'],'columnSelect-selectAll'))]//input[@type='checkbox']"
    )
    SELECT_ALL_COLUMNS_CHECKBOX = (
        f"xpath=//div[contains(@*[name()='wire:key'],'{TABLE_NAME}-columnSelect-selectAll-')]//input[@type='checkbox']"
    )

    # ── Table ────────────────────────────────────────────────────────────────
    TABLE = f"#table-{TABLE_NAME}"
    TABLE_HEADERS = f"#table-{TABLE_NAME} thead th"
    TABLE_ROWS = f"#table-{TABLE_NAME} tbody tr"
    NO_RECORDS_MSG = (
        "xpath=//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no items found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no record') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no data') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no result') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'not found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'nothing found')]"
    )

    # ── Row action: View only (no edit/delete in this dump) ──────────────────
    VIEW_ICON_IN_ROW = "xpath=.//*[contains(@data-tooltip-target,'tooltip-view-')]"

    # ── Pagination results text (note: "total-", not "paged-") ───────────────
    PAGINATION_RESULTS_TEXT = ".total-pagination-results"

    # ── User menu / logout (global header, confirmed identical to every
    # other page in this app). ──────────────────────────────────────────────
    USER_MENU_BUTTON = "xpath=//button[contains(@class,'rounded-full') and .//img]"
    LOGOUT_LINK = "xpath=//a[@title='Log out']"

    # ── Navigation / page state ─────────────────────────────────────────────

    def navigate(self):
        self.open(self.REPORT_URL)
        self.page.wait_for_timeout(2000)
        return self

    navigate_to_report = navigate

    def is_agent_page(self):
        url = self.get_current_url()
        return "/rcs/senderid" in url and "login" not in url.lower()

    def get_page_title_text(self):
        return self.h.wait_for_element_visible(self.PAGE_TITLE).inner_text().strip()

    def get_breadcrumb_text(self):
        return self.h.wait_for_element_visible(self.BREADCRUMB).inner_text().strip()

    def wait_for_table_load(self, timeout=15000):
        self.page.locator(self.TABLE).first.wait_for(state="attached", timeout=timeout)
        self.page.wait_for_timeout(1000)

    def refresh_page(self):
        self.page.reload()
        self.wait_for_table_load(timeout=15000)

    def _is_visible(self, locator, timeout=1000):
        try:
            return self.page.locator(locator).first.is_visible()
        except Exception:
            return False

    # ── Search ───────────────────────────────────────────────────────────────

    def _wait_for_search_to_settle(self, timeout_ms=8000):
        last_state = [None]

        def _stable():
            current = self.get_row_count()
            no_msg = self.is_element_present(self.NO_RECORDS_MSG, timeout=500)
            state = (current, no_msg)
            if state == last_state[0]:
                return True
            last_state[0] = state
            return False

        self.h.wait_until(_stable, timeout_ms=timeout_ms, interval_ms=600)

    def search(self, value):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.fill(value)
        self.page.wait_for_timeout(500)
        self._wait_for_search_to_settle()
        self.page.wait_for_timeout(300)

    def clear_search(self):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.fill("")
        self.page.wait_for_timeout(500)
        self._wait_for_search_to_settle()
        self.page.wait_for_timeout(300)

    # ── Table / rows ─────────────────────────────────────────────────────────

    def has_records(self):
        return self.is_element_present(self.TABLE_ROWS, timeout=5000) and self.get_row_count() > 0

    @staticmethod
    def _is_empty_state_row(tds):
        return tds.count() == 1 and tds.first.get_attribute("colspan")

    def has_no_records_message(self):
        if self.is_element_present(self.NO_RECORDS_MSG, timeout=3000):
            return True
        rows = self.page.locator(self.TABLE_ROWS)
        if rows.count() == 1:
            tds = rows.first.locator("td")
            if self._is_empty_state_row(tds):
                return True
        return self.get_row_count() == 0

    def get_row_count(self):
        return self._count_data_rows(self.TABLE_ROWS)

    def get_visible_column_headers(self):
        return self._get_headers_safe(self.TABLE_HEADERS)

    def get_column_values(self, column_name):
        idx = self.COLUMN_INDEX.get(column_name)
        if idx is None:
            return []
        rows = self.page.locator(self.TABLE_ROWS)
        values = []
        for i in range(rows.count()):
            tds = rows.nth(i).locator("td")
            if tds.count() > idx:
                values.append(tds.nth(idx).inner_text().strip())
        return values

    def get_first_data_row(self):
        return self._first_visible_data_row(f"#table-{self.TABLE_NAME} tbody tr")

    # ── Sorting ──────────────────────────────────────────────────────────────

    def sort_by_agent_name(self):
        self._js_click(self.SORT_AGENT_NAME_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_display_name(self):
        self._js_click(self.SORT_DISPLAY_NAME_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_use_case(self):
        self._js_click(self.SORT_USE_CASE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_status(self):
        self._js_click(self.SORT_STATUS_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_verification_status(self):
        self._js_click(self.SORT_VERIFICATION_STATUS_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_created_at(self):
        self._js_click(self.SORT_CREATED_AT_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def get_applied_sort_pill_text(self):
        if self.is_element_present(self.APPLIED_SORT_PILL, timeout=3000):
            return self.h.wait_for_element_visible(self.APPLIED_SORT_PILL).inner_text().strip()
        return None

    def clear_all_sorts(self):
        self._js_click(self.CLEAR_ALL_SORTS_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    # ── Filters popover ──────────────────────────────────────────────────────

    def open_filters_popover(self):
        if self._is_visible(self.FILTER_CREATED_FROM, timeout=1000):
            return
        self._js_click(self.FILTERS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def set_created_from_filter(self, from_date):
        self.open_filters_popover()
        el = self.h.wait_for_element_visible(self.FILTER_CREATED_FROM)
        el.fill(from_date)
        self.page.wait_for_timeout(1200)

    def set_created_to_filter(self, to_date):
        self.open_filters_popover()
        el = self.h.wait_for_element_visible(self.FILTER_CREATED_TO)
        el.fill(to_date)
        self.page.wait_for_timeout(1200)

    def set_date_range_filter(self, from_date, to_date):
        self.set_created_from_filter(from_date)
        self.set_created_to_filter(to_date)

    def get_filter_values(self):
        self.open_filters_popover()
        from_el = self.h.wait_for_element_visible(self.FILTER_CREATED_FROM)
        to_el = self.h.wait_for_element_visible(self.FILTER_CREATED_TO)
        return from_el.input_value(), to_el.input_value()

    def clear_date_filters(self):
        """No dedicated 'Clear Filters' button exists in the supplied DOM
        (see module docstring caveat #5) — clearing is done by resetting
        both confirmed date inputs directly, the same DOM-grounded
        technique used to set them."""
        self.open_filters_popover()
        from_el = self.h.wait_for_element_visible(self.FILTER_CREATED_FROM)
        from_el.fill("")
        self.page.wait_for_timeout(600)
        to_el = self.h.wait_for_element_visible(self.FILTER_CREATED_TO)
        to_el.fill("")
        self.page.wait_for_timeout(1200)

    # ── Bulk Actions ─────────────────────────────────────────────────────────

    def open_bulk_actions_dropdown(self):
        self._js_click(self.BULK_ACTIONS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def select_first_row_checkbox(self):
        cb = self.h.wait_for_element_visible(self.ROW_CHECKBOX)
        cb.scroll_into_view_if_needed()
        cb.click(force=True)
        self.page.wait_for_timeout(500)

    def export_csv(self, timeout_ms=30000):
        """Opens Bulk Actions and clicks Export, capturing the resulting
        download via page.expect_download() (no row checkboxes selected
        first -- mirrors the confirmed-working Bulk Actions -> Export
        pattern already proven on SmsBlockedNumbersPage.export_csv(): the
        export acts on the current filtered listing, not an explicit row
        selection). The "Export to XLSX only" note already on
        BULK_ACTION_EXPORT above suggests this download may not be a
        plain .csv -- callers should read headers via
        utils/file_validator.py's read_file_headers()/validate_file_headers(),
        which dispatch on file extension, not assume one.

        Returns {"elapsed_s", "file_path", "file_size"} on success, or
        None on failure (timeout / no download triggered) -- same
        never-raises contract used throughout this codebase's Bulk
        Actions -> Export methods."""
        try:
            self.open_bulk_actions_dropdown()
            btn = self.h.wait_for_element_clickable(self.BULK_ACTION_EXPORT, timeout=10000)
            btn.scroll_into_view_if_needed()
            start = time.time()
            with self.page.expect_download(timeout=timeout_ms) as dl_info:
                btn.click(force=True)
            download = dl_info.value
            filename = download.suggested_filename or "rcs_agents_export.csv"
            dest = os.path.join(DOWNLOAD_DIR, filename)
            download.save_as(dest)
            return {
                "elapsed_s": time.time() - start,
                "file_path": dest,
                "file_size": os.path.getsize(dest),
            }
        except Exception:
            return None

    # ── Columns dropdown ─────────────────────────────────────────────────────

    def open_columns_dropdown(self):
        if self._is_visible(self.COLUMN_CHECKBOXES, timeout=1000):
            return
        self._js_click(self.COLUMNS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def toggle_column(self, value):
        """value: 'action' | 'agent-name' | 'display-name' | 'use-case' |
        'status' | 'verification-status' | 'created-at' (NOT 'logo' — it
        has no checkbox, see module docstring caveat #2)."""
        self.open_columns_dropdown()
        cb = self.h.wait_for_element_visible(f"input[type='checkbox'][value='{value}']")
        cb.scroll_into_view_if_needed()
        cb.click(force=True)
        self.page.wait_for_timeout(800)

    def is_column_checked(self, value):
        self.open_columns_dropdown()
        try:
            return self.page.locator(f"input[type='checkbox'][value='{value}']").first.is_checked()
        except Exception:
            return None

    def restore_default_columns(self):
        """Restores the CONFIRMED default column state: all 7 toggleable
        checkboxes checked (action/agent-name/display-name/use-case/status/
        verification-status/created-at)."""
        defaults = {"action": True, "agent-name": True, "display-name": True,
                    "use-case": True, "status": True,
                    "verification-status": True, "created-at": True}
        for value, should_be_checked in defaults.items():
            self.open_columns_dropdown()
            cb = self.page.locator(f"input[type='checkbox'][value='{value}']")
            if cb.count() == 0:
                continue
            cb = cb.first
            if cb.is_checked() != should_be_checked:
                cb.scroll_into_view_if_needed()
                cb.click(force=True)
                self.page.wait_for_timeout(500)

    # ── Row action: View ─────────────────────────────────────────────────────

    def click_view_on_first_row(self):
        row = self.get_first_data_row()
        if row is None:
            return False
        btn = row.locator(self.VIEW_ICON_IN_ROW)
        if btn.count() == 0:
            return False
        btn.first.scroll_into_view_if_needed()
        btn.first.click(force=True)
        self.page.wait_for_timeout(1500)
        return True

    def is_modal_open(self):
        try:
            return self.page.locator(self.MODAL_CONTAINER).first.is_visible()
        except Exception:
            return False

    # ── Pagination ───────────────────────────────────────────────────────────

    def get_pagination_results_text(self):
        return self.h.wait_for_element_visible(self.PAGINATION_RESULTS_TEXT).inner_text().strip()

    # ── Logout ───────────────────────────────────────────────────────────────

    def logout(self):
        self._js_click(self.USER_MENU_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)
        self._js_click(self.LOGOUT_LINK, timeout=10000)
        self.page.wait_for_timeout(1500)
