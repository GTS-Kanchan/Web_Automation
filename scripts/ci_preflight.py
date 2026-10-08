
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from utils.config import Config, required_secret_vars, missing_required_secrets  # noqa: E402


def main(argv=None) -> int:
    env = (os.environ.get("ENV") or Config.ENV or "qa").strip().lower()
    required = required_secret_vars(env)

    print("=" * 40)
    print(" CI Pre-flight: required secrets")
    print("=" * 40)
    print(f"Environment : {env}")
    print()

    if not required:
        print(f"[INFO] No required secrets are mapped for environment '{env}'.")
        print(f"       (SECRET_ENV_MAPPING only covers: qa, staging)")
        print("=" * 40)
        return 0

    missing = set(missing_required_secrets(env))
    for _key, var_name in required.items():
        if var_name in missing:
            print(f"[MISSING] {var_name} is not set")
        else:
            print(f"[OK] {var_name} is set")

    print()
    if missing:
        print(f"Pre-flight FAILED -- missing required secrets for environment '{env}':")
        print("    " + ", ".join(sorted(missing)))
        print("=" * 40)
        return 1

    print("Pre-flight PASSED -- all required secrets are present.")
    print("=" * 40)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
