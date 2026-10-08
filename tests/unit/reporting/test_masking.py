"""
Covers requirement #15/#38: DLR failures must not expose a recipient's
full phone number in any report output (summary/failures.json, the
HTML dashboard, or raw error/stack-trace text). No browser launched --
pure function tests against reporting.models / reporting.collector.
"""
from reporting.collector import build_record
from reporting.models import mask_phone_numbers


def test_mask_phone_numbers_keeps_last_four_digits():
    assert mask_phone_numbers("DLR for +15551234567 timed out") == "DLR for +XXXXXXX4567 timed out"


def test_mask_phone_numbers_handles_number_without_plus():
    masked = mask_phone_numbers("recipient 447911123456 did not receive")
    assert "447911123456" not in masked
    assert masked.endswith("3456 did not receive")


def test_mask_phone_numbers_leaves_short_numeric_tokens_alone():
    # Status codes / durations / small counts must never be mistaken
    # for a phone number.
    assert mask_phone_numbers("status code 500") == "status code 500"
    assert mask_phone_numbers("wait=12.5s timeout=30") == "wait=12.5s timeout=30"


def test_mask_phone_numbers_empty_and_none_safe():
    assert mask_phone_numbers("") == ""
    assert mask_phone_numbers(None) is None


def test_build_record_masks_phone_number_for_dlr_category():
    record = build_record(
        nodeid="tests/sms/dlr/test_dlr.py::test_dlr_timeout",
        status="failed",
        duration=31.4,
        exc_type="DLRTimeoutError",
        message="DLR not received for +15551234567 within 30s",
        longrepr_text="E DLRTimeoutError: DLR not received for +15551234567 within 30s",
    )
    assert record["category"] == "DLR"
    assert "15551234567" not in (record["error"] or "")
    assert "15551234567" not in (record["error_raw"] or "")
    assert "15551234567" not in (record["stack_trace"] or "")
    assert "4567" in record["error_raw"]  # last 4 digits still visible for debugging


def test_build_record_does_not_mask_non_dlr_categories():
    # Masking is scoped to DLR -- an assertion failure that happens to
    # contain a long digit run (e.g. an order id) must not be altered.
    record = build_record(
        nodeid="tests/sms/test_send.py::test_order_id_matches",
        status="failed",
        duration=0.5,
        exc_type="AssertionError",
        message="expected order id 1234567890 but got 1234567891",
    )
    assert record["category"] == "ASSERTION"
    assert record["error_raw"] == "expected order id 1234567890 but got 1234567891"
