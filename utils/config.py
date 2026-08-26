"""
Configuration loader for CPaaS+ test automation.

All values come from .env (or real environment variables).
To switch instances: edit .env — no test file changes needed.

Copy .env.example → .env and fill in your values before running.

Environment-based config (ENV=dev|qa|staging): if an ENV var is set and
config/environments/<ENV>.env exists, it is loaded FIRST — then the plain
root .env (if present) is loaded on top without overriding already-set
values, so a developer's local .env can still override an environment
file's placeholders (e.g. real credentials) without editing the environment
file itself. If ENV is unset, behavior is 100% unchanged from before: only
the root .env is loaded, exactly as it always has been.

    ENV=qa pytest tests/sms          # loads config/environments/qa.env
    pytest tests/sms                 # unchanged — loads ./.env only

NOTE (migrated from Selenium suite): BROWSER is no longer read from .env.
pytest-playwright chooses the browser engine via the --browser CLI flag
(chromium / firefox / webkit) — see pytest.ini `addopts` or pass
`--browser firefox` on the command line. HEADLESS is still read from .env
and wired into the `browser_type_launch_args` fixture in conftest.py.
"""
import os
from dotenv import load_dotenv

from utils.parallel import worker_scoped_dir

_ENV_NAME = os.getenv("ENV")
if _ENV_NAME:
    _env_file = os.path.join(
        os.path.dirname(__file__), "..", "config", "environments", f"{_ENV_NAME}.env"
    )
    if os.path.isfile(_env_file):
        load_dotenv(_env_file)

# Root .env always loads too (override=False -- never clobbers a value the
# environment file, or a real OS environment variable, already set).
load_dotenv(override=False)

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
DOWNLOAD_DIR = worker_scoped_dir(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports", "downloads"))
)

# Reports root — screenshots/logs/downloads/html report all live under here.
REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports"))


class Config:
    # ── Environment / tenant ─────────────────────────────────────────────────
    ENV            = os.getenv("ENV", "qa")
    TENANT         = os.getenv("TENANT", "default")
    API_URL        = os.getenv("API_URL", "")
    # Same worker-scoped directory as the module-level DOWNLOAD_DIR constant
    # above (`from utils.config import DOWNLOAD_DIR`, used directly by every
    # download-center page object) -- exposed here too so `Config.DOWNLOAD_DIR`
    # is also valid, matching every other constant's Config.<NAME> convention.
    DOWNLOAD_DIR   = DOWNLOAD_DIR
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

    # ── Login credentials ────────────────────────────────────────────────────
    VALID_EMAIL    = os.getenv("VALID_EMAIL", "")
    VALID_PASSWORD = os.getenv("VALID_PASSWORD", "")

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

    # ── RCS Campaign test data ────────────────────────────────────────────────
    # Visible name of the RCS Agent used when creating a campaign
    RCS_AGENT_NAME = os.getenv("RCS_AGENT_NAME", "agentsim")
