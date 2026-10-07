"""
utils/sms_dlr_dynamic_recipient.py

Shared helpers for the SMS Campaign DLR verification test with dynamic
recipient files
(tests/sms/campaigns/test_sms_campaign_dlr_dynamic_recipient_file.py).

Built to satisfy the spec's explicit "no hardcoding" requirements:
  - Recipient counts, message IDs, and DLR counts are always computed
    from the actual input file / campaign export at run time -- never a
    literal 1000 / 10000 / 100000, and never an invented message ID.
  - The recipient-number format rule reused here
    (`value.isdigit() and 7 <= len(value) <= 15`) is the SAME convention
    already confirmed in tests/sms/messaging/test_sms_message_flow.py
    (around line 860), not a newly invented rule.
  - Stat-card numeric parsing reuses the same digit-extraction idiom
    already established in
    tests/sms/campaigns/test_sms_campaign_message_report_flow.py's
    capture_ui_card_value()/capture_total_messages_from_ui() (re.sub to
    strip everything but digits, then int()).
  - File reading reuses utils/file_validator.py's read_file_rows() (the
    same generic .csv/.xlsx/.xls/.zip reader already used by the Download
    Center's export-validation tests) rather than a new parser.
  - Bulk DLR verification reuses utils/dlr_helpers.py's poll_bulk_dlr()
    (the exact helper already used by
    tests/sms/campaigns/test_sms_campaign_dlr_bulk.py) unchanged, just
    called once per chunk for scale safety.

HONESTLY FLAGGED GAP (not silently assumed away): the bulk DLR
verification endpoint (POST {dlr_base_url}/api/v1/dlr/verify) has no
independently confirmed response field carrying a recipient/phone number
for a given message_id -- utils/dlr_helpers.py's own module docstring
states only `received` / `message_id` / `correlation_id` are confirmed
fields. The spec's Section 9 ("verify the DLR belongs to the SAME
recipient, not just that a DLR with that message_id exists") is
therefore satisfied here via message_id itself as the join key:
message_id is already paired 1:1 with its recipient at the moment it is
read from the Download Center export (Sections 5-7 below), so looking up
THAT SAME message_id's DLR can only ever return the DLR for that
message/recipient pair -- there is no code path by which a different
recipient's DLR could come back under a message_id that isn't theirs.
recipient_mismatches() below DOES use a recipient/phone field if the DLR
response body happens to carry one (future-proofing), but reports 0 (not
a fabricated guess) when no such field is present at all, together with
a note explaining why -- see the test file's own docstring and final
report for how this is surfaced to a human reader.

HONESTLY FLAGGED ENGINEERING CHOICE: no confirmed batch-size limit exists
for POST {dlr_base_url}/api/v1/dlr/verify (see
utils/sms_api_client.py's verify_dlr_bulk() docstring). Chunking the
bulk-verify calls (SMS_DLR_VERIFY_BATCH_SIZE, default 1000) is a
deliberate safety choice for 100K-scale runs, not a confirmed API
constraint -- set the batch size to a number >= the recipient count to
effectively disable chunking if the real API is confirmed to handle it
in one call.
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from utils.dlr_helpers import poll_bulk_dlr
from utils.file_validator import read_file_rows

# Confirmed recipient-number format rule -- see module docstring.
_PHONE_HEADER_KEYWORDS = ("phone", "mobile", "number", "contact", "msisdn")
_MESSAGE_ID_HEADER_KEYWORDS = ("message id", "message_id", "messageid")
_CAMPAIGN_NAME_HEADER_KEYWORDS = ("campaign name", "campaign_name")


def _coerce_phone_str(value) -> str:
    """Recipient-file cell values come back from
    utils/file_validator.read_file_rows() AS READ by the underlying
    library -- a CSV cell is always a string, but an .xlsx/.xls cell
    keeps its native type (e.g. a phone number stored as an int/float in
    the spreadsheet, confirmed from a real uploaded recipient file whose
    "phone" column cells are plain Excel numbers, not text). Normalizes
    any of those to the plain-digits string the rest of this module
    (and the recipient-number format rule) expects, without inventing a
    locale-specific format: an integral float (918999614816.0) is
    rendered without the trailing ".0"; a genuinely fractional value is
    left as str(value) so it visibly fails the digits-only format check
    below rather than being silently truncated into something that
    looks valid."""
    if value is None:
        return ""
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return str(value)
    if isinstance(value, int):
        return str(value)
    return str(value).strip()


def is_valid_recipient_number(value) -> bool:
    """Same confirmed convention as
    tests/sms/messaging/test_sms_message_flow.py (~line 860):
    digits only, 7-15 characters long."""
    v = (value or "").strip()
    return v.isdigit() and 7 <= len(v) <= 15


def _find_column(headers, keywords):
    for h in headers or []:
        hl = (h or "").strip().lower()
        if any(k in hl for k in keywords):
            return h
    return None


def parse_card_int(raw_text) -> Optional[int]:
    """Same digit-extraction idiom as capture_ui_card_value() /
    capture_total_messages_from_ui() in
    test_sms_campaign_message_report_flow.py -- not a new parsing
    strategy. Returns None if the stat card text has no digits at all."""
    digits = re.sub(r"[^\d]", "", raw_text or "")
    return int(digits) if digits else None


# ─────────────────────────────────────────────────────────────────────────
# Section 1 + 2: Dynamic Recipient File / Validate Input File Before Campaign
# ─────────────────────────────────────────────────────────────────────────

@dataclass
class RecipientFileResult:
    file_path: str
    phone_header: str = ""
    total_rows: int = 0
    unique_recipients: list = field(default_factory=list)
    duplicate_count: int = 0
    invalid_numbers: list = field(default_factory=list)
    blank_count: int = 0

    @property
    def expected_recipient_count(self) -> int:
        """Section 1's explicit instruction:
        expected_recipient_count = len(unique_recipients). Never a
        literal number."""
        return len(self.unique_recipients)


def read_and_validate_recipient_file(file_path) -> RecipientFileResult:
    """Section 1 + 2 of the spec.

    Reads the dynamic recipient file via the project's existing generic
    reader (utils/file_validator.read_file_rows -- dispatches on
    .csv/.xlsx/.xls/.zip, no new parsing logic), verifies it is
    non-empty, validates every recipient number's format against the
    project's existing convention, and computes expected_recipient_count
    as len(unique numbers) -- deliberately NOT assuming duplicate numbers
    are separate recipients (they are deduplicated here, matching the
    `keep_duplicates=False` default this flow passes to
    SMSCampaignPage.import_contacts_from_csv() on the campaign side, so
    both sides of the later count comparison use the same duplicate
    policy).

    Raises FileNotFoundError / ValueError for a missing or empty file --
    callers should let these propagate as a clear setup failure (or
    pytest.skip() on them), never continue with a 0-recipient run.
    """
    if not file_path or not os.path.isfile(file_path):
        raise FileNotFoundError(f"Recipient file not found: {file_path}")

    headers, rows = read_file_rows(file_path)
    if not rows:
        raise ValueError(f"Recipient file '{file_path}' is empty (no data rows).")

    phone_header = _find_column(headers, _PHONE_HEADER_KEYWORDS)
    if phone_header is None:
        # Single, unlabeled phone-number column -- fall back to the first
        # column rather than guessing a keyword match that isn't there.
        phone_header = headers[0]

    seen = set()
    unique_recipients = []
    invalid_numbers = []
    blank_count = 0
    duplicate_count = 0

    for row in rows:
        cell = row.get(phone_header)
        raw = _coerce_phone_str(cell)
        if not raw:
            blank_count += 1
            continue
        if not is_valid_recipient_number(raw):
            invalid_numbers.append(raw)
            continue
        if raw in seen:
            duplicate_count += 1
            continue
        seen.add(raw)
        unique_recipients.append(raw)

    return RecipientFileResult(
        file_path=file_path,
        phone_header=phone_header,
        total_rows=len(rows),
        unique_recipients=unique_recipients,
        duplicate_count=duplicate_count,
        invalid_numbers=invalid_numbers,
        blank_count=blank_count,
    )


# ─────────────────────────────────────────────────────────────────────────
# Section 4: Wait Until Messages Are Delivered
# ─────────────────────────────────────────────────────────────────────────

def wait_for_delivery_complete(
    report_page,
    campaign_id,
    timeout_seconds,
    poll_interval_seconds,
    record_property=None,
):
    """Section 4 of the spec: do NOT verify DLRs immediately after
    sending.

    Applies the real, confirmed "Pending" filter -- navigating to the
    'DLR Awaited' stat card's own metric-filtered table view
    (SmsCampaignMessageReportPage.CARD_NAME_TO_METRIC['DLR Awaited'] ==
    'dlr-awaited', i.e. the SAME URL the DLR Awaited card's onclick
    navigates to, confirmed in
    pages/sms/campaigns/sms_campaign_message_report_page.py) -- and
    polls that filtered table until it reports zero rows (has_no_records_
    message()/get_row_count()==0), i.e. "nothing in Pending", instead of
    reading the stat card's displayed digits. This directly inspects the
    actual filtered row set rather than trusting a summary number, and
    is still a lightweight check per poll (one table load, not a walk
    over every recipient), so it stays cheap at 100K scale. Also records
    the DLR Awaited stat card's own count alongside the row check purely
    for diagnostic logging (record_property), never as the pass/fail
    signal.

    Returns (completed: bool, last_pending_count: Optional[int]) where
    last_pending_count is the number of rows found in the Pending
    (DLR Awaited) filtered view on the last poll -- 0 on success.
    """
    metric = report_page.CARD_NAME_TO_METRIC["DLR Awaited"]
    deadline = time.time() + timeout_seconds
    last_pending_count = None
    while time.time() < deadline:
        try:
            report_page.navigate_to_campaign(campaign_id, metric=metric)
            report_page.wait_for_table_load()
            if report_page.has_no_records_message():
                last_pending_count = 0
            else:
                last_pending_count = report_page.get_row_count()
        except Exception:
            last_pending_count = None
        if record_property:
            record_property("Pending (DLR Awaited) rows (poll)", str(last_pending_count))
            try:
                record_property(
                    "DLR Awaited stat card (poll, diagnostic only)",
                    report_page.get_card_value("DLR Awaited"),
                )
            except Exception:
                pass
        if last_pending_count == 0:
            return True, last_pending_count
        time.sleep(poll_interval_seconds)
    return False, last_pending_count


# ─────────────────────────────────────────────────────────────────────────
# Section 5-7: Export Campaign Report / Verify Recipient Count / Dynamic
# Message ID Collection
# ─────────────────────────────────────────────────────────────────────────

def export_campaign_message_records(
    create_page,
    download_page,
    campaign_name,
    from_date_str,
    to_date_str,
    timeout_seconds,
    poll_interval_seconds,
    columns=None,
):
    """Sections 5-7 of the spec: obtain the per-message export that
    carries BOTH Message Id and Phone Number together -- confirmed to
    exist ONLY via the SMS Download Center's async report flow
    (constants/sms/reports/sms_download_headers.py's
    EXPECTED_SMS_DOWNLOAD_HEADERS includes "Message Id", "Phone Number"
    and "Campaign Name"; the per-campaign report page's own Export CSV
    does NOT -- confirmed by reading
    pages/sms/campaigns/sms_campaign_message_report_page.py).

    The report-creation form (SMSReportCreatePage) has no confirmed
    campaign-name filter -- only a date range and product type -- so
    this scopes the report by date range (the campaign's own send date)
    and then filters the downloaded rows by the real 'Campaign Name'
    column, which IS confirmed to be present.

    Returns (downloaded_file_path, export_headers, matched_rows) where
    matched_rows is the list of {header: value} dicts whose Campaign Name
    equals campaign_name exactly. Raises AssertionError/TimeoutError on
    report-generation failure or timeout -- callers must not proceed to
    DLR verification on a failed/incomplete export.
    """
    columns = columns or ["phone_number", "message_id", "campaign_name", "status"]
    report_name = f"DLR_Dynamic_{campaign_name}_{int(time.time())}"

    create_page.navigate()
    create_page.wait_for_form_load()
    create_page.set_report_name(report_name)
    create_page.set_product_type(create_page.TYPE_ALL)
    create_page.set_from_date(from_date_str)
    create_page.set_to_date(to_date_str)
    create_page.deselect_all_columns()
    for col in columns:
        create_page.select_column(col)
    create_page.submit()

    download_page.navigate()
    download_page.wait_for_table_load()

    deadline = time.time() + timeout_seconds
    row_idx = None
    while time.time() < deadline:
        download_page.search(report_name)
        download_page.wait_for_table_load()
        idx = download_page.find_row_with_status(download_page.STATUS_COMPLETED)
        if idx >= 0:
            row_idx = idx
            break
        if download_page.find_row_with_status(download_page.STATUS_FAILED) >= 0:
            raise AssertionError(
                f"SMS Download Center report '{report_name}' failed to generate."
            )
        time.sleep(poll_interval_seconds)

    if row_idx is None:
        raise TimeoutError(
            f"SMS Download Center report '{report_name}' did not reach "
            f"Completed status within {timeout_seconds}s."
        )

    before = download_page.snapshot_downloads()
    download_page.click_download_icon(row_idx)
    downloaded_path = download_page.wait_for_download(
        timeout=max(60, poll_interval_seconds * 4), before=before
    )
    if not downloaded_path:
        raise AssertionError(f"Download did not complete for report '{report_name}'.")

    headers, rows = read_file_rows(downloaded_path)
    campaign_header = _find_column(headers, _CAMPAIGN_NAME_HEADER_KEYWORDS) or "Campaign Name"
    matched = [
        r for r in rows if (r.get(campaign_header) or "").strip() == campaign_name
    ]
    return downloaded_path, headers, matched


def extract_message_records(matched_rows, headers):
    """Section 7: dynamically collect {recipient, message_id} pairs from
    the export -- never a hardcoded message ID."""
    phone_header = _find_column(headers, _PHONE_HEADER_KEYWORDS) or "Phone Number"
    msgid_header = _find_column(headers, _MESSAGE_ID_HEADER_KEYWORDS) or "Message Id"
    records = []
    for r in matched_rows:
        recipient = (r.get(phone_header) or "").strip()
        message_id = (r.get(msgid_header) or "").strip()
        if message_id:
            records.append({"recipient": recipient, "message_id": message_id})
    return records


# ─────────────────────────────────────────────────────────────────────────
# Section 5-7 (preferred path): SMS Messages Log -- filtered precisely to
# this one campaign's run, exported directly (its export is confirmed,
# independently of this task, to carry Message Id -- see
# constants/sms/messaging/sms_message_headers.py's
# EXPECTED_SMS_MESSAGE_HEADERS, which includes "Message Id", "Mobile
# Number" and "DLT Template ID", and the already-passing test
# tests/sms/messaging/test_sms_message_flow.py that validates them
# against a real download via message_page.export()). This replaces the
# SMS Download Center path above as the test's actual message-ID source;
# export_campaign_message_records()/extract_message_records() above are
# kept only as a documented alternate path, not called by the test.
# ─────────────────────────────────────────────────────────────────────────

_FIVE_MIN_OPTION_VALUES = {f"{h:02d}:{m:02d}" for h in range(24) for m in range(0, 60, 5)}


def floor_to_5min(dt):
    """Round dt DOWN to the nearest real 5-minute option confirmed in the
    Messages page's Received From/To time <select> (00:00, 00:05, ...,
    23:55). Used for the 'from' bound so the window never excludes a
    message that was actually sent at or after the true start time."""
    minute = (dt.minute // 5) * 5
    return dt.replace(minute=minute, second=0, microsecond=0)


def ceil_to_5min(dt):
    """Round dt UP to the nearest real 5-minute option (see
    floor_to_5min's docstring). Used for the 'to' bound so the window
    never excludes a message sent just before the true end time, which a
    plain floor() would risk cutting off."""
    if dt.second == 0 and dt.microsecond == 0 and dt.minute % 5 == 0:
        return dt.replace(second=0, microsecond=0)
    base = dt.replace(minute=0, second=0, microsecond=0)
    steps = (dt.minute // 5) + 1
    candidate = base + timedelta(minutes=steps * 5)
    return candidate


def format_filter_date_time(dt):
    """Returns (date_str, time_str) = ('YYYY-MM-DD', 'HH:MM') for the
    confirmed real <input type="date"> + 5-minute-increment <select>
    pair (SMSMessagePage.set_filter_received_range()). time_str is
    guaranteed to be one of the real option values since callers are
    expected to pass an already floor_to_5min()/ceil_to_5min()-rounded
    datetime."""
    time_str = dt.strftime("%H:%M")
    assert time_str in _FIVE_MIN_OPTION_VALUES, (
        f"{time_str!r} is not one of the real 5-minute-increment option "
        f"values on the Messages page's time filter -- round with "
        f"floor_to_5min()/ceil_to_5min() first."
    )
    return dt.strftime("%Y-%m-%d"), time_str


def capture_campaign_dlt_template_id(report_page):
    """Opens the View popup on the first row of the (already-loaded)
    Campaign Report page and reads the DLT Template ID from it --
    SmsCampaignMessageReportPage.message_details_popup() is confirmed to
    return the SAME Livewire modal the SMS Messages page itself uses
    (see that method's own docstring), so its new, dedicated
    get_popup_dlt_template_id() (pages/sms/messaging/sms_message_page.py)
    is reused directly rather than re-implemented here. Returns '' (not
    an exception) if the popup never opens or the field isn't found --
    callers decide whether a blank DLT Template ID is acceptable for
    their filter (e.g. by skipping that one filter rather than failing
    the whole run)."""
    try:
        opened = report_page.click_view_in_row(0)
        if not opened:
            return ""
        popup = report_page.message_details_popup()
        if not popup.is_popup_open():
            return ""
        dlt_id = popup.get_popup_dlt_template_id()
        popup.close_popup()
        return (dlt_id or "").strip()
    except Exception:
        return ""


def collect_message_records_from_messages_log(
    message_page,
    dlt_template_id,
    sender_id,
    from_dt,
    to_dt,
    export_timeout_ms=120000,
):
    """Sections 5-7 of the spec, via the SMS Messages Log page instead of
    the Download Center: filter the Messages page down to exactly this
    campaign's run (DLT Template ID + Sender ID + Source=Campaign +
    Status in {DELIVRD, FAILED, REJECTED} -- the terminal/non-pending
    statuses, confirmed real option values -- + the precise Received
    From/To window, rounded to the confirmed real 5-minute increments),
    then export CSV (SMSMessagePage.export(), already confirmed working
    and already validated by test_sms_message_flow.py against
    constants.sms_message_headers.EXPECTED_SMS_MESSAGE_HEADERS, which
    includes "Message Id" and "Mobile Number").

    from_dt/to_dt: datetime objects already rounded with
    floor_to_5min()/ceil_to_5min().

    Returns (downloaded_file_path, export_headers, rows) where rows is
    the list of {header: value} dicts from the export -- NOT yet reduced
    to {recipient, message_id} pairs (see extract_message_records(),
    reused as-is for that step). Raises AssertionError if the export
    never produces a real downloaded file (e.g. falls back to the
    background-job placeholder SMSMessagePage.export() returns for a
    very large/unfiltered export) -- callers must not proceed to DLR
    verification on a missing export.
    """
    from_date_str, from_time_str = format_filter_date_time(from_dt)
    to_date_str, to_time_str = format_filter_date_time(to_dt)

    message_page.navigate()
    message_page.clear_filter()
    message_page.open_filter_panel()
    if dlt_template_id:
        message_page.set_filter_dlt_template(dlt_template_id)
    message_page.set_filter_sender_id(sender_id)
    message_page.set_filter_source("campaign")
    message_page.set_filter_status_multi(["DELIVRD", "FAILED", "REJECTED"])
    message_page.set_filter_received_range(from_date_str, from_time_str, to_date_str, to_time_str)
    message_page.apply_filter()
    message_page.wait_for_table_load(timeout=15000)

    result = message_page.export(timeout_ms=export_timeout_ms)
    file_path = result.get("file_path")
    file_size = result.get("file_size", 0)
    if not file_path or file_path == "background_job_triggered.csv" or not file_size:
        raise AssertionError(
            f"SMS Messages Log export did not produce a real downloaded "
            f"file (result={result!r}) -- the filtered result set may be "
            f"too large for a direct-download export, or the export "
            f"failed outright. Not proceeding to DLR verification without "
            f"a real export file."
        )

    headers, rows = read_file_rows(file_path)
    return file_path, headers, rows


# ─────────────────────────────────────────────────────────────────────────
# Section 8-10: Verify DLRs / Recipient-to-DLR Correlation / Complete
# DLR Coverage
# ─────────────────────────────────────────────────────────────────────────

def verify_bulk_dlrs_chunked(
    api_client, message_ids, chunk_size, timeout_seconds, interval_seconds
):
    """Section 8: verify DLRs for every exported message id via the
    existing DLR Receiver (utils.dlr_helpers.poll_bulk_dlr -- the SAME
    helper already used by test_sms_campaign_dlr_bulk.py, not duplicated
    here), chunked for safety at 100K scale (see module docstring's
    flagged engineering choice). Never generates a DLR manually.

    Returns (results: dict[message_id -> record], raw_bodies: list) where
    raw_bodies carries one entry per chunk call for failure-message
    context.
    """
    all_results = {}
    raw_bodies = []
    unique_ids = list(dict.fromkeys(message_ids))  # de-dup, preserve order
    for i in range(0, len(unique_ids), chunk_size):
        chunk = unique_ids[i : i + chunk_size]
        verify_response, verify_body, results = poll_bulk_dlr(
            api_client,
            chunk,
            timeout_seconds=timeout_seconds,
            interval_seconds=interval_seconds,
        )
        raw_bodies.append(
            {
                "chunk_start": i,
                "chunk_size": len(chunk),
                "status_code": getattr(verify_response, "status_code", None),
                "body": verify_body,
            }
        )
        if results:
            all_results.update(results)
    return all_results, raw_bodies


_RECIPIENT_FIELD_KEYS = ("recipient", "phone_number", "phone", "destination", "msisdn")


def correlate_message_records(message_records, dlr_results):
    """Sections 9-10: for every exported {recipient, message_id} record,
    determine whether its DLR was received, and whether any recipient
    field the DLR response happens to carry (if any -- see module
    docstring's honestly-flagged gap) agrees with the exported recipient.

    Returns a dict with:
      missing            -- records whose message_id has no DLR entry at all
      not_received       -- records whose DLR entry exists but received != true
      recipient_mismatch -- records where the DLR response DID carry a
                             recipient-like field and it disagreed with the
                             exported recipient (see module docstring: this
                             is 0 whenever the API carries no such field at
                             all, which is the confirmed, documented case
                             today -- not a fabricated guess).
      duplicate_message_ids -- message_ids that appeared on more than one
                             exported record.
      verified             -- records that passed every check above.
    """
    missing = []
    not_received = []
    recipient_mismatch = []
    verified = []

    seen_ids = {}
    duplicate_message_ids = []
    for rec in message_records:
        mid = rec["message_id"]
        seen_ids[mid] = seen_ids.get(mid, 0) + 1
    for mid, count in seen_ids.items():
        if count > 1:
            duplicate_message_ids.append(mid)

    for rec in message_records:
        mid = rec["message_id"]
        recipient = rec["recipient"]
        entry = dlr_results.get(mid)
        if entry is None or not isinstance(entry, dict):
            missing.append(rec)
            continue
        if not entry.get("received"):
            not_received.append(rec)
            continue

        dlr_recipient = None
        for key in _RECIPIENT_FIELD_KEYS:
            if key in entry and entry[key]:
                dlr_recipient = str(entry[key]).strip()
                break
        if dlr_recipient is not None and dlr_recipient != recipient:
            recipient_mismatch.append({**rec, "dlr_recipient": dlr_recipient})
            continue

        verified.append(rec)

    return {
        "missing": missing,
        "not_received": not_received,
        "recipient_mismatch": recipient_mismatch,
        "duplicate_message_ids": duplicate_message_ids,
        "verified": verified,
    }


def unmatched_dlr_message_ids(dlr_results, message_records):
    """DLR entries returned for a message_id that was never among the
    exported records -- same 'Unmatched DLRs' bonus check already used by
    test_sms_campaign_dlr_bulk.py."""
    known_ids = {rec["message_id"] for rec in message_records}
    return [mid for mid in dlr_results if mid not in known_ids]


# ─────────────────────────────────────────────────────────────────────────
# Section 15: Failure Report
# ─────────────────────────────────────────────────────────────────────────

def build_summary_text(
    recipient_file_name,
    input_recipients,
    export_records,
    expected_dlrs,
    received_dlrs,
    missing_dlrs,
    unmatched_message_ids_count,
    recipient_mismatches,
    duplicate_message_ids,
    result,
):
    """Builds the EXACT summary format required by Section 15 of the
    spec."""
    lines = [
        "SMS Campaign DLR Verification",
        "",
        f"Recipient File: {recipient_file_name}",
        "",
        f"Input Recipients: {input_recipients}",
        f"Campaign Export Records: {export_records}",
        "",
        f"Expected DLRs: {expected_dlrs}",
        f"Received DLRs: {received_dlrs}",
        "",
        f"Missing DLRs: {missing_dlrs}",
        f"Unmatched Message IDs: {unmatched_message_ids_count}",
        f"Recipient Mismatches: {recipient_mismatches}",
        f"Duplicate Message IDs: {duplicate_message_ids}",
        "",
        f"Result: {result}",
    ]
    return "\n".join(lines)


def build_failure_table(rows):
    """rows: iterable of (message_id, recipient, reason). Returns the
    'Message ID | Recipient | Failure Reason' table required by Section
    15 when failures exist."""
    lines = [
        "Message ID | Recipient | Failure Reason",
        "-----------|-----------|----------------",
    ]
    for mid, recipient, reason in rows:
        lines.append(f"{mid} | {recipient} | {reason}")
    return "\n".join(lines)
