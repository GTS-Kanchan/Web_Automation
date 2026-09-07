from pages.common.base_page import BasePage


class WhatsappSenderIdPage(BasePage):
    """
    WhatsApp Numbers (Sender ID) — page object.

    Grounded in a full live DOM capture of
    https://.../whatsapp/channels/senderid (reached via the WhatsApp
    channel's main "Numbers" tab — NOT the "More" dropdown, unlike
    Incoming Messages / OptOut / Blocked Users). The manual QA checklist
    calls this page "WhatsApp Numbers" / "sender id page" interchangeably;
    the app's own h1 confirms "WhatsApp Numbers" as the real on-page title
    even though the URL segment and Livewire component are both named
    "sender-id". Confirmed facts driving every locator below:

    1. Livewire component: memo.name = "whatsapp.sender-id.table",
       memo.path = "whatsapp/channels/senderid". tableName =
       "wa_sender_ids" (confirmed via wire:snapshot's data.tableName and
       every id/wire:key on the page, e.g.
       `<table id="table-wa_sender_ids">`,
       `x-init="setTableId('table-wa_sender_ids')"`).
    2. Header: `<h1 class="text-md font-semibold whitespace-nowrap">WhatsApp Numbers</h1>`.
       A confirmed bonus "Create New App" link
       (`href=".../whatsapp/channels/meta/create"`) sits beside the
       header — not requested by the checklist, included here only as a
       reachability check (companion "bonus" test), never asserting
       anything about the create-app flow itself (its own page's DOM was
       never captured).
    3. Search: `<input wire:model.live="search" placeholder="Search" type="text" autocomplete="off">`
       — same confirmed CSS-selector pattern used identically elsewhere in
       this session (no id on this page's search box, same as Incoming
       Messages/OptOut/Blocked Users).
    4. Filters panel (slide-down, Alpine `x-on:click="filtersOpen = !filtersOpen"`
       on the "Filters" button — NOT wire:click, a plain client-side
       toggle). Confirmed filterCount: 4 (department, user,
       created_at_from, created_at_to). IMPORTANT correction vs. this
       page's own manual QA wording ("Select date range, Department and
       user"): Department and User are CONFIRMED plain
       `<input type="text" wire:model.live.debounce.500ms="filterComponents.department|user">`
       free-text fields — NOT `<select>` dropdowns like on other pages
       (e.g. WhatsApp Incoming Messages' WABA Number/Type filters). The
       two date fields are plain native
       `<input type="date" wire:model.live="filterComponents.created_at_from|to">`
       with NO paired time-select (unlike Incoming Messages' "Received
       From/To", which pairs each date with a 5-minute-increment
       `<select>`). No "Clear Filters" pill/button exists anywhere in the
       capture for this page (confirmed absence — filters must be reset
       by blanking each field directly; same treatment as Blocked Users'
       confirmed absence of a Filters panel entirely).
    5. Table: `<table id="table-wa_sender_ids">`. 10 real, confirmed
       selectable columns (selectableColumns in wire:snapshot): Action,
       App Name, WABA Number, Department, User, Status, Quality, Message
       Limit, MM Lite APIs, Created At. Only 8 are selected BY DEFAULT
       (selectedColumns) — Department and User are CONFIRMED
       deselected-by-default (columnSelectColumns.deselected /
       defaultdeselected both list exactly
       `{"department":"Department","user":"User"}`) — the first WhatsApp
       page this session with a non-all-selected default column set
       (structurally mirrors the RCS OptOut precedent, but new for
       WhatsApp). Confirmed rendered header/column order for the 8
       default columns (matches COLUMN_INDEX below exactly): Action, App
       Name, WABA Number, Status, Quality, Message Limit, MM Lite APIs,
       Created At.
    6. Sorting: only 4 of the 8 default columns are sortable, each via a
       real, confirmed `wire:click="sortBy(...)"` button — note the
       sortBy() field names do NOT match the column's own slug:
         - App Name    -> `sortBy('name')`
         - WABA Number -> `sortBy('number')`
         - Status      -> `sortBy('status')`
         - Created At  -> `sortBy('created_at')`
       Quality / Message Limit / MM Lite APIs are plain `<span>` headers
       with no sortBy button. Default sort is `created_at desc`
       (wire:snapshot's sorts:{"created_at":"desc"}), and a real rendered
       sorting pill was genuinely captured for it:
       `wire:key="wa_sender_ids-sorting-pill-created_at"`, text
       "Created At: Z-A", with a per-pill clear
       `wire:click="clearSort('created_at')"` (no `.prevent` — confirmed
       directly, same convention as every other WhatsApp page this
       session) and a clear-all `wire:click.prevent="clearSorts"` (WITH
       `.prevent`).
    7. Bulk Actions: NONE exist on this page — wire:snapshot's
       bulkActions is a genuinely empty array, bulkActionConfirms is
       empty, and there is no header/row select-all or per-row checkbox
       anywhere in the table markup (confirmed absence, not a gap). The
       manual QA checklist's TC006 ("Verify Bulk Action ... Data should
       download") does NOT map to a real bulk-actions/row-selection
       feature on this page — it maps instead to the CONFIRMED "Export to
       XLSX" mechanism: an Alpine-only trigger button
       (`@click="showModal = true"`, NOT wire:click) that opens a confirm
       dialog (Alpine `x-show="showModal"`, entangled to this same
       Livewire component's `modalOpen` property) with text "Are you sure
       you want to export the selected data?", a "No" cancel button
       (`@click="showModal = false"`) and a "Yes, Export" confirm button
       (`wire:click="exportAll"`). The dialog also has
       `wire:poll.5000ms.visible` while open and an Alpine `$watch` on
       `exportStatus` that reopens the modal once the backend sets it to
       `'ready'` — that ready/download-link render state was never
       actually reached during capture (the export was never triggered),
       so it remains a documented gap: this suite verifies the dialog
       opens with the right text and that clicking "Yes, Export" is
       accepted (dispatches `exportAll` without erroring), but does not
       assert a specific "download ready" UI state that was never
       observed.
    8. Two DISTINCT row actions in the Action column (not one, like most
       other pages) — both confirmed via real per-row markup (example:
       row id 15):
         - "View" (tooltip via `data-tooltip-target="tooltip-view-{id}"`,
           `wire:click.prevent="$dispatch('openModal', {component:
           'whatsapp.sender-id.view', arguments: {senderId: {...full row
           object...}}})"`).
         - "Optimize MMT" (tooltip
           `data-tooltip-target="tooltip-updateStatus-{id}"`,
           `wire:click.prevent="$dispatch('openModal', {component:
           'whatsapp.sender-id.optimize-mmt', arguments: {senderId:
           {id}}})"`) — a genuinely-confirmed BONUS feature not mentioned
           anywhere in the user's checklist, included here only as a
           "the modal opens" reachability check.
       Both dispatch into the SAME app-wide livewire-ui-modal
       (`id="modal-container"`, `x-data="LivewireUIModal()"`, confirmed
       elsewhere in this session, e.g. whatsapp_incoming_messages_page.py)
       but via two different modal components. Neither modal's internal
       content was ever captured (`showActiveComponent` was empty in this
       capture since neither button was actually clicked) — so, per this
       project's "never guess" rule, only "the modal opens" is asserted
       for TC007 (View) and the Optimize MMT bonus test; the fields
       inside each modal are a documented gap.
    9. MM Lite APIs column (TC013): a real, confirmed clickable colored
       pill — `<span wire:click.prevent="getMmLiteStatus({id})"
       data-tooltip-target="tooltip-mmLite-{id}">Enabled|Disabled</span>`,
       tooltip text "Sync MM Lite APIs Status". This is the CONFIRMED
       real mechanism directly matching the checklist's "Click
       Enabled/Disabled in MM lite column ... should fetch latest status
       from META".
    10. TPS (TC014) — UNRESOLVED GAP: wire:snapshot confirms the
        component has `editingTps` (null) and `tpsValue` (default 20)
        properties, and every row has a real `rate_limit_per_second`
        value (60 or 20 observed across the 10 captured rows) — but NO
        clickable UI element to trigger TPS editing was found anywhere in
        the captured DOM (not in the table, not in either action button).
        It most likely lives inside the uncaptured View modal's internal
        markup. Per this project's "never guess" rule, this page object
        exposes no TPS-editing locator/method at all, and the
        corresponding test is a documented `@pytest.mark.skip` rather
        than a fabricated one.
    11. Status column: only two codes observed across the 10 captured
        rows — 3="Approved" (green
        `bg-green-500`/`dark:bg-green-700`, with a real
        `data-popover-target="popover-default-{n}"` "Comments" popover
        showing `data.comment` when present) and 1="Pending" (no popover
        rendered for this state). Quality/Message Limit correlation
        confirmed: Quality="Green" pairs with a real "X/day" Message
        Limit; Quality="Error" pairs with "Error" Message Limit text.
    12. WABA Number can be genuinely EMPTY for a non-Meta provider (row
        "cpaasglobe" has an empty waba-number cell) — confirmed real
        business-logic edge case, not a rendering bug.
    13. Pagination: `.total-pagination-results` class (same convention as
        every other WhatsApp table this session), rendering the
        single-count "Showing N results" format (10 rows captured, all on
        one page — no Next/gotoPage button was exercised).
    14. TC008-TC011 are simply ABSENT from the manual QA checklist
        supplied for this page (not blank placeholder rows — the
        checklist jumps straight from TC007 to TC012) — intentionally not
        fabricated here; this suite's test IDs skip that range to mirror
        the checklist exactly.
    """

    REPORT_URL = "/whatsapp/channels/senderid"
    TABLE_NAME = "wa_sender_ids"

    # Confirmed default-rendered column order (8 of 10 selectable columns
    # — Department/User are deselected by default, so they are NOT part
    # of this baseline index map; toggling them on inserts them into the
    # live DOM in a position never captured, so no test relies on their
    # index).
    COLUMN_INDEX = {
        "action": 0, "app_name": 1, "waba_number": 2, "status": 3,
        "quality": 4, "message_limit": 5, "mm_lite_apis": 6, "created_at": 7,
    }

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[normalize-space()='WhatsApp Numbers']"
    CREATE_NEW_APP_LINK = "xpath=//a[contains(normalize-space(.),'Create New App')]"
    MODAL_CONTAINER = "#modal-container"

    # ── Search ────────────────────────────────────────────────────────────────
    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search']"

    # ── Filters panel (slide-down, Alpine-toggled — NOT wire:click) ─────────
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')][not(ancestor::table)]"
    FILTER_DEPARTMENT = f"#{TABLE_NAME}-filter-department"
    FILTER_USER = f"#{TABLE_NAME}-filter-user"
    FILTER_CREATED_AT_FROM = f"#{TABLE_NAME}-filter-created_at_from"
    FILTER_CREATED_AT_TO = f"#{TABLE_NAME}-filter-created_at_to"

    # ── Export to XLSX (Alpine trigger + confirm dialog — maps to the
    # checklist's "Bulk Action" TC006; no real bulk-actions feature exists
    # on this page) ─────────────────────────────────────────────────────────
    EXPORT_TRIGGER_BTN = "xpath=//button[normalize-space(.)='Export to XLSX']"
    EXPORT_DIALOG_TEXT = (
        "xpath=//p[contains(normalize-space(.),"
        "'Are you sure you want to export the selected data?')]"
    )
    EXPORT_CANCEL_BTN = "xpath=//button[normalize-space(.)='No']"
    EXPORT_CONFIRM_BTN = "xpath=//button[@*[name()='wire:click']='exportAll']"

    # ── Sorting (App Name / WABA Number / Status / Created At only —
    # confirmed; sortBy() field names deliberately don't match column
    # slugs) ─────────────────────────────────────────────────────────────────
    SORT_APP_NAME_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('name')\")]"
    SORT_WABA_NUMBER_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('number')\")]"
    SORT_STATUS_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('status')\")]"
    SORT_CREATED_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('created_at')\")]"
    APPLIED_SORT_PILL = f"xpath=//span[contains(@*[name()='wire:key'],'{TABLE_NAME}-sorting-pill-')]"
    CLEAR_ALL_SORTS_BTN = "xpath=//button[contains(@*[name()='wire:click.prevent'],'clearSorts')]"

    # ── Columns dropdown (10 selectable, 8 selected by default) ─────────────
    COLUMNS_BUTTON = "xpath=//button[contains(normalize-space(.),'Columns')][not(ancestor::table)]"
    COLUMN_SELECT_ALL_CHECKBOX = (
        "xpath=//input[@type='checkbox' and @*[name()='wire:click']='selectAllColumns']"
    )
    COLUMN_CHECKBOX_BY_VALUE = "input[type='checkbox'][value='{value}']"
    ALL_COLUMN_VALUES = [
        "action", "app-name", "waba-number", "department", "user",
        "status", "quality", "message-limit", "mm-lite-apis", "created-at",
    ]
    DEFAULT_SELECTED_COLUMNS = [
        "action", "app-name", "waba-number", "status", "quality",
        "message-limit", "mm-lite-apis", "created-at",
    ]
    DEFAULT_DESELECTED_COLUMNS = ["department", "user"]

    # ── Table ────────────────────────────────────────────────────────────────
    TABLE = f"#table-{TABLE_NAME}"
    TABLE_HEADERS = f"{TABLE} thead th"
    TABLE_ROWS = f"{TABLE} tbody tr"
    # No empty-state text was ever captured (table had 10 real rows at
    # capture time) — documented gap, same treatment as every other page
    # object built this session with a fully-populated capture.

    # ── Row actions (two distinct actions per row — confirmed) ──────────────
    VIEW_ACTION_BTN = (
        "xpath=(//button[contains(@*[name()='wire:click.prevent'],"
        "\"component: 'whatsapp.sender-id.view'\")])[1]"
    )
    OPTIMIZE_MMT_ACTION_BTN = (
        "xpath=(//button[contains(@*[name()='wire:click.prevent'],"
        "\"component: 'whatsapp.sender-id.optimize-mmt'\")])[1]"
    )

    # ── MM Lite APIs pill (TC013 — confirmed clickable) ──────────────────────
    MM_LITE_PILL = (
        "xpath=(//span[contains(@*[name()='wire:click.prevent'],"
        "'getMmLiteStatus')])[1]"
    )

    # ── Pagination ───────────────────────────────────────────────────────────
    PAGINATION_RESULTS_TEXT = ".total-pagination-results"

    # -------------------------------------------------------------------------
    # Navigation / page state
    # -------------------------------------------------------------------------

    def __init__(self, page):
        super().__init__(page)

    def navigate(self):
        self.open(self.REPORT_URL)
        self.page.wait_for_timeout(2000)
        return self

    navigate_to_report = navigate

    def is_sender_id_page(self):
        url = self.get_current_url()
        return "/whatsapp/channels/senderid" in url and "login" not in url.lower()

    def get_page_title_text(self):
        try:
            el = self.page.locator(self.PAGE_TITLE).first
            el.wait_for(state="visible", timeout=8000)
            return el.inner_text().strip()
        except Exception:
            return ""

    def wait_for_table_load(self, timeout=15000):
        try:
            self.page.locator(self.TABLE).wait_for(state="attached", timeout=timeout)
            self.page.wait_for_timeout(1000)
        except Exception:
            pass

    def _is_visible(self, locator, timeout=1000):
        try:
            return self.page.locator(locator).first.is_visible()
        except Exception:
            return False

    def is_create_new_app_link_present(self):
        return self.is_element_present(self.CREATE_NEW_APP_LINK, timeout=5000)

    def is_modal_open(self, timeout=10000):
        try:
            self.page.locator(self.MODAL_CONTAINER).first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def close_modal(self):
        try:
            self.page.keyboard.press("Escape")
        except Exception:
            pass
        self.page.wait_for_timeout(1000)

    # -------------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------------

    def _wait_for_search_to_settle(self, timeout=8000):
        end_time = self.page.evaluate("() => Date.now()") + timeout
        last_state = None
        while self.page.evaluate("() => Date.now()") < end_time:
            current = self.get_row_count()
            no_msg = self.has_no_records_message()
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
    # Filters panel
    # -------------------------------------------------------------------------

    def open_filters_panel(self):
        if self._is_visible(self.FILTER_DEPARTMENT, timeout=1000):
            return
        self._js_click(self.FILTERS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def filter_by_department(self, text):
        """Confirmed plain free-text input (debounced 500ms), NOT a
        <select> — pass any substring to match against, or '' to clear."""
        self.open_filters_panel()
        box = self.h.wait_for_element_visible(self.FILTER_DEPARTMENT)
        box.evaluate(
            "(el, v) => { el.value = v; "
            "el.dispatchEvent(new Event('input', {bubbles: true})); "
            "el.dispatchEvent(new Event('change', {bubbles: true})); }",
            text
        )
        self.page.wait_for_timeout(1200)

    def filter_by_user(self, text):
        """Confirmed plain free-text input (debounced 500ms), NOT a
        <select> — pass any substring to match against, or '' to clear."""
        self.open_filters_panel()
        box = self.h.wait_for_element_visible(self.FILTER_USER)
        box.evaluate(
            "(el, v) => { el.value = v; "
            "el.dispatchEvent(new Event('input', {bubbles: true})); "
            "el.dispatchEvent(new Event('change', {bubbles: true})); }",
            text
        )
        self.page.wait_for_timeout(1200)

    def set_created_at_from(self, date_str):
        """date_str: 'YYYY-MM-DD'. Plain native date input, no time
        component (confirmed — unlike Incoming Messages' paired date+time
        filter)."""
        self.open_filters_panel()
        el = self.h.wait_for_element_visible(self.FILTER_CREATED_AT_FROM)
        el.evaluate(
            "(el, v) => { el.value = v; el.dispatchEvent(new Event('change', {bubbles: true})); }",
            date_str
        )
        self.page.wait_for_timeout(1000)

    def set_created_at_to(self, date_str):
        self.open_filters_panel()
        el = self.h.wait_for_element_visible(self.FILTER_CREATED_AT_TO)
        el.evaluate(
            "(el, v) => { el.value = v; el.dispatchEvent(new Event('change', {bubbles: true})); }",
            date_str
        )
        self.page.wait_for_timeout(1000)

    def get_created_at_from_value(self):
        el = self.h.wait_for_element_visible(self.FILTER_CREATED_AT_FROM)
        return el.input_value()

    def get_created_at_to_value(self):
        el = self.h.wait_for_element_visible(self.FILTER_CREATED_AT_TO)
        return el.input_value()

    def clear_all_filters(self):
        """No 'Clear Filters' button exists on this page (confirmed
        absence) — reset each of the 4 fields directly instead."""
        self.open_filters_panel()
        for locator in (self.FILTER_DEPARTMENT, self.FILTER_USER):
            try:
                el = self.page.locator(locator).first
                el.evaluate(
                    "(el) => { el.value = ''; "
                    "el.dispatchEvent(new Event('input', {bubbles: true})); "
                    "el.dispatchEvent(new Event('change', {bubbles: true})); }"
                )
            except Exception:
                pass
        for locator in (self.FILTER_CREATED_AT_FROM, self.FILTER_CREATED_AT_TO):
            try:
                el = self.page.locator(locator).first
                el.evaluate(
                    "(el) => { el.value = ''; el.dispatchEvent(new Event('change', {bubbles: true})); }"
                )
            except Exception:
                pass
        self.page.wait_for_timeout(1200)

    # -------------------------------------------------------------------------
    # Export to XLSX (maps to checklist's "Bulk Action" TC006)
    # -------------------------------------------------------------------------

    def click_export_trigger(self):
        self._js_click(self.EXPORT_TRIGGER_BTN, timeout=10000)
        self.page.wait_for_timeout(800)

    def is_export_dialog_open(self, timeout=8000):
        return self.is_element_present(self.EXPORT_DIALOG_TEXT, timeout=timeout)

    def cancel_export_dialog(self):
        self._js_click(self.EXPORT_CANCEL_BTN, timeout=8000)
        self.page.wait_for_timeout(500)

    def confirm_export(self):
        """Clicks 'Yes, Export' (wire:click="exportAll"). The subsequent
        'ready'/download-link UI state was never captured in the supplied
        DOM evidence — this method only confirms the click is accepted,
        it does not assert any specific post-export UI."""
        self._js_click(self.EXPORT_CONFIRM_BTN, timeout=8000)
        self.page.wait_for_timeout(1500)

    # -------------------------------------------------------------------------
    # Table / rows
    # -------------------------------------------------------------------------

    @staticmethod
    def _is_empty_state_row(tds):
        return len(tds) == 1 and tds[0].get_attribute("colspan")

    def has_no_records_message(self):
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            if rows.count() == 1:
                tds = rows.nth(0).locator("td")
                td_list = [tds.nth(i) for i in range(tds.count())]
                if self._is_empty_state_row(td_list):
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
                td_list = [tds.nth(j) for j in range(n)]
                if self._is_empty_state_row(td_list):
                    continue
                if any(td.inner_text().strip() for td in td_list):
                    count += 1
            return count
        except Exception:
            return 0

    def get_table_headers(self):
        return self._get_headers_safe(self.TABLE_HEADERS)

    def get_column_values(self, column_name):
        """column_name: one of COLUMN_INDEX's keys. Only valid while the
        page is showing the default 8 columns (Department/User are
        deselected by default and not covered by COLUMN_INDEX)."""
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

    # -------------------------------------------------------------------------
    # Sorting
    # -------------------------------------------------------------------------

    def sort_by_app_name(self):
        self._js_click(self.SORT_APP_NAME_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_waba_number(self):
        self._js_click(self.SORT_WABA_NUMBER_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_status(self):
        self._js_click(self.SORT_STATUS_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_created_at(self):
        self._js_click(self.SORT_CREATED_AT_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def get_applied_sort_pill_text(self):
        if self.is_element_present(self.APPLIED_SORT_PILL, timeout=3000):
            return self.h.wait_for_element_visible(self.APPLIED_SORT_PILL).inner_text().strip()
        return None

    def clear_all_sorts(self):
        try:
            self._js_click(self.CLEAR_ALL_SORTS_BTN, timeout=8000)
            self.page.wait_for_timeout(1000)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Columns dropdown
    # -------------------------------------------------------------------------

    def open_columns_dropdown(self):
        if self._is_visible(self.COLUMN_CHECKBOX_BY_VALUE.format(value="action"), timeout=1000):
            return
        self._js_click(self.COLUMNS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def is_column_checkbox_present(self, value):
        try:
            return self.page.locator(self.COLUMN_CHECKBOX_BY_VALUE.format(value=value)).count() > 0
        except Exception:
            return False

    def toggle_column(self, value):
        self.open_columns_dropdown()
        cb = self.h.wait_for_element_visible(self.COLUMN_CHECKBOX_BY_VALUE.format(value=value))
        cb.scroll_into_view_if_needed()
        cb.click(force=True)
        self.page.wait_for_timeout(800)

    def is_column_checked(self, value):
        self.open_columns_dropdown()
        try:
            return self.page.locator(self.COLUMN_CHECKBOX_BY_VALUE.format(value=value)).first.is_checked()
        except Exception:
            return None

    def restore_default_columns(self):
        """Ensures Department/User end up unchecked and every default
        column ends up checked, regardless of current state."""
        self.open_columns_dropdown()
        for value in self.DEFAULT_DESELECTED_COLUMNS:
            if self.is_column_checked(value):
                self.toggle_column(value)
        for value in self.DEFAULT_SELECTED_COLUMNS:
            if not self.is_column_checked(value):
                self.toggle_column(value)

    # -------------------------------------------------------------------------
    # Row actions (View / Optimize MMT)
    # -------------------------------------------------------------------------

    def click_view_action(self):
        self._js_click(self.VIEW_ACTION_BTN, timeout=10000)
        self.page.wait_for_timeout(1000)

    def click_optimize_mmt_action(self):
        self._js_click(self.OPTIMIZE_MMT_ACTION_BTN, timeout=10000)
        self.page.wait_for_timeout(1000)

    # -------------------------------------------------------------------------
    # MM Lite APIs (TC013)
    # -------------------------------------------------------------------------

    def click_mm_lite_pill(self):
        self._js_click(self.MM_LITE_PILL, timeout=10000)
        self.page.wait_for_timeout(1500)

    def get_mm_lite_pill_text(self):
        try:
            return self.page.locator(self.MM_LITE_PILL).first.inner_text().strip()
        except Exception:
            return ""

    # -------------------------------------------------------------------------
    # Pagination
    # -------------------------------------------------------------------------

    def get_pagination_results_text(self):
        try:
            return self.page.locator(self.PAGINATION_RESULTS_TEXT).first.inner_text().strip()
        except Exception:
            return ""

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
