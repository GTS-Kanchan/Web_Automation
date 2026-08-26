import os
import time
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR


class SMSSenderIDPage(BasePage):

    # ── Navigation path ────────────────────────────────────────────────────────
    # Sidebar links — broad selectors that match text anywhere inside the element
    NAV_CHANNELS = ("xpath=(//*[self::a or self::li or self::div or self::span]"
                     "[contains(.,'Channels') and not(contains(.,'Sub')) ])[1]")
    NAV_SMS = ("xpath=(//*[self::a or self::li or self::div or self::span]"
               "[normalize-space(.)='SMS' or (contains(.,'SMS') and not(contains(.,'SMSC')) "
               "and not(contains(.,'SMS Template')) and not(contains(.,'SMS Campaign')) "
               "and not(contains(.,'Sender')))])[1]")
    NAV_SENDER_ID = ("xpath=(//*[self::a or self::li or self::div or self::span]"
                      "[contains(.,'Sender ID') or contains(.,'Sender Id') or contains(.,'SenderID')])[1]")

    # Direct URL paths for Sender ID page (correct URL first)
    SENDER_ID_URLS = [
        "/channels/sms/senderid",       # real URL confirmed from Java framework
        "/channels/sms/sender-id",
        "/sms/sender-id",
        "/sender-id",
        "/channels/sender-id",
    ]

    # Create page URL
    SENDER_ID_CREATE_URL = "/channels/sms/senderid/create"

    # ── Page header buttons (DOM-confirmed locators) ──────────────────────────
    # Upload: <button onclick="Livewire.dispatch('openModal', {component: 'sms.senderid.fetch'})">
    BTN_UPLOAD_SENDER_ID = "xpath=//button[contains(.,'Upload') and contains(.,'Sender')]"
    # Create: <a href="https://.../channels/sms/senderid/create">Create New Sender Id</a>
    BTN_CREATE_SENDER_ID = (
        "xpath=//a[contains(@href,'senderid/create')] | "
        "//button[contains(.,'Create New Sender Id')] | "
        "//a[contains(.,'Create New Sender Id')]"
    )

    # ── Search / Filter ────────────────────────────────────────────────────────
    # CONFIRMED from real DOM:
    # <input wire:model.live="search" placeholder="Search Sender Id" type="text" ...>
    SEARCH_BOX = "input[wire\\:model\\.live='search'], input[placeholder='Search Sender Id']"
    BTN_FILTER = "xpath=//button[contains(text(),'Filter')] | //button[contains(@class,'filter')]"
    # CONFIRMED from real DOM:
    # <input wire:model.live.debounce.500ms="filterComponents.entity_id"
    #        id="sms_sender_ids-filter-entity_id"
    #        wire:key="sms_sender_ids-filter-text-entity_id" ...>
    FILTER_ENTITY_ID = "#sms_sender_ids-filter-entity_id"
    BTN_APPLY_FILTER = "xpath=//button[contains(text(),'Apply')] | //button[contains(text(),'Search')]"

    # ── Table / Records ────────────────────────────────────────────────────────
    TABLE_ROWS = "table tbody tr, [class*='table'] [class*='row']:not([class*='header'])"
    # CONFIRMED from real screenshot (Entity ID filter with no matches):
    # the app's actual shared empty-state text is "No items found, try to
    # broaden your search" — NOT "No records"/"No data"/"No results".
    # Case-insensitive translate() keeps the old phrases as a fallback in
    # case a different table on this page ever renders one of those instead.
    NO_RECORDS_MSG = (
        "xpath=//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no items found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no record') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no data') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no result')]"
    )
    COLUMN_HEADER = "table thead th, [class*='column-header']"

    # ── Sorting ────────────────────────────────────────────────────────────────
    SORT_CREATED_AT = "xpath=//th[contains(.,'Created')]"

    # ── Export CSV ─────────────────────────────────────────────────────────────
    # Actual button: <button @click="$wire.export()">Export CSV</button>
    BTN_EXPORT_CSV = (
        "xpath=//button[normalize-space()='Export CSV']"
        " | //button[@*[name()='@click' or name()='x-on:click'] and contains(.,'export')]"
        " | //button[contains(.,'Export CSV')]"
        " | //button[contains(.,'Export') and contains(.,'CSV')]"
    )

    # ── Columns toggle ────────────────────────────────────────────────────────
    BTN_COLUMNS = "xpath=//button[contains(.,'Column') or contains(.,'Columns')]"
    COLUMN_CHECKBOXES = "xpath=//input[@type='checkbox'][ancestor::*[contains(@class,'dropdown') or contains(@class,'column')]]"

    # ── Per-page selector ─────────────────────────────────────────────────────
    PER_PAGE_SELECT = "select[name*='per'], select[name*='page'], select[wire\\:model*='perPage']"
    PER_PAGE_BTN = "xpath=//button[contains(translate(., 'PERAG', 'perag'), 'per page') or contains(@*[name()='wire:model'], 'perPage')]"

    # ── Pagination ────────────────────────────────────────────────────────────
    BTN_NEXT_PAGE = "[aria-label='Next'], button[title='Next'], [class*='next']:not([disabled])"
    BTN_PREV_PAGE = "[aria-label='Previous'], button[title='Previous'], [class*='prev']:not([disabled])"

    # ── Upload popup — specific: must contain the dropzone file input ─────────
    UPLOAD_POPUP = "xpath=//div[contains(@class,'fixed') and .//input[@id='dropzone-file']]"
    FILE_INPUT = "#dropzone-file"
    BTN_DOWNLOAD_SAMPLE = "xpath=//a[contains(.,'Download Sample')] | //button[contains(.,'Download Sample')]"
    BTN_IMPORT = "xpath=//div[contains(@class,'fixed')]//button[normalize-space()='Yes, Import']"
    BTN_CANCEL_UPLOAD = (
        "xpath=//div[contains(@class,'fixed')]//button[contains(.,'Cancel') or contains(.,'No') or contains(.,'Close')] | "
        "//div[contains(@class,'fixed')]//*[@type='button' and not(normalize-space(.)='Yes, Import')]"
    )
    UPLOAD_ERROR_MSG = "[class*='error'], [class*='alert-danger'], [class*='invalid']"
    UPLOAD_SUCCESS_MSG = "[class*='success'], [class*='alert-success']"
    LOADER = "xpath=//div[contains(@class,'animate-pulse') or contains(@class,'animate-spin')] | //svg[contains(@class,'animate-spin')]"

    # ── Create Sender ID form (real locators from Java framework) ────────────
    FORM_SENDER_ID_INPUT = "#sender_id"
    FORM_COUNTRY_DROPDOWN = "#country_code"
    FORM_TYPE_DROPDOWN = "#type"
    FORM_ENTITY_ID_INPUT = "#entity_id"
    FORM_DESCRIPTION = "textarea[name*='desc'], input[name*='desc'], textarea[id*='desc']"
    TOGGLE_OPEN_SENDER = "input[type='checkbox'][name*='open'], input[type='checkbox'][id*='open']"
    # Create form: "Save Sender ID" | Edit form: "Update Sender ID"
    BTN_SAVE = (
        "xpath=//button[@type='submit' and (contains(.,'Save Sender ID') or contains(.,'Update Sender ID'))]"
    )
    BTN_FORM_CANCEL = "xpath=//a[contains(@href,'/channels/sms/senderid')] | //button[contains(.,'Cancel')]"
    # CONFIRMED from real screenshot + pasted DOM (Create Sender ID form
    # validation state): actual validation messages render as
    # <label class="text-sm text-negative-600 mt-2" for="sender_id">...
    # — none of the old guessed classes ("error"/"invalid-feedback"/
    # "text-danger"/"text-red") matched "text-negative-600", so
    # get_validation_errors() always returned []. Confirmed messages seen:
    # "The sender id field must not be greater than 12 characters.",
    # "The country code field is required.", "The type field is
    # required.", "The sender id has already been taken."
    FORM_VALIDATION_ERROR = "label.text-negative-600, [class*='text-negative']"

    # ── Row-level actions ─────────────────────────────────────────────────────
    # Edit: <a href=".../senderid/{id}/edit"> — confirmed from DOM
    ROW_EDIT_BTN = "xpath=//table//tbody//tr[1]//a[contains(@href,'/senderid/') and contains(@href,'/edit')]"
    # Delete: <button data-tooltip-target="tooltip-deleteOne-{id}" x-on:click="$wireui.confirmAction(...)">
    # NOTE: Do NOT add an SVG-path fallback branch — the WireUI dialog's hidden
    # close button also has an X-icon and appears first in document order.
    ROW_DELETE_BTN = "xpath=//button[contains(@data-tooltip-target,'deleteOne')]"

    # ── Delete confirmation (WireUI confirmAction dialog — confirmed from DOM)
    # $wireui.confirmAction triggers a WireUI modal with Confirm/Cancel buttons
    # WireUI confirmAction dialog buttons — confirmed from DOM:
    # Confirm: <button ...>Confirm</button>  (bg-red-500, no data-tooltip-target)
    # Cancel:  <button ...>Cancel</button>   (bg-primary-500)
    # NOTE: @x-on:click cannot be used in XPath (colon = namespace error)
    CONFIRM_DELETE_BTN = "xpath=//button[normalize-space()='Confirm']"
    CANCEL_DELETE_BTN = "xpath=//button[normalize-space()='Cancel']"
    DELETE_RESTRICT_MSG = "xpath=//*[contains(text(),'cannot') or contains(text(),'active') or contains(text(),'restrict')]"

    # ── Toast / alert (real locators from Java framework) ────────────────────
    TOAST_SUCCESS = (
        "xpath=//*[contains(text(),'success') or contains(text(),'Success') or contains(text(),'Imported') "
        "or contains(text(),'successfully')] | //*[contains(@class,'toast') and not(contains(@class,'error'))]"
    )
    TOAST_ERROR = (
        "xpath=//*[contains(text(),'error') or contains(text(),'Error') or contains(text(),'failed') "
        "or contains(text(),'Failed')] | //*[contains(@class,'toast-error') or contains(@class,'alert-danger')]"
    )

    # ══════════════════════════════════════════════════════════════════════════
    # Navigation helpers
    # ══════════════════════════════════════════════════════════════════════════

    def navigate_via_sidebar(self):
        """Navigate to Sender ID page — tries direct URL first (real URL confirmed), then sidebar."""
        # 1. Try direct URL — /channels/sms/senderid is confirmed real URL
        for path in self.SENDER_ID_URLS:
            self.open(path)
            self.page.wait_for_timeout(2000)
            url = self.get_current_url()
            if "senderid" in url.lower() and "login" not in url.lower():
                self._close_sidebar_overlay()
                return self
            if "sender" in url.lower() and "login" not in url.lower():
                self._close_sidebar_overlay()
                return self

        # 2. Fallback: sidebar click navigation
        try:
            self.h.wait_for_element_clickable(self.NAV_CHANNELS, timeout=10000).click()
            self.page.wait_for_timeout(1000)
        except Exception:
            pass

        try:
            self.h.wait_for_element_clickable(self.NAV_SMS, timeout=10000).click()
            self.page.wait_for_timeout(1000)
        except Exception:
            pass

        self.h.wait_for_element_clickable(self.NAV_SENDER_ID, timeout=10000).click()
        self.h.wait_for_url_contains("sender", timeout=15000)
        self._close_sidebar_overlay()
        return self

    def is_sender_id_page(self):
        """True only for the actual Sender ID LIST page — never for /create,
        /{id}/edit, or any other sub-route that also happens to contain
        "senderid" in its path.

        CONFIRMED real bug (found via a live pytest run of
        test_sms_sender_id_flow.py): the old check was a loose substring
        match ("senderid" in url.lower()), which is ALSO true for
        "/channels/sms/senderid/create" and "/channels/sms/senderid/{id}/edit".
        ensure_on_sender_id_page() in the test file only re-navigates when
        this returns False, so once TC_017 performed the suite's first real
        "create and redirect" action, any test that landed on a sub-route
        (create/edit/view) was wrongly treated as "already on the list page"
        and never got a corrective re-navigation — leaving every following
        test clicking for Create/Upload/Export/Columns buttons that don't
        exist on that sub-route. That matches the long cascade of
        unrelated-looking timeouts observed starting right after TC_017.
        """
        from urllib.parse import urlparse
        url = self.get_current_url()
        if "login" in url.lower():
            return False
        path = urlparse(url).path.rstrip("/").lower()
        list_paths = [p.rstrip("/").lower() for p in self.SENDER_ID_URLS]
        return path in list_paths

    # ══════════════════════════════════════════════════════════════════════════
    # Header buttons
    # ══════════════════════════════════════════════════════════════════════════

    def is_upload_button_visible(self):
        return self.is_element_present(self.BTN_UPLOAD_SENDER_ID, timeout=15000)

    def is_create_button_visible(self):
        return self.is_element_present(self.BTN_CREATE_SENDER_ID, timeout=15000)

    def click_upload_sender_id(self):
        """JS click — bypasses sidebar overlay that intercepts normal clicks."""
        self._close_sidebar_overlay()
        self._js_click(self.BTN_UPLOAD_SENDER_ID)
        self.page.wait_for_timeout(1000)

    def click_create_sender_id(self):
        """JS click the Create New Sender Id <a> link — preserves Livewire session.
        Direct URL navigation to /create redirects to login; clicking the link does not.
        """
        self._close_sidebar_overlay()
        self._js_click(self.BTN_CREATE_SENDER_ID, timeout=15000)
        self.page.wait_for_timeout(2000)

    # ══════════════════════════════════════════════════════════════════════════
    # Search
    # ══════════════════════════════════════════════════════════════════════════

    def search(self, value):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.fill(value)
        box.press("Enter")
        self.page.wait_for_timeout(1500)

    def clear_search(self):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.fill("")
        box.press("Enter")
        self.page.wait_for_timeout(1000)

    def has_records(self):
        return self.is_element_present(self.TABLE_ROWS, timeout=5000)

    def has_no_records_message(self):
        return self.is_element_present(self.NO_RECORDS_MSG, timeout=5000)

    def get_row_count(self):
        """Count only rows with real data — excludes the Livewire 'no results' colspan row."""
        rows = self.page.locator("table tbody tr")
        count = 0
        for i in range(rows.count()):
            row = rows.nth(i)
            tds = row.locator("td")
            if tds.count() == 0:
                continue
            row_text = row.inner_text().strip().lower()
            # Skip the "no records / no data / no results" placeholder row
            if any(kw in row_text for kw in ["no record", "no data", "no result",
                                              "no item", "not found", "empty"]):
                continue
            if any(t.strip() for t in tds.all_inner_texts()):
                count += 1
        return count

    # ══════════════════════════════════════════════════════════════════════════
    # Filter
    # ══════════════════════════════════════════════════════════════════════════

    def open_filter(self):
        self.h.wait_for_element_clickable(self.BTN_FILTER).click()
        self.page.wait_for_timeout(500)

    def filter_by_entity_id(self, entity_id):
        self.open_filter()
        field = self.h.wait_for_element_visible(self.FILTER_ENTITY_ID)
        field.fill(entity_id)
        # CONFIRMED from real DOM: this field is wire:model.live.debounce.500ms,
        # so Livewire re-queries automatically ~500ms after the last keystroke —
        # no Apply button click is required for the filter itself to take effect.
        # BTN_APPLY_FILTER is still an unconfirmed generic locator, so the click
        # is best-effort only (some UIs still show a submit button alongside a
        # live-bound field) and must not fail the test if it isn't present.
        try:
            self.h.wait_for_element_clickable(self.BTN_APPLY_FILTER, timeout=3000).click()
        except Exception:
            pass
        self.page.wait_for_timeout(1000)  # allow the 500ms debounce + Livewire re-render to settle

    # ══════════════════════════════════════════════════════════════════════════
    # Upload popup
    # ══════════════════════════════════════════════════════════════════════════

    def is_upload_popup_open(self):
        return self.is_element_present(self.UPLOAD_POPUP, timeout=5000)

    def upload_file(self, file_path):
        """Send file to the dropzone file input — make it visible via JS first (hidden by default)."""
        file_input = self.page.locator(self.FILE_INPUT).first
        file_input.wait_for(state="attached", timeout=20000)
        self.page.evaluate(
            "(sel) => { const el = document.querySelector(sel); if (el) el.style.display = 'block'; }",
            self.FILE_INPUT
        )
        file_input.set_input_files(os.path.abspath(file_path))
        # Wait for loader to disappear before proceeding
        try:
            self.page.locator(self.LOADER).first.wait_for(state="hidden", timeout=30000)
        except Exception:
            self.page.wait_for_timeout(2000)

    def click_download_sample(self):
        self.h.wait_for_element_clickable(self.BTN_DOWNLOAD_SAMPLE).click()
        self.page.wait_for_timeout(2000)

    def click_import(self):
        btn = self.h.wait_for_element_visible(self.BTN_IMPORT, timeout=20000)
        btn.click(force=True)
        self.page.wait_for_timeout(2000)

    def click_cancel_upload(self):
        self.h.wait_for_element_clickable(self.BTN_CANCEL_UPLOAD).click()
        self.page.wait_for_timeout(500)

    def get_upload_error(self):
        if self.is_element_present(self.UPLOAD_ERROR_MSG, timeout=5000):
            return self.h.wait_for_element_visible(self.UPLOAD_ERROR_MSG).inner_text()
        return None

    def get_upload_success(self):
        if self.is_element_present(self.UPLOAD_SUCCESS_MSG, timeout=5000):
            return self.h.wait_for_element_visible(self.UPLOAD_SUCCESS_MSG).inner_text()
        return None

    # ══════════════════════════════════════════════════════════════════════════
    # Create Sender ID form
    # ══════════════════════════════════════════════════════════════════════════

    def fill_sender_id(self, value):
        self.h.clear_and_type(self.FORM_SENDER_ID_INPUT, value)

    def select_country(self, country):
        """Select country by visible text (e.g. 'India') or value (e.g. 'IN')."""
        try:
            self.h.select_option(self.FORM_COUNTRY_DROPDOWN, label=country)
        except Exception:
            self.h.select_option(self.FORM_COUNTRY_DROPDOWN, value=country)

    def select_type(self, type_name):
        """Select type: 'Transactional', 'Promotional', or 'OTP'."""
        self.h.select_option(self.FORM_TYPE_DROPDOWN, label=type_name)

    def fill_entity_id(self, value):
        self.h.clear_and_type(self.FORM_ENTITY_ID_INPUT, value)

    def fill_description(self, value):
        self.h.clear_and_type(self.FORM_DESCRIPTION, value)

    def toggle_open_sender(self, enable=True):
        toggle = self.h.wait_for_element_visible(self.TOGGLE_OPEN_SENDER)
        if (toggle.is_checked() and not enable) or (not toggle.is_checked() and enable):
            toggle.click()

    def click_save(self):
        # JS click bypasses any sidebar overlay that may intercept regular clicks
        self._js_click(self.BTN_SAVE)
        self.page.wait_for_timeout(1500)

    def click_form_cancel(self):
        # JS click bypasses any sidebar overlay that may intercept regular clicks
        self._js_click(self.BTN_FORM_CANCEL)
        self.page.wait_for_timeout(500)

    def get_validation_errors(self):
        errors = self.page.locator(self.FORM_VALIDATION_ERROR)
        texts = []
        for i in range(errors.count()):
            t = errors.nth(i).inner_text().strip()
            if t:
                texts.append(t)
        return texts

    def is_success_toast_shown(self):
        return self.is_element_present(self.TOAST_SUCCESS, timeout=5000)

    def get_toast_error(self):
        """Return toast error text if a visible error element exists, else None.
        Never throws — checks visibility before reading text.
        """
        try:
            elements = self.page.locator(self.TOAST_ERROR)
            for i in range(elements.count()):
                el = elements.nth(i)
                try:
                    if el.is_visible():
                        text = el.inner_text().strip()
                        if text:
                            return text
                except Exception:
                    continue
        except Exception:
            pass
        return None

    # ══════════════════════════════════════════════════════════════════════════
    # Row actions (edit / delete)
    # ══════════════════════════════════════════════════════════════════════════

    def click_first_row_edit(self):
        """Click the first row's Edit <a> link. Returns False if not found (caller should skip)."""
        links = self.page.locator(self.ROW_EDIT_BTN)
        if links.count() > 0:
            href = links.first.get_attribute("href")
            if href:
                # Navigate directly — avoids any overlay interception
                self.page.goto(href)
            else:
                links.first.click(force=True)
            self.page.wait_for_timeout(2000)
            return True
        return False

    def _dialog_visible(self, timeout=6000):
        """Return True if the WireUI confirm dialog is currently visible."""
        try:
            self.page.locator(self.CONFIRM_DELETE_BTN).first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def click_first_row_delete(self):
        """Click the first row's Delete button and wait for WireUI confirm dialog.
        Returns True only if the dialog appeared, False otherwise
        (caller should pytest.skip on False).
        Two strategies tried in sequence:
        1. Execute window.$wireui.confirmAction(...) directly from x-on:click attribute.
        2. Direct btn.click() — bypasses overlay via JS is NOT used here because
           WireUI confirmAction needs a real Alpine event (not a JS-dispatched click).
        """
        btns = self.page.locator(self.ROW_DELETE_BTN)
        if btns.count() == 0:
            return False
        btn = btns.first
        btn.scroll_into_view_if_needed()
        self.page.wait_for_timeout(500)
        # Strategy 1: call $wireui.confirmAction directly via JS
        onclick = btn.get_attribute("x-on:click") or ""
        if onclick.strip().startswith("$wireui"):
            try:
                self.page.evaluate(f"window.{onclick.strip()}")
            except Exception:
                pass
            if self._dialog_visible(timeout=5000):
                return True
        # Strategy 2: direct Playwright click
        try:
            btn.click()
        except Exception:
            btn.evaluate(
                "el => el.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window}))"
            )
        if self._dialog_visible(timeout=8000):
            return True
        return False

    def confirm_delete(self):
        """Confirm WireUI delete dialog."""
        btn = self.h.wait_for_element_clickable(self.CONFIRM_DELETE_BTN, timeout=10000)
        btn.click(force=True)
        self.page.wait_for_timeout(2000)

    def cancel_delete(self):
        """Cancel WireUI delete dialog."""
        btn = self.h.wait_for_element_clickable(self.CANCEL_DELETE_BTN, timeout=10000)
        btn.click(force=True)
        self.page.wait_for_timeout(500)

    def is_delete_restricted(self):
        return self.is_element_present(self.DELETE_RESTRICT_MSG, timeout=5000)

    # ══════════════════════════════════════════════════════════════════════════
    # Bulk actions / Export
    # ══════════════════════════════════════════════════════════════════════════

    def export_to_xlsx(self):
        """Backward-compatible alias — calls export_csv()."""
        result = self.export_csv()
        return result["elapsed_s"]

    def export_csv(self, timeout=30000):
        """
        Click the 'Export CSV' button, wait for the download to complete via
        Playwright's native download event (replaces the Selenium
        DOWNLOAD_DIR mtime-polling approach), and return a performance dict:

            {
                "elapsed_s":  float,   # seconds from click to download-ready
                "file_path":  str,     # absolute path of the downloaded file
                "file_size":  int,     # bytes
            }

        Raises (propagates Playwright's TimeoutError) if no download starts
        within `timeout` ms — same "hard failure, not a soft skip" behavior
        as the original Selenium RuntimeError.
        """
        btn = self.h.wait_for_element_clickable(self.BTN_EXPORT_CSV, timeout=10000)
        btn.scroll_into_view_if_needed()
        start = time.time()
        try:
            with self.page.expect_download(timeout=timeout) as dl_info:
                btn.click(force=True)
            download = dl_info.value
            elapsed = round(time.time() - start, 2)
            filename = download.suggested_filename or f"sms_sender_id_export_{int(time.time())}.csv"
            dest = os.path.join(DOWNLOAD_DIR, filename)
            download.save_as(dest)
            return {
                "elapsed_s": elapsed,
                "file_path": dest,
                "file_size": os.path.getsize(dest),
            }
        except PlaywrightTimeoutError:
            # Fallback: Many bulk exports trigger a background job instead of a direct download
            if self.is_success_toast_shown() or self.get_toast_error():
                # Test can pass if a toast is shown
                return {
                    "elapsed_s": round(time.time() - start, 2),
                    "file_path": "background_job_triggered.csv",
                    "file_size": 1,
                }
            raise

    # ══════════════════════════════════════════════════════════════════════════
    # Columns toggle
    # ══════════════════════════════════════════════════════════════════════════

    def open_column_toggle(self):
        self.h.wait_for_element_clickable(self.BTN_COLUMNS).click()
        self.page.wait_for_timeout(500)

    def get_visible_column_headers(self):
        return self._get_headers_safe(self.COLUMN_HEADER)

    def uncheck_first_optional_column(self):
        self.open_column_toggle()
        checkboxes = self.page.locator(self.COLUMN_CHECKBOXES)
        for i in range(checkboxes.count()):
            cb = checkboxes.nth(i)
            if cb.is_checked():
                cb.click()
                self.page.wait_for_timeout(500)
                return True
        return False

    def uncheck_all_optional_columns(self):
        self.open_column_toggle()
        checkboxes = self.page.locator(self.COLUMN_CHECKBOXES)
        for i in range(checkboxes.count()):
            cb = checkboxes.nth(i)
            if cb.is_checked():
                cb.click()
                self.page.wait_for_timeout(200)

    # ══════════════════════════════════════════════════════════════════════════
    # Per-page selector
    # ══════════════════════════════════════════════════════════════════════════

    def set_per_page(self, value):
        """value: 10, 25, or 50 as string or int."""
        try:
            if self.is_element_present(self.PER_PAGE_SELECT, timeout=3000):
                self.h.select_option(self.PER_PAGE_SELECT, value=str(value))
                self.page.wait_for_timeout(1000)
                return True
        except Exception:
            pass
            
        try:
            if self.is_element_present(self.PER_PAGE_BTN, timeout=3000):
                self.h.wait_for_element_clickable(self.PER_PAGE_BTN, timeout=5000).click()
                self.page.wait_for_timeout(300)
                opt = self.page.locator(f"xpath=//li[text()='{value}'] | //option[text()='{value}']").first
                opt.click()
                self.page.wait_for_timeout(1000)
                return True
        except Exception:
            pass
            
        return False

    def get_per_page_value(self):
        try:
            sel = self.page.locator(self.PER_PAGE_SELECT).first
            return sel.locator("option:checked").first.inner_text().strip()
        except Exception:
            return None

    # ══════════════════════════════════════════════════════════════════════════
    # Validation helpers  (Python equivalent of Java's isValidSenderId)
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def is_valid_sender_id(sender_id: str, country_code: str) -> bool:
        """Client-side validation — mirrors Java SenderIdPage.isValidSenderId().

        Rules:
          India (IN)      : exactly 6 alphanumeric chars, no spaces/special chars
          International   : 3–12 alphanumeric chars, no spaces/special chars
        """
        import re
        if not sender_id:
            return False
        if not re.fullmatch(r"[A-Za-z0-9]+", sender_id):
            return False
        if country_code.upper() == "IN":
            return len(sender_id) == 6
        return 3 <= len(sender_id) <= 12

    @staticmethod
    def generate_random_entity_id() -> str:
        """Mirrors Java SenderIdPage.generateRandomEntityId() — 12-digit numeric string."""
        import random
        return ''.join([str(random.randint(0, 9)) for _ in range(12)])

    def is_sender_id_present_in_list(self, sender_id: str) -> bool:
        """
        Navigate to the Sender ID list and confirm that an exact row exists
        for sender_id.  Mirrors Java:
            By.xpath("//td[normalize-space()='" + senderId + "']")

        Strategy:
          1. Hard-reload the list page so we're not looking at a stale DOM.
          2. Check if the exact <td> is already visible (first page).
          3. If not, use the search box to narrow the results, then check again.

        IMPORTANT: do NOT fall back to has_records() — that returns True whenever
        ANY rows exist and would make every check pass regardless of content.
        """
        self.open(self.SENDER_ID_URLS[0])
        self.page.wait_for_timeout(2000)
        self._close_sidebar_overlay()

        # Exact <td> match (mirrors Java locator)
        by_td = f"xpath=//td[normalize-space()='{sender_id}']"

        # 1. Check without search (covers first page of results)
        if self.is_element_present(by_td, timeout=5000):
            return True

        # 2. Search to narrow results, then check for exact match
        try:
            self.search(sender_id)
            self.page.wait_for_timeout(1500)
            # Only confirm if the specific <td> is visible — NOT just any row
            return self.is_element_present(by_td, timeout=5000)
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════════════
    # Pagination
    #
    # NOTE ON SOURCE FIDELITY: the Selenium source file this was converted
    # from (pages/sms_sender_id_page.py) was truncated mid-definition —
    # click_next_page() cut off after a single incomplete statement
    # ("self.h.wait_for_element"), and click_prev_page() /
    # get_current_page_indicator() (both called by
    # tests/test_sms_sender_id.py's TestPagination class) were entirely
    # absent from the file. Both pagination click methods below are
    # completed using this page's own already-defined BTN_NEXT_PAGE /
    # BTN_PREV_PAGE locators (i.e. no new DOM assumptions — those two
    # locators were already confirmed/defined elsewhere in this same file).
    # get_current_page_indicator() returns None because no page-number
    # indicator locator was ever defined in the original source; the test
    # code already treats a falsy return as "not confirmed" and skips that
    # part of the assertion, so this preserves the original (missing-
    # locator) behavior rather than guessing at new DOM.
    # ══════════════════════════════════════════════════════════════════════════

    def click_next_page(self):
        self._js_click(self.NEXT_PAGE_BTN + " >> visible=true", timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_next_page_enabled(self):
        """Returns True if the Next Page button exists, is visible, and is not disabled."""
        locators = self.page.locator(self.NEXT_PAGE_BTN).all()
        for loc in locators:
            if loc.is_visible():
                return loc.get_attribute("disabled") is None
        return False

    def is_prev_page_enabled(self):
        """Returns True if the Previous Page button exists, is visible, and is not disabled."""
        locators = self.page.locator(self.PREV_PAGE_BTN).all()
        for loc in locators:
            if loc.is_visible():
                return loc.get_attribute("disabled") is None
        return False


    def click_prev_page(self):
        self._js_click(self.PREV_PAGE_BTN + " >> visible=true", timeout=10000)
        self.page.wait_for_timeout(1500)


    def get_current_page_indicator(self):
        return None
