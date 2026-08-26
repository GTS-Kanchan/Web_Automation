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


def short_unique_tag(width: int = 6) -> str:
    """A compact, worker-safe alternative to the pre-existing
    `str(int(time.time()))[-N:]` pattern found at a handful of call sites
    (test_segmentation_flow.py, test_tags_flow.py, test_contacts_flow.py,
    the RCS template/campaign creation flows) that predate parallel
    execution being a concern. Those call sites use a bare second-
    resolution timestamp tail as their only uniqueness mechanism -- two
    workers (or two separate pytest invocations against the same shared
    account, since this whole suite runs on ONE account) creating a record
    in the same wall-clock second produce the exact same name.

    Prefer unique_name()/unique_suffix() when the target field has enough
    room (they're more strongly collision-proof, per-call not just
    per-second). This exists for fields with a tight, previously
    hand-tuned character budget, where swapping in the full
    unique_suffix() (20+ chars) would meaningfully change or exceed the
    field's length limit.

    NOTE: `width` sizes only the millisecond-timestamp portion -- the
    worker tag (1-2 chars) and random suffix (2 chars) add up to 4 more
    chars on top, so the total length is `width + up to 4`, not `width`.
    Pick `width` with that headroom in mind when a field has a hard cap."""
    ms_tail = str(int(time.time() * 1000))[-width:]
    w = worker_id()
    wtag = "m" if w == "master" else w[-2:]
    rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=2))
    return f"{ms_tail}{wtag}{rand}"


def short_unique_digits(width: int = 5) -> str:
    """Digits-only counterpart to short_unique_tag() -- for a handful of
    call sites that build a scratch value from a bare timestamp tail and
    then also use it somewhere that must look like a phone number/numeric
    ID (e.g. test_contacts_flow.py's scratch-contact phone field), where
    short_unique_tag()'s letters would be invalid input. Combines a
    millisecond timestamp tail with a numeric worker index and a short
    random digit suffix, so it's still effectively worker-safe. Same
    `width` caveat as short_unique_tag(): total length is `width + 4`
    (a 2-digit worker index + 2 random digits) -- the width=5 default
    yields 9 digits total, matching the original bare-timestamp call
    sites' length exactly."""
    ms_tail = str(int(time.time() * 1000))[-width:]
    w = worker_id()
    try:
        worker_num = int(w[2:]) if w.startswith("gw") else 0
    except ValueError:
        worker_num = 0
    rand = "".join(random.choices(string.digits, k=2))
    return f"{ms_tail}{worker_num % 100:02d}{rand}"


def worker_scoped_dir(base_dir: str) -> str:
    """base_dir/<worker_id>/ — created if missing. Use for any output each
    worker writes independently (screenshots, downloads, temp files) so two
    workers never touch the same file on disk."""
    path = os.path.join(base_dir, worker_id())
    os.makedirs(path, exist_ok=True)
    return path
