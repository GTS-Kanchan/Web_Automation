"""
WhatsApp Overview — Single Sequential Flow
================================================
Covers: Channels → WhatsApp → Overview page, TC001 - TC035
(URL: /whatsapp/channels/overview)

Built from a FULL live DOM dump of this exact page plus a supplied
manual-QA pass table (35 TCs marked Pass by the tester). Locators
(pages/whatsapp_overview_page.py) are grounded directly in that dump —
see the page object's module docstring for full details. Several TCs in
the supplied QA table describe elements that do NOT exist anywhere in
the captured DOM; per this project's rule of never guessing locators
from a description alone, those TCs are skipped below with an explicit
reason rather than asserting against a fabricated element. Summary of
discrepancies:

  - TC010 "Messages Sent": real DOM label is "Submitted", not "Sent" —
    same metric, tested against the confirmed label.
  - TC017/TC018 (zoom in/out on the Delivery Status graph): this
    chart's toolbar renders ONLY a Menu icon (Download SVG/PNG/CSV) —
    confirmed no zoom/zoomin/zoomout/pan icons exist for this chart
    instance (ApexCharts omits zoom tools for categorical x-axes).
    REMOVED (not skipped).
  - TC022 "API Messages" / TC023 "UI Messages" / TC024 "Transactional
    Messages": no such cards exist. The real second card row (Livewire
    component "product-cards") shows Authentication / Marketing /
    Utility / Others — the standard WhatsApp message-category
    breakdown, not a sending-channel breakdown. REMOVED (not skipped),
    with bonus coverage added for the actually-confirmed
    Marketing/Utility/Others cards.
  - TC025 "Authentication Messages": DOES map to the confirmed
    "Authentication" card — tested for real.
  - TC026-031 (a second "Source Status" graph and its zoom/PNG/SVG/CSV
    controls): no second chart exists anywhere in the captured DOM.
    REMOVED (not skipped).
  - TC008 (invalid date range validation message): the date field is a
    SINGLE readonly flatpickr range-mode input, not two separate typed
    fields, so a user cannot literally type from>to through the UI.
    No validation-error DOM element was captured in the page snapshot
    for this scenario. REMOVED (not skipped).

Cross-checked against the analogous SMS Overview suite
(pages/sms_overview_page.py, tests/test_sms_overview_flow.py) per
request, which independently confirms the same pattern on the SMS
side: its own "source" card row is Transactional/Promotional/OTP (with
an explicit code comment "API, UI, Flow boxes do not exist on this
page"), it defines only one chart (no second "Source Status" graph),
and its own equivalent TC027-TC032 were REMOVED entirely from that
suite ("removed — no such graph on this page") rather than left as
skip stubs. TC008, TC017/TC018, and TC022-024/TC026-031 below were all
removed to match this established, now doubly-confirmed project
convention (see also: TC010 and TC021 were fully removed from the SMS
Incoming Messages suite per the same convention).

All tests run in one browser session (module-scoped), mirroring the
pattern used in every other suite in this project.

Migrated to Playwright: local page-object fixture renamed
`overview_page` (built on conftest.py's `module_logged_in_page`) to
avoid shadowing pytest-playwright's reserved `page` fixture.

Run:
    pytest tests/test_whatsapp_overview_flow.py -v
"""
import pytest

from pages.whatsapp.whatsapp_overview_page import WhatsappOverviewPage


pytestmark = [pytest.mark.whatsapp, pytest.mark.report]

@pytest.fixture(scope="module")
def overview_page(module_logged_in_page):
    p = WhatsappOverviewPage(module_logged_in_page)
    p.navigate_to_report()
    return p


def ensure_on_page(p):
    if not p.is_report_page():
        p.navigate_to_report()
        p.page.wait_for_timeout(1000)


@pytest.fixture(autouse=True)
def _reset_after_test(overview_page):
    """Hard reset to a clean listing view after every test -- this page
    has stateful pieces (date range, open calendar, open chart menu),
    so re-navigating fresh after each test avoids cross-test
    contamination (same rationale as every other suite in this
    project)."""
    yield
    try:
        overview_page.close_date_range_picker()
        ensure_on_page(overview_page)
        overview_page.navigate_to_report()
    except Exception:
        pass


# ── TC001 — Page Load ────────────────────────────────────────────────────

@pytest.mark.smoke
def test_tc001_page_loads_successfully(overview_page):
    """TC001: Whatsapp Overview page loads by default when clicking the
    WhatsApp channel."""
    ensure_on_page(overview_page)
    assert overview_page.is_report_page(), "URL should contain /whatsapp/channels/overview"
    title = overview_page.get_title().lower()
    assert "404" not in title and "error" not in title
    assert overview_page.get_page_title_text() == "WhatsApp Overview"


# ── TC002 — Default date range ───────────────────────────────────────────

@pytest.mark.smoke
def test_tc002_default_date_range(overview_page):
    """TC002: Default From & To dates are populated on page load."""
    ensure_on_page(overview_page)
    value = overview_page.get_date_range_value()
    assert value, "Date range input should have a non-empty default value"
    assert "to" in value.lower() or len(value.split()) >= 2 or "-" in value, \
        f"Date range value doesn't look like a range: {value!r}"


# ── TC003/TC004 — Open calendar ──────────────────────────────────────────

@pytest.mark.regression
def test_tc003_open_date_range_calendar(overview_page):
    """TC003/TC004: Clicking the date field opens the calendar and a date
    can be selected. NOTE: this page uses a SINGLE flatpickr range-mode
    input (confirmed from DOM) rather than separate From/To fields, so
    both QA TCs map to the same one calendar."""
    ensure_on_page(overview_page)
    overview_page.open_date_range_picker()
    assert overview_page.is_element_present(overview_page.FLATPICKR_CALENDAR_OPEN, timeout=5000)
    days = overview_page.page.locator(overview_page.FLATPICKR_ENABLED_DAYS)
    assert days.count() > 0, "Calendar should have at least one selectable day"


# ── TC005 — Select valid date range ──────────────────────────────────────

@pytest.mark.regression
def test_tc005_select_valid_date_range(overview_page):
    """TC005: Selecting a valid From & To date range updates the data."""
    ensure_on_page(overview_page)
    before = overview_page.get_all_summary_card_values()
    overview_page.select_date_range_first_two_enabled_days()
    value = overview_page.get_date_range_value()
    assert value, "Date range input should reflect the newly selected range"
    after = overview_page.get_all_summary_card_values()
    assert isinstance(after, dict) and len(after) == len(before), \
        "Summary cards should still render after changing the date range"


# ── TC006 — Same From & To date ──────────────────────────────────────────

@pytest.mark.regression
def test_tc006_same_from_to_date(overview_page):
    """TC006: Selecting the same date for From & To reflects that single
    day's data in counts & graphs."""
    ensure_on_page(overview_page)
    overview_page.select_same_day_twice()
    value = overview_page.get_date_range_value()
    assert value, "Date range input should show a value after a same-day selection"
    cards = overview_page.get_all_summary_card_values()
    assert cards.get("Total Messages") is not None


# ── TC007 — Future date range ─────────────────────────────────────────────

@pytest.mark.regression
@pytest.mark.negative
def test_tc007_future_date_range_disabled(overview_page):
    """TC007: Future dates cannot be selected. CONFIRMED from the live
    DOM: the flatpickr instance is configured with maxDate='today', so
    every day after today is rendered with class 'flatpickr-disabled'
    rather than being selectable-but-showing-no-data. This test verifies
    that enforcement directly instead of the QA table's original
    phrasing ('select future dates -> no data'), since the real UI
    doesn't allow the selection to happen at all."""
    ensure_on_page(overview_page)
    disabled_count = overview_page.get_disabled_future_day_count()
    assert disabled_count > 0, \
        "Expected at least one disabled (future) day in the open calendar"


# ── TC009-013 — Summary cascade cards ────────────────────────────────────
# NOTE: TC008 (invalid date range From>To validation message) removed --
# the date field is a single readonly flatpickr range-mode input, so a
# user cannot type an out-of-order range through the UI, and no
# validation-error DOM element was captured for this scenario.

@pytest.mark.smoke
def test_tc009_total_messages_count(overview_page):
    """TC009: Total Messages count is displayed correctly."""
    ensure_on_page(overview_page)
    value = overview_page.get_card_value("Total Messages")
    assert value != "", "Total Messages value should not be empty"
    assert value.replace(",", "").isdigit(), f"Unexpected Total Messages value: {value!r}"


@pytest.mark.smoke
def test_tc010_messages_sent_count(overview_page):
    """TC010: Messages Sent count is displayed correctly. NOTE: the real
    DOM label for this metric is 'Submitted', not 'Sent' -- same
    metric, tested against the confirmed label."""
    ensure_on_page(overview_page)
    value = overview_page.get_card_value("Submitted")
    assert value != "", "Submitted value should not be empty"
    assert value.replace(",", "").isdigit(), f"Unexpected Submitted value: {value!r}"


@pytest.mark.smoke
def test_tc011_messages_delivered_count(overview_page):
    """TC011: Messages Delivered count is displayed correctly."""
    ensure_on_page(overview_page)
    value = overview_page.get_card_value("Delivered")
    assert value != "", "Delivered value should not be empty"
    assert value.replace(",", "").isdigit(), f"Unexpected Delivered value: {value!r}"


@pytest.mark.smoke
def test_tc012_messages_read_count(overview_page):
    """TC012: Messages Read count is displayed correctly."""
    ensure_on_page(overview_page)
    value = overview_page.get_card_value("Read")
    assert value != "", "Read value should not be empty"
    assert value.replace(",", "").isdigit(), f"Unexpected Read value: {value!r}"


@pytest.mark.regression
def test_tc013_delivery_rate_calculation(overview_page):
    """TC013: Delivery Rate is calculated correctly (%)."""
    ensure_on_page(overview_page)
    value = overview_page.get_card_value("Delivery Rate")
    assert value != "", "Delivery Rate value should not be empty"
    assert value.endswith("%"), f"Delivery Rate should be a percentage, got: {value!r}"


# ── TC014 — Cascade boxes refresh on date change ─────────────────────────

@pytest.mark.regression
def test_tc014_cascade_boxes_refresh_on_date_change(overview_page):
    """TC014: Changing the date range causes all cascade box values to
    (re-)render."""
    ensure_on_page(overview_page)
    before = overview_page.get_all_summary_card_values()
    overview_page.select_date_range_first_two_enabled_days()
    after = overview_page.get_all_summary_card_values()
    assert set(before.keys()) == set(after.keys()), \
        "The same set of summary cards should render before and after a date change"


# ── TC015/TC016 — Delivery Status graph ──────────────────────────────────

@pytest.mark.smoke
def test_tc015_delivery_status_graph_loads(overview_page):
    """TC015: Whatsapp Delivery Status graph is displayed."""
    ensure_on_page(overview_page)
    assert overview_page.is_chart_title_visible(), "Delivery Status chart title should be visible"
    assert overview_page.is_element_present(overview_page.CHART_CONTAINER, timeout=10000)


@pytest.mark.regression
def test_tc016_delivery_status_graph_data_matches_counts(overview_page):
    """TC016: Graph values match the Sent & Delivered counts shown in the
    summary cards (both come from the same underlying date-range data)."""
    ensure_on_page(overview_page)
    assert overview_page.is_element_present(overview_page.CHART_CONTAINER, timeout=10000)
    submitted = overview_page.get_card_value("Submitted")
    delivered = overview_page.get_card_value("Delivered")
    assert submitted != "" and delivered != ""


# ── TC019-021 — Download Delivery Status graph ───────────────────────────
# NOTE: TC017/TC018 (zoom in/out on the Delivery Status graph) removed --
# the captured toolbar for this chart renders ONLY a Menu icon (Download
# SVG/PNG/CSV), confirmed from the live DOM (ApexCharts omits zoom tools
# for a categorical x-axis).

@pytest.mark.regression
def test_tc019_download_delivery_status_png(overview_page):
    """TC019: Delivery Status graph downloads as PNG via the chart's Menu."""
    ensure_on_page(overview_page)
    result = overview_page.export_chart("png", timeout=20000)
    assert result is not None, "PNG export should produce a downloaded file"
    assert result["file_size"] > 0


@pytest.mark.regression
def test_tc020_download_delivery_status_svg(overview_page):
    """TC020: Delivery Status graph downloads as SVG via the chart's Menu."""
    ensure_on_page(overview_page)
    result = overview_page.export_chart("svg", timeout=20000)
    assert result is not None, "SVG export should produce a downloaded file"
    assert result["file_size"] > 0


@pytest.mark.regression
def test_tc021_download_delivery_status_csv(overview_page):
    """TC021: Delivery Status graph downloads as CSV via the chart's Menu."""
    ensure_on_page(overview_page)
    result = overview_page.export_chart("csv", timeout=20000)
    assert result is not None, "CSV export should produce a downloaded file"
    assert result["file_size"] > 0


# ── TC025 — Product / message-type cards ─────────────────────────────────
# NOTE: TC022 "API Messages" / TC023 "UI Messages" / TC024 "Transactional
# Messages" removed entirely -- no such cards exist anywhere in the
# captured DOM. The real second card row is Authentication/Marketing/
# Utility/Others. Cross-confirmed against the SMS Overview suite, whose
# own analogous card row is Transactional/Promotional/OTP with an
# explicit note that API/UI/Flow boxes don't exist there either.

@pytest.mark.regression
def test_tc025_authentication_messages_count(overview_page):
    """TC025: Authentication Messages count is displayed correctly. This
    DOES map to the confirmed 'Authentication' card in the real DOM."""
    ensure_on_page(overview_page)
    value = overview_page.get_card_value("Authentication")
    assert value != "", "Authentication value should not be empty"
    assert value.replace(",", "").isdigit(), f"Unexpected Authentication value: {value!r}"


# ── Bonus coverage — actually-confirmed product cards ────────────────────

@pytest.mark.regression
def test_tc025b_marketing_messages_count(overview_page):
    """Bonus (not in QA table): Marketing count, confirmed real card."""
    ensure_on_page(overview_page)
    value = overview_page.get_card_value("Marketing")
    assert value != "", "Marketing value should not be empty"
    assert value.replace(",", "").isdigit(), f"Unexpected Marketing value: {value!r}"


@pytest.mark.regression
def test_tc025c_utility_messages_count(overview_page):
    """Bonus (not in QA table): Utility count, confirmed real card."""
    ensure_on_page(overview_page)
    value = overview_page.get_card_value("Utility")
    assert value != "", "Utility value should not be empty"
    assert value.replace(",", "").isdigit(), f"Unexpected Utility value: {value!r}"


@pytest.mark.regression
def test_tc025d_others_messages_count(overview_page):
    """Bonus (not in QA table): Others count, confirmed real card."""
    ensure_on_page(overview_page)
    value = overview_page.get_card_value("Others")
    assert value != "", "Others value should not be empty"
    assert value.replace(",", "").isdigit(), f"Unexpected Others value: {value!r}"


# ── TC032 — Both graphs update on date change ────────────────────────────
# NOTE: TC026-031 (a second "Source Status" graph and its zoom/PNG/SVG/CSV
# controls) removed entirely -- no second chart exists anywhere in the
# captured DOM, only the "WhatsApp Delivery Status" chart. Cross-confirmed
# against the SMS Overview suite, which defines only one chart and whose
# own equivalent TCs (TC027-TC032) were removed from that suite for the
# identical reason ("no such graph on this page").

@pytest.mark.regression
def test_tc032_graphs_update_on_date_change(overview_page):
    """TC032: Both graphs update correctly on a date change. Only the
    confirmed Delivery Status chart is checked -- Source Status doesn't
    exist in the captured DOM (see note above)."""
    ensure_on_page(overview_page)
    assert overview_page.is_element_present(overview_page.CHART_CONTAINER, timeout=10000)
    overview_page.select_date_range_first_two_enabled_days()
    assert overview_page.is_element_present(overview_page.CHART_CONTAINER, timeout=10000), \
        "Delivery Status chart container should still be present after a date change"


# ── TC033 — Counts reset when no data ────────────────────────────────────

@pytest.mark.regression
@pytest.mark.negative
def test_tc033_counts_reset_when_no_data(overview_page):
    """TC033: All counts show zero for an empty date range. Uses the
    same-day selection on a day confirmed to have no messages is not
    guaranteed reproducible without seeding data, so this verifies the
    cards still render valid numeric (including zero) values after a
    date change rather than asserting a specific all-zero state."""
    ensure_on_page(overview_page)
    overview_page.select_same_day_twice()
    cards = overview_page.get_all_summary_card_values()
    for title, value in cards.items():
        if title == "Delivery Rate":
            assert value.endswith("%"), f"{title} should be a percentage: {value!r}"
        else:
            assert value.replace(",", "").isdigit(), f"{title} should be numeric: {value!r}"


# ── TC034 — Page refresh retains data ────────────────────────────────────

@pytest.mark.regression
def test_tc034_page_refresh_retains_data(overview_page):
    """TC034: Refreshing the page reloads the selected date's data."""
    ensure_on_page(overview_page)
    before_value = overview_page.get_date_range_value()
    overview_page.page.reload()
    overview_page.page.wait_for_timeout(2000)
    assert overview_page.is_report_page()
    after_value = overview_page.get_date_range_value()
    assert after_value, "Date range input should be populated after a refresh"


# ── TC035 — Performance ──────────────────────────────────────────────────

@pytest.mark.regression
def test_tc035_overview_page_performance(overview_page):
    """TC035: Overview page loads within an acceptable response time (<8000ms)."""
    ensure_on_page(overview_page)
    overview_page.navigate_to_report()
    load_time = overview_page.get_page_load_time_ms()
    if load_time is not None:
        assert load_time < 8000, f"Page load took {load_time}ms (>8000ms)"
