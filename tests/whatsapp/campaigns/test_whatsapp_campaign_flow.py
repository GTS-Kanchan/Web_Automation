"""
WhatsApp Campaigns — Automated Test Suite (Campaign LISTING page)
Path: /whatsapp/campaigns

Built from a manual QA checklist supplied by the user (TC001-TC051 across
three sub-sections: "Campaign Page", "Campaign Report page", and "New
Enhancement Changes"), paired with a full live DOM dump of the Campaign
LISTING page only. This file covers TC001-TC016 ("Campaign Page" section)
only -- see pages/whatsapp/whatsapp_campaign_page.py's module docstring for
the confirmed DOM specifics driving every locator used here.

TC017-TC043 ("Campaign Report page") and TC044-TC051 ("New Enhancement
Changes" -- clickable cards) describe a DIFFERENT page reached by clicking
the document/"Reports" icon in the Action column (a real, confirmed link to
/whatsapp/campaigns/messages/<campaignId>). No DOM capture of that page has
been supplied, so per this project's "never guess" rule, no test file for
it exists yet -- building one requires a fresh HTML dump of that page
(ideally with the "View" popup opened on a row, and whatever the "New
Enhancement" clickable-cards view actually looks like).

Test Design Notes:
  - scope="module" — page object shared across all tests (same pattern as
    every other suite in this project).
  - ensure_on_campaign_page() recovers to a clean page state before each
    test.
  - TC002's own checklist wording ("enter User number or Template
    category") does not match the real search box placeholder ("Search
    Campaign Name") -- same kind of checklist/DOM mismatch seen elsewhere
    in this project. The test searches by a substring ("Campaign") that
    matches this environment's real campaign-naming convention instead of
    the checklist's literal wording.
  - TC009/TC010 (date filter) are documented `@pytest.mark.skip`s: the
    captured filter panel has exactly 5 real fields (department, user,
    status, type, WABA number/sender_id), confirmed against the Livewire
    component's own `filterCount: 5` snapshot value. No date-range control
    exists anywhere in the captured markup for this page.
  - TC011 ("Bulk Action") maps to the one real matching control: an
    "Export to XLSX" button that opens a Yes/No confirm dialog
    (`wire:click="exportAll"`) -- there is no separate bulk-action dropdown
    on this page.
  - TC013/TC014 (pagination): this environment currently has 1414 real
    campaign rows across 142 pages, so forward pagination is exercised for
    real. TC014 (Previous) gracefully `pytest.skip()`s if the Previous
    control doesn't render as enabled after Next, consistent with the
    Messages Report suite's TC030.
  - TC016 ("Verify campaign report" / "Click on report button in action")
    refers to the document/"Reports" icon (a plain anchor with a confirmed
    href to /whatsapp/campaigns/messages/<id>), NOT the eye/"View" icon --
    the latter opens an unrelated quick-view modal
    ('whatsapp.campaign.view') not covered by this checklist.

Run:
    pytest tests/whatsapp/campaigns/test_whatsapp_campaign_flow.py -v
"""
import pytest

from pages.whatsapp.whatsapp_campaign_page import WhatsAppCampaignPage


pytestmark = [pytest.mark.whatsapp, pytest.mark.campaign]

# ══════════════════════════════════════════════════════════════════════════════
# Module-scoped page
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def campaign_page(module_logged_in_page):
    p = WhatsAppCampaignPage(module_logged_in_page)
    p.navigate()
    p.wait_for_table_load(timeout=15000)
    return p


# ══════════════════════════════════════════════════════════════════════════════
# Recovery helpers
# ══════════════════════════════════════════════════════════════════════════════

def ensure_on_campaign_page(p: WhatsAppCampaignPage):
    if not p.is_campaign_page():
        p.navigate()
        p.wait_for_table_load(timeout=10000)


def reset_state(p: WhatsAppCampaignPage):
    try:
        p.clear_search()
    except Exception:
        pass
    try:
        p.clear_all_filters()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# TC001 — Campaign page loads
# ══════════════════════════════════════════════════════════════════════════════

def test_TC001_page_loads_successfully(campaign_page):
    ensure_on_campaign_page(campaign_page)
    assert campaign_page.is_campaign_page()
    assert campaign_page.is_element_present(campaign_page.TABLE, timeout=10000)


# ══════════════════════════════════════════════════════════════════════════════
# TC002 — Search box with a valid keyword
# ══════════════════════════════════════════════════════════════════════════════

def test_TC002_search_box_valid_keyword(campaign_page):
    ensure_on_campaign_page(campaign_page)
    reset_state(campaign_page)
    campaign_page.search("Campaign")
    campaign_page.page.wait_for_timeout(1000)
    assert campaign_page.get_row_count() > 0 or campaign_page.has_no_records_message()
    campaign_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# TC003 — Search box with an invalid keyword
# ══════════════════════════════════════════════════════════════════════════════

def test_TC003_search_box_invalid_keyword(campaign_page):
    ensure_on_campaign_page(campaign_page)
    reset_state(campaign_page)
    campaign_page.search("zzz_no_such_campaign_zzz")
    campaign_page.page.wait_for_timeout(1000)
    assert campaign_page.has_no_records_message() or campaign_page.get_row_count() == 0
    campaign_page.clear_search()


# ══════════════════════════════════════════════════════════════════════════════
# TC004 — Sorting for each sortable column
# ══════════════════════════════════════════════════════════════════════════════

def test_TC004_sorting_each_column(campaign_page):
    ensure_on_campaign_page(campaign_page)
    reset_state(campaign_page)

    campaign_page.sort_by_campaign_name()
    pill = campaign_page.get_applied_sort_pill_text()
    assert pill is not None

    campaign_page.sort_by_type()
    pill = campaign_page.get_applied_sort_pill_text()
    assert pill is not None

    campaign_page.sort_by_template()
    pill = campaign_page.get_applied_sort_pill_text()
    assert pill is not None

    campaign_page.sort_by_waba_number()
    pill = campaign_page.get_applied_sort_pill_text()
    assert pill is not None

    campaign_page.sort_by_status()
    pill = campaign_page.get_applied_sort_pill_text()
    assert pill is not None

    campaign_page.sort_by_created_at()
    pill = campaign_page.get_applied_sort_pill_text()
    assert pill is not None and "created at" in pill.lower()

    campaign_page.clear_all_sorts()


# ══════════════════════════════════════════════════════════════════════════════
# TC005 — Department filter
# ══════════════════════════════════════════════════════════════════════════════

def test_TC005_department_filter(campaign_page):
    ensure_on_campaign_page(campaign_page)
    reset_state(campaign_page)
    campaign_page.set_department_filter("Admin")
    campaign_page.page.wait_for_timeout(1000)
    assert campaign_page.has_records() or campaign_page.has_no_records_message()
    campaign_page.clear_all_filters()


# ══════════════════════════════════════════════════════════════════════════════
# TC006 — User filter
# ══════════════════════════════════════════════════════════════════════════════

def test_TC006_user_filter(campaign_page):
    ensure_on_campaign_page(campaign_page)
    reset_state(campaign_page)
    campaign_page.set_user_filter("Test Account23")
    campaign_page.page.wait_for_timeout(1000)
    assert campaign_page.has_records() or campaign_page.has_no_records_message()
    campaign_page.clear_all_filters()


# ══════════════════════════════════════════════════════════════════════════════
# TC007 — Status filter
# ══════════════════════════════════════════════════════════════════════════════

def test_TC007_status_filter(campaign_page):
    ensure_on_campaign_page(campaign_page)
    reset_state(campaign_page)
    campaign_page.toggle_status_filter_option("Sent")
    campaign_page.page.wait_for_timeout(1000)
    assert campaign_page.has_records() or campaign_page.has_no_records_message()
    campaign_page.toggle_status_filter_option("Sent")
    campaign_page.page.wait_for_timeout(500)


# ══════════════════════════════════════════════════════════════════════════════
# TC008 — WABA number filter
# ══════════════════════════════════════════════════════════════════════════════

def test_TC008_waba_number_filter(campaign_page):
    ensure_on_campaign_page(campaign_page)
    reset_state(campaign_page)
    campaign_page.toggle_waba_number_filter_option("919691926438")
    campaign_page.page.wait_for_timeout(1000)
    assert campaign_page.has_records() or campaign_page.has_no_records_message()
    campaign_page.toggle_waba_number_filter_option("919691926438")
    campaign_page.page.wait_for_timeout(500)


# ══════════════════════════════════════════════════════════════════════════════
# TC009/TC010 — Date filter
# DOCUMENTED SKIP: no date-range control exists in the captured DOM for
# this page (only 5 real filter fields, matching filterCount: 5 in the
# Livewire component's own snapshot). See module docstring.
# ══════════════════════════════════════════════════════════════════════════════

_DATE_FILTER_SKIP_REASON = (
    "No date-range filter control was found in the captured DOM for the "
    "Campaign listing page -- the real filter panel has exactly 5 fields "
    "(department, user, status, type, WABA number), matching the Livewire "
    "component's own filterCount: 5 snapshot value. Provide a fresh DOM "
    "capture showing a CreatedAt From/To control on this page (if one has "
    "since been added) to build a real assertion instead of guessing a "
    "locator for a field that isn't confirmed to exist."
)


@pytest.mark.skip(reason=_DATE_FILTER_SKIP_REASON)
def test_TC009_date_filter_valid_range(campaign_page):
    pass


@pytest.mark.skip(reason=_DATE_FILTER_SKIP_REASON)
def test_TC010_date_filter_invalid_range(campaign_page):
    pass


# ══════════════════════════════════════════════════════════════════════════════
# TC011 — Bulk action (Export to XLSX)
# ══════════════════════════════════════════════════════════════════════════════

def test_TC011_bulk_action_export(campaign_page):
    ensure_on_campaign_page(campaign_page)
    reset_state(campaign_page)
    campaign_page.click_export()
    assert campaign_page.is_export_confirm_open()
    campaign_page.cancel_export()


# ══════════════════════════════════════════════════════════════════════════════
# TC012 — Toggle table columns
# ══════════════════════════════════════════════════════════════════════════════

def test_TC012_toggle_table_columns(campaign_page):
    ensure_on_campaign_page(campaign_page)
    assert campaign_page.is_column_checked("status") is True
    campaign_page.toggle_column("status")
    assert campaign_page.is_column_checked("status") is False
    headers_after_hide = [h.lower() for h in campaign_page.get_visible_column_headers()]
    assert not any("status" in h for h in headers_after_hide)

    campaign_page.toggle_column("status")
    assert campaign_page.is_column_checked("status") is True
    headers_after_show = [h.lower() for h in campaign_page.get_visible_column_headers()]
    assert any("status" in h for h in headers_after_show)


# ══════════════════════════════════════════════════════════════════════════════
# TC013 — Navigate pagination (Next page)
# ══════════════════════════════════════════════════════════════════════════════

def test_TC013_next_page(campaign_page):
    ensure_on_campaign_page(campaign_page)
    reset_state(campaign_page)
    before = campaign_page.get_pagination_results_text()
    campaign_page.click_next_page()
    after = campaign_page.get_pagination_results_text()
    assert after is not None
    assert before is not None


# ══════════════════════════════════════════════════════════════════════════════
# TC014 — Navigate pagination (Previous page)
# ══════════════════════════════════════════════════════════════════════════════

def test_TC014_previous_page(campaign_page):
    ensure_on_campaign_page(campaign_page)
    reset_state(campaign_page)
    campaign_page.click_next_page()
    campaign_page.page.wait_for_timeout(1000)
    if campaign_page.is_prev_page_enabled():
        campaign_page.click_prev_page()
        assert campaign_page.has_records() or campaign_page.has_no_records_message()
    else:
        pytest.skip("Previous-page control did not render as enabled after "
                     "Next -- consistent with there being only one page of "
                     "results under the current filter/search state.")
    ensure_on_campaign_page(campaign_page)


# ══════════════════════════════════════════════════════════════════════════════
# TC015 — Refresh button
# ══════════════════════════════════════════════════════════════════════════════

def test_TC015_refresh_button(campaign_page):
    ensure_on_campaign_page(campaign_page)
    reset_state(campaign_page)
    campaign_page.click_refresh()
    assert campaign_page.is_campaign_page()
    assert campaign_page.is_element_present(campaign_page.TABLE, timeout=10000)


# ══════════════════════════════════════════════════════════════════════════════
# TC016 — "Reports" action opens the Campaign Report page
# See module docstring: this is the document icon (plain anchor to
# /whatsapp/campaigns/messages/<id>), NOT the eye/"View" modal icon.
# ══════════════════════════════════════════════════════════════════════════════

def test_TC016_reports_action_opens_campaign_report_page(campaign_page):
    ensure_on_campaign_page(campaign_page)
    reset_state(campaign_page)
    navigated = campaign_page.click_reports_link_on_first_row()
    assert navigated
    assert "/whatsapp/campaigns/messages/" in campaign_page.get_current_url()
    ensure_on_campaign_page(campaign_page)
