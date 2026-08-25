import csv
import glob
import os
import time

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR


class WhatsappDownloadCenterPage(BasePage):

    DOWNLOAD_CENTER_PATH = "/whatsapp/channels/download/center"
    CREATE_PATH = "/whatsapp/channels/download/center/create"

    # Status constants (actual <select> option values - lowercase, confirmed)
    STATUS_PENDING    = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED  = "completed"
    STATUS_FAILED     = "failed"

    # Table
    TABLE         = "table"
    TABLE_ROWS    = "table tbody tr"
    TABLE_HEADERS = "table thead th"
    NO_RECORDS    = (
        "xpath=//*[contains(text(),'No items found') or contains(text(),'No records')"
        "    or contains(text(),'No data') or contains(text(),'No results')]"
    )
    PAGE_INFO     = "xpath=//*[contains(text(),'Showing') and contains(text(),'result')]"

    # Page header
    PAGE_TITLE = "xpath=//h1[normalize-space()='Whatsapp Download Center']"

    # Search
    SEARCH_BOX = "input[placeholder='Search by report name...']"

    # Filter panel (slide-down, opened via Alpine filtersOpen)
    BTN_FILTER = "xpath=//button[contains(normalize-space(),'Filters')][not(ancestor::table)]"

    # Status filter: native <select wire:model.live="filterComponents.status">
    FILTER_STATUS_SELECT = "#whatsapp_report_requests-filter-status"

    # Date range filter: Flatpickr on a text input, format: "dd-mm-yyyy to dd-mm-yyyy"
    FILTER_DATE_INPUT = "#whatsapp_report_requests-filter-dateRange-created_at"

    # Clear filters pill button
    BTN_CLEAR_FILTER = (
        "xpath=//button[.//*[normalize-space()='Clear'] or normalize-space()='Clear']"
        "[not(ancestor::table)]"
    )

    # Column sort headers (wire:click="sortBy(...)" - target by text, not attribute)
    HEADER_CREATED_AT = (
        "xpath=//th//button[contains(normalize-space(),'Created')]"
        " | //th[contains(normalize-space(),'Created') and not(.//button)]"
    )
    APPLIED_SORT_PILL = (
        "xpath=//small[contains(normalize-space(),'Applied Sorting')]"
        "/following-sibling::span[1]"
    )

    # Refresh link (<a> tag, NOT a <button>)
    REFRESH_LINK = "xpath=//a[contains(normalize-space(),'Refresh')][not(contains(@href,'create'))]"

    # Create New Report link
    CREATE_REPORT_LINK = (
        "xpath=//a[contains(normalize-space(),'Create') and contains(normalize-space(),'Report')]"
        " | //a[contains(@href,'create')]"
    )

    # ── Columns dropdown (confirmed present on THIS page; not on the SMS one) ─
    BTN_COLUMNS = "xpath=//button[contains(normalize-space(),'Columns')][not(ancestor::table)]"
    COLUMN_SELECT_ALL_CHECKBOX = (
        "xpath=//label[.//span[normalize-space()='All Columns']]//input[@type='checkbox']"
    )
    # Confirmed values: actions, name, category, from, to, created-at, status
    COLUMN_CHECKBOX_BY_VALUE_XPATH = "xpath=//input[@type='checkbox' and @value='{value}']"

    # Row action buttons - EXACT confirmed titles (differ from the SMS reference)
    ROW_VIEW_ICON = "xpath=(//button[@title='View Summary'])[1]"
    ROW_DOWNLOAD_ICON = "xpath=(//a[@title='Download Report'])[1]"
    ROW_DELETE_ICON = "xpath=(//button[@title='Delete Report'])[1]"

    # Delete confirmation: Livewire wire:confirm triggers the browser's NATIVE
    # confirm() dialog (confirmed from DOM) -- SweetAlert2 kept only as a
    # fallback path for parity with the SMS reference's dual strategy.
    DELETE_CONFIRM_BTN = "button.swal2-confirm, .swal2-actions .swal2-confirm"
    DELETE_CANCEL_BTN  = "button.swal2-cancel, .swal2-actions .swal2-cancel"
    SWAL2_CONTAINER    = ".swal2-container, .swal2-popup"

    # Summary / View modal (Livewire showSummaryModal -- confirmed property
    # name from this page's own wire:snapshot data)
    POPUP_CONTAINER = (
        "xpath=//div[@id='modal-container' and .//*[self::div or self::section]]"
        " | //div[@role='dialog']"
        " | //div[contains(@class,'fixed') and contains(@class,'inset') and .//h2]"
    )
    POPUP_CLOSE_BTN = (
        "xpath=//div[@id='modal-container']//button[contains(.,'Close') or @aria-label='Close'"
        "    or contains(.,'x') or contains(.,'X')]"
        " | //div[@role='dialog']//button[@aria-label='Close' or contains(.,'Close')]"
    )

    # Pagination (unconfirmed here - only 1 page of data was captured; kept
    # for parity with the shared livewire-tables pagination component)
    BTN_NEXT = (
        "xpath=//button[@aria-label='Next' or normalize-space()='Next' or"
        "         normalize-space()='Next Page'][not(@disabled)]"
        " | //nav//button[contains(.,'Next')][not(@disabled)]"
    )
    BTN_PREV = (
        "xpath=//button[@aria-label='Previous' or normalize-space()='Previous']"
        "[not(@disabled)]"
        " | //nav//button[contains(.,'Previous')][not(@disabled)]"
    )

    # -------------------------------------------------------------------------
    # Init — registers a page-level download listener. Playwright surfaces
    # downloads as an event on the page rather than as files that silently
    # appear in an OS folder the way Selenium's Chrome download prefs did,
    # so this listener is the migration's equivalent of the Selenium
    # version's OS-folder polling: every completed download gets saved into
    # DOWNLOAD_DIR and appended to self._downloaded_paths, which
    # snapshot_downloads()/wait_for_download() below consume.
    # -------------------------------------------------------------------------

    def __init__(self, page):
        super().__init__(page)
        self._downloaded_paths = []
        self.page.on("download", self._on_download)

    def _on_download(self, download):
        try:
            filename = download.suggested_filename or f"whatsapp_report_{int(time.time() * 1000)}.csv"
            dest = os.path.join(DOWNLOAD_DIR, filename)
            download.save_as(dest)
            self._downloaded_paths.append(dest)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Navigation
    # -------------------------------------------------------------------------

    def navigate(self):
        self.open(self.DOWNLOAD_CENTER_PATH)
        self.page.wait_for_timeout(1500)

    def is_download_center_page(self):
        url = self.get_current_url()
        return "download" in url.lower() and "whatsapp" in url.lower()

    def get_page_title_text(self):
        try:
            el = self.page.locator(self.PAGE_TITLE).first
            el.wait_for(state="visible", timeout=8000)
            return el.inner_text().strip()
        except Exception:
            return ""

    # -------------------------------------------------------------------------
    # Table helpers
    # -------------------------------------------------------------------------

    def wait_for_table_load(self, timeout=15000):
        try:
            self.h.wait_until(
                lambda: self.page.locator(self.TABLE_ROWS).count() > 0
                or self.page.locator(self.NO_RECORDS).count() > 0,
                timeout_ms=timeout, interval_ms=500
            )
            self.page.wait_for_timeout(500)
        except Exception:
            pass

    def get_row_count(self):
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            count = 0
            for i in range(rows.count()):
                if rows.nth(i).is_visible():
                    count += 1
            return count
        except Exception:
            return 0

    def get_table_headers(self):
        try:
            ths = self.page.locator(self.TABLE_HEADERS)
            result = []
            for i in range(ths.count()):
                text = ths.nth(i).inner_text().strip()
                if text:
                    result.append(text)
            return result
        except Exception:
            return []

    def get_cell_text(self, row_idx, col_idx):
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            if row_idx >= rows.count():
                return ""
            cols = rows.nth(row_idx).locator("td")
            if col_idx >= cols.count():
                return ""
            return cols.nth(col_idx).inner_text().strip()
        except Exception:
            return ""

    def is_no_records_visible(self):
        try:
            els = self.page.locator(self.NO_RECORDS)
            for i in range(els.count()):
                if els.nth(i).is_visible():
                    return True
            return False
        except Exception:
            return False

    def get_status_column_index(self):
        headers = self.get_table_headers()
        return next(
            (i for i, h in enumerate(headers) if "status" in h.lower()), -1
        )

    def get_row_status(self, row_idx):
        col_idx = self.get_status_column_index()
        if col_idx < 0:
            return ""
        return self.get_cell_text(row_idx, col_idx)

    def find_row_with_status(self, status_text):
        """Return index of first row whose Status cell matches (case-insensitive), or -1."""
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            col_idx = self.get_status_column_index()
            for idx in range(rows.count()):
                cells = rows.nth(idx).locator("td")
                if col_idx < cells.count():
                    if status_text.lower() in cells.nth(col_idx).inner_text().strip().lower():
                        return idx
        except Exception:
            pass
        return -1

    # -------------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------------

    def search(self, text):
        try:
            box = self.h.wait_for_element_clickable(self.SEARCH_BOX, timeout=10000)
            box.fill("")
            box.fill(text)
            self.page.wait_for_timeout(1500)
        except Exception:
            pass

    def clear_search(self):
        try:
            box = self.page.locator(self.SEARCH_BOX).first
            box.fill("")
            box.press("Enter")
            self.page.wait_for_timeout(1000)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Filter panel
    # -------------------------------------------------------------------------

    def open_filter_panel(self):
        """Click the Filters button to slide the filter panel open."""
        try:
            self._js_click(self.BTN_FILTER, timeout=10000)
            self.page.wait_for_timeout(600)
        except Exception:
            pass

    def set_filter_status(self, value):
        """
        Set the status filter.
        value: 'pending' | 'processing' | 'completed' | 'failed' | '' (All)

        Observed in a live run against a slower environment: a single
        select_option() + fixed 1s sleep sometimes left the table showing
        unfiltered rows (e.g. a 'completed' row appeared under a
        'processing' filter) -- either the native select-option click
        didn't register on the first try, or Livewire's wire:model.live
        round-trip hadn't finished yet. This now verifies the underlying
        <select> element's value actually changed, retries with a forced
        JS value-set + dispatched change/input events if not, and only
        falls back to poking the Livewire component's
        filterComponents.status property directly (bypassing the <select>
        DOM entirely) as a last resort.
        """
        val = value.lower()
        applied = False
        for attempt in range(3):
            try:
                el = self.h.wait_for_element_clickable(self.FILTER_STATUS_SELECT, timeout=8000)
                self.h.select_option(self.FILTER_STATUS_SELECT, value=val)
                self.page.wait_for_timeout(600)
                if (el.input_value() or "").lower() == val:
                    applied = True
                    break
            except Exception:
                pass
            try:
                el = self.page.locator(self.FILTER_STATUS_SELECT).first
                el.evaluate(
                    "(elm, v) => { elm.value = v;"
                    "elm.dispatchEvent(new Event('input', {bubbles: true}));"
                    "elm.dispatchEvent(new Event('change', {bubbles: true})); }",
                    val
                )
                self.page.wait_for_timeout(600)
                if (el.input_value() or "").lower() == val:
                    applied = True
                    break
            except Exception:
                pass
            self.page.wait_for_timeout(500)
        if not applied:
            try:
                self.page.evaluate(
                    "(v) => { window.Livewire && window.Livewire.all().forEach(function(c) {"
                    "  try { c.set('filterComponents.status', v); } catch(e) {}"
                    "}); }",
                    val
                )
            except Exception:
                pass
        # Extra settle time for Livewire's network round-trip regardless
        # of which path applied the value -- the table re-render is not
        # instant even once the <select> itself reflects the new value.
        self.page.wait_for_timeout(2000)
        return applied

    def set_date_filter(self, from_date, to_date):
        """
        Set the date range filter (Flatpickr, format dd-mm-yyyy).
        from_date / to_date: 'YYYY-MM-DD' string.
        """
        def fmt(d):
            parts = str(d).split("-")
            return "{2}-{1}-{0}".format(*parts) if len(parts) == 3 else str(d)

        from_fmt  = fmt(from_date)
        to_fmt    = fmt(to_date)
        range_str = from_fmt + " to " + to_fmt

        # Primary: set via Flatpickr text input + change event
        try:
            inp = self.page.locator(self.FILTER_DATE_INPUT).first
            inp.wait_for(state="attached", timeout=8000)
            inp.evaluate(
                "(el, v) => { el.value = v;"
                "el.dispatchEvent(new Event('input',  {bubbles:true}));"
                "el.dispatchEvent(new Event('change', {bubbles:true})); }",
                range_str
            )
            self.page.wait_for_timeout(400)
        except Exception:
            pass

        # Flatpickr JS API
        try:
            self.page.evaluate(
                "([f, t]) => { var el = document.getElementById("
                "  'whatsapp_report_requests-filter-dateRange-created_at');"
                "if(el && el._flatpickr) {"
                "  el._flatpickr.setDate([f, t], true);"
                "} }",
                [from_fmt, to_fmt]
            )
            self.page.wait_for_timeout(400)
        except Exception:
            pass

        # Livewire JS fallback
        try:
            self.page.evaluate(
                "([f, t]) => { window.Livewire && window.Livewire.all().forEach(function(c) {"
                "  try { c.set('filterComponents.created_at',"
                "    [{minDate: f, maxDate: t}, {s:'arr'}]);"
                "  } catch(e) {}"
                "}); }",
                [from_fmt, to_fmt]
            )
            self.page.wait_for_timeout(1000)
        except Exception:
            pass

    def apply_filter(self):
        """No-op: filters are wire:model.live - no Apply button exists."""
        self.page.wait_for_timeout(1500)

    def clear_filter(self):
        """Reset all filters via Clear pill button or Livewire JS."""
        try:
            btn = self.page.locator(self.BTN_CLEAR_FILTER).first
            btn.wait_for(state="visible", timeout=5000)
            btn.click(force=True)
            self.page.wait_for_timeout(1000)
            return
        except Exception:
            pass
        try:
            self.page.evaluate(
                "() => { window.Livewire && window.Livewire.all().forEach(function(c) {"
                "  try {"
                "    c.set('filterComponents', {created_at: null, status: null});"
                "    c.set('search', '');"
                "  } catch(e) {}"
                "}); }"
            )
            self.page.wait_for_timeout(1000)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Columns dropdown (confirmed present on this page)
    # -------------------------------------------------------------------------

    def open_columns_panel(self):
        try:
            self._js_click(self.BTN_COLUMNS, timeout=10000)
            self.page.wait_for_timeout(500)
        except Exception:
            pass

    def is_column_checkbox_present(self, value):
        try:
            xpath = self.COLUMN_CHECKBOX_BY_VALUE_XPATH.format(value=value)
            return self.page.locator(xpath).count() > 0
        except Exception:
            return False

    def toggle_column(self, value):
        """Toggle a column's visibility checkbox by its confirmed value
        (actions/name/category/from/to/created-at/status)."""
        try:
            xpath = self.COLUMN_CHECKBOX_BY_VALUE_XPATH.format(value=value)
            cb = self.page.locator(xpath).first
            cb.wait_for(state="attached", timeout=5000)
            cb.click(force=True)
            self.page.wait_for_timeout(800)
        except Exception:
            pass

    def get_column_checkbox_state(self, value):
        try:
            xpath = self.COLUMN_CHECKBOX_BY_VALUE_XPATH.format(value=value)
            return self.page.locator(xpath).first.is_checked()
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # Sorting
    # -------------------------------------------------------------------------

    def click_created_at_header(self):
        """Click the Created at column header to toggle sort order."""
        try:
            self._js_click(self.HEADER_CREATED_AT, timeout=10000)
            self.page.wait_for_timeout(1500)
        except Exception:
            try:
                self.page.evaluate(
                    "() => { window.Livewire && window.Livewire.all().forEach(function(c) {"
                    "  try { c.call('sortBy', 'created_at'); } catch(e) {}"
                    "}); }"
                )
                self.page.wait_for_timeout(1500)
            except Exception:
                pass

    def get_applied_sort_pill_text(self):
        try:
            return self.page.locator(self.APPLIED_SORT_PILL).first.inner_text().strip()
        except Exception:
            return ""

    def get_created_at_values(self):
        """Return list of Created at cell texts from all visible rows."""
        try:
            headers = self.get_table_headers()
            col_idx = next(
                (i for i, h in enumerate(headers)
                 if "created" in h.lower() or "date" in h.lower()),
                -1
            )
            if col_idx < 0:
                return []
            rows = self.page.locator(self.TABLE_ROWS)
            vals = []
            for i in range(rows.count()):
                cells = rows.nth(i).locator("td")
                if col_idx < cells.count():
                    vals.append(cells.nth(col_idx).inner_text().strip())
            return vals
        except Exception:
            return []

    # -------------------------------------------------------------------------
    # Refresh (it's an <a> link, not a button)
    # -------------------------------------------------------------------------

    def click_refresh(self):
        """Click the Refresh <a> link."""
        try:
            self._js_click(self.REFRESH_LINK, timeout=8000)
            self.page.wait_for_timeout(2500)
        except Exception:
            try:
                self.page.reload()
                self.page.wait_for_timeout(2500)
            except Exception:
                pass

    # -------------------------------------------------------------------------
    # Row action buttons
    # -------------------------------------------------------------------------

    def _action_btn_for_row(self, row_idx, icon_type):
        """Locate action element (view/download/delete) in a specific table
        row using the EXACT confirmed title attributes for this page:
        "View Summary" / "Download Report" / "Delete Report"."""
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            if row_idx >= rows.count():
                return None
            row = rows.nth(row_idx)
            title_values = {
                "view":     ["View Summary"],
                "download": ["Download Report"],
                "delete":   ["Delete Report"],
            }
            for attr_val in title_values.get(icon_type, []):
                try:
                    el = row.locator(f"xpath=.//*[@title=\"{attr_val}\"]").first
                    if el.count() > 0 and el.is_visible():
                        return el
                except Exception:
                    pass
            # Positional fallback -- Actions column is the first <td>,
            # icon order confirmed as: View Summary, Download, (Delete last).
            cells = row.locator("td")
            if cells.count() == 0:
                return None
            pos_map = {"view": 0, "download": 1, "delete": -1}
            action_cell = cells.nth(0)
            btns = action_cell.locator("xpath=.//button | .//a")
            p = pos_map.get(icon_type, 0)
            count = btns.count()
            if count:
                try:
                    idx = p if p >= 0 else count + p
                    candidate = btns.nth(idx)
                    if candidate.is_visible():
                        return candidate
                except Exception:
                    pass
        except Exception:
            pass
        return None

    def click_view_icon(self, row_idx=0):
        btn = self._action_btn_for_row(row_idx, "view")
        if btn is not None:
            try:
                btn.scroll_into_view_if_needed()
                btn.click(force=True)
            except Exception:
                pass
        else:
            try:
                el = self.h.wait_for_element_clickable(self.ROW_VIEW_ICON, timeout=8000)
                el.click(force=True)
            except Exception:
                pass
        self.page.wait_for_timeout(1500)

    def click_download_icon(self, row_idx=0):
        """
        Click the download action for the given row.
        Does NOT sleep long after clicking -- callers needing a delay
        should use snapshot_downloads() + wait_for_download() which poll
        properly (same pattern as SMS/RCS). The actual download event is
        captured by the page-level listener registered in __init__.
        """
        clicked = False

        btn = self._action_btn_for_row(row_idx, "download")
        if btn is not None:
            try:
                btn.scroll_into_view_if_needed()
                btn.click(force=True)
                clicked = True
            except Exception:
                pass

        if not clicked:
            try:
                el = self.h.wait_for_element_clickable(self.ROW_DOWNLOAD_ICON, timeout=8000)
                el.scroll_into_view_if_needed()
                el.click(force=True)
                clicked = True
            except Exception:
                pass

        self.page.wait_for_timeout(500)

    def is_download_btn_disabled(self, row_idx=0):
        """Return True if the Download element is absent, disabled, or not clickable."""
        btn = self._action_btn_for_row(row_idx, "download")
        if btn is None:
            return True
        try:
            disabled = btn.get_attribute("disabled")
            cls = btn.get_attribute("class") or ""
            href = btn.get_attribute("href") or ""
        except Exception:
            return True
        return (
            bool(disabled)
            or "disabled"           in cls.lower()
            or "cursor-not-allowed" in cls
            or "opacity-50"         in cls
            or href.strip() == "#"
        )

    def click_delete_icon(self, row_idx=0):
        """
        Click the delete action for the given row.

        Two real Selenium runs of this suite showed TC12 failing at the
        exact same point ("Delete confirmation did not appear") across two
        different click strategies (JS-dispatched click, then a native
        Selenium .click()) -- since changing the click mechanism didn't
        change the outcome, the click mechanism probably wasn't the actual
        cause. A native confirm() dialog blocks page script execution
        until answered, which means the click that triggers it never
        "finishes" from Playwright's point of view until the dialog is
        handled -- so the handler must be registered with
        page.once("dialog", ...) BEFORE the click, not awaited afterward.
        This method registers a handler that simply records the dialog and
        leaves it open (native dialogs cannot be "left open" across two
        separate Python calls the way Selenium's driver.switch_to.alert
        could, so is_delete_modal_visible() / confirm_delete() /
        cancel_delete() below are adapted to work off of a flag rather
        than a live dialog handle -- see their docstrings). Also records
        debug evidence (button found? which tag/title/outerHTML? row
        status/count at call time) into self.last_delete_click_debug so a
        failing test can surface it instead of leaving another unexplained
        assertion.
        """
        debug = {
            "btn_found": False,
            "btn_tag": None,
            "btn_title": None,
            "btn_href": None,
            "btn_outer_html": None,
            "click_method": None,
            "click_error": None,
            "alert_seen_after_click": False,
            "row_status": None,
            "row_count_at_call": None,
            "actions_cell_outer_html": None,
        }

        try:
            debug["row_count_at_call"] = self.get_row_count()
            debug["row_status"] = self.get_row_status(row_idx)
            rows = self.page.locator(self.TABLE_ROWS)
            if row_idx < rows.count():
                cells = rows.nth(row_idx).locator("td")
                if cells.count() > 0:
                    debug["actions_cell_outer_html"] = (
                        cells.nth(0).evaluate("el => el.outerHTML") or ""
                    )[:600]
        except Exception:
            pass

        btn = self._action_btn_for_row(row_idx, "delete")
        if btn is None:
            try:
                btn = self.h.wait_for_element_clickable(self.ROW_DELETE_ICON, timeout=8000)
            except Exception:
                btn = None

        if btn is not None:
            debug["btn_found"] = True
            try:
                debug["btn_tag"] = btn.evaluate("el => el.tagName")
                debug["btn_title"] = btn.get_attribute("title")
                debug["btn_href"] = btn.get_attribute("href")
                debug["btn_outer_html"] = (btn.evaluate("el => el.outerHTML") or "")[:400]
            except Exception as exc:
                debug["click_error"] = "attr read failed: " + str(exc)

        self._pending_native_dialog = False
        self._native_dialog_handled = False

        def _capture_dialog(dialog):
            self._pending_native_dialog = True
            self._native_dialog_obj = dialog

        clicked = False
        if btn is not None:
            try:
                btn.scroll_into_view_if_needed()
                self.page.wait_for_timeout(200)
                self.page.once("dialog", _capture_dialog)
                btn.click(force=True)
                clicked = True
                debug["click_method"] = "js_forced_click"
            except Exception as exc:
                debug["click_error"] = "click failed: " + str(exc)

        if clicked:
            self.page.wait_for_timeout(600)
            if getattr(self, "_pending_native_dialog", False):
                debug["alert_seen_after_click"] = True
        self.page.wait_for_timeout(500)

        self.last_delete_click_debug = debug
        return debug

    def confirm_delete(self):
        """
        Accept the delete confirmation.
        Tries the native dialog captured by click_delete_icon() first
        (CONFIRMED as the mechanism here via wire:confirm), then
        SweetAlert2 as a fallback.

        Observed in a live run against a slower environment: a modal could
        be detected and accepted without error, yet the row count still
        didn't decrease (before=1, after=1) -- meaning the accept happened
        but either the server-side delete didn't take effect, or something
        else kept the row matching. Records which path was taken (native
        alert vs SweetAlert2 vs neither) in self.last_confirm_delete_debug
        so the calling test can surface it on failure instead of leaving
        this as an unexplained assertion — same evidence-first pattern
        already used in click_delete_icon().
        """
        debug = {"path": None, "error": None}
        if getattr(self, "_pending_native_dialog", False):
            try:
                self._native_dialog_obj.accept()
                self._pending_native_dialog = False
                debug["path"] = "native_alert"
                self.last_confirm_delete_debug = debug
                self.page.wait_for_timeout(3500)
                return
            except Exception as exc:
                debug["error"] = "native alert accept failed: " + str(exc)
        try:
            btn = self.page.locator(self.DELETE_CONFIRM_BTN).first
            btn.wait_for(state="visible", timeout=5000)
            btn.click(force=True)
            debug["path"] = "sweetalert2"
            self.page.wait_for_timeout(3500)
        except Exception as exc2:
            debug["path"] = "neither"
            debug["error"] = (debug["error"] or "") + " | sweetalert2 click also failed: " + str(exc2)
        self.last_confirm_delete_debug = debug

    def cancel_delete(self):
        """
        Dismiss the delete confirmation.
        Tries the native dialog captured by click_delete_icon() first
        (confirmed mechanism), then SweetAlert2 fallback.
        """
        if getattr(self, "_pending_native_dialog", False):
            try:
                self._native_dialog_obj.dismiss()
                self._pending_native_dialog = False
                self.page.wait_for_timeout(500)
                return
            except Exception:
                pass
        try:
            btn = self.page.locator(self.DELETE_CANCEL_BTN).first
            btn.wait_for(state="visible", timeout=5000)
            btn.click(force=True)
            self.page.wait_for_timeout(500)
        except Exception:
            pass

    def is_delete_modal_visible(self):
        """
        Return True if a delete confirmation is open.
        Checks the pending-native-dialog flag set by click_delete_icon()
        first (confirmed mechanism), then SweetAlert2.
        """
        if getattr(self, "_pending_native_dialog", False):
            return True
        try:
            els = self.page.locator(self.SWAL2_CONTAINER)
            for i in range(els.count()):
                if els.nth(i).is_visible():
                    return True
        except Exception:
            pass
        return False

    def dismiss_any_alert(self):
        """Silently dismiss a pending native browser alert/confirm, if any."""
        if getattr(self, "_pending_native_dialog", False):
            try:
                self._native_dialog_obj.dismiss()
            except Exception:
                pass
            self._pending_native_dialog = False

    # -------------------------------------------------------------------------
    # Summary / View popup
    # -------------------------------------------------------------------------

    def is_popup_open(self):
        """Return True if the summary/detail modal is currently visible.
        Checks Livewire's showSummaryModal property -- CONFIRMED present by
        this exact name in this page's own wire:snapshot data."""
        try:
            result = self.page.evaluate(
                "() => window.Livewire ? window.Livewire.all().some(function(c) {"
                "  try { return c.get('showSummaryModal') === true; }"
                "  catch(e) { return false; }"
                "}) : false"
            )
            if result:
                return True
        except Exception:
            pass
        try:
            els = self.page.locator(self.POPUP_CONTAINER)
            for i in range(els.count()):
                if els.nth(i).is_visible():
                    return True
            return False
        except Exception:
            return False

    def get_popup_all_text(self):
        try:
            return self.page.locator(self.POPUP_CONTAINER).first.inner_text().strip()
        except Exception:
            return ""

    def close_popup(self):
        try:
            btn = self.h.wait_for_element_clickable(self.POPUP_CLOSE_BTN, timeout=5000)
            btn.click()
            self.page.wait_for_timeout(800)
            return
        except Exception:
            pass
        try:
            self.page.evaluate(
                "() => { window.Livewire && window.Livewire.all().forEach(function(c) {"
                "  try { c.set('showSummaryModal', false); } catch(e) {}"
                "}); }"
            )
            self.page.wait_for_timeout(500)
        except Exception:
            pass
        try:
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(500)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Pagination
    # -------------------------------------------------------------------------

    def click_next_page(self):
        try:
            self._js_click(self.BTN_NEXT, timeout=5000)
            self.page.wait_for_timeout(2000)
        except Exception:
            pass

    def is_next_page_enabled(self):
        try:
            btns = self.page.locator(self.BTN_NEXT)
            for i in range(btns.count()):
                b = btns.nth(i)
                if b.is_enabled() and b.is_visible():
                    return True
            return False
        except Exception:
            return False

    def get_page_info_text(self):
        try:
            return self.page.locator(self.PAGE_INFO).first.inner_text().strip()
        except Exception:
            return ""

    # -------------------------------------------------------------------------
    # Download file helpers
    # -------------------------------------------------------------------------

    _INCOMPLETE_SUFFIXES = (".crdownload", ".part", ".tmp")

    _FALLBACK_DIRS = [
        os.path.join(os.path.expanduser("~"), "Downloads"),
        os.path.join(os.path.expanduser("~"), "Desktop"),
        os.path.join(os.path.expanduser("~"), "OneDrive", "Downloads"),
    ]

    def clear_download_dir(self):
        """Remove ALL files from DOWNLOAD_DIR before a download test."""
        for f in glob.glob(os.path.join(DOWNLOAD_DIR, "*")):
            if os.path.isfile(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    def _list_complete_files(self, directory):
        try:
            return {
                f for f in glob.glob(os.path.join(directory, "*"))
                if os.path.isfile(f)
                and not any(f.endswith(s) for s in self._INCOMPLETE_SUFFIXES)
            }
        except Exception:
            return set()

    def snapshot_downloads(self):
        """Capture a snapshot of files present in watched download dirs
        BEFORE clicking download, to avoid missing fast downloads. Kept for
        API parity with the Selenium suite's before/after pattern —
        click_download_icon() + wait_for_download() now mainly rely on
        Playwright's native download event (self._downloaded_paths), but
        the filesystem snapshot is still returned/consumed here in case a
        download bypasses the event (e.g. opens in a new tab)."""
        watch_dirs = [DOWNLOAD_DIR] + [
            d for d in self._FALLBACK_DIRS if os.path.isdir(d)
        ]
        return {d: self._list_complete_files(d) for d in watch_dirs}

    def wait_for_download(self, timeout=60, before=None):
        """Wait up to timeout seconds for a new complete file to appear —
        checks Playwright's captured download events first (fast path),
        then falls back to polling the watched directories for parity with
        the original Selenium approach."""
        deadline = time.time() + timeout
        start_count = len(self._downloaded_paths)

        watch_dirs = [DOWNLOAD_DIR] + [
            d for d in self._FALLBACK_DIRS if os.path.isdir(d)
        ]
        if before is None:
            before = {d: self._list_complete_files(d) for d in watch_dirs}
        else:
            for d in watch_dirs:
                if d not in before:
                    before[d] = set()

        while time.time() < deadline:
            if len(self._downloaded_paths) > start_count:
                return self._downloaded_paths[-1]
            for d in watch_dirs:
                current = self._list_complete_files(d)
                new_files = current - before[d]
                finished = [
                    f for f in new_files
                    if not any(f.endswith(s) for s in self._INCOMPLETE_SUFFIXES)
                ]
                if finished:
                    return max(finished, key=os.path.getmtime)
            time.sleep(1)
        return None

    def get_csv_headers(self, file_path):
        try:
            with open(file_path, newline="", encoding="utf-8-sig") as fh:
                headers = next(csv.reader(fh), [])
                return [h.strip() for h in headers]
        except Exception:
            return []

    def get_csv_row_count(self, file_path):
        try:
            with open(file_path, newline="", encoding="utf-8-sig") as fh:
                return max(0, len(list(csv.reader(fh))) - 1)
        except Exception:
            return 0

    # -------------------------------------------------------------------------
    # Performance
    # -------------------------------------------------------------------------

    def measure_load_time_ms(self):
        try:
            return self.page.evaluate(
                "() => { var t = window.performance.timing;"
                "return t.domContentLoadedEventEnd - t.navigationStart; }"
            ) or 0
        except Exception:
            return 0
