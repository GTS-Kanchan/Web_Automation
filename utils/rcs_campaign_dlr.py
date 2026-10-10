"""
utils/rcs_campaign_dlr.py

DLR (delivery-receipt / webhook event) verification for a launched RCS UI
campaign, used by tests/rcs/campaigns/test_rcs_campaign_create_flow.py::
test_e2ecopypastenumber_send_now (wired in directly after that test's
existing campaign-launch + list-persistence assertions -- see that test's
body; this module adds NO new test case and does NOT re-launch/re-submit
the campaign).

Flow (per the project owner's spec, 2026-10-10):
  1. Campaign list -> search the campaign -> open its Reports page
     (RCSCampaignPage.search_campaign() + click_reports_icon_on_row()).
  2. Wait until the report lists the campaign's recipients (a
     just-launched campaign fills its report asynchronously).
  3. Collect every row's internal message id DIRECTLY from the table's
     `rowpk` attribute (RCSCampaignReportPage.get_row_pks() -- CONFIRMED
     present on each <tr>) and recipient number (Contact column) -- no
     popup-walking needed, unlike the SMS reference pattern
     (utils/campaign_dlr.py's _collect_message_ids()), because this
     table already exposes the message id structurally.
  4. For EACH collected message id, poll
     GET {dlr_base_url}/api/v1/dlr/{message_id} (via
     utils.rcs_dlr_helpers.poll_for_rcs_delivery(), reusing
     utils.sms_api_client.SmsApiClient.get_dlr() -- same endpoint/client
     SMS DLR tests already use) until a message_delivery/delivered event
     is observed or the timeout elapses. The response is a SINGLE object
     reflecting the message's current/latest state (not a list).
  5. Validate the final event's schema (utils.rcs_dlr_helpers.
     validate_event_schema()), correlate it against the message id/
     recipient/campaign id captured from the UI (correlate_event()), and
     validate its delivery_info block (validate_delivery_info()).
  6. Every recipient must have a delivered DLR; any failure raises
     RcsCampaignDlrError (an AssertionError) carrying the exact
     section-8 failure-report format for that message, so the calling
     test FAILS with a precise, non-generic reason.

Deliberately NOT done, per the project owner's explicit spec:
  - No DLR is ever generated/forced -- only observed via polling.
  - A successful campaign submission is never treated as DLR received.
  - rcs_message_id and delivery_info.read_at are never required to be
    populated (confirmed null in every real sample).
  - external_message_id is required to be PRESENT (schema check) but is
    only cross-validated against an earlier-captured value when the
    caller actually has one -- this module's single-poll design has no
    separate "dispatch-only" capture to compare against, so that cross-
    check is a no-op here (see correlate_event()'s own docstring: "only
    when the caller already captured one from an earlier dispatch
    event").

Env (mirrors utils/campaign_dlr.py's SMS_CAMPAIGN_* naming):
  RCS_CAMPAIGN_DLR_VERIFY     "false" disables the check entirely (default: enabled)
  RCS_CAMPAIGN_DLR_TIMEOUT    seconds to wait for EACH message's delivered DLR (default 120)
  RCS_CAMPAIGN_REPORT_TIMEOUT seconds to wait for the report rows to appear/stabilize (default 120)
  RCS_DLR_POLL_INTERVAL_SECONDS  poll interval for each GET (see utils/rcs_dlr_helpers.py; default 5)
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Optional

from pages.rcs.campaigns.rcs_campaign_page import RCSCampaignPage
from pages.rcs.campaigns.rcs_campaign_report_page import RCSCampaignReportPage
from utils.rcs_dlr_helpers import (
    EVENT_TYPE_DELIVERY,
    STATUS_DELIVERED,
    RCS_DLR_POLL_INTERVAL_SECONDS,
    build_failure_report,
    correlate_event,
    poll_for_rcs_delivery,
    validate_delivery_info,
    validate_event_schema,
)

DLR_VERIFY_ENABLED = os.getenv("RCS_CAMPAIGN_DLR_VERIFY", "true").strip().lower() not in ("0", "false", "no", "off")
DLR_TIMEOUT_SECONDS = int(os.getenv("RCS_CAMPAIGN_DLR_TIMEOUT", "120"))
REPORT_TIMEOUT_SECONDS = int(os.getenv("RCS_CAMPAIGN_REPORT_TIMEOUT", "120"))
MAX_REPORT_PAGES = 50


class RcsCampaignDlrError(AssertionError):
    """Raised with the section-8 failure-report text as the message, and
    the same text again on `.failure_report` for a caller that wants it
    without re-parsing the exception message."""

    def __init__(self, message, failure_report=None):
        super().__init__(message)
        self.failure_report = failure_report or message


@dataclass
class RcsCampaignDlrResult:
    campaign_name: str
    campaign_id: Optional[str] = None
    recipients: list = field(default_factory=list)          # [(recipient, internal_message_id), ...]
    delivered: dict = field(default_factory=dict)            # internal_message_id -> last event body
    events_seen: dict = field(default_factory=dict)          # placeholder
    summary: list = field(default_factory=list)

    def summary_text(self):
        width = max(len(k) for k, _ in self.summary) if self.summary else 0
        return "\n".join(f"{k.ljust(width)}   {v}" for k, v in self.summary)


def _record(record_property, key, value):
    if record_property is not None:
        record_property(key, value)


def _open_campaign_report(page, campaign_name, timeout_s):
    """Campaigns list -> search -> Reports of the (first/only) matching
    row. Retries until timeout, because a just-launched campaign may take
    a moment to be listed -- same rationale as the SMS reference
    (utils/campaign_dlr.py::_open_campaign_report())."""
    campaign_page = RCSCampaignPage(page)
    deadline = time.time() + timeout_s
    found = False
    while True:
        campaign_page.load_campaign_list()
        campaign_page.search_campaign(campaign_name)
        found = campaign_page.is_campaign_name_in_list(campaign_name, timeout=10000)
        if found and campaign_page.click_reports_icon_on_row(0):
            return "opened"
        if time.time() >= deadline:
            return "report" if found else "not_found"
        time.sleep(5)


def _wait_for_report_rows(report_page, timeout_s, expected_recipients):
    """Reload the report until it has rows and the count is stable (and,
    if known, at least `expected_recipients`). Returns the final row
    count."""
    deadline = time.time() + timeout_s
    previous = -1
    while True:
        try:
            report_page.wait_for_table_load()
            rows = report_page.get_row_count()
        except Exception:
            rows = 0
        enough = expected_recipients is None or rows >= expected_recipients
        if rows > 0 and rows == previous and enough:
            return rows
        if time.time() >= deadline:
            return rows
        previous = rows
        time.sleep(5)
        report_page.page.reload()


def _collect_recipients_and_message_ids(report_page):
    """Reads every visible row's Contact cell + `rowpk` (internal message
    id) directly off the table -- no View-popup walking needed (see
    module docstring point 3). Returns (recipients, problems) where
    `recipients` is a de-duplicated (by message id) list of
    (recipient, message_id) tuples, in row order, and `problems` names
    any structural issue ((missing Contact column, a row with no rowpk)."""
    contact_col = report_page.get_column_index("Contact")
    if contact_col is None:
        return None, {"no_contact_column": report_page.get_visible_column_headers()}

    row_count = report_page.get_row_count()
    pks = report_page.get_row_pks()
    problems = {"no_rowpk": []}
    recipients = []
    seen_ids = set()
    for i in range(row_count):
        recipient = report_page.get_cell_text(i, contact_col)
        message_id = pks[i] if i < len(pks) else None
        if not message_id:
            problems["no_rowpk"].append(recipient or f"<row {i}>")
            continue
        if message_id in seen_ids:
            continue
        seen_ids.add(message_id)
        recipients.append((recipient, message_id))
    return recipients, problems


def verify_rcs_campaign_dlrs(page, api_client, campaign_name, record_property=None,
                              expected_recipients=None, report_timeout=None,
                              dlr_timeout=None, dlr_interval=None):
    """Runs the full RCS campaign DLR check on Playwright `page`, for a
    campaign that has ALREADY been created and launched (Send Now) by the
    caller -- this function never submits/launches anything itself.

    Returns RcsCampaignDlrResult on success; raises RcsCampaignDlrError
    (an AssertionError, so the calling test FAILS) carrying the exact
    section-8 failure-report format for the first message that didn't
    pass.
    """
    report_timeout = REPORT_TIMEOUT_SECONDS if report_timeout is None else report_timeout
    dlr_timeout = DLR_TIMEOUT_SECONDS if dlr_timeout is None else dlr_timeout
    dlr_interval = RCS_DLR_POLL_INTERVAL_SECONDS if dlr_interval is None else dlr_interval

    result = RcsCampaignDlrResult(campaign_name)
    result.summary.append(("Campaign", campaign_name))

    def fail_generic(step, message):
        result.summary.append((step, "FAIL"))
        result.summary.append(("Final Result", "FAIL"))
        for k, v in result.summary:
            _record(record_property, f"RCS DLR {k}", v)
        print("\n" + result.summary_text())
        raise RcsCampaignDlrError(f"[{campaign_name}] {step}: {message}")

    # Campaign found / Report opened
    state = _open_campaign_report(page, campaign_name, report_timeout)
    if state == "not_found":
        fail_generic("Campaign Found", f"campaign '{campaign_name}' could not be found in the Campaigns list")
    result.summary.append(("Campaign Found", "PASS"))

    report_page = RCSCampaignReportPage(page)
    if state != "opened" or not report_page.is_report_page():
        fail_generic("Report Opened", f"Reports could not be opened (URL: {report_page.get_current_url()})")
    result.summary.append(("Report Opened", "PASS"))
    _record(record_property, "RCS DLR campaign_report_url", report_page.get_current_url())

    campaign_id = report_page.get_campaign_id_from_url()
    result.campaign_id = campaign_id
    _record(record_property, "RCS DLR campaign_id", campaign_id)

    # Recipients + message ids (retry while the report is still filling in)
    deadline = time.time() + report_timeout
    while True:
        _wait_for_report_rows(report_page, max(5, deadline - time.time()), expected_recipients)
        recipients, problems = _collect_recipients_and_message_ids(report_page)
        if recipients is None:
            fail_generic("Recipients Collected", f"no 'Contact' column on the report; headers={problems['no_contact_column']!r}")
        incomplete = bool(problems["no_rowpk"]) or not recipients or (
            expected_recipients is not None and len(recipients) < expected_recipients)
        if not incomplete or time.time() >= deadline:
            break
        time.sleep(5)
        report_page.page.reload()

    if not recipients:
        fail_generic("Recipients Collected", "the campaign report lists no recipients")
    if problems["no_rowpk"]:
        fail_generic("Recipients Collected", f"no 'rowpk' (internal message id) for row(s): {problems['no_rowpk']}")
    result.recipients = recipients
    result.summary.append(("Recipients Collected", f"PASS ({len(recipients)})"))
    for recipient, message_id in recipients:
        _record(record_property, f"RCS DLR message_id[{recipient}]", message_id)

    # Per-message DLR polling + schema/correlation/delivery-info verification
    for recipient, message_id in recipients:
        last_response, last_body, events_seen = poll_for_rcs_delivery(
            api_client, message_id, timeout_seconds=dlr_timeout, interval_seconds=dlr_interval,
        )
        result.events_seen[message_id] = events_seen
        _record(record_property, f"RCS DLR events_seen[{message_id}]", events_seen)

        actual_event = last_body.get("event_type") if isinstance(last_body, dict) else None
        actual_status = last_body.get("status") if isinstance(last_body, dict) else None
        dlr_received = actual_event == EVENT_TYPE_DELIVERY and actual_status == STATUS_DELIVERED

        if not dlr_received:
            report_text = build_failure_report(
                campaign_id=campaign_id,
                internal_message_id=message_id,
                external_message_id=(last_body or {}).get("external_message_id") if isinstance(last_body, dict) else None,
                recipient=recipient,
                actual_event=actual_event,
                actual_status=actual_status,
                dlr_received=False,
                schema_validation=None,
                correlation_validation=None,
                failure_reason=(
                    f"DLR not received before timeout ({dlr_timeout}s): last observed "
                    f"event_type={actual_event!r} status={actual_status!r}; "
                    f"HTTP status={getattr(last_response, 'status_code', None)}"
                ),
            )
            result.summary.append(("All DLRs Received", "FAIL"))
            result.summary.append(("Final Result", "FAIL"))
            for k, v in result.summary:
                _record(record_property, f"RCS DLR {k}", v)
            print("\n" + report_text)
            raise RcsCampaignDlrError(report_text, failure_report=report_text)

        # Schema validation (dispatch vs delivery fields checked SEPARATELY,
        # see utils/rcs_dlr_helpers.validate_event_schema()'s own docstring)
        schema_ok, missing_fields, invalid_timestamps = validate_event_schema(last_body)

        # Correlation (internal id / recipient / campaign id; external id
        # is a no-op here -- see module docstring)
        correlation = correlate_event(
            last_body, expected_message_id=message_id,
            expected_number=recipient, expected_campaign_id=campaign_id,
        )
        correlation_ok = (
            correlation.get("internal_message_id_match") is True
            and correlation.get("recipient_match") in (True, None)
            and correlation.get("campaign_id_match") in (True, None)
        )

        # Delivery-info block (delivery_info.delivered_at populated,
        # delivery_status.status == "delivered", read_at never required)
        delivery_info_ok, delivery_info_problems = validate_delivery_info(last_body)

        external_message_id = last_body.get("external_message_id")

        if schema_ok and correlation_ok and delivery_info_ok:
            result.delivered[message_id] = last_body
            continue

        failure_reasons = []
        if not schema_ok:
            failure_reasons.append(
                f"invalid event structure -- missing fields: {missing_fields}; "
                f"invalid timestamps: {invalid_timestamps}"
            )
        if correlation.get("internal_message_id_match") is False:
            failure_reasons.append("internal message ID mismatch")
        if correlation.get("recipient_match") is False:
            failure_reasons.append("recipient mismatch")
        if correlation.get("campaign_id_match") is False:
            failure_reasons.append("campaign ID mismatch")
        if not delivery_info_ok:
            failure_reasons.append(
                "delivery status not equal to delivered / delivery_info invalid: "
                + "; ".join(delivery_info_problems)
            )

        report_text = build_failure_report(
            campaign_id=campaign_id,
            internal_message_id=message_id,
            external_message_id=external_message_id,
            recipient=recipient,
            actual_event=actual_event,
            actual_status=actual_status,
            dlr_received=True,
            schema_validation=schema_ok,
            correlation_validation=correlation_ok,
            failure_reason="; ".join(failure_reasons) or "unknown validation failure",
        )
        result.summary.append(("All DLRs Received", "FAIL"))
        result.summary.append(("Final Result", "FAIL"))
        for k, v in result.summary:
            _record(record_property, f"RCS DLR {k}", v)
        print("\n" + report_text)
        raise RcsCampaignDlrError(report_text, failure_report=report_text)

    result.summary.append(("All DLRs Received", "PASS"))
    result.summary.append(("Final Result", "PASS"))
    for k, v in result.summary:
        _record(record_property, f"RCS DLR {k}", v)
    print("\n" + result.summary_text())
    return result
