"""
utils/datetime_verification.py

Generic, browser/pytest-independent Date/Date-Time verification utility,
shared across every SMS module's UI-vs-export date/date-time checks
(SMS Messages, Campaign List, Sender IDs, Templates, Download Center,
Incoming Messages, Block Keywords, Block Numbers, Error Codes).

Reuses utils/report_data_validator.py's already-established DATE_FORMATS
/ parse_report_date() (same "dd-mm-yyyy" / "dd-mm-yyyy hh:mm:ss" spec,
same strptime-based real-calendar-validity check) rather than
reimplementing date parsing a second time -- this module builds
UI-vs-export COMPARISON on top of that, which report_data_validator.py
does not do (it validates export-only data against a spec, never against
a second, independently-captured UI value set).

Per-module integration does NOT hardcode a single date column: each
caller passes its own confirmed date column list (built from this
project's own constants/*_ui_headers.py / *_headers.py -- the existing
single-source-of-truth header specs already used by every module's
header-verification tests) via `date_columns`/`export_date_columns`.

Row correspondence -- the "1:1 same row" limitation
-----------------------------------------------------
Playwright can read the on-screen table's CURRENTLY VISIBLE rows (one
page of results), while an export is typically the full filtered result
set. Nothing in this project confirms the two are guaranteed to render
in the same order (sort direction, pagination, or export ordering could
differ), and assuming positional row-N-on-screen == row-N-in-export
would silently compare unrelated rows on any page whose order doesn't
happen to match -- exactly the kind of false failure/false pass this
task's own spec warns against ("prevent false failures caused by
whitespace or equivalent representation").

So compare_ui_and_export_datetime() supports two, explicit modes:

  * key_field given (e.g. "Phone Number", "Sender Id", "Campaign Name" --
    whatever real column uniquely identifies a row for that module):
    matches each UI row to its export row via that key, so a genuine
    per-row UI-value-vs-export-value mismatch is reported with real
    Row/UI Value/Export Value detail, exactly per this task's required
    failure format.

  * key_field omitted: falls back to a MULTISET comparison per column --
    every UI value must appear the same number of times somewhere in the
    export's values for that column, and vice versa. This still catches
    a genuine data mismatch (a UI value with no matching export value, or
    an export value with no matching UI source) without assuming row
    order, and is used for a module where no reliable natural key column
    is confirmed on both sides.

Both modes normalize before comparing (normalize_datetime()) so
whitespace or an equivalent-but-differently-formatted representation
(e.g. a trailing space, or a real datetime.datetime object from an .xlsx
cell vs. the same value as a string) never causes a false mismatch.
"""
from __future__ import annotations

import datetime

from utils.report_data_validator import DATE_FORMATS, parse_report_date

# CONFIRMED real, live app behavior (project owner + a real pasted export
# file, rcs_country_report_*.csv): RCS/WhatsApp Analytics report EXPORTS
# (not their UI, which stays the project-wide dd-mm-yyyy convention) render
# their "Duration" column as ISO yyyy-mm-dd, e.g. "2026-09-27" -- a raw-text
# fact in the downloaded CSV itself, not a display artifact of opening it in
# Excel (Excel's own locale-formatted DISPLAY of a recognized date string is
# a separate thing from the file's actual text). This is NOT accepted by
# default anywhere in this module -- every existing caller (SMS/RCS/WhatsApp
# transactional modules) keeps requiring strict dd-mm-yyyy, per this task's
# own "2026-09-28" (yyyy-mm-dd) INVALID example. It is only tried when a
# caller explicitly passes accept_iso=True (see verify_analytics_report_dates()
# in utils/analytics_report_date_verification.py, the only confirmed use).


class DateVerificationError(AssertionError):
    """Base class for every error this module raises."""


class DateFormatValidationError(DateVerificationError):
    """One or more values failed format/real-date validation.
    `.failures` is a list of dicts: {module, column, row, actual, expected}."""

    def __init__(self, message, failures):
        super().__init__(message)
        self.failures = failures


class DateComparisonError(DateVerificationError):
    """One or more UI values didn't match their corresponding export
    value (or vice versa). `.failures` -- same shape as above, plus
    ui_value/export_value/reason."""

    def __init__(self, message, failures):
        super().__init__(message)
        self.failures = failures


# CONFIRMED real app behavior (real pasted pytest failure, RCS Messages):
# a conditional timestamp column that only applies to one outcome of a
# status field (e.g. "Failed At" on a row that was actually Delivered,
# or "Delivered At" on a row that actually Failed) renders a placeholder
# dash on screen instead of being truly empty -- "—" (em dash) was the
# real observed character, so this is not a real value to format-check
# and not itself a bug; it means "not applicable for this row", exactly
# like a genuinely empty cell. Treated as blank here (not a format
# violation) for every module that uses this utility, not just RCS
# Messages -- any other module with a conditional timestamp column
# (e.g. SMS's own "DLR Received At" before a DLR has arrived) gets the
# same real-world tolerance for free.
_BLANK_PLACEHOLDER_TOKENS = {"-", "--", "—", "–", "n/a", "na", "null", "none"}


def _is_blank(value):
    if value is None:
        return True
    if isinstance(value, str):
        text = value.strip()
        if text == "":
            return True
        if text.lower() in _BLANK_PLACEHOLDER_TOKENS:
            return True
    return False


def parse_date_value(value):
    """Thin, explicitly-named re-export of
    utils.report_data_validator.parse_report_date() -- same contract
    (real datetime.datetime/date, a "dd-mm-yyyy[ hh:mm:ss]" string, or
    None for anything else, never raises). Kept as its own name here per
    this task's requested reusable-function list, without duplicating
    the parsing logic itself."""
    return parse_report_date(value)


def validate_date_format(value, field_kind="auto", accept_iso=False, accept_no_seconds=False, accept_text_month=False, accept_iso_datetime=False):
    """Returns (ok: bool, parsed: datetime.datetime | None, detected_kind:
    "date" | "date-time" | None).

    `field_kind`:
      - "date"      -- require plain "dd-mm-yyyy" (reject a value that
                        also carries a time component as not date-only,
                        since this project's DATE_FORMATS tries the
                        date-time pattern first -- see below).
      - "date-time" -- require the full "dd-mm-yyyy hh:mm:ss".
      - "auto" (default) -- accept either; detected_kind reports which
                        one actually matched.

    `accept_iso` (default False): also accept a strict ISO "yyyy-mm-dd"
    string as a valid "date" match, tried only after both entries in
    DATE_FORMATS fail. Off by default everywhere in this project -- see
    this module's own top-of-file note on why (real, confirmed export
    behavior for RCS/WhatsApp Analytics reports specifically, NOT a
    general relaxation of the dd-mm-yyyy convention).

    Never raises -- an unparseable value returns (False, None, None).
    Trims whitespace before validation (a bare str.strip(); a native
    datetime/date object has no whitespace to trim)."""
    raw = value
    if isinstance(value, str):
        raw = value.strip()
        if raw == "":
            return False, None, None

    if isinstance(raw, datetime.datetime):
        return (field_kind != "date-only-strict"), raw, "date-time"
    if isinstance(raw, datetime.date):
        return True, datetime.datetime(raw.year, raw.month, raw.day), "date"

    if not isinstance(raw, str):
        return False, None, None

    for fmt in DATE_FORMATS:  # ["%d-%m-%Y %H:%M:%S", "%d-%m-%Y"] -- datetime tried first
        try:
            parsed = datetime.datetime.strptime(raw, fmt)
        except ValueError:
            continue
        detected = "date-time" if fmt == "%d-%m-%Y %H:%M:%S" else "date"
        if field_kind == "date" and detected == "date-time":
            # A full timestamp where only a bare date was expected --
            # still a real, parseable value, just not the configured
            # shape for this field. Report it as non-matching so a
            # module explicitly configured "date-only" catches a field
            # that unexpectedly started carrying a time component.
            return False, parsed, detected
        if field_kind == "date-time" and detected == "date":
            return False, parsed, detected
        return True, parsed, detected

    if accept_iso and field_kind != "date-time":
        try:
            parsed = datetime.datetime.strptime(raw, "%Y-%m-%d")
            return True, parsed, "date"
        except ValueError:
            pass

    if accept_iso_datetime and field_kind != "date":
        # CONFIRMED real behavior (real pasted DOM, RCS Download Center
        # Summary popup): "Generated at"/"Completed at" render ISO
        # yyyy-mm-dd hh:mm:ss WITH A SPACE separator (e.g. "2026-09-28
        # 15:44:03") -- a third real format, distinct from both this
        # project's usual dd-mm-yyyy hh:mm:ss and the bare ISO
        # yyyy-mm-dd already seen on RCS/WhatsApp Analytics exports
        # (accept_iso). Opt-in and scoped to just the specific field(s)
        # confirmed to render it -- not a general relaxation.
        try:
            parsed = datetime.datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
            return True, parsed, "date-time"
        except ValueError:
            pass

    if accept_text_month and field_kind != "date-time":
        # CONFIRMED real behavior (real pasted pytest failure, RCS
        # Message Type Analytics export): this report's own "Duration"
        # export column renders a THIRD format, "dd Mon yyyy" (e.g.
        # "27 Sep 2026"), distinct from both this project's usual
        # dd-mm-yyyy and the already-confirmed ISO yyyy-mm-dd export
        # variant (accept_iso). Opt-in and scoped to just the specific
        # module(s) confirmed to actually render it (see
        # verify_analytics_report_dates()'s own accept_text_month
        # parameter) -- not a general relaxation.
        try:
            parsed = datetime.datetime.strptime(raw, "%d %b %Y")
            return True, parsed, "date"
        except ValueError:
            pass

    if accept_no_seconds and field_kind != "date":
        # CONFIRMED real behavior (project-owner-confirmed): SMS Latency
        # Report / SMS Status Report default to hourly Report Type, and
        # their "Duration" column renders an hour-bucket timestamp
        # WITHOUT seconds, e.g. "28-09-2026 15:00" -- dd-mm-yyyy hh:mm,
        # not this project's usual strict dd-mm-yyyy hh:mm:ss. Opt-in and
        # scoped to just those two modules' Duration column (see
        # utils/analytics_report_date_verification.py), not a project-
        # wide relaxation of the seconds-required date-time convention.
        try:
            parsed = datetime.datetime.strptime(raw, "%d-%m-%Y %H:%M")
            return True, parsed, "date-time"
        except ValueError:
            pass

    return False, None, None


def normalize_datetime(value, field_kind="auto", accept_iso=False, accept_no_seconds=False, accept_text_month=False, accept_iso_datetime=False):
    """Returns a canonical, whitespace/representation-independent form
    for comparison: a real datetime.datetime (date-only values are
    normalized to midnight, exactly like parse_report_date() already
    does for a bare "dd-mm-yyyy"), or None if `value` isn't a valid
    date/date-time. Two values that printed differently but represent
    the same real date/time (e.g. an .xlsx-native datetime.date vs. the
    equivalent "28-09-2026" string, or a value with incidental leading/
    trailing whitespace) normalize to the same datetime.datetime and so
    compare equal -- this is what "the normalized comparison must
    prevent false failures caused by whitespace or equivalent
    representation" (task spec) means in practice here.

    field_kind="date": the comparison is DATE-ONLY -- normalizes to a
    datetime with the time component zeroed, so a date-only field
    compared against a date-only field never fails over an absent
    time-of-day, matching this task's "If the field is configured as
    date-only, compare only the date portion" rule.

    `accept_iso` (default False): see validate_date_format()'s own note
    -- lets a "yyyy-mm-dd" value (CONFIRMED real for RCS/WhatsApp
    Analytics report exports) normalize to the same calendar date as its
    dd-mm-yyyy UI counterpart, so a UI-vs-export comparison across that
    specific format difference isn't a false failure.
    """
    ok, parsed, _detected = validate_date_format(
        value, field_kind="auto", accept_iso=accept_iso, accept_no_seconds=accept_no_seconds,
        accept_text_month=accept_text_month, accept_iso_datetime=accept_iso_datetime,
    )
    if not ok or parsed is None:
        return None
    if field_kind == "date":
        return datetime.datetime(parsed.year, parsed.month, parsed.day)
    return parsed


def column_index_lookup(headers):
    """Returns a get_column_index(header_name)-shaped callable bound to a
    static headers list already read from a page. Convenience so a
    caller doesn't have to write its own header-index loop, or depend on
    every page object exposing headers under one exact method name --
    this project's page objects vary (get_visible_column_headers() on
    most, get_table_headers() on SMSMessagePage, get_csv_headers() for a
    downloaded file elsewhere) -- the caller just reads whatever list
    that page already provides and hands it here."""
    def _lookup(name):
        for i, h in enumerate(headers):
            if isinstance(h, str) and h.strip().lower() == name.strip().lower():
                return i
        return None
    return _lookup


def detect_date_columns(headers, candidate_columns):
    """Return the subset of `candidate_columns` that are actually present
    in `headers` (case-insensitive, whitespace-trimmed match) -- dynamic
    detection instead of assuming every configured column exists on
    every module/every run. `headers` is whatever the caller already read
    (e.g. page.get_visible_column_headers(), or the export's own header
    row from utils.file_validator.read_file_rows()/read_file_headers()).
    Order follows `candidate_columns`, not `headers`.

    Returns each match using `headers`' OWN real spelling/casing, not the
    candidate's -- a caller almost always turns around and uses the
    result as an exact dict key into the same row data `headers` came
    from (e.g. read_export_datetime_values()'s `column not in rows[0]`),
    so returning the candidate's casing when it differs from the export's
    real casing (CONFIRMED real bug: an RCS/WhatsApp Analytics export's
    actual column is "duration", lowercase, not the "Duration" the
    candidate list assumed) would silently produce zero matches
    downstream despite this function correctly detecting the column as
    present."""
    real_spelling_by_key = {}
    for h in headers:
        if isinstance(h, str):
            key = h.strip().lower()
            if key not in real_spelling_by_key:
                real_spelling_by_key[key] = h
    return [
        real_spelling_by_key[c.strip().lower()]
        for c in candidate_columns
        if c.strip().lower() in real_spelling_by_key
    ]


def detect_ui_date_columns(ui_headers, date_columns, ui_column_names=None):
    """Same detection as detect_date_columns(), but for the UI side of a
    module where the UI's real header label can differ from the
    canonical/export name (see date_module_config.py's "ui_column_names"
    docstring -- e.g. UI "Created at" vs canonical/export "Created At").
    Checks each canonical column's REAL UI label (ui_column_names.get(col,
    col)) against `ui_headers`, and returns the matching entries as their
    CANONICAL names -- so the result lines up directly with
    read_export_datetime_values()'s keys for
    capture_ui_datetime_values(..., column_pairs=ui_column_names) /
    validate_ui_export_dates() to compare the right pair of columns."""
    ui_column_names = ui_column_names or {}
    normalized_headers = {h.strip().lower() for h in ui_headers if isinstance(h, str)}
    detected = []
    for canonical in date_columns:
        ui_label = ui_column_names.get(canonical, canonical)
        if ui_label.strip().lower() in normalized_headers:
            detected.append(canonical)
    return detected


def capture_ui_datetime_values(get_cell_text, get_column_index, row_count, date_columns, column_pairs=None):
    """Read every populated value in each of `date_columns` from the
    CURRENTLY VISIBLE UI table, using the caller's own already-confirmed
    per-page cell readers (page.get_cell_text(row, col) /
    page.get_column_index(header) -- every page object in this project
    already exposes these, or inherits them from BasePage) rather than
    this module reaching into Playwright itself (this module stays
    Playwright-independent, matching report_data_validator.py's own
    design). `row_count` is the caller's own page.get_row_count().

    `column_pairs` (optional): {canonical_name: ui_header_name}. This
    project's own UI header labels and export header labels for the SAME
    real field routinely differ only in casing (e.g. UI "Created at" vs
    export "Created At" -- confirmed across every *_ui_headers.py /
    *_headers.py pair in constants/). Returned dict keys must line up
    EXACTLY with read_export_datetime_values()'s keys (the export's own
    header text) for validate_ui_export_dates()/
    compare_ui_and_export_datetime() to compare the right pair of
    columns -- passing `column_pairs` here (keyed by the EXPORT/canonical
    name, valued by the real UI header text to look up) is what makes
    that alignment correct instead of silently comparing nothing when
    the two sides' casing differs. When omitted, `date_columns` is used
    directly as both the UI lookup name and the returned dict key
    (correct only when a module's UI and export header text for that
    column happen to be identical, e.g. SMS Messages' "Received At").

    Returns {column: [values_by_row_index]}; a column not found on the
    page (get_column_index returns None) is simply omitted -- callers
    should already have narrowed `date_columns` via detect_date_columns()
    first. A blank cell contributes "" (not skipped), so row indices stay
    aligned with the real table; callers filter blanks out downstream."""
    values_by_column = {}
    for column in date_columns:
        ui_lookup_name = (column_pairs or {}).get(column, column)
        col_index = get_column_index(ui_lookup_name)
        if col_index is None:
            continue
        values = []
        for row in range(row_count):
            values.append(get_cell_text(row, col_index))
        values_by_column[column] = values
    return values_by_column


def read_export_datetime_values(rows, date_columns):
    """Extract every populated value in each of `date_columns` from
    already-read export rows (utils.file_validator.read_file_rows()'s
    list-of-dicts shape -- CSV and XLSX are already normalized to the
    same shape by that function, so this needs no format-specific
    branching of its own). A column not present in a row's dict is
    skipped for that row (rather than inserting a fabricated blank),
    matching the export's real per-row header set (a module's export can
    have rows with a differing populated column set is not expected here,
    but this is defensive rather than assuming a fixed shape).

    Returns {column: [values_by_row_index]}, one list per requested
    column that's actually present in `rows`' own headers (a column
    absent from the export entirely is omitted, exactly like
    capture_ui_datetime_values() omits an absent UI column)."""
    values_by_column = {}
    for column in date_columns:
        if not rows or column not in rows[0]:
            continue
        values_by_column[column] = [row.get(column) for row in rows]
    return values_by_column


def _format_date_failures(title, module, failures):
    lines = [f"{title} FAILED (module: {module}): {len(failures)} issue(s) found."]
    for f in failures:
        lines.append("")
        lines.append(f"Module: {module}")
        lines.append(f"Column: {f['column']}")
        lines.append(f"Row: {f['row']}")
        for key in ("actual", "ui_value", "export_value"):
            if key in f:
                label = {"actual": "Actual", "ui_value": "UI Value", "export_value": "Export Value"}[key]
                lines.append(f"{label}: {f[key]}")
        if "expected" in f:
            lines.append(f"Expected: {f['expected']}")
        if "reason" in f:
            lines.append(f"Reason: {f['reason']}")
    return "\n".join(lines)


def validate_date_values_format(module, column, values, field_kind="auto", accept_iso=False, accept_no_seconds=False, accept_text_month=False, accept_iso_datetime=False):
    """Format/Date-Time Verification for one already-extracted list of
    values (UI or export side) -- validates EVERY populated value (not
    just that the column exists), skips genuinely blank entries ("do not
    fail a test merely because a module does not contain a date column" /
    "ignore completely empty rows" -- a blank cell in an otherwise
    populated column is not itself a format violation), trims whitespace
    first, and never silently ignores a real invalid value. Raises
    DateFormatValidationError (one exception, every bad row listed) if
    any populated value fails; returns the parsed/normalized values
    (blank rows -> None) on success.

    `accept_iso` (default False): see validate_date_format()'s own note."""
    failures = []
    normalized = []
    for row_index, raw in enumerate(values, start=1):
        text = raw.strip() if isinstance(raw, str) else raw
        if _is_blank(text):
            normalized.append(None)
            continue
        ok, parsed, _detected = validate_date_format(
            text, field_kind=field_kind, accept_iso=accept_iso, accept_no_seconds=accept_no_seconds,
            accept_text_month=accept_text_month, accept_iso_datetime=accept_iso_datetime,
        )
        if not ok:
            expected = {
                "date": "dd-mm-yyyy",
                "date-time": "dd-mm-yyyy hh:mm:ss",
            }.get(field_kind, "dd-mm-yyyy or dd-mm-yyyy hh:mm:ss")
            if accept_iso and field_kind != "date-time":
                expected += " (or yyyy-mm-dd)"
            if accept_no_seconds and field_kind != "date":
                expected += " (or dd-mm-yyyy hh:mm, no seconds)"
            if accept_text_month and field_kind != "date-time":
                expected += " (or dd Mon yyyy, e.g. 27 Sep 2026)"
            if accept_iso_datetime and field_kind != "date":
                expected += " (or yyyy-mm-dd hh:mm:ss)"
            failures.append({
                "column": column, "row": row_index,
                "actual": repr(raw), "expected": expected,
            })
            normalized.append(None)
        else:
            normalized.append(normalize_datetime(
                text, field_kind=field_kind, accept_iso=accept_iso, accept_no_seconds=accept_no_seconds,
                accept_text_month=accept_text_month, accept_iso_datetime=accept_iso_datetime,
            ))
    if failures:
        raise DateFormatValidationError(
            _format_date_failures("Date Format Validation", module, failures), failures
        )
    return normalized


def compare_ui_and_export_datetime(module, column, ui_values, export_values, field_kind="auto", key_values=None, accept_iso=False, accept_no_seconds=False, accept_text_month=False):
    """UI vs Export Date/Date-Time Comparison for one column.

    `ui_values`/`export_values`: raw (unparsed) value lists, as captured
    by capture_ui_datetime_values()/read_export_datetime_values() --
    format validation happens here too (via normalize_datetime()) so a
    caller doesn't have to pre-validate before comparing.

    `key_values` (optional): a list of natural-key values (e.g. Phone
    Number/Sender Id/Campaign Name), the SAME LENGTH as `ui_values`,
    identifying which export row each UI row corresponds to. When given,
    this does an exact per-row keyed comparison (real Row/UI Value/Export
    Value failure detail). When omitted, this falls back to a MULTISET
    SUBSET comparison: every UI value must appear (with at least as many
    occurrences) among the export values -- NOT the reverse, since the
    export is normally the full filtered result set while the UI only
    shows whatever page is currently rendered, so the export having
    additional values beyond what's on screen right now is expected, not
    a failure. See this module's docstring for why no positional
    row-order correspondence is assumed without a confirmed natural key.

    Blank UI values are skipped (nothing to compare); a populated UI
    value with no corresponding export value (or vice versa) is a real
    failure, not silently ignored, per the task's own rules.

    `accept_iso` (default False): see validate_date_format()'s own note
    -- normalizes an export-side "yyyy-mm-dd" value to the same calendar
    date as its dd-mm-yyyy UI counterpart (CONFIRMED real for RCS/
    WhatsApp Analytics report exports), so this format difference alone
    doesn't register as a mismatch."""
    failures = []

    if key_values is not None:
        assert len(key_values) == len(ui_values), (
            f"key_values length ({len(key_values)}) must match ui_values "
            f"length ({len(ui_values)}) for module {module!r}, column {column!r}"
        )
        export_by_key = {}
        for key, val in zip(key_values, export_values):
            export_by_key.setdefault(key, []).append(val)
        # export_values here is assumed pre-aligned to the same key order
        # by the caller when using keyed mode with export's own key
        # column -- see validate_ui_export_dates()'s docstring for the
        # exact contract.
        for row_index, (key, ui_raw) in enumerate(zip(key_values, ui_values), start=1):
            ui_text = ui_raw.strip() if isinstance(ui_raw, str) else ui_raw
            if _is_blank(ui_text):
                continue
            ui_norm = normalize_datetime(
                ui_text, field_kind=field_kind, accept_iso=accept_iso, accept_no_seconds=accept_no_seconds,
                accept_text_month=accept_text_month,
            )
            candidates = export_by_key.get(key, [])
            match = any(
                normalize_datetime(
                    c, field_kind=field_kind, accept_iso=accept_iso, accept_no_seconds=accept_no_seconds,
                    accept_text_month=accept_text_month,
                ) == ui_norm
                for c in candidates if not _is_blank(c)
            )
            if not match:
                failures.append({
                    "column": column, "row": row_index,
                    "ui_value": repr(ui_raw),
                    "export_value": repr(candidates[0]) if candidates else "<no matching export row>",
                    "reason": "UI and export date-time values do not match.",
                })
    else:
        def _norm_multiset(values):
            counts = {}
            for v in values:
                text = v.strip() if isinstance(v, str) else v
                if _is_blank(text):
                    continue
                norm = normalize_datetime(
                    text, field_kind=field_kind, accept_iso=accept_iso, accept_no_seconds=accept_no_seconds,
                    accept_text_month=accept_text_month,
                )
                key = norm.isoformat() if norm is not None else f"<invalid:{text!r}>"
                counts[key] = counts.get(key, 0) + 1
            return counts

        ui_counts = _norm_multiset(ui_values)
        export_counts = _norm_multiset(export_values)
        # UI -> export only (UI subset-of export), never the reverse: the
        # export is typically the FULL filtered result set while the UI
        # only shows whatever page is currently rendered, so the export
        # legitimately containing MORE distinct/duplicate values than are
        # visible on screen right now is expected, not a mismatch. What
        # must never happen is a value genuinely shown on screen having no
        # corresponding value anywhere in the export.
        for key, count in ui_counts.items():
            if export_counts.get(key, 0) < count:
                failures.append({
                    "column": column, "row": "-",
                    "ui_value": key, "export_value": "<not found in export>",
                    "reason": "A UI date-time value has no corresponding export value.",
                })

    if failures:
        raise DateComparisonError(
            _format_date_failures("Date-Time Validation", module, failures), failures
        )
    return True


def validate_ui_export_dates(module_name, ui_values_by_column, export_values_by_column, field_kinds=None, key_values_by_column=None):
    """Top-level orchestrator -- the single entry point a test should
    call. Runs, per configured date column:

        Date/Date-Time Format Verification (UI side)
                v
        Date/Date-Time Format Verification (export side)
                v
        UI vs Export Date/Date-Time Comparison

    `ui_values_by_column`/`export_values_by_column`: {column: [values]},
    as returned by capture_ui_datetime_values()/
    read_export_datetime_values(). Only columns present in BOTH dicts are
    checked (a column the caller couldn't find on one side is already
    excluded by detect_date_columns() upstream -- this does not silently
    skip a column that exists on both sides, only one truly absent from
    one of them).

    `field_kinds` (optional): {column: "date" | "date-time"}. Omitted ->
    "auto" (accepts either shape, per-value) for every column.

    `key_values_by_column` (optional): {column: key_values_list} for a
    column that should use compare_ui_and_export_datetime()'s keyed mode
    instead of the multiset fallback.

    Returns a dict {column: {"ui": [...], "export": [...]}} of the
    validated raw value lists on success. Raises the FIRST
    DateFormatValidationError/DateComparisonError encountered (module
    already names which column/row in its message) -- callers wanting
    every column checked regardless of an earlier failure should catch
    per-column themselves; the individual functions above are exposed
    for exactly that."""
    field_kinds = field_kinds or {}
    key_values_by_column = key_values_by_column or {}
    results = {}
    for column, ui_values in ui_values_by_column.items():
        if column not in export_values_by_column:
            continue
        export_values = export_values_by_column[column]
        field_kind = field_kinds.get(column, "auto")

        validate_date_values_format(module_name, column, ui_values, field_kind=field_kind)
        validate_date_values_format(module_name, column, export_values, field_kind=field_kind)
        compare_ui_and_export_datetime(
            module_name, column, ui_values, export_values,
            field_kind=field_kind, key_values=key_values_by_column.get(column),
        )
        results[column] = {"ui": ui_values, "export": export_values}
    return results
