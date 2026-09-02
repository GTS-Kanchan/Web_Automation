"""
RCS Campaign Page Object
Covers: list page (TC001–TC021) and create flow.
"""
import os
import time

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR


class RCSCampaignPage(BasePage):

    CAMPAIGN_LIST_URL   = "/rcs/campaign"
    CAMPAIGN_CREATE_URL = "/rcs/campaign/create"

    # ── List page ──────────────────────────────────────────────────────────────
    BTN_CREATE          = (
        "xpath=//a[contains(@href,'create')] | //button[contains(.,'Create')]"
        " | //a[contains(.,'Create')]"
    )
    BTN_REFRESH         = (
        "xpath=//button[@*[name()='wire:click' and (contains(.,'refresh') or contains(.,'Refresh'))]]"
        " | //button[.//svg[contains(@class,'refresh') or contains(@class,'arrow')]]"
    )
    INPUT_SEARCH        = (
        "input[type='search'],"
        "input[placeholder*='Search'],"
        "input[placeholder*='search'],"
        "input[placeholder*='Campaign']"
    )
    NO_RECORDS          = (
        "xpath=//*[contains(text(),'No records') or contains(text(),'no records')"
        " or contains(text(),'No data') or contains(text(),'No campaigns')"
        " or contains(text(),'no campaigns') or contains(text(),'No results')"
        " or contains(text(),'no results') or contains(text(),'Nothing found')"
        " or contains(text(),'There are no') or contains(text(),'there are no')"
        " or contains(text(),'Not found') or contains(text(),'0 campaigns')"
        " or contains(text(),'No matching')]"
    )
    TABLE_ROWS          = (
        "xpath=//table//tbody//tr | //div[contains(@class,'table')]//div[contains(@class,'row')]"
    )

    # Filter locators (standard Livewire table filter structure)
    BTN_FILTER               = "xpath=//button[contains(.,'Filter') or @*[name()='wire:click' and contains(.,'filter')]]"
    SELECT_FILTER_DEPARTMENT = "#rcs_campaigns-filter-department"
    SELECT_FILTER_USER       = "#rcs_campaigns-filter-user"
    # SELECT_FILTER_STATUS is LEGACY/UNCONFIRMED: kept only so nothing
    # importing it breaks. Confirmed live markup (screenshot + DOM dump)
    # shows Status is actually a custom Alpine multiselect -- a "Select
    # status (N)" button opening a checkbox panel (Draft/Scheduled/
    # Running/Paused/Completed/Cancelled/Failed) -- NOT a native
    # <select>, so select_option() against this id never matched
    # anything real. Use BTN_STATUS_FILTER + set_status_filter() below.
    SELECT_FILTER_STATUS     = "#rcs_campaigns-filter-status"
    INPUT_FILTER_TEMPLATE_NAME = "#rcs_campaigns-filter-template_name"

    # ── Confirmed live markup: Status/Agent custom multiselects ─────────────
    # Both use the same "Select <thing> (N)" trigger button + a
    # dropdown panel of <label><input type=checkbox><span x-text=
    # "option.name"></span></label> rows (Alpine x-show/x-for). Status's
    # exact option list (Draft/Scheduled/Running/Paused/Completed/
    # Cancelled/Failed) was confirmed directly; Agent's option markup
    # was not independently captured, only its trigger button + the
    # shared widget pattern, so Agent selection is best-effort.
    BTN_STATUS_FILTER = "xpath=//button[contains(normalize-space(.),'Select status')]"
    BTN_AGENT_FILTER   = "xpath=//button[contains(normalize-space(.),'Select agent')]"

    # ── Type / Created From / Created To -- labels confirmed via
    # screenshot; located by label-proximity since their exact id/name
    # attributes were not independently captured in a DOM dump.
    SELECT_FILTER_TYPE        = "xpath=//label[normalize-space(.)='Type']/following::select[1]"
    INPUT_FILTER_CREATED_FROM = "xpath=//label[normalize-space(.)='Created From']/following::input[1]"
    INPUT_FILTER_CREATED_TO   = "xpath=//label[normalize-space(.)='Created To']/following::input[1]"

    # Bulk action / export / columns
    BTN_BULK_ACTION     = "xpath=//button[contains(.,'Bulk Action') or contains(.,'Actions')]"
    BTN_EXPORT          = "xpath=//button[contains(.,'Export')] | //a[contains(.,'Export')]"
    BTN_COLUMNS         = "xpath=//button[contains(.,'Columns')]"
    COLUMN_CHECKBOX     = "xpath=(//input[@type='checkbox'])[2]"

    # Per page
    SELECT_PER_PAGE     = "xpath=//select[@*[name()='wire:model' and (contains(.,'perPage') or contains(.,'per_page'))]]"

    # ── Pagination -- confirmed live markup ─────────────────────────────────
    # <button wire:click="gotoPage(N, 'rcs_campaignsPage')"
    #   aria-label="Go to page N">N</button>
    PAGE_NUMBER_BTN_TMPL = "xpath=//button[@aria-label='Go to page {n}']"

    # ── Create page ────────────────────────────────────────────────────────────
    INPUT_CAMPAIGN_NAME = (
        "xpath=//input["
        "@*[name()='wire:model'       and (contains(.,'campaign_name') or contains(.,'campaign'))] or "
        "@*[name()='wire:model.live'  and (contains(.,'campaign_name') or contains(.,'campaign'))] or "
        "@*[name()='wire:model.defer' and (contains(.,'campaign_name') or contains(.,'campaign'))] or "
        "@id='campaign_name' or @name='campaign_name' or "
        "contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'campaign name')"
        "]"
    )

    # ── Actions ────────────────────────────────────────────────────────────────

    def load_campaign_list(self):
        """Navigate to the RCS Campaigns list page."""
        self.open(self.CAMPAIGN_LIST_URL)
        self.wait_for_spinner_to_disappear()
        self.page.wait_for_timeout(1000)

    def wait_for_spinner_to_disappear(self):
        """Wait for any loading spinner to disappear."""
        try:
            self.page.locator(".spinner, .loading, [wire\\:loading]").first.wait_for(
                state="hidden", timeout=5000)
        except Exception:
            pass
        self.page.wait_for_timeout(500)

    def search_campaign(self, term: str):
        """Search the Livewire table."""
        self.wait_for_spinner_to_disappear()
        inp = self.h.wait_for_element_visible(self.INPUT_SEARCH)
        inp.fill(term)
        self.page.wait_for_timeout(1000)
        self.wait_for_spinner_to_disappear()
        self.page.wait_for_timeout(1000)

    def get_table_rows(self):
        """Return the list of current rows (ignoring 'No records' placeholder)."""
        self.wait_for_spinner_to_disappear()
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            count = rows.count()
            if count == 1 and rows.first.locator(self.NO_RECORDS).count() > 0:
                return []
            return [rows.nth(i) for i in range(count)]
        except Exception:
            return []

    def set_per_page(self, limit: str):
        """Set the items-per-page dropdown."""
        self.wait_for_spinner_to_disappear()
        self.h.select_option(self.SELECT_PER_PAGE, value=str(limit))
        self.wait_for_spinner_to_disappear()
        self.page.wait_for_timeout(1000)

    def open_filters(self):
        """Click the filter button to reveal the filter dropdown/panel."""
        self.wait_for_spinner_to_disappear()
        btn = self.h.wait_for_element_visible(self.BTN_FILTER)
        if btn.get_attribute("aria-expanded") != "true":
            btn.click()
            self.page.wait_for_timeout(500)

    def _select_multiselect_checkbox(self, trigger_locator, label):
        """Shared helper for the confirmed 'Select <thing> (N)' Alpine
        multiselect widget (Status/Agent): click the trigger button to
        open its checkbox panel, then check the row whose <span x-text=
        "option.name"> text equals *label* exactly."""
        try:
            btn = self.h.wait_for_element_clickable(trigger_locator, timeout=8000)
            btn.click()
            self.page.wait_for_timeout(500)
        except Exception:
            return False
        try:
            cb_xpath = (
                f"xpath=//label[.//span[normalize-space(text())='{label}']]"
                f"//input[@type='checkbox']"
            )
            cb = self.page.locator(cb_xpath).first
            cb.wait_for(state="visible", timeout=5000)
            if not cb.is_checked():
                cb.click(force=True)
            self.page.wait_for_timeout(300)
            try:
                # Close the panel so it doesn't obscure subsequent actions.
                self.page.keyboard.press("Escape")
            except Exception:
                pass
            self.wait_for_spinner_to_disappear()
            self.page.wait_for_timeout(800)
            return True
        except Exception:
            return False

    def set_status_filter(self, status: str):
        """Filter by status. Confirmed live markup: Status is a custom
        Alpine multiselect ('Select status (N)' button + a checkbox
        panel listing Draft/Scheduled/Running/Paused/Completed/
        Cancelled/Failed) -- NOT the native <select> this method
        previously assumed (SELECT_FILTER_STATUS/select_option() never
        matched anything real against the live app)."""
        return self._select_multiselect_checkbox(self.BTN_STATUS_FILTER, status)

    def set_agent_filter(self, agent_name: str):
        """Filter by agent, using the same confirmed 'Select agent (N)'
        multiselect pattern as Status. Best-effort: the option markup
        for a specific agent name was not independently confirmed the
        way Status's exact option list was, only the shared widget
        pattern and the trigger button."""
        return self._select_multiselect_checkbox(self.BTN_AGENT_FILTER, agent_name)

    def set_type_filter(self, label: str):
        """Filter by campaign Type. Best-effort: located via
        label-proximity (the 'Type' <label> immediately preceding its
        <select>, confirmed only via screenshot, not a captured DOM
        dump)."""
        try:
            self.h.select_option(self.SELECT_FILTER_TYPE, label=label)
            self.wait_for_spinner_to_disappear()
            self.page.wait_for_timeout(800)
            return True
        except Exception:
            return False

    def set_created_date_range(self, from_date: str, to_date: str):
        """Set the Created From / Created To date filters ('YYYY-MM-DD').
        Best-effort: located via label-proximity, confirmed only via
        screenshot (labels + dd-mm-yyyy placeholder), not a captured DOM
        dump of the actual input elements."""
        ok = True
        try:
            self.page.locator(self.INPUT_FILTER_CREATED_FROM).first.fill(from_date)
        except Exception:
            ok = False
        try:
            self.page.locator(self.INPUT_FILTER_CREATED_TO).first.fill(to_date)
        except Exception:
            ok = False
        self.wait_for_spinner_to_disappear()
        self.page.wait_for_timeout(800)
        return ok

    def is_page_number_button_present(self, page_number, timeout=5000):
        """Confirmed live markup: numbered pagination buttons via
        wire:click="gotoPage(N, 'rcs_campaignsPage')",
        aria-label='Go to page N'."""
        return self.is_element_present(
            self.PAGE_NUMBER_BTN_TMPL.format(n=page_number), timeout=timeout
        )

    def go_to_page(self, page_number):
        """Click the confirmed numbered pagination button for
        *page_number*."""
        try:
            btn = self.page.locator(self.PAGE_NUMBER_BTN_TMPL.format(n=page_number)).first
            btn.wait_for(state="visible", timeout=5000)
            btn.scroll_into_view_if_needed()
            btn.click()
            self.wait_for_spinner_to_disappear()
            self.page.wait_for_timeout(1000)
            return True
        except Exception:
            return False

    def export_data(self):
        """Click the Export button (no download capture -- kept as-is
        for existing callers). See click_export_csv() for the version
        that captures and saves the download."""
        self.wait_for_spinner_to_disappear()
        self.h.wait_for_element_clickable(self.BTN_EXPORT).click()
        self.page.wait_for_timeout(2000)

    def click_export_csv(self, timeout_ms=30000):
        """Clicks Export, capturing the resulting download via
        page.expect_download() -- ported from the confirmed pattern
        already used by RcsMessagePage.click_export() and
        sms_campaign_report_page.py's click_export_csv(). NOTE: despite
        the button being labeled "Export CSV", a confirmed live download
        showed the actual file is an .xlsx ("Table Export.xlsx") -- so
        header validation must go through utils.file_validator's
        read_file_headers()/validate_file_headers(), which dispatch on
        file extension, not assume a raw .csv.

        Returns {"elapsed_s", "file_path", "file_size"} on success
        (same shape as sms_campaign_report_page.py's click_export_csv()),
        or None on failure (button not found, or no download event
        within timeout_ms)."""
        self.wait_for_spinner_to_disappear()
        try:
            btn = self.h.wait_for_element_clickable(self.BTN_EXPORT, timeout=10000)
            btn.scroll_into_view_if_needed()
            start = time.time()
            with self.page.expect_download(timeout=timeout_ms) as dl_info:
                btn.click()
            download = dl_info.value
            filename = download.suggested_filename or "rcs_campaigns_export.xlsx"
            dest = os.path.join(DOWNLOAD_DIR, filename)
            download.save_as(dest)
            return {
                "elapsed_s": time.time() - start,
                "file_path": dest,
                "file_size": os.path.getsize(dest),
            }
        except Exception:
            return None

    def is_campaign_name_in_list(self, name: str, timeout: int = 10000) -> bool:
        """Return True if *name* appears in the campaign table on this
        list page. Ported from the confirmed SMS reference
        (pages/sms/sms_campaign_page.py.is_campaign_name_in_list()):
        tries the search input first, then falls back to scanning all
        visible table cells so the check is resilient to pagination.
        Added so RCS Campaign create-flow launch tests can verify a
        launched campaign actually persisted, instead of only trusting a
        redirect/toast signal on the create page."""
        try:
            inp = self.page.locator(self.INPUT_SEARCH).first
            inp.wait_for(state="visible", timeout=4000)
            inp.fill(name)
            inp.evaluate(
                "(el) => { el.dispatchEvent(new Event('input', {bubbles:true})); "
                "el.dispatchEvent(new Event('change', {bubbles:true})); }"
            )
            self.page.wait_for_timeout(2000)
        except Exception:
            pass

        deadline = self.page.evaluate("() => Date.now()") + timeout
        while self.page.evaluate("() => Date.now()") < deadline:
            found = self.page.evaluate(
                """(name) => {
                    var cells = document.querySelectorAll('table td, table th');
                    for (var i = 0; i < cells.length; i++) {
                        if (cells[i].offsetParent !== null && cells[i].textContent.includes(name)) return true;
                    }
                    return false;
                }""",
                name,
            )
            if found:
                return True
            self.page.wait_for_timeout(500)
        return False

    def get_status_for_campaign_name(self, name: str, timeout: int = 15000) -> str:
        """Search the list for *name* and return the Status column text
        of the matching row ("" if not found within timeout). Confirmed
        via live testing that the list table has a 'Status' column
        (header `<span>Status</span>`); reading it -- rather than only
        matching on the campaign name -- confirms the matched row is a
        genuine, fully-rendered campaign record (not an empty/loading
        placeholder row that happens to contain the name text)."""
        try:
            inp = self.page.locator(self.INPUT_SEARCH).first
            inp.wait_for(state="visible", timeout=4000)
            inp.fill(name)
            inp.evaluate(
                "(el) => { el.dispatchEvent(new Event('input', {bubbles:true})); "
                "el.dispatchEvent(new Event('change', {bubbles:true})); }"
            )
            self.page.wait_for_timeout(2000)
        except Exception:
            pass

        deadline = self.page.evaluate("() => Date.now()") + timeout
        while self.page.evaluate("() => Date.now()") < deadline:
            self.wait_for_spinner_to_disappear()
            status = self.page.evaluate(
                """(name) => {
                    var table = document.querySelector('table');
                    if (!table) return '';
                    var headerCells = table.querySelectorAll('thead th, thead td');
                    var statusIdx = -1;
                    for (var h = 0; h < headerCells.length; h++) {
                        if (headerCells[h].textContent.trim().toLowerCase() === 'status') { statusIdx = h; break; }
                    }
                    var rows = table.querySelectorAll('tbody tr');
                    for (var i = 0; i < rows.length; i++) {
                        if (rows[i].offsetParent === null || !rows[i].textContent.includes(name)) continue;
                        var cells = rows[i].querySelectorAll('td');
                        if (statusIdx >= 0 && cells[statusIdx]) return cells[statusIdx].textContent.trim();
                        return '';
                    }
                    return null;
                }""",
                name,
            )
            if status:
                return status
            if status == "":
                # Row matched but no Status column/index found -- stop polling,
                # this won't resolve by waiting longer.
                return ""
            self.page.wait_for_timeout(500)
        return ""

    def count_campaign_name_occurrences(self, name: str, timeout: int = 15000) -> int:
        """Search the list for *name* and return how many table rows
        actually contain it -- a stronger check than
        is_campaign_name_in_list()'s boolean presence test. Added for
        TC147 (double-submit): searching narrows the Livewire table down
        to just rows matching this (already-unique, per-test) name, so a
        row count of 1 confirms a single persisted campaign, while a
        count of 2+ would confirm the double-submit actually created a
        duplicate. Uses the same search-input-then-poll approach as
        is_campaign_name_in_list() for consistency."""
        try:
            inp = self.page.locator(self.INPUT_SEARCH).first
            inp.wait_for(state="visible", timeout=4000)
            inp.fill(name)
            inp.evaluate(
                "(el) => { el.dispatchEvent(new Event('input', {bubbles:true})); "
                "el.dispatchEvent(new Event('change', {bubbles:true})); }"
            )
            self.page.wait_for_timeout(2000)
        except Exception:
            pass

        deadline = self.page.evaluate("() => Date.now()") + timeout
        last_count = 0
        while self.page.evaluate("() => Date.now()") < deadline:
            self.wait_for_spinner_to_disappear()
            count = self.page.evaluate(
                """(name) => {
                    var rows = document.querySelectorAll('table tbody tr');
                    var n = 0;
                    for (var i = 0; i < rows.length; i++) {
                        if (rows[i].offsetParent !== null && rows[i].textContent.includes(name)) n++;
                    }
                    return n;
                }""",
                name,
            )
            last_count = count
            if count > 0:
                return count
            self.page.wait_for_timeout(500)
        return last_count
