from pages.common.base_page import BasePage


class WhatsappOptInPage(BasePage):
    """
    WhatsApp OptIn Numbers — page object.

    Grounded in a full live DOM capture of
    https://.../whatsapp/campaigns/opt-in (reached via the top nav's
    "More" dropdown -> "Opt-in", confirmed nav link
    `href=".../whatsapp/campaigns/opt-in"`, icon mdi-account-check). This
    page is the near-mirror of the already-automated WhatsApp Opt-out
    Numbers page (pages/whatsapp/whatsapp_optout_page.py) — same
    livewire-tables scaffolding, same filter/sort/column/bulk-action/
    delete-confirm mechanisms — with the direction reversed (opt-IN vs
    opt-OUT) and one extra top action (Export) that Opt-out does not
    have.

    Confirmed facts driving every locator below:

    1. Livewire component: memo.name = "whatsapp.campaign.opt-in-table",
       memo.path = "whatsapp/campaigns/opt-in". tableName =
       "whatsapp_opt_in_numbers" (confirmed via wire:snapshot's
       data.tableName and every id/wire:key on the page, e.g.
       `<table id="table-whatsapp_opt_in_numbers">`,
       `x-init="setTableId('table-whatsapp_opt_in_numbers')"`).
    2. Header: `<h1 class="text-md font-semibold whitespace-nowrap">WhatsApp OptIn Numbers</h1>`
       (confirmed exact text — "OptIn" as one capitalized word, no space).
       Breadcrumb: Home > Channels > "Opt-in Numbers" (plain `<span>`,
       standard breadcrumb convention for this app — note the breadcrumb
       DOES use a hyphen and a space ("Opt-in Numbers"), unlike the h1's
       "OptIn").
    3. THREE top action controls (confirmed, one MORE than Opt-out's two):
         - "Export": plain
           `<button onclick="Livewire.dispatch('exportOptInNumbers')" title="Export OptIn Numbers">`
           — a direct dispatch with NO confirm dialog observed (unlike
           Sender ID's "Export to XLSX" which opens an Alpine confirm
           dialog first). No feedback/toast markup was ever captured for
           this action being fired (button was never clicked during
           capture) — documented gap; this page object exposes only a
           safe click that verifies the page remains stable afterward,
           not any specific success message.
         - "Upload OptIn Numbers": plain
           `<button onclick="Livewire.dispatch('openModal', {component: 'whatsapp.campaign.optin.fetch'})" title="Upload OptIn Numbers from Excel/CSV file">`
           — opens the shared app-wide livewire-ui-modal (`id="modal-container"`,
           `x-data="LivewireUIModal()"`, confirmed again here, path
           "whatsapp/campaigns/opt-in"). The modal's internal content
           (upload dropzone, submit) was NEVER captured (showActiveComponent
           was empty since the button was never clicked) — documented gap,
           same treatment as every other uncaptured modal this session.
         - "Add New OptIn Number": a REAL navigable link,
           `<a href=".../whatsapp/campaigns/opt-in/create">` — NOT a
           modal trigger, same pattern as Opt-out's "Add New OptOut
           Number". Only reachability is confirmed; the create page's own
           form DOM was never supplied.
    4. Search: `<input wire:model.live="search" placeholder="Search by phone number or sender..." type="text" autocomplete="off">`
       — CONFIRMED plain `wire:model.live` with NO debounce modifier
       (unlike this page's own filter inputs below, which DO use
       `.debounce.500ms` / are plain `wire:model.live` for the date
       fields).
    5. Filters: CONFIRMED "slide-down" layout (`filterLayout:
       "slide-down"`, `filterSlideDownDefaultVisible: false`, toggled via
       `x-on:click="filtersOpen = !filtersOpen"` on the "Filters" button)
       — matching Opt-out/Sender ID's mechanism, NOT Flows' "popover".
       Three confirmed filter fields (filterCount: 3):
         - Sender: plain text input,
           `id="whatsapp_opt_in_numbers-filter-sender"`,
           `wire:model.live.debounce.500ms="filterComponents.sender"`,
           placeholder "Search by sender name or number...".
         - Opted In From: plain `type="date"` input,
           `id="whatsapp_opt_in_numbers-filter-opted_in_from"`,
           `wire:model.live="filterComponents.opted_in_from"` (no debounce).
         - Opted In To: same pattern,
           `id="whatsapp_opt_in_numbers-filter-opted_in_to"`.
       No "Clear Filters" button was found in the supplied DOM (confirmed
       absence, matching Opt-out's identical documented gap) — this page
       object resets the three fields directly via JS instead of guessing
       a hidden button locator (same approach as
       whatsapp_optout_page.py's clear_all_filters()).
    6. Table: `<table id="table-whatsapp_opt_in_numbers">`. FOUR real,
       confirmed selectable columns (selectableColumns in wire:snapshot):
       Action, Phone Number, Sender, Opted In At. ALL FOUR are selected
       by default (deselectedColumns is empty) — same "all columns on by
       default" state as Opt-out, unlike Sender ID/Flows which each have
       one column off by default.
    7. Sorting: 3 of the 4 columns are sortable, each via a real,
       confirmed `wire:click="sortBy(...)"` button:
         - Phone Number -> `sortBy('phone_number')`
         - Sender       -> `sortBy('sender_id')`
         - Opted In At  -> `sortBy('opted_in_at')`
       Action is a plain `<span>` header with no sortBy button. Default
       sort is `opted_in_at desc`, with a real rendered sorting pill
       genuinely captured: `wire:key="whatsapp_opt_in_numbers-sorting-pill-opted_in_at"`,
       text "Opted In At: Z-A", per-pill clear
       `wire:click="clearSort('opted_in_at')"` (no `.prevent`), clear-all
       `wire:click.prevent="clearSorts"` (WITH `.prevent`) — same
       conventions confirmed on every other WhatsApp page this session.
    8. Bulk Actions ARE real here (CONFIRMED `bulkActionsStatus: true`,
       unlike Flows which has none): a "Bulk Actions" dropdown button
       (`id="whatsapp_opt_in_numbers-bulkActionsDropdown"`) containing one
       action, "Bulk Delete"
       (`wire:click="bulkDelete"`,
       `wire:key="whatsapp_opt_in_numbers-bulk-action-bulkDelete"`), plus
       a header "select all" checkbox and one row checkbox per row
       (`wire:key="whatsapp_opt_in_numbersselectedItems-{id}"`,
       `@change="$wire.toggleBulkSelectionRow(...)"`). "Bulk Delete" is
       DESTRUCTIVE (deletes every selected opt-in record) — this page
       object exposes only presence checks for the dropdown/button and
       the row checkboxes, deliberately NOT a method that clicks
       "Bulk Delete" through, consistent with this project's caution
       around irreversible actions against real QA data.
    9. Row delete action: a WireUI CONFIRM-ACTION mechanism, confirmed
       identical structure to whatsapp_optout_page.py's row delete AND
       to whatsapp_flows_page.py's "Deprecate" button —
       `x-on:click="$wireui.confirmAction({title: 'Are you sure to
       delete this item ?', icon: 'warning', method: 'deleteOptIn',
       params: [{id}], accept: {style:'solid', color:'red'}},
       '{wireId}')"`, tooltip via
       `data-tooltip-target="tooltip-delete-{id}"`. This app's own
       `<style>` block (confirmed present in the captured `<head>`,
       `--swal2-*` custom properties and `.swal2-*` rules) confirms
       $wireui.confirmAction renders a SweetAlert2 dialog — matching the
       EXACT same confirmed mechanism already automated non-destructively
       on whatsapp_optout_page.py (open the dialog, read its title via
       the standard SweetAlert2 `.swal2-title`/`.swal2-html-container`
       classes, then click `.swal2-cancel` — never `.swal2-confirm`).
       This page object follows that same established, already-verified
       pattern: real coverage of the confirm-dialog flow WITHOUT ever
       performing the destructive delete itself.
    10. Pagination: CONFIRMED `.total-pagination-results` class (single-
        count format "Showing 5 results" — only 5 opt-in numbers existed
        at capture time, so no page-number controls were rendered) —
        matching Opt-out/Sender ID/Blocked Users' convention, NOT the
        richer `.paged-pagination-results` format used by Flows/Incoming
        Messages.
    11. Row data confirmed: Phone Number is masked (e.g. "91992*****87"),
        Sender renders as "{name} ({number})" (e.g. "Globe Teleservices
        Pte. Ltd. (919202511257)"), Opted In At renders as
        "DD-MM-YYYY HH:MM:SS" (e.g. "27-08-2026 15:43:46").

    No manual QA checklist (TC numbers) was supplied for this page — only
    the raw DOM dump — so the paired test file uses descriptive test
    names rather than TCxxx numbering.
    """

    REPORT_URL = "/whatsapp/campaigns/opt-in"
    CREATE_URL = "/whatsapp/campaigns/opt-in/create"
    TABLE_NAME = "whatsapp_opt_in_numbers"

    # Confirmed column order for the DEFAULT (all-selected) column state,
    # including the leading bulk-selection checkbox column.
    COLUMN_INDEX = {
        "bulk_checkbox": 0, "action": 1, "phone_number": 2,
        "sender": 3, "opted_in_at": 4,
    }

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'WhatsApp OptIn Numbers')]"
    BREADCRUMB = "xpath=//nav[@aria-label='Breadcrumb']"
    MODAL_CONTAINER = "#modal-container"

    # ── Top action controls (confirmed THREE distinct mechanisms) ───────────
    EXPORT_BTN = "xpath=//button[@title='Export OptIn Numbers']"
    UPLOAD_BTN = "xpath=//button[@title='Upload OptIn Numbers from Excel/CSV file']"
    ADD_NEW_BTN = (
        "xpath=//a[contains(@href,'/whatsapp/campaigns/opt-in/create') and "
        "contains(normalize-space(.),'Add New OptIn Number')]"
    )

    # ── Search (confirmed NO debounce modifier, unlike the filter inputs) ───
    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search by phone number or sender...']"

    # ── Filters (slide-down layout, three confirmed fields) ─────────────────
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')]"
    FILTER_SENDER = "#whatsapp_opt_in_numbers-filter-sender"
    FILTER_OPTED_IN_FROM = "#whatsapp_opt_in_numbers-filter-opted_in_from"
    FILTER_OPTED_IN_TO = "#whatsapp_opt_in_numbers-filter-opted_in_to"

    # ── Bulk Actions (confirmed REAL, unlike Flows) ─────────────────────────
    BULK_ACTIONS_BUTTON = "#whatsapp_opt_in_numbers-bulkActionsDropdown"
    BULK_ACTION_DELETE = (
        "xpath=//button[@*[name()='wire:click']='bulkDelete' and "
        "contains(@*[name()='wire:key'],'bulk-action-bulkDelete')]"
    )
    ROW_CHECKBOX = "input[type='checkbox'][wire\\:key^='whatsapp_opt_in_numbersselectedItems-']"

    # ── Sorting (Phone Number / Sender / Opted In At — Action not sortable) ─
    SORT_PHONE_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('phone_number')\")]"
    SORT_SENDER_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('sender_id')\")]"
    SORT_OPTED_IN_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('opted_in_at')\")]"
    CLEAR_ALL_SORTS_BTN = "xpath=//button[contains(@*[name()='wire:click.prevent'],'clearSorts')]"
    APPLIED_SORT_PILL = f"xpath=//span[contains(@*[name()='wire:key'],'{TABLE_NAME}-sorting-pill-')]"

    # ── Columns dropdown (4 selectable, ALL selected by default) ────────────
    COLUMNS_BUTTON = "xpath=//button[contains(normalize-space(.),'Columns')]"
    ALL_COLUMN_VALUES = ["action", "phone-number", "sender", "opted-in-at"]
    DEFAULT_SELECTED_COLUMNS = ["action", "phone-number", "sender", "opted-in-at"]
    DEFAULT_DESELECTED_COLUMNS = []

    # ── Table ────────────────────────────────────────────────────────────────
    TABLE = f"#table-{TABLE_NAME}"
    TABLE_HEADERS = f"{TABLE} thead th"
    TABLE_ROWS = f"{TABLE} tbody tr"
    # No empty-state text was captured directly on this page (5 real rows
    # present at capture time) — this is the SAME generic, already-confirmed
    # pattern reused verbatim from whatsapp_optout_page.py (an identical
    # pattern found elsewhere in this codebase), not a fresh guess.
    NO_RECORDS_MSG = (
        "xpath=//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no items found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no record') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no data') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no result') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'not found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'nothing found')]"
    )

    # ── Delete (row) — $wireui.confirmAction -> SweetAlert2, confirmed both
    # in THIS page's own captured DOM (the x-on:click handler's literal
    # source text) and via the identical, already-automated mechanism on
    # whatsapp_optout_page.py. ─────────────────────────────────────────────
    DELETE_ICON_IN_ROW = "xpath=.//*[contains(@data-tooltip-target,'tooltip-delete-')]"
    DELETE_CONFIRM_TITLE = ".swal2-title"
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

    # ── Pagination ───────────────────────────────────────────────────────────
    PAGINATION_RESULTS_TEXT = ".total-pagination-results"

    # ── Navigation / page state ──────────────────────────────────────────────

    def navigate(self):
        self.open(self.REPORT_URL)
        self.page.wait_for_timeout(2000)
        return self

    navigate_to_report = navigate

    def is_optin_page(self):
        url = self.get_current_url()
        return "/whatsapp/campaigns/opt-in" in url and "login" not in url.lower()

    def get_page_title_text(self):
        el = self.h.wait_for_element_visible(self.PAGE_TITLE)
        return el.inner_text().strip()

    def wait_for_table_load(self, timeout=15000):
        self.page.locator(self.TABLE).wait_for(state="attached", timeout=timeout)
        self.page.wait_for_timeout(1000)

    def _is_visible(self, locator, timeout=1000):
        try:
            loc = self.page.locator(locator)
            for i in range(loc.count()):
                if loc.nth(i).is_visible():
                    return True
            return False
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # Top action controls
    # -------------------------------------------------------------------------

    def is_export_button_present(self):
        return self.is_element_present(self.EXPORT_BTN, timeout=5000)

    def click_export(self):
        """Fires the confirmed direct dispatch('exportOptInNumbers'). No
        confirm dialog or success-toast markup was ever captured for this
        action (see module docstring caveat), so this only performs the
        click — callers should assert the page remains stable, not any
        specific feedback text."""
        self._js_click(self.EXPORT_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def click_add_new_optin_number(self):
        self._js_click(self.ADD_NEW_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def click_upload_optin_numbers(self):
        self._js_click(self.UPLOAD_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_upload_popup_open(self):
        return (self.is_element_present("#dropzone-file", timeout=8000)
                or self.is_element_present(self.MODAL_CONTAINER, timeout=3000))

    def is_create_page(self):
        return "/whatsapp/campaigns/opt-in/create" in self.get_current_url()

    # -------------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------------

    def _wait_for_search_to_settle(self, timeout_ms=8000):
        end_time = self.page.evaluate("() => Date.now()") + timeout_ms
        last_state = None
        while self.page.evaluate("() => Date.now()") < end_time:
            current = self.get_row_count()
            no_msg = self.is_element_present(self.NO_RECORDS_MSG, timeout=500)
            state = (current, no_msg)
            if state == last_state:
                return
            last_state = state
            self.page.wait_for_timeout(600)

    def search(self, value):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.evaluate(
            "(el, v) => { el.value = v; "
            "el.dispatchEvent(new Event('input', {bubbles: true})); "
            "el.dispatchEvent(new Event('change', {bubbles: true})); }",
            value
        )
        self.page.wait_for_timeout(500)
        self._wait_for_search_to_settle()
        self.page.wait_for_timeout(300)

    def clear_search(self):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.evaluate(
            "(el) => { el.value = ''; "
            "el.dispatchEvent(new Event('input', {bubbles: true})); "
            "el.dispatchEvent(new Event('change', {bubbles: true})); }"
        )
        self.page.wait_for_timeout(500)
        self._wait_for_search_to_settle()
        self.page.wait_for_timeout(300)

    # -------------------------------------------------------------------------
    # Table / rows
    # -------------------------------------------------------------------------

    def has_records(self):
        return self.is_element_present(self.TABLE_ROWS, timeout=5000) and self.get_row_count() > 0

    @staticmethod
    def _is_empty_state_row(tds):
        return tds.count() == 1 and tds.nth(0).get_attribute("colspan")

    def has_no_records_message(self):
        if self.is_element_present(self.NO_RECORDS_MSG, timeout=3000):
            return True
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            if rows.count() == 1:
                tds = rows.nth(0).locator("td")
                if self._is_empty_state_row(tds):
                    return True
        except Exception:
            pass
        return self.get_row_count() == 0

    def get_row_count(self):
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            count = 0
            for i in range(rows.count()):
                row = rows.nth(i)
                tds = row.locator("td")
                n = tds.count()
                if n == 0:
                    continue
                if self._is_empty_state_row(tds):
                    continue
                if any(t.strip() for t in tds.all_inner_texts()):
                    count += 1
            return count
        except Exception:
            return 0

    def get_visible_column_headers(self):
        return self._get_headers_safe(self.TABLE_HEADERS)

    def get_column_values(self, column_name):
        idx = self.COLUMN_INDEX.get(column_name)
        if idx is None:
            return []
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            values = []
            for i in range(rows.count()):
                tds = rows.nth(i).locator("td")
                if tds.count() > idx:
                    values.append(tds.nth(idx).inner_text().strip())
            return values
        except Exception:
            return []

    def get_first_data_row(self):
        return self._first_visible_data_row(f"{self.TABLE} tbody tr")

    # -------------------------------------------------------------------------
    # Sorting
    # -------------------------------------------------------------------------

    def sort_by_phone_number(self):
        self._js_click(self.SORT_PHONE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_sender(self):
        self._js_click(self.SORT_SENDER_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_opted_in_at(self):
        self._js_click(self.SORT_OPTED_IN_AT_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def get_applied_sort_pill_text(self):
        if self.is_element_present(self.APPLIED_SORT_PILL, timeout=3000):
            return self.h.wait_for_element_visible(self.APPLIED_SORT_PILL).inner_text().strip()
        return None

    def clear_all_sorts(self):
        self._js_click(self.CLEAR_ALL_SORTS_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    # -------------------------------------------------------------------------
    # Filters (slide-down)
    # -------------------------------------------------------------------------

    def open_filters_panel(self):
        if self._is_visible(self.FILTER_SENDER, timeout=1000):
            return
        self._js_click(self.FILTERS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def set_sender_filter(self, value):
        self.open_filters_panel()
        el = self.h.wait_for_element_visible(self.FILTER_SENDER)
        el.evaluate(
            "(elm, v) => { elm.value = v; "
            "elm.dispatchEvent(new Event('input', {bubbles: true})); "
            "elm.dispatchEvent(new Event('change', {bubbles: true})); }",
            value
        )
        self.page.wait_for_timeout(1200)

    def set_date_filter(self, from_date, to_date):
        self.open_filters_panel()
        from_el = self.h.wait_for_element_visible(self.FILTER_OPTED_IN_FROM)
        from_el.evaluate(
            "(elm, v) => { elm.value = v; "
            "elm.dispatchEvent(new Event('input', {bubbles: true})); "
            "elm.dispatchEvent(new Event('change', {bubbles: true})); }",
            from_date
        )
        self.page.wait_for_timeout(600)
        to_el = self.h.wait_for_element_visible(self.FILTER_OPTED_IN_TO)
        to_el.evaluate(
            "(elm, v) => { elm.value = v; "
            "elm.dispatchEvent(new Event('input', {bubbles: true})); "
            "elm.dispatchEvent(new Event('change', {bubbles: true})); }",
            to_date
        )
        self.page.wait_for_timeout(1500)

    def get_filter_values(self):
        self.open_filters_panel()
        sender_el = self.h.wait_for_element_visible(self.FILTER_SENDER)
        from_el = self.h.wait_for_element_visible(self.FILTER_OPTED_IN_FROM)
        to_el = self.h.wait_for_element_visible(self.FILTER_OPTED_IN_TO)
        return (sender_el.get_attribute("value"), from_el.get_attribute("value"),
                to_el.get_attribute("value"))

    def clear_all_filters(self):
        """No dedicated 'Clear Filters' button was confirmed in the
        supplied DOM dump (same documented absence as Opt-out) — resets
        all three confirmed filter inputs directly via JS instead of
        guessing a hidden button locator."""
        self.open_filters_panel()
        for locator in (self.FILTER_SENDER, self.FILTER_OPTED_IN_FROM, self.FILTER_OPTED_IN_TO):
            try:
                el = self.h.wait_for_element_visible(locator)
                el.evaluate(
                    "(elm) => { elm.value = ''; "
                    "elm.dispatchEvent(new Event('input', {bubbles: true})); "
                    "elm.dispatchEvent(new Event('change', {bubbles: true})); }"
                )
                self.page.wait_for_timeout(500)
            except Exception:
                pass
        self.page.wait_for_timeout(1000)

    # -------------------------------------------------------------------------
    # Bulk Actions (presence-only — see module docstring caveat #8)
    # -------------------------------------------------------------------------

    def is_bulk_actions_button_present(self):
        return self.is_element_present(self.BULK_ACTIONS_BUTTON, timeout=5000)

    def open_bulk_actions_dropdown(self):
        self._js_click(self.BULK_ACTIONS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def is_bulk_delete_option_present(self):
        self.open_bulk_actions_dropdown()
        return self.is_element_present(self.BULK_ACTION_DELETE, timeout=5000)

    def select_first_row_checkbox(self):
        cb = self.h.wait_for_element_visible(self.ROW_CHECKBOX)
        cb.scroll_into_view_if_needed()
        cb.click(force=True)
        self.page.wait_for_timeout(500)

    def is_row_checkbox_present(self):
        return self.is_element_present(self.ROW_CHECKBOX, timeout=5000)

    # -------------------------------------------------------------------------
    # Columns dropdown
    # -------------------------------------------------------------------------

    def open_columns_dropdown(self):
        if self._is_visible(f"input[type='checkbox'][value='action']", timeout=1000):
            return
        self._js_click(self.COLUMNS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def toggle_column(self, value):
        """value: one of ALL_COLUMN_VALUES ('action' | 'phone-number' |
        'sender' | 'opted-in-at')."""
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
        """Restores the CONFIRMED default column state: ALL FOUR columns
        (action/phone-number/sender/opted-in-at) checked."""
        for value in self.DEFAULT_SELECTED_COLUMNS:
            self.open_columns_dropdown()
            try:
                cb = self.page.locator(f"input[type='checkbox'][value='{value}']").first
                if cb.count() == 0:
                    continue
            except Exception:
                continue
            if not cb.is_checked():
                cb.scroll_into_view_if_needed()
                cb.click(force=True)
                self.page.wait_for_timeout(500)

    # -------------------------------------------------------------------------
    # Delete (row) — open + read + CANCEL only, never confirm
    # -------------------------------------------------------------------------

    def click_delete_on_first_row(self):
        row = self.get_first_data_row()
        if row is None:
            return False
        try:
            btn = row.locator(self.DELETE_ICON_IN_ROW).first
            if btn.count() == 0:
                return False
        except Exception:
            return False
        btn.scroll_into_view_if_needed()
        btn.click(force=True)
        self.page.wait_for_timeout(1000)
        return True

    def get_delete_confirm_title(self):
        try:
            el = self.page.locator(self.DELETE_CONFIRM_TITLE).first
            el.wait_for(state="visible", timeout=8000)
            return el.inner_text().strip()
        except Exception:
            return ""

    def cancel_delete(self):
        try:
            btn = self.page.locator(self.CANCEL_DELETE_BTN).first
            btn.wait_for(state="visible", timeout=10000)
        except Exception:
            return False
        btn.click()
        self.page.wait_for_timeout(1000)
        return True

    # -------------------------------------------------------------------------
    # Pagination
    # -------------------------------------------------------------------------

    def get_pagination_results_text(self):
        el = self.h.wait_for_element_visible(self.PAGINATION_RESULTS_TEXT)
        return el.inner_text().strip()
