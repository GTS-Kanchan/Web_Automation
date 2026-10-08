"""
tests/unit/reporting/test_trend.py -- reporting/trend.py.
"""
from reporting.trend import compute_flaky, compute_new_recurring_recovered


def test_no_previous_run_means_all_current_failures_are_new():
    current = {"t1": "passed", "t2": "failed", "t3": "failed"}
    result = compute_new_recurring_recovered(current, None)
    assert result["history_available"] is False
    assert sorted(result["new"]) == ["t2", "t3"]
    assert result["recurring"] == []
    assert result["recovered"] == []


def test_new_recurring_recovered_classified_correctly():
    previous = {"tests": {"t1": "passed", "t2": "failed", "t3": "failed", "t4": "passed"}}
    current = {"t1": "passed", "t2": "failed", "t3": "passed", "t4": "failed"}
    result = compute_new_recurring_recovered(current, previous)
    assert result["history_available"] is True
    assert result["new"] == ["t4"]        # failed now, was passing before
    assert result["recurring"] == ["t2"]  # failed both times
    assert result["recovered"] == ["t3"]  # failed before, passes now


def test_recovered_requires_passing_now_not_just_absent():
    # A test that simply didn't run this time should NOT be reported as
    # "recovered" -- only one that actually passed now counts.
    previous = {"tests": {"t1": "failed"}}
    current = {"t2": "passed"}  # t1 doesn't even appear this run
    result = compute_new_recurring_recovered(current, previous)
    assert result["recovered"] == []


def test_flaky_requires_at_least_three_executions():
    history_records = [
        {"tests": {"t1": "passed"}},
        {"tests": {"t1": "failed"}},
    ]
    current = {"t1": "passed"}  # only 3 total -- exactly at the minimum
    flaky = compute_flaky(history_records, current, min_runs=3)
    assert "t1" in flaky
    assert flaky["t1"]["executions"] == 3


def test_flaky_not_flagged_with_only_two_executions():
    history_records = [{"tests": {"t1": "failed"}}]
    current = {"t1": "passed"}  # only 2 total
    flaky = compute_flaky(history_records, current, min_runs=3)
    assert "t1" not in flaky


def test_flaky_not_flagged_when_always_passing():
    history_records = [{"tests": {"t1": "passed"}}, {"tests": {"t1": "passed"}}]
    current = {"t1": "passed"}
    flaky = compute_flaky(history_records, current, min_runs=3)
    assert "t1" not in flaky


def test_flaky_not_flagged_after_a_single_failure():
    # requirement #12: "Do not mark a test flaky after a single failure."
    history_records = [{"tests": {"t1": "passed"}}, {"tests": {"t1": "passed"}}]
    current = {"t1": "failed"}  # 3rd execution, only ONE failure total
    flaky = compute_flaky(history_records, current, min_runs=3)
    assert "t1" in flaky  # 3 executions + both outcomes observed -> flagged
    assert flaky["t1"]["failed"] == 1
    assert flaky["t1"]["flaky_rate"] == round(1 / 3 * 100, 2)


def test_flaky_rate_calculation():
    history_records = [
        {"tests": {"t1": "passed"}},
        {"tests": {"t1": "failed"}},
        {"tests": {"t1": "passed"}},
        {"tests": {"t1": "failed"}},
    ]
    current = {"t1": "passed"}
    flaky = compute_flaky(history_records, current, min_runs=3)
    assert flaky["t1"]["executions"] == 5
    assert flaky["t1"]["passed"] == 3
    assert flaky["t1"]["failed"] == 2
    assert flaky["t1"]["flaky_rate"] == 40.0
