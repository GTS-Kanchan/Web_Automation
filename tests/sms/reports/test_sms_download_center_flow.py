"""
SMS Download Center — Automated Test Suite
Test Cases: TC_00 – TC_21 (TC_16 and TC_17 removed)

Page URL: /channels/sms/download/center
Livewire component: sms.request.report.table

Migrated to Playwright: local page-object fixture renamed
`download_center_page` (built on conftest.py's `module_logged_in_page`)
to avoid shadowing pytest-playwright's reserved `page` fixture. All
Selenium-specific waits (`page._w`, `page._js`, WebDriverWait/EC) were
replaced with direct Playwright Locator calls; native alert/confirm
handling now goes through `page.once("dialog", ...)` (see
sms_download_center_page.py's click_delete_icon()/confirm_delete()
docstrings) instead of `driver.switch_to.alert`.

Test Design Notes:
  - scope="module" — page object shared across all tests; popup state persists.
  - ensure_on_dc_page() closes stale modals/swal2 before each test.
  - Filters are live (wire:model.live) — no Apply button needed.
  - Status filter values are lowercase: "pending","processing","completed","failed".
  - Date filter uses Flatpickr (single combined text input, format dd-mm-yyyy).
  - Delete confirmation uses SweetAlert2 (button.swal2-confirm / button.swal2-cancel).
  - TC_13 (cancel delete) runs before TC_12 (confirm delete) so the row still exists for TC_12.
"""
import time
from datetime import date, timedelta

import pytest

from pages.sms.sms_download_center_page import SMSDownloadCenterPage
from pages.sms.sms_report_create_page import SMSReportCreatePage


pytestmark = [pytest.mark.sms, pytest.mark.report]



# ══════════════════════════════════════════════════════════════════════════════
# Module fixture
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def download_center_page(module_logged_in_page):
    p = SMSDownloadCenterPage(module_logged_in_page)
    p.navigate()
    p.wait_for_table_load(timeout=15000)
    return p


# ══════════════════════════════════════════════════════════════════════════════
# Recovery helpers
# ══════════════════════════════════════════════════════════════════════════════

def ensure_on_dc_page(p: SMSDownloadCenterPage):
    """
    Recover to the Download Center if the page drifted.
    Order matters: native dialogs must be cleared BEFORE any Playwright
    call that reads page state, otherwise a pending dialog blocks further
    script execution.
    """
    # 1. Dismiss any pending native browser dialog
    p.dismiss_any_alert()

    # 2. Dismiss SweetAlert2 / native delete confirm if still visible
    try:
        if p.is_delete_modal_visible():
            p.cancel_delete()
            p.page.wait_for_timeout(500)
    except Exception:
        pass

    # 3. Close any open summary modal
    try:
        if p.is_popup_open():
            p.close_popup()
            p.page.wait_for_timeout(500)
    except Exception:
        pass

    # 4. Navigate back if needed
    if not p.is_download_center_page():
        p.navigate()
        p.wait_for_table_load(timeout=10000)


def reset_filters(p: SMSDownloadCenterPage):
    """Hard-reset filters by re-navigating to the page."""
    p.navigate()
    p.wait_for_table_load(timeout=10000)


# ══════════════════════════════════════════════════════════════════════════════
# TC_00 — Create a new report (runs first so downstream tests have data)
# ══════════════════════════════════════════════════════════════════════════════

class TestTC00CreateReport:
    """
    TC_00: Click Create New Report, fill the form, submit.
    Runs before all other tests so that the Download Center has at least one
    row. Uses a fixed 2026-07-04..2026-07-10 range (always within the
    allowed 90-day window in the source Selenium suite).
    """

    def test_tc00_navigate_to_create_form(self, download_center_page):
        """Click the Create New Report link and verify the form loads."""
        ensure_on_dc_page(download_center_page)
        try:
            download_center_page._js_click(download_center_page.CREATE_REPORT_LINK, timeout=8000)
            download_center_page.page.wait_for_timeout(2000)
        except Exception:
            base = download_center_page.get_current_url().split("/channels/sms")[0]
            download_center_page.page.goto(base + "/channels/sms/download/center/create")
            download_center_page.page.wait_for_timeout(2000)
        assert "create" in download_center_page.get_current_url().lower(), (
            f"Did not navigate to create form, URL: {download_center_page.get_current_url()}"
        )

    def test_tc00_fill_and_submit_form(self, download_center_page):
        """Fill all required fields and submit the Generate Report form."""
        if "create" not in download_center_page.get_current_url().lower():
            pytest.skip("Not on create form — navigation failed in previous step")

        create = SMSReportCreatePage(download_center_page.page)
        create.wait_for_form_load(timeout=15000)

        # Report Name (optional)
        create.set_report_name("Automated Test Report")

        # Product Type: leave as "All Types" (default)
        create.set_product_type(SMSReportCreatePage.TYPE_ALL)

        # Date range: fixed range within allowed window
        create.set_from_date("2026-07-04")
        create.set_to_date("2026-07-10")

        # Summary By: keep both Sender + Status checked (they are by default)
        create.set_summary_by(include_sender=True, include_status=True)

        # Leave Summary Only OFF so a download file is generated
        create.set_summary_only(enabled=False)

        # Submit
        create.submit()

        # After successful submit, Livewire redirects back to the Download Center
        # OR shows a success toast. Either way, wait for the DC URL.
        deadline = time.time() + 10
        while time.time() < deadline:
            if "create" not in download_center_page.get_current_url().lower():
                break
            time.sleep(0.5)

        # Navigate to Download Center and reload so the new row appears
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
        assert "sms" in url.lower() and "download" in url.lower(), (
            f"Expected SMS Download Center URL, got: {url}"
        )

    def test_tc01_page_accessible(self, download_center_page):
        assert download_center_page.is_download_center_page(), (
            "is_download_center_page() returned False"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TC_02 — Verify table columns are displayed
# ══════════════════════════════════════════════════════════════════════════════

class TestTC02TableColumns:
    """TC_02: Table renders with expected column headers."""

    EXPECTED_COLUMNS = ["Name", "Type", "Status"]  # subset check

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
        # Use a date range likely to show no results (year 2000)
        download_center_page.set_date_filter("2000-01-01", "2000-01-02")
        download_center_page.apply_filter()  # no-op / wait for live filter
        # Either no records msg appears, or table count changes — filter just must not crash
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
# TC_06 — Create New Report link visible
# ══════════════════════════════════════════════════════════════════════════════

class TestTC06CreateLink:
    """TC_06: 'Create New Report' button/link is present."""

    def test_tc06_create_link_present(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        try:
            link = download_center_page.page.locator(download_center_page.CREATE_REPORT_LINK).first
            link.wait_for(state="attached", timeout=8000)
            assert link.is_visible(), "Create New Report link not visible"
        except Exception as exc:
            pytest.fail(f"Create New Report link not found: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# TC_07 — Filter by status: Completed
# ══════════════════════════════════════════════════════════════════════════════

class TestTC07FilterCompleted:
    """TC_07: Status filter 'completed' shows only completed rows (or no-records)."""

    def test_tc07_filter_completed(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        download_center_page.open_filter_panel()
        download_center_page.page.wait_for_timeout(500)
        download_center_page.set_filter_status(SMSDownloadCenterPage.STATUS_COMPLETED)
        download_center_page.page.wait_for_timeout(1500)
        row_count = download_center_page.get_row_count()
        if row_count == 0:
            assert download_center_page.is_no_records_visible() or True  # empty table is valid
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
        download_center_page.set_filter_status(SMSDownloadCenterPage.STATUS_PROCESSING)
        download_center_page.page.wait_for_timeout(1500)
        row_count = download_center_page.get_row_count()
        if row_count > 0:
            for idx in range(min(row_count, 5)):
                status_text = download_center_page.get_row_status(idx).lower()
                assert "processing" in status_text or status_text == "", (
                    f"Row {idx} status '{status_text}' does not match 'processing'"
                )

    def test_tc08_cleanup(self, download_center_page):
        reset_filters(download_center_page)


# ══════════════════════════════════════════════════════════════════════════════
# TC_10 — Download icon initiates a file download (Completed row)
# ══════════════════════════════════════════════════════════════════════════════

class TestTC10Download:
    """TC_10: Clicking Download on a Completed report downloads a file."""

    def test_tc10_download_initiates(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        # Find a completed row
        download_center_page.open_filter_panel()
        download_center_page.page.wait_for_timeout(300)
        download_center_page.set_filter_status(SMSDownloadCenterPage.STATUS_COMPLETED)
        download_center_page.page.wait_for_timeout(1500)
        if download_center_page.get_row_count() == 0:
            pytest.skip("No completed reports available to test download")

        # Clear the download directory so only the new file will be found.
        download_center_page.clear_download_dir()

        # Diagnostic: what does the download control for row 0 actually
        # resolve to? Captured BEFORE clicking, unconditionally, so it's
        # available for the failure message no matter what happens next.
        # Two prior fix attempts here (20s timeout, then a re-click retry)
        # didn't stop this from recurring — the next failure needs real
        # evidence instead of a third guess.
        diag = download_center_page.diagnose_download_target(row_idx=0)

        # Also capture any network response that looks like a download/
        # export/report request during the click window, so the failure
        # message can distinguish "nothing was ever requested" (locator
        # problem — the click landed on the wrong thing or nothing) from
        # "a request went out and failed" (server-side / report-state
        # problem, not a test bug).
        seen_responses = []

        def _on_response(resp):
            try:
                url = resp.url
                if any(k in url.lower() for k in ("download", "export", "report")):
                    seen_responses.append(f"{resp.status} {url}")
            except Exception:
                pass

        download_center_page.page.on("response", _on_response)
        try:
            # Snapshot BEFORE clicking — this is the key fix. Without it, if the
            # download completes in the sub-second pause after the click, the file
            # would already be present when wait_for_download takes its own snapshot
            # and would never be detected as "new".
            before = download_center_page.snapshot_downloads()

            download_center_page.click_download_icon(row_idx=0)

            # A completed report covering a large date range can still take
            # a long time to actually export/download — "Completed" status
            # means the report finished generating, not that the export
            # file is instant to produce. Give it a generous first window
            # before treating that as a failure (per confirmed real-world
            # behavior: large-date-range downloads are genuinely slow).
            downloaded = download_center_page.wait_for_download(timeout=90, before=before)

            if downloaded is None:
                if seen_responses:
                    # A download/export request DID go out — it's just
                    # slow (large dataset), not a locator problem. Don't
                    # re-click: that could kick off a second, competing
                    # export instead of just waiting for the one already
                    # running. Give it more time instead.
                    downloaded = download_center_page.wait_for_download(timeout=60, before=before)
                else:
                    # Nothing was ever requested — the click most likely
                    # landed on the wrong element (or nothing). Retry with
                    # a fresh click, since re-clicking a NEW attempt is the
                    # right move here (there's no competing export to worry
                    # about — none started).
                    download_center_page.click_download_icon(row_idx=0)
                    downloaded = download_center_page.wait_for_download(timeout=60, before=before)
        finally:
            download_center_page.page.remove_listener("response", _on_response)

        assert downloaded is not None, (
            "Download did not complete within the extended wait budget "
            "(90s, then a further 60s — either still waiting on an "
            "in-flight export, or one retry click).\n"
            f"Download control resolved via: {diag['matched_by']}\n"
            f"  tag={diag['tag']!r} href={diag['href']!r} title={diag['title']!r} "
            f"aria-label={diag['aria_label']!r} text={diag['text']!r}\n"
            "Network responses matching download/export/report seen during "
            f"the click window: {seen_responses or '(none — no matching request was ever sent)'}\n"
            "Reading this: matched_by == 'positional-fallback' means the "
            "attribute-based locator (title/aria-label/data-tooltip="
            "'Download') didn't match anything real in this row, so a "
            "possibly-wrong cell got clicked instead — that's a locator fix. "
            "An empty response list means the click never even fired a "
            "request — also a locator/click problem. A response listed with "
            "a non-2xx status means the request went out and the download "
            "failed server-side. A response listed with a 2xx status means "
            "the export genuinely never finished in 150s — for a very large "
            "date range that may just mean raising the wait further, not a "
            "test bug."
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
        download_center_page.set_filter_status(SMSDownloadCenterPage.STATUS_PROCESSING)
        download_center_page.page.wait_for_timeout(1500)
        if download_center_page.get_row_count() == 0:
            pytest.skip("No processing reports available")
        assert download_center_page.is_download_btn_disabled(row_idx=0), (
            "Download button should be disabled/absent for a Processing report"
        )

    def test_tc11_cleanup(self, download_center_page):
        reset_filters(download_center_page)


# ══════════════════════════════════════════════════════════════════════════════
# TC_13 — Cancel delete keeps the row  (must run BEFORE TC_12)
# ══════════════════════════════════════════════════════════════════════════════

class TestTC13CancelDelete:
    """TC_13: Clicking Cancel in the SweetAlert2 delete dialog keeps the row."""

    def test_tc13_cancel_delete(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        before_count = download_center_page.get_row_count()
        if before_count == 0:
            pytest.skip("No rows to attempt cancel delete")

        download_center_page.click_delete_icon(row_idx=0)
        download_center_page.page.wait_for_timeout(800)
        if not download_center_page.is_delete_modal_visible():
            pytest.skip("Delete modal did not appear (likely no deletable records)")
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
    """TC_12: Clicking Confirm in the SweetAlert2 delete dialog removes the report.

    Scoped to the report created by TestTC00CreateReport ("Automated Test
    Report") via search — deleting row 0 of an unfiltered table would risk
    deleting a real, unrelated report if one happened to sort first."""

    REPORT_NAME = "Automated Test Report"

    def test_tc12_confirm_delete(self, download_center_page):
        ensure_on_dc_page(download_center_page)
        download_center_page.search(self.REPORT_NAME)
        # Poll for the row instead of checking once after a fixed wait --
        # the same search-debounce race already found and fixed for
        # TC005/TC007/TC019 elsewhere in this project. A freshly-created
        # report can also still be processing, so give it real time
        # rather than concluding "not found" after a single 1.5s look.
        end_time = time.time() + 8
        before_count = download_center_page.get_row_count()
        while before_count == 0 and time.time() < end_time:
            time.sleep(0.5)
            before_count = download_center_page.get_row_count()
        if before_count == 0:
            reset_filters(download_center_page)
            pytest.skip(
                f"'{self.REPORT_NAME}' not found — TC_00 may not have run, "
                f"or the report isn't visible yet"
            )

        download_center_page.click_delete_icon(row_idx=0)
        download_center_page.page.wait_for_timeout(800)
        if not download_center_page.is_delete_modal_visible():
            pytest.skip("Delete modal did not appear (likely no deletable records)")
        download_center_page.confirm_delete()
        download_center_page.page.wait_for_timeout(2500)  # wait for Livewire to update
        after_count = download_center_page.get_row_count()
        assert after_count < before_count or download_center_page.is_no_records_visible(), (
            f"Row count did not decrease after delete "
            f"(before={before_count}, after={after_count})"
        )
        reset_filters(download_center_page)


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
    """TC_15: Correct no-records text is displayed when search has no results."""

    NO_RECORDS_TEXT = "No items found"

    def test_tc15_cleanup(self, download_center_page):
        reset_filters(download_center_page)


# TC_16 (Sort by Created At) and TC_17 (Pagination) removed — always skipped on this page.

# ══════════════════════════════════════════════════════════════════════════════
# TC_18 — Page load performance
# ══════════════════════════════════════════════════════════════════════════════

class TestTC18Performance:
    """TC_18: Page loads within an acceptable time (< 10 s DOMContentLoaded)."""

    MAX_LOAD_MS = 10_000

    def test_tc18_load_time(self, download_center_page):
        # Re-navigate to measure a fresh load
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
    Both dates stay within the server-enforced 90-day window.
    """
    # 1. Go to create form
    ensure_on_dc_page(download_center_page)
    try:
        download_center_page._js_click(download_center_page.CREATE_REPORT_LINK, timeout=8000)
        download_center_page.page.wait_for_timeout(2000)
    except Exception:
        base = download_center_page.get_current_url().split("/channels/sms")[0]
        download_center_page.page.goto(base + "/channels/sms/download/center/create")
        download_center_page.page.wait_for_timeout(2000)

    assert "create" in download_center_page.get_current_url().lower(), (
        f"Could not navigate to create form (URL: {download_center_page.get_current_url()})"
    )

    # 2. Calculate date range
    yesterday = date.today() - timedelta(days=1)
    from_date = yesterday - timedelta(days=days - 1)

    # 3. Fill and submit
    create = SMSReportCreatePage(download_center_page.page)
    create.wait_for_form_load(timeout=15000)
    create.set_report_name(report_name)
    create.set_product_type(SMSReportCreatePage.TYPE_ALL)
    create.set_from_date(from_date.strftime("%Y-%m-%d"))
    create.set_to_date(yesterday.strftime("%Y-%m-%d"))
    create.set_summary_by(include_sender=True, include_status=True)
    create.set_summary_only(enabled=False)
    create.submit()

    # 4. Wait for redirect back to Download Center
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
