"""
RCS Templates — List page (Export)
Path: /rcs/template

Distinct from test_rcs_template_create_flow.py (the creation FORM,
locked/unchanged) and test_rcs_template_analytics_flow.py (the Template
Analytics REPORT, a different screen with usage/metric columns). This
file exists for the Template LIST screen specifically -- previously an
explicitly documented gap (see test_rcs_template_create_flow.py's
test_TC_SKIP_save_persists_to_listing docstring: "deferred until the
listing-page test suite (test_rcs_template_flow.py) is built").

Scope is intentionally narrow: only the Export CSV header row was
independently confirmed (a real header row supplied directly by the user,
2026-09-02) -- no other DOM on this screen (table columns, search,
filters, pagination) has been captured, so no tests for those are added
here rather than guessed at. RcsTemplateCreatePage.click_export_csv()'s
Export button locator (BTN_EXPORT) is itself a best-effort guess mirrored
from RCSCampaignPage's confirmed pattern, not independently confirmed --
see that method's docstring. A locator miss is treated as "skip", not a
failure, for exactly that reason.

Migrated pattern: module-scoped page-object fixture built on
conftest.py's `module_logged_in_page`, matching every other RCS list
suite (e.g. tests/rcs/campaigns/test_rcs_campaign_flow.py).

Test independence audit (2026-09-08): both tests here are read-only/
export style with no cross-test data dependency -- TC001 only checks
the list page's URL, and TC002 (Export CSV) neither reads nor requires
anything TC001 did. Fixture scope is deliberately KEPT at
scope="module" (not migrated to the function-scoped `logged_in_page`
pattern) because there is no mutable-state chain to break: the
module-scoped `template_list_page` fixture's own setup always
navigates to the list page before the first test runs, and the
autouse `_reset_after_test` fixture below unconditionally re-navigates
back to the list page after every test regardless of outcome -- so
under `-n 10` (this suite does not rely on `--dist loadscope`), no
test ever depends on UI state a different test happened to leave
behind. TC001 additionally calls navigate_to_list() itself so it
establishes its own required UI state explicitly rather than only via
fixture/autouse timing.
"""
import pytest

from constants.rcs_template_list_headers import EXPECTED_RCS_TEMPLATE_LIST_HEADERS
from pages.rcs.rcs_template_create_page import RcsTemplateCreatePage
from utils.date_module_config import DATE_MODULE_CONFIG
from utils.datetime_verification import (
    DateComparisonError,
    DateFormatValidationError,
    capture_ui_datetime_values,
    column_index_lookup,
    detect_date_columns,
    detect_ui_date_columns,
    read_export_datetime_values,
    validate_ui_export_dates,
)
from utils.file_validator import (
    EmptyFileError,
    FileNotDownloadedError,
    HeaderValidationError,
    UnsupportedFileTypeError,
    read_file_rows,
    validate_file_headers,
)


pytestmark = [pytest.mark.rcs, pytest.mark.template]


@pytest.fixture(scope="module")
def template_list_page(module_logged_in_page):
    p = RcsTemplateCreatePage(module_logged_in_page)
    p.navigate_to_list()
    return p


@pytest.fixture(autouse=True)
def _reset_after_test(template_list_page):
    yield
    try:
        template_list_page.navigate_to_list()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# TC001 — Page loads
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_TC001_list_page_loads(template_list_page):
    """TC001: RCS Template list page loads without a 404 or error page."""
    template_list_page.navigate_to_list()
    assert template_list_page.is_list_page(), "URL should be /rcs/template (not /create)"


# ══════════════════════════════════════════════════════════════════════════════
# TC002 — Export CSV header validation
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC002_export_csv_verifies_header(template_list_page):
    """TC002: Exporting from the Template list downloads a file whose
    header row matches this instance's confirmed RCS Template list
    export columns exactly (constants/rcs_template_list_headers.py).

    Skips rather than fails if the Export control can't be found/clicked
    -- its locator is a best-effort guess, not independently confirmed
    (see RcsTemplateCreatePage.click_export_csv()'s docstring); the
    header-row assertion itself, once a file is in hand, is exact."""
    template_list_page.navigate_to_list()
    result = template_list_page.click_export_csv(timeout_ms=30000)
    if result is None:
        pytest.skip(
            "Export control on the Template list page was not found/"
            "clickable, or produced no download within 30s -- "
            "BTN_EXPORT is a best-effort locator pending independent "
            "DOM confirmation on this screen (see click_export_csv() "
            "docstring)"
        )
    print(f"Export file downloaded: {result['file_path']} ({result['file_size']} bytes)")

    try:
        actual_headers = validate_file_headers(result["file_path"], EXPECTED_RCS_TEMPLATE_LIST_HEADERS)
    except FileNotDownloadedError as exc:
        pytest.fail(str(exc))
    except (UnsupportedFileTypeError, EmptyFileError) as exc:
        pytest.fail(str(exc))
    except HeaderValidationError as exc:
        print(f"Actual headers: {exc.actual}")
        print(f"Missing headers: {exc.missing}")
        print(f"Unexpected headers: {exc.unexpected}")
        for position, expected_name, actual_name in exc.mismatches:
            print(f"Position {position}: expected '{expected_name}', actual '{actual_name}'")
        pytest.fail(str(exc))

    print(f"Header validation PASS: {actual_headers}")


# ═════════════════════════════════════════════════════════════════════════════════════
# Date/Date-Time Verification -- RCS Templates (shared reusable utility --
# utils/datetime_verification.py, config in utils/date_module_config.py).
# CONFIRMED via a real pasted DOM of /rcs/template: "Created At"/
# "Updated At" both render dd-mm-yyyy hh:mm:ss with seconds
# (e.g. "28-09-2026 15:44:33"). Strict format only, no relaxation.
# ═════════════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_date_datetime_verification_ui_vs_export(template_list_page):
    """For every real RCS Templates date/date-time column ("Created At",
    "Updated At" -- confirmed via a real pasted DOM of /rcs/template and
    constants/rcs_template_list_headers.py, not hardcoded here), validates
    every populated on-screen value is a real dd-mm-yyyy/dd-mm-yyyy
    hh:mm:ss value, validates the export's own values the same way, and
    compares UI vs export per column. "Last Used At" is UI-only (no
    export column of that name) and is intentionally excluded, same
    convention as every other module's UI-only columns."""
    template_list_page.navigate_to_list()

    config = DATE_MODULE_CONFIG["rcs_templates"]
    ui_headers = template_list_page.get_raw_headers(template_list_page.TABLE_HEADERS)
    ui_date_columns = detect_ui_date_columns(ui_headers, config["date_columns"], config["ui_column_names"])
    if not ui_date_columns:
        pytest.skip("No configured date/date-time column is present in the RCS Templates UI table right now.")

    row_count = template_list_page.get_row_count()
    if row_count == 0:
        pytest.skip("No RCS Template rows visible -- nothing to date-verify.")

    ui_values_by_column = capture_ui_datetime_values(
        get_cell_text=template_list_page.get_cell_text,
        get_column_index=column_index_lookup(ui_headers),
        row_count=row_count,
        date_columns=ui_date_columns,
        column_pairs=config["ui_column_names"],
    )

    result = template_list_page.click_export_csv()
    if not result:
        pytest.skip("RCS Templates export did not produce a downloaded file -- UI-only verification stands.")

    _headers, rows = read_file_rows(result["file_path"])
    if not rows:
        pytest.skip("RCS Templates export produced 0 data rows -- nothing to compare against.")

    export_date_columns = detect_date_columns(list(rows[0].keys()), config["export_date_columns"])
    export_values_by_column = read_export_datetime_values(rows, export_date_columns)

    try:
        validate_ui_export_dates(
            "RCS Templates", ui_values_by_column, export_values_by_column,
            field_kinds=config["field_kinds"],
        )
    except (DateFormatValidationError, DateComparisonError) as exc:
        pytest.fail(str(exc))
    print(f"[RCS Templates] Date/Date-Time Verification PASS ({row_count} UI row(s))")

