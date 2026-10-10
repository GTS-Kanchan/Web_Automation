import csv
import glob
import os
import time

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR


class SMSDownloadCenterPage(BasePage):

    DOWNLOAD_CENTER_PATH = "/channels/sms/download/center"

    # Status constants (actual <select> option values - lowercase)
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

    # Search
    SEARCH_BOX = "input[placeholder='Search by report name...']"

    # Filter panel (slide-down, opened via Alpine filtersOpen)
    BTN_FILTER = "xpath=//button[contains(normalize-space(),'Filters')][not(ancestor::table)]"

    # Status filter: native <select wire:model.live="filterComponents.status">
    FILTER_STATUS_SELECT = "#sms_report_requests-filter-status"

    # Date range filter: Flatpickr on a text input, format: "dd-mm-yyyy to dd-mm-yyyy"
    FILTER_DATE_INPUT = "#sms_report_requests-filter-dateRange-created_at"

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

    # Refresh link (<a> tag, NOT a <button>)
    REFRESH_LINK = "xpath=//a[contains(normalize-space(),'Refresh')][not(contains(@href,'create'))]"

    # Create New Report link
    CREATE_REPORT_LINK = (
        "xpath=//a[contains(normalize-space(),'Create') and contains(normalize-space(),'Report')]"
        " | //a[contains(@href,'create')]"
    )

    # Row action buttons
    # NOTE: a real pasted screenshot (2026-10-10) confirms the row action
    # tooltips read "Delete Report" (and presumably "View Report"/
    # "Download Report" by the same naming convention), not the bare
    # "View"/"Download"/"Delete" these locators originally assumed --
    # switched to contains() so the primary locator matches directly
    # instead of relying on the positional-cell fallback in
    # _action_btn_for_row().
    ROW_VIEW_ICON = (
        "xpath=(//button[contains(@title,'View') or contains(@aria-label,'View')"
        "  or contains(@data-tooltip,'View') or contains(@class,'view')])[1]"
        " | (//a[contains(@title,'View') or contains(@aria-label,'View')])[1]"
    )
    ROW_DOWNLOAD_ICON = (
        "xpath=(//button[contains(@title,'Download') or contains(@aria-label,'Download')"
        "  or contains(@data-tooltip,'Download')])[1]"
        " | (//a[contains(@title,'Download') or contains(@aria-label,'Download')"
        "       or (contains(@href,'download') and not(contains(@href,'center')))])[1]"
    )
    ROW_DELETE_ICON = (
        "xpath=(//button[contains(@title,'Delete') or contains(@aria-label,'Delete')"
        "  or contains(@data-tooltip,'Delete')"
        "  or contains(@class,'delete') or contains(@class,'trash')])[1]"
    )

    # Delete confirmation: this is a NATIVE browser confirm() dialog --
    # CONFIRMED via a real pasted screenshot (2026-10-10) showing a
    # plain browser-chrome "<host> says: Are you sure you want to delete
    # this report?" prompt with OK/Cancel, not a styled SweetAlert2
    # popup. The SweetAlert2 locators below are kept only as a
    # best-effort fallback in case a different environment/build uses a
    # styled modal instead -- click_delete_icon()/confirm_delete()/
    # is_delete_modal_visible() all check the native dialog path first.
    DELETE_CONFIRM_BTN = "button.swal2-confirm, .swal2-actions .swal2-confirm"
    DELETE_CANCEL_BTN  = "button.swal2-cancel, .swal2-actions .swal2-cancel"
    SWAL2_CONTAINER    = ".swal2-container, .swal2-popup"

    # Summary / View modal (Livewire showSummaryModal)
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

    # Summary popup date/date-time fields -- CONFIRMED from a real pasted
    # DOM of the "Automated Report - <N> Days - Summary" modal:
    #   <p>Generated at: 28-09-2026 13:47:26</p>
    #   <p>Completed at: 28-09-2026 13:47:34</p>
    #   <p><span>Period:</span> 08-09-2026 - 27-09-2026</p>
    # (Generated at / Completed at are date-time; Period is a date-only
    # RANGE -- "dd-mm-yyyy - dd-mm-yyyy" -- not a single value.)
    POPUP_GENERATED_AT_TEXT = (
        "xpath=(//*[@id='modal-container' or @role='dialog'"
        "    or (contains(@class,'fixed') and contains(@class,'inset'))]"
        "//p[contains(normalize-space(.),'Generated at:')])[1]"
    )
    POPUP_COMPLETED_AT_TEXT = (
        "xpath=(//*[@id='modal-container' or @role='dialog'"
        "    or (contains(@class,'fixed') and contains(@class,'inset'))]"
        "//p[contains(normalize-space(.),'Completed at:')])[1]"
    )
    POPUP_PERIOD_TEXT = (
        "xpath=(//*[@id='modal-container' or @role='dialog'"
        "    or (contains(@class,'fixed') and contains(@class,'inset'))]"
        "//p[.//span[normalize-space()='Period:']])[1]"
    )

    # Pagination
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
        # Real-run fix (2026-10-10): a real run showed wait_for_download()
        # returning None (timeout) even though the failure message's own
        # network capture proved the click DID land on a real download
        # link and the browser DID receive a 200 response for the actual
        # file bytes (an S3 object URL, not a status-poll endpoint) --
        # i.e. the download genuinely happened at the network level, but
        # something after that was never recorded. _on_download below used
        # to swallow any exception from download.save_as() silently
        # ("except Exception: pass"), which would produce exactly this
        # symptom: Playwright's 'download' event DOES fire (so the browser
        # really did download it), but if save_as() ever throws, nothing
        # is appended to _downloaded_paths and no trace of the failure
        # survives anywhere. These counters/lists make that distinction
        # observable instead of invisible: _download_events_seen proves
        # whether the event fired at all; _download_errors captures
        # exactly why a save attempt failed, if it did.
        self._download_events_seen = 0
        self._download_errors = []
        self.page.on("download", self._on_download)

    def _on_download(self, download):
        self._download_events_seen += 1
        try:
            os.makedirs(DOWNLOAD_DIR, exist_ok=True)
            filename = download.suggested_filename or f"sms_report_{int(time.time() * 1000)}.csv"
            dest = os.path.join(DOWNLOAD_DIR, filename)
            download.save_as(dest)
            self._downloaded_paths.append(dest)
        except Exception as exc:
            self._download_errors.append(f"{type(exc).__name__}: {exc}")
            # save_as() failing doesn't mean the download itself failed --
            # Playwright keeps the completed download at its own internal
            # temp path (download.path()) regardless of whether save_as()
            # could copy it to DOWNLOAD_DIR. Try that as a fallback before
            # giving up entirely, so a save_as()-specific problem (a bad
            # destination path, a permissions issue, ...) doesn't also
            # cost us the file itself.
            try:
                internal_path = download.path()
                if internal_path:
                    self._downloaded_paths.append(internal_path)
            except Exception as exc2:
                self._download_errors.append(
                    f"fallback download.path() also failed: "
                    f"{type(exc2).__name__}: {exc2}"
                )

    def get_download_diagnostics(self):
        """Real evidence for a wait_for_download() timeout's failure
        message: distinguishes "the browser's download event never fired
        at all" (events_seen == 0 -- a real locator/click/network problem)
        from "it fired but something after that went wrong" (events_seen
        > 0, errors non-empty -- see _download_errors for exactly what)."""
        return {
            "events_seen": self._download_events_seen,
            "errors": list(self._download_errors),
            "saved_paths": list(self._downloaded_paths),
        }

    # -------------------------------------------------------------------------
    # Navigation
    # -------------------------------------------------------------------------

    def navigate(self):
        self.open(self.DOWNLOAD_CENTER_PATH)
        self.page.wait_for_timeout(1500)

    def is_download_center_page(self):
        url = self.get_current_url()
        return "download" in url.lower() and "sms" in url.lower()

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

    def get_status_badge_classes(self, row_idx):
        """Return CSS class string of the status badge in the given row."""
        try:
            col_idx = self.get_status_column_index()
            rows = self.page.locator(self.TABLE_ROWS)
            if row_idx >= rows.count():
                return ""
            cells = rows.nth(row_idx).locator("td")
            if col_idx < cells.count():
                cell = cells.nth(col_idx)
                try:
                    badge = cell.locator(
                        "xpath=.//*[contains(@class,'badge') or contains(@class,'status')"
                        "     or contains(@class,'rounded') or self::span]"
                    ).first
                    if badge.count() > 0:
                        cls = badge.get_attribute("class") or ""
                        if cls:
                            return cls
                except Exception:
                    pass
                return cell.get_attribute("class") or ""
        except Exception:
            return ""
        return ""

    # -------------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------------

    def search(self, text):
        try:
            box = self.h.wait_for_element_clickable(self.SEARCH_BOX, timeout=10000)
            box.fill("")
            box.fill(text)
            # fill() only dispatches an 'input' event. If this field's
            # Livewire binding only reacts to 'change'/blur (wire:model
            # .lazy/.blur) rather than 'input' (wire:model.live/.debounce),
            # fill() alone silently never triggers the search -- same bug
            # class already found and fixed for the SMS Campaigns search
            # box (TC005). Dispatching 'change' + blurring covers both
            # binding styles.
            box.dispatch_event("change")
            box.blur()
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
        self.page.wait_for_timeout(1000)
        return applied

    def set_date_filter(self, from_date, to_date):
        """
        Set the date range filter (Flatpickr, single combined text input,
        format dd-mm-yyyy).
        from_date / to_date: 'YYYY-MM-DD' strings.
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
                "  'sms_report_requests-filter-dateRange-created_at');"
                "if (el && el._flatpickr) {"
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
        """Locate action element (view/download/delete) in a specific table row."""
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            if row_idx >= rows.count():
                return None
            row = rows.nth(row_idx)
            attr_values = {
                "view":     ["View", "Summary"],
                "download": ["Download"],
                "delete":   ["Delete"],
            }
            for attr_val in attr_values.get(icon_type, []):
                for attr in ("title", "aria-label", "data-tooltip"):
                    try:
                        el = row.locator(f"xpath=.//*[contains(@{attr},'{attr_val}')]").first
                        if el.count() > 0 and el.is_visible():
                            return el
                    except Exception:
                        pass
            # Positional fallback — try last cell first (typical Actions column),
            # then first cell, to handle both table layouts.
            cells = row.locator("td")
            cell_count = cells.count()
            if cell_count == 0:
                return None
            pos_map = {"view": 0, "download": 1, "delete": 2}
            p = pos_map.get(icon_type, 0)
            for cell_idx in (cell_count - 1, 0):
                action_cell = cells.nth(cell_idx)
                btns = action_cell.locator("xpath=.//button | .//a")
                if p < btns.count():
                    candidate = btns.nth(p)
                    if candidate.is_visible():
                        return candidate
        except Exception:
            pass
        return None

    def diagnose_download_target(self, row_idx=0):
        """Best-effort read of the download control's own attributes for
        the given row, WITHOUT clicking it. Used to tell 'nothing was ever
        actually clicked / _action_btn_for_row's positional fallback
        clicked the wrong cell' apart from 'the right element was clicked
        but the download itself never fired' when a download test fails —
        the two look identical from the test's-eye view (wait_for_download
        just returns None either way), but need very different fixes."""
        info = {
            "matched_by": None, "tag": None, "href": None,
            "title": None, "aria_label": None, "class": None, "text": None,
        }
        btn = self._action_btn_for_row(row_idx, "download")
        info["matched_by"] = "attribute" if btn is not None else None
        if btn is None:
            try:
                candidate = self.page.locator(self.ROW_DOWNLOAD_ICON).first
                if candidate.count() > 0:
                    btn = candidate
                    info["matched_by"] = "global-fallback-locator"
            except Exception:
                pass
        if btn is None:
            try:
                rows = self.page.locator(self.TABLE_ROWS)
                if row_idx < rows.count():
                    cells = rows.nth(row_idx).locator("td")
                    if cells.count() > 0:
                        last_cell_btns = cells.nth(cells.count() - 1).locator("xpath=.//button | .//a")
                        if last_cell_btns.count() > 1:
                            btn = last_cell_btns.nth(1)  # pos_map["download"] = 1
                            info["matched_by"] = "positional-fallback (last cell, index 1)"
            except Exception:
                pass
        if btn is not None:
            try:
                info["tag"] = btn.evaluate("el => el.tagName")
                info["href"] = btn.get_attribute("href")
                info["title"] = btn.get_attribute("title")
                info["aria_label"] = btn.get_attribute("aria-label")
                info["class"] = btn.get_attribute("class")
                info["text"] = (btn.inner_text() or "").strip()[:40]
            except Exception:
                pass
        return info

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
        Tries multiple strategies in order of reliability:
          1. Attribute-based lookup inside the specific row (title/aria-label/data-tooltip)
          2. href-pattern anchor search inside the row
          3. Global ROW_DOWNLOAD_ICON locator
        Does NOT sleep long after clicking — callers that need a delay should use
        snapshot_downloads() + wait_for_download() which poll properly.
        """
        clicked = False

        # ── Strategy 1: attribute-based, scoped to the row ──────────────────
        btn = self._action_btn_for_row(row_idx, "download")
        if btn is not None:
            try:
                btn.scroll_into_view_if_needed()
                btn.evaluate("node => node.removeAttribute('target')")
                btn.click(force=True)
                clicked = True
            except Exception:
                pass

        # ── Strategy 2: look for any <a> with download-related href
        #    inside the row ──────────────────────────────────────────────────
        if not clicked:
            try:
                rows = self.page.locator(self.TABLE_ROWS)
                if row_idx < rows.count():
                    row = rows.nth(row_idx)
                    anchors = row.locator(
                        "xpath=.//a[contains(@href,'download') and not(contains(@href,'center'))"
                        "     and not(contains(@href,'create'))]"
                    )
                    if anchors.count() > 0:
                        el = anchors.first
                        el.scroll_into_view_if_needed()
                        el.evaluate("node => node.removeAttribute('target')")
                        el.click(force=True)
                        clicked = True
            except Exception:
                pass

        # ── Strategy 3: global locator ───────────────────────────────────────
        if not clicked:
            try:
                el = self.h.wait_for_element_clickable(self.ROW_DOWNLOAD_ICON, timeout=8000)
                el.scroll_into_view_if_needed()
                el.evaluate("node => node.removeAttribute('target')")
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

        A native confirm() dialog blocks page script execution until
        answered, so the handler must be registered with
        page.once("dialog", ...) BEFORE the click. This method registers a
        handler that records the dialog for confirm_delete()/cancel_delete()
        to act on afterward (native dialogs can't be "left open" across two
        separate Python calls the way Selenium's driver.switch_to.alert
        could).
        """
        btn = self._action_btn_for_row(row_idx, "delete")
        if btn is None:
            try:
                btn = self.h.wait_for_element_clickable(self.ROW_DELETE_ICON, timeout=8000)
            except Exception:
                btn = None

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
            except Exception:
                try:
                    self.page.once("dialog", _capture_dialog)
                    btn.click(force=True)
                    clicked = True
                except Exception:
                    pass

        if clicked:
            # Poll for the native dialog instead of a single fixed sleep --
            # this row's delete action is a Livewire wire:click.confirm,
            # and a real run showed the confirm() prompt can take longer
            # than a flat 600ms to appear (same class of timing issue
            # already fixed elsewhere in this project via poll/retry
            # rather than a single fixed wait). Exits early as soon as the
            # dialog is captured.
            end_time = time.time() + 3.0
            while not self._pending_native_dialog and time.time() < end_time:
                self.page.wait_for_timeout(150)
        self.page.wait_for_timeout(200)

    def confirm_delete(self):
        """
        Accept the delete confirmation.
        Tries the native dialog captured by click_delete_icon() first, then
        SweetAlert2 fallback.
        """
        debug = {"path": None, "error": None}
        if getattr(self, "_pending_native_dialog", False):
            try:
                self._native_dialog_obj.accept()
                self._pending_native_dialog = False
                debug["path"] = "native_alert"
                self.last_confirm_delete_debug = debug
                self.page.wait_for_timeout(2000)
                return
            except Exception as exc:
                debug["error"] = "native alert accept failed: " + str(exc)
        try:
            btn = self.page.locator(self.DELETE_CONFIRM_BTN).first
            btn.wait_for(state="visible", timeout=5000)
            btn.click(force=True)
            debug["path"] = "sweetalert2"
            self.page.wait_for_timeout(2000)
        except Exception as exc2:
            debug["path"] = "neither"
            debug["error"] = (debug["error"] or "") + " | sweetalert2 click also failed: " + str(exc2)
        self.last_confirm_delete_debug = debug

    def cancel_delete(self):
        """
        Dismiss the delete confirmation.
        Tries the native dialog captured by click_delete_icon() first, then
        SweetAlert2 fallback.
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
        first, then SweetAlert2.
        """
        if getattr(self, "_pending_native_dialog", False):
            return True
        try:
            el = self.page.locator(self.SWAL2_CONTAINER).first
            el.wait_for(state="visible", timeout=6000)
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

    def has_view_icon(self):
        """Returns True if any row has a View icon."""
        return self.is_element_present(self.ROW_VIEW_ICON, timeout=3000)

    # -------------------------------------------------------------------------
    # Summary / View popup
    # -------------------------------------------------------------------------

    def is_popup_open(self):
        """Return True if the summary/detail modal is currently visible."""
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

    def get_popup_generated_at(self):
        """Summary popup 'Generated at' date-time value ('' if not present)."""
        try:
            txt = self.page.locator(self.POPUP_GENERATED_AT_TEXT).first.inner_text()
            return txt.split("Generated at:", 1)[-1].strip()
        except Exception:
            return ""

    def get_popup_completed_at(self):
        """Summary popup 'Completed at' date-time value ('' if not present --
        e.g. a report that's still Processing has no Completed at yet)."""
        try:
            txt = self.page.locator(self.POPUP_COMPLETED_AT_TEXT).first.inner_text()
            return txt.split("Completed at:", 1)[-1].strip()
        except Exception:
            return ""

    def get_popup_period_dates(self):
        """Summary popup 'Period' date RANGE, split into (start, end) date-only
        values, e.g. ('08-09-2026', '27-09-2026'). Returns ('', '') if the
        Period text isn't present or doesn't parse as a "X - Y" range."""
        try:
            txt = self.page.locator(self.POPUP_PERIOD_TEXT).first.inner_text()
            txt = txt.split("Period:", 1)[-1].strip()
            parts = [p.strip() for p in txt.split(" - ") if p.strip()]
            if len(parts) == 2:
                return parts[0], parts[1]
            return "", ""
        except Exception:
            return "", ""

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
        self._js_click(self.NEXT_PAGE_BTN + " >> visible=true", timeout=10000)
        self.page.wait_for_timeout(1500)


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

    # In-progress suffixes Chrome uses while downloading
    _INCOMPLETE_SUFFIXES = (".crdownload", ".part", ".tmp")

    # Fallback download locations to check if DOWNLOAD_DIR has nothing
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
        """Return set of complete (non-temp) file paths currently in directory."""
        try:
            return {
                f for f in glob.glob(os.path.join(directory, "*"))
                if os.path.isfile(f)
                and not any(f.endswith(s) for s in self._INCOMPLETE_SUFFIXES)
            }
        except Exception:
            return set()

    def snapshot_downloads(self):
        """
        Capture a snapshot of all files currently present in watched download
        directories. Call this BEFORE clicking the download button, then pass
        the result to wait_for_download(before=...) so that even fast downloads
        are detected correctly.

        Returns a dict: { directory_path -> set_of_file_paths }
        """
        watch_dirs = [DOWNLOAD_DIR] + [
            d for d in self._FALLBACK_DIRS if os.path.isdir(d)
        ]
        return {d: self._list_complete_files(d) for d in watch_dirs}

    def wait_for_download(self, timeout=60, before=None):
        """
        Wait up to timeout seconds for a new complete file to appear —
        checks Playwright's captured download events first (fast path),
        then falls back to polling the watched directories for parity with
        the original Selenium approach.
        """
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
                current   = self._list_complete_files(d)
                new_files = current - before[d]
                finished  = [
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
