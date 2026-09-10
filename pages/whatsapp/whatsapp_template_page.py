"""
Page Object: WhatsApp Templates listing page
Path: /whatsapp/channels/template
Livewire component: whatsapp.template.table (rappasoft/laravel-livewire-tables
package -- tableName "wa_templates"; same package/theme already confirmed
elsewhere in this app, e.g. pages/whatsapp/whatsapp_optout_page.py).

Built from a genuine, pasted live-DOM capture of this exact page (full page
source, ~1027 real template rows across 103 pages at capture time). The
component's wire:id ("RQ2wevp4NXeFHGtftsuH") is per-session/per-load and is
NOT hardcoded into any locator below -- only stable ids/names/wire:model
targets/values are used.

Confirmed facts from the real capture (do not "fix" these without a fresh
capture proving otherwise):

 1. Breadcrumb: Home > Channels > "WhatsApp Templates" (plain <span>, not a
    link). Header: <h1 class="text-md font-semibold whitespace-nowrap">
    WhatsApp Template</h1> (singular -- deliberately different text from
    the breadcrumb's plural "WhatsApp Templates").
 2. Search: <input wire:model.live="search" placeholder="Search" type="text">
    -- no id/wire:key, located by the wire:model.live attribute + placeholder.
 3. Filters panel (toggled via a "Filters" button, x-on:click="filtersOpen =
    !filtersOpen"; slide-down layout) has exactly 6 real fields, matching
    the Livewire snapshot's own "filterCount":6:
      - Department: <input id="wa_templates-filter-department"
        wire:model.live.debounce.500ms="filterComponents.department"
        type="text">
      - User: <input id="wa_templates-filter-user"
        wire:model.live.debounce.500ms="filterComponents.user" type="text">
      - Type: <select id="wa_templates-filter-type"
        wire:model.live="filterComponents.type"> -- confirmed real
        <option> values (see TYPE_OPTIONS below: "All" + 9 real types).
      - Status: <select id="wa_templates-filter-status"
        wire:model.live="filterComponents.status"> -- confirmed real
        value/label pairs (see STATUS_OPTIONS below: "All" + 8 real
        statuses).
      - Created From / Created To: <input type="date"
        id="wa_templates-filter-created_from"/"...created_to"
        wire:model.live="filterComponents.created_from"/"...created_to">,
        both with a max= attribute equal to "today" at render time.
 4. Bulk Action / Export: there is no dropdown -- the single confirmed
    control is a page-level "Export to XLSX" button (Alpine-only,
    @click="showModal = true") that opens a local confirm modal ("Export"
    header, "Are you sure you want to export the selected data?" text,
    "No" cancel / "Yes, Export" -> wire:click="exportAll"). The checklist's
    "Select any date range, Department and user -> click bulk action"
    wording does not match this real control: filters and export are
    independent, export is not gated on any filter selection. The modal's
    "ready to download" state (exportStatus/downloadUrl, watched via
    x-init/$watch plus a 5s wire:poll while the modal is open) was never
    captured with a populated value in this dump (exportStatus was null at
    capture time) -- so no "download link" locator is built here; only the
    confirm-and-fire step is exercised/exposed.
 5. Columns dropdown ("Columns" button, x-on:click="open = !open") has an
    "All Columns" checkbox (wire:click="selectAllColumns") plus 10 real
    per-column checkboxes (wire:model.live="selectedColumns", matching the
    Livewire snapshot's own "selectableColumns"): action/name/category/
    type/waba-number/department/user/status/quality/created-at. The
    default "selectedColumns" (8, confirmed from the snapshot) excludes
    "department" and "user" -- those two start unchecked.
 6. Table: <table id="table-wa_templates">, <tbody id="wa_templates-tbody">,
    data rows id="wa_templates-row-{id}" / rowpk="{id}". Column headers in
    DOM order: Action (static, no sort), then 7 CONFIRMED sortable columns
    via wire:click="sortBy(...)" on a <button> inside each <th>: Name
    (sortBy('name')), Category (sortBy('category')), Type (sortBy('type')),
    WABA Number (sortBy('senderId.number')), Status (sortBy('status')),
    Quality (sortBy('quality')), Created at (sortBy('created_at')).
    Default applied sort: "created_at" desc (confirmed sorting pill text:
    "Created at: Z-A"). Sorting pills use wire:key=
    "wa_templates-sorting-pill-{column}" with a per-pill
    wire:click="clearSort('{column}')", plus one global "Clear" pill-style
    button (wire:click.prevent="clearSorts") -- same pattern already
    confirmed on pages/whatsapp/whatsapp_optout_page.py.
 7. Row Actions column has up to 4 real, confirmed controls per row:
      - View: wire:click.prevent="$dispatch('openModal', { component:
        'whatsapp.template.view', arguments: {"templateId":<id>} })",
        data-tooltip-target="tooltip-view-{id}", tooltip text "View".
      - Edit: <a href="{base}/whatsapp/channels/template/{id}/edit"
        data-tooltip-target="tooltip-edit-{id}"> -- not in this checklist,
        not built.
      - Delete: <button data-tooltip-target="tooltip-delete-{id}"
        x-on:click="$wireui.confirmAction({title: 'Are you sure to delete
        this item ?', icon: 'warning', method: 'delete', params:
        ['Gts\\Whatsapp\\Models\\Template', <id>], accept: {style: 'solid',
        color: 'red'}}, '<componentId>')">, tooltip text "Delete". Same
        WireUI confirmAction -> SweetAlert2 convention already confirmed
        app-wide (pages/whatsapp/whatsapp_optout_page.py,
        pages/common/contacts_page.py, etc.) -- CONFIRM_DELETE_BTN /
        CANCEL_DELETE_BTN below are the same generic swal2-based locators
        already confirmed on whatsapp_optout_page.py (duplicated here per
        this project's no-cross-file-inheritance convention, not
        re-guessed).
      - Update Status: <button wire:click.prevent="updateStatus(<id>)"
        wire:loading.attr="disabled" wire:target="updateStatus(<id>)"
        data-tooltip-target="tooltip-update-status-{id}"> (green button),
        tooltip text "Update Status".
 8. **TC008 vs TC010 checklist duplication**: the checklist lists both
    "Verify View button in Actions" (TC008) and "Verify Template preview
    button in Actions" (TC010) as if they were two different controls. The
    real, captured DOM has exactly ONE such control per row -- the "View"
    button described in point 7 above, which dispatches the SAME
    'whatsapp.template.view' Livewire modal either way. There is no
    second, distinct "Preview" button anywhere in the captured markup.
    Both TC008 and TC010 are therefore automated against this single
    confirmed control rather than inventing a second one.
 9. **TC011 checklist mismatch**: TC011's own "Steps" column text ("Create
    new template with required data ... Click on save") does not describe
    its own "Test Case" title ("Verify Update template status button in
    Actions"). The real, matching control is the confirmed
    updateStatus(<id>) button from point 7 -- automated against that,
    per this project's "document, don't silently fix" convention.
10. **TC012 numbering gap**: the supplied checklist jumps from TC011
    straight to TC013 -- TC012 does not exist in the source spreadsheet.
    This is a numbering artifact only; no functionality is missing.
11. **Template Preview content** (opened by the View button, point 7): the
    'whatsapp.template.view' component's real rendered content was
    separately confirmed in a different capture (a minimal one-line "hi"
    body template): a "Preview" <h1> header, a close button that
    dispatches closeModal, a "Template ID: <id>" line, a chat-bubble-
    styled body <p>, a timestamp <p>, and a conditional opt-in/opt-out
    indicator (<i class="mdi mdi-reply">). That capture had NO template
    with Header/Footer/variables/buttons actually populated, so this page
    object exposes only the CONFIRMED elements (header, template ID, body
    text) -- it does not assert the Header/Footer/variables/buttons
    sub-sections the checklist mentions, since no capture of a template
    with those populated was ever supplied. These exact locator strings
    were already built once from the same source capture on
    pages/whatsapp/whatsapp_campaign_create_page.py -- duplicated here
    verbatim rather than shared/imported, per this project's flat-file/
    no-mixins convention for pages/whatsapp/.
12. Fetch Template: a real, global page-level button exists
    (onclick="Livewire.dispatch('openModal', { component:
    'whatsapp.template.fetch' })"), matching the checklist's TC015. Per
    explicit user instruction ("don't add fetch template"), NO locator or
    method for this control is built here, and no TC015 test exists in
    the paired test file.
13. Pagination: standard rappasoft/Laravel pagination markup (role=
    "navigation" aria-label="Pagination Navigation"). "Previous" renders
    as a non-interactive <span aria-disabled="true"> when on page 1;
    "Next"/numbered pages are real wire:click="nextPage('wa_templatesPage')"
    / wire:click="gotoPage(N, 'wa_templatesPage')" buttons (1027 rows /
    103 pages at capture time). No "Showing X to Y of Z results" summary
    text was present anywhere in this capture -- not built/asserted.
14. Delete is genuinely destructive here and this page has no "Create
    Template" flow in scope to manufacture a safe scratch row first
    (templates are synced from Meta/Gupshup via "Fetch Template", which is
    explicitly excluded per point 12) -- unlike e.g.
    tests/email/templates/test_email_template_flow.py's delete-confirm
    test, which creates its own scratch template first. TC009 is
    therefore exercised as open-dialog-then-CANCEL only; no real template
    row is deleted by this suite. click_delete_on_first_row()/
    is_delete_confirm_dialog_open()/cancel_delete()/confirm_delete() are
    all still exposed here (confirm_delete() intentionally unused by the
    paired test file) so a future scratch-data-capable suite can use them.

No cross-page inheritance/mixins per this project's established convention
(confirmed via `grep -rn "^class .*Page(" pages/ | grep -v "BasePage"`
returning zero matches).
"""
from pages.common.base_page import BasePage


class WhatsAppTemplatePage(BasePage):
    PATH = "/whatsapp/channels/template"
    TABLE_NAME = "wa_templates"

    # ── Header / breadcrumb ──────────────────────────────────────────────────
    PAGE_HEADER = "xpath=//h1[normalize-space()='WhatsApp Template']"
    BREADCRUMB_ACTIVE = "xpath=//nav[@aria-label='Breadcrumb']//li[contains(normalize-space(.),'WhatsApp Templates')]"

    # ── Search ───────────────────────────────────────────────────────────────
    SEARCH_INPUT = "input[wire\\:model\\.live='search'][placeholder='Search']"

    # ── Filters (slide-down layout, 6 confirmed fields) ─────────────────────
    FILTERS_TOGGLE_BTN = "xpath=//button[contains(normalize-space(.),'Filters')]"
    FILTER_DEPARTMENT = "#wa_templates-filter-department"
    FILTER_USER = "#wa_templates-filter-user"
    FILTER_TYPE = "#wa_templates-filter-type"
    FILTER_STATUS = "#wa_templates-filter-status"
    FILTER_CREATED_FROM = "#wa_templates-filter-created_from"
    FILTER_CREATED_TO = "#wa_templates-filter-created_to"

    # CONFIRMED real <option value>: <option label> pairs (module docstring #3)
    TYPE_OPTIONS = {
        "": "All",
        "custom_message": "Custom Message",
        "carousel": "Carousel",
        "catalog_message": "Catalog",
        "multi_product_message": "Multi-Product Message",
        "lto": "Limited Time Offer",
        "product_carousel": "Product Card Carousel",
        "order_status": "Order Status",
        "order_details": "Order Details",
        "authentication": "Authentication",
        "spm": "Single Product Message",
    }
    STATUS_OPTIONS = {
        "": "All",
        "3": "Approved",
        "9": "Archived",
        "10": "Deleted",
        "8": "Disabled",
        "6": "Failed",
        "7": "Paused",
        "1": "Pending",
        "4": "Rejected",
    }

    # ── Bulk Action / Export ─────────────────────────────────────────────────
    EXPORT_BTN = "xpath=//button[normalize-space()='Export to XLSX']"
    EXPORT_MODAL_HEADER = "xpath=//h2[normalize-space()='Export']"
    EXPORT_CONFIRM_TEXT = "xpath=//p[contains(normalize-space(.),'Are you sure you want to export the selected data')]"
    EXPORT_YES_BTN = "button[wire\\:click='exportAll']"
    EXPORT_NO_BTN = "xpath=//div[.//h2[normalize-space()='Export']]//button[normalize-space()='No']"

    # ── Columns dropdown ─────────────────────────────────────────────────────
    COLUMNS_TOGGLE_BTN = "xpath=//button[contains(normalize-space(.),'Columns')]"
    COLUMN_SELECT_ALL_CHECKBOX = "input[type='checkbox'][wire\\:click='selectAllColumns']"
    SELECTABLE_COLUMNS = {
        "action": "Action",
        "name": "Name",
        "category": "Category",
        "type": "Type",
        "waba-number": "WABA Number",
        "department": "Department",
        "user": "User",
        "status": "Status",
        "quality": "Quality",
        "created-at": "Created at",
    }
    DEFAULT_SELECTED_COLUMNS = ["action", "name", "category", "type", "waba-number",
                                "status", "quality", "created-at"]

    # ── Table ────────────────────────────────────────────────────────────────
    TABLE = f"#table-{TABLE_NAME}"
    TABLE_HEADERS = f"#table-{TABLE_NAME} thead th"
    TABLE_ROWS = f"#table-{TABLE_NAME} tbody tr"
    NO_RECORDS_MSG = (
        "xpath=//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no items found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no record') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no data') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no result') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'not found')]"
    )

    # CONFIRMED sortBy(...) targets (module docstring #6) -- key is the
    # checklist-facing column name, value is the exact sortBy() argument.
    SORT_KEYS = {
        "name": "name",
        "category": "category",
        "type": "type",
        "waba_number": "senderId.number",
        "status": "status",
        "quality": "quality",
        "created_at": "created_at",
    }
    # wire:click.prevent, not wire:click -- see module docstring point 6
    # above (this file's own confirmed DOM: 'button (wire:click.prevent=
    # "clearSorts")'), and the identical, correctly-written locator on the
    # two sibling pages with this same pattern: whatsapp_campaign_page.py's
    # and whatsapp_campaign_report_page.py's CLEAR_ALL_SORTS_BTN both use
    # name()='wire:click.prevent'. XPath's name()='wire:click' only matches
    # an attribute named EXACTLY that string -- it does not match
    # 'wire:click.prevent', a different attribute name -- so this locator
    # could never match anything, confirmed by a real run timing out with
    # zero matches in clear_all_sorts() after a sort pill was already
    # confirmed present (test_TC013_sorting_created_at_column).
    CLEAR_ALL_SORTS_BTN = "xpath=//button[contains(@*[name()='wire:click.prevent'],'clearSorts')]"

    # ── Delete confirmation dialog (WireUI confirmAction -> SweetAlert2) ────
    # SAME generic locators already confirmed on whatsapp_optout_page.py.
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

    # ── Pagination (standard rappasoft/Laravel markup) ──────────────────────
    PAGINATION_NAV = "nav[aria-label='Pagination Navigation']"
    PAGINATION_NEXT_BTN = f"nav[aria-label='Pagination Navigation'] button[wire\\:click=\"nextPage('{TABLE_NAME}Page')\"]"
    PAGINATION_PREV_DISABLED = "nav[aria-label='Pagination Navigation'] span[aria-disabled='true']"
    PAGINATION_CURRENT_PAGE = "nav[aria-label='Pagination Navigation'] span[aria-current='page']"

    # ── Template Preview panel (whatsapp.template.view component) ──────────
    # CONFIRMED content, duplicated verbatim from the same source capture
    # already used once on pages/whatsapp/whatsapp_campaign_create_page.py
    # (see module docstring #11 -- no shared base per this project's
    # flat-file convention for pages/whatsapp/).
    MODAL_CONTAINER = "#modal-container"
    TEMPLATE_PREVIEW_HEADER = "xpath=//h1[normalize-space()='Preview']"
    TEMPLATE_PREVIEW_CLOSE_BTN = "button[wire\\:click=\"$dispatch('closeModal')\"]"
    TEMPLATE_PREVIEW_ID_TEXT = "xpath=//p[contains(.,'Template ID:')]"
    TEMPLATE_PREVIEW_BODY_TEXT = "xpath=//div[contains(@class,'break-words')]//p[contains(@class,'text-left')]"

    # ══════════════════════════════════════════════════════════════════════
    # Navigation / page state
    # ══════════════════════════════════════════════════════════════════════

    def navigate(self):
        self.open(self.PATH)
        self.page.wait_for_timeout(2000)
        return self

    def is_template_list_page(self):
        url = self.get_current_url().lower()
        return ("/whatsapp/channels/template" in url and "login" not in url
                and "/edit" not in url)

    def wait_for_table_load(self, timeout=15000):
        self.page.locator(self.TABLE).wait_for(state="attached", timeout=timeout)
        self.page.wait_for_timeout(1000)

    def get_page_header_text(self):
        return self.h.wait_for_element_visible(self.PAGE_HEADER).inner_text().strip()

    def get_breadcrumb_text(self):
        return self.h.wait_for_element_visible(self.BREADCRUMB_ACTIVE).inner_text().strip()

    def _is_visible(self, locator, timeout=1000):
        try:
            loc = self.page.locator(locator)
            for i in range(loc.count()):
                if loc.nth(i).is_visible():
                    return True
            return False
        except Exception:
            return False

    @staticmethod
    def _dispatch_input(el, value):
        el.evaluate(
            "(elm, v) => { elm.value = v; "
            "elm.dispatchEvent(new Event('input', {bubbles: true})); "
            "elm.dispatchEvent(new Event('change', {bubbles: true})); }",
            value
        )

    # ══════════════════════════════════════════════════════════════════════
    # Search
    # ══════════════════════════════════════════════════════════════════════

    def search(self, value):
        box = self.h.wait_for_element_visible(self.SEARCH_INPUT)
        self._dispatch_input(box, value)
        self.page.wait_for_timeout(1500)

    def clear_search(self):
        box = self.h.wait_for_element_visible(self.SEARCH_INPUT)
        self._dispatch_input(box, "")
        self.page.wait_for_timeout(1000)

    # ══════════════════════════════════════════════════════════════════════
    # Filters
    # ══════════════════════════════════════════════════════════════════════

    def open_filters_panel(self):
        if self._is_visible(self.FILTER_TYPE, timeout=1000):
            return
        self._js_click(self.FILTERS_TOGGLE_BTN, timeout=10000)
        self.page.wait_for_timeout(500)

    def set_department_filter(self, value):
        self.open_filters_panel()
        el = self.h.wait_for_element_visible(self.FILTER_DEPARTMENT)
        self._dispatch_input(el, value)
        self.page.wait_for_timeout(1200)

    def set_user_filter(self, value):
        self.open_filters_panel()
        el = self.h.wait_for_element_visible(self.FILTER_USER)
        self._dispatch_input(el, value)
        self.page.wait_for_timeout(1200)

    def select_type_filter(self, value):
        """value is one of TYPE_OPTIONS' keys (empty string = 'All')."""
        self.open_filters_panel()
        self.h.select_option(self.FILTER_TYPE, value=value)
        self.page.wait_for_timeout(1200)

    def select_status_filter(self, value):
        """value is one of STATUS_OPTIONS' keys (empty string = 'All')."""
        self.open_filters_panel()
        self.h.select_option(self.FILTER_STATUS, value=value)
        self.page.wait_for_timeout(1200)

    def set_date_filter(self, from_date, to_date):
        self.open_filters_panel()
        from_el = self.h.wait_for_element_visible(self.FILTER_CREATED_FROM)
        self._dispatch_input(from_el, str(from_date))
        self.page.wait_for_timeout(600)
        to_el = self.h.wait_for_element_visible(self.FILTER_CREATED_TO)
        self._dispatch_input(to_el, str(to_date))
        self.page.wait_for_timeout(1500)

    def get_filter_values(self):
        # input_value(), not get_attribute("value") -- these fields are set
        # via _dispatch_input()'s elm.value = ... (a live DOM PROPERTY
        # assignment), which never touches the static HTML value attribute.
        # Same bug class confirmed broken (and fixed) on the WhatsApp
        # Message/Campaign Report pages' get_filter_date_values() and the
        # WhatsApp Opt-out page's get_filter_values() -- this was almost
        # certainly why an earlier get_filter_values() call for
        # test_TC005_invalid_date_filter never returned a usable
        # created_from/created_to reading.
        self.open_filters_panel()
        dept = self.h.wait_for_element_visible(self.FILTER_DEPARTMENT).input_value()
        user = self.h.wait_for_element_visible(self.FILTER_USER).input_value()
        from_v = self.h.wait_for_element_visible(self.FILTER_CREATED_FROM).input_value()
        to_v = self.h.wait_for_element_visible(self.FILTER_CREATED_TO).input_value()
        return {"department": dept, "user": user, "created_from": from_v, "created_to": to_v}

    def clear_all_filters(self):
        """No dedicated 'Clear Filters' button was confirmed in the supplied
        DOM dump -- resets the confirmed text/date filter inputs directly
        (same approach as whatsapp_optout_page.py's clear_all_filters) and
        resets both selects back to 'All' via select_option."""
        self.open_filters_panel()
        for locator in (self.FILTER_DEPARTMENT, self.FILTER_USER,
                        self.FILTER_CREATED_FROM, self.FILTER_CREATED_TO):
            try:
                el = self.h.wait_for_element_visible(locator)
                self._dispatch_input(el, "")
                self.page.wait_for_timeout(400)
            except Exception:
                pass
        try:
            self.h.select_option(self.FILTER_TYPE, value="")
            self.h.select_option(self.FILTER_STATUS, value="")
        except Exception:
            pass
        self.page.wait_for_timeout(1000)

    # ══════════════════════════════════════════════════════════════════════
    # Bulk Action / Export
    # ══════════════════════════════════════════════════════════════════════

    def click_export_button(self):
        self._js_click(self.EXPORT_BTN, timeout=10000)
        self.page.wait_for_timeout(500)

    def is_export_modal_open(self):
        return self.is_element_visible(self.EXPORT_MODAL_HEADER, timeout=5000)

    def get_export_confirm_text(self):
        return self.h.wait_for_element_visible(self.EXPORT_CONFIRM_TEXT).inner_text().strip()

    def confirm_export(self):
        self._js_click(self.EXPORT_YES_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def cancel_export(self):
        self._js_click(self.EXPORT_NO_BTN, timeout=10000)
        self.page.wait_for_timeout(500)

    # ══════════════════════════════════════════════════════════════════════
    # Columns dropdown
    # ══════════════════════════════════════════════════════════════════════

    def open_columns_dropdown(self):
        if self._is_visible(self.COLUMN_SELECT_ALL_CHECKBOX, timeout=1000):
            return
        self._js_click(self.COLUMNS_TOGGLE_BTN, timeout=10000)
        self.page.wait_for_timeout(500)

    def toggle_column(self, value):
        """value: one of SELECTABLE_COLUMNS' keys, e.g. 'department'."""
        self.open_columns_dropdown()
        cb = self.h.wait_for_element_visible(f"input[type='checkbox'][value='{value}']")
        cb.scroll_into_view_if_needed()
        cb.click(force=True)
        self.page.wait_for_timeout(800)

    def is_column_checked(self, value):
        self.open_columns_dropdown()
        try:
            cb = self.page.locator(f"input[type='checkbox'][value='{value}']").first
            return cb.is_checked()
        except Exception:
            return None

    def restore_default_columns(self):
        """Restores the CONFIRMED default column state (module docstring
        #5): every SELECTABLE_COLUMNS key checked EXCEPT 'department' and
        'user'."""
        for value in self.SELECTABLE_COLUMNS:
            should_be_checked = value in self.DEFAULT_SELECTED_COLUMNS
            self.open_columns_dropdown()
            try:
                cb = self.page.locator(f"input[type='checkbox'][value='{value}']").first
                if cb.count() == 0:
                    continue
                if cb.is_checked() != should_be_checked:
                    cb.scroll_into_view_if_needed()
                    cb.click(force=True)
                    self.page.wait_for_timeout(500)
            except Exception:
                continue

    # ══════════════════════════════════════════════════════════════════════
    # Table / rows
    # ══════════════════════════════════════════════════════════════════════

    def get_visible_column_headers(self):
        return self._get_headers_safe(self.TABLE_HEADERS)

    @staticmethod
    def _is_empty_state_row(tds):
        return tds.count() == 1 and tds.nth(0).get_attribute("colspan")

    def get_row_count(self):
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            count = 0
            for i in range(rows.count()):
                row = rows.nth(i)
                tds = row.locator("td")
                if tds.count() == 0:
                    continue
                if self._is_empty_state_row(tds):
                    continue
                if any(t.strip() for t in tds.all_inner_texts()):
                    count += 1
            return count
        except Exception:
            return 0

    def has_records(self):
        return self.is_element_present(self.TABLE_ROWS, timeout=5000) and self.get_row_count() > 0

    def has_no_records_message(self):
        if self.is_element_present(self.NO_RECORDS_MSG, timeout=3000):
            return True
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            if rows.count() == 1 and self._is_empty_state_row(rows.nth(0).locator("td")):
                return True
        except Exception:
            pass
        return self.get_row_count() == 0

    def get_first_data_row(self):
        return self._first_visible_data_row(self.TABLE_ROWS)

    def sort_by(self, column_key):
        """column_key: one of SORT_KEYS' keys, e.g. 'created_at' or
        'waba_number'."""
        sort_arg = self.SORT_KEYS[column_key]
        locator = f"xpath=//button[contains(@*[name()='wire:click'],\"sortBy('{sort_arg}')\")]"
        self._js_click(locator, timeout=10000)
        self.page.wait_for_timeout(1500)

    def get_applied_sort_pill_text(self):
        locator = f"xpath=//span[contains(@*[name()='wire:key'],'{self.TABLE_NAME}-sorting-pill-')]"
        if self.is_element_present(locator, timeout=3000):
            return self.h.wait_for_element_visible(locator).inner_text().strip()
        return None

    def clear_all_sorts(self):
        self._js_click(self.CLEAR_ALL_SORTS_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    # ══════════════════════════════════════════════════════════════════════
    # Row actions — View / Template Preview (module docstring #7, #8)
    # ══════════════════════════════════════════════════════════════════════

    def click_view_on_first_row(self):
        row = self.get_first_data_row()
        if row is None:
            return False
        btn = row.locator("button[data-tooltip-target^='tooltip-view-']")
        if btn.count() == 0:
            return False
        btn.first.scroll_into_view_if_needed()
        btn.first.click(force=True)
        self.page.wait_for_timeout(1000)
        return True

    # Alias — TC010 ("Template Preview button") is the SAME control as
    # TC008 ("View button"); see module docstring #8.
    click_template_preview_on_first_row = click_view_on_first_row

    def is_template_preview_open(self):
        return self.is_element_visible(self.TEMPLATE_PREVIEW_HEADER, timeout=5000)

    def get_template_preview_id_text(self):
        return self.page.locator(self.TEMPLATE_PREVIEW_ID_TEXT).first.inner_text().strip()

    def get_template_preview_body_text(self):
        return self.page.locator(self.TEMPLATE_PREVIEW_BODY_TEXT).first.inner_text().strip()

    def close_template_preview(self):
        try:
            self.page.locator(self.TEMPLATE_PREVIEW_CLOSE_BTN).first.click()
        except Exception:
            self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(500)

    # ══════════════════════════════════════════════════════════════════════
    # Row actions — Delete (module docstring #7, #14: cancel-only)
    # ══════════════════════════════════════════════════════════════════════

    def click_delete_on_first_row(self):
        row = self.get_first_data_row()
        if row is None:
            return False
        btn = row.locator("button[data-tooltip-target^='tooltip-delete-']")
        if btn.count() == 0:
            return False
        btn.first.scroll_into_view_if_needed()
        btn.first.click(force=True)
        self.page.wait_for_timeout(1000)
        return True

    def is_delete_confirm_dialog_open(self, timeout=8000):
        try:
            self.page.locator(self.CONFIRM_DELETE_BTN).first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def cancel_delete(self):
        try:
            btn = self.page.locator(self.CANCEL_DELETE_BTN).first
            btn.wait_for(state="visible", timeout=10000)
        except Exception:
            return False
        btn.click()
        self.page.wait_for_timeout(1000)
        return True

    def confirm_delete(self):
        """Exposed for a future scratch-data-capable suite -- intentionally
        NOT called by the paired test file (module docstring #14)."""
        btn = self.h.wait_for_element_clickable(self.CONFIRM_DELETE_BTN, timeout=10000)
        btn.click(force=True)
        self.page.wait_for_timeout(2000)

    # ══════════════════════════════════════════════════════════════════════
    # Row actions — Update Status (module docstring #7, #9)
    # ══════════════════════════════════════════════════════════════════════

    def click_update_status_on_first_row(self):
        row = self.get_first_data_row()
        if row is None:
            return False
        btn = row.locator("button[data-tooltip-target^='tooltip-update-status-']")
        if btn.count() == 0:
            return False
        btn.first.scroll_into_view_if_needed()
        btn.first.click(force=True)
        self.page.wait_for_timeout(500)
        return True

    def is_update_status_first_row_present(self):
        row = self.get_first_data_row()
        if row is None:
            return False
        return row.locator("button[data-tooltip-target^='tooltip-update-status-']").count() > 0

    # ══════════════════════════════════════════════════════════════════════
    # Pagination
    # ══════════════════════════════════════════════════════════════════════

    def is_previous_page_disabled(self):
        return self.is_element_present(self.PAGINATION_PREV_DISABLED, timeout=3000)

    def is_next_page_enabled(self):
        return self.is_element_present(self.PAGINATION_NEXT_BTN, timeout=3000)

    def get_current_page_number(self):
        try:
            return self.page.locator(self.PAGINATION_CURRENT_PAGE).first.inner_text().strip()
        except Exception:
            return None

    def click_next_page(self):
        self._js_click(self.PAGINATION_NEXT_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def go_to_page(self, page_number):
        locator = f"xpath=//nav[@aria-label='Pagination Navigation']//button[contains(@*[name()='wire:click'],\"gotoPage({page_number}, '{self.TABLE_NAME}Page')\")]"
        self._js_click(locator, timeout=10000)
        self.page.wait_for_timeout(1500)
