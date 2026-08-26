# CPaaS+ Playwright Test Automation

**Status: conversion complete.** This folder is the full Selenium →
Playwright migration of `cpaas_selenium_tests/`. Every suite from the
original Selenium project has been converted: the framework core (config,
page-object base classes, helpers, error monitor, HTML reporting) plus all
functional modules — **Login, Dashboard, Forgot Password, SMS, RCS,
WhatsApp, Email, Contacts, Segmentation, Tags, and Communication Flow**.

The converted suite currently totals **62 page objects** and **64 test
files** (**1,844 tests**), all collecting cleanly under
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
`pytestmark` channel/feature tags. The suite totals **1,844 tests**
(common 74, SMS 645, RCS 585, WhatsApp 402, Email 136 — 1,842 across
those five folders, plus 2 pre-existing `test_temp_dump*.py` scratch/debug
files at the `tests/` root that predate this migration and are unrelated
to it).

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
# All tests (full suite — 1,844 tests)
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
│   └── tags.py                      # Marker-name constants, mirrors pytest.ini
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
├── tests/                           # 64 test files, 1,844 tests total
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
│   └── test_data_generator.py       # Generates the files under tests/test_data/
│
├── scripts/
│   └── run_tests.py                 # PLAYWRIGHT_WORKERS/ENV -> real pytest -n/--dist flags (see below)
│
└── reports/                         # HTML report + screenshots after each run
```

---

## Coverage

| Module | Page objects | Test files | Tests collected |
|---|---|---|---|
| Core (Login, Dashboard, Forgot Password) | 3 | 3 | — |
| SMS | 18 | 20 | 645 |
| RCS | 19 | 19 | 585 |
| WhatsApp | 12 | 12 | 402 |
| Email | 5 | 5 | 136 |
| Contacts, Segmentation, Tags, Communication Flow | 4 | 3 (no dedicated Communication Flow test) | — |
| Shared (`base_page.py`) | 1 | — | — |
| Pre-existing scratch/debug (`test_temp_dump*.py`) | — | 2 | 2 |
| **Total** | **62** | **64** | **1,844** |

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
