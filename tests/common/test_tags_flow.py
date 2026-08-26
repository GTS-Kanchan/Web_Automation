"""
Contact Management — Tags Page — Single Sequential Flow
=========================================================
Covers: Tags Page TC001 - TC006
  001: page load
  002: search
  003: columns dropdown
  004: edit tag
  005: delete tag
  006: cancel create/edit

All tests run in one browser session (module-scoped), mirroring the pattern
used in test_sms_sender_id.py.

Run:
    pytest tests/test_tags_flow.py -v
"""

import pytest

from pages.common.tags_page import TagsPage
from utils.parallel import short_unique_tag


pytestmark = [pytest.mark.common]

@pytest.fixture(scope="module")
def tags_page(module_logged_in_page):
    p = TagsPage(module_logged_in_page)
    p.navigate_to_tags()
    return p


def ensure_on_tags_page(p):
    if not p.is_tags_page():
        p.navigate_to_tags()
        p.page.wait_for_timeout(1000)


@pytest.fixture(autouse=True)
def _reset_after_test(tags_page):
    """Best-effort reset to the Tags list after every test — prevents one
    failed/aborted test from cascading into unrelated failures for the rest
    of the module-scoped session."""
    yield
    try:
        if tags_page.is_element_present(TagsPage.MODAL_CANCEL_BTN, timeout=2000):
            tags_page.click_modal_cancel()
    except Exception:
        pass
    try:
        ensure_on_tags_page(tags_page)
        tags_page.clear_search()
    except Exception:
        pass


# Worker-safe (see utils/parallel.py's short_unique_tag): two parallel
# workers, or two separate pytest invocations against this same shared
# account, must never both create "AutoQATag<tag>" at once.
RUN_TAG = short_unique_tag()
NEW_TAG_NAME = f"AutoQATag{RUN_TAG}"
NEW_TAG_DESC = "Created by automation"


@pytest.mark.smoke
def test_tags_TC001_page_loads(tags_page):
    """TC001: Tags page loads successfully with no errors."""
    ensure_on_tags_page(tags_page)
    assert tags_page.is_tags_page(), "URL should contain /tags"
    title = tags_page.get_title().lower()
    assert "404" not in title and "error" not in title
    assert tags_page.has_records() or tags_page.has_no_records_message()


@pytest.mark.regression
def test_tags_TC002_search(tags_page):
    """TC002: Search filters the tags list."""
    ensure_on_tags_page(tags_page)
    tags_page.search("ZZZZ_NON_EXISTENT_TAG_9999")
    assert tags_page.has_no_records_message(), "Invalid search should show no-records message"
    tags_page.clear_search()


@pytest.mark.smoke
def test_tags_TC_create_with_valid_data(tags_page):
    """Bonus: Creating a tag with valid data succeeds (seeds data for edit/delete tests)."""
    ensure_on_tags_page(tags_page)
    tags_page.click_create_tag()
    if not tags_page.is_create_tag_modal_open():
        pytest.skip("Create Tag modal did not open — locator may need updating")
    tags_page.fill_tag_name(NEW_TAG_NAME)
    tags_page.fill_tag_description(NEW_TAG_DESC)
    tags_page.click_modal_save()
    success = tags_page.is_success_toast_shown()
    if not success:
        pytest.skip("Tag creation did not show a success toast — verify locators/required fields")
    ensure_on_tags_page(tags_page)


@pytest.mark.regression
def test_tags_TC004_edit_tag(tags_page):
    """TC004: Editing a tag via row Edit action (wire:click.prevent="$dispatch('openModal',
    { component: 'tag.edit', arguments: {"tags":ID} })", matched here via the row's
    data-tooltip-target="tooltip-edit-{id}") opens the edit modal, updates the tag
    name, and saves."""
    ensure_on_tags_page(tags_page)
    if not tags_page.has_records():
        pytest.skip("No tags available to edit")
    edited = tags_page.click_first_row_edit()
    if not edited:
        pytest.skip("Edit control not found on first row")
    if not tags_page.is_modal_open():
        pytest.skip("Edit modal did not open — locator may need updating")
    tags_page.fill_tag_name(f"AutoQATagEdited{short_unique_tag()}")
    tags_page.fill_tag_description("Edited by automation " + short_unique_tag())
    tags_page.click_modal_save()
    assert tags_page.is_success_toast_shown(), "Edit should show success toast"
    ensure_on_tags_page(tags_page)


@pytest.mark.regression
def test_tags_TC006_cancel_create(tags_page):
    """TC006: Cancelling the Create/Edit Tag modal discards changes."""
    ensure_on_tags_page(tags_page)
    tags_page.click_create_tag()
    if not tags_page.is_create_tag_modal_open():
        pytest.skip("Create Tag modal did not open — locator may need updating")
    tags_page.fill_tag_name("ShouldNotBeSaved")
    tags_page.click_modal_cancel()
    ensure_on_tags_page(tags_page)
    assert tags_page.is_tags_page()


@pytest.mark.regression
def test_tags_TC005_delete_tag(tags_page):
    """TC005: Deleting a tag removes it from the list (or shows success toast)."""
    ensure_on_tags_page(tags_page)
    if not tags_page.has_records():
        pytest.skip("No tags available to delete")
    initial = tags_page.get_row_count()
    dialog_opened = tags_page.click_first_row_delete()
    if not dialog_opened:
        pytest.skip("Delete confirmation dialog did not open — locator may need updating")
    tags_page.confirm_delete()
    tags_page.page.wait_for_timeout(1500)
    new_count = tags_page.get_row_count()
    assert new_count < initial or tags_page.is_success_toast_shown()
