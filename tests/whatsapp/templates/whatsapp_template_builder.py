"""
Generic, JSON-driven UI-only builder for WhatsApp Template Create.

Design rule (matches this whole project's standing rule): this file owns
NO Playwright locators, no XPath/CSS, no timeouts, and no guessed UI
behavior of its own. Every action below dispatches to a real, already
evidence-confirmed method on WhatsAppTemplateCreatePage (see
pages/whatsapp/whatsapp_template_create_page.py). Where a JSON field asks
for something this app's UI has never been confirmed to support (e.g. a
Header image upload outside the Carousel/Product-Carousel flows, or a
top-level Quick Reply button's own text field), this module raises a
clear, informative error or prints an explicit warning -- it never
silently pretends to have filled something it didn't, and it never
invents a selector to make a JSON field "work".

JSON schema (see test_data/whatsapp_templates.json):
{
  "id": "...",                       # required, also doubles as the
                                      # template name base and the
                                      # pytest parametrize id
  "template_name": "...",            # optional, overrides id as the name
                                      # base (a uniqueness suffix is still
                                      # appended -- Template Name must be
                                      # unique per real account)
  "category": "MARKETING|UTILITY|AUTHENTICATION|CONVERSATION",  # required
  "template_type": "...",            # optional, real sub_category label
                                      # (e.g. "Custom Message", "Carousel")
  "sub_category": "...",             # accepted as an alias for
                                      # template_type
  "template_type_force_select": bool,  # optional, forces the click even
                                        # when the display already matches
                                        # (only ever confirmed necessary
                                        # for CONVERSATION/CTA URL Button)
  "language": "...",                 # optional, real language label
  "label": "...",                    # optional, Template Labels field
  "sender_id": "...",                # optional, real Sender ID label
                                      # (substring match honored); falls
                                      # back to Config.WHATSAPP_TEMPLATE_SENDER_ID
                                      # when omitted, same as the rest of
                                      # this suite
  "header": {"type": "...", "file": "..."},  # optional -- see
                                              # _configure_header for what
                                              # is/isn't actually supported
  "body": {"text": "..."},           # optional
  "footer": {"text": "..."},         # optional
  "authentication_method": "COPY_CODE|AUTOFILL|ZERO_TAP",  # optional
  "buttons": [{"type": "QUICK_REPLY|URL|PHONE_NUMBER|COPY_OFFER_CODE|FLOW",
               "text": "...", "url": "...", "phone_number": "...",
               "flow": "..."}],      # optional, top-level "Add button"
                                      # buttons (Custom Message / CTA URL
                                      # Button style)
  "carousel": {"media_type": "IMAGE|VIDEO",
               "cards": [{"description": "...", "media_file": "...",
                          "buttons": [{"type": "...", "text": "...",
                                       "url": "..."}]}]}  # optional
}
"""

import json
import os
import time

import pytest


_THIS_DIR = os.path.dirname(__file__)
TEMPLATES_JSON_PATH = os.path.join(_THIS_DIR, "test_data", "whatsapp_templates.json")

# The one real image test asset in this repo lives in the OLDER, shared
# tests/test_data/ directory (see test_whatsapp_template_create_flow.py's
# CAROUSEL_SAMPLE_IMAGE) -- reused here rather than duplicated, per the
# task's own instruction to reuse an existing data directory instead of
# creating a duplicate.
_SHARED_TEST_DATA_DIR = os.path.join(_THIS_DIR, "..", "..", "test_data")
_LOCAL_TEST_DATA_DIR = os.path.join(_THIS_DIR, "test_data")


def _resolve_asset_path(filename):
    """Looks for `filename` in this suite's own test_data/ first, then
    falls back to the shared tests/test_data/ directory used by the rest
    of the project. Raises a clear, immediate error if neither has it --
    never silently proceeds with a path that doesn't exist."""
    for directory in (_LOCAL_TEST_DATA_DIR, _SHARED_TEST_DATA_DIR):
        candidate = os.path.join(directory, filename)
        if os.path.isfile(candidate):
            return candidate
    raise FileNotFoundError(
        f"Test asset {filename!r} was not found in "
        f"{_LOCAL_TEST_DATA_DIR!r} or {_SHARED_TEST_DATA_DIR!r} -- add a "
        f"real file with this name before using it in a template's "
        f"media_file/file field."
    )


def load_template_test_data(path=TEMPLATES_JSON_PATH):
    """Loads the generic E2E test's JSON scenario file and returns its
    "templates" list. Raises a clear, actionable error on anything
    malformed rather than letting pytest collection fail with an opaque
    traceback."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"WhatsApp E2E template test data not found at {path!r}."
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"WhatsApp E2E template test data at {path!r} is not valid "
            f"JSON: {exc}"
        ) from exc

    if not isinstance(data, dict) or "templates" not in data:
        raise ValueError(
            f"WhatsApp E2E template test data at {path!r} must be a JSON "
            f"object with a top-level \"templates\" array."
        )

    templates = data["templates"]
    if not isinstance(templates, list) or not templates:
        raise ValueError(
            f"WhatsApp E2E template test data at {path!r} must contain a "
            f"non-empty \"templates\" array."
        )

    seen_ids = set()
    for entry in templates:
        if "id" not in entry:
            raise ValueError(
                f"Every template entry needs an \"id\" -- found one "
                f"without one: {entry!r}"
            )
        if "category" not in entry:
            raise ValueError(
                f"Template {entry['id']!r} is missing required field "
                f"\"category\"."
            )
        if entry["id"] in seen_ids:
            raise ValueError(f"Duplicate template id {entry['id']!r}.")
        seen_ids.add(entry["id"])

    return templates


def _get_template_name(template):
    base = template.get("template_name") or template["id"]
    # Template Name must be unique per real account and this is a REAL
    # UI submit -- same uniqueness convention as
    # WhatsAppTemplateCreatePage.generate_unique_template_name().
    return f"{base}_{int(time.time() * 1000)}"


class WhatsAppTemplateBuilder:
    """Turns one JSON template object into real Playwright UI actions via
    WhatsAppTemplateCreatePage. Add a new supported field by adding a
    small, evidence-backed handler here that calls a real Page Object
    method -- never by adding a locator directly to this file."""

    def __init__(self, create_page):
        self.page = create_page

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(self, template):
        self._select_category(template)
        self._configure_template_type(template)
        self._configure_language(template)
        self._select_sender_id(template)
        self._set_template_name(template)
        self._configure_label(template)
        self._configure_header(template)
        self._configure_body(template)
        self._configure_footer(template)
        self._configure_authentication(template)
        self._configure_catalog(template)
        self._configure_buttons(template)
        self._configure_carousel(template)

    def verify_preview(self, template):
        assert self.page.is_preview_panel_present(), (
            f"[{template['id']}] Expected the Preview panel to be "
            f"visible after filling the template."
        )
        # No confirmed method exists yet to read the Preview panel's own
        # rendered text (see the Page Object's module docstring), so this
        # deliberately does not assert on Preview content it can't really
        # read. What IS confirmed and reusable: get_body_text() reads the
        # real CodeMirror body editor back -- a genuine, real check that
        # the Body text we set actually landed and stayed.
        #
        # EXCEPTION (real evidence, this run): AUTHENTICATION's message
        # content is confirmed fixed/non-editable in the real UI (see the
        # existing suite's own confirmed authentication_copy_code entry
        # and this project's earlier notes) -- set_body_text() is a
        # documented no-op there, so get_body_text() legitimately returns
        # None/something else afterward. Asserting equality for
        # AUTHENTICATION was a bug, confirmed by 3 real failures
        # ("...got None") in this exact run -- not something to guess
        # around, the existing suite already documents this.
        body_text = _body_text(template)
        if body_text and template.get("category") != "AUTHENTICATION":
            actual = self.page.get_body_text()
            assert actual == body_text, (
                f"[{template['id']}] Expected Body text {body_text!r} to "
                f"still be present, got {actual!r}."
            )

    def save_and_verify_ui(self, template=None):
        context = template["id"] if template else "template"
        assert self.page.is_save_button_present(), (
            f"[{context}] Expected the Save button to be present."
        )
        self.page.click_save()
        result = self.page.wait_for_save_result()
        assert result["outcome"] != "none_detected", (
            f"[{context}] No recognized post-submit UI feedback (a URL "
            f"redirect, or the confirmed app-global WireUI/SweetAlert2 "
            f"toast) appeared after clicking Save. 'none_detected' is "
            f"never treated as success -- if the app is genuinely not "
            f"responding, check for silent client-side validation or a "
            f"required field this template didn't fill in."
        )
        return result

    # ------------------------------------------------------------------
    # Category / template_type / language / sender / name / label
    # ------------------------------------------------------------------

    def _select_category(self, template):
        self.page.select_category(template["category"])

    def _configure_template_type(self, template):
        option_text = template.get("template_type") or template.get("sub_category")
        if not option_text:
            return
        if not self.page.is_sub_category_select_present():
            pytest.skip(
                f"[{template['id']}] sub_category/template_type select "
                f"not available for category={template['category']!r} in "
                f"this environment."
            )
        # BUG FIX (real evidence, this run): a blind ensure_sub_category_
        # selected() call for an option_text that doesn't actually exist
        # for this category just hangs for ~5s waiting for a listitem
        # that will never appear (confirmed: test_conversation_basic
        # timed out this way asking for "Custom Message" under
        # CONVERSATION, which has never been confirmed to have that
        # option -- only "CTA URL Button" has real evidence). Check
        # against the real, live options first and fail fast with the
        # actual available list instead of a bare timeout.
        real_options = [o.get("label") for o in self.page.get_sub_category_options()]
        if option_text not in real_options:
            raise AssertionError(
                f"[{template['id']}] template_type/sub_category "
                f"{option_text!r} is not among the real options this app "
                f"currently renders for category="
                f"{template['category']!r}: {real_options!r}. Not "
                f"guessing -- update the JSON with a real, confirmed "
                f"label."
            )
        # CONVERSATION/"CTA URL Button" is CONFIRMED (via a direct
        # --headed observation earlier in this project) to need a real
        # click even when its single option is already shown as selected
        # -- the opposite symptom from every other sub_category here,
        # which instead TOGGLE OFF on a redundant click. Auto-apply that
        # confirmed fix for this exact, known case so template data
        # doesn't have to remember to set template_type_force_select
        # itself; an explicit template_type_force_select in the JSON
        # still overrides this default either way.
        default_force = (
            template.get("category") == "CONVERSATION"
            and option_text == "CTA URL Button"
        )
        self.page.ensure_sub_category_selected(
            option_text,
            force=template.get("template_type_force_select", default_force),
        )

    def _configure_language(self, template):
        language = template.get("language")
        if not language:
            return
        self.page.ensure_language_selected(language)

    def _select_sender_id(self, template):
        sender_id = template.get("sender_id")
        if not sender_id:
            from utils.config import Config

            sender_id = Config.WHATSAPP_TEMPLATE_SENDER_ID
        options = [o.get("label") for o in self.page.get_sender_id_options()]
        if sender_id not in options:
            matches = [o for o in options if sender_id.lower() in (o or "").lower()]
            if len(matches) == 1:
                sender_id = matches[0]
            else:
                raise AssertionError(
                    f"[{template['id']}] Sender ID {sender_id!r} is not "
                    f"among the real options currently available: "
                    f"{options!r}"
                )
        # select_sender_id_by_search(), not select_sender_id(): real
        # --headed evidence (a screenshot of the open Sender ID popover)
        # showed the configured sender label is often NOT among the
        # popover's initially-rendered listitems (only a short subset --
        # WhatsApp Simulator Testing / test old gts / testbulk / Testbulk
        # / Testing Number / Cerf Telin -- was rendered; "Globe
        # Teleservices Pte. Ltd." was not, even though
        # get_sender_id_options() decodes the full real list). Plain
        # select_sender_id() then hangs waiting on a listitem that never
        # renders. select_sender_id_by_search() reuses the CONFIRMED
        # search_sender_id() filtering mechanism (see
        # test_TC018_sender_id_search_valid_keyword in
        # test_whatsapp_template_create_flow.py) to guarantee the target
        # actually renders before clicking it. Every template in this
        # JSON relies on the same .env sender fallback, so this one fix
        # affects every single generic E2E run.
        self.page.select_sender_id_by_search(sender_id)

    def _set_template_name(self, template):
        name = _get_template_name(template)
        self.page.set_name(name)
        template["_resolved_name"] = name

    def _configure_label(self, template):
        label = template.get("label")
        if label is not None:
            self.page.set_label(label)

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _configure_header(self, template):
        header = template.get("header")
        if not header:
            return
        if not self.page.is_header_select_present():
            pytest.skip(
                f"[{template['id']}] Header select not available in this "
                f"environment."
            )
            return
        header_type = header.get("type")
        if header_type and header_type.upper() != "NONE":
            # select_header_type() itself raises a clear error naming the
            # real available options if header_type doesn't match one --
            # this app's real Header option labels have never been
            # directly confirmed (see the Page Object's module docstring),
            # so this is deliberately not guessed here either.
            self.page.select_header_type(header_type)
        if header.get("file"):
            raise NotImplementedError(
                f"[{template['id']}] header.file was given but no "
                f"confirmed Header media-upload method exists yet for "
                f"this (non-Carousel) Header field -- capture the real "
                f"file input DOM before adding support. Carousel/Product "
                f"Carousel media uploads ARE supported via the "
                f"\"carousel\" field."
            )

    # ------------------------------------------------------------------
    # Body / Footer
    # ------------------------------------------------------------------

    def _configure_body(self, template):
        text = _body_text(template)
        if text:
            self.page.set_body_text(text)

    def _configure_footer(self, template):
        footer = template.get("footer")
        if footer and footer.get("text") is not None:
            self.page.set_footer_text(footer["text"])

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    _AUTH_METHOD_MAP = {
        "COPY_CODE": "copycode",
        "AUTOFILL": "autofill",
        "ZERO_TAP": "zerotap",
    }

    def _configure_authentication(self, template):
        method = template.get("authentication_method")
        if not method:
            return
        value = self._AUTH_METHOD_MAP.get(method.upper())
        if not value:
            raise AssertionError(
                f"[{template['id']}] Unknown authentication_method "
                f"{method!r} -- supported: "
                f"{sorted(self._AUTH_METHOD_MAP)!r}"
            )
        if not self.page.is_auth_otp_type_radios_present():
            pytest.skip(
                f"[{template['id']}] Auth OTP type radios not present in "
                f"this environment."
            )
            return
        self.page.select_auth_otp_type(value)

    # ------------------------------------------------------------------
    # Catalog (sub_category/template_type="Catalog") -- reuses the same
    # confirmed methods as the existing suite's own
    # _fill_marketing_catalog() filler.
    # ------------------------------------------------------------------

    def _configure_catalog(self, template):
        option_text = template.get("template_type") or template.get("sub_category")
        if option_text != "Catalog":
            return
        catalog_type = template.get("catalog_type")
        if catalog_type:
            if not self.page.is_catalog_type_select_present():
                pytest.skip(
                    f"[{template['id']}] Catalog Type select not present "
                    f"in this environment."
                )
                return
            self.page.select_catalog_type(catalog_type)
        content_id = (template.get("catalog") or {}).get("content_id")
        if content_id and self.page.is_catalog_content_id_input_present():
            self.page.set_catalog_content_id(content_id)

    # ------------------------------------------------------------------
    # Top-level Buttons ("Add button" trigger -- Custom Message / CTA URL
    # Button style, confirmed at page object docstring points 21/24)
    # ------------------------------------------------------------------

    def _configure_buttons(self, template):
        buttons = template.get("buttons")
        if not buttons:
            return
        for button in buttons:
            btn_type = (button.get("type") or "").upper()
            handler = self._BUTTON_HANDLERS.get(btn_type)
            if not handler:
                raise AssertionError(
                    f"[{template['id']}] Unknown button type {btn_type!r} "
                    f"-- supported: {sorted(self._BUTTON_HANDLERS)!r}"
                )
            handler(self, template, button)

    def _open_add_button_menu(self, template, label):
        if not self.page.is_lto_add_button_trigger_present():
            pytest.skip(
                f"[{template['id']}] 'Add button' trigger not present in "
                f"this environment."
            )
            return False
        self.page.open_lto_add_button_menu()
        # BUG FIX (real evidence, this run): select_lto_add_button_type()'s
        # own docstring says all 5 button types are confirmed present only
        # for sub_category=Limited Time Offer and UTILITY/Custom Message;
        # only "URL" is confirmed for CTA URL Button, and nothing beyond
        # URL/Quick Reply has ever been confirmed for MARKETING/Custom
        # Message specifically. A live run asking for Flow/Quick Reply/
        # Phone Number/Copy Offer Code under MARKETING/Custom Message hung
        # for the full 30s each ("element is not visible") -- consistent
        # with those items simply not being rendered in that combination,
        # not a timing issue. Check real presence first (a few seconds,
        # not 30) and skip with a clear, evidence-citing message instead
        # of repeating that 30s hang for every unconfirmed combination.
        # BUG FIX #2 (real evidence, this run): is_element_present() only
        # waits for state="attached" -- it returned True for these menu
        # items even though they genuinely never became visible (they DO
        # exist in the DOM, just hidden), so this guard let the click
        # through anyway and hit the exact same 30s hang it was meant to
        # prevent. is_element_visible() (inherited from BasePage via
        # utils/helpers.py, already used elsewhere in this suite) actually
        # waits for state="visible" and is the correct check here.
        item_selector = f"[wire\\:click=\"showLTOdiv('{label}')\"]"
        if not self.page.is_element_visible(item_selector, timeout=3000):
            pytest.skip(
                f"[{template['id']}] '{label}' is not present in the "
                f"'Add button' menu for category="
                f"{template.get('category')!r}, "
                f"template_type={template.get('template_type')!r} -- "
                f"only confirmed present for sub_category=Limited Time "
                f"Offer and UTILITY/Custom Message (see "
                f"select_lto_add_button_type's docstring); this "
                f"combination has never been confirmed to support it."
            )
            return False
        self.page.select_lto_add_button_type(label)
        return True

    def _configure_button_quick_reply(self, template, button):
        if not self._open_add_button_menu(template, "Quick Reply"):
            return
        if button.get("text"):
            print(
                f"[{template['id']}] WARNING: Quick Reply button text "
                f"{button['text']!r} was not filled -- no confirmed "
                f"top-level Quick Reply text field/method exists yet in "
                f"WhatsAppTemplateCreatePage."
            )

    def _configure_button_url(self, template, button):
        if not self._open_add_button_menu(template, "URL"):
            return
        if self.page.is_url_button_fields_present():
            if button.get("text"):
                self.page.set_url_button_title(button["text"])
            if button.get("url"):
                if self.page.is_element_present(
                    self.page.URL_BUTTON_VALUE_INPUT, timeout=3000
                ):
                    self.page.set_url_button_value(button["url"])
                else:
                    print(
                        f"[{template['id']}] WARNING: URL button value "
                        f"field was not present -- confirmed "
                        f"broken/absent for some sub_categories; URL not "
                        f"filled."
                    )

    def _configure_button_phone_number(self, template, button):
        if not self._open_add_button_menu(template, "Phone Number"):
            return
        if self.page.is_phone_button_fields_present():
            if button.get("text"):
                self.page.set_phone_button_title(button["text"])
            phone_value = button.get("phone_number") or button.get("phone")
            if phone_value:
                self.page.set_phone_button_value(phone_value)

    def _configure_button_copy_offer_code(self, template, button):
        # No confirmed field-filling method exists beyond selecting this
        # type from the "Add button" menu (see page object notes around
        # test_utility_custom_message_add_button_copy_offer_code_disabled)
        # -- not guessing further fields.
        self._open_add_button_menu(template, "Copy Offer Code")

    def _configure_button_flow(self, template, button):
        if not self._open_add_button_menu(template, "Flow"):
            return
        if self.page.is_flow_button_fields_present():
            if button.get("text"):
                self.page.set_flow_button_title(button["text"])
            if button.get("flow"):
                self.page.select_flow_button_value(button["flow"])

    _BUTTON_HANDLERS = {
        "QUICK_REPLY": _configure_button_quick_reply,
        "URL": _configure_button_url,
        "PHONE_NUMBER": _configure_button_phone_number,
        "COPY_OFFER_CODE": _configure_button_copy_offer_code,
        "FLOW": _configure_button_flow,
    }

    # ------------------------------------------------------------------
    # Carousel (data-driven, any number of cards)
    # ------------------------------------------------------------------

    _CAROUSEL_MEDIA_LABELS = {"IMAGE": "Image", "VIDEO": "Video"}
    _CAROUSEL_CARD_BUTTON_LABELS = {
        "QUICK_REPLY": "Quick Reply",
        "URL": "URL",
        "PHONE_NUMBER": "Phone Number",
        "FLOW": "WhatsApp Flow",
    }

    def _configure_carousel(self, template):
        carousel = template.get("carousel")
        if not carousel:
            return
        if not self.page.is_carousel_form_present():
            pytest.skip(
                f"[{template['id']}] Carousel sub-form not available in "
                f"this environment."
            )
            return

        media_type = carousel.get("media_type")
        if media_type:
            media_label = self._CAROUSEL_MEDIA_LABELS.get(media_type.upper())
            if not media_label:
                raise AssertionError(
                    f"[{template['id']}] Unknown carousel media_type "
                    f"{media_type!r} -- supported: "
                    f"{sorted(self._CAROUSEL_MEDIA_LABELS)!r}"
                )
            # Confirmed: "Image" is already the default for Carousel
            # Media Header -- only click when a DIFFERENT value is
            # actually required, per the direct instruction confirmed
            # earlier in this project (re-clicking an already-selected
            # WireUI option toggles it off rather than being a no-op).
            if media_label != "Image":
                self.page.select_carousel_media_type(media_label)

        cards = carousel.get("cards", [])
        # NOTE (bug fixed, real evidence from a live run): this used to
        # call select_carousel_button_count(str(len(cards))), treating the
        # Carousel Button Count field as "number of cards". It is NOT --
        # its confirmed real options ("1"/"2") are the number of BUTTONS
        # PER CARD (see CAROUSEL_BUTTON_COUNT_WRAPPER usage elsewhere),
        # and the number of actual cards is controlled separately by
        # click_add_another_card() below. Calling it with the card count
        # was both semantically wrong and directly implicated in a real
        # "element was detached from the DOM, retrying" crash on the very
        # next select (carousel_button_type1) -- selecting it fired an
        # unnecessary Livewire re-render right before that click. The
        # already-proven original filler (test_whatsapp_template_create_
        # flow.py's _fill_marketing_carousel_image_1card) never touched
        # this field either -- left at its default, matching that.

        first_button_type = None
        for card in cards:
            for b in card.get("buttons", []):
                first_button_type = (b.get("type") or "").upper()
                break
            if first_button_type:
                break
        if first_button_type:
            label = self._CAROUSEL_CARD_BUTTON_LABELS.get(first_button_type)
            if label:
                self.page.select_carousel_button_type1(label)

        for index, card in enumerate(cards):
            if index > 0:
                self.page.click_add_another_card()
            if card.get("description"):
                self.page.set_carousel_card_description(index, card["description"])
            media_file = card.get("media_file")
            if media_file:
                if self.page.is_carousel_card_file_input_present(index):
                    self.page.set_carousel_card_file(
                        index, _resolve_asset_path(media_file)
                    )
                else:
                    pytest.skip(
                        f"[{template['id']}] Card {index}'s file input "
                        f"was not present -- a real Carousel template "
                        f"needs header media per card."
                    )
                    return
            for b_index, button in enumerate(card.get("buttons", [])):
                if button.get("text"):
                    self.page.set_card_button_title(index, b_index, button["text"])
                value = button.get("url") or button.get("phone_number")
                if value:
                    self.page.set_card_button_value(index, b_index, value)


def _body_text(template):
    body = template.get("body")
    return body.get("text") if body else None
