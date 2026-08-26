"""
fixtures/common_fixtures.py — cross-channel pytest fixtures, registered as a
pytest plugin from the root conftest.py (`pytest_plugins = [...]`) so every
test in the suite can request them without a per-file import.

`authenticated_storage_state` is the single source of truth for the
suite's one-login-per-run authentication (see utils/auth_state.py) —
conftest.py's `logged_in_page` / `module_logged_in_page` fixtures, which
every existing test file already depends on, are built on top of it, so
existing test files keep working with zero changes even though the
underlying login mechanism changed (a fresh UI login per fixture call ->
one shared login for the whole run). New/migrated channel test files can
also use `authenticated_module_page` directly instead of repeating the
module_logged_in_page pattern from scratch (see fixtures/sms_fixtures.py
for an example, and channels/fixture_factory.py for the page-object-fixture
helper).

Safe for parallel execution: every fixture here either returns a
worker-derived path/id, plain immutable data, or the shared authenticated
storage_state path (itself made cross-process-safe by
utils/auth_state.py's file lock) — nothing here is global mutable state.
"""
import os

import pytest

from utils.auth_state import ensure_authenticated_state
from utils.config import Config
from utils.logger import TestLogger
from utils.parallel import unique_suffix, worker_id, worker_scoped_dir


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
def authenticated_storage_state(browser) -> str:
    """The shared, single-login-per-run Playwright storage_state path (see
    utils/auth_state.py). Session-scoped so each worker process calls this
    at most once per fixture cache, but the ONE real login is enforced
    across the whole run -- not per worker -- by ensure_authenticated_state's
    cross-process file lock: whichever worker/test gets here first performs
    the real UI login and every other caller (this worker's later tests, or
    any other worker) reuses the same file. Returns the path, ready to pass
    as `storage_state=` to `browser.new_context(...)`.

    This is the fixture conftest.py's `logged_in_page` / `module_logged_in_page`
    build on -- see conftest.py for how the majority of the suite consumes
    it. Also usable directly by new/migrated test files via
    `authenticated_module_page` below."""
    return ensure_authenticated_state(browser)


@pytest.fixture(scope="module")
def authenticated_module_page(browser, authenticated_storage_state):
    """Like conftest.py's `module_page` -> `module_logged_in_page`, but
    builds the context directly from the shared, single-login storage_state
    instead of going through conftest.py's fixtures. Equivalent alternative
    for new/migrated channel test files; existing files keep using
    module_logged_in_page (which now reuses the exact same storage_state
    under the hood)."""
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
    """utils.config.DOWNLOAD_DIR — reports/downloads/<worker_id>/ — so two
    workers downloading a same-named export file can never collide. The
    directory itself is already worker-scoped at the source (see
    utils/config.py), so this fixture is now just a documented, explicit
    way for a test to ask for it; every page object that imports
    DOWNLOAD_DIR directly (`from utils.config import DOWNLOAD_DIR`) already
    gets the same isolation without needing this fixture at all.

    NOTE: this used to read `Config.DOWNLOAD_DIR` before DOWNLOAD_DIR was
    also exposed as a Config class attribute (see utils/config.py) — it was
    previously only a module-level constant, so this line would have
    raised AttributeError the first time anything actually called this
    fixture. Nothing did (0 consumers before this pass), which is how it
    went unnoticed."""
    return Config.DOWNLOAD_DIR
