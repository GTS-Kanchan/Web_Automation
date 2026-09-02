# CPaaS+ Playwright Test Automation

**Status: conversion complete.** This folder is the full Selenium →
Playwright migration of `cpaas_selenium_tests/`. Every suite from the
original Selenium project has been converted: the framework core (config,
page-object base classes, helpers, error monitor, HTML reporting) plus all
functional modules — **Login, Dashboard, Forgot Password, SMS, RCS,
WhatsApp, Email, Contacts, Segmentation, Tags, and Communication Flow**.

The converted suite currently totals **62 page objects** and **64 test
files** (**1,939 tests**), all collecting cleanly under
`pytest --collect-only` with the original `smoke` / `regression` /
`negative` markers intact. The "Project structure" and "Coverage"
sections below reflect the current, channel-based file locations; see
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full migration
history and rationale.

Playwright + pytest (`pytest-playwright`), same Page Object Model layout,
same pytest markers (`smoke` / `regression` / `negative`) and the same
custom HTML report (pass-rate banner, marker badges, colour-coded
durations, screenshot-on-failure, platform error monitor) as the original
Selenium suite.

---

## Channel-based architecture (new)

The suite has been fully reorganized into a scalable, channel-based
architecture that supports parallel execution across SMS/WhatsApp/RCS/Email
and makes adding a future channel low-risk. **Every suite is migrated:**
`tests/sms/`+`pages/sms/`, `tests/rcs/`+`pages/rcs/`,
`tests/whatsapp/`+`pages/whatsapp/`, `tests/email/`+`pages/email/`, and the
common/cross-channel suites at `tests/common/`+`pages/common/` (login,
dashboard, forgot password, contacts, segmentation, tags) — each organized
into feature subfolders (campaigns, templates, reports, etc.) with
`pytestmark` channel/feature tags. The suite totals **1,939 tests**
(common 74, SMS 643, RCS 682, WhatsApp 402, Email 136 — 1,937 across
those five folders, plus 2 pre-existing `test_temp_dump*.py` scratch/debug
files at the `tests/` root that predate this migration and are unrelated
to it). All five counts above are from a real `pytest --collect-only`
run against this working tree, not estimates.

Supporting the channel structure are a `channels/` package (a
`BaseChannel`/`SMSChannel`/`RCSChannel`/`WhatsAppChannel`/`EmailChannel`
abstraction used for worker-safe unique test-data names, e.g.
`SMSChannel.unique_campaign_name()`), `fixtures/` (per-channel pytest
plugins registered in `conftest.py` — `sms_fixtures.py`,
`rcs_fixtures.py`, etc.), `config/environments/` (`dev.env`/`qa.env`/
`staging.env`, selected via `ENV=<name>`), and an `api/` scaffold
(`BaseApiClient` plus empty per-channel packages, not yet filled in). See
the "Project structure" section below for the full tree.

The old flat file locations (`pages/sms_*.py`, `tests/test_rcs_*.py`,
etc.) no longer exist in this folder — the migration's re-export
shims/stub files have already been removed, so
`cleanup_old_flat_duplicates.bat` and `cleanup_common_flat_duplicates.bat`
have nothing left to do if run again; they're kept only as a record of
that cleanup step.

Full details, the exact commands for parallel/channel/marker execution,
and the full migration history: see
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). To add a new channel:
[`docs/ADDING_A_CHANNEL.md`](docs/ADDING_A_CHANNEL.md).

---

## Parallel execution architecture

This suite runs against **one shared platform account**. The app blocks/
rate-limits repeated login attempts within a short window (~5 minutes), so
the suite performs the real login **exactly once per run**, no matter how
many parallel workers are used, and every worker/test reuses that one
session instead of logging in itself:

```text
                 SINGLE PLATFORM ACCOUNT
                           │
                           ↓
                      LOGIN ONCE
                           │
                           ↓
                 AUTHENTICATION STATE
                    (storage_state)
                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
       Worker 1         Worker 2         Worker 3
          │                │                │
          ↓                ↓                ↓
         SMS            WhatsApp           RCS
          │                │                │
          └────────────────┼────────────────┘
                           ↓
                         Email
```

**How the "login once" guarantee actually holds under `-n N`:** pytest-xdist
runs each worker as a separate OS process, so a plain per-test or
session-scoped fixture is only "once per worker", not "once per run" — with
10 workers that's still 10 logins. `utils/auth_state.py` closes that gap
with a cross-process file lock: whichever worker/test reaches
`ensure_authenticated_state()` first performs the one real UI login and
saves a Playwright `storage_state` file; every other caller — same worker
later, or any other worker at any time — either finds the file already
there or briefly waits on the lock and then reuses it. Nobody else ever
calls the login page. `conftest.py`'s `logged_in_page` / `module_logged_in_page`
fixtures (used by the vast majority of the suite — see "Coverage" below)
are built on this directly, so **no existing test file had to change** to
get this behavior.

Full design (the file lock, session-expiry re-authentication, failure
handling, why a plain "delete then relogin" approach isn't safe under
concurrency): see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#authentication-architecture).

### Authentication state

The shared session lives at `reports/.auth/state.json` by default
(override with `AUTH_STATE_PATH` in `.env`). It contains live session
cookies for `VALID_EMAIL`/`VALID_PASSWORD` — **never commit it**;
`reports/.auth/` is in `.gitignore`. It's an on-disk cache, not a secret
you configure: delete it (or the whole `reports/.auth/` folder) any time
to force a clean login on the next run; leaving it in place between runs
is intentional and lets a second `pytest` invocation skip the login
entirely as long as the session is still valid.

`tests/common/test_login.py` and `test_forgot_password.py` are the one
deliberate exception — they exercise the login form itself (including
invalid-credential/empty-field negative cases), so their fixtures
(`login_page`, plain `page`) are never pre-authenticated from this state.

### Worker configuration

```bash
pytest tests/sms                                       # single worker (default, unchanged)
PLAYWRIGHT_WORKERS=5  python scripts/run_tests.py tests/sms   # 5 workers
PLAYWRIGHT_WORKERS=10 python scripts/run_tests.py              # 10 workers, full suite
PLAYWRIGHT_WORKERS=20 python scripts/run_tests.py tests/sms tests/rcs
```

`scripts/run_tests.py` turns `PLAYWRIGHT_WORKERS` into pytest-xdist's
`-n`/`--dist loadscope` flags (see the script's own docstring for why this
can't be done from inside `conftest.py`). `--dist loadscope` keeps every
test from one module on the same worker — required because most existing
files are module-scoped "single sequential flow" suites where later tests
depend on state earlier tests in the *same file* left behind (see
"Coverage" below), not just a performance choice. Calling
`pytest -n <N> --dist loadscope` directly still works exactly the same;
the env var is purely a convenience.

Pick a worker count for your machine/CI runner, not the other way around
— nothing here auto-scales to a large number. Start small (5), confirm
things are stable, then raise it; a developer laptop and a CI runner
rarely tolerate the same count (CPU/RAM for N browser processes, and the
target app's own response time/rate limits under N concurrent sessions).

### Test-data isolation

Every worker shares the same account, so test data must never collide.
`utils/parallel.py` provides the building blocks used throughout the
suite:

- `unique_name(prefix)` / `unique_suffix()` — `<ms-epoch>_<worker>_<counter>_<random>`,
  used by `channels/*.py`'s `unique_campaign_name()`/`unique_template_name()`/`unique(label)`
  and directly in several test files.
- `short_unique_tag()` / `short_unique_digits()` — the same idea, compact,
  for the handful of fields with a tight hand-tuned character budget
  (e.g. RCS template/campaign names) or that must look like a phone
  number.
- `worker_scoped_dir(base_dir)` — `base_dir/<worker_id>/`, used for
  screenshots, logs, and downloads (`utils.config.DOWNLOAD_DIR` is
  worker-scoped at the source, so every download-center page object gets
  this for free) so two workers writing a same-named file never collide.

`worker_id()` returns `"master"` outside of `-n`, so none of this changes
behavior for a plain single-process run.

### Troubleshooting login restrictions

- **A test fails with `AuthenticationError`** — the one real login attempt
  itself failed (bad credentials, unexpected redirect, etc.). This is
  reported once, clearly, as a fixture-setup error on every dependent
  test — by design, no test retries the login on its own (that would be
  the exact login storm this architecture exists to prevent). Fix the
  root cause (usually `.env` credentials or the app being unreachable) and
  rerun.
- **You suspect the 5-minute lockout was triggered anyway** — check
  `reports/logs/<worker>.jsonl` and the `[AUTH]` lines on stderr for how
  many real login attempts actually happened; there should be exactly
  one. If you deliberately want a clean login (e.g. after changing
  `.env` credentials), delete `reports/.auth/` first rather than waiting
  out the lockout.
- **A worker seems stuck at startup** — another worker is mid-login and
  holding the lock; this resolves itself once that login finishes
  (normally seconds, not minutes). A lock file older than a few minutes is
  treated as abandoned and cleared automatically.

### CI/CD parallel execution

```yaml
env:
  ENV: staging
  PLAYWRIGHT_WORKERS: 8
  VALID_EMAIL: ${{ secrets.QA_EMAIL }}
  VALID_PASSWORD: ${{ secrets.QA_PASSWORD }}
steps:
  - run: pip install -r requirements.txt
  - run: python -m playwright install --with-deps chromium
  - run: python scripts/run_tests.py -m smoke
  - uses: actions/upload-artifact@v4
    if: always()
    with: { name: test-report, path: reports/ }
```

Never commit real credentials or `reports/.auth/` — set them as CI
secrets/variables, same as `.env` locally.

---

## What changed vs. the Selenium suite

| Selenium suite | Playwright suite | Why |
|---|---|---|
| `driver` fixture (Selenium `WebDriver`) | `page` fixture (built into `pytest-playwright`) | Playwright's own plugin already manages browser/context/page lifecycle per test |
| `utils/driver_factory.py` (ChromeOptions/FirefoxOptions) | `browser_type_launch_args` / `browser_context_args` fixtures in `conftest.py` | Same configuration surface, Playwright-native |
| `BROWSER=chrome` in `.env` | `--browser chromium\|firefox\|webkit` CLI flag (set in `pytest.ini` `addopts`) | pytest-playwright's own convention; `.env` no longer controls the engine |
| `HEADLESS=true/false` in `.env` | Same — still read from `.env`, wired into `browser_type_launch_args` | Unchanged |
| Locators as `(By.CSS_SELECTOR, "...")` tuples | Locators as plain selector strings, `"xpath=..."` prefix for XPath | Playwright's `page.locator()` API |
| `element.text` | `locator.inner_text()` | Matches Selenium's "visible rendered text" semantics (`text_content()` would include hidden text) |
| Manual `WebDriverWait` / `StaleElementReferenceException` retry loops | Playwright's auto-waiting + auto-retrying locators | Playwright locators re-resolve the DOM on every call, so most of the old retry code is now redundant (kept as defensive fallback in `base_page.py`, see comments there) |
| Chrome download-directory prefs + CDP override | `Helpers.download_via()` using `page.expect_download()` | Playwright captures downloads as events per action instead of writing to a fixed browser download folder |
| `import time; time.sleep(n)` | Kept as `page.wait_for_timeout(n)` for now | These were already fixed sleeps in the original suite (not proper waits) — ported 1:1 for behavioral parity in this pilot; worth replacing with `expect(...).to_have_...()` polling assertions in a follow-up pass now that Playwright makes that easy |

Everything else — test IDs, assertions, pytest markers, folder layout,
`.env` variable names (aside from `BROWSER`) — is unchanged, so existing
CI invocations like `pytest -v -m smoke` or `pytest -v -k "TC_C021"` keep
working the same way once pointed at this folder.

---

## Setup

### 1. Install dependencies

```bash
cd cpaas_playwright_tests
pip install -r requirements.txt
playwright install          # downloads the Chromium/Firefox/WebKit browser binaries
```

### 2. Create `.env`

```bash
copy .env.example .env        # Windows
# or
cp .env.example .env          # Mac/Linux
```

Fill in `VALID_EMAIL` / `VALID_PASSWORD` and any test-data variables you
already use in the Selenium suite's `.env` — the variable names are the
same (see the table above for the one exception, `BROWSER`).

---

## Running tests

```bash
# All tests (full suite — 1,939 tests)
pytest

# A single channel, e.g. SMS
pytest tests/sms

# A single suite, e.g. Login
pytest tests/common/test_login.py

# Smoke tests only (fast)
pytest -m smoke

# Regression tests only
pytest -m regression

# Specific test by name
pytest -k "test_valid_credentials_redirect"

# Stop on first failure
pytest -x

# Run against Firefox or WebKit instead of Chromium
pytest --browser firefox
pytest --browser webkit

# Run against all three engines in one go
pytest --browser chromium --browser firefox --browser webkit
```

### Parallel execution (multiple workers, one shared account)

**Recommended: warm the session once before scaling out to workers.**
`scripts/warm_auth.py` performs the one real login *up front*, single
process, before any `-n` workers exist — so by the time they start,
`reports/.auth/state.json` already exists and every worker takes the
fast, zero-contention path with no login of its own. This isn't required
for correctness (the file lock in `utils/auth_state.py` already guarantees
at most one real login no matter how many workers start cold), but it
removes the race window for that run entirely and gives you one
unambiguous checkpoint — if the account is locked out or `.env`
credentials are wrong, you find out in seconds instead of after N workers
have all queued up:

```bash
python scripts/warm_auth.py            # log in once; reuses a cached session if one exists
python scripts/warm_auth.py --fresh    # force a clean login (clears any stale state/lock/failure marker first)
```

Then run the parallel suite as normal — nothing else changes:

```bash
# 5 workers — good starting point on a laptop
python scripts/warm_auth.py && pytest -n 5 --dist loadscope
PLAYWRIGHT_WORKERS=5 python scripts/run_tests.py

# 10 workers — full suite
python scripts/warm_auth.py && pytest -n 10 --dist loadscope
PLAYWRIGHT_WORKERS=10 python scripts/run_tests.py

# 20 workers — CI runner with enough CPU/RAM for 20 browser processes
python scripts/warm_auth.py && pytest -n 20 --dist loadscope tests/sms tests/rcs
PLAYWRIGHT_WORKERS=20 python scripts/run_tests.py tests/sms tests/rcs
```

`--dist loadscope` is required, not optional, whenever you pass `-n`
directly instead of going through `scripts/run_tests.py` (which adds it
for you) — see "Worker configuration" and "Coverage" above for why.
All workers authenticate against the *same* CPaaS+ account through the
shared, file-locked `storage_state` described in "Parallel execution
architecture" above, so raising `-n`/`PLAYWRIGHT_WORKERS` never multiplies
login attempts. See the "Channel-based architecture" section above for
channel/marker commands (`pytest tests/<channel>`, `pytest -m <channel>`).

**If you ever see more than one real login happen** (multiple `[AUTH]
Starting authentication` lines on stderr for one run), that's not expected
behavior — see "Troubleshooting login restrictions" above, and check for a
leftover `reports/.auth/state.json.lock` file from a previous crashed run
(a lock older than a few minutes is auto-cleared, but if you want to rule
it out immediately, delete `reports/.auth/` and rerun `warm_auth.py`
alone first).

### Headless vs. headed

Controlled by `HEADLESS=true`/`false`, read from `.env` by default but
overridable per-run without editing that file — a shell/CLI-set
`HEADLESS` always wins over `.env` (same override rule `PLAYWRIGHT_WORKERS`
and `ENV` follow):

```bash
HEADLESS=false pytest tests/sms          # watch the browser
HEADLESS=true pytest tests/sms           # no UI (also .env's default)
HEADLESS=false python scripts/run_tests.py tests/sms   # headed + parallel
```

PowerShell (two lines, or `;` to combine on one):
```powershell
$env:HEADLESS='false'
pytest tests\sms
```

pytest-playwright's own `--headed` flag is a simpler alternative when you
just want to watch a run once and don't need it configurable per-CI-job:
```bash
pytest tests/sms --headed
```

---

## HTML Report

After every run, open:
```
reports/test_report.html
```
Same layout as the Selenium suite's report: pass-rate banner, marker
badges, colour-coded durations, and an embedded screenshot on every
failure (plus a red banner if the platform error monitor detects a
500/Whoops/Livewire-exception page during the run).

---

## Project structure

```
cpaas_playwright_tests/
├── conftest.py                     # Playwright fixtures, HTML report hooks, plugin
│                                    #   registration (fixtures/*.py), logged_in_page /
│                                    #   module_logged_in_page fixtures
├── pytest.ini                      # smoke/regression/negative + channel/feature markers
├── requirements.txt
├── .env.example
│
├── config/
│   └── environments/                # dev.env / qa.env / staging.env — selected via ENV=<name>
│
├── channels/                        # BaseChannel + one subclass per channel (SMS/RCS/
│   │                                 #   WhatsApp/Email) — worker-safe unique test-data
│   │                                 #   names (e.g. unique_campaign_name()) used by the
│   │                                 #   parallel-safe example tests below
│   └── fixture_factory.py           # module_page_fixture() helper for new/migrated files
│
├── fixtures/                        # Per-channel pytest plugins, registered in conftest.py
│   ├── common_fixtures.py           #   correlation_id, test_logger, etc.
│   └── sms_fixtures.py / rcs_fixtures.py / whatsapp_fixtures.py / email_fixtures.py
│
├── api/                             # Scaffold only: BaseApiClient (Playwright
│                                     #   APIRequestContext) plus empty per-channel
│                                     #   packages, not yet filled in
│
├── constants/
│   ├── tags.py                      # Marker-name constants, mirrors pytest.ini
│   ├── sms_download_headers.py      # EXPECTED_SMS_DOWNLOAD_HEADERS — single source of
│   │                                 #   truth for the SMS Download Center's 20 export headers
│   ├── sms_template_headers.py      # EXPECTED_SMS_TEMPLATE_HEADERS — single source of
│   │                                 #   truth for the SMS Template list's 8 export headers
│   ├── sms_sender_id_headers.py     # EXPECTED_SMS_SENDER_ID_HEADERS — single source of
│   │                                 #   truth for the SMS Sender ID list's 9 export headers
│   ├── sms_message_headers.py       # EXPECTED_SMS_MESSAGE_HEADERS — single source of
│   │                                 #   truth for the SMS Messages list's 18 export headers
│   ├── sms_incoming_messages_headers.py  # EXPECTED_SMS_INCOMING_MESSAGES_HEADERS — single
│   │                                 #   source of truth for the SMS Incoming Messages
│   │                                 #   export's 7 headers
│   ├── sms_blocked_numbers_headers.py    # EXPECTED_SMS_BLOCKED_NUMBERS_HEADERS — single
│   │                                 #   source of truth for the SMS Blocked Numbers
│   │                                 #   export's 5 headers
│   ├── sms_usage_report_headers.py       # EXPECTED_SMS_USAGE_REPORT_HEADERS — single
│   │                                 #   source of truth for the SMS Usage Report
│   │                                 #   export's 18 headers
│   ├── sms_campaign_report_headers.py    # EXPECTED_SMS_CAMPAIGN_REPORT_HEADERS — 20 headers
│   ├── sms_status_report_headers.py      # EXPECTED_SMS_STATUS_REPORT_HEADERS — 7 headers
│   ├── sms_error_code_report_headers.py  # EXPECTED_SMS_ERROR_CODE_REPORT_HEADERS — 7 headers
│   ├── sms_sender_report_headers.py      # EXPECTED_SMS_SENDER_REPORT_HEADERS — 19 headers
│   ├── sms_template_report_headers.py    # EXPECTED_SMS_TEMPLATE_REPORT_HEADERS — 20 headers
│   ├── sms_country_report_headers.py     # EXPECTED_SMS_COUNTRY_REPORT_HEADERS — 20 headers
│   ├── sms_latency_report_headers.py     # EXPECTED_SMS_LATENCY_REPORT_HEADERS — 12 headers
│   └── rcs_campaign_headers.py      # EXPECTED_RCS_CAMPAIGN_HEADERS — single source of
│                                     #   truth for the RCS Campaign list's 21 export headers
│
├── pages/                           # 62 page objects (POM), channel-based layout
│   ├── common/                      # 8 files — base_page.py (shared BasePage superclass),
│   │                                 #   login/dashboard/forgot_password (3),
│   │                                 #   contacts/segmentation/tags/communication_flow (4)
│   ├── sms/                         # 18 files
│   ├── rcs/                         # 19 files
│   ├── whatsapp/                    # 12 files
│   └── email/                       # 5 files
│
├── tests/                           # 64 test files, 1,939 tests total
│   ├── common/                      # 6 files — test_login, test_dashboard,
│   │                                 #   test_forgot_password, test_contacts_flow,
│   │                                 #   test_segmentation_flow, test_tags_flow
│   │                                 #   (no dedicated Communication Flow test — see
│   │                                 #   pages/common/communication_flow_page.py's own
│   │                                 #   docstring)
│   ├── sms/                         # 20 files across campaigns/ messaging/ opt_out/
│   │                                 #   reports/ sender_id/ templates/ — includes
│   │                                 #   test_campaign_creation.py and the
│   │                                 #   parallel-execution reference example,
│   │                                 #   test_sms_parallel_example_flow.py
│   ├── rcs/                         # 19 files across agent/ campaigns/ messaging/
│   │                                 #   opt_out/ reports/ templates/
│   ├── whatsapp/                    # 12 files across opt_out/ reports/
│   ├── email/                       # 5 files across campaigns/ reports/ templates/
│   ├── test_data/                   # Generated test-data files (xlsx/csv), written with
│   │                                 #   an atomic write-to-temp-then-replace pattern so
│   │                                 #   parallel workers never collide on the same file
│   ├── unit/                        # Browser-free unit tests, e.g. test_file_validator.py
│   └── test_temp_dump.py / test_temp_dump_modal.py
│                                     #   2 pre-existing scratch/debug files, unrelated to
│                                     #   the channel migration
│
├── utils/
│   ├── config.py                    # Reads .env — same variables as the Selenium suite (minus BROWSER)
│   ├── helpers.py                   # Playwright-native wait/screenshot/download helpers
│   ├── error_monitor.py             # Platform error detection (500s, Whoops, Livewire errors, etc.)
│   ├── parallel.py                  # unique_name() — worker-safe, collision-resistant test-data names
│   ├── logger.py                    # Structured/correlation-id-aware logging
│   ├── file_validator.py            # validate_file_headers() — downloaded-file header
│   │                                 #   validation (CSV/xlsx/xls), no Playwright/pytest dependency
│   └── test_data_generator.py       # Generates the files under tests/test_data/
│
├── scripts/
│   └── run_tests.py                 # PLAYWRIGHT_WORKERS/ENV -> real pytest -n/--dist flags (see below)
│
└── reports/                         # HTML report + screenshots after each run
```

---

## Downloaded File Header Validation

The SMS Download Center test (`tests/sms/reports/test_sms_download_center_flow.py`,
`TestTC10Download::test_tc10_download_initiates`) validates that a
downloaded report's file headers exactly match a predefined specification —
in addition to (and using the same download mechanism as) the existing
"did a file download at all" check.

```
Download
   ↓
Read CSV/Excel
   ↓
Extract headers
   ↓
Exact comparison
   ↓
PASS / FAIL
```

Scope (phase 1): **headers only**. Row data, values, data types, record
counts, and business logic are NOT validated by this check. SMS (11
exports) and RCS (the Campaign list export) are covered — WhatsApp/Email
are not implemented yet. The RCS export is documented in full, alongside
the rest of the RCS channel, in the ["RCS Channel"](#rcs-channel) section
below rather than repeated here.

**Single source of truth for expected headers:**
[`constants/sms_download_headers.py`](constants/sms_download_headers.py) —
`EXPECTED_SMS_DOWNLOAD_HEADERS`, the 20 SMS Download Center column names in
the exact order the export must contain them.

**Validator:** [`utils/file_validator.py`](utils/file_validator.py) —
`validate_file_headers(file_path, expected_headers)`. Reads only the
header row (via the stdlib `csv` module for `.csv`, `openpyxl` for
`.xlsx`, `xlrd` for legacy `.xls`) and compares it against
`expected_headers` name-for-name and position-for-position — capitalization
and spacing are part of the comparison and are never normalized. The
function has no Playwright/pytest dependency, so it can be unit-tested
without a browser: see `tests/unit/test_file_validator.py`
(`pytest tests/unit/test_file_validator.py -v`).

The live SMS Download Center export is a **`.zip`** wrapping the actual
`.csv`/`.xlsx`/`.xls` report (confirmed from a real failing run —
`report.zip` containing an `.xlsx`, not a bare `.xlsx`). `validate_file_headers`
handles this transparently: a `.zip` is unzipped in memory/temp, the one
report entry inside is located and read, and everything downstream
(comparison, error messages) behaves exactly as if that file had been
downloaded directly. A `.zip` with no `.csv`/`.xlsx`/`.xls` entry inside is
still reported as `UnsupportedFileTypeError`, distinct from a header
mismatch.

**Also validated: SMS Template list export.** The same generic validator
covers a second real export — `tests/sms/templates/test_sms_template.py`,
`TestExportTemplateList::test_export_template_list_headers` — using
[`constants/sms_template_headers.py`](constants/sms_template_headers.py)'s
`EXPECTED_SMS_TEMPLATE_HEADERS` (8 columns: DLT Template Id, Template Name,
Sender Id, Content, Status, Product, Short URL, Created At). This also
fixed `SMSTemplatePage.export_to_xlsx()`, which previously clicked the
Export option and discarded the download — it now captures it via
`page.expect_download()` (mirroring `ContactsPage.export_to_xlsx()`) and
returns the saved file path. Its `MENU_EXPORT` locator also needed a real
fix: `@wire:click='export'` is invalid XPath (the colon is parsed as an
undeclared namespace prefix, which silently fails the *entire* expression,
including the `contains(.,'Export')` fallback in the same union) — the
correct form, already used elsewhere in this codebase
(`pages/rcs/*_analytics_page.py`), is `@*[name()='wire:click']='export'`.

**Also validated: SMS Sender ID export.** A third real export —
`tests/sms/sender_id/test_sms_sender_id.py`,
`TestExportSenderIds::test_export_csv` (this test already existed for the
download-SLA check; header validation was added to it rather than
duplicating a new test) — using
[`constants/sms_sender_id_headers.py`](constants/sms_sender_id_headers.py)'s
`EXPECTED_SMS_SENDER_ID_HEADERS` (9 columns: Sender Id, Department, User,
Status, Type, Entity Id, Country code, Created At, Updated At).
`SMSSenderIDPage.export_csv()` has a background-job fallback path (the
export queues instead of downloading directly) — when that path is taken
there's no file to validate, so the test skips rather than fails.

**Also validated: SMS Messages export.** A fourth real export —
`tests/sms/messaging/test_sms_message_flow.py`,
`test_TC020B_export_headers_today` — using
[`constants/sms_message_headers.py`](constants/sms_message_headers.py)'s
`EXPECTED_SMS_MESSAGE_HEADERS` (18 columns: Mobile Number, Country Code,
Sender ID, DLT Template ID, Entity ID, Status, Correlation ID, Message Id,
SMS Count, Source, Sub-Source, Type, Product, Received At, Submitted At,
DLR Received At, Message Content, Status Description). The message log can
be large, so this test narrows the date-range filter before exporting — it
only cares about the header row, not export volume.

This was originally attempted as a 1-hour window, but the real Messages
date filter turned out to be a native `<input type="date">`
(`x-model="date"`, `x-on:change="updateDateTime()"`) with no time-of-day
component anywhere in the DOM — confirmed both from the live widget's
markup and from the app's own "Applied Filters" chips, which always show
`00:00:00`–`23:59:00` day boundaries no matter what value is assigned.
Assigning a full datetime string gets silently truncated by the browser to
just the date portion. The finest granularity actually available through
this UI is a single calendar day (`from_date == to_date`), so the test
narrows to "today" as the closest honest equivalent of "keep the export
small" that the real filter supports. `SMSMessagePage.set_filter_date_range()`
sets the real `<input>` elements directly (`.value` + dispatched
`input`/`change` events, mirroring `SMSReportCreatePage._set_date_input()`)
rather than only reflecting into Livewire component state, and strips any
time suffix before assignment. A `diagnose_date_filter()` helper prints the
from/to input's match count, visibility, value, and outerHTML snippet
unconditionally, for evidence if the applied filter ever needs re-checking
against a UI change.

This also fixed `SMSMessagePage.export()`, which previously clicked the
Export link and discarded the download entirely (2s sleep, no capture) —
it now wraps the click in `page.expect_download()` and returns
`{"elapsed_s", "file_path", "file_size"}` on success. To avoid breaking the
three existing callers (TC018/019/020, which discard the return value and
never expected an exception), a timeout or click failure now returns the
same `"background_job_triggered.csv"` placeholder shape
`SMSSenderIDPage.export_csv()` already uses, instead of raising.

**Also validated: SMS Incoming Messages export.** A fifth real export —
`tests/sms/messaging/test_sms_incoming_messages_flow.py`,
`test_tc018_export_csv_button` (this test already existed to confirm the
Export CSV button produces a file; header validation was added to it
rather than duplicating a new test, the same approach used for the Sender
ID export) — using
[`constants/sms_incoming_messages_headers.py`](constants/sms_incoming_messages_headers.py)'s
`EXPECTED_SMS_INCOMING_MESSAGES_HEADERS` (7 columns: Campaign Name, Sender
ID, Country Code, User Number, Message ID, Status, Received At). Note the
exported file's columns are a superset of the 6 columns shown in the
on-screen table (Action, Campaign Name, Sender ID, Country Code, User
Number, Received At) — the export additionally includes Message ID and
Status. `SmsIncomingMessagesPage.export_csv()` already correctly captured
the download via `page.expect_download()`, so no page-object fix was
needed here — only the header constant and the validation call.

**Also validated: SMS Blocked Numbers export.** A sixth real export —
`tests/sms/opt_out/test_sms_blocked_numbers_flow.py`,
`test_tc008b_export_csv_headers` (new test, added alongside the existing
`test_tc008_bulk_actions_dropdown` which only checked that the Export
option is present in the Bulk Actions dropdown, not that it produces a
file) — using
[`constants/sms_blocked_numbers_headers.py`](constants/sms_blocked_numbers_headers.py)'s
`EXPECTED_SMS_BLOCKED_NUMBERS_HEADERS` (5 columns: ID, Phone Number,
Department, User, Created At). `SmsBlockedNumbersPage.export_csv()` is
new — it opens Bulk Actions and clicks Export, capturing the download via
`page.expect_download()` without selecting any row checkboxes first,
mirroring the confirmed-working Bulk Actions → Export pattern already
proven on the Template/Sender ID pages (the export acts on the current
filtered listing, not on an explicit row selection). Returns `None` on
failure rather than raising, the same never-raises contract used by
`SmsIncomingMessagesPage.export_csv()`.

**Also validated: SMS Usage Report export.** A seventh real export —
`tests/sms/reports/test_sms_usage_report_flow.py`,
`test_usage_report_TC14_export_csv` (this test already existed to confirm
the Export CSV button triggers a download; header validation was added to
it rather than duplicating a new test) — using
[`constants/sms_usage_report_headers.py`](constants/sms_usage_report_headers.py)'s
`EXPECTED_SMS_USAGE_REPORT_HEADERS` (18 columns: Duration, Total/Submitted/
Delivered/Failed/Rejected/DLR Awaited Count, the same six as Units, Total
Charges, Delivery Charges, Surcharge, Delivery Surcharge, Delivery %).
This also fixed `SmsUsageReportPage.click_export_csv()`, which previously
clicked the Export CSV button and slept 1.5s without capturing anything —
it now wraps the click in `page.expect_download()` and returns
`{"elapsed_s", "file_path", "file_size"}` on success, or `None` on
failure, preserving the existing caller's behavior since it discarded the
return value and never expected an exception.

**Also validated: the six other SMS analytics report exports** — Campaign,
Status, Error Code, Sender, Template, and Latency Report all share the
same rappasoft/livewire-tables `EXPORT_CSV_BUTTON` / `click_export_csv()`
convention as Usage Report (same broken "click and sleep, no capture"
implementation, same fix applied identically to each), so all six were
fixed and validated together as one batch:

| Report | Test (existing, extended) | Constants file | Columns |
| --- | --- | --- | --- |
| Campaign | `tests/sms/reports/test_sms_campaign_report_flow.py::test_campaign_report_TC15_export_csv` | [`sms_campaign_report_headers.py`](constants/sms_campaign_report_headers.py) | 20 |
| Status | `tests/sms/reports/test_sms_status_report_flow.py::test_tc15_export_csv` | [`sms_status_report_headers.py`](constants/sms_status_report_headers.py) | 7 |
| Error Code | `tests/sms/reports/test_sms_error_code_report_flow.py::test_tc13_export_csv_functionality` | [`sms_error_code_report_headers.py`](constants/sms_error_code_report_headers.py) | 7 |
| Sender | `tests/sms/reports/test_sms_sender_report_flow.py::test_sender_report_TC13_export_csv` | [`sms_sender_report_headers.py`](constants/sms_sender_report_headers.py) | 19 |
| Template | `tests/sms/templates/test_sms_template_report_flow.py::test_template_report_TC13_export_csv` | [`sms_template_report_headers.py`](constants/sms_template_report_headers.py) | 20 |
| Latency | `tests/sms/reports/test_sms_latency_report_flow.py::test_tc12_export_latency_report_csv` | [`sms_latency_report_headers.py`](constants/sms_latency_report_headers.py) | 12 |

Notes: Error Code Report's `ERROR CODE`/`ERROR DESCRIPTION` headers are
genuinely all-caps in the real export (preserved verbatim, unlike every
other header in this project). Template Report's constants file is
distinct from `sms_template_headers.py` (the Template *list's* export,
already validated separately) — same feature name, different screens.

**Also validated: SMS Country Report export** —
`tests/sms/reports/test_sms_country_report_flow.py::test_country_report_TC15_export_csv`,
using
[`constants/sms_country_report_headers.py`](constants/sms_country_report_headers.py)'s
`EXPECTED_SMS_COUNTRY_REPORT_HEADERS` (20 columns: Duration, Country Code,
Product, plus the same Count/Units/Charges breakdown as Sender/Campaign
Report). Same `click_export_csv()` fix applied. Note: the first header
list given for this report was identical to Template Report's (Template
Name/DLT Template ID) — confirmed as a copy-paste mistake and corrected to
the real Country Code-based breakdown before implementing.

The validator is deliberately generic — the same call works for any future
channel/feature by swapping the expected-header list:
```python
validate_file_headers(rcs_file, EXPECTED_RCS_CAMPAIGN_HEADERS)  # implemented — see "RCS Channel" below
validate_file_headers(email_file, EXPECTED_EMAIL_HEADERS)       # not implemented yet
```

---

## RCS Channel

How the RCS channel is built and what it actually covers, at the same
level of detail as the SMS export write-ups above. RCS mirrors SMS's
architecture throughout (channel-based folders, single-login/worker-safe
fixtures, worker-safe unique test data) — this section calls out what's
shared, what's RCS-specific, and the confirmed live-DOM behavior the tests
are written against.

### Page objects (`pages/rcs/`, 19 files)

| Page object | Covers |
| --- | --- |
| `rcs_agent_page.py` | Agent list/create screen |
| `rcs_campaign_create_page.py` | Campaign creation wizard — name, agent/template pickers, contact import (paste + CSV), schedule controls, Test Campaign, Launch Campaign, modal handling |
| `rcs_campaign_page.py` | Campaign list — search, Status multiselect filter, pagination, CSV/xlsx export |
| `rcs_template_create_page.py` | Template creation (Text/Rich Card/Carousel types) |
| `rcs_message_page.py` | Outgoing message log |
| `rcs_incoming_messages_page.py` | Incoming message log |
| `rcs_optout_page.py` | Opt-out/blocked-number list |
| `rcs_download_center_page.py` | Download Center (async export jobs) |
| `rcs_overview_page.py` | Analytics overview/dashboard |
| `rcs_campaign_analytics_page.py`, `rcs_agent_analytics_page.py`, `rcs_template_analytics_page.py`, `rcs_usage_analytics_page.py`, `rcs_status_analytics_page.py`, `rcs_error_code_analytics_page.py`, `rcs_error_codes_page.py`, `rcs_message_type_analytics_page.py`, `rcs_country_analytics_page.py` | One page object per analytics/report screen, same `EXPORT_CSV_BUTTON` + `click_export_csv()` convention as SMS's report pages |

All 19 extend the shared `pages/common/base_page.py` `BasePage`, so they
get the same locator/wait helpers, table-row lookups, and
`page.expect_download()`-based export capture as every other channel —
nothing RCS-specific was needed there.

### Fixtures, config, and test data

- `fixtures/rcs_fixtures.py` is registered as a pytest plugin in
  `conftest.py`, the same mechanism SMS/WhatsApp/Email use — no RCS-only
  fixture wiring exists outside this file.
- `channels/rcs_channel.py`'s `RCSChannel` is intentionally thin — it only
  exposes `agent_name` (worker-safe), unlike `SMSChannel`'s
  `sender_id`/`template_name`/`template_with_vars`/`paste_contacts`/
  `campaign_prefix`. This was checked directly against the two Campaign
  test files (`test_rcs_campaign_flow.py`, `test_rcs_campaign_create_flow.py`)
  and confirmed **not** to be a functional gap: neither file actually uses
  `RCSChannel` — both generate their own worker-safe unique names locally
  (the same `unique_name()`/`short_unique_tag()` building blocks from
  `utils/parallel.py` that `RCSChannel` itself is built on), so campaign
  test data is already collision-safe across parallel workers without it.
- `Config.RCS_AGENT_NAME` (`.env`, default `"agentsim"`) is the agent used
  wherever a test needs to select *some* valid agent without caring which
  one.
- `Config.RCS_OPTOUT_NUMBERS` (`.env`, comma-separated, **empty by
  default**) backs the opt-out negative-path tests. With it unset those
  tests self-skip with an explicit reason rather than failing or using a
  fabricated number — set it to a real test number in your own `.env` to
  bring them into the run.

### Tests (`tests/rcs/`, 19 files, 682 tests)

| Folder | Files | What's covered |
| --- | --- | --- |
| `agent/` | 1 | Agent list/create flow |
| `campaigns/` | 2 | `test_rcs_campaign_create_flow.py` (creation wizard, 144 tests) + `test_rcs_campaign_flow.py` (list/export, 6 tests) — see below |
| `messaging/` | 2 | Outgoing + incoming message logs |
| `opt_out/` | 1 | Opt-out/blocked-number list |
| `reports/` | 12 | Download Center + one file per analytics screen, incl. `test_rcs_parallel_example_flow.py` (the RCS equivalent of `test_sms_parallel_example_flow.py` — function-scoped `logged_in_page` + worker-safe unique data, the reference pattern for genuine per-test parallelism) |
| `templates/` | 1 | Template creation (Text/Rich Card/Carousel) |

**`test_rcs_campaign_create_flow.py` is the deep end of the channel** —
144 tests against the campaign creation wizard, covering (per the RCS
Campaign spec this suite was built from): the full happy path for both
Send Now and Scheduled campaigns; contact import via copy/paste and CSV
upload, including the Import Completed summary panel; duplicate-phone
handling; agent/template selection; the opt-out flow; required-field and
inline validations; Test Campaign (preview-only, must **not** create a
real campaign record — see below); Launch Campaign positive, negative,
and duplicate-submission cases; and the Import Contacts / other modals'
open/close behavior.

Two tests added this session close out the one previously-unverified
claim in that spec — that "Test Campaign" is a preview action and never
persists a real campaign:

- `test_TC158_test_campaign_does_not_create_real_campaign` — fills a
  complete campaign (name, agent, template, one pasted contact), clicks
  Test Campaign, then re-opens a **fresh** campaign list page and asserts
  the campaign's name appears **zero** times there.
- `test_TC159_test_campaign_without_agent_no_real_campaign_created` —
  same assertion, but deliberately skips agent/template/contact selection
  first, to also confirm clicking Test Campaign on an incomplete form
  neither crashes (no 404/500 page) nor silently creates a record.

Both open a second, independent `RCSCampaignPage` instance to check the
list rather than trusting only the creation page's own toast/redirect —
the same "verify persistence, not just the UI signal" principle applied
to `test_TC041_launch_campaign` (now also tagged `smoke`, and extended to
confirm the launched campaign both appears in the list and has a
non-empty Status value) and `test_TC140_scheduled_campaign_status_after_creation`
(extended to assert the Status column reads exactly `"Scheduled"`, not
just that the row exists).

**`test_rcs_campaign_flow.py`** covers the campaign *list* screen: TC001
through TC009, including CSV/xlsx export + header validation via
`utils/file_validator.py` and
[`constants/rcs_campaign_headers.py`](constants/rcs_campaign_headers.py)'s
`EXPECTED_RCS_CAMPAIGN_HEADERS` (21 columns: ID, Campaign Name, Type,
Department, User, Template, Agent, Status, Total Messages, Sent Count,
Delivered Count, Read Count, Interactions, Failed Count, Created At,
Scheduled At, Send Type, Started At, Completed At, Message Content,
Updated At) — the same generic `validate_file_headers()` pattern used
for every SMS export above, applied here for the first time outside SMS.

### Confirmed live-DOM behavior (not guessed)

These were checked against the real app's markup before being encoded as
assertions, and are called out here so a future maintainer doesn't
"fix" a test back to an incorrect assumption:

- The **Import Contacts modal's close control** is `wire:click="$dispatch('closeModal')"`
  on its header `×` button, not a generic dialog-close pattern —
  `RCSCampaignCreatePage.click_modal_close_x()` targets this exact
  attribute.
- After a CSV upload, the modal shows an **"Import Completed" summary
  panel** (total rows, imported count, duplicates, etc.) before contacts
  are confirmed into the campaign — `is_import_summary_present()`,
  `get_import_summary_stat()`, and `get_import_total_rows_count()` read
  this panel; `click_confirm_import()` is the separate action that
  commits it.
- The campaign list's **Status filter is a custom Alpine multiselect**
  (a "Select status (N)" trigger button opening a checkbox panel), not a
  native `<select>`. Confirmed live values: Draft, Scheduled, Running,
  Paused, Completed, Cancelled, Failed.
- **Pagination** is numbered, driven by
  `wire:click="gotoPage(N, 'rcs_campaignsPage')"` per page-number
  element — the same Livewire pagination convention used elsewhere in
  this app.
- The campaign list's **"Export CSV" button actually downloads an
  `.xlsx`** file named `"Table Export.xlsx"`, not a `.csv` — confirmed
  from a real download, not a defect, and `RCSCampaignPage.click_export_csv()`
  / the header-validation tests above are written against that reality.

### Parity with SMS: single login and test independence

Checked directly this session, by diffing the historical commit that
introduced SMS's single-login/worker-safe architecture
(`961ffe8`, "Single login with multiple workers") against the current
state of the RCS Campaign create-flow file — RCS already has full parity,
with no changes needed:

- **Single login across workers**: RCS test files use the same
  `logged_in_page` / `module_logged_in_page` fixtures from `conftest.py`
  as every other channel. Both are built directly on
  `utils/auth_state.py`'s cross-process file lock (see "Parallel
  execution architecture" above), so this required zero RCS-specific
  code — any file using these fixtures gets it automatically.
- **Test independence**: `test_rcs_campaign_create_flow.py` contains
  zero `time.sleep()` calls, uses the shared
  `wait_for_validation_error_or_toast()` polling helper (not a fixed
  sleep) in the three places it needs to wait on an async
  validation/toast, and every one of its ten `except Exception` blocks is
  narrowly scoped to optional setup/precondition steps (e.g. "skip if
  this optional picker isn't present") rather than swallowing genuine
  assertion failures as false skips.

No RCS-specific "port the SMS improvements" work was required — it was
already there.

---

## Coverage

| Module | Page objects | Test files | Tests collected |
|---|---|---|---|
| Core (Login, Dashboard, Forgot Password) | 3 | 3 | — |
| SMS | 18 | 20 | 643 |
| RCS | 19 | 19 | 682 |
| WhatsApp | 12 | 12 | 402 |
| Email | 5 | 5 | 136 |
| Contacts, Segmentation, Tags, Communication Flow | 4 | 3 (no dedicated Communication Flow test) | — |
| Shared (`base_page.py`) | 1 | — | — |
| Pre-existing scratch/debug (`test_temp_dump*.py`) | — | 2 | 2 |
| **Total** | **62** | **64** | **1,939** |

(Test-collected counts above are from a real `pytest --collect-only -q`
run against this working tree, not estimates — re-run it yourself with
`pytest tests/<channel> --collect-only -q` any time to reconfirm.)

(Core + Contacts/Segmentation/Tags/Communication Flow together make up
`tests/common/`'s 6 test files and 74 collected tests.)

All page objects follow the same conversion patterns established from the
first pilot suites: plain-string locators (`"xpath=..."` prefix for
XPath), `Helpers`/`BasePage` for waits and table-row helpers, native
`page.expect_download()` for file downloads, and `page.wait_for_function()`
/ `page.evaluate()` for JS-driven widgets (e.g. the TinyMCE editor on the
Email Template Create page). Module-scoped "single login, sequential
flow" suites (SMS/RCS/WhatsApp/Email) share one authenticated `page` per
test module via a `module_logged_in_page` fixture in `conftest.py` — this
is the majority pattern, and later tests in these files frequently depend
on state earlier tests in the *same file* left behind, so these files
cannot safely be split across parallel workers mid-file (`--dist
loadscope` keeps each module on one worker; see "Channel-based
architecture" above). Neither `module_logged_in_page` nor `logged_in_page`
performs its own fresh UI login anymore: both attach to the shared,
disk-persisted `storage_state` produced by the single-login authentication
layer (`utils/auth_state.py`), doing at most a lightweight session-validity
check and a re-authentication if that state has expired. This is what
makes it safe to run every module concurrently under many workers against
one CPaaS+ account without each of them independently hammering the login
form — see "Parallel execution architecture" above and
`docs/ARCHITECTURE.md#authentication-architecture` for the full design.
Each channel also has one function-scoped example file
(`test_sms_parallel_example_flow.py` and its RCS/WhatsApp/Email
equivalents) built the opposite way — a fresh `logged_in_page` (still
backed by the same shared storage state, not a fresh login) and
worker-safe unique test data (`channels/*.py`'s `unique_campaign_name()`
etc.) per test — as a reference for genuine test-case-level parallelism.
Every original pytest marker (`smoke`, `regression`, `negative`) and
every `pytest.mark.skip` stub (with its original skip-reason docstring)
carried over unchanged from the Selenium suite.
