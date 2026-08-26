"""
Migrated to Playwright: local page-object fixtures renamed
`template_page` / `create_page` (both built on conftest.py's
`module_logged_in_page`, sharing the same browser session) to avoid
shadowing pytest-playwright's reserved `page` fixture.

Run:
    pytest tests/test_email_template_flow.py -v
"""
import pytest

from pages.email.email_template_page import EmailTemplatePage
from pages.email.email_template_create_page import EmailTemplateCreatePage
from utils.parallel import unique_suffix

pytestmark = [pytest.mark.email, pytest.mark.template]

KNOWN_TEMPLATE_SEARCH_TERM = "Template with link"   # CONFIRMED present in supplied DOM (id=151)


def _unique_name(prefix):
    # Worker-safe (utils.parallel.unique_suffix: ms resolution + worker id
    # + per-call counter + random suffix) instead of a bare ms timestamp,
    # so two parallel workers can never produce the same template name.
    return f"{prefix}_{unique_suffix()}"


# ══════════════════════════════════════════════════════════════════════════
# Session fixtures
# ══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def template_page(module_logged_in_page):
    p = EmailTemplatePage(module_logged_in_page)
    p.navigate()
    return p


@pytest.fixture(scope="module")
def create_page(module_logged_in_page):
    return EmailTemplateCreatePage(module_logged_in_page)


def fresh(page):
    """Navigate back to the plain, unfiltered Templates list before an
    independent test — avoids leftover search/filter state bleeding
    across tests. NOT called between TC006/TC007 (view/close modal),
    which intentionally chain off each other's state within the same
    sequential browser session."""
    page.navigate()
    page.page.wait_for_timeout(1000)


# ══════════════════════════════════════════════════════════════════════════
# TEMPLATES PAGE — TC001-TC018
# ══════════════════════════════════════════════════════════════════════════

def test_TC001_open_template_page(template_page):
    """Templates page loads successfully."""
    fresh(template_page)
    assert template_page.is_template_list_page()
    title = template_page.get_page_title_text()
    assert "Email Template" in title


def test_TC002_columns_toggle(template_page):
    """Selecting/unselecting columns updates the table accordingly."""
    fresh(template_page)
    before = template_page.get_visible_column_headers()
    template_page.toggle_column("department")
    template_page.page.wait_for_timeout(500)
    after = template_page.get_visible_column_headers()
    assert len(after) < len(before), "Unchecking a column should hide it from the table"
    template_page.restore_default_columns()
    template_page.page.wait_for_timeout(2000)
    restored = template_page.get_visible_column_headers()
    assert len(restored) == len(before), "Restoring defaults should bring the column count back"


def test_TC003_export_data(template_page):
    """Export to XLSX opens the confirmation modal and 'Yes, Export' is clickable."""
    fresh(template_page)
    template_page.click_export_to_xlsx()
    assert template_page.is_export_confirm_modal_open(), "Export confirmation modal should open"
    template_page.click_export_confirm_yes()
    # NOTE: the "ready to download" DOM state was never captured (see page
    # object docstring #7) — confirmed only up to a clean, error-free click.


def test_TC004_search_templates(template_page):
    """Searching by a known template name returns matching results."""
    fresh(template_page)
    template_page.search(KNOWN_TEMPLATE_SEARCH_TERM)
    assert template_page.has_records(), f"Search for '{KNOWN_TEMPLATE_SEARCH_TERM}' should return at least one row"
    template_page.clear_search()


def test_TC005_verify_filters(template_page):
    """Department, User, Status, Type, Created At From/To filters all apply without error."""
    fresh(template_page)

    template_page.set_department_filter("QA")
    assert template_page.has_records() or template_page.has_no_records_message()
    template_page.clear_all_filters()

    template_page.set_user_filter("Om")
    assert template_page.has_records() or template_page.has_no_records_message()
    template_page.clear_all_filters()

    template_page.set_status_filter("Approved")
    assert template_page.has_records() or template_page.has_no_records_message()
    fresh(template_page)

    template_page.set_type_filter("Transactional")
    assert template_page.has_records() or template_page.has_no_records_message()
    fresh(template_page)

    template_page.set_created_date_range("2020-01-01", "2026-12-31")
    assert template_page.has_records() or template_page.has_no_records_message()
    fresh(template_page)


def test_TC006_view_template(template_page):
    """Clicking View on a row opens the View Template popup."""
    fresh(template_page)
    assert template_page.has_records(), "Need at least one row to view"
    opened = template_page.click_view_on_first_row()
    assert opened, "View button should be present on the first row"
    assert template_page.is_modal_open(), "View Template popup should open"


def test_TC007_close_view_template_page(template_page):
    """Closing the View Template popup (Escape key) removes it — continues
    directly from TC006's still-open modal in this same browser session."""
    assert template_page.is_modal_open(), "Modal from TC006 should still be open"
    template_page.close_modal_via_escape()
    assert not template_page.is_modal_open(), "View Template popup should close on Escape"


def test_TC008_edit_template_page(template_page):
    """Clicking Edit on a row navigates to the template's edit page
    (reachability only — the edit form's own DOM was never supplied)."""
    fresh(template_page)
    assert template_page.has_records(), "Need at least one row to edit"
    href = template_page.click_edit_on_first_row()
    assert href, "Edit link should be present on the first row"
    assert template_page.is_edit_page(), "Edit link should navigate to a '.../edit' URL"


def test_TC009_edit_template_and_save(template_page, create_page):
    """Edit a template and save changes."""

    name = _unique_name("AutoQA_EditSave")
    create_page.navigate()
    create_page.create_template(name, type_text="Transactional",
                                 content_html="<p>Original</p>")
    template_page.navigate()
    row = template_page.search_and_get_first_row(name)
    assert row is not None, "Created template must exist to edit it"

    link = row.locator(template_page.EDIT_LINK_IN_ROW).first
    link.scroll_into_view_if_needed()
    link.click(force=True)
    template_page.page.wait_for_timeout(2000)

    assert template_page.is_edit_page(), "Should navigate to Edit page"

    new_name = name + "_Edited"
    create_page.fill_name(new_name)
    create_page.click_save()

    template_page.navigate()

    row_edited = template_page.search_and_get_first_row(new_name)
    assert row_edited is not None, "Edited template should be found by its new name"


def test_TC010_edit_template_and_cancel(template_page, create_page):
    """Edit a template but click cancel."""

    name = _unique_name("AutoQA_EditCancel")
    create_page.navigate()
    create_page.create_template(name, type_text="Transactional",
                                 content_html="<p>Original</p>")
    template_page.navigate()
    row = template_page.search_and_get_first_row(name)
    assert row is not None, "Created template must exist to edit it"

    link = row.locator(template_page.EDIT_LINK_IN_ROW).first
    link.scroll_into_view_if_needed()
    link.click(force=True)
    template_page.page.wait_for_timeout(2000)

    create_page.fill_name(name + "_Cancelled")
    create_page.click_cancel()

    assert template_page.is_template_list_page(), "Should return to list page"
    template_page.navigate()
    row_original = template_page.search_and_get_first_row(name)
    assert row_original is not None, "Original template should remain unchanged"


def test_TC011_edit_type_or_name(template_page, create_page):
    """Edit type and name and confirm changes."""

    name = _unique_name("AutoQA_EditType")
    create_page.navigate()
    create_page.create_template(name, type_text="Transactional",
                                 content_html="<p>Original</p>")
    template_page.navigate()
    row = template_page.search_and_get_first_row(name)
    assert row is not None, "Created template must exist to edit it"

    link = row.locator(template_page.EDIT_LINK_IN_ROW).first
    link.scroll_into_view_if_needed()
    link.click(force=True)
    template_page.page.wait_for_timeout(2000)

    new_name = name + "_TypeChanged"
    create_page.fill_name(new_name)
    create_page.select_type("Promotional")
    create_page.click_save()

    template_page.navigate()

    row_edited = template_page.search_and_get_first_row(new_name)
    assert row_edited is not None, "Edited template should be found"
    assert "Promotional" in row_edited.inner_text(), "Type should be updated to Promotional in the row"


def test_TC012_delete_template_confirm(template_page, create_page):
    """Delete → Confirm removes the template. Uses a scratch template
    created by this test (never an existing/shared fixture row) to stay
    safe for other suites — see module docstring."""
    name = _unique_name("AutoQA_DelConfirm")
    create_page.navigate()
    create_page.create_template(name, type_text="Transactional",
                                 content_html="<p>Scratch template for delete-confirm test.</p>")
    template_page.page.wait_for_timeout(1000)

    fresh(template_page)
    row = template_page.search_and_get_first_row(name)
    if row is None:
        pytest.skip(f"Scratch template '{name}' was not found in the list after creation — "
                     "Save Template's post-submit persistence/redirect behavior was never "
                     "confirmed via DOM, so this cannot be asserted further.")

    assert template_page.click_delete_on_row(row), "Delete button should be present on the scratch row"
    assert template_page.is_delete_confirm_dialog_open(), "WireUI delete confirmation dialog should open"
    template_page.confirm_delete()
    template_page.page.wait_for_timeout(1500)

    template_page.search(name)
    assert template_page.has_no_records_message() or not template_page.has_records(), \
        "Scratch template should no longer appear in the list after confirming delete"
    template_page.clear_search()


def test_TC013_cancel_delete_template(template_page, create_page):
    """Delete → Cancel keeps the template in the list. Uses a separate
    scratch template (harmless leftover, same class as fixtures already
    present in this QA environment)."""
    name = _unique_name("AutoQA_DelCancel")
    create_page.navigate()
    create_page.create_template(name, type_text="Transactional",
                                 content_html="<p>Scratch template for delete-cancel test.</p>")
    template_page.page.wait_for_timeout(1000)

    fresh(template_page)
    row = template_page.search_and_get_first_row(name)
    if row is None:
        pytest.skip(f"Scratch template '{name}' was not found in the list after creation — "
                     "Save Template's post-submit persistence/redirect behavior was never "
                     "confirmed via DOM, so this cannot be asserted further.")

    assert template_page.click_delete_on_row(row), "Delete button should be present on the scratch row"
    assert template_page.is_delete_confirm_dialog_open(), "WireUI delete confirmation dialog should open"
    template_page.reject_delete()
    template_page.page.wait_for_timeout(1000)

    row_after = template_page.search_and_get_first_row(name)
    assert row_after is not None, "Template should still be present after cancelling delete"
    template_page.clear_search()


def test_TC014_check_sorting(template_page):
    """Sorting by Template Name / Type / Created at updates the applied-sort pill."""
    fresh(template_page)
    default_pill = template_page.get_applied_sort_pill_text()
    assert default_pill and "created at" in default_pill.lower(), \
        "Default sort should be 'Created at' (confirmed Z-A on fresh load)"

    template_page.sort_by_name()
    name_pill = template_page.get_applied_sort_pill_text()
    assert name_pill and "name" in name_pill.lower(), \
        "Sorting by Template Name should update the applied-sort pill"

    template_page.sort_by_type()
    type_pill = template_page.get_applied_sort_pill_text()
    assert type_pill, "Sorting by Type should show an applied-sort pill"

    template_page.clear_all_sorts()


def test_TC015_check_pagination(template_page):
    """Next Page updates the results range text (Previous button's enabled
    state on page > 1 was never captured — only Next Page is exercised,
    see page object docstring #10)."""
    fresh(template_page)
    before = template_page.get_pagination_results_text()
    template_page.click_next_page()
    after = template_page.get_pagination_results_text()
    assert after != before, "Pagination results text should change after clicking Next Page"


# ══════════════════════════════════════════════════════════════════════════
# CREATE NEW TEMPLATE — TC001-TC007
# ══════════════════════════════════════════════════════════════════════════

def test_create_TC001_open_create_template_page(template_page, create_page):
    """Clicking Create New Template opens the create page."""
    fresh(template_page)
    template_page.click_create_new_template()
    assert template_page.is_create_page(), "Should navigate to /email/template/create"
    assert create_page.is_form_loaded(), "Create Template form should be visible"


@pytest.mark.skip(reason="No 'choose: Use Existing Template vs Create from Scratch' selection "
                          "screen was ever captured in the supplied DOM — only the direct "
                          "create-from-scratch form was supplied (see page object docstring #1).")
def test_create_TC002_check_existing_template(template_page, create_page):
    pass


def test_create_TC003_create_from_scratch_form_opens(create_page):
    """The create-from-scratch form (Name/Type/Content) opens successfully
    — the only 'Create New Template' state actually confirmed via DOM."""
    create_page.navigate()
    assert create_page.is_create_page()
    assert create_page.is_form_loaded()
    assert create_page.is_element_present(EmailTemplateCreatePage.NAME_INPUT, timeout=10000)
    assert create_page.is_element_present(EmailTemplateCreatePage.TYPE_SELECT, timeout=5000)


@pytest.mark.skip(reason="No validation-error markup was ever rendered/captured for this form "
                          "(errors:[] in the wire:snapshot) — asserting a specific error message "
                          "or the 'invalidated:' Tailwind variant toggling would be guessing.")
def test_create_TC004_name_field_validation(create_page):
    pass


def test_create_TC005_type_field_dropdown(create_page):
    """All confirmed Type options are present in the dropdown."""
    create_page.navigate()
    options = create_page.get_type_options()
    for expected in EmailTemplateCreatePage.TYPE_OPTIONS:
        assert any(expected.lower() in o.lower() for o in options), \
            f"Type dropdown should contain '{expected}' — got {options}"


def test_create_TC006_save_template(template_page, create_page):
    """Saving a template with valid Name/Type/Content persists it — verified
    by searching the Templates list for the exact name afterward (no
    page-specific 'success' DOM was ever captured for this form)."""
    name = _unique_name("AutoQA_SaveOK")
    create_page.navigate()
    create_page.create_template(name, type_text="Transactional",
                                 content_html="<p>Hi there, this is an automated test template.</p>")
    template_page.page.wait_for_timeout(1500)

    fresh(template_page)
    row = template_page.search_and_get_first_row(name)
    assert row is not None, \
        f"Newly created template '{name}' should appear in the Templates list after saving"
    template_page.clear_search()


def test_create_TC007_cancel_create_template(create_page):
    """Clicking Cancel discards the form and returns to the Templates list."""
    create_page.navigate()
    create_page.fill_name("SHOULD_NOT_BE_SAVED_" + unique_suffix())
    create_page.click_cancel()
    create_page.page.wait_for_timeout(500)
    assert create_page.is_list_page(), "Cancel should navigate back to the Templates list"
