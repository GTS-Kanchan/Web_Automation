import re

from pages.common.base_page import BasePage


class WhatsAppCampaignReportPage(BasePage):
    """Page object for the per-campaign "Campaign Report" page
    (/whatsapp/campaigns/messages/<campaignId>) -- reached from the
    Campaign LISTING page by clicking the document/"Reports" icon in the
    Action column (see pages/whatsapp/whatsapp_campaign_page.py). Built
    entirely from a genuine live DOM dump of this page for campaign id
    1418 (Livewire components 'whatsapp.campaign.summary-cards' for the
    stat cards and 'whatsapp.campaign.message.table', table name literally
    "table", for the message list).

    Confirmed facts driving every locator/method below:

    1. The page has NO fixed URL of its own -- the campaign id is part of
       the path (`/whatsapp/campaigns/messages/<id>`), so this page object
       has no `navigate()`/`REPORT_URL` the way every other page in this
       project does. Tests reach it via
       WhatsAppCampaignPage.click_reports_link_on_first_row(), then use
       `get_campaign_id_from_url()` / `navigate_to_campaign_id()` here to
       recover to the SAME campaign's report page if a test navigates away.
    2. The <h1> title is NOT a static string -- it renders as
       "<date/time> - Campaign " (a schedule timestamp prefix), confirmed
       in the captured DOM ("September 2 2026 12:37 PM - Campaign "). No
       test asserts its exact text, only that it renders non-empty.
    3. STATS CARDS ('whatsapp.campaign.summary-cards') are the SAME
       component already used in the eye/"View" icon's "Campaign Details"
       quick-view popup on the listing page, but HERE they are rendered
       inline on the page itself and are genuinely clickable plain <div>s
       with `onclick="window.location='?metric=<value>'"` (a real page
       navigation via query string, not a Livewire action). CONFIRMED
       clickable metrics: total, submitted, delivered, read, dlr_awaited,
       failed, rejected, quick_reply_total, cta_total_clicks, user_reply.
       CONFIRMED NOT clickable (class "opacity-60 stats-card", no onclick):
       Delivery Rate, Quick Reply Unique, CTA Unique Clicks. This inline,
       clickable rendering is what the QA checklist's "New Enhancement
       Changes" section (TC044-051, "clickable cards") describes -- those
       steps literally read "Goto Campaign >> Click on Campaign reports"
       then interact with the cards, i.e. THIS SAME page, not a separate
       one.
    4. The FILTER PANEL has exactly 3 real fields (`filterCount: 3`,
       confirmed in the Livewire snapshot): a Status <select> and genuine
       Created From / Created To date+time Alpine pickers -- UNLIKE the
       Campaign listing page, this page DOES have a real date range
       filter. No dedicated "Clear all filters" button exists here either
       (only a "Clear" pill for SORTS, `wire:click.prevent="clearSorts"`,
       confirmed distinct from any filter-clearing control) --
       `clear_all_filters()` resets each real control individually.
    5. Search box placeholder is CONFIRMED "Search Mobile Number" (matches
       the Messages Report tab, NOT the Campaign listing page's "Search
       Campaign Name").
    6. Export is a PLAIN ANCHOR (not a confirm-modal like the listing
       page's Export to XLSX), with a confirmed href pattern
       `.../whatsapp/campaign/<uuid>/messages/export?metric=<active
       metric>&columns[N]=<column>...` -- the active metric and currently
       selected columns are both reflected in the href, confirmed directly
       in the captured markup.
    7. Only the "Contact" column is sortable (`wire:click="sortBy('number')"`)
       -- every other header (Country Code, Status, Is MM Lite Used,
       Created At, Sent At, Delivered At, Failed At, Read At) is a plain
       non-interactive <span>, confirmed by direct inspection of every
       <th> in the captured table. Default sort is Sent At (desc).
    8. The "All Columns" checkbox here is CHECKED BY DEFAULT and wired to
       `wire:click="deselectAllColumns"` -- the INVERSE of the Campaign
       listing page's `selectAllColumns` convention. Individual column
       checkboxes (`selectedColumns`) behave the same way as elsewhere.
       Selectable columns confirmed: action, contact, country-code,
       status, is-mm-lite-used, created-at, sent-at, delivered-at,
       failed-at, read-at (no "source"/"sub-source"/"template-category"
       columns exist on this table, unlike the Messages Report tab).
    9. The row "View" action dispatches the SAME shared Livewire component
       already fully automated for the Messages Report tab --
       'whatsapp.campaign.message.view' (confirmed identical
       `$dispatch('openModal', ...)` call, same "Message Details" popup
       markup for the same message id, 129644, appearing in both this
       page's table and the Messages tab's table). The message-detail
       modal locators/getters below are therefore an intentional,
       confirmed-safe DUPLICATE of the ones in
       pages/whatsapp/whatsapp_message_report_page.py (this project's
       convention keeps pages/whatsapp/ flat with no cross-page
       inheritance or mixins -- confirmed by inspecting the rest of
       pages/ -- so the shared component's locators are copied here
       rather than imported).
    10. PAGINATION: this specific campaign only has 2 messages ("Showing 1
        to 2"), so no page-number/Next/Prev controls are rendered in the
        captured DOM -- forward/backward pagination locators below are
        INFERRED from the identical, already-confirmed pagination package
        convention used on every other table in this app (`nextPage`/
        `previousPage` with the table's own name, "table", giving
        `tablePage`), consistent with the same documented-inference
        pattern already used on the Messages Report and Campaign listing
        pages. Tests using them must gracefully skip if a control isn't
        actually enabled, exactly like those other suites.
    """

    TABLE_NAME = "table"

    # ── Page header / breadcrumb ─────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(@class,'text-md') and contains(@class,'font-semibold')]"
    BREADCRUMB = "xpath=//nav[@aria-label='Breadcrumb']"

    # ── Top actions ──────────────────────────────────────────────────────────
    REFRESH_LINK = "xpath=//a[contains(normalize-space(.),'Refresh')]"
    BACK_LINK = "xpath=//a[contains(normalize-space(.),'Back')]"

    # ── Stats cards ('whatsapp.campaign.summary-cards') -- see class
    # docstring caveat #3. ────────────────────────────────────────────────
    CLICKABLE_METRICS = (
        "total", "submitted", "delivered", "read", "dlr_awaited", "failed",
        "rejected", "quick_reply_total", "cta_total_clicks", "user_reply",
    )
    NON_CLICKABLE_STATS_LABELS = ("Delivery Rate", "Quick Reply Unique", "CTA Unique Clicks")

    MODAL_CONTAINER = "#modal-container"

    # ── "View" popup internals (component 'whatsapp.campaign.message.view')
    # -- CONFIRMED IDENTICAL to the popup already automated on the Messages
    # Report page; see class docstring caveat #9. ───────────────────────────
    MODAL_TITLE = "xpath=//h3[normalize-space(.)='Message Details']"
    MODAL_CLOSE_BUTTON = "xpath=//button[contains(@*[name()='wire:click'],'closeModal')]"
    MODAL_CURRENT_STATUS = "xpath=//p[normalize-space(.)='Current Status']/preceding-sibling::h4[1]"
    MODAL_CONTACT_NUMBER = "xpath=//p[normalize-space(.)='Contact Number']/following-sibling::p[1]"
    MODAL_CATEGORY_TYPE = "xpath=//p[normalize-space(.)='Category Type']/following-sibling::span[1]"
    MODAL_MESSAGE_CONTENT = (
        "xpath=//h4[contains(normalize-space(.),'Message Content')]/parent::div"
        "//p[contains(@class,'whitespace-pre-wrap')]"
    )
    MODAL_SECTION_BASIC_INFO = "Basic Information"
    MODAL_SECTION_WABA_INFO = "WABA Information"
    MODAL_SECTION_TEMPLATE_DETAILS = "Template Details"
    MODAL_SECTION_CAMPAIGN_INFO = "Campaign Information"
    MODAL_SECTION_TIMELINE = "Timeline"

    # ── Search (CONFIRMED placeholder "Search Mobile Number" -- see class
    # docstring caveat #5) ───────────────────────────────────────────────────
    SEARCH_BOX = "input[wire\\:model\\.live='search'][placeholder='Search Mobile Number']"

    # ── Filters (slide-down panel) -- 3 real fields, see class docstring
    # caveat #4 ──────────────────────────────────────────────────────────────
    FILTERS_BUTTON = "xpath=//button[contains(normalize-space(.),'Filters')]"
    FILTER_STATUS = f"#{TABLE_NAME}-filter-status"
    FILTER_CREATED_FROM_WRAPPER = f"#{TABLE_NAME}-filter-created_from-wrapper"
    FILTER_CREATED_TO_WRAPPER = f"#{TABLE_NAME}-filter-created_to-wrapper"

    # ── Export (plain anchor, reflects active metric + selected columns --
    # see class docstring caveat #6) ────────────────────────────────────────
    EXPORT_CSV_LINK = (
        "xpath=//a[contains(@href,'/messages/export') and contains(normalize-space(.),'Export CSV')]"
    )

    # ── Sorting -- ONLY Contact is sortable, see class docstring caveat #7 ──
    SORT_CONTACT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('number')\")]"
    CLEAR_ALL_SORTS_BTN = "xpath=//button[contains(@*[name()='wire:click.prevent'],'clearSorts')]"
    APPLIED_SORT_PILL = f"xpath=//span[contains(@*[name()='wire:key'],'{TABLE_NAME}-sorting-pill-')]"

    # ── Columns dropdown -- "All Columns" default state is INVERTED here,
    # see class docstring caveat #8 ─────────────────────────────────────────
    COLUMNS_BUTTON = "xpath=//button[contains(normalize-space(.),'Columns')]"
    COLUMN_CHECKBOXES = (
        f"xpath=//div[contains(@*[name()='wire:key'],'{TABLE_NAME}-columnSelect-') and "
        f"not(contains(@*[name()='wire:key'],'columnSelect-selectAll'))]//input[@type='checkbox']"
    )
    SELECT_ALL_COLUMNS_CHECKBOX = (
        f"xpath=//div[contains(@*[name()='wire:key'],'{TABLE_NAME}-columnSelect-selectAll-')]//input[@type='checkbox']"
    )

    # ── Table ────────────────────────────────────────────────────────────────
    TABLE = f"#table-{TABLE_NAME}"
    TABLE_HEADERS = f"#table-{TABLE_NAME} thead th"
    TABLE_ROWS = f"#table-{TABLE_NAME} tbody tr"
    NO_RECORDS_MSG = (
        "xpath=//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no items found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no record') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no data') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no result') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'not found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'nothing found')]"
    )

    # ── Row action: View (opens the shared message-detail modal) ────────────
    VIEW_ICON_IN_ROW = "xpath=.//*[contains(@data-tooltip-target,'tooltip-view-')]"

    # ── Pagination -- INFERRED, see class docstring caveat #10 ──────────────
    PAGINATION_RESULTS_TEXT = ".paged-pagination-results"
    NEXT_PAGE_BTN = f"xpath=//button[contains(@*[name()='wire:click'],\"nextPage('{TABLE_NAME}Page')\")]"
    PREV_PAGE_BTN = f"xpath=//button[contains(@*[name()='wire:click'],\"previousPage('{TABLE_NAME}Page')\")]"

    # ── User menu / logout (global header) ──────────────────────────────────
    USER_MENU_BUTTON = "xpath=//button[contains(@class,'rounded-full') and .//img]"
    LOGOUT_LINK = "xpath=//a[@title='Log out']"

    # ── Navigation / page state ──────────────────────────────────────────────

    def navigate_to_campaign_id(self, campaign_id):
        self.open(f"/whatsapp/campaigns/messages/{campaign_id}")
        self.page.wait_for_timeout(2000)
        return self

    def get_campaign_id_from_url(self):
        match = re.search(r"/whatsapp/campaigns/messages/(\d+)", self.get_current_url())
        return match.group(1) if match else None

    def remember_campaign_id(self):
        """Caches the campaign id confirmed from the current URL so
        ensure_on_report_page() can recover to THIS SAME campaign's report
        page even after a test navigates away (e.g. via the Back link)."""
        cid = self.get_campaign_id_from_url()
        if cid:
            self._campaign_id = cid
        return cid

    def is_campaign_report_page(self):
        url = self.get_current_url()
        return "/whatsapp/campaigns/messages/" in url and "login" not in url.lower()

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

    def _set_input_value(self, locator_or_element, value, event="input"):
        el = locator_or_element if hasattr(locator_or_element, "evaluate") else self.page.locator(locator_or_element).first
        el.evaluate(
            "(elm, args) => { elm.value = args[0];"
            "elm.dispatchEvent(new Event(args[1], {bubbles: true})); }",
            [value, event]
        )

    # ── Top actions ──────────────────────────────────────────────────────────

    def click_refresh(self):
        with self.page.expect_navigation(timeout=15000):
            self._js_click(self.REFRESH_LINK, timeout=10000)
        self.page.wait_for_timeout(1000)

    # ── Stats cards ──────────────────────────────────────────────────────────

    def stats_card_locator(self, metric):
        return f"xpath=//div[@onclick=\"window.location='?metric={metric}'\"]"

    def get_stats_card_value(self, metric):
        card = self.h.wait_for_element_visible(self.stats_card_locator(metric), timeout=8000)
        value_el = card.locator(".stats-value").first
        return value_el.inner_text().strip()

    def click_stats_card(self, metric):
        locator = self.stats_card_locator(metric)
        with self.page.expect_navigation(timeout=15000):
            self._js_click(locator, timeout=10000)
        self.page.wait_for_timeout(1000)

    def is_metric_active(self, metric):
        url = self.get_current_url()
        if f"metric={metric}" in url:
            return True
        # "total" is the confirmed default active metric when no ?metric=
        # query param is present at all (activeMetric:"total" in the
        # captured Livewire snapshot).
        return metric == "total" and "metric=" not in url

    def get_non_clickable_stat_value(self, label):
        xpath = (
            f"xpath=//div[contains(@class,'stats-card') and contains(@class,'opacity-60')]"
            f"[.//span[normalize-space(text())='{label}']]//div[contains(@class,'stats-value')]"
        )
        el = self.h.wait_for_element_visible(xpath, timeout=8000)
        return el.inner_text().strip()

    # ── Search ───────────────────────────────────────────────────────────────

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
        self._set_input_value(box, value, "input")
        box.evaluate("el => el.dispatchEvent(new Event('change', {bubbles: true}))")
        self.page.wait_for_timeout(500)
        self._wait_for_search_to_settle()
        self.page.wait_for_timeout(300)

    def clear_search(self):
        box = self.h.wait_for_element_visible(self.SEARCH_BOX)
        self._set_input_value(box, "", "input")
        box.evaluate("el => el.dispatchEvent(new Event('change', {bubbles: true}))")
        self.page.wait_for_timeout(500)
        self._wait_for_search_to_settle()
        self.page.wait_for_timeout(300)

    # ── Table / rows ─────────────────────────────────────────────────────────

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

    def get_column_values(self, header_substring):
        headers = self.get_visible_column_headers()
        idx = None
        for i, h in enumerate(headers):
            if header_substring.lower() in h.lower():
                idx = i
                break
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
        return self._first_visible_data_row(f"#table-{self.TABLE_NAME} tbody tr")

    # ── Sorting -- only Contact, see class docstring caveat #7 ──────────────

    def sort_by_contact(self):
        self._js_click(self.SORT_CONTACT_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def get_applied_sort_pill_text(self):
        if self.is_element_present(self.APPLIED_SORT_PILL, timeout=3000):
            return self.h.wait_for_element_visible(self.APPLIED_SORT_PILL).inner_text().strip()
        return None

    def clear_all_sorts(self):
        self._js_click(self.CLEAR_ALL_SORTS_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    # ── Filters (slide-down panel) ───────────────────────────────────────────

    def open_filters_panel(self):
        if self._is_visible(self.FILTER_STATUS, timeout=1000):
            return
        self._js_click(self.FILTERS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def set_status_filter(self, value):
        """value: '' | 'rejected' | 'pending' | 'read' | 'delivered' |
        'sent' | 'failed' (options CONFIRMED in the live <select>)."""
        self.open_filters_panel()
        self.h.wait_for_element_visible(self.FILTER_STATUS)
        self.h.select_option(self.FILTER_STATUS, value=value)
        self.page.wait_for_timeout(1200)

    def _date_input_in_wrapper(self, wrapper_locator):
        wrapper = self.h.wait_for_element_visible(wrapper_locator)
        return wrapper.locator("input[type='date']").first

    def _time_select_in_wrapper(self, wrapper_locator):
        wrapper = self.h.wait_for_element_visible(wrapper_locator)
        return wrapper.locator("select").first

    def set_created_from_filter(self, date_value, time_value=None):
        self.open_filters_panel()
        date_el = self._date_input_in_wrapper(self.FILTER_CREATED_FROM_WRAPPER)
        self._set_input_value(date_el, date_value, "input")
        self.page.wait_for_timeout(300)
        if time_value:
            time_el = self._time_select_in_wrapper(self.FILTER_CREATED_FROM_WRAPPER)
            time_el.select_option(value=time_value)
        else:
            date_el.evaluate("el => el.dispatchEvent(new Event('change', {bubbles: true}))")
        self.page.wait_for_timeout(1200)

    def set_created_to_filter(self, date_value, time_value=None):
        self.open_filters_panel()
        date_el = self._date_input_in_wrapper(self.FILTER_CREATED_TO_WRAPPER)
        self._set_input_value(date_el, date_value, "input")
        self.page.wait_for_timeout(300)
        if time_value:
            time_el = self._time_select_in_wrapper(self.FILTER_CREATED_TO_WRAPPER)
            time_el.select_option(value=time_value)
        else:
            date_el.evaluate("el => el.dispatchEvent(new Event('change', {bubbles: true}))")
        self.page.wait_for_timeout(1200)

    def set_date_range_filter(self, from_date, to_date, from_time=None, to_time=None):
        self.set_created_from_filter(from_date, from_time)
        self.set_created_to_filter(to_date, to_time)

    def get_filter_date_values(self):
        # input_value(), not get_attribute("value") -- these fields are set
        # via this file's own _set_input_value()'s elm.value = ... (a live
        # DOM PROPERTY assignment), which never touches the static HTML
        # value attribute. Identical code/bug to the sibling Message Report
        # page's get_filter_date_values(), confirmed broken there by a real
        # run (get_attribute("value") returned None right after a date was
        # set). Same proven fix already used on the WhatsApp Incoming
        # Messages page and the RCS Opt-out page's get_filter_values().
        self.open_filters_panel()
        from_el = self._date_input_in_wrapper(self.FILTER_CREATED_FROM_WRAPPER)
        to_el = self._date_input_in_wrapper(self.FILTER_CREATED_TO_WRAPPER)
        return from_el.input_value(), to_el.input_value()

    def clear_all_filters(self):
        """No dedicated "Clear all filters" button exists on this page
        (see class docstring caveat #4) -- resets the Status select and
        both date inputs individually instead."""
        self.open_filters_panel()
        try:
            self.h.select_option(self.FILTER_STATUS, value="")
        except Exception:
            pass
        try:
            date_el = self._date_input_in_wrapper(self.FILTER_CREATED_FROM_WRAPPER)
            self._set_input_value(date_el, "", "change")
        except Exception:
            pass
        try:
            date_el = self._date_input_in_wrapper(self.FILTER_CREATED_TO_WRAPPER)
            self._set_input_value(date_el, "", "change")
        except Exception:
            pass
        self.page.wait_for_timeout(1200)

    # ── Export ───────────────────────────────────────────────────────────────

    def get_export_csv_href(self):
        el = self.h.wait_for_element_visible(self.EXPORT_CSV_LINK)
        return el.get_attribute("href")

    # ── Columns dropdown ─────────────────────────────────────────────────────

    def open_columns_dropdown(self):
        if self._is_visible(self.COLUMN_CHECKBOXES, timeout=1000):
            return
        self._js_click(self.COLUMNS_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)

    def toggle_column(self, value):
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

    # ── Row action: View ─────────────────────────────────────────────────────

    def click_view_on_first_row(self):
        row = self.get_first_data_row()
        if row is None:
            return False
        try:
            btn = row.locator(self.VIEW_ICON_IN_ROW).first
            if btn.count() == 0:
                return False
        except Exception:
            return False
        btn.scroll_into_view_if_needed()
        btn.click(force=True)
        self.page.wait_for_timeout(1500)
        return True

    def is_modal_open(self):
        try:
            return self.page.locator(self.MODAL_CONTAINER).first.is_visible()
        except Exception:
            return False

    def is_message_view_popup_open(self):
        return self.is_element_present(self.MODAL_TITLE, timeout=5000)

    def close_message_view_popup(self):
        self._js_click(self.MODAL_CLOSE_BUTTON, timeout=5000)
        self.page.wait_for_timeout(500)

    def get_modal_current_status(self):
        el = self.h.wait_for_element_visible(self.MODAL_CURRENT_STATUS, timeout=8000)
        return el.inner_text().strip()

    def get_modal_contact_number(self):
        el = self.h.wait_for_element_visible(self.MODAL_CONTACT_NUMBER, timeout=8000)
        return el.inner_text().strip()

    def get_modal_category_type(self):
        el = self.h.wait_for_element_visible(self.MODAL_CATEGORY_TYPE, timeout=8000)
        return el.inner_text().strip()

    def get_modal_message_content(self):
        el = self.h.wait_for_element_visible(self.MODAL_MESSAGE_CONTENT, timeout=8000)
        return el.inner_text().strip()

    def _modal_section_field(self, section_heading, label, timeout=8000):
        xpath = (
            f"xpath=//h4[contains(normalize-space(.),'{section_heading}')]/parent::div"
            f"//span[normalize-space(text())='{label}:']/following-sibling::span[1]"
        )
        el = self.h.wait_for_element_visible(xpath, timeout=timeout)
        return el.inner_text().strip()

    def get_modal_basic_info_field(self, label):
        return self._modal_section_field(self.MODAL_SECTION_BASIC_INFO, label)

    def get_modal_waba_field(self, label):
        return self._modal_section_field(self.MODAL_SECTION_WABA_INFO, label)

    def get_modal_template_field(self, label):
        return self._modal_section_field(self.MODAL_SECTION_TEMPLATE_DETAILS, label)

    def get_modal_campaign_info_field(self, label):
        return self._modal_section_field(self.MODAL_SECTION_CAMPAIGN_INFO, label)

    def get_modal_timeline_field(self, label, timeout=3000):
        xpath = (
            f"xpath=//h4[contains(normalize-space(.),'{self.MODAL_SECTION_TIMELINE}')]/parent::div"
            f"//span[normalize-space(text())='{label}:']/following-sibling::span[1]"
        )
        if not self.is_element_present(xpath, timeout=timeout):
            return None
        return self.page.locator(xpath).first.inner_text().strip()

    def has_button_click_section(self):
        return self.is_element_present(
            "xpath=//h4[contains(normalize-space(.),'Button Click')]", timeout=3000
        )

    def has_error_section(self):
        return self.is_element_present(
            "xpath=//h4[contains(normalize-space(.),'Error')]", timeout=3000
        )

    # ── Pagination ───────────────────────────────────────────────────────────

    def get_pagination_results_text(self):
        el = self.h.wait_for_element_visible(self.PAGINATION_RESULTS_TEXT)
        return el.inner_text().strip()

    def click_next_page(self):
        self._js_click(self.NEXT_PAGE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_next_page_enabled(self):
        try:
            return self.page.locator(self.NEXT_PAGE_BTN).first.count() > 0
        except Exception:
            return False

    def is_prev_page_enabled(self):
        try:
            return self.page.locator(self.PREV_PAGE_BTN).first.count() > 0
        except Exception:
            return False

    def click_prev_page(self):
        self._js_click(self.PREV_PAGE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    # ── Logout ───────────────────────────────────────────────────────────────

    def logout(self):
        self._js_click(self.USER_MENU_BUTTON, timeout=10000)
        self.page.wait_for_timeout(500)
        self._js_click(self.LOGOUT_LINK, timeout=10000)
        self.page.wait_for_timeout(1500)
