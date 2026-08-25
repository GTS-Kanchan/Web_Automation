from pages.common.base_page import BasePage


class TagsPage(BasePage):

    TAGS_URL = "/tags"

    BTN_CREATE_TAG = "xpath=//button[contains(.,'Create New Tag')] | //a[contains(.,'Create New Tag')]"

    SEARCH_BOX = "input[wire\\:model\\.live='search'], input[placeholder*='Search' i]"

    BTN_COLUMNS = "xpath=//button[contains(.,'Column') or contains(.,'Columns')]"
    # CONFIRMED from live DOM captured on the Segmentation page (same
    # rappasoft/livewire-tables package — identical "-column-select-button" /
    # "-columnSelect-N" wire:key convention, "rappasoft-striped-row" table
    # rows, and data-tooltip-target row actions all match this app's Tags
    # table too): the dropdown panel's per-column checkboxes live inside
    # <div wire:key="{table}-columnSelect-{N}"> wrappers, each with a plain
    # <input type="checkbox" wire:model.live="selectedColumns" value="...">
    # — NOT inside anything with class="dropdown" or class="column" (that
    # was a guess that never matched any real element, which is why
    # uncheck_first_optional_column() always found zero checkboxes and the
    # test skipped). There's also a separate "All Columns" checkbox in a
    # wire:key="...-columnSelect-selectAll-{n}" wrapper (wire:click=
    # "deselectAllColumns", no wire:model.live) — explicitly excluded here
    # since toggling it hides every column, not just one.
    COLUMN_CHECKBOXES = (
        "xpath=//div[contains(@wire:key,'columnSelect-') and not(contains(@wire:key,'columnSelect-selectAll'))]"
        "//input[@type='checkbox']"
    )
    COLUMN_HEADER = "table thead th"

    TABLE_ROWS = "table tbody tr"
    # CONFIRMED elsewhere via real screenshots (SMS Error Codes / Sender ID
    # pages) that this app's shared empty-state text is "No items found,
    # try to broaden your search" — added case-insensitively alongside the
    # original phrases, which are kept as a fallback.
    NO_RECORDS_MSG = (
        "xpath=//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no items found') "
        "or contains(text(),'No records') or contains(text(),'No data') or contains(text(),'No results') "
        "or contains(text(),'No tags')]"
    )

    ROW_EDIT_BTN = "xpath=(//table//tbody//tr)[1]//*[contains(@data-tooltip-target,'tooltip-edit')]"
    ROW_DELETE_BTN = (
        "xpath=(//table//tbody//tr)[1]//*[contains(@data-tooltip-target,'tooltip-deleteOne') "
        "or contains(@data-tooltip-target,'deleteOne')]"
    )

    # CONFIRMED convention (same as contacts_page.py): delete triggers
    # $wireui.confirmAction(...), WireUI's helper which renders a SweetAlert2
    # dialog — its buttons always carry swal2-confirm/swal2-cancel classes
    # regardless of label text, which is more reliable than guessing the label.
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

    MODAL_ROOT = "xpath=//div[contains(@class,'fixed') and (.//h1 or .//h2 or .//h3)]"
    FORM_TAG_NAME = "input[wire\\:model\\.defer='tag_name'], #tag_name"
    FORM_TAG_DESC = "textarea[wire\\:model\\.defer='tag_desc'], #tag_desc"
    MODAL_SAVE_BTN = "xpath=//div[contains(@class,'fixed')]//button[@type='submit']"
    MODAL_CANCEL_BTN = (
        "xpath=//div[contains(@class,'fixed')]//button[contains(.,'Cancel')] "
        "| //div[contains(@class,'fixed')]//button[@type='button' and contains(.,'Close')]"
    )
    FORM_VALIDATION_ERROR = "[class*='error'], [class*='invalid-feedback'], .text-danger, [class*='text-red']"

    TOAST_SUCCESS = (
        "xpath=//*[contains(text(),'success') or contains(text(),'Success') or contains(text(),'successfully')] "
        "| //*[contains(@class,'toast') and not(contains(@class,'error'))]"
    )
    TOAST_ERROR = (
        "xpath=//*[contains(text(),'error') or contains(text(),'Error') or contains(text(),'failed') or contains(text(),'Failed')] "
        "| //*[contains(@class,'toast-error') or contains(@class,'alert-danger')]"
    )

    def navigate_to_tags(self):
        self.open(self.TAGS_URL)
        self.page.wait_for_timeout(2000)
        self._close_sidebar_overlay()
        return self

    def is_tags_page(self):
        url = self.get_current_url()
        return "/tags" in url and "login" not in url.lower()

    def click_create_tag(self):
        self._close_sidebar_overlay()
        self._js_click(self.BTN_CREATE_TAG, timeout=15000)
        self.page.wait_for_timeout(1000)

    def is_create_tag_modal_open(self):
        return self.is_element_present(self.FORM_TAG_NAME, timeout=5000)

    def search(self, value):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.fill(value)
        self.page.wait_for_timeout(1500)

    def clear_search(self):
        """CONFIRMED convention (same as segmentation/contacts pages): the
        search box is wire:model.live='search', so clearing it should fire
        an immediate Livewire round trip that reloads the table — no Enter
        key needed. But a live run of the Selenium suite showed a plain
        clear() alone wasn't always enough: the browser could be left stuck
        on /tags?table-search=<stale value> (the query string is aliased to
        "table-search", per the same queryStringConfig convention seen on
        the Segmentation table) if the 'input' event Livewire listens for
        didn't reliably fire/land in time. Belt-and-suspenders fix: fill('')
        (which itself dispatches input/change), then poll for the table to
        settle. As a last-resort guarantee, if the URL still shows a search
        query string after all that, hard-navigate back to the clean Tags
        URL — this must never leave the browser stuck on a filtered view,
        since _reset_after_test() relies on it to reset state between every
        test in this module-scoped session."""
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.fill("")
        self.page.wait_for_timeout(500)
        self.h.wait_until(lambda: self.has_records() or self.has_no_records_message(), timeout_ms=6000)
        self.page.wait_for_timeout(500)
        if "search=" in self.get_current_url():
            self.navigate_to_tags()

    def has_records(self):
        return self.is_element_present(self.TABLE_ROWS, timeout=5000)

    def has_no_records_message(self):
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

    def open_column_toggle(self):
        self.h.wait_for_element_clickable(self.BTN_COLUMNS).click()
        self.page.wait_for_timeout(500)

    def get_visible_column_headers(self):
        return self._get_headers_safe(self.COLUMN_HEADER)

    def uncheck_first_optional_column(self):
        """Uses a JS-style force click on the checkbox (not a plain native
        click) since it sits inside an Alpine x-show dropdown panel — the
        same class of element that has needed a force click elsewhere in
        this app (e.g. the Active toggle) to avoid a styled sibling/overlay
        intercepting the click point."""
        self.open_column_toggle()
        checkboxes = self.page.locator(self.COLUMN_CHECKBOXES)
        for i in range(checkboxes.count()):
            cb = checkboxes.nth(i)
            if cb.is_checked():
                cb.scroll_into_view_if_needed()
                cb.click(force=True)
                self.page.wait_for_timeout(800)
                return True
        return False

    def fill_tag_name(self, value):
        self.h.clear_and_type(self.FORM_TAG_NAME, value)

    def fill_tag_description(self, value):
        self.h.clear_and_type(self.FORM_TAG_DESC, value)

    def click_modal_save(self):
        self._js_click(self.MODAL_SAVE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def click_modal_cancel(self):
        self._js_click(self.MODAL_CANCEL_BTN, timeout=10000)
        self.page.wait_for_timeout(500)

    def is_modal_open(self):
        return self.is_element_present(self.MODAL_ROOT, timeout=5000)

    def get_validation_errors(self):
        errors = self.page.locator(self.FORM_VALIDATION_ERROR)
        return [t for t in errors.all_inner_texts() if t.strip()]

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

    # Relative (row-scoped) versions of ROW_EDIT_BTN/ROW_DELETE_BTN, used with
    # _first_visible_data_row() (BasePage) so the search is anchored to a
    # confirmed-visible row instead of a bare "(//table//tbody//tr)[1]"
    # document-order query, which can silently match a hidden duplicate
    # table row (e.g. a mobile-breakpoint copy) that lacks the same buttons.
    _ROW_EDIT_REL = "xpath=.//*[contains(@data-tooltip-target,'tooltip-edit')]"
    _ROW_DELETE_REL = "xpath=.//*[contains(@data-tooltip-target,'tooltip-deleteOne') or contains(@data-tooltip-target,'deleteOne')]"

    def click_first_row_edit(self):
        row = self._first_visible_data_row()
        if row is None:
            return False
        el = row.locator(self._ROW_EDIT_REL)
        if el.count() == 0:
            return False
        el.first.scroll_into_view_if_needed()
        el.first.click(force=True)
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
