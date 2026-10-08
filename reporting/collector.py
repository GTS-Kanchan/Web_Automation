"""
reporting/collector.py -- turns one pytest TestReport (already-executed
test phase) into the canonical record dict this whole package shares.

Called from conftest.py's pytest_runtest_logreport hook (requirement #29:
reuse existing hooks, do not add a second competing plugin) for every
phase of every test, in BOTH a plain run and under pytest-xdist -- xdist
replays each worker's report through this same hook on the controller
(the exact mechanism terminalreporter/pytest-html already depend on), so
appending to a module-level list from this hook is xdist-safe as long as
only the controller process's list is ever written to reports/ (see
conftest.py's pytest_sessionfinish/_is_xdist_worker guard).

No browser/network access here -- pure data transformation, which is
also why this module (unlike conftest.py) is safely unit-testable.
"""
from reporting.classifier import classify
from reporting.fingerprint import fingerprint, normalize_message
from reporting.models import mask_phone_numbers


def channel_and_feature(nodeid: str):
    """tests/<channel>/<feature>/test_x.py::test_y -> (channel, feature).
    Derived purely from the path -- never a second, hand-maintained
    channel list (requirement #6/#7)."""
    path = (nodeid or "").split("::")[0].replace("\\", "/")
    parts = [p for p in path.split("/") if p]
    channel = parts[1] if len(parts) > 1 and parts[0] == "tests" else "unknown"
    feature = parts[2] if len(parts) > 2 else "general"
    return channel, feature


def build_record(
    nodeid: str,
    status: str,
    duration: float = 0.0,
    when: str = "call",
    marker: str = "-",
    worker: str = "master",
    exc_type: str = "",
    message: str = "",
    longrepr_text: str = "",
    screenshot: str = None,
    log: str = None,
) -> dict:
    """status: "passed" | "failed" | "skipped" | "xfailed" | "xpassed".
    Only a FAILED record gets a category/fingerprint -- there is nothing
    to classify or fingerprint about a pass or a skip."""
    channel, feature = channel_and_feature(nodeid)
    category = None
    fp = None
    if status == "failed":
        category = classify(exc_type, message, longrepr_text)
        fp = fingerprint(nodeid, exc_type, message)

    error = normalize_message(message)[:1000] if message else None
    error_raw = (message or "")[:2000] or None
    stack_trace = (longrepr_text or "")[:8000] or None

    # DLR failures carry a real recipient phone number in their error
    # text/stack trace (requirement #15/#38) -- mask it before it ever
    # reaches failures.json/dashboard.html. Non-DLR categories are left
    # untouched: masking everywhere would risk hiding useful debug
    # numbers (status codes, durations, worker ids) with no privacy
    # requirement attached to them.
    if category == "DLR":
        error = mask_phone_numbers(error)
        error_raw = mask_phone_numbers(error_raw)
        stack_trace = mask_phone_numbers(stack_trace)

    return {
        "test": nodeid,
        "channel": channel,
        "feature": feature,
        "status": status,
        "when": when,
        "marker": marker,
        "worker": worker,
        "duration": round(duration or 0.0, 2),
        "category": category,
        "fingerprint": fp,
        "error": error,
        "error_raw": error_raw,
        "stack_trace": stack_trace,
        "screenshot": screenshot,
        "log": log,
    }
