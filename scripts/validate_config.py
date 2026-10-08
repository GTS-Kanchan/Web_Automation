#!/usr/bin/env python3
"""
scripts/validate_config.py -- fail-fast validation of the resolved
ENV/INSTANCE configuration, BEFORE Playwright (or any browser) starts.

Part of the Environment and Instance Configuration work (see README's
section of that name). This script does NOT itself launch any browser --
it only re-reads the exact same Config the real test run would use (same
resolution order: runtime env vars > config/instances/<INSTANCE>.env >
config/environments/<ENV>.env > root .env > Config defaults -- see
utils/config.py's module docstring) and checks it's actually usable.

Usage:
    python scripts/validate_config.py
    ENV=staging INSTANCE=staging-01 python scripts/validate_config.py
    ENV=staging INSTANCE=staging-01 python scripts/validate_config.py --show

Exit code 0 on PASSED, 1 on FAILED -- scripts/run_tests.py calls this
before invoking pytest and aborts the whole run on a non-zero exit,
exactly like requirement #4's "fail fast before Playwright starts".
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.config import Config, is_secret_name, mask_value, missing_required_secrets  # noqa: E402

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_ENVIRONMENTS_DIR = os.path.join(_PROJECT_ROOT, "config", "environments")
_INSTANCES_DIR = os.path.join(_PROJECT_ROOT, "config", "instances")

# Config attributes an API/DLR-dependent test actually needs. Checked only
# as a WARNING (not a hard failure) when empty -- plenty of real test runs
# (UI-only channels, non-DLR tests) never touch these, so an empty DLR_URL
# alone must not block e.g. `pytest tests/rcs`.
_API_RELATED_FIELDS = ("API_URL", "DLR_URL")

# Verified ENV -> expected API/DLR environment (ENV_NAME, resolved by the
# SEPARATE utils/sms_api_config_loader.py system -- config/sms_api/
# environments.yaml) pairing, confirmed by comparing real host URLs on
# both sides (see scripts/run_tests.py's module docstring for the
# original evidence, and config/environments/<ENV>.env's own ENV_NAME=
# line for where each pairing is actually applied). This is NOT a plain
# string-equality check -- "qa" verifiably pairs with API environment
# "dev" (same real host), not "qa" -- so it's its own explicit table,
# kept in sync by hand with scripts/run_tests.py's INSTANCE_MAP and the
# ENV_NAME= line in each config/environments/*.env file. If a pairing
# ever changes, update all three places together.
_VERIFIED_ENV_NAME_PAIRINGS = {
    "dev": "dev",
    "qa": "dev",
    "staging": "staging",
}


def _legacy_instance_names() -> set:
    """Names the LEGACY INSTANCE shorthand in scripts/run_tests.py
    already recognizes (today: "staging", "qa") -- see that script's
    module docstring for the full "ENV vs ENV_NAME vs INSTANCE" history.
    A bare INSTANCE=staging is a fully legitimate, pre-existing,
    already-resolved invocation by the time this script runs (run_tests.py
    applies that shorthand BEFORE calling this validator) -- it must never
    be reported as an unknown/missing instance just because no
    config/instances/staging.env file exists (that file was never
    supposed to exist for the legacy shorthand). Returns an empty set
    (never raises) if run_tests.py can't be imported for any reason --
    this is a best-effort backward-compat allowance, not a hard
    dependency."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import run_tests  # scripts/run_tests.py -- same directory
        return set(run_tests.INSTANCE_MAP)
    except Exception:
        return set()


def _available_names(directory: str) -> list:
    if not os.path.isdir(directory):
        return []
    names = []
    for fname in sorted(os.listdir(directory)):
        if fname.endswith(".env"):
            names.append(fname[: -len(".env")])
    return names


def validate() -> tuple:
    """Returns (passed: bool, errors: list[str], warnings: list[str])."""
    errors = []
    warnings = []

    env_name = Config.ENV
    instance_name = Config.INSTANCE

    # ENV: Config.ENV always has a value (defaults to "qa" per
    # utils/config.py), so "ENV exists" is really "does a real ENV var
    # with a value outside the built-in default have a matching file".
    # Only enforced when ENV was EXPLICITLY set (os.environ, not the
    # Config default) -- an ENV-less invocation (plain `pytest`, using
    # only root .env) must never be told its "environment" is invalid.
    explicit_env = os.environ.get("ENV", "").strip()
    if explicit_env:
        env_file = os.path.join(_ENVIRONMENTS_DIR, f"{explicit_env}.env")
        if not os.path.isfile(env_file):
            errors.append(
                f"Environment configuration not found:\n"
                f"    config/environments/{explicit_env}.env\n\n"
                f"Available environments:\n"
                + "\n".join(f"- {n}" for n in _available_names(_ENVIRONMENTS_DIR))
            )

    # INSTANCE: only validated when actually provided -- requirement #5
    # ("do not force the user to create an instance file just to run
    # locally") means an INSTANCE-less run is never faulted for it.
    if instance_name and instance_name not in _legacy_instance_names():
        instance_file = os.path.join(_INSTANCES_DIR, f"{instance_name}.env")
        if not os.path.isfile(instance_file):
            errors.append(
                f"Instance configuration not found:\n"
                f"    config/instances/{instance_name}.env\n\n"
                f"Available instances:\n"
                + "\n".join(f"- {n}" for n in _available_names(_INSTANCES_DIR))
            )
        else:
            # "instance configuration is valid" -- at minimum, parseable
            # (already proven by Config having loaded it without raising)
            # and non-empty.
            if os.path.getsize(instance_file) == 0:
                errors.append(f"Instance configuration file is empty: config/instances/{instance_name}.env")

    # required BASE_URL
    if not Config.BASE_URL:
        errors.append("Required configuration missing: BASE_URL is empty.")

    # required credentials / SMS API token -- reports the exact missing
    # environment variable NAME(S) (e.g. "QA_EMAIL"), never a value.
    # missing_required_secrets() already treats the legacy VALID_EMAIL/
    # VALID_PASSWORD/SMS_API_TOKEN fallback as satisfying the check (same
    # leniency the previous "VALID_EMAIL / VALID_PASSWORD are not both
    # set" check had for an ENV-less, root-.env-only local run), so this
    # is checked unconditionally -- same strictness as before, just with
    # the exact missing variable name(s) now named instead of a generic
    # message.
    missing_secrets = missing_required_secrets(explicit_env or None)
    if missing_secrets:
        errors.append(
            f"Missing required secrets for environment '{explicit_env or Config.ENV}': "
            + ", ".join(missing_secrets)
        )

    # API/DLR config -- warning only (see _API_RELATED_FIELDS docstring above)
    for field in _API_RELATED_FIELDS:
        if not getattr(Config, field, ""):
            warnings.append(
                f"{field} is empty -- fine for most test runs, but any test that "
                f"depends on it (DLR/API checks) will fail with a clear error "
                f"when it actually tries to use it."
            )

    # Environment mismatch -- a HARD failure, checked only when ENV was
    # explicitly set (same "don't fault an ENV-less run" rule as above).
    # Catches a misconfigured runtime ENV_NAME (CI/CD, requirement #20:
    # "Do not allow ENV=staging + QA credentials unless explicitly
    # configured" -- the concrete, automatable half of that requirement:
    # the UI environment and the API/DLR environment must be the
    # VERIFIED matching pair, not just happen to both be set to
    # something). A mismatch here means either a bad runtime ENV_NAME
    # override, or a pairing that was never actually verified -- either
    # way, tests must NOT start against possibly-wrong, possibly
    # cross-environment data.
    env_mismatch = None
    if explicit_env and explicit_env in _VERIFIED_ENV_NAME_PAIRINGS:
        try:
            from utils.sms_api_config_loader import get_environment_name
            actual_env_name = get_environment_name()
        except Exception:
            actual_env_name = None
        expected_env_name = _VERIFIED_ENV_NAME_PAIRINGS[explicit_env]
        if actual_env_name is not None and actual_env_name != expected_env_name:
            env_mismatch = {
                "requested": explicit_env,
                "ui": explicit_env,
                "api": actual_env_name,
                "dlr": actual_env_name,  # same ENV_NAME-keyed yaml block resolves both
            }
            errors.append(
                "Environment mismatch detected.\n\n"
                f"Requested environment : {env_mismatch['requested']}\n"
                f"UI environment        : {env_mismatch['ui']}\n"
                f"API environment       : {env_mismatch['api']}\n"
                f"DLR environment       : {env_mismatch['dlr']}\n\n"
                "Tests will NOT start."
            )

    return (len(errors) == 0, errors, warnings)


def _print_banner(channel=None, test_type=None, workers=None):
    """Plain standalone use (no extra args) prints the original, simpler
    banner. When run_tests.py/CI calls this with channel/test_type/workers
    (display-only -- they affect nothing in validate()), the fuller CI
    banner (Environment and Instance Configuration CI/CD work,
    requirement #20) is printed instead, right before tests start --
    never a password/token/cookie/storage-state value, matching every
    other diagnostic print in this project."""
    if channel is not None or test_type is not None or workers is not None:
        print("=" * 45)
        print(" CPaaS Playwright CI")
        print("=" * 45)
        print()
        print(f"Environment : {Config.ENV}")
        print(f"Channel     : {channel or '(n/a)'}")
        print(f"Test Type   : {test_type or '(n/a)'}")
        print(f"Workers     : {workers or '(n/a)'}")
        print(f"Headless    : {str(Config.HEADLESS).lower()}")
        print()
        print("=" * 45)
        return
    print("=" * 40)
    print(" CPaaS Automation Configuration")
    print("=" * 40)
    print()
    print(f"Environment : {Config.ENV}")
    print(f"Instance    : {Config.INSTANCE or '(none)'}")
    print(f"Base URL    : {Config.BASE_URL or '(not set)'}")
    print()


def _print_show():
    """--show: print every resolved Config attribute, masking secrets by
    NAME (utils.config.is_secret_name/mask_value) -- never a real
    credential, token, or other secret value, regardless of what's
    actually configured."""
    print("-" * 40)
    print(" Resolved configuration (secrets masked)")
    print("-" * 40)
    for name in sorted(vars(Config)):
        if name.startswith("_"):
            continue
        value = getattr(Config, name)
        if callable(value):
            continue
        print(f"{name:28s} = {mask_value(name, value)!r}")
    print("-" * 40)


def main(argv=None) -> int:
    """`argv`: explicit arg list (e.g. [] or ["--show"]) -- used by
    scripts/run_tests.py, which calls this in-process and must NOT let
    this parser see run_tests.py's own forwarded pytest arguments
    (sys.argv). Standalone CLI use (`python scripts/validate_config.py`)
    leaves this as None, which argparse resolves to the real sys.argv[1:]
    as usual."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--show",
        action="store_true",
        help="Also print every resolved (non-secret) configuration value.",
    )
    parser.add_argument("--channel", default=None, help="Display-only, for the CI banner (e.g. 'sms').")
    parser.add_argument("--test-type", default=None, help="Display-only, for the CI banner (e.g. 'smoke').")
    parser.add_argument("--workers", default=None, help="Display-only, for the CI banner.")
    args = parser.parse_args(argv)

    _print_banner()
    passed, errors, warnings = validate()
    _print_banner(channel=args.channel, test_type=args.test_type, workers=args.workers)
    for w in warnings:
        print(f"WARNING: {w}")
    if warnings:
        print()

    if passed:
        print("Configuration validation: PASSED")
        print("=" * 40)
        if args.show:
            print()
            _print_show()
        return 0

    print("Configuration validation: FAILED")
    print()
    print(f"Environment : {Config.ENV}")
    print(f"Instance    : {Config.INSTANCE or '(none)'}")
    print()
    for e in errors:
        print(e)
        print()
    print("=" * 40)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
