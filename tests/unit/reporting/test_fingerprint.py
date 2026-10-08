"""
tests/unit/reporting/test_fingerprint.py -- reporting/fingerprint.py.
"""
from reporting.fingerprint import fingerprint, normalize_message


def test_normalize_strips_uuid():
    msg = "DLR not received for message 11112222-3333-4444-5555-666677778888"
    assert "11112222-3333-4444-5555-666677778888" not in normalize_message(msg)


def test_normalize_strips_long_digit_runs():
    msg = "Campaign 123456789012 failed validation"
    normalized = normalize_message(msg)
    assert "123456789012" not in normalized


def test_normalize_strips_timestamp():
    msg = "Failed at 2026-10-07T18:56:00.123Z during upload"
    normalized = normalize_message(msg)
    assert "2026-10-07T18:56:00.123Z" not in normalized


def test_normalize_strips_worker_id():
    msg = "Worker gw3 crashed unexpectedly"
    assert "gw3" not in normalize_message(msg)


def test_normalize_collapses_whitespace():
    assert normalize_message("a   b\n\nc") == "a b c"


def test_normalize_never_raises_on_empty_or_none():
    assert normalize_message(None) == ""
    assert normalize_message("") == ""


def test_fingerprint_stable_for_same_inputs():
    a = fingerprint("tests/sms/x.py::test_a", "TimeoutError", "DLR timeout for message 11112222-3333-4444-5555-666677778888")
    b = fingerprint("tests/sms/x.py::test_a", "TimeoutError", "DLR timeout for message 11112222-3333-4444-5555-666677778888")
    assert a == b


def test_fingerprint_same_despite_different_dynamic_ids():
    # requirement #10: normalize dynamic values (message IDs here) BEFORE
    # hashing, so the SAME underlying failure produces the SAME
    # fingerprint across two different runs with two different message IDs.
    a = fingerprint("tests/sms/x.py::test_a", "TimeoutError", "DLR timeout for message 11112222-3333-4444-5555-666677778888")
    b = fingerprint("tests/sms/x.py::test_a", "TimeoutError", "DLR timeout for message 99998888-7777-6666-5555-444433332222")
    assert a == b


def test_fingerprint_differs_for_different_test():
    a = fingerprint("tests/sms/x.py::test_a", "TimeoutError", "DLR timeout")
    b = fingerprint("tests/sms/y.py::test_b", "TimeoutError", "DLR timeout")
    assert a != b


def test_fingerprint_differs_for_different_exception_type():
    a = fingerprint("tests/sms/x.py::test_a", "TimeoutError", "failed")
    b = fingerprint("tests/sms/x.py::test_a", "AssertionError", "failed")
    assert a != b


def test_fingerprint_never_contains_raw_uuid():
    fp = fingerprint("tests/sms/x.py::test_a", "TimeoutError", "id 11112222-3333-4444-5555-666677778888")
    assert "11112222-3333-4444-5555-666677778888" not in fp
