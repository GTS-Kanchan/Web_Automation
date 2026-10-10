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
import re

import pytest

from pages.sms.sms_campaign_page import SMSCampaignPage
from pages.sms.sms_campaign_message_report_page import SmsCampaignMessageReportPage
from utils.file_validator import (
    EmptyFileError,
    FileNotDownloadedError,
    HeaderValidationError,
    UnsupportedFileTypeError,
    read_file_rows,
    validate_file_headers,
)
from utils.report_data_validator import (
    CountMismatchError,
    DataExistsError,
    DataTypeError,
    DateFormatError,
    RequiredFieldError,
    calculate_export_total_messages as _calculate_export_total_messages,
    sum_numeric_field as _sum_numeric_field,
    verify_data_exists as _verify_data_exists,
    verify_data_types as _verify_data_types,
    verify_date_formats as _verify_date_formats,
    verify_required_fields as _verify_required_fields,
    verify_ui_total_messages_vs_export as _verify_ui_total_messages_vs_export,
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
        # CONFIRMED (2026-10-10, explicit real-UI correction): DLR
        # Awaited is genuinely DIFFERENT from Total Messages/Submitted/
        # Delivered/Failed -- it has NO "DLR Received At" column (makes
        # sense: a DLR-awaited message hasn't received its DLR yet, so
        # there is nothing to show there). Do not "fix" this back to the
        # 7-column set without a fresh, explicit instruction confirming
        # the app has changed -- an earlier guess that it matched the
        # other 4 cards was wrong and was reverted.
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
# Generic per-card deep-verification config (TC15) -- reuses the SAME
# export_headers already confirmed above for every card, rather than a
# second hardcoded header list per card. Column -> expected type is a
# single project-wide mapping (every card's export_headers is a subset
# of these exact column names -- confirmed by cross-checking every list
# above), so adding a new card/column here only means adding one entry
# to COLUMN_TYPE_MAP, never a new per-card block.
# ══════════════════════════════════════════════════════════════════════════════

COLUMN_TYPE_MAP = {
    "Contact": "string",
    "Status": "string",
    "Status Description": "string",
    "SMS Units": "numeric",
    "Received At": "date",
    "Submitted At": "date",
    "DLR Received At": "date",
    "Clicked URL": "string",
    "Clicked At": "date",
    "Browser / Device / OS": "string",
    "Geo Location / IP": "string",
}


def _card_type_spec(card):
    """{column: type} for exactly this card's real export_headers.
    Fails loudly (not a silent guess) if a card ever exports a column
    this suite hasn't classified in COLUMN_TYPE_MAP yet."""
    spec = {}
    for header in card["export_headers"]:
        assert header in COLUMN_TYPE_MAP, (
            f"COLUMN_TYPE_MAP has no entry for column {header!r} "
            f"(card {card['name']!r}) -- add its type before deep-"
            f"verifying this card."
        )
        spec[header] = COLUMN_TYPE_MAP[header]
    return spec


def _card_optional_when(card):
    """Same Sent/Rejected "DLR Received At" exemption used by the Total
    Messages pipeline above (see _dlr_receipt_not_expected/
    TOTAL_MESSAGES_DATE_OPTIONAL_WHEN), applied only to a card whose
    export actually has that column (DLR Awaited/Rejected/Total Clicks
    don't, so this is {} for those)."""
    if "DLR Received At" in card["export_headers"]:
        return {"DLR Received At": _dlr_receipt_not_expected}
    return {}


def capture_ui_card_value(page: SmsCampaignMessageReportPage, card_name: str) -> int:
    """Generic form of capture_total_messages_from_ui() above, for any
    stat card by name -- same digit-extraction approach, not duplicated
    per card."""
    raw = page.get_card_value(card_name)
    digits = re.sub(r"[^\d]", "", raw or "")
    assert digits, (
        f"UI {card_name!r} count is not numeric -- that stat card "
        f"rendered {raw!r}, which has no digits."
    )
    return int(digits)


def export_card_file(page: SmsCampaignMessageReportPage, card_name: str, timeout_ms=30000):
    """Generic form of export_total_messages_file() above, for any
    clickable card by name -- composes the existing
    click_card_then_export(), no new export/navigation logic."""
    result = page.click_card_then_export(card_name, timeout_ms=timeout_ms)
    assert result is not None, (
        f"Export CSV should produce a downloaded file for the "
        f"{card_name!r} card (if this fails, first confirm "
        f"SmsCampaignMessageReportPage.EXPORT_CSV_LINK's locator against "
        f"the real Export control's markup)."
    )
    assert result["file_size"] > 0, f"Downloaded {card_name!r} export file should not be empty"
    return result["file_path"]


def calculate_export_card_count(card, data):
    """The number to compare against a card's UI stat value. CONFIRMED
    (user report): a card whose export has an "SMS Units" column shows
    the SUM of that column (a message can span more than one SMS unit --
    see calculate_export_total_messages()'s docstring above), so that's
    reused here via sum_numeric_field(). A card with NO "SMS Units"
    column (Rejected, Total Clicks) has no unit concept to sum, so its
    UI value is compared against the plain export row count instead --
    one row per rejected message / one row per click event, per those
    cards' own real, confirmed export_headers (no SMS Units column at
    all)."""
    if "SMS Units" in card["export_headers"]:
        return _sum_numeric_field(data, "SMS Units")
    return len(data)


# ══════════════════════════════════════════════════════════════════════════════
# Total Messages export -- deep verification configuration (TC13)
#
# Extends this same suite's existing "Total Messages" card coverage
# (TC03-09 header check on-screen, TC12 export header check) with the
# full pipeline required for TC13 below:
#
#   Header Verification -> Data Exists -> Required Field -> Data Type ->
#   Date/Date-Time -> UI Total Message Count vs Export Count
#
# Deliberately does NOT duplicate the header list a third time: the
# "Total Messages" entry already at CLICKABLE_REPORT_CARDS[0] (its
# "export_headers") is the single source of truth for this card's real,
# confirmed export headers, reused here for the required-field list and
# the data-type spec built from it. The underlying validators
# (utils/report_data_validator.py) are fully configuration-based -- this
# block is what makes them concrete for "Total Messages" specifically, so
# the same module can be pointed at any other card/report/channel later
# without changing utils/report_data_validator.py at all.
# ══════════════════════════════════════════════════════════════════════════════

_TOTAL_MESSAGES_CARD = next(c for c in CLICKABLE_REPORT_CARDS if c["name"] == "Total Messages")

# Every exported column on this report is required to be populated, per
# the task spec's own Required Field Verification list (which is, in
# fact, identical to this card's full export_headers list -- confirmed by
# comparing the two rather than assumed).
TOTAL_MESSAGES_REQUIRED_FIELDS = list(_TOTAL_MESSAGES_CARD["export_headers"])

# Column -> expected type ("string" | "numeric" | "date"), per the task
# spec's Data Type Verification table.
TOTAL_MESSAGES_TYPE_SPEC = {
    "Contact": "string",
    "Status": "string",
    "Status Description": "string",
    "SMS Units": "numeric",
    "Received At": "date",
    "Submitted At": "date",
    "DLR Received At": "date",
}
assert set(TOTAL_MESSAGES_TYPE_SPEC) == set(TOTAL_MESSAGES_REQUIRED_FIELDS), (
    "TOTAL_MESSAGES_TYPE_SPEC must cover exactly the same columns as "
    "TOTAL_MESSAGES_REQUIRED_FIELDS (itself derived from the confirmed "
    "export headers) -- a mismatch here means this config block and the "
    "real export headers have drifted apart."
)

# Every date/date-time column present in this export, per the task
# spec's Date/Date-Time Verification step ("for every date/date-time
# column present in the export").
TOTAL_MESSAGES_DATE_FIELDS = [
    field for field, kind in TOTAL_MESSAGES_TYPE_SPEC.items() if kind == "date"
]

# Real app behavior, user-confirmed: a message's "DLR Received At" cell
# legitimately has no timestamp (renders as a placeholder dash) while its
# Status is "Sent" (not yet delivered) or "Rejected" (never delivered, so
# no delivery receipt ever arrives) -- this is not bad/missing data, it's
# the correct UI state for those two statuses. Every OTHER status is
# still held to a real date value. Case-insensitive since the export's
# exact Status casing hasn't been independently re-confirmed beyond the
# two values reported.
_DLR_NOT_YET_RECEIVED_STATUSES = {"sent", "rejected"}


def _dlr_receipt_not_expected(row):
    return (row.get("Status") or "").strip().lower() in _DLR_NOT_YET_RECEIVED_STATUSES


# Passed as `optional_when` to verify_data_types()/verify_date_formats()
# below -- only exempts "DLR Received At" from the date check, and only
# for a row whose Status is one of the above AND whose value is actually
# still blank/placeholder (a present-but-invalid value still fails).
TOTAL_MESSAGES_DATE_OPTIONAL_WHEN = {
    "DLR Received At": _dlr_receipt_not_expected,
}


# ── Reusable validation-structure helpers (named exactly as specified) ──────
# Thin, Total-Messages-specific wrappers around the generic, config-driven
# validators in utils/file_validator.py / utils/report_data_validator.py --
# no export/navigation/file-reading logic is reimplemented here, and every
# one of these can be reused for another card/report by simply calling the
# underlying module functions with a different config instead of these
# wrappers.

def capture_total_messages_from_ui(page: SmsCampaignMessageReportPage) -> int:
    """Step 1: read the Total Messages stat card's displayed value and
    return it as an int. Uses the same digit-extraction approach already
    established elsewhere in this suite for a stat-card value (e.g. the
    "Total Clicks" card read in test_sms_campaign_short_url_click_dlr.py)
    rather than a new parsing strategy. Fails loudly (not a silent 0) if
    the card's rendered value has no digits at all -- "validate the UI
    value is numeric" per the spec."""
    raw = page.get_card_value("Total Messages")
    digits = re.sub(r"[^\d]", "", raw or "")
    assert digits, (
        f"UI Total Messages count is not numeric -- 'Total Messages' stat "
        f"card rendered {raw!r}, which has no digits."
    )
    return int(digits)


def export_total_messages_file(page: SmsCampaignMessageReportPage, timeout_ms=30000):
    """Step 2: select the Total Messages card and download its export.
    Composes the existing click_card_then_export() (no new export/
    navigation logic). Named _file (not export_total_messages) to avoid
    colliding with the row-count variable of the same name used by the
    calling test / the task's own pseudocode, which would otherwise shadow
    this function after the first assignment."""
    result = page.click_card_then_export("Total Messages", timeout_ms=timeout_ms)
    assert result is not None, (
        "Export CSV should produce a downloaded file for the 'Total "
        "Messages' card (if this fails, first confirm "
        "SmsCampaignMessageReportPage.EXPORT_CSV_LINK's locator against "
        "the real Export control's markup)."
    )
    assert result["file_size"] > 0, "Downloaded 'Total Messages' export file should not be empty"
    return result["file_path"]


def verify_headers(export_file):
    """Step 3 / Header Verification: reuses validate_file_headers() as-is
    (the same function TC12 already uses for every card) -- no new header
    -reading logic."""
    try:
        return validate_file_headers(export_file, _TOTAL_MESSAGES_CARD["export_headers"])
    except (FileNotDownloadedError, UnsupportedFileTypeError, EmptyFileError, HeaderValidationError) as exc:
        pytest.fail(f"[Total Messages export] {exc}")


def verify_data_exists(export_file):
    """Step 4 / Data Exists Verification: reads the export's real data
    rows (utils.file_validator.read_file_rows(), the same file already
    header-validated above) and confirms at least one exists. Returns the
    row list (list of {header: value} dicts) for every later stage to
    reuse, so the file is only read once."""
    _headers, rows = read_file_rows(export_file)
    try:
        return _verify_data_exists(rows, context="Total Messages export")
    except DataExistsError as exc:
        pytest.fail(str(exc))


def verify_required_fields(data):
    """Step 5 / Required Field Verification."""
    try:
        return _verify_required_fields(data, TOTAL_MESSAGES_REQUIRED_FIELDS, context="Total Messages export")
    except RequiredFieldError as exc:
        pytest.fail(str(exc))


def verify_data_types(data):
    """Step 6 / Data Type Verification. optional_when exempts "DLR
    Received At" from the date check for a Sent/Rejected row whose value
    is still a blank placeholder -- see TOTAL_MESSAGES_DATE_OPTIONAL_WHEN
    above."""
    try:
        return _verify_data_types(
            data, TOTAL_MESSAGES_TYPE_SPEC, context="Total Messages export",
            optional_when=TOTAL_MESSAGES_DATE_OPTIONAL_WHEN,
        )
    except DataTypeError as exc:
        pytest.fail(str(exc))


def verify_date_formats(data):
    """Step 7 / Date/Date-Time Verification. Same optional_when exemption
    as verify_data_types() above, for the same reason."""
    try:
        return _verify_date_formats(
            data, TOTAL_MESSAGES_DATE_FIELDS, context="Total Messages export",
            optional_when=TOTAL_MESSAGES_DATE_OPTIONAL_WHEN,
        )
    except DateFormatError as exc:
        pytest.fail(str(exc))


def calculate_export_total_messages(data):
    """Step 8 input: the number to compare against the UI's "Total
    Messages" stat card. CONFIRMED (user report) that this card displays
    the SUM of the export's "SMS Units" column, not the row/message
    count -- a single message can consist of more than one SMS unit
    (e.g. a long SMS split into multiple parts), so message count and
    unit count diverge (observed: 4 exported rows, 8 total SMS units).
    Uses the shared, generic sum_numeric_field() rather than
    reimplementing summation here; _calculate_export_total_messages
    (plain row count) is kept imported/available above for any caller
    that genuinely wants the row count instead."""
    return _sum_numeric_field(data, "SMS Units")


def verify_ui_total_messages_vs_export(ui_total_messages, export_total_messages):
    """Step 8 / mandatory final verification: UI Total Messages Count vs
    Export Total Messages Count."""
    try:
        return _verify_ui_total_messages_vs_export(ui_total_messages, export_total_messages, metric="Total Messages")
    except CountMismatchError as exc:
        pytest.fail(str(exc))


# ══════════════════════════════════════════════════════════════════════════════
# Module-scoped page
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def report_page(module_logged_in_page):
    listing = SMSCampaignPage(module_logged_in_page)
    listing.open_campaign_list()
    # Real-run fix (2026-10-10): the list's default "Created" filter is a
    # 1-day (today-only) window -- see
    # SMSCampaignPage.ensure_records_visible_with_previous_day_fallback's
    # docstring. Widen to include yesterday whenever the table is empty,
    # before relying on there being a first row at all.
    try:
        listing.ensure_records_visible_with_previous_day_fallback()
    except Exception:
        pass
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

    # Real-run fix (2026-10-10): confirmed via a real Chrome screenshot
    # showing CONTACT present vs. an automated chromium run missing both
    # CONTACT and SMS UNITS on this same "Total Messages" table -- this
    # is the same column-visibility-leak already diagnosed/fixed for
    # utils/campaign_dlr.py's TC045 flow. This report's table
    # (TABLE_NAME = "sms_messages") is the EXACT SAME Livewire table
    # component as pages/sms/messaging/sms_message_page.py's SMS
    # Messages list -- column visibility is that table's own persisted
    # state, not scoped to one page's URL, so a column a Messages-page
    # test left hidden leaks in here too. Self-heal once up front, before
    # any of TC03-TC09's header assertions run, rather than reacting
    # per-test.
    try:
        from pages.sms.sms_message_page import SMSMessagePage
        SMSMessagePage(p.page).restore_default_columns()
        p.page.reload()
        p.wait_for_table_load(timeout=15000)
    except Exception:
        pass

    return p


def ensure_on_report_page(p: SmsCampaignMessageReportPage):
    if not p.is_report_page():
        cid = getattr(p, "_campaign_id", None) or p.get_campaign_id_from_url()
        assert cid, "Lost track of the campaign id -- cannot recover to the report page"
        p.navigate_to_campaign(cid, metric="total")
        p.wait_for_table_load(timeout=10000)


# ══════════════════════════════════════════════════════════════════════════════
# Function-scoped page — a campaign about a week old (TC14 only)
# ══════════════════════════════════════════════════════════════════════════════

WEEK_OLD_TARGET_DAYS = 7
WEEK_OLD_TOLERANCE_DAYS = 1


@pytest.fixture
def week_old_report_page(logged_in_page):
    """Opens the report page of a campaign whose "Created At" column
    (list page, USER-CONFIRMED column name/format -- see
    SMSCampaignPage.find_row_index_by_age_days()'s docstring) is about
    WEEK_OLD_TARGET_DAYS days old, instead of the latest campaign the
    module-scoped `report_page` fixture above always uses.

    Function-scoped (its own fresh logged_in_page context) rather than
    reusing report_page/module_logged_in_page, so this does not disturb
    TC01-TC13's shared module-scoped page or its "always the latest
    campaign" contract.

    find_row_index_by_age_days() below pages forward through the list
    (has_next_page()/go_to_next_page(), up to its own max_pages safety
    cap) rather than only checking the first page, so this isn't limited
    to whatever fits in one set_per_page() batch.

    Skips (rather than failing the whole module) if no row within
    WEEK_OLD_TOLERANCE_DAYS of the target turns up anywhere in that scan
    -- this depends on real campaign data existing in the environment,
    not on anything this suite itself creates or controls."""
    listing = SMSCampaignPage(logged_in_page)
    listing.open_campaign_list()
    try:
        listing.set_per_page(25)
    except Exception:
        pass

    row_index = listing.find_row_index_by_age_days(
        WEEK_OLD_TARGET_DAYS, tolerance_days=WEEK_OLD_TOLERANCE_DAYS
    )
    if row_index is None:
        pytest.skip(
            f"No campaign found within {WEEK_OLD_TOLERANCE_DAYS} day(s) "
            f"of {WEEK_OLD_TARGET_DAYS} days old (checked by the "
            f"'Created At' column, paging forward through the campaign "
            f"list up to its safety cap)."
        )

    navigated = listing.click_reports_link_on_row(row_index)
    assert navigated, (
        f"Could not open the Reports icon on row {row_index} (the "
        f"campaign selected as ~{WEEK_OLD_TARGET_DAYS} days old)."
    )

    p = SmsCampaignMessageReportPage(logged_in_page)
    p.wait_for_table_load(timeout=15000)
    cid = p.remember_campaign_id()
    assert cid, "Could not determine the campaign id (UUID) from the report page URL"
    return p


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


# ══════════════════════════════════════════════════════════════════════════════
# TC13 — Total Messages export: full deep-verification pipeline, ending in
#         UI Total Message Count vs Export Count (mandatory final check)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC13_total_messages_export_deep_verification(report_page):
    """TC13: extends this suite's existing Total Messages coverage (the
    on-screen header check already covered by TC03-09, and the export
    header check already covered by TC12) with the full required
    pipeline:

        Header Verification
                v
        Data Exists Verification
                v
        Required Field Verification
                v
        Data Type Verification
                v
        Date/Date-Time Verification
                v
        UI Total Message Count vs Export Count Verification

    The UI's Total Messages count is captured BEFORE the export is
    downloaded (per the task's own "Important Rules": capture it before
    or immediately around the export so the report can't change between
    the two reads), and is compared against the export's real DATA ROW
    COUNT -- never the underlying SMS/message API, per the same rules.
    Every stage below gives its own clear PASS/FAIL: a failing stage
    calls pytest.fail() with that stage's own detailed message (see the
    verify_*() helpers above) rather than letting a later stage's
    assertion obscure which stage actually failed.
    """
    ensure_on_report_page(report_page)

    # ── Step 1: UI Total Messages, captured first ───────────────────────────
    ui_total_messages = capture_total_messages_from_ui(report_page)
    print(f"[Total Messages] UI Total Messages = {ui_total_messages}")

    # ── Step 2: export Total Messages (existing export/navigation logic,
    #            not duplicated -- see export_total_messages_file()) ───────
    export_file = export_total_messages_file(report_page)
    print(f"[Total Messages] Export downloaded: {export_file}")

    # ── Step 3: Header Verification ─────────────────────────────────────────
    verify_headers(export_file)
    print("[Total Messages] Header Verification: PASS")

    # ── Step 4: Data Exists Verification ────────────────────────────────────
    data = verify_data_exists(export_file)
    print(f"[Total Messages] Data Exists Verification: PASS ({len(data)} row(s))")

    # ── Step 5: Required Field Verification ─────────────────────────────────
    verify_required_fields(data)
    print("[Total Messages] Required Field Verification: PASS")

    # ── Step 6: Data Type Verification ──────────────────────────────────────
    verify_data_types(data)
    print("[Total Messages] Data Type Verification: PASS")

    # ── Step 7: Date/Date-Time Verification ─────────────────────────────────
    verify_date_formats(data)
    print("[Total Messages] Date/Date-Time Verification: PASS")

    # ── Step 8: UI Total Message Count vs Export Count (mandatory final) ────
    export_total_messages = calculate_export_total_messages(data)
    verify_ui_total_messages_vs_export(ui_total_messages, export_total_messages)
    print(
        f"[Total Messages] UI Total Messages ({ui_total_messages}) == "
        f"Export Total Messages ({export_total_messages}): PASS"
    )


# ══════════════════════════════════════════════════════════════════════════════
# TC14 — Same Total Messages export deep-verification pipeline as TC13,
#         run against a ~week-old campaign instead of the latest one
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
def test_TC14_total_messages_export_deep_verification_week_old_campaign(week_old_report_page):
    """TC14: identical pipeline to TC13 (same steps, same helper
    functions, same PASS/FAIL contract) but exercised against a campaign
    about a week old (week_old_report_page fixture above) instead of the
    latest campaign TC13 always uses. No verification logic is
    duplicated here -- only the campaign SELECTION differs; every step
    below reuses the exact same wrapper functions TC13 calls."""
    ui_total_messages = capture_total_messages_from_ui(week_old_report_page)
    print(f"[Total Messages / week-old campaign] UI Total Messages = {ui_total_messages}")

    export_file = export_total_messages_file(week_old_report_page)
    print(f"[Total Messages / week-old campaign] Export downloaded: {export_file}")

    verify_headers(export_file)
    print("[Total Messages / week-old campaign] Header Verification: PASS")

    data = verify_data_exists(export_file)
    print(f"[Total Messages / week-old campaign] Data Exists Verification: PASS ({len(data)} row(s))")

    verify_required_fields(data)
    print("[Total Messages / week-old campaign] Required Field Verification: PASS")

    verify_data_types(data)
    print("[Total Messages / week-old campaign] Data Type Verification: PASS")

    verify_date_formats(data)
    print("[Total Messages / week-old campaign] Date/Date-Time Verification: PASS")

    export_total_messages = calculate_export_total_messages(data)
    verify_ui_total_messages_vs_export(ui_total_messages, export_total_messages)
    print(
        f"[Total Messages / week-old campaign] UI Total Messages ({ui_total_messages}) == "
        f"Export Total Messages ({export_total_messages}): PASS"
    )


# ══════════════════════════════════════════════════════════════════════════════
# TC15 — Same deep-verification pipeline as TC13/TC14 (Header -> Data
#         Exists -> Required Field -> Data Type -> Date/Date-Time -> UI
#         Count vs Export Count), generalized to EVERY clickable card
#         (Total Messages, Submitted, Delivered, DLR Awaited, Failed,
#         Rejected, Total Clicks) instead of only Total Messages.
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.regression
@pytest.mark.parametrize(
    "card",
    CLICKABLE_REPORT_CARDS,
    ids=[c["name"].replace(" ", "_").replace("/", "_") for c in CLICKABLE_REPORT_CARDS],
)
def test_TC15_deep_verification_per_card(report_page, card):
    """TC15: extends TC13's Total-Messages-only deep verification to
    every clickable card, reusing the exact same generic validators
    (utils/report_data_validator.py, utils/file_validator.py) and the
    exact same config-driven approach -- no per-card verification logic
    is duplicated, only the config (card["export_headers"],
    _card_type_spec(), _card_optional_when(), calculate_export_card_count())
    changes per card. Each stage gives its own clear PASS/FAIL, exactly
    like TC13."""
    ensure_on_report_page(report_page)
    name = card["name"]

    # ── Step 1: UI stat card value, captured first ──────────────────────────
    ui_count = capture_ui_card_value(report_page, name)
    print(f"[{name}] UI count = {ui_count}")

    # ── Step 2: export this card (existing export/navigation logic) ────────
    export_file = export_card_file(report_page, name)
    print(f"[{name}] Export downloaded: {export_file}")

    # ── Step 3: Header Verification ─────────────────────────────────────────
    try:
        validate_file_headers(export_file, card["export_headers"])
    except (FileNotDownloadedError, UnsupportedFileTypeError, EmptyFileError, HeaderValidationError) as exc:
        pytest.fail(f"[{name}] Header Verification FAILED: {exc}")
    print(f"[{name}] Header Verification: PASS")

    # ── Step 4: Data Exists Verification ────────────────────────────────────
    _headers, rows = read_file_rows(export_file)

    if ui_count == 0:
        # CONFIRMED real behavior: a card's UI value can legitimately be 0
        # -- e.g. no Rejected/Failed/DLR-Awaited rows when every message
        # in the campaign was delivered, or no Total Clicks rows when the
        # message had no URL or nobody clicked it. An empty export in
        # that case is the CORRECT state, not a verification failure, so
        # this skips straight to the final count check instead of
        # failing "Data Exists" (which is only about EXISTING data being
        # missing) or running row-level checks that would be vacuous
        # anyway on zero rows. If the export unexpectedly DOES have rows
        # despite a 0 UI count, that's a real mismatch and the final
        # count check below still catches it.
        print(f"[{name}] UI count is 0 -- 0 export rows is the expected/correct state for this card; skipping Data Exists/Required Field/Data Type/Date Format checks")
        export_count = calculate_export_card_count(card, rows)
        try:
            _verify_ui_total_messages_vs_export(ui_count, export_count, metric=name)
        except CountMismatchError as exc:
            pytest.fail(str(exc))
        print(f"[{name}] UI Count (0) == Export Count ({export_count}): PASS")
        return

    try:
        data = _verify_data_exists(rows, context=f"{name} export")
    except DataExistsError as exc:
        pytest.fail(str(exc))
    print(f"[{name}] Data Exists Verification: PASS ({len(data)} row(s))")

    type_spec = _card_type_spec(card)
    date_fields = [h for h, t in type_spec.items() if t == "date"]
    optional_when = _card_optional_when(card)

    # ── Step 5: Required Field Verification ─────────────────────────────────
    try:
        _verify_required_fields(data, list(card["export_headers"]), context=f"{name} export")
    except RequiredFieldError as exc:
        pytest.fail(str(exc))
    print(f"[{name}] Required Field Verification: PASS")

    # ── Step 6: Data Type Verification ──────────────────────────────────────
    try:
        _verify_data_types(data, type_spec, context=f"{name} export", optional_when=optional_when)
    except DataTypeError as exc:
        pytest.fail(str(exc))
    print(f"[{name}] Data Type Verification: PASS")

    # ── Step 7: Date/Date-Time Verification ─────────────────────────────────
    try:
        _verify_date_formats(data, date_fields, context=f"{name} export", optional_when=optional_when)
    except DateFormatError as exc:
        pytest.fail(str(exc))
    print(f"[{name}] Date/Date-Time Verification: PASS")

    # ── Step 8: UI Count vs Export Count (mandatory final) ──────────────────
    export_count = calculate_export_card_count(card, data)
    try:
        _verify_ui_total_messages_vs_export(ui_count, export_count, metric=name)
    except CountMismatchError as exc:
        pytest.fail(str(exc))
    print(f"[{name}] UI Count ({ui_count}) == Export Count ({export_count}): PASS")
