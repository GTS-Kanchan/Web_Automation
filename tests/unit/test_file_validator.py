"""
tests/unit/test_file_validator.py — fast, browser-free unit tests for
utils/file_validator.py.

These tests never open a browser or touch the live Download Center — they
build small temporary .csv/.xlsx files with pytest's built-in `tmp_path`
fixture and call validate_file_headers()/read_file_headers() directly, so
header-validation logic can be verified in seconds and independently of
the SMS Download Center UI test (tests/sms/reports/test_sms_download_center_flow.py).

Run just this file with:
    pytest tests/unit/test_file_validator.py -v
"""
import csv
import zipfile

import openpyxl
import pytest

from utils.file_validator import (
    EmptyFileError,
    FileNotDownloadedError,
    HeaderValidationError,
    UnsupportedFileTypeError,
    read_file_headers,
    validate_file_headers,
)

EXPECTED = ["Phone Number", "Message Id", "Correlation Id"]


# ─────────────────────────────────────────────────────────────────────────
# Helpers to build temp fixture files
# ─────────────────────────────────────────────────────────────────────────

def _write_csv(path, header_row, data_row=None):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header_row)
        if data_row is not None:
            writer.writerow(data_row)
    return str(path)


def _write_csv_bytes(path, raw_bytes):
    with open(path, "wb") as f:
        f.write(raw_bytes)
    return str(path)


def _write_zip(path, inner_filename, inner_bytes, extra_entries=None):
    """Build a .zip containing one report file (inner_filename/inner_bytes)
    plus any extra_entries {name: bytes} — mirrors the real Download Center
    export, which zips the report and may include other files alongside it."""
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(inner_filename, inner_bytes)
        for name, data in (extra_entries or {}).items():
            zf.writestr(name, data)
    return str(path)


def _csv_bytes(header_row, data_row=None):
    import io
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(header_row)
    if data_row is not None:
        writer.writerow(data_row)
    return buf.getvalue().encode("utf-8")


def _write_xlsx(path, header_row, data_row=None):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(header_row)
    if data_row is not None:
        ws.append(data_row)
    wb.save(str(path))
    return str(path)


# ─────────────────────────────────────────────────────────────────────────
# Positive cases
# ─────────────────────────────────────────────────────────────────────────

def test_valid_sms_csv_passes(tmp_path):
    file_path = _write_csv(tmp_path / "valid_sms.csv", EXPECTED, ["+1234567890", "MSG1", "CORR1"])
    actual = validate_file_headers(file_path, EXPECTED)
    assert actual == EXPECTED


def test_valid_sms_xlsx_passes(tmp_path):
    file_path = _write_xlsx(tmp_path / "valid_sms.xlsx", EXPECTED, ["+1234567890", "MSG1", "CORR1"])
    actual = validate_file_headers(file_path, EXPECTED)
    assert actual == EXPECTED


def test_zipped_csv_passes(tmp_path):
    """The real Download Center export is a .zip wrapping the report file
    (confirmed from a live run: report.zip containing an .xlsx) — this
    covers the .zip-containing-.csv case."""
    inner_bytes = _csv_bytes(EXPECTED, ["+1234567890", "MSG1", "CORR1"])
    zip_path = _write_zip(tmp_path / "report.zip", "sms_report.csv", inner_bytes)
    actual = validate_file_headers(zip_path, EXPECTED)
    assert actual == EXPECTED


def test_zipped_xlsx_passes(tmp_path):
    """Covers the exact real-world shape that surfaced this bug: a .zip
    wrapping an .xlsx report."""
    xlsx_path = _write_xlsx(tmp_path / "inner.xlsx", EXPECTED, ["+1234567890", "MSG1", "CORR1"])
    inner_bytes = open(xlsx_path, "rb").read()
    zip_path = _write_zip(tmp_path / "report.zip", "sms_report.xlsx", inner_bytes)
    actual = validate_file_headers(zip_path, EXPECTED)
    assert actual == EXPECTED


def test_zipped_report_with_header_mismatch_still_fails(tmp_path):
    """Unzipping must not bypass validation — a bad header inside the zip
    still fails exactly like a bad header in a bare file."""
    bad_headers = ["Phone Number", "Message Id", "Campaign"]  # not "Correlation Id"
    inner_bytes = _csv_bytes(bad_headers)
    zip_path = _write_zip(tmp_path / "report.zip", "sms_report.csv", inner_bytes)

    with pytest.raises(HeaderValidationError) as exc_info:
        validate_file_headers(zip_path, EXPECTED)
    assert (3, "Correlation Id", "Campaign") in exc_info.value.mismatches


def test_zip_with_no_report_file_fails(tmp_path):
    """A .zip that doesn't contain any .csv/.xlsx/.xls entry (e.g. only a
    manifest/readme) is a distinct, clearly-reported failure."""
    zip_path = tmp_path / "empty_report.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("readme.txt", b"not a report")

    with pytest.raises(UnsupportedFileTypeError) as exc_info:
        validate_file_headers(str(zip_path), EXPECTED)
    assert ".zip" in str(exc_info.value) or "zip" in str(exc_info.value).lower()


def test_bom_prefixed_csv_header_still_passes(tmp_path):
    """A leading UTF-8 BOM is a parsing artifact (common in Excel-exported
    CSVs), not a real header difference — must not be treated as a mismatch."""
    raw = ("﻿" + ",".join(EXPECTED) + "\n+1234567890,MSG1,CORR1\n").encode("utf-8")
    file_path = _write_csv_bytes(tmp_path / "bom.csv", raw)
    actual = validate_file_headers(file_path, EXPECTED)
    assert actual == EXPECTED


# ─────────────────────────────────────────────────────────────────────────
# Negative cases — header content
# ─────────────────────────────────────────────────────────────────────────

def test_missing_header_fails(tmp_path):
    actual_headers = ["Phone Number", "Message Id"]  # Correlation Id dropped
    file_path = _write_csv(tmp_path / "missing_header.csv", actual_headers)

    with pytest.raises(HeaderValidationError) as exc_info:
        validate_file_headers(file_path, EXPECTED)

    err = exc_info.value
    assert err.missing == ["Correlation Id"]
    assert err.unexpected == []
    assert "Missing headers:" in str(err)
    assert "Correlation Id" in str(err)


def test_extra_header_fails(tmp_path):
    actual_headers = EXPECTED + ["Extra Column"]
    file_path = _write_csv(tmp_path / "extra_header.csv", actual_headers)

    with pytest.raises(HeaderValidationError) as exc_info:
        validate_file_headers(file_path, EXPECTED)

    err = exc_info.value
    assert err.unexpected == ["Extra Column"]
    assert err.missing == []
    assert "Unexpected headers:" in str(err)


def test_wrong_header_name_fails(tmp_path):
    actual_headers = ["Phone Number", "Message Id", "Campaign"]  # not "Correlation Id"
    file_path = _write_csv(tmp_path / "wrong_header.csv", actual_headers)

    with pytest.raises(HeaderValidationError) as exc_info:
        validate_file_headers(file_path, EXPECTED)

    err = exc_info.value
    assert (3, "Correlation Id", "Campaign") in err.mismatches
    assert "Position 3" in str(err)
    assert "Expected: Correlation Id" in str(err)
    assert "Actual: Campaign" in str(err)


def test_wrong_order_fails_by_default(tmp_path):
    actual_headers = ["Phone Number", "Correlation Id", "Message Id"]  # swapped
    file_path = _write_csv(tmp_path / "wrong_order.csv", actual_headers)

    with pytest.raises(HeaderValidationError) as exc_info:
        validate_file_headers(file_path, EXPECTED)

    err = exc_info.value
    # Same set of headers present -> order-sensitive comparison is the only
    # thing that can catch this; missing/unexpected must be empty.
    assert err.missing == []
    assert err.unexpected == []
    assert len(err.mismatches) > 0


def test_wrong_order_passes_when_order_insensitive(tmp_path):
    """The order_sensitive flag exists so order-independent comparison can
    be introduced later without redesigning the validator."""
    actual_headers = ["Phone Number", "Correlation Id", "Message Id"]
    file_path = _write_csv(tmp_path / "wrong_order.csv", actual_headers)

    actual = validate_file_headers(file_path, EXPECTED, order_sensitive=False)
    assert sorted(actual) == sorted(EXPECTED)


def test_wrong_header_count_fails(tmp_path):
    actual_headers = ["Phone Number", "Message Id"]  # 2 instead of 3
    file_path = _write_csv(tmp_path / "wrong_count.csv", actual_headers)

    with pytest.raises(HeaderValidationError) as exc_info:
        validate_file_headers(file_path, EXPECTED)

    assert "Expected header count: 3" in str(exc_info.value)
    assert "Actual header count: 2" in str(exc_info.value)


def test_exact_match_is_case_and_space_sensitive(tmp_path):
    """Capitalization/spacing differences must FAIL — never silently
    normalized (e.g. 'Phone number', 'PhoneNumber', trailing/double spaces)."""
    cases = [
        ["Phone number", "Message Id", "Correlation Id"],   # wrong case
        ["PhoneNumber", "Message Id", "Correlation Id"],    # missing space
        ["Phone Number ", "Message Id", "Correlation Id"],  # trailing space
        ["Phone  Number", "Message Id", "Correlation Id"],  # double space
    ]
    for i, headers in enumerate(cases):
        file_path = _write_csv(tmp_path / f"case_{i}.csv", headers)
        with pytest.raises(HeaderValidationError):
            validate_file_headers(file_path, EXPECTED)


# ─────────────────────────────────────────────────────────────────────────
# Negative cases — file-level problems
# ─────────────────────────────────────────────────────────────────────────

def test_empty_file_fails(tmp_path):
    file_path = tmp_path / "empty.csv"
    file_path.write_text("", encoding="utf-8")

    with pytest.raises(EmptyFileError):
        validate_file_headers(str(file_path), EXPECTED)


def test_unsupported_extension_fails(tmp_path):
    file_path = tmp_path / "report.txt"
    file_path.write_text("Phone Number,Message Id,Correlation Id\n", encoding="utf-8")

    with pytest.raises(UnsupportedFileTypeError) as exc_info:
        validate_file_headers(str(file_path), EXPECTED)

    assert ".txt" in str(exc_info.value)
    assert ".csv" in str(exc_info.value)
    assert ".xlsx" in str(exc_info.value)


def test_file_not_downloaded_fails(tmp_path):
    missing_path = str(tmp_path / "does_not_exist.csv")

    with pytest.raises(FileNotDownloadedError) as exc_info:
        validate_file_headers(missing_path, EXPECTED)

    assert "not downloaded" in str(exc_info.value).lower()


def test_read_file_headers_does_not_read_row_data(tmp_path):
    """The validator's contract is headers-only — confirm read_file_headers()
    never returns more than the single header row even when data rows exist."""
    file_path = _write_csv(
        tmp_path / "with_data.csv", EXPECTED, ["+1234567890", "MSG1", "CORR1"]
    )
    headers = read_file_headers(file_path)
    assert headers == EXPECTED
