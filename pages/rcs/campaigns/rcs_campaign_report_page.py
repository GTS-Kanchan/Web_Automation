import os
import re
import time

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR


class RCSCampaignReportPage(BasePage):
    """Page object for the per-campaign RCS "Campaign Report" page --
    reached per-campaign, from the RCS Campaign listing page
    (pages/rcs/campaigns/rcs_campaign_page.py::RCSCampaignPage), by
    clicking the confirmed "Reports" link on a campaign row
    (RCSCampaignPage.click_reports_icon_on_row()). NOT the same page as
    pages/rcs/campaigns/rcs_campaign_analytics_page.py (that one is the
    AGGREGATE analytics report listing every campaign).

    Built entirely from real, pasted DOM captures (never fabricated):

    1. URL shape (confirmed): /rcs/campaign/messages/<metric>/<campaignId>,
       e.g. ".../rcs/campaign/messages/total/01a0e872-be6f-71d5-a9ae-
       dfb4e4e7893a". The metric is a path segment ("total", ...), the
       campaign id a UUID. "Back" button on this page links to
       "/rcs/campaign" (the Campaign List), confirming the relationship.
    2. Breadcrumb (confirmed): Home > Channels > RCS Campaigns > RCS
       Campaign Report (last segment a plain, non-link <span>).
    3. Summary/stat cards (confirmed, `#campaign-stats-wrap` /
       `.stats-card` divs): Total Messages, Submitted, Delivered, Read,
       Failed, DLR Awaited, Rejected, Delivery Rate, Quick Reply Unique,
       Quick Reply Total, CTA Unique Clicks, CTA Total Clicks, User
       Replies -- each `onclick="window.location='.../rcs/campaign/
       messages/<metric>/<campaignId>'"`.
    4. Table: Livewire component `rcs.campaign.message.total-table`,
       CONFIRMED generic ids `table`/`#table-table` (NOT a prefixed
       `rcs_campaign_report`-style TABLE_NAME like other pages'
       convention). 8 real columns in DOM order: Action, Contact,
       Status, Created At, Submitted At, Delivered At, Read At, Failed
       At -- only Contact, Status and Created At are sortable
       (`sortBy('number')`, `sortBy('status')`, `sortBy('created_at')`);
       Action/Submitted At/Delivered At/Read At/Failed At are plain,
       non-sortable spans. A missing event's timestamp cell renders the
       em-dash placeholder "--", same convention used elsewhere in this
       project.
    5. Search: `<input wire:model.live="search"
       placeholder="Search Mobile Number">`.
    6. Status filter: `<select wire:model.live="filterComponents.status">`
       with options "" / "queued" / "sent" / "delivered" / "read" /
       "failed" / "rejected" (labels All/Pending/Sent/Delivered/Read/
       Failed/Rejected).
    7. Export: a plain `<a href="https://<host>/rcs/campaign/<campaignId>
       /messages/export?table=TotalTable">Export CSV</a>` -- NO confirm
       modal (direct link, unlike several WhatsApp pages).
    8. Row "View" action (CONFIRMED): same tooltip-view pattern as every
       other page in this suite --
       `<button data-tooltip-target="tooltip-view-<messageId>"
         wire:click.prevent="$dispatch('openModal', { component:
         'rcs.campaign.message.view', arguments: {"messageId":...,
         "date":...} })">`, tooltip text "View".
    9. Message View popup (CONFIRMED via a real, pasted opened-modal
       capture): heading "Message Details" -- IDENTICAL markup/shape to
       pages/rcs/messaging/rcs_message_page.py::RcsMessagePage's own
       "Message Details" popup (same POPUP_HEADING, same Timeline
       `<span>{Field}:</span><span>{value}</span>` pairs for Created/
       Scheduled/Submitted/Delivered/Read/Failed, each conditionally
       rendered -- a field not yet reached is simply absent from the
       DOM, not rendered blank). Since this is the SAME Livewire
       component/markup, this page reuses RcsMessagePage's confirmed
       popup readers (is_popup_open/close_popup/get_popup_*) via
       message_details_popup(), rather than duplicating them -- same
       pattern already used by
       pages/sms/campaigns/sms_campaign_message_report_page.py's
       message_details_popup().
    """

    # -- Navigation / page state ---------------------------------------------

    def navigate_to_campaign(self, campaign_id, metric="total"):
        self.open(f"/rcs/campaign/messages/{metric}/{campaign_id}")
        self.page.wait_for_timeout(2000)
        return self

    def get_campaign_id_from_url(self):
        match = re.search(
            r"/rcs/campaign/messages/[^/]+/([0-9a-fA-F-]{36})", self.get_current_url()
        )
        return match.group(1) if match else None

    def get_active_metric_from_url(self):
        match = re.search(
            r"/rcs/campaign/messages/([^/]+)/[0-9a-fA-F-]{36}", self.get_current_url()
        )
        return match.group(1) if match else None

    def is_report_page(self):
        url = self.get_current_url()
        return "/rcs/campaign/messages/" in url and "login" not in url.lower()

    def wait_for_spinner_to_disappear(self):
        try:
            self.page.locator(".spinner, .loading, [wire\\:loading]").first.wait_for(
                state="hidden", timeout=5000)
        except Exception:
            pass
        self.page.wait_for_timeout(500)

    # -- Breadcrumb -----------------------------------------------------------

    BREADCRUMB_LAST = (
        "xpath=//*[normalize-space(text())='RCS Campaign Report']"
    )

    def is_breadcrumb_visible(self):
        try:
            return self.page.locator(self.BREADCRUMB_LAST).first.is_visible()
        except Exception:
            return False

    # -- Stat cards -------------------------------------------------------------

    ALL_CARD_NAMES = (
        "Total Messages", "Submitted", "Delivered", "Read", "Failed",
        "DLR Awaited", "Rejected", "Delivery Rate",
        "Quick Reply Unique", "Quick Reply Total",
        "CTA Unique Clicks", "CTA Total Clicks", "User Replies",
    )

    def _card_by_label_xpath(self, name):
        """Same confirmed direct-child nesting already established for
        the sibling SMS report page's stat cards -- see
        SmsCampaignMessageReportPage._card_by_label_xpath()'s docstring
        for why matching the label as a direct child (not a `.//p`
        descendant) is required to land on the real card div rather
        than an outer container."""
        return f"xpath=//div[p[normalize-space(text())='{name}']]/../.."

    def is_card_visible(self, name):
        return self.is_element_visible(self._card_by_label_xpath(name), timeout=8000)

    def get_card_value(self, name):
        card = self.h.wait_for_element_visible(self._card_by_label_xpath(name))
        paragraphs = card.locator("p")
        return paragraphs.nth(1).inner_text().strip()

    # -- Search / filter --------------------------------------------------------

    INPUT_SEARCH = "input[placeholder='Search Mobile Number']"
    SELECT_FILTER_STATUS = "select[wire\\:model\\.live='filterComponents.status']"

    def search_mobile_number(self, term: str):
        self.wait_for_spinner_to_disappear()
        inp = self.h.wait_for_element_visible(self.INPUT_SEARCH)
        inp.fill(term)
        self.page.wait_for_timeout(1000)
        self.wait_for_spinner_to_disappear()
        self.page.wait_for_timeout(1000)

    def set_status_filter(self, value: str):
        """*value* is one of the confirmed option values: "", "queued",
        "sent", "delivered", "read", "failed", "rejected"."""
        try:
            self.h.select_option(self.SELECT_FILTER_STATUS, value=value)
            self.wait_for_spinner_to_disappear()
            self.page.wait_for_timeout(800)
            return True
        except Exception:
            return False

    # -- Table / rows -------------------------------------------------------------

    TABLE = "#table-table"
    TABLE_HEADERS = "#table-table thead th"
    TABLE_ROWS = "#table-table tbody tr"
    VIEW_BTN_IN_ROW = (
        "xpath=.//*[self::button or self::a][contains(@data-tooltip-target,'tooltip-view-')]"
    )
    NO_RECORDS_MSG = (
        "xpath=//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no items found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no record') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no data') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no result') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'not found')]"
    )

    def wait_for_table_load(self, timeout=15000):
        self.page.locator(self.TABLE).wait_for(state="attached", timeout=timeout)
        self.page.wait_for_timeout(1000)

    def has_records(self):
        return self.is_element_present(self.TABLE_ROWS, timeout=5000) and self._count_data_rows(self.TABLE_ROWS) > 0

    def has_no_records_message(self):
        if self.is_element_present(self.NO_RECORDS_MSG, timeout=3000):
            return True
        return self._count_data_rows(self.TABLE_ROWS) == 0

    def get_row_count(self):
        return self._count_data_rows(self.TABLE_ROWS)

    def get_visible_column_headers(self):
        return self._get_headers_safe(self.TABLE_HEADERS)

    def verify_table_headers(self, expected_headers):
        """True if the table's real headers match *expected_headers*
        exactly, once a leading "Action" column is stripped -- same
        convention as SmsCampaignMessageReportPage.verify_table_headers()
        (every row carries a leading, non-data Action column first)."""
        headers = self.get_visible_column_headers()
        if headers and headers[0].strip().lower() == "action":
            headers = headers[1:]
        return headers == list(expected_headers)

    def click_view_in_row(self, row_index):
        """Click the View action of the row at *row_index* (0-based,
        visible data rows of the report table). Returns False when that
        row has no View control -- never raises, so a test can
        pytest.skip() instead of guessing at a fallback."""
        try:
            row = self.page.locator(self.TABLE_ROWS).nth(row_index)
            btn = row.locator(self.VIEW_BTN_IN_ROW).first
            if btn.count() == 0:
                return False
            btn.scroll_into_view_if_needed()
            btn.click(force=True)
            self.page.wait_for_timeout(2000)  # Livewire modal render
            return True
        except Exception:
            return False

    # -- Message View popup ------------------------------------------------------

    def message_details_popup(self):
        """The "Message Details" modal opened from this page's row View
        action is the SAME Livewire component/markup as
        pages/rcs/messaging/rcs_message_page.py::RcsMessagePage's own
        popup (confirmed via a real, pasted opened-modal capture), so
        its confirmed readers (is_popup_open, get_popup_created/
        scheduled/submitted/delivered/read/failed, close_popup) are
        reused as-is rather than duplicated."""
        from pages.rcs.messaging.rcs_message_page import RcsMessagePage
        return RcsMessagePage(self.page)


    # -- Refresh / Back --------------------------------------------------------

    BTN_REFRESH = "xpath=//button[contains(normalize-space(.),'Refresh')]"
    BTN_BACK = (
        "xpath=//a[contains(normalize-space(.),'Back')] "
        "| //button[contains(normalize-space(.),'Back')]"
    )

    def click_refresh(self):
        """Click the confirmed "Refresh" button. Does not assert on what
        changes -- callers that need to confirm the report actually
        reloaded should re-read cards/table after calling this."""
        try:
            btn = self.h.wait_for_element_clickable(self.BTN_REFRESH, timeout=8000)
            btn.click()
            self.wait_for_spinner_to_disappear()
            self.page.wait_for_timeout(1000)
            return True
        except Exception:
            return False

    def click_back(self):
        """Click the confirmed "Back" link/button (real href ending in
        "/rcs/campaign" -- the Campaign List). A genuine page
        navigation, so the click is wrapped in expect_navigation().
        Returns False (never raises) if no such control is found."""
        try:
            btn = self.h.wait_for_element_clickable(self.BTN_BACK, timeout=8000)
        except Exception:
            return False
        with self.page.expect_navigation(timeout=15000):
            btn.click()
        self.page.wait_for_timeout(1000)
        return True

    # -- Filters panel ------------------------------------------------------------

    # CONFIRMED from a real, pasted DOM capture: an Alpine toggle button
    # (x-on:click="filtersOpen = !filtersOpen") labeled "Filters". Only
    # ONE real filter field was confirmed inside the panel it reveals --
    # the Status <select> below (SELECT_FILTER_STATUS) -- no date-range
    # filter was captured on THIS page (unlike the Campaign List page's
    # own Created From/To filters), so this page object does not expose
    # one.
    BTN_FILTERS = "xpath=//button[contains(normalize-space(.),'Filters')]"

    def open_filters(self):
        """Click the confirmed "Filters" toggle button to reveal the
        filter panel (currently known to contain only the Status
        select)."""
        try:
            btn = self.h.wait_for_element_clickable(self.BTN_FILTERS, timeout=8000)
            btn.click()
            self.page.wait_for_timeout(500)
            return True
        except Exception:
            return False

    def is_filters_button_visible(self):
        return self.is_element_visible(self.BTN_FILTERS, timeout=8000)

    def clear_status_filter(self):
        """Reset the Status filter back to its confirmed default (All /
        empty value) -- the established way of clearing a plain
        <select>-based filter in this project."""
        return self.set_status_filter("")

    # -- Sorting --------------------------------------------------------------------

    # CONFIRMED sortable headers (wire:click="sortBy('<field>')") -- same
    # convention already used by the sibling SMS report page
    # (SORT_CONTACT_BTN/SORT_STATUS_BTN). Submitted At/Delivered At/Read
    # At/Failed At are plain, non-sortable spans -- no locator is defined
    # for them since clicking them has no confirmed sort behavior.
    SORT_CONTACT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('number')\")]"
    SORT_STATUS_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('status')\")]"
    SORT_CREATED_AT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('created_at')\")]"

    # CONFIRMED default-sort indicator pill: "Applied Sorting: Created At:
    # Z-A", wire:click="clearSort('created_at')".
    APPLIED_SORT_PILL = "xpath=//*[contains(normalize-space(.),'Applied Sorting')]"

    def get_applied_sort_text(self):
        try:
            return self.page.locator(self.APPLIED_SORT_PILL).first.inner_text().strip()
        except Exception:
            return ""

    def sort_by_contact(self):
        self._js_click(self.SORT_CONTACT_BTN, timeout=10000)
        self.wait_for_spinner_to_disappear()
        self.page.wait_for_timeout(1000)

    def sort_by_status(self):
        self._js_click(self.SORT_STATUS_BTN, timeout=10000)
        self.wait_for_spinner_to_disappear()
        self.page.wait_for_timeout(1000)

    def sort_by_created_at(self):
        self._js_click(self.SORT_CREATED_AT_BTN, timeout=10000)
        self.wait_for_spinner_to_disappear()
        self.page.wait_for_timeout(1000)

    # -- Columns dropdown -----------------------------------------------------------

    # CONFIRMED from a real, pasted DOM capture: a "Columns"-labeled
    # button (same generic convention already used elsewhere in this
    # suite, e.g. RCSCampaignPage.BTN_COLUMNS) opening a panel with an
    # "All Columns" checkbox (wire:click="deselectAllColumns") plus 8
    # real per-column checkboxes (wire:model.live="selectedColumns"),
    # values: action, contact, status, created-at, submitted-at,
    # delivered-at, read-at, failed-at -- all 8 selected by default.
    BTN_COLUMNS = "xpath=//button[contains(.,'Columns')]"
    COLUMN_CHECKBOX_TMPL = (
        "xpath=//input[@type='checkbox' and @*[name()='wire:model.live' "
        "and contains(.,'selectedColumns')] and @value='{value}']"
    )
    COLUMN_VALUE_TO_HEADER = {
        "action": "Action",
        "contact": "Contact",
        "status": "Status",
        "created-at": "Created At",
        "submitted-at": "Submitted At",
        "delivered-at": "Delivered At",
        "read-at": "Read At",
        "failed-at": "Failed At",
    }

    def open_columns_dropdown(self):
        try:
            btn = self.h.wait_for_element_clickable(self.BTN_COLUMNS, timeout=8000)
            btn.click()
            self.page.wait_for_timeout(500)
            return True
        except Exception:
            return False

    def is_column_checkbox_visible(self, value):
        return self.is_element_visible(
            self.COLUMN_CHECKBOX_TMPL.format(value=value), timeout=5000
        )

    def set_column_checked(self, value, checked):
        """Check/uncheck the confirmed per-column checkbox for *value*
        (one of COLUMN_VALUE_TO_HEADER's keys). Returns False (never
        raises) if the checkbox cannot be found/clicked."""
        try:
            cb = self.page.locator(self.COLUMN_CHECKBOX_TMPL.format(value=value)).first
            cb.wait_for(state="visible", timeout=5000)
            if cb.is_checked() != checked:
                cb.click(force=True)
            self.wait_for_spinner_to_disappear()
            self.page.wait_for_timeout(800)
            return True
        except Exception:
            return False

    def hide_column(self, value):
        return self.set_column_checked(value, False)

    def show_column(self, value):
        return self.set_column_checked(value, True)

    def is_column_header_visible(self, header_text):
        return header_text in self.get_visible_column_headers()

    # -- Row-level data helpers -------------------------------------------------

    def get_cell_text(self, row_index, col_index):
        """Same convention as every other report page object in this
        suite (e.g. SmsCampaignMessageReportPage.get_cell_text())."""
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            cells = rows.nth(row_index).locator("td")
            return cells.nth(col_index).inner_text().strip()
        except Exception:
            return ""

    def get_column_index(self, header_name):
        for i, h in enumerate(self.get_visible_column_headers()):
            if h.strip().lower() == header_name.strip().lower():
                return i
        return None

    def get_row_status_text(self, row_index):
        idx = self.get_column_index("Status")
        if idx is None:
            return ""
        return self.get_cell_text(row_index, idx)

    def get_row_pks(self):
        """Returns the `rowpk` attribute of every currently visible table
        row -- CONFIRMED present on each <tr> (rowpk="<message-uuid>") --
        used to detect duplicate rows structurally rather than by
        comparing rendered cell text."""
        try:
            return self.page.eval_on_selector_all(
                self.TABLE_ROWS, "els => els.map(el => el.getAttribute('rowpk'))"
            )
        except Exception:
            return []

    # -- Export -------------------------------------------------------------------

    EXPORT_CSV_LINK = (
        "xpath=//a[contains(@href,'/messages/export') and contains(normalize-space(.),'Export CSV')]"
    )

    def get_export_csv_href(self):
        el = self.h.wait_for_element_visible(self.EXPORT_CSV_LINK)
        return el.get_attribute("href")

    def click_export_csv(self, timeout_ms=30000):
        """Clicks Export CSV and captures the resulting download via
        page.expect_download() -- identical pattern already used by
        SmsCampaignMessageReportPage.click_export_csv() (this page's
        Export control is likewise a real <a> anchor, not a <button>
        -- see EXPORT_CSV_LINK docstring). Returns {"elapsed_s",
        "file_path", "file_size"} on success, or None on failure
        (never-raises contract)."""
        try:
            link = self.h.wait_for_element_clickable(self.EXPORT_CSV_LINK, timeout=10000)
            link.scroll_into_view_if_needed()
            start = time.time()
            with self.page.expect_download(timeout=timeout_ms) as dl_info:
                self._js_click(self.EXPORT_CSV_LINK, timeout=10000)
            download = dl_info.value
            filename = download.suggested_filename or "rcs_campaign_report_export.csv"
            dest = os.path.join(DOWNLOAD_DIR, filename)
            download.save_as(dest)
            return {
                "elapsed_s": time.time() - start,
                "file_path": dest,
                "file_size": os.path.getsize(dest),
            }
        except Exception:
            return None
