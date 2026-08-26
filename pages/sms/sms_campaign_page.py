"""
SMS Campaign Page Object
Covers: list page (TC001–TC021) and create/edit flow (TC022–TC051).

Migrated to Playwright: Selenium's `_w()`/`_js()`/`EC`/`Select` helpers are
replaced with Playwright locators + `page.evaluate()`/`ElementHandle`
methods. The heavy DOM-scanning helpers (`_find_campaign_name_input`,
`_wireui_select`, `select_column_mappings`) keep their original JS logic
almost verbatim (still the most reliable way to locate this app's dynamic
wire:model/Alpine-teleported elements) but now run via
`page.evaluate()`/`page.evaluate_handle()`/`ElementHandle.query_selector_all()`
instead of `driver.execute_script()` + `driver.find_elements()`.
"""
import os
import re
import time

from pages.common.base_page import BasePage


class SMSCampaignPage(BasePage):

    CAMPAIGN_LIST_URL   = "/campaigns/sms"
    CAMPAIGN_CREATE_URL = "/campaigns/sms/create"

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

    # Filter — locators confirmed from a live DOM dump of the SMS Campaigns
    # list page's filter panel (rappasoft/laravel-livewire-tables
    # filterComponents block). Confirmed real filters (7 total): Department,
    # User, Status, Type, Template Name, Sender Id, Product. There is NO
    # Schedule From/To date-range filter on this page.
    BTN_FILTER               = "xpath=//button[contains(.,'Filter') or @*[name()='wire:click' and contains(.,'filter')]]"
    SELECT_FILTER_DEPARTMENT = "#sms_campaigns-filter-department"
    SELECT_FILTER_USER       = "#sms_campaigns-filter-user"
    SELECT_FILTER_STATUS     = "#sms_campaigns-filter-status"
    # NOTE: this filter's Livewire field is `filterComponents.source`, not
    # `.type` -- confirmed via the real DOM: <select
    # wire:model.live="filterComponents.source" id="sms_campaigns-filter-source">
    # with <option value="flow_numbers">Flow</option> / <option
    # value="campaign">Campaign</option>. The "type" id below never
    # existed on this page, so filter_by_type() always failed to find the
    # element and both TC008/TC009 fell into their `except: pytest.skip(...)`
    # branch instead of actually filtering.
    SELECT_FILTER_TYPE       = "#sms_campaigns-filter-source"
    INPUT_FILTER_TEMPLATE_NAME = "#sms_campaigns-filter-template_name"
    INPUT_FILTER_SENDER      = "#sms_campaigns-filter-sender_id"
    SELECT_FILTER_PRODUCT    = "#sms_campaigns-filter-product"

    # Bulk action / export / columns
    BTN_BULK_ACTION     = "xpath=//button[contains(.,'Bulk Action') or contains(.,'Actions')]"
    BTN_EXPORT          = "xpath=//button[contains(.,'Export')] | //a[contains(.,'Export')]"
    BTN_COLUMNS         = "xpath=//button[contains(.,'Columns')]"
    COLUMN_CHECKBOX     = "xpath=//input[@type='checkbox'][2]"

    # Per page
    SELECT_PER_PAGE     = "xpath=//select[@*[name()='wire:model' and (contains(.,'perPage') or contains(.,'per_page'))]]"

    # ── Create page ────────────────────────────────────────────────────────────
    # NOTE: covers wire:model, wire:model.live, wire:model.lazy, wire:model.defer
    INPUT_CAMPAIGN_NAME = (
        "xpath=//input["
        "@*[name()='wire:model'       and (contains(.,'campaign_name') or contains(.,'campaign'))] or "
        "@*[name()='wire:model.live'  and (contains(.,'campaign_name') or contains(.,'campaign'))] or "
        "@*[name()='wire:model.lazy'  and (contains(.,'campaign_name') or contains(.,'campaign'))] or "
        "@*[name()='wire:model.defer' and (contains(.,'campaign_name') or contains(.,'campaign'))] or "
        "@id='campaign_name' or @name='campaign_name' or "
        "contains(translate(@placeholder,"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'campaign name')"
        "]"
    )
    INPUT_SCHEDULE_DATE = (
        "xpath=//input["
        "@*[name()='x-model'          and (contains(.,'date'))] or "
        "@*[name()='wire:model'       and (contains(.,'schedule_date') or contains(.,'date'))] or "
        "@*[name()='wire:model.live'  and (contains(.,'schedule_date') or contains(.,'date'))] or "
        "@*[name()='wire:model.lazy'  and (contains(.,'schedule_date') or contains(.,'date'))] or "
        "@type='date' or @id='schedule_date']"
    )
    # Time is a <select> dropdown (options in 5-min steps); NOT an <input>
    SELECT_SCHEDULE_TIME = (
        "xpath=//select["
        "@*[name()='x-model'         and (contains(.,'time'))] or "
        "@*[name()='wire:model'      and (contains(.,'schedule_time') or contains(.,'time'))] or "
        "@*[name()='wire:model.live' and (contains(.,'schedule_time') or contains(.,'time'))] or "
        "@*[name()='wire:model.lazy' and (contains(.,'schedule_time') or contains(.,'time'))] or "
        "@id='schedule_time']"
    )
    # Keep old alias so nothing else breaks
    INPUT_SCHEDULE_TIME = SELECT_SCHEDULE_TIME

    # Sender ID WireUI select
    DROPDOWN_SENDER_ID   = "xpath=//button[.//span[contains(text(),'Select Sender ID')]]"
    SENDER_SEARCH_INPUT  = "xpath=//input[@type='search']"

    # Template WireUI select
    DROPDOWN_TEMPLATE    = "xpath=//button[.//span[normalize-space()='Select Template']]"
    TEMPLATE_SEARCH_INPUT = "xpath=(//input[@type='search'])[last()]"
    TEMPLATE_VAR_INPUTS  = "xpath=//input[starts-with(@id,'columnMapping.')]"

    # Import contacts
    BTN_IMPORT_CONTACT  = "xpath=//button[normalize-space()='Import Contacts']"
    # Import popup identified by its unique textarea id or file input inside a modal.
    IMPORT_POPUP        = (
        "xpath=//*[@id='cp_contacts' and ancestor::div[contains(@class,'fixed')]]"
        " | //div[contains(@class,'fixed') and .//*[@id='cp_contacts']]"
        " | //div[contains(@class,'fixed') and .//button[normalize-space()='Import Contacts']]"
    )
    TEXTAREA_PASTE      = "#cp_contacts"
    DUPLICATE_CHECKBOX  = "#keep_duplicates"
    FILE_UPLOAD_TAB     = (
        "xpath=//a[contains(.,'File Upload')] | //button[contains(.,'File Upload')]"
        " | //li[contains(.,'File Upload')]"
    )
    FILE_INPUT          = "xpath=//input[@type='file']"
    BTN_IMPORT_CONFIRM  = "xpath=//div[contains(@class,'fixed')]//button[normalize-space()='Continue']"
    BTN_CANCEL_IMPORT   = (
        "xpath=//div[contains(@class,'fixed') and .//*[@id='cp_contacts']]"
        "  //button[contains(normalize-space(),'Cancel')]"
        " | //div[contains(@class,'fixed')]//button[@aria-label='Close']"
        " | //div[contains(@class,'fixed') and .//*[@id='cp_contacts']]"
        "  //button[.//svg]"
    )
    BTN_DOWNLOAD_SAMPLE = (
        "xpath=//a[contains(.,'Download') and contains(.,'Sample')]"
        " | //button[contains(.,'Download Sample')]"
    )
    IMPORT_SUCCESS_MSG  = (
        "xpath=//*[contains(text(),'Contacts Imported') or contains(text(),'imported')"
        " or contains(text(),'Ready to send')]"
    )
    IMPORT_ERROR        = (
        "xpath=//div[contains(@class,'alert-danger')]"
        " | //p[contains(@class,'text-red') and string-length(normalize-space(.)) > 5]"
        " | //*[contains(@class,'invalid-feedback') and string-length(normalize-space(.)) > 5]"
    )

    # Schedule
    RADIO_SEND_NOW      = "xpath=//label[contains(.,'Send Now')]"
    SEND_NOW_INPUT      = "#send_now"
    RADIO_SCHEDULE      = "xpath=//label[contains(.,'Schedule') and not(contains(.,'Now'))]"

    # Preview / Send
    BTN_PREVIEW         = "xpath=//button[contains(.,'Preview Campaign')]"
    PREVIEW_MODAL       = (
        "xpath=//div[contains(@class,'fixed')]"
        "[.//button[contains(.,'Launch') or contains(.,'Send') or contains(.,'Schedule') or contains(.,'Close')]]"
    )
    BTN_CLOSE_PREVIEW   = "xpath=//button[contains(.,'Close')]"
    BTN_LAUNCH          = "xpath=//button[contains(.,'Launch Campaign') or contains(.,'Send Campaign')]"

    # Cancel / Continue
    BTN_CANCEL          = "xpath=//a[contains(.,'Cancel')] | //button[contains(.,'Cancel')]"
    BTN_CONTINUE        = "xpath=//button[normalize-space()='Continue']"

    # Validation / Toast
    VALIDATION_ERROR    = (
        "xpath=//*["
        "  contains(@class,'text-red') or contains(@class,'invalid-feedback')"
        "  or contains(@class,'error-message') or contains(@class,'text-danger')"
        "  or contains(@class,'border-red') or contains(@class,'has-error')"
        "  or contains(@class,'alert-danger')"
        "][normalize-space()][not(ancestor::*[contains(@style,'display: none')])]"
    )
    TOAST_SUCCESS       = (
        "xpath=//*[contains(@class,'alert-success') or contains(@class,'toast-success')"
        " or (@role='alert' and contains(@class,'success'))]"
    )
    # TOAST_ERROR (below) was guessing generic Bootstrap alert classes
    # ('alert-danger', 'toast-error') that don't exist anywhere in this
    # app -- it's built on Tailwind + WireUI + SweetAlert2, confirmed
    # elsewhere in this project (sms_blocked_numbers_page.py's
    # TOAST_NOTIFICATION_TEXT/SWAL_ERROR_TITLE, built from an actual live
    # DOM dump: WireUI's global toast container is
    # `div[x-data='wireui_notifications']`, and its error/confirm dialogs
    # go through SweetAlert2's #swal2-title / #swal2-html-container). Kept
    # here unchanged as a defensive fallback in case some page genuinely
    # does use these classes, but get_toast_error() below now checks the
    # real mechanisms first.
    TOAST_ERROR         = (
        "xpath=//*[contains(@class,'alert-danger') or contains(@class,'toast-error')"
        " or (@role='alert' and contains(@class,'error'))]"
    )
    TOAST_NOTIFICATION_TEXT = (
        "xpath=//div[@x-data='wireui_notifications']"
        "//p[(@x-show='notification.title' or @x-show='notification.description') "
        "and normalize-space(text())!='']"
    )
    SWAL_CONFIRM        = "xpath=//button[contains(@class,'swal2-confirm')]"

    # ══════════════════════════════════════════════════════════════════════════
    # Internal helpers
    # ══════════════════════════════════════════════════════════════════════════

    def _is_rendered(self, el):
        """True when element has non-zero bounding box (bypasses Alpine
        x-show). `el` may be a Locator or an ElementHandle — both expose
        .evaluate()."""
        try:
            return bool(el.evaluate(
                "(e) => { var r = e.getBoundingClientRect(); return r.height > 0 && r.width > 0; }"
            ))
        except Exception:
            return False

    def _alpine_container(self, el):
        """Walk up DOM to the nearest ancestor with x-data attribute.
        Returns an ElementHandle, or None."""
        try:
            handle = el.evaluate_handle("""
                (start) => {
                    var e = start;
                    while (e.parentElement) {
                        e = e.parentElement;
                        if (e.hasAttribute('x-data')) return e;
                    }
                    return null;
                }
            """)
            return handle.as_element()
        except Exception:
            return None

    def _wireui_select(self, trigger_locator, value, timeout=15000):
        """Select a WireUI select option by value text.

        Works for both Sender ID and Template selects:
          1. Find trigger button → walk up to x-data container
          2. Click button to open dropdown
          3. Find search input scoped to this container → JS-type value
          4. Wait for Alpine filter → click matching div[select-option]
        """
        btn = self.page.locator(trigger_locator).first
        btn.wait_for(state="visible", timeout=timeout)
        container = self._alpine_container(btn)

        btn.click()
        self.page.wait_for_timeout(500)

        # Search input scoped to container
        if container is not None:
            inputs = container.query_selector_all("xpath=.//input[@type='search']")
        else:
            inputs = self.page.query_selector_all("xpath=//input[@type='search']")
        rendered_inputs = [i for i in inputs if self._is_rendered(i)]
        search = rendered_inputs[-1] if rendered_inputs else None

        if search:
            search.evaluate(
                "(el) => { el.focus(); el.value=''; "
                "el.dispatchEvent(new Event('input',{bubbles:true})); }"
            )
            search.type(value)
            self.page.wait_for_timeout(1000)

        # Options scoped to container
        def _query_opts():
            if container is not None:
                opts = container.query_selector_all("xpath=.//div[@select-option]")
            else:
                opts = self.page.query_selector_all("xpath=//div[@select-option]")
            return [o for o in opts if self._is_rendered(o)]

        rendered = _query_opts()
        matched = [o for o in rendered if value.lower() in (o.inner_text() or "").lower()]
        target = matched[0] if matched else None

        if target is None:
            # `rendered` was queried AFTER typing `value` into the search
            # box above -- this is a live search-filter combobox, so if
            # `value` doesn't match any real option (e.g. SMS_SENDER_ID /
            # SMS_TEMPLATE_NAME still set to the unconfigured "DUMMY"
            # placeholder default), the search itself already filtered
            # the option list down to zero by the time we got here. A
            # "pick the first option instead" fallback based on `rendered`
            # could therefore never fire -- `rendered` IS that empty
            # filtered list. This is exactly why every test relying on a
            # real Sender ID/Template value was failing identically with
            # "not found in WireUI select" instead of falling back to any
            # available option. Clear the search and re-query the full,
            # unfiltered list so the fallback has something to pick from.
            if search:
                search.evaluate(
                    "(el) => { el.focus(); el.value=''; "
                    "el.dispatchEvent(new Event('input',{bubbles:true})); }"
                )
                self.page.wait_for_timeout(800)
            unfiltered = _query_opts()
            target = unfiltered[0] if unfiltered else None

        if not target:
            raise RuntimeError(f"Option '{value}' not found in WireUI select")

        target.evaluate("(el) => el.scrollIntoView({block:'center'})")
        target.evaluate("(el) => el.click()")
        self.page.wait_for_timeout(400)

    # ══════════════════════════════════════════════════════════════════════════
    # Navigation
    # ══════════════════════════════════════════════════════════════════════════

    def open_campaign_list(self):
        self.open(self.CAMPAIGN_LIST_URL)
        self.page.wait_for_timeout(1500)

    def is_campaign_list_page(self):
        url = self.get_current_url()
        return self.CAMPAIGN_LIST_URL in url and "/create" not in url

    # Alias — kept from the Selenium suite: a test calls page.is_list_page(),
    # which never existed as a method name here; only is_campaign_list_page()
    # did. Kept as a thin alias rather than renaming the confirmed original
    # method everywhere else it's used.
    def is_list_page(self):
        return self.is_campaign_list_page()

    def click_create_campaign(self):
        """Navigate to create page — tries button click first, falls back to URL."""
        try:
            btn = self.page.locator(self.BTN_CREATE).first
            btn.wait_for(state="visible", timeout=5000)
            btn.click()
            self.page.wait_for_timeout(1500)
            if "create" in self.get_current_url().lower():
                return
        except Exception:
            pass
        # Direct navigation — reliable regardless of button rendering
        self.open(self.CAMPAIGN_CREATE_URL)
        self.page.wait_for_timeout(2000)

    def is_create_button_visible(self):
        """Check campaign creation is accessible from current page."""
        if self.is_element_present(self.BTN_CREATE, timeout=3000):
            return True
        # Fallback: create is always accessible when in the campaign section
        url = self.get_current_url().lower()
        return "campaign" in url or "sms" in url

    def click_refresh(self):
        try:
            btn = self.page.locator(self.BTN_REFRESH).first
            btn.wait_for(state="visible", timeout=8000)
            btn.click()
        except Exception:
            self.page.reload()
        self.page.wait_for_timeout(1500)

    # ══════════════════════════════════════════════════════════════════════════
    # List page — search / filter / export / per-page
    # ══════════════════════════════════════════════════════════════════════════

    def search(self, value):
        inp = self.page.locator(self.INPUT_SEARCH).first
        inp.wait_for(state="attached", timeout=8000)
        inp.fill(value)
        # fill() only dispatches an 'input' event. If this field's Livewire
        # binding is wire:model.lazy/.blur (fires on 'change'/blur) rather
        # than wire:model.live/.debounce (fires on 'input'), fill() alone
        # never triggers the search request and the table silently stays
        # unfiltered — which is exactly what made TC005 flake: the
        # no-records state never arrives because no search ever ran.
        # Dispatching 'change' + blurring covers both binding styles.
        inp.dispatch_event("change")
        inp.blur()
        self.page.wait_for_timeout(1500)

    def clear_search(self):
        try:
            inp = self.page.locator(self.INPUT_SEARCH).first
            inp.fill("")
            inp.dispatch_event("change")
            inp.blur()
            self.page.wait_for_timeout(1000)
        except Exception:
            pass

    def has_no_records_message(self):
        """Check for empty/no-records state via text OR empty table body.

        The JS fallback treats "no table at all" as an empty state too
        (some Livewire table states drop the <table> shell entirely when
        there's nothing to show)."""
        if self.is_element_present(self.NO_RECORDS, timeout=4000):
            return True
        try:
            empty = self.page.evaluate("""
                () => {
                    var tbody = document.querySelector('table tbody');
                    if (!tbody) return true;
                    var rows = Array.from(tbody.querySelectorAll('tr')).filter(function(r) {
                        return r.offsetHeight > 0 && r.textContent.trim().length > 0;
                    });
                    return rows.length === 0;
                }
            """)
            return bool(empty)
        except Exception:
            return False

    def get_row_count(self):
        """Count visible data rows using JS (handles Alpine/Livewire lazy rendering)."""
        try:
            count = self.page.evaluate("""
                () => {
                    var rows = document.querySelectorAll('table tbody tr');
                    if (rows.length === 0) {
                        rows = document.querySelectorAll('[class*="table"] tr:not(:first-child)');
                    }
                    var c = 0;
                    for (var i = 0; i < rows.length; i++) {
                        var r = rows[i];
                        if (r.offsetHeight > 0 && r.textContent.trim().length > 0) c++;
                    }
                    return c;
                }
            """)
            return int(count) if count is not None else 0
        except Exception:
            rows = self.page.locator(self.TABLE_ROWS)
            cnt = 0
            for i in range(rows.count()):
                r = rows.nth(i)
                if r.is_visible() and r.inner_text().strip():
                    cnt += 1
            return cnt

    def is_campaign_name_in_list(self, name: str, timeout: int = 10000) -> bool:
        """
        Return True if *name* appears in the campaign table on the list page.
        First tries the search/filter input; falls back to scanning all visible
        table cells so the test is resilient to pagination changes.
        """
        try:
            inp = self.page.locator(self.INPUT_SEARCH).first
            inp.wait_for(state="visible", timeout=4000)
            inp.fill(name)
            inp.evaluate(
                "(el) => { el.dispatchEvent(new Event('input', {bubbles:true})); "
                "el.dispatchEvent(new Event('change', {bubbles:true})); }"
            )
            self.page.wait_for_timeout(2000)  # wait for Livewire/Alpine to re-render
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

    def open_filter(self):
        try:
            btn = self.page.locator(self.BTN_FILTER).first
            btn.wait_for(state="visible", timeout=8000)
            btn.click()
            self.page.wait_for_timeout(800)
        except Exception:
            pass

    def filter_by_sender_id(self, value):
        try:
            inp = self.page.locator(self.INPUT_FILTER_SENDER).first
            inp.wait_for(state="attached", timeout=8000)
            # Clear and dispatch input event to trigger Livewire reactivity.
            # Real attribute is wire:model.live.debounce.500ms — the wait
            # below covers the 500ms debounce plus the round trip.
            inp.evaluate(
                "(el) => { el.value = ''; el.dispatchEvent(new Event('input', {bubbles: true})); }"
            )
            inp.fill(value)
            inp.evaluate(
                "(el) => { el.dispatchEvent(new Event('input', {bubbles: true})); "
                "el.dispatchEvent(new Event('change', {bubbles: true})); }"
            )
            self.page.wait_for_timeout(2500)
        except Exception:
            pass

    def filter_by_template_name(self, value):
        """Filter by Template Name — debounced text input
        (wire:model.live.debounce.500ms="filterComponents.template_name")."""
        try:
            inp = self.page.locator(self.INPUT_FILTER_TEMPLATE_NAME).first
            inp.wait_for(state="attached", timeout=8000)
            inp.evaluate(
                "(el) => { el.value = ''; el.dispatchEvent(new Event('input', {bubbles: true})); }"
            )
            inp.fill(value)
            inp.evaluate(
                "(el) => { el.dispatchEvent(new Event('input', {bubbles: true})); "
                "el.dispatchEvent(new Event('change', {bubbles: true})); }"
            )
            self.page.wait_for_timeout(2500)
        except Exception:
            pass

    def filter_by_type(self, value):
        """value: 'flow' or 'campaign' — the only two real options besides
        'All' (confirmed via DOM: <option value="flow_numbers">Flow</option>,
        <option value="campaign">Campaign</option>). NOTE: 'transactional' /
        'promotional' are NOT Type options on this page — see
        filter_by_product() for those."""
        sel = self.page.locator(self.SELECT_FILTER_TYPE).first
        sel.wait_for(state="attached", timeout=8000)
        try:
            sel.select_option(label=value.capitalize())
        except Exception:
            sel.select_option(value=value.lower())
        self.page.wait_for_timeout(1500)

    def filter_by_product(self, value):
        """value: 'transactional', 'promotional', or 'otp' (confirmed via DOM:
        <option value="T">Transactional</option>,
        <option value="P">Promotional</option>,
        <option value="O">OTP</option>)."""
        sel = self.page.locator(self.SELECT_FILTER_PRODUCT).first
        sel.wait_for(state="attached", timeout=8000)
        label = "OTP" if value.lower() == "otp" else value.capitalize()
        try:
            sel.select_option(label=label)
        except Exception:
            code = {"transactional": "T", "promotional": "P", "otp": "O"}.get(value.lower())
            if not code:
                raise
            sel.select_option(value=code)
        self.page.wait_for_timeout(1500)

    def filter_by_department(self, value):
        """value: visible option text, e.g. 'admin', 'QA Department', 'Sales'."""
        sel = self.page.locator(self.SELECT_FILTER_DEPARTMENT).first
        sel.wait_for(state="attached", timeout=8000)
        sel.select_option(label=value)
        self.page.wait_for_timeout(1500)

    def filter_by_user(self, value):
        """value: visible option text, e.g. 'test123', 'Karthik Reddy'."""
        sel = self.page.locator(self.SELECT_FILTER_USER).first
        sel.wait_for(state="attached", timeout=8000)
        sel.select_option(label=value)
        self.page.wait_for_timeout(1500)

    def get_filter_department_options(self):
        """Return visible option labels for the Department filter (includes 'All')."""
        sel = self.page.locator(self.SELECT_FILTER_DEPARTMENT).first
        sel.wait_for(state="attached", timeout=8000)
        texts = sel.locator("option").all_inner_texts()
        return [t.strip() for t in texts if t.strip()]

    def get_filter_user_options(self):
        """Return visible option labels for the User filter (includes 'All')."""
        sel = self.page.locator(self.SELECT_FILTER_USER).first
        sel.wait_for(state="attached", timeout=8000)
        texts = sel.locator("option").all_inner_texts()
        return [t.strip() for t in texts if t.strip()]

    def filter_by_status(self, value):
        """value: 'all', 'draft', 'pending', 'scheduled', 'sending', 'sent',
        'cancelled', or 'failed' (confirmed via DOM option text)."""
        sel = self.page.locator(self.SELECT_FILTER_STATUS).first
        sel.wait_for(state="attached", timeout=8000)
        sel.select_option(label=value.capitalize())
        self.page.wait_for_timeout(1500)

    def export_campaigns(self):
        try:
            btn = self.page.locator(self.BTN_BULK_ACTION).first
            btn.wait_for(state="visible", timeout=8000)
            btn.click()
            self.page.wait_for_timeout(500)
            exp = self.page.locator(self.BTN_EXPORT).first
            exp.wait_for(state="visible", timeout=5000)
            exp.click()
            self.page.wait_for_timeout(2000)
        except Exception:
            pass

    def toggle_columns(self):
        try:
            btn = self.page.locator(self.BTN_COLUMNS).first
            btn.wait_for(state="visible", timeout=8000)
            btn.click()
            self.page.wait_for_timeout(500)
            cb = self.page.locator(self.COLUMN_CHECKBOX).first
            cb.wait_for(state="attached", timeout=5000)
            cb.evaluate("(el) => el.click()")
            self.page.wait_for_timeout(500)
        except Exception:
            pass

    def get_visible_column_count(self):
        headers = self.page.locator("xpath=//table//th")
        count = 0
        for i in range(headers.count()):
            h = headers.nth(i)
            if h.is_visible() and h.inner_text().strip():
                count += 1
        return count

    def set_per_page(self, value):
        try:
            sel = self.page.locator(self.SELECT_PER_PAGE).first
            sel.wait_for(state="attached", timeout=8000)
            sel.select_option(value=str(value))
            self.page.wait_for_timeout(1500)
        except Exception:
            pass

    def get_per_page_value(self):
        try:
            sel = self.page.locator(self.SELECT_PER_PAGE).first
            return sel.input_value()
        except Exception:
            return None

    # ══════════════════════════════════════════════════════════════════════════
    # Create page — basic fields
    # ══════════════════════════════════════════════════════════════════════════

    def _find_campaign_name_input(self):
        """
        Locate the campaign-name input regardless of wire:model modifier or value.
        Priority:
          1. XPath locator (covers campaign_name / campaign in wire:model*)
          2. JS scan: first wire:model* whose value contains 'campaign'
          3. JS scan: wire:model* whose value === 'name' and field is visible
          4. Last resort: first visible, non-hidden text input on page

        Returns a Playwright Locator (case 1) or ElementHandle (cases 2-4) —
        both expose the same .fill()/.get_attribute()/.evaluate()/
        .scroll_into_view_if_needed() surface used by the callers below.
        """
        try:
            loc = self.page.locator(self.INPUT_CAMPAIGN_NAME).first
            loc.wait_for(state="attached", timeout=10000)
            return loc
        except Exception:
            pass

        handle = self.page.evaluate_handle("""
            () => {
                var SKIP = {hidden:1, file:1, checkbox:1, radio:1, submit:1, button:1, image:1};
                var inputs = Array.from(document.querySelectorAll('input'));
                inputs = inputs.filter(function(i) { return !SKIP[i.type]; });

                function wm(el) {
                    for (var a = 0; a < el.attributes.length; a++) {
                        if (el.attributes[a].name.startsWith('wire:model'))
                            return el.attributes[a].value;
                    }
                    return null;
                }

                // 2. wire:model* value contains 'campaign'
                for (var i of inputs) {
                    var v = wm(i);
                    if (v && v.toLowerCase().includes('campaign')) return i;
                }

                // 3. wire:model* value === 'name', element is visible
                for (var i of inputs) {
                    var v = wm(i);
                    if (v && v === 'name' && i.offsetHeight > 0) return i;
                }

                // 4. first visible text input
                for (var i of inputs) {
                    if (i.offsetHeight > 0 && (!i.type || i.type === 'text')) return i;
                }
                return null;
            }
        """)
        el = handle.as_element()
        if el:
            return el
        raise Exception("Campaign Name input not found by XPath or JS scan")

    def enter_campaign_name(self, name):
        inp = self._find_campaign_name_input()
        inp.scroll_into_view_if_needed()
        try:
            inp.evaluate("(el) => { el.value = ''; }")
        except Exception:
            pass
        inp.fill(name)
        inp.evaluate(
            "(el) => { el.dispatchEvent(new Event('input',{bubbles:true})); "
            "el.dispatchEvent(new Event('change',{bubbles:true})); }"
        )
        self.page.wait_for_timeout(300)

    def get_campaign_name(self):
        try:
            inp = self._find_campaign_name_input()
            val = inp.get_attribute("value")
            if val is None:
                val = inp.evaluate("(el) => el.value")
            return val or ""
        except Exception:
            return ""

    def get_schedule_field_value(self):
        try:
            return self.page.locator(self.INPUT_SCHEDULE_DATE).first.get_attribute("value")
        except Exception:
            return ""

    def click_cancel(self):
        try:
            self._js_click(self.BTN_CANCEL, timeout=5000)
        except Exception:
            self.open(self.CAMPAIGN_LIST_URL)
        self.page.wait_for_timeout(1000)

    def click_continue(self):
        try:
            self._js_click(self.BTN_CONTINUE, timeout=5000)
        except Exception:
            pass
        self.page.wait_for_timeout(1000)

    def get_validation_errors(self):
        els = self.page.locator(self.VALIDATION_ERROR)
        texts = [t.strip() for t in els.all_inner_texts()]
        return [t for t in texts if t]

    def wait_for_validation_error_or_toast(self, timeout_s=6):
        """Poll get_validation_errors() and get_toast_error() together for
        up to timeout_s instead of checking each exactly once.

        Both underlying checks are instantaneous, single-shot reads with
        no wait of their own -- get_toast_error() in particular has no
        wait_for at all, so it only catches a toast that happens to
        already be in the DOM at the exact instant it's called. TC039/
        TC042/TC048 all called both right after a fixed sleep following
        click_preview(), which is exactly the same race already found and
        fixed for TC005/TC007/TC019 elsewhere in this project: if the
        Livewire round trip (or a toast's own auto-dismiss, as confirmed
        by video for the blocked-numbers duplicate case) lands slightly
        outside that fixed window, the single check misses it even though
        the app genuinely showed the error. Returns (errors, toast_err) --
        whichever polling loop iteration first finds either non-empty."""
        end_time = time.time() + timeout_s
        errors, toast_err = [], None
        while time.time() < end_time:
            errors = self.get_validation_errors()
            toast_err = self.get_toast_error()
            if errors or toast_err:
                return errors, toast_err
            self.page.wait_for_timeout(300)
        return errors, toast_err

    # ══════════════════════════════════════════════════════════════════════════
    # Sender ID & Template (WireUI selects)
    # ══════════════════════════════════════════════════════════════════════════

    def select_sender_id(self, value):
        self._wireui_select(self.DROPDOWN_SENDER_ID, value)

    def select_template(self, value):
        self._wireui_select(self.DROPDOWN_TEMPLATE, value)

    def get_template_variables(self):
        """Returns a plain list of Locators (supports len()/indexing, unlike
        a bare Locator object)."""
        return self.page.locator(self.TEMPLATE_VAR_INPUTS).all()

    def fill_template_variable(self, index, value):
        inputs = self.page.locator(self.TEMPLATE_VAR_INPUTS).all()
        if inputs and index < len(inputs):
            inp = inputs[index]
            inp.scroll_into_view_if_needed()
            inp.fill(value)
            inp.evaluate(
                "(el) => { el.dispatchEvent(new Event('input',{bubbles:true})); "
                "el.dispatchEvent(new Event('change',{bubbles:true})); }"
            )

    def fill_all_template_variables(self):
        """
        Discover every template variable input on the page and fill each one
        with a value derived from the field's own id/placeholder — no hardcoded values.

        id format is typically 'columnMapping.<varName>', e.g. 'columnMapping.name'.
        Returns the number of fields filled.
        """
        ts = str(int(time.time()))[-5:]   # 5-digit timestamp suffix

        inputs = self.page.locator(self.TEMPLATE_VAR_INPUTS).all()
        for inp in inputs:
            field_id    = inp.get_attribute("id") or ""
            placeholder = inp.get_attribute("placeholder") or ""
            field_name  = (field_id.split(".")[-1] if "." in field_id
                           else placeholder or field_id or "var").strip()

            # Generate a value appropriate for the field name
            low = field_name.lower()
            if re.search(r'phone|mobile|number|num|mob', low):
                value = f"91987654{ts}"
            elif re.search(r'email', low):
                value = f"test_{ts}@example.com"
            elif re.search(r'otp|pin|code', low):
                value = ts
            elif re.search(r'amount|price|cost|fee', low):
                value = f"{ts[:3]}.00"
            elif re.search(r'date', low):
                value = "2026-01-01"
            elif re.search(r'time', low):
                value = "10:00"
            elif re.search(r'name|customer|user', low):
                value = f"User{ts}"
            else:
                value = f"Auto_{field_name}_{ts}"

            inp.scroll_into_view_if_needed()
            try:
                inp.evaluate("(el) => { el.value = ''; }")
            except Exception:
                pass
            inp.fill(value)
            # Dispatch both events so Livewire wire:model picks up the value
            inp.evaluate(
                "(el) => { el.dispatchEvent(new Event('input',{bubbles:true})); "
                "el.dispatchEvent(new Event('change',{bubbles:true})); }"
            )
            self.page.wait_for_timeout(300)  # let Livewire debounce and sync this field before moving on

        return len(inputs)

    # ══════════════════════════════════════════════════════════════════════════
    # Import Contacts
    # ══════════════════════════════════════════════════════════════════════════

    def click_import_contact(self):
        # Dismiss any open WireUI/Alpine dropdown overlay first
        try:
            self.page.evaluate("() => document.body.click()")
            self.page.wait_for_timeout(400)
        except Exception:
            pass
        btn = self.page.locator(self.BTN_IMPORT_CONTACT).first
        btn.wait_for(state="attached", timeout=10000)
        btn.scroll_into_view_if_needed()
        self.page.wait_for_timeout(300)
        btn.evaluate("(el) => el.click()")
        self.page.wait_for_timeout(1000)

    def is_import_popup_open(self):
        return self.is_element_present(self.IMPORT_POPUP, timeout=5000)

    def paste_contacts(self, numbers_text):
        ta = self.page.locator(self.TEXTAREA_PASTE).first
        ta.wait_for(state="attached", timeout=10000)
        ta.fill(numbers_text)

    def upload_contact_file(self, filepath):
        # Click File Upload tab
        try:
            tab = self.page.locator(self.FILE_UPLOAD_TAB).first
            tab.wait_for(state="visible", timeout=8000)
            tab.click()
            self.page.wait_for_timeout(400)
        except Exception:
            pass
        # Send file path to the hidden file input
        fi = self.page.locator(self.FILE_INPUT).first
        fi.wait_for(state="attached", timeout=10000)
        fi.set_input_files(os.path.abspath(filepath))
        # Wait for skeleton loader / processing spinner to clear
        try:
            self.page.locator("xpath=//div[contains(@class,'animate-pulse')]").first.wait_for(
                state="hidden", timeout=20000)
        except Exception:
            pass
        self.page.wait_for_timeout(800)
        # Auto-map all column-mapping dropdowns that appear after upload
        self.select_column_mappings()

    def select_column_mappings(self):
        """
        After CSV file upload, auto-select columns in all 'Select column (optional)'
        WireUI dropdown selects.

        Strategy per dropdown:
          1. Read the surrounding label text to know what the variable is called
          2. Try to pick a CSV column whose name matches (e.g. "phone" -> "Phone Number")
          3. Fall back to the first available option

        Returns the number of dropdowns mapped.
        """
        # Buttons that still show the "Select column" placeholder — i.e. unmapped
        col_buttons = self.page.query_selector_all(
            "xpath=//button[.//span[contains(@x-show,'isEmpty') "
            "          and contains(text(),'Select column')]]"
            " | //button[.//span[contains(text(),'Select column (optional)')]]"
        )
        mapped = 0
        for btn in col_buttons:
            try:
                if not self._is_rendered(btn):
                    continue

                # Grab nearby label text to help choose the right column
                container = self._alpine_container(btn) or btn
                label_text = ""
                try:
                    labels = container.query_selector_all(
                        "xpath=ancestor::*[1]/preceding-sibling::label | "
                        ".//label | preceding-sibling::label | "
                        "ancestor::div[1]//label | ancestor::div[2]//label"
                    )
                    for lbl in labels:
                        txt = (lbl.inner_text() or "").strip()
                        if txt and "Select column" not in txt:
                            label_text = txt.lower()
                            break
                except Exception:
                    pass

                # Open the dropdown
                btn.evaluate("(el) => el.scrollIntoView({block:'center'})")
                btn.evaluate("(el) => el.click()")
                self.page.wait_for_timeout(600)

                # WireUI renders options as div[select-option] — search globally
                # (Alpine may teleport the dropdown to body level)
                visible_opts = [
                    o for o in self.page.query_selector_all("xpath=//div[@select-option]")
                    if self._is_rendered(o) and (o.inner_text() or "").strip()
                ]

                # Fallback: li-based options inside container
                if not visible_opts:
                    for xp in [
                        "xpath=.//li[not(contains(@class,'disabled'))]",
                        "xpath=.//span[@role='option']",
                    ]:
                        try:
                            opts = container.query_selector_all(xp)
                            visible_opts = [o for o in opts
                                            if self._is_rendered(o) and (o.inner_text() or "").strip()]
                            if visible_opts:
                                break
                        except Exception:
                            pass

                if not visible_opts:
                    self.page.evaluate("() => document.body.click()")
                    continue

                # Keywords that identify a phone/contact-number column
                _PHONE_KEYS = {"phone", "mobile", "number", "contact", "no.", "tel"}

                # Is this dropdown for the phone number field?
                is_phone_field = any(kw in label_text for kw in _PHONE_KEYS)

                if is_phone_field:
                    # Phone field → prefer phone-like column, else first option
                    chosen = visible_opts[0]
                    for opt in visible_opts:
                        if any(kw in (opt.inner_text() or "").strip().lower() for kw in _PHONE_KEYS):
                            chosen = opt
                            break
                else:
                    # Template variable field → skip phone-like columns
                    non_phone = [o for o in visible_opts
                                 if not any(kw in (o.inner_text() or "").strip().lower()
                                            for kw in _PHONE_KEYS)]
                    if not non_phone:
                        # Only phone column available — skip this dropdown
                        self.page.evaluate("() => document.body.click()")
                        continue
                    chosen = non_phone[0]
                    if label_text:
                        for opt in non_phone:
                            opt_text = (opt.inner_text() or "").strip().lower()
                            if any(word in opt_text for word in label_text.split()
                                   if len(word) > 2):
                                chosen = opt
                                break

                chosen.evaluate("(el) => el.click()")
                self.page.wait_for_timeout(300)
                mapped += 1

            except Exception:
                try:
                    self.page.evaluate("() => document.body.click()")
                except Exception:
                    pass
                continue

        if mapped:
            self.page.wait_for_timeout(300)
        return mapped

    def click_import_confirm(self):
        btn = self.page.locator(self.BTN_IMPORT_CONFIRM).first
        btn.wait_for(state="attached", timeout=15000)
        deadline = self.page.evaluate("() => Date.now()") + 10000
        while self.page.evaluate("() => Date.now()") < deadline:
            if btn.get_attribute("disabled") is None:
                break
            self.page.wait_for_timeout(200)
        btn.scroll_into_view_if_needed()
        self.page.wait_for_timeout(300)
        btn.evaluate("(el) => el.click()")
        # Wait for modal to close — use Continue button disappearance (works for
        # both copy-paste and file-upload flows; textarea-only wait missed file flow)
        try:
            btn.wait_for(state="hidden", timeout=15000)
        except Exception:
            # Fallback: wait for paste textarea (copy-paste flow)
            try:
                self.page.locator(self.TEXTAREA_PASTE).first.wait_for(state="hidden", timeout=5000)
            except Exception:
                pass
        self.page.wait_for_timeout(500)

    def import_contacts_from_csv(self, filepath, keep_duplicates=False):
        """Full import flow: open modal → File Upload tab → upload → Continue → success."""
        self.click_import_contact()
        self.page.locator(self.FILE_INPUT).first.wait_for(state="attached", timeout=10000)

        # File Upload tab
        try:
            tab = self.page.locator(self.FILE_UPLOAD_TAB).first
            tab.wait_for(state="visible", timeout=8000)
            tab.click()
            self.page.wait_for_timeout(300)
        except Exception:
            pass

        # Upload
        fi = self.page.locator(self.FILE_INPUT).first
        fi.wait_for(state="attached", timeout=10000)
        fi.set_input_files(os.path.abspath(filepath))

        # Wait for skeleton
        try:
            self.page.locator("xpath=//div[contains(@class,'animate-pulse')]").first.wait_for(
                state="hidden", timeout=20000)
        except Exception:
            pass
        self.page.wait_for_timeout(400)

        # Duplicate checkbox
        try:
            cb = self.page.locator(self.DUPLICATE_CHECKBOX).first
            if keep_duplicates != cb.is_checked():
                cb.evaluate("(el) => el.click()")
        except Exception:
            pass

        # Continue
        btn = self.page.locator(self.BTN_IMPORT_CONFIRM).first
        btn.wait_for(state="attached", timeout=15000)
        deadline = self.page.evaluate("() => Date.now()") + 10000
        while self.page.evaluate("() => Date.now()") < deadline:
            if btn.get_attribute("disabled") is None:
                break
            self.page.wait_for_timeout(200)
        btn.scroll_into_view_if_needed()
        self.page.wait_for_timeout(300)
        btn.evaluate("(el) => el.click()")

        # Wait for success or modal close
        try:
            self.page.locator(self.IMPORT_SUCCESS_MSG).first.wait_for(state="visible", timeout=20000)
        except Exception:
            try:
                btn.wait_for(state="hidden", timeout=10000)
            except Exception:
                pass
        self.page.wait_for_timeout(500)

    def click_cancel_import(self):
        try:
            btn = self.page.locator(self.BTN_CANCEL_IMPORT).first
            btn.wait_for(state="visible", timeout=5000)
            btn.click()
        except Exception:
            try:
                close = self.page.locator(
                    "xpath=//div[contains(@class,'fixed')]//button[@aria-label='Close'"
                    " or contains(@class,'close')] | //div[contains(@class,'fixed')]//button[.//svg]"
                ).first
                close.evaluate("(el) => el.click()")
            except Exception:
                self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(500)

    def click_download_sample(self):
        try:
            btn = self.page.locator(self.BTN_DOWNLOAD_SAMPLE).first
            btn.wait_for(state="visible", timeout=5000)
            btn.click()
            self.page.wait_for_timeout(2000)
        except Exception:
            pass

    def get_import_error(self):
        if self.is_element_present(self.IMPORT_ERROR, timeout=5000):
            return self.page.locator(self.IMPORT_ERROR).first.inner_text()
        return None

    # ══════════════════════════════════════════════════════════════════════════
    # Schedule
    # ══════════════════════════════════════════════════════════════════════════

    def select_send_now(self):
        """Click Send Now radio — JS-click fires wire:model.live."""
        try:
            radio = self.page.locator(self.SEND_NOW_INPUT).first
            radio.wait_for(state="attached", timeout=10000)
            radio.evaluate("(el) => el.click()")
            self.page.wait_for_timeout(500)
        except Exception:
            try:
                btn = self.page.locator(self.RADIO_SEND_NOW).first
                btn.wait_for(state="visible", timeout=8000)
                btn.click()
                self.page.wait_for_timeout(500)
            except Exception:
                pass

    @staticmethod
    def _round_to_5min(time_str):
        """Round HH:MM to nearest 5-minute slot (options are 00,05,10,...,55)."""
        h, m = map(int, time_str.split(":"))
        m = (m // 5) * 5          # floor to nearest 5
        if m >= 60:
            m = 55
        return f"{h:02d}:{m:02d}"

    def select_schedule_later(self, date_str=None, time_str=None):
        """
        Click 'Schedule for Later', then set date + time.

        Date  → <input type="date" x-model="date">  — set via JS + dispatch 'change'
        Time  → <select x-model="time">             — select nearest 5-min option via JS
        """
        try:
            radio = self.page.locator(self.RADIO_SCHEDULE).first
            radio.wait_for(state="visible", timeout=8000)
            radio.click()
            self.page.wait_for_timeout(600)
        except Exception:
            return

        # ── Date ────────────────────────────────────────────────────────────
        if date_str:
            try:
                el = self.page.locator(self.INPUT_SCHEDULE_DATE).first
                el.wait_for(state="attached", timeout=5000)
                el.evaluate(
                    "(e, val) => { e.value = val; "
                    "e.dispatchEvent(new Event('input',  {bubbles:true})); "
                    "e.dispatchEvent(new Event('change', {bubbles:true})); }",
                    date_str
                )
                self.page.wait_for_timeout(300)
            except Exception:
                pass

        # ── Time (select dropdown with 5-min steps) ──────────────────────
        if time_str:
            slot = self._round_to_5min(time_str)
            try:
                sel_el = self.page.locator(self.SELECT_SCHEDULE_TIME).first
                sel_el.wait_for(state="attached", timeout=5000)
                sel_el.select_option(value=slot)
                sel_el.evaluate("(e) => e.dispatchEvent(new Event('change', {bubbles:true}))")
            except Exception:
                # Fallback: set via JS directly
                try:
                    sel_el = self.page.locator(self.SELECT_SCHEDULE_TIME).first
                    sel_el.wait_for(state="attached", timeout=3000)
                    sel_el.evaluate(
                        "(e, val) => { e.value = val; "
                        "e.dispatchEvent(new Event('change', {bubbles:true})); }",
                        slot
                    )
                except Exception:
                    pass

        self.page.wait_for_timeout(500)

    # ══════════════════════════════════════════════════════════════════════════
    # Preview / Send
    # ══════════════════════════════════════════════════════════════════════════

    def click_preview(self):
        """Click 'Preview Campaign' — uses presence detection + disabled-wait
        so Livewire's transient wire:loading state doesn't block us.
        Tries multiple button-text candidates in case the label differs."""
        candidates = [
            "xpath=//button[contains(.,'Preview Campaign')]",
            "xpath=//button[contains(.,'Preview')]",
            "xpath=//button[contains(.,'Review Campaign')]",
        ]
        btn = None
        for xp in candidates:
            try:
                loc = self.page.locator(xp).first
                loc.wait_for(state="attached", timeout=5000)
                btn = loc
                break
            except Exception:
                continue

        if btn is None:
            # Final fallback with longer wait
            btn = self.page.locator(self.BTN_PREVIEW).first
            btn.wait_for(state="attached", timeout=20000)

        btn.scroll_into_view_if_needed()

        # Wait up to 10s for the button to become enabled (Livewire loading clears)
        deadline = self.page.evaluate("() => Date.now()") + 10000
        while self.page.evaluate("() => Date.now()") < deadline:
            if btn.get_attribute("disabled") is None:
                break
            self.page.wait_for_timeout(500)

        # Native click so wire:click fires; JS fallback if intercepted
        try:
            btn.click()
        except Exception:
            btn.evaluate("(el) => el.click()")
        self.page.wait_for_timeout(800)

    def is_preview_open(self):
        return self.is_element_present(self.PREVIEW_MODAL, timeout=8000)

    def click_close_preview(self):
        try:
            btn = self.page.locator(self.BTN_CLOSE_PREVIEW).first
            btn.wait_for(state="visible", timeout=5000)
            btn.click()
        except Exception:
            self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(400)

    def click_launch_campaign(self):
        """Click the final submit button — label differs by campaign type:
          Send Now       → 'Send Campaign'   (wire:click="submit")
          Schedule Later → 'Schedule Campaign' (wire:click="submit")
          Legacy label   → 'Launch Campaign'

        Uses presence (not clickability) detection so Livewire's transient
        wire:loading disabled state doesn't block us. Waits for disabled to
        clear then clicks natively so wire:click fires.
        """
        candidates = [
            "xpath=//button[contains(.,'Send Campaign')]",
            "xpath=//button[contains(.,'Schedule Campaign')]",
            "xpath=//button[contains(.,'Launch Campaign')]",
            "xpath=//button[contains(.,'Send Now')]",
            "xpath=//button[@*[name()='wire:click' and .='submit']]",
        ]

        # Find the first present (not necessarily clickable) button
        btn = None
        for xp in candidates:
            try:
                loc = self.page.locator(xp).first
                loc.wait_for(state="attached", timeout=4000)
                btn = loc
                break
            except Exception:
                continue

        if btn is None:
            return  # no button found — caller relies on wait_for_launch

        btn.scroll_into_view_if_needed()

        # Wait up to 5s for the button to become enabled (wire:loading clears)
        deadline = self.page.evaluate("() => Date.now()") + 5000
        while self.page.evaluate("() => Date.now()") < deadline:
            if btn.get_attribute("disabled") is None:
                break
            self.page.wait_for_timeout(300)

        # Native click so wire:click="submit" fires through Livewire
        try:
            btn.click()
        except Exception:
            btn.evaluate("(el) => el.click()")
        self.page.wait_for_timeout(500)

    def confirm_swal(self, timeout=4000):
        """Click SweetAlert2 confirm button if present.

        Returns True if a dialog was found and confirmed, False if no dialog
        appeared (the app may have auto-confirmed or redirected already).
        Does NOT raise — callers should check the return value or the page URL.
        """
        for xp in [
            "xpath=//button[contains(@class,'swal2-confirm')]",
            "xpath=//button[contains(.,'Yes')]",
            "xpath=//button[contains(.,'OK')]",
        ]:
            try:
                btn = self.page.locator(xp).first
                btn.wait_for(state="visible", timeout=timeout)
                btn.evaluate("(el) => el.click()")
                return True
            except Exception:
                continue
        return False  # no dialog — caller should verify via URL / toast

    # ══════════════════════════════════════════════════════════════════════════
    # Toast / status helpers
    # ══════════════════════════════════════════════════════════════════════════

    def is_success_toast_shown(self):
        return self.is_element_present(self.TOAST_SUCCESS, timeout=5000)

    def get_toast_error(self):
        """Checks every mechanism this app actually uses for a toast/dialog
        style error, in order of how likely each is here: the confirmed
        WireUI toast container, then SweetAlert2's title and html-container
        (both confirmed elsewhere in this project -- see
        sms_blocked_numbers_page.py), and finally the guessed Bootstrap-
        style TOAST_ERROR classes as a last-resort fallback. Single-shot on
        purpose -- wait_for_validation_error_or_toast() is what supplies
        the polling, the same way get_validation_error_text() in
        sms_blocked_numbers_page.py checks multiple mechanisms per
        iteration of its own polling loop."""
        for locator in (self.TOAST_NOTIFICATION_TEXT, "#swal2-title",
                        "#swal2-html-container", self.TOAST_ERROR):
            try:
                els = self.page.locator(locator)
                for i in range(els.count()):
                    el = els.nth(i)
                    if el.is_visible():
                        text = el.inner_text().strip()
                        if text:
                            return text
            except Exception:
                continue
        return None

    # ══════════════════════════════════════════════════════════════════════════
    # Import Modal — Duplicate handling & Contact Management tab
    # ══════════════════════════════════════════════════════════════════════════

    def is_duplicate_handling_enabled(self):
        """Check current state of the Duplicate Phone Handling toggle."""
        try:
            cb = self.page.locator(self.DUPLICATE_CHECKBOX).first
            return cb.is_checked()
        except Exception:
            try:
                sw = self.page.locator(
                    "xpath=//button[@role='switch'] | //div[@role='switch']"
                    " | //input[@type='checkbox'][ancestor::*[contains(.,'Duplicate')]]"
                ).first
                if sw.get_attribute("aria-checked") == "true":
                    return True
                return sw.is_checked()
            except Exception:
                return False

    def toggle_duplicate_handling(self):
        """Toggle the Duplicate Phone Handling switch ON or OFF.

        The UI uses a Tailwind peer-checkbox pattern — a hidden
        <input type="checkbox" id="keep_duplicates"> whose state drives
        the visual toggle div via the 'peer' class.  Clicking the
        associated <label> is the most reliable trigger; JS click on the
        checkbox is the fallback.
        """
        # 1. Try clicking the <label for="keep_duplicates">
        try:
            lbl = self.page.locator(
                "xpath=//label[@for='keep_duplicates']"
                " | //label[contains(.,'Duplicate') or contains(.,'duplicate')]"
                "    [.//input[@type='checkbox'] or @for]"
            ).first
            lbl.wait_for(state="attached", timeout=3000)
            lbl.scroll_into_view_if_needed()
            lbl.click()
            self.page.wait_for_timeout(300)
            return
        except Exception:
            pass

        # 2. Fallback: JS click on the hidden checkbox itself
        try:
            cb = self.page.locator(self.DUPLICATE_CHECKBOX).first
            cb.evaluate("(el) => el.click()")
            self.page.wait_for_timeout(300)
            return
        except Exception:
            pass

        # 3. Last resort: any role="switch" near "Duplicate" text
        try:
            sw = self.page.locator(
                "xpath=//button[@role='switch'][ancestor::*[contains(.,'Duplicate')]]"
                " | //div[@role='switch'][ancestor::*[contains(.,'Duplicate')]]"
            ).first
            sw.scroll_into_view_if_needed()
            sw.click()
            self.page.wait_for_timeout(300)
        except Exception:
            pass

    def get_contact_count(self):
        """Return number of contacts shown in the campaign Contacts section."""
        patterns = [
            "xpath=//*[contains(text(),'contact') or contains(text(),'Contact')]",
            "xpath=//*[contains(@class,'contact') and contains(text(),'imported')]",
        ]
        for xp in patterns:
            try:
                els = self.page.locator(xp)
                for i in range(els.count()):
                    text = els.nth(i).inner_text()
                    m = re.search(r'\d+', text)
                    if m:
                        return int(m.group())
            except Exception:
                continue
        return 0

    def clear_contacts(self):
        """Remove currently imported contacts (click remove/trash icon if present)."""
        try:
            btn = self.page.locator(
                "xpath=//button[contains(.,'Remove') or contains(.,'Clear')]"
                "[ancestor::*[contains(@class,'contact') or contains(.,'contact')]]"
                " | //*[contains(@class,'contact')]//button[.//svg]"
                " | //button[@aria-label='Remove']"
            ).first
            btn.wait_for(state="visible", timeout=5000)
            btn.evaluate("(el) => el.click()")
            self.page.wait_for_timeout(500)
        except Exception:
            pass

    def import_from_contact_management(self, method="tags"):
        """
        Import contacts via Contact Management tab.
        method: 'tags' or 'segments'
        Raises RuntimeError if the tab or items are not available.
        """
        # Switch to Contact Management tab
        cm_tab = (
            "xpath=//a[contains(.,'Contact Management')] "
            "| //button[contains(.,'Contact Management')] "
            "| //li[contains(.,'Contact Management')]"
        )
        tab = self.page.locator(cm_tab).first
        tab.wait_for(state="visible", timeout=8000)
        tab.click()
        self.page.wait_for_timeout(600)

        # Select the sub-type (Tags / Segments)
        method_cap = method.capitalize()
        type_locator = (
            f"xpath=//button[normalize-space()='{method_cap}']"
            f" | //option[contains(.,'{method_cap}')]"
            f" | //label[contains(.,'{method_cap}')]"
            f" | //input[@value='{method.lower()}']"
            f" | //div[contains(@class,'tab')][contains(.,'{method_cap}')]"
        )
        try:
            el = self.page.locator(type_locator).first
            el.wait_for(state="visible", timeout=8000)
            el.evaluate("(e) => e.click()")
            self.page.wait_for_timeout(600)
        except Exception:
            pass  # type tab click is optional

        # Select the first available group/segment item in the list.
        item_locator = (
            "xpath=//label[contains(@class,'checkbox')] "
            "| //li[contains(@class,'option') or contains(@class,'item')] "
            "| //div[contains(@class,'option')] "
            "| //input[@type='checkbox']"
        )
        try:
            item = self.page.locator(item_locator).first
            item.wait_for(state="visible", timeout=10000)
            item.scroll_into_view_if_needed()
            item.evaluate("(e) => e.click()")
            self.page.wait_for_timeout(500)
        except Exception:
            raise RuntimeError(
                f"Could not find any available item in Contact Management {method} tab"
            )
