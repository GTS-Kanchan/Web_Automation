from pages.common.base_page import BasePage


class WhatsappBlockedUsersPage(BasePage):
    """
    WhatsApp Blocked Users — page object.

    Grounded in a full live DOM capture of
    https://.../whatsapp/blocked-users (reached via the top nav's "More"
    dropdown -> "Blocked Users", not one of the main channel tabs — the
    manual QA checklist calls this "sender id page" / "Blocked users tab").
    This is a DIFFERENT feature from WhatsApp OptOut Numbers
    (whatsapp_optout_page.py, /whatsapp/campaigns/opt-out,
    tableName "opt_out_numbers") even though both live under the same
    "More" dropdown -- Blocked Users has its own URL, its own Livewire
    component, and its own tableName. Confirmed facts driving every
    locator below:

    1. Livewire component: memo.name = "whatsapp.blocked-users.table",
       memo.path = "whatsapp/blocked-users". tableName =
       "whatsapp_blocked_users" (confirmed via wire:snapshot's
       data.tableName and every id/wire:key on the page, e.g.
       `<table id="table-whatsapp_blocked_users">`).
    2. Header: `<h1 class="text-md font-semibold whitespace-nowrap">WhatsApp Blocked Users</h1>`.
       Breadcrumb: Home > "WhatsApp Blocked Users" (plain `<span>`,
       standard breadcrumb convention for this app).
    3. Three top action buttons, all plain `<button onclick="Livewire.dispatch('openModal', ...)">`
       (NOT wire:click -- confirmed distinct mechanism from every other
       modal-trigger button in this session, which all use
       wire:click.prevent="$dispatch(...)"):
         - "Sync from API" -> opens component
           'whatsapp.blocked-users.sync-blocked-users'.
         - "Block Users" -> opens component
           'whatsapp.blocked-users.import-users' with arguments
           {action: 'block'}.
         - "Unblock Users" -> opens component
           'whatsapp.blocked-users.import-users' with arguments
           {action: 'unblock'}.
       All three open the same app-wide livewire-ui-modal
       (`id="modal-container"`, `x-data="LivewireUIModal()"`) already
       confirmed elsewhere in this session (e.g.
       whatsapp_incoming_messages_page.py). The modal's INTERNAL content
       (the sender-id select, the "Sync blocked users" button, the
       file-upload dropzone, the manual-entry fields) was NEVER captured
       -- `<div id="modal-container">` was present but its
       showActiveComponent slot was empty at capture time, since none of
       the three buttons was actually clicked during the capture. Per
       this project's "never guess" rule, only "the modal opens" is
       asserted for real; the fields inside each modal are a documented
       gap (same treatment as every other uncaptured modal in this
       session, e.g. the WhatsApp Messages Report "View" popup).
    4. Search: `<input wire:model.live="search" placeholder="Search" type="text" autocomplete="off">`
       -- same confirmed CSS-selector pattern used identically elsewhere
       in this session (WhatsApp Incoming Messages, WhatsApp OptOut
       Numbers, SMS Incoming Messages).
    5. NO Filters button/panel exists anywhere on this page --
       wire:snapshot's filterComponents is a genuinely empty array and
       filterCount is 0 (confirmed absence, not a gap). This matches the
       manual QA checklist itself, which only ever mentions a "search
       box" for this page (TC002/TC003), never a Filters panel or a WABA
       number filter dropdown like the Incoming Messages / Download
       Center pages have.
    6. Table: `<table id="table-whatsapp_blocked_users">`. 4 real,
       confirmed columns (plus a bulk-select checkbox column), all
       selected by default per wire:snapshot's selectedColumns
       (["phone-number","sender-id","blocked-at","actions"]): Phone
       Number, Sender ID, Blocked At, Actions. Only Phone Number
       (`sortBy('phone_number')`) and Blocked At (`sortBy('blocked_at')`)
       are sortable -- confirmed via real `wire:click="sortBy(...)"`
       buttons; Sender ID and Actions are plain `<span>` headers with no
       sortBy button at all.
    7. Default sort is `created_at desc` (wire:snapshot's
       sorts:{"created_at":"desc"}) -- but "created_at" is NOT one of
       this page's 4 displayed/sortable columns, so no sorting pill ever
       renders for it (confirmed: the "Applied Sorting:" label is
       followed immediately by the Clear button with an empty pill
       list in the capture). The clear-ALL-sorts control IS confirmed:
       `wire:click.prevent="clearSorts"` (WITH .prevent, consistent with
       every other WhatsApp page in this session).
    8. Bulk Actions: "Bulk Actions" dropdown button
       (`id="whatsapp_blocked_users-bulkActionsDropdown"`) containing
       exactly ONE confirmed action, "Unblock Selected"
       (`wire:click="unblock"`,
       `wire:key="whatsapp_blocked_users-bulk-action-unblock"`). A
       header "select all" checkbox IS directly confirmed in this
       capture (`x-ref="bulkSelectAllCheckbox"` inside a
       `wire:key="whatsapp_blocked_users-thead-bulk-actions"` `<th>`).
       Individual PER-ROW checkboxes were NOT directly observed --
       the capture's table had 0 rows at the time (paginationTotalItemCount:
       0) -- but the row-checkbox wire:key naming convention
       (`{tableName}selectedItems-{id}`) is an ALREADY-CONFIRMED,
       identical, repeatedly-used pattern from the same livewire-tables
       bulk-action package elsewhere in this exact codebase
       (pages/sms/sms_blocked_numbers_page.py's ROW_CHECKBOX, reused
       identically in pages/rcs/rcs_optout_page.py,
       pages/whatsapp/whatsapp_optout_page.py, and
       pages/rcs/rcs_agent_page.py) -- so reusing that same confirmed
       pattern here (with this page's own tableName substituted in) is a
       same-package generalization, not a fabricated guess.
    9. Columns dropdown: "Columns" button, "All Columns" checkbox
       (`wire:click="deselectAllColumns"`), and 4 confirmed real column
       checkboxes (all selected by default): phone-number, sender-id,
       blocked-at, actions.
    10. Empty state is GENUINELY CAPTURED here (unlike every other page
        object built this session, where the empty state had to be
        inferred): the table had 0 real rows at capture time, rendering
        the exact confirmed text "No items found, try to broaden your
        search" inside a `wire:key="empty-message-{wireId}"` row with
        `colspan="100"`.
    11. Pagination: `.total-pagination-results` class (same convention as
        whatsapp_optout_page.py), rendering "Showing N results" (a
        single-count format, not the richer "X to Y of Z" format seen on
        WhatsApp Incoming Messages / Download Center). Since
        paginationTotalItemCount was 0 at capture time, no Next/gotoPage
        button was ever rendered -- this page object exposes no
        pagination-navigation methods, only reading the results text, to
        avoid guessing an unconfirmed multi-page control.
    12. NO per-row "Unblock" action button in the Actions column was ever
        captured (0 rows at capture time) -- so this page object exposes
        no row-level unblock locator/method at all. The manual QA
        checklist's TC006 ("click on Unblock of any contact in actions")
        is therefore an intentional gap: never guessed, must be a
        documented skip in the test file.
    13. `wire:offline` shows the same real "You are not connected to the
        internet." banner confirmed elsewhere in this session (hidden by
        default, not exercised by any test here).
    """

    REPORT_URL = "/whatsapp/blocked-users"
    TABLE_NAME = "whatsapp_blocked_users"

    # Confirmed column order (bulk-select checkbox column + 4 real
    # columns, all selected by default).
    COLUMN_INDEX = {
        "bulk_checkbox": 0, "phone_number": 1, "sender_id": 2,
        "blocked_at": 3, "actions": 4,
    }

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[normalize-space()='WhatsApp Blocked Users']"

    # ── Top action buttons (confirmed: plain onclick, NOT wire:click) ───────
    SYNC_FROM_API_BTN = "xpath=//button[normalize-space(.)='Sync from API']"
    BLOCK_USERS_BTN = "xpath=//button[normalize-space(.)='Block Users']"
    UNBLOCK_USERS_BTN = "xpath=//button[normalize-space(.)='Unblock Users']"
    MODAL_CONTAINER = "#modal-container"

    # ── Search (no Filters panel exists on this page — confirmed absence) ───
    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search']"

    # ── Sorting (only Phone Number / Blocked At are sortable — confirmed) ───
    SORT_PHONE_NUMBER_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('phone_number')\")]"
    SORT_BLOCKED_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('blocked_at')\")]"
    # Generic pill locator (same convention as whatsapp_optout_page.py) —
    # no per-field pill was ever rendered in the capture since the default
    # sort field (created_at) isn't a displayed column.
    APPLIED_SORT_PILL = f"xpath=//span[contains(@*[name()='wire:key'],'{TABLE_NAME}-sorting-pill-')]"
    CLEAR_ALL_SORTS_BTN = "xpath=//button[contains(@*[name()='wire:click.prevent'],'clearSorts')]"

    # ── Bulk Actions ─────────────────────────────────────────────────────────
    BULK_ACTIONS_BUTTON = f"#{TABLE_NAME}-bulkActionsDropdown"
    BULK_ACTION_UNBLOCK = (
        "xpath=//button[@*[name()='wire:click']='unblock' and "
        "contains(@*[name()='wire:key'],'bulk-action-unblock')]"
    )
    # Confirmed directly in this page's own capture (x-ref attribute).
    SELECT_ALL_ROWS_CHECKBOX = "xpath=//input[@x-ref='bulkSelectAllCheckbox']"
    # Same-package pattern already confirmed elsewhere in this codebase
    # (sms_blocked_numbers_page.py / rcs_optout_page.py /
    # whatsapp_optout_page.py / rcs_agent_page.py) — this page's own
    # tableName substituted in; no row of this table was ever captured to
    # confirm this exact string directly.
    ROW_CHECKBOX = f"input[type='checkbox'][wire\\:key^='{TABLE_NAME}selectedItems-']"

    # ── Columns dropdown ─────────────────────────────────────────────────────
    COLUMNS_BUTTON = "xpath=//button[contains(normalize-space(.),'Columns')][not(ancestor::table)]"
    COLUMN_SELECT_ALL_CHECKBOX = (
        "xpath=//label[.//span[normalize-space()='All Columns']]//input[@type='checkbox']"
    )
    COLUMN_CHECKBOX_BY_VALUE = "input[type='checkbox'][value='{value}']"
    ALL_COLUMN_VALUES = ["phone-number", "sender-id", "blocked-at", "actions"]

    # ── Table ────────────────────────────────────────────────────────────────
    TABLE = f"#table-{TABLE_NAME}"
    TABLE_HEADERS = f"{TABLE} thead th"
    TABLE_ROWS = f"{TABLE} tbody tr"
    # Genuinely captured exact text (this page's table had 0 rows at
    # capture time) — not a guessed/broadened fallback like every other
    # page object built this session.
    NO_RECORDS_MSG = (
        "xpath=//*[contains(normalize-space(.),"
        "'No items found, try to broaden your search')]"
    )

    # ── Pagination (confirmed: single-count "Showing N results" format,
    # same convention as whatsapp_optout_page.py; no Next/gotoPage button
    # was ever rendered since paginationTotalItemCount was 0) ──────────────
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

    def is_blocked_users_page(self):
        url = self.get_current_url()
        return "/whatsapp/blocked-users" in url and "login" not in url.lower()

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

    # -------------------------------------------------------------------------
    # Top action buttons (Sync from API / Block Users / Unblock Users)
    # -------------------------------------------------------------------------

    def click_sync_from_api(self):
        self._js_click(self.SYNC_FROM_API_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def click_block_users(self):
        self._js_click(self.BLOCK_USERS_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def click_unblock_users(self):
        self._js_click(self.UNBLOCK_USERS_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

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
        return len(tds) == 1 and tds[0].get_attribute("colspan")

    def has_no_records_message(self):
        if self.is_element_present(self.NO_RECORDS_MSG, timeout=3000):
            return True
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
        return self._first_visible_data_row(self.TABLE_ROWS)

    # -------------------------------------------------------------------------
    # Sorting
    # -------------------------------------------------------------------------

    def sort_by_phone_number(self):
        self._js_click(self.SORT_PHONE_NUMBER_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_blocked_at(self):
        self._js_click(self.SORT_BLOCKED_AT_BTN, timeout=10000)
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
    # Bulk Actions
    # -------------------------------------------------------------------------

    def open_bulk_actions_dropdown(self):
        self._js_click(self.BULK_ACTIONS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def is_select_all_checkbox_present(self):
        return self.is_element_present(self.SELECT_ALL_ROWS_CHECKBOX, timeout=5000)

    def click_select_all_checkbox(self):
        cb = self.h.wait_for_element_visible(self.SELECT_ALL_ROWS_CHECKBOX)
        cb.scroll_into_view_if_needed()
        cb.click(force=True)
        self.page.wait_for_timeout(500)

    def select_first_row_checkbox(self):
        cb = self.h.wait_for_element_visible(self.ROW_CHECKBOX)
        cb.scroll_into_view_if_needed()
        cb.click(force=True)
        self.page.wait_for_timeout(500)

    def click_bulk_unblock(self):
        self.open_bulk_actions_dropdown()
        self._js_click(self.BULK_ACTION_UNBLOCK, timeout=10000)
        self.page.wait_for_timeout(1500)

    # -------------------------------------------------------------------------
    # Columns dropdown
    # -------------------------------------------------------------------------

    def open_columns_dropdown(self):
        if self._is_visible(self.COLUMN_CHECKBOX_BY_VALUE.format(value="phone-number"), timeout=1000):
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

    def get_column_checkbox_state(self, value):
        self.open_columns_dropdown()
        try:
            return self.page.locator(self.COLUMN_CHECKBOX_BY_VALUE.format(value=value)).first.is_checked()
        except Exception:
            return None

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
