"""
utils/campaign_dlr.py

DLR verification for a launched SMS UI campaign, shared by every test that
launches one (see the `campaign_dlr` fixture in tests/sms/campaigns/conftest.py)
and by test_sms_campaign_otp_test_dlr.py.

Flow (per the "Verify DLR for SMS Campaign" test case):
  1. Campaigns list -> search the campaign -> open Reports of the newest row
     whose name matches exactly.
  2. Wait until the report lists the campaign's recipients (a just-launched
     campaign fills its report asynchronously).
  3. For every recipient row (all report pages): View -> read message_id from
     the message-details popup -> close.
  4. ONE bulk POST {dlr_base_url}/api/v1/dlr/verify with every message_id,
     polled until all are received or the timeout expires.
  5. Every message_id must have a correlated DLR (received=true); 0 missing.

DLR status / provider_status / status_code are deliberately NOT validated.

Env:
  SMS_CAMPAIGN_DLR_VERIFY          "false" disables the check for launch tests
  SMS_CAMPAIGN_DLR_TIMEOUT         seconds to wait for all DLRs (default 180)
  SMS_CAMPAIGN_REPORT_TIMEOUT      seconds to wait for the report rows (default 120)
"""

import os
import time
from dataclasses import dataclass, field

from pages.sms.sms_campaign_page import SMSCampaignPage
from pages.sms.sms_campaign_message_report_page import SmsCampaignMessageReportPage
from utils.dlr_format_validator import (
    aggregate_bulk_dlr_validation,
    build_bulk_dlr_validation_report,
)
from utils.dlr_helpers import DLR_POLL_INTERVAL_SECONDS, poll_bulk_dlr

DLR_VERIFY_ENABLED = os.getenv("SMS_CAMPAIGN_DLR_VERIFY", "true").strip().lower() not in ("0", "false", "no", "off")
DLR_TIMEOUT_SECONDS = int(os.getenv("SMS_CAMPAIGN_DLR_TIMEOUT", "180"))
REPORT_TIMEOUT_SECONDS = int(os.getenv("SMS_CAMPAIGN_REPORT_TIMEOUT", "120"))
MAX_REPORT_PAGES = 50


class CampaignDlrError(AssertionError):
    """Raised with the failing step; `summary` holds the Expected Result table so far."""

    def __init__(self, message, summary):
        super().__init__(message)
        self.summary = summary


@dataclass
class CampaignDlrResult:
    campaign_name: str
    recipients: list = field(default_factory=list)
    message_ids: dict = field(default_factory=dict)   # recipient label -> message_id
    message_contents: dict = field(default_factory=dict)  # recipient label -> popup text (message body, for short-URL extraction)
    missing: list = field(default_factory=list)
    summary: list = field(default_factory=list)       # [(label, value)]
    verify_response_text: str = ""

    def summary_text(self):
        width = max(len(k) for k, _ in self.summary) if self.summary else 0
        return "\n".join(f"{k.ljust(width)}   {v}" for k, v in self.summary)


def _record(record_property, key, value):
    if record_property is not None:
        record_property(key, value)


def _open_campaign_report(page, campaign_name, timeout_s):
    """Campaigns list -> search -> Reports of the exact-name row. Retries until
    timeout, because a just-launched campaign may take a moment to be listed."""
    campaign_page = SMSCampaignPage(page)
    deadline = time.time() + timeout_s
    found = False
    while True:
        campaign_page.open_campaign_list()
        campaign_page.search(campaign_name)
        found = campaign_page.is_campaign_name_in_list(campaign_name, timeout=10000)
        if found and campaign_page.click_reports_link_for_exact_name(campaign_name):
            return "opened"
        if time.time() >= deadline:
            return "report" if found else "not_found"
        time.sleep(5)


def _wait_for_report_rows(report_page, timeout_s, expected_recipients):
    """Reload the report until it has rows and the count is stable (and, if
    known, at least `expected_recipients`). Returns the final row count."""
    deadline = time.time() + timeout_s
    previous = -1
    while True:
        try:
            report_page.wait_for_table_load()
            rows = report_page.get_row_count()
        except Exception:
            rows = 0
        enough = expected_recipients is None or rows >= expected_recipients or report_page.has_next_page()
        if rows > 0 and rows == previous and enough:
            return rows
        if time.time() >= deadline:
            return rows
        previous = rows
        time.sleep(5)
        report_page.page.reload()


def _collect_message_ids(report_page):
    """Walks every report page; returns (recipients, message_ids, message_contents, problems).

    message_contents captures each row's popup text (get_popup_content(),
    falling back to get_popup_all_text() if the "Message"/"Content"/"Body"
    label isn't matched) at the SAME time the popup is already open for
    message_id -- no extra navigation/View click needed. Used by callers
    that need to find something inside the message body (e.g. a short URL)
    without re-walking the report a second time. Best-effort: an empty
    string is stored (never fabricated) if neither read returns anything."""
    contact_col = report_page.get_column_index("Contact")
    if contact_col is None:
        # Real-run fix (2026-10-10): a real run showed this missing
        # exactly CONTACT and SMS UNITS -- both confirmed-present
        # defaults for every clickable card on this page -- with every
        # other column present and in order. This report page renders
        # the SAME underlying Livewire table ("sms_messages") as the
        # standalone SMS Messages page
        # (pages/sms/messaging/sms_message_page.py), and column
        # visibility is that table's own persisted state, not scoped to
        # one page's URL -- so a column a Messages-page test left hidden
        # (an interrupted toggle-and-restore) leaks into this completely
        # different report page too. Attempt one self-heal: restore
        # defaults via SMSMessagePage.restore_default_columns() (adds
        # the missing method this report page never had of its own),
        # then reload THIS report page and retry the lookup once before
        # giving up.
        try:
            from pages.sms.sms_message_page import SMSMessagePage
            SMSMessagePage(report_page.page).restore_default_columns()
            report_page.page.reload()
            report_page.wait_for_table_load()
            contact_col = report_page.get_column_index("Contact")
        except Exception:
            pass
    if contact_col is None:
        return None, None, None, {"no_contact_column": report_page.get_visible_column_headers()}
    popup = report_page.message_details_popup()
    recipients, message_ids, message_contents = [], {}, {}
    problems = {"no_view": [], "no_popup": [], "no_message_id": []}

    for page_no in range(1, MAX_REPORT_PAGES + 1):
        for i in range(report_page.get_row_count()):
            recipient = report_page.get_cell_text(i, contact_col)
            if not recipient:
                continue
            label = f"{recipient} (page {page_no}, row {i + 1})"
            recipients.append(label)
            if not report_page.click_view_in_row(i):
                problems["no_view"].append(label)
                continue
            if not popup.is_popup_open():
                problems["no_popup"].append(label)
                continue
            message_id = (popup.get_popup_message_id() or "").strip()
            content = (popup.get_popup_content() or "").strip()
            if not content:
                content = (popup.get_popup_all_text() or "").strip()
            popup.close_popup()
            if not message_id:
                problems["no_message_id"].append(label)
                continue
            message_ids[label] = message_id
            message_contents[label] = content
        if not report_page.has_next_page():
            break
        report_page.go_to_next_page()
    return recipients, message_ids, message_contents, problems


def verify_campaign_dlrs(page, api_client, campaign_name, record_property=None,
                         expected_recipients=None, dlr_timeout=None, report_timeout=None,
                         summary_prefix=None):
    """Runs the full campaign DLR check on Playwright `page`.

    Returns CampaignDlrResult on success; raises CampaignDlrError (an
    AssertionError, so the calling test FAILS) naming the failing step.
    """
    dlr_timeout = DLR_TIMEOUT_SECONDS if dlr_timeout is None else dlr_timeout
    report_timeout = REPORT_TIMEOUT_SECONDS if report_timeout is None else report_timeout
    result = CampaignDlrResult(campaign_name)
    # summary_prefix: extra leading rows of the Expected Result table
    # (e.g. template name/type, "Campaign Created").
    result.summary.extend(summary_prefix or [])
    result.summary.append(("Campaign", campaign_name))

    def fail(step, message):
        result.summary.append((step, "FAIL"))
        result.summary.append(("Final Result", "FAIL"))
        for k, v in result.summary:
            _record(record_property, f"DLR {k}", v)
        print("\n" + result.summary_text())
        raise CampaignDlrError(f"[{campaign_name}] {step}: {message}", result.summary)

    # Campaign found / Report opened
    state = _open_campaign_report(page, campaign_name, report_timeout)
    if state == "not_found":
        fail("Campaign Found", f"campaign '{campaign_name}' could not be found in the Campaigns list")
    result.summary.append(("Campaign Found", "PASS"))
    report_page = SmsCampaignMessageReportPage(page)
    if state != "opened" or not report_page.is_report_page():
        fail("Report Opened", f"Reports could not be opened (URL: {report_page.get_current_url()})")
    result.summary.append(("Report Opened", "PASS"))
    _record(record_property, "DLR campaign_report_url", report_page.get_current_url())

    # Recipients + message ids (retry while the report is still filling in)
    deadline = time.time() + report_timeout
    while True:
        rows = _wait_for_report_rows(report_page, max(5, deadline - time.time()), expected_recipients)
        recipients, message_ids, message_contents, problems = _collect_message_ids(report_page)
        if recipients is None:
            fail("Recipients Collected", f"no 'Contact' column on the report; headers={problems['no_contact_column']!r}")
        incomplete = any(problems.values()) or not recipients or (
            expected_recipients is not None and len(recipients) < expected_recipients)
        if not incomplete or time.time() >= deadline:
            break
        time.sleep(5)
        report_page.page.reload()

    if not recipients:
        fail("Recipients Collected", "the campaign report lists no recipients")
    if expected_recipients is not None and len(recipients) < expected_recipients:
        fail("Recipients Collected",
             f"report lists {len(recipients)} recipient(s), expected at least {expected_recipients}")
    result.recipients = recipients
    result.summary.append(("Recipients Collected", f"PASS ({len(recipients)})"))

    if problems["no_view"]:
        fail("Message IDs Collected", f"View button is unavailable for: {problems['no_view']}")
    if problems["no_popup"]:
        fail("Message IDs Collected", f"message details did not open for: {problems['no_popup']}")
    if problems["no_message_id"]:
        fail("Message IDs Collected", f"message_id could not be extracted for: {problems['no_message_id']}")
    result.message_ids = message_ids
    result.message_contents = message_contents
    result.summary.append(("Message IDs Collected", f"PASS ({len(message_ids)})"))
    for label, mid in message_ids.items():
        _record(record_property, f"message_id[{label}]", mid)

    # One bulk verify request (polled) with every collected id
    ids = list(dict.fromkeys(message_ids.values()))
    response, body, results = poll_bulk_dlr(
        api_client, ids, expected_status=None, require_billing=None,
        timeout_seconds=dlr_timeout, interval_seconds=DLR_POLL_INTERVAL_SECONDS,
    )
    result.verify_response_text = response.text if response is not None else ""
    _record(record_property, "DLR verify response", result.verify_response_text)
    if response is None or response.status_code != 200 or body is None or results is None:
        fail("DLR Verification", f"status={getattr(response, 'status_code', None)} body={result.verify_response_text}")
    result.summary.append(("DLR Verification", "PASS"))

    by_id = {mid: label for label, mid in message_ids.items()}
    not_correlated = [mid for mid in ids if mid not in results]
    not_received = [mid for mid in ids if mid in results and not results[mid].get("received")]
    result.missing = not_correlated + not_received
    if not_correlated:
        result.summary.append(("Missing DLRs", str(len(result.missing))))
        fail("All DLRs Received", f"DLR could not be correlated for {[(m, by_id.get(m)) for m in not_correlated]}")
    if not_received:
        result.summary.append(("Missing DLRs", str(len(result.missing))))
        fail("All DLRs Received",
             f"no DLR within {dlr_timeout}s for {len(not_received)} of {len(ids)}: "
             f"{[(m, by_id.get(m)) for m in not_received]}")

    result.summary += [("All DLRs Received", "PASS"), ("Missing DLRs", "0")]

    # ── DLR Format/Schema Verification for every received DLR (generic
    #               check -- status/code are only checked to EXIST, never
    #               compared to a specific value, per the "Important
    #               Existing DLR Rule"). This single injection point
    #               covers every test that calls verify_campaign_dlrs()
    #               directly or via the `campaign_dlr` fixture ──────────
    expected_mobiles = {mid: label.split(" (page")[0] for label, mid in message_ids.items()}
    format_counts, format_failures = aggregate_bulk_dlr_validation(
        ids, results, expected_mobiles=expected_mobiles
    )
    bulk_report = build_bulk_dlr_validation_report(format_counts)
    _record(record_property, "DLR Format Validation Report", bulk_report)
    print("\n" + bulk_report)
    if format_counts["invalid_format"] or format_counts["message_id_mismatches"] or format_counts["mobile_mismatches"] or format_counts["duplicate_dlrs"]:
        result.summary.append(("DLR Format Validation", "FAIL"))
        result.summary.append(("Final Result", "FAIL"))
        for k, v in result.summary:
            _record(record_property, f"DLR {k}", v)
        print("\n" + result.summary_text())
        # Diagnostic: the raw bulk-verify record for the FIRST id,
        # included directly in the failure message (not just recorded as
        # a property, which doesn't survive into the HTML report/pasted
        # traceback) -- this is what confirms the real response shape
        # when the assumed schema doesn't match, without needing a
        # separate repro step.
        sample_id = ids[0] if ids else None
        sample_entry = results.get(sample_id) if sample_id is not None else None
        raise CampaignDlrError(
            f"[{campaign_name}] DLR Format Validation: {format_counts} -- {format_failures}\n"
            f"Raw bulk-verify entry for message_id={sample_id!r}: {sample_entry!r}\n"
            f"Full raw bulk-verify response body: {body!r}",
            result.summary,
        )
    result.summary.append(("DLR Format Validation", "PASS"))

    result.summary.append(("Final Result", "PASS"))
    for k, v in result.summary:
        _record(record_property, f"DLR {k}", v)
    print("\n" + result.summary_text())
    return result
