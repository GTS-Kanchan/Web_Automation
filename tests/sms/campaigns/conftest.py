"""
tests/sms/campaigns/conftest.py

Scoped conftest for the SMS Campaigns UI suite. This directory is
browser/UI-first (SMSCampaignPage, logged_in_page from the root
conftest.py) and normally has no need for the SMS API suite's fixtures.
test_sms_campaign_dlr_bulk.py is the exception -- it drives a real
campaign through the UI (steps 1-10) but then verifies DLRs for the
collected message_ids via the API's bulk endpoint (steps 11-15), so it
needs the `api_client` fixture here too.

This mirrors tests/sms/api/conftest.py's env_config/test_data/
api_request_context/api_client fixtures (same underlying
utils.sms_api_client.SmsApiClient / utils.sms_api_config_loader
functions -- nothing reimplemented, just the same thin pytest wiring
duplicated into this directory, since pytest only loads a conftest's
fixtures for paths on the actual collection path; a conftest under
tests/sms/api is never loaded for tests collected under
tests/sms/campaigns, and vice versa -- see that file's own docstring).

IMPORTANT: this deliberately does NOT call `parser.addoption("--env", ...)`
again. tests/sms/api/conftest.py already registers that flag, and a run
that collects both directories at once (e.g. `pytest tests/sms`) loads
both conftests -- calling addoption for the same flag twice raises an
argparse conflict and aborts the whole run. Instead, env_config below
looks up "--env" defensively: if tests/sms/api/conftest.py registered it
(because this run also collected something under tests/sms/api) it's
used; otherwise this falls back to None, and load_environment_config()'s
own documented fallback chain (ENV_NAME env var, then
config/sms_api/environments.yaml's `active_environment`) takes over --
same behavior as running tests/sms/api's tests without --env.
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


# ─────────────────────────────────────────────────────────────────────────────
# DLR verification for every launched SMS campaign
# ─────────────────────────────────────────────────────────────────────────────
#
# A test that launches a campaign requests `campaign_dlr` and registers the
# campaign right after naming it:
#
#     name = go_to_create(page, "LAUNCH")
#     campaign_dlr.launched(page, name)
#
# If (and only if) the test body then PASSES, pytest_pyfunc_call below opens
# that campaign's report, collects every recipient's message_id via View and
# verifies all DLRs with ONE POST /api/v1/dlr/verify (utils/campaign_dlr.py).
# A DLR failure fails the test itself (not a teardown error). Skipped or
# failed tests never trigger the check. Scheduled campaigns must not register
# (they have no DLRs until their scheduled time).
# Disable globally with SMS_CAMPAIGN_DLR_VERIFY=false.

from utils.campaign_dlr import DLR_VERIFY_ENABLED, verify_campaign_dlrs


class CampaignDlrVerifier:
    def __init__(self, request):
        self._request = request
        self._launched = []

    def launched(self, campaign_page, campaign_name, expected_recipients=None):
        """Register a campaign launched (Send Now) by this test. `campaign_page`
        is the page object (or a Playwright Page) the test used."""
        page = getattr(campaign_page, "page", campaign_page)
        self._launched.append((page, campaign_name, expected_recipients))

    def verify_all(self):
        if not DLR_VERIFY_ENABLED or not self._launched:
            return
        api_client = self._request.getfixturevalue("api_client")
        record_property = self._request.getfixturevalue("record_property")
        for page, name, expected in self._launched:
            try:
                verify_campaign_dlrs(page, api_client, name, record_property=record_property,
                                     expected_recipients=expected)
            finally:
                # module-scoped pages are shared with the next test: leave them on the list page
                try:
                    from pages.sms.sms_campaign_page import SMSCampaignPage
                    SMSCampaignPage(page).open_campaign_list()
                except Exception:
                    pass


@pytest.fixture
def campaign_dlr(request):
    return CampaignDlrVerifier(request)


@pytest.hookimpl(wrapper=True)
def pytest_pyfunc_call(pyfuncitem):
    result = yield  # re-raises if the test body failed or skipped -> no DLR check
    verifier = pyfuncitem.funcargs.get("campaign_dlr")
    if verifier is not None:
        verifier.verify_all()
    return result
