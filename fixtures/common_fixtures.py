"""
fixtures/common_fixtures.py — cross-channel pytest fixtures, registered as a
pytest plugin from the root conftest.py (`pytest_plugins = [...]`) so every
test in the suite can request them without a per-file import.

These are ADDITIVE: nothing here replaces the existing `module_logged_in_page`
/ `logged_in_page` / `module_page` fixtures in conftest.py, which every
existing test file already depends on and continues to work unchanged.
New/migrated channel test files are encouraged to build on these instead of
repeating patterns from scratch (see fixtures/sms_fixtures.py for an
example, and channels/fixture_factory.py for the page-object-fixture
helper).

Safe for parallel execution: every fixture here either returns a
worker-derived path/id (no cross-worker sharing) or plain immutable data —
nothing here is global mutable state.
"""
import os

import pytest

from utils.config import Config
from utils.logger import TestLogger
from utils.parallel import unique_suffix, worker_id, worker_scoped_dir

AUTH_DIR = os.path.join(os.path.dirname(__file__), "..", "reports", ".auth")


@pytest.fixture(scope="session")
def current_worker_id() -> str:
    return worker_id()


@pytest.fixture
def correlation_id() -> str:
    """A fresh unique ID per test — thread it through campaign/template/
    message creation and into log lines so a live-app record can be traced
    back to the exact test + worker that created it."""
    return unique_suffix()


@pytest.fixture
def test_logger(request, correlation_id) -> TestLogger:
    """Structured logger pre-tagged with this test's name and, if the test
    module lives under tests/<channel>/..., its channel."""
    module_path = str(request.node.fspath)
    channel = "-"
    for candidate in ("sms", "whatsapp", "rcs", "email"):
        if f"{os.sep}{candidate}{os.sep}" in module_path or f"/tests/{candidate}/" in module_path:
            channel = candidate
            break
    log = TestLogger(channel=channel, test_name=request.node.name, env=os.getenv("ENV", "qa"))
    log.info("Test started", correlation_id=correlation_id)
    yield log
    log.info("Test finished", correlation_id=correlation_id)


@pytest.fixture(scope="session")
def worker_storage_state_path() -> str:
    """reports/.auth/<worker_id>.json — the on-disk Playwright storage_state
    (cookies + localStorage) for this worker's session. Isolated per worker
    by construction (the path itself is worker-scoped), so parallel workers
    never share or race on the same auth file, but each worker only has to
    perform the actual UI login once per run instead of once per test
    module. Opt-in — see authenticated_storage_state below for the fixture
    that actually performs/reuses the login."""
    os.makedirs(AUTH_DIR, exist_ok=True)
    return os.path.join(AUTH_DIR, f"{worker_id()}.json")


@pytest.fixture(scope="session")
def authenticated_storage_state(browser, worker_storage_state_path):
    """Session-scoped (once per worker process): logs in via a throwaway
    context/page exactly once per worker and saves storage_state to disk;
    on a second call within the same worker (e.g. a second test module),
    reuses the cached file instead of logging in again. Returns the path,
    ready to pass as `storage_state=` to `browser.new_context(...)`.

    This is the mechanism for requirement #8 (reuse auth via storageState
    without letting parallel workers interfere with each other) — opt-in,
    not wired into the existing module_logged_in_page fixture, so it does
    not change behavior for any currently-passing test."""
    if os.path.exists(worker_storage_state_path):
        return worker_storage_state_path

    from pages.common.login_page import LoginPage

    context = browser.new_context()
    page = context.new_page()
    lp = LoginPage(page)
    lp.navigate()
    lp.login(Config.VALID_EMAIL, Config.VALID_PASSWORD)
    lp.h.wait_for_url_contains("/", timeout=15000)
    context.storage_state(path=worker_storage_state_path)
    context.close()
    return worker_storage_state_path


@pytest.fixture(scope="module")
def authenticated_module_page(browser, authenticated_storage_state):
    """Like conftest.py's `module_page` -> `module_logged_in_page`, but
    builds the context from the cached per-worker storage_state instead of
    performing a fresh UI login for every module. Opt-in for new/migrated
    channel test files; existing files keep using module_logged_in_page."""
    from conftest import _viewport_context_args
    context = browser.new_context(
        storage_state=authenticated_storage_state,
        **_viewport_context_args(),
        accept_downloads=True,
    )
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="module")
def module_download_dir() -> str:
    """Worker-scoped download directory — reports/downloads/<worker_id>/ —
    so two workers downloading a same-named export file can never collide."""
    return worker_scoped_dir(Config.DOWNLOAD_DIR)
