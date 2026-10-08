"""
scripts/validate_auth_lock.py — offline validation harness for
utils/auth_state.py's single-login-across-workers mechanism, WITHOUT
hitting the real application.

Environments without network access to the real app's BASE_URL have no way
to run a genuine end-to-end login. What CAN be verified without the
network is the part that actually implements "the platform receives only
one login operation per test run": the cross-process file lock in
utils/auth_state.py. This script spawns N real OS processes (simulating N
pytest-xdist workers), each calling
utils.auth_state.ensure_authenticated_state() concurrently, with
pages.common.login_page.LoginPage swapped for a fake that just records how
many times it was actually invoked (no network I/O) and simulates a
successful login. If the locking logic is correct, the fake login must be
invoked exactly once no matter how many "workers" call in at once.

Usage:
    python scripts/validate_auth_lock.py 20   # simulate 20 concurrent workers

Not a substitute for a real staging-environment run against the live app —
see docs/ARCHITECTURE.md's Validation section for what this does and does
not prove, and for the separate end-to-end validation performed against a
local mock login page (real Playwright + real pytest-xdist, no network).
"""
import multiprocessing
import os
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class FakeHelpers:
    def __init__(self, page):
        self.page = page

    def wait_for_url_contains(self, text, timeout=None):
        # Simulates the redirect-away-from-/login that a real login does.
        self.page.url = self.page.url  # already set by FakeLoginPage.login()


class FakePage:
    def __init__(self):
        self.url = "https://fake.test/login"

    def goto(self, url):
        self.url = url


class FakeContext:
    def __init__(self):
        self._page = FakePage()

    def new_page(self):
        return self._page

    def storage_state(self, path):
        with open(path, "w") as f:
            f.write('{"cookies": [], "origins": []}')

    def close(self):
        pass


class FakeBrowser:
    def new_context(self):
        return FakeContext()


def _make_fake_login_page_cls(call_counter_path, call_lock_path):
    class FakeLoginPage:
        def __init__(self, page):
            self.page = page
            self.h = FakeHelpers(page)

        def navigate(self):
            self.page.url = "https://fake.test/login"

        def login(self, email, password):
            # Record that a real "login" happened -- this is the thing the
            # test asserts stays at exactly 1 no matter how many workers
            # call ensure_authenticated_state() concurrently.
            fd = os.open(call_lock_path + ".counting", os.O_CREAT | os.O_WRONLY)
            os.close(fd)
            with open(call_counter_path, "a") as f:
                f.write(f"login-call pid={os.getpid()} t={time.time()}\n")
            # Simulate a slow real login (network round-trip) so concurrent
            # callers genuinely overlap and exercise the lock-wait path,
            # not just the already-exists fast path.
            time.sleep(1.5)
            self.page.url = "https://fake.test/dashboard"

        def is_login_page(self):
            return "login" in self.page.url

        def get_error_message(self):
            return None

    return FakeLoginPage


def _worker(state_path, call_counter_path, call_lock_path, result_path):
    os.environ["AUTH_STATE_PATH"] = state_path
    os.environ["VALID_EMAIL"] = "fake@example.com"
    os.environ["VALID_PASSWORD"] = "fake-password"

    import utils.auth_state as auth_state
    import pages.common.login_page as login_page_mod

    login_page_mod.LoginPage = _make_fake_login_page_cls(call_counter_path, call_lock_path)

    # Reload so the module picks up AUTH_STATE_PATH set just above (module-
    # level STATE_PATH is computed at import time).
    import importlib
    importlib.reload(auth_state)
    login_page_mod.LoginPage = _make_fake_login_page_cls(call_counter_path, call_lock_path)

    try:
        path = auth_state.ensure_authenticated_state(FakeBrowser())
        ok = os.path.isfile(path)
        with open(result_path, "a") as f:
            f.write(f"pid={os.getpid()} worker=OK path={path} exists={ok}\n")
    except Exception as exc:
        with open(result_path, "a") as f:
            f.write(f"pid={os.getpid()} worker=FAIL error={exc!r}\n")


def main(num_workers=8):
    tmp_dir = tempfile.mkdtemp(prefix="auth_dry_run_")
    state_path = os.path.join(tmp_dir, "state.json")
    call_counter_path = os.path.join(tmp_dir, "login_calls.log")
    call_lock_path = os.path.join(tmp_dir, "lock_marker")
    result_path = os.path.join(tmp_dir, "results.log")

    print(f"[dry-run] tmp_dir={tmp_dir}")
    print(f"[dry-run] spawning {num_workers} concurrent 'worker' processes calling "
          f"ensure_authenticated_state() at (almost) the same instant...")

    ctx = multiprocessing.get_context("fork")
    procs = [
        ctx.Process(target=_worker, args=(state_path, call_counter_path, call_lock_path, result_path))
        for _ in range(num_workers)
    ]
    start = time.time()
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=60)
    elapsed = time.time() - start

    login_calls = 0
    if os.path.isfile(call_counter_path):
        with open(call_counter_path) as f:
            login_calls = sum(1 for _ in f)

    results = ""
    if os.path.isfile(result_path):
        with open(result_path) as f:
            results = f.read()

    print(f"[dry-run] elapsed={elapsed:.1f}s")
    print(f"[dry-run] real 'login' calls recorded: {login_calls} (must be exactly 1)")
    print(f"[dry-run] state file exists: {os.path.isfile(state_path)}")
    print("[dry-run] per-process results:")
    print(results)

    ok = (login_calls == 1) and os.path.isfile(state_path) and all(
        "FAIL" not in line for line in results.splitlines()
    )
    print(f"[dry-run] RESULT: {'PASS' if ok else 'FAIL'}")

    shutil.rmtree(tmp_dir, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    raise SystemExit(main(n))
