"""
test_sms_campaign_short_url_click_dlr.py

Test Case: Verify DLR and Short URL Click Count
DLR Verification API: POST {dlr_base_url}/api/v1/dlr/verify

The template comes ONLY from .env, its own dedicated variable (kept
separate from SMS_TRANSACTION_TEMPLATE, used by the sibling
test_sms_campaign_transaction_template_dlr.py, so the two tests can be
pointed at different templates independently):
    SMS_URL_CLICK_TEMPLATE=test_url_template
    SMS_URL_CLICK_TEMPLATE_TYPE=TRANSACTIONAL

Steps 1-9 (launch the campaign with that template, find it, open its
report, collect every recipient's message_id via View, ONE bulk
POST /api/v1/dlr/verify, every id must have a correlated DLR) reuse
utils/campaign_dlr.verify_campaign_dlrs() exactly as
test_sms_campaign_transaction_template_dlr.py and
test_sms_campaign_otp_test_dlr.py do -- nothing about that flow is
reimplemented here.

What THIS test adds on top (steps 10-16 of the spec) needed one small,
purely-additive extension to utils/campaign_dlr.py: _collect_message_ids()
already opens each recipient's message-details popup to read
get_popup_message_id() -- it now ALSO reads get_popup_content() (falling
back to get_popup_all_text()) from that SAME already-open popup and
returns it as message_contents[label], with no extra View click/page
load. CampaignDlrResult carries this new field; existing callers that
never look at it are unaffected -- confirmed via
`pytest tests/sms/campaigns --collect-only` after the change (104 tests
still collect, same as before).

Locating the short URL (step 6): scans every collected recipient's
message_contents for the first http(s) URL (a generic URL regex -- no
specific short-link domain is assumed/fabricated, since none was ever
confirmed for this app; whatever real short-link host the template
renders is picked up as-is). If the template's short-link merge field
renders the SAME link for every recipient (unconfirmed either way --
never verified against a real send), this still works: it just finds
that shared link on the first recipient whose popup content contains it.

Click count (steps 10, 14-15): the per-campaign report page's own
"Total Clicks" stat card (SmsCampaignMessageReportPage.get_card_value(),
CONFIRMED real element -- see that class's docstring and
test_sms_campaign_message_report_flow.py) is used as `click_count`, since
it is the only place on this page a numeric click COUNT genuinely exists
structurally. (The card's own drill-down table, reached via
click_report_card("Total Clicks"), lists individual CLICK EVENTS with a
"Clicked URL" column -- confirmed real headers: Contact/Status/Clicked
URL/Clicked At/Browser-Device-OS/Geo Location-IP -- but that table has no
row at all for a not-yet-clicked message, so it cannot supply the *before*
count; the stat card can.) Per the spec's own "Important" note, this does
NOT assume the count starts at 0 -- it reads the real value before
clicking. The spec's own steps/example walk through exactly ONE click
("click URL once ... final_click_count = X + 1"); this test clicks
NUM_CLICKS times instead (5 by default) and asserts the real value after
clicking is exactly `initial + NUM_CLICKS`, generalizing the same "no
more, no less" check the spec applies to one click.

Clicking the short URL (steps 11-13): opened in a NEW Playwright page in
the same browser context (logged_in_page.context.new_page()) rather than
navigating logged_in_page itself, so the authenticated dashboard session/
tab is never disturbed. A genuine browser navigation (page.goto), not a
raw HTTP request -- matches "click/open the short URL" and lets Playwright's
own redirect-following confirm "the URL redirects successfully" via the
final page.url differing from the short URL requested.

DLR-after-click (step 16): re-checks the SAME message_id with
utils/dlr_helpers.poll_for_dlr() (the standard single-id DLR poll used
everywhere else in this suite) after the click, asserting received is
still true -- proving the click didn't disturb DLR state, not re-deriving
DLR status_code/provider_status (still deliberately not validated
anywhere in this test, per the spec).
"""

import re
import time

import pytest

from pages.sms.sms_campaign_page import SMSCampaignPage
from pages.sms.campaigns.sms_campaign_message_report_page import SmsCampaignMessageReportPage
from utils.campaign_dlr import verify_campaign_dlrs
from utils.config import Config
from utils.dlr_format_validator import (
    build_click_validation_report,
    build_dlr_validation_report,
    extract_click_fields,
    extract_full_dlr_fields,
    is_click_event_body,
    validate_click_correlation,
    validate_click_format,
    validate_dlr_correlation,
    validate_dlr_format,
)
from utils.dlr_helpers import DLR_POLL_TIMEOUT_SECONDS, poll_for_dlr

pytestmark = [pytest.mark.sms, pytest.mark.campaign]

TEMPLATE = Config.SMS_URL_CLICK_TEMPLATE
TEMPLATE_TYPE = Config.SMS_URL_CLICK_TEMPLATE_TYPE or "TRANSACTIONAL"
SENDER_ID = Config.SMS_SENDER_ID
PASTE_CONTACTS = Config.SMS_PASTE_CONTACTS.replace("\\n", "\n")

# Two matchers, tried in order -- no specific short-link domain is assumed
# (never fabricated), only the SHAPE is generic:
#   1. An explicit http(s):// URL.
#   2. A SCHEME-LESS short link -- CONFIRMED necessary from a real message
#      body pasted by the project owner:
#          "Click on the link below:\n stqa.gtls.in/DUMMY/PpA/KZ3T2Z"
#      i.e. a bare "<labels>.<tld>/<path>" with no "http(s)://" prefix at
#      all. Requires a real dotted host (>=2 labels, letters-only TLD)
#      followed by "/" and at least one more path character, so it won't
#      match an ordinary sentence that merely contains a "word.word"
#      (e.g. an abbreviation) with no path after it.
# Both trim common trailing punctuation a sentence might leave attached to
# the URL (".", ",", ")", "]", etc.).
URL_RE = re.compile(r"https?://[^\s<>\"']+")
SCHEMELESS_URL_RE = re.compile(
    r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}/[^\s<>\"']+"
)
_TRAILING_PUNCT = ".,);]}\"'"

# Not given a concrete number by the spec ("wait for the click event to be
# processed" has no attached timeout) -- bounds what would otherwise be an
# unbounded reload loop. Tighten once real click-tracking latency is
# confirmed for this instance.
CLICK_COUNT_POLL_TIMEOUT_SECONDS = 60
CLICK_COUNT_POLL_INTERVAL_SECONDS = 5

# Number of times the short URL is clicked/opened. The original spec's
# own steps/example only walk through ONE click ("initial_click_count = X
# ... click URL once ... final_click_count = X + 1") -- raised to 5 per
# request, generalized below (expected_click_count = initial + NUM_CLICKS)
# rather than hard-coding "+1" or "+5" separately.
NUM_CLICKS = 5


def _print_summary(record_property, rows):
    width = max(len(k) for k, _ in rows)
    for k, v in rows:
        record_property(k, v)
    print("\n" + "\n".join(f"{k.ljust(width)}   {v}" for k, v in rows))


def _extract_short_url(text):
    text = text or ""
    match = URL_RE.search(text) or SCHEMELESS_URL_RE.search(text)
    if not match:
        return None
    url = match.group(0)
    return url.rstrip(_TRAILING_PUNCT)


def _navigable_url(short_url):
    """A scheme-less short link (see SCHEMELESS_URL_RE above) isn't a
    valid Playwright goto() target as-is -- add "https://" so it can
    actually be opened. The unmodified `short_url` (as it appeared in the
    message) is still what's recorded/reported; this is only the click
    target."""
    return short_url if re.match(r"^https?://", short_url) else f"https://{short_url}"


def _goto_with_cert_fallback(page, url, had_scheme, timeout=30000):
    """Navigates to *url*, returning the URL actually used.

    If the app's message literally had NO scheme of its own (so
    "https://" was only added by _navigable_url(), never sent by the
    app) and the navigation fails with a CERTIFICATE error, retries once
    over plain http:// -- a real, CONFIRMED staging-environment quirk
    (net::ERR_CERT_COMMON_NAME_INVALID on the short-link host, from an
    actual pytest run against it), not a blanket bypass of certificate
    checks: a scheme the app itself sent (an explicit https:// URL in the
    message body) is never downgraded, and a non-certificate failure is
    never retried. Re-raises the original exception when the fallback
    doesn't apply or also fails."""
    try:
        page.goto(url, wait_until="load", timeout=timeout)
        return url
    except Exception as exc:
        is_cert_error = "cert" in str(exc).lower()
        if is_cert_error and not had_scheme and url.startswith("https://"):
            fallback_url = "http://" + url[len("https://"):]
            page.goto(fallback_url, wait_until="load", timeout=timeout)
            return fallback_url
        raise


def _create_and_launch(campaign_page, name, template):
    """Name -> sender -> template (required) -> paste contacts -> Send Now ->
    Preview -> Launch. Returns None on success, else the failure reason.
    Identical sequence to
    test_sms_campaign_transaction_template_dlr.py::_create_and_launch --
    kept local (not imported from that test module), since test modules
    aren't meant to be imported as shared libraries in this suite."""
    campaign_page.open_campaign_list()
    campaign_page.click_create_campaign()
    campaign_page.page.wait_for_timeout(1000)
    campaign_page.enter_campaign_name(name)

    try:
        campaign_page.select_sender_id(SENDER_ID)
    except Exception as exc:
        return f"sender ID '{SENDER_ID}' could not be selected: {exc}"
    try:
        campaign_page.select_template(template)
    except Exception as exc:
        return f"template '{template}' could not be selected: {exc}"

    campaign_page.click_import_contact()
    campaign_page.paste_contacts(PASTE_CONTACTS)
    campaign_page.click_import_confirm()
    campaign_page.page.wait_for_timeout(1000)
    if campaign_page.is_campaign_list_page():
        return None  # app auto-submitted after import

    campaign_page.select_send_now()
    campaign_page.page.wait_for_timeout(1000)
    if campaign_page.is_campaign_list_page():
        return None

    campaign_page.click_preview()
    campaign_page.page.wait_for_timeout(1000)
    if campaign_page.is_campaign_list_page():
        return None
    if not campaign_page.is_preview_open():
        return "preview did not open, campaign could not be launched"
    campaign_page.page.wait_for_timeout(2000)
    campaign_page.click_launch_campaign()

    deadline = time.time() + 20
    while time.time() < deadline:
        campaign_page.confirm_swal(timeout=1000)
        if campaign_page.is_campaign_list_page():
            return None
        if campaign_page.is_element_present(campaign_page.TOAST_SUCCESS, timeout=1000):
            return None
        campaign_page.page.wait_for_timeout(500)
    return f"no success signal after Launch (URL: {campaign_page.get_current_url()})"


def _read_click_count(report_page, summary, record_property, step_label):
    raw = report_page.get_card_value("Total Clicks")
    digits = re.sub(r"[^\d]", "", raw or "")
    if not digits:
        summary.append((step_label, "FAIL"))
        summary.append(("Final Result", "FAIL"))
        _print_summary(record_property, summary)
        pytest.fail(
            f"Click count cannot be retrieved -- 'Total Clicks' stat card "
            f"rendered {raw!r}, which has no digits."
        )
    return int(digits)


@pytest.mark.smoke
def test_dlr_and_short_url_click_count(api_client, logged_in_page, record_property):
    # Step 1 (template from .env only, same guard as the sibling test)
    if not TEMPLATE:
        _print_summary(record_property, [("Click Template", "<not set>"), ("Final Result", "FAIL")])
        pytest.fail("Click-count template is not available in .env: set SMS_URL_CLICK_TEMPLATE=<template name>")

    summary = [("Click Template", TEMPLATE), ("Template Type", TEMPLATE_TYPE)]

    # ── Step 1: run the SMS UI campaign with the transaction template ───────
    campaign_page = SMSCampaignPage(logged_in_page)
    name = f"{Config.SMS_CAMPAIGN_PREFIX}_CLICK_{int(time.time())}"
    error = _create_and_launch(campaign_page, name, TEMPLATE)
    if error:
        _print_summary(record_property, summary + [("Campaign", name), ("Campaign execution", "FAIL"),
                                                   ("Final Result", "FAIL")])
        pytest.fail(f"Campaign creation failed for '{name}' with template '{TEMPLATE}': {error}")
    summary.append(("Campaign execution", "PASS"))

    # ── Steps 2-9: Campaigns list -> search -> Reports -> collect every
    #               recipient's message_id (+ message content, for the short
    #               URL below) -> ONE bulk DLR verify -> all DLRs received ──
    expected = len([n for n in PASTE_CONTACTS.split("\n") if n.strip()])
    result = verify_campaign_dlrs(logged_in_page, api_client, name, record_property=record_property,
                                  expected_recipients=expected, summary_prefix=summary)
    summary = list(result.summary)  # verify_campaign_dlrs already recorded/printed PASS rows through here

    # ── Step 6 (cont'd)/7: identify the short URL among the collected
    #               message bodies -- first recipient whose popup content
    #               contains one, in collection order ──────────────────────
    short_url = None
    short_url_label = None
    for label, content in result.message_contents.items():
        url = _extract_short_url(content)
        if url:
            short_url, short_url_label = url, label
            break

    if not short_url:
        summary.append(("Short URL found", "FAIL"))
        summary.append(("Final Result", "FAIL"))
        _print_summary(record_property, summary)
        pytest.fail(
            f"Short URL cannot be found in any of the {len(result.message_contents)} "
            f"collected message(s) for campaign '{name}'."
        )
    summary.append(("Short URL found", "PASS"))
    record_property("short_url", short_url)
    record_property("short_url_recipient", short_url_label)
    message_id = result.message_ids[short_url_label]
    record_property("short_url_message_id", message_id)

    # ── Step 10: record the click count BEFORE clicking -- never assumed
    #             to start at 0, per the spec's own "Important" note ───────
    report_page = SmsCampaignMessageReportPage(logged_in_page)
    initial_click_count = _read_click_count(report_page, summary, record_property, "Initial click count")
    summary.append(("Initial click count", str(initial_click_count)))
    record_property("initial_click_count", str(initial_click_count))

    # ── Steps 11-12: click/open the short URL NUM_CLICKS times, each in its
    #                 own new tab (same browser context, so logged_in_page's
    #                 session is undisturbed), verifying every single click
    #                 actually redirects before moving to the next one ─────
    click_target = _navigable_url(short_url)
    had_scheme = bool(re.match(r"^https?://", short_url))
    record_property("short_url_click_target", click_target)

    for click_no in range(1, NUM_CLICKS + 1):
        click_page = logged_in_page.context.new_page()
        try:
            try:
                used_target = _goto_with_cert_fallback(click_page, click_target, had_scheme)
                if click_no == 1 and used_target != click_target:
                    record_property("short_url_click_target_used", used_target)
            except Exception as exc:
                summary.append((f"URL clicked ({click_no}/{NUM_CLICKS})", "FAIL"))
                summary.append(("Final Result", "FAIL"))
                _print_summary(record_property, summary)
                pytest.fail(f"Short URL '{short_url}' could not be opened on click {click_no}: {exc}")

            final_url = click_page.url
            if click_no == 1:
                record_property("short_url_final_url", final_url)
            if final_url.rstrip("/") == used_target.rstrip("/"):
                summary.append((f"URL redirected ({click_no}/{NUM_CLICKS})", "FAIL"))
                summary.append(("Final Result", "FAIL"))
                _print_summary(record_property, summary)
                pytest.fail(
                    f"Short URL '{short_url}' did not redirect on click {click_no} -- "
                    f"final page URL is identical to the short URL."
                )

            # ── Step 13: wait for this click event to be processed before
            #             firing the next one ─────────────────────────────
            click_page.wait_for_timeout(2000)
        finally:
            click_page.close()
    summary.append(("URL clicked", f"PASS ({NUM_CLICKS}x)"))
    summary.append(("URL redirected", f"PASS ({NUM_CLICKS}x)"))
    record_property("clicks_performed", str(NUM_CLICKS))

    # ── Steps 14-15: reload the campaign report, poll (bounded) until the
    #                 click count reflects all NUM_CLICKS clicks ──────────
    expected_click_count = initial_click_count + NUM_CLICKS
    deadline = time.time() + CLICK_COUNT_POLL_TIMEOUT_SECONDS
    final_click_count = initial_click_count
    while time.time() < deadline:
        report_page.page.reload()
        report_page.page.wait_for_timeout(1000)
        final_click_count = _read_click_count(report_page, summary, record_property, "Click event received")
        if final_click_count >= expected_click_count:
            break
        time.sleep(CLICK_COUNT_POLL_INTERVAL_SECONDS)

    record_property("final_click_count", str(final_click_count))
    if final_click_count <= initial_click_count:
        summary.append(("Click event received", "FAIL"))
        summary.append(("Final click count", str(final_click_count)))
        summary.append(("Final Result", "FAIL"))
        _print_summary(record_property, summary)
        pytest.fail(
            f"Click count did not increase within {CLICK_COUNT_POLL_TIMEOUT_SECONDS}s "
            f"for campaign '{name}': initial={initial_click_count}, "
            f"still={final_click_count} after {NUM_CLICKS} click(s)."
        )
    summary.append(("Click event received", "PASS"))
    summary.append(("Final click count", str(final_click_count)))
    assert final_click_count == expected_click_count, (
        f"Expected exactly {NUM_CLICKS} additional click(s) (initial="
        f"{initial_click_count}, expected={expected_click_count}), got "
        f"final={final_click_count} for campaign '{name}'."
    )

    # ── Step 16: DLR remains correctly received for the message after the
    #             URL click -- re-checked with the standard single-id poll,
    #             status/provider_status/status_code still NOT validated ──
    dlr_response, dlr_body, fields = poll_for_dlr(api_client, message_id)
    record_property("post_click_dlr_response", dlr_response.text if dlr_response is not None else "")
    if dlr_response is None or dlr_response.status_code != 200 or dlr_body is None:
        summary.append(("DLR after click", "FAIL"))
        summary.append(("Final Result", "FAIL"))
        _print_summary(record_property, summary)
        pytest.fail(
            f"DLR API could not be re-checked for message_id={message_id} after the "
            f"click within {DLR_POLL_TIMEOUT_SECONDS}s."
        )

    # Confirmed real behavior (project owner's own sample response body):
    # after a short URL is clicked, looking up this SAME message_id on
    # the DLR Receiver returns a "short_link" CLICK-EVENT body instead of
    # the plain DLR body -- it carries no top-level `received` field at
    # all, so the plain received=true check below only applies when the
    # body is still shaped like a plain DLR. Branch on the real shape
    # rather than assuming one or the other.
    if is_click_event_body(dlr_body):
        # ── Click Event Format/Schema Verification -- message_id/contact/
        #               short_url correlation is dynamic throughout,
        #               never hard-coded ───────────────────────────────────
        click_fields = extract_click_fields(dlr_body)
        expected_contact = short_url_label.split(" (page")[0]
        click_format_result = validate_click_format(click_fields)
        click_correlation_result = validate_click_correlation(
            click_fields,
            expected_message_id=message_id,
            expected_contact=expected_contact,
            expected_short_url=short_url,
        )
        click_report = build_click_validation_report(click_format_result, click_correlation_result)
        record_property("post_click_event_validation_report", click_report)
        print("\n" + click_report)
        if not click_format_result["passed"] or not click_correlation_result["passed"]:
            summary.append(("DLR after click", "FAIL"))
            summary.append(("Final Result", "FAIL"))
            _print_summary(record_property, summary)
            pytest.fail(
                f"Click-event format/correlation validation failed for "
                f"message_id={message_id} after the click.\n{click_report}\nBody: {dlr_body}"
            )
        summary.append(("DLR after click", "PASS"))
        summary.append(("Click Event Format Validation", "PASS"))
    else:
        if not fields["received"]:
            summary.append(("DLR after click", "FAIL"))
            summary.append(("Final Result", "FAIL"))
            _print_summary(record_property, summary)
            pytest.fail(
                f"DLR for message_id={message_id} is no longer received=true after "
                f"the URL click. Body: {dlr_body}"
            )
        summary.append(("DLR after click", "PASS"))

        # ── DLR Format/Schema Verification for the post-click DLR (generic
        #               check -- status/code only checked to EXIST) ──────
        dlr_fields_full = extract_full_dlr_fields(dlr_body)
        format_result = validate_dlr_format(dlr_fields_full)
        correlation_result = validate_dlr_correlation(dlr_fields_full, expected_message_id=message_id)
        report = build_dlr_validation_report(format_result, correlation_result)
        record_property("post_click_dlr_validation_report", report)
        print("\n" + report)
        if not format_result["passed"] or not correlation_result["passed"]:
            summary.append(("DLR Format Validation (after click)", "FAIL"))
            summary.append(("Final Result", "FAIL"))
            _print_summary(record_property, summary)
            pytest.fail(
                f"DLR format/correlation validation failed for message_id={message_id} "
                f"after the click.\n{report}\nBody: {dlr_body}"
            )
        summary.append(("DLR Format Validation (after click)", "PASS"))

    summary.append(("Final Result", "PASS"))
    _print_summary(record_property, summary)
