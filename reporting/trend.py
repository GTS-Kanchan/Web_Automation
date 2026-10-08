"""
reporting/trend.py -- new/recurring/recovered classification (requirement
#11) and flaky-test detection (requirement #12), both computed purely
from history.py's filesystem records -- no browser, no network.
"""

DEFAULT_FLAKY_MIN_RUNS = 3


def compute_new_recurring_recovered(current_tests: dict, previous_record) -> dict:
    """`current_tests`: {test_nodeid: status} for every test THIS run.
    `previous_record`: the dict load_previous_comparable() returned, or
    None.

    new       = failed now, passed (or didn't fail) in the previous run
    recurring = failed now AND failed in the previous run
    recovered = failed in the previous run, passes now

    Never fabricated when there's no previous run (requirement #11)."""
    current_failed = {t for t, s in current_tests.items() if s == "failed"}

    if previous_record is None:
        return {
            "new": sorted(current_failed),
            "recurring": [],
            "recovered": [],
            "history_available": False,
        }

    previous_tests = previous_record.get("tests", {})
    previous_failed = {t for t, s in previous_tests.items() if s == "failed"}

    new = sorted(current_failed - previous_failed)
    recurring = sorted(current_failed & previous_failed)
    recovered = sorted(t for t in previous_failed if current_tests.get(t) == "passed")

    return {
        "new": new,
        "recurring": recurring,
        "recovered": recovered,
        "history_available": True,
    }


def compute_flaky(history_records: list, current_tests: dict, min_runs: int = DEFAULT_FLAKY_MIN_RUNS) -> dict:
    """requirement #12: a test needs AT LEAST `min_runs` (default 3)
    recorded executions AND both a pass and a fail among them before it
    is called flaky -- a single failure is never enough.

    `history_records`: oldest -> newest list from
    history.load_all_comparable(); `current_tests` is folded in as the
    latest data point."""
    per_test = {}
    for record in history_records:
        for test, status in record.get("tests", {}).items():
            per_test.setdefault(test, []).append(status)
    for test, status in current_tests.items():
        per_test.setdefault(test, []).append(status)

    flaky = {}
    for test, statuses in per_test.items():
        if len(statuses) < min_runs:
            continue
        passed = sum(1 for s in statuses if s == "passed")
        failed = sum(1 for s in statuses if s == "failed")
        if passed > 0 and failed > 0:
            total = passed + failed
            flaky[test] = {
                "executions": total,
                "passed": passed,
                "failed": failed,
                "flaky_rate": round((failed / total) * 100, 2),
            }
    return flaky
