"""
Test Suite: Chatbot -> Download Center -> Create Request Report (Single-session E2E flow)
===========================================================================================
Test Cases:
  CHATBOT_REPORT_001 – CHATBOT_REPORT_004: Page Load, Breadcrumb & Field Inspection (4 TCs)
  CHATBOT_REPORT_005 – CHATBOT_REPORT_009: Report Name Validation & Input Handling (5 TCs)
  CHATBOT_REPORT_010 – CHATBOT_REPORT_017: Bot Type Dropdown & Option Selection (8 TCs)
  CHATBOT_REPORT_018 – CHATBOT_REPORT_027: Date Fields & Boundary Constraints (10 TCs)
Total: 27 test cases.

Target Page: /chatbot/download/center/create

Run:
    pytest tests/chatbot/download_center/test_chatbot_request_report_flow.py -v
"""

from datetime import datetime, timedelta
import pytest

from pages.chatbot.chatbot_request_report_page import ChatbotRequestReportPage
from constants.chatbot_report_constants import (
    EXPECTED_PAGE_HEADING,
    EXPECTED_PAGE_SUBHEADING,
    EXPECTED_BREADCRUMB_ITEMS,
    EXPECTED_REPORT_NAME_PLACEHOLDER,
    REPORT_NAME_MAX_LENGTH,
    EXPECTED_BOT_TYPES,
    BOT_TYPE_OPTIONS_MAP,
    FROM_DATE_HELPER_TEXT,
    TO_DATE_HELPER_TEXT,
    MAX_HISTORICAL_DAYS,
)


pytestmark = [
    pytest.mark.chatbot,
    pytest.mark.report,
]


# ══════════════════════════════════════════════════════════════════════════════
# Fixture & Form State Helper
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def report_page(module_logged_in_page):
    """Module-level fixture navigating once to the Create Request Report page."""
    p = ChatbotRequestReportPage(module_logged_in_page)
    p.navigate()
    return p


def ensure_on_report_page(p: ChatbotRequestReportPage):
    """Ensure browser is currently on the Request a Report page."""
    if not p.is_request_report_page():
        p.navigate()


def reset_form_state(p: ChatbotRequestReportPage):
    """Reset form fields to a clean initial state."""
    try:
        p.clear_report_name()
    except Exception:
        pass

    try:
        p.select_bot_type("")
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# Page Load & Field Inspection (CHATBOT_REPORT_001 – CHATBOT_REPORT_004)
# ══════════════════════════════════════════════════════════════════════════════

def test_CHATBOT_REPORT_001_verify_page_loads(report_page):
    """Request a Report page loads successfully."""
    ensure_on_report_page(report_page)
    assert report_page.is_request_report_page(), "Create Request Report page should load"
    assert report_page.get_heading_text() == EXPECTED_PAGE_HEADING, (
        f"Heading should be '{EXPECTED_PAGE_HEADING}'"
    )
    assert EXPECTED_PAGE_SUBHEADING in report_page.get_subheading_text()


def test_CHATBOT_REPORT_002_verify_breadcrumb(report_page):
    """Check Home > Download Center > Create Request Report breadcrumb."""
    ensure_on_report_page(report_page)
    bc_text = report_page.get_breadcrumb_text()
    for item in EXPECTED_BREADCRUMB_ITEMS:
        assert item in bc_text, f"Breadcrumb '{bc_text}' should contain '{item}'"


def test_CHATBOT_REPORT_003_verify_report_name_field(report_page):
    """Report Name field is displayed and marked mandatory."""
    ensure_on_report_page(report_page)
    assert report_page.is_report_name_visible(), "Report Name field should be visible"
    assert report_page.is_report_name_mandatory(), "Report Name field should be marked mandatory"


def test_CHATBOT_REPORT_004_verify_report_name_placeholder(report_page):
    """Placeholder such as 'e.g., Weekly Chatbot Report' is displayed."""
    ensure_on_report_page(report_page)
    placeholder = report_page.get_report_name_placeholder()
    assert EXPECTED_REPORT_NAME_PLACEHOLDER in placeholder, (
        f"Expected placeholder '{EXPECTED_REPORT_NAME_PLACEHOLDER}', got '{placeholder}'"
    )


# ══════════════════════════════════════════════════════════════════════════════
# Report Name Validation (CHATBOT_REPORT_005 – CHATBOT_REPORT_009)
# ══════════════════════════════════════════════════════════════════════════════

def test_CHATBOT_REPORT_005_generate_report_without_report_name(report_page):
    """Validation message is displayed and report is not generated when name is empty."""
    ensure_on_report_page(report_page)
    reset_form_state(report_page)
    report_page.clear_report_name()
    report_page.click_generate_report()

    # Verify form is not submitted: still on create page or validation error shown
    assert report_page.is_request_report_page(), (
        "Should remain on Request a Report page when mandatory Report Name is missing"
    )


def test_CHATBOT_REPORT_006_enter_valid_report_name(report_page):
    """Enter a valid report name -> accepted."""
    ensure_on_report_page(report_page)
    valid_name = "Weekly Chatbot Audit 2026"
    report_page.enter_report_name(valid_name)
    assert report_page.get_report_name_value() == valid_name, (
        "Report name should match entered value"
    )


def test_CHATBOT_REPORT_007_enter_whitespace_only_report_name(report_page):
    """Enter only spaces and click Generate Report -> validation prevents submission."""
    ensure_on_report_page(report_page)
    report_page.enter_report_name("     ")
    report_page.click_generate_report()
    assert report_page.is_request_report_page(), (
        "Whitespace-only report name should not trigger report generation"
    )


def test_CHATBOT_REPORT_008_enter_very_long_report_name(report_page):
    """Application validates or limits input according to maximum length (100 chars)."""
    ensure_on_report_page(report_page)
    max_len = report_page.get_report_name_maxlength()
    assert max_len == REPORT_NAME_MAX_LENGTH, (
        f"Expected Report Name maxlength to be {REPORT_NAME_MAX_LENGTH}, got {max_len}"
    )
    long_name = "A" * 120
    report_page.enter_report_name(long_name)
    actual_value = report_page.get_report_name_value()
    assert len(actual_value) <= REPORT_NAME_MAX_LENGTH, (
        f"Input should be capped at {REPORT_NAME_MAX_LENGTH} characters"
    )


def test_CHATBOT_REPORT_009_enter_special_characters_in_report_name(report_page):
    """Input special characters handled correctly without UI/API error."""
    ensure_on_report_page(report_page)
    special_name = "Report #1 - Test & Demo (2026)!"
    report_page.enter_report_name(special_name)
    assert report_page.get_report_name_value() == special_name, (
        "Report name with special characters should be accepted"
    )
    reset_form_state(report_page)


# ══════════════════════════════════════════════════════════════════════════════
# Bot Type Dropdown (CHATBOT_REPORT_010 – CHATBOT_REPORT_017)
# ══════════════════════════════════════════════════════════════════════════════

def test_CHATBOT_REPORT_010_verify_bot_type_dropdown(report_page):
    """Dropdown opens and available bot types are displayed."""
    ensure_on_report_page(report_page)
    assert report_page.is_bot_type_dropdown_visible(), "Bot Type dropdown should be visible"
    options = report_page.get_bot_type_options()
    for expected in EXPECTED_BOT_TYPES:
        assert expected in options, f"Option '{expected}' should be in Bot Type dropdown: {options}"


def test_CHATBOT_REPORT_011_verify_default_bot_type(report_page):
    """Default value is 'All Types'."""
    ensure_on_report_page(report_page)
    reset_form_state(report_page)
    selected = report_page.get_selected_bot_type()
    assert selected == "All Types", f"Default Bot Type should be 'All Types', got '{selected}'"


def test_CHATBOT_REPORT_012_select_all_types(report_page):
    """Select 'All Types'."""
    ensure_on_report_page(report_page)
    report_page.select_bot_type("All Types")
    assert report_page.get_selected_bot_type() == "All Types"
    assert report_page.get_selected_bot_type_value() == ""


def test_CHATBOT_REPORT_013_select_web(report_page):
    """Select 'Web' from Bot Type."""
    ensure_on_report_page(report_page)
    report_page.select_bot_type("web")
    assert report_page.get_selected_bot_type() == "Web"
    assert report_page.get_selected_bot_type_value() == "web"


def test_CHATBOT_REPORT_014_select_whatsapp(report_page):
    """Select 'WhatsApp' from Bot Type."""
    ensure_on_report_page(report_page)
    report_page.select_bot_type("whatsapp")
    assert report_page.get_selected_bot_type() == "WhatsApp"
    assert report_page.get_selected_bot_type_value() == "whatsapp"


def test_CHATBOT_REPORT_015_select_telegram(report_page):
    """Select 'Telegram' from Bot Type."""
    ensure_on_report_page(report_page)
    report_page.select_bot_type("telegram")
    assert report_page.get_selected_bot_type() == "Telegram"
    assert report_page.get_selected_bot_type_value() == "telegram"


def test_CHATBOT_REPORT_016_select_rcs(report_page):
    """Select 'RCS' from Bot Type."""
    ensure_on_report_page(report_page)
    report_page.select_bot_type("rcs")
    assert report_page.get_selected_bot_type() == "RCS"
    assert report_page.get_selected_bot_type_value() == "rcs"


def test_CHATBOT_REPORT_017_select_facebook(report_page):
    """Select 'Facebook' from Bot Type."""
    ensure_on_report_page(report_page)
    report_page.select_bot_type("facebook")
    assert report_page.get_selected_bot_type() == "Facebook"
    assert report_page.get_selected_bot_type_value() == "facebook"
    reset_form_state(report_page)


# ══════════════════════════════════════════════════════════════════════════════
# Date Fields & Boundary Constraints (CHATBOT_REPORT_018 – CHATBOT_REPORT_027)
# ══════════════════════════════════════════════════════════════════════════════

def test_CHATBOT_REPORT_018_verify_from_date_field(report_page):
    """From Date is displayed and marked mandatory."""
    ensure_on_report_page(report_page)
    assert report_page.is_from_date_visible(), "From Date field should be visible"
    assert report_page.is_from_date_mandatory(), "From Date should be marked mandatory"


def test_CHATBOT_REPORT_019_verify_from_date_maximum_range(report_page):
    """From Date cannot exceed configured 90-day historical limit."""
    ensure_on_report_page(report_page)
    helper = report_page.get_from_date_helper_text()
    assert FROM_DATE_HELPER_TEXT in helper, (
        f"Expected helper text '{FROM_DATE_HELPER_TEXT}', got '{helper}'"
    )
    min_date = report_page.get_from_date_min()
    assert min_date != "", "From Date min attribute should be configured"


def test_CHATBOT_REPORT_020_select_valid_from_date(report_page):
    """Select a date within allowed range -> accepted."""
    ensure_on_report_page(report_page)
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    report_page.enter_from_date(yesterday)
    assert report_page.get_from_date_value() == yesterday, "Valid from_date should be accepted"


def test_CHATBOT_REPORT_021_select_date_older_than_90_days(report_page):
    """Attempt to select a date older than allowed range -> prevented or invalid."""
    ensure_on_report_page(report_page)
    min_date = report_page.get_from_date_min()
    too_old_date = (datetime.now() - timedelta(days=120)).strftime("%Y-%m-%d")

    # Entering a date older than min
    report_page.enter_from_date(too_old_date)
    val = report_page.get_from_date_value()

    # The browser's HTML5 validity or min attribute restricts it
    if min_date:
        is_valid = report_page.check_input_validity(report_page.from_date_input)
        assert not is_valid or val >= min_date, (
            f"Date older than {min_date} should be marked invalid or prevented"
        )


def test_CHATBOT_REPORT_022_verify_to_date_field(report_page):
    """To Date is displayed and marked mandatory."""
    ensure_on_report_page(report_page)
    assert report_page.is_to_date_visible(), "To Date field should be visible"
    assert report_page.is_to_date_mandatory(), "To Date should be marked mandatory"


def test_CHATBOT_REPORT_023_verify_to_date_maximum(report_page):
    """To Date is restricted to maximum yesterday as shown in UI."""
    ensure_on_report_page(report_page)
    helper = report_page.get_to_date_helper_text()
    assert TO_DATE_HELPER_TEXT in helper, (
        f"Expected helper text '{TO_DATE_HELPER_TEXT}', got '{helper}'"
    )
    max_date = report_page.get_to_date_max()
    assert max_date != "", "To Date max attribute should be configured"


def test_CHATBOT_REPORT_024_select_valid_to_date(report_page):
    """Select a valid date up to yesterday -> accepted."""
    ensure_on_report_page(report_page)
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    report_page.enter_to_date(yesterday)
    assert report_page.get_to_date_value() == yesterday, "Valid to_date should be accepted"


def test_CHATBOT_REPORT_025_select_future_to_date(report_page):
    """Future date cannot be selected or validation is displayed."""
    ensure_on_report_page(report_page)
    max_date = report_page.get_to_date_max()
    future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    report_page.enter_to_date(future_date)
    val = report_page.get_to_date_value()

    if max_date:
        is_valid = report_page.check_input_validity(report_page.to_date_input)
        assert not is_valid or val <= max_date, (
            f"Date beyond max '{max_date}' should be marked invalid or prevented"
        )


def test_CHATBOT_REPORT_026_from_date_greater_than_to_date(report_page):
    """Set From Date later than To Date -> validation prevents generation."""
    ensure_on_report_page(report_page)
    report_page.enter_report_name("Invalid Date Range Test")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    two_days_ago = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")

    # From Date is yesterday, To Date is two days ago (From > To)
    report_page.enter_from_date(yesterday)
    report_page.enter_to_date(two_days_ago)

    report_page.click_generate_report()
    assert report_page.is_request_report_page(), (
        "Application should prevent generation when From Date > To Date"
    )
    reset_form_state(report_page)


def test_CHATBOT_REPORT_027_from_date_equal_to_to_date(report_page):
    """Set both dates to the same valid date -> single-day range accepted."""
    ensure_on_report_page(report_page)
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    report_page.enter_from_date(yesterday)
    report_page.enter_to_date(yesterday)

    assert report_page.get_from_date_value() == yesterday
    assert report_page.get_to_date_value() == yesterday

    is_from_valid = report_page.check_input_validity(report_page.from_date_input)
    is_to_valid = report_page.check_input_validity(report_page.to_date_input)
    assert is_from_valid and is_to_valid, "Same-day valid dates should be valid in HTML5 inputs"
    reset_form_state(report_page)
