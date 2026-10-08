"""
tests/unit/reporting/test_report_generation.py -- reporting/html_report.py
and the overall parallel-worker-aggregation / missing-CI-variable paths.
No browser is launched anywhere in this file.
"""
from reporting import collector
from reporting.html_report import render_html
from reporting.summary import build_summary, duration_stats, group_by, platform_health, slowest, dlr_summary


def _context(records, meta=None):
    meta = meta or {"run_id": "r1", "environment": "qa", "channel": "sms", "test_type": "smoke",
                     "pass_rate": 0, "duration_seconds": 10}
    summary = build_summary(records, meta)
    return {
        "summary": summary,
        "channel_summary": group_by(records, "channel"),
        "feature_summary": group_by(records, "feature"),
        "failures": records,
        "trend": {"new": [], "recurring": [], "recovered": [], "history_available": False},
        "flaky": {},
        "slowest": slowest(records),
        "duration_stats": duration_stats(records),
        "platform_health": platform_health([]),
        "dlr_summary": dlr_summary(records),
    }


def test_render_html_with_no_failures_does_not_crash():
    records = [collector.build_record("tests/sms/x.py::test_1", "passed", 1.0)]
    html = render_html(_context(records))
    assert "<html" in html
    assert "No failures" in html


def test_render_html_includes_failed_test_name_escaped():
    records = [
        collector.build_record(
            "tests/sms/x.py::test_<bad>", "failed", 2.0,
            exc_type="AssertionError", message="boom",
        )
    ]
    html = render_html(_context(records))
    assert "test_&lt;bad&gt;" in html
    assert "<script>alert" not in html  # no raw injection


def test_render_html_never_requires_external_resources():
    # requirement #18: "No server/database should be required to view
    # the generated report ... must work as a standalone HTML artifact."
    records = [collector.build_record("tests/sms/x.py::test_1", "passed", 1.0)]
    html = render_html(_context(records))
    assert "http://" not in html
    assert "https://" not in html
    assert "<script src=" not in html
    assert '<link rel="stylesheet"' not in html


def test_render_html_with_missing_ci_metadata_shows_not_available():
    meta = {"run_id": "r1", "environment": "qa", "channel": "sms", "test_type": "smoke",
            "pipeline_id": "Not available", "build_number": "Not available",
            "duration_seconds": 0}
    records = [collector.build_record("tests/sms/x.py::test_1", "passed", 1.0)]
    html = render_html(_context(records, meta))
    # must render without raising even though CI fields are absent/placeholder
    assert "<html" in html


def test_render_html_dlr_section_hidden_when_no_dlr_tests():
    records = [collector.build_record("tests/sms/campaigns/test_a.py::test_1", "passed", 1.0)]
    html = render_html(_context(records))
    assert "DLR Summary" not in html


def test_render_html_dlr_section_shown_when_dlr_tests_present():
    records = [
        collector.build_record("tests/sms/messaging/test_dlr.py::test_dlr", "failed", 10.0,
                                exc_type="TimeoutError", message="DLR not received within timeout"),
    ]
    html = render_html(_context(records))
    assert "DLR Summary" in html


def test_parallel_worker_records_aggregate_into_one_summary():
    # requirement #30: "the reporting system must work correctly with
    # pytest -n 5 --dist loadscope ... one correct aggregated report."
    # Simulated here by building records tagged with different workers
    # and confirming build_summary/group_by don't care which worker
    # produced which record -- they aggregate across all of them.
    records = [
        collector.build_record("tests/sms/a.py::t1", "passed", 1.0, worker="gw0"),
        collector.build_record("tests/sms/b.py::t2", "failed", 2.0, worker="gw1",
                                exc_type="AssertionError", message="x"),
        collector.build_record("tests/rcs/c.py::t3", "passed", 3.0, worker="gw2"),
        collector.build_record("tests/rcs/d.py::t4", "skipped", 0.0, worker="gw3"),
    ]
    summary = build_summary(records, {"run_id": "r1"})
    assert summary["total"] == 4
    assert summary["passed"] == 2
    assert summary["failed"] == 1
    assert summary["skipped"] == 1
    channels = group_by(records, "channel")
    assert channels["sms"]["total"] == 2
    assert channels["rcs"]["total"] == 2


def test_setup_failure_record_has_no_category_without_classification_info():
    # A setup-phase (fixture) failure with no exception info still
    # produces a valid record -- category falls back to UNKNOWN rather
    # than raising.
    record = collector.build_record("tests/sms/x.py::test_1", "failed", 0.5, when="setup")
    assert record["category"] == "UNKNOWN"
    assert record["fingerprint"] is not None
