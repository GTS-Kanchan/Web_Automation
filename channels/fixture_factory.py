
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
