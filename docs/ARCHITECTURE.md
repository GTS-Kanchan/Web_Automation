# CPaaS+ Automation — Channel-Based Architecture

Status: **migration complete.** All four channels (SMS, RCS, WhatsApp,
Email) plus the common/cross-channel suites are now organized into the
channel-based folder structure — nothing remains in the old flat layout
except thin re-export shims / empty stubs left behind for backward
compatibility (see "Old flat paths" below). SMS was migrated first as the
reference channel; RCS, WhatsApp, and Email followed the identical,
mechanically-verified pattern (grep for zero cross-channel importers →
move pages → move tests → fix imports → fix any move-breaking relative
paths → add `pytestmark` tags → verify `py_compile` + `--collect-only`
count unchanged → deliver). The **common pages** batch (`base_page.py`,
`login_page.py`, `dashboard_page.py`, `forgot_password_page.py`,
`contacts_page.py`, `segmentation_page.py`, `tags_page.py`,
`communication_flow_page.py` → `pages/common/`; their 6 test files →
`tests/common/`) went last, as one deliberate pass — it's the one batch
that touches every other channel's imports at once, since 61 of the 62
page objects subclass `BasePage`. All 1,844 tests still collect (1,842
across the four channels + common, plus 2 pre-existing scratch/debug test
files at the flat `tests/` root that predate this migration and were left
alone); per-channel path-based (`pytest tests/<channel>`) and marker-based
(`pytest -m <channel>`) selection agree exactly for every channel and for
`common` (SMS 645, RCS 585, WhatsApp 402, Email 136, common 74). These
counts include the four function-scoped "parallel example" test files
added after the channel migration itself (§12) — one per channel, none
for `common`.

Stack: **Python + pytest + pytest-playwright** (the request's spec was
written in TypeScript/Playwright-Test conventions; every deliverable below
is the Python/pytest equivalent of that spec, confirmed with the user
before implementation).

---

## 1. What was analyzed

- 61 test files, 62 page objects, one 409-line `conftest.py`, all flat
  under `tests/` and `pages/`.
- Every SMS/WhatsApp/RCS/Email flow test follows one architecture: a
  **module-scoped "single sequential flow"** — one login, one browser
  context, one Playwright `Page`, shared by every test function in that
  file, executed top-to-bottom (`module_logged_in_page` fixture in
  `conftest.py`). Later tests in a file frequently depend on state earlier
  tests in the *same file* left behind (a template created by TC020,
  searched for by TC021). This is why test-case-level parallelism cannot
  safely be retrofitted onto existing files without rewriting them (see
  §4).
- Duplicate code found: every one of the 19 SMS test files (and, by the
  same shape, most of the other 42) repeats a 4–6 line module-scoped
  page-object fixture (`def X_page(module_logged_in_page): ... return
  PageClass(module_logged_in_page)`). Centralized as an opt-in helper —
  `channels/fixture_factory.py::module_page_fixture()` — for new/migrated
  files; existing files were **not** rewritten to use it (see §21 rule 1).
- Common utilities already existed and were reused, not duplicated:
  `utils/helpers.py` (`Helpers` — waiting, retry, screenshot, download),
  `utils/config.py` (`Config`), `utils/error_monitor.py`,
  `pages/base_page.py` (`BasePage`, superclass of the other 61 page objects).
- Test-data collision risk found: campaign names used
  `f"{prefix}_{suffix}_{int(time.time())}"` — second-resolution only, so
  two parallel workers creating a campaign in the same second could
  collide. Fixed at the one real call site that had it
  (`tests/sms/campaigns/test_sms_campaign_flow.py::start_create`) and
  replaced with the new worker-safe `unique_name()` (§7).
- Shared-file race found: `utils/test_data_generator.py`'s `generate_all()`
  runs once per test *module* (every flow file's autouse fixture calls it)
  and writes static files (e.g. `valid_template.xlsx`) to one shared
  `tests/test_data/` directory. Under `-n`, two workers could write the
  same file at the same instant. Fixed with an atomic
  write-to-temp-then-`os.replace()` pattern (`os.replace` is atomic on
  both POSIX and Windows) in every `_write_csv`/`_write_xlsx`/direct-write
  helper in that module.
- Global-mutable-state bug found (pre-existing, not previously exercised
  because nothing ran under `-n` before): `conftest.py` incremented a
  module-level `_results` dict inside `pytest_runtest_makereport`, which
  only runs in the **worker** process under `pytest-xdist` — the
  **controller** process (which renders the HTML report) would see a
  permanently-zero pass/fail/skip count. Fixed by computing the summary
  banner's counts once, in `pytest_sessionfinish`, from pytest's own
  aggregated `terminalreporter.stats` (correct with or without `-n`).

---

## 2. Final project structure

```
cpaas_playwright_tests/
├── conftest.py                     # unchanged fixtures/hooks + new: plugin
│                                    #   registration, worker-safe screenshot
│                                    #   dir, xdist-safe summary banner
├── pytest.ini                      # + channel/feature markers
├── requirements.txt                # unchanged (pytest-xdist was already listed)
│
├── config/
│   ├── __init__.py
│   └── environments/
│       ├── dev.env
│       ├── qa.env
│       └── staging.env             # ENV=<name> selects one — see §9
│
├── channels/                       # NEW — the Channel abstraction (§3)
│   ├── __init__.py                 # factory: get_channel("sms", page=...)
│   ├── base_channel.py             # BaseChannel
│   ├── sms_channel.py              # SMSChannel(BaseChannel)
│   ├── whatsapp_channel.py         # WhatsAppChannel(BaseChannel)
│   ├── rcs_channel.py              # RCSChannel(BaseChannel)
│   ├── email_channel.py            # EmailChannel(BaseChannel)
│   └── fixture_factory.py          # module_page_fixture() — kills the
│                                    #   duplicated fixture boilerplate
│
├── fixtures/                       # NEW — registered as pytest plugins
│   ├── common_fixtures.py          #   correlation_id, test_logger,
│   │                                  authenticated_storage_state, ...
│   ├── sms_fixtures.py             #   sms_channel
│   ├── whatsapp_fixtures.py        #   whatsapp_channel
│   ├── rcs_fixtures.py             #   rcs_channel
│   └── email_fixtures.py           #   email_channel
│
├── api/                            # NEW — scaffold only, see §11
│   ├── common/base_client.py       # BaseApiClient (Playwright APIRequestContext)
│   ├── sms/  whatsapp/  rcs/  email/   # empty, documented, ready to fill in
│
├── constants/
│   └── tags.py                     # marker-name constants, mirrors pytest.ini
│
├── scripts/
│   └── run_tests.py                # PLAYWRIGHT_WORKERS -> real `-n`/`--dist` (§5)
│
├── utils/
│   ├── config.py                   # + ENV-based env-file loading, API_URL/TENANT
│   ├── parallel.py                 # NEW — worker_id(), unique_name(), ...
│   ├── logger.py                   # NEW — structured per-worker logging (§16)
│   ├── helpers.py                  # unchanged
│   ├── error_monitor.py            # unchanged
│   └── test_data_generator.py      # + atomic writes for parallel safety
│
├── pages/
│   ├── common/                     # MOVED — 8 cross-channel page objects:
│   │   ├── base_page.py, login_page.py, dashboard_page.py,
│   │   ├── forgot_password_page.py, contacts_page.py,
│   │   └── segmentation_page.py, tags_page.py, communication_flow_page.py
│   ├── sms/                        # MOVED — 18 SMS page objects
│   ├── rcs/                        # MOVED — 19 RCS page objects
│   ├── whatsapp/                   # MOVED — 12 WhatsApp page objects
│   └── email/                      # MOVED — 5 Email page objects
│
├── tests/
│   ├── common/                     # MOVED — 6 cross-channel test files:
│   │   ├── test_login.py, test_dashboard.py, test_forgot_password.py,
│   │   └── test_contacts_flow.py, test_segmentation_flow.py, test_tags_flow.py
│   ├── sms/                        # MOVED — 20 test files, 6 subfolders
│   │   │                           #   (19 from the migration + 1 parallel-
│   │   │                           #   example file added after, see §12):
│   │   ├── campaigns/  templates/  sender_id/  messaging/  reports/  opt_out/
│   ├── rcs/                        # MOVED — 19 test files, 6 subfolders
│   │   │                           #   (18 + 1 parallel-example file):
│   │   ├── campaigns/  templates/  agent/  messaging/  opt_out/  reports/
│   ├── whatsapp/                   # MOVED — 12 test files, 2 subfolders
│   │   │                           #   (11 + 1 parallel-example file):
│   │   ├── reports/  opt_out/
│   ├── email/                      # MOVED — 5 test files, 3 subfolders
│   │   │                           #   (4 + 1 parallel-example file):
│   │   ├── campaigns/  templates/  reports/
│   ├── test_temp_dump.py, test_temp_dump_modal.py   # pre-existing scratch/
│   │                                #   debug files, unrelated to this
│   │                                #   migration — left in place, imports
│   │                                #   updated to pages.common.* so they
│   │                                #   still run
│   └── test_data/                  # unchanged location — DATA_DIR resolved
│                                    #   via utils/test_data_generator.py, not
│                                    #   __file__-relative, so it survives moves
│
└── docs/
    ├── ARCHITECTURE.md             # this file
    └── ADDING_A_CHANNEL.md
```

### Old flat paths

Every file's original flat location (`pages/base_page.py`,
`pages/sms_campaign_page.py`, `tests/test_login.py`,
`tests/test_rcs_agent_flow.py`, etc. — 120 files across all five
migration batches) was overwritten with a thin re-export shim (pages) or
an empty stub (tests) rather than deleted, because the delivery mechanism
used for this migration (a remote-device file bridge) cannot delete files.
A companion cleanup script removes these once you've verified the new
locations work — see the repo root for `cleanup_old_flat_duplicates.bat`
(SMS/RCS/WhatsApp/Email batch) and `cleanup_common_flat_duplicates.bat`
(common-pages batch). **Run `pytest --collect-only -q` before and after
each cleanup script and confirm the count is unchanged** — a stub/shim
file collects zero tests either way, so removing it never changes the
count; if the count ever drops, something besides the listed duplicate
files was touched, and you should stop and check.

---

## 3. Channel architecture

```
BaseChannel
    |
    +-- SMSChannel
    +-- WhatsAppChannel
    +-- RCSChannel
    +-- EmailChannel
    +-- <FutureChannel>
```

This suite is 100% UI automation — there's no existing network/API layer
for `BaseChannel` to wrap, so it's a **composition point**, not a protocol
abstraction: channel-scoped config, worker-safe unique naming
(`unique_campaign_name()`, `unique_template_name()`, `unique(label)`), a
pre-tagged structured logger, and the channel's test-data directory. It
does **not** reimplement waiting/retry/auth/context handling — those stay
exactly where they already lived (`Helpers` / `conftest.py`), composed in,
not duplicated.

`RCSChannel.unique_campaign_name()` deliberately **overrides** the base
version rather than using it as-is: the RCS Campaign Name field has a
tight, hand-tuned character budget that `unique_name()`'s longer
epoch/worker/counter/random suffix would exceed, so it uses
`short_unique_tag()` instead (a primitive `utils/parallel.py` already
names RCS campaign/template creation as an intended use site for). This
consolidates a `_unique_name()` helper that used to be duplicated locally
inside `tests/rcs/campaigns/test_rcs_campaign_create_flow.py` — same
output shape, same behavior, one place to maintain it.

`channels/__init__.py` is a factory (`get_channel("sms", page=...)`) plus a
`register_channel(name, cls)` escape hatch so a new channel package can
register itself without editing this file.

---

## 4. Parallel execution — what's real vs. what's structural

**Channel-level and file-level parallelism: yes, today, unconditionally.**
Every test file's module-scoped fixture already runs in its own isolated
Playwright browser context; `pytest-xdist` forks separate OS *processes*
per worker, so distributing whole files/channels across workers requires
no fixture changes — SMS, WhatsApp, RCS, Email files (and files within a
channel) can already run on different workers simultaneously.

**Test-case-level parallelism within one existing flow file: no, by
design, and changing that would mean rewriting the file.** The existing
"single sequential flow" architecture trades per-test isolation for speed
(one login instead of dozens) and correctness for stateful chains (TC021
depends on TC020's leftover state). Splitting such a file's tests across
workers would run them out of order in different processes and break that
chained state — this is not a limitation of the new architecture, it's
what the existing tests already require to keep passing. **The right unit
of parallel distribution for this suite is the file/module, not the
individual test inside a single-sequential-flow file.**

`--dist loadscope` (wired automatically by `scripts/run_tests.py` whenever
`-n`/`PLAYWRIGHT_WORKERS` is used, see §5) enforces exactly this: every
test from one module stays on one worker, in file order — required for
correctness, not just performance.

True test-case-level parallelism **is** fully supported and demonstrated
for tests that are actually independent — see the four new example files
in §12, which use function-scoped `page`/`logged_in_page` fixtures (fresh
login, fresh context per test) instead of the module-scoped pattern.
New channel work should default to this style unless there's a specific
reason (speed, a genuinely sequential business flow) to use the
module-scoped one instead.

```
                 Test Runner
                     |
       +-------------+-------------+-------------+
       v             v             v             v
      SMS         WhatsApp        RCS          Email
       |             |             |             |
       v             v             v             v
  6 subfolders   2 subfolders  6 subfolders  3 subfolders
  20 files       12 files      19 files      5 files
  each file =    each file =   each file =   each file =
  1 worker-unit  1 worker-unit 1 worker-unit 1 worker-unit
  (loadscope)    (loadscope)   (loadscope)   (loadscope)
```

---

## 5. Worker configuration

```bash
# explicit, always works, exactly as pytest-xdist has always supported:
pytest tests/sms -n 4 --dist loadscope
pytest tests/sms -n auto --dist loadscope

# env-var driven (the PLAYWRIGHT_WORKERS requirement) — via the wrapper:
PLAYWRIGHT_WORKERS=10 python scripts/run_tests.py tests/sms
```

**Why a wrapper script and not a `conftest.py` hook:** two conftest-hook
approaches (`pytest_configure` mutating `config.option.numprocesses`, and
`pytest_load_initial_conftests` injecting into `args`) were implemented
and empirically verified **not to work** — `pytest-xdist` decides whether
and how many workers to fork inside its own `pytest_cmdline_main`
hookimpl, which runs before a project conftest gets a chance to influence
it (`pytest_load_initial_conftests` additionally never fires for the very
rootdir conftest it's defined in — it only affects *other*, not-yet-loaded
conftests). Both were tested against a real `pytest-xdist` install in this
environment: no `gw0`/`gw1` workers ever appeared. `scripts/run_tests.py`
sidesteps this entirely by building the actual CLI args before the pytest
process starts parsing anything — verified working (`created: 2/2 workers`,
`LoadScopeScheduling`, `[gw0]` in real output).

No worker count is hard-coded anywhere. Config files under
`config/environments/` each set a conservative `PLAYWRIGHT_WORKERS`
default (2–4) as a *starting point* — raise it only after confirming the
target app/API and CI runner tolerate it (rule: don't blindly maximize
workers; a laptop and a CI runner do not have the same CPU/RAM).

---

## 6. Channel-specific execution

```bash
pytest tests/sms                       # SMS only (645 tests)
pytest tests/rcs                       # RCS only (585 tests)
pytest tests/whatsapp                  # WhatsApp only (402 tests)
pytest tests/email                     # Email only (136 tests)
pytest tests/common                    # login/dashboard/contacts/etc. (74 tests)
pytest                                 # everything (testpaths=tests)
pytest tests/sms tests/whatsapp        # combination — plain pytest supports
                                        #   multiple positional paths natively
pytest -m sms                          # marker-based — identical count to
                                        #   the path-based form above for
                                        #   every channel and common (verified)
pytest -m "rcs and agent"              # channel + feature marker combo
```

---

## 7. Test-data isolation

`utils/parallel.py`:

- `worker_id()` — `"gw0"`, `"gw1"`, ... under `-n`; `"master"` in a plain
  single-process run (so nothing changes for existing non-parallel usage).
- `unique_name(prefix)` — `f"{prefix}_{epoch_ms}_{worker}_{counter}_{4-random-chars}"`.
  Collision-proof across workers, across tests in the same worker, and
  across repeated calls within one test (process-local counter as a
  tie-breaker on top of the timestamp + random suffix).
- `worker_scoped_dir(base_dir)` — `base_dir/<worker_id>/`, created on
  demand — for any output a worker writes independently (screenshots,
  downloads).

Wired in:
- `channels/base_channel.py` — `unique_campaign_name()` /
  `unique_template_name()` / `unique(label)`, prefixed per-channel
  (`SMS_CAMPAIGN_...`, `EMAIL_CAMPAIGN_...`) so two channels can never
  collide even with the same base label.
- `tests/sms/campaigns/test_sms_campaign_flow.py::start_create` — the one
  real existing call site using second-resolution timestamps, switched to
  `unique_name()`.
- `conftest.py`'s `SCREENSHOT_DIR` — now `reports/screenshots/<worker_id>/`.
- `utils/test_data_generator.py` — atomic writes (§1) so the *shared*
  static files multiple workers legitimately both need don't corrupt each
  other; per-worker *unique* data still needs `unique_name()` at the call
  site the same way the campaign-name fix demonstrates.

---

## Authentication architecture

Every worker runs against **one** CPaaS+ account, and repeated login
attempts in a short window trigger a ~5 minute account lockout. So the
hard requirement isn't "log in efficiently" — it's that a whole run, at
any `-n`/`PLAYWRIGHT_WORKERS` count, must perform **exactly one** real UI
login, and every worker/test after that reuses the same authenticated
session. `fixtures/common_fixtures.py` originally had a session-scoped
`authenticated_storage_state` fixture that logged in once **per worker
process** — still `N` real logins under `-n N`, not good enough for this
platform's lockout window. That fixture (and `authenticated_module_page`,
built on top of it) was **not removed** — new/migrated channel test files
can still request it directly — but it was rewired to delegate to
`utils/auth_state.py::ensure_authenticated_state()` below instead of
performing its own login, so it, `conftest.py`'s `logged_in_page`/
`module_logged_in_page`, and any future consumer all share the exact same
one-login-for-the-whole-run guarantee rather than each enforcing it
separately (or not enforcing it at all).

### Design: a single, file-locked, disk-persisted `storage_state`

`utils/auth_state.py` owns a single shared Playwright `storage_state` JSON
file (`STATE_PATH`, default `reports/.auth/state.json`, overridable via
`AUTH_STATE_PATH`) guarded by a cross-process file lock:

- The first caller — in any worker, in any test, in the whole run — to
  reach `ensure_authenticated_state()` acquires the lock (an atomic
  `os.O_CREAT | os.O_EXCL` lockfile create; atomic on POSIX and Windows,
  no `filelock`/`portalocker` dependency needed at this project's scale),
  finds no state file, performs the one real UI login
  (`utils/auth_state.py::_perform_login`, via a throwaway
  `browser.new_context()`/page, never the shared per-test page), writes
  `storage_state` to a temp file in the same directory, and
  `os.replace()`s it into place — atomic on both POSIX and Windows, so no
  concurrent reader ever observes a partially-written file — then
  releases the lock.
- Every other caller, before or after that, either finds the state file
  already present (fast path, no lock touched at all) or briefly blocks
  on the lock and picks up the file once the first caller finishes.
  Nobody else ever calls the login page.
- A lock older than `_LOCK_STALE_SECONDS` (180s) is treated as abandoned
  by a crashed worker and force-cleared, so the run can't deadlock
  forever on a lock nobody will release. A waiter gives up after
  `_LOCK_WAIT_TIMEOUT` (150s, deliberately shorter than the stale
  threshold so a slow-but-legitimate login is never preempted) and raises
  `AuthenticationError` rather than attempting its own login.
- There is no `time.sleep(300)`/arbitrary fixed delay anywhere in this
  module — a waiting worker polls `_LOCK_POLL_SECONDS` (0.5s) against a
  real timeout, so it waits only as long as the one real login actually
  takes.

`conftest.py` wires this in for the two fixtures the whole suite already
depends on — `logged_in_page` (function-scoped) and `module_logged_in_page`
(module-scoped) — via a shared helper, `_open_authenticated_context()`:
both call `ensure_authenticated_state(browser)` to get the shared state
path, then build their own fresh, isolated Playwright context from it
(`browser.new_context(storage_state=state_path, ...)`). No context or page
is ever shared across tests or workers — only the underlying cookies/
storage in the state file are shared. This is what turns "one login per
test (or per module)" into "one login for the entire run" without editing
any of the ~55 existing SMS/RCS/WhatsApp/Email test files that depend on
these two fixtures.

### Session-expiry re-authentication

`_open_authenticated_context()` opens its context from the cached state
and checks the landing URL; if it's bounced back to `/login`, the cached
session has expired. It then calls
`reauthenticate_if_still_stale(browser, observed_mtime)`, passing the
state file's mtime **as observed before** this context was opened. That
function:

1. Re-acquires the lock.
2. Compares the file's *current* mtime against `observed_mtime`. If the
   file is now newer, another worker already detected the same
   staleness and finished re-authenticating first — this caller just
   reuses that fresh file instead of logging in again.
3. Otherwise it performs exactly one more real login
   (`_perform_login_recording_failure`), again writing via
   temp-file-then-atomic-`os.replace()` — deliberately **not**
   delete-then-relogin (see the race-condition note below) — and
   releases the lock.

The caller then reopens a context from the (possibly refreshed) state
path; if it's *still* on `/login`, it raises `AuthenticationError` rather
than looping — the suite fails loudly instead of silently running against
a logged-out session.

### Failure handling

If the one real login attempt itself fails (bad credentials, unexpected
redirect, platform error), `_record_failure()` writes a marker file
(`STATE_PATH + ".failed"`, TTL `_FAILURE_MARKER_TTL_SECONDS` = 1800s so it
doesn't block a later, separate rerun) **while the lock is still held**,
then re-raises. Every other caller — already waiting on the lock, or
arriving afterward — checks that marker (`_raise_if_recently_failed()`,
called both before and after acquiring the lock) and raises the *same*
`AuthenticationError` immediately instead of attempting its own login.
pytest reports this as a fixture-setup error on every dependent test, so
one root-cause failure (bad `.env` credentials, app unreachable) shows up
once, clearly, across the whole run — not as one confusing failure per
worker plus a login storm on top of it.

### Race conditions found and fixed during parallel dry-run validation

Three races surfaced only under genuine concurrent load (`pytest -n 5/10/20`
against a local mock login server — see "Validation" below) and are now
covered by the design above:

1. **Duplicate login on concurrent session-expiry** — two workers detecting
   the same expired session at nearly the same instant could both decide
   to re-authenticate. Fixed by making `reauthenticate_if_still_stale()`
   lock-guarded *and* mtime-guarded: a worker only re-logs-in if the file
   on disk is still the exact stale copy it originally observed; if
   someone else already refreshed it, it reuses that instead.
2. **`FileNotFoundError` from a delete-then-relogin race** — an earlier
   version deleted `STATE_PATH` before performing the fresh login, which
   opened a window where a concurrent `browser.new_context(storage_state=
   STATE_PATH)` call elsewhere could hit a missing file. Fixed by never
   deleting the file on the re-auth path — `_perform_login()` always
   overwrites it via an atomic `os.replace()`, so a concurrent reader
   always sees either the old-but-valid content or the new content, never
   nothing.
3. **Login storm on the failure path** — without a failure marker, a
   failed login left no state file behind, so every other waiting/arriving
   worker independently concluded "no state file yet" and attempted its
   own login — the exact storm this whole module exists to prevent, now
   triggered *by* a failure instead of prevented by the lock. Fixed by the
   failure-marker mechanism described above.

`invalidate_authenticated_state()` is a separate, deliberately blunt
maintenance tool (unconditional delete, no lock) for a human forcing a
clean login before the next run — e.g. after rotating `.env` credentials —
and is not used anywhere in the automatic session-expiry path.

Different tenants/environments/channels are handled through
`Config`/`config/environments/<ENV>.env` (§9), not by branching inside the
auth module itself.

### Validation

The real CPaaS+ app is not reachable from a network-restricted sandbox, so
this architecture is validated two ways instead of (and in addition to,
once a network-enabled environment is available for) a real staging run:

1. **`scripts/validate_auth_lock.py`** — an offline harness that spawns N
   real OS processes calling `ensure_authenticated_state()` concurrently
   with `LoginPage` swapped for a fake that records call counts instead of
   doing network I/O. Verifies the lock logic itself in isolation. Run
   with `python3 scripts/validate_auth_lock.py <N>`; passed at N=5, 10,
   and 20 with exactly 1 recorded login call each time.
2. **`scripts/validate_auth_e2e.sh`** (+ `scripts/mock_login_server.py`,
   `scripts/_auth_e2e/`) — a genuine end-to-end run: real Playwright
   browsers, real `pytest -n N` worker *processes*, and the actual
   `conftest.py` fixtures every real test file depends on
   (`logged_in_page` / `module_logged_in_page`, completely unmodified),
   pointed at a small local HTTP server that mimics just the `/login`
   form-submit-redirect flow `LoginPage` drives, instead of the real app.
   This is what proves the fixture wiring itself — not just the
   underlying lock — behaves correctly under real concurrency. Run with
   `./scripts/validate_auth_e2e.sh <N>` (see that script and
   `scripts/mock_login_server.py` for the `PYTHON_BIN`/
   `EXTRA_PYTEST_ARGS` override used to point at a Playwright client
   version matched to whatever browser binaries are actually installed in
   a given environment — a sandbox-only concern, not something the real
   project's normal `pytest` invocation needs).

   Results at N=5, 10, and 20 workers, for both `logged_in_page` and
   `module_logged_in_page`: every test passed, and the mock server's
   `/__stats` counter recorded **exactly one** real `POST /login` per
   pytest invocation regardless of worker count. A follow-up run with a
   deliberately wrong password (N=8) produced 24/24 tests failing with
   the same `AuthenticationError` fixture-setup error and, critically,
   still only **one** real login attempt recorded — confirming the
   failure-marker mechanism (race #3 above) actually prevents a login
   storm on the failure path, not just in theory.

   Not a substitute for a real staging-environment run: it cannot catch a
   locator drifting from the live app's real login page, a slower real
   network round-trip changing timing behavior, or a subtlety in the
   platform's own session-expiry behavior. It exercises the concurrency
   and locking logic — the part that's otherwise very hard to trust
   without either real parallel load or a stand-in for it.

---

## 9. Environment configuration

```bash
ENV=qa pytest tests/sms                 # loads config/environments/qa.env
ENV=staging PLAYWRIGHT_WORKERS=8 python scripts/run_tests.py
pytest tests/sms                        # ENV unset -> loads ./.env only,
                                         #   100% unchanged from before
```

`utils/config.py`: if `ENV` is set and `config/environments/<ENV>.env`
exists, it loads first; the root `.env` (if present) then loads on top
with `override=False`, so a developer's local `.env` can still supply real
credentials without editing the checked-in environment file. `Config` gained
`ENV`, `TENANT`, `API_URL`, `PLAYWRIGHT_WORKERS` fields (all optional,
defaulted, backward compatible — nothing existing broke). Every field the
spec asked for: `BASE_URL`, `API_URL`, credentials, `TENANT`, per-channel
config (`SMS_*`/`EMAIL_*`/`RCS_*` — no `WHATSAPP_*` yet, see
`channels/whatsapp_channel.py`'s docstring for why), `TIMEOUT`
(`EXPLICIT_WAIT`/`IMPLICIT_WAIT`), `WORKERS`, `HEADLESS`. No credential or
environment URL is hard-coded in any test file — everything comes from
`Config`, which comes from `.env`/environment files/real OS env vars. In
CI, set these as secret variables rather than committing a real `.env`.

---

## 10. Page Object Model

Unchanged pattern (`BasePage` superclass, one page object per screen,
`self.h` composes `Helpers` for waiting/retry/screenshot). SMS pages moved
to `pages/sms/` (18 files); WhatsApp/RCS/Email/common pages stay flat —
see "What was NOT done."

---

## 11. API layer

Scaffold only (`api/common/base_client.py` + empty `api/{sms,whatsapp,rcs,email}/`)
— see that file's docstring for why no fabricated client code was written
against unconfirmed endpoints, and the concrete pattern to fill in real
ones later, built on Playwright's own `APIRequestContext` (already a
dependency).

**RCS specifically was investigated** (as a candidate for a minimal
`RCSApiClient` to speed up agent/template setup in
`test_rcs_campaign_create_flow.py`) and found not implementable
responsibly right now: `Config.API_URL` defaults to `""` and is unset in
every `config/environments/*.env` in this repo, no endpoint, auth scheme,
or request/response shape for creating/deleting an RCS agent or template
is documented anywhere in this codebase, and the live platform
(`testqa.cpaas.globeteleservices.com`) wasn't reachable from either the
automation shell used for this work or its cloud counterpart (both got a
403 from an egress proxy) to discover or confirm one directly. Building
`api/rcs/rcs_client.py` against guessed endpoints would be exactly the
"dead code implying capabilities the suite doesn't have" `base_client.py`'s
own docstring warns against — so it wasn't done. If a real RCS API (or a
Postman/Swagger doc for one) exists, share it and this can be revisited.

---

## 12. Fixtures

`fixtures/common_fixtures.py` (`correlation_id`, `test_logger`,
`authenticated_storage_state`, `authenticated_module_page`,
`module_download_dir`) + one `<channel>_fixtures.py` per channel
(`sms_channel`, `whatsapp_channel`, `rcs_channel`, `email_channel` —
function-scoped, built on `logged_in_page`). Registered via
`pytest_plugins` in the root `conftest.py`. No global mutable state in any
of them — everything is either worker-derived (paths, IDs) or plain
per-call data.

**Example parallel tests per channel** (all read-only / non-mutating,
function-scoped `page`, marked `@pytest.mark.smoke` + channel/feature
tags):

- `tests/sms/campaigns/test_sms_parallel_example_flow.py` — unique
  campaign-name round-trip + collision check
- `tests/whatsapp/reports/test_whatsapp_parallel_example_flow.py`
- `tests/rcs/reports/test_rcs_parallel_example_flow.py`
- `tests/email/reports/test_email_parallel_example_flow.py`

Each of the WhatsApp/RCS/Email examples reuses that channel's own
already-existing, already-proven `*OverviewPage` (`navigate_to_report()`,
`is_report_page()`, `get_all_summary_card_values()`/`get_all_card_values()`)
rather than inventing untested new page-object methods.

---

## 13. Test naming and tags

`pytest.ini` `markers`: `smoke`, `regression`, `negative` (unchanged) +
`sms`, `whatsapp`, `rcs`, `email`, `campaign`, `template`, `sender_id`,
`messaging`, `report`, `opt_out`, `agent` (added during the RCS migration,
RCS-only concept), `common` (added during the common-pages batch, no
feature pairing — just `pytest.mark.common`). Every one of the 62 moved
test files (19 SMS + 18 RCS + 11 WhatsApp + 4 Email + 6 common, plus the 4
example files with `.<channel>`/`.report` tags) got a `pytestmark = [...]`
line (mechanical, additive — doesn't touch any test logic). Python/pytest's
equivalent of the spec's `--grep @sms` is `-m`:

```bash
pytest -m sms
pytest -m smoke
pytest -m "sms or whatsapp"
pytest -m "sms and smoke"
```

Verified: `pytest -m sms --collect-only` selects exactly the 645 SMS tests;
`pytest tests/sms --collect-only` selects the same 645 — path-based and
marker-based selection agree.

---

## 14. Reporting

Unchanged `pytest-html`-based report (pass-rate banner, marker badges,
colour-coded durations, screenshot-on-failure, platform-error-monitor
embed) with one correctness fix: the pass/fail/skip counts now come from
`pytest_sessionfinish`'s aggregated `terminalreporter.stats` instead of a
hand-rolled counter that silently zeroed out under `-n` (§1). Screenshots
now land in `reports/screenshots/<worker_id>/` so two workers never
collide on a same-named file. Channel/worker/environment are already
visible per test via markers + the structured log files (§16); the report
itself doesn't yet group rows by channel visually — a follow-up would be a
`pytest-html` results-table column for channel, same mechanism as the
existing marker/duration columns in `conftest.py`.

---

## 15. Failure handling

Unchanged: screenshot + platform-error-monitor capture on failure,
original exception never swallowed by any of the new code. Retries remain
exactly as configurable as before (nothing in this pass added blanket
retries — the project's established principle, documented throughout this
suite's history, is targeted evidence-based fixes over blind retries).

---

## 16. Logging

`utils/logger.py` — `TestLogger(channel, test_name, env)`: every line
carries timestamp, environment, channel, test name, worker ID, and a
correlation ID (`fixtures/common_fixtures.py::correlation_id`, one per
test, threadable into a created campaign/template/message ID). Writes to
stderr (human-readable, visible under `pytest -s` / CI logs) **and** to
`reports/logs/<worker_id>.jsonl` (structured, one file per worker — avoids
interleaved-unreadable output when many workers run at once). This is the
mechanism for correlating a DLR/callback/campaign ID in the live app back
to the exact worker + test that produced it, per the CPaaS-specific
requirement.

---

## 17. Cleanup

Unchanged principle (already established in this project before this
pass): non-mutating example tests were deliberately written read-only so
they need no cleanup at all. `authenticated_storage_state`'s cache file is
the only new on-disk artifact this pass introduces outside `reports/`, and
it's meant to persist across a run (that's the point — reuse). No new
mutating test data is left behind by anything added in this pass.

---

## 18. CI/CD readiness

```bash
npm_equivalent() {
  pip install -r requirements.txt
  python -m playwright install --with-deps chromium
  ENV=staging PLAYWRIGHT_WORKERS=8 python scripts/run_tests.py -m smoke
}
```

Example GitHub Actions-style job:

```yaml
jobs:
  smoke:
    runs-on: ubuntu-latest
    env:
      ENV: staging
      PLAYWRIGHT_WORKERS: 8
      VALID_EMAIL: ${{ secrets.QA_EMAIL }}
      VALID_PASSWORD: ${{ secrets.QA_PASSWORD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: python -m playwright install --with-deps chromium
      - run: python scripts/run_tests.py -m smoke
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-report
          path: reports/
```

No worker count is assumed equal to a developer laptop's — `PLAYWRIGHT_WORKERS`
is a CI variable, set independently per job/runner size.

---

## 19–20. Performance & future channels

Worker defaults per environment start conservative (2–4, see
`config/environments/*.env`) — raise only after confirming the live app's
API/DB tolerates it; nothing here blindly maximizes workers.
`docs/ADDING_A_CHANNEL.md` is the full "add Telegram" walkthrough — the
short version is a new `channels/<x>_channel.py` subclass, a
`fixtures/<x>_fixtures.py`, page objects wherever they already live (or a
new `pages/<x>/` if you want that from day one), and one entry in
`channels/__init__.py`'s registry. Nothing in SMS/WhatsApp/RCS/Email needs
to change.

---

## What was NOT done (and why)

- **Existing SMS/RCS/WhatsApp/Email test files' internal fixtures were not
  rewritten** to use `channels/fixture_factory.py` — only new example files
  use it. Rule: don't rewrite working tests unnecessarily.
- **No fabricated API client code** against endpoints nobody has confirmed
  (`api/` is a scaffold, not fake business logic) — see §11.
- **`WHATSAPP_*` campaign-creation config** doesn't exist in `Config` yet
  because no WhatsApp campaign-creation tests exist yet (current WhatsApp
  coverage is read/analytics-focused) — `WhatsAppChannel` documents exactly
  where to add it when that testing arrives.

### Migration history (completed, same mechanical pattern each time)

1. **SMS** — 18 page objects → `pages/sms/`, 19 test files → `tests/sms/`
   (`campaigns/`, `templates/`, `sender_id/`, `messaging/`, `reports/`,
   `opt_out/`). Reference channel; done first.
2. **RCS** — 19 page objects → `pages/rcs/`, 18 test files → `tests/rcs/`
   (`campaigns/`, `templates/`, `agent/`, `messaging/`, `opt_out/`,
   `reports/`). One inline `os.path.dirname(__file__)`-relative path
   (`test_rcs_campaign_create_flow.py`, contact-file upload) fixed to use
   `utils.test_data_generator.DATA_DIR` before the move. Added the new
   `agent` feature marker (RCS-only concept, no SMS/WhatsApp/Email
   equivalent) to `pytest.ini` and `constants/tags.py`.
3. **WhatsApp** — 12 page objects → `pages/whatsapp/`, 11 test files →
   `tests/whatsapp/` (`reports/`, `opt_out/`). Zero path-breaking patterns
   found — cleanest of the four migrations.
4. **Email** — 5 page objects → `pages/email/`, 4 test files →
   `tests/email/` (`campaigns/`, `templates/`, `reports/`). Zero
   path-breaking patterns found.
5. **Common pages** (final batch) — 8 cross-channel page objects
   (`base_page.py`, `login_page.py`, `dashboard_page.py`,
   `forgot_password_page.py`, `contacts_page.py`, `segmentation_page.py`,
   `tags_page.py`, `communication_flow_page.py`) → `pages/common/`; their 6
   test files → `tests/common/`. This one touched every other channel's
   imports at once — 74 files needed their `pages.base_page` (and, for a
   handful, `pages.login_page`) import updated to `pages.common.*`,
   spanning every SMS/RCS/WhatsApp/Email page object plus `conftest.py`,
   `fixtures/common_fixtures.py`, and 5 stray test files that imported
   `login_page` directly for re-login scenarios. Verified via a full
   recursive grep (not scoped to one channel's folder, unlike the
   per-channel batches) before and after. `tests/test_contacts_flow.py`
   had a `DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")`
   that needed the same `utils.test_data_generator.DATA_DIR` fix used in
   earlier batches, since the file moved one directory deeper.
   `communication_flow_page.py` had zero importers (an orphaned page
   object with no test file — moved anyway, zero risk).

Every batch followed: grep zero cross-channel importers (recursively —
see the note on batch 5 below, where an earlier non-recursive grep in the
RCS/WhatsApp/Email batches missed 3 pre-existing example test files that
lived inside those channels' own subfolders and got their imports fixed
silently by a broader `sed`, but never re-delivered — caught only when
the SMS/RCS/WhatsApp/Email cleanup script removed the flat shims those
example files still depended on) → grep zero internal cross-imports →
grep for `os.path.dirname(__file__)`/hardcoded relative paths and fix any
found → move pages then tests → fix `pages.<ch>_x` → `pages.<ch>.<ch>_x`
imports → add `pytestmark` → verify `py_compile` clean and `pytest
--collect-only -q` count unchanged → verify path-based and marker-based
selection return the identical count for that channel → deliver **every**
file whose import changed, not just the files that physically moved →
shim/stub the old flat paths (the remote-device bridge used for delivery
cannot delete files, so old paths were overwritten with thin re-export
shims for pages and empty stubs for tests, rather than left as risky
duplicates).

**Lesson from this run, worth keeping in mind for any future batch:**
when a `sed` import-fix is scoped to a directory (e.g. `tests/rcs
pages/rcs`), it silently fixes *every* `.py` file under that path,
including ones that weren't part of the "files I'm about to deliver"
mental list — re-deliver the full set the `sed` touched, not just the
files you moved.
