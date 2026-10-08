"""
tests/unit/reporting/test_classifier.py -- reporting/classifier.py.

No browser, no network -- pure rule-based text classification.
"""
from reporting.classifier import (
    ASSERTION, AUTHENTICATION, DLR, PLATFORM_ERROR, TIMEOUT, UNKNOWN, classify,
)


def test_dlr_timeout_classified_as_dlr_not_timeout():
    # requirement #9's own example: "DLR timeout -> DLR" (DLR is checked
    # before the generic TIMEOUT rule, since it's the more specific signal).
    assert classify("TimeoutError", "DLR not received within timeout") == DLR


def test_playwright_timeout_without_dlr_classified_as_timeout():
    assert classify("TimeoutError", "Timeout 30000ms exceeded waiting for selector") == TIMEOUT


def test_platform_error_whoops_page():
    assert classify("", "Whoops, something went wrong on our end") == PLATFORM_ERROR


def test_authentication_401():
    assert classify("", "Request failed with status 401 Unauthorized") == AUTHENTICATION


def test_assertion_error():
    assert classify("AssertionError", "Expected 'ACTIVE' but got 'PENDING'") == ASSERTION


def test_unknown_when_nothing_matches():
    assert classify("WeirdCustomError", "something entirely unrelated happened") == UNKNOWN


def test_unknown_on_empty_input():
    assert classify("", "", "") == UNKNOWN


def test_never_misclassifies_plain_assertion_as_platform_error():
    # requirement #14: "Do not classify normal assertion failures as
    # platform errors."
    result = classify("AssertionError", "Expected 5 but got 3")
    assert result != PLATFORM_ERROR
    assert result == ASSERTION
