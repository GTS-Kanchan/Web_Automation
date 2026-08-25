from pages.common.base_page import BasePage


class SegmentationPage(BasePage):

    SEGMENTATION_URL = "/contacts/segmentation"
    SEGMENTATION_KEYS_URL = "/contacts/segmentation/fields"

    BTN_CREATE_SEGMENT = "xpath=//button[contains(.,'Create Segment')] | //a[contains(.,'Create Segment')]"
    LINK_SEGMENT_KEYS = "xpath=//a[contains(.,'Segment Keys')]"
    LINK_BACK_TO_CONTACTS = "xpath=//a[contains(.,'Back to Contacts')]"

    SEARCH_BOX = "input[wire\\:model\\.live='search'], input[placeholder*='Search' i]"

    TABLE_ROWS = "table tbody tr"
    # CONFIRMED elsewhere via real screenshots (SMS Error Codes / Sender ID
    # pages) that this app's shared empty-state text is "No items found,
    # try to broaden your search" — added case-insensitively alongside the
    # original phrases, which are kept as a fallback.
    NO_RECORDS_MSG = (
        "xpath=//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no items found') "
        "or contains(text(),'No records') or contains(text(),'No data') or contains(text(),'No results') "
        "or contains(text(),'No segments')]"
    )

    ROW_VIEW_BTN = (
        "xpath=(//table//tbody//tr)[1]//*[contains(@data-tooltip-target,'tooltip-view') "
        "or @*[name()='wire:click' and contains(.,\"'segmentation.view-conditions'\")]]"
    )
    ROW_EDIT_BTN = (
        "xpath=(//table//tbody//tr)[1]//*[contains(@data-tooltip-target,'tooltip-edit') "
        "or @*[name()='wire:click' and contains(.,\"'segmentation.edit-segment'\")]]"
    )
    ROW_DELETE_BTN = (
        "xpath=(//table//tbody//tr)[1]//*[contains(@data-tooltip-target,'tooltip-deleteOne') "
        "or contains(@data-tooltip-target,'deleteOne')]"
    )

    # CONFIRMED via pasted DOM: delete triggers x-on:click="$wireui.confirmAction(...)"
    # which renders WireUI's OWN Alpine dialog (x-data="wireui_dialog(...)"), NOT
    # SweetAlert2 — the actual accept button captured is:
    #   <button type="button" x-on:click="accept"> Confirm </button>
    # Same mechanism already confirmed on SMSSenderIDPage / SMSTemplatePage.
    CONFIRM_DELETE_BTN = "xpath=//button[normalize-space()='Confirm']"
    CANCEL_DELETE_BTN = "xpath=//button[normalize-space()='Cancel']"

    MODAL_ROOT = "xpath=//div[contains(@class,'fixed') and (.//h1 or .//h2 or .//h3)]"
    FORM_NAME = "#name"
    FORM_DESCRIPTION = "#description"
    FORM_ACTIVE_TOGGLE = "#segment_active_create"
    BTN_ADD_CONDITION = "xpath=//button[contains(.,'Add Condition')]"
    # NOTE: scoped to the modal (not text-matched) — the Edit Segment modal's
    # submit button reads "Update Segment", not "Save Segment", so matching on
    # text caused click_modal_save() to time out during edit-flow tests.
    MODAL_SAVE_BTN = "xpath=//div[contains(@class,'fixed')]//button[@type='submit']"
    MODAL_CANCEL_BTN = (
        "xpath=//div[contains(@class,'fixed')]//button[contains(.,'Cancel')] "
        "| //div[contains(@class,'fixed')]//button[@type='button' and contains(.,'Close')]"
    )
    # CONFIRMED from live DOM (Create Segment modal): per-field validation
    # errors render as <label class="text-sm text-negative-600 mt-2" for="name">
    # The name field is required.</label> — same WireUI "negative" variant
    # used on the Create Contact form.
    FORM_VALIDATION_ERROR = "label.text-negative-600, .text-negative-600"

    VIEW_CONDITIONS_MODAL = "xpath=//div[contains(@class,'fixed') and contains(.,'Condition')]"

    TOAST_SUCCESS = (
        "xpath=//*[contains(text(),'success') or contains(text(),'Success') or contains(text(),'successfully')] "
        "| //*[contains(@class,'toast') and not(contains(@class,'error'))]"
    )
    TOAST_ERROR = (
        "xpath=//*[contains(text(),'error') or contains(text(),'Error') or contains(text(),'failed') or contains(text(),'Failed')] "
        "| //*[contains(@class,'toast-error') or contains(@class,'alert-danger')]"
    )

    KEYS_TABLE_ROWS = "table tbody tr"
    KEY_ROW_EDIT_BTN = (
        "xpath=(//table//tbody//tr)[1]//*[contains(@data-tooltip-target,'tooltip-edit') "
        "or @*[name()='wire:click' and contains(.,\"'segmentation.edit-field'\")]]"
    )
    KEY_ROW_DELETE_BTN = (
        "xpath=(//table//tbody//tr)[1]//*[contains(@data-tooltip-target,'tooltip-deleteOne') "
        "or contains(@data-tooltip-target,'deleteOne')]"
    )
    KEY_FORM_NAME = "input[wire\\:model\\.defer='key'], #key, input[name='key']"
    KEY_FORM_TYPE = "select[wire\\:model\\.defer='type'], #type, select[name='type']"
    KEY_MODAL_SAVE_BTN = "xpath=//div[contains(@class,'fixed')]//button[@type='submit']"

    def navigate_to_segmentation(self):
        self.open(self.SEGMENTATION_URL)
        self.page.wait_for_timeout(2000)
        self._close_sidebar_overlay()
        return self

    def navigate_to_segmentation_keys(self):
        self.open(self.SEGMENTATION_KEYS_URL)
        self.page.wait_for_timeout(2000)
        self._close_sidebar_overlay()
        return self

    def is_segmentation_page(self):
        url = self.get_current_url()
        return "/contacts/segmentation" in url and "fields" not in url and "login" not in url.lower()

    def is_segmentation_keys_page(self):
        url = self.get_current_url()
        return "/contacts/segmentation/fields" in url and "login" not in url.lower()

    def click_create_segment(self):
        self._close_sidebar_overlay()
        self._js_click(self.BTN_CREATE_SEGMENT, timeout=15000)
        self.page.wait_for_timeout(1000)

    def click_segment_keys_link(self):
        self._js_click(self.LINK_SEGMENT_KEYS, timeout=10000)
        self.page.wait_for_timeout(1500)

    def click_back_to_contacts(self):
        self._js_click(self.LINK_BACK_TO_CONTACTS, timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_create_segment_modal_open(self):
        return self.is_element_present(self.FORM_NAME, timeout=5000)

    def search(self, value):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.fill(value)
        self.page.wait_for_timeout(1500)

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

    def fill_name(self, value):
        """CONFIRMED from live DOM: #name is bound wire:model.live="name" — every
        clear/keystroke fires an immediate Livewire round trip (debounced ~150ms)
        that morphs the modal's DOM, e.g. clearing it live-validates and injects
        the "The name field is required." error label without needing Save
        clicked at all. If click_modal_save() (or any other action) fires while
        that morph is still in flight, the click can land mid-morph — right as
        Alpine/Livewire are re-binding wire:submit.prevent on the new <form>
        node — and the click ends up hitting a plain, not-yet-hooked
        type="submit" button, causing a real native HTML form POST (full page
        refresh) instead of the intended Livewire-handled submit. Waiting
        briefly here lets that live round trip finish before any caller moves
        on, so the modal's DOM/listeners are stable by the time Save is clicked."""
        self.h.clear_and_type(self.FORM_NAME, value)
        self.page.wait_for_timeout(1500)

    def fill_description(self, value):
        self.h.clear_and_type(self.FORM_DESCRIPTION, value)

    def toggle_active(self, enable=True):
        """CONFIRMED from live DOM: the toggle is a visually-hidden Tailwind
        switch (class="sr-only peer") — a native click is blocked ('not
        clickable') because a styled sibling <div> intercepts the point.
        Force-click the input itself instead, which still fires the
        click/change events Alpine/Livewire listen for."""
        toggle = self.page.locator(self.FORM_ACTIVE_TOGGLE).first
        toggle.wait_for(state="attached", timeout=10000)
        if (toggle.is_checked() and not enable) or (not toggle.is_checked() and enable):
            toggle.click(force=True)
            self.page.wait_for_timeout(300)

    def is_active_checked(self):
        try:
            return self.page.locator(self.FORM_ACTIVE_TOGGLE).first.is_checked()
        except Exception:
            return None

    def click_add_condition(self):
        self.h.wait_for_element_clickable(self.BTN_ADD_CONDITION).click()
        self.page.wait_for_timeout(500)

    def _condition_locator(self, row_index, field):
        name = f"conditions.{row_index}.{field}"
        return f"[wire\\:model*='{name}'], [name*='{name}']"

    def select_condition_group(self, row_index, group_value):
        self.page.locator(self._condition_locator(row_index, "group_index")).first.select_option(value=str(group_value))

    def select_condition_field(self, row_index, field_label):
        loc = self.page.locator(self._condition_locator(row_index, "field_id")).first
        try:
            loc.select_option(label=field_label)
        except Exception:
            loc.select_option(value=field_label)

    def select_condition_operator(self, row_index, operator_label):
        loc = self.page.locator(self._condition_locator(row_index, "operator")).first
        try:
            loc.select_option(label=operator_label)
        except Exception:
            loc.select_option(value=operator_label)

    def fill_condition_value(self, row_index, value):
        self.h.clear_and_type(self._condition_locator(row_index, "value"), value)

    def add_condition(self, group_value, field_label, operator_label, value, row_index=0):
        """CONFIRMED from live DOM: the Create Segment modal's Livewire component
        initializes with ONE condition row already present at index 0
        (initial snapshot: conditions=[{field_id:null,group_index:1,operator:null,
        value:null,logic:'AND'}]) — it does NOT start empty. Clicking "Add
        Condition" unconditionally appends a SECOND, completely empty row
        (index 1) whose field_id/operator are required by backend validation
        but never get filled, which silently fails the save (no success
        toast) even though row 0 was filled correctly. Only click "Add
        Condition" when targeting a row beyond the first."""
        if row_index > 0:
            self.click_add_condition()
            self.page.wait_for_timeout(500)
        try:
            self.select_condition_group(row_index, group_value)
        except Exception:
            pass
        self.select_condition_field(row_index, field_label)
        self.select_condition_operator(row_index, operator_label)
        self.fill_condition_value(row_index, value)

    def click_modal_save(self):
        """Retries once: since #name is wire:model.live, a Livewire morph can
        still be landing when this is called (see fill_name()); if the
        button node we grabbed gets replaced out from under the click,
        re-locate and click the fresh one instead of letting the click
        silently miss/hit a stale node. Playwright's Locator API re-resolves
        on every call, so this retry is mostly a timing cushion rather than
        a strict-necessity fix."""
        try:
            self._js_click(self.MODAL_SAVE_BTN, timeout=10000)
        except Exception:
            self.page.wait_for_timeout(500)
            self._js_click(self.MODAL_SAVE_BTN, timeout=10000)
        self.page.wait_for_timeout(2000)

    def click_modal_cancel(self):
        self._js_click(self.MODAL_CANCEL_BTN, timeout=10000)
        self.page.wait_for_timeout(500)

    def is_modal_open(self):
        return self.is_element_present(self.MODAL_ROOT, timeout=5000)

    def get_validation_errors(self, timeout_ms=8000):
        """Polls rather than a single instant snapshot: Livewire round trips
        elsewhere in this app have needed similar waits (filter panels,
        import submit, etc.) — a single check right after
        click_modal_save()'s fixed wait can land before the submit's AJAX
        response has re-rendered the error label into the DOM. Poll for up
        to `timeout_ms`, returning as soon as a non-empty error is found."""
        result = []

        def _check():
            texts = [t for t in self.page.locator(self.FORM_VALIDATION_ERROR).all_inner_texts() if t.strip()]
            if texts:
                result.extend(texts)
                return True
            return False

        self.h.wait_until(_check, timeout_ms=timeout_ms)
        return result

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

    # Relative (row-scoped) versions of ROW_VIEW_BTN/ROW_EDIT_BTN/ROW_DELETE_BTN,
    # used with _first_visible_data_row() (BasePage) so the search is anchored
    # to a confirmed-visible row instead of a bare "(//table//tbody//tr)[1]"
    # document-order query, which can silently match a hidden duplicate table
    # row (e.g. a mobile-breakpoint copy) that lacks the same buttons.
    _ROW_VIEW_REL = (
        "xpath=.//*[contains(@data-tooltip-target,'tooltip-view') "
        "or @*[name()='wire:click' and contains(.,\"'segmentation.view-conditions'\")]]"
    )
    _ROW_EDIT_REL = (
        "xpath=.//*[contains(@data-tooltip-target,'tooltip-edit') "
        "or @*[name()='wire:click' and contains(.,\"'segmentation.edit-segment'\")]]"
    )
    _ROW_DELETE_REL = "xpath=.//*[contains(@data-tooltip-target,'tooltip-deleteOne') or contains(@data-tooltip-target,'deleteOne')]"
    _KEY_ROW_EDIT_REL = (
        "xpath=.//*[contains(@data-tooltip-target,'tooltip-edit') "
        "or @*[name()='wire:click' and contains(.,\"'segmentation.edit-field'\")]]"
    )
    _KEY_ROW_DELETE_REL = "xpath=.//*[contains(@data-tooltip-target,'tooltip-deleteOne') or contains(@data-tooltip-target,'deleteOne')]"

    def click_first_row_view(self):
        """Click the View (conditions) icon on the first visible data row.

        Records what _first_visible_data_row() actually returned in
        `last_row_view_debug` so a failure shows whether the row itself was
        the problem (e.g. no row found, or a row found with no matching
        button inside it) rather than guessing a locator change blind."""
        row = self._first_visible_data_row()
        if row is None:
            self.last_row_view_debug = {"row_found": False}
            return False
        els = row.locator(self._ROW_VIEW_REL)
        n = els.count()
        self.last_row_view_debug = {
            "row_found": True,
            "row_outer_html": (row.evaluate("el => el.outerHTML") or "")[:500],
            "matching_buttons": n,
        }
        if n == 0:
            return False
        els.first.scroll_into_view_if_needed()
        els.first.click(force=True)
        self.page.wait_for_timeout(1500)
        return True

    def is_view_conditions_modal_open(self):
        return self.is_element_present(self.VIEW_CONDITIONS_MODAL, timeout=5000)

    def click_first_row_edit(self):
        """Click the Edit icon on the first visible data row.

        Same evidence-capture rationale as click_first_row_view()."""
        row = self._first_visible_data_row()
        if row is None:
            self.last_row_edit_debug = {"row_found": False}
            return False
        els = row.locator(self._ROW_EDIT_REL)
        n = els.count()
        self.last_row_edit_debug = {
            "row_found": True,
            "row_outer_html": (row.evaluate("el => el.outerHTML") or "")[:500],
            "matching_buttons": n,
        }
        if n == 0:
            return False
        els.first.scroll_into_view_if_needed()
        els.first.click(force=True)
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

    def keys_has_records(self):
        return self.is_element_present(self.KEYS_TABLE_ROWS, timeout=5000)

    def keys_get_row_count(self):
        rows = self.page.locator("table tbody tr")
        count = 0
        for i in range(rows.count()):
            row = rows.nth(i)
            tds = row.locator("td")
            if tds.count() == 0:
                continue
            if any(t.strip() for t in tds.all_inner_texts()):
                count += 1
        return count

    def click_first_key_edit(self):
        row = self._first_visible_data_row()
        if row is None:
            return False
        els = row.locator(self._KEY_ROW_EDIT_REL)
        if els.count() == 0:
            return False
        els.first.scroll_into_view_if_needed()
        els.first.click(force=True)
        self.page.wait_for_timeout(1500)
        return True

    def fill_key_name(self, value):
        self.h.clear_and_type(self.KEY_FORM_NAME, value)

    def select_key_type(self, type_name):
        loc = self.h.wait_for_element_visible(self.KEY_FORM_TYPE)
        try:
            loc.select_option(label=type_name)
        except Exception:
            loc.select_option(value=type_name)

    def click_key_modal_save(self):
        self._js_click(self.KEY_MODAL_SAVE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def click_first_key_delete(self):
        row = self._first_visible_data_row()
        if row is None:
            return False
        btns = row.locator(self._KEY_ROW_DELETE_REL)
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
