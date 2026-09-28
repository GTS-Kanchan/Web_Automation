import os
import re
import time

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR


class SmsCampaignMessageReportPage(BasePage):
    """Page object for the per-campaign SMS "message report" page with its
    9 clickable/non-clickable stat cards -- NOT the same page as
    pages/sms/sms_campaign_report_page.py (that one is the AGGREGATE
    report listing every campaign, at /channels/sms/reports/campaign,
    with a per-row "Campaign Status Details" modal). This page is reached
    per-campaign, from the SMS Campaign listing page
    (pages/sms/sms_campaign_page.py::SMSCampaignPage), by clicking the
    "Reports" icon on a campaign row.

    Built entirely from real, pasted DOM captures (never fabricated):

    1. The row's "Reports" link (SMSCampaignPage.REPORTS_LINK_IN_ROW) is a
       plain <a data-tooltip-target="tooltip-reports-<id>"
       href="https://<host>/campaigns/messages/total/<uuid>">, confirmed
       identical in convention to the WhatsApp Campaign listing page's own
       Reports icon -- but the URL SHAPE is different and must not be
       assumed from that sibling page:
         - NO "/channels/sms/" or "/whatsapp/" prefix -- this page lives
           directly at /campaigns/messages/<metric>/<campaign_id>.
         - The metric is a PATH SEGMENT ("total", "submitted", ...), not
           a "?metric=" query string like the WhatsApp equivalent.
         - The campaign id in the URL is a UUID (e.g.
           "facb2dcb-8baf-40bc-a04f-983977595517"), not an integer.
    2. STAT CARDS: a grid of 9 plain <div>s (no shared parent id/wire:key
       captured -- located generically via the grid classes below). Each
       CARD has exactly two <p> children: the first is its label (e.g.
       "Total Messages"), the second (class "text-xl font-bold") is its
       current value -- used POSITIONALLY (first/second <p>), not by
       Tailwind class, since position is a stable structural fact and
       Tailwind classes are avoided where a structural alternative exists.
       CONFIRMED CLICKABLE cards carry a real
       onclick="window.location='https://<host>/campaigns/messages/
       <metric>/<uuid>'" attribute -- a genuine full-page navigation, not
       a Livewire action:
         Total Messages -> total
         Submitted      -> submitted
         Delivered      -> delivered
         DLR Awaited    -> dlr-awaited
         Failed         -> failed
         Rejected       -> rejected
         Total Clicks   -> total-clicks
       CONFIRMED NON-CLICKABLE cards (Delivery Rate, Unique Clicks) have
       NO onclick attribute at all. Clickability is therefore checked
       STRUCTURALLY (onclick attribute present/absent), not via a CSS
       class -- the "opacity-70" class seen on both non-clickable cards
       is a general styling difference, not confirmed to be an exclusive
       "non-clickable" marker, so it is not relied on for that judgment.
       The currently ACTIVE metric's card additionally renders
       "border-2 border-purple-500 scale-[1.02] ring-purple-200 ..."
       (confirmed on the "Total Messages" card while on the "total"
       metric) -- not used for activeness checks here since the URL's own
       metric path segment is a more direct, confirmed signal.
    3. TABLE: a rappasoft/livewire-tables table, name CONFIRMED literally
       "sms_messages" (wire:key="sms_messages-table-head-0" etc.) for the
       default "total" metric's rendered table. Only Contact
       (wire:click="sortBy('number')") and Status
       (wire:click="sortBy('status')") are sortable; every other header
       is a plain non-interactive <span>. Every captured table ALSO
       renders a leading "Action" column (header index 0) that is not
       part of any of this task's own expected-header lists -- so
       verify_table_headers() strips a leading "Action" header before
       comparing, rather than requiring an exact full-list match that
       would always fail on that account.
       Each metric's table renders a DIFFERENT column set (per this
       task's own specification -- e.g. Rejected has only 3 real
       columns, DLR Awaited omits "DLR Received At", Total Clicks has an
       entirely different column set) -- but the table's own element id
       (#table-sms_messages) is assumed STABLE across metrics, since only
       the "total" metric's <thead> was independently captured (same
       Livewire component instance, differently filtered data). If a
       different metric's table genuinely uses a different id,
       get_visible_column_headers() returns [] rather than silently
       mismatching, and callers should treat that as a real, reportable
       gap rather than a false pass.
    """

    TABLE_NAME = "sms_messages"

    # ── URL / metric mapping ─────────────────────────────────────────────────
    CARD_NAME_TO_METRIC = {
        "Total Messages": "total",
        "Submitted": "submitted",
        "Delivered": "delivered",
        "DLR Awaited": "dlr-awaited",
        "Failed": "failed",
        "Rejected": "rejected",
        "Total Clicks": "total-clicks",
    }
    NON_CLICKABLE_CARD_NAMES = ("Delivery Rate", "Unique Clicks")
    ALL_CARD_NAMES = (
        "Total Messages", "Submitted", "Delivered", "DLR Awaited", "Failed",
        "Rejected", "Delivery Rate", "Total Clicks", "Unique Clicks",
    )

    # ── Stat cards ───────────────────────────────────────────────────────────
    # Grid wrapper (confirmed classes "grid gap-4 ... lg:grid-cols-5") --
    # used only as an optional scoping ancestor; card lookups below match
    # by label text directly and don't strictly require this wrapper.
    CARD_GRID = "xpath=//div[contains(@class,'grid') and contains(@class,'gap-4')]"

    # ── Export ───────────────────────────────────────────────────────────────
    # CONFIRMED from a real, pasted DOM capture: a plain <a> anchor (NOT a
    # <button> -- an earlier version of this locator wrongly assumed the
    # aggregate SMS Campaign Report page's <button> convention), styled as
    # a button via Tailwind classes. Real confirmed href shape:
    #   https://<host>/campaigns/messages/<campaign_uuid>/export?table=<TableName>
    # (e.g. "?table=TotalTable" while viewing the "total" metric) -- NOTE
    # this is a different URL shape from the card-navigation URLs
    # (/campaigns/messages/<metric>/<uuid>): here the uuid comes directly
    # after "messages/", then "/export", then a PascalCase "table" query
    # param. The exact table= value per metric (Submitted/Delivered/...)
    # is NOT independently confirmed for every card, so this locator
    # matches on the stable, confirmed parts only (href containing
    # "/export" + the visible "Export CSV" text) rather than a specific
    # table= value, and no test asserts on the table= value itself.
    EXPORT_CSV_LINK = "xpath=//a[contains(@href,'/export') and contains(normalize-space(.),'Export CSV')]"

    # ── Table ────────────────────────────────────────────────────────────────
    TABLE = f"#table-{TABLE_NAME}"
    TABLE_HEADERS = f"#table-{TABLE_NAME} thead th"
    TABLE_ROWS = f"#table-{TABLE_NAME} tbody tr"
    # Row "View" action in the leading Action column. Same data-tooltip-target
    # convention ("tooltip-view-<uuid>") as the confirmed View icon on the SMS
    # Messages page (SMSMessagePage.ALL_VIEW_ICONS), whose button opens the
    # Livewire modal component 'sms.campaign.message.view' -- i.e. the
    # campaign-message details modal. Scoped to ONE row, so each recipient's
    # own View is clicked. If the report renders its View differently, the
    # test fails with "View button is unavailable" instead of guessing.
    VIEW_BTN_IN_ROW = "xpath=.//*[self::button or self::a][contains(@data-tooltip-target,'tooltip-view-')]"
    # rappasoft/livewire-tables pagination: nextPage('<table>Page'), the same
    # naming as the email/rcs pages' confirmed NEXT_PAGE_BTN locators.
    NEXT_PAGE_BTN = f"xpath=//button[contains(@*[name()='wire:click'],\"nextPage('{TABLE_NAME}Page')\")]"

    SORT_CONTACT_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('number')\")]"
    SORT_STATUS_BTN = "xpath=//button[contains(@*[name()='wire:click'],\"sortBy('status')\")]"
    NO_RECORDS_MSG = (
        "xpath=//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no items found') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no record') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no data') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no result') "
        "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'not found')]"
    )

    # ── Navigation / page state ──────────────────────────────────────────────

    def navigate_to_campaign(self, campaign_id, metric="total"):
        self.open(f"/campaigns/messages/{metric}/{campaign_id}")
        self.page.wait_for_timeout(2000)
        return self

    def get_campaign_id_from_url(self):
        match = re.search(
            r"/campaigns/messages/[^/]+/([0-9a-fA-F-]{36})", self.get_current_url()
        )
        return match.group(1) if match else None

    def get_active_metric_from_url(self):
        match = re.search(
            r"/campaigns/messages/([^/]+)/[0-9a-fA-F-]{36}", self.get_current_url()
        )
        return match.group(1) if match else None

    def remember_campaign_id(self):
        """Caches the campaign id confirmed from the current URL so
        ensure_on_report_page() can recover to THIS SAME campaign's
        report page even after a test navigates away."""
        cid = self.get_campaign_id_from_url()
        if cid:
            self._campaign_id = cid
        return cid

    def is_report_page(self):
        url = self.get_current_url()
        return "/campaigns/messages/" in url and "login" not in url.lower()

    def wait_for_table_load(self, timeout=15000):
        self.page.locator(self.TABLE).wait_for(state="attached", timeout=timeout)
        self.page.wait_for_timeout(1000)

    # ── Stat cards ───────────────────────────────────────────────────────────

    def _card_by_label_xpath(self, name):
        """Locate the actual STAT CARD div (the one carrying the onclick
        handler, when clickable) by its exact, real label text.

        CONFIRMED nesting (identical for every clickable and non-clickable
        card): the label <p> and value <p> are direct children of an
        inner wrapper <div>, itself a direct child of a middle
        "flex items-center justify-between" <div>, itself a direct child
        of the outer card <div> (the one with onclick="window.location=
        ..." when clickable). An earlier version of this locator matched
        the label via a `.//p` DESCENDANT predicate, which is genuinely
        ambiguous here: every ancestor up to and including the whole
        9-card grid container also has that same label <p> somewhere
        inside it and >=2 total <p> descendants, so `.first` picked the
        OUTERMOST match in document order -- the grid container itself,
        which has no onclick attribute at all. That is why
        is_card_clickable() returned False for every genuinely clickable
        card in a real run. Matching the label as a DIRECT CHILD of its
        immediate wrapper is unambiguous (only that one inner div has it
        as a direct child), and walking up exactly two confirmed ancestor
        levels reaches the real card div for every card, clickable or
        not."""
        return f"xpath=//div[p[normalize-space(text())='{name}']]/../.."

    def is_card_visible(self, name):
        return self.is_element_visible(self._card_by_label_xpath(name), timeout=8000)

    def _get_card(self, name, timeout=8000):
        return self.h.wait_for_element_visible(self._card_by_label_xpath(name), timeout=timeout)

    def is_card_clickable(self, name):
        """True if the card has a real onclick handler -- the confirmed,
        structural signal for clickability on this page (see class
        docstring point 2). Never relies on a CSS class."""
        card = self._get_card(name)
        return bool(card.get_attribute("onclick"))

    def get_card_value(self, name):
        card = self._get_card(name)
        paragraphs = card.locator("p")
        return paragraphs.nth(1).inner_text().strip()

    def click_report_card(self, name):
        """Click a CLICKABLE stat card by its real label text. This is a
        genuine full-page navigation (onclick="window.location=...'"),
        not a Livewire action, so the click is wrapped in
        expect_navigation(). Raises ValueError (a real programming error,
        not a flaky app condition) if the named card has no onclick
        handler -- callers verifying non-clickable cards should use
        click_non_clickable_card() instead."""
        card = self._get_card(name)
        if not card.get_attribute("onclick"):
            raise ValueError(
                f"Card {name!r} has no onclick handler -- it is not a "
                f"clickable card on this page. Use click_non_clickable_card() "
                f"to verify non-clickable behavior instead."
            )
        with self.page.expect_navigation(timeout=15000):
            card.click(force=True)
        self.page.wait_for_timeout(1000)

    def click_non_clickable_card(self, name):
        """Click a card confirmed to have NO onclick handler (Delivery
        Rate, Unique Clicks). Returns (url_before, url_after, headers_
        before, headers_after) so a test can assert nothing navigated and
        the table didn't change, without this method guessing what "no
        effect" should look like."""
        url_before = self.get_current_url()
        headers_before = self.get_visible_column_headers()
        card = self._get_card(name)
        card.click(force=True)
        self.page.wait_for_timeout(800)
        url_after = self.get_current_url()
        headers_after = self.get_visible_column_headers()
        return url_before, url_after, headers_before, headers_after

    # ── Table / rows ─────────────────────────────────────────────────────────

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

    def get_cell_text(self, row_index, col_index):
        """Return text of cell at (row_index, col_index) -- 0-based.
        Same convention as SMSMessagePage.get_cell_text() (pages/sms/
        sms_message_page.py), reused here for row-level data (e.g. the
        CONTACT column) that get_visible_column_headers()/get_row_count()
        alone don't expose."""
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            cells = rows.nth(row_index).locator("td")
            return cells.nth(col_index).inner_text().strip()
        except Exception:
            return ""

    def get_column_index(self, header_name):
        """0-based index of the column whose header equals *header_name*
        (case-insensitive), or None."""
        for i, h in enumerate(self.get_visible_column_headers()):
            if h.strip().lower() == header_name.strip().lower():
                return i
        return None

    def has_next_page(self):
        try:
            btns = self.page.locator(self.NEXT_PAGE_BTN)
            return any(b.is_visible() and b.is_enabled() for b in btns.all())
        except Exception:
            return False

    def go_to_next_page(self):
        self._js_click_first_visible(self.NEXT_PAGE_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)
        self.wait_for_table_load()

    def click_view_in_row(self, row_index):
        """Click the View action of the row at *row_index* (0-based, visible
        data rows of the report table). Returns False when that row has no
        View control."""
        try:
            row = self.page.locator(self.TABLE_ROWS).nth(row_index)
            btn = row.locator(self.VIEW_BTN_IN_ROW).first
            if btn.count() == 0:
                return False
            btn.scroll_into_view_if_needed()
            btn.click()
            self.page.wait_for_timeout(2000)  # Livewire modal render
            return True
        except Exception:
            return False

    def message_details_popup(self):
        """The message-details modal is the same Livewire modal the SMS
        Messages page opens, so its confirmed readers (is_popup_open,
        get_popup_message_id, close_popup, ...) are reused as-is."""
        from pages.sms.messaging.sms_message_page import SMSMessagePage
        return SMSMessagePage(self.page)

    def verify_table_headers(self, expected_headers):
        """True if the table's real headers match `expected_headers`
        exactly, once a leading "Action" column is stripped (every
        captured table on this page renders that extra, non-data column
        first -- see class docstring point 3; it is not part of any of
        this task's own expected-header lists)."""
        headers = self.get_visible_column_headers()
        if headers and headers[0].strip().lower() == "action":
            headers = headers[1:]
        return headers == list(expected_headers)

    def sort_by_contact(self):
        self._js_click(self.SORT_CONTACT_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    def sort_by_status(self):
        self._js_click(self.SORT_STATUS_BTN, timeout=10000)
        self.page.wait_for_timeout(1500)

    # ── Export ───────────────────────────────────────────────────────────────

    def get_export_csv_href(self):
        """Returns the Export CSV anchor's real href (confirmed shape:
        .../campaigns/messages/<campaign_uuid>/export?table=<TableName>)
        -- same accessor shape as
        WhatsAppCampaignReportPage.get_export_csv_href(), for callers that
        want to sanity-check the link itself without downloading."""
        el = self.h.wait_for_element_visible(self.EXPORT_CSV_LINK)
        return el.get_attribute("href")

    def click_export_csv(self, timeout_ms=30000):
        """Clicks Export CSV for whichever card/metric is currently active
        and captures the resulting download via page.expect_download() --
        identical pattern to
        SmsCampaignReportPage.click_export_csv(), reused rather than
        reimplemented (only the locator differs, since this page's Export
        control is a real <a> anchor, not a <button> -- see EXPORT_CSV_LINK
        docstring). Returns {"elapsed_s", "file_path", "file_size"} on
        success, or None on failure (never-raises contract, same as that
        sibling method, so an existing caller that discards the return
        value is unaffected)."""
        try:
            link = self.h.wait_for_element_clickable(self.EXPORT_CSV_LINK, timeout=10000)
            link.scroll_into_view_if_needed()
            start = time.time()
            with self.page.expect_download(timeout=timeout_ms) as dl_info:
                self._js_click(self.EXPORT_CSV_LINK, timeout=10000)
            download = dl_info.value
            filename = download.suggested_filename or "sms_campaign_message_report_export.csv"
            dest = os.path.join(DOWNLOAD_DIR, filename)
            download.save_as(dest)
            return {
                "elapsed_s": time.time() - start,
                "file_path": dest,
                "file_size": os.path.getsize(dest),
            }
        except Exception:
            return None

    def click_card_then_export(self, card_name, timeout_ms=30000):
        """Clicks a CLICKABLE stat card (selecting/"activating" it -- see
        class docstring point 2 on the confirmed active-border styling),
        waits for its table to load, then triggers Export CSV. Returns
        click_export_csv()'s result for THAT card's exported file. Composes
        the existing click_report_card() + wait_for_table_load() +
        click_export_csv() methods rather than duplicating any of their
        logic."""
        self.click_report_card(card_name)
        self.wait_for_table_load(timeout=15000)
        return self.click_export_csv(timeout_ms=timeout_ms)
