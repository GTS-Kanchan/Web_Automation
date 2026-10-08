"""
reporting/history.py -- filesystem-based run history (requirement #22).

Each history file holds ONLY summary/result metadata (requirement #22:
"Do not copy screenshots into history") -- screenshots/logs stay under
reports/runs/<run-id>/, never duplicated here. History is pruned to the
last REPORT_HISTORY_LIMIT (default 100) records (requirement #22).
"""
import glob
import json
import os
import time

HISTORY_LIMIT_DEFAULT = 100


def history_dir(reports_root: str) -> str:
    path = os.path.join(reports_root, "history")
    os.makedirs(path, exist_ok=True)
    return path


def save_history(reports_root: str, summary: dict, failures: list) -> str:
    """Writes reports/history/<timestamp>_<run_id>.json and prunes old
    entries. `summary` must already be the full dict build_summary()
    returned (run_id/environment/instance/channel/test_type + counts) --
    this function does not recompute anything, only persists.

    The filename includes run_id (not just the second-granularity
    timestamp) because two runs finishing within the same wall-clock
    second would otherwise silently overwrite each other's history file
    instead of both being recorded -- confirmed by a unit test
    (tests/unit/reporting/test_history.py) running several save_history()
    calls in a tight loop. run_id is already unique per execution
    (Config.RUN_ID), so appending it guarantees a distinct filename while
    the leading timestamp keeps entries sorted chronologically."""
    path = history_dir(reports_root)
    run_id = (summary.get("run_id") or "").strip()
    stamp = time.strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(path, f"{stamp}_{run_id}.json" if run_id else f"{stamp}_{os.getpid()}.json")
    record = {
        "summary": summary,
        # test -> status, for every test that ran this run (not just
        # failures) -- this is what makes flaky detection and
        # new/recurring/recovered possible without re-reading JUnit.
        "tests": {f["test"]: f["status"] for f in failures},
    }
    with open(filename, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2)
    _prune(path)
    return filename


def _prune(path: str, limit: int = None) -> None:
    limit = limit or int(os.environ.get("REPORT_HISTORY_LIMIT", HISTORY_LIMIT_DEFAULT) or HISTORY_LIMIT_DEFAULT)
    files = sorted(glob.glob(os.path.join(path, "*.json")))
    excess = len(files) - limit
    for stale in files[:max(0, excess)]:
        try:
            os.remove(stale)
        except OSError:
            pass


def _is_comparable(hist_summary: dict, environment, instance, channel, test_type) -> bool:
    """requirement #23/#24: same environment, same instance (if any),
    same channel, same test_type -- never cross-environment, never
    cross-test-type unless explicitly requested (callers decide that by
    what they pass in, not this function)."""
    return (
        hist_summary.get("environment") == environment
        and (hist_summary.get("instance") or None) == (instance or None)
        and hist_summary.get("channel") == channel
        and hist_summary.get("test_type") == test_type
    )


def _load_json(path: str):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def load_previous_comparable(reports_root, environment, instance, channel, test_type, exclude_run_id=None):
    """Most recent PAST comparable run, or None (requirement #11: "If no
    previous run exists: History: Not available -- do not fabricate
    comparisons")."""
    path = history_dir(reports_root)
    for filename in sorted(glob.glob(os.path.join(path, "*.json")), reverse=True):
        record = _load_json(filename)
        if not record:
            continue
        summary = record.get("summary", {})
        if exclude_run_id and summary.get("run_id") == exclude_run_id:
            continue
        if _is_comparable(summary, environment, instance, channel, test_type):
            return record
    return None


def load_all_comparable(reports_root, environment, instance, channel, test_type, exclude_run_id=None, limit=None):
    """Oldest -> newest list of comparable history records, for flaky
    detection (reporting/trend.py), which needs more than just the
    single most recent run."""
    path = history_dir(reports_root)
    out = []
    for filename in sorted(glob.glob(os.path.join(path, "*.json"))):
        record = _load_json(filename)
        if not record:
            continue
        summary = record.get("summary", {})
        if exclude_run_id and summary.get("run_id") == exclude_run_id:
            continue
        if _is_comparable(summary, environment, instance, channel, test_type):
            out.append(record)
    if limit:
        out = out[-limit:]
    return out
