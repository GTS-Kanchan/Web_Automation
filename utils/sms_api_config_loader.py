"""
config_loader.py

Central place that resolves which environment/instance to run against and
returns a fully-resolved config object. This is the single thing you touch
to "switch instances" — either by:

  1. Editing `active_environment` in config/environments.yaml, or
  2. Setting env var ENV_NAME=production, or
  3. Passing --env production on the pytest CLI (see conftest.py)

Auth tokens are resolved with this priority (highest first), so CI/CD
pipelines never need the token committed to the repo:

  1. The UI's selected-ENV-mapped secret (utils.config.SECRET_ENV_MAPPING,
     e.g. SMS_API_TOKEN_QA when the real ENV env var is "qa") -- ONLY when
     ENV is actually set to a mapped value, so the UI and the API/DLR
     client can never silently resolve a different environment's token
     from each other (the historical "UI=QA, API=dev" risk -- see
     scripts/validate_config.py's _VERIFIED_ENV_NAME_PAIRINGS). A
     standalone API-only run that sets ENV_NAME (not ENV) to something
     else (e.g. production/malaysia/testqa) is untouched by this -- ENV
     being unset means this priority level is skipped entirely.
  2. Environment variable  SMS_API_TOKEN_<ENVNAME>   (e.g. SMS_API_TOKEN_TESTQA)
  3. Generic fallback env var  SMS_API_TOKEN
  4. `auth_token` value in environments.yaml (legacy escape hatch -- this
     should no longer hold a real token; see environments.yaml's own
     comments)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from utils.config import SECRET_ENV_MAPPING
from utils.config import Config as _UIConfig

# Namespaced under config/sms_api/ (not config/environments/, which the
# main UI suite's utils/config.py already owns for its own .env-per-ENV
# mechanism) so the two environment-switching systems never collide on
# the same directory.
CONFIG_DIR = Path(__file__).resolve().parent.parent / "config" / "sms_api"
ENVIRONMENTS_FILE = CONFIG_DIR / "environments.yaml"
TEST_DATA_FILE = CONFIG_DIR / "test_data.yaml"


@dataclass
class EnvironmentConfig:
    name: str
    base_url: str
    sms_send_url: str
    campaign_send_url: str
    template_send_url: str
    send_msg_url: str
    sms_json_url: str
    webengage_send_url: str
    dlr_url: str
    dlr_verify_url: str
    auth_token: str
    campaign_id: str
    template_id: str
    timeout_seconds: int
    verify_ssl: bool

    @property
    def headers(self) -> dict:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}",
        }


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    # Explicit UTF-8 is required here: on Windows, Python's default open()
    # encoding is the system locale (often cp1252), which cannot decode
    # non-ASCII characters (e.g. Unicode test payloads) and raises
    # UnicodeDecodeError. YAML files are UTF-8 by spec, so always read them
    # that way regardless of platform.
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_environment_name(cli_env: str | None = None) -> str:
    """Resolution order: CLI flag > ENV_NAME env var > yaml default."""
    if cli_env:
        return cli_env
    if os.environ.get("ENV_NAME"):
        return os.environ["ENV_NAME"]
    data = _load_yaml(ENVIRONMENTS_FILE)
    return data["active_environment"]


def load_environment_config(cli_env: str | None = None) -> EnvironmentConfig:
    data = _load_yaml(ENVIRONMENTS_FILE)
    env_name = get_environment_name(cli_env)

    envs = data.get("environments", {})
    if env_name not in envs:
        raise KeyError(
            f"Environment '{env_name}' not found in environments.yaml. "
            f"Available: {list(envs.keys())}"
        )

    env = envs[env_name]

    # Token resolution -- see this module's own docstring for the full
    # priority order. `ui_token` is only even attempted when the real ENV
    # env var is explicitly set to a SECRET_ENV_MAPPING key (qa/staging):
    # Config.SMS_API_TOKEN always resolves to SOMETHING (it has its own
    # legacy fallback), so gating on the raw ENV var -- not on whether
    # Config.SMS_API_TOKEN happened to be truthy -- is what keeps a
    # standalone API-only run (ENV unset, only ENV_NAME=production set)
    # from accidentally picking up a QA/staging secret meant for the UI.
    explicit_ui_env = os.environ.get("ENV", "").strip().lower()
    ui_token = _UIConfig.SMS_API_TOKEN if explicit_ui_env in SECRET_ENV_MAPPING else ""
    token_env_var = f"SMS_API_TOKEN_{env_name.upper()}"
    auth_token = (
        ui_token
        or os.environ.get(token_env_var)
        or os.environ.get("SMS_API_TOKEN")
        or env.get("auth_token", "")
    )

    if not auth_token:
        raise ValueError(
            f"No auth token found for environment '{env_name}'. Set "
            f"SMS_API_TOKEN_{explicit_ui_env.upper()} (when ENV={explicit_ui_env!r}) or "
            f"{token_env_var} as an environment variable -- never in "
            f"environments.yaml."
            if explicit_ui_env in SECRET_ENV_MAPPING else
            f"No auth token found for environment '{env_name}'. Set "
            f"{token_env_var} (or SMS_API_TOKEN) as an environment variable -- "
            f"never in environments.yaml."
        )

    base_url = env["base_url"].rstrip("/")

    # DLR service lives on its own host:port, separate from base_url (see
    # the comment on dlr_base_url in environments.yaml). Not every
    # environment block is guaranteed to define it yet, so this stays
    # optional rather than raising KeyError for environments that haven't
    # been given a DLR host.
    dlr_url = ""
    if env.get("dlr_base_url") and env.get("dlr_path"):
        dlr_url = env["dlr_base_url"].rstrip("/") + env["dlr_path"]

    # Bulk DLR verification endpoint (POST .../api/v1/dlr/verify) -- same
    # optionality reasoning as dlr_url above.
    dlr_verify_url = ""
    if env.get("dlr_base_url") and env.get("dlr_verify_path"):
        dlr_verify_url = env["dlr_base_url"].rstrip("/") + env["dlr_verify_path"]

    return EnvironmentConfig(
        name=env_name,
        base_url=base_url,
        sms_send_url=base_url + env["sms_send_path"],
        campaign_send_url=base_url + env["campaign_send_path"],
        template_send_url=base_url + env["template_send_path"],
        send_msg_url=base_url + env["send_msg_path"],
        sms_json_url=base_url + env["sms_json_path"],
        webengage_send_url=base_url + env["webengage_send_path"],
        dlr_url=dlr_url,
        dlr_verify_url=dlr_verify_url,
        auth_token=auth_token,
        campaign_id=env.get("campaign_id", ""),
        template_id=env.get("template_id", ""),
        timeout_seconds=int(env.get("timeout_seconds", 15)),
        verify_ssl=bool(env.get("verify_ssl", True)),
    )


def load_test_data() -> dict[str, Any]:
    return _load_yaml(TEST_DATA_FILE)
