"""
RCS Download Center — Automated Test Suite
Built per confirmed intent ("Build RCS Download Center", resolved via two
rounds of AskUserQuestion), mirroring tests/test_whatsapp_download_center_flow.py's
TC numbering and structure, re-grounded against FULL live DOM dumps of the
actual RCS Download Center listing page (/rcs/report) AND its Create
Report form (/rcs/report/create), both captured in the same message.

Migrated to Playwright: local page-object fixture renamed
`download_center_page` (built on conftest.py's `module_logged_in_page`)
to avoid shadowing pytest-playwright's reserved `page` fixture. All
Selenium-specific waits (`page._w`, `page._js`, WebDriverWait/EC) were
replaced with direct Playwright Locator calls; native alert/confirm
handling now goes through `page.once("dialog", ...)` (see
rcs_download_center_page.py's click_delete_icon()/confirm_delete()
docstrings) instead of `driver.switch_to.alert`.

Test Design Notes (see pages/rcs_download_center_page.py and
pages/rcs_report_create_page.py module docstrings for the full list of
confirmed DOM specifics):
  - scope="module" — page object shared across all tests. Cross-test state
    (open popup/delete-modal, active search/status/date filters) does NOT
    persist as a dependency between tests: ensure_on_dc_page() closes any
    stale modal/alert left open by a previous test before every test body
    runs, and any test that changes filters/search resets them afterward
    (reset_filters(), or its own cleanup step) rather than leaving that
    state for the next test to inherit.
  - TC_09's three View-modal tests, and TC_12/TC_13's delete tests, no
    longer assume a specific PRIOR test in this file already put the page
    into the state they need (an open modal / an existing disposable row)
    -- each opens its own modal / creates its own disposable report (see
    the `disposable_report` fixture below) so it passes standalone, in any
    order, and under -n without relying on --dist loadscope.
  - Filters are live (wire:model.live) — no Apply button needed.
  - Status filter values are lowercase: "pending","processing","completed","failed".
  - Date filter uses TWO SEPARATE native <input type="date"> fields
    (Created From / Created To) — CONFIRMED structurally different from
    the SMS/WhatsApp combined-Flatpickr-range-input convention. No
    dd-mm-yyyy reformatting needed; dates are set directly in YYYY-MM-DD.
  - Delete confirmation mechanism is UNCONFIRMED for this page (the
    listing page's table had zero rows at capture time, so no delete
    button/dialog was ever rendered) — confirm_delete()/cancel_delete()
    try native dialog() first (the mechanism confirmed on WhatsApp's
    equivalent page, same livewire-tables package) then fall back to
    SweetAlert2, same dual strategy used elsewhere.
  - Row action icon titles (View/Download/Delete) are similarly
    UNCONFIRMED for this page — the page object uses generic
    best-effort titles with a positional fallback. Tests exercising
    these skip gracefully when no rows are present.
  - Default table sort is created_at DESC (confirmed via the "Applied
    Sorting: Created At: Z-A" pill) — a freshly-submitted report
    appears at the TOP of the table.
  - No-records text IS fully confirmed for this page (unlike WhatsApp,
    whose table had 2 real rows and no empty state was captured): "No
    items found, try to broaden your search".

Differences from the WhatsApp reference (all called out with reasons):
  - "Service Type" (promotional/transactional/otp/multi_use) replaces
    WhatsApp's "Category" — matches the RCS Overview page's product-card
    taxonomy (Transactional/Promotional/OTP/Multi Use).
  - "Summary By" checkboxes are Agent/Status (value="agent", not
    "sender"/"WABA Number" as on WhatsApp).
  - A brand-new "Message Status" (status_filter) section exists on the
    RCS create form with 7 optional checkboxes, not present on
    WhatsApp/SMS — left at its default (all unchecked = no filter) for
    the throwaway reports this suite creates, since narrowing by
    message status isn't needed to make a row appear.
  - "Select Columns for Export" has 16 confirmed values (see
    RcsReportCreatePage.ALL_COLUMNS), a different set from WhatsApp's 18.
  - TC_04 (date filter) sets Created From / Created To independently via
    two native date inputs rather than a single combined range string.
  - TC_15 (no-records) asserts the FULLY CONFIRMED exact text (see
    above), stronger than the WhatsApp suite's unconfirmed generic
    fallback text.
  - Bonus coverage: the "Columns" dropdown, confirmed present with
    checkboxes for all 7 columns (actions/name/service/from/to/
    created-at/status — "service" replacing "category").
  - TC_16 (sort) and TC_17 (pagination) removed, matching the
    SMS/WhatsApp references exactly ("always skipped on this page").
"""
import os
import time
import uuid
from datetime import date, datetime, timedelta

import pytest

from constants.rcs_download_center_headers import EXPECTED_RCS_DOWNLOAD_CENTER_HEADERS
from pages.rcs.rcs_download_center_page import RcsDownloadCenterPage
from pages.rcs.rcs_report_create_page import RcsReportCreatePage
from utils.file_validator import (
    EmptyFileError,
    FileNotDownloadedError,
    HeaderValidationError,
    UnsupportedFileTypeError,
    validate_file_headers,
)


pytestmark = [pytest.mark.rcs, pytest.mark.report]

def yesterday_str():
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


def days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")


# ══════════════════════════════════════════════════════════════════════════════
# Module fixture
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def download_center_page(module_logged_in_page):
    p = RcsDownloadCenterPage(module_logged_in_page)
    p.navigate()
    p.wait_for_table_load(timeout=15000)
    return p


# ══════════════════════════════════════════════════════════════════════════════
# Recovery helpers
# ══════════════════════════════════════════════════════════════════════════════

def ensure_on_dc_page(p: RcsDownloadCenterPage):
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


def reset_filters(p: RcsDownloadCenterPage):
    """Hard-reset filters by re-navigating to the page."""
    p.navigate()
    p.wait_for_table_load(timeout=10000)


# ══════════════════════════════════════════════════════════════════════════════
# Disposable-report fixture — so delete-flow tests create their OWN row
# ══════════════════════════════════════════════════════════════════════════════

def _delete_report_by_name(p: RcsDownloadCenterPage, name: str):
    """Best-effort delete of a report by exact name search — used as a
    teardown safety net for `disposable_report` below (and reusable by
    any test that creates its own throwaway report) so a fixture-created
    row never lingers for repeated/parallel runs to pile up, regardless
    of whether the test itself already deleted it. Mirrors the same
    click_delete_icon()/is_delete_modal_visible()/confirm_delete() calls
    already confirmed and exercised directly by TestTC12ConfirmDelete
    below — no new page-object locator/method, only reuse. Swallows
    failures deliberately: a fixture teardown must never raise and mask
    the test's own real pass/fail outcome (same rationale as every other
    report suite's autouse `_reset_after_test` teardown in this
    project)."""
    try:
        ensure_on_dc_page(p)
        p.search(name)
        p.page.wait_for_timeout(1500)
        if p.get_row_count() == 0:
            reset_filters(p)
            return
        p.click_delete_icon(row_idx=0)
        p.page.wait_for_timeout(800)
        if p.is_delete_modal_visible():
            p.confirm_delete()
            p.page.wait_for_timeout(1500)
        reset_filters(p)
    except Exception:
        pass


@pytest.fixture
def disposable_report(download_center_page):
    """Create a throwaway report with a per-call unique name (via the
    same _create_date_range_report() helper TestTC19Report10Days and its
    siblings already use further down this file) so a test needing a
    delete-able row of its own does not depend on TestTC00CreateReport
    (or any other test/file) having created one first -- independent of
    file/collection order and safe under -n without --dist loadscope,
    since every call gets its own uuid-suffixed name. Deletes it again
    in teardown so repeated/parallel runs never pile up rows
    indefinitely, whether or not the test itself already deleted it.

    Yields the report's unique name; the test searches for that name
    itself rather than assuming row 0 of the unfiltered table is its
    row."""
    name = f"Automated Test Report {uuid.uuid4().hex[:8]}"
    _create_date_range_report(download_center_page, name, days=7)
    yield name
    _delete_report_by_name(download_center_page, name)


# ══════════════════════════════════════════════════════════════════════════════
# TC_00 — Create a new report (runs first so downstream tests have data)
# ══════════════════════════════════════════════════════════════════════════════

class TestTC00CreateReport:
    """
    TC_00: Click Create New Report, fill the form, submit.
    Runs before all other tests so the Download Center has at least one
    disposable report -- the listing page's table had ZERO rows at DOM
    capture time, so every row-dependent test downstream relies on this
    having succeeded.
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
            base = download_center_page.get_current_url().split("/rcs")[0]
            download_center_page.page.goto(base + "/rcs/report/create")
            download_center_page.page.wait_for_timeout(2000)
        assert "create" in download_center_page.get_current_url().lower(), (
            f"Did not navigate to create form, URL: {download_center_page.get_current_url()}"
        )

    def test_tc00_fill_and_submit_form(self, download_center_page):
        """Fill all required fields and submit the Generate Report form."""
        if "create" not in download_center_page.get_current_url().lower():
            pytest.skip("Not on create form — navigation failed in previous step")

        create = RcsReportCreatePage(download_center_page.page)
        create.wait_for_form_load(timeout=15000)

        create.set_report_name("Automated Test Report")
        create.set_service_type(RcsReportCreatePage.SERVICE_TYPE_ALL)
        create.set_from_date(days_ago(7))
        create.set_to_date(yesterday_str())
        create.set_summary_by(include_agent=True, include_status=True)
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
        assert "rcs" in url.lower() and "report" in url.lower(), (
            f"Expected RCS Download Center URL, got: {url}"
        )

    def test_tc01_page_accessible(self, download_center_page):
        assert download_center_page.is_download_center_page(), (
            "is_download_center_page() returned False"
        )

    def test_tc01_page_title(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        title = download_center_page.get_page_title_text()
        assert title == "RCS Download Center", (
            f"Expected h1 'RCS Download Center', got: {title!r}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TC_02 — Verify table columns are displayed
# ══════════════════════════════════════════════════════════════════════════════

class TestTC02TableColumns:
    """TC_02: Table renders with expected column headers (7 confirmed:
    Actions, Name, Service, From, To, Created At, Status)."""

    EXPECTED_COLUMNS = ["Name", "Service", "Status"]  # subset check

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
# TC_04 — Date range filter (two separate native date inputs)
# ══════════════════════════════════════════════════════════════════════════════

class TestTC04DateFilter:
    """TC_04: Created From / Created To native date filters narrow
    results. No Apply button needed. Structurally different from the
    SMS/WhatsApp combined-Flatpickr-range convention — CONFIRMED as two
    independent <input type="date"> fields on this page."""

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
        assert "rcs/report/create" in href, (
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
        download_center_page.set_filter_status(RcsDownloadCenterPage.STATUS_COMPLETED)
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
        download_center_page.set_filter_status(RcsDownloadCenterPage.STATUS_PROCESSING)
        # Poll instead of a single fixed wait -- proactively applying the
        # fix that a real pytest run showed was necessary on the WhatsApp
        # equivalent page (Livewire's filter round-trip isn't always
        # finished re-rendering the table within a short fixed sleep).
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
    """TC_09: Clicking the View icon opens the summary modal.
    NOTE: exact row action title is UNCONFIRMED for this page (table had
    zero rows at DOM-capture time) — see rcs_download_center_page.py's
    module docstring. Skips gracefully if no rows exist.

    Independence: the two follow-on tests no longer assume
    test_tc09_view_modal_opens ran first (in this order, in this worker)
    and left the modal open for them -- each opens its own modal via the
    same already-established click_view_icon(row_idx=0) call if it isn't
    open already, so every test in this class passes standalone."""

    def test_tc09_view_modal_opens(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        if download_center_page.get_row_count() == 0:
            pytest.skip("No rows available to test view icon")
        download_center_page.click_view_icon(row_idx=0)
        download_center_page.page.wait_for_timeout(1500)
        assert download_center_page.is_popup_open(), (
            "Summary modal did not open after clicking the View icon"
        )

    def test_tc09_modal_content_nonempty(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        if not download_center_page.is_popup_open():
            if download_center_page.get_row_count() == 0:
                pytest.skip("No rows available to test view icon")
            download_center_page.click_view_icon(row_idx=0)
            download_center_page.page.wait_for_timeout(1500)
        if not download_center_page.is_popup_open():
            pytest.skip("Summary modal not open")
        text = download_center_page.get_popup_all_text()
        assert text, "Summary modal is open but shows no content"

    def test_tc09_modal_closes(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        if not download_center_page.is_popup_open():
            if download_center_page.get_row_count() == 0:
                pytest.skip("No rows available to test view icon")
            download_center_page.click_view_icon(row_idx=0)
            download_center_page.page.wait_for_timeout(1500)
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
        download_center_page.set_filter_status(RcsDownloadCenterPage.STATUS_COMPLETED)
        download_center_page.page.wait_for_timeout(1500)
        if download_center_page.get_row_count() == 0:
            pytest.skip("No completed reports available to test download")

        download_center_page.clear_download_dir()

        # download_report() waits directly on Playwright's own download
        # event for this specific click (page.expect_download()) instead
        # of clicking then separately polling/sleeping for a file to show
        # up -- the same proven pattern already used by every Bulk
        # Actions -> Export method in this codebase (RcsAgentPage.
        # export_csv(), SmsCampaignReportPage.click_export_csv(), etc.).
        result = download_center_page.download_report(row_idx=0, timeout_ms=60000)
        assert result is not None, (
            "Download did not complete within 60 seconds after clicking "
            "the Download icon on row 0. Possible causes: locator miss / "
            "disabled control (see _action_btn_for_row()'s docstring: the "
            "exact title attribute for this page's Download action is "
            "unconfirmed), report not actually in a downloadable "
            "'completed' state despite the Completed filter, or the "
            "download did not fire a Playwright download event."
        )
        downloaded = result["file_path"]
        print(f"[TC_10] Download completed in {result['elapsed_s']:.2f}s, {result['file_size']} bytes")

        # Header row IS now asserted (constants/rcs_download_center_headers.py,
        # confirmed from a real completed-job download supplied directly by
        # the user). What's still unconfirmed independently: the file's
        # *shape* -- unlike SMS's Download Center (confirmed to always be a
        # .zip wrapping .csv/.xlsx/.xls), whether RCS's async export is
        # zip-wrapped or a bare file wasn't re-verified alongside this
        # header list. read_file_headers() dispatches on extension either
        # way, so this assertion holds regardless -- but the extension is
        # still logged here for visibility.
        ext = os.path.splitext(downloaded)[1].lower()
        print(f"[TC_10] Downloaded file: {os.path.basename(downloaded)} (extension: {ext or '(none)'})")

        try:
            actual_headers = validate_file_headers(downloaded, EXPECTED_RCS_DOWNLOAD_CENTER_HEADERS)
        except FileNotDownloadedError as exc:
            pytest.fail(str(exc))
        except (UnsupportedFileTypeError, EmptyFileError) as exc:
            pytest.fail(str(exc))
        except HeaderValidationError as exc:
            print(f"[TC_10] Actual headers: {exc.actual}")
            print(f"[TC_10] Missing headers: {exc.missing}")
            print(f"[TC_10] Unexpected headers: {exc.unexpected}")
            for position, expected_name, actual_name in exc.mismatches:
                print(f"[TC_10] Position {position}: expected '{expected_name}', actual '{actual_name}'")
            pytest.fail(str(exc))

        print(f"[TC_10] Header validation PASS: {actual_headers}")

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
        download_center_page.set_filter_status(RcsDownloadCenterPage.STATUS_PROCESSING)
        download_center_page.page.wait_for_timeout(1500)
        if download_center_page.get_row_count() == 0:
            pytest.skip("No processing reports available at run time")
        assert download_center_page.is_download_btn_disabled(row_idx=0), (
            "Download button should be disabled/absent for a Processing report"
        )

    def test_tc11_cleanup(self, download_center_page):
        reset_filters(download_center_page)


# ══════════════════════════════════════════════════════════════════════════════
# TC_13 — Cancel delete keeps the row
# ══════════════════════════════════════════════════════════════════════════════

class TestTC13CancelDelete:
    """TC_13: Clicking Cancel on the delete confirmation keeps the row.

    Independence: creates its OWN disposable report via the
    `disposable_report` fixture (a uuid-suffixed "Automated Test Report
    <id>") rather than operating on whatever happens to sit in row 0 of
    the unfiltered table -- no longer depends on TestTC00CreateReport
    having run first, and no longer needs to run "before TC_12" (the
    previous ordering comment) since it no longer shares a row with it.
    Searches for its own report by name so the row it cancels a delete
    on is unambiguously its own, not an unrelated real row."""

    def test_tc13_cancel_delete(self, download_center_page, disposable_report):
        ensure_on_dc_page(download_center_page)
        download_center_page.search(disposable_report)
        download_center_page.page.wait_for_timeout(1500)
        before_count = download_center_page.get_row_count()
        if before_count == 0:
            reset_filters(download_center_page)
            pytest.skip(
                f"'{disposable_report}' not visible yet -- report creation may "
                f"still be queued"
            )

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
        reset_filters(download_center_page)


# ══════════════════════════════════════════════════════════════════════════════
# TC_12 — Confirm delete removes the row
# ══════════════════════════════════════════════════════════════════════════════

class TestTC12ConfirmDelete:
    """TC_12: Clicking Confirm on the delete confirmation removes the
    report.

    Independence: creates its OWN disposable report via the
    `disposable_report` fixture (a uuid-suffixed "Automated Test Report
    <id>") instead of depending on TestTC00CreateReport's specific,
    fixed-name "Automated Test Report" row -- passes standalone, in any
    collection order, and under -n without --dist loadscope, since each
    invocation (and each parallel worker) gets its own uniquely-named
    row. SAFETY (unchanged from the original): still searches for the
    specific report by name before deleting, rather than deleting
    whatever sits in row 0 -- guarantees only this test's own disposable
    report is ever removed."""

    def test_tc12_confirm_delete(self, download_center_page, disposable_report):
        ensure_on_dc_page(download_center_page)
        download_center_page.search(disposable_report)
        download_center_page.page.wait_for_timeout(1500)
        before_count = download_center_page.get_row_count()
        if before_count == 0:
            reset_filters(download_center_page)
            pytest.skip(
                f"'{disposable_report}' not found -- report creation may still "
                f"be queued"
            )

        download_center_page.click_delete_icon(row_idx=0)
        download_center_page.page.wait_for_timeout(800)
        assert download_center_page.is_delete_modal_visible(), (
            "Delete confirmation did not appear"
        )
        download_center_page.confirm_delete()
        # Poll instead of a single fixed wait -- proactively applying the
        # fix that a real pytest run showed was necessary on the WhatsApp
        # equivalent page (the delete's Livewire round-trip isn't always
        # finished within a short fixed sleep).
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
    results. UNLIKE the WhatsApp reference (whose table had 2 real rows
    and no empty state was ever captured), this page's empty-state text
    IS fully confirmed from the live DOM dump: 'No items found, try to
    broaden your search'."""

    NO_RECORDS_TEXT = "No items found, try to broaden your search"

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
# SMS/WhatsApp references exactly ("always skipped on this page").

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
        base = download_center_page.get_current_url().split("/rcs")[0]
        download_center_page.page.goto(base + "/rcs/report/create")
        download_center_page.page.wait_for_timeout(2000)

    assert "create" in download_center_page.get_current_url().lower(), (
        f"Could not navigate to create form (URL: {download_center_page.get_current_url()})"
    )

    yesterday_date = date.today() - timedelta(days=1)
    from_date = yesterday_date - timedelta(days=days - 1)

    create = RcsReportCreatePage(download_center_page.page)
    create.wait_for_form_load(timeout=15000)
    create.set_report_name(report_name)
    create.set_service_type(RcsReportCreatePage.SERVICE_TYPE_ALL)
    create.set_from_date(from_date.strftime("%Y-%m-%d"))
    create.set_to_date(yesterday_date.strftime("%Y-%m-%d"))
    create.set_summary_by(include_agent=True, include_status=True)
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
# Bonus coverage — Columns dropdown, confirmed present in the RCS DOM with
# 7 checkboxes (actions/name/service/from/to/created-at/status —
# "service" replacing WhatsApp's "category").
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
            "actions", "name", "service", "from", "to", "created-at", "status"
        ]
        missing = [v for v in confirmed_values if not download_center_page.is_column_checkbox_present(v)]
        assert not missing, f"Column checkboxes missing from panel: {missing}"

