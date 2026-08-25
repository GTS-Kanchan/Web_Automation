#!/usr/bin/env python3
"""
scripts/run_tests.py — cross-platform (Windows/macOS/Linux) launcher that
turns the PLAYWRIGHT_WORKERS / ENV environment variables into real pytest
CLI flags, then execs pytest.

Why this exists (and why it's not a conftest.py hook)
-------------------------------------------------------
pytest-xdist decides whether/how many workers to fork inside its own
`pytest_cmdline_main` hook, which reads `config.option.numprocesses` as
parsed from the raw command line BEFORE any project conftest.py gets a
chance to run. Two conftest.py-hook-based approaches to defaulting `-n`
from an env var were implemented and empirically verified NOT to work
(pytest silently stayed single-process). The only place that reliably
works is here — before pytest even starts parsing arguments.

Usage
-----
    python scripts/run_tests.py tests/sms
    python scripts/run_tests.py tests/sms tests/whatsapp -m smoke
    PLAYWRIGHT_WORKERS=10 python scripts/run_tests.py tests/sms
    ENV=qa PLAYWRIGHT_WORKERS=auto python scripts/run_tests.py
    HEADLESS=false python scripts/run_tests.py tests/sms      # watch it run
    HEADLESS=true python scripts/run_tests.py tests/sms       # default, no UI

PowerShell (two lines, since PowerShell has no VAR=value prefix syntax):
    $env:HEADLESS='false'
    python scripts\run_tests.py tests\sms
  or as one line:
    $env:HEADLESS='false'; python scripts\run_tests.py tests\sms

Anything you pass on the command line is forwarded to pytest as-is; an
explicit -n/--numprocesses or --dist you pass always wins over the env var
defaults below. With no arguments at all, runs the whole suite
(pytest.ini's testpaths=tests already scopes discovery).

HEADLESS itself isn't handled by this script — it's read directly by
utils/config.py -> Config.HEADLESS (from utils/config.py's `load_dotenv`,
override=False), so a shell/CLI-set HEADLESS always wins over whatever
.env has, exactly like PLAYWRIGHT_WORKERS and ENV. This script just prints
the value being used below so it isn't a silent guess. `pytest --headed`
is pytest-playwright's own equivalent (headed only, no env var), and still
works too if you prefer it.
"""
import os
import subprocess
import sys


def main() -> int:
    forwarded = sys.argv[1:]

    has_dash_n = any(
        a == "-n" or a.startswith("-n=") or a.startswith("--numprocesses") for a in forwarded
    )
    has_dist = any(a == "--dist" or a.startswith("--dist=") for a in forwarded)

    extra = []
    if not has_dash_n:
        workers = os.environ.get("PLAYWRIGHT_WORKERS", "")
        if workers:
            extra += ["-n", workers]
            has_dash_n = True

    if has_dash_n and not has_dist:
        # loadscope: keep every test from one module (and therefore every
        # module-scoped "single sequential flow" test file this suite is
        # built on) on ONE worker, in file order. Required for correctness,
        # not just speed — those files rely on state earlier tests in the
        # same file left behind.
        extra += ["--dist", "loadscope"]

    cmd = [sys.executable, "-m", "pytest"] + forwarded + extra
    print(f"[run_tests] ENV={os.environ.get('ENV', '(unset -> qa default)')}  "
          f"PLAYWRIGHT_WORKERS={os.environ.get('PLAYWRIGHT_WORKERS', '(unset)')}  "
          f"HEADLESS={os.environ.get('HEADLESS', '(unset -> .env value used)')}")
    print(f"[run_tests] {' '.join(cmd)}")
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
