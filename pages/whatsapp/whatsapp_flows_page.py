from pages.common.base_page import BasePage


class WhatsappFlowsPage(BasePage):
    """
    WhatsApp Flows — page object.

    Grounded in a full live DOM capture of
    https://.../whatsapp/flows (reached via the top nav's "More" dropdown
    -> "Flows", confirmed nav link `href=".../whatsapp/flows"`,
    icon mdi-sitemap-outline). This page object covers ONLY the flows
    LISTING page — see the IMPORTANT SCOPE NOTE at the bottom of this
    docstring: the manual QA checklist's TC005-TC025 all target the
    separate Flow Builder page (/whatsapp/flows/builder, reached via the
    confirmed "Create Flow" link), whose DOM (screens, component palette,
    edit-content panel) was NEVER captured — this project's "never guess"
    rule means none of that is modeled here.

    Confirmed facts driving every locator below:

    1. Livewire component: memo.name = "whatsapp.flow.table", memo.path =
       "whatsapp/flows". tableName = "whatsapp_flows" (confirmed via
       wire:snapshot's data.tableName and every id/wire:key on the page,
       e.g. `<table id="table-whatsapp_flows">`,
       `x-init="setTableId('table-whatsapp_flows')"`).
    2. Header: `<h1 class="text-md font-semibold whitespace-nowrap">WhatsApp Flow</h1>`
       (singular "Flow", not "Flows" — confirmed exact text). Breadcrumb:
       Home > Channels > "WhatsApp Flows" (plain `<span>`, standard
       breadcrumb convention for this app — note the breadcrumb DOES say
       "Flows" plural, unlike the h1).
    3. Two top action controls (confirmed DIFFERENT mechanisms from each
       other — not a uniform pair):
         - "Sync Flows": plain
           `<button onclick="Livewire.dispatch('openModal', {component: 'whatsapp.flow.sync-flows'})">`
           (NOT wire:click — same plain-onclick mechanism confirmed on
           WhatsApp Blocked Users' top buttons). Opens the shared
           app-wide livewire-ui-modal (`id="modal-container"`,
           `x-data="LivewireUIModal()"`, confirmed again here, path
           "whatsapp/flows"). The modal's internal content (sender
           select, "Sync flows" confirm button) was NEVER captured
           (showActiveComponent was empty since the button was never
           clicked) — documented gap, same treatment as every other
           uncaptured modal this session.
         - "Create Flow": a REAL navigable link,
           `<a href=".../whatsapp/flows/builder">` — NOT a modal trigger.
           This is the Flow Builder entry point that TC005-TC025 all
           describe; only its reachability is confirmed here (see scope
           note below).
       A `<div id="sync-success-message" class="hidden">` exists with a
       JS listener on the `hideSuccessMessage` Livewire event that
       unhides it for 3s — confirmed real success-toast mechanism for
       "Sync Flows", though it was never actually triggered during
       capture (class stayed "hidden" throughout).
    4. Search: `<input wire:model.live="search" placeholder="Search By flow name" type="text" autocomplete="off">`
       — note the more specific placeholder text vs. other WhatsApp pages
       ("Search By flow name", not just "Search").
    5. Filters: CONFIRMED "popover" layout (`filterLayout: "popover"`,
       toggled via `x-on:click="filterPopoverOpen = !filterPopoverOpen"`
       on the "Filters" button) — a DIFFERENT filter-panel mechanism from
       Sender ID/Incoming Messages' "slide-down" layout. Only ONE filter
       exists: "sender" (filterCount: 1), and it is a complex async-select
       Livewire sub-component (`memo.name: "async-select"`,
       `endpoint: "/whatsapp/search-sender"`, placeholder "Search
       Sender") — NOT a plain `<select>` or text input like other pages'
       filters. Its own search box is confirmed:
       `<input x-ref="search" wire:model.live.debounce.300ms="search" placeholder="Search Sender">`.
       No "Clear Filters" button was found for this single-filter page
       (confirmed absence, matching WhatsApp Numbers/Blocked Users'
       precedent of some pages having none).
    6. Table: `<table id="table-whatsapp_flows">`. 8 real, confirmed
       selectable columns (selectableColumns in wire:snapshot): Action,
       Flow Id, Name, Sender, WABA Number, Status, Categories, Created
       At. Only "Sender" is deselected by default
       (columnSelectColumns.deselected = {"sender":"Sender"}) — the other
       7 are selected by default. Confirmed rendered header/column order
       for the 7 default columns (matches COLUMN_INDEX below exactly):
       Action, Flow Id, Name, WABA Number, Status, Categories, Created
       At.
    7. Sorting: 3 of the 7 default columns are sortable, each via a real,
       confirmed `wire:click="sortBy(...)"` button:
         - Name       -> `sortBy('name')`
         - Status     -> `sortBy('status')`
         - Created At -> `sortBy('created_at')`
       Flow Id / WABA Number / Categories / Action are plain `<span>`
       headers with no sortBy button. Default sort is `created_at desc`,
       with a real rendered sorting pill genuinely captured:
       `wire:key="whatsapp_flows-sorting-pill-created_at"`, text
       "Created At: Z-A", per-pill clear
       `wire:click="clearSort('created_at')"` (no `.prevent`), clear-all
       `wire:click.prevent="clearSorts"` (WITH `.prevent`) — same
       conventions confirmed on every other WhatsApp page this session.
    8. No Bulk Actions exist on this page — wire:snapshot's bulkActions is
       a genuinely empty array and there is no header/row checkbox
       anywhere in the table (confirmed absence).
    9. Two DISTINCT row actions in the Action column (confirmed via real
       per-row markup, example: row id 200):
         - "Deprecate" (red button, tooltip via
           `data-tooltip-target="tooltip-deleteOne-{id}"`) — a WireUI
           CONFIRM-ACTION mechanism (`x-on:click="$wireui.confirmAction({
           title: 'Are you sure to deprecate this flow ?', icon:
           'warning', method: 'deleteOne', params: ['Gts\\Whatsapp\\
           Models\\WhatsappFlow', {id}], accept: {style:'solid',
           color:'red'} }, '{wireId}')"`) — a DIFFERENT confirm mechanism
           from every other destructive action modeled this session
           (which all used $dispatch('openModal', ...) instead). This
           action is DESTRUCTIVE (deprecates a real flow) — this page
           object exposes only a way to check the button/tooltip exist,
           deliberately NOT a way to click through the confirm dialog,
           consistent with this project's caution around irreversible
           actions against QA data.
         - "Preview" (primary button, tooltip via
           `data-tooltip-target="tooltip-preview-{id}"`,
           `wire:click.prevent="$dispatch('openModal', {component:
           'whatsapp.flow.preview', arguments: {flow_id: {id}}})"`) —
           opens the same shared `#modal-container`. Its internal content
           was never captured (documented gap, same as Sync Flows').
    10. Status values confirmed across the 10 captured rows: "PUBLISHED"
        (9 rows) and "DEPRECATED" (1 row) — rendered as plain uppercase
        text, no colored pill/badge markup (unlike Sender ID's Status
        column). No "DRAFT" status was observed in this capture.
    11. Categories column renders the raw JSON array as literal text,
        e.g. `["APPOINTMENT_BOOKING","SIGN_IN"]` — confirmed NOT rendered
        as separate chips/badges.
    12. Pagination: CONFIRMED `.paged-pagination-results` class (matching
        the richer WhatsApp Incoming Messages precedent, NOT the
        single-count `.total-pagination-results` convention used by
        Sender ID/OptOut/Blocked Users) — format "Showing X to Y of Z
        results", with real numbered/Previous/Next controls
        (`wire:click="nextPage('whatsapp_flowsPage')"`, uniquely
        identified by `dusk="nextPage.whatsapp_flowsPage.after"` on
        desktop / `.before` on mobile, matching the identical dusk-attr
        convention on whatsapp_incoming_messages_page.py). 178 total
        flows existed at capture time (10 per page, 18 pages).

    IMPORTANT SCOPE NOTE (read before extending this suite): the manual QA
    checklist supplied for "WhatsApp Flows" has 25 test cases (TC001-
    TC025), but the DOM capture backing this page object is ONLY of the
    flows LISTING page above. TC005 ("Verify create flows") through
    TC025 (screens/components/edit-content inside the Flow Builder) all
    describe the SEPARATE Flow Builder page reached via the "Create Flow"
    link (`/whatsapp/flows/builder`) — a complex drag-and-drop
    screen/component editor whose DOM (screen list, "Add screen"/delete
    controls, the content-type picker for Large Heading/Small Heading/
    Caption/Body/Image/Short Answer/Paragraph/Date Picker/Single Choice/
    Multiple Choice/Dropdown/Opt-in, the live preview pane) was NEVER
    supplied. Per this project's "never guess" rule, NONE of that is
    modeled here — only the listing page (TC001-TC004) plus the
    confirmed reachability of "Create Flow" (part of TC005) are covered
    with real locators. TC006-TC025 are documented skips in the test
    file pending a DOM capture of the Flow Builder page itself.
    """

    REPORT_URL = "/whatsapp/flows"
    TABLE_NAME = "whatsapp_flows"

    # Confirmed default-rendered column order (7 of 8 selectable columns
    # — Sender is deselected by default, so it is NOT part of this
    # baseline index map).
    COLUMN_INDEX = {
        "action": 0, "flow_id": 1, "name": 2, "waba_number": 3,
        "status": 4, "categories": 5, "created_at": 6,
    }

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[normalize-space()='WhatsApp Flow']"
    MODAL_CONTAINER = "#modal-container"

    # ── Top action controls (confirmed DIFFERENT mechanisms) ────────────────
    SYNC_FLOWS_BTN = "xpath=//button[normalize-space(.)='Sync Flows']"
    CREATE_FLOW_LINK = "xpath=//a[contains(normalize-space(.),'Create Flow')]"
    SYNC_SUCCESS_MESSAGE = "#sync-success-message"

    # ── Search ────────────────────────────────────────────────────────────────
    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search By flow name']"

    # ── Filters (confirmed "popover" layout — different from Sender ID's
    # "slide-down") ──────────────────────────────────────────────────────────
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')][not(ancestor::table)]"
    FILTER_SENDER_SEARCH_INPUT = "input[placeholder='Search Sender']"

    # ── Sorting (Name / Status / Created At only — confirmed) ───────────────
    SORT_NAME_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('name')\")]"
    SORT_STATUS_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('status')\")]"
    SORT_CREATED_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('created_at')\")]"
    APPLIED_SORT_PILL = f"xpath=//span[contains(@*[name()='wire:key'],'{TABLE_NAME}-sorting-pill-')]"
    CLEAR_ALL_SORTS_BTN = "xpath=//button[contains(@*[name()='wire:click.prevent'],'clearSorts')]"

    # ── Columns dropdown (8 selectable, 7 selected by default) ──────────────
    COLUMNS_BUTTON = "xpath=//button[contains(normalize-space(.),'Columns')][not(ancestor::table)]"
    COLUMN_SELECT_ALL_CHECKBOX = (
        "xpath=//input[@type='checkbox' and @*[name()='wire:click']='selectAllColumns']"
    )
    COLUMN_CHECKBOX_BY_VALUE = "input[type='checkbox'][value='{value}']"
    ALL_COLUMN_VALUES = [
        "action", "flow-id", "name", "sender", "waba-number",
        "status", "categories", "created-at",
    ]
    DEFAULT_SELECTED_COLUMNS = [
        "action", "flow-id", "name", "waba-number",
        "status", "categories", "created-at",
    ]
    DEFAULT_DESELECTED_COLUMNS = ["sender"]

    # ── Table ────────────────────────────────────────────────────────────────
    TABLE = f"#table-{TABLE_NAME}"
    TABLE_HEADERS = f"{TABLE} thead th"
    TABLE_ROWS = f"{TABLE} tbody tr"
    # No empty-state text was ever captured (table had 10 real rows, 178
    # total, at capture time) — documented gap.

    # ── Row actions (two distinct actions per row — confirmed) ──────────────
    # "Deprecate" is DESTRUCTIVE — only presence/tooltip is exposed below,
    # deliberately no method to click through its WireUI confirm dialog.
    DEPRECATE_ACTION_BTN = (
        "xpath=(//button[contains(@*[name()='x-on:click'],'confirmAction') "
        "and contains(@*[name()='x-on:click'],'deleteOne')])[1]"
    )
    PREVIEW_ACTION_BTN = (
        "xpath=(//button[contains(@*[name()='wire:click.prevent'],"
        "\"component: 'whatsapp.flow.preview'\")])[1]"
    )

    # ── Pagination (confirmed richer "paged-pagination-results" format,
    # matching whatsapp_incoming_messages_page.py's convention) ─────────────
    PAGINATION_RESULTS_TEXT = ".paged-pagination-results"
    NEXT_PAGE_BTN = f"button[dusk='nextPage.{TABLE_NAME}Page.after']"
    NEXT_PAGE_BTN_MOBILE = f"button[dusk='nextPage.{TABLE_NAME}Page.before']"

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

    def is_flows_page(self):
        url = self.get_current_url()
        return "/whatsapp/flows" in url and "builder" not in url and "login" not in url.lower()

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
    # Top action controls
    # -------------------------------------------------------------------------

    def click_sync_flows(self):
        self._js_click(self.SYNC_FLOWS_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_create_flow_link_present(self):
        return self.is_element_present(self.CREATE_FLOW_LINK, timeout=5000)

    def get_create_flow_link_href(self):
        try:
            return self.page.locator(self.CREATE_FLOW_LINK).first.get_attribute("href") or ""
        except Exception:
            return ""

    def click_create_flow(self):
        self._js_click(self.CREATE_FLOW_LINK, timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_on_flow_builder_page(self):
        return "/whatsapp/flows/builder" in self.get_current_url()

    # -------------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------------

    def _wait_for_search_to_settle(self, timeout=8000):
        end_time = self.page.evaluate("() => Date.now()") + timeout
        last_state = None
        while self.page.evaluate("() => Date.now()") < end_time:
            current = self.get_row_count()
            state = current
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
    # Filters
    # -------------------------------------------------------------------------

    def open_filters_popover(self):
        if self._is_visible(self.FILTER_SENDER_SEARCH_INPUT, timeout=1000):
            return
        self._js_click(self.FILTERS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def is_sender_filter_search_present(self):
        self.open_filters_popover()
        return self.is_element_present(self.FILTER_SENDER_SEARCH_INPUT, timeout=5000)

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
        page is showing the default 7 columns (Sender is deselected by
        default and not covered by COLUMN_INDEX)."""
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

    def sort_by_name(self):
        self._js_click(self.SORT_NAME_BTN, timeout=10000)
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
        """Ensures Sender ends up unchecked and every default column
        ends up checked, regardless of current state."""
        self.open_columns_dropdown()
        for value in self.DEFAULT_DESELECTED_COLUMNS:
            if self.is_column_checked(value):
                self.toggle_column(value)
        for value in self.DEFAULT_SELECTED_COLUMNS:
            if not self.is_column_checked(value):
                self.toggle_column(value)

    # -------------------------------------------------------------------------
    # Row actions (Deprecate / Preview)
    # -------------------------------------------------------------------------

    def is_deprecate_action_present(self):
        return self.is_element_present(self.DEPRECATE_ACTION_BTN, timeout=5000)

    def click_preview_action(self):
        self._js_click(self.PREVIEW_ACTION_BTN, timeout=10000)
        self.page.wait_for_timeout(1000)

    # -------------------------------------------------------------------------
    # Pagination
    # -------------------------------------------------------------------------

    def get_pagination_results_text(self):
        try:
            return self.page.locator(self.PAGINATION_RESULTS_TEXT).first.inner_text().strip()
        except Exception:
            return ""

    def click_next_page(self):
        try:
            self._js_click(self.NEXT_PAGE_BTN, timeout=10000)
        except Exception:
            self._js_click(self.NEXT_PAGE_BTN_MOBILE, timeout=10000)
        self.page.wait_for_timeout(1500)

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
