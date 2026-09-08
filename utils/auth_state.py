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

UPDATED (2026-09-08): hardened for HIGHER worker counts, not lower
---------------------------------------------------------------------
A real run on rcs-simulator at PLAYWRIGHT_WORKERS=16 showed ~70% of the
suite pass, then ~165 tests ERROR in one cascade, all traced back to ONE
event: `AuthenticationError: The one-time login did not redirect away from
/login (no error message found)`. That is the architecture doing exactly
what it was designed to do (stop every dependent test rather than let each
one retry login independently and risk an account lockout) — but the
underlying login attempt itself had ZERO tolerance for a single slow or
flaky moment, and the user's stated direction is to run with MORE workers
in the future, not fewer. Three changes below make the one real login
resilient to the kind of transient slowness that gets more likely, not
less, as worker count goes up (more Chromium processes launching at once,
more CPU/network contention on the server the one login attempt is racing
against):

  1. Bounded, in-process RETRIES for ambiguous/transient login failures
     (no redirect AND no platform-reported error message, or a raw
     Playwright/network exception — i.e. "looks like infra flakiness", not
     "the platform rejected these credentials"). A REAL platform-reported
     rejection (get_error_message() found actual text) is never retried —
     retrying that would just be more login attempts against a real
     rejection, which is the one thing this module must never do. All
     retries happen serially, inside the single lock holder — never a
     second worker attempting its own concurrent login (that would be the
     login storm this module exists to prevent).
  2. A LOCK HEARTBEAT: while the lock holder is doing the (possibly
     retried) login, a background thread keeps the lock file's mtime
     fresh. Without this, a login that legitimately takes longer than the
     stale-lock threshold under heavy load would let ANOTHER worker
     conclude the holder crashed, force-clear the lock, and start its own
     login — two real logins in flight at once. The heartbeat makes
     "stale" mean "the holder's process is actually gone", never "the
     holder is still working, just slowly".
  3. Every timeout in this module is now env-var configurable
     (AUTH_LOGIN_TIMEOUT_MS, AUTH_LOGIN_MAX_ATTEMPTS,
     AUTH_LOGIN_RETRY_BACKOFF_SECONDS, AUTH_LOCK_WAIT_TIMEOUT_SECONDS,
     AUTH_LOCK_STALE_SECONDS, AUTH_LOCK_HEARTBEAT_SECONDS), with defaults
     raised to comfortably cover a full multi-attempt login under load,
     so scaling PLAYWRIGHT_WORKERS up doesn't require also editing this
     file — see the constants below for the worst-case math.
"""
import os
import sys
import threading
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

# ── Login attempt tuning (env-var configurable — see module docstring) ─────
# How long a single login attempt waits for the app to redirect away from
# /login before deciding it's stuck. Raised from a flat 20000ms: under
# heavy parallel load (many Chromium processes launching/running at once)
# the one real login can simply be slower to get a response, and a false
# "failed" here poisons the whole run for _FAILURE_MARKER_TTL_SECONDS.
_LOGIN_TIMEOUT_MS = int(os.getenv("AUTH_LOGIN_TIMEOUT_MS", "45000"))
# How many times the ONE lock holder will retry an ambiguous/transient
# login failure (see _RetryableLoginError below) before giving up and
# recording a real failure. A real platform-reported rejection (bad
# credentials, account locked, etc.) is never retried regardless of this
# value -- only "looks like infra flakiness" failures are.
_LOGIN_MAX_ATTEMPTS = int(os.getenv("AUTH_LOGIN_MAX_ATTEMPTS", "3"))
# Backoff before each retry, multiplied by the attempt number that just
# failed (attempt 1 fails -> wait 1x this, attempt 2 fails -> wait 2x this,
# ...) -- gives a transient load spike a little time to pass rather than
# retrying back-to-back into the same contention.
_LOGIN_RETRY_BACKOFF_SECONDS = float(os.getenv("AUTH_LOGIN_RETRY_BACKOFF_SECONDS", "5"))

# A lock file older than this is assumed to belong to a worker that crashed
# mid-login (e.g. killed process) rather than one still legitimately
# working — it is force-cleared so the run can't deadlock forever on a
# lock nobody will ever release. The lock HEARTBEAT (below) keeps a
# legitimately slow/retrying login's lock file fresh, so in normal
# operation this threshold is only ever hit by a genuinely dead holder.
_LOCK_STALE_SECONDS = int(os.getenv("AUTH_LOCK_STALE_SECONDS", "300"))
# How long a worker will wait for whichever worker is currently holding the
# lock (i.e. currently performing the one real login, including any
# retries) before giving up. Worst case with the defaults above is roughly
# _LOGIN_MAX_ATTEMPTS attempts at up to _LOGIN_TIMEOUT_MS each, plus
# backoff between them (~3 * 50s + 5s + 10s =~ 165s) — this default is set
# comfortably above that, and comfortably below _LOCK_STALE_SECONDS so a
# slow-but-legitimate login is not preempted by another worker deciding
# the lock is stale.
_LOCK_WAIT_TIMEOUT = int(os.getenv("AUTH_LOCK_WAIT_TIMEOUT_SECONDS", "240"))
_LOCK_POLL_SECONDS = 0.5
# How often the lock heartbeat thread refreshes the lock file's mtime while
# the one real login (including retries) is in progress. Comfortably
# smaller than _LOCK_STALE_SECONDS so the file never goes stale while the
# holder is genuinely still working.
_LOCK_HEARTBEAT_SECONDS = int(os.getenv("AUTH_LOCK_HEARTBEAT_SECONDS", "20"))


class AuthenticationError(RuntimeError):
    """Raised when the one-time login itself fails (after every retry is
    exhausted), or when no other worker ever releases the lock. Let this
    propagate out of the fixture that calls ensure_authenticated_state() —
    pytest will report every dependent test as a fixture-setup ERROR with
    this message, which is the desired "stop/skip dependent tests, don't
    let each one retry login independently" behavior (requirement #11)."""


class _RetryableLoginError(RuntimeError):
    """Internal signal only — never raised out of this module. Means "this
    particular login attempt failed in a way that looks like transient
    infra/load flakiness" (no redirect AND no platform-reported error
    message, or a raw Playwright/network exception) rather than "the
    platform rejected these credentials". _perform_login() retries this
    (still inside the single lock holder, still exactly one real login
    flow in flight at a time) up to _LOGIN_MAX_ATTEMPTS times before
    finally raising a real AuthenticationError."""


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
                    "Not retrying login independently — see utils/auth_state.py. "
                    "If this keeps happening at a higher PLAYWRIGHT_WORKERS count, "
                    "raise AUTH_LOCK_WAIT_TIMEOUT_SECONDS rather than lowering "
                    "worker count."
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


class _LockHeartbeat:
    """Context manager that keeps _LOCK_PATH's mtime fresh in the
    background for as long as it's open — used only by the lock holder,
    only while it's doing the (possibly multi-attempt) real login. See the
    module docstring's point 2 for why this matters more as worker count
    goes up: without it, a legitimately slow login under heavy load can
    get its lock force-cleared by another worker mid-attempt, producing
    two real logins in flight at once. A daemon thread is used so a
    crashed holder process can never leave a heartbeat running against a
    lock file that should now be eligible for staleness-based recovery."""

    def __init__(self):
        self._stop = threading.Event()
        self._thread = None

    def __enter__(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def _run(self):
        while not self._stop.wait(_LOCK_HEARTBEAT_SECONDS):
            try:
                os.utime(_LOCK_PATH, None)
            except OSError:
                return  # lock file already gone -- nothing left to keep alive

    def __exit__(self, exc_type, exc, tb):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
        return False


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
    from a previous attempt; on failure (after every retry _perform_login
    itself already attempted internally), records the error (lock-held, so
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


def _save_auth_failure_screenshot(page, label: str) -> str:
    """Best-effort screenshot of the login page at the exact moment an
    authentication attempt fails, saved next to the shared auth state
    (reports/.auth/<label>_<timestamp>.png) so a future failure doesn't
    require digging through an unrelated test's own failure screenshot to
    see what the login page actually looked like (that's how the very
    first occurrence of this had to be diagnosed -- see the run where
    test_TC010_messages_sent_count_displayed's re-auth failed with "no
    error message found": the only visual evidence available was a
    coincidental screenshot from test_TC009, a different, earlier test,
    because setup-phase fixture errors aren't covered by conftest.py's
    own call-phase-only screenshot-on-failure hook).

    Returns a " -- screenshot saved to <path>" suffix for the exception
    message, or "" if the screenshot itself couldn't be taken -- never
    lets a screenshot failure mask the real authentication error."""
    try:
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        path = os.path.join(
            os.path.dirname(STATE_PATH),
            f"{label}_{time.strftime('%Y%m%d_%H%M%S')}.png",
        )
        page.screenshot(path=path)
        return f" -- screenshot saved to {path}"
    except Exception:
        return ""


def _perform_login_attempt(browser, attempt: int) -> None:
    """ONE real UI login attempt. `browser` is pytest-playwright's
    session-scoped fixture (one real browser process per worker) — this
    uses a throwaway context/page that is closed again immediately after,
    never the shared per-test page.

    Raises AuthenticationError directly (never retried by _perform_login)
    when the platform itself reported a rejection — retrying a real
    rejection would just be more login attempts against it, which is what
    this whole module exists to avoid. Raises _RetryableLoginError (caught
    and possibly retried by _perform_login) for everything that looks like
    transient infra/load flakiness instead: no redirect AND no platform
    error message, or a raw exception (Playwright timeout, network
    error, ...)."""
    from pages.common.login_page import LoginPage  # local import: keeps this
    # module import-cycle-free at load time (conftest.py imports this module
    # AND pages.common.login_page).

    context = browser.new_context()
    page = context.new_page()
    try:
        lp = LoginPage(page)
        lp.navigate()
        lp.login(Config.VALID_EMAIL, Config.VALID_PASSWORD)
        lp.h.wait_for_url_contains("/", timeout=_LOGIN_TIMEOUT_MS)
        if lp.is_login_page():
            error = lp.get_error_message()
            if error:
                # A real, platform-reported rejection (bad credentials,
                # locked account, ...) -- non-retryable.
                shot = _save_auth_failure_screenshot(page, "login_failed")
                raise AuthenticationError(
                    f"The one-time login did not redirect away from /login "
                    f"— platform said: {error}" + shot
                )
            # No redirect AND no error message -- ambiguous. Under load
            # this has been observed to be a slow/stuck page rather than a
            # real rejection; retryable.
            shot = _save_auth_failure_screenshot(page, "login_failed")
            raise _RetryableLoginError(
                f"attempt {attempt}: The one-time login did not redirect "
                f"away from /login within {_LOGIN_TIMEOUT_MS}ms (no error "
                "message found)" + shot
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
    except (AuthenticationError, _RetryableLoginError):
        raise
    except Exception as exc:
        # Anything else (a raw Playwright timeout from navigate()/login()/
        # wait_for_url_contains(), a network error, ...) is treated as
        # transient/retryable too -- the same reasoning as the ambiguous
        # "no redirect, no error message" case above: this is infra/load
        # flakiness, not a platform-reported rejection.
        shot = _save_auth_failure_screenshot(page, "login_error")
        raise _RetryableLoginError(
            f"attempt {attempt}: The one-time login raised "
            f"{exc.__class__.__name__}: {exc}" + shot
        ) from exc
    finally:
        context.close()


def _perform_login(browser) -> None:
    """The ONE real UI login for the whole run — now with bounded,
    in-process retries for transient/ambiguous failures (see module
    docstring). Every attempt still happens serially, inside the single
    worker holding the lock (via _LockHeartbeat, so a slow retry sequence
    can't get its lock preempted) — never more than one real login flow in
    flight across the whole run, whether that flow takes one attempt or
    _LOGIN_MAX_ATTEMPTS."""
    _auth_log("Starting authentication")
    if not Config.VALID_EMAIL or not Config.VALID_PASSWORD:
        raise AuthenticationError(
            "VALID_EMAIL/VALID_PASSWORD are not set (check .env) — cannot "
            "perform the one-time login."
        )

    for attempt in range(1, _LOGIN_MAX_ATTEMPTS + 1):
        try:
            _perform_login_attempt(browser, attempt)
            return
        except _RetryableLoginError as exc:
            if attempt >= _LOGIN_MAX_ATTEMPTS:
                raise AuthenticationError(
                    f"The one-time login failed after {_LOGIN_MAX_ATTEMPTS} "
                    f"attempts (last error: {exc}). Not retrying further — "
                    "if this keeps happening at a higher PLAYWRIGHT_WORKERS "
                    "count, raise AUTH_LOGIN_TIMEOUT_MS / "
                    "AUTH_LOGIN_MAX_ATTEMPTS rather than lowering worker "
                    "count; if it happens at any worker count, treat it as "
                    "a real credentials/environment problem."
                ) from exc
            backoff = _LOGIN_RETRY_BACKOFF_SECONDS * attempt
            _auth_log(
                f"Login attempt {attempt}/{_LOGIN_MAX_ATTEMPTS} looked like "
                f"transient flakiness ({exc}) — retrying in {backoff:.0f}s "
                "(still the single lock holder; no other worker attempts "
                "its own login)"
            )
            time.sleep(backoff)
    # Unreachable (the loop always returns or raises), kept for clarity.
    raise AuthenticationError("The one-time login failed for an unknown reason.")


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
        with _LockHeartbeat():
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
        with _LockHeartbeat():
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
