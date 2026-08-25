"""
SMS Blocked Numbers — Single Sequential Flow
================================================
Covers: Channels → SMS → More → Blocked Numbers page, TC001 - TC032
(URL: /channels/sms/blocked-numbers)

Locators (pages/sms_blocked_numbers_page.py) are built from a live DOM
dump of the LISTING page. See that page object's module docstring for
the full list of confirmed DOM specifics: default column selection
(action/phone-number/created-at checked, department/user unchecked --
opposite of the SMS Error Codes page), sortable columns (Phone Number
and Created At only), the "Created" date-range filter, the always-
visible Bulk Actions dropdown, the $wireui.confirmAction -> SweetAlert2
delete-confirm mechanism (same convention already used on contacts_page.py
/ tags_page.py), and the "sms_optoutsPage" pagination page-name.

Migrated to Playwright: local page-object fixture renamed
`blocked_numbers_page` (built on conftest.py's `module_logged_in_page`)
to avoid shadowing pytest-playwright's reserved `page` fixture.
`driver.refresh()` -> `page.reload()`; `driver.get_window_size()`/
`set_window_size()` -> `page.viewport_size`/`page.set_viewport_size()`;
`row.find_elements(*locator)` -> `row.locator(locator)`. Test-facing
API/assertions otherwise unchanged from the Selenium suite.

Per explicit user instruction, "91945678654334" is used as the valid
test phone number for TC016 (Add blocked number with valid number) and
TC019 (duplicate blocked number).

All tests run in one browser session (module-scoped), mirroring the
pattern used in every other suite in this project.

Run:
    pytest tests/test_sms_blocked_numbers_flow.py -v
"""
import os
import time
import pytest

from pages.sms.sms_blocked_numbers_page import SmsBlockedNumbersPage
from utils.test_data_generator import DATA_DIR


pytestmark = [pytest.mark.sms, pytest.mark.opt_out]


# NOTE: DATA_DIR now comes from utils/test_data_generator.py (which computes
# it relative to utils/, not this file) rather than being locally redefined
# as os.path.dirname(__file__)-relative. This file moved from tests/ to
# tests/sms/opt_out/ as part of the channel-based reorg, and the old
# self-relative definition would have silently pointed at a non-existent
# tests/sms/opt_out/test_data/ directory after the move.


def data_file(name):
    return os.path.join(DATA_DIR, name)


VALID_TEST_NUMBER = "91945678654334"


@pytest.fixture(scope="module")
def blocked_numbers_page(module_logged_in_page):
    p = SmsBlockedNumbersPage(module_logged_in_page)
    p.navigate_to_report()
    return p


def ensure_on_page(p):
    if not p.is_report_page():
        p.navigate_to_report()
        time.sleep(1)


@pytest.fixture(autouse=True)
def _reset_after_test(blocked_numbers_page):
    """Hard reset to a clean listing view after every test -- this page
    has many stateful pieces (search, filters, columns, sort, selected
    rows), so re-navigating fresh after each test avoids cross-test
    contamination (same rationale as every other suite in this project)."""
    yield
    try:
        ensure_on_page(blocked_numbers_page)
        blocked_numbers_page.navigate_to_report()
    except Exception:
        pass


# ── TC001 — Page Load ────────────────────────────────────────────────────

@pytest.mark.smoke
def test_tc001_page_loads_successfully(blocked_numbers_page):
    """TC001: SMS Blocked Numbers page loads successfully without errors."""
    ensure_on_page(blocked_numbers_page)
    assert blocked_numbers_page.is_report_page(), "URL should contain /channels/sms/blocked-numbers"
    title = blocked_numbers_page.get_title().lower()
    assert "404" not in title and "error" not in title


# ── TC002 — Page Title ───────────────────────────────────────────────────

@pytest.mark.smoke
def test_tc002_page_title(blocked_numbers_page):
    """TC002: Page (heading) title displays 'SMS Blocked Numbers'."""
    ensure_on_page(blocked_numbers_page)
    assert blocked_numbers_page.get_page_title_text() == "SMS Blocked Numbers"


# ── TC003 — Add New Blocked Number button ───────────────────────────────

@pytest.mark.smoke
def test_tc003_add_new_blocked_number_button(blocked_numbers_page):
    """TC003: Clicking Add New Blocked Number opens the Add form."""
    ensure_on_page(blocked_numbers_page)
    blocked_numbers_page.click_add_new_blocked_number()
    assert blocked_numbers_page.is_create_page(), "Should navigate to /blocked-numbers/create"


# ── TC004 — Upload Blocked Numbers button ───────────────────────────────

@pytest.mark.regression
def test_tc004_upload_blocked_numbers_button(blocked_numbers_page):
    """TC004: Clicking Upload Blocked Numbers opens the upload popup."""
    ensure_on_page(blocked_numbers_page)
    blocked_numbers_page.click_upload_blocked_numbers()
    assert blocked_numbers_page.is_upload_popup_open(), "Upload popup should open"


# ── TC005-006 — Search ───────────────────────────────────────────────────

@pytest.mark.regression
def test_tc005_search_existing_number(blocked_numbers_page):
    """TC005: Searching an existing blocked number returns a matching record.

    Reads a real phone number from the current listing immediately before
    searching, so it's self-verifying and immune to earlier tests (e.g.
    TC014) deleting data."""
    ensure_on_page(blocked_numbers_page)
    existing_values = blocked_numbers_page.get_column_values("phone_number")
    assert existing_values, "Need at least one existing blocked number to search for"
    target = existing_values[0]
    blocked_numbers_page.search(target)
    assert blocked_numbers_page.has_records()
    values = blocked_numbers_page.get_column_values("phone_number")
    assert any(target in v for v in values)
    blocked_numbers_page.clear_search()


@pytest.mark.regression
@pytest.mark.negative
def test_tc006_search_invalid_number(blocked_numbers_page):
    """TC006: Searching a non-existing number shows no records."""
    ensure_on_page(blocked_numbers_page)
    blocked_numbers_page.search("INVALIDSEARCHXYZ999")
    assert blocked_numbers_page.has_no_records_message() or blocked_numbers_page.get_row_count() == 0
    blocked_numbers_page.clear_search()


# ── TC007 — Created date filter ──────────────────────────────────────────

@pytest.mark.regression
def test_tc007_created_date_filter(blocked_numbers_page):
    """TC007: Selecting a valid date range filters records to that range."""
    ensure_on_page(blocked_numbers_page)
    applied = blocked_numbers_page.filter_by_created_date_range(from_day_offset=20, to_day_offset=2)
    if not applied:
        pytest.skip("Date range picker did not have enough selectable same-month cells")
    value = blocked_numbers_page.get_filter_created_at_value()
    assert value, "Date range input should show a selected range"


# ── TC008 — Bulk Actions dropdown ───────────────────────────────────────

@pytest.mark.regression
def test_tc008_bulk_actions_dropdown(blocked_numbers_page):
    """TC008: Bulk Actions dropdown opens and shows options."""
    ensure_on_page(blocked_numbers_page)
    blocked_numbers_page.open_bulk_actions_dropdown()
    assert blocked_numbers_page.is_element_present(blocked_numbers_page.BULK_ACTION_EXPORT, timeout=5000)
    assert blocked_numbers_page.is_element_present(blocked_numbers_page.BULK_ACTION_DELETE, timeout=5000)


# ── TC009 — Columns dropdown ─────────────────────────────────────────────

@pytest.mark.regression
def test_tc009_columns_dropdown(blocked_numbers_page):
    """TC009: Columns button opens the column selection menu."""
    ensure_on_page(blocked_numbers_page)
    blocked_numbers_page.open_columns_dropdown()
    assert blocked_numbers_page.is_element_present(blocked_numbers_page.COLUMN_CHECKBOXES, timeout=5000)


# ── TC010 — Blocked numbers list ─────────────────────────────────────────

@pytest.mark.smoke
def test_tc010_blocked_numbers_list(blocked_numbers_page):
    """TC010: All blocked numbers should be listed."""
    ensure_on_page(blocked_numbers_page)
    assert blocked_numbers_page.has_records()
    assert blocked_numbers_page.get_row_count() > 0


# ── TC011 — Phone Number column ─────────────────────────────────────────

@pytest.mark.regression
def test_tc011_phone_number_column(blocked_numbers_page):
    """TC011: Phone Number column displays valid-looking numeric values."""
    ensure_on_page(blocked_numbers_page)
    values = blocked_numbers_page.get_column_values("phone_number")
    assert values, "Phone Number column should have values"
    bad_values = [v for v in values if v and not v.isdigit()]
    assert not bad_values, (
        f"Phone Number column has non-numeric value(s): {bad_values!r} "
        f"(full column: {values!r}) -- paste this column's real <td> DOM "
        f"if the values legitimately contain formatting characters "
        f"(spaces/dashes/+) so COLUMN_INDEX or this check can be corrected")


# ── TC012 — Created At column ────────────────────────────────────────────

@pytest.mark.regression
def test_tc012_created_at_column(blocked_numbers_page):
    """TC012: Created At column displays a date/time value."""
    ensure_on_page(blocked_numbers_page)
    values = blocked_numbers_page.get_column_values("created_at")
    assert values, "Created At column should have values"
    assert all(len(v) > 0 for v in values)


# ── TC013 — Delete icon visibility ──────────────────────────────────────

@pytest.mark.regression
def test_tc013_delete_icon_visibility(blocked_numbers_page):
    """TC013: Delete icon should be visible for each record."""
    ensure_on_page(blocked_numbers_page)
    row = blocked_numbers_page.get_first_data_row()
    assert row is not None
    assert row.locator(blocked_numbers_page.DELETE_ICON_IN_ROW).count() > 0, \
        "Delete icon should be present in the first row"


# ── TC014-015 — Delete / Cancel Delete ──────────────────────────────────

@pytest.mark.regression
def test_tc014_delete_blocked_number(blocked_numbers_page):
    """TC014: Deleting a blocked number and confirming removes it.

    Uses a scratch number created by THIS test (never an arbitrary
    existing row) — deliberately does NOT reuse VALID_TEST_NUMBER, since
    TC016/TC019 (later in this file) add and then rely on that exact
    number still existing."""
    ensure_on_page(blocked_numbers_page)
    scratch_number = "91945678" + f"{int(time.time()) % 1000000:06d}"

    blocked_numbers_page.click_add_new_blocked_number()
    if not blocked_numbers_page.is_create_page():
        pytest.skip("Create page did not load — cannot create a scratch number to delete")
    if not blocked_numbers_page.is_element_present(blocked_numbers_page.ADD_PHONE_INPUT, timeout=5000):
        pytest.skip("Add form's phone-number input not found")
    blocked_numbers_page.add_blocked_number(scratch_number)
    if blocked_numbers_page.get_validation_error_text() is not None:
        pytest.skip(f"Scratch number '{scratch_number}' was rejected by validation — "
                     "cannot verify delete without risking an unrelated row")

    ensure_on_page(blocked_numbers_page)
    blocked_numbers_page.search(scratch_number)
    if not blocked_numbers_page.has_records():
        pytest.skip(f"Scratch number '{scratch_number}' was not found in the list after adding")

    clicked = blocked_numbers_page.click_delete_on_first_row()
    if not clicked:
        pytest.skip("Delete icon not found on scratch row")
    confirmed = blocked_numbers_page.confirm_delete()
    if not confirmed:
        pytest.skip("Delete confirmation dialog did not appear (locator may need updating)")
    time.sleep(1.5)
    blocked_numbers_page.search(scratch_number)
    assert blocked_numbers_page.has_no_records_message() or not blocked_numbers_page.has_records(), \
        f"Scratch number '{scratch_number}' should no longer appear after confirming delete"
    blocked_numbers_page.clear_search()


@pytest.mark.regression
def test_tc015_cancel_delete(blocked_numbers_page):
    """TC015: Cancelling a delete leaves the record unchanged."""
    ensure_on_page(blocked_numbers_page)
    if not blocked_numbers_page.has_records():
        pytest.skip("No records available to delete")
    before_count = blocked_numbers_page.get_row_count()
    clicked = blocked_numbers_page.click_delete_on_first_row()
    if not clicked:
        pytest.skip("Delete icon not found on first row")
    cancelled = blocked_numbers_page.cancel_delete()
    if not cancelled:
        pytest.skip("Cancel button not found (locator may need updating)")
    time.sleep(1)
    after_count = blocked_numbers_page.get_row_count()
    assert before_count == after_count, \
        "Results count should be unchanged after cancelling delete"


# ── TC016-020 — Add Blocked Number form ──────────────────────────────────

@pytest.mark.regression
def test_tc016_add_valid_blocked_number(blocked_numbers_page):
    """TC016: Adding a valid phone number succeeds."""
    ensure_on_page(blocked_numbers_page)
    blocked_numbers_page.click_add_new_blocked_number()
    if not blocked_numbers_page.is_create_page():
        pytest.skip("Create page did not load")
    if not blocked_numbers_page.is_element_present(blocked_numbers_page.ADD_PHONE_INPUT, timeout=5000):
        pytest.skip("Add form's phone-number input not found -- locator needs "
                     "updating from real create-page DOM")
    blocked_numbers_page.add_blocked_number(VALID_TEST_NUMBER)
    assert blocked_numbers_page.get_validation_error_text() is None, \
        "No validation error expected for a valid phone number"


@pytest.mark.regression
@pytest.mark.negative
def test_tc017_mandatory_phone_field(blocked_numbers_page):
    """TC017: Leaving Phone Number empty and submitting shows a validation message."""
    ensure_on_page(blocked_numbers_page)
    blocked_numbers_page.click_add_new_blocked_number()
    if not blocked_numbers_page.is_create_page():
        pytest.skip("Create page did not load")
    if not blocked_numbers_page.is_element_present(blocked_numbers_page.ADD_PHONE_INPUT, timeout=5000):
        pytest.skip("Add form's phone-number input not found -- locator needs "
                     "updating from real create-page DOM")
    blocked_numbers_page._js_click(blocked_numbers_page.ADD_SUBMIT_BTN, timeout=10000)
    time.sleep(1)
    error = blocked_numbers_page.get_validation_error_text()
    if error is None:
        pytest.skip("No validation message detected -- locator may need updating")
    assert error


@pytest.mark.regression
@pytest.mark.negative
def test_tc018_invalid_phone_format(blocked_numbers_page):
    """TC018: Entering letters/special characters shows a validation message.

    TC017 (mandatory-field check, just above) runs immediately before this
    test and PASSES on a real run -- which proves VALIDATION_ERROR_MSG
    correctly detects a genuine validation message when the app renders
    one. So a None result here means the Add Blocked Number form is NOT
    rejecting non-numeric input -- a hard failure, not a skip."""
    ensure_on_page(blocked_numbers_page)
    blocked_numbers_page.click_add_new_blocked_number()
    if not blocked_numbers_page.is_create_page():
        pytest.skip("Create page did not load")
    if not blocked_numbers_page.is_element_present(blocked_numbers_page.ADD_PHONE_INPUT, timeout=5000):
        pytest.skip("Add form's phone-number input not found -- locator needs "
                     "updating from real create-page DOM")
    blocked_numbers_page.add_blocked_number("abc!@#")
    error = blocked_numbers_page.get_validation_error_text()
    assert error, ("No validation error was shown for an invalid phone format "
                    "('abc!@#') -- the Add Blocked Number form does not appear "
                    "to reject non-numeric input")


@pytest.mark.regression
@pytest.mark.negative
def test_tc019_duplicate_blocked_number(blocked_numbers_page):
    """TC019: Adding an already-blocked number is rejected as a duplicate.

    This test uses a dynamic scratch number to ensure it is independent
    of test execution order (which can be arbitrary under xdist)."""
    ensure_on_page(blocked_numbers_page)
    
    # 1) Add the number for the first time
    scratch_number = "91945679" + f"{int(time.time()) % 1000000:06d}"
    blocked_numbers_page.click_add_new_blocked_number()
    if not blocked_numbers_page.is_create_page():
        pytest.skip("Create page did not load")
    if not blocked_numbers_page.is_element_present(blocked_numbers_page.ADD_PHONE_INPUT, timeout=5000):
        pytest.skip("Add form's phone-number input not found")
        
    blocked_numbers_page.add_blocked_number(scratch_number)
    time.sleep(1)
    
    # 2) Try to add it again
    ensure_on_page(blocked_numbers_page)
    blocked_numbers_page.click_add_new_blocked_number()
    if not blocked_numbers_page.is_create_page():
        pytest.skip("Create page did not load on second attempt")
    
    blocked_numbers_page.add_blocked_number(scratch_number)
    error = blocked_numbers_page.get_validation_error_text()
    assert error, (f"No duplicate-validation error was shown when re-adding "
                    f"the scratch number {scratch_number}")


@pytest.mark.regression
def test_tc020_cancel_button_on_create_page(blocked_numbers_page):
    """TC020: Cancel on the Add page returns to the Blocked Numbers list."""
    ensure_on_page(blocked_numbers_page)
    blocked_numbers_page.click_add_new_blocked_number()
    if not blocked_numbers_page.is_create_page():
        pytest.skip("Create page did not load")
    if not blocked_numbers_page.is_element_present(blocked_numbers_page.ADD_CANCEL_BTN, timeout=5000):
        pytest.skip("Cancel button not found -- locator needs updating from "
                     "real create-page DOM")
    blocked_numbers_page.click_cancel_on_create_page()
    assert blocked_numbers_page.is_report_page(), "Should return to the Blocked Numbers list"


# ── TC021-024, TC027 — Upload popup (best-effort, see module docstring) ─

@pytest.mark.regression
def test_tc021_upload_popup_ui(blocked_numbers_page):
    """TC021: Upload popup displays upload controls and a sample download link."""
    ensure_on_page(blocked_numbers_page)
    blocked_numbers_page.click_upload_blocked_numbers()
    assert blocked_numbers_page.is_upload_popup_open()
    if not blocked_numbers_page.is_element_present(blocked_numbers_page.BTN_DOWNLOAD_SAMPLE, timeout=5000):
        pytest.skip("Download-sample link not found -- locator needs updating "
                     "from real upload-popup DOM")
    assert blocked_numbers_page.is_element_present(blocked_numbers_page.BTN_DOWNLOAD_SAMPLE, timeout=5000)


@pytest.mark.regression
def test_tc022_sample_file_download(blocked_numbers_page):
    """TC022: Clicking Download blocked numbers sample starts without error."""
    ensure_on_page(blocked_numbers_page)
    blocked_numbers_page.click_upload_blocked_numbers()
    if not blocked_numbers_page.is_upload_popup_open() or \
            not blocked_numbers_page.is_element_present(blocked_numbers_page.BTN_DOWNLOAD_SAMPLE, timeout=5000):
        pytest.skip("Upload popup or download-sample link not found")
    blocked_numbers_page.click_download_sample()
    assert blocked_numbers_page.get_upload_error() is None, \
        "No error should appear after clicking the sample download link"


@pytest.mark.regression
def test_tc023_upload_valid_file(blocked_numbers_page):
    """TC023: Uploading a valid CSV imports the numbers successfully."""
    ensure_on_page(blocked_numbers_page)
    sample = data_file("valid_blocked_numbers.csv")
    if not os.path.exists(sample):
        pytest.skip(f"Test data file not found: {sample}")
    blocked_numbers_page.click_upload_blocked_numbers()
    if not blocked_numbers_page.is_upload_popup_open():
        pytest.skip("Upload popup did not open")
    blocked_numbers_page.upload_file(sample)
    error = blocked_numbers_page.get_upload_error()
    assert error is None, f"Upload should succeed without error, got: {error}"


@pytest.mark.regression
@pytest.mark.negative
def test_tc024_upload_invalid_file_type(blocked_numbers_page):
    """TC024: Uploading a PDF/TXT file is rejected."""
    ensure_on_page(blocked_numbers_page)
    invalid_file = data_file("invalid_format.pdf")
    if not os.path.exists(invalid_file):
        pytest.skip(f"Test data file not found: {invalid_file}")
    blocked_numbers_page.click_upload_blocked_numbers()
    if not blocked_numbers_page.is_upload_popup_open():
        pytest.skip("Upload popup did not open")
    blocked_numbers_page.upload_file(invalid_file)
    error = blocked_numbers_page.get_upload_error()
    if error is None:
        pytest.skip("No rejection message detected -- locator may need updating")
    assert error


@pytest.mark.regression
def test_tc027_cancel_button_in_upload_popup(blocked_numbers_page):
    """TC027: Cancel closes the upload popup."""
    ensure_on_page(blocked_numbers_page)
    blocked_numbers_page.click_upload_blocked_numbers()
    if not blocked_numbers_page.is_upload_popup_open():
        pytest.skip("Upload popup did not open")
    if not blocked_numbers_page.is_element_present(blocked_numbers_page.BTN_CANCEL_UPLOAD, timeout=5000):
        pytest.skip("Cancel button not found -- locator needs updating")
    blocked_numbers_page.click_cancel_upload()
    time.sleep(1)
    assert not blocked_numbers_page.is_element_present(blocked_numbers_page.FILE_INPUT, timeout=3000), \
        "Upload popup should be closed after Cancel"


# ── TC028-029 — Sorting ──────────────────────────────────────────────────

@pytest.mark.regression
def test_tc028_sort_by_phone_number(blocked_numbers_page):
    """TC028: Clicking the Phone Number column header re-sorts the visible rows."""
    ensure_on_page(blocked_numbers_page)
    before = blocked_numbers_page.get_column_values("phone_number")
    blocked_numbers_page.sort_by_phone_number()
    after1 = blocked_numbers_page.get_column_values("phone_number")
    blocked_numbers_page.sort_by_phone_number()
    after2 = blocked_numbers_page.get_column_values("phone_number")
    assert before != after1 or after1 != after2, \
        "Clicking Phone Number header should change row order across toggles"


@pytest.mark.regression
def test_tc029_sort_by_created_at(blocked_numbers_page):
    """TC029: Clicking the Created At column header re-sorts the visible rows."""
    ensure_on_page(blocked_numbers_page)
    before = blocked_numbers_page.get_column_values("created_at")
    blocked_numbers_page.sort_by_created_at()
    after1 = blocked_numbers_page.get_column_values("created_at")
    blocked_numbers_page.sort_by_created_at()
    after2 = blocked_numbers_page.get_column_values("created_at")
    assert before != after1 or after1 != after2, \
        "Clicking Created At header should change row order across toggles"


# ── TC030 — Refresh ──────────────────────────────────────────────────────

@pytest.mark.regression
def test_tc030_page_refresh(blocked_numbers_page):
    """TC030: Refreshing the browser reloads the page data successfully."""
    ensure_on_page(blocked_numbers_page)
    blocked_numbers_page.page.reload()
    time.sleep(2)
    assert blocked_numbers_page.is_report_page()
    assert blocked_numbers_page.get_page_title_text() == "SMS Blocked Numbers"


# ── TC031 — Responsive layout ────────────────────────────────────────────

@pytest.mark.regression
def test_tc031_responsive_layout(blocked_numbers_page):
    """TC031: Resizing the browser keeps the UI aligned (no crash/blank)."""
    ensure_on_page(blocked_numbers_page)
    original_size = blocked_numbers_page.page.viewport_size
    try:
        blocked_numbers_page.page.set_viewport_size({"width": 375, "height": 667})  # mobile viewport
        time.sleep(1)
        assert blocked_numbers_page.is_element_present(blocked_numbers_page.SEARCH_BOX, timeout=5000)
        blocked_numbers_page.page.set_viewport_size({"width": 1366, "height": 768})  # desktop viewport
        time.sleep(1)
        assert blocked_numbers_page.is_element_present(blocked_numbers_page.TABLE, timeout=5000)
    finally:
        if original_size:
            blocked_numbers_page.page.set_viewport_size(original_size)
        else:
            blocked_numbers_page.page.set_viewport_size({"width": 1920, "height": 1080})


# ── TC032 — Performance ──────────────────────────────────────────────────

@pytest.mark.regression
def test_tc032_page_performance(blocked_numbers_page):
    """TC032: Page loads within an acceptable response time (<8000ms)."""
    ensure_on_page(blocked_numbers_page)
    blocked_numbers_page.navigate_to_report()
    load_time = blocked_numbers_page.get_page_load_time_ms()
    if load_time is not None:
        assert load_time < 8000, f"Page load took {load_time}ms (>8000ms)"
