"""
utils/table_date_verification.py -- shared test-support helper for the
"standard list-table" Date/Date-Time Verification flow used across this
project's SMS/RCS/WhatsApp modules: a table whose date/date-time columns
are declared once in utils/date_module_config.py's DATE_MODULE_CONFIG,
read via BasePage's own generic get_raw_headers()/get_cell_text()/
get_column_index() (every page object in this project already has these
for free -- no per-page date-specific code required), and validated via
utils/datetime_verification.py.

Do NOT duplicate this flow inline in each module's test file -- import
verify_table_date_columns() from here, same convention as
utils/analytics_report_date_verification.py's verify_analytics_report_dates()
for the "Duration" analytics-report family.
"""
import pytest

from utils.file_validator import read_file_rows
from utils.date_module_config import DATE_MODULE_CONFIG
from utils.datetime_verification import (
    DateComparisonError,
    DateFormatValidationError,
    capture_ui_datetime_values,
    column_index_lookup,
    detect_date_columns,
    detect_ui_date_columns,
    read_export_datetime_values,
    validate_date_values_format,
    validate_ui_export_dates,
)


def verify_table_date_columns(page, module_name, config_key, click_export_csv=None):
    """Full Date/Date-Time Verification for one list-table module.

    `page`: the module's page object (must define TABLE_HEADERS and
    provide get_row_count()/get_raw_headers()/get_cell_text()/
    get_column_index() -- every page object in this project already
    does, via BasePage).
    `module_name`: human-readable label used in skip/fail messages.
    `config_key`: this module's key in DATE_MODULE_CONFIG.
    `click_export_csv` (optional): zero-arg callable returning a dict
    with a "file_path" key on a successful download, or a falsy value
    on failure/no download. Only used when
    DATE_MODULE_CONFIG[config_key]["export_date_columns"] is not None;
    omit entirely for a UI-only module (export_date_columns is None).

    Calls pytest.skip()/pytest.fail() directly -- test-support code,
    only ever meant to be called from inside a test function:

        def test_date_datetime_verification_ui_format(some_page):
            verify_table_date_columns(some_page, "WhatsApp Number", "whatsapp_number")
    """
    config = DATE_MODULE_CONFIG[config_key]
    ui_headers = page.get_raw_headers(page.TABLE_HEADERS)
    ui_date_columns = detect_ui_date_columns(ui_headers, config["date_columns"], config["ui_column_names"])
    if not ui_date_columns:
        pytest.skip(f"No configured date/date-time column is present in the {module_name} UI table right now.")

    row_count = page.get_row_count()
    if row_count == 0:
        pytest.skip(f"No {module_name} rows visible -- nothing to date-verify.")

    ui_values_by_column = capture_ui_datetime_values(
        get_cell_text=page.get_cell_text,
        get_column_index=column_index_lookup(ui_headers),
        row_count=row_count,
        date_columns=ui_date_columns,
        column_pairs=config["ui_column_names"],
    )

    def _ui_only():
        for column, values in ui_values_by_column.items():
            field_kind = config["field_kinds"].get(column, "auto")
            try:
                validate_date_values_format(module_name, column, values, field_kind=field_kind)
            except DateFormatValidationError as exc:
                pytest.fail(str(exc))
        print(f"[{module_name}] UI Date/Date-Time Format Verification PASS ({row_count} row(s))")

    if config["export_date_columns"] is None or click_export_csv is None:
        _ui_only()
        return

    result = click_export_csv()
    if not result:
        _ui_only()
        pytest.skip(f"{module_name} export did not produce a downloaded file -- UI-only verification stands (passed above).")

    _headers, rows = read_file_rows(result["file_path"])
    if not rows:
        _ui_only()
        pytest.skip(f"{module_name} export produced 0 data rows -- nothing to compare against (UI-only verification stands, passed above).")

    export_date_columns = detect_date_columns(list(rows[0].keys()), config["export_date_columns"])
    if not export_date_columns:
        _ui_only()
        pytest.skip(
            f"No configured date column detected in the {module_name} export "
            f"(export headers: {list(rows[0].keys())}) -- UI-only verification stands (passed above)."
        )

    export_values_by_column = read_export_datetime_values(rows, export_date_columns)

    try:
        validate_ui_export_dates(
            module_name, ui_values_by_column, export_values_by_column, field_kinds=config["field_kinds"],
        )
    except (DateFormatValidationError, DateComparisonError) as exc:
        pytest.fail(str(exc))
    print(f"[{module_name}] UI vs Export Date/Date-Time Verification PASS ({row_count} UI row(s))")
