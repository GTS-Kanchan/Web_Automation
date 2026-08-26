"""
utils/auth_state.py — single-login-per-run authentication state.

The problem this solves
------------------------
fixtures/common_fixtures.py originally had an `authenticated_storage_state`
fixture that logged in ONCE PER WORKER PROCESS — session-scoped, so under
`pytest -n 10` that was still 10 real UI logins (one per gw0..gw9), just
fewer than the old "one login per test module" behavior. That's not good
enough for this platform: repeated login attempts in a short window trigger
a ~5 minute account lockout, so the whole test run — any number of
pytest-xdist workers — must perform exactly ONE real UI login, and every
worker/test after that must reuse the same saved session.

How it works
-------------
A single shared Playwright `storage_state` JSON file (STATE_PATH, default
reports/.auth/state.json, overridable via the AUTH_STATE_PATH env var) is
guarded by a cross-process file lock:

  * The first caller (in any worker, in any test) to reach
    `ensure_authenticated_state()` acquires the lock, finds no state file,
    performs the one real UI login, saves `storage_state`, and releases the
    lock.
  * Every other caller — same worker or a different one, before or after
    that — either sees the state file already present (fast path, no lock
    needed) or briefly blocks on the lock and then sees it once the first
    caller finishes. Nobody else ever calls the login page.

This directly implements the "single account, single login, storageState,
parallel workers" architecture: authentication is a one-time setup step,
not something each worker/test repeats.

No new dependency: the lock is a plain atomic-create lockfile
(`os.O_CREAT | os.O_EXCL`), which is atomic on both POSIX and Windows —
no `filelock`/`portalocker` package needed for this project's scale.

Explicitly NOT solved with delays
-----------------------------------
There is no `time.sleep(300)` / `wait_for_timeout(300000)` anywhere in this
module. A waiting worker polls a short interval (`_LOCK_POLL_SECONDS`) with
a real timeout (`_LOCK_WAIT_TIMEOUT`) — it waits only as long as the one
real login actually takes, not an arbitrary five minutes, and it never
performs a login of its own while waiting.
"""
import os
import sys
import time

from utils.config import Config
from utils.parallel import worker_id

_DEFAULT_STATE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "reports", ".auth", "state.json"
)
# Overridable per requirement #14 (AUTH_STATE_PATH env var); defaults to the
# existing reports/ convention already used for screenshots/logs/downloads.
STATE_PATH = os.path.abspath(os.getenv("AUTH_STATE_PATH", _DEFAULT_STATE_PATH))
_LOCK_PATH = STATE_PATH + ".lock"
# Written (atomically, lock-held) if the one real login attempt itself
# fails -- see ensure_authenticated_state / reauthenticate_if_still_stale.
# Without this, a FAILED login leaves no state file behind, so every
# subsequent worker would see "no state file yet" and independently retry
# the login itself -- a login storm on the failure path, which is exactly
# what requirement #11 (authentication failure handling) prohibits.
_FAILURE_MARKER_PATH = STATE_PATH + ".failed"
# A failure marker older than this is treated as belonging to a previous,
# separate `pytest` invocation (e.g. a human fixed the credentials and
# re-ran later) rather than this run -- so it does not block forever.
# Comfortably longer than any single suite run, comfortably shorter than
# "the next time someone reruns the suite" in practice.
_FAILURE_MARKER_TTL_SECONDS = 1800

# A lock file older than this is assumed to belong to a worker that crashed
# mid-login (e.g. killed process) rather than one still legitimately
# working — it is force-cleared so the run can't deadlock forever on a
# lock nobody will ever release.
_LOCK_STALE_SECONDS = 180
# How long a worker will wait for whichever worker is currently holding the
# lock (i.e. currently performing the one real login) before giving up.
# Comfortably longer than a real login should ever take, comfortably
# shorter than _LOCK_STALE_SECONDS so a slow-but-legitimate login is not
# preempted by another worker deciding the lock is stale.
_LOCK_WAIT_TIMEOUT = 150
_LOCK_POLL_SECONDS = 0.5


class AuthenticationError(RuntimeError):
    """Raised when the one-time login itself fails, or when no other
    worker ever releases the lock. Let this propagate out of the fixture
    that calls ensure_authenticated_state() — pytest will report every
    dependent test as a fixture-setup ERROR with this message, which is
    the desired "stop/skip dependent tests, don't let each one retry login
    independently" behavior (requirement #11)."""


def _auth_log(message: str) -> None:
    """[AUTH][<worker>] ... on stderr — visible under `pytest -s` / CI logs,
    same channel utils/logger.py's TestLogger uses. Never pass a credential,
    token, cookie, or storage_state content into this function."""
    print(f"[AUTH][{worker_id()}] {message}", file=sys.stderr, flush=True)


def _acquire_lock() -> int:
    """Blocking, cross-process, cross-platform mutual exclusion using
    exclusive file creation (atomic on POSIX and Windows — no fcntl/msvcrt
    needed). Returns the open fd; caller must release via _release_lock."""
    os.makedirs(os.path.dirname(_LOCK_PATH), exist_ok=True)
    waited = 0.0
    while True:
        try:
            fd = os.open(_LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            return fd
        except FileExistsError:
            try:
                age = time.time() - os.path.getmtime(_LOCK_PATH)
            except OSError:
                age = 0.0  # lock disappeared between the open() and stat() -- retry
            if age > _LOCK_STALE_SECONDS:
                _auth_log(
                    f"Clearing stale authentication lock ({age:.0f}s old) — "
                    "assuming an earlier worker crashed mid-login"
                )
                try:
                    os.remove(_LOCK_PATH)
                except OSError:
                    pass
                continue
            if waited >= _LOCK_WAIT_TIMEOUT:
                raise AuthenticationError(
                    f"Timed out after {_LOCK_WAIT_TIMEOUT}s waiting for another "
                    f"worker to finish the one-time login (lock file: {_LOCK_PATH}). "
                    "Not retrying login independently — see utils/auth_state.py."
                )
            time.sleep(_LOCK_POLL_SECONDS)
            waited += _LOCK_POLL_SECONDS


def _release_lock(fd: int) -> None:
    try:
        os.close(fd)
    finally:
        try:
            os.remove(_LOCK_PATH)
        except OSError:
            pass


def _raise_if_recently_failed() -> None:
    """If the one real login attempt already failed recently in this run,
    raise immediately with the SAME error instead of letting the caller
    attempt its own login. Call this before acquiring the lock (fast path)
    AND again after acquiring it (in case the failure happened while this
    caller was waiting)."""
    try:
        age = time.time() - os.path.getmtime(_FAILURE_MARKER_PATH)
    except OSError:
        return
    if age > _FAILURE_MARKER_TTL_SECONDS:
        return  # stale marker from an earlier, separate run -- ignore it
    try:
        with open(_FAILURE_MARKER_PATH, "r", encoding="utf-8") as f:
            message = f.read().strip()
    except OSError:
        message = "(failure marker present but unreadable)"
    raise AuthenticationError(
        "Authentication already failed earlier in this run -- not attempting "
        f"another login (that would be exactly the login storm this suite "
        f"must avoid). Original error: {message}"
    )


def _record_failure(message: str) -> None:
    try:
        os.makedirs(os.path.dirname(_FAILURE_MARKER_PATH), exist_ok=True)
        tmp_path = f"{_FAILURE_MARKER_PATH}.tmp.{os.getpid()}"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(message)
        os.replace(tmp_path, _FAILURE_MARKER_PATH)
    except OSError:
        pass


def _clear_failure_marker() -> None:
    try:
        os.remove(_FAILURE_MARKER_PATH)
    except OSError:
        pass


def _perform_login_recording_failure(browser) -> None:
    """Wraps _perform_login: on success, clears any stale failure marker
    from a previous attempt; on failure, records the error (lock-held, so
    this write itself can't race) and re-raises. Every call site that
    performs the real login goes through this, not _perform_login
    directly, so a failure is recorded exactly once no matter which
    function (initial login or session-expiry re-auth) triggered it."""
    try:
        _perform_login(browser)
    except Exception as exc:
        _record_failure(str(exc))
        raise
    else:
        _clear_failure_marker()


def _perform_login(browser) -> None:
    """The ONE real UI login for the whole run. Only ever called by the
    single worker holding the lock, immediately after confirming the state
    file does not already exist. `browser` is pytest-playwright's
    session-scoped fixture (one real browser process per worker) — this
    uses a throwaway context/page that is closed again immediately after,
    never the shared per-test page."""
    from pages.common.login_page import LoginPage  # local import: keeps this
    # module import-cycle-free at load time (conftest.py imports this module
    # AND pages.common.login_page).

    _auth_log("Starting authentication")
    if not Config.VALID_EMAIL or not Config.VALID_PASSWORD:
        raise AuthenticationError(
            "VALID_EMAIL/VALID_PASSWORD are not set (check .env) — cannot "
            "perform the one-time login."
        )

    context = browser.new_context()
    page = context.new_page()
    try:
        lp = LoginPage(page)
        lp.navigate()
        lp.login(Config.VALID_EMAIL, Config.VALID_PASSWORD)
        lp.h.wait_for_url_contains("/", timeout=20000)
        if lp.is_login_page():
            error = lp.get_error_message()
            raise AuthenticationError(
                "The one-time login did not redirect away from /login"
                + (f" — platform said: {error}" if error else " (no error message found)")
            )
        _auth_log("Login successful")

        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        # Write to a temp file in the same directory then atomically rename
        # into place (os.replace is atomic on both POSIX and Windows) so a
        # concurrent reader can never observe a partially-written state file.
        tmp_path = f"{STATE_PATH}.tmp.{os.getpid()}"
        context.storage_state(path=tmp_path)
        os.replace(tmp_path, STATE_PATH)
        _auth_log(f"Authentication state saved -> {STATE_PATH}")
    finally:
        context.close()


def ensure_authenticated_state(browser) -> str:
    """Return STATE_PATH, guaranteeing that exactly one real UI login has
    happened for this run (any number of pytest-xdist workers, or a plain
    single-process run) before returning. Safe to call from every worker
    and every test/module that needs authenticated state: only the very
    first caller across the whole run does real work; everyone else takes
    the fast path (file already exists, no lock needed) or a short
    lock-wait (another worker is mid-login right now)."""
    if os.path.isfile(STATE_PATH):
        return STATE_PATH
    _raise_if_recently_failed()

    fd = _acquire_lock()
    try:
        if os.path.isfile(STATE_PATH):
            # Another worker won the race and finished while we were
            # waiting for the lock -- nothing left for us to do.
            return STATE_PATH
        # Re-check for a failure recorded WHILE we were waiting for the
        # lock (another worker's login attempt failed in the meantime) --
        # without this second check, we would try our own login right
        # after acquiring the lock instead of surfacing that failure.
        _raise_if_recently_failed()
        _perform_login_recording_failure(browser)
    finally:
        _release_lock(fd)
    return STATE_PATH


def state_mtime():
    """mtime of the current state file, or None if it doesn't exist. Callers
    doing session-expiry detection should snapshot this BEFORE deciding the
    session is stale, and pass it to reauthenticate_if_still_stale() -- see
    that function for why (a plain "just delete it" approach has a real
    race: see the comment there)."""
    try:
        return os.path.getmtime(STATE_PATH)
    except OSError:
        return None


def reauthenticate_if_still_stale(browser, observed_mtime) -> str:
    """Controlled re-authentication entry point (requirement #12: session
    expiration). `observed_mtime` is the value state_mtime() returned at
    the moment the CALLER detected the cached session no longer works
    (bounced back to /login).

    Why this isn't just "delete the file, then ensure_authenticated_state()
    again": if two workers detect the same stale session at nearly the same
    time, worker A can finish its whole re-login (delete -> lock -> login ->
    write the FRESH file -> unlock) before worker B gets around to acting on
    what IT observed. An unconditional delete from B at that point would
    destroy the fresh file A just produced and force a second, unnecessary
    real login -- exactly the "login storm" this whole module exists to
    prevent. Guarding the delete with the lock AND a same-or-older mtime
    check closes that race: B only deletes+relogs-in if the file on disk is
    still the exact stale one it originally observed; if someone else
    already refreshed it (newer mtime), B just reuses that instead."""
    fd = _acquire_lock()
    try:
        current = state_mtime()
        if current is not None and observed_mtime is not None and current > observed_mtime:
            # Someone else already refreshed it since we detected staleness.
            _auth_log("Authentication state was already refreshed by another worker -- reusing it")
            return STATE_PATH
        _raise_if_recently_failed()
        _auth_log("Session appears expired -- re-authenticating (single-flight, lock-held)")
        # Deliberately NOT deleting STATE_PATH first: _perform_login()
        # overwrites it via os.replace(tmp, STATE_PATH), which is atomic --
        # a concurrent browser.new_context(storage_state=STATE_PATH) call
        # elsewhere (a worker that fetched this same path moments ago and
        # hasn't opened its context yet) always sees either the old stale
        # content or the new fresh content, never a missing file. An
        # explicit delete-then-relogin here would open exactly that
        # missing-file window and intermittently crash such a caller with
        # FileNotFoundError -- this was caught by this project's own
        # parallel dry-run validation (see the final report).
        _perform_login_recording_failure(browser)
    finally:
        _release_lock(fd)
    return STATE_PATH


def invalidate_authenticated_state(reason: str = "") -> None:
    """Unconditionally deletes the shared state file so the *next*
    ensure_authenticated_state() call performs a fresh login. This is a
    blunt manual/maintenance tool (e.g. "force a clean login on the next
    run") -- it does NOT hold the lock and is NOT race-safe against a
    concurrently-running suite, so automatic session-expiry handling uses
    reauthenticate_if_still_stale() above instead, not this function."""
    _auth_log(f"Invalidating authentication state{f' ({reason})' if reason else ''}")
    try:
        os.remove(STATE_PATH)
    except OSError:
        pass
