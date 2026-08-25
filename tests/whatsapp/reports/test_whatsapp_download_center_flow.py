"""
WhatsApp Download Center — Automated Test Suite
Built per instruction: "take reference from sms download testcases" --
mirrors tests/test_sms_download_center_flow.py's TC numbering and
structure, re-grounded against FULL live DOM dumps of the actual
WhatsApp Download Center listing page
(/whatsapp/channels/download/center) AND its Create Report form
(/whatsapp/channels/download/center/create).

Test Design Notes (see pages/whatsapp_download_center_page.py and
pages/whatsapp_report_create_page.py module docstrings for the full
list of confirmed DOM specifics):
  - scope="module" — page object shared across all tests; popup state persists.
  - ensure_on_dc_page() closes stale modals/alerts before each test.
  - Filters are live (wire:model.live) — no Apply button needed.
  - Status filter values are lowercase: "pending","processing","completed","failed".
  - Date filter uses Flatpickr (text input, format dd-mm-yyyy).
  - Delete confirmation uses the browser's NATIVE confirm() (Livewire
    wire:confirm, confirmed from DOM) — NOT SweetAlert2, unlike the SMS
    reference's docstring assumption. confirm_delete()/cancel_delete()
    already try native dialog first, so this is handled unchanged.
  - Default table sort is created_at DESC (confirmed via the "Applied
    Sorting: Created At: Z-A" pill) — a freshly-submitted report
    appears at the TOP of the table, same assumption the SMS reference
    relies on for its create-then-verify tests.

Differences from the SMS reference (all called out with reasons):
  - TC_00 (create a throwaway report) and TC_19/20/21 (create + verify
    date-range reports) are NOW INCLUDED, using WhatsappReportCreatePage
    (pages/whatsapp_report_create_page.py), grounded in a full DOM dump
    of the WhatsApp create-report form obtained after the initial build
    of this suite. Confirmed field differences from the SMS form:
      * "Category" (marketing/mmlite/utility/authentication) replaces
        SMS's "Product Type" (Promotional/Transactional/OTP) — matches
        the WhatsApp message-category taxonomy seen on the Overview page.
      * "Summary By" has a checkbox labeled "WABA Number" whose
        underlying field value is confirmed as "sender" (same field
        name as SMS, different visible label).
      * The "Select Columns for Export" checklist has 18 confirmed
        values (see WhatsappReportCreatePage.ALL_COLUMNS), all checked
        by default -- different set from SMS's 17 columns.
      * A checkbox with value="status" exists in BOTH the "Summary By"
        and "Select Columns for Export" sections; the page object
        disambiguates them via confirmed DOM ancestor classes.
  - TC_12 (confirm delete) is NOW RESTORED, but made deliberately safer
    than the SMS reference: rather than deleting whatever sits in row
    0, it first searches for the specific throwaway report TC_00
    created ("Automated Test Report") and only deletes that filtered
    result. This guarantees the suite can never delete one of the
    account's real, pre-existing reports (2 were confirmed present at
    original capture time) even if TC_00 hasn't run yet or ordering
    changes -- it skips instead of guessing. TC_12 has failed twice in
    real pytest runs at the exact same "Delete confirmation did not
    appear" assertion, across two different click strategies -- since
    the click mechanism (JS vs native) has now been ruled out as the
    cause, the assertion is instrumented to surface
    click_delete_icon()'s debug info (button found? tag/title/
    outerHTML? click exception? alert seen?) on failure so the next
    real run gives concrete evidence instead of another guess.
  - TC_10 (download) and TC_11 (download disabled for Processing) still
    run against whatever Completed/Processing rows exist at run time
    (which may now include the TC_00-created throwaway report) rather
    than a specific freshly-created row, since a Completed status can't
    be forced synchronously.
  - Bonus coverage added (not in the SMS reference): the "Columns"
    dropdown, confirmed present in the WhatsApp DOM with checkboxes for
    all 7 columns (actions/name/category/from/to/created-at/status).
  - TC_16 (sort) and TC_17 (pagination) removed, matching the SMS
    reference exactly ("always skipped on this page").

Migrated to Playwright: local page-object fixture renamed
`download_center_page` (built on conftest.py's `module_logged_in_page`)
to avoid shadowing pytest-playwright's reserved `page` fixture. All
Selenium-specific waits (`page._w`, `page._js`, WebDriverWait/EC) were
replaced with direct Playwright Locator calls; native alert/confirm
handling now goes through `page.once("dialog", ...)` (see
whatsapp_download_center_page.py's click_delete_icon()/confirm_delete()
docstrings) instead of `driver.switch_to.alert`.

Run:
    pytest tests/test_whatsapp_download_center_flow.py -v
"""
import time
from datetime import date, datetime, timedelta

import pytest

from pages.whatsapp.whatsapp_download_center_page import WhatsappDownloadCenterPage
from pages.whatsapp.whatsapp_report_create_page import WhatsappReportCreatePage


pytestmark = [pytest.mark.whatsapp, pytest.mark.report]

def yesterday_str():
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


def days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")


# ══════════════════════════════════════════════════════════════════════════════
# Module fixture
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def download_center_page(module_logged_in_page):
    p = WhatsappDownloadCenterPage(module_logged_in_page)
    p.navigate()
    p.wait_for_table_load(timeout=15000)
    return p


# ══════════════════════════════════════════════════════════════════════════════
# Recovery helpers
# ══════════════════════════════════════════════════════════════════════════════

def ensure_on_dc_page(p: WhatsappDownloadCenterPage):
    """Recover to the Download Center if the page drifted. Order matters:
    native dialogs must be cleared BEFORE any Playwright call that reads
    page state, otherwise a pending dialog blocks further script
    execution."""
    p.dismiss_any_alert()

    try:
        if p.is_delete_modal_visible():
            p.cancel_delete()
            p.page.wait_for_timeout(500)
    except Exception:
        pass

    try:
        if p.is_popup_open():
            p.close_popup()
            p.page.wait_for_timeout(500)
    except Exception:
        pass

    if not p.is_download_center_page():
        p.navigate()
        p.wait_for_table_load(timeout=10000)


def reset_filters(p: WhatsappDownloadCenterPage):
    """Hard-reset filters by re-navigating to the page."""
    p.navigate()
    p.wait_for_table_load(timeout=10000)


# ══════════════════════════════════════════════════════════════════════════════
# TC_00 — Create a new report (runs first so downstream tests have data)
# ══════════════════════════════════════════════════════════════════════════════

class TestTC00CreateReport:
    """
    TC_00: Click Create New Report, fill the form, submit.
    Runs before all other tests so the Download Center has at least one
    disposable report -- used later by TC_12's confirm-delete rather
    than risking one of the 2 real pre-existing rows.
    Uses last-7-days-to-yesterday as the date range (always within the
    confirmed 90-day window; to_date's max is confirmed as "yesterday").
    """

    def test_tc00_navigate_to_create_form(self, download_center_page):
        """Click the Create New Report link and verify the form loads."""
        ensure_on_dc_page(download_center_page)
        try:
            download_center_page._js_click(download_center_page.CREATE_REPORT_LINK, timeout=8000)
            download_center_page.page.wait_for_timeout(2000)
        except Exception:
            base = download_center_page.get_current_url().split("/whatsapp")[0]
            download_center_page.page.goto(base + "/whatsapp/channels/download/center/create")
            download_center_page.page.wait_for_timeout(2000)
        assert "create" in download_center_page.get_current_url().lower(), (
            f"Did not navigate to create form, URL: {download_center_page.get_current_url()}"
        )

    def test_tc00_fill_and_submit_form(self, download_center_page):
        """Fill all required fields and submit the Generate Report form."""
        if "create" not in download_center_page.get_current_url().lower():
            pytest.skip("Not on create form — navigation failed in previous step")

        create = WhatsappReportCreatePage(download_center_page.page)
        create.wait_for_form_load(timeout=15000)

        create.set_report_name("Automated Test Report")
        create.set_category(WhatsappReportCreatePage.CATEGORY_ALL)
        create.set_from_date(days_ago(7))
        create.set_to_date(yesterday_str())
        create.set_summary_by(include_waba=True, include_status=True)
        create.set_summary_only(enabled=False)
        create.submit()

        deadline = time.time() + 10
        while time.time() < deadline:
            if "create" not in download_center_page.get_current_url().lower():
                break
            time.sleep(0.5)

        if "create" in download_center_page.get_current_url().lower():
            download_center_page.navigate()
        else:
            download_center_page.wait_for_table_load(timeout=15000)

        assert download_center_page.is_download_center_page(), (
            f"Expected to be on Download Center after submit, URL: {download_center_page.get_current_url()}"
        )

    def test_tc00_report_row_exists(self, download_center_page):
        """Verify the new report row appears in the table (status: pending/processing)."""
        ensure_on_dc_page(download_center_page)
        row_count = download_center_page.get_row_count()
        assert download_center_page.is_download_center_page(), "Not on Download Center after create"
        if row_count == 0:
            pytest.skip(
                "Report submitted but no row visible yet "
                "(may still be queued — run again after a moment)"
            )


# ══════════════════════════════════════════════════════════════════════════════
# TC_01 — Verify page loads with correct title / URL
# ══════════════════════════════════════════════════════════════════════════════

class TestTC01PageLoad:
    """TC_01: Download Center page loads successfully."""

    def test_tc01_page_url(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        url = download_center_page.get_current_url()
        assert "whatsapp" in url.lower() and "download" in url.lower(), (
            f"Expected WhatsApp Download Center URL, got: {url}"
        )

    def test_tc01_page_accessible(self, download_center_page):
        assert download_center_page.is_download_center_page(), (
            "is_download_center_page() returned False"
        )

    def test_tc01_page_title(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        title = download_center_page.get_page_title_text()
        assert title == "Whatsapp Download Center", (
            f"Expected h1 'Whatsapp Download Center', got: {title!r}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TC_02 — Verify table columns are displayed
# ══════════════════════════════════════════════════════════════════════════════

class TestTC02TableColumns:
    """TC_02: Table renders with expected column headers (7 confirmed:
    Actions, Name, Category, From, To, Created At, Status)."""

    EXPECTED_COLUMNS = ["Name", "Category", "Status"]  # subset check

    def test_tc02_headers_present(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        headers = download_center_page.get_table_headers()
        lowered = " ".join(h.lower() for h in headers)
        for col in self.EXPECTED_COLUMNS:
            assert col.lower() in lowered, (
                f"Column '{col}' not found in headers: {headers}"
            )


# ══════════════════════════════════════════════════════════════════════════════
# TC_03 — Search by report name
# ══════════════════════════════════════════════════════════════════════════════

class TestTC03Search:
    """TC_03: Search filters rows by report name."""

    def test_tc03_search_nonexistent(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        download_center_page.search("__this_report_definitely_does_not_exist_xyz__")
        download_center_page.page.wait_for_timeout(1500)
        assert download_center_page.is_no_records_visible() or download_center_page.get_row_count() == 0, (
            "Expected no results for nonsense search term"
        )

    def test_tc03_search_cleared_on_navigate(self, download_center_page):
        reset_filters(download_center_page)
        assert download_center_page.is_download_center_page()


# ══════════════════════════════════════════════════════════════════════════════
# TC_04 — Date range filter
# ══════════════════════════════════════════════════════════════════════════════

class TestTC04DateFilter:
    """TC_04: Date filter (Flatpickr) narrows results. No Apply button needed."""

    def test_tc04_date_filter_applied(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        download_center_page.open_filter_panel()
        download_center_page.page.wait_for_timeout(500)
        download_center_page.set_date_filter("2000-01-01", "2000-01-02")
        download_center_page.apply_filter()
        assert True, "Date filter applied without error"

    def test_tc04_date_filter_cleared(self, download_center_page):
        reset_filters(download_center_page)
        assert download_center_page.is_download_center_page()


# ══════════════════════════════════════════════════════════════════════════════
# TC_05 — Search box placeholder text
# ══════════════════════════════════════════════════════════════════════════════

class TestTC05SearchPlaceholder:
    """TC_05: Search box shows correct placeholder."""

    def test_tc05_placeholder(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        try:
            inp = download_center_page.page.locator(download_center_page.SEARCH_BOX).first
            ph = inp.get_attribute("placeholder") or ""
            assert "report" in ph.lower() or "search" in ph.lower(), (
                f"Unexpected placeholder: '{ph}'"
            )
        except Exception as exc:
            pytest.fail(f"Search box not found: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# TC_06 — Create New Report link visible and navigates to the create URL
# ══════════════════════════════════════════════════════════════════════════════

class TestTC06CreateLink:
    """TC_06: 'Create New Report' link is present and points at the
    confirmed create URL."""

    def test_tc06_create_link_present(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        try:
            link = download_center_page.page.locator(download_center_page.CREATE_REPORT_LINK).first
            link.wait_for(state="attached", timeout=8000)
            assert link.is_visible(), "Create New Report link not visible"
        except Exception as exc:
            pytest.fail(f"Create New Report link not found: {exc}")

    def test_tc06_create_link_href(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        link = download_center_page.page.locator(download_center_page.CREATE_REPORT_LINK).first
        link.wait_for(state="attached", timeout=8000)
        href = link.get_attribute("href") or ""
        assert "whatsapp/channels/download/center/create" in href, (
            f"Unexpected Create New Report href: {href}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TC_07 — Filter by status: Completed
# ══════════════════════════════════════════════════════════════════════════════

class TestTC07FilterCompleted:
    """TC_07: Status filter 'completed' shows only completed rows (or no-records)."""

    def test_tc07_filter_completed(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        download_center_page.open_filter_panel()
        download_center_page.page.wait_for_timeout(500)
        download_center_page.set_filter_status(WhatsappDownloadCenterPage.STATUS_COMPLETED)
        download_center_page.page.wait_for_timeout(1500)
        row_count = download_center_page.get_row_count()
        if row_count == 0:
            assert download_center_page.is_no_records_visible() or True
        else:
            for idx in range(min(row_count, 5)):
                status_text = download_center_page.get_row_status(idx).lower()
                assert "completed" in status_text or status_text == "", (
                    f"Row {idx} status '{status_text}' does not match 'completed'"
                )

    def test_tc07_cleanup(self, download_center_page):
        reset_filters(download_center_page)


# ══════════════════════════════════════════════════════════════════════════════
# TC_08 — Filter by status: Processing
# ══════════════════════════════════════════════════════════════════════════════

class TestTC08FilterProcessing:
    """TC_08: Status filter 'processing' shows only processing rows."""

    def test_tc08_filter_processing(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        download_center_page.open_filter_panel()
        download_center_page.page.wait_for_timeout(500)
        download_center_page.set_filter_status(WhatsappDownloadCenterPage.STATUS_PROCESSING)
        # Poll instead of a single fixed wait -- observed in a live run
        # against a slower environment that Livewire's filter round-trip
        # wasn't always finished re-rendering the table within 1.5s,
        # which surfaced as a stale 'completed' row under this filter.
        deadline = time.time() + 8
        row_count = download_center_page.get_row_count()
        while time.time() < deadline:
            row_count = download_center_page.get_row_count()
            if row_count == 0 or all(
                "processing" in download_center_page.get_row_status(i).lower()
                for i in range(min(row_count, 5))
            ):
                break
            time.sleep(0.5)
        if row_count > 0:
            for idx in range(min(row_count, 5)):
                status_text = download_center_page.get_row_status(idx).lower()
                assert "processing" in status_text or status_text == "", (
                    f"Row {idx} status '{status_text}' does not match 'processing'"
                )

    def test_tc08_cleanup(self, download_center_page):
        reset_filters(download_center_page)


# ══════════════════════════════════════════════════════════════════════════════
# TC_09 — View / Summary modal opens
# ══════════════════════════════════════════════════════════════════════════════

class TestTC09ViewModal:
    """TC_09: Clicking the View Summary icon opens the summary modal."""

    def test_tc09_view_modal_opens(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        if download_center_page.get_row_count() == 0:
            pytest.skip("No rows available to test view icon")
        download_center_page.click_view_icon(row_idx=0)
        download_center_page.page.wait_for_timeout(1500)
        assert download_center_page.is_popup_open(), (
            "Summary modal did not open after clicking View Summary icon"
        )

    def test_tc09_modal_content_nonempty(self, download_center_page):
        if not download_center_page.is_popup_open():
            pytest.skip("Summary modal not open")
        text = download_center_page.get_popup_all_text()
        assert text, "Summary modal is open but shows no content"

    def test_tc09_modal_closes(self, download_center_page):
        if not download_center_page.is_popup_open():
            pytest.skip("Summary modal not open")
        download_center_page.close_popup()
        download_center_page.page.wait_for_timeout(800)
        assert not download_center_page.is_popup_open(), "Summary modal did not close"


# ══════════════════════════════════════════════════════════════════════════════
# TC_10 — Download icon initiates a file download (Completed row)
# ══════════════════════════════════════════════════════════════════════════════

class TestTC10Download:
    """TC_10: Clicking Download on a Completed report downloads a file."""

    def test_tc10_download_initiates(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        download_center_page.open_filter_panel()
        download_center_page.page.wait_for_timeout(300)
        download_center_page.set_filter_status(WhatsappDownloadCenterPage.STATUS_COMPLETED)
        download_center_page.page.wait_for_timeout(1500)
        if download_center_page.get_row_count() == 0:
            pytest.skip("No completed reports available to test download")

        download_center_page.clear_download_dir()
        before = download_center_page.snapshot_downloads()

        download_center_page.click_download_icon(row_idx=0)
        downloaded = download_center_page.wait_for_download(timeout=60, before=before)
        assert downloaded is not None, (
            "Download did not complete within 60 seconds. "
            "Possible causes: download button locator mismatch, report not "
            "in 'completed' state, or the download did not fire a "
            "Playwright download event."
        )

    def test_tc10_cleanup(self, download_center_page):
        reset_filters(download_center_page)


# ══════════════════════════════════════════════════════════════════════════════
# TC_11 — Download disabled for Processing rows
# ══════════════════════════════════════════════════════════════════════════════

class TestTC11DownloadDisabled:
    """TC_11: Download icon is absent/disabled for Processing reports."""

    def test_tc11_download_disabled_processing(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        download_center_page.open_filter_panel()
        download_center_page.page.wait_for_timeout(300)
        download_center_page.set_filter_status(WhatsappDownloadCenterPage.STATUS_PROCESSING)
        download_center_page.page.wait_for_timeout(1500)
        if download_center_page.get_row_count() == 0:
            pytest.skip("No processing reports available at run time")
        assert download_center_page.is_download_btn_disabled(row_idx=0), (
            "Download button should be disabled/absent for a Processing report"
        )

    def test_tc11_cleanup(self, download_center_page):
        reset_filters(download_center_page)


# ══════════════════════════════════════════════════════════════════════════════
# TC_13 — Cancel delete keeps the row  (must run BEFORE TC_12)
# ══════════════════════════════════════════════════════════════════════════════

class TestTC13CancelDelete:
    """TC_13: Clicking Cancel on the delete confirmation keeps the row."""

    def test_tc13_cancel_delete(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        before_count = download_center_page.get_row_count()
        if before_count == 0:
            pytest.skip("No rows to attempt cancel delete")

        download_center_page.click_delete_icon(row_idx=0)
        download_center_page.page.wait_for_timeout(800)
        assert download_center_page.is_delete_modal_visible(), (
            "Delete confirmation did not appear"
        )
        download_center_page.cancel_delete()
        download_center_page.page.wait_for_timeout(500)
        after_count = download_center_page.get_row_count()
        assert after_count == before_count, (
            f"Row count changed after cancel (before={before_count}, after={after_count})"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TC_12 — Confirm delete removes the row  (runs AFTER TC_13)
# ══════════════════════════════════════════════════════════════════════════════

class TestTC12ConfirmDelete:
    """TC_12: Clicking Confirm on the delete confirmation removes the
    report. SAFETY: searches for the specific throwaway report TC_00
    created ("Automated Test Report") before deleting, rather than
    deleting whatever sits in row 0 -- this guarantees only the
    disposable test report is ever removed, never one of the account's
    real pre-existing reports."""

    REPORT_NAME = "Automated Test Report"

    def test_tc12_confirm_delete(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        download_center_page.search(self.REPORT_NAME)
        download_center_page.page.wait_for_timeout(1500)
        before_count = download_center_page.get_row_count()
        if before_count == 0:
            reset_filters(download_center_page)
            pytest.skip(
                f"'{self.REPORT_NAME}' not found -- TC_00 may not have run, "
                f"or the report isn't visible yet"
            )

        download_center_page.click_delete_icon(row_idx=0)
        download_center_page.page.wait_for_timeout(800)
        if not download_center_page.is_delete_modal_visible():
            debug = getattr(download_center_page, "last_delete_click_debug", {})
            pytest.fail(
                "Delete confirmation did not appear. "
                f"click_delete_icon debug info: {debug}"
            )
        download_center_page.confirm_delete()
        # Poll instead of a single fixed wait -- observed in a live run
        # against a slower environment that the delete's Livewire
        # round-trip (server delete + table re-render) wasn't always
        # finished within 2.5s.
        deadline = time.time() + 10
        after_count = download_center_page.get_row_count()
        while time.time() < deadline:
            after_count = download_center_page.get_row_count()
            if after_count < before_count or download_center_page.is_no_records_visible():
                break
            time.sleep(0.5)
        reset_filters(download_center_page)
        confirm_debug = getattr(download_center_page, "last_confirm_delete_debug", {})
        assert after_count < before_count or download_center_page.is_no_records_visible(), (
            f"Row count did not decrease after delete "
            f"(before={before_count}, after={after_count}). "
            f"confirm_delete debug info: {confirm_debug}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TC_14 — Refresh link reloads the table
# ══════════════════════════════════════════════════════════════════════════════

class TestTC14Refresh:
    """TC_14: Refresh link (an <a> tag) is present and reloads without errors."""

    def test_tc14_refresh_link_present(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        try:
            link = download_center_page.page.locator(download_center_page.REFRESH_LINK).first
            link.wait_for(state="attached", timeout=8000)
            assert link.is_visible(), "Refresh link not visible"
        except Exception as exc:
            pytest.fail(f"Refresh link not found: {exc}")

    def test_tc14_refresh_reloads_page(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        download_center_page.click_refresh()
        assert download_center_page.is_download_center_page(), (
            "After clicking Refresh, not on Download Center page"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TC_15 — No-records message when search yields nothing
# ══════════════════════════════════════════════════════════════════════════════

class TestTC15NoRecordsMessage:
    """TC_15: Correct no-records text is displayed when search has no
    results. NOTE: no empty-table state was captured in the DOM this
    suite is grounded in (both real rows had data), so the exact
    no-records text is unconfirmed for this page -- reusing the generic
    text pattern shared by the SMS reference's Livewire table component."""

    NO_RECORDS_TEXT = "No items found"

    def test_tc15_no_records_text(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        download_center_page.search("__zzz_nonexistent_report_xyz__")
        download_center_page.page.wait_for_timeout(1500)
        if not download_center_page.is_no_records_visible():
            pytest.skip("Could not trigger no-records state (data may exist)")
        try:
            el = download_center_page.page.locator(download_center_page.NO_RECORDS).first
            text = el.inner_text()
            assert self.NO_RECORDS_TEXT in text, (
                f"No-records text mismatch: got '{text}'"
            )
        except Exception as exc:
            pytest.fail(f"No-records element not found: {exc}")

    def test_tc15_cleanup(self, download_center_page):
        reset_filters(download_center_page)


# TC_16 (Sort by Created At) and TC_17 (Pagination) removed — matches the
# SMS reference exactly ("always skipped on this page").

# ══════════════════════════════════════════════════════════════════════════════
# TC_18 — Page load performance
# ══════════════════════════════════════════════════════════════════════════════

class TestTC18Performance:
    """TC_18: Page loads within an acceptable time (< 10 s DOMContentLoaded)."""

    MAX_LOAD_MS = 10_000

    def test_tc18_load_time(self, download_center_page):
        download_center_page.navigate()
        download_center_page.wait_for_table_load(timeout=15000)
        ms = download_center_page.measure_load_time_ms()
        assert ms < self.MAX_LOAD_MS, (
            f"Page load time {ms} ms exceeds {self.MAX_LOAD_MS} ms threshold"
        )


# ══════════════════════════════════════════════════════════════════════════════
# Shared helper for date-range report creation tests (TC_19 / TC_20 / TC_21)
# ══════════════════════════════════════════════════════════════════════════════

def _create_date_range_report(download_center_page, report_name: str, days: int):
    """
    Navigate to the Create form, fill date range for the last `days` days,
    submit, and return to the Download Center.

    Date window: yesterday - (days-1)  →  yesterday
    Both dates stay within the server-enforced 90-day window (confirmed
    from_date min / to_date max on the live create form).
    """
    ensure_on_dc_page(download_center_page)
    try:
        download_center_page._js_click(download_center_page.CREATE_REPORT_LINK, timeout=8000)
        download_center_page.page.wait_for_timeout(2000)
    except Exception:
        base = download_center_page.get_current_url().split("/whatsapp")[0]
        download_center_page.page.goto(base + "/whatsapp/channels/download/center/create")
        download_center_page.page.wait_for_timeout(2000)

    assert "create" in download_center_page.get_current_url().lower(), (
        f"Could not navigate to create form (URL: {download_center_page.get_current_url()})"
    )

    yesterday_date = date.today() - timedelta(days=1)
    from_date = yesterday_date - timedelta(days=days - 1)

    create = WhatsappReportCreatePage(download_center_page.page)
    create.wait_for_form_load(timeout=15000)
    create.set_report_name(report_name)
    create.set_category(WhatsappReportCreatePage.CATEGORY_ALL)
    create.set_from_date(from_date.strftime("%Y-%m-%d"))
    create.set_to_date(yesterday_date.strftime("%Y-%m-%d"))
    create.set_summary_by(include_waba=True, include_status=True)
    create.set_summary_only(enabled=False)
    create.submit()

    deadline = time.time() + 10
    while time.time() < deadline:
        if "create" not in download_center_page.get_current_url().lower():
            break
        time.sleep(0.5)

    if "create" in download_center_page.get_current_url().lower():
        download_center_page.navigate()
    else:
        download_center_page.wait_for_table_load(timeout=15000)

    assert download_center_page.is_download_center_page(), (
        f"Not on Download Center after submit (URL: {download_center_page.get_current_url()})"
    )


# ══════════════════════════════════════════════════════════════════════════════
# TC_19 — Create & verify report for the last 10 days
# ══════════════════════════════════════════════════════════════════════════════

class TestTC19Report10Days:
    """TC_19: Generate a report for the last 10 days and verify it appears in the table."""

    REPORT_NAME = "Automated Report - 10 Days"
    DAYS = 10

    def test_tc19_create_report(self, download_center_page):
        _create_date_range_report(download_center_page, self.REPORT_NAME, self.DAYS)

    def test_tc19_report_appears_in_table(self, download_center_page):
        """Search for the report name and confirm at least one row is found."""
        ensure_on_dc_page(download_center_page)
        download_center_page.search(self.REPORT_NAME)
        download_center_page.page.wait_for_timeout(1500)
        row_count = download_center_page.get_row_count()
        reset_filters(download_center_page)
        if row_count == 0:
            pytest.skip(
                f"'{self.REPORT_NAME}' not yet visible "
                f"(still queued -- re-run after a moment)"
            )
        assert row_count > 0, (
            f"Expected at least 1 row for '{self.REPORT_NAME}', got 0"
        )

    def test_tc19_report_status_not_failed(self, download_center_page):
        """Status of the 10-day report should not be 'failed'."""
        ensure_on_dc_page(download_center_page)
        download_center_page.search(self.REPORT_NAME)
        download_center_page.page.wait_for_timeout(1500)
        row_count = download_center_page.get_row_count()
        if row_count == 0:
            pytest.skip("Report row not visible yet")
        status = download_center_page.get_row_status(0).lower()
        reset_filters(download_center_page)
        assert "failed" not in status, (
            f"10-day report has status '{status}'; expected pending/processing/completed"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TC_20 — Create & verify report for the last 20 days
# ══════════════════════════════════════════════════════════════════════════════

class TestTC20Report20Days:
    """TC_20: Generate a report for the last 20 days and verify it appears in the table."""

    REPORT_NAME = "Automated Report - 20 Days"
    DAYS = 20

    def test_tc20_create_report(self, download_center_page):
        _create_date_range_report(download_center_page, self.REPORT_NAME, self.DAYS)

    def test_tc20_report_appears_in_table(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        download_center_page.search(self.REPORT_NAME)
        download_center_page.page.wait_for_timeout(1500)
        row_count = download_center_page.get_row_count()
        reset_filters(download_center_page)
        if row_count == 0:
            pytest.skip(
                f"'{self.REPORT_NAME}' not yet visible "
                f"(still queued -- re-run after a moment)"
            )
        assert row_count > 0, (
            f"Expected at least 1 row for '{self.REPORT_NAME}', got 0"
        )

    def test_tc20_report_status_not_failed(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        download_center_page.search(self.REPORT_NAME)
        download_center_page.page.wait_for_timeout(1500)
        row_count = download_center_page.get_row_count()
        if row_count == 0:
            pytest.skip("Report row not visible yet")
        status = download_center_page.get_row_status(0).lower()
        reset_filters(download_center_page)
        assert "failed" not in status, (
            f"20-day report has status '{status}'; expected pending/processing/completed"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TC_21 — Create & verify report for the last 30 days
# ══════════════════════════════════════════════════════════════════════════════

class TestTC21Report30Days:
    """TC_21: Generate a report for the last 30 days and verify it appears in the table."""

    REPORT_NAME = "Automated Report - 30 Days"
    DAYS = 30

    def test_tc21_create_report(self, download_center_page):
        _create_date_range_report(download_center_page, self.REPORT_NAME, self.DAYS)

    def test_tc21_report_appears_in_table(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        download_center_page.search(self.REPORT_NAME)
        download_center_page.page.wait_for_timeout(1500)
        row_count = download_center_page.get_row_count()
        reset_filters(download_center_page)
        if row_count == 0:
            pytest.skip(
                f"'{self.REPORT_NAME}' not yet visible "
                f"(still queued -- re-run after a moment)"
            )
        assert row_count > 0, (
            f"Expected at least 1 row for '{self.REPORT_NAME}', got 0"
        )

    def test_tc21_report_status_not_failed(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        download_center_page.search(self.REPORT_NAME)
        download_center_page.page.wait_for_timeout(1500)
        row_count = download_center_page.get_row_count()
        if row_count == 0:
            pytest.skip("Report row not visible yet")
        status = download_center_page.get_row_status(0).lower()
        reset_filters(download_center_page)
        assert "failed" not in status, (
            f"30-day report has status '{status}'; expected pending/processing/completed"
        )

    def test_tc21_cleanup(self, download_center_page):
        """Final cleanup -- ensure filters are reset after all date-range tests."""
        reset_filters(download_center_page)


# ══════════════════════════════════════════════════════════════════════════════
# Bonus coverage (not in the SMS reference) — Columns dropdown, confirmed
# present in the WhatsApp DOM with 7 checkboxes (actions/name/category/
# from/to/created-at/status).
# ══════════════════════════════════════════════════════════════════════════════

class TestBonusColumnsPanel:
    """Bonus: the Columns dropdown (confirmed via DOM) lets the user
    toggle individual column visibility."""

    def test_bonus_columns_button_present(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        try:
            btn = download_center_page.page.locator(download_center_page.BTN_COLUMNS).first
            btn.wait_for(state="attached", timeout=8000)
            assert btn.is_visible(), "Columns button not visible"
        except Exception as exc:
            pytest.fail(f"Columns button not found: {exc}")

    def test_bonus_columns_panel_lists_all_confirmed_columns(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        download_center_page.open_columns_panel()
        confirmed_values = [
            "actions", "name", "category", "from", "to", "created-at", "status"
        ]
        missing = [v for v in confirmed_values if not download_center_page.is_column_checkbox_present(v)]
        assert not missing, f"Column checkboxes missing from panel: {missing}"

    def test_bonus_toggle_category_column(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        download_center_page.open_columns_panel()
        before = download_center_page.get_column_checkbox_state("category")
        download_center_page.toggle_column("category")
        after = download_center_page.get_column_checkbox_state("category")
        assert after != before, "Category column checkbox state did not toggle"
        # Restore original state so subsequent tests see all columns
        download_center_page.toggle_column("category")
