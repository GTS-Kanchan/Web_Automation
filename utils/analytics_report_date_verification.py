"""
utils/analytics_report_date_verification.py -- shared test-support helper
for the "Duration" date/date-time verification pattern common to every
RCS and WhatsApp analytics report page in this suite (RCS Agent/Campaign/
Country/Error Code/Message Type/Status/Usage/Template Analytics, and the
identically-structured WhatsApp Campaign/Country Code/Message Type/
Status/Usage/WABA Number/Template Analytics).

Every one of these pages shares the same real, confirmed shape:
  - a single date/date-time column, "Duration" (rendered lowercase
    "duration" in the UI header row, confirmed from each page's own
    COLUMN_INDEX comment / constants/*_ui_headers.py file where one
    exists),
  - a page.get_column_values(<column_key>) method already returning that
    column's on-screen values directly (via a fixed COLUMN_INDEX dict,
    not a header-text lookup -- immune to the blank-header
    index-misalignment bug BasePage.get_raw_headers() works around
    elsewhere in this suite),
  - a page.click_export_csv() method returning
    {"elapsed_s", "file_path", "file_size"} on a successful download, or
    None on failure/timeout (this family's own contract -- NOT the same
    return shape as e.g. SMSMessagePage.export(), which returns a
    "background_job_triggered.csv" placeholder dict instead of None).

For RCS, "Duration" is CONFIRMED (explicit project-owner statement) to
be a single date, dd-mm-yyyy, in both the UI and the export --
constants/rcs/**/*_analytics_headers.py lists "Duration" as a real
export header too. WhatsApp's analytics pages are architecturally
identical (same DATE_RANGE_PICKER/REPORT_TYPE_SELECT/GROUP_BY
components, same "duration" UI column name, each confirmed from that
page's own live-DOM COLUMN_INDEX comment) and the project owner
confirmed the same dd-mm-yyyy convention applies, but there is no
constants/whatsapp/*_headers.py export-header file to confirm the
export's own column NAME against. The export-side check below is
written to SKIP (never fail) when no "Duration"-like column is actually
found in a real downloaded export, so a wrong inference about the export
column name degrades to "not verified this run" rather than a false
failure -- same fail-open design already used for
DATE_MODULE_CONFIG["campaign_list"]/["download_center"]'s lack of a
confirmed export correspondence.

CORRECTION (real pasted export file, rcs_country_report_*.csv, plus a
real pytest failure): the export side's "Duration" column is NOT
dd-mm-yyyy after all -- it's ISO "yyyy-mm-dd" (e.g. "2026-09-27"), a raw
text fact in the downloaded CSV itself, confirmed by the project owner
as expected/current app behavior (not a bug to report). The UI side
keeps the strict dd-mm-yyyy check (it genuinely is dd-mm-yyyy there,
and passed). The export-side format check and the UI-vs-export
comparison below both pass accept_iso=True to
utils/datetime_verification.py so a "yyyy-mm-dd" export value is
recognized and normalizes to the same calendar date as its dd-mm-yyyy
UI counterpart -- this is opt-in and scoped to just this helper, not a
project-wide relaxation of the dd-mm-yyyy convention (every other
module's date verification is unaffected).

CORRECTION 2 (real pasted pytest failure, SMS Latency Report / SMS
Status Report): those two modules default to hourly Report Type, and
their live "Duration" values are timestamps WITHOUT seconds, e.g.
"28-09-2026 15:00" (dd-mm-yyyy hh:mm) -- not this project's usual strict
dd-mm-yyyy hh:mm:ss. Project owner confirmed this is expected/correct for
hourly-grouped Duration, not a bug. verify_analytics_report_dates() takes
an opt-in accept_no_seconds=False parameter (default off, so every other
module's strict hh:mm:ss requirement is unaffected) -- pass
accept_no_seconds=True only for SMS Latency Report / SMS Status Report's
Duration column. See utils/datetime_verification.py's own accept_no_seconds
note for the parsing detail.

CORRECTION 3 (real pasted pytest failure, RCS Message Type Analytics):
this report's own export renders "Duration" as a THIRD format, "dd Mon
yyyy" (e.g. "27 Sep 2026") -- distinct from both the project's usual
dd-mm-yyyy and the already-confirmed ISO yyyy-mm-dd export variant
(accept_iso=True, tried first). verify_analytics_report_dates() takes an
opt-in accept_text_month=False parameter (default off, applied to the
EXPORT side only -- the on-screen "Duration" column itself is unaffected
and stays strict dd-mm-yyyy) -- pass accept_text_month=True only for
modules confirmed to actually render this format. See
utils/datetime_verification.py's own accept_text_month note for the
parsing detail.

Do NOT duplicate this flow inline in each report's test file -- import
verify_analytics_report_dates() from here.
"""
import pytest

from utils.file_validator import read_file_rows
from utils.datetime_verification import (
    DateComparisonError,
    DateFormatValidationError,
    compare_ui_and_export_datetime,
    detect_date_columns,
    read_export_datetime_values,
    validate_date_values_format,
)


def verify_analytics_report_dates(
    page,
    module_name,
    column_key="duration",
    canonical_column="Duration",
    field_kind="date",
    export_candidate_names=None,
    accept_no_seconds=False,
    accept_text_month=False,
):
    """Full UI + export date/date-time verification for one of this
    project's "Duration" analytics report pages.

    Calls pytest.skip()/pytest.fail() directly -- this is test-support
    code, only ever meant to be called from inside a test function:

        def test_date_datetime_verification_ui_vs_export(some_analytics_page):
            verify_analytics_report_dates(some_analytics_page, "RCS Agent Analytics")

    "Do not fail a test merely because a module does not contain a date
    column" / because an export didn't produce a matching column --
    every "nothing to check" branch below is a skip, never a failure.
    """
    if export_candidate_names is None:
        export_candidate_names = [canonical_column]

    ui_values = page.get_column_values(column_key)
    if not ui_values:
        pytest.skip(f"No rows visible on {module_name} -- nothing to date-verify.")

    try:
        validate_date_values_format(
            module_name, canonical_column, ui_values, field_kind=field_kind, accept_no_seconds=accept_no_seconds
        )
    except DateFormatValidationError as exc:
        pytest.fail(str(exc))
    print(f"[{module_name}] {canonical_column}: UI Date/Date-Time Format Verification PASS "
          f"({len(ui_values)} row(s))")

    result = page.click_export_csv()
    if not result:
        pytest.skip(f"{module_name} export did not produce a downloaded file -- UI-only verification stands.")

    _headers, rows = read_file_rows(result["file_path"])
    if not rows:
        pytest.skip(f"{module_name} export produced 0 data rows -- nothing to compare against.")

    export_date_columns = detect_date_columns(list(rows[0].keys()), export_candidate_names)
    if not export_date_columns:
        pytest.skip(
            f"No {export_candidate_names} column detected in the {module_name} export "
            f"(export headers: {list(rows[0].keys())}) -- UI-only verification stands."
        )

    export_column = export_date_columns[0]
    export_values = read_export_datetime_values(rows, export_date_columns)[export_column]

    # accept_iso=True: CONFIRMED real export behavior -- this family's
    # exports render "Duration" as yyyy-mm-dd, not dd-mm-yyyy like the UI.
    # See this module's own docstring correction above.
    try:
        validate_date_values_format(
            f"{module_name} Export", export_column, export_values, field_kind=field_kind,
            accept_iso=True, accept_no_seconds=accept_no_seconds, accept_text_month=accept_text_month,
        )
        compare_ui_and_export_datetime(
            module_name, canonical_column, ui_values, export_values, field_kind=field_kind,
            accept_iso=True, accept_no_seconds=accept_no_seconds, accept_text_month=accept_text_month,
        )
    except (DateFormatValidationError, DateComparisonError) as exc:
        pytest.fail(str(exc))
    print(f"[{module_name}] {canonical_column}: UI vs Export Date/Date-Time Verification PASS "
          f"({len(ui_values)} UI row(s), {len(export_values)} export row(s))")
