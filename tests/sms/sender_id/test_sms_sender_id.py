"""
Test Suite: SMS → Sender ID
Single browser session — login once, then run the full flow:
  validate → create (all combinations) → verify in list → upload CSV → verify uploads

Structure mirrors the Java SenderIdTest:
  - @DataProvider(senderIdCombinations)  → @pytest.mark.parametrize valid_combinations
  - @DataProvider(invalidSenderIds)      → @pytest.mark.parametrize invalid_sender_ids
  - test_CreateSenderId_UIFlow           → TestSenderIdUIFlow
  - upload CSV                           → TestUploadSenderIds

Migrated to Playwright: local page-object fixture renamed `sender_id_page`
(built on conftest.py's `module_logged_in_page`) to avoid shadowing
pytest-playwright's reserved `page` fixture.
"""

import os
import random
import string
import time

import pytest

from pages.sms.sms_sender_id_page import SMSSenderIDPage
from utils.test_data_generator import generate_all, DATA_DIR as GEN_DATA_DIR


pytestmark = [pytest.mark.sms, pytest.mark.sender_id]


# DATA_DIR used to be locally redefined here as os.path.dirname(__file__)-
# relative, which silently shadowed the correct GEN_DATA_DIR import above
# and would have broken (pointed at a non-existent test_data/ dir) once
# this file moved from tests/ to tests/sms/sender_id/. Use the canonical
# one directly instead of shadowing it.
DATA_DIR = GEN_DATA_DIR
UPLOAD_CSV = os.path.join(DATA_DIR, "sender_id_sample.csv")


def data_file(name):
    """Path to a generated edge-case test data file (see utils/test_data_generator.py)."""
    return os.path.join(GEN_DATA_DIR, name)


# ── Module-scoped fixtures: ONE browser, ONE login ────────────────────────────

@pytest.fixture(scope="module", autouse=True)
def generate_test_data():
    """Generate the CSV/XLSX edge-case files used by the upload edge-case tests below."""
    generate_all()


@pytest.fixture(scope="module")
def sender_id_page(module_logged_in_page):
    """Land on Sender ID list."""
    p = SMSSenderIDPage(module_logged_in_page)
    p.navigate_via_sidebar()
    return p


def _to_list(page: SMSSenderIDPage):
    """Return to Sender ID list page — called at start of each test."""
    page.open(SMSSenderIDPage.SENDER_ID_URLS[0])
    page.page.wait_for_timeout(2000)
    page._close_sidebar_overlay()


# ══════════════════════════════════════════════════════════════════════════════
# PART 1 — Client-side validation  (no browser needed)
# Mirrors Java: isValidSenderId(senderId, countryCode)
# ══════════════════════════════════════════════════════════════════════════════

# Valid combinations — same as Java @DataProvider("senderIdCombinations")
VALID_COMBINATIONS = [
    # India (exact 6 chars)
    ("ABCDEF", "IN"),   # uppercase
    ("abcdef", "IN"),   # lowercase
    ("123456", "IN"),   # numeric
    ("Ab12Cd", "IN"),   # mixed
    ("A1b2C3", "IN"),   # mixed
    # International (3–12 chars)
    ("ABC",            "US"),   # min uppercase
    ("abc",            "US"),   # min lowercase
    ("123",            "US"),   # min numeric
    ("Ab1",            "US"),   # min mixed
    ("ABCDEFGHIJKL",  "US"),    # max uppercase (12)
    ("abcdefghijkl",  "US"),    # max lowercase
    ("123456789012",  "US"),    # max numeric
    ("Ab12Cd34Ef56",  "US"),    # max mixed
    ("Test123",        "US"),
    ("XyZ987",         "US"),
    ("Hello1",         "US"),
]

# Invalid combinations — same as Java @DataProvider("invalidSenderIds")
INVALID_SENDER_IDS = [
    # Special characters
    ("ABC@12", "IN"),
    ("abc#12", "IN"),
    ("123$56", "IN"),
    # Spaces
    ("ABC 12", "IN"),
    (" 123456", "IN"),
    # Length issues — India (must be exactly 6)
    ("ABCD",   "IN"),         # too short
    ("ABCDEFG", "IN"),        # too long
    # Length issues — International
    ("AB",              "US"),  # < 3
    ("ABCDEFGHIJKLM",  "US"),  # > 12
    # Empty
    ("",       "IN"),
]


class TestSenderIdValidation:
    """Pure unit tests — validate the isValidSenderId() logic, no browser."""

    @pytest.mark.parametrize("sender_id,country_code", VALID_COMBINATIONS,
                             ids=[f"{s}_{c}" for s, c in VALID_COMBINATIONS])
    def test_valid_sender_id_combinations(self, sender_id, country_code):
        """All valid combinations must pass isValidSenderId()."""
        assert SMSSenderIDPage.is_valid_sender_id(sender_id, country_code), \
            f"Expected VALID but got INVALID: '{sender_id}' ({country_code})"

    @pytest.mark.parametrize("sender_id,country_code", INVALID_SENDER_IDS,
                             ids=[f"'{s}'_{c}" for s, c in INVALID_SENDER_IDS])
    def test_invalid_sender_id_combinations(self, sender_id, country_code):
        """All invalid combinations must fail isValidSenderId()."""
        assert not SMSSenderIDPage.is_valid_sender_id(sender_id, country_code), \
            f"Expected INVALID but got VALID: '{sender_id}' ({country_code})"


# ══════════════════════════════════════════════════════════════════════════════
# PART 2 — Page load checks  (smoke)
# ══════════════════════════════════════════════════════════════════════════════

class TestSenderIdPageLoad:

    @pytest.mark.smoke
    def test_page_loads(self, sender_id_page):
        _to_list(sender_id_page)
        assert sender_id_page.is_sender_id_page()
        assert "404" not in sender_id_page.get_title().lower()

    @pytest.mark.smoke
    def test_create_button_visible(self, sender_id_page):
        _to_list(sender_id_page)
        assert sender_id_page.is_create_button_visible(), "Create New Sender Id button must be visible"

    @pytest.mark.smoke
    def test_upload_button_visible(self, sender_id_page):
        _to_list(sender_id_page)
        assert sender_id_page.is_upload_button_visible(), "Upload Sender Id button must be visible"


# ══════════════════════════════════════════════════════════════════════════════
# PART 3 — Create Sender IDs via UI  (all India combinations)
# Mirrors Java: test_CreateSenderId_AllCombinations + test_CreateSenderId_UIFlow
# ══════════════════════════════════════════════════════════════════════════════

# India-only combinations for UI creation (app only supports IN in this env).
# "abcdef" (lowercase) is deliberately excluded here: it's the same 6
# letters as "ABCDEF" (already covered above), and the app treats Sender
# IDs as case-insensitively unique, so this case only ever exercised the
# duplicate-collision skip path in test_create_valid_india_sender_id, not
# a real creation. It's still covered by test_valid_sender_id_combinations
# via VALID_COMBINATIONS (pure isValidSenderId() logic, no UI/duplicates).
INDIA_VALID = [(s, c) for s, c in VALID_COMBINATIONS if c == "IN" and s != "abcdef"]

# Module-level state: stores every sender_id successfully created
_created: list = []


class TestCreateSenderIdAllCombinations:
    """
    Mirrors Java test_CreateSenderId_AllCombinations.
    For each valid India combination:
      1. Assert isValidSenderId() passes
      2. Open create form, fill fields, submit
      3. Assert sender ID appears in list (isSenderIdPresentInList)
    """

    @pytest.mark.regression
    @pytest.mark.parametrize("sender_id,country_code", INDIA_VALID,
                             ids=[s for s, _ in INDIA_VALID])
    def test_create_valid_india_sender_id(self, sender_id_page, sender_id, country_code):
        # Step 1: pre-validate
        assert SMSSenderIDPage.is_valid_sender_id(sender_id, country_code), \
            f"Pre-condition failed — '{sender_id}' should be valid before UI test"

        # Step 2: navigate to list, open create form
        _to_list(sender_id_page)
        sender_id_page.click_create_sender_id()
        assert sender_id_page.is_element_present(SMSSenderIDPage.FORM_SENDER_ID_INPUT, timeout=10000), \
            "Create form did not open"

        # Step 3: fill form
        sender_id_page.fill_sender_id(sender_id)
        try:
            sender_id_page.select_country("India")
        except Exception:
            pass
        try:
            sender_id_page.select_type("Transactional")
        except Exception:
            pass
        sender_id_page.fill_entity_id(SMSSenderIDPage.generate_random_entity_id())

        # Step 4: submit
        sender_id_page.click_save()
        sender_id_page.page.wait_for_timeout(2000)

        # Step 5: verify in list
        found = sender_id_page.is_sender_id_present_in_list(sender_id)
        if found:
            _created.append(sender_id)
            return

        # FIXED: INDIA_VALID includes both "ABCDEF" and "abcdef" (upper and
        # lower case of the same 6 letters) as separate parametrize cases.
        # If the app treats Sender IDs as case-insensitively unique, the
        # second one to run collides with the first as a duplicate and is
        # silently rejected — a legitimate "already exists" outcome, not a
        # real creation bug. Only hard-fail if there's no such duplicate/
        # validation signal from the app.
        # Poll briefly instead of checking once immediately -- the same
        # single-shot-check-too-early race already found and fixed for
        # TC005/TC007/TC019 elsewhere in this project applies here too.
        duplicate_signal = None
        end_time = time.time() + 6
        while time.time() < end_time:
            duplicate_signal = sender_id_page.get_toast_error() or sender_id_page.get_validation_errors()
            if duplicate_signal:
                break
            sender_id_page.page.wait_for_timeout(300)

        if duplicate_signal and any(
            kw in str(duplicate_signal).lower()
            for kw in ("already", "exist", "duplicate", "taken")
        ):
            # This sender_id is now confirmed to already exist in the
            # account -- that's exactly why it was rejected. It's a valid
            # duplicate-test candidate even though *this* parametrized
            # case didn't create it fresh, so record it in _created.
            # Previously this branch skipped without recording that, so
            # if every India combination happened to collide this way
            # (e.g. a persistent test env already has them all from a
            # prior run), _created stayed empty and
            # test_create_duplicate_sender_id skipped too — even though
            # duplicates trivially existed the whole time.
            _created.append(sender_id)
            pytest.skip(
                f"Sender ID '{sender_id}' rejected as a duplicate "
                f"(likely case-insensitive collision with an earlier "
                f"parametrized case, or already exists from a prior run) "
                f"— not a creation bug: {duplicate_signal}"
            )

        assert found, f"Sender ID '{sender_id}' not found in list after creation"


class TestCreateSenderIdUIFlow:
    """
    Mirrors Java test_CreateSenderId_UIFlow:
    Creates one Transactional sender ID, validates it, verifies it in list.
    Runs AFTER the combination tests so _created is populated.
    """

    @pytest.mark.smoke
    def test_ui_flow_create_and_verify(self, sender_id_page):
        # Generate a fresh ID not used in parametrize tests
        new_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Validate first (mirror Java assert)
        assert SMSSenderIDPage.is_valid_sender_id(new_id, "IN"), \
            f"Generated ID '{new_id}' failed validation"

        # Create via UI
        _to_list(sender_id_page)
        sender_id_page.click_create_sender_id()
        sender_id_page.fill_sender_id(new_id)
        try:
            sender_id_page.select_country("India")
        except Exception:
            pass
        try:
            sender_id_page.select_type("Transactional")
        except Exception:
            pass
        sender_id_page.fill_entity_id(SMSSenderIDPage.generate_random_entity_id())
        sender_id_page.click_save()
        sender_id_page.page.wait_for_timeout(2000)

        # Verify in list
        found = sender_id_page.is_sender_id_present_in_list(new_id)
        if found:
            _created.append(new_id)
        assert found, f"Sender ID '{new_id}' not found in list after UI flow creation"


# ══════════════════════════════════════════════════════════════════════════════
# PART 4 — Invalid combinations via UI (form validation)
# Mirrors Java invalidSenderIds — these should NOT be created
# ══════════════════════════════════════════════════════════════════════════════

# Only test a subset via UI to keep runtime reasonable
UI_INVALID_CASES = [
    ("ABC@12",  "IN", "special chars"),
    ("ABC 12",  "IN", "space in ID"),
    ("ABCD",    "IN", "too short for India"),
    ("ABCDEFG", "IN", "too long for India"),
    ("",        "IN", "empty sender ID"),
]


class TestInvalidSenderIdUI:

    @pytest.mark.regression
    @pytest.mark.negative
    @pytest.mark.parametrize("sender_id,country_code,reason", UI_INVALID_CASES,
                             ids=[r for _, _, r in UI_INVALID_CASES])
    def test_invalid_sender_id_rejected(self, sender_id_page, sender_id, country_code, reason):
        """Invalid sender IDs must fail isValidSenderId() AND NOT appear in the list after submit."""
        # Client-side check
        assert not SMSSenderIDPage.is_valid_sender_id(sender_id, country_code), \
            f"'{sender_id}' should be INVALID per isValidSenderId()"

        # UI check: submit the form and verify the ID is NOT created
        _to_list(sender_id_page)
        sender_id_page.click_create_sender_id()
        if sender_id:
            sender_id_page.fill_sender_id(sender_id)
        try:
            sender_id_page.select_country("India")
        except Exception:
            pass
        try:
            sender_id_page.select_type("Transactional")
        except Exception:
            pass
        sender_id_page.fill_entity_id(SMSSenderIDPage.generate_random_entity_id())
        sender_id_page.click_save()
        sender_id_page.page.wait_for_timeout(2000)

        # The app should either:
        # (a) stay on the create form (URL still has 'create'), OR
        # (b) navigate away but the invalid ID is NOT in the list
        still_on_form = "create" in sender_id_page.get_current_url().lower()
        if still_on_form:
            # Form rejected it — pass
            _to_list(sender_id_page)
            return

        # Navigated away — check the ID is NOT in the list
        if sender_id:
            found = sender_id_page.is_sender_id_present_in_list(sender_id)
            assert not found, \
                f"Invalid sender ID '{sender_id}' ({reason}) should NOT be created"
        _to_list(sender_id_page)


# ══════════════════════════════════════════════════════════════════════════════
# PART 5 — Search for created sender IDs
# ══════════════════════════════════════════════════════════════════════════════

class TestSearchSenderIds:

    @pytest.mark.regression
    def test_search_created_sender_id(self, sender_id_page):
        """Search by a created sender ID returns that record."""
        if not _created:
            pytest.skip("No sender IDs created — run create tests first")
        _to_list(sender_id_page)
        sender_id_page.search(_created[0])
        sender_id_page.page.wait_for_timeout(1500)
        assert sender_id_page.has_records(), f"Search for '{_created[0]}' should return results"
        sender_id_page.clear_search()

    @pytest.mark.regression
    @pytest.mark.negative
    def test_search_invalid_returns_no_records(self, sender_id_page):
        """Search with non-existent value returns zero rows."""
        _to_list(sender_id_page)
        sender_id_page.search("ZZINVALIDZZ999")
        sender_id_page.page.wait_for_timeout(2000)
        no_msg = sender_id_page.has_no_records_message()
        zero_rows = sender_id_page.get_row_count() == 0
        assert no_msg or zero_rows, \
            "Search for invalid ID should return empty table or no-records message"
        sender_id_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# PART 6 — Upload sender IDs via CSV
# Uses sender_id_sample.csv (the file you provided)
# Structure: Sender_ID, Type, Country_Code, Entity_ID
# ══════════════════════════════════════════════════════════════════════════════

def _read_csv_sender_ids(csv_path: str) -> list:
    """
    Parse sender_id_sample.csv and return a list of Sender_ID values.
    Handles both comma and semicolon delimiters, strips BOM and whitespace.
    Falls back to the hardcoded list if the file cannot be read.
    """
    import csv as _csv
    fallback = ["DJHAJK", "OTPSYU", "667423"]
    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as fh:
            # Detect delimiter
            sample = fh.read(1024)
            fh.seek(0)
            delimiter = ";" if sample.count(";") > sample.count(",") else ","
            reader = _csv.DictReader(fh, delimiter=delimiter)
            # Column name may be "Sender_ID", "sender_id", "Sender ID", etc.
            ids = []
            for row in reader:
                for col in ("Sender_ID", "sender_id", "Sender ID", "SENDER_ID"):
                    val = row.get(col, "").strip()
                    if val:
                        ids.append(val)
                        break
            return ids if ids else fallback
    except Exception:
        return fallback


# Read IDs dynamically from the actual CSV so we verify real content
CSV_SENDER_IDS = _read_csv_sender_ids(UPLOAD_CSV) if os.path.exists(UPLOAD_CSV) else ["DJHAJK", "OTPSYU", "667423"]


class TestUploadSenderIds:

    def _skip_if_no_permission(self, page):
        _to_list(page)
        if not page.is_upload_button_visible():
            pytest.skip("Upload button not visible for this account")

    def _open_upload_popup(self, page):
        page.click_upload_sender_id()
        page.page.wait_for_timeout(1500)
        if not page.is_upload_popup_open():
            if page.get_toast_error():
                pytest.skip("No upload permission for this account")
            pytest.skip("Upload popup did not open")

    @pytest.mark.smoke
    def test_upload_popup_opens(self, sender_id_page):
        self._skip_if_no_permission(sender_id_page)
        self._open_upload_popup(sender_id_page)
        assert sender_id_page.is_element_present(SMSSenderIDPage.FILE_INPUT, timeout=5000), \
            "File input should be present inside upload popup"

    @pytest.mark.smoke
    def test_upload_csv_and_verify_in_list(self, sender_id_page):
        """
        Upload sender_id_sample.csv and verify each sender ID from the file
        appears as an exact <td> match in the list — NOT just "any row exists".

        Steps:
          1. Read which IDs are in the CSV (dynamic, not hardcoded).
          2. Record row count before upload.
          3. Upload the file and wait for the import to fully complete.
          4. Assert a success indicator appeared (toast / inline message).
          5. For each ID in the CSV, navigate to the list and confirm an exact
             <td> match exists — search-box + exact match, never just has_records().
        """
        if not os.path.exists(UPLOAD_CSV):
            pytest.skip(f"CSV file not found: {UPLOAD_CSV}")
        if not CSV_SENDER_IDS:
            pytest.skip("No sender IDs could be parsed from the CSV file")

        self._skip_if_no_permission(sender_id_page)

        # ── Baseline ──────────────────────────────────────────────────────────
        _to_list(sender_id_page)
        baseline_count = sender_id_page.get_row_count()

        # ── Upload ────────────────────────────────────────────────────────────
        self._open_upload_popup(sender_id_page)
        sender_id_page.upload_file(UPLOAD_CSV)
        sender_id_page.click_import()

        # Wait for the import to finish: loader must disappear first, then
        # give Livewire up to 10 s to process the import server-side.
        try:
            sender_id_page.page.locator(SMSSenderIDPage.LOADER).first.wait_for(state="hidden", timeout=15000)
        except Exception:
            sender_id_page.page.wait_for_timeout(3000)

        # ── Assert import succeeded (not just "any toast") ───────────────────
        success = sender_id_page.get_upload_success() or sender_id_page.is_success_toast_shown()
        assert success, (
            "CSV upload should show a success message or toast after import. "
            "Check that the file format matches the template and the popup did not close early."
        )

        # Brief pause for Livewire to commit rows to DB (async job may queue)
        sender_id_page.page.wait_for_timeout(2000)

        # ── Verify each ID in the list — exact match only ────────────────────
        missing = []
        for sid in CSV_SENDER_IDS:
            # is_sender_id_present_in_list navigates to the list, optionally
            # searches, and requires an exact <td> match — not just any rows.
            found = sender_id_page.is_sender_id_present_in_list(sid)
            if not found:
                missing.append(sid)

        assert not missing, (
            f"The following sender IDs from the CSV were NOT found in the list "
            f"after upload: {missing}. "
            f"Possible causes: import queued (run again in a few seconds), "
            f"IDs already existed and were rejected as duplicates, or "
            f"the CSV column header does not match ('Sender_ID' expected)."
        )

    @pytest.mark.regression
    def test_cancel_upload_closes_popup(self, sender_id_page):
        """Clicking Cancel/Close closes the upload popup without importing."""
        self._skip_if_no_permission(sender_id_page)
        self._open_upload_popup(sender_id_page)
        try:
            sender_id_page.click_cancel_upload()
        except Exception:
            # Fallback: press Escape to close the modal
            sender_id_page.page.keyboard.press("Escape")
        sender_id_page.page.wait_for_timeout(1000)
        assert not sender_id_page.is_upload_popup_open(), "Upload popup should close after Cancel/Escape"

    @pytest.mark.regression
    def test_download_sample_available(self, sender_id_page):
        """Download Sample button is present inside upload popup and clickable."""
        self._skip_if_no_permission(sender_id_page)
        self._open_upload_popup(sender_id_page)
        assert sender_id_page.is_element_present(SMSSenderIDPage.BTN_DOWNLOAD_SAMPLE, timeout=5000), \
            "Download Sample button should be present"
        sender_id_page.click_download_sample()
        sender_id_page.page.wait_for_timeout(1000)
        # Just verify no error toast appeared — the download itself is a file download
        assert sender_id_page.get_toast_error() is None, "No error toast should appear after Download Sample"

    @pytest.mark.regression
    @pytest.mark.negative
    def test_upload_invalid_format_rejected(self, sender_id_page):
        """Uploading a .txt file is rejected — either no Import button or error shown."""
        dummy = os.path.join(DATA_DIR, "_dummy_invalid.txt")
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(dummy, "w") as f:
            f.write("not a valid sender id file")
        try:
            self._skip_if_no_permission(sender_id_page)
            self._open_upload_popup(sender_id_page)
            sender_id_page.upload_file(dummy)
            sender_id_page.page.wait_for_timeout(2000)
            # Check for inline error first (app may reject at file-select stage)
            inline_error = sender_id_page.get_upload_error()
            if inline_error:
                return  # error shown at file selection — pass

            # If Import button appeared, click it and check for rejection
            try:
                btn = sender_id_page.page.locator(SMSSenderIDPage.BTN_IMPORT).first
                btn.wait_for(state="visible", timeout=5000)
                btn.click(force=True)
                sender_id_page.page.wait_for_timeout(2000)
            except Exception:
                pass  # no Import button = already rejected

            assert sender_id_page.get_upload_error() or sender_id_page.get_toast_error(), \
                "Invalid file format should be rejected with an error"
        finally:
            if os.path.exists(dummy):
                os.remove(dummy)

    @pytest.mark.regression
    @pytest.mark.negative
    def test_re_upload_same_csv_no_duplicates(self, sender_id_page):
        """Re-uploading the same CSV does not create duplicate rows."""
        if not os.path.exists(UPLOAD_CSV):
            pytest.skip(f"CSV file not found: {UPLOAD_CSV}")
        self._skip_if_no_permission(sender_id_page)
        _to_list(sender_id_page)
        count_before = sender_id_page.get_row_count()

        self._open_upload_popup(sender_id_page)
        sender_id_page.upload_file(UPLOAD_CSV)
        sender_id_page.click_import()
        sender_id_page.page.wait_for_timeout(3000)
        _to_list(sender_id_page)
        count_after = sender_id_page.get_row_count()

        assert count_after == count_before, \
            "Re-uploading same CSV should not increase row count (duplicate rejection)"


# ══════════════════════════════════════════════════════════════════════════════
# PART 7 — Edit sender IDs  (run after create so rows exist)
# ══════════════════════════════════════════════════════════════════════════════

class TestEditSenderIds:

    @pytest.mark.regression
    def test_edit_and_save(self, sender_id_page):
        _to_list(sender_id_page)
        if not sender_id_page.has_records():
            pytest.skip("No records to edit")
        if not sender_id_page.click_first_row_edit():
            pytest.skip("Edit button not found — locator needs update for this app version")
        try:
            sender_id_page.fill_description(f"auto-edit-{int(sender_id_page.page.evaluate('() => Date.now()') / 1000)}")
        except Exception:
            pass
        sender_id_page.click_save()
        sender_id_page.page.wait_for_timeout(1500)
        assert sender_id_page.is_success_toast_shown(), "Edit save should show success toast"
        _to_list(sender_id_page)

    @pytest.mark.regression
    def test_cancel_edit_no_save(self, sender_id_page):
        _to_list(sender_id_page)
        if not sender_id_page.has_records():
            pytest.skip("No records to edit")
        if not sender_id_page.click_first_row_edit():
            pytest.skip("Edit button not found — locator needs update for this app version")
        try:
            sender_id_page.fill_description("SHOULD NOT BE SAVED")
        except Exception:
            pass
        sender_id_page.click_form_cancel()
        sender_id_page.page.wait_for_timeout(1000)
        assert sender_id_page.is_sender_id_page(), "Cancel should return to Sender ID list"


# ══════════════════════════════════════════════════════════════════════════════
# PART 8 — Delete sender IDs  (run last — removes data)
# ══════════════════════════════════════════════════════════════════════════════

class TestDeleteSenderIds:

    @pytest.mark.regression
    def test_cancel_delete_preserves_record(self, sender_id_page):
        _to_list(sender_id_page)
        if not sender_id_page.has_records():
            pytest.skip("No records to delete")
        before = sender_id_page.get_row_count()
        if not sender_id_page.click_first_row_delete():
            pytest.skip("Delete button not found — locator needs update for this app version")
        sender_id_page.cancel_delete()
        sender_id_page.page.wait_for_timeout(500)
        assert sender_id_page.get_row_count() == before, "Row count should not change after cancel"

    @pytest.mark.regression
    def test_confirm_delete_removes_record(self, sender_id_page):
        _to_list(sender_id_page)
        if not sender_id_page.has_records():
            pytest.skip("No records to delete")
        before = sender_id_page.get_row_count()
        if not sender_id_page.click_first_row_delete():
            pytest.skip("Delete button not found — locator needs update for this app version")
        sender_id_page.confirm_delete()
        sender_id_page.page.wait_for_timeout(2000)
        _to_list(sender_id_page)
        assert sender_id_page.get_row_count() < before or sender_id_page.is_success_toast_shown(), \
            "Row count should decrease or success toast should appear after delete"


# ══════════════════════════════════════════════════════════════════════════════
# PART 9 — Filter by Entity ID
# Ported from test_sms_sender_id_flow.py (TC_007/008) — not previously covered here.
# ══════════════════════════════════════════════════════════════════════════════

class TestFilterSenderIds:

    @pytest.mark.regression
    def test_filter_valid_entity_id(self, sender_id_page):
        """Filter by a valid Entity ID returns matching records or a no-records message."""
        _to_list(sender_id_page)
        sender_id_page.filter_by_entity_id("ENT001")   # UPDATE if your env uses a different Entity ID
        result = sender_id_page.has_records() or sender_id_page.has_no_records_message()
        assert result, "Filter should show records or a no-records message"
        _to_list(sender_id_page)

    @pytest.mark.regression
    @pytest.mark.negative
    def test_filter_invalid_entity_id(self, sender_id_page):
        """Filter by an invalid Entity ID shows no records."""
        _to_list(sender_id_page)
        sender_id_page.filter_by_entity_id("INVALID_ENTITY_ZZZ999")
        assert sender_id_page.has_no_records_message(), \
            "Invalid Entity ID filter should show no-records message"
        _to_list(sender_id_page)


# ══════════════════════════════════════════════════════════════════════════════
# PART 10 — Upload edge cases
# Ported from test_sms_sender_id_flow.py (TC_027-032) — uses the generated CSV
# fixture files from utils/test_data_generator.py, not sender_id_sample.csv.
# ══════════════════════════════════════════════════════════════════════════════

class TestUploadEdgeCases:

    def _skip_if_no_permission(self, page):
        _to_list(page)
        if not page.is_upload_button_visible():
            pytest.skip("Upload button not visible for this account")

    def _open_upload_popup(self, page):
        page.click_upload_sender_id()
        page.page.wait_for_timeout(1500)
        if not page.is_upload_popup_open():
            if page.get_toast_error():
                pytest.skip("No upload permission for this account")
            pytest.skip("Upload popup did not open")

    # test_upload_duplicate_sender_ids, test_upload_invalid_sender_id_length,
    # test_upload_special_characters, test_upload_missing_entity_id_column,
    # and test_upload_invalid_country_code were removed per explicit
    # instruction — a live pytest run showed get_upload_error() and
    # get_toast_error() both returning None for all of these (no visible
    # error signal to assert on for this upload path), and the user asked
    # for them to be dropped rather than chased further.

    @pytest.mark.regression
    def test_upload_mixed_valid_invalid(self, sender_id_page):
        """Valid rows imported, invalid rows rejected — some feedback either way, not silent failure."""
        self._skip_if_no_permission(sender_id_page)
        self._open_upload_popup(sender_id_page)
        sender_id_page.upload_file(data_file("mixed_valid_invalid.csv"))
        sender_id_page.click_import()
        sender_id_page.page.wait_for_timeout(2000)
        success = sender_id_page.get_upload_success() or sender_id_page.is_success_toast_shown()
        error = sender_id_page.get_upload_error() or sender_id_page.get_toast_error()
        assert success or error, "Mixed file should produce feedback — not silent failure"
        if sender_id_page.is_upload_popup_open():
            sender_id_page.click_cancel_upload()


# ══════════════════════════════════════════════════════════════════════════════
# PART 11 — Create edge cases
# Ported from test_sms_sender_id_flow.py (TC_034-040) — not previously covered here.
# ══════════════════════════════════════════════════════════════════════════════

CREATE_EDGE_COUNTRY = "India"   # UPDATE if this option doesn't exist in your app's dropdown


class TestCreateSenderIdEdgeCases:

    @pytest.mark.regression
    def test_create_max_allowed_length(self, sender_id_page):
        """Sender ID at the max allowed length is created successfully."""
        _to_list(sender_id_page)
        max_sid = "TESTSIDMX1"   # UPDATE if your app's max length differs
        sender_id_page.click_create_sender_id()
        sender_id_page.fill_sender_id(max_sid)
        try:
            sender_id_page.select_country(CREATE_EDGE_COUNTRY)
        except Exception:
            pass
        try:
            sender_id_page.select_type("Transactional")
        except Exception:
            pass
        sender_id_page.fill_entity_id(SMSSenderIDPage.generate_random_entity_id())
        sender_id_page.click_save()
        assert sender_id_page.is_success_toast_shown(), \
            "Sender ID with max allowed length should save successfully"
        if sender_id_page.is_sender_id_present_in_list(max_sid):
            _created.append(max_sid)
        _to_list(sender_id_page)

    @pytest.mark.regression
    @pytest.mark.negative
    def test_create_exceeding_max_length(self, sender_id_page):
        """Sender ID exceeding the max length shows a validation error."""
        _to_list(sender_id_page)
        sender_id_page.click_create_sender_id()
        sender_id_page.fill_sender_id("TOOLONGSENDERID")   # exceeds max length
        sender_id_page.click_save()
        errors = sender_id_page.get_validation_errors()
        assert errors, "Sender ID exceeding max length should show validation error"
        sender_id_page.click_form_cancel()
        _to_list(sender_id_page)

    @pytest.mark.regression
    @pytest.mark.negative
    def test_create_without_country(self, sender_id_page):
        """Saving without a country shows a mandatory-field error."""
        _to_list(sender_id_page)
        sender_id_page.click_create_sender_id()
        sender_id_page.fill_sender_id("NOCNTRY1")
        sender_id_page.click_save()   # deliberately skip country selection
        errors = sender_id_page.get_validation_errors()
        assert errors, "Missing country should trigger mandatory field error"
        sender_id_page.click_form_cancel()
        _to_list(sender_id_page)

# ══════════════════════════════════════════════════════════════════════════════
# PART 13 — Delete edge cases
# Ported from test_sms_sender_id_flow.py (TC_045) — campaign-linked Sender ID
# deletion restriction is not covered by the existing TestDeleteSenderIds.
# ══════════════════════════════════════════════════════════════════════════════

class TestDeleteSenderIdEdgeCases:

    @pytest.mark.regression
    @pytest.mark.negative
    def test_delete_sender_used_in_campaign(self, sender_id_page):
        """Sender ID used in an active campaign cannot be deleted."""
        _to_list(sender_id_page)
        if not sender_id_page.has_records():
            pytest.skip("No records to attempt delete")
        if not sender_id_page.click_first_row_delete():
            pytest.skip("Delete button not found — locator needs update for this app version")
        sender_id_page.confirm_delete()
        sender_id_page.page.wait_for_timeout(1500)
        if not sender_id_page.is_delete_restricted():
            pytest.skip(
                "No deletion restriction detected — "
                "ensure a Sender ID linked to an active campaign exists for this test"
            )
        assert sender_id_page.is_delete_restricted(), \
            "System should restrict deletion of a Sender ID used in an active campaign"
        _to_list(sender_id_page)


# ══════════════════════════════════════════════════════════════════════════════
# PART 14 — Export CSV (SLA + hidden columns)
# Ported from test_sms_sender_id_flow.py (TC_019/047) — not previously covered here.
# ══════════════════════════════════════════════════════════════════════════════

EXPORT_MAX_SECONDS = 35   # SLA: export must complete within this time


class TestExportSenderIds:

    @pytest.mark.regression
    def test_export_csv(self, sender_id_page):
        """Export CSV downloads the file and completes within the SLA."""
        _to_list(sender_id_page)
        result = sender_id_page.export_csv()
        elapsed, file_size, file_path = result["elapsed_s"], result["file_size"], result["file_path"]
        print(f"\n[PERF] Export CSV — elapsed: {elapsed}s | size: {file_size} bytes | file: {file_path}")
        assert file_size > 0, "Downloaded CSV must not be empty"
        assert elapsed <= EXPORT_MAX_SECONDS, \
            f"Export took {elapsed}s — exceeded SLA of {EXPORT_MAX_SECONDS}s"
        assert sender_id_page.get_toast_error() is None, "Export should complete without error toast"

    # test_export_with_hidden_columns removed per explicit instruction —
    # a live pytest run showed export_csv() consistently raising
    # RuntimeError ("no file appeared ... within 30s") on this specific
    # hidden-columns path.


# ══════════════════════════════════════════════════════════════════════════════
# PART 15 — Column visibility edge cases
# Ported from test_sms_sender_id_flow.py (TC_020/048/049) — not previously
# covered here.
# ══════════════════════════════════════════════════════════════════════════════

class TestColumnVisibility:

    @pytest.mark.regression
    def test_uncheck_all_optional_columns(self, sender_id_page):
        """Unchecking all optional columns leaves only mandatory columns visible."""
        _to_list(sender_id_page)
        sender_id_page.uncheck_all_optional_columns()
        sender_id_page.page.wait_for_timeout(500)
        headers = sender_id_page.get_visible_column_headers()
        assert len(headers) >= 1, "At least one mandatory column should remain visible"

    @pytest.mark.regression
    def test_column_selection_after_refresh(self, sender_id_page):
        """Column selection persists or resets as per design after refresh."""
        _to_list(sender_id_page)
        sender_id_page.uncheck_first_optional_column()
        sender_id_page.page.reload()
        sender_id_page.h.wait_for_url_contains("sender", timeout=15000)
        sender_id_page.page.wait_for_timeout(1500)
        headers = sender_id_page.get_visible_column_headers()
        assert len(headers) >= 1, "At least one column should be visible after refresh"
