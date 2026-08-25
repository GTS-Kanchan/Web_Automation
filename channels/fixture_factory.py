"""
channels/fixture_factory.py — eliminates the copy-pasted module-scoped
page-object fixture that exists (in slightly different shapes) at the top
of every one of the 19 SMS flow files, e.g.:

    @pytest.fixture(scope="module")
    def campaign_page(module_logged_in_page):
        generate_all()
        camp = SMSCampaignPage(module_logged_in_page)
        camp.open_campaign_list()
        return camp

This is a genuinely identified duplicate-code pattern (same 4-line shape,
19 times, one per existing SMS test file) — see the architecture doc for
the full inventory. Existing test files are NOT rewritten to use this (the
"preserve working tests" rule from the request), but every NEWLY migrated
or newly written channel test file should build its page-object fixture
with this factory instead of repeating the boilerplate again.

Usage (new test file):

    from channels.fixture_factory import module_page_fixture
    from pages.sms.sms_campaign_page import SMSCampaignPage

    campaign_page = module_page_fixture(
        SMSCampaignPage, setup=lambda p: p.open_campaign_list()
    )
"""
import pytest


def module_page_fixture(page_object_cls, setup=None):
    """Returns a pytest fixture function, scope="module", that:
      1. builds `page_object_cls(module_logged_in_page)`
      2. calls `setup(page_object)` if given (e.g. navigate to the right
         list/tab before the module's tests start)
      3. returns the page object

    `setup` receives the page object and may return a value; if it does,
    that value replaces the page object as the fixture's yielded value
    (matches the existing per-file pattern where e.g. `open_campaign_list()`
    is called for its side effect and the original page object is returned).
    """
    @pytest.fixture(scope="module")
    def _fixture(module_logged_in_page):
        page_object = page_object_cls(module_logged_in_page)
        if setup is not None:
            result = setup(page_object)
            if result is not None:
                return result
        return page_object

    return _fixture
