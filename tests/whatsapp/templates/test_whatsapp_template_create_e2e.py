"""
Generic, JSON-driven UI-only E2E test for WhatsApp Template Creation.

ONE test function drives every scenario in test_data/whatsapp_templates.json
via WhatsAppTemplateBuilder -- adding a new valid template scenario means
adding a JSON object, never a new Python test function (see that JSON
file's own module note and whatsapp_template_builder.py's docstring for
the schema and what is/isn't supported yet).

This is UI-only automation: Playwright driving the real Create-page UI
exactly like a user (navigate, select, fill, click Save), verified through
real UI signals (a Preview panel that's actually visible, a Body value
that's actually retained, a post-Save redirect/toast/SweetAlert2 that's
actually observed). No API calls, no direct backend/database access, no
API-based template creation or validation anywhere in this file.

This file is a NEW, separate suite alongside the existing
test_whatsapp_template_create_flow.py -- it does not replace, modify, or
remove any of that file's tests or its own (differently-shaped)
tests/test_data/whatsapp_templates.json.
"""

import pytest

from pages.whatsapp.whatsapp_template_create_page import WhatsAppTemplateCreatePage
from tests.whatsapp.templates.whatsapp_template_builder import (
    WhatsAppTemplateBuilder,
    load_template_test_data,
)


pytestmark = [pytest.mark.whatsapp, pytest.mark.template]


@pytest.fixture(scope="module")
def create_page(module_logged_in_page):
    return WhatsAppTemplateCreatePage(module_logged_in_page)


@pytest.mark.parametrize(
    "template",
    load_template_test_data(),
    ids=lambda template: template["id"],
)
def test_whatsapp_template_creation_e2e(create_page, template):
    # Fresh page load per template (not just per-module) -- several real,
    # confirmed WireUI selects on this page (Sender ID, Language,
    # sub_category, ...) TOGGLE an already-selected option OFF if clicked
    # again rather than being idempotent (see
    # ensure_sub_category_selected's docstring in the Page Object for the
    # original evidence). A fresh navigate() per template guarantees every
    # scenario starts from the same known, default UI state instead of
    # inheriting whatever the previous parametrized template left behind.
    create_page.navigate()

    builder = WhatsAppTemplateBuilder(create_page)

    builder.create(template)
    builder.verify_preview(template)
    builder.save_and_verify_ui(template)
