# CI/CD Setup — SMS Automation on Bitbucket Pipelines (Self-Hosted Runner)

This document covers running the **existing** CPaaS Playwright SMS
automation automatically from Bitbucket Pipelines, on a dedicated Linux
server, via a **Bitbucket self-hosted runner**. It does not change how the
framework works locally — every command below (`pytest`, `ENV=... pytest`,
`scripts/run_tests.py`, ...) is exactly what a developer already runs on
their own machine.

No real credentials appear anywhere in this document.

## 1. What runs where

- **Bitbucket Cloud** controls the repository, triggers pipelines, and
  stores secured variables (credentials). It does **not** run the tests
  itself.
- **Your self-hosted runner**, installed on a dedicated Ubuntu/Linux
  server, polls Bitbucket for work and actually executes the pipeline
  steps — including the Playwright browser. This is required because
  Bitbucket's own hosted (cloud) runners cannot reach your QA/Staging
  environments and cannot give Playwright/Chromium the persistent,
  pre-provisioned environment this suite needs.
- `bitbucket-pipelines.yml` (repo root) defines the pipelines and targets
  the self-hosted runner via `runs-on` labels.

## 2. Server requirements

- Ubuntu/Linux (any reasonably current LTS; the pipeline itself has no
  hard version pin beyond Python below).
- Python **3.12**.
- Git.
- Chromium's runtime dependencies (installed once via Playwright's
  `--with-deps` flag, below — this needs `sudo` and is a one-time, manual
  step, never run by the pipeline itself).
- The Bitbucket self-hosted runner agent.

## 3. One-time server setup

Run these once, as a user who can `sudo` (steps 3.4 and 3.6 only), on the
dedicated server. After this, the pipeline itself never needs `sudo` and
never installs system packages.

### 3.1 Clone the repository

```bash
git clone <your-repo-url> /opt/cpaas_playwright_tests
cd /opt/cpaas_playwright_tests
```

(Any path works — `/opt/cpaas_playwright_tests` is just the convention
used in the rest of this document. Whatever path you pick, that's where
the runner's working directory for this repository must be.)

### 3.2 Create a persistent virtual environment

The pipeline activates this venv on every run; it does not create or
recreate it. Creating it outside ephemeral paths means dependency
installs in step 3.3 (and in every pipeline run after) don't start from
zero.

```bash
python3.12 -m venv ~/cpaas_venv
source ~/cpaas_venv/bin/activate
```

### 3.3 Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.4 Install Playwright + Chromium, with system dependencies

This is the **one-time, `sudo`-requiring** install. The pipeline itself
only ever runs `playwright install chromium` (no `--with-deps`, no
`sudo`) to verify/refresh the browser binary — it assumes the system
libraries below are already present.

```bash
python3 -m playwright install --with-deps chromium
```

### 3.5 Set `VENV_PATH` for the runner

The pipeline looks for `VENV_PATH` (a plain, non-secret Bitbucket
repository variable) pointing at the venv from step 3.2. If unset, it
defaults to `$HOME/cpaas_venv` on the runner's host — set this explicitly
if you used a different path:

Repository settings → Repository variables → add `VENV_PATH` =
`/home/<runner-user>/cpaas_venv` (not secured; it's a path, not a
secret).

### 3.6 Register the Bitbucket self-hosted runner

In Bitbucket: **Repository settings → Runners → Add runner**. Choose
**Linux**, and when prompted for labels, add a label that matches what
`bitbucket-pipelines.yml` expects — by default:

```
self.hosted, linux, cpaas-automation
```

(`self.hosted` and `linux` are assigned automatically; `cpaas-automation`
is the custom label you type in. If you use a different custom label,
update `runs-on` in `bitbucket-pipelines.yml` to match.)

Bitbucket will give you a download + registration command for the runner
agent — run that on the server (this step needs `sudo` to install the
runner as a system service; follow Bitbucket's own on-screen
instructions). Once registered, the runner shows as **Online** in
Repository settings → Runners.

### 3.7 Configure secured repository variables

**Repository settings → Repository variables.** Add these six, and
check **Secured** on all of them so their values are never shown in the
Bitbucket UI or pipeline logs:

| Variable               | Value                                   |
|-------------------------|-------------------------------------------|
| `QA_EMAIL`              | the QA test account's login email       |
| `QA_PASSWORD`            | the QA test account's password          |
| `SMS_API_TOKEN_QA`       | the QA environment's SMS API token      |
| `STAGING_EMAIL`          | the Staging test account's login email  |
| `STAGING_PASSWORD`        | the Staging test account's password     |
| `SMS_API_TOKEN_STAGING`   | the Staging environment's SMS API token |

`utils/config.py`'s `SECRET_ENV_MAPPING` reads `QA_EMAIL`/`QA_PASSWORD`/
`SMS_API_TOKEN_QA` directly when `ENV=qa` (same for the `STAGING_*`
trio when `ENV=staging`) -- both the UI login flow and the SMS API/DLR
client resolve through this one mapping, so they can never pick up a
different environment's secret from each other. The pipeline script
additionally mirrors the email/password pair onto the legacy
`VALID_EMAIL`/`VALID_PASSWORD` names as an early bash-level guard, and
runs `scripts/ci_preflight.py` to confirm all three variables for the
selected `ENV` are present before anything else starts. None of these
six are ever written into `bitbucket-pipelines.yml` or into any
`config/environments/*.env` file.

Also add (not secured — these are not secrets):

| Variable      | Value                                            |
|---------------|---------------------------------------------------|
| `VENV_PATH`   | absolute path to the venv from step 3.2, if not using the default `$HOME/cpaas_venv` |

### 3.8 Validate configuration before enabling automatic runs

With the venv from step 3.2 active and `cd`'d into the repo:

```bash
# QA
ENV=qa python scripts/validate_config.py
ENV=qa python scripts/warm_auth.py
ENV=qa PLAYWRIGHT_WORKERS=2 python scripts/run_tests.py tests/sms -m smoke

# Staging
ENV=staging python scripts/validate_config.py
ENV=staging python scripts/warm_auth.py
ENV=staging PLAYWRIGHT_WORKERS=2 python scripts/run_tests.py tests/sms -m smoke
```

For these manual commands, set `QA_EMAIL`/`QA_PASSWORD`/
`SMS_API_TOKEN_QA` (or `STAGING_EMAIL`/`STAGING_PASSWORD`/
`SMS_API_TOKEN_STAGING`) in your shell or your own root `.env` — not
from the Bitbucket secured variables, which only exist inside a pipeline
run, and not from `config/environments/*.env`, which no longer holds
credentials at all (see README's "Secrets" section). The legacy
`VALID_EMAIL`/`VALID_PASSWORD`/`SMS_API_TOKEN` names also still work as
a fallback. Never commit real values anywhere.

**All six commands above must pass before enabling the automatic
pipelines** (pull-request/branch triggers) in step 5. If any fails, fix
the underlying configuration (not the pipeline) and re-run — this is the
same configuration a real pipeline run will use.

## 4. How the pipeline is structured

`bitbucket-pipelines.yml` defines one reusable step (`&run-sms-tests`,
via a YAML anchor) and five triggers that reuse it, rather than six
separate copies of the same script:

| Trigger                                   | ENV      | TEST_TYPE    | Workers | When |
|--------------------------------------------|----------|--------------|---------|------|
| Pull request                               | qa       | smoke        | 5       | automatic, every PR |
| Push to `main`                             | qa       | smoke        | 5       | automatic |
| Custom: `sms-manual-run`                   | your pick (qa/staging) | your pick (smoke/regression/full) | your pick | manual, from Bitbucket's "Run pipeline" UI |
| Custom: `sms-nightly-staging-regression`   | staging (fixed) | regression (fixed) | 8 (fixed) | scheduled (see step 6) — never production |

No developer needs to edit this YAML file for a normal run: `ENV`,
`TEST_TYPE`, and `PLAYWRIGHT_WORKERS` are exposed as pipeline variables
on the manual pipeline, with sensible defaults everywhere else.

Each run:

1. Validates the repo (confirms it's checked out in the right place —
   never runs `git pull`; the runner's own checkout controls the commit).
2. Activates the persistent venv and checks the Python version.
3. Installs/updates dependencies from `requirements.txt`.
4. Verifies the Playwright Chromium binary.
5. Resolves `ENV` → credentials from the secured variables (email,
   password, and the SMS API token), and fails immediately if any are
   missing (`scripts/ci_preflight.py`) — never silently falls back or
   mixes QA secrets into a Staging run.
6. Runs `scripts/validate_config.py`, which prints the safety banner
   (Environment / Channel / Test Type / Workers / Headless — never a
   secret) and hard-fails on a UI/API/DLR environment mismatch.
7. Runs `scripts/warm_auth.py` once, before any parallel worker starts.
8. Runs the tests through `scripts/run_tests.py` (never a hand-rolled
   `pytest` command, and never with `|| true` — a test failure fails the
   pipeline).
9. Collects reports, even on failure (Bitbucket's `after-script` always
   runs).
10. Publishes `reports/test_report.html`, `reports/screenshots/**`,
    `reports/logs/**`, `reports/junit.xml`, and `reports/summary.json` as
    pipeline artifacts. `reports/.auth/**` (authentication/storage state)
    is never published.

## 5. Enabling automatic execution

Only after every command in step 3.8 has passed:

1. Merge/push `bitbucket-pipelines.yml` to `main`.
2. Open a test pull request — confirm the "SMS Smoke - QA (PR)" pipeline
   runs on the self-hosted runner and passes.
3. Confirm artifacts (test report, junit.xml, summary.json) are attached
   to the pipeline run.

## 6. Scheduling the nightly Staging regression

Bitbucket Pipelines YAML has no native `schedule:` key — nightly runs are
configured from the Bitbucket UI, not in this file:

**Pipelines → Schedules → New schedule**
- Pipeline: `custom: sms-nightly-staging-regression`
- Branch: `main`
- Frequency: Nightly (pick your preferred time)

This pipeline's `ENV`/`TEST_TYPE`/`PLAYWRIGHT_WORKERS` variables each
have exactly one allowed value (`staging` / `regression` / `8`), so it
can't be accidentally pointed at a different environment or test type,
whether triggered by the schedule or run manually from the UI. It is
never wired to any production-like environment.

## 7. Adding `INSTANCE` later

This phase intentionally does **not** wire up multi-instance
(`INSTANCE=qa-01`, `INSTANCE=staging-01`, ...) execution in the pipeline,
even though the framework already supports `INSTANCE` locally. When
that's needed:

- Add an `INSTANCE` pipeline variable (optional, default empty) to the
  manual and/or scheduled pipeline definitions.
- Forward it as an environment variable in the shared script step
  (`export INSTANCE="${INSTANCE:-}"`), exactly like `ENV`/`TEST_TYPE`.
- No other structural change should be needed — `scripts/run_tests.py`
  and `scripts/validate_config.py` already understand `INSTANCE`.

No fake or placeholder instance files have been created as part of this
phase.

## 8. Troubleshooting

- **"venv not found at $VENV_PATH"** — step 3.2/3.5 wasn't completed, or
  `VENV_PATH` points at the wrong path. Check the repository variable.
- **"credentials for ENV=... are not configured as secured repository
  variables"** or **"SMS_API_TOKEN_QA/STAGING is not configured as a
  secured repository variable"** — the corresponding `QA_*`/`STAGING_*`
  secured variable is empty or missing. Check step 3.7. Running
  `python scripts/ci_preflight.py` locally (with `ENV` set) shows exactly
  which of the three required variables for that environment are
  missing, without printing any value.
- **Environment mismatch error from `validate_config.py`** — the
  requested `ENV` and the actual resolved API/DLR environment
  (`ENV_NAME`) don't pair up as expected. This is a hard stop by design;
  fix the underlying `config/environments/<ENV>.env`'s `ENV_NAME=` line
  rather than overriding it in the pipeline.
- **Runner shows offline in Bitbucket** — check the runner service is
  running on the server (`sudo systemctl status <runner-service-name>`,
  name depends on how Bitbucket's installer registered it).
