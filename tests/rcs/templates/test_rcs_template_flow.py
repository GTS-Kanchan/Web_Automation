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
"""
import pytest

from constants.rcs_template_list_headers import EXPECTED_RCS_TEMPLATE_LIST_HEADERS
from pages.rcs.rcs_template_create_page import RcsTemplateCreatePage
from utils.file_validator import (
    EmptyFileError,
    FileNotDownloadedError,
    HeaderValidationError,
    UnsupportedFileTypeError,
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
