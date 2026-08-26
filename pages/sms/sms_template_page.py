import os
import time

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR


class SMSTemplatePage(BasePage):

    # ── Direct URLs ────────────────────────────────────────────────────────────
    TEMPLATE_LIST_URL = "/channels/sms/template"
    TEMPLATE_CREATE_URL = "/channels/sms/template/create"

    # ── Sidebar navigation ─────────────────────────────────────────────────────
    NAV_SMS = "xpath=//nav//a[contains(@href,'/channels')] | //a[contains(.,'SMS')]"
    NAV_TEMPLATES = "xpath=//a[contains(.,'Template') or contains(@href,'/template')]"

    # ── List page header buttons ───────────────────────────────────────────────
    BTN_UPLOAD_TEMPLATE = "xpath=//button[contains(.,'Upload') and contains(.,'Template')]"
    BTN_CREATE_TEMPLATE = (
        "xpath=//a[contains(@href,'/template/create')] | "
        "//button[contains(.,'Create') and contains(.,'Template')]"
    )

    # ── Search ─────────────────────────────────────────────────────────────────
    SEARCH_BOX = "input[placeholder*='Search'], input[type='search']"
    TABLE_ROWS = "table tbody tr"
    NO_RECORDS = (
        "xpath=//*[contains(text(),'No records') or contains(text(),'No data') "
        "    or contains(text(),'No results') or contains(text(),'No template')]"
    )
    COLUMN_HEADERS = "table thead th"
    SORT_CREATED_AT = "xpath=//th[contains(.,'Created')]"

    # ── Filters ────────────────────────────────────────────────────────────────
    BTN_FILTER = "xpath=//button[contains(text(),'Filter')]"
    FILTER_DLT_ID = "input[placeholder*='DLT'], input[name*='dlt']"
    FILTER_SENDER_ID = "select[name*='sender'], input[name*='sender']"
    FILTER_STATUS = "select[name*='status']"
    FILTER_TYPE = "select[name*='type']"
    FILTER_FROM_DATE = "input[name*='from'], input[placeholder*='From']"
    FILTER_TO_DATE = "input[name*='to'], input[placeholder*='To']"
    BTN_APPLY_FILTER = "xpath=//button[contains(text(),'Apply')] | //button[contains(text(),'Search')]"

    # ── Bulk Actions / Export ──────────────────────────────────────────────────
    BTN_BULK_ACTIONS = "xpath=//button[contains(text(),'Bulk Action') or contains(text(),'Actions')]"
    # Real DOM (confirmed from a live run):
    #   <button wire:click="export" ...><span>Export to CSV</span></button>
    #
    # Two locator bugs stacked here across two fix attempts:
    #   1. The label text lives in a nested <span>, not as a direct text
    #      node of the <button> — xpath's text() only matches DIRECT
    #      text-node children, so `contains(text(),'Export')` never matched.
    #   2. `@wire:click='export'` is INVALID xpath here: the colon makes the
    #      parser treat "wire" as a namespace prefix, which is undeclared in
    #      this HTML document — the whole expression then fails to evaluate
    #      (not just that clause), which silently killed the `contains(.,
    #      'Export')` fallback union branches too. This exact gotcha is
    #      already documented/worked around elsewhere in this codebase (see
    #      pages/rcs/*_analytics_page.py's "@*[name()='wire:click']" pattern)
    #      — use that form, never a bare @wire:click.
    # contains(.,...) (descendant text, not just direct children) is kept as
    # a fallback in case a future markup change drops the wire:click attribute.
    MENU_EXPORT = (
        "xpath=//button[@*[name()='wire:click']='export'] "
        "| //a[contains(.,'Export')] | //li[contains(.,'Export')] | //button[contains(.,'Export')]"
    )

    # ── Columns & Per Page ────────────────────────────────────────────────────
    BTN_COLUMNS = "xpath=//button[contains(text(),'Column') or contains(text(),'Columns')]"
    COLUMN_CHECKBOXES = "xpath=//input[@type='checkbox'][ancestor::*[contains(@class,'dropdown') or contains(@class,'column')]]"
    PER_PAGE_SELECT = "select[name*='per'], select[name*='page']"
    PER_PAGE_BTN = "xpath=//button[contains(.,'per page') or contains(.,'Per Page')]"
    BTN_NEXT_PAGE = "[aria-label='Next'], button[title='Next'], [class*='next']:not([disabled])"
    BTN_PREV_PAGE = "[aria-label='Previous'], button[title='Previous'], [class*='prev']:not([disabled])"

    # ── Row-level actions (same app pattern as SenderID) ─────────────────────
    # Edit: <a href=".../template/{id}/edit" data-tooltip-target="tooltip-edit-{id}">
    ROW_EDIT_BTN = (
        "xpath=(//a[contains(@href,'/template/') and contains(@href,'/edit')])[1] | "
        "(//a[contains(@data-tooltip-target,'tooltip-edit-')])[1]"
    )
    # Delete: <button data-tooltip-target="tooltip-deleteOne-{id}" x-on:click="$wireui.confirmAction(...)">
    # NOTE: Do NOT add an SVG-path fallback branch — the WireUI dialog's hidden
    # close button also has an X-icon and appears first in document order,
    # so the union would put btns[0] on that hidden button instead of a row button.
    ROW_DELETE_BTN = "xpath=//button[contains(@data-tooltip-target,'deleteOne')]"
    # View: <a href=".../template/{id}"> or button with eye icon
    ROW_VIEW_BTN = (
        "xpath=(//a[contains(@href,'/template/') and not(contains(@href,'/edit'))])[1] | "
        "(//button[contains(@data-tooltip-target,'view')])[1]"
    )

    # ── WireUI delete confirmation ────────────────────────────────────────────
    # After clicking delete, WireUI shows: Confirm (x-on:click="accept") + Cancel (x-on:click="reject")
    # NOTE: CSS [x-on\:click=...] does NOT work — use text-based XPath instead.
    CONFIRM_DELETE_BTN = "xpath=//button[normalize-space()='Confirm']"
    CANCEL_DELETE_BTN = "xpath=//button[normalize-space()='Cancel']"
    DELETE_RESTRICT_MSG = "xpath=//*[contains(text(),'cannot') or contains(text(),'active') or contains(text(),'restrict')]"

    # ── Upload popup (specific: contains dropzone-file input) ─────────────────
    UPLOAD_POPUP = "xpath=//div[contains(@class,'fixed') and .//input[@id='dropzone-file']]"
    FILE_INPUT = "#dropzone-file"
    BTN_DOWNLOAD_SAMPLE = "xpath=//a[contains(.,'Download Sample')] | //button[contains(.,'Download Sample')]"
    BTN_IMPORT = "xpath=//div[contains(@class,'fixed')]//button[normalize-space()='Yes, Import']"
    BTN_CANCEL_UPLOAD = (
        "xpath=//div[contains(@class,'fixed')]//button[contains(.,'Cancel') or contains(.,'No') or contains(.,'Close')] | "
        "//div[contains(@class,'fixed')]//*[@type='button' and not(normalize-space(.)='Yes, Import')]"
    )
    UPLOAD_ERROR = "[class*='error'], [class*='alert-danger']"
    UPLOAD_SUCCESS = "[class*='success'], [class*='alert-success']"
    LOADER = "xpath=//div[contains(@class,'animate-pulse') or contains(@class,'animate-spin')] | //svg[contains(@class,'animate-spin')]"

    # ── Create / Edit Template form ───────────────────────────────────────────
    # Confirmed from DOM:
    #   <input id="template_name" name="template_name" ...>
    #   Sender ID: Alpine.js multi-select — search input, type + Enter to add tags
    #   <select id="type" name="type"> options: Transactional, Promotional, OTP
    #   DLT ID: input with id/name containing 'dlt_id' or 'template_dlt_id'
    #           (may appear after Livewire detects an Indian sender)
    #   <textarea id="format" name="format"> — message content
    #   <textarea id="sample" name="sample"> — sample message
    #   Submit: <button type="submit">Save</button>  (Edit: "Update")
    FORM_TEMPLATE_NAME = "#template_name"
    FORM_TYPE = "#type"
    FORM_DLT_ID = "#template_id"   # wire:model.live="template_id"
    FORM_CONTENT = "#format"
    FORM_SAMPLE = "#sample"
    # Sender ID is a custom Alpine.js multi-select — use select_sender_ids() method
    BTN_ADD_SHORT_URL = "xpath=//button[contains(.,'Short URL')] | //a[contains(.,'Short URL')]"
    # Create: "Save" | Edit: "Update"
    BTN_SAVE = "xpath=//button[@type='submit' and (contains(.,'Save') or contains(.,'Update'))]"
    BTN_FORM_CANCEL = (
        "xpath=//a[contains(@href,'/channels/sms/template')] | "
        "//button[contains(.,'Cancel') and not(@data-tooltip-target)]"
    )
    # CONFIRMED via pasted DOM (two labels — "format" and "content_type" fields):
    #   <label class="text-sm text-negative-600 mt-2" for="format">The format field is required.</label>
    #   <label class="text-sm text-negative-600 mt-2" for="content_type">The content type field is required.</label>
    # Same WireUI pattern already confirmed on SMSSenderIDPage — none of the old
    # guessed classes ("invalid-feedback"/"text-danger"/"text-red"/"error") match.
    VALIDATION_ERROR = "label.text-negative-600, [class*='text-negative']"

    # ── Preview / View popup ──────────────────────────────────────────────────
    PREVIEW_POPUP = "[role='dialog'] >> visible=true, [class*='modal'] >> visible=true"
    BTN_CLOSE_PREVIEW = "xpath=//button[contains(.,'Close')] | //button[@aria-label='Close'] | //button[@aria-label='close']"

    # ── Toast ──────────────────────────────────────────────────────────────────
    TOAST_SUCCESS = (
        "xpath=//*[contains(text(),'success') or contains(text(),'Success') "
        "    or contains(text(),'Imported') or contains(text(),'successfully')] | "
        "//*[contains(@class,'toast') and not(contains(@class,'error'))]"
    )
    TOAST_ERROR = (
        "xpath=//*[contains(text(),'error') or contains(text(),'Error') "
        "    or contains(text(),'failed') or contains(text(),'Failed')] | "
        "//*[contains(@class,'toast-error') or contains(@class,'alert-danger')]"
    )

    # ══════════════════════════════════════════════════════════════════════════
    # Navigation
    # ══════════════════════════════════════════════════════════════════════════

    def navigate_via_sidebar(self):
        self.open(self.TEMPLATE_LIST_URL)
        self.page.wait_for_timeout(2000)
        url = self.get_current_url()
        
        # Recover if session expired
        if "login" in url.lower():
            from pages.common.login_page import LoginPage
            from utils.config import Config
            LoginPage(self.page).login(Config.VALID_EMAIL, Config.VALID_PASSWORD)
            self.page.wait_for_url(lambda u: "login" not in u.lower(), timeout=30000)
            self.open(self.TEMPLATE_LIST_URL)
            self.page.wait_for_timeout(2000)
            url = self.get_current_url()

        if "template" in url.lower() and "login" not in url.lower():
            self._close_sidebar_overlay()
            return self
        try:
            self.h.wait_for_element_clickable(self.NAV_SMS, timeout=10000).click()
            self.page.wait_for_timeout(500)
        except Exception:
            pass
        self.h.wait_for_element_clickable(self.NAV_TEMPLATES, timeout=10000).click()
        self.h.wait_for_url_contains("template", timeout=15000)
        self._close_sidebar_overlay()
        return self

    def is_template_list_page(self):
        """
        A real pytest run showed this loosely matching '/channels/sms/
        template/create' too (both contain 'template'), which made
        ensure_on_template_page() think it was already on the list page
        while actually stuck on the Create Template sub-page — since
        BTN_CREATE_TEMPLATE / BTN_UPLOAD_TEMPLATE only exist on the real
        list page, every subsequent test in the module-scoped session then
        failed the same way (button never found), cascading from one
        earlier test that got interrupted mid-create-flow. Excluding
        '/create' (and 'edit', for the same reason) makes this an accurate
        check again.
        """
        url = self.get_current_url().lower()
        return (
            "template" in url
            and "login" not in url
            and "/create" not in url
            and "/edit" not in url
        )

    # ══════════════════════════════════════════════════════════════════════════
    # List page helpers
    # ══════════════════════════════════════════════════════════════════════════

    def get_row_count(self):
        """Count data rows only — skips Livewire empty-state placeholder row."""
        rows = self.page.locator("table tbody tr")
        count = 0
        for i in range(rows.count()):
            row = rows.nth(i)
            tds = row.locator("td")
            if tds.count() == 0:
                continue
            row_text = row.inner_text().strip().lower()
            if any(kw in row_text for kw in ["no record", "no data", "no result",
                                              "no item", "not found", "empty", "no template"]):
                continue
            if any(t.strip() for t in tds.all_inner_texts()):
                count += 1
        return count

    def has_records(self):
        return self.get_row_count() > 0

    def has_no_records_message(self):
        return self.is_element_present(self.NO_RECORDS, timeout=5000) or self.get_row_count() == 0

    def search(self, value):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.fill(value)
        box.press("Enter")
        self.page.wait_for_timeout(2000)

    def clear_search(self):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        box.fill("")
        box.press("Enter")
        self.page.wait_for_timeout(1000)

    def is_template_present_in_list(self, name: str) -> bool:
        """Check if a template name appears in the list (exact or contains match).

        Strategy:
          1. Navigate fresh to ensure Livewire renders the latest data.
          2. Wait up to 5 s for the table to settle.
          3. Exact td text match first (fast path).
          4. contains() match as fallback (handles whitespace / badge wrapping).
          5. Search by name + recheck both match styles.
        """
        self.open(self.TEMPLATE_LIST_URL)
        self.page.wait_for_timeout(3000)   # give Livewire time to render after navigation
        self._close_sidebar_overlay()

        by_exact = f"xpath=//td[normalize-space()='{name}']"
        by_contains = f"xpath=//td[contains(normalize-space(),'{name}')]"

        if self.is_element_present(by_exact, timeout=5000):
            return True
        if self.is_element_present(by_contains, timeout=2000):
            return True

        # Search fallback
        try:
            self.search(name)
            self.page.wait_for_timeout(2000)
            if self.is_element_present(by_exact, timeout=5000):
                return True
            return self.is_element_present(by_contains, timeout=3000)
        except Exception:
            return False

    # ── Filters ────────────────────────────────────────────────────────────────

    def open_filter(self):
        self.h.wait_for_element_clickable(self.BTN_FILTER).click()
        self.page.wait_for_timeout(500)

    def diagnose_filter_control(self, locator, label):
        """Best-effort snapshot of a filter control, used to turn a blind
        'not found — update locator' skip into an actionable one.

        TC007-TC010 (sender ID / status / type / date range) wrap their
        filter call in try/except -> pytest.skip, a placeholder pattern
        inherited verbatim from the original Selenium suite (confirmed
        against the true Selenium source — same locators, same try/except,
        same 'UPDATE: match your app's status options' comment, never
        completed even there). That means every skip today is silent: we
        don't know if FILTER_STATUS/FILTER_TYPE simply don't match anything
        in the live filter panel, or if they match but the option label
        passed in ("Active"/"Transactional") doesn't exist verbatim in the
        real <option> list. This never raises -- it always returns a
        string, even when the control is completely absent, so the skip
        reason carries real evidence instead of a guess.
        """
        try:
            count = self.page.locator(locator).count()
        except Exception as e:
            return f"{label}: locator query itself raised ({e})"
        if count == 0:
            return f"{label}: 0 DOM matches for {locator!r} — control not present/not rendered"
        try:
            el = self.page.locator(locator).first
            tag = el.evaluate("n => n.tagName.toLowerCase()")
            visible = el.is_visible()
            info = f"{label}: {count} match(es), first=<{tag}> visible={visible}"
            if tag == "select":
                options = el.evaluate(
                    "n => Array.from(n.options).map(o => o.textContent.trim())"
                )
                info += f" available_options={options}"
            return info
        except Exception as e:
            return f"{label}: {count} match(es) but inspection raised ({e})"

    def filter_by_dlt_id(self, value):
        """DLT ID search uses the same search box as template name search."""
        self.search(value)

    def filter_by_status(self, status):
        self.open_filter()
        self.h.select_option(self.FILTER_STATUS, label=status)
        self.h.wait_for_element_clickable(self.BTN_APPLY_FILTER).click()
        self.page.wait_for_timeout(1500)

    def filter_by_type(self, type_val):
        self.open_filter()
        self.h.select_option(self.FILTER_TYPE, label=type_val)
        self.h.wait_for_element_clickable(self.BTN_APPLY_FILTER).click()
        self.page.wait_for_timeout(1500)

    # NOTE ON SOURCE FIDELITY: filter_by_sender_id(), filter_by_date_range(),
    # get_preview_verification_id() and click_add_short_url() below were
    # CALLED by the Selenium test files (test_sms_template_flow.py TC007/
    # TC010/TC018/TC019/TC032) but were never actually defined in the
    # Selenium source page object — a genuine gap in that file, not a
    # locator this conversion is guessing at. Each is implemented here using
    # ONLY this page object's own already-defined, already-confirmed
    # locators (FILTER_SENDER_ID, FILTER_FROM_DATE/FILTER_TO_DATE,
    # PREVIEW_POPUP, BTN_ADD_SHORT_URL) — no new DOM assumptions — and every
    # one degrades gracefully (raises on a genuinely missing control, or
    # returns None) exactly the way the calling tests already expect
    # (try/except → skip, or a None/falsy assertion failure) rather than
    # crashing with AttributeError as the original file would have.

    def filter_by_sender_id(self, value):
        """FILTER_SENDER_ID matches either a <select> or a plain <input> —
        detect which one rendered and interact accordingly."""
        self.open_filter()
        el = self.h.wait_for_element_visible(self.FILTER_SENDER_ID)
        tag = el.evaluate("node => node.tagName.toLowerCase()")
        if tag == "select":
            el.select_option(label=value)
        else:
            el.fill(value)
        try:
            self.h.wait_for_element_clickable(self.BTN_APPLY_FILTER, timeout=3000).click()
        except Exception:
            pass
        self.page.wait_for_timeout(1500)

    def filter_by_date_range(self, from_date, to_date):
        self.open_filter()
        self.h.wait_for_element_visible(self.FILTER_FROM_DATE).fill(str(from_date))
        self.h.wait_for_element_visible(self.FILTER_TO_DATE).fill(str(to_date))
        try:
            self.h.wait_for_element_clickable(self.BTN_APPLY_FILTER, timeout=3000).click()
        except Exception:
            pass
        self.page.wait_for_timeout(1500)

    # ── Export ─────────────────────────────────────────────────────────────────

    def export_to_xlsx(self, timeout_ms=30000):
        """
        Opens the Bulk Actions dropdown, then clicks Export, capturing the
        resulting download.

        A real pytest run showed this timing out on MENU_EXPORT even
        though the BTN_BULK_ACTIONS click itself didn't raise.
        BTN_BULK_ACTIONS matches ANY button containing the word 'Actions'
        (contains(text(),'Actions')), which is broad enough to match a
        per-row Actions menu instead of the real page-level Bulk Actions
        trigger, if one happens to appear earlier in the DOM — clicking
        the wrong one would open a menu that never contains 'Export'.
        Rather than trust the first match blindly, this tries each
        BTN_BULK_ACTIONS candidate in turn until one actually reveals an
        Export option, and raises a diagnostic error (what was tried, and
        how many candidates existed) if none of them do.

        The Export click itself is wrapped in page.expect_download() —
        same pattern as ContactsPage.export_to_xlsx() — so the file is
        actually captured and saved to DOWNLOAD_DIR instead of being
        clicked and discarded (the original version here only clicked and
        slept, returning nothing usable to the caller).

        Returns a dict: {"elapsed_s": float, "file_path": str,
        "file_size": int} — file_path is the saved download (whatever
        extension the app actually produces: .csv/.xlsx/.zip/etc.).
        """
        candidates = self.page.locator(self.BTN_BULK_ACTIONS)
        count = candidates.count()
        tried = []
        for i in range(count):
            btn = candidates.nth(i)
            try:
                btn.scroll_into_view_if_needed()
                btn.click(force=True)
                self.page.wait_for_timeout(500)
            except Exception:
                continue
            try:
                tried.append((btn.inner_text() or "").strip()[:40])
            except Exception:
                tried.append("?")
            try:
                export_el = self.h.wait_for_element_clickable(self.MENU_EXPORT, timeout=4000)
            except Exception:
                # Wrong dropdown (or none opened) — close it and try the
                # next BTN_BULK_ACTIONS candidate.
                try:
                    btn.click(force=True)
                except Exception:
                    pass
                continue

            start = time.time()
            with self.page.expect_download(timeout=timeout_ms) as dl_info:
                export_el.click()
            download = dl_info.value
            elapsed = round(time.time() - start, 2)
            dest = os.path.join(DOWNLOAD_DIR, download.suggested_filename)
            download.save_as(dest)
            return {"elapsed_s": elapsed, "file_path": dest, "file_size": os.path.getsize(dest)}

        raise RuntimeError(
            f"export_to_xlsx: could not find a working 'Bulk Actions' "
            f"trigger among {count} candidate(s) matching BTN_BULK_ACTIONS "
            f"(tried: {tried!r}) — none revealed an 'Export' option. The "
            f"locator is likely matching the wrong button (e.g. a per-row "
            f"Actions menu) instead of the real page-level Bulk Actions "
            f"control — needs a live-DOM check to narrow BTN_BULK_ACTIONS "
            f"to the correct one."
        )

    # ── Columns & Per Page ────────────────────────────────────────────────────

    def get_visible_column_headers(self):
        return self._get_headers_safe(self.COLUMN_HEADERS)

    def uncheck_first_optional_column(self):
        self.h.wait_for_element_clickable(self.BTN_COLUMNS).click()
        self.page.wait_for_timeout(400)
        checkboxes = self.page.locator(self.COLUMN_CHECKBOXES)
        for i in range(checkboxes.count()):
            cb = checkboxes.nth(i)
            if cb.is_checked():
                cb.click()
                self.page.wait_for_timeout(300)
                return True
        return False

    def set_per_page(self, value):
        try:
            self.h.select_option(self.PER_PAGE_SELECT, value=str(value))
        except Exception:
            self.h.wait_for_element_clickable(self.PER_PAGE_BTN).click()
            self.page.wait_for_timeout(300)
            self.page.locator(f"xpath=//li[text()='{value}'] | //option[text()='{value}']").first.click()
        self.page.wait_for_timeout(1000)

    def get_per_page_value(self):
        try:
            sel = self.page.locator(self.PER_PAGE_SELECT).first
            return sel.locator("option:checked").first.inner_text().strip()
        except Exception:
            return None

    def click_next_page(self):
        self._js_click(self.NEXT_PAGE_BTN + " >> visible=true", timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_next_page_enabled(self):
        """Returns True if the Next Page button exists, is visible, and is not disabled."""
        locators = self.page.locator(self.NEXT_PAGE_BTN).all()
        for loc in locators:
            if loc.is_visible():
                return loc.get_attribute("disabled") is None
        return False

    def is_prev_page_enabled(self):
        """Returns True if the Previous Page button exists, is visible, and is not disabled."""
        locators = self.page.locator(self.PREV_PAGE_BTN).all()
        for loc in locators:
            if loc.is_visible():
                return loc.get_attribute("disabled") is None
        return False


    def click_prev_page(self):
        self._js_click(self.PREV_PAGE_BTN + " >> visible=true", timeout=10000)
        self.page.wait_for_timeout(1500)


    # ── Row actions ────────────────────────────────────────────────────────────

    def click_first_row_view(self):
        btns = self.page.locator(self.ROW_VIEW_BTN)
        if btns.count() > 0:
            btns.first.click(force=True)
            self.page.wait_for_timeout(1000)
            return True
        return False

    def click_first_row_edit(self):
        """Navigate via href — same pattern as SenderID edit."""
        links = self.page.locator(self.ROW_EDIT_BTN)
        if links.count() == 0:
            return False
        href = links.first.get_attribute("href")
        if href:
            self.page.goto(href)
        else:
            links.first.click(force=True)
        self.page.wait_for_timeout(2000)
        return True

    def _dialog_visible(self, timeout=6000):
        """Return True if the WireUI confirm dialog is currently visible."""
        try:
            self.page.locator(self.CONFIRM_DELETE_BTN).first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def click_first_row_delete(self):
        """Click delete and wait for WireUI confirm dialog.
        Returns True only if the dialog actually appeared, False otherwise
        (caller should pytest.skip on False).

        Two strategies tried in sequence:
        1. Execute window.$wireui.confirmAction(...) directly from the button's
           x-on:click attribute — bypasses any tooltip overlay.
        2. Direct btn.click() — confirmed working in diagnostic fresh session.
        """
        btns = self.page.locator(self.ROW_DELETE_BTN)
        if btns.count() == 0:
            return False
        btn = btns.first
        btn.scroll_into_view_if_needed()
        self.page.wait_for_timeout(500)

        # Strategy 1: call $wireui.confirmAction directly via JS
        onclick = btn.get_attribute("x-on:click") or ""
        if onclick.strip().startswith("$wireui"):
            try:
                self.page.evaluate(f"window.{onclick.strip()}")
            except Exception:
                pass
            if self._dialog_visible(timeout=5000):
                return True

        # Strategy 2: direct Playwright click
        try:
            btn.click()
        except Exception:
            btn.evaluate(
                "el => el.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window}))"
            )
        if self._dialog_visible(timeout=8000):
            return True

        # Dialog never appeared after both strategies
        return False

    def confirm_delete(self):
        btn = self.h.wait_for_element_clickable(self.CONFIRM_DELETE_BTN, timeout=10000)
        btn.click(force=True)
        self.page.wait_for_timeout(2000)

    def cancel_delete(self):
        btn = self.h.wait_for_element_clickable(self.CANCEL_DELETE_BTN, timeout=10000)
        btn.click(force=True)
        self.page.wait_for_timeout(500)

    # ── Upload popup ──────────────────────────────────────────────────────────

    def click_upload_template(self):
        self._close_sidebar_overlay()
        self._js_click(self.BTN_UPLOAD_TEMPLATE)
        self.page.wait_for_timeout(1000)

    def is_upload_popup_open(self):
        return self.is_element_present(self.UPLOAD_POPUP, timeout=5000)

    def upload_file(self, filepath):
        fi = self.page.locator(self.FILE_INPUT).first
        fi.wait_for(state="attached", timeout=20000)
        self.page.evaluate(
            "(sel) => { const el = document.querySelector(sel); if (el) el.style.display = 'block'; }",
            self.FILE_INPUT
        )
        fi.set_input_files(os.path.abspath(filepath))
        try:
            self.page.locator(self.LOADER).first.wait_for(state="hidden", timeout=30000)
        except Exception:
            self.page.wait_for_timeout(2000)

    def click_download_sample(self):
        self.h.wait_for_element_clickable(self.BTN_DOWNLOAD_SAMPLE).click()
        self.page.wait_for_timeout(2000)

    def click_import(self):
        """Click 'Yes, Import' with a native Playwright click.

        A force/JS click is unreliable for buttons with wire:click / x-on:click
        handlers (same issue as the campaign 'Send Campaign' button). A native
        click ensures Livewire/Alpine event listeners fire.
        """
        btn = self.page.locator(self.BTN_IMPORT).first
        btn.wait_for(state="attached", timeout=20000)
        btn.scroll_into_view_if_needed()
        # Wait up to 5 s for the button to become enabled
        import time as _time
        deadline = _time.time() + 5
        while _time.time() < deadline:
            if btn.get_attribute("disabled") is None:
                break
            self.page.wait_for_timeout(200)
        try:
            btn.click()   # native click — fires Livewire/Alpine events
        except Exception:
            btn.click(force=True)
        self.page.wait_for_timeout(2000)

    def click_cancel_upload(self):
        try:
            self.h.wait_for_element_clickable(self.BTN_CANCEL_UPLOAD).click()
        except Exception:
            self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(500)

    def get_upload_error(self):
        try:
            elements = self.page.locator(self.UPLOAD_ERROR)
            for i in range(elements.count()):
                el = elements.nth(i)
                if el.is_visible():
                    text = el.inner_text().strip()
                    if text:
                        return text
        except Exception:
            pass
        return None

    def get_upload_success(self):
        try:
            elements = self.page.locator(self.UPLOAD_SUCCESS)
            for i in range(elements.count()):
                el = elements.nth(i)
                if el.is_visible():
                    text = el.inner_text().strip()
                    if text and "importing" not in text.lower() and "processing" not in text.lower():
                        return text
        except Exception:
            pass
        return None

    # ── Create / Edit Template form ───────────────────────────────────────────

    def click_create_template(self):
        self._close_sidebar_overlay()
        self._js_click(self.BTN_CREATE_TEMPLATE, timeout=15000)
        self.page.wait_for_timeout(2000)

    def is_create_button_visible(self):
        return self.is_element_present(self.BTN_CREATE_TEMPLATE, timeout=15000)

    def is_upload_button_visible(self):
        return self.is_element_present(self.BTN_UPLOAD_TEMPLATE, timeout=15000)

    def fill_template_name(self, value):
        self.h.clear_and_type(self.FORM_TEMPLATE_NAME, value)

    # ── Sender ID Alpine.js multi-select helpers ──────────────────────────────

    # XPath for the toggle button: covers both "Select one or more" initial state
    # and "N selected" state after selections have been made.
    _SENDER_TOGGLE_XPATH = (
        "xpath=//button[@type='button' and ("
        "  contains(.,'Select one or more')"
        "  or contains(.,'selected')"
        "  or contains(.,'dummy')"
        "  or contains(.,'AM-SMS')"
        ")]"
        " | "
        "//label[contains(.,'Sender')]/following-sibling::div//button[@type='button'][1]"
    )
    _SENDER_SEARCH_XPATH = (
        "xpath=//ul/preceding-sibling::input[@type='text']"
        " | "
        "//input[@type='text' and contains(@placeholder,'Search')]"
    )

    def _open_sender_dropdown(self):
        """Click the toggle button to open the Sender ID Alpine.js dropdown."""
        btn = self.page.locator(self._SENDER_TOGGLE_XPATH).first
        btn.wait_for(state="attached", timeout=8000)
        btn.scroll_into_view_if_needed()
        btn.click(force=True)
        self.page.wait_for_timeout(500)

    def _pick_sender_option(self, value: str):
        """Type *value* in the search box to filter, then click the matching <li>.

        The <li> items use @click="select(option['id'])" (Alpine.js). We filter
        by typing to avoid having to match case exactly, then click the first
        visible result.
        """
        # Type to filter
        try:
            sb = self.page.locator(self._SENDER_SEARCH_XPATH).first
            sb.fill(value)
            self.page.wait_for_timeout(400)
        except Exception:
            pass

        # Click first visible <li> in the filtered list (force click bypasses overlay)
        opts = self.page.locator("xpath=//li[contains(@class,'cursor-pointer')]")
        for i in range(opts.count()):
            opt = opts.nth(i)
            if opt.is_visible():
                opt.click(force=True)
                break
        self.page.wait_for_timeout(300)

    def select_sender_ids(self, values):
        """Select one or more sender IDs from the Alpine.js multi-select dropdown.

        For each value:
          1. Opens (or re-opens) the dropdown toggle.
          2. Types the value in the search box to filter the list.
          3. Clicks the first visible <li> — which calls select(option['id']).
        All exceptions are swallowed; sender IDs are optional for form submission.

        Args:
            values: list of sender ID strings, e.g. ["dummy", "AM-SMS"]
        """
        for value in values:
            if not value:
                continue
            try:
                self._open_sender_dropdown()
                self._pick_sender_option(value)
            except Exception:
                pass

        # Close the dropdown
        try:
            self.page.locator("body").click()
            self.page.wait_for_timeout(300)
        except Exception:
            pass

    def select_sender_id(self, value=""):
        """Convenience wrapper — select a single sender ID.

        For multiple IDs use select_sender_ids(values).
        """
        if value:
            self.select_sender_ids([value])

    def select_type(self, value):
        try:
            self.h.select_option(self.FORM_TYPE, label=value)
        except Exception:
            pass

    def fill_dlt_id(self, value):
        """Fill the DLT Template ID field (id='template_id', wire:model.live='template_id')."""
        self.h.clear_and_type(self.FORM_DLT_ID, value)

    def fill_content(self, value):
        self.h.clear_and_type(self.FORM_CONTENT, value)

    def fill_sample(self, value):
        self.h.clear_and_type(self.FORM_SAMPLE, value)

    def click_save(self):
        # JS click bypasses any sidebar overlay that may intercept regular clicks
        self._js_click(self.BTN_SAVE)
        self.page.wait_for_timeout(2000)

    def click_form_cancel(self):
        # JS click bypasses any sidebar overlay that may intercept regular clicks
        self._js_click(self.BTN_FORM_CANCEL)
        self.page.wait_for_timeout(1000)

    def get_validation_errors(self):
        errors = self.page.locator(self.VALIDATION_ERROR)
        texts = []
        for i in range(errors.count()):
            t = errors.nth(i).inner_text().strip()
            if t:
                texts.append(t)
        return texts

    def click_add_short_url(self):
        """See 'NOTE ON SOURCE FIDELITY' above filter_by_sender_id() — this
        method was called by the Selenium test suite but never defined in
        the Selenium source page object. Uses the already-defined
        BTN_ADD_SHORT_URL locator only."""
        self.h.wait_for_element_clickable(self.BTN_ADD_SHORT_URL, timeout=5000).click()
        self.page.wait_for_timeout(500)

    # ── Toast ──────────────────────────────────────────────────────────────────

    def is_success_toast_shown(self):
        return self.is_element_present(self.TOAST_SUCCESS, timeout=6000)

    def get_toast_error(self):
        """Safe — never throws. Returns visible error text or None."""
        try:
            elements = self.page.locator(self.TOAST_ERROR)
            for i in range(elements.count()):
                el = elements.nth(i)
                try:
                    if el.is_visible():
                        text = el.inner_text().strip()
                        if text:
                            return text
                except Exception:
                    continue
        except Exception:
            pass
        return None

    # ── Preview ───────────────────────────────────────────────────────────────

    def is_preview_open(self):
        return self.is_element_present(self.PREVIEW_POPUP, timeout=5000)

    def close_preview(self):
        try:
            self.h.wait_for_element_clickable(self.BTN_CLOSE_PREVIEW).click()
        except Exception:
            self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(500)

    def get_preview_verification_id(self):
        """See 'NOTE ON SOURCE FIDELITY' above filter_by_sender_id() — this
        method was called by the Selenium test suite but never defined in
        the Selenium source page object. Implemented as a generic
        label-adjacent text lookup scoped to PREVIEW_POPUP (same pattern
        already used elsewhere in this project, e.g.
        sms_message_page._popup_text_by_label) — returns None (rather than
        guessing at a specific field id) if no 'Verification'-labelled
        value can be found, which the calling test already treats as a
        legitimate assertion failure, not a crash."""
        try:
            candidates = self.page.locator(
                "xpath=(//*[contains(.,'Verification')]/following-sibling::*)[1] | "
                "(//*[contains(.,'Verification')]/../following-sibling::*)[1]"
            )
            for i in range(candidates.count()):
                el = candidates.nth(i)
                if not el.is_visible():
                    continue
                txt = el.inner_text().strip()
                if txt and "verification" not in txt.lower():
                    return txt
        except Exception:
            pass
        return None

    # ── Static validation (no browser) ────────────────────────────────────────

    @staticmethod
    def is_valid_template_name(name: str) -> bool:
        """Template name: 3–100 chars, no leading/trailing spaces."""
        if not name or not name.strip():
            return False
        name = name.strip()
        return 3 <= len(name) <= 100

    @staticmethod
    def is_valid_dlt_id(dlt_id: str) -> bool:
        """DLT Template ID: 10–20 digits."""
        if not dlt_id:
            return False
        return dlt_id.isdigit() and 10 <= len(dlt_id) <= 20

    @staticmethod
    def generate_dlt_id() -> str:
        """Generate a random 12-digit DLT Template ID for testing."""
        import random
        return ''.join([str(random.randint(0, 9)) for _ in range(12)])
