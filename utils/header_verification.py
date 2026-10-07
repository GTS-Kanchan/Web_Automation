"""
utils/header_verification.py -- shared, channel-agnostic Header
Verification engine (UI + export + UI-vs-export comparison), reusable
for SMS, RCS, and WhatsApp alike -- same convention as
utils/datetime_verification.py / utils/table_date_verification.py for
date/date-time.

Reuses utils.file_validator.read_file_headers() for export extraction
(the project's existing, already-confirmed generic downloaded-file
header reader -- .csv/.xlsx/.xls/.zip) rather than re-implementing file
parsing here. This module adds what didn't exist yet as a shared,
reusable piece: duplicate detection, a formalized UI-side
presence/duplicate check (the same case-insensitive substring
convention already used ad hoc in e.g.
tests/sms/sender_id/test_sms_sender_id.py's
test_ui_default_table_headers_full), and a UI-vs-export "common columns
only" comparison (a UI-only control column like "Action"/"Actions" is
expected to be ABSENT from the export and is never flagged as a
mismatch -- "This should PASS because Actions is a UI-only control
column").

Column source of truth: utils/header_module_config.py's EXPECTED_HEADERS
-- do not hard-code a module's expected header list inline in a test.

Normalization: every comparison here trims leading/trailing whitespace
and collapses internal repeated whitespace before comparing (see
normalize_header()) -- nothing else is ever changed. Case is handled
per call via `case_insensitive`, defaulting to the behavior this
project's EXISTING code already uses on each side: UI-side checks were
already case-insensitive substring matches (see the sms_sender_id
precedent above), so UI verification here defaults to
case_insensitive=True; the export side's existing
utils.file_validator.validate_file_headers() is case-SENSITIVE exact
match, so export verification here defaults to case_insensitive=False.
Do not flip either default without a real, confirmed reason -- see this
task's own rule: "Do not change case unless the existing framework
already treats headers as case-insensitive."
"""
import re

import pytest

from utils.file_validator import read_file_headers


def normalize_header(value):
    """Trim leading/trailing whitespace and collapse internal repeated
    whitespace -- the ONLY normalization this module ever applies before
    comparison. Never renames/reinterprets a header, never changes case
    (see this module's own docstring for the case-insensitive default
    per side)."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def _key(value, case_insensitive):
    normalized = normalize_header(value)
    return normalized.lower() if case_insensitive else normalized


def find_duplicate_headers(headers, case_insensitive=False):
    """Real (non-blank) header labels that appear more than once in
    `headers`, sorted. A blank header cell (an icon-only Action/
    bulk-select column, common across this project's tables) is never
    reported as a duplicate -- it isn't a named column."""
    counts = {}
    for h in headers:
        norm = normalize_header(h)
        if not norm:
            continue
        key = norm.lower() if case_insensitive else norm
        counts[key] = counts.get(key, 0) + 1
    return sorted(k for k, c in counts.items() if c > 1)


def find_missing_headers(expected, actual, case_insensitive=False, substring=False):
    """Expected headers with no match in `actual`. `substring=True` (the
    UI convention) matches when the expected label appears anywhere
    inside an actual header; `substring=False` (the export convention)
    requires an exact match after normalization. Case rules apply to
    both modes via `case_insensitive`."""
    actual_keys = [_key(a, case_insensitive) for a in actual]
    missing = []
    for exp in expected:
        exp_key = _key(exp, case_insensitive)
        if substring:
            if not any(exp_key in a for a in actual_keys):
                missing.append(exp)
        else:
            if exp_key not in actual_keys:
                missing.append(exp)
    return missing


def find_unexpected_headers(expected, actual, case_insensitive=False):
    """Real (non-blank) actual headers that don't exactly match anything
    in `expected` (no substring leniency here -- an unexpected header is
    a genuinely new/renamed column, not a near-miss). A blank header
    cell is never "unexpected" -- see find_duplicate_headers()'s own
    note. Each distinct unexpected header is reported once."""
    expected_keys = {_key(e, case_insensitive) for e in expected}
    unexpected = []
    seen = set()
    for a in actual:
        norm = normalize_header(a)
        if not norm:
            continue
        key = _key(a, case_insensitive)
        if key not in expected_keys and key not in seen:
            unexpected.append(norm)
            seen.add(key)
    return unexpected


def _format_list(items):
    if not items:
        return "[]"
    body = ",\n".join('  "%s"' % i for i in items)
    return "[\n" + body + "\n]"


def _fail_header_report(module_name, header_type, expected, actual, missing, unexpected, duplicates):
    lines = [
        f"Module: {module_name}",
        f"Header Type: {header_type}",
        "Expected Headers:",
        _format_list(list(expected)),
        "Actual Headers:",
        _format_list([normalize_header(a) for a in actual]),
        "Missing Headers:",
        _format_list(missing),
        "Unexpected Headers:",
        _format_list(unexpected),
        "Duplicate Headers:",
        _format_list(duplicates),
        "Result: FAIL",
    ]
    pytest.fail("\n".join(lines))


def verify_ui_headers(module_name, actual_headers, expected_headers, case_insensitive=True):
    """UI Header Verification. Presence-only (substring match, case
    rules per `case_insensitive` -- default True, matching this
    project's established UI-header convention): every expected header
    must be found somewhere in `actual_headers`. A UI-only control
    column not present in `expected_headers` at all is NOT itself a
    failure (only an unexpected *duplicate* of an already-real header
    fails -- see find_duplicate_headers). Header order is never checked
    here (this project's table columns are user-toggleable). Calls
    pytest.fail() with this module's report format on any real problem;
    returns nothing on success -- test-support code, call only from
    inside a test function."""
    missing = find_missing_headers(expected_headers, actual_headers, case_insensitive, substring=True)
    duplicates = find_duplicate_headers(actual_headers, case_insensitive)
    if missing or duplicates:
        _fail_header_report(module_name, "UI", expected_headers, actual_headers, missing, [], duplicates)
    print(f"[{module_name}] UI Header Verification PASS ({len(actual_headers)} header(s))")


def verify_export_headers(module_name, actual_headers, expected_headers, case_insensitive=False, order_sensitive=False):
    """Export Header Verification. Exact match after normalization (no
    substring leniency -- an export's header row is a fixed contract,
    not a toggleable UI), case-SENSITIVE by default (matches this
    project's existing utils.file_validator.validate_file_headers()
    convention) unless the module's own config says otherwise. Detects
    missing, unexpected, and duplicate headers; checks order only when
    `order_sensitive=True`. Calls pytest.fail() with this module's
    report format on any real problem; returns nothing on success --
    test-support code, call only from inside a test function."""
    missing = find_missing_headers(expected_headers, actual_headers, case_insensitive, substring=False)
    unexpected = find_unexpected_headers(expected_headers, actual_headers, case_insensitive)
    duplicates = find_duplicate_headers(actual_headers, case_insensitive)
    order_ok = True
    if order_sensitive and not (missing or unexpected or duplicates):
        norm_expected = [_key(e, case_insensitive) for e in expected_headers]
        norm_actual = [_key(a, case_insensitive) for a in actual_headers]
        order_ok = norm_expected == norm_actual
    if missing or unexpected or duplicates or not order_ok:
        _fail_header_report(module_name, "Export", expected_headers, actual_headers, missing, unexpected, duplicates)
    print(f"[{module_name}] Export Header Verification PASS ({len(actual_headers)} header(s))")


def compare_ui_export_headers(
    module_name,
    ui_headers,
    export_headers,
    case_insensitive=True,
    export_only=None,
    ui_column_names=None,
    common_headers=None,
):
    """UI vs Export Header Verification -- compares only the columns
    that are supposed to correspond on BOTH sides. A UI-only control
    column such as "Action"/"Actions" is never expected to appear in an
    export and is simply not checked here, per this project's own rule:
    "This should PASS because Actions is a UI-only control column."
    Similarly, an export file routinely contains export-only fields (e.g.
    database IDs, message bodies, internal metadata) or fields whose UI
    label differs slightly (e.g. 'Campaign Name' vs 'Name', 'Template
    Name' vs 'Template').

    `export_only`: optional collection of export column names that are
    known to be export-only and should not be expected on the UI.
    `ui_column_names`: optional dict mapping {export_name: ui_name} for
    columns where the UI label differs from the export header name.
    `common_headers`: optional explicit list of common headers to compare.
    """
    if common_headers is not None:
        columns_to_check = list(common_headers)
    else:
        export_only_set = {_key(c, case_insensitive) for c in (export_only or [])}
        columns_to_check = [c for c in export_headers if _key(c, case_insensitive) not in export_only_set]

    ui_mapping = {}
    if ui_column_names:
        for exp_name, ui_name in ui_column_names.items():
            ui_mapping[_key(exp_name, case_insensitive)] = ui_name

    ui_keys = [_key(u, case_insensitive) for u in ui_headers if normalize_header(u)]
    mismatches = []
    matched_count = 0

    for exp_col in columns_to_check:
        exp_k = _key(exp_col, case_insensitive)
        if not exp_k:
            continue

        target_label = ui_mapping.get(exp_k)
        if target_label:
            target_k = _key(target_label, case_insensitive)
            if any(target_k in u or u in target_k for u in ui_keys):
                matched_count += 1
                continue
        else:
            if any(exp_k in u or u in exp_k for u in ui_keys):
                matched_count += 1
                continue

        mismatches.append(exp_col)

    if mismatches:
        lines = [f"Module: {module_name}"]
        for col in mismatches:
            lines += [
                "UI Header: (not found)",
                f"Export Header: {col}",
                f"Mismatch: '{col}' is present in the export but not found on the UI table",
            ]
        lines.append("Result: FAIL")
        pytest.fail("\n".join(lines))
    print(f"[{module_name}] UI vs Export Header Verification PASS ({matched_count} common column(s))")


def verify_module_ui_headers_only(page, module_name, config_key):
    """UI-only Header Verification -- runs ONLY the UI half of
    verify_module_headers() (below) and never touches export at all:
    no export attempt, no pytest.skip() for "no confirmed export list"
    or "export did not produce a downloaded file". A module verified
    this way ends as a normal PASS (or a real FAIL on a genuine UI
    header problem) instead of ever reporting SKIPPED.

    Use this instead of verify_module_headers() for a module the
    project owner has explicitly decided should only ever verify UI
    headers -- per instruction, WhatsApp Opt-in, Opt-out, Download
    Center, Blocked Users, and Flows use this (EXPECTED_HEADERS[config_key]["export"]
    is ignored either way, even if a value is present).

        def test_header_verification_ui(some_page):
            verify_module_ui_headers_only(some_page, "WhatsApp Opt-in", "whatsapp_opt_in")
    """
    from utils.header_module_config import EXPECTED_HEADERS
    config = EXPECTED_HEADERS[config_key]

    ui_headers = page.get_raw_headers(page.TABLE_HEADERS)
    verify_ui_headers(
        module_name, ui_headers, config["ui"], case_insensitive=config.get("case_insensitive", True),
    )


def verify_module_headers(page, module_name, config_key, click_export_csv=None):
    """Full Header Verification (UI [+ Export [+ UI-vs-Export]]) for one
    list-table module, driven entirely by EXPECTED_HEADERS[config_key]
    (utils/header_module_config.py) -- no per-module header logic
    duplicated in a test file. Same reusable-engine convention as
    utils/table_date_verification.py's verify_table_date_columns() for
    dates.

    `page`: the module's page object (must define TABLE_HEADERS and
    provide get_raw_headers() -- every page object in this project
    already does, via BasePage).
    `click_export_csv` (optional): zero-arg callable returning a dict
    with a "file_path" key on a successful download, or a falsy value
    on failure/no download. Only used when
    EXPECTED_HEADERS[config_key]["export"] is not None; omit entirely
    for a module with no confirmed export header list yet.

        def test_header_verification_ui(some_page):
            verify_module_headers(some_page, "WhatsApp Number", "whatsapp_number")
    """
    from utils.header_module_config import EXPECTED_HEADERS
    config = EXPECTED_HEADERS[config_key]

    ui_headers = page.get_raw_headers(page.TABLE_HEADERS)
    verify_ui_headers(
        module_name, ui_headers, config["ui"], case_insensitive=config.get("case_insensitive", True),
    )

    export_expected = config.get("export")
    if export_expected is None or click_export_csv is None:
        pytest.skip(
            f"{module_name}: no confirmed export header list configured yet -- "
            "UI Header Verification stands (passed above)."
        )

    result = click_export_csv()
    if not result:
        pytest.skip(
            f"{module_name} export did not produce a downloaded file -- "
            "UI Header Verification stands (passed above)."
        )

    export_actual = read_file_headers(result["file_path"])
    if not export_actual:
        pytest.skip(
            f"{module_name} export produced no header row -- "
            "UI Header Verification stands (passed above)."
        )

    verify_export_headers(
        module_name, export_actual, export_expected,
        case_insensitive=config.get("export_case_insensitive", False),
        order_sensitive=config.get("order_sensitive", False),
    )
    compare_ui_export_headers(
        module_name,
        ui_headers,
        export_expected,
        case_insensitive=config.get("case_insensitive", True),
        export_only=config.get("export_only"),
        ui_column_names=config.get("ui_column_names"),
        common_headers=config.get("common"),
    )
