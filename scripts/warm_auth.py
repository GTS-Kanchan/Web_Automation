"""
scripts/warm_auth.py — perform the ONE real login up front, single process,
before any pytest-xdist workers exist.

Why this exists
----------------
utils/auth_state.py already guarantees at most one real login across any
number of parallel workers (see docs/ARCHITECTURE.md's "Authentication
architecture" section) via a cross-process file lock. That guarantee holds
regardless of whether you run this script first. What this script adds is
operational, not correctness:

  * It removes the race window entirely for the run that follows — by the
    time `pytest -n N` starts, reports/.auth/state.json already exists, so
    every worker takes the fast, no-lock-contention path
    (`ensure_authenticated_state` returns immediately, see that function's
    first line: `if os.path.isfile(STATE_PATH): return STATE_PATH`).
  * It gives you one unambiguous checkpoint to confirm the login itself
    actually succeeded BEFORE you spend time on a full parallel run — if
    your account is mid-lockout, or credentials in .env are wrong, you find
    out here, in seconds, instead of watching N workers fail.
  * If you suspect a run went wrong (e.g. "every worker seemed to log in"),
    running this alone, watching for exactly one `[AUTH]` line pair, is
    the fastest way to isolate "is the lock broken" from "was the account
    already locked out before this run started."

Usage:
    python scripts/warm_auth.py            # log in once, print the result
    python scripts/warm_auth.py --fresh     # delete any existing state/lock
                                             #   /failure-marker first, then
                                             #   log in clean

Then run your parallel suite as normal -- nothing else changes:
    pytest tests/sms -n 10 --dist loadscope
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from playwright.sync_api import sync_playwright

from utils import auth_state
from utils.config import Config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Delete any existing state file, lock file, and failure marker "
        "first, so this performs a guaranteed-clean login instead of "
        "possibly reusing an already-cached session.",
    )
    args = parser.parse_args()

    print(f"[warm_auth] STATE_PATH = {auth_state.STATE_PATH}")
    print(f"[warm_auth] BASE_URL   = {Config.BASE_URL}")

    if args.fresh:
        for path in (
            auth_state.STATE_PATH,
            auth_state._LOCK_PATH,
            auth_state._FAILURE_MARKER_PATH,
        ):
            try:
                os.remove(path)
                print(f"[warm_auth] removed stale file: {path}")
            except OSError:
                pass

    if os.path.isfile(auth_state.STATE_PATH) and not args.fresh:
        print(
            "[warm_auth] state file already exists -- reusing it, no login "
            "performed. Pass --fresh to force a clean login instead."
        )
        return 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=Config.HEADLESS)
        try:
            path = auth_state.ensure_authenticated_state(browser)
        except auth_state.AuthenticationError as exc:
            print(f"[warm_auth] LOGIN FAILED: {exc}", file=sys.stderr)
            return 1
        finally:
            browser.close()

    print(f"[warm_auth] Login OK -- state saved to {path}")
    print(
        "[warm_auth] Every worker in the parallel run that follows will "
        "reuse this file and perform zero additional logins."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
