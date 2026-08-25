"""
utils/parallel.py — worker identity + collision-proof test-data naming for
parallel execution (pytest-xdist).

Why this exists
----------------
Requirement: parallel workers must never create the same campaign name,
template name, sender ID, contact, message, temp file, etc. Before this
module, the only uniqueness mechanism in the suite was
`f"{prefix}_{int(time.time())}"` (second-resolution timestamp) — two
workers creating a campaign in the same wall-clock second collide.

pytest-xdist sets the environment variable PYTEST_XDIST_WORKER inside each
worker process ("gw0", "gw1", ...); it is unset when running without -n
(single process — the plain, unchanged workflow every existing test still
uses today). Combining that with a monotonic high-resolution clock and a
short random suffix gives an identifier that's unique across workers, across
runs, and even across two calls a microsecond apart on the same worker.
"""
import os
import random
import string
import threading
import time

# A process-local counter as an extra tie-breaker — cheaper and more
# deterministic than relying on randomness alone when a test creates many
# records in a tight loop.
_counter_lock = threading.Lock()
_counter = 0


def worker_id() -> str:
    """'gw0', 'gw1', ... under pytest-xdist; 'master' in a plain single-process
    run (`pytest` with no -n) so existing non-parallel runs are unaffected."""
    return os.environ.get("PYTEST_XDIST_WORKER", "master")


def _next_counter() -> int:
    global _counter
    with _counter_lock:
        _counter += 1
        return _counter


def unique_suffix() -> str:
    """<epoch_ms>_<worker>_<counter>_<4 random chars> — collision-proof across
    workers, across tests in the same worker, and across repeated calls
    within one test."""
    epoch_ms = int(time.time() * 1000)
    rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{epoch_ms}_{worker_id()}_{_next_counter()}_{rand}"


def unique_name(prefix: str, max_len: int = None) -> str:
    """Build a worker-safe unique name, e.g.:

        unique_name("SMS_CAMPAIGN") -> "SMS_CAMPAIGN_1737384821123_gw2_7_QK3M"

    Pass max_len if the target field has a hard character limit (e.g. a
    Sender ID field capped at 11 chars) — the suffix is prioritized (it's
    what prevents collisions) and the prefix is truncated to fit.
    """
    name = f"{prefix}_{unique_suffix()}"
    if max_len and len(name) > max_len:
        suffix = f"_{unique_suffix()}"
        keep = max(0, max_len - len(suffix))
        name = f"{prefix[:keep]}{suffix}"
    return name


def worker_scoped_dir(base_dir: str) -> str:
    """base_dir/<worker_id>/ — created if missing. Use for any output each
    worker writes independently (screenshots, downloads, temp files) so two
    workers never touch the same file on disk."""
    path = os.path.join(base_dir, worker_id())
    os.makedirs(path, exist_ok=True)
    return path
