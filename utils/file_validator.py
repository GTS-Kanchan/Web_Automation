"""
utils/file_validator.py — generic, browser-independent downloaded-file
header validator.

Used by Download Center tests (SMS today; RCS/WhatsApp/Email can reuse the
exact same validate_file_headers() call with their own expected-header list
once those channels are in scope — see constants/sms_download_headers.py
for the SMS-specific configuration that plugs into this generic function).

This module intentionally has zero dependency on Playwright or pytest — it
only needs a file path and a list of expected header strings — so it can be
exercised in plain, fast unit tests without starting a browser (see
tests/unit/test_file_validator.py).

Scope (phase 1): headers only.
    FILE -> HEADERS -> exact-match comparison -> PASS/FAIL
Row data, values, data types, record counts, and business logic are
deliberately NOT read or validated here.
"""
import csv
import os
import tempfile
import zipfile

try:
    import openpyxl
except ImportError:  # pragma: no cover - exercised only when openpyxl is absent
    openpyxl = None

try:
    import xlrd
except ImportError:  # pragma: no cover - exercised only when xlrd is absent
    xlrd = None

# Extensions this validator knows how to read directly. Keep this in sync
# with the read_file_headers() dispatch below — it is the single source of
# truth for "supported download formats" referenced in error messages.
# .zip is handled separately (see _read_zip_headers): the SMS Download
# Center's real export is a .zip containing one of these — confirmed from
# an actual failing run where a live download produced report.zip wrapping
# an .xlsx report, not a bare .xlsx.
SUPPORTED_EXTENSIONS = (".csv", ".xlsx", ".xls", ".zip")
SUPPORTED_INNER_EXTENSIONS = (".csv", ".xlsx", ".xls")


# ─────────────────────────────────────────────────────────────────────────
# Exceptions
#
# All subclass AssertionError so a raise from inside a test is reported by
# pytest as a normal (readable) assertion failure with no extra wiring,
# while still being distinct, catchable types so callers can differentiate
# "file not downloaded" from "header mismatch" (see requirement: don't
# report a missing download as a header-validation failure).
# ─────────────────────────────────────────────────────────────────────────

class FileValidationError(AssertionError):
    """Base class for every error this module raises."""


class FileNotDownloadedError(FileValidationError):
    """The expected downloaded file does not exist on disk."""


class UnsupportedFileTypeError(FileValidationError):
    """The file's extension isn't one this validator can read."""


class EmptyFileError(FileValidationError):
    """The file exists but has no header row (empty file, or a header row
    that is entirely blank)."""


class HeaderValidationError(FileValidationError):
    """The file's headers were read successfully but don't exactly match
    (name, spelling, capitalization, spacing, count, or order) the expected
    list.

    Carries the comparison details as attributes (missing / unexpected /
    mismatches / expected / actual) so callers — the live UI test or a unit
    test — can assert on specifics without re-parsing the message string.
    """

    def __init__(self, message, *, missing=None, unexpected=None, mismatches=None,
                 expected=None, actual=None):
        super().__init__(message)
        self.missing = missing or []
        self.unexpected = unexpected or []
        self.mismatches = mismatches or []  # list of (position_1_based, expected, actual)
        self.expected = expected or []
        self.actual = actual or []


# ─────────────────────────────────────────────────────────────────────────
# Header extraction
# ─────────────────────────────────────────────────────────────────────────

def _strip_bom(value):
    """Strip a UTF-8 BOM character if it's stuck to the first header cell.
    This is a parser/encoding artifact (Excel-exported CSVs commonly write
    a BOM), NOT a real header difference, so it is the one thing this
    module normalizes — everything else (case, spacing, spelling) is left
    exactly as read, on purpose, so those remain part of the comparison."""
    if isinstance(value, str) and value.startswith("﻿"):
        return value[1:]
    return value


def _read_csv_headers(file_path):
    # utf-8-sig transparently drops a leading BOM at the codec level too;
    # _strip_bom() below is a belt-and-suspenders second pass in case a
    # BOM character survived (e.g. it was embedded mid-decode by an
    # unusual export).
    with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header_row = next(reader, None)
    if not header_row:
        return []
    return [_strip_bom(cell) for cell in header_row]


def _read_xlsx_headers(file_path):
    if openpyxl is None:
        raise UnsupportedFileTypeError(
            "Cannot read .xlsx file — the 'openpyxl' package is not installed.\n"
            f"File: {file_path}\n"
            "Install it with: pip install openpyxl"
        )
    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    try:
        ws = wb.active
        header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), None)
    finally:
        wb.close()
    if header_row is None:
        return []
    return [_strip_bom(cell) if cell is not None else "" for cell in header_row]


def _read_xls_headers(file_path):
    if xlrd is None:
        raise UnsupportedFileTypeError(
            "Cannot read legacy .xls file — the 'xlrd' package is not installed.\n"
            f"File: {file_path}\n"
            "Install it with: pip install xlrd"
        )
    wb = xlrd.open_workbook(file_path)
    sheet = wb.sheet_by_index(0)
    if sheet.nrows == 0:
        return []
    header_row = sheet.row_values(0)
    return [_strip_bom(cell) if cell is not None else "" for cell in header_row]


def _read_zip_headers(file_path):
    """The live SMS Download Center export is a .zip that contains exactly
    one .csv/.xlsx/.xls report file — extract that one entry to a temp
    file and read its headers the normal way. Never inspects any other
    entry's contents (e.g. a manifest/readme also in the zip)."""
    try:
        with zipfile.ZipFile(file_path) as zf:
            candidates = [
                name for name in zf.namelist()
                if not name.endswith("/")
                and os.path.splitext(name)[1].lower() in SUPPORTED_INNER_EXTENSIONS
                and not os.path.basename(name).startswith((".", "~$"))
            ]
            if not candidates:
                raise UnsupportedFileTypeError(
                    "Downloaded .zip file does not contain a .csv/.xlsx/.xls "
                    "report file.\n"
                    f"File: {file_path}\n"
                    f"Zip contents: {zf.namelist()}"
                )
            inner_name = candidates[0]
            inner_ext = os.path.splitext(inner_name)[1].lower()
            data = zf.read(inner_name)
    except zipfile.BadZipFile:
        raise UnsupportedFileTypeError(
            f"Downloaded file has a .zip extension but is not a valid zip archive.\n"
            f"File: {file_path}"
        )

    fd, tmp_path = tempfile.mkstemp(suffix=inner_ext)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        return read_file_headers(tmp_path)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def read_file_headers(file_path):
    """Read ONLY the first (header) row of file_path and return it as a
    list of strings. Dispatches on file extension:
        .csv           -> csv.reader (stdlib)
        .xlsx          -> openpyxl
        .xls (legacy)  -> xlrd
        .zip           -> unzip the single .csv/.xlsx/.xls entry inside,
                          then read that (the real Download Center export
                          format — the report is always zipped)
    Row data below the header is never read.

    Raises UnsupportedFileTypeError for any other extension.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        return _read_csv_headers(file_path)
    if ext == ".xlsx":
        return _read_xlsx_headers(file_path)
    if ext == ".xls":
        return _read_xls_headers(file_path)
    if ext == ".zip":
        return _read_zip_headers(file_path)
    raise UnsupportedFileTypeError(
        f"Unsupported downloaded file type:\n{ext or '(no extension)'}\n\n"
        "Supported formats:\n.csv\n.xlsx\n.xls\n.zip (containing .csv/.xlsx/.xls)"
    )


# ─────────────────────────────────────────────────────────────────────────
# Formatting helpers (failure messages only — never dumps file contents)
# ─────────────────────────────────────────────────────────────────────────

def _format_list(items):
    if not items:
        return "[]"
    body = ",\n".join(f'  "{item}"' for item in items)
    return f"[\n{body}\n]"


# ─────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────

def validate_file_headers(file_path, expected_headers, order_sensitive=True):
    """
    Validate that file_path's header row EXACTLY matches expected_headers —
    same names, same spelling, same capitalization, same spacing — and (by
    default) in the same order.

    Only the header row is read; row data, values, data types, record
    counts, and business logic are never inspected here.

    Args:
        file_path: path to the downloaded .csv/.xlsx/.xls file, or a .zip
            containing exactly one of those (the real Download Center export).
        expected_headers: ordered list of expected header strings.
        order_sensitive: when True (default), a correct set of headers in
            the wrong order still FAILS (position-by-position comparison).
            Set False to allow order-independent comparison — kept as a
            parameter (instead of hardcoding order-sensitivity) so this can
            change later without redesigning the validator.

    Returns:
        The actual header list, on success.

    Raises:
        FileNotDownloadedError   — file_path doesn't exist.
        UnsupportedFileTypeError — file_path's extension isn't .csv/.xlsx/.xls/.zip,
            or a .zip was given but contains no .csv/.xlsx/.xls entry.
        EmptyFileError           — the file has no header row at all.
        HeaderValidationError    — headers were read but don't exactly match.
    """
    if not file_path or not os.path.isfile(file_path):
        raise FileNotDownloadedError(
            "SMS Download Center file was not downloaded.\n"
            f"Expected file at: {file_path}"
        )

    actual_headers = read_file_headers(file_path)

    if not actual_headers or all((h is None or h == "") for h in actual_headers):
        raise EmptyFileError(
            "SMS Download Center downloaded file is empty or contains no headers.\n"
            f"File: {file_path}"
        )

    expected = list(expected_headers)
    missing = [h for h in expected if h not in actual_headers]
    unexpected = [h for h in actual_headers if h not in expected]

    mismatches = []
    if order_sensitive:
        for i in range(min(len(expected), len(actual_headers))):
            if expected[i] != actual_headers[i]:
                mismatches.append((i + 1, expected[i], actual_headers[i]))

    is_match = (
        len(expected) == len(actual_headers)
        and not missing
        and not unexpected
        and not mismatches
    )
    if is_match:
        return actual_headers

    lines = [
        "SMS Download Center header validation failed.",
        "",
        f"Expected header count: {len(expected)}",
        f"Actual header count: {len(actual_headers)}",
        "",
        "Expected headers:",
        _format_list(expected),
        "",
        "Actual headers:",
        _format_list(actual_headers),
        "",
        "Missing headers:",
        _format_list(missing),
        "",
        "Unexpected headers:",
        _format_list(unexpected),
    ]
    if mismatches:
        lines.append("")
        lines.append("Header mismatch:")
        for position, expected_name, actual_name in mismatches:
            lines.append(f"Position {position}")
            lines.append(f"Expected: {expected_name}")
            lines.append(f"Actual: {actual_name}")

    raise HeaderValidationError(
        "\n".join(lines),
        missing=missing,
        unexpected=unexpected,
        mismatches=mismatches,
        expected=expected,
        actual=actual_headers,
    )
