#!/usr/bin/env python3
r"""
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

ENV vs ENV_NAME vs INSTANCE (UI environment and API environment are
TWO INDEPENDENT settings -- read this before assuming "dev"/"qa"/
"staging" mean the same thing on both sides)
------------------------------------------------------------------
ENV picks the UI's BASE_URL (utils/config.py loads
config/environments/<ENV>.env on top of .env). ENV_NAME picks the API
client's instance (utils/sms_api_config_loader.py selects a block from
config/sms_api/environments.yaml). These were built independently and
their names do NOT correspond 1:1 to the same real backend -- CONFIRMED
by comparing the actual URLs in both config files:

    UI ENV     UI BASE_URL                             API ENV_NAME   API base_url                             SAME HOST?
    --------   --------------------------------------   ------------   --------------------------------------   ----------
    staging    https://testqa.cpaas.globeteleservices.com  staging     https://testqa.cpaas.globeteleservices.com   YES
    qa         https://testqa.gtsstaging.com               dev         https://testqa.gtsstaging.com                YES
    dev        https://dev.gtsstaging.com                  (none)      no API env targets this host yet             --

CONFIRMED 2026-09-28 by diffing config/environments/*.env against
config/sms_api/environments.yaml directly (an earlier version of this
table had ENV=staging paired with API ENV_NAME=dev, which is WRONG --
ENV_NAME=dev actually hits testqa.gtsstaging.com, a different real host
than ENV=staging's testqa.cpaas.globeteleservices.com; that mismatch is
what INSTANCE_MAP below now avoids). ENV=dev and API ENV_NAME=dev are
also NOT the same instance despite sharing a name -- ENV=dev's UI hits
dev.gtsstaging.com, and no API environment block currently targets that
host at all (API ENV_NAME=dev actually matches UI ENV=qa's host
instead). Re-verify this table against both config files any time either
one changes -- an env file's BASE_URL/base_url can move without the other
side's file being updated to match.

INSTANCE is a single shorthand that sets BOTH ENV and ENV_NAME correctly
for a real, CONFIRMED-matching backend (table above) -- use it instead of
setting ENV/ENV_NAME separately when you want the UI and the APIs to hit
the SAME real instance:

    INSTANCE=staging python scripts/run_tests.py tests/sms   # -> ENV=staging, ENV_NAME=staging
    INSTANCE=qa      python scripts/run_tests.py tests/sms   # -> ENV=qa,      ENV_NAME=dev

    PowerShell:
        $env:INSTANCE='staging'; python scripts\run_tests.py tests\sms

Only "staging" and "qa" are defined in INSTANCE_MAP below, because those
are the only two UI environments with a CONFIRMED matching API
environment today. INSTANCE set to anything else (e.g. "dev",
"production", "malaysia", "testqa") is a hard error, on purpose -- rather
than silently guessing at a pairing that was never verified against a
real URL, this script tells you to either add a real, confirmed block for
that instance to both config/environments/ and
config/sms_api/environments.yaml first, or set ENV / ENV_NAME
independently if you genuinely want the UI and the APIs on two different
backends.

If INSTANCE is not set at all, ENV and ENV_NAME behave exactly as before
-- fully independent, unaffected by anything in this section. An ENV or
ENV_NAME you set explicitly in the shell always wins over whatever
INSTANCE would have set for that one variable (same "explicit wins" rule
this script already applies to -n/--dist/--reruns below).

INSTANCE also now has a SECOND, layered meaning (Environment and Instance
Configuration work): a sub-instance WITHIN an environment, e.g.
"staging-01"/"staging-02", backed by config/instances/<INSTANCE>.env (see
utils/config.py's module docstring for the full resolution order -- that
file is what actually loads it; this script never reads it directly).
These two meanings never collide in practice -- the legacy INSTANCE_MAP
above only recognizes the bare names "staging"/"qa", and every new-style
instance name has a "-NN" suffix -- so this script checks for a matching
config/instances/<INSTANCE>.env FIRST; only if none exists does it fall
back to the legacy INSTANCE_MAP lookup, and only if NEITHER matches is
INSTANCE treated as invalid:

    INSTANCE=staging-01 python scripts/run_tests.py tests/sms   # new-style: matches config/instances/staging-01.env, passed through as-is
    INSTANCE=staging    python scripts/run_tests.py tests/sms   # legacy shorthand: still sets ENV=staging, ENV_NAME=staging exactly as before

A new-style instance name does NOT auto-set ENV -- pass ENV explicitly
alongside it (every example in the README's "Environment and Instance
Configuration" section does this: `ENV=staging INSTANCE=staging-01 ...`),
matching how config/instances/ files are designed to layer on TOP of an
explicitly-chosen environment, not replace choosing one.

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

Automatic one-time rerun of failed tests
-----------------------------------------
Every run through this script gets `--reruns 1` added automatically
(requires the pytest-rerunfailures plugin — see requirements.txt), so a
test that fails its first attempt is retried once, in-process, before the
final report is written. Only the failed test item is re-executed — the
plugin re-runs just that node, not the whole suite — and the FINAL
outcome (last attempt) is what counts toward the pass/fail totals and the
process exit code: a test that fails then passes on rerun is a final
PASS; a test that fails both times is a final FAIL (see pytest-
rerunfailures' own docs for the exact semantics this delegates to). This
is a resilience mechanism for real UI/network flakiness, not a way to
hide a genuinely broken test — every rerun still shows up as a separate
"Rerun" row in the existing HTML report (pytest-html understands
pytest-rerunfailures' rerun outcome natively, no extra flags needed), so
a test that needed a retry is never indistinguishable from one that
passed cleanly on the first try.

Configure the retry count with PYTEST_RERUNS (default 1 when unset):
    PYTEST_RERUNS=0 python scripts/run_tests.py tests/rcs   # disable reruns
    PYTEST_RERUNS=2 python scripts/run_tests.py tests/rcs   # retry up to twice

If you pass --reruns yourself on the command line (directly, or via
--reruns=N), that explicit value is always respected as-is and
PYTEST_RERUNS / the default are not applied — same "explicit CLI flag
wins" rule this script already uses for -n/--dist above. Reruns work the
same way under -n/--dist loadscope as without it: pytest-rerunfailures
reruns a failed item on whichever worker ran it, so parallel execution,
loadscope module-affinity, and everything else in this file are
unaffected.
"""
import os
import subprocess
import sys
import time

# Real, CONFIRMED UI-instance <-> API-instance pairings (see the module
# docstring's "ENV vs ENV_NAME vs INSTANCE" section for the URL evidence).
# Only add an entry here once both sides have been verified to hit the
# SAME real backend -- an unverified guess here would silently send UI
# traffic and API traffic to two different environments while looking
# like a single, consistent setting.
INSTANCE_MAP = {
    "staging": {"ENV": "staging", "ENV_NAME": "staging"},
    "qa": {"ENV": "qa", "ENV_NAME": "dev"},
}


_INSTANCES_DIR = os.path.join(os.path.dirname(__file__), "..", "config", "instances")


def _new_style_instance_file(instance: str) -> str:
    return os.path.join(_INSTANCES_DIR, f"{instance}.env")


def _apply_instance() -> str | None:
    """If INSTANCE is set, resolves it two ways, new-style first (see the
    module docstring's "second meaning" paragraph):

      1. config/instances/<INSTANCE>.env exists -- a new-style
         per-environment sub-instance. Nothing to do here: utils/config.py
         (imported inside the pytest subprocess) loads that file itself
         from the INSTANCE env var it already inherits. Passed through
         unchanged.
      2. Otherwise, falls back to the legacy INSTANCE_MAP shorthand
         exactly as before -- sets ENV / ENV_NAME in os.environ (inherited
         by the pytest subprocess below) for whichever of the two the
         user hasn't ALREADY set explicitly.

    Exits the process with a clear error if INSTANCE matches NEITHER,
    rather than silently proceeding with something that will just fail
    later, deep inside the actual test run. Returns the resolved instance
    name for the diagnostic print line, or None if INSTANCE wasn't set at
    all."""
    instance = os.environ.get("INSTANCE", "").strip()
    if not instance:
        return None
    if os.path.isfile(_new_style_instance_file(instance)):
        return instance
    if instance in INSTANCE_MAP:
        mapping = INSTANCE_MAP[instance]
        for var, value in mapping.items():
            os.environ.setdefault(var, value)
        return instance
    available = sorted(
        n[: -len(".env")] for n in os.listdir(_INSTANCES_DIR) if n.endswith(".env")
    ) if os.path.isdir(_INSTANCES_DIR) else []
    print(
        f"[run_tests] ERROR: INSTANCE={instance!r} matches neither a "
        f"config/instances/{{instance}}.env file (available: {available}) "
        f"nor the legacy INSTANCE_MAP shorthand (available: "
        f"{sorted(INSTANCE_MAP)}). Add a config/instances/{instance}.env "
        f"file, use one of the names above, or set ENV / ENV_NAME "
        f"independently instead of INSTANCE.",
        file=sys.stderr,
    )
    raise SystemExit(2)


def _channel_label(forwarded: list) -> str:
    """Best-effort channel label for the CI banner (CI/CD work,
    requirement #20) -- same derivation as conftest.py's
    _channel_from_args(), kept independent (display-only, never used for
    test SELECTION) so scripts/run_tests.py doesn't have to import
    conftest.py just for a label."""
    paths = [a for a in forwarded if not a.startswith("-")]
    if not paths:
        return "full suite"
    channels = []
    for a in paths:
        norm = a.replace("\\", "/").strip("/")
        parts = norm.split("/")
        if parts[0] == "tests" and len(parts) > 1:
            channels.append(parts[1])
    return "+".join(dict.fromkeys(channels)) if channels else "full suite"


def _test_type_label(forwarded: list) -> str:
    """Best-effort test-type label for the CI banner, read back from the
    `-m` marker expression actually on the forwarded pytest command line
    (never a second selection mechanism -- this only LABELS what pytest's
    own `-m` already selected)."""
    for i, a in enumerate(forwarded):
        if a == "-m" and i + 1 < len(forwarded):
            return forwarded[i + 1]
        if a.startswith("-m="):
            return a[len("-m="):]
        if a.startswith("--markexpr="):
            return a[len("--markexpr="):]
    return "full"


def _validate_config(channel=None, test_type=None, workers=None) -> int:
    """Runs scripts/validate_config.py in-process (same interpreter, same
    already-resolved os.environ) BEFORE pytest/Playwright starts --
    Environment and Instance Configuration work, requirement #11 step 2
    ("Validate configuration") / requirement #4 ("fail fast before
    Playwright starts"). Returns validate_config.main()'s exit code
    (0 = passed) without raising, so the caller decides whether to abort.
    `channel`/`test_type`/`workers` (CI/CD work, requirement #20) are
    forwarded to validate_config's own CI banner, display-only -- never
    seen by its validate() logic, and never let it see run_tests.py's own
    forwarded pytest args."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # scripts/ itself
    import validate_config  # scripts/validate_config.py -- same directory
    argv = []
    if channel is not None:
        argv += ["--channel", channel]
    if test_type is not None:
        argv += ["--test-type", test_type]
    if workers is not None:
        argv += ["--workers", str(workers)]
    return validate_config.main(argv=argv)


def main() -> int:
    instance = _apply_instance()

    # Computed BEFORE validation so the CI banner (requirement #20) can
    # show the real channel/test-type/workers that are about to run --
    # display-only labels, read back from the command line/env exactly as
    # pytest itself will see them; never a second selection mechanism.
    forwarded = sys.argv[1:]
    _channel = _channel_label(forwarded)
    _test_type = _test_type_label(forwarded)
    _workers = os.environ.get("PLAYWRIGHT_WORKERS", "") or None

    # requirement #11 step 1-2: resolve, then validate, BEFORE touching
    # pytest/Playwright at all. A failed validation aborts here with
    # validate_config.py's own FAILED banner already printed -- never
    # launches a browser against a BASE_URL/credentials we already know
    # are wrong/missing.
    validation_exit = _validate_config(channel=_channel, test_type=_test_type, workers=_workers)
    if validation_exit != 0:
        print("[run_tests] Aborting -- configuration validation failed (see above).", file=sys.stderr)
        return validation_exit

    # requirement #9 (env/instance work) + requirement #3 (Advanced
    # Reporting work): a stable run-id, computed ONCE here (before
    # pytest, and therefore before pytest-xdist forks any worker), so
    # every worker in this run agrees on it -- see utils/config.py's
    # _resolve_run_id()/REPORTS_DIR docstrings for why this can't be
    # computed reliably from inside a conftest.py hook instead.
    #
    # REPORT_RUN_ID is now ALWAYS set (every run gets a RUN_ID -- the
    # reporting system's requirement #3 applies regardless of INSTANCE),
    # but `run_id` (the local variable controlling whether REPORTS_DIR
    # nests under reports/<env>/<instance>/<run-id>/) stays INSTANCE-only,
    # exactly as before -- an INSTANCE-less run keeps writing to the same
    # flat reports/ location it always has.
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))  # project root
    from utils.config import Config as _Config  # noqa: E402  (resolves/sets REPORT_RUN_ID as a side effect)
    os.environ.setdefault("REPORT_RUN_ID", _Config.RUN_ID)
    run_id = os.environ["REPORT_RUN_ID"] if instance else None

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

    has_reruns = any(
        a == "--reruns" or a.startswith("--reruns=") for a in forwarded
    )
    reruns_value = None
    if not has_reruns:
        # Unset or empty PYTEST_RERUNS -> default of 1 (see module
        # docstring). Always pass --reruns explicitly (including "0") so
        # the resolved value is visible in the printed command below
        # instead of silently relying on the plugin's own default.
        reruns_value = os.environ.get("PYTEST_RERUNS", "").strip() or "1"
        extra += ["--reruns", reruns_value]

    # requirement #9: explicit --html/--junitxml pointed at the
    # env/instance[/run-id]-scoped reports directory -- overrides
    # pytest.ini's flat `addopts = --html=reports/test_report.html`
    # (confirmed: the LAST --html wins, no conflict) only when INSTANCE is
    # set; otherwise the flat default is left completely alone.
    has_html = any(a == "--html" or a.startswith("--html=") for a in forwarded)
    has_junit = any(a == "--junitxml" or a.startswith("--junitxml=") for a in forwarded)
    if instance and not (has_html and has_junit):
        from utils.config import Config  # import AFTER REPORT_RUN_ID is set, so
        # Config.REPORTS_DIR (computed at import time) already includes it.
        os.makedirs(Config.REPORTS_DIR, exist_ok=True)
        if not has_html:
            extra += ["--html", os.path.join(Config.REPORTS_DIR, "test_report.html"), "--self-contained-html"]
        if not has_junit:
            extra += ["--junitxml", os.path.join(Config.REPORTS_DIR, "junit.xml")]

    cmd = [sys.executable, "-m", "pytest"] + forwarded + extra
    print(f"[run_tests] INSTANCE={instance if instance else '(unset -> ENV/ENV_NAME independent)'}  "
          f"ENV={os.environ.get('ENV', '(unset -> qa default)')}  "
          f"ENV_NAME={os.environ.get('ENV_NAME', '(unset -> environments.yaml active_environment default)')}  "
          f"PLAYWRIGHT_WORKERS={os.environ.get('PLAYWRIGHT_WORKERS', '(unset)')}  "
          f"HEADLESS={os.environ.get('HEADLESS', '(unset -> .env value used)')}  "
          f"RERUNS={reruns_value if reruns_value is not None else '(explicit --reruns on command line)'}  "
          f"RUN_ID={run_id if run_id else '(n/a -- no INSTANCE)'}")
    print(f"[run_tests] {' '.join(cmd)}")
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
