"""pages/common/flow_summary_report_page.py — page object for the
Communication Flow Summary Report (Automation Flows → Summary tab,
/flow/summary).

Locators below are built from a live DOM dump of this exact page
(rappasoft/livewire-tables + Alpine, same conventions as every SMS/RCS/
WhatsApp report page in this project — see e.g.
pages/sms/reports/sms_campaign_report_page.py for the shared pattern).

CONFIRMED DOM facts worth calling out (this page differs from the SMS/
RCS/WhatsApp report pages it otherwise mirrors):

  * There is no Date Range / Report Type / Group By trio here. Instead
    the Filters popover has three fields: From Date, To Date, Flow Name
    (a plain <select>, not an async-select) — CONFIRMED
    filterComponents: {from_date, to_date, flow_name}.
  * The table has a leading bulk-select checkbox column (bulkActionsStatus:
    true), so every data column's <td> index is offset by +1 versus a
    report with no checkbox column.
  * Export is NOT a standalone "Export CSV" button — it's one item
    ("Export to CSV", wire:click="export") inside a "Bulk Actions"
    dropdown. CONFIRMED hideBulkActionsWhenEmpty: false, so that dropdown
    is always visible regardless of row selection (unlike the TC spec's
    stated precondition of "one or more rows selected").
  * Column order (table-head-0..6): Flow Name, Date, Trigger Count,
    SMS Count, Email Count, Voice Count, WhatsApp Count — CONFIRMED 7
    columns, i.e. one MORE than the TC spec's stated 6 (WhatsApp Count is
    present in the live DOM but absent from the spec's TC_SUM_003 list).
  * Pagination wire:click targets use TABLE_NAME + "Page"
    (nextPage('communication_flow_summary_reportPage')), unlike the
    plain TABLE_NAME used by every SMS/RCS report page's Next/Prev
    button — CONFIRMED live DOM. previousPage(...) itself was not
    observed (page 1 was the only page captured) so it is inferred by
    symmetry with nextPage, same inference this project already makes
    on sms_error_code_report_page.py.
  * "Applied Sorting" renders a removable chip per active sort
    (wire:click="clearSort('created_at')") plus a "Clear" button
    (wire:click.prevent="clearSorts") that clears ALL sorts. No
    "Applied Filters" chip was observed in the captured DOM (no filter
    was applied at capture time) even though filterPillsStatus: true
    exists in the wire:snapshot — so a filter chip is expected to appear
    the same way once a filter is applied, but its exact markup is
    inferred rather than confirmed.
  * No "No records / No data" empty-state markup was captured (the live
    page had 215 rows at capture time) — the NO_RECORDS_MSG locator
    below is the same generic best-effort fallback used across this
    project's other report pages, not a DOM-confirmed locator.
"""
import os
import time

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR


class FlowSummaryReportPage(BasePage):

    REPORT_URL = "/flow/summary"
    TABLE_NAME = "communication_flow_summary_report"
    PAGE_NAME = f"{TABLE_NAME}Page"

    # Confirmed column order from the live <thead> (table-head-0 .. -6).
    # Index 0 is the bulk-select checkbox column, so data columns start at 1.
    COLUMN_INDEX = {
        "flow_name": 1, "date": 2, "trigger_count": 3, "sms_count": 4,
        "email_count": 5, "voice_count": 6, "whatsapp_count": 7,
    }

    # ── Page header / tabs ───────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'Communication Flow Summary Report')]"
    TAB_FLOW = "xpath=//a[contains(normalize-space(.),'Flow')][not(contains(normalize-space(.),'Automation'))]"
    TAB_CAMPAIGNS = "xpath=//a[contains(@href,'/flow/campaign')]"
    TAB_SUMMARY = "xpath=//a[contains(@href,'/flow/summary')]"
    TAB_DETAILED = "xpath=//a[contains(@href,'/flow/detailed')]"

    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search']"

    # ── Filters popover ──────────────────────────────────────────────────────
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')]"
    FILTER_FROM_DATE = f"#{TABLE_NAME}-filter-from_date"
    FILTER_TO_DATE = f"#{TABLE_NAME}-filter-to_date"
    FILTER_FLOW_NAME_SELECT = f"#{TABLE_NAME}-filter-flow_name"

    # ── Applied Sorting / Filters chips ──────────────────────────────────────
    APPLIED_SORTING_LABEL = "xpath=//small[contains(normalize-space(.),'Applied Sorting')]"
    SORT_CHIP = (
        "xpath=//small[contains(normalize-space(.),'Applied Sorting')]"
        "/following-sibling::span[contains(@class,'rounded-full')]"
    )
    CLEAR_SORT_CHIP_BTN = f"xpath=//button[contains(@*[name()='wire:click'],\"clearSort(\")]"
    CLEAR_ALL_SORTS_BTN = "xpath=//button[contains(@*[name()='wire:click.prevent'],'clearSorts')]"
    APPLIED_FILTERS_LABEL = "xpath=//small[contains(normalize-space(.),'Applied Filter')]"
    FILTER_CHIP_REMOVE_BTN = (
        "xpath=//small[contains(normalize-space(.),'Applied Filter')]"
        "/following-sibling::span[contains(@class,'rounded-full')]//button"
    )

    # ── Bulk Actions / Export ────────────────────────────────────────────────
    BULK_ACTIONS_BUTTON = f"#{TABLE_NAME}-bulkActionsDropdown"
    BULK_ACTION_EXPORT_CSV = (
        f"xpath=//button[contains(@*[name()='wire:key'],'{TABLE_NAME}-bulk-action-export')]"
    )
    SELECT_ALL_CHECKBOX = (
        f"xpath=//table[@id='table-{TABLE_NAME}']//th[contains(@*[name()='wire:key'],"
        f"'{TABLE_NAME}-thead-bulk-actions')]//input[@type='checkbox']"
    )
    ROW_CHECKBOXES = f"xpath=//table[@id='table-{TABLE_NAME}']//tbody//input[@type='checkbox']"
    # CONFIRMED live DOM: delaySelectAll is false, so clicking the header
    # Select All checkbox does NOT tick each row's own checkbox -- it only
    # sets the server-side selectAllStatus flag (via $wire.setAllSelected())
    # and reveals a banner row (wire:key="{TABLE_NAME}-bulk-select-message")
    # reading "You are currently selecting all N rows." with a "Deselect
    # All" button. Individual row checkboxes staying unchecked while this
    # banner is shown is expected behaviour, not a bug.
    SELECT_ALL_BANNER = (
        "xpath=//*[contains(normalize-space(.),'You are currently selecting all')]"
    )
    DESELECT_ALL_BTN = "xpath=//button[contains(normalize-space(.),'Deselect All')]"

    # ── Columns dropdown ─────────────────────────────────────────────────────
    COLUMNS_BUTTON = "xpath=//button[contains(normalize-space(.),'Columns')]"
    # Chrome's native document.evaluate() rejects the "@wire:key" XPath
    # shorthand as an unresolvable namespace prefix (confirmed repeatedly on
    # every other report page in this project) -- use @*[name()='wire:key'].
    COLUMN_CHECKBOXES = (
        f"xpath=//div[contains(@*[name()='wire:key'],'{TABLE_NAME}-columnSelect-') and "
        f"not(contains(@*[name()='wire:key'],'columnSelect-selectAll'))]//input[@type='checkbox']"
    )
    COLUMN_SELECT_ALL_CHECKBOX = (
        f"xpath=//div[contains(@*[name()='wire:key'],'{TABLE_NAME}-columnSelect-selectAll')]"
        f"//input[@type='checkbox']"
    )

    # ── Table ─────────────────────────────────────────────────────────────────
    TABLE = f"#table-{TABLE_NAME}"
    TABLE_HEADERS = f"#table-{TABLE_NAME} thead th"
    TABLE_ROWS = f"#table-{TABLE_NAME} tbody tr"
    SORT_BTN = {
        "flow_name": "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('flow_name')\")]",
        "date": "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('created_at')\")]",
        "trigger_count": "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('trigger_count')\")]",
        "sms_count": "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('sms_count')\")]",
        "email_count": "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('email_count')\")]",
        "voice_count": "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('voice_count')\")]",
        "whatsapp_count": "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('whatsapp_count')\")]",
    }
    NO_RECORDS_MSG = (
        "xpath=//*[contains(text(),'No records') or contains(text(),'No data') "
        "or contains(text(),'No results')]"
    )

    # ── Pagination ────────────────────────────────────────────────────────────
    PAGINATION_RESULTS_TEXT = ".paged-pagination-results"
    NEXT_PAGE_BTN = f"xpath=//button[contains(@*[name()='wire:click'],\"nextPage('{PAGE_NAME}')\")]"
    PREV_PAGE_BTN = f"xpath=//button[contains(@*[name()='wire:click'],\"previousPage('{PAGE_NAME}')\")]"

    # ── Navigation / page state ─────────────────────────────────────────────

    def navigate_to_report(self):
        self.open(self.REPORT_URL)
        self.page.wait_for_timeout(2000)
        return self

    def is_report_page(self):
        url = self.get_current_url()
        return "/flow/summary" in url and "login" not in url.lower()

    def get_page_title_text(self):
        return self.h.wait_for_element_visible(self.PAGE_TITLE).inner_text().strip()

    def are_filters_visible(self):
        self.open_filters_popover()
        return (self.is_element_present(self.FILTER_FROM_DATE, timeout=5000)
                and self.is_element_present(self.FILTER_TO_DATE, timeout=5000)
                and self.is_element_present(self.FILTER_FLOW_NAME_SELECT, timeout=5000))

    def _is_visible(self, locator, timeout=1000):
        """Presence + visibility check, used to make the Filters/Columns/
        Bulk Actions toggle buttons idempotent -- each is a plain Alpine
        `open = !open` toggle, so calling its _js_click a second time while
        already open would close it instead of being a no-op (same
        rationale as every other report page in this project)."""
        try:
            return self.page.locator(locator).first.is_visible()
        except Exception:
            return False

    # ── Search ────────────────────────────────────────────────────────────────

    def search(self, value):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.fill(value)
        # This table's Livewire round-trip has been observed to take
        # noticeably longer than the other report pages' 1500ms -- a plain
        # has_records()/has_no_records_message() poll can't tell "stale
        # pre-request data" from "settled", since old rows stay in the DOM
        # (and therefore keep has_records() == True) until the response
        # actually lands, so this waits on a fixed, generous delay instead.
        self.page.wait_for_timeout(3000)

    def clear_search(self):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.fill("")
        self.page.wait_for_timeout(500)
        self.h.wait_until(
            lambda: self.has_records() or self.has_no_records_message(),
            timeout_ms=8000, interval_ms=500
        )
        self.page.wait_for_timeout(500)
        import re
        current_url = self.get_current_url()
        if re.search(r"[?&][\w-]*search=(?!&|$)[^&]+", current_url):
            self.navigate_to_report()

    # ── Table / rows ─────────────────────────────────────────────────────────

    def has_records(self):
        return self.is_element_present(self.TABLE_ROWS, timeout=5000) and self.get_row_count() > 0

    def has_no_records_message(self):
        if self.is_element_present(self.NO_RECORDS_MSG, timeout=3000):
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

    # ── Sorting ───────────────────────────────────────────────────────────────

    def sort_by(self, column_name):
        """Clicks the given column's sort header and waits for the
        "Applied Sorting" chip text to actually change before returning
        (rather than trusting a fixed sleep) -- this table's Livewire
        round-trip for a sort click has been observed to take longer than
        the flat 1500ms used elsewhere in this project. Returns True if
        the chip text changed within the timeout, False otherwise (best-
        effort signal for callers that want to distinguish "sort applied"
        from "no visible change yet")."""
        locator = self.SORT_BTN.get(column_name)
        if not locator:
            raise ValueError(f"Unknown sortable column: {column_name}")
        before = self.get_applied_sort_chip_text()
        self._js_click(locator, timeout=10000)
        changed = self.h.wait_until(
            lambda: self.get_applied_sort_chip_text() != before,
            timeout_ms=8000, interval_ms=400
        )
        self.page.wait_for_timeout(300)
        return changed

    def get_applied_sort_chip_text(self):
        if not self.is_element_present(self.SORT_CHIP, timeout=3000):
            return ""
        return self.page.locator(self.SORT_CHIP).first.inner_text().strip()

    def clear_sort_chip(self):
        before = self.get_applied_sort_chip_text()
        self._js_click(self.CLEAR_SORT_CHIP_BTN, timeout=5000)
        self.h.wait_until(
            lambda: self.get_applied_sort_chip_text() != before,
            timeout_ms=8000, interval_ms=400
        )
        self.page.wait_for_timeout(300)

    def clear_all_sorts(self):
        """NOTE: CONFIRMED live wire:snapshot: defaultSortColumn=
        "created_at", defaultSortDirection="desc" -- clearSorts() resets
        to that default rather than to "no sort at all", so the chip
        reappears rather than disappearing whenever the default sort IS
        the currently-applied one."""
        before = self.get_applied_sort_chip_text()
        self._js_click(self.CLEAR_ALL_SORTS_BTN, timeout=5000)
        self.h.wait_until(
            lambda: self.get_applied_sort_chip_text() != before,
            timeout_ms=8000, interval_ms=400
        )
        self.page.wait_for_timeout(300)

    # ── Filters popover ──────────────────────────────────────────────────────

    def open_filters_popover(self):
        if self._is_visible(self.FILTER_FLOW_NAME_SELECT, timeout=1000):
            return
        self._js_click(self.FILTERS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def filter_by_from_date(self, yyyy_mm_dd):
        self.open_filters_popover()
        box = self.h.wait_for_element_visible(self.FILTER_FROM_DATE)
        box.fill(yyyy_mm_dd)
        box.dispatch_event("change")
        self.page.wait_for_timeout(1500)

    def filter_by_to_date(self, yyyy_mm_dd):
        self.open_filters_popover()
        box = self.h.wait_for_element_visible(self.FILTER_TO_DATE)
        box.fill(yyyy_mm_dd)
        box.dispatch_event("change")
        self.page.wait_for_timeout(1500)

    def filter_by_flow_name(self, value):
        """value: '' (All) | any option value from the live <select>
        (e.g. an actual flow name, CONFIRMED plain <select>, not an
        async-select like the SMS/RCS report pages' Sender/Department/User
        filters)."""
        self.open_filters_popover()
        self.h.select_option(self.FILTER_FLOW_NAME_SELECT, value=value)
        self.page.wait_for_timeout(1500)

    def get_flow_name_filter_options(self):
        self.open_filters_popover()
        select = self.h.wait_for_element_visible(self.FILTER_FLOW_NAME_SELECT)
        return [o.strip() for o in select.locator("option").all_inner_texts() if o.strip()]

    def has_applied_filter_chip(self):
        return self.is_element_present(self.APPLIED_FILTERS_LABEL, timeout=3000)

    def remove_first_filter_chip(self):
        if not self.is_element_present(self.FILTER_CHIP_REMOVE_BTN, timeout=3000):
            return False
        self._js_click(self.FILTER_CHIP_REMOVE_BTN, timeout=5000)
        self.page.wait_for_timeout(1000)
        return True

    # ── Row / bulk selection ─────────────────────────────────────────────────

    def select_row_checkbox(self, index=0):
        boxes = self.page.locator(self.ROW_CHECKBOXES)
        if boxes.count() <= index:
            return False
        cb = boxes.nth(index)
        cb.scroll_into_view_if_needed()
        cb.click(force=True)
        self.page.wait_for_timeout(500)
        return True

    def is_row_selected(self, index=0):
        boxes = self.page.locator(self.ROW_CHECKBOXES)
        if boxes.count() <= index:
            return False
        return boxes.nth(index).is_checked()

    def click_select_all(self):
        self._js_click(self.SELECT_ALL_CHECKBOX, timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_select_all_checked(self):
        return self.page.locator(self.SELECT_ALL_CHECKBOX).first.is_checked()

    def get_selected_row_count(self):
        boxes = self.page.locator(self.ROW_CHECKBOXES)
        return sum(1 for i in range(boxes.count()) if boxes.nth(i).is_checked())

    def has_select_all_banner(self):
        """True once the "You are currently selecting all N rows." banner
        is visible -- CONFIRMED live behaviour (delaySelectAll: false) for
        what "select all" actually does on this table: it does NOT tick
        each row's own checkbox, it only flips a server-side flag and shows
        this banner."""
        return self.is_element_present(self.SELECT_ALL_BANNER, timeout=5000)

    def click_deselect_all(self):
        self._js_click(self.DESELECT_ALL_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    # ── Bulk Actions / Export ────────────────────────────────────────────────

    def open_bulk_actions_menu(self):
        if self._is_visible(self.BULK_ACTION_EXPORT_CSV, timeout=1000):
            return
        self._js_click(self.BULK_ACTIONS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def click_export_csv(self, timeout_ms=30000):
        """Opens the Bulk Actions dropdown and clicks "Export to CSV",
        capturing the resulting download via page.expect_download().

        Returns {"elapsed_s", "file_path", "file_size"} on success, or
        None on failure -- never-raises contract, same as every other
        report page in this project.
        """
        try:
            self.open_bulk_actions_menu()
            btn = self.h.wait_for_element_clickable(self.BULK_ACTION_EXPORT_CSV, timeout=10000)
            btn.scroll_into_view_if_needed()
            start = time.time()
            with self.page.expect_download(timeout=timeout_ms) as dl_info:
                self._js_click(self.BULK_ACTION_EXPORT_CSV, timeout=10000)
            download = dl_info.value
            filename = download.suggested_filename or "flow_summary_report_export.csv"
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

    def uncheck_first_optional_column(self):
        """Returns the unchecked checkbox's `value` attribute (e.g.
        'sms-count') on success, or None if there was nothing to uncheck.
        Waits for the header count to actually drop rather than a fixed
        sleep -- this table's Livewire round-trip for a column toggle has
        been observed to take longer than the 800ms used elsewhere in this
        project."""
        self.open_columns_dropdown()
        checkboxes = self.page.locator(self.COLUMN_CHECKBOXES)
        before_count = len(self.get_visible_column_headers())
        for i in range(checkboxes.count()):
            cb = checkboxes.nth(i)
            if cb.is_checked():
                value = cb.get_attribute("value")
                cb.scroll_into_view_if_needed()
                cb.click(force=True)
                self.h.wait_until(
                    lambda: len(self.get_visible_column_headers()) < before_count,
                    timeout_ms=8000, interval_ms=400
                )
                self.page.wait_for_timeout(300)
                return value
        return None

    def check_column(self, value):
        """Re-check a specific column checkbox by its `value` attribute.
        Column selection persists in sessionStorage (CONFIRMED live
        wire:snapshot: sessionStorageStatus.columnselect=true) and
        survives a plain navigate_to_report() -- used to restore state
        after uncheck_first_optional_column() in tests."""
        self.open_columns_dropdown()
        cb = self.page.locator(f"input[type='checkbox'][value='{value}']")
        if cb.count() == 0:
            return False
        cb = cb.first
        if not cb.is_checked():
            before_count = len(self.get_visible_column_headers())
            cb.scroll_into_view_if_needed()
            cb.click(force=True)
            self.h.wait_until(
                lambda: len(self.get_visible_column_headers()) > before_count,
                timeout_ms=8000, interval_ms=400
            )
            self.page.wait_for_timeout(300)
        return True

    # ── Pagination ────────────────────────────────────────────────────────────

    def get_pagination_results_text(self):
        return self.h.wait_for_element_visible(self.PAGINATION_RESULTS_TEXT).inner_text().strip()

    def click_next_page(self):
        before = self.get_column_values("flow_name")
        self._js_click(self.NEXT_PAGE_BTN + " >> visible=true", timeout=10000)
        self.h.wait_until(
            lambda: self.get_column_values("flow_name") != before,
            timeout_ms=8000, interval_ms=400
        )
        self.page.wait_for_timeout(300)

    def click_prev_page(self):
        before = self.get_column_values("flow_name")
        self._js_click(self.PREV_PAGE_BTN + " >> visible=true", timeout=10000)
        self.h.wait_until(
            lambda: self.get_column_values("flow_name") != before,
            timeout_ms=8000, interval_ms=400
        )
        self.page.wait_for_timeout(300)

    def is_next_page_enabled(self):
        locators = self.page.locator(self.NEXT_PAGE_BTN).all()
        for loc in locators:
            if loc.is_visible():
                return loc.get_attribute("disabled") is None
        return False

    def is_prev_page_enabled(self):
        locators = self.page.locator(self.PREV_PAGE_BTN).all()
        for loc in locators:
            if loc.is_visible():
                return loc.get_attribute("disabled") is None
        return False

    # ── Performance ──────────────────────────────────────────────────────────

    def get_page_load_time_ms(self):
        try:
            return self.page.evaluate(
                "() => window.performance.timing.loadEventEnd - "
                "window.performance.timing.navigationStart"
            )
        except Exception:
            return None
