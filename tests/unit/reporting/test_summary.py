"""
tests/unit/reporting/test_summary.py -- reporting/summary.py.
"""
from reporting import collector
from reporting.summary import (
    build_summary, duration_stats, group_by, platform_health, slowest, dlr_summary,
)


def _records():
    return [
        collector.build_record("tests/sms/campaigns/test_a.py::test_1", "passed", 10.0),
        collector.build_record("tests/sms/campaigns/test_a.py::test_2", "failed", 20.0,
                                exc_type="AssertionError", message="Expected X got Y"),
        collector.build_record("tests/sms/messaging/test_b.py::test_3", "skipped", 0.0),
        collector.build_record("tests/rcs/reports/test_c.py::test_4", "passed", 5.0),
    ]


def test_build_summary_counts_are_never_hardcoded():
    records = _records()
    meta = {"run_id": "r1", "environment": "qa", "instance": None, "channel": "full", "test_type": "full"}
    summary = build_summary(records, meta)
    assert summary["total"] == 4
    assert summary["passed"] == 2
    assert summary["failed"] == 1
    assert summary["skipped"] == 1
    assert summary["status"] == "FAILED"
    assert summary["pass_rate"] == 50.0
    # meta fields pass through untouched
    assert summary["run_id"] == "r1"
    assert summary["environment"] == "qa"


def test_build_summary_all_passed_is_status_passed():
    records = [collector.build_record("tests/sms/x.py::test_1", "passed", 1.0)]
    summary = build_summary(records, {"run_id": "r2"})
    assert summary["status"] == "PASSED"
    assert summary["failed"] == 0
    assert summary["pass_rate"] == 100.0


def test_build_summary_empty_records_no_division_by_zero():
    summary = build_summary([], {"run_id": "r3"})
    assert summary["total"] == 0
    assert summary["pass_rate"] == 0.0


def test_group_by_channel():
    groups = group_by(_records(), "channel")
    assert groups["sms"]["total"] == 3
    assert groups["sms"]["passed"] == 1
    assert groups["sms"]["failed"] == 1
    assert groups["sms"]["skipped"] == 1
    assert groups["rcs"]["total"] == 1
    assert groups["rcs"]["pass_rate"] == 100.0


def test_group_by_feature():
    groups = group_by(_records(), "feature")
    assert groups["campaigns"]["total"] == 2
    assert groups["messaging"]["total"] == 1
    assert groups["reports"]["total"] == 1


def test_slowest_orders_descending_and_respects_limit():
    records = _records()
    top2 = slowest(records, limit=2)
    assert [r["duration"] for r in top2] == [20.0, 10.0]


def test_duration_stats_computed_from_actual_durations():
    # Only PASSED/FAILED durations count (a "skipped" test has no real
    # execution time to average in) -- same filter slowest() already
    # applies. _records() has three timed entries: 10.0, 20.0, 5.0.
    stats = duration_stats(_records())
    assert stats["total"] == 35.0
    assert stats["average"] == round(35.0 / 3, 2)
    assert stats["median"] == 10.0
    assert stats["p95"] == 20.0


def test_duration_stats_empty_list_returns_zeros():
    stats = duration_stats([])
    assert stats == {"total": 0.0, "average": 0.0, "median": 0.0, "p95": 0.0}


def test_platform_health_healthy_when_no_captures():
    health = platform_health([])
    assert health["healthy"] is True
    assert health["total"] == 0


def test_platform_health_buckets_by_pattern():
    captures = [
        {"pattern": "500 Internal Server Error"},
        {"pattern": "Whoops, something went wrong"},
        {"pattern": "Livewire encountered an error"},
    ]
    health = platform_health(captures)
    assert health["healthy"] is False
    assert health["http_500"] == 1
    assert health["whoops"] == 1
    assert health["livewire"] == 1
    assert health["total"] == 3


def test_dlr_summary_zero_when_no_dlr_tests():
    records = [collector.build_record("tests/sms/campaigns/test_a.py::test_1", "passed", 1.0)]
    assert dlr_summary(records)["total"] == 0


def test_dlr_summary_picks_up_dlr_category_and_path():
    records = [
        collector.build_record("tests/sms/messaging/test_dlr.py::test_dlr", "failed", 125.4,
                                exc_type="TimeoutError", message="DLR not received within timeout"),
        collector.build_record("tests/sms/messaging/test_dlr.py::test_dlr_ok", "passed", 8.0),
    ]
    dlr = dlr_summary(records)
    assert dlr["total"] == 2
    assert dlr["passed"] == 1
    assert dlr["failed"] == 1
    assert dlr["timeout_failures"] == 1
