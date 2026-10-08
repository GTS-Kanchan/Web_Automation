"""
reporting/summary.py -- aggregate counts from actual collected records.
Never hardcodes a total/pass/fail count (requirement #5/#6/#7) -- every
number here is computed from the `records` list the collector built.
"""
import statistics


def _pct(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100, 2) if denominator else 0.0


def build_summary(records: list, meta: dict) -> dict:
    """`meta` carries the run-identity fields (run_id, environment,
    instance, channel, test_type, git_commit, ..., duration_seconds,
    workers, browser, headless) collected separately (see artifacts in
    conftest.py) -- this function only adds the computed result counts,
    so it never needs to know about CI variables or git."""
    total   = len(records)
    passed  = sum(1 for r in records if r["status"] == "passed")
    failed  = sum(1 for r in records if r["status"] == "failed")
    skipped = sum(1 for r in records if r["status"] == "skipped")
    xfailed = sum(1 for r in records if r["status"] == "xfailed")
    xpassed = sum(1 for r in records if r["status"] == "xpassed")

    summary = dict(meta)
    summary.update({
        "status": "FAILED" if failed else "PASSED",
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "xfailed": xfailed,
        "xpassed": xpassed,
        "pass_rate": _pct(passed, total),
    })
    return summary


def group_by(records: list, key: str) -> dict:
    """{key_value: {total, passed, failed, skipped, pass_rate}} -- used
    for both the channel summary (key="channel") and the feature summary
    (key="feature"). Order of insertion is preserved (dict, py3.7+), but
    callers should sort for display if a specific order matters."""
    groups = {}
    for r in records:
        k = r.get(key) or "unknown"
        g = groups.setdefault(k, {"total": 0, "passed": 0, "failed": 0, "skipped": 0})
        g["total"] += 1
        if r["status"] in g:
            g[r["status"]] += 1
    for g in groups.values():
        g["pass_rate"] = _pct(g["passed"], g["total"])
    return groups


def _timed(records: list) -> list:
    """PASSED/FAILED records only -- a "skipped" test never actually ran,
    so its (always-0) duration would skew an average/median/p95 computed
    over "actual test duration data" (requirement #13) downward for no
    real reason. slowest() and duration_stats() share this same filter."""
    return [r for r in records if r.get("duration") is not None and r["status"] in ("passed", "failed")]


def slowest(records: list, limit: int = 10) -> list:
    return sorted(_timed(records), key=lambda r: r["duration"], reverse=True)[:limit]


def duration_stats(records: list) -> dict:
    durations = [r["duration"] for r in _timed(records)]
    if not durations:
        return {"total": 0.0, "average": 0.0, "median": 0.0, "p95": 0.0}
    ordered = sorted(durations)
    p95_index = min(len(ordered) - 1, max(0, round(len(ordered) * 0.95) - 1))
    return {
        "total": round(sum(durations), 2),
        "average": round(statistics.mean(durations), 2),
        "median": round(statistics.median(durations), 2),
        "p95": round(ordered[p95_index], 2),
    }


def platform_health(error_captures: list) -> dict:
    """error_captures: list of {"pattern": str} dicts (from
    utils.error_monitor.ErrorCapture instances collected during the run).
    Buckets by a short label derived from the matched regex pattern text
    -- never reclassifies a normal assertion failure as a platform error
    (this only ever sees captures ErrorMonitor itself already decided
    were platform errors; it has no opinion on test assertions)."""
    buckets = {
        "http_500": 0, "whoops": 0, "livewire": 0,
        "network": 0, "browser_crash": 0, "other": 0,
    }
    for cap in error_captures:
        pattern = (cap.get("pattern") or "").lower()
        if "500" in pattern or "internal server" in pattern:
            buckets["http_500"] += 1
        elif "whoops" in pattern:
            buckets["whoops"] += 1
        elif "livewire" in pattern:
            buckets["livewire"] += 1
        elif "redis" in pattern or "connection" in pattern or "database" in pattern:
            buckets["network"] += 1
        elif "crash" in pattern:
            buckets["browser_crash"] += 1
        else:
            buckets["other"] += 1
    buckets["total"] = sum(v for k, v in buckets.items() if k != "total")
    buckets["healthy"] = buckets["total"] == 0
    return buckets


def dlr_summary(records: list) -> dict:
    """Only meaningful when at least one DLR-categorized or DLR-path test
    ran -- callers should check total > 0 before rendering this section
    (requirement #15: "add a DLR subsection WHEN DLR tests execute")."""
    dlr_records = [
        r for r in records
        if r.get("category") == "DLR" or "dlr" in (r.get("test") or "").lower()
    ]
    total = len(dlr_records)
    passed = sum(1 for r in dlr_records if r["status"] == "passed")
    failed = sum(1 for r in dlr_records if r["status"] == "failed")
    waits = [r["duration"] for r in dlr_records if r.get("duration") is not None]
    timeout_failures = sum(
        1 for r in dlr_records if r["status"] == "failed" and r.get("category") == "DLR"
        and "timeout" in (r.get("error") or "").lower()
    )
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "average_wait": round(statistics.mean(waits), 2) if waits else 0.0,
        "max_wait": round(max(waits), 2) if waits else 0.0,
        "timeout_failures": timeout_failures,
    }
