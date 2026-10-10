"""
tests/rcs/campaigns/conftest.py

Scoped conftest for the RCS Campaigns UI suite. This directory is
browser/UI-first (RcsCampaignCreatePage/RCSCampaignPage, logged_in_page
from the root conftest.py) and normally has no need for the SMS API
suite's fixtures. test_rcs_campaign_create_flow.py::
test_e2ecopypastenumber_send_now is the exception -- it drives a real
RCS campaign through the UI (Create -> Send Now) and then verifies the
resulting webhook/DLR events via utils/rcs_campaign_dlr.py, which polls
GET {dlr_base_url}/api/v1/dlr/{message_id} through the SAME
utils.sms_api_client.SmsApiClient.get_dlr() the SMS DLR tests already
use (confirmed identical host/endpoint shape -- see
utils/rcs_dlr_helpers.py's module docstring), so it needs an `api_client`
fixture here too.

This mirrors tests/sms/campaigns/conftest.py's env_config/
api_request_context/api_client fixtures (same underlying
utils.sms_api_client.SmsApiClient / utils.sms_api_config_loader
functions -- nothing reimplemented, just the same thin pytest wiring
duplicated into this directory, since pytest only loads a conftest's
fixtures for paths on the actual collection path).

Deliberately does NOT include tests/sms/campaigns/conftest.py's
`campaign_dlr` fixture / `pytest_pyfunc_call` auto-verify hook -- the
RCS DLR check is wired directly, inline, into
test_e2ecopypastenumber_send_now itself (via
utils.rcs_campaign_dlr.verify_rcs_campaign_dlrs()) rather than through
an implicit post-test hook, per the project owner's explicit
instruction to integrate the verification into that existing test
rather than add new indirection around it.

IMPORTANT: this deliberately does NOT call `parser.addoption("--env", ...)`
again -- same defensive lookup as tests/sms/campaigns/conftest.py, to
avoid an argparse conflict when a run collects tests/sms/api too (which
registers that flag). See that file's own docstring for the full
rationale; this is a byte-for-byte port of its env_config/
api_request_context/api_client fixtures into this directory.
"""

import pytest

from utils.sms_api_client import SmsApiClient
from utils.sms_api_config_loader import load_environment_config, load_test_data


@pytest.fixture(scope="session")
def env_config(request):
    try:
        cli_env = request.config.getoption("--env")
    except ValueError:
        # --env wasn't registered in this run (tests/sms/api/conftest.py's
        # pytest_addoption didn't fire because nothing under tests/sms/api
        # was collected) -- fall back to ENV_NAME / environments.yaml.
        cli_env = None
    return load_environment_config(cli_env=cli_env)


@pytest.fixture(scope="session")
def test_data(env_config):
    return load_test_data()


@pytest.fixture(scope="session")
def api_request_context(playwright, env_config):
    context = playwright.request.new_context(
        ignore_https_errors=not env_config.verify_ssl,
    )
    yield context
    context.dispose()


@pytest.fixture(scope="session")
def api_client(env_config, api_request_context):
    return SmsApiClient(env_config, api_request_context)
