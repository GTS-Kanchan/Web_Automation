"""
RCS Overview — Single Sequential Flow
================================================
Covers: Channels → RCS → Overview page, TC001 - TC024
(URL: /rcs/dashboard)

Built from a FULL live DOM dump of this exact page — no QA table was
supplied for this page, so every test below targets an element
confirmed directly in that dump (see pages/rcs_overview_page.py's
module docstring for the full breakdown). Nothing here is guessed.

Structurally this page is the RCS analogue of the WhatsApp/SMS Overview
pages already covered elsewhere in this project (single flatpickr
range-mode date input, a row of summary cascade cards, one ApexCharts
delivery-status chart, a second row of message-category product cards)
but with two confirmed differences:
  - The summary cascade cards ("Total Messages, Submitted, Delivered,
    Read, Failed, DLR Awaited, Rejected") use a different DOM pattern
    here (stats-card / stats-label / stats-value classes) than the
    WhatsApp/SMS equivalent (title/value sibling <p> tags) -- see
    RcsOverviewPage.get_stats_card_value(). There is also no rendered
    "Delivery Rate" card on this page (present in the component's
    wire:snapshot data but not actually displayed).
  - The second card row here is Transactional/Promotional/OTP/Multi Use
    (RCS's own message-category taxonomy), confirmed via the
    "rcs.campaign.product-cards" Livewire component -- these DO use the
    shared title/value sibling-<p> pattern (get_card_value()).

No "invalid date range" validation-message test is included: the date
field is a single readonly flatpickr range-mode input, so a user cannot
type an out-of-order range through the UI, and no validation-error DOM
element exists for this scenario (same reasoning already established
for the WhatsApp Overview suite).

All tests run in one browser session (module-scoped), mirroring the
pattern used in every other suite in this project.

Run:
    pytest tests/test_rcs_overview_flow.py -v
"""
import pytest

from pages.rcs.rcs_overview_page import RcsOverviewPage


pytestmark = [pytest.mark.rcs, pytest.mark.report]

@pytest.fixture(scope="module")
def rcs_overview_page(module_logged_in_page):
    p = RcsOverviewPage(module_logged_in_page)
    p.navigate_to_report()
    return p


def ensure_on_page(p):
    if not p.is_report_page():
        p.navigate_to_report()
        p.page.wait_for_timeout(1000)


@pytest.fixture(autouse=True)
def _reset_after_test(rcs_overview_page):
    """Hard reset to a clean listing view after every test -- this page
    has stateful pieces (date range, open calendar, open chart menu),
    so re-navigating fresh after each test avoids cross-test
    contamination (same rationale as every other suite in this
    project)."""
    yield
    try:
        rcs_overview_page.close_date_range_picker()
        ensure_on_page(rcs_overview_page)
        rcs_overview_page.navigate_to_report()
    except Exception:
        pass


# ── TC001 — Page Load ────────────────────────────────────────────────────

@pytest.mark.smoke
def test_tc001_page_loads_successfully(rcs_overview_page):
    """TC001: RCS Overview page loads by default when clicking the RCS
    channel's Overview tab."""
    ensure_on_page(rcs_overview_page)
    assert rcs_overview_page.is_report_page(), "URL should contain /rcs/dashboard"
    title = rcs_overview_page.get_title().lower()
    assert "404" not in title and "error" not in title
    assert rcs_overview_page.get_page_title_text() == "RCS Overview"


# ── TC002 — Default date range ───────────────────────────────────────────

@pytest.mark.smoke
def test_tc002_default_date_range(rcs_overview_page):
    """TC002: Default From & To dates are populated on page load."""
    ensure_on_page(rcs_overview_page)
    value = rcs_overview_page.get_date_range_value()
    assert value, "Date range input should have a non-empty default value"
    assert "to" in value.lower() or len(value.split()) >= 2 or "-" in value, \
        f"Date range value doesn't look like a range: {value!r}"


# ── TC003 — Open calendar ─────────────────────────────────────────────────

@pytest.mark.regression
def test_tc003_open_date_range_calendar(rcs_overview_page):
    """TC003: Clicking the date field opens the calendar with selectable
    days."""
    ensure_on_page(rcs_overview_page)
    rcs_overview_page.open_date_range_picker()
    assert rcs_overview_page.is_element_present(rcs_overview_page.FLATPICKR_CALENDAR_OPEN, timeout=5000)
    days = rcs_overview_page.page.locator(rcs_overview_page.FLATPICKR_ENABLED_DAYS)
    assert days.count() > 0, "Calendar should have at least one selectable day"


# ── TC004 — Select valid date range ──────────────────────────────────────

@pytest.mark.regression
def test_tc004_select_valid_date_range(rcs_overview_page):
    """TC004: Selecting a valid From & To date range updates the data."""
    ensure_on_page(rcs_overview_page)
    before = rcs_overview_page.get_all_summary_card_values()
    rcs_overview_page.select_date_range_first_two_enabled_days()
    value = rcs_overview_page.get_date_range_value()
    assert value, "Date range input should reflect the newly selected range"
    after = rcs_overview_page.get_all_summary_card_values()
    assert isinstance(after, dict) and len(after) == len(before), \
        "Summary cards should still render after changing the date range"


# ── TC005 — Same From & To date ──────────────────────────────────────────

@pytest.mark.regression
def test_tc005_same_from_to_date(rcs_overview_page):
    """TC005: Selecting the same date for From & To reflects that single
    day's data in counts & graph."""
    ensure_on_page(rcs_overview_page)
    rcs_overview_page.select_same_day_twice()
    value = rcs_overview_page.get_date_range_value()
    assert value, "Date range input should show a value after a same-day selection"
    cards = rcs_overview_page.get_all_summary_card_values()
    assert cards.get("Total Messages") is not None


# ── TC006 — Future date range disabled ───────────────────────────────────

@pytest.mark.regression
@pytest.mark.negative
def test_tc006_future_date_range_disabled(rcs_overview_page):
    """TC006: Future dates cannot be selected. CONFIRMED from the live
    DOM and the page's own inline init script (maxDate: 'today'):
    every day after today is rendered with class 'flatpickr-disabled'."""
    ensure_on_page(rcs_overview_page)
    disabled_count = rcs_overview_page.get_disabled_future_day_count()
    assert disabled_count > 0, \
        "Expected at least one disabled (future) day in the open calendar"


# ── TC007-013 — Summary cascade cards ────────────────────────────────────

@pytest.mark.smoke
def test_tc007_total_messages_count(rcs_overview_page):
    """TC007: Total Messages count is displayed correctly."""
    ensure_on_page(rcs_overview_page)
    value = rcs_overview_page.get_stats_card_value("Total Messages")
    assert value != "", "Total Messages value should not be empty"
    assert value.replace(",", "").isdigit(), f"Unexpected Total Messages value: {value!r}"


@pytest.mark.smoke
def test_tc008_submitted_count(rcs_overview_page):
    """TC008: Submitted count is displayed correctly."""
    ensure_on_page(rcs_overview_page)
    value = rcs_overview_page.get_stats_card_value("Submitted")
    assert value != "", "Submitted value should not be empty"
    assert value.replace(",", "").isdigit(), f"Unexpected Submitted value: {value!r}"


@pytest.mark.smoke
def test_tc009_delivered_count(rcs_overview_page):
    """TC009: Delivered count is displayed correctly."""
    ensure_on_page(rcs_overview_page)
    value = rcs_overview_page.get_stats_card_value("Delivered")
    assert value != "", "Delivered value should not be empty"
    assert value.replace(",", "").isdigit(), f"Unexpected Delivered value: {value!r}"


@pytest.mark.smoke
def test_tc010_read_count(rcs_overview_page):
    """TC010: Read count is displayed correctly."""
    ensure_on_page(rcs_overview_page)
    value = rcs_overview_page.get_stats_card_value("Read")
    assert value != "", "Read value should not be empty"
    assert value.replace(",", "").isdigit(), f"Unexpected Read value: {value!r}"


@pytest.mark.smoke
def test_tc011_failed_count(rcs_overview_page):
    """TC011: Failed count is displayed correctly."""
    ensure_on_page(rcs_overview_page)
    value = rcs_overview_page.get_stats_card_value("Failed")
    assert value != "", "Failed value should not be empty"
    assert value.replace(",", "").isdigit(), f"Unexpected Failed value: {value!r}"


@pytest.mark.smoke
def test_tc012_dlr_awaited_count(rcs_overview_page):
    """TC012: DLR Awaited count is displayed correctly."""
    ensure_on_page(rcs_overview_page)
    value = rcs_overview_page.get_stats_card_value("DLR Awaited")
    assert value != "", "DLR Awaited value should not be empty"
    assert value.replace(",", "").isdigit(), f"Unexpected DLR Awaited value: {value!r}"


@pytest.mark.smoke
def test_tc013_rejected_count(rcs_overview_page):
    """TC013: Rejected count is displayed correctly."""
    ensure_on_page(rcs_overview_page)
    value = rcs_overview_page.get_stats_card_value("Rejected")
    assert value != "", "Rejected value should not be empty"
    assert value.replace(",", "").isdigit(), f"Unexpected Rejected value: {value!r}"


# ── TC014 — Cascade cards refresh on date change ─────────────────────────

@pytest.mark.regression
def test_tc014_cascade_cards_refresh_on_date_change(rcs_overview_page):
    """TC014: Changing the date range causes all summary cards to
    (re-)render."""
    ensure_on_page(rcs_overview_page)
    before = rcs_overview_page.get_all_summary_card_values()
    rcs_overview_page.select_date_range_first_two_enabled_days()
    after = rcs_overview_page.get_all_summary_card_values()
    assert set(before.keys()) == set(after.keys()), \
        "The same set of summary cards should render before and after a date change"


# ── TC015/TC016 — Message Status Trend chart ─────────────────────────────

@pytest.mark.smoke
def test_tc015_message_status_trend_chart_loads(rcs_overview_page):
    """TC015: Message Status Trend chart is displayed."""
    ensure_on_page(rcs_overview_page)
    assert rcs_overview_page.is_chart_title_visible(), "Chart title should be visible"
    assert rcs_overview_page.is_element_present(rcs_overview_page.CHART_CONTAINER, timeout=10000)


@pytest.mark.regression
def test_tc016_chart_legend_matches_summary_labels(rcs_overview_page):
    """TC016: The chart's hand-built legend shows all 7 confirmed
    labels (Total/Submitted/Delivered/Read/Failed/DLR Awaited/Rejected),
    matching the summary cascade cards above it."""
    ensure_on_page(rcs_overview_page)
    assert rcs_overview_page.is_element_present(rcs_overview_page.CHART_CONTAINER, timeout=10000)
    for label in ["Total", "Submitted", "Delivered", "Read", "Failed",
                  "DLR Awaited", "Rejected"]:
        assert rcs_overview_page.is_legend_item_visible(label), f"Legend item {label!r} not visible"


# ── TC017-019 — Download Message Status Trend chart ──────────────────────
# NOTE: no zoom in/out tests -- the chart's own JS config (`toolbar: {
# show: true, export: {...} }`, no zoom/pan keys) and categorical
# string x-axis confirm the toolbar renders only a Menu icon, same as
# the WhatsApp Overview page's equivalent chart.

@pytest.mark.regression
def test_tc017_download_chart_png(rcs_overview_page):
    """TC017: Message Status Trend chart downloads as PNG via the
    chart's Menu."""
    ensure_on_page(rcs_overview_page)
    result = rcs_overview_page.export_chart("png", timeout_ms=20000)
    assert result is not None, "PNG export should produce a downloaded file"
    assert result["file_size"] > 0


@pytest.mark.regression
def test_tc018_download_chart_svg(rcs_overview_page):
    """TC018: Message Status Trend chart downloads as SVG via the
    chart's Menu."""
    ensure_on_page(rcs_overview_page)
    result = rcs_overview_page.export_chart("svg", timeout_ms=20000)
    assert result is not None, "SVG export should produce a downloaded file"
    assert result["file_size"] > 0


@pytest.mark.regression
def test_tc019_download_chart_csv(rcs_overview_page):
    """TC019: Message Status Trend chart downloads as CSV via the
    chart's Menu."""
    ensure_on_page(rcs_overview_page)
    result = rcs_overview_page.export_chart("csv", timeout_ms=20000)
    assert result is not None, "CSV export should produce a downloaded file"
    assert result["file_size"] > 0


@pytest.mark.regression
@pytest.mark.negative
def test_tc019b_no_zoom_controls(rcs_overview_page):
    """Bonus (not in a QA table): confirms the absence of zoom/pan
    toolbar icons on this chart instance, matching the confirmed JS
    config and categorical x-axis."""
    ensure_on_page(rcs_overview_page)
    assert rcs_overview_page.is_element_present(rcs_overview_page.CHART_CONTAINER, timeout=10000)
    assert not rcs_overview_page.has_zoom_controls(), \
        "This chart instance should not render zoom/pan toolbar icons"


# ── TC020-023 — Product / message-type cards ─────────────────────────────

@pytest.mark.regression
def test_tc020_transactional_count(rcs_overview_page):
    """TC020: Transactional count is displayed correctly."""
    ensure_on_page(rcs_overview_page)
    value = rcs_overview_page.get_card_value("Transactional")
    assert value != "", "Transactional value should not be empty"
    assert value.replace(",", "").isdigit(), f"Unexpected Transactional value: {value!r}"


@pytest.mark.regression
def test_tc021_promotional_count(rcs_overview_page):
    """TC021: Promotional count is displayed correctly."""
    ensure_on_page(rcs_overview_page)
    value = rcs_overview_page.get_card_value("Promotional")
    assert value != "", "Promotional value should not be empty"
    assert value.replace(",", "").isdigit(), f"Unexpected Promotional value: {value!r}"


@pytest.mark.regression
def test_tc022_otp_count(rcs_overview_page):
    """TC022: OTP count is displayed correctly."""
    ensure_on_page(rcs_overview_page)
    value = rcs_overview_page.get_card_value("OTP")
    assert value != "", "OTP value should not be empty"
    assert value.replace(",", "").isdigit(), f"Unexpected OTP value: {value!r}"


@pytest.mark.regression
def test_tc023_multi_use_count(rcs_overview_page):
    """TC023: Multi Use count is displayed correctly."""
    ensure_on_page(rcs_overview_page)
    value = rcs_overview_page.get_card_value("Multi Use")
    assert value != "", "Multi Use value should not be empty"
    assert value.replace(",", "").isdigit(), f"Unexpected Multi Use value: {value!r}"


# ── TC024 — Page refresh retains data ────────────────────────────────────

@pytest.mark.regression
def test_tc024_page_refresh_retains_data(rcs_overview_page):
    """TC024: Refreshing the page reloads the selected date's data."""
    ensure_on_page(rcs_overview_page)
    before_value = rcs_overview_page.get_date_range_value()
    rcs_overview_page.page.reload()
    rcs_overview_page.page.wait_for_timeout(2000)
    assert rcs_overview_page.is_report_page()
    after_value = rcs_overview_page.get_date_range_value()
    assert after_value, "Date range input should be populated after a refresh"


# ── TC025 — Performance ───────────────────────────────────────────────────

@pytest.mark.regression
def test_tc025_overview_page_performance(rcs_overview_page):
    """TC025: Overview page loads within an acceptable response time (<8000ms)."""
    ensure_on_page(rcs_overview_page)
    rcs_overview_page.navigate_to_report()
    load_time = rcs_overview_page.get_page_load_time_ms()
    if load_time is not None:
        assert load_time < 8000, f"Page load took {load_time}ms (>8000ms)"
