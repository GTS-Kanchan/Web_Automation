"""
Configuration loader for CPaaS+ test automation.

All values come from .env (or real environment variables).
To switch instances: edit .env -- no test file changes needed.

Copy .env.example -> .env and fill in your values before running.

Environment + instance resolution (see README "Environment and Instance
Configuration" for the full write-up). Four layers, highest priority first:

    1. Runtime environment variables (whatever the shell/CI already set)
    2. config/instances/<INSTANCE>.env   -- only when INSTANCE is set
    3. config/environments/<ENV>.env     -- only when ENV is set
    4. root .env
    5. (not a file -- the hardcoded defaults on each Config attribute below)

Each layer is loaded with python-dotenv's override=False, so a layer never
clobbers a value an EARLIER (higher-priority) layer already put into
os.environ -- including a real runtime env var, which was already in
os.environ before any of this module's code runs. Loading order is
therefore INSTANCE file, then ENV file, then root .env: by the time root
.env loads, anything the instance file or the environment file already set
is untouchable by it, and anything the instance file already set is
untouched by the environment file.

    ENV=qa pytest tests/sms                           # loads config/environments/qa.env
    ENV=staging INSTANCE=staging-01 pytest tests/sms  # loads instances/staging-01.env, then environments/staging.env
    pytest tests/sms                                  # unchanged -- loads ./.env only

If INSTANCE is unset, behavior is 100% unchanged from before INSTANCE
existed: no config/instances/ file is ever consulted, and every other
instance-aware default in this module (REPORTS_DIR, DOWNLOAD_DIR, the
auth-state path in utils/auth_state.py) falls back to the exact original,
flat path it always used. INSTANCE is a purely additive, opt-in layer --
see the README's "Environment and Instance Configuration" section for why
this matters: existing local/CI invocations that only ever used ENV (or
nothing at all) must keep working byte-for-byte unchanged.

NOTE (migrated from Selenium suite): BROWSER is no longer read from .env.
pytest-playwright chooses the browser engine via the --browser CLI flag
(chromium / firefox / webkit) -- see pytest.ini `addopts` or pass
`--browser firefox` on the command line. HEADLESS is still read from .env
and wired into the `browser_type_launch_args` fixture in conftest.py.
"""
import os
from dotenv import load_dotenv

from utils.parallel import worker_scoped_dir

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _config_file_path(subdir: str, name: str) -> str:
    return os.path.join(_PROJECT_ROOT, "config", subdir, f"{name}.env")


_ENV_NAME = os.getenv("ENV", "").strip()
_INSTANCE_NAME = os.getenv("INSTANCE", "").strip()

# 1. Instance file (highest-priority FILE, below only real env vars --
#    see the module docstring's resolution order). Unset INSTANCE -> this
#    block never runs, so an INSTANCE-less invocation is untouched by it.
if _INSTANCE_NAME:
    _instance_file = _config_file_path("instances", _INSTANCE_NAME)
    if os.path.isfile(_instance_file):
        load_dotenv(_instance_file)

# 2. Environment file (unchanged from before INSTANCE existed).
if _ENV_NAME:
    _env_file = _config_file_path("environments", _ENV_NAME)
    if os.path.isfile(_env_file):
        load_dotenv(_env_file)

# 3. Root .env always loads too (override=False -- never clobbers a value
#    an earlier, higher-priority layer -- runtime env var, instance file,
#    or environment file -- already set).
load_dotenv(override=False)

# -- Secret masking (section 7 of the Environment and Instance
#    Configuration work) -- used by scripts/validate_config.py's --show
#    and by any other startup/diagnostic print that might otherwise leak a
#    credential. A variable NAME containing any of these substrings
#    (case-insensitive) is treated as secret regardless of its actual
#    value -- this is a name-based allowlist-of-what-to-print, not a
#    value-based heuristic, so it can never be fooled by what a secret
#    happens to look like. --------------------------------------------
_SECRET_NAME_MARKERS = ("PASSWORD", "TOKEN", "SECRET", "KEY", "AUTH", "COOKIE")


def is_secret_name(name: str) -> bool:
    """True if `name` (a Config attribute / env var name) should never have
    its real value printed/logged -- see _SECRET_NAME_MARKERS above."""
    upper = (name or "").upper()
    return any(marker in upper for marker in _SECRET_NAME_MARKERS)


def mask_value(name: str, value):
    """Returns `value` unchanged unless `is_secret_name(name)`, in which
    case a fixed "****" placeholder is returned instead -- never a
    partial/truncated real value, which could still leak something
    useful. Falsy/empty secret values are still masked (as "****"), so
    "is this variable even set" can't be inferred from whether masking
    kicked in."""
    if is_secret_name(name):
        return "****"
    return value


# -- Environment-secret separation ---------------------------------------
# Login credentials and the SMS API token must come from real environment
# variables (a developer's shell / root .env locally, Bitbucket secured
# repository variables in CI) -- NEVER from config/environments/<ENV>.env,
# which is tracked in git (as *.env.example templates) and read by anyone
# with repo access.
#
# One mapping, consulted by BOTH this module's Config.VALID_EMAIL /
# Config.VALID_PASSWORD / Config.SMS_API_TOKEN (used by the UI login flow)
# AND utils/sms_api_config_loader.py's auth_token resolution (used by the
# SMS API/DLR client) -- so there is exactly one place that says "ENV=qa
# means the QA_* variables", and the UI and the API/DLR client can no
# longer silently resolve a DIFFERENT environment's secret from each
# other (the historical "UI=QA, API=dev" risk documented in
# scripts/run_tests.py and scripts/validate_config.py).
#
# Keyed by the UI's ENV value (qa / staging) -- NOT by
# utils/sms_api_config_loader.py's own ENV_NAME (which can legitimately
# differ, e.g. ENV=qa pairs with the verified ENV_NAME=dev -- see that
# loader's docstring). Intentionally only covers the two CI-supported
# environments; an ENV with no entry here (e.g. a local-only ENV=dev) has
# no "required" secrets and falls back to the legacy variable names below.
SECRET_ENV_MAPPING = {
    "qa": {
        "email": "QA_EMAIL",
        "password": "QA_PASSWORD",
        "sms_api_token": "SMS_API_TOKEN_QA",
    },
    "staging": {
        "email": "STAGING_EMAIL",
        "password": "STAGING_PASSWORD",
        "sms_api_token": "SMS_API_TOKEN_STAGING",
    },
}

# What each secret used to be called in config/environments/*.env, before
# this separation. Checked as a fallback ONLY -- after the ENV-mapped
# variable above is tried and found unset -- so an existing developer's
# root .env with a bare VALID_EMAIL/VALID_PASSWORD/SMS_API_TOKEN keeps
# working untouched, and an ENV with no SECRET_ENV_MAPPING entry still has
# a way to supply its secrets locally.
_LEGACY_SECRET_VAR = {
    "email": "VALID_EMAIL",
    "password": "VALID_PASSWORD",
    "sms_api_token": "SMS_API_TOKEN",
}


def required_secret_vars(env: str = None) -> dict:
    """{key: env_var_name} for `env` (default: the active ENV), e.g.
    {"email": "QA_EMAIL", "password": "QA_PASSWORD",
    "sms_api_token": "SMS_API_TOKEN_QA"}. Empty dict for an ENV with no
    SECRET_ENV_MAPPING entry -- nothing is "required" there."""
    env = (env or _ENV_NAME or "qa").strip().lower()
    return dict(SECRET_ENV_MAPPING.get(env, {}))


def resolve_secret(key: str, env: str = None) -> str:
    """Resolves one secret (`key` in "email" / "password" /
    "sms_api_token") for `env` (default: the active ENV). Priority:
      1. The ENV-mapped variable (e.g. QA_EMAIL when ENV=qa) -- the
         Bitbucket secured variable / CI path.
      2. The legacy/generic variable (VALID_EMAIL, VALID_PASSWORD,
         SMS_API_TOKEN) -- local-dev fallback (root .env), and the only
         option for an ENV with no SECRET_ENV_MAPPING entry.
    Never raises and never logs -- returns "" when nothing is set. See
    missing_required_secrets()/validate_required_secrets() for the
    fail-fast check that's actually supposed to catch that."""
    mapped_var = required_secret_vars(env).get(key)
    if mapped_var:
        value = os.getenv(mapped_var, "")
        if value:
            return value
    legacy_var = _LEGACY_SECRET_VAR.get(key)
    if legacy_var:
        return os.getenv(legacy_var, "")
    return ""


def missing_required_secrets(env: str = None) -> list:
    """Names (never values) of required secret variables that are unset
    for `env`, e.g. ["QA_EMAIL", "SMS_API_TOKEN_QA"]. Only checks the
    ENV-mapped variable -- a value present only via the legacy fallback
    still counts as "set" (resolve_secret() would find it), so this never
    reports a false positive for a working local-dev setup. Empty list
    for an ENV with no SECRET_ENV_MAPPING entry."""
    missing = []
    for key, var_name in required_secret_vars(env).items():
        if os.getenv(var_name, "").strip():
            continue
        if os.getenv(_LEGACY_SECRET_VAR.get(key, ""), "").strip():
            continue
        missing.append(var_name)
    return missing


def validate_required_secrets(env: str = None) -> None:
    """Fail-fast check -- raises RuntimeError naming exactly the missing
    variable NAME(S), never a value:
        Missing required secrets for environment 'qa': QA_EMAIL, QA_PASSWORD
    No-op for an ENV with no SECRET_ENV_MAPPING entry (nothing required).
    Deliberately NOT called at this module's import time -- that would
    make importing utils.config (unit tests, any ENV-less/offline
    invocation) fail just because secrets aren't set. Called explicitly
    by scripts/validate_config.py and scripts/ci_preflight.py instead,
    both of which run BEFORE Playwright starts."""
    env = (env or _ENV_NAME or "qa").strip().lower()
    missing = missing_required_secrets(env)
    if missing:
        raise RuntimeError(
            f"Missing required secrets for environment '{env}': " + ", ".join(missing)
        )

# Central download directory — all CSV/XLSX exports land here so tests can
# verify them. Playwright captures each download as an event per action
# (see Helpers.download_via / ContactsPage.export_to_xlsx) rather than
# relying on the browser writing to a fixed OS folder the way the old
# driver_factory.DOWNLOAD_DIR + Chrome prefs/CDP override did — this
# constant is now just the destination `download.save_as()` is pointed at.
#
# Worker-scoped (reports/downloads/<worker_id>/ -- "master" outside of -n,
# so a plain single-process run is unaffected): every download-center page
# object across every channel (sms/rcs/whatsapp/email) falls back to
# `f"..._{int(time.time() * 1000)}..."` for a filename when the app doesn't
# suggest one, and the app's suggested filename itself is frequently a
# fixed name (e.g. "campaign_report.csv") -- neither is unique enough to
# share a single directory once two parallel workers can download a report
# at close to the same instant. Scoping the directory itself per worker
# (here, once, for every consumer of this constant) closes that gap without
# having to touch each page object's own filename logic individually.
# Reports root -- screenshots/logs/downloads/html report all live under
# here. Additive instance-aware scoping: when INSTANCE is unset (every
# invocation that predates this feature, and every plain `pytest`/
# `ENV=<x> pytest` run today), this resolves to EXACTLY the same flat
# "reports/" directory as always -- see the module docstring. Only an
# explicit INSTANCE nests it under reports/<env>/<instance>/[<run-id>]/,
# so staging-01 and staging-02 (or any two instances) never share a
# downloads/screenshots/logs/report directory. <run-id> is only added when
# REPORT_RUN_ID is present in the environment -- scripts/run_tests.py sets
# it once, before pytest (and therefore before any pytest-xdist worker) is
# even launched, so every worker in one run agrees on the same run-id
# folder; a direct `pytest` invocation (no run_tests.py) with INSTANCE set
# still gets full env/instance isolation, just without the extra per-run
# timestamp subfolder (there is no single pre-pytest moment to compute one
# run-id and hand it to every xdist worker without that launcher).
_REPORTS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports"))


def _resolve_reports_dir() -> str:
    if not _INSTANCE_NAME:
        return _REPORTS_ROOT
    env_name = _ENV_NAME or "default"
    run_id = os.environ.get("REPORT_RUN_ID", "").strip()
    parts = [_REPORTS_ROOT, env_name, _INSTANCE_NAME]
    if run_id:
        parts.append(run_id)
    path = os.path.join(*parts)
    os.makedirs(path, exist_ok=True)
    return path


REPORTS_DIR = _resolve_reports_dir()


def _resolve_run_id() -> str:
    """Unique per EXECUTION (not per worker -- requirement #3 of the
    Advanced Reporting work). If REPORT_RUN_ID is already in the
    environment (scripts/run_tests.py sets it, see that module, BEFORE
    pytest/xdist starts), every worker in this run agrees on the same
    value automatically, since they all inherit this process's
    environment. A bare `pytest` / `pytest -n N` invocation with no
    launcher still gets a single, consistent RUN_ID: this module is
    imported once per process, but for `-n N` that import happens here,
    in the controller, BEFORE pytest-xdist spawns any worker subprocess
    (worker processes inherit the environment as it stood at spawn time)
    -- so setting it into os.environ here (not just returning a local
    value) is what makes every worker see the same RUN_ID even without
    scripts/run_tests.py.

    Format: <timestamp>_<git-short-commit> when git info is available,
    else <timestamp>_<random-suffix> (requirement #3's own example:
    "20261007_185600_a81c92d")."""
    existing = os.environ.get("REPORT_RUN_ID", "").strip()
    if existing:
        return existing

    import subprocess
    import time

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    suffix = None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=_PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            suffix = result.stdout.strip() or None
    except Exception:
        suffix = None
    if not suffix:
        import random
        import string
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=7))

    run_id = f"{timestamp}_{suffix}"
    os.environ["REPORT_RUN_ID"] = run_id
    return run_id


RUN_ID = _resolve_run_id()

# Worker-scoped (<REPORTS_DIR>/downloads/<worker_id>/ -- "master" outside
# of -n, so a plain single-process run is unaffected): every download-
# center page object across every channel (sms/rcs/whatsapp/email) falls
# back to `f"..._{int(time.time() * 1000)}..."` for a filename when the
# app doesn't suggest one, and the app's suggested filename itself is
# frequently a fixed name (e.g. "campaign_report.csv") -- neither is
# unique enough to share a single directory once two parallel workers can
# download a report at close to the same instant. Scoping the directory
# itself per worker (here, once, for every consumer of this constant)
# closes that gap without having to touch each page object's own filename
# logic individually.
DOWNLOAD_DIR = worker_scoped_dir(os.path.join(REPORTS_DIR, "downloads"))


class Config:
    # ── Environment / tenant ─────────────────────────────────────────────────
    ENV            = os.getenv("ENV", "qa")
    # Sub-instance within ENV (e.g. "staging-01", "dev-02") -- see
    # config/instances/<INSTANCE>.env and the module docstring's
    # resolution order. Empty string (never None) when unset, matching
    # every other Config attribute's convention.
    INSTANCE       = os.getenv("INSTANCE", "").strip()
    TENANT         = os.getenv("TENANT", "default")
    API_URL        = os.getenv("API_URL", "")
    # DLR receiver base URL for this environment/instance. Additive and
    # independent of utils/sms_api_config_loader.py's own ENV_NAME-keyed
    # `dlr_base_url` (config/sms_api/environments.yaml) -- that system
    # already resolves its own DLR host for the SMS API client and is
    # untouched by this. Config.DLR_URL exists so a config/instances/ or
    # config/environments/ file can also expose a plain DLR_URL for
    # anything that wants it directly from Config rather than going
    # through the YAML-based loader.
    DLR_URL        = os.getenv("DLR_URL", "")
    # Same worker-scoped directory as the module-level DOWNLOAD_DIR constant
    # above (`from utils.config import DOWNLOAD_DIR`, used directly by every
    # download-center page object) -- exposed here too so `Config.DOWNLOAD_DIR`
    # is also valid, matching every other constant's Config.<NAME> convention.
    DOWNLOAD_DIR   = DOWNLOAD_DIR
    # Same instance-aware reports root the module-level REPORTS_DIR
    # constant above resolves to -- exposed as Config.REPORTS_DIR too so
    # other modules (conftest.py, utils/error_monitor.py, utils/logger.py)
    # can nest their own subdirectory under the SAME root consistently.
    REPORTS_DIR    = REPORTS_DIR
    # Advanced Reporting work, requirement #3 -- unique per execution,
    # shared by every worker in this run (see _resolve_run_id() above).
    RUN_ID         = RUN_ID
    # Configurable worker count (requirement: PLAYWRIGHT_WORKERS env var) —
    # read by scripts/run_tests.py to turn into a real `-n`/`--dist` flag
    # when not passed explicitly on the CLI. 0/unset = don't force a value;
    # plain `pytest` (no -n) still runs single-process exactly as before.
    PLAYWRIGHT_WORKERS = os.getenv("PLAYWRIGHT_WORKERS", "")

    # Where the shared single-login Playwright storage_state file lives
    # (see utils/auth_state.py). Every worker/test that needs an
    # authenticated session reuses this same file instead of logging in
    # itself. Read directly from the env by utils/auth_state.py (it needs
    # the value at import time, before Config's own module-level code
    # necessarily runs first in every import order) -- exposed here too so
    # it's discoverable/documented alongside every other .env variable.
    AUTH_STATE_PATH = os.getenv("AUTH_STATE_PATH", "")

    # ── Browser / driver ────────────────────────────────────────────────────
    BASE_URL       = os.getenv("BASE_URL", "https://testqa.gtsstaging.com")
    HEADLESS       = os.getenv("HEADLESS", "false").lower() == "true"
    IMPLICIT_WAIT  = int(os.getenv("IMPLICIT_WAIT", 10))
    EXPLICIT_WAIT  = int(os.getenv("EXPLICIT_WAIT", 20))
    # Playwright timeouts are in milliseconds; Selenium's were in seconds.
    EXPLICIT_WAIT_MS = EXPLICIT_WAIT * 1000
    IMPLICIT_WAIT_MS = IMPLICIT_WAIT * 1000

    # ── Login credentials / SMS API token ───────────────────────────────────
    # Resolved via SECRET_ENV_MAPPING (ENV-mapped Bitbucket/CI variable
    # first, e.g. QA_EMAIL for ENV=qa; falls back to the legacy
    # VALID_EMAIL/VALID_PASSWORD/SMS_API_TOKEN var for local dev or an ENV
    # with no mapping entry) -- see resolve_secret() above. Property
    # names unchanged on purpose: existing test code already reads
    # Config.VALID_EMAIL / Config.VALID_PASSWORD, and must keep working
    # without modification -- only WHERE the value comes from changed.
    VALID_EMAIL    = resolve_secret("email")
    VALID_PASSWORD = resolve_secret("password")
    # New attribute (nothing currently reads Config.SMS_API_TOKEN
    # directly -- utils/sms_api_config_loader.py's auth_token resolution
    # consults it, see that module), exposed here too so it's available
    # through the same Config object as every other setting, and so a
    # future direct consumer doesn't have to re-implement the mapping.
    SMS_API_TOKEN  = resolve_secret("sms_api_token")

    # ── Page URLs (derived) ──────────────────────────────────────────────────
    LOGIN_URL           = f"{BASE_URL}/login"
    FORGOT_PASSWORD_URL = f"{BASE_URL}/forgot-password"
    DASHBOARD_URL       = f"{BASE_URL}/dashboard"

    # ── SMS Campaign test data ───────────────────────────────────────────────
    # Sender ID that exists on this instance (e.g. "DUMMY", "CERFGS", "AM-SMS")
    SMS_SENDER_ID = os.getenv("SMS_SENDER_ID", "DUMMY")

    # Template name used for basic campaign tests (no variables)
    SMS_TEMPLATE_NAME = os.getenv("SMS_TEMPLATE_NAME", "click test - click_test")

    # Template that contains dynamic variables (used in TC_C023 / TC_C024)
    SMS_TEMPLATE_WITH_VARS = os.getenv("SMS_TEMPLATE_WITH_VARS", "newtempdemo")

    # OTP-type template name, for the OTP campaign E2E test
    SMS_OTP_TEMPLATE_NAME = os.getenv("SMS_OTP_TEMPLATE_NAME", "OTP_Test")

    # TRANSACTIONAL template for the "Verify DLR for Transaction SMS Template"
    # test. No default on purpose: the test must fail when .env lacks it.
    SMS_TRANSACTION_TEMPLATE = os.getenv("SMS_TRANSACTION_TEMPLATE", "").strip()
    SMS_TRANSACTION_TEMPLATE_TYPE = os.getenv("SMS_TRANSACTION_TEMPLATE_TYPE", "TRANSACTIONAL").strip()

    # Template for the "Verify DLR and Short URL Click Count" test. No
    # default on purpose: the test must fail when .env lacks it.
    SMS_URL_CLICK_TEMPLATE = os.getenv("SMS_URL_CLICK_TEMPLATE", "").strip()
    SMS_URL_CLICK_TEMPLATE_TYPE = os.getenv("SMS_URL_CLICK_TEMPLATE_TYPE", "TRANSACTIONAL").strip()

    # Phone numbers pasted into "Copy-Paste" import (newline-separated)
    SMS_PASTE_CONTACTS = os.getenv(
        "SMS_PASTE_CONTACTS",
        "919876543210\n919988887777\n919999999999\n919888888888"
    )

    # Short prefix for auto-generated campaign names
    SMS_CAMPAIGN_PREFIX = os.getenv("SMS_CAMPAIGN_PREFIX", "AutoCamp")

    # ── Email Campaign test data ──────────────────────────────────────────────
    # Email Service option value or name on this instance (e.g. "4", "AmazonSES")
    EMAIL_SERVICE = os.getenv("EMAIL_SERVICE", "4")

    # Email template ID or name used for basic campaign tests (no variables)
    EMAIL_TEMPLATE_NAME = os.getenv(
        "EMAIL_TEMPLATE_NAME", "b85d84de-f6b5-4f21-a8e6-70e230a5c9e4"
    )

    # Email template that contains dynamic variables
    EMAIL_TEMPLATE_WITH_VARS = os.getenv(
        "EMAIL_TEMPLATE_WITH_VARS", "b85d84de-f6b5-4f21-a8e6-70e230a5c9e4"
    )

    # Email addresses pasted into "Copy-Paste" import (newline-separated)
    EMAIL_PASTE_CONTACTS = os.getenv(
        "EMAIL_PASTE_CONTACTS",
        "qa1@example.com\nqa2@example.com\nqa3@example.com\nqa4@example.com"
    )

    # Short prefix for auto-generated email campaign names
    EMAIL_CAMPAIGN_PREFIX = os.getenv("EMAIL_CAMPAIGN_PREFIX", "AutoEmailCamp")

    # Default Email Subject line
    EMAIL_SUBJECT = os.getenv("EMAIL_SUBJECT", "QA Automated Subject Line")

    # ── Contacts / Segmentation test data ────────────────────────────────────
    # Valid contact tag names that exist on this instance (comma-separated)
    CONTACT_TAGS = [t.strip() for t in os.getenv("CONTACT_TAGS", "demo,test,campaign").split(",") if t.strip()]

    # Valid segmentation custom-field names that exist on this instance (comma-separated)
    SEGMENT_FIELDS = [f.strip() for f in os.getenv("SEGMENT_FIELDS", "address,education").split(",") if f.strip()]

    # ── WhatsApp Template test data ──────────────────────────────────────────
    # Visible label (or a unique substring of it) of the Sender ID used when
    # creating a WhatsApp template end-to-end -- e.g.
    # "Globe Teleservices Pte. Ltd.". Matched case-insensitively as a
    # substring against the real Sender ID options returned by the app (see
    # WhatsAppTemplateCreatePage.fill_required_base_fields), so a shorter
    # value like "Globe Teleservices" still matches the fuller real label.
    # Falls back to the first available Sender ID option (with a printed
    # warning, never silently) if no option matches -- e.g. a different
    # environment/account where this sender isn't provisioned. Override in
    # .env only if the target instance's confirmed WhatsApp Sender ID differs.
    WHATSAPP_TEMPLATE_SENDER_ID = os.getenv(
        "WHATSAPP_TEMPLATE_SENDER_ID", "Globe Teleservices Pte. Ltd."
    )

    # ── RCS Campaign test data ────────────────────────────────────────────────
    # Visible name of the RCS Agent used when creating a campaign. Shared
    # across every parallel worker (one account, one agent) -- confirmed
    # safe to share: audited every RCS test file that touches this agent
    # (tests/rcs/agent/test_rcs_agent_flow.py and the agent-selection
    # tests in tests/rcs/campaigns/test_rcs_campaign_create_flow.py) and
    # neither pages/rcs/rcs_agent_page.py nor
    # pages/rcs/rcs_campaign_create_page.py exposes a create/edit/delete/
    # save method for an agent -- selection is read-only (a dropdown
    # pick), and the agent list page's Bulk Actions dropdown is only ever
    # opened to assert Export is present, never used to act on a selected
    # row. No per-worker scoping is needed unless a future test starts
    # mutating agent state.
    RCS_AGENT_NAME = os.getenv("RCS_AGENT_NAME", "agentsim")

    # ── RCS Template test data ───────────────────────────────────────────────
    # Visible name of the RCS Agent used when creating a TEMPLATE.
    # Deliberately a SEPARATE variable from RCS_AGENT_NAME above, NOT a
    # reuse of it: every Template Type dropdown option confirmed in
    # pages/rcs/rcs_template_create_page.py and tests/rcs/templates/
    # test_rcs_template_create_flow.py (which options render at all, e.g.
    # "Text Message with Document" vs "Rich Message") was captured live
    # with the agent named "jioagent" selected -- a DIFFERENT agent from
    # RCS_AGENT_NAME's default ("agentsim"). Defaulting this to "jioagent"
    # preserves that confirmed behavior; silently reusing RCS_AGENT_NAME
    # here instead would risk running the whole Template Type-dropdown
    # suite against an agent whose options were never captured in a DOM
    # dump. Override in .env only if you've re-confirmed the Type
    # dropdown's options for the new agent.
    RCS_TEMPLATE_AGENT_NAME = os.getenv("RCS_TEMPLATE_AGENT_NAME", "jioagent")

    # Phone number(s) already in an opted-out state on this instance
    # (comma-separated, e.g. 919876543210,919876543211). Required for the
    # opt-out validation tests (TC156/TC157) -- left empty by default since
    # this project has no seeding utility and spec section 18 forbids
    # hardcoding a real customer/personal number; populate with a real
    # opted-out test number from this instance.
    RCS_OPTOUT_NUMBERS = [n.strip() for n in os.getenv("RCS_OPTOUT_NUMBERS", "").split(",") if n.strip()]

    # Phone number(s) pasted into RCS Campaign's "Copy Paste Numbers"
    # import tab. Same convention as SMS_PASTE_CONTACTS/EMAIL_PASTE_CONTACTS
    # above -- NEWLINE-separated for more than one, using a literal "\n"
    # escape in .env (real newlines don't survive a single-line .env
    # value), unescaped back to real newlines at the point of use (see
    # RCS_PASTE_CONTACTS in tests/rcs/campaigns/test_rcs_campaign_create_flow.py).
    # Defaults to the single number this suite already used inline before
    # it was externalized here; override in .env to point at number(s)
    # valid for this instance.
    RCS_PASTE_CONTACTS = os.getenv("RCS_PASTE_CONTACTS", "919202511257")
