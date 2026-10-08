"""
tests/unit/test_secret_config.py -- environment/secret separation
(Bitbucket secured variables work).

Covers utils.config.SECRET_ENV_MAPPING / resolve_secret() /
missing_required_secrets() / validate_required_secrets(), and that
scripts/ci_preflight.py never prints a secret value. No browser.

Same subprocess technique as tests/unit/test_environment_config.py and
for the same reason -- utils/config.py resolves everything at MODULE
IMPORT TIME from os.environ (and from the project's real root .env via
python-dotenv's override=False), so each scenario needs a fresh process
with an exactly-controlled environment, not importlib.reload() in a
shared process.

IMPORTANT: load_dotenv(override=False) leaves an already-present key in
os.environ untouched, INCLUDING one explicitly set to "" -- so a
"nothing is set" scenario below explicitly passes VALID_EMAIL="" /
VALID_PASSWORD="" / SMS_API_TOKEN="" (the legacy fallback variable
names) to neutralize whatever this real project's own root .env/
config/environments/*.env files happen to contain locally. Without
that, a developer's own populated root .env would silently satisfy the
legacy fallback and these "missing" tests would pass for the wrong
reason.
"""
import json
import os
import subprocess
import sys

import pytest

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Neutralizes the legacy fallback (and, since these are explicit keys,
# also pre-empts load_dotenv(override=False) from ever filling them from
# a real local .env/config/environments/<ENV>.env file).
_BLANK_LEGACY = {"VALID_EMAIL": "", "VALID_PASSWORD": "", "SMS_API_TOKEN": ""}


def _run(env_overrides: dict, snippet: str) -> subprocess.CompletedProcess:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": _PROJECT_ROOT,
    }
    env.update(_BLANK_LEGACY)
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-c", snippet],
        cwd=_PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _resolve_json(env_overrides: dict, snippet: str) -> dict:
    result = _run(env_overrides, snippet)
    assert result.returncode == 0, f"subprocess failed (exit {result.returncode}):\n{result.stderr}"
    return json.loads(result.stdout.strip().splitlines()[-1])


_CONFIG_SECRETS_SNIPPET = (
    "import json; from utils.config import Config; "
    "print(json.dumps({"
    "'valid_email': Config.VALID_EMAIL, 'valid_password': Config.VALID_PASSWORD, "
    "'sms_api_token': Config.SMS_API_TOKEN, 'base_url': Config.BASE_URL}))"
)

_VALIDATE_SNIPPET = (
    "import json; from utils.config import validate_required_secrets; "
    "ok = True; message = ''\n"
    "try:\n"
    "    validate_required_secrets()\n"
    "except RuntimeError as exc:\n"
    "    ok = False; message = str(exc)\n"
    "print(json.dumps({'ok': ok, 'message': message}))"
)


# ─────────────────────────────────────────────────────────────────────────
# 1-3. ENV=qa resolves QA_EMAIL / QA_PASSWORD / SMS_API_TOKEN_QA
# ─────────────────────────────────────────────────────────────────────────

def test_env_qa_resolves_qa_email():
    result = _resolve_json(
        {"ENV": "qa", "QA_EMAIL": "qa-user@example.com", "QA_PASSWORD": "qa-pass", "SMS_API_TOKEN_QA": "qa-token"},
        _CONFIG_SECRETS_SNIPPET,
    )
    assert result["valid_email"] == "qa-user@example.com"


def test_env_qa_resolves_qa_password():
    result = _resolve_json(
        {"ENV": "qa", "QA_EMAIL": "qa-user@example.com", "QA_PASSWORD": "qa-pass", "SMS_API_TOKEN_QA": "qa-token"},
        _CONFIG_SECRETS_SNIPPET,
    )
    assert result["valid_password"] == "qa-pass"


def test_env_qa_resolves_sms_api_token_qa():
    result = _resolve_json(
        {"ENV": "qa", "QA_EMAIL": "qa-user@example.com", "QA_PASSWORD": "qa-pass", "SMS_API_TOKEN_QA": "qa-token"},
        _CONFIG_SECRETS_SNIPPET,
    )
    assert result["sms_api_token"] == "qa-token"


# ─────────────────────────────────────────────────────────────────────────
# 4-6. ENV=staging resolves STAGING_EMAIL / STAGING_PASSWORD / SMS_API_TOKEN_STAGING
# ─────────────────────────────────────────────────────────────────────────

def test_env_staging_resolves_staging_email():
    result = _resolve_json(
        {
            "ENV": "staging", "STAGING_EMAIL": "staging-user@example.com",
            "STAGING_PASSWORD": "staging-pass", "SMS_API_TOKEN_STAGING": "staging-token",
        },
        _CONFIG_SECRETS_SNIPPET,
    )
    assert result["valid_email"] == "staging-user@example.com"


def test_env_staging_resolves_staging_password():
    result = _resolve_json(
        {
            "ENV": "staging", "STAGING_EMAIL": "staging-user@example.com",
            "STAGING_PASSWORD": "staging-pass", "SMS_API_TOKEN_STAGING": "staging-token",
        },
        _CONFIG_SECRETS_SNIPPET,
    )
    assert result["valid_password"] == "staging-pass"


def test_env_staging_resolves_sms_api_token_staging():
    result = _resolve_json(
        {
            "ENV": "staging", "STAGING_EMAIL": "staging-user@example.com",
            "STAGING_PASSWORD": "staging-pass", "SMS_API_TOKEN_STAGING": "staging-token",
        },
        _CONFIG_SECRETS_SNIPPET,
    )
    assert result["sms_api_token"] == "staging-token"


# ─────────────────────────────────────────────────────────────────────────
# 7-9. Missing individual qa secrets fail clearly, by name
# ─────────────────────────────────────────────────────────────────────────

def test_missing_qa_email_fails_clearly():
    result = _resolve_json(
        {"ENV": "qa", "QA_PASSWORD": "qa-pass", "SMS_API_TOKEN_QA": "qa-token"},
        _VALIDATE_SNIPPET,
    )
    assert result["ok"] is False
    assert "QA_EMAIL" in result["message"]
    assert "qa-pass" not in result["message"]
    assert "qa-token" not in result["message"]


def test_missing_qa_password_fails_clearly():
    result = _resolve_json(
        {"ENV": "qa", "QA_EMAIL": "qa-user@example.com", "SMS_API_TOKEN_QA": "qa-token"},
        _VALIDATE_SNIPPET,
    )
    assert result["ok"] is False
    assert "QA_PASSWORD" in result["message"]
    assert "qa-token" not in result["message"]


def test_missing_sms_api_token_qa_fails_clearly():
    result = _resolve_json(
        {"ENV": "qa", "QA_EMAIL": "qa-user@example.com", "QA_PASSWORD": "qa-pass"},
        _VALIDATE_SNIPPET,
    )
    assert result["ok"] is False
    assert "SMS_API_TOKEN_QA" in result["message"]
    assert "qa-pass" not in result["message"]


# ─────────────────────────────────────────────────────────────────────────
# 10. Missing staging secrets fail clearly (all three named together)
# ─────────────────────────────────────────────────────────────────────────

def test_missing_all_staging_secrets_fails_clearly():
    result = _resolve_json({"ENV": "staging"}, _VALIDATE_SNIPPET)
    assert result["ok"] is False
    assert "staging" in result["message"]
    assert "STAGING_EMAIL" in result["message"]
    assert "STAGING_PASSWORD" in result["message"]
    assert "SMS_API_TOKEN_STAGING" in result["message"]


# ─────────────────────────────────────────────────────────────────────────
# 11. Secret values are never printed anywhere -- ci_preflight.py output
# ─────────────────────────────────────────────────────────────────────────

def test_ci_preflight_never_prints_secret_values():
    secret_email = "super-secret-user@example.com"
    secret_password = "Sup3rSecretPassword!"  # pragma: allowlist secret
    secret_token = "sk-super-secret-token-value-123456"
    result = _run(
        {
            "ENV": "qa", "QA_EMAIL": secret_email, "QA_PASSWORD": secret_password,
            "SMS_API_TOKEN_QA": secret_token,
        },
        "",  # unused -- we invoke the script below instead of -c
    )
    script = os.path.join(_PROJECT_ROOT, "scripts", "ci_preflight.py")
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": _PROJECT_ROOT}
    env.update(_BLANK_LEGACY)
    env.update({
        "ENV": "qa", "QA_EMAIL": secret_email, "QA_PASSWORD": secret_password,
        "SMS_API_TOKEN_QA": secret_token,
    })
    proc = subprocess.run(
        [sys.executable, script], cwd=_PROJECT_ROOT, env=env,
        capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    combined = proc.stdout + proc.stderr
    assert secret_email not in combined
    assert secret_password not in combined
    assert secret_token not in combined
    assert "[OK] QA_EMAIL is set" in combined
    assert "[OK] QA_PASSWORD is set" in combined
    assert "[OK] SMS_API_TOKEN_QA is set" in combined


def test_ci_preflight_reports_missing_without_printing_values():
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": _PROJECT_ROOT}
    env.update(_BLANK_LEGACY)
    env.update({"ENV": "staging", "STAGING_EMAIL": "present@example.com"})
    script = os.path.join(_PROJECT_ROOT, "scripts", "ci_preflight.py")
    proc = subprocess.run(
        [sys.executable, script], cwd=_PROJECT_ROOT, env=env,
        capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 1
    assert "[OK] STAGING_EMAIL is set" in proc.stdout
    assert "[MISSING] STAGING_PASSWORD is not set" in proc.stdout
    assert "[MISSING] SMS_API_TOKEN_STAGING is not set" in proc.stdout
    assert "present@example.com" not in proc.stdout


# ─────────────────────────────────────────────────────────────────────────
# 12. Existing non-secret environment configuration still loads correctly
# ─────────────────────────────────────────────────────────────────────────

def test_non_secret_configuration_still_loads_correctly():
    result = _resolve_json(
        {"ENV": "staging", "STAGING_EMAIL": "x@example.com", "STAGING_PASSWORD": "x", "SMS_API_TOKEN_STAGING": "x"},
        _CONFIG_SECRETS_SNIPPET,
    )
    assert result["base_url"] == "https://testqa.cpaas.globeteleservices.com"


# ─────────────────────────────────────────────────────────────────────────
# 13. An ENV with no SECRET_ENV_MAPPING entry has nothing "required"
#     (e.g. local-only ENV=dev) -- existing behavior for that case is
#     unchanged/not broken by this feature.
# ─────────────────────────────────────────────────────────────────────────

def test_env_with_no_mapping_entry_has_no_required_secrets():
    result = _resolve_json({"ENV": "dev"}, _VALIDATE_SNIPPET)
    assert result["ok"] is True
