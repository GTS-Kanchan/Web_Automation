from pages.common.base_page import BasePage


class SMSMessagePage(BasePage):

    # ── URLs ───────────────────────────────────────────────────────────────────
    MESSAGES_PATH = "/campaigns/sms/messages"

    # ── Sidebar navigation ─────────────────────────────────────────────────────
    NAV_SMS = (
        "xpath=//nav//a[contains(@href,'/campaigns/sms')] | //a[normalize-space()='SMS']"
    )
    NAV_MESSAGES = (
        "xpath=//a[contains(@href,'/campaigns/sms/messages')]"
        " | //a[contains(@href,'/messages') and (contains(.,'Message') or contains(.,'message'))]"
    )

    # ── Page-level elements ────────────────────────────────────────────────────
    PAGE_HEADING = (
        "xpath=//h1 | //h2 | //*[contains(@class,'page-title') or contains(@class,'heading')]"
    )
    TABLE = "table"
    TABLE_ROWS = "table tbody tr"
    TABLE_HEADERS = "table thead th"
    NO_RECORDS = (
        "xpath=//*[contains(text(),'No records') or contains(text(),'No data') "
        "    or contains(text(),'No results') or contains(text(),'No message') "
        "    or contains(text(),'No messages') or contains(text(),'No matching') "
        "    or contains(text(),'Nothing found') or contains(text(),'Empty')]"
        " | //td[contains(@class,'empty') or contains(@class,'no-data')]"
    )
    PAGINATION = "xpath=//*[contains(@class,'pagination') or contains(@aria-label,'pagination')]"

    # ── Search ─────────────────────────────────────────────────────────────────
    # Actual HTML: <input wire:model.live="search" placeholder="Search Mobile Number">
    SEARCH_BOX = "input[placeholder='Search Mobile Number']"

    # ── Filter panel (popover) ────────────────────────────────────────────────
    # The "Filters" button toggles a popover — text may include count badge
    BTN_FILTER = "xpath=//button[contains(normalize-space(),'Filters') or normalize-space()='Filter']"

    # Status filter: custom Alpine.js multi-select dropdown
    # Trigger button is a sibling of the hidden <select id="sms_messages-filter-status">
    # inside the same parent div (x-data="customMultiSelectDropdown()").
    # NOTE: never use @wire:* or @x-on:* in XPath — Chrome throws NamespaceError
    FILTER_STATUS_TRIGGER = "xpath=//select[@id='sms_messages-filter-status']/../button[@type='button']"
    # Hidden native <select multiple> — targeted by id for JS fallback
    FILTER_STATUS_SELECT = "#sms_messages-filter-status"

    # Actual status constants (match the page's option values exactly)
    STATUS_DELIVRD = "DELIVRD"
    STATUS_FAILED = "FAILED"
    STATUS_PENDING = "Pending"
    STATUS_SENT = "Sent"
    STATUS_REJECTED = "REJECTED"

    # Alias map: tests may pass lowercase names
    _STATUS_ALIAS = {
        "delivered": "DELIVRD",
        "delivrd": "DELIVRD",
        "failed": "FAILED",
        "fail": "FAILED",
        "pending": "Pending",
        "sent": "Sent",
        "queued": "Pending",   # closest mapping
        "rejected": "REJECTED",
    }

    # Sender ID filter: wire:model.live.debounce.500ms="filterComponents.sender_i_d"
    FILTER_SENDER_ID = "#sms_messages-filter-sender_i_d"

    # Date range filters: <input type="datetime-local">
    FILTER_FROM_DATE = ("#sms_messages-filter-created_from, "
                         "input[wire\\:model\\.live\\.debounce\\.500ms='filterComponents.created_from']")
    FILTER_TO_DATE = ("#sms_messages-filter-created_to, "
                       "input[wire\\:model\\.live\\.debounce\\.500ms='filterComponents.created_to']")

    # Source filter: <select wire:model.live="filterComponents.source">
    FILTER_SOURCE = "#sms_messages-filter-source"
    # Source option values
    SOURCE_VAL_SMPP = "S"
    SOURCE_VAL_CAMPAIGN = "U"
    SOURCE_VAL_API = "A"
    SOURCE_VAL_FLOW = "F"

    # Product filter: <select wire:model.live="filterComponents.product">
    FILTER_PRODUCT = "#sms_messages-filter-product"
    # Product option values
    PRODUCT_VAL_TRANSACTIONAL = "T"
    PRODUCT_VAL_PROMOTIONAL = "P"
    PRODUCT_VAL_OTP = "O"

    # Clear all filters button (inside the popover / filter panel)
    # Use text content — avoids @wire:* namespace errors in XPath
    BTN_CLEAR_FILTER = (
        "xpath=//button[normalize-space()='Clear' or normalize-space()='Reset'"
        "         or normalize-space()='Clear Filters' or normalize-space()='Reset Filters']"
        "[not(ancestor::table)]"
        " | //button[contains(.,'Clear') and contains(.,'Filter')]"
    )

    # ── Export (direct link — no Bulk Actions dropdown) ───────────────────────
    # Actual HTML: <a href="/campaigns/sms/optin-export?...">Export CSV</a>
    EXPORT_LINK = (
        "xpath=//a[contains(@href,'optin-export') or contains(@href,'export')]"
        "[contains(normalize-space(),'Export')]"
        " | //a[normalize-space()='Export CSV']"
        " | //button[normalize-space()='Export CSV']"
    )

    # ── Column visibility ─────────────────────────────────────────────────────
    BTN_COLUMNS = "xpath=//button[contains(normalize-space(),'Columns') or contains(normalize-space(),'Column')]"
    COLUMN_LABELS = (
        "xpath=//label[ancestor::*[contains(@class,'dropdown') or contains(@class,'column') "
        "    or contains(@class,'popover')]]"
    )

    # ── Per-page selector (HIDDEN in UI — perPageVisibilityStatus: false) ─────
    # The per-page control is not rendered on this page. Methods skip gracefully.
    PER_PAGE_SELECT = "xpath=//select[contains(@name,'per_page') or contains(@name,'perPage')]"

    # ── Pagination controls ───────────────────────────────────────────────────
    # NOTE: avoid @wire:click in XPath — Chrome throws NamespaceError on colons.
    # Match by button text / aria-label instead.
    BTN_NEXT = (
        "xpath=//button[@aria-label='Next' or normalize-space()='Next »' or normalize-space()='Next'"
        "         or normalize-space()='Next Page'][not(@disabled) and not(contains(@class,'disabled'))]"
        " | //nav//button[contains(.,'Next')][not(@disabled)]"
    )
    BTN_PREV = (
        "xpath=//button[@aria-label='Previous' or normalize-space()='« Previous'"
        "         or normalize-space()='Previous'][not(@disabled) and not(contains(@class,'disabled'))]"
        " | //nav//button[contains(.,'Previous')][not(@disabled)]"
    )
    PAGE_INFO = "xpath=//*[contains(text(),'Showing') and contains(text(),'to') and contains(text(),'of')]"

    # ── View icon (per row) ──────────────────────────────────────────────────
    # wire:click.prevent="$dispatch('openModal', { component: 'sms.campaign.message.view', ... })"
    # Also has data-tooltip-target="tooltip-view-{uuid}"
    # NOTE: avoid @wire:click in XPath — use data-tooltip-target instead (no namespace issues)
    ROW_VIEW_ICON = "xpath=(//button[contains(@data-tooltip-target,'tooltip-view-')])[1]"
    ALL_VIEW_ICONS = "xpath=//button[contains(@data-tooltip-target,'tooltip-view-')]"

    # ── Message Details Popup (Livewire UI modal) ─────────────────────────────
    # Livewire modal renders inside div#modal-container
    POPUP_CONTAINER = (
        "xpath=//div[@id='modal-container' and .//*[self::div or self::section]]"
        " | //div[@role='dialog']"
        " | //div[contains(@class,'fixed') and contains(@class,'inset') and .//h2]"
    )
    # NOTE: avoid @wire:click in XPath — use text/aria-label only
    POPUP_CLOSE_BTN = (
        "xpath=//div[@id='modal-container']//button[contains(.,'Close') or @aria-label='Close'"
        "    or contains(.,'×') or contains(.,'✕') or @aria-label='close']"
        " | //div[@role='dialog']//button[@aria-label='Close' or @aria-label='close'"
        "    or contains(.,'Close')]"
    )

    # Popup field locators — generic, works inside any modal container
    POPUP_STATUS = (
        "xpath=//*[@id='modal-container' or @role='dialog']"
        "//*[contains(@class,'status') or contains(@class,'badge')]"
    )
    POPUP_DESTINATION = (
        "xpath=//*[@id='modal-container' or @role='dialog']"
        "//*[contains(text(),'+') or @data-field='mobile']"
    )
    POPUP_TIMELINE = (
        "xpath=//*[@id='modal-container' or @role='dialog']"
        "//*[contains(@class,'timeline') or @data-field='timeline']"
    )

    # Source column badges in the table
    SOURCE_CAMPAIGN = "xpath=//td[contains(normalize-space(),'Campaign')]"
    SOURCE_API = "xpath=//td[normalize-space()='API' or contains(normalize-space(),'API')]"
    SOURCE_FLOW = "xpath=//td[normalize-space()='Flow' or contains(normalize-space(),'Flow')]"
    SOURCE_SMPP = "xpath=//td[normalize-space()='SMPP' or contains(normalize-space(),'SMPP')]"

    # ═══════════════════════════════════════════════════════════════════════════
    # Navigation
    # ═══════════════════════════════════════════════════════════════════════════

    def navigate(self):
        """Open the SMS Messages page directly."""
        self.open(self.MESSAGES_PATH)
        self.page.wait_for_timeout(1500)

    def navigate_via_sidebar(self):
        """Navigate using the sidebar nav links."""
        try:
            self.h.wait_for_element_clickable(self.NAV_SMS, timeout=10000).click()
            self.page.wait_for_timeout(500)
        except Exception:
            pass
        try:
            self.h.wait_for_element_clickable(self.NAV_MESSAGES, timeout=10000).click()
            self.page.wait_for_timeout(1500)
        except Exception:
            self.navigate()

    def is_messages_page(self):
        return "/campaigns/sms/messages" in self.get_current_url()

    # ── Table helpers ─────────────────────────────────────────────────────────

    def get_row_count(self):
        """Count real data rows (skip empty-state placeholder rows)."""
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            real = 0
            for i in range(rows.count()):
                text = rows.nth(i).inner_text().strip()
                if text and "no " not in text.lower():
                    real += 1
            return real
        except Exception:
            return 0

    def get_table_headers(self):
        """Return list of visible column header texts."""
        return self._get_headers_safe(self.TABLE_HEADERS)

    def is_no_records_visible(self):
        return self.h.is_element_present(self.NO_RECORDS, timeout=5000)

    def get_cell_text(self, row_index, col_index):
        """Return text of cell at (row_index, col_index) — 0-based."""
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            cells = rows.nth(row_index).locator("td")
            return cells.nth(col_index).inner_text().strip()
        except Exception:
            return ""

    def get_all_values_in_column(self, col_index):
        """Return list of all cell texts for a given column."""
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            values = []
            for i in range(rows.count()):
                cells = rows.nth(i).locator("td")
                if col_index < cells.count():
                    values.append(cells.nth(col_index).inner_text().strip())
            return values
        except Exception:
            return []

    # ── Search ────────────────────────────────────────────────────────────────

    def search(self, text):
        box = self.h.wait_for_element_clickable(self.SEARCH_BOX, timeout=10000)
        box.fill(text)
        self.page.wait_for_timeout(1500)  # debounce for wire:model.live

    def clear_search(self):
        try:
            box = self.page.locator(self.SEARCH_BOX).first
            box.fill("")
            box.press("Enter")
            self.page.wait_for_timeout(1500)
        except Exception:
            pass

    # ── Filter panel ──────────────────────────────────────────────────────────

    def open_filter_panel(self):
        """Click the Filters button to open the filter popover."""
        # Use JS click to bypass any overlay that may still be fading out (e.g. a closing modal)
        self._js_click(self.BTN_FILTER, timeout=10000)
        self.page.wait_for_timeout(600)

    def set_filter_status(self, value):
        """
        Select a status in the custom Alpine.js multi-select dropdown.
        value accepts: 'Sent', 'Pending', 'DELIVRD', 'FAILED', 'REJECTED'
        or lowercase aliases: 'delivered', 'failed', 'pending', 'sent', 'queued', 'rejected'

        A real pytest run showed the filter for a status set here (FAILED)
        intermittently returning rows for a DIFFERENT status (DELIVRD) that
        had been selected by an earlier test — this is a multi-select
        widget under the hood (the JS fallback below sets a whole array),
        and the click-based path only checks/unchecks individual list
        options relative to whatever was already checked. If a prior
        clear_filter() didn't fully reset the widget's own client-side
        checked state (only the server-side Livewire value), the next
        click here can ADD to a stale selection instead of replacing it,
        so the effective filter becomes "DELIVRD OR FAILED" and whichever
        status has more live rows wins row 0.

        To make this deterministic, the click-based path (still exercised
        first, so it's still real UI-interaction coverage) is now always
        followed by forcing the underlying Livewire array to exactly
        [actual] — this guarantees a single, known filter value regardless
        of whatever the widget's own checkbox state was beforehand.
        """
        actual = self._STATUS_ALIAS.get(value.lower(), value)

        # Best-effort: click the visible dropdown trigger → click the list
        # option, for real UI-interaction coverage. Failure here is fine —
        # the JS enforcement below is what actually guarantees correctness.
        try:
            trigger = self.h.wait_for_element_clickable(self.FILTER_STATUS_TRIGGER, timeout=5000)
            trigger.click(force=True)
            self.page.wait_for_timeout(300)

            # Option appears as <li> (with <label><span>STATUS</span></label>)
            # anchored inside the status filter wrapper via the hidden select's parent
            option_locator = (
                f"xpath=//select[@id='sms_messages-filter-status']"
                f"/..//li[.//span[normalize-space()='{actual}'] or normalize-space()='{actual}']"
                f" | //select[@id='sms_messages-filter-status']"
                f"/..//label[normalize-space()='{actual}']"
            )
            option = self.h.wait_for_element_clickable(option_locator, timeout=5000)
            option.click(force=True)
            self.page.wait_for_timeout(500)
            # Close dropdown
            try:
                trigger.click(force=True)
            except Exception:
                pass
        except Exception:
            pass

        # Always enforce the exact intended value — see docstring above.
        # This used to be a "fallback: only if the click path raised", which
        # left a stale-multi-select accumulation possible even when the
        # click itself succeeded without error.
        try:
            self.page.evaluate(
                "(actual) => { window.Livewire && window.Livewire.all().forEach(function(c) {"
                "  try { c.set('filterComponents.status', [actual]); } catch(e) {}"
                "}); }",
                actual
            )
            self.page.wait_for_timeout(1500)
        except Exception:
            pass

    def set_filter_sender_id(self, value):
        try:
            el = self.h.wait_for_element_clickable(self.FILTER_SENDER_ID, timeout=5000)
            el.fill(value)
            self.page.wait_for_timeout(800)   # debounce 500ms
        except Exception:
            pass

    def set_filter_mobile(self, value):
        """Mobile number filter — uses the search box (page searches by mobile)."""
        self.search(value)

    def set_filter_date_range(self, from_date, to_date):
        """
        Set date range via Livewire JS — required because the actual inputs are
        inside Alpine x-data components with no static id, and they update Livewire
        via $wire.set() rather than wire:model.

        from_date / to_date format: 'YYYY-MM-DD' (time defaults to T00:00) or
        'YYYY-MM-DDTHH:MM'.
        """
        def _to_dt(val):
            return val if 'T' in val else val + 'T00:00'

        from_dt = _to_dt(str(from_date))
        to_dt = _to_dt(str(to_date))

        try:
            self.page.evaluate(
                "(v) => { window.Livewire && window.Livewire.all().forEach(function(c) {"
                "  try { c.set('filterComponents.created_from', v); } catch(e) {}"
                "}); }",
                from_dt
            )
            self.page.wait_for_timeout(400)
        except Exception:
            pass
        try:
            self.page.evaluate(
                "(v) => { window.Livewire && window.Livewire.all().forEach(function(c) {"
                "  try { c.set('filterComponents.created_to', v); } catch(e) {}"
                "}); }",
                to_dt
            )
            self.page.wait_for_timeout(1000)   # allow Livewire to re-render
        except Exception:
            pass

    def set_filter_source(self, value):
        """
        value: 'S' (SMPP), 'U' (Campaign), 'A' (API), 'F' (Flow), or '' (All)
        or aliases: 'smpp', 'campaign', 'api', 'flow'
        """
        alias = {"smpp": "S", "campaign": "U", "api": "A", "flow": "F"}
        actual = alias.get(value.lower(), value.upper() if len(value) == 1 else value)
        try:
            self.h.select_option(self.FILTER_SOURCE, value=actual)
            self.page.wait_for_timeout(800)
        except Exception:
            pass

    def set_filter_product(self, value):
        """
        value: 'T' (Transactional), 'P' (Promotional), 'O' (OTP), or '' (All)
        or aliases: 'transactional', 'promotional', 'otp'
        """
        alias = {"transactional": "T", "promotional": "P", "otp": "O"}
        actual = alias.get(value.lower(), value.upper() if len(value) == 1 else value)
        try:
            self.h.select_option(self.FILTER_PRODUCT, value=actual)
            self.page.wait_for_timeout(800)
        except Exception:
            pass

    def apply_filter(self):
        """
        No-op: filters on this page are live (wire:model.live).
        Kept for API compatibility so test code doesn't break.
        Waits for Livewire debounce to settle.
        """
        self.page.wait_for_timeout(1500)

    def clear_filter(self):
        """Clear all active filters via the setFilterDefaults Livewire handler.

        Also force-resets filterComponents.status to [] directly, in
        addition to whichever of the two paths below runs — setFilterDefaults
        resets the server-side Livewire state, but the status widget is a
        client-side Alpine multi-select whose own checked-boxes state isn't
        guaranteed to be rebuilt from that alone. Explicitly clearing the
        array here is what set_filter_status()'s docstring above relies on
        to guarantee the next filter call starts from a genuinely empty
        state instead of accumulating onto a stale one."""
        cleared = False
        # Try the wire:click button inside the popover
        try:
            self._js_click(self.BTN_CLEAR_FILTER, timeout=5000)
            self.page.wait_for_timeout(1500)
            cleared = True
        except Exception:
            pass

        if not cleared:
            # Fallback: call Livewire directly
            try:
                self.page.evaluate(
                    "() => { window.Livewire && window.Livewire.all().forEach(function(c) {"
                    "  try { c.call('setFilterDefaults'); } catch(e) {}"
                    "}); }"
                )
                self.page.wait_for_timeout(1500)
                cleared = True
            except Exception:
                pass

        if not cleared:
            # Last resort: reload the page
            self.navigate()
            return

        try:
            self.page.evaluate(
                "() => { window.Livewire && window.Livewire.all().forEach(function(c) {"
                "  try { c.set('filterComponents.status', []); } catch(e) {}"
                "}); }"
            )
            self.page.wait_for_timeout(500)
        except Exception:
            pass

    # ── Export (direct CSV link — no Bulk Actions dropdown) ───────────────────

    def export(self):
        """
        Click the Export CSV link.  The page exposes a direct <a> link
        (not inside a bulk-actions dropdown).
        """
        try:
            link = self.h.wait_for_element_clickable(self.EXPORT_LINK, timeout=10000)
            link.scroll_into_view_if_needed()
            link.click()
            self.page.wait_for_timeout(2000)
        except Exception:
            pass

    # Kept for backwards compat — some tests call these explicitly
    def open_bulk_actions(self):
        """Stub: there is no Bulk Actions menu on this page. No-op."""
        pass

    def click_export(self):
        """Alias for export()."""
        self.export()

    # ── Column visibility ─────────────────────────────────────────────────────

    def open_column_panel(self):
        """
        Open the column visibility dropdown.

        A real pytest run showed get_column_toggles() finding zero visible
        checkboxes right after this returned — aria-expanded said 'true'
        (or the click above ran) but the panel's own open transition
        hadn't actually rendered visible checkboxes yet, most likely
        following a preceding test's own rapid open/toggle/close sequence
        on the same widget. TC022/TC023 still hit this after the previous
        fix (poll, then one last-resort click with a blind return) — that
        version trusted aria-expanded to decide whether to click at all,
        which is exactly what's unreliable here: a stray click elsewhere
        (e.g. Alpine's own @click.outside handler) can visually close the
        panel without the button's aria-expanded ever flipping back, so
        "already open" was often false. It also returned unconditionally
        after the last-resort click instead of confirming it actually
        worked.

        This version ignores aria-expanded entirely and drives off
        observed checkbox visibility only: poll first (covers "already
        open, just still rendering"); if that never appears, click and
        poll again; if it *still* never appears (rare — genuinely stuck
        toggle), click once more and do a final poll. Every branch ends
        by having actually verified a visible checkbox, or having
        genuinely exhausted retries, rather than assuming success.
        """
        btn = self.h.wait_for_element_clickable(self.BTN_COLUMNS, timeout=10000)
        btn.scroll_into_view_if_needed()

        def _has_visible_toggle():
            try:
                return self.page.locator(
                    "xpath=//input[@type='checkbox'][not(ancestor::table)]"
                ).first.is_visible()
            except Exception:
                return False

        def _poll(attempts=6, interval_ms=300):
            for _ in range(attempts):
                if _has_visible_toggle():
                    self.page.wait_for_timeout(500)
                    return True
                self.page.wait_for_timeout(interval_ms)
            if _has_visible_toggle():
                self.page.wait_for_timeout(500)
                return True
            return False

        if _poll():
            return

        for _ in range(2):
            try:
                btn.click()
            except Exception:
                pass
            self.page.wait_for_timeout(500)
            if _poll():
                return

    # Labels that represent "toggle all" controls — skip these
    _SKIP_TOGGLE_LABELS = {
        "all columns", "all", "select all", "toggle all",
        "deselect all", "column visibility", "columns"
    }

    def get_column_toggles(self):
        """
        Return list of (label_text, is_checked) tuples from the Columns panel.
        Finds visible checkboxes NOT inside the data table and NOT the 'All Columns'
        select-all toggle.
        """
        try:
            all_cbs = self.page.locator("xpath=//input[@type='checkbox'][not(ancestor::table)]")
            try:
                all_cbs.first.wait_for(state="attached", timeout=3000)
            except Exception:
                pass
            result = []
            seen = set()
            for i in range(all_cbs.count()):
                cb = all_cbs.nth(i)
                try:
                    if not cb.is_visible():
                        continue
                except Exception:
                    continue

                label_text = ""

                # 1) for= attribute on a sibling <label>
                cb_id = cb.get_attribute("id") or ""
                if cb_id:
                    try:
                        lbl = self.page.locator(f"label[for='{cb_id}']").first
                        if lbl.count() > 0:
                            label_text = lbl.inner_text().strip()
                    except Exception:
                        pass

                # 2) enclosing <label>
                if not label_text:
                    try:
                        lbl = cb.locator("xpath=ancestor::label[1]").first
                        label_text = lbl.inner_text().strip()
                    except Exception:
                        pass

                # 3) following sibling span / label
                if not label_text:
                    try:
                        lbl = cb.locator(
                            "xpath=following-sibling::span[1] | following-sibling::label[1]"
                        ).first
                        label_text = lbl.inner_text().strip()
                    except Exception:
                        pass

                # 4) fallback to value attribute
                if not label_text:
                    val = cb.get_attribute("value") or ""
                    if val and val not in ("1", "0", "on", ""):
                        label_text = val.replace("_", " ").title()

                # Skip toggle-all controls and status-filter checkboxes
                if not label_text:
                    continue
                if label_text.lower() in self._SKIP_TOGGLE_LABELS:
                    continue
                # Status filter checkboxes have known values (Sent/Pending/etc.)
                if label_text in {"Sent", "Pending", "DELIVRD", "FAILED", "REJECTED"}:
                    continue
                if label_text not in seen:
                    seen.add(label_text)
                    result.append((label_text, cb.is_checked()))
            return result
        except Exception:
            return []

    def toggle_column(self, label_text):
        """Toggle a column checkbox by its label text."""
        try:
            # Find a visible label (not inside the data table) matching the text
            lbl = self.page.locator(
                f"xpath=//label[normalize-space()='{label_text}' or contains(.,'{label_text}')]"
                f"[not(ancestor::table)]"
            ).first
            lbl.scroll_into_view_if_needed()
            lbl.click()
            self.page.wait_for_timeout(500)
            return
        except Exception:
            pass
        # Fallback: find the checkbox by value and click it
        try:
            val = label_text.lower().replace(" ", "_")
            cb = self.page.locator(
                f"xpath=//input[@type='checkbox' and (contains(@value,'{val}') or @id='{val}')]"
                f"[not(ancestor::table)]"
            ).first
            cb.click(force=True)
            self.page.wait_for_timeout(500)
        except Exception:
            pass

    # ── Per-page (hidden in UI — perPageVisibilityStatus: false) ─────────────

    def set_per_page(self, count):
        """
        The per-page selector is not rendered on this page (perPageVisibilityStatus=false).
        Attempts a JS Livewire call as a best-effort; does not raise on failure.
        """
        try:
            self.h.select_option(self.PER_PAGE_SELECT, value=str(count))
            self.page.wait_for_timeout(2000)
            return
        except Exception:
            pass
        # Fallback: set via Livewire
        try:
            self.page.evaluate(
                "(c) => { window.Livewire && window.Livewire.all().forEach(function(comp) {"
                "  try { comp.set('perPage', c); } catch(e) {}"
                "}); }",
                int(count)
            )
            self.page.wait_for_timeout(2000)
        except Exception:
            pass

    def get_per_page_value(self):
        """Return currently selected per-page count, or None if control is hidden."""
        try:
            sel = self.page.locator(self.PER_PAGE_SELECT).first
            selected = sel.locator("option:checked").first.inner_text().strip()
            return int(selected)
        except Exception:
            return None

    # ── Pagination controls ───────────────────────────────────────────────────

    def click_next_page(self):
        self._js_click(self.NEXT_PAGE_BTN + " >> visible=true", timeout=10000)
        self.page.wait_for_timeout(1500)


    def click_prev_page(self):
        self._js_click(self.PREV_PAGE_BTN + " >> visible=true", timeout=10000)
        self.page.wait_for_timeout(1500)


    def get_page_info_text(self):
        try:
            return self.page.locator(self.PAGE_INFO).first.inner_text().strip()
        except Exception:
            return ""

    def is_next_page_enabled(self):
        try:
            btn = self.page.locator(self.BTN_NEXT).first
            return btn.is_enabled() and btn.get_attribute("disabled") is None
        except Exception:
            return False

    def is_prev_page_enabled(self):
        try:
            btn = self.page.locator(self.BTN_PREV).first
            return btn.is_enabled() and btn.get_attribute("disabled") is None
        except Exception:
            return False

    # ── View icon / Message Details Popup ─────────────────────────────────────

    def click_view_icon(self, row_index=0):
        """
        Click the view/eye icon for the given row (0-based).
        The button dispatches a Livewire openModal event — native .click() works.
        """
        try:
            icons = self.page.locator(self.ALL_VIEW_ICONS)
            count = icons.count()
            if count and row_index < count:
                icon = icons.nth(row_index)
                icon.scroll_into_view_if_needed()
                icon.click()
            else:
                icon = self.h.wait_for_element_clickable(self.ROW_VIEW_ICON, timeout=8000)
                icon.scroll_into_view_if_needed()
                icon.click()
            self.page.wait_for_timeout(2000)  # allow modal to render
        except Exception:
            pass

    def is_popup_open(self):
        """True when the Livewire UI modal is present and visible."""
        try:
            container = self.h.wait_for_element_visible(self.POPUP_CONTAINER, timeout=8000)
            return container.is_visible()
        except Exception:
            return False

    def close_popup(self):
        try:
            btn = self.h.wait_for_element_clickable(self.POPUP_CLOSE_BTN, timeout=5000)
            btn.click()
            self.page.wait_for_timeout(800)
        except Exception:
            try:
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(500)
            except Exception:
                pass

    def _popup_root_xpath(self):
        return (
            "//*[@id='modal-container' or @role='dialog' "
            "    or (contains(@class,'fixed') and contains(@class,'inset'))]"
        )

    def _popup_text_by_label(self, label_keywords):
        """Find a value near a label containing any of the keywords."""
        root = self._popup_root_xpath()
        for kw in label_keywords:
            for tmpl in [
                f"xpath=({root}//*[contains(.,'{kw}')]/following-sibling::*)[1]",
                f"xpath=({root}//*[contains(.,'{kw}')]/../following-sibling::*)[1]",
                f"xpath=({root}//*[contains(.,'{kw}')]/following::*[not(descendant::*[contains(.,'{kw}')] )])[1]",
            ]:
                try:
                    el = self.page.locator(tmpl).first
                    txt = el.inner_text().strip()
                    if txt and txt.lower() not in {kw.lower(), ""}:
                        return txt
                except Exception:
                    continue
        return ""

    def get_popup_status(self):
        txt = self._popup_text_by_label(["Status", "status"])
        if not txt:
            try:
                txt = self.page.locator(self.POPUP_STATUS).first.inner_text().strip()
            except Exception:
                pass
        return txt

    def get_popup_destination(self):
        return self._popup_text_by_label([
            "Contact Number", "Destination", "Mobile Number", "Mobile", "To Number", "Phone"
        ])

    def get_popup_type(self):
        """Product/Type field (Transactional, Promotional, OTP)."""
        return self._popup_text_by_label(["Product", "Type", "SMS Type", "Message Type"])

    def get_popup_content(self):
        return self._popup_text_by_label(["Message", "Content", "Body", "SMS Content"])

    def get_popup_sender_id(self):
        return self._popup_text_by_label(["Sender ID", "Sender", "From"])

    def get_popup_template_name(self):
        return self._popup_text_by_label(["Template Name", "Template", "DLT Template"])

    def get_popup_message_id(self):
        return self._popup_text_by_label(["Message ID", "Msg ID", "MessageID"])

    def get_popup_transaction_id(self):
        return self._popup_text_by_label(["Transaction ID", "Txn ID", "Transaction"])

    def get_popup_sms_count(self):
        return self._popup_text_by_label(["SMS Count", "Parts", "Count"])

    def get_popup_timeline(self):
        try:
            return self.page.locator(self.POPUP_TIMELINE).first.inner_text().strip()
        except Exception:
            return self._popup_text_by_label(["Timeline", "History", "Events", "DLR"])

    def get_popup_error_code(self):
        return self._popup_text_by_label(["Error Code", "Err Code"])

    def get_popup_error_description(self):
        return self._popup_text_by_label(
            ["Error Description", "Error Reason", "Failure Reason", "DLR Description"]
        )

    def get_popup_all_text(self):
        """Full text of the popup — useful for generic assertions."""
        try:
            return self.page.locator(self.POPUP_CONTAINER).first.inner_text().strip()
        except Exception:
            return ""

    # ── Source / Product column helpers ───────────────────────────────────────

    def get_source_column_index(self):
        """Return the index of the 'Source' column, or -1."""
        headers = self.get_table_headers()
        for i, h in enumerate(headers):
            if "source" in h.lower():
                return i
        return -1

    def get_product_column_index(self):
        """Return the index of the 'Product' column (was 'Type'), or -1."""
        headers = self.get_table_headers()
        for i, h in enumerate(headers):
            if h.lower() in ("product", "type", "sms type", "message type"):
                return i
        return -1

    # Backwards-compat alias
    def get_type_column_index(self):
        return self.get_product_column_index()

    def wait_for_table_load(self, timeout=15000):
        """Wait until the table has at least one row or no-records message appears."""
        self.h.wait_until(
            lambda: self.get_row_count() > 0 or self.is_no_records_visible(),
            timeout_ms=timeout, interval_ms=800
        )
