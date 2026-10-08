"""
tests/unit/test_environment_config.py — fast, browser-free unit tests for
the Environment and Instance Configuration resolution chain (see README's
"Environment and Instance Configuration" section).

Why subprocess, not import/reload
-----------------------------------
utils/config.py resolves ENV/INSTANCE and loads the matching .env files at
MODULE IMPORT TIME, reading os.environ as it was at that exact moment. A
single test process that imports utils.config once can't cleanly re-run
that resolution under a dozen different ENV/INSTANCE combinations just by
mutating os.environ afterwards or importlib.reload()-ing (dotenv's
override=False semantics mean a reload would see values already left in
os.environ by a PREVIOUS scenario in this same test run, contaminating the
next one). Each test below instead launches a tiny, fully isolated `python
-c` subprocess with exactly the env vars that scenario needs, and reads
back a small JSON blob it prints -- the same technique used to manually
verify this feature end-to-end while building it, and the only one that
exercises the real, unmodified import-time code path with a clean
os.environ every time.

Run just this file with:
    pytest tests/unit/test_environment_config.py -v
"""
import json
import os
import subprocess
import sys

import pytest

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _resolve(env_overrides: dict, snippet: str) -> dict:
    """Runs `snippet` (a python -c body that must print exactly one JSON
    object to stdout) in a fresh subprocess, with a clean environment
    (PATH/PYTHON* passthrough only, plus `env_overrides`) rooted at the
    project directory. Returns the parsed JSON. Raises AssertionError with
    the full stderr on a non-zero exit, so a resolution-chain failure
    shows up as a clear test failure rather than a cryptic JSON parse
    error."""
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": _PROJECT_ROOT,
    }
    env.update(env_overrides)
    result = subprocess.run(
        [sys.executable, "-c", snippet],
        cwd=_PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"subprocess failed (exit {result.returncode}):\n{result.stderr}"
    )
    return json.loads(result.stdout.strip().splitlines()[-1])


_CONFIG_SNIPPET = (
    "import json; from utils.config import Config; "
    "print(json.dumps({"
    "'env': Config.ENV, 'instance': Config.INSTANCE, "
    "'base_url': Config.BASE_URL, 'api_url': Config.API_URL, "
    "'dlr_url': Config.DLR_URL, 'headless': Config.HEADLESS, "
    "'reports_dir': Config.REPORTS_DIR}))"
)

_AUTH_STATE_SNIPPET = (
    "import json; from utils import auth_state; "
    "print(json.dumps({'state_path': auth_state.STATE_PATH}))"
)


# ─────────────────────────────────────────────────────────────────────────
# 1. Root .env fallback
# ─────────────────────────────────────────────────────────────────────────

def test_root_env_fallback_with_no_env_or_instance():
    """No ENV, no INSTANCE -- root .env (+ Config's hardcoded defaults)
    only, exactly as before this feature existed."""
    result = _resolve({}, _CONFIG_SNIPPET)
    assert result["env"] == "qa"  # Config.ENV's own hardcoded default
    assert result["instance"] == ""
    assert result["base_url"]  # root .env's real BASE_URL, non-empty


# ─────────────────────────────────────────────────────────────────────────
# 2. Environment override
# ─────────────────────────────────────────────────────────────────────────

def test_environment_override():
    result = _resolve({"ENV": "staging"}, _CONFIG_SNIPPET)
    assert result["env"] == "staging"
    assert result["base_url"] == "https://testqa.cpaas.globeteleservices.com"


# ─────────────────────────────────────────────────────────────────────────
# 3. Instance override
# ─────────────────────────────────────────────────────────────────────────

def test_instance_override():
    result = _resolve({"ENV": "staging", "INSTANCE": "staging-01"}, _CONFIG_SNIPPET)
    assert result["instance"] == "staging-01"
    assert result["base_url"] == "https://staging-01.example.com"
    assert result["api_url"] == "https://staging-01-api.example.com"
    assert result["dlr_url"] == "https://staging-01-dlr.example.com"


def test_different_instances_resolve_different_urls():
    """staging-01 and staging-02 must never resolve to the same BASE_URL
    -- the whole point of instance support."""
    one = _resolve({"ENV": "staging", "INSTANCE": "staging-01"}, _CONFIG_SNIPPET)
    two = _resolve({"ENV": "staging", "INSTANCE": "staging-02"}, _CONFIG_SNIPPET)
    assert one["base_url"] != two["base_url"]


# ─────────────────────────────────────────────────────────────────────────
# 4. Runtime environment variable override (highest priority)
# ─────────────────────────────────────────────────────────────────────────

def test_runtime_env_var_wins_over_instance_and_environment_files():
    result = _resolve(
        {"ENV": "staging", "INSTANCE": "staging-01", "BASE_URL": "https://temporary.example.com"},
        _CONFIG_SNIPPET,
    )
    assert result["base_url"] == "https://temporary.example.com"


# ─────────────────────────────────────────────────────────────────────────
# 5. Missing environment (no config/environments/<ENV>.env for it)
# ─────────────────────────────────────────────────────────────────────────

def test_missing_environment_file_does_not_crash_and_falls_back():
    """ENV set to something with no matching file -- Config silently
    falls back to root .env/defaults for the fields that file would have
    set (requirement #4's hard validation failure is scripts/
    validate_config.py's job, not Config's -- Config itself stays
    permissive at import time, exactly like it already was for ENV before
    INSTANCE existed)."""
    result = _resolve({"ENV": "does-not-exist"}, _CONFIG_SNIPPET)
    assert result["env"] == "does-not-exist"
    assert result["base_url"]  # still resolved, from root .env


# ─────────────────────────────────────────────────────────────────────────
# 6. Missing instance (no config/instances/<INSTANCE>.env for it)
# ─────────────────────────────────────────────────────────────────────────

def test_missing_instance_file_does_not_crash_and_falls_back():
    result = _resolve({"ENV": "staging", "INSTANCE": "does-not-exist"}, _CONFIG_SNIPPET)
    assert result["instance"] == "does-not-exist"
    # No instances/does-not-exist.env -> falls through to environments/staging.env's BASE_URL
    assert result["base_url"] == "https://testqa.cpaas.globeteleservices.com"


# ─────────────────────────────────────────────────────────────────────────
# 7. Invalid instance -- scripts/validate_config.py's job to REJECT
# ─────────────────────────────────────────────────────────────────────────

def test_validate_config_rejects_invalid_instance():
    result = subprocess.run(
        [sys.executable, "scripts/validate_config.py"],
        cwd=_PROJECT_ROOT,
        env={
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": _PROJECT_ROOT,
            "ENV": "staging",
            "INSTANCE": "staging-99",
        },
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1
    assert "FAILED" in result.stdout
    assert "staging-99" in result.stdout


def test_validate_config_accepts_valid_instance():
    result = subprocess.run(
        [sys.executable, "scripts/validate_config.py"],
        cwd=_PROJECT_ROOT,
        env={
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": _PROJECT_ROOT,
            "ENV": "staging",
            "INSTANCE": "staging-01",
            # Environment/secret separation work added a THIRD required
            # secret (the SMS API token) to validate_config.py's checks,
            # alongside email/password -- VALID_EMAIL/VALID_PASSWORD for
            # this scenario already come from the real root .env (legacy
            # fallback, see utils.config.resolve_secret()), but nothing
            # provides an SMS token the same way, so one must be supplied
            # explicitly here now. Generic SMS_API_TOKEN (not
            # SMS_API_TOKEN_STAGING) deliberately, to also exercise that
            # legacy-fallback path rather than only the new ENV-mapped one.
            "SMS_API_TOKEN": "test-instance-token",
        },
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert "PASSED" in result.stdout


# ─────────────────────────────────────────────────────────────────────────
# 8. Environment-only execution
# ─────────────────────────────────────────────────────────────────────────

def test_environment_only_execution_leaves_instance_unset():
    result = _resolve({"ENV": "qa"}, _CONFIG_SNIPPET)
    assert result["env"] == "qa"
    assert result["instance"] == ""
    assert result["reports_dir"].endswith("/reports")  # flat, unscoped


# ─────────────────────────────────────────────────────────────────────────
# 9. Environment + instance execution
# ─────────────────────────────────────────────────────────────────────────

def test_environment_and_instance_execution():
    result = _resolve({"ENV": "dev", "INSTANCE": "dev-01"}, _CONFIG_SNIPPET)
    assert result["env"] == "dev"
    assert result["instance"] == "dev-01"
    assert result["base_url"] == "https://dev-01.example.com"


# ─────────────────────────────────────────────────────────────────────────
# 10. Auth state path generation
# ─────────────────────────────────────────────────────────────────────────

def test_auth_state_path_unscoped_without_instance():
    result = _resolve({"ENV": "staging"}, _AUTH_STATE_SNIPPET)
    assert result["state_path"].replace("\\", "/").endswith("reports/.auth/state.json")


def test_auth_state_path_scoped_with_instance():
    result = _resolve({"ENV": "staging", "INSTANCE": "staging-01"}, _AUTH_STATE_SNIPPET)
    normalized = result["state_path"].replace("\\", "/")
    assert normalized.endswith("reports/.auth/staging/staging-01/state.json")


def test_auth_state_path_different_per_instance():
    """requirement #8: staging-01's cookies must never be reused against
    staging-02."""
    one = _resolve({"ENV": "staging", "INSTANCE": "staging-01"}, _AUTH_STATE_SNIPPET)
    two = _resolve({"ENV": "staging", "INSTANCE": "staging-02"}, _AUTH_STATE_SNIPPET)
    assert one["state_path"] != two["state_path"]


def test_auth_state_path_explicit_override_always_wins():
    result = _resolve(
        {"ENV": "staging", "INSTANCE": "staging-01", "AUTH_STATE_PATH": "/tmp/custom_state.json"},
        _AUTH_STATE_SNIPPET,
    )
    assert result["state_path"] == "/tmp/custom_state.json"


# ─────────────────────────────────────────────────────────────────────────
# 11. Report path generation
# ─────────────────────────────────────────────────────────────────────────

def test_report_path_unscoped_without_instance():
    result = _resolve({}, _CONFIG_SNIPPET)
    assert result["reports_dir"].replace("\\", "/").endswith("/reports")


def test_report_path_scoped_with_instance():
    result = _resolve({"ENV": "staging", "INSTANCE": "staging-01"}, _CONFIG_SNIPPET)
    normalized = result["reports_dir"].replace("\\", "/")
    assert normalized.endswith("/reports/staging/staging-01")


def test_report_path_includes_run_id_when_set():
    result = _resolve(
        {"ENV": "staging", "INSTANCE": "staging-01", "REPORT_RUN_ID": "20261007_120000"},
        _CONFIG_SNIPPET,
    )
    normalized = result["reports_dir"].replace("\\", "/")
    assert normalized.endswith("/reports/staging/staging-01/20261007_120000")


# ─────────────────────────────────────────────────────────────────────────
# 12. Secret masking
# ─────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "name",
    ["VALID_PASSWORD", "API_TOKEN", "AUTH_SECRET", "SOME_KEY", "AUTH_STATE_PATH", "SESSION_COOKIE"],
)
def test_secret_names_are_masked(name):
    from utils.config import is_secret_name, mask_value

    assert is_secret_name(name) is True
    assert mask_value(name, "real-value-should-never-appear") == "****"


@pytest.mark.parametrize("name", ["BASE_URL", "ENV", "INSTANCE", "HEADLESS", "PLAYWRIGHT_WORKERS"])
def test_non_secret_names_are_not_masked(name):
    from utils.config import is_secret_name, mask_value

    assert is_secret_name(name) is False
    assert mask_value(name, "visible-value") == "visible-value"


# ─────────────────────────────────────────────────────────────────────────
# 13. Worker-specific report paths (pytest-xdist's PYTEST_XDIST_WORKER)
# ─────────────────────────────────────────────────────────────────────────

def test_worker_scoped_dir_nests_under_instance_aware_reports_dir(tmp_path):
    snippet = (
        "import json; from utils.config import Config; "
        "from utils.parallel import worker_scoped_dir; "
        "import os; "
        "path = worker_scoped_dir(os.path.join(Config.REPORTS_DIR, 'screenshots')); "
        "print(json.dumps({'path': path}))"
    )
    result = _resolve(
        {"ENV": "staging", "INSTANCE": "staging-01", "PYTEST_XDIST_WORKER": "gw3"},
        snippet,
    )
    normalized = result["path"].replace("\\", "/")
    assert normalized.endswith("/reports/staging/staging-01/screenshots/gw3")


def test_worker_scoped_dir_falls_back_to_master_outside_xdist():
    snippet = (
        "import json; from utils.config import Config; "
        "from utils.parallel import worker_scoped_dir; "
        "import os; "
        "path = worker_scoped_dir(os.path.join(Config.REPORTS_DIR, 'screenshots')); "
        "print(json.dumps({'path': path}))"
    )
    result = _resolve({"ENV": "staging", "INSTANCE": "staging-01"}, snippet)
    normalized = result["path"].replace("\\", "/")
    assert normalized.endswith("/reports/staging/staging-01/screenshots/master")
