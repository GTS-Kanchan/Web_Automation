import os
import re
import time

from pages.common.base_page import BasePage
from utils.config import Config, DOWNLOAD_DIR


class ContactsPage(BasePage):

    # ── URLs ───────────────────────────────────────────────────────────────────
    CONTACTS_URL = "/contacts"
    CREATE_CONTACT_URL = "/contacts/create"

    # ── Navigation (sidebar fallback) ─────────────────────────────────────────
    NAV_CONTACTS = (
        "xpath=(//*[self::a or self::li or self::div or self::span]"
        "[contains(.,'Contacts') and not(contains(.,'Segmentation'))])[1]"
    )

    # ── Page header ────────────────────────────────────────────────────────────
    BTN_CREATE_CONTACT = (
        "xpath=//a[contains(@href,'/contacts/create')] | //button[contains(.,'Create New Contact')] "
        "| //a[contains(.,'Create New Contact')] | //a[contains(.,'Add Contact')]"
    )
    BTN_IMPORT_CONTACTS = "xpath=//button[contains(.,'Import')] | //a[contains(.,'Import')]"

    # ── Search / Filters ──────────────────────────────────────────────────────
    SEARCH_BOX = "input[wire\\:model\\.live='search'], input[placeholder*='Search' i]"
    BTN_FILTERS = "xpath=//button[contains(.,'Filter')]"
    FILTER_DEPARTMENT = "select[wire\\:model*='department'], [name*='department']"
    FILTER_USER = "select[wire\\:model*='user'], [name*='user']"
    # CONFIRMED from live DOM: <select wire:model.live="filterComponents.blacklist_contact"
    # id="contacts-filter-blacklist_contact"> with options value="" (All),
    # value="1" (Yes), value="0" (No).
    FILTER_BLACKLIST = "#contacts-filter-blacklist_contact"
    FILTER_TAGS = "select[wire\\:model*='tags'], [name*='tags']"
    FILTER_SEGMENT = "select[wire\\:model*='segment'], [name*='segment']"
    FILTER_CREATED_FROM = "input[wire\\:model*='created_from'], [name*='created_from']"
    FILTER_CREATED_TO = "input[wire\\:model*='created_to'], [name*='created_to']"
    BTN_APPLY_FILTER = "xpath=//button[contains(.,'Apply')] | //button[contains(.,'Search')]"
    BTN_RESET_FILTER = "xpath=//button[contains(.,'Reset')] | //button[contains(.,'Clear')]"

    # ── Columns dropdown ──────────────────────────────────────────────────────
    BTN_COLUMNS = "xpath=//button[contains(.,'Column') or contains(.,'Columns')]"
    COLUMN_CHECKBOXES = "xpath=//input[@type='checkbox'][ancestor::*[contains(@class,'dropdown') or contains(@class,'column')]]"
    COLUMN_HEADER = "table thead th"

    # ── Bulk actions / Export ─────────────────────────────────────────────────
    # CONFIRMED from live DOM:
    #   <button id="contacts-bulkActionsDropdown" x-on:click="open = !open">Bulk Actions</button>
    #   <button wire:click="export" wire:key="contacts-bulk-action-export"><span>Export to XLSX</span></button>
    BTN_BULK_ACTIONS = (
        "xpath=//button[@id='contacts-bulkActionsDropdown'] "
        "| //button[contains(.,'Bulk Action') or contains(.,'Bulk Actions') or contains(.,'Bulk')]"
    )
    BTN_EXPORT_XLSX = (
        "xpath=//button[@*[name()='wire:click' and .='export']] "
        "| //button[contains(.,'Export to XLSX')] | //a[contains(.,'Export to XLSX')] "
        "| //*[contains(.,'Export') and contains(.,'XLSX')]"
    )

    # Priority-ordered locator lists for _first_visible_of(). A single OR'd
    # XPath is unsafe here: '|' returns matches in DOCUMENT order, not
    # specificity, so the generic "//*[contains(.,'Export') and
    # contains(.,'XLSX')]" clause can match a wrapping <div>/<li> container
    # that sits BEFORE the actual <button> in the DOM. _first_visible() would
    # then return and click that container — the click "succeeds" (no
    # exception) but never fires wire:click="export" since the listener is
    # bound to the button, not its ancestor. Trying the most specific locator
    # first avoids ever falling back to the container match when the real
    # button is present.
    BTN_BULK_ACTIONS_LOCATORS = [
        "#contacts-bulkActionsDropdown",
        "xpath=//button[contains(.,'Bulk Action') or contains(.,'Bulk Actions') or contains(.,'Bulk')]",
    ]
    BTN_EXPORT_XLSX_LOCATORS = [
        "xpath=//button[@*[name()='wire:click' and .='export']]",
        "xpath=//button[contains(normalize-space(.),'Export to XLSX')]",
        "xpath=//a[contains(normalize-space(.),'Export to XLSX')]",
        # Last resort — restricted to self::button/self::a so it can never
        # match a wrapping container even though the text-contains() check
        # is broad.
        "xpath=//*[(self::button or self::a) and contains(.,'Export') and contains(.,'XLSX')]",
    ]

    # ── Table / Records ───────────────────────────────────────────────────────
    TABLE_ROWS = "table tbody tr"
    # CONFIRMED elsewhere via real screenshots (SMS Error Codes / Sender ID
    # pages) that this app's shared empty-state text is "No items found,
    # try to broaden your search" — added case-insensitively alongside the
    # original phrases, which are kept as a fallback.
    NO_RECORDS_MSG = (
        "xpath=//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no items found') "
        "or contains(text(),'No records') or contains(text(),'No data') or contains(text(),'No results') "
        "or contains(text(),'No contacts')]"
    )

    # ── Sorting ────────────────────────────────────────────────────────────────
    SORT_FULL_NAME = (
        "xpath=//th[.//*[@*[name()='wire:click' and .=\"sortBy('full_name')\"]] or contains(.,'Full Name')]"
    )
    SORT_CREATED_AT = (
        "xpath=//th[.//*[@*[name()='wire:click' and .=\"sortBy('created_at')\"]] or contains(.,'Created At')]"
    )

    def sort_by_header(self, field_name):
        # NOTE: @wire:click cannot be used directly in XPath (colon = namespace error) —
        # use @*[name()='wire:click' ...] instead. Prefer click_sort(header_text) below,
        # which clicks by visible header text and doesn't depend on knowing the exact
        # internal field key.
        return f"xpath=//*[@*[name()='wire:click' and .=\"sortBy('{field_name}')\"]]"

    # ── Row-level actions ──────────────────────────────────────────────────────
    ROW_VIEW_BTN = (
        "xpath=(//table//tbody//tr)[1]//a[contains(@data-tooltip-target,'tooltip-view') "
        "or (contains(@href,'/contacts/') and not(contains(@href,'edit')) and not(contains(@href,'create')))]"
    )
    ROW_EDIT_BTN = "xpath=(//table//tbody//tr)[1]//*[contains(@data-tooltip-target,'tooltip-edit')]"
    ROW_BLACKLIST_BTN = "xpath=(//table//tbody//tr)[1]//*[contains(@data-tooltip-target,'tooltip-block')]"
    ROW_DELETE_BTN = (
        "xpath=(//table//tbody//tr)[1]//*[contains(@data-tooltip-target,'tooltip-deleteOne') "
        "or contains(@data-tooltip-target,'deleteOne')]"
    )

    # ── Delete confirmation ────────────────────────────────────────────────
    # CONFIRMED from live DOM: the delete button invokes $wireui.confirmAction(...),
    # WireUI's helper which renders a SweetAlert2 dialog (not a plain WireUI modal).
    CONFIRM_DELETE_BTN = (
        "xpath=//button[contains(@class,'swal2-confirm')] "
        "| //div[contains(@class,'swal2-actions')]//button[not(contains(@class,'swal2-cancel')) "
        "and not(contains(@class,'swal2-deny'))] "
        "| //button[normalize-space()='Confirm' or normalize-space()='Yes' "
        "or normalize-space()='Yes, delete it!' or normalize-space()='OK' "
        "or normalize-space()='Delete' or normalize-space()='Accept']"
    )
    CANCEL_DELETE_BTN = (
        "xpath=//button[contains(@class,'swal2-cancel')] "
        "| //button[normalize-space()='Cancel' or normalize-space()='No']"
    )

    # ── Blacklist native confirm() dialog is handled via page.expect_event("dialog") ──

    # ── Edit Contact modal (opened via $dispatch openModal contact.edit) ─────
    MODAL_ROOT = "xpath=//div[contains(@class,'fixed') and (.//h1 or .//h2 or .//h3)]"
    MODAL_CANCEL_BTN = (
        "xpath=//div[contains(@class,'fixed')]//button[contains(.,'Cancel')] "
        "| //div[contains(@class,'fixed')]//button[@type='button' and contains(.,'Close')]"
    )
    MODAL_SAVE_BTN = "xpath=//div[contains(@class,'fixed')]//button[@type='submit']"

    # ── Toasts ─────────────────────────────────────────────────────────────────
    TOAST_SUCCESS = (
        "xpath=//*[contains(text(),'success') or contains(text(),'Success') or contains(text(),'successfully')] "
        "| //*[contains(@class,'toast') and not(contains(@class,'error'))]"
    )
    TOAST_ERROR = (
        "xpath=//*[contains(text(),'error') or contains(text(),'Error') or contains(text(),'failed') or contains(text(),'Failed')] "
        "| //*[contains(@class,'toast-error') or contains(@class,'alert-danger')]"
    )

    # ══════════════════════════════════════════════════════════════════════════
    # Create New Contact form (/contacts/create)
    # ══════════════════════════════════════════════════════════════════════════
    FORM_FIRST_NAME = "input[wire\\:model='first_name'], #first_name"
    FORM_LAST_NAME = "input[wire\\:model='last_name'], #last_name"
    FORM_COUNTRY = "select[wire\\:model='country'], #country"
    FORM_PHONE = "input[wire\\:model\\.defer='phone'], #phone"
    FORM_EMAIL = "input[wire\\:model\\.defer='email'], #email"
    FORM_COMPANY = "input[wire\\:model\\.defer='company'], #company"
    FORM_TAGS_INPUT = "#tags"
    FORM_TAGS_DROPDOWN_OPTIONS = "xpath=//ul[contains(@class,'dropdown') or @role='listbox']//li"
    BTN_ADD_CUSTOM_FIELD = "xpath=//button[contains(.,'Add Custom Field')]"
    CUSTOM_FIELD_EMPTY_MSG = "xpath=//*[contains(text(),'No custom fields added yet')]"
    CUSTOM_FIELD_ROWS = "[class*='custom-field-row'], [wire\\:key*='custom-field']"
    BTN_FORM_CANCEL = "xpath=//a[contains(@href,'/contacts') and contains(.,'Cancel')] | //a[normalize-space()='Cancel']"
    BTN_FORM_SAVE = "xpath=//button[@type='submit' and (contains(.,'Save') or contains(.,'Update'))]"
    # CONFIRMED from live DOM: per-field validation errors render as
    # <label class="text-sm text-negative-600 mt-2" for="first_name">The First
    # Name field is required.</label> — a WireUI/Tailwind "negative" (red)
    # variant.
    FORM_VALIDATION_ERROR = "label.text-negative-600, .text-negative-600"

    # ══════════════════════════════════════════════════════════════════════════
    # View Contact page (/contacts/{id})
    # ══════════════════════════════════════════════════════════════════════════
    VIEW_FULL_NAME = "xpath=//*[self::h1 or self::h2 or self::h3][contains(@class,'name') or 1]"
    VIEW_INFO_PANEL = "[class*='contact-info'], [class*='profile']"
    VIEW_BLACKLIST_BTN = (
        "xpath=//button[contains(.,'Blacklist')] | //*[@*[name()='x-on:click' and contains(.,'block')]] "
        "| //*[contains(@data-tooltip-target,'block')]"
    )
    VIEW_CUSTOM_FIELDS_SECTION = "xpath=//*[contains(text(),'Custom Field')]"

    # ══════════════════════════════════════════════════════════════════════════
    # Import Contacts modal
    # ══════════════════════════════════════════════════════════════════════════
    IMPORT_MODAL = "xpath=//div[contains(@class,'fixed') and (.//input[@id='dropzone-file'] or contains(.,'Import'))]"
    IMPORT_TAB_COPY_PASTE = "xpath=//button[contains(.,'Copy') and contains(.,'Paste')] | //a[contains(.,'Copy') and contains(.,'Paste')]"
    IMPORT_TAB_UPLOAD = "xpath=//button[contains(.,'Upload')] | //a[contains(.,'Upload')]"
    IMPORT_PASTE_TEXTAREA = "textarea[wire\\:model*='paste'], textarea[wire\\:model*='contacts']"
    IMPORT_TAG_DROPDOWN = "#import_tags"
    IMPORT_FILE_INPUT = "#dropzone-file"
    BTN_DOWNLOAD_SAMPLE = "xpath=//a[contains(.,'Download Sample')] | //button[contains(.,'Download Sample')]"
    # CONFIRMED from live DOM: when duplicate contacts are detected after
    # upload, the app shows "(N) Duplicate Contacts Detected" and the actual
    # submit button reads "Continue" (wire:click="submit") — NOT "Import" or
    # "Yes, Import" as originally guessed. Matching the wire:click="submit"
    # attribute directly is more robust than the button's label, which can
    # vary by import state (first-time import vs. duplicate-detected
    # confirmation).
    BTN_IMPORT_SUBMIT = (
        "xpath=//div[contains(@class,'fixed')]//button[@*[name()='wire:click' and .='submit']] "
        "| //div[contains(@class,'fixed')]//button[contains(.,'Continue') or contains(.,'Import') "
        "or contains(.,'Yes, Import')]"
    )
    BTN_CANCEL_IMPORT = "xpath=//div[contains(@class,'fixed')]//button[contains(.,'Cancel') or contains(.,'Close')]"
    IMPORT_ERROR_MSG = "[class*='error'], [class*='alert-danger'], [class*='invalid']"
    IMPORT_SUCCESS_MSG = "[class*='success'], [class*='alert-success']"
    LOADER = "xpath=//div[contains(@class,'animate-pulse') or contains(@class,'animate-spin')] | //svg[contains(@class,'animate-spin')]"

    # ══════════════════════════════════════════════════════════════════════════
    # Navigation helpers
    # ══════════════════════════════════════════════════════════════════════════

    def navigate_to_contacts(self):
        self.open(self.CONTACTS_URL)
        self.page.wait_for_timeout(2000)
        self._close_sidebar_overlay()
        return self

    def navigate_to_create_contact(self):
        self.open(self.CREATE_CONTACT_URL)
        self.page.wait_for_timeout(2000)
        self._close_sidebar_overlay()
        return self

    def is_contacts_page(self):
        """True only for the Contacts LIST page — excludes /contacts/create,
        /contacts/{id} (view), and /contacts/segmentation (substring collisions
        that previously caused ensure_on_contacts_page() to silently no-op)."""
        url = self.get_current_url()
        if "login" in url.lower():
            return False
        return bool(re.search(r"/contacts/?(\?.*)?$", url))

    def is_create_contact_page(self):
        return "/contacts/create" in self.get_current_url()

    def click_create_contact(self):
        self._close_sidebar_overlay()
        self._js_click(self.BTN_CREATE_CONTACT, timeout=15000)
        self.page.wait_for_timeout(2000)

    def click_import_contacts(self):
        self._close_sidebar_overlay()
        self._js_click(self.BTN_IMPORT_CONTACTS, timeout=15000)
        self.page.wait_for_timeout(1000)

    # ══════════════════════════════════════════════════════════════════════════
    # Search / records
    # ══════════════════════════════════════════════════════════════════════════

    def search(self, value):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.fill(value)
        self.page.wait_for_timeout(1500)

    def clear_search(self):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.fill("")
        box.press("Enter")
        self.page.wait_for_timeout(1000)

    def _ensure_filters_panel_open(self):
        """The Filters section (Department/User/Blacklist Contact/Tags/Segment/
        Created From/To) is a Livewire "slide-down" panel that is COLLAPSED
        by default. The filter <select> elements exist in the DOM (so
        is_element_present() reports True) but are not visible until the
        "Filters" toggle button is clicked — this is what caused
        filter_by_blacklist() to time out in wait_for_element_visible()
        even though the earlier is_element_present() presence-check passed."""
        try:
            el = self.page.locator(self.FILTER_BLACKLIST).first
            if el.is_visible():
                return
        except Exception:
            pass
        try:
            self._js_click(self.BTN_FILTERS, timeout=5000)
            self.page.wait_for_timeout(1000)
        except Exception:
            pass

    def filter_by_blacklist(self, value):
        """Select an option in the Blacklist Contact filter dropdown.
        value: "Yes" / "No" / "All" (visible text) — falls back to the
        underlying option value ("1"/"0"/"") if the visible text doesn't
        match, since this is a wire:model.live-bound <select> that reloads
        the table via Livewire on change."""
        self._ensure_filters_panel_open()
        el = self.h.wait_for_element_visible(self.FILTER_BLACKLIST)
        try:
            el.select_option(label=value)
        except Exception:
            fallback = {"all": "", "yes": "1", "no": "0"}.get(str(value).strip().lower(), value)
            el.select_option(value=fallback)
        self.page.wait_for_timeout(1500)

    def has_records(self):
        return self.is_element_present(self.TABLE_ROWS, timeout=5000)

    def has_no_records_message(self):
        """True if an explicit empty-state message is shown, OR the table
        has zero real data rows (covers apps whose empty-state text doesn't
        match our generic keyword list)."""
        if self.is_element_present(self.NO_RECORDS_MSG, timeout=3000):
            return True
        return self.get_row_count() == 0

    def get_row_count(self):
        rows = self.page.locator("table tbody tr")
        count = 0
        for i in range(rows.count()):
            row = rows.nth(i)
            tds = row.locator("td")
            if tds.count() == 0:
                continue
            row_text = row.inner_text().strip().lower()
            if any(kw in row_text for kw in ["no record", "no data", "no result", "no item", "not found", "empty"]):
                continue
            if any(t.strip() for t in tds.all_inner_texts()):
                count += 1
        return count

    def get_visible_column_headers(self):
        return self._get_headers_safe(self.COLUMN_HEADER)

    def get_column_index(self, header_text):
        """Resolve a column's index dynamically by matching its visible header
        text (case-insensitive substring match). Returns None if not found.
        Prefer this over hardcoding an index — column order can shift if a
        selection checkbox column exists, or if a user has hidden/reordered
        columns via the Columns dropdown."""
        headers = self.get_visible_column_headers()
        for i, h in enumerate(headers):
            if header_text.lower() in h.lower():
                return i
        return None

    # ══════════════════════════════════════════════════════════════════════════
    # Columns dropdown
    # ══════════════════════════════════════════════════════════════════════════

    def open_column_toggle(self):
        self.h.wait_for_element_clickable(self.BTN_COLUMNS).click()
        self.page.wait_for_timeout(500)

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

    # ══════════════════════════════════════════════════════════════════════════
    # Sorting
    # ══════════════════════════════════════════════════════════════════════════

    def click_sort(self, header_text):
        """Click a sortable column header by its visible text (e.g. 'Full Name').
        More resilient than guessing the exact wire:click('sortBy(...)') field key.
        """
        locator = f"xpath=//th[contains(normalize-space(.),'{header_text}')]"
        self._js_click(locator, timeout=10000)
        self.page.wait_for_timeout(1500)

    def get_column_values(self, col_index):
        rows = self.page.locator("table tbody tr")
        values = []
        for i in range(rows.count()):
            tds = rows.nth(i).locator("td")
            if tds.count() > col_index:
                values.append(tds.nth(col_index).inner_text().strip())
        return values

    # ══════════════════════════════════════════════════════════════════════════
    # Bulk actions / Export
    # ══════════════════════════════════════════════════════════════════════════

    def _first_visible(self, locator):
        """Return the first genuinely VISIBLE Locator matching `locator`, or
        None. Mere DOM presence isn't enough — Alpine's x-show/x-on:click=
        "open = !open" dropdown keeps the Export option's node in the DOM at
        all times (just display:none when closed), and some Tailwind layouts
        render duplicate mobile/desktop copies of the same button. Filtering
        by is_visible() avoids clicking a hidden/off-screen duplicate that
        silently does nothing."""
        try:
            els = self.page.locator(locator)
            for i in range(els.count()):
                el = els.nth(i)
                try:
                    if el.is_visible():
                        return el
                except Exception:
                    continue
        except Exception:
            pass
        return None

    def _click_visible(self, el):
        el.scroll_into_view_if_needed()
        el.click(force=True)

    def _first_visible_of(self, locators):
        """Try each locator IN ORDER, return the first genuinely visible
        match. Prefer this over a single OR'd XPath when one clause is a
        broad text-contains() — with '|' the match is chosen by document
        order, not specificity, which can silently return a wrapping
        container instead of the actual clickable button/link."""
        for locator in locators:
            el = self._first_visible(locator)
            if el is not None:
                return el
        return None

    def export_to_xlsx(self, timeout_ms=30000):
        """Migration note: the Selenium version polled DOWNLOAD_DIR on disk
        for a new/updated .xlsx file (this app names every export the same
        "Contact Summary.xlsx", so it had to match on mtime rather than
        filename). Playwright captures the download as an event directly —
        page.expect_download() wraps the click and returns the Download
        object as soon as the browser starts it, with no folder polling or
        filename collisions to worry about."""
        self._close_sidebar_overlay()

        # The Export option lives inside the "Bulk Actions" dropdown menu (an
        # Alpine x-on:click="open = !open" toggle). Its DOM node exists even
        # while the dropdown is closed — so we must check VISIBILITY, not mere
        # presence, before deciding whether the dropdown still needs opening.
        export_el = self._first_visible_of(self.BTN_EXPORT_XLSX_LOCATORS)
        for attempt in range(4):
            if export_el is not None:
                break
            bulk_el = self._first_visible_of(self.BTN_BULK_ACTIONS_LOCATORS)
            if bulk_el is not None:
                self._click_visible(bulk_el)
            else:
                # Fall back to a presence-based click on the very first attempt
                # in case is_visible() is momentarily unreliable mid-render.
                try:
                    self._js_click(self.BTN_BULK_ACTIONS, timeout=5000)
                except Exception:
                    pass
            self.page.wait_for_timeout(1000)
            export_el = self._first_visible_of(self.BTN_EXPORT_XLSX_LOCATORS)

        if export_el is None:
            raise RuntimeError(
                "Export XLSX: could not find a visible 'Export to XLSX' option after "
                "opening the Bulk Actions dropdown — locator may need updating"
            )

        start = time.time()
        with self.page.expect_download(timeout=timeout_ms) as dl_info:
            self._click_visible(export_el)
        download = dl_info.value
        elapsed = round(time.time() - start, 2)
        dest = os.path.join(DOWNLOAD_DIR, download.suggested_filename)
        download.save_as(dest)
        return {"elapsed_s": elapsed, "file_path": dest, "file_size": os.path.getsize(dest)}

    # ══════════════════════════════════════════════════════════════════════════
    # Row actions
    # ══════════════════════════════════════════════════════════════════════════

    # Relative (row-scoped) versions of the ROW_*_BTN XPaths above, used with
    # _first_visible_data_row() so the search never risks matching a hidden
    # duplicate table's first row (see _first_visible_data_row docstring).
    _ROW_VIEW_REL = (
        "xpath=.//a[contains(@data-tooltip-target,'tooltip-view') "
        "or (contains(@href,'/contacts/') and not(contains(@href,'edit')) and not(contains(@href,'create')))]"
    )
    _ROW_EDIT_REL = "xpath=.//*[contains(@data-tooltip-target,'tooltip-edit')]"
    _ROW_BLACKLIST_REL = "xpath=.//*[contains(@data-tooltip-target,'tooltip-block')]"
    _ROW_DELETE_REL = "xpath=.//*[contains(@data-tooltip-target,'tooltip-deleteOne') or contains(@data-tooltip-target,'deleteOne')]"

    def click_first_row_view(self):
        row = self._first_visible_data_row()
        if row is None:
            return False
        links = row.locator(self._ROW_VIEW_REL)
        if links.count() > 0:
            href = links.first.get_attribute("href")
            if href:
                url = href if href.startswith("http") else f"{Config.BASE_URL}{href}"
                self.page.goto(url)
            else:
                links.first.click(force=True)
            self.page.wait_for_timeout(2000)
            return True
        return False

    def click_first_row_edit(self):
        row = self._first_visible_data_row()
        if row is None:
            return False
        els = row.locator(self._ROW_EDIT_REL)
        if els.count() == 0:
            return False
        els.first.scroll_into_view_if_needed()
        els.first.click(force=True)
        self.page.wait_for_timeout(1500)
        return True

    def click_first_row_blacklist(self, accept=True):
        """Blacklist uses a native JS confirm() dialog. A native confirm()
        blocks page script execution until answered, which means the click
        that triggers it never "finishes" from Playwright's point of view
        until the dialog is handled — so the handler MUST be registered with
        page.once("dialog", ...) BEFORE the click, not awaited afterward via
        expect_event() (that pattern deadlocks here: the click call blocks
        waiting for its own dialog to be dismissed, and the dismiss code
        never runs because it's written to run after the click returns).
        This replaces Selenium's driver.switch_to.alert."""
        row = self._first_visible_data_row()
        if row is None:
            return False
        els = row.locator(self._ROW_BLACKLIST_REL)
        if els.count() == 0:
            return False
        els.first.scroll_into_view_if_needed()

        def _handle_dialog(dialog):
            if accept:
                dialog.accept()
            else:
                dialog.dismiss()

        self.page.once("dialog", _handle_dialog)
        try:
            els.first.click()
        except Exception:
            # A native click can be intercepted by a leftover overlay (e.g. a
            # modal backdrop from a prior test that didn't close cleanly).
            # dispatch_event bypasses hit-testing but still fires the
            # x-on:click.prevent handler that opens the native confirm().
            els.first.dispatch_event("click")
        self.page.wait_for_timeout(1500)
        return True

    def _dialog_visible(self, timeout=6000):
        try:
            self.page.locator(self.CONFIRM_DELETE_BTN).first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def click_first_row_delete(self):
        row = self._first_visible_data_row()
        if row is None:
            return False
        btns = row.locator(self._ROW_DELETE_REL)
        if btns.count() == 0:
            return False
        btn = btns.first
        btn.scroll_into_view_if_needed()
        self.page.wait_for_timeout(500)
        try:
            btn.click()
        except Exception:
            btn.dispatch_event("click")
        return self._dialog_visible(timeout=8000)

    def confirm_delete(self):
        btn = self.h.wait_for_element_clickable(self.CONFIRM_DELETE_BTN, timeout=10000)
        btn.click(force=True)
        self.page.wait_for_timeout(2000)

    def cancel_delete(self):
        btn = self.h.wait_for_element_clickable(self.CANCEL_DELETE_BTN, timeout=10000)
        btn.click(force=True)
        self.page.wait_for_timeout(500)

    # ══════════════════════════════════════════════════════════════════════════
    # Modal (Edit contact) cancel / save
    # ══════════════════════════════════════════════════════════════════════════

    def is_modal_open(self):
        return self.is_element_present(self.MODAL_ROOT, timeout=5000)

    def click_modal_cancel(self):
        self._js_click(self.MODAL_CANCEL_BTN, timeout=10000)
        self.page.wait_for_timeout(500)

    def click_modal_save(self):
        """CONFIRMED from live DOM: the Edit Contact modal's submit button is a
        plain <button type="submit">Save</button> with no other distinguishing
        class — matches MODAL_SAVE_BTN's scoped '//div[fixed]//button[@type=submit]'."""
        self._js_click(self.MODAL_SAVE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_success_toast_shown(self):
        return self.is_element_present(self.TOAST_SUCCESS, timeout=5000)

    def get_toast_error(self):
        try:
            elements = self.page.locator(self.TOAST_ERROR)
            for i in range(elements.count()):
                el = elements.nth(i)
                try:
                    if el.is_visible() and el.inner_text().strip():
                        return el.inner_text().strip()
                except Exception:
                    continue
        except Exception:
            pass
        return None

    # ══════════════════════════════════════════════════════════════════════════
    # Create New Contact form
    # ══════════════════════════════════════════════════════════════════════════

    def fill_first_name(self, value):
        self.h.clear_and_type(self.FORM_FIRST_NAME, value)

    def fill_last_name(self, value):
        self.h.clear_and_type(self.FORM_LAST_NAME, value)

    def select_country(self, country):
        el = self.h.wait_for_element_visible(self.FORM_COUNTRY)
        try:
            el.select_option(label=country)
        except Exception:
            el.select_option(value=country)

    def fill_phone(self, value):
        self.h.clear_and_type(self.FORM_PHONE, value)

    def fill_email(self, value):
        self.h.clear_and_type(self.FORM_EMAIL, value)

    def fill_company(self, value):
        self.h.clear_and_type(self.FORM_COMPANY, value)

    def open_tags_dropdown(self):
        """The #tags element is a hidden input (wire:model carrier) behind a custom
        Alpine/WireUI multiselect trigger — it is never itself 'clickable'.
        Try a normal click first, then fall back to a force click on the input or its
        visible ancestor wrapper (which normally owns the toggle-open handler)."""
        try:
            self.h.wait_for_element_clickable(self.FORM_TAGS_INPUT, timeout=3000).click()
            self.page.wait_for_timeout(1000)
            return
        except Exception:
            pass
        try:
            self.page.locator(self.FORM_TAGS_INPUT).first.click(force=True)
        except Exception:
            pass
        self.page.wait_for_timeout(500)
        try:
            wrapper = self.page.locator(
                "xpath=//*[@id='tags']/ancestor::div[not(contains(@style,'display: none'))][1]"
            ).first
            wrapper.click(force=True)
        except Exception:
            pass
        self.page.wait_for_timeout(1000)

    def get_tags_dropdown_options(self):
        self.open_tags_dropdown()
        return [t.strip() for t in self.page.locator(self.FORM_TAGS_DROPDOWN_OPTIONS).all_inner_texts() if t.strip()]

    def select_tags(self, tag_names):
        """Open the tags multiselect and click each option whose visible text
        matches an entry in tag_names (e.g. ['demo', 'test', 'campaign'] —
        confirmed valid tag values on testqa.cpaas.globeteleservices.com).
        Silently skips any tag not found in the dropdown — the multiselect's
        exact markup can vary, so this is best-effort rather than a hard
        requirement."""
        self.open_tags_dropdown()
        for name in tag_names:
            try:
                opt = self.page.locator(
                    "xpath=//ul[contains(@class,'dropdown') or @role='listbox']"
                    f"//li[contains(normalize-space(.),'{name}')]"
                ).first
                opt.scroll_into_view_if_needed()
                opt.click(force=True)
                self.page.wait_for_timeout(400)
            except Exception:
                continue

    def click_add_custom_field(self):
        self.h.wait_for_element_clickable(self.BTN_ADD_CUSTOM_FIELD).click()
        self.page.wait_for_timeout(500)

    def is_custom_field_empty_state_shown(self):
        return self.is_element_present(self.CUSTOM_FIELD_EMPTY_MSG, timeout=5000)

    def get_custom_field_row_count(self):
        return self.page.locator(self.CUSTOM_FIELD_ROWS).count()

    def click_form_cancel(self):
        self._js_click(self.BTN_FORM_CANCEL, timeout=10000)
        self.page.wait_for_timeout(1000)

    def click_form_save(self):
        self._js_click(self.BTN_FORM_SAVE, timeout=10000)
        self.page.wait_for_timeout(1500)

    def get_validation_errors(self):
        return [t for t in self.page.locator(self.FORM_VALIDATION_ERROR).all_inner_texts() if t.strip()]

    def fill_contact_form(self, first_name=None, last_name=None, country=None,
                           phone=None, email=None, company=None):
        if first_name is not None:
            self.fill_first_name(first_name)
        if last_name is not None:
            self.fill_last_name(last_name)
        if country is not None:
            try:
                self.select_country(country)
            except Exception:
                pass
        if phone is not None:
            self.fill_phone(phone)
        if email is not None:
            self.fill_email(email)
        if company is not None:
            self.fill_company(company)

    # ══════════════════════════════════════════════════════════════════════════
    # View Contact page
    # ══════════════════════════════════════════════════════════════════════════

    def navigate_to_view_contact(self, contact_id):
        self.open(f"/contacts/{contact_id}")
        self.page.wait_for_timeout(2000)
        self._close_sidebar_overlay()

    def is_view_contact_page(self):
        return bool(re.search(r"/contacts/\d+", self.get_current_url()))

    def is_view_blacklist_btn_visible(self):
        return self.is_element_present(self.VIEW_BLACKLIST_BTN, timeout=5000)

    def is_custom_fields_section_visible(self):
        return self.is_element_present(self.VIEW_CUSTOM_FIELDS_SECTION, timeout=5000)

    # ══════════════════════════════════════════════════════════════════════════
    # Import Contacts modal
    # ══════════════════════════════════════════════════════════════════════════

    def is_import_modal_open(self):
        return self.is_element_present(self.IMPORT_MODAL, timeout=5000)

    def click_import_tab_copy_paste(self):
        self.h.wait_for_element_clickable(self.IMPORT_TAB_COPY_PASTE).click()
        self.page.wait_for_timeout(500)

    def click_import_tab_upload(self):
        self.h.wait_for_element_clickable(self.IMPORT_TAB_UPLOAD).click()
        self.page.wait_for_timeout(500)

    def paste_contacts(self, text):
        box = self.h.wait_for_element_visible(self.IMPORT_PASTE_TEXTAREA)
        box.fill(text)

    def select_import_tag(self, tag_name):
        try:
            el = self.h.wait_for_element_visible(self.IMPORT_TAG_DROPDOWN)
            el.click()
            self.page.wait_for_timeout(500)
            self.page.locator(f"xpath=//li[contains(.,'{tag_name}')]").first.click()
        except Exception:
            pass

    def upload_file(self, file_path):
        """Playwright's set_input_files() works on file inputs regardless of
        visibility, unlike Selenium's send_keys() which needed the input's
        display:none forced to 'block' first."""
        file_input = self.page.locator(self.IMPORT_FILE_INPUT).first
        file_input.wait_for(state="attached", timeout=20000)
        file_input.set_input_files(os.path.abspath(file_path))
        try:
            self.page.locator(self.LOADER).first.wait_for(state="hidden", timeout=30000)
        except Exception:
            # LOADER locator may not match this app's loading indicator at
            # all — fall back to a flat wait long enough for the server-side
            # XLSX parse/validation round trip to finish before callers check
            # for the Submit button.
            self.page.wait_for_timeout(5000)

    def click_download_sample(self):
        self.h.wait_for_element_clickable(self.BTN_DOWNLOAD_SAMPLE).click()
        self.page.wait_for_timeout(2000)

    def click_import_submit(self):
        btn = self.page.locator(self.BTN_IMPORT_SUBMIT).first
        btn.wait_for(state="visible", timeout=20000)
        btn.click(force=True)
        self.page.wait_for_timeout(2000)

    def try_click_import_submit(self, timeout_ms=8000):
        """Non-throwing variant of click_import_submit(). Some import flows
        show validation errors immediately after file selection and never
        surface/enable the submit button — return False instead of raising
        so callers can fall back to checking for an inline error."""
        try:
            btn = self.page.locator(self.BTN_IMPORT_SUBMIT).first
            btn.wait_for(state="visible", timeout=timeout_ms)
            btn.click(force=True)
            self.page.wait_for_timeout(2000)
            return True
        except Exception:
            return False

    def click_cancel_import(self):
        self.h.wait_for_element_clickable(self.BTN_CANCEL_IMPORT).click()
        self.page.wait_for_timeout(500)

    def get_import_error(self):
        if self.is_element_present(self.IMPORT_ERROR_MSG, timeout=5000):
            return self.h.wait_for_element_visible(self.IMPORT_ERROR_MSG).inner_text()
        return None

    def get_import_success(self):
        if self.is_element_present(self.IMPORT_SUCCESS_MSG, timeout=5000):
            return self.h.wait_for_element_visible(self.IMPORT_SUCCESS_MSG).inner_text()
        return None
