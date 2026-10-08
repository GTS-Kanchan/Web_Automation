"""
tests/unit/reporting/test_history.py -- reporting/history.py.

Uses pytest's built-in `tmp_path` fixture as an isolated reports_root for
every test, so nothing here ever touches the real reports/ directory.
"""
import json
import os

from reporting import history


def _summary(run_id, environment="qa", instance=None, channel="sms", test_type="smoke"):
    return {
        "run_id": run_id, "environment": environment, "instance": instance,
        "channel": channel, "test_type": test_type,
    }


def test_save_history_writes_a_file(tmp_path):
    path = history.save_history(str(tmp_path), _summary("r1"), [{"test": "t1", "status": "passed"}])
    assert os.path.isfile(path)
    with open(path) as f:
        data = json.load(f)
    assert data["summary"]["run_id"] == "r1"
    assert data["tests"] == {"t1": "passed"}


def test_save_history_never_includes_screenshot_paths(tmp_path):
    # requirement #22: "Each history file should contain only
    # summary/result metadata ... Do not copy screenshots into history."
    failures = [{"test": "t1", "status": "failed", "screenshot": "screenshots/gw0/t1.png"}]
    path = history.save_history(str(tmp_path), _summary("r1"), failures)
    with open(path) as f:
        raw = f.read()
    assert "screenshot" not in raw


def test_prune_respects_history_limit(tmp_path, monkeypatch):
    monkeypatch.setenv("REPORT_HISTORY_LIMIT", "3")
    for i in range(5):
        history.save_history(str(tmp_path), _summary(f"r{i}"), [])
    remaining = os.listdir(history.history_dir(str(tmp_path)))
    assert len(remaining) == 3


def test_load_previous_comparable_returns_none_when_nothing_matches(tmp_path):
    history.save_history(str(tmp_path), _summary("r1", environment="staging"), [])
    result = history.load_previous_comparable(str(tmp_path), "qa", None, "sms", "smoke")
    assert result is None


def test_load_previous_comparable_matches_same_env_instance_channel_test_type(tmp_path):
    history.save_history(str(tmp_path), _summary("r1", environment="qa", channel="sms", test_type="smoke"), [])
    # a DIFFERENT test_type must not match (requirement #24)
    other = history.load_previous_comparable(str(tmp_path), "qa", None, "sms", "regression")
    assert other is None
    match = history.load_previous_comparable(str(tmp_path), "qa", None, "sms", "smoke")
    assert match is not None
    assert match["summary"]["run_id"] == "r1"


def test_load_previous_comparable_never_crosses_environments(tmp_path):
    # requirement #23: "Do NOT compare: QA run vs STAGING run"
    history.save_history(str(tmp_path), _summary("r1", environment="qa"), [])
    history.save_history(str(tmp_path), _summary("r2", environment="staging"), [])
    qa_match = history.load_previous_comparable(str(tmp_path), "qa", None, "sms", "smoke")
    assert qa_match["summary"]["run_id"] == "r1"
    staging_match = history.load_previous_comparable(str(tmp_path), "staging", None, "sms", "smoke")
    assert staging_match["summary"]["run_id"] == "r2"


def test_load_previous_comparable_excludes_current_run(tmp_path):
    history.save_history(str(tmp_path), _summary("r1"), [])
    result = history.load_previous_comparable(str(tmp_path), "qa", None, "sms", "smoke", exclude_run_id="r1")
    assert result is None


def test_load_all_comparable_oldest_to_newest(tmp_path):
    # Write directly with controlled, already-ordered filenames rather
    # than relying on save_history()'s second-granularity timestamp
    # (which would need a real sleep between calls to guarantee order).
    directory = history.history_dir(str(tmp_path))
    for i, name in enumerate(("20260101_000000", "20260101_000001", "20260101_000002")):
        with open(os.path.join(directory, f"{name}.json"), "w") as f:
            json.dump({"summary": _summary(f"r{i}"), "tests": {}}, f)
    records = history.load_all_comparable(str(tmp_path), "qa", None, "sms", "smoke")
    assert [r["summary"]["run_id"] for r in records] == ["r0", "r1", "r2"]
