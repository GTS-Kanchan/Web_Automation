"""
tests/sms/api/conftest.py

Scoped conftest for the SMS API automation suite (migrated in from the
standalone `cpaas-api-automation` project). Only loaded for tests under
this directory, so it can't affect the browser-based UI suites elsewhere
in this project (tests/sms/campaigns, tests/rcs/..., etc.) and vice versa.

Adds a --env CLI flag so you can run:
    pytest tests/sms/api --env production
    pytest tests/sms/api --env testqa
without touching any files. Falls back to ENV_NAME env var, then the
`active_environment` set in config/sms_api/environments.yaml.

NOTE on --env: because pytest only registers a CLI flag from a conftest.py
that's actually on the collection path, `--env` is only recognized when
your pytest invocation targets tests/sms/api (or a path under it) --
e.g. `pytest tests/sms/api --env production` or
`python scripts/run_tests.py tests/sms/api --env production`. A broader
run (`pytest tests/sms` or the whole suite) will still collect and run
these tests fine, but won't understand a bare `--env` flag on that
command line -- environment selection then falls back to the ENV_NAME
env var / environments.yaml's `active_environment` default instead.

NOTE on reporting: this conftest deliberately does NOT redefine
pytest_html_results_table_header/row or override config.option.htmlpath
the way the original standalone project's conftest.py did -- the root
conftest.py already implements those hooks (Marker/Duration columns,
reports/test_report.html), and pytest calls every conftest's
implementation of a given hook, so duplicating them here would corrupt
the shared HTML report's column layout. Per-test Expected/Actual values
are still captured via pytest's built-in `record_property` fixture (see
the test files), which lands in the JUnit XML / item.user_properties
regardless of any custom HTML columns.

MIGRATION NOTE (unchanged from the original project): the `playwright`
fixture used below comes from the `pytest-playwright` plugin (already a
dependency of this project), session-scoped, so the underlying
Playwright driver process is started once per test session (per
pytest-xdist worker, if running in parallel). `api_request_context`
builds one Playwright `APIRequestContext` on top of it and reuses it for
the whole session, mirroring how the original framework reused a single
`requests` configuration (base headers / timeout / verify) across all
calls.
"""

import pytest

from utils.sms_api_client import SmsApiClient
from utils.sms_api_config_loader import load_environment_config, load_test_data


def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default=None,
        help="Which SMS API environment/instance to run against (e.g. "
             "testqa, dev, production, malaysia). Overrides ENV_NAME env "
             "var and config/sms_api/environments.yaml's active_environment "
             "default. Only recognized when the pytest invocation targets "
             "tests/sms/api or a path under it -- see this file's module "
             "docstring.",
    )


@pytest.fixture(scope="session")
def env_config(request):
    cli_env = request.config.getoption("--env")
    return load_environment_config(cli_env=cli_env)


@pytest.fixture(scope="session")
def test_data(env_config):
    data = load_test_data()

    # Inject environment-specific IDs into the valid payloads so that test
    # code never needs to branch on env_config.name -- just use valid_payload.
    #
    # IMPORTANT: payloads listed in the skip sets below intentionally carry
    # a specific invalid/nonexistent ID as their test data -- overwriting
    # them would make those negative tests meaningless (they'd always get
    # 200).
    CAMPAIGN_ID_SKIP = {
        "invalid_id_format_payload",  # id: "not-a-valid-uuid"
        "missing_id_payload",          # no id at all -- skip silently
    }
    TEMPLATE_ID_SKIP = {
        "nonexistent_template_id_payload",  # id: "999999999"
        "non_numeric_id_payload",           # id: "not-a-template-id"
        "missing_id_payload",               # no id field
    }

    if env_config.campaign_id:
        for section in ("campaign_send", "send_msg"):
            if section in data:
                for key, payload in data[section].items():
                    if key in CAMPAIGN_ID_SKIP:
                        continue
                    if isinstance(payload, dict) and "id" in payload:
                        payload["id"] = env_config.campaign_id
                    if isinstance(payload, dict) and "campaign_id" in payload:
                        payload["campaign_id"] = env_config.campaign_id

    if env_config.template_id:
        if "template_send" in data:
            for key, payload in data["template_send"].items():
                if key in TEMPLATE_ID_SKIP:
                    continue
                if isinstance(payload, dict) and "id" in payload:
                    payload["id"] = env_config.template_id

    return data


@pytest.fixture(scope="session")
def api_request_context(playwright, env_config):
    """Session-scoped Playwright `APIRequestContext`, created once per
    test session (once per pytest-xdist worker when running in parallel)
    and reused across all API calls -- equivalent to sharing a single
    `requests.Session`/config across the old client.

    `ignore_https_errors` is the Playwright equivalent of the old
    `requests` `verify=False` kwarg; it's configured once here rather
    than per-call."""
    context = playwright.request.new_context(
        ignore_https_errors=not env_config.verify_ssl,
    )
    yield context
    context.dispose()


@pytest.fixture(scope="session")
def api_client(env_config, api_request_context):
    return SmsApiClient(env_config, api_request_context)


def pytest_report_header(config):
    cli_env = config.getoption("--env")
    try:
        env_config = load_environment_config(cli_env=cli_env)
        return [
            f"SMS API automation running against environment: '{env_config.name}'",
            f"Base URL: {env_config.base_url}",
        ]
    except Exception as e:  # keep header non-fatal even if config is broken
        return [f"Could not resolve SMS API environment config for header: {e}"]
