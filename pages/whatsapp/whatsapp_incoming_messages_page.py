import os

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR


class WhatsappIncomingMessagesPage(BasePage):
    """
    WhatsApp Incoming Messages — page object.

    Grounded entirely in a full live DOM capture of
    https://.../whatsapp/campaigns/incoming-messages (reached via the top
    nav's "More" dropdown -> "Incoming Messages", NOT one of the main
    channel tabs). Confirmed facts driving every locator below:

    1. Livewire component: memo.name = "whatsapp.campaign.incoming-message.table",
       memo.path = "whatsapp/campaigns/incoming-messages". The underlying
       livewire-tables package uses a STABLE, developer-configured
       tableName = "wa_incoming_messages" (confirmed via
       `wire:snapshot`'s data.tableName and every id/wire:key on the page,
       e.g. `<table id="table-wa_incoming_messages">`) — this is what
       every locator below is built from, not the session-specific
       `wire:id`.
    2. Header: `<h1 class="text-md font-semibold whitespace-nowrap">WhatsApp Incoming Messages</h1>`.
       Breadcrumb: Home > Channels > "WhatsApp Incoming Messages" (plain
       `<span>`, matching this app's standard breadcrumb convention).
    3. Search: `<input wire:model.live="search" placeholder="Search" type="text" autocomplete="off">`
       — no id, but the wire:model.live + placeholder combo is a stable,
       already-confirmed CSS-selector pattern used identically on the SMS
       Incoming Messages page (pages/sms/sms_incoming_messages_page.py)
       and reused here.
    4. Filters panel (slide-down, `x-on:click="filtersOpen = !filtersOpen"`
       on the "Filters" button) contains 4 real fields
       (filterComponents: sender_id, type, received_from, received_to):
         - WABA Number: `<select wire:model.live="filterComponents.sender_id"
           id="wa_incoming_messages-filter-sender_id">`. CONFIRMED option
           VALUES are internal numeric sender ids, NOT the phone numbers
           themselves: value=""->All, value="3"->15557702525,
           value="9"->919202511257, value="6"->919326395073. Selecting by
           phone number therefore requires mapping through
           WABA_NUMBER_TO_ID below.
         - Type: `<select wire:model.live="filterComponents.type"
           id="wa_incoming_messages-filter-type">`. CONFIRMED 11 real
           option values (alphabetical): audio, button, contacts,
           document, image, interactive, location, reaction, sticker,
           text, video (plus ""->All).
         - Received From / Received To: NOT a Flatpickr range input (that
           is the Download Center page's mechanism) — here each is a
           native `<input type="date">` + a separate 5-minute-increment
           `<select>` (00:00..23:55), combined by an Alpine
           `updateDateTime()` handler into an ISO `YYYY-MM-DDTHH:MM`
           value written to `filterComponents.received_from` /
           `.received_to` on the input's `change` event. Wrapper divs:
           `id="wa_incoming_messages-filter-received_from-wrapper"` /
           `...-received_to-wrapper"`. This exact mechanism (native date
           input + change-event dispatch) is already confirmed and used
           identically on pages/sms/sms_incoming_messages_page.py — same
           underlying Alpine component, reused here.
    5. No "Clear filters" pill was ever rendered in the capture (no filter
       was active in that session), but wire:effects.listeners explicitly
       lists "clearFilters"/"clear-filters" — the exact same situation
       already documented (and solved the same way) in
       pages/sms/sms_incoming_messages_page.py's CLEAR_FILTERS_BTN: a
       wire:click-attribute-based locator with a text-based fallback,
       inferred from the confirmed listener rather than a captured pill.
    6. Sorting: default sort is `received_at desc` (confirmed via
       sorts:{"received_at":"desc"} and the rendered
       "Applied Sorting: Received At: Z-A" pill,
       `wire:key="wa_incoming_messages-sorting-pill-received_at"`, whose
       remove control is `wire:click="clearSort('received_at')"` — plain
       wire:click, NOT wire:click.prevent). The clear-ALL-sorts control is
       `wire:click.prevent="clearSorts"` (WITH .prevent — confirmed
       distinct from the single-pill form, same distinction already
       documented on the Download Center page). Only 2 of the 9 table
       headers are sortable — CONFIRMED via real `wire:click="sortBy(...)"`
       buttons: Received At (`sortBy('received_at')`) and Created At
       (`sortBy('created_at')`). The other 7 headers (Action, Campaign
       Name, WABA Number, Country Code, User Number, User Name, Type) are
       plain `<span>` with no sortBy button at all — NOT sortable.
    7. Columns dropdown: "Columns" button, "All Columns" checkbox
       (`wire:click="deselectAllColumns"`, label text "All Columns"), and
       9 confirmed real column checkboxes (all selected by default per
       wire:snapshot's selectedColumns): action, campaign-name,
       waba-number, country-code, user-number, user-name, type,
       received-at, created-at.
    8. Export CSV: a plain `<a href="https://.../whatsapp/campaigns/incoming-messages/export">Export CSV</a>`
       link (NOT a wire:click button) — clicking it triggers a real file
       download, confirmed by its real href pointing at a dedicated
       `/export` route.
    9. Table: `<table id="table-wa_incoming_messages">`. 9 confirmed
       headers in this exact order (0-indexed): Action, Campaign Name,
       WABA Number, Country Code, User Number, User Name, Type,
       Received At, Created At. 10 real rows captured (ids 2857-2866),
       giving concrete, confirmed column value patterns:
         - Action: a single "View" button (`data-tooltip-target="tooltip-view-{id}"`,
           tooltip text "View", eye icon) that dispatches
           `wire:click.prevent="$dispatch('openModal', { component: 'whatsapp.campaign.incoming-message.view', arguments: {incomingMessageId: ID} })"`.
           There is NO Download or Delete action on this page (unlike
           the Download Center) — View is the only row action.
         - Campaign Name: either a real campaign label ending in
           " - Campaign" (e.g. "August 26 2026 1:26 PM - Campaign ") or
           the literal string "N/A" when no campaign preceded the
           message — CONFIRMED via a genuine mix of both across the 10
           captured rows, matching this page's documented business rule.
         - WABA Number: the literal sender phone number, e.g.
           "919202511257" (matches the phone-number labels shown in the
           WABA Number filter's own dropdown options).
         - Country Code: literal 2-letter code, e.g. "IN".
         - User Number: PARTIALLY MASKED, e.g. "91873*****03",
           "91996*****10" — CONFIRMED real masking pattern (leading
           digits + a run of asterisks + trailing digits), never a raw
           unmasked number.
         - User Name: plain real name text, e.g. "Divesh Dwivedi".
         - Type: one of the 11 confirmed Type filter values (e.g. "text",
           "button" both observed in the captured rows).
         - Received At / Created At: "DD-MM-YYYY HH:MM:SS" timestamp
           strings; Received At is always <= Created At in every captured
           row (received, then processed a couple seconds later).
    10. Row action's modal uses the app-wide `livewire-ui-modal` package
        (`x-data="LivewireUIModal()"`, container `id="modal-container"`,
        `x-on:keydown.escape.window="show && closeModalOnEscape()"`) — a
        DIFFERENT mechanism from the Download Center page's own
        component-local `showSummaryModal` Livewire property. This exact
        `#modal-container` + Escape-to-close mechanism is already
        confirmed and used identically on
        pages/sms/sms_incoming_messages_page.py (same package), and is
        reused here rather than the Download Center's page-local
        approach, since the confirmed DOM mechanism actually differs.
    11. Pagination is REAL and multi-page here (unlike Download Center's
        single page of 2 rows) — 2603 total items / 261 pages confirmed
        via `paginationTotalItemCount` and the rendered numbered page
        buttons. Confirmed elements:
          - Result text: `<p class="paged-pagination-results ...">Showing
            <span>1</span> to <span>10</span> of <span>2603</span>
            results</p>` — a DIFFERENT class name and richer "X to Y of
            Z" text than the Download Center's `.total-pagination-results`
            ("Showing N results" only).
          - Desktop Next button: `wire:click="nextPage('wa_incoming_messagesPage')"`,
            uniquely identified by `dusk="nextPage.wa_incoming_messagesPage.after"`.
          - Mobile Next button: same wire:click, `dusk="nextPage.wa_incoming_messagesPage.before"`.
          - Numbered page buttons (pages 2-10, 260, 261 all confirmed
            present at capture time): `wire:click="gotoPage(N, 'wa_incoming_messagesPage')"`.
            Page 1 was the active page at capture time, rendered as a
            non-clickable `aria-current="page"` span rather than a
            button — but pages 2-10 all render via the identical
            Blade-loop button, so generalizing that same gotoPage(N, ...)
            button to other values of N (not literally captured, e.g.
            N=1 when a different page is active) is a same-template
            generalization rather than a guess about a different
            mechanism.
          - Previous, on page 1, is DISABLED and rendered as a plain
            (non-wire:click) `<span aria-disabled="true" aria-label="&laquo; Previous">`
            — no ENABLED Previous wire:click method name was ever
            captured (we were always on page 1), so this page object
            does NOT expose a `click_previous_page()` — going back a
            page in tests uses `goto_page(1)` instead, which IS a
            confirmed mechanism (see above).
    12. `wire:offline` shows a real "You are not connected to the
        internet." banner (hidden by default) — not exercised by any
        test here (would require simulating an offline network state).
    13. No genuine empty/no-records state was ever captured (all 10
        sampled rows had real data) — NO_RECORDS_MSG below reuses the
        exact same broadened, case-insensitive fallback locator already
        established for this identical situation on
        pages/sms/sms_incoming_messages_page.py (same livewire-tables
        package, same class of gap), rather than guessing this page's
        specific empty-state wording.
    """

    REPORT_URL = "/whatsapp/campaigns/incoming-messages"
    TABLE_NAME = "wa_incoming_messages"

    # Confirmed column order (all 9 columns selected by default).
    COLUMN_INDEX = {
        "action": 0, "campaign_name": 1, "waba_number": 2, "country_code": 3,
        "user_number": 4, "user_name": 5, "type": 6, "received_at": 7,
        "created_at": 8,
    }

    # Confirmed real WABA Number filter options: phone number -> internal id.
    WABA_NUMBER_TO_ID = {
        "15557702525": "3",
        "919202511257": "9",
        "919326395073": "6",
    }

    # Confirmed real Type filter option values (alphabetical, plus "" = All).
    TYPE_FILTER_VALUES = [
        "audio", "button", "contacts", "document", "image", "interactive",
        "location", "reaction", "sticker", "text", "video",
    ]

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[normalize-space()='WhatsApp Incoming Messages']"

    # ── Search ───────────────────────────────────────────────────────────────
    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search']"

    # ── Filters panel ────────────────────────────────────────────────────────
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')][not(ancestor::table)]"
    FILTER_SENDER_SELECT = f"#{TABLE_NAME}-filter-sender_id"
    FILTER_TYPE_SELECT = f"#{TABLE_NAME}-filter-type"
    FILTER_RECEIVED_FROM_WRAPPER = f"#{TABLE_NAME}-filter-received_from-wrapper"
    FILTER_RECEIVED_TO_WRAPPER = f"#{TABLE_NAME}-filter-received_to-wrapper"
    FILTER_RECEIVED_FROM_DATE = f"{FILTER_RECEIVED_FROM_WRAPPER} input[type='date']"
    FILTER_RECEIVED_FROM_TIME = f"{FILTER_RECEIVED_FROM_WRAPPER} select"
    FILTER_RECEIVED_TO_DATE = f"{FILTER_RECEIVED_TO_WRAPPER} input[type='date']"
    FILTER_RECEIVED_TO_TIME = f"{FILTER_RECEIVED_TO_WRAPPER} select"
    # Not a captured rendered pill (no filter was active at capture time) --
    # inferred from the confirmed "clearFilters"/"clear-filters" Livewire
    # listeners, same documented gap/fix as sms_incoming_messages_page.py.
    CLEAR_FILTERS_BTN = (
        "xpath=//button[contains(@*[name()='wire:click'],'clearFilters') "
        "or contains(@*[name()='wire:click.prevent'],'clearFilters') "
        "or normalize-space()='Clear']"
    )

    # ── Sorting (only 2 of 9 headers are sortable — confirmed) ──────────────
    SORT_RECEIVED_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('received_at')\")]"
    SORT_CREATED_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('created_at')\")]"
    CLEAR_SORT_PILL_BY_FIELD_XPATH = (
        "xpath=//button[contains(@*[name()='wire:click'],\"clearSort('{field}')\")]"
    )
    CLEAR_ALL_SORTS_BTN = "xpath=//button[contains(@*[name()='wire:click.prevent'],'clearSorts')]"

    # ── Columns dropdown ─────────────────────────────────────────────────────
    COLUMNS_BUTTON = "xpath=//button[contains(normalize-space(.),'Columns')][not(ancestor::table)]"
    COLUMN_SELECT_ALL_CHECKBOX = (
        "xpath=//label[.//span[normalize-space()='All Columns']]//input[@type='checkbox']"
    )
    COLUMN_CHECKBOX_BY_VALUE = "input[type='checkbox'][value='{value}']"
    # Confirmed real values, all selected by default:
    ALL_COLUMN_VALUES = [
        "action", "campaign-name", "waba-number", "country-code",
        "user-number", "user-name", "type", "received-at", "created-at",
    ]

    # ── Export CSV (plain <a> link, not a wire:click button) ────────────────
    EXPORT_CSV_LINK = (
        "xpath=//a[contains(@href,'/whatsapp/campaigns/incoming-messages/export') "
        "and contains(normalize-space(.),'Export CSV')]"
    )

    # ── Table ────────────────────────────────────────────────────────────────
    TABLE = f"#table-{TABLE_NAME}"
    TABLE_HEADERS = f"{TABLE} thead th"
    TABLE_ROWS = f"{TABLE} tbody tr"
    # Package-level fallback, same gap/fix already documented for this exact
    # situation on pages/sms/sms_incoming_messages_page.py.
    NO_RECORDS_MSG = (
        "xpath=//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no record') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no data') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no result') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'not found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'nothing found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no messages')]"
    )

    # ── Row action (View) / modal ────────────────────────────────────────────
    ACTION_VIEW_BTN_IN_ROW = "xpath=.//button[contains(@data-tooltip-target,'tooltip-view-')]"
    # Confirmed: the app-wide livewire-ui-modal package, NOT the Download
    # Center page's own component-local showSummaryModal mechanism.
    MODAL_CONTAINER = "#modal-container"

    # ── Pagination (real, multi-page here — confirmed 2603 items / 261 pages) ─
    PAGINATION_RESULTS_TEXT = ".paged-pagination-results"
    NEXT_PAGE_BTN = f"button[dusk='nextPage.{TABLE_NAME}Page.after']"
    NEXT_PAGE_BTN_MOBILE = f"button[dusk='nextPage.{TABLE_NAME}Page.before']"
    PREV_PAGE_DISABLED = "xpath=//span[@aria-disabled='true' and @aria-label='« Previous']"
    GOTO_PAGE_BTN_TEMPLATE = (
        "button[wire\\:click=\"gotoPage({page}, '" + TABLE_NAME + "Page')\"]"
    )

    # -------------------------------------------------------------------------
    # Init — registers a page-level download listener for Export CSV
    # (mirrors the pattern used on other pages with a real file download).
    # -------------------------------------------------------------------------

    def __init__(self, page):
        super().__init__(page)

    # -------------------------------------------------------------------------
    # Navigation / page state
    # -------------------------------------------------------------------------

    def navigate(self):
        self.open(self.REPORT_URL)
        self.page.wait_for_timeout(2000)
        return self

    navigate_to_report = navigate

    def is_incoming_messages_page(self):
        url = self.get_current_url()
        return "/whatsapp/campaigns/incoming-messages" in url and "login" not in url.lower()

    def get_page_title_text(self):
        try:
            el = self.page.locator(self.PAGE_TITLE).first
            el.wait_for(state="visible", timeout=8000)
            return el.inner_text().strip()
        except Exception:
            return ""

    def wait_for_table_load(self, timeout=15000):
        try:
            self.h.wait_until(
                lambda: self.page.locator(self.TABLE_ROWS).count() > 0
                or self.page.locator(self.NO_RECORDS_MSG).count() > 0,
                timeout_ms=timeout, interval_ms=500
            )
            self.page.wait_for_timeout(500)
        except Exception:
            pass

    def _is_visible(self, locator, timeout=1000):
        try:
            return self.page.locator(locator).first.is_visible()
        except Exception:
            return False

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
        """JS-driven single 'input'+'change' dispatch (not type char-by-char)
        to avoid a wire:model.live per-keystroke race -- same proven fix
        already used on this exact search-input mechanism on the SMS
        Incoming Messages page."""
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

    @staticmethod
    def is_valid_campaign_name_value(text):
        """Confirmed business rule: either 'N/A' (no preceding campaign)
        or a real campaign label ending in ' - Campaign'."""
        text = (text or "").strip()
        return text == "N/A" or "Campaign" in text

    @staticmethod
    def is_masked_user_number(text):
        """Confirmed real masking pattern: leading digits, a run of
        asterisks, trailing digits (e.g. '91873*****03') -- never a raw
        unmasked number."""
        import re
        return bool(re.match(r"^\d+\*+\d+$", (text or "").strip()))

    # -------------------------------------------------------------------------
    # Filters panel
    # -------------------------------------------------------------------------

    def open_filters_panel(self):
        if self._is_visible(self.FILTER_SENDER_SELECT, timeout=1000):
            return
        self._js_click(self.FILTERS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def filter_by_waba_number(self, value):
        """value: a confirmed phone number ('919202511257', ...), its
        internal id ('9', ...), or '' for All. Phone numbers are mapped
        through WABA_NUMBER_TO_ID since the <select>'s real option
        values are internal ids, not the phone numbers themselves."""
        self.open_filters_panel()
        select_value = self.WABA_NUMBER_TO_ID.get(value, value)
        self.h.select_option(self.FILTER_SENDER_SELECT, value=select_value)
        self.page.wait_for_timeout(1500)

    def filter_by_type(self, value):
        """value: one of TYPE_FILTER_VALUES, or '' for All."""
        self.open_filters_panel()
        self.h.select_option(self.FILTER_TYPE_SELECT, value=value)
        self.page.wait_for_timeout(1500)

    def set_received_from(self, date_str, time_str=None):
        """date_str: 'YYYY-MM-DD'. time_str: 'HH:MM' matching one of the
        confirmed 5-minute-increment <select> options, or None to leave
        the Alpine default (00:00, per the confirmed updateDateTime()
        fallback when only a date is set)."""
        self.open_filters_panel()
        date_el = self.h.wait_for_element_visible(self.FILTER_RECEIVED_FROM_DATE)
        date_el.evaluate(
            "(el, v) => { el.value = v; el.dispatchEvent(new Event('change', {bubbles: true})); }",
            date_str
        )
        self.page.wait_for_timeout(400)
        if time_str:
            time_el = self.page.locator(self.FILTER_RECEIVED_FROM_TIME).first
            time_el.select_option(value=time_str)
            self.page.wait_for_timeout(400)
        self.page.wait_for_timeout(1000)

    def set_received_to(self, date_str, time_str=None):
        self.open_filters_panel()
        date_el = self.h.wait_for_element_visible(self.FILTER_RECEIVED_TO_DATE)
        date_el.evaluate(
            "(el, v) => { el.value = v; el.dispatchEvent(new Event('change', {bubbles: true})); }",
            date_str
        )
        self.page.wait_for_timeout(400)
        if time_str:
            time_el = self.page.locator(self.FILTER_RECEIVED_TO_TIME).first
            time_el.select_option(value=time_str)
            self.page.wait_for_timeout(400)
        self.page.wait_for_timeout(1000)

    def get_filter_received_from_value(self):
        # input_value(), not get_attribute('value') -- setting .value via
        # JS updates the live DOM property but not the HTML attribute
        # (same proven fix already used on the SMS Incoming Messages page
        # and the RCS Download Center's filter verification).
        el = self.h.wait_for_element_visible(self.FILTER_RECEIVED_FROM_DATE)
        return el.input_value()

    def get_filter_received_to_value(self):
        el = self.h.wait_for_element_visible(self.FILTER_RECEIVED_TO_DATE)
        return el.input_value()

    def click_clear_all_filters(self):
        if not self.is_element_present(self.CLEAR_FILTERS_BTN, timeout=5000):
            return False
        self._js_click(self.CLEAR_FILTERS_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)
        return True

    # -------------------------------------------------------------------------
    # Sorting
    # -------------------------------------------------------------------------

    def sort_by_received_at(self):
        self._js_click(self.SORT_RECEIVED_AT_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_created_at(self):
        self._js_click(self.SORT_CREATED_AT_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_sort_applied(self, field):
        try:
            xpath = self.CLEAR_SORT_PILL_BY_FIELD_XPATH.format(field=field)
            return self.page.locator(xpath).count() > 0
        except Exception:
            return False

    def clear_sort(self, field):
        try:
            xpath = self.CLEAR_SORT_PILL_BY_FIELD_XPATH.format(field=field)
            self._js_click(xpath, timeout=8000)
            self.page.wait_for_timeout(1000)
        except Exception:
            pass

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

    def get_column_checkbox_state(self, value):
        self.open_columns_dropdown()
        try:
            return self.page.locator(self.COLUMN_CHECKBOX_BY_VALUE.format(value=value)).first.is_checked()
        except Exception:
            return None

    # -------------------------------------------------------------------------
    # Export CSV
    # -------------------------------------------------------------------------

    def export_csv(self, timeout=30000):
        try:
            link = self.h.wait_for_element_clickable(self.EXPORT_CSV_LINK, timeout=10000)
            link.scroll_into_view_if_needed()
            with self.page.expect_download(timeout=timeout) as dl_info:
                link.click(force=True)
            download = dl_info.value
            filename = download.suggested_filename or "wa_incoming_messages_export.csv"
            dest = os.path.join(DOWNLOAD_DIR, filename)
            download.save_as(dest)
            return {"file_path": dest, "file_size": os.path.getsize(dest)}
        except Exception:
            return None

    # -------------------------------------------------------------------------
    # Row action (View) / modal
    # -------------------------------------------------------------------------

    def click_view_on_row(self, row_idx=0):
        rows = self.page.locator(self.TABLE_ROWS)
        if row_idx >= rows.count():
            return False
        row = rows.nth(row_idx)
        try:
            btn = row.locator(self.ACTION_VIEW_BTN_IN_ROW).first
            if btn.count() == 0:
                return False
            btn.scroll_into_view_if_needed()
            btn.click(force=True)
        except Exception:
            return False
        self.page.wait_for_timeout(1500)
        return True

    def click_view_on_first_row(self):
        row = self.get_first_data_row()
        if row is None:
            return False
        try:
            btn = row.locator(self.ACTION_VIEW_BTN_IN_ROW).first
            if btn.count() == 0:
                return False
            btn.scroll_into_view_if_needed()
            btn.click(force=True)
        except Exception:
            return False
        self.page.wait_for_timeout(1500)
        return True

    def is_modal_open(self, timeout=10000):
        try:
            self.page.locator(self.MODAL_CONTAINER).first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def close_modal(self):
        """Confirmed mechanism: the app-wide livewire-ui-modal component's
        own x-on:keydown.escape.window handler."""
        try:
            self.page.keyboard.press("Escape")
        except Exception:
            pass
        self.page.wait_for_timeout(1000)

    # -------------------------------------------------------------------------
    # Pagination
    # -------------------------------------------------------------------------

    def get_pagination_results_text(self):
        try:
            return self.page.locator(self.PAGINATION_RESULTS_TEXT).first.inner_text().strip()
        except Exception:
            return ""

    def is_previous_page_disabled(self):
        # UNCONFIRMED / likely wrong -- PREV_PAGE_DISABLED assumes Laravel's
        # default pagination markup (a disabled "<< Previous" <span>), but a
        # real live check of this page's pagination showed only numbered
        # gotoPage(N, ...) buttons (aria-label="Go to page N") -- no
        # Previous/Next-labeled control anywhere. This was never confirmed
        # from a real DOM capture in the first place (see this class's own
        # docstring point 11: "no ENABLED Previous wire:click method name
        # was ever captured"), so PREV_PAGE_DISABLED was built by pattern
        # convention, not evidence. Left in place rather than deleted so a
        # future capture of the real "on page 1" marker (if one exists) has
        # somewhere to go -- do not trust this method's return value until
        # that happens. See test_bonus_pagination_previous_disabled_on_first_page
        # in the paired test file, which now skips instead of asserting on it.
        return self.is_element_present(self.PREV_PAGE_DISABLED, timeout=3000)

    def click_next_page(self):
        try:
            self._js_click(self.NEXT_PAGE_BTN, timeout=10000)
            self.page.wait_for_timeout(2000)
            return True
        except Exception:
            return False

    def goto_page(self, page_num):
        """Confirmed for pages 2-10, 260, 261 at capture time; other
        values of N are the identical templated button, just a different
        N (see class docstring point 11)."""
        try:
            locator = self.GOTO_PAGE_BTN_TEMPLATE.format(page=page_num)
            self._js_click(locator, timeout=10000)
            self.page.wait_for_timeout(2000)
            return True
        except Exception:
            return False

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
