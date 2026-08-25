# CPaaS+ Playwright Test Automation

**Status: conversion complete.** This folder is the full Selenium →
Playwright migration of `cpaas_selenium_tests/`. Every suite from the
original Selenium project has been converted: the framework core (config,
page-object base classes, helpers, error monitor, HTML reporting) plus all
functional modules — **Login, Dashboard, Forgot Password, SMS, RCS,
WhatsApp, Email, Contacts, Segmentation, Tags, and Communication Flow**.

The converted suite currently totals **63 page objects** and **58 test
files** (**1,846 tests**), all collecting cleanly under
`pytest --collect-only` with the original `smoke` / `regression` /
`negative` markers intact. The file *locations* below (`pages/sms_*.py`,
`tests/test_rcs_*.py`, etc.) describe the original conversion's flat
layout; the suite has since been reorganized into the channel-based
folder structure described in the section above and in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — see that document for
the current, accurate file locations.

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
`pytestmark` channel/feature tags. The suite totals **1,846 tests**
(1,844 across the five folders above, plus 2 pre-existing scratch/debug
test files unrelated to this migration).

The old flat file locations were overwritten with thin re-export shims
(pages) / empty stub files (tests) rather than deleted, since the tooling
used to deliver this migration couldn't delete files directly — run
`cleanup_old_flat_duplicates.bat` and `cleanup_common_flat_duplicates.bat`
in this folder to remove them once you've confirmed the new locations
work (`pytest --collect-only -q` should read the same before and after).

Full details, the exact commands for parallel/channel/marker execution,
and the full migration history: see
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). To add a new channel:
[`docs/ADDING_A_CHANNEL.md`](docs/ADDING_A_CHANNEL.md).

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
# All tests (full suite — 1,846 tests)
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

See the "Channel-based architecture" section above for channel/marker/
parallel execution commands (`pytest tests/<channel>`, `pytest -m
<channel>`, `PLAYWRIGHT_WORKERS=N python scripts/run_tests.py ...`).

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
├── conftest.py                    # Playwright fixtures + HTML report hooks
├── pytest.ini
├── requirements.txt
├── .env.example
├── pages/                          # 63 page objects (POM, 1:1 with the Selenium suite)
│   ├── base_page.py                # Shared helpers (wait, open URL, table row helpers)
│   ├── login_page.py / dashboard_page.py / forgot_password_page.py
│   ├── sms_*.py                    # 18 files — campaign, incoming messages, blocked
│   │                                #   numbers, sender IDs, templates, reports
│   │                                #   (campaign/country/error-code/latency/sender/
│   │                                #   status/template/usage), download center,
│   │                                #   error codes, overview
│   ├── rcs_*.py                    # 19 files — agent, campaign (create/list/analytics),
│   │                                #   messages, incoming messages, optout, download
│   │                                #   center, error codes, overview, reports, template
│   │                                #   create/analytics, country/status/message-type/
│   │                                #   usage analytics
│   ├── whatsapp_*.py               # 12 files — campaign/country/message-type/status/
│   │                                #   template/usage/WABA-number analytics, download
│   │                                #   center, message report, optout, overview
│   ├── email_*.py                  # 5 files — overview, template, template create,
│   │                                #   campaign, campaign create
│   └── contacts_page.py / segmentation_page.py / tags_page.py /
│       communication_flow_page.py
├── tests/                          # 58 test files, 1,836 tests total
│   ├── test_login.py / test_dashboard.py / test_forgot_password.py
│   ├── test_sms_*.py / test_rcs_*.py / test_whatsapp_*.py / test_email_*.py
│   └── test_contacts_flow.py / test_segmentation_flow.py / test_tags_flow.py /
│       test_campaign_creation.py
├── utils/
│   ├── config.py                   # Reads .env — same variables as the Selenium suite (minus BROWSER)
│   ├── helpers.py                  # Playwright-native wait/screenshot/download helpers
│   └── error_monitor.py            # Platform error detection (500s, Whoops, Livewire errors, etc.)
└── reports/                        # HTML report + screenshots after each run
```

---

## Coverage

| Module | Page objects | Test files |
|---|---|---|
| Core (Login, Dashboard, Forgot Password) | 3 | 3 |
| SMS | 18 | 18 |
| RCS | 19 | 18 |
| WhatsApp | 12 | 11 |
| Email | 5 | 4 |
| Contacts, Segmentation, Tags, Communication Flow | 4 | 4 |
| Shared (`base_page.py`, `__init__.py`) | 2 | — |
| **Total** | **63** | **58 (1,836 tests)** |

All page objects follow the same conversion patterns established from the
first pilot suites: plain-string locators (`"xpath=..."` prefix for
XPath), `Helpers`/`BasePage` for waits and table-row helpers, native
`page.expect_download()` for file downloads, and `page.wait_for_function()`
/ `page.evaluate()` for JS-driven widgets (e.g. the TinyMCE editor on the
Email Template Create page). Module-scoped "single login, sequential
flow" suites (SMS/RCS/WhatsApp/Email) share one authenticated `page` per
test module via a `module_logged_in_page` fixture in `conftest.py`. Every
original pytest marker (`smoke`, `regression`, `negative`) and every
`pytest.mark.skip` stub (with its original skip-reason docstring) carried
over unchanged from the Selenium suite.
