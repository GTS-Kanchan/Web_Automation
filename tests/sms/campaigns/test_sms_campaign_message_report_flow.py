"""
SMS Campaign Message Report page — Automated Test Suite
Path: /campaigns/messages/<metric>/<campaignUuid>

Covers the per-campaign SMS report page's 9 stat cards (7 clickable, 2
non-clickable) and the exact table-header contract for each clickable
card's resulting table, per the task specification supplied for this
suite. This is NOT the same page as
tests/sms/reports/test_sms_campaign_report_flow.py (that one covers the
AGGREGATE report listing every campaign, at /channels/sms/reports/
campaign, with a per-row "Campaign Status Details" modal).

Built from real, pasted DOM captures -- never fabricated: the SMS
Campaign listing page's row "Reports" icon
(data-tooltip-target="tooltip-reports-<id>"), the report page's own 9
stat cards markup (onclick="window.location='.../campaigns/messages/
<metric>/<uuid>'" for the 7 clickable cards; no onclick at all for
Delivery Rate / Unique Clicks), and the message table's <thead> for the
default "total" metric. See
pages/sms/sms_campaign_message_report_page.py's module docstring for
every confirmed DOM detail driving the locators/methods used here.

Test Design Notes:
  - scope="module" -- the page is reached ONCE per module by navigating
    the SMS Campaign listing page and clicking the Reports icon on its
    first row (there is no campaign-agnostic URL -- the campaign id, a
    UUID, is part of the path). ensure_on_report_page() recovers to the
    SAME campaign's report page (via the cached campaign id) if a test
    navigates away.
  - TC03-TC09 (data-driven card + expected-header coverage) use
    pytest.mark.parametrize over CLICKABLE_REPORT_CARDS rather than one
    duplicated test method per card, per the task's explicit instruction.
  - Non-clickable cards (Delivery Rate, Unique Clicks) are verified
    STRUCTURALLY (no onclick handler present) rather than via a CSS
    class -- see the page object docstring for why. Clicking them is
    asserted to change neither the URL nor the table headers.
  - Each metric's table renders a different header set (confirmed by the
    task's own specification, e.g. Rejected has only 3 columns); the
    page object's verify_table_headers() strips a leading "Action"
    column before comparing, since every captured table -- independently
    of which metric -- renders that extra, non-data column first.
  - Each card dict in CLICKABLE_REPORT_CARDS carries TWO separate
    expected-header lists, deliberately NOT shared:
      * "headers" -- the ON-SCREEN table headers used by TC03-09.
        CONFIRMED rendered in UPPERCASE (e.g. "CONTACT", "STATUS") --
        almost certainly a CSS text-transform rather than the real
        underlying header text, but Playwright's inner_text() (used by
        get_visible_column_headers()) returns rendered text, so the
        comparison must use the same UPPERCASE strings actually seen on
        screen.
      * "export_headers" -- the DOWNLOADED FILE headers used by TC12, in
        Title Case (e.g. "Contact", "Status") -- CONFIRMED per-metric
        directly from a real exported file's header rows (a
        server-generated export does not apply the live page's CSS
        uppercase transform, exactly as expected): total/submitted/
        delivered/failed all share the same 7 columns ending in "DLR
        Received At"; DLR Awaited omits that trailing column (6 total);
        Rejected has only 3 (Contact, Status, Received At); Total Clicks
        has its own distinct 6-column set.
  - TC12 (export-per-card header validation) reuses the project's
    existing generic utils/file_validator.validate_file_headers() -- the
    SAME validator already used by
    tests/sms/reports/test_sms_campaign_report_flow.py -- rather than any
    new CSV-reading logic. Unlike TC03-09, this does NOT strip a leading
    "Action" column, since an exported file (no interactive buttons) is
    not confirmed to carry that column the way the on-screen table does.
    The Export CSV control's locator
    (SmsCampaignMessageReportPage.EXPORT_CSV_LINK) IS now confirmed from
    a real DOM paste: a plain <a> anchor (not a <button>), href shape
    ".../campaigns/messages/<campaign_uuid>/export?table=<TableName>" --
    see that constant's docstring for the full detail.

Run:
    pytest tests/sms/campaigns/test_sms_campaign_message_report_flow.py -v
"""
import pytest

from pages.sms.sms_campaign_page import SMSCampaignPage
from pages.sms.sms_campaign_message_report_page import SmsCampaignMessageReportPage
from utils.file_validator import (
    EmptyFileError,
    FileNotDownloadedError,
    HeaderValidationError,
    UnsupportedFileTypeError,
    validate_file_headers,
)


pytestmark = [pytest.mark.sms, pytest.mark.campaign, pytest.mark.report]

# ══════════════════════════════════════════════════════════════════════════════
# Data-driven card + expected-header spec
# ══════════════════════════════════════════════════════════════════════════════

CLICKABLE_REPORT_CARDS = [
    {
        "name": "Total Messages",
        "headers": [
            "CONTACT",
            "STATUS",
            "STATUS DESCRIPTION",
            "SMS UNITS",
            "RECEIVED AT",
            "SUBMITTED AT",
            "DLR RECEIVED AT",
        ],
        "export_headers": [
            "Contact",
            "Status",
            "Status Description",
            "SMS Units",
            "Received At",
            "Submitted At",
            "DLR Received At",
        ],
    },
    {
        "name": "Submitted",
        "headers": [
            "CONTACT",
            "STATUS",
            "STATUS DESCRIPTION",
            "SMS UNITS",
            "RECEIVED AT",
            "SUBMITTED AT",
            "DLR RECEIVED AT",
        ],
        "export_headers": [
            "Contact",
            "Status",
            "Status Description",
            "SMS Units",
            "Received At",
            "Submitted At",
            "DLR Received At",
        ],
    },
    {
        "name": "Delivered",
        "headers": [
            "CONTACT",
            "STATUS",
            "STATUS DESCRIPTION",
            "SMS UNITS",
            "RECEIVED AT",
            "SUBMITTED AT",
            "DLR RECEIVED AT",
        ],
        "export_headers": [
            "Contact",
            "Status",
            "Status Description",
            "SMS Units",
            "Received At",
            "Submitted At",
            "DLR Received At",
        ],
    },
    {
        "name": "DLR Awaited",
        "headers": [
            "CONTACT",
            "STATUS",
            "STATUS DESCRIPTION",
            "SMS UNITS",
            "RECEIVED AT",
            "SUBMITTED AT",
        ],
        "export_headers": [
            "Contact",
            "Status",
            "Status Description",
            "SMS Units",
            "Received At",
            "Submitted At",
        ],
    },
    {
        "name": "Failed",
        "headers": [
            "CONTACT",
            "STATUS",
            "STATUS DESCRIPTION",
            "SMS UNITS",
            "RECEIVED AT",
            "SUBMITTED AT",
            "DLR RECEIVED AT",
        ],
        "export_headers": [
            "Contact",
            "Status",
            "Status Description",
            "SMS Units",
            "Received At",
            "Submitted At",
            "DLR Received At",
        ],
    },
    {
        "name": "Rejected",
        "headers": [
            "CONTACT",
            "STATUS",
            "RECEIVED AT",
        ],
        "export_headers": [
            "Contact",
            "Status",
            "Received At",
        ],
    },
    {
        "name": "Total Clicks",
        "headers": [
            "CONTACT",
            "STATUS",
            "CLICKED URL",
            "CLICKED AT",
            "BROWSER / DEVICE / OS",
            "GEO LOCATION / IP",
        ],
        "export_headers": [
            "Contact",
            "Status",
            "Clicked URL",
            "Clicked At",
            "Browser / Device / OS",
            "Geo Location / IP",
        ],
    },
]

NON_CLICKABLE_CARDS = ["Delivery Rate", "Unique Clicks"]

ALL_CARD_NAMES = [c["name"] for c in CLICKABLE_REPORT_CARDS] + NON_CLICKABLE_CARDS


# ══════════════════════════════════════════════════════════════════════════════
# Module-scoped page
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def report_page(module_logged_in_page):
    listing = SMSCampaignPage(module_logged_in_page)
    listing.open_campaign_list()
    navigated = listing.click_reports_link_on_first_row()
    assert navigated, (
        "Could not open an SMS Campaign message report page from the "
        "listing page's first row -- no data row, or no Reports icon "
        "(data-tooltip-target='tooltip-reports-<id>') on it"
    )

    p = SmsCampaignMessageReportPage(module_logged_in_page)
    p.wait_for_table_load(timeout=15000)
    cid = p.remember_campaign_id()
    assert cid, "Could not determine the campaign id (UUID) from the report page URL"
    return p


def ensure_on_report_page(p: SmsCampaignMessageReportPage):
    if not p.is_report_page():
        cid = getattr(p, "_campaign_id", None) or p.get_campaign_id_from_url()
        assert cid, "Lost track of the campaign id -- cannot recover to the report page"
        p.navigate_to_campaign(cid, metric="total")
        p.wait_for_table_load(timeout=10000)


@pytest.fixture(autouse=True)
def _reset_after_test(report_page):
    """Reset to the default 'total' metric after every test so card
    selection/table state from one test never bleeds into the next --
    same rationale as every other module-scoped report suite in this
    project (e.g. tests/sms/reports/test_sms_campaign_report_flow.py)."""
    yield
    try:
        cid = getattr(report_page, "_campaign_id", None) or report_page.get_campaign_id_from_url()
        if cid:
            report_page.navigate_to_campaign(cid, metric="total")
            report_page.wait_for_table_load(timeout=10000)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# TC01 — Page loads
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
def test_TC01_report_page_loads(report_page):
    """TC01: SMS Campaign message report page loads successfully."""
    ensure_on_report_page(report_page)
    assert report_page.is_report_page()
    title = report_page.get_title().lower()
    assert "404" not in title and "error" not in title


# ══════════════════════════════════════════════════════════════════════════════
# TC02 — All 9 report cards visible
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.smoke
@pytest.mark.parametrize("card_name", ALL_CARD_NAMES, ids=lambda n: n.replace(" ", "_"))
def test_TC02_report_card_visible(report_page, card_name):
    """TC02: Each of the 9 report cards is visible."""
    ensure_on_report_page(report_page)
    assert report_page.is_card_visible(card_name), f"Expected card {card_name!r} to be visible"


# ══════════════════════════════════════════════════════════════════════════════
# TC03-TC09 — Clickable cards: visible, clickable, click -> exact headers
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
@pytest.mark.parametrize(
    "card",
    CLICKABLE_REPORT_CARDS,
    ids=lambda card: card["name"].replace(" ", "_"),
)
def test_click_report_card_and_verify_headers(report_page, card):
    """TC03-TC09: each clickable card is visible, is confirmed clickable
    (has a real onclick handler), navigating via it loads that metric's
    report, and the resulting table's headers exactly match the card's
    own expected header list (a leading 'Action' column is excluded from
    the comparison -- see page object docstring point 3)."""
    ensure_on_report_page(report_page)

    assert report_page.is_card_visible(card["name"]), f"Expected card {card['name']!r} to be visible"
    assert report_page.is_card_clickable(card["name"]), f"Expected card {card['name']!r} to be clickable"

    report_page.click_report_card(card["name"])
    report_page.wait_for_table_load(timeout=15000)

    expected_metric = SmsCampaignMessageReportPage.CARD_NAME_TO_METRIC[card["name"]]
    actual_metric = report_page.get_active_metric_from_url()
    assert actual_metric == expected_metric, (
        f"Expected URL metric segment {expected_metric!r} after clicking "
        f"{card['name']!r}, got {actual_metric!r} (url: {report_page.get_current_url()!r})"
    )

    actual_headers = report_page.get_visible_column_headers()
    assert report_page.verify_table_headers(card["headers"]), (
        f"Table headers for {card['name']!r} did not match expected. "
        f"Expected (leading 'Action' column excluded): {card['headers']!r}. "
        f"Actual headers: {actual_headers!r}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# TC10 — Delivery Rate: not clickable
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC10_delivery_rate_not_clickable(report_page):
    """TC10: Delivery Rate card is visible, is NOT treated as clickable
    (no onclick handler present), and clicking it changes neither the
    URL nor the table headers."""
    ensure_on_report_page(report_page)
    name = "Delivery Rate"
    assert report_page.is_card_visible(name), f"Expected card {name!r} to be visible"
    assert not report_page.is_card_clickable(name), f"Expected card {name!r} to NOT be clickable"

    url_before, url_after, headers_before, headers_after = report_page.click_non_clickable_card(name)
    assert url_after == url_before, "Clicking Delivery Rate must not navigate to another report"
    assert headers_after == headers_before, "Clicking Delivery Rate must not change the table"


# ══════════════════════════════════════════════════════════════════════════════
# TC11 — Unique Clicks: not clickable
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC11_unique_clicks_not_clickable(report_page):
    """TC11: Unique Clicks card is visible, is NOT treated as clickable
    (no onclick handler present), and clicking it changes neither the
    URL nor the table headers."""
    ensure_on_report_page(report_page)
    name = "Unique Clicks"
    assert report_page.is_card_visible(name), f"Expected card {name!r} to be visible"
    assert not report_page.is_card_clickable(name), f"Expected card {name!r} to NOT be clickable"

    url_before, url_after, headers_before, headers_after = report_page.click_non_clickable_card(name)
    assert url_after == url_before, "Clicking Unique Clicks must not navigate to another report"
    assert headers_after == headers_before, "Clicking Unique Clicks must not change the table"


# ══════════════════════════════════════════════════════════════════════════════
# TC12 — Export CSV per clickable card: downloaded file's headers match
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
@pytest.mark.parametrize(
    "card",
    CLICKABLE_REPORT_CARDS,
    ids=lambda card: card["name"].replace(" ", "_"),
)
def test_TC12_export_headers_per_card(report_page, card):
    """TC12: for every clickable card, selecting it and using Export CSV
    downloads a real file whose header row exactly matches that card's
    own EXPORT header list (card["export_headers"] -- deliberately a
    SEPARATE list from the on-screen table's card["headers"] used by
    TC03-09, see Test Design Notes above: the on-screen headers are
    confirmed rendered in UPPERCASE, almost certainly a CSS
    text-transform rather than the real underlying header text, and a
    server-generated export file would not be expected to apply that
    same CSS transform). Validated with the project's existing, generic
    utils/file_validator.validate_file_headers(), exactly as
    tests/sms/reports/test_sms_campaign_report_flow.py already does for
    the aggregate SMS Campaign Report's own export -- no new validation
    logic is introduced here."""
    ensure_on_report_page(report_page)

    result = report_page.click_card_then_export(card["name"], timeout_ms=30000)
    assert result is not None, (
        f"Export CSV should produce a downloaded file for card {card['name']!r} "
        f"(if this fails, first confirm SmsCampaignMessageReportPage."
        f"EXPORT_CSV_LINK's locator against the real Export control's markup)"
    )
    assert result["file_size"] > 0, (
        f"Downloaded export file for card {card['name']!r} should not be empty"
    )

    try:
        actual_headers = validate_file_headers(result["file_path"], card["export_headers"])
    except FileNotDownloadedError as exc:
        pytest.fail(f"[{card['name']}] {exc}")
    except (UnsupportedFileTypeError, EmptyFileError) as exc:
        pytest.fail(f"[{card['name']}] {exc}")
    except HeaderValidationError as exc:
        print(f"[{card['name']}] Expected headers: {exc.expected}")
        print(f"[{card['name']}] Actual headers: {exc.actual}")
        print(f"[{card['name']}] Missing headers: {exc.missing}")
        print(f"[{card['name']}] Unexpected headers: {exc.unexpected}")
        pytest.fail(f"[{card['name']}] {exc}")

    print(f"[{card['name']}] Export header validation PASS: {actual_headers}")
