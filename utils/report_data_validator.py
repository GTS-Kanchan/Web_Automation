"""
utils/report_data_validator.py

Generic, browser/pytest-independent, CONFIGURATION-based validators for
already-extracted report row data (utils.file_validator.read_file_rows()'s
list-of-dicts shape). Built for the Campaign Report "Total Messages"
export deep-verification flow, but every function here is parameterized
by column name / field spec so it can be reused for any other export
(other cards on this same report page, other channels/report types) --
per the task's own explicit "Keep this configuration-based so it can be
reused for other exports" instruction.

Pipeline this module implements (Header Verification is
utils.file_validator.validate_file_headers(), already existing and reused
as-is by the calling test, NOT reimplemented here):

    Data Exists Verification         -> verify_data_exists()
    Required Field Verification      -> verify_required_fields()
    Data Type Verification           -> verify_data_types()
    Date/Date-Time Verification      -> verify_date_formats()
    (UI count vs export count)       -> verify_ui_total_messages_vs_export()

Every function raises a specific AssertionError subclass (so pytest
reports it as a normal, readable assertion failure with no extra wiring)
rather than returning True/False, matching utils/file_validator.py's
existing exception-based contract. Every multi-row check collects EVERY
failure found (not just the first) before raising, so one run of the
suite surfaces the full list of bad rows/columns instead of only the
first one hit.
"""
from __future__ import annotations

import datetime

# The two formats the task specifies, tried in this order (more specific
# first, so "28-09-2026 12:42:52" isn't mis-parsed by the date-only
# pattern truncating at the space). datetime.strptime already rejects a
# calendar-impossible date (e.g. "31-02-2026", "29-02-2027") with
# ValueError, so format matching and real calendar validity are both
# covered by the same call -- no separate validity check is needed.
DATE_FORMATS = ["%d-%m-%Y %H:%M:%S", "%d-%m-%Y"]


class ReportDataError(AssertionError):
    """Base class for every error this module raises."""


class DataExistsError(ReportDataError):
    """The export has no data rows at all."""


class RequiredFieldError(ReportDataError):
    """One or more required fields are missing/blank in one or more rows.
    `.failures` carries EVERY failure found (not just the first) as a
    list of {row, column, actual_value, expected} dicts."""

    def __init__(self, message, failures):
        super().__init__(message)
        self.failures = failures


class DataTypeError(ReportDataError):
    """One or more fields don't match their configured type. `.failures`
    -- same shape as RequiredFieldError."""

    def __init__(self, message, failures):
        super().__init__(message)
        self.failures = failures


class DateFormatError(ReportDataError):
    """One or more date/date-time columns contain a value that isn't a
    real date in one of DATE_FORMATS (or an already-valid
    datetime.date/datetime.datetime object, e.g. from an .xlsx cell).
    `.failures` -- same shape as the above."""

    def __init__(self, message, failures):
        super().__init__(message)
        self.failures = failures


class CountMismatchError(ReportDataError):
    """UI Total Messages count doesn't match the export's data-row count."""


def parse_report_date(value):
    """Returns a real datetime.datetime if `value` is a valid date per
    this project's supported formats, else None. Never raises.

    Accepts THREE kinds of input:
      - a real datetime.datetime / datetime.date (as read from a native
        Excel date cell by utils.file_validator.read_file_rows() -- it is
        already a valid date, nothing to parse).
      - a string matching "dd-mm-yyyy hh:mm:ss" or "dd-mm-yyyy" (the two
        formats this task specifies) -- strptime rejects a
        calendar-impossible date on its own, so real validity is
        confirmed by the same call as format matching.
      - anything else (None, "", a non-date string, a bare number) ->
        None.
    """
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, datetime.date):
        return datetime.datetime(value.year, value.month, value.day)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        for fmt in DATE_FORMATS:
            try:
                return datetime.datetime.strptime(text, fmt)
            except ValueError:
                continue
    return None


def _is_blank(value):
    return value is None or (isinstance(value, str) and value.strip() == "")


# Real app behavior (user-confirmed): a message whose Status is "Sent"
# has NOT yet received a delivery receipt, so its "DLR Received At" cell
# legitimately renders as a placeholder dash ("—") rather than a real
# timestamp -- this is not missing/bad data, it's the correct UI state for
# a message still awaiting DLR. _is_unset_placeholder() recognizes both a
# genuinely blank value AND that placeholder character, for use ONLY by
# the optional_when exemption below (never by verify_required_fields(),
# which correctly still treats "—" as "present" -- the column has real
# rendered content, it's just not a date).
_PLACEHOLDER_VALUES = {"—"}


def _is_unset_placeholder(value):
    if _is_blank(value):
        return True
    return isinstance(value, str) and value.strip() in _PLACEHOLDER_VALUES


def _field_is_exempt(field, row, value, optional_when):
    """True if `field`'s value in `row` is allowed to be blank/placeholder
    for this specific row, per the caller-supplied `optional_when` map
    ({column: callable(row) -> bool}). Only exempts when the value is
    ALSO actually blank/placeholder -- a row that matches the predicate
    but has a real (possibly invalid) value in that column is still
    checked normally, so this can't be used to silently hide a genuine
    bad value."""
    if not optional_when or field not in optional_when:
        return False
    if not _is_unset_placeholder(value):
        return False
    try:
        return bool(optional_when[field](row))
    except Exception:
        return False


def _is_numeric(value):
    if isinstance(value, bool):
        return False  # bool is technically an int subclass -- not a real "numeric" field value
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return False
        try:
            float(text)
            return True
        except ValueError:
            return False
    return False


def _is_nonempty_string(value):
    if isinstance(value, str):
        return value.strip() != ""
    # A non-string, non-blank value (e.g. a number an .xlsx export left
    # unquoted) still has real textual content once stringified -- this
    # is about "has real text", not "Python str is the literal type".
    return value is not None and str(value).strip() != ""


def verify_data_exists(rows, context=""):
    """Data Exists Verification: the export must contain at least one
    data row (the header row is never counted -- `rows` here is already
    just the data rows, as returned by
    utils.file_validator.read_file_rows()). Returns `rows` unchanged on
    success (so callers can chain: `data = verify_data_exists(rows)`)."""
    if not rows:
        raise DataExistsError(
            f"Data Exists Verification FAILED{f' ({context})' if context else ''}: "
            f"export contains 0 data rows (header row only, or completely empty)."
        )
    return rows


def _format_failures(title, context, failures):
    lines = [f"{title} FAILED{f' ({context})' if context else ''}: "
             f"{len(failures)} issue(s) found."]
    for f in failures:
        lines += [
            "",
            f"Row: {f['row']}",
            f"Column: {f['column']}",
            f"Actual Value: {f['actual_value']}",
            f"Expected: {f['expected']}",
        ]
    return "\n".join(lines)


def verify_required_fields(rows, required_fields, context=""):
    """Required Field Verification: every field in `required_fields` must
    be present and non-blank in EVERY row."""
    failures = []
    for row_index, row in enumerate(rows, start=1):
        for field in required_fields:
            if field not in row:
                failures.append({
                    "row": row_index, "column": field,
                    "actual_value": "<column not present>",
                    "expected": "column to be present and non-blank",
                })
            elif _is_blank(row[field]):
                failures.append({
                    "row": row_index, "column": field,
                    "actual_value": repr(row[field]),
                    "expected": "non-blank value",
                })
    if failures:
        raise RequiredFieldError(
            _format_failures("Required Field Verification", context, failures), failures
        )
    return rows


def verify_data_types(rows, type_spec, context="", optional_when=None):
    """Data Type Verification: type_spec is {column: "string"|"numeric"|
    "date"}, so this is reusable for any export's own field set -- not
    hardcoded to the Total Messages report.

    `optional_when` (optional): {column: callable(row) -> bool}. For a
    row where the column's value is blank/placeholder (see
    _is_unset_placeholder()) AND the callable returns True for that row,
    the type check for that column is skipped instead of failing -- e.g.
    a "DLR Received At" date column that's legitimately still a
    placeholder while a message's Status is "Sent" (DLR not received
    yet). A present-but-invalid value in that column still fails
    normally; this only exempts the real "nothing to show yet" case."""
    failures = []
    for row_index, row in enumerate(rows, start=1):
        for field, expected_type in type_spec.items():
            if field not in row:
                continue  # verify_required_fields() already reports a missing column
            value = row[field]
            if expected_type == "string":
                ok = _is_nonempty_string(value)
                expected_desc = "non-empty string"
            elif expected_type == "numeric":
                ok = _is_numeric(value)
                expected_desc = "numeric/integer value"
            elif expected_type == "date":
                if _field_is_exempt(field, row, value, optional_when):
                    continue
                ok = parse_report_date(value) is not None
                expected_desc = "valid date/date-time (dd-mm-yyyy or dd-mm-yyyy hh:mm:ss)"
            else:
                raise ValueError(f"Unknown expected_type {expected_type!r} for column {field!r}")
            if not ok:
                failures.append({
                    "row": row_index, "column": field,
                    "actual_value": repr(value),
                    "expected": expected_desc,
                })
    if failures:
        raise DataTypeError(
            _format_failures("Data Type Verification", context, failures), failures
        )
    return rows


def verify_date_formats(rows, date_fields, context="", optional_when=None):
    """Date/Date-Time Verification: for every column named in
    `date_fields` ("every date/date-time column present in the export",
    per the task -- pass the export's own confirmed date columns here),
    every row's value must be a real date in one of DATE_FORMATS
    ("dd-mm-yyyy" / "dd-mm-yyyy hh:mm:ss") or an already-valid native
    date object. A DISTINCT pipeline stage from verify_data_types()'s
    "date" check (same underlying parser, but its own PASS/FAIL per the
    task's own pipeline diagram).

    `optional_when` -- same contract as verify_data_types()'s parameter
    of the same name (see its docstring): exempts a row/column from this
    check only when the value is ALSO actually blank/placeholder."""
    failures = []
    for row_index, row in enumerate(rows, start=1):
        for field in date_fields:
            if field not in row:
                continue
            value = row[field]
            if _field_is_exempt(field, row, value, optional_when):
                continue
            if parse_report_date(value) is None:
                failures.append({
                    "row": row_index, "column": field,
                    "actual_value": repr(value),
                    "expected": "dd-mm-yyyy or dd-mm-yyyy hh:mm:ss (a real calendar date)",
                })
    if failures:
        raise DateFormatError(
            _format_failures("Date/Date-Time Verification", context, failures), failures
        )
    return rows


def calculate_export_total_messages(rows):
    """Row count, exposed as its own named function per the task's
    Reusable Validation Structure -- does not count the header row
    (`rows` here is already the DATA rows only, as returned by
    utils.file_validator.read_file_rows())."""
    return len(rows)


def sum_numeric_field(rows, field):
    """Sum a numeric column across every row -- generic (any export, any
    numeric column), added because the "Total Messages" UI stat card is
    CONFIRMED (user report) to display the SUM of the export's "SMS
    Units" column, not the row/message count: a single message can
    consist of more than one SMS unit (e.g. a long SMS split into
    multiple parts), so a campaign can show e.g. 8 "Total Messages" for
    only 4 exported rows. A blank/non-numeric value contributes 0 rather
    than raising -- verify_data_types() (Data Type Verification, already
    run before this stage in the pipeline) is what's responsible for
    catching a genuinely bad "SMS Units" value; this function assumes
    that stage already passed."""
    total = 0
    for row in rows:
        value = row.get(field)
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            total += value
            continue
        if isinstance(value, str):
            text = value.strip()
            if not text:
                continue
            try:
                total += float(text)
            except ValueError:
                continue
    # Whole-number totals (the normal case -- SMS Units is an integer
    # count) come back as int rather than e.g. 8.0, matching the UI
    # card's own integer display.
    if isinstance(total, float) and total.is_integer():
        return int(total)
    return total


def verify_ui_total_messages_vs_export(ui_total_messages, export_total_messages, metric="Total Messages"):
    """UI Total Message Count vs Export Count Verification -- the
    mandatory final pipeline stage. Raises CountMismatchError with the
    task's exact required failure-message shape (Metric/UI Count/Export
    Count/Difference) on mismatch."""
    if ui_total_messages == export_total_messages:
        return True
    difference = abs(ui_total_messages - export_total_messages)
    raise CountMismatchError(
        "UI Total Messages vs Export Total Messages Verification FAILED.\n\n"
        f"Metric: {metric}\n"
        f"UI Count: {ui_total_messages}\n"
        f"Export Count: {export_total_messages}\n"
        f"Difference: {difference}"
    )
