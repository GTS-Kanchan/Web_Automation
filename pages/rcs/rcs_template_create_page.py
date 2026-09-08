import os
import time

from pages.common.base_page import BasePage
from utils.config import Config, DOWNLOAD_DIR


class RcsTemplateCreatePage(BasePage):

    CREATE_URL = "/rcs/template/create"
    LIST_URL = "/rcs/template"

    # Best-effort -- mirrors the confirmed BTN_EXPORT convention already
    # proven on RCSCampaignPage (rcs_campaign_page.py), the closest
    # sibling "list export" screen, since this button was never
    # independently confirmed on the Template list itself. See
    # click_export_csv() below for how a locator miss degrades (skip,
    # not a guessed-selector failure).
    BTN_EXPORT = "xpath=//button[contains(.,'Export')] | //a[contains(.,'Export')]"

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_HEADING = (
        "xpath=//h1[contains(normalize-space(.),'Create') and "
        "contains(normalize-space(.),'Template')] | "
        "//h2[contains(normalize-space(.),'Create') and "
        "contains(normalize-space(.),'Template')]"
    )
    BREADCRUMB = "nav[aria-label='Breadcrumb']"

    # ── Global WireUI notification toast ────────────────────────────────────
    NOTIFICATION_TITLE = "xpath=//div[@x-data='wireui_notifications']//p[@x-show='notification.title']"

    # ── Form fields ──────────────────────────────────────────────────────────
    NAME_INPUT = "#name"
    TYPE_SELECT = "#type"
    # Plain <textarea> (NOT TinyMCE) — confirmed by emoji-picker in DOM
    BODY_TEXTAREA = (
        "xpath=//textarea[contains(@*[name()='wire:model.live'],'message_content') "
        "or contains(@*[name()='wire:model.defer'],'body') "
        "or contains(@*[name()='wire:model'],'body') "
        "or @id='message_content-input' or @name='message_content']"
    )
    # Emoji picker trigger button (confirmed by emoji-picker CSS in page)
    EMOJI_TRIGGER = (
        "xpath=//button[contains(@class,'emoji') or @data-emoji-trigger "
        "or contains(@class,'picker')] | "
        "//span[contains(@class,'emoji') and @role='button']"
    )
    CHAR_COUNTER = (
        "xpath=//*[contains(@class,'char') and contains(text(),'/')] | "
        "//*[contains(@x-text,'charCount') or contains(@x-text,'length')]"
    )

    # ── Agent select (used by create_template flow) ──────────────────────────
    AGENT_SELECT = (
        "xpath=//select[@id='agent_id'] | //select[@id='rcs_agent_id'] "
        "| //select[contains(@*[name()='wire:model'], 'agent')]"
    )

    # ── Rich Card Stand-alone specific fields ─────────────────────────────────
    # Confirmed via a live DOM capture taken with Template Type = "Rich Card
    # Stand-alone" selected: a set of indexed (".0" suffix) wire:model.live
    # fields -- Card Orientation (select#card_orientation.0, wire:model.live=
    # "card_orientation.0": "" placeholder "Select" / value="VERTICAL" /
    # value="HORIZONTAL"), Media Type (select#media_type.0, wire:model.live=
    # "media_type.0": "" placeholder "Select" / value="Image" /
    # value="Video" / value="Document" -- option values re-confirmed via a
    # second live DOM capture), Card Title (input, id="card_title.0-input",
    # 200-char counter shown), Card Description (textarea,
    # id="card_description.0-input", 2000-char counter shown), plus a
    # "Suggested Actions/Reply Buttons" section with a "+ Add Suggestion"
    # button (wire:click="addRichSuggestionCount").
    #
    # Media Type IS now selected by fill_rich_card_standalone_fields()
    # below (the option values were confirmed via a second live DOM
    # capture). Selecting a Media Type (Image/Video/Document) almost
    # certainly reveals a further media-source field (an upload or URL
    # input) whose locator has still never been captured -- that field is
    # deliberately NOT filled here, so a save may still fail validation on
    # it; see fill_rich_card_standalone_fields()'s docstring and TC022's
    # "launched" skip message. The Suggested Actions/Reply Buttons "+ Add
    # Suggestion" flow also remains unwired for the same "never guess a
    # locator" reason.
    #
    # Card Height: selecting Card Orientation="VERTICAL" reveals a further
    # select#mediaheight.0 (wire:model.live="mediaheight.0", NOTE no
    # underscore -- confirmed via a live DOM capture: "" placeholder
    # "Select height" / value="SHORT_HEIGHT" text "SHORT" /
    # value="MEDIUM_HEIGHT" text "MEDIUM"). This capture was originally
    # pasted under Rich Card Carousel's (TC023) test header, but a
    # subsequent real pytest skip on TC022 (Rich Card Stand-alone) --
    # reporting Card Height still unselected -- confirmed it actually
    # belongs here: Stand-alone is the only Template Type with a Card
    # Orientation concept, matching the user's own description ("when it
    # select the vertical, it skip to select the card height"). Whether
    # Card Orientation="HORIZONTAL" reveals a different/analogous field
    # (e.g. a width select, mirroring Carousel's separate width/height
    # pair) has never been captured and is NOT guessed at -- Card Height
    # is only filled by fill_rich_card_standalone_fields() below when
    # orientation="VERTICAL" (the method's default).
    CARD_ORIENTATION_SELECT = "xpath=//select[@id='card_orientation.0']"
    CARD_MEDIA_TYPE_SELECT = "xpath=//select[@id='media_type.0']"
    CARD_MEDIA_HEIGHT_SELECT = "xpath=//select[@id='mediaheight.0']"
    CARD_TITLE_INPUT = "xpath=//input[@id='card_title.0-input']"
    CARD_DESCRIPTION_TEXTAREA = "xpath=//textarea[@id='card_description.0-input']"

    # ── Rich Card Carousel specific fields ────────────────────────────────────
    # Confirmed via a live full-page DOM dump captured with Template Type =
    # "Rich Card Carousel" selected (agent: jioagent): two REQUIRED top-level
    # selects -- Media Width (select#media_width: "" placeholder "Select" /
    # value="SMALL_WIDTH" text "SMALL" / value="MEDIUM_WIDTH" text "MEDIUM")
    # and Media Height (select#media_height: "" placeholder "Select" /
    # value="SHORT_HEIGHT" text "SHORT" / value="MEDIUM_HEIGHT" text
    # "MEDIUM") -- both confirmed required via live wire:snapshot validation
    # errors ("The media width field is required." / "The media height
    # field is required."). A "+ Add Card Carousel" control
    # (wire:click="addCardCount") appends further per-card subforms; the
    # wire:snapshot also confirmed minCardFieldCount: 2 / maxCardFieldCount:
    # 10, i.e. Carousel requires at least 2 cards to save successfully.
    #
    # Card index 0 (rendered by default, "Card 1") reuses the SAME id
    # pattern already confirmed for Rich Card Stand-alone above --
    # media_type.0 / card_title.0-input / card_description.0-input.
    # Card index 1 ("Card 2", after clicking "+ Add Card Carousel") was
    # independently confirmed via a second live DOM capture to follow the
    # exact same id pattern (media_type.1 / card_title.1-input /
    # card_description.1-input / addCarouselSuggestionCount(1) /
    # cardOptOut1) -- Carousel's Media Type select is confirmed at BOTH
    # indices to only offer Image/Video (no Document option, unlike
    # Standalone). Locators for index 2+ remain extrapolated from that
    # confirmed ".{index}" suffix pattern (the project's "already-
    # confirmed pattern at a different index" exception).
    #
    # Media Type IS now selected per card by fill_rich_card_carousel_fields()
    # below (values confirmed at both index 0 and index 1). Selecting a
    # Media Type (Image/Video) almost certainly reveals a further
    # media-source field (an upload input) that has never been captured in
    # a DOM dump -- that field is deliberately NOT filled here, so a save
    # may still fail validation on it; see fill_rich_card_carousel_fields()'s
    # docstring and TC023's "launched" skip message. Each card's per-card
    # "+ Add Suggestion" button (wire:click="addCarouselSuggestionCount(i)")
    # and the "Include opt-out button for this card" checkbox
    # (input#cardOptOut{i}, wire:model.live="cardOptOut.{i}") remain
    # unwired for the same "never guess a locator" reason.
    #
    # CORRECTION: a per-card Media Height select (id="mediaheight.0", no
    # underscore) was briefly wired in here based on a DOM capture pasted
    # under this test's header, but a subsequent real pytest skip for TC022
    # (Rich Card Stand-alone) -- reporting Card Height still unselected --
    # confirmed that field actually belongs to the Stand-alone flow (it is
    # revealed by Stand-alone's Card Orientation="VERTICAL", a concept
    # Carousel has no equivalent of). See CARD_MEDIA_HEIGHT_SELECT in the
    # Stand-alone block above and fill_rich_card_standalone_fields() below.
    # Carousel does NOT select any Media Height per card here unless/until
    # a DOM capture confirms Carousel cards render that field too.
    MEDIA_WIDTH_SELECT = "xpath=//select[@id='media_width']"
    MEDIA_HEIGHT_SELECT = "xpath=//select[@id='media_height']"
    ADD_CARD_CAROUSEL_BTN = "xpath=//*[@*[name()='wire:click']='addCardCount']"

    # ── Rich Message specific fields ──────────────────────────────────────────
    # Confirmed via a live DOM capture taken with Template Type = "Rich
    # Message" selected (this is the option that actually renders in the
    # Type dropdown's second slot for the 'jioagent' agent, in place of
    # "Text Message with Document" -- see create_and_verify_template()'s
    # docstring and TC021's skip message in the test file for that
    # unresolved discrepancy): a "Suggested Actions/Reply Buttons"-style
    # section with a "+ Add Suggestion" button (wire:click=
    # "addSuggestionCount") and an indexed (".0" suffix) subform that
    # renders by default for the first suggestion (no need to click "+
    # Add Suggestion" for suggestion #1 -- same "index 0 renders by
    # default" pattern already confirmed for Rich Card Stand-alone/
    # Carousel's Card 1):
    #   - Type of Action (select#type_of_action.0, wire:model.live=
    #     "type_of_action.0"): "" Select / reply / url_action /
    #     dialer_action / view_location_latlong / view_location_query /
    #     share_location / calendar_event.
    #   - Display Text (input#suggestion_text.0, wire:model.live=
    #     "suggestion_text.0", 25-char limit, plus an "Add Variable"
    #     button next to it -- not wired up here).
    #   - Phone Number to Dial (input#phone_number_to_dial.0,
    #     wire:model="phone_number_to_dial.0", placeholder
    #     "91XXXXXXXXXX") -- confirmed present in the supplied capture
    #     alongside this subform; only wired up here for the
    #     "dialer_action" Type of Action (see fill_suggestion() below).
    #
    # Deliberately NOT wired up: whatever extra field(s) the other Type
    # of Action options (url_action, view_location_latlong,
    # view_location_query, share_location, calendar_event) almost
    # certainly render -- none of those were captured in this DOM dump.
    # fill_suggestion() below only supports "reply" (no extra field) and
    # "dialer_action" (Phone Number to Dial), and raises rather than
    # guessing for any other action_type.
    ADD_SUGGESTION_BTN = "xpath=//*[@*[name()='wire:click']='addSuggestionCount']"

    # ── Footer actions ───────────────────────────────────────────────────────
    CANCEL_LINK = (
        "xpath=//a[contains(@href,'/rcs/template') and "
        "not(contains(@href,'/create')) and "
        "normalize-space()='Cancel']"
    )
    SAVE_BTN = (
        "xpath=//button[@type='submit'] | "
        "//button[contains(normalize-space(.),'Save') or "
        "contains(normalize-space(.),'Create') or "
        "contains(normalize-space(.),'Submit')]"
    )

    # ── Known type options (same taxonomy as every other RCS form) ───────────
    TYPE_OPTIONS_EXPECTED = ["Text Message", "Text Message with Document", "Rich Card Stand-alone", "Rich Card Carousel"]

    # ── Navigation / page state ─────────────────────────────────────────────

    def navigate(self):
        self.open(self.CREATE_URL)
        self.page.wait_for_timeout(2000)
        return self

    def navigate_to_list(self):
        self.open(self.LIST_URL)
        self.page.wait_for_timeout(2000)
        return self

    def is_create_page(self):
        return "/rcs/template/create" in self.get_current_url()

    def is_list_page(self):
        url = self.get_current_url()
        return "/rcs/template" in url and "/create" not in url

    def is_form_loaded(self):
        return (self.is_element_present(self.NAME_INPUT, timeout=10000)
                and self.is_element_present(self.TYPE_SELECT, timeout=5000))

    def get_page_heading_text(self):
        el = self.h.wait_for_element_visible(self.PAGE_HEADING)
        return el.inner_text().strip()

    def get_breadcrumb_text(self):
        el = self.h.wait_for_element_visible(self.BREADCRUMB)
        return " ".join(el.inner_text().split())

    # ── Field getters / setters ──────────────────────────────────────────────

    def fill_name(self, value):
        el = self.h.wait_for_element_visible(self.NAME_INPUT)
        el.fill("")
        el.fill(value)

    def get_name_value(self):
        return self.h.wait_for_element_visible(self.NAME_INPUT).input_value()

    def get_type_options(self):
        el = self.h.wait_for_element_visible(self.TYPE_SELECT)
        opts = el.locator("option")
        return [opts.nth(i).inner_text().strip() for i in range(opts.count()) if opts.nth(i).inner_text().strip()]

    def select_type(self, visible_text):
        """Selects the Type option whose text contains *visible_text*
        (case-insensitive substring match), then selects it by its
        underlying <option> value rather than relying on Playwright's
        select_option(label=...) exact-string match.

        Fixes a real, confirmed failure: TC021 ("Text Message with
        Document") hung for the full 30s Playwright timeout repeating
        "did not find some options" against select_option(label=...) --
        get_type_options() (which reads the very same <option> elements
        via inner_text()) had already confirmed a matching option exists
        (TC005), so the mismatch was in exact-label matching (e.g.
        incidental whitespace), not in a missing/guessed option. This
        loop-and-select-by-value approach is the same resilient pattern
        already proven by select_agent() on this same page, applied to
        the SAME already-confirmed TYPE_SELECT locator -- no new locator
        is introduced. Raises immediately (no 30s hang) if truly no
        option matches."""
        el = self.h.wait_for_element_visible(self.TYPE_SELECT)
        opts = el.locator("option")
        count = opts.count()
        needle = visible_text.strip().lower()
        for i in range(count):
            opt = opts.nth(i)
            text = opt.inner_text().strip()
            if needle in text.lower():
                value = opt.get_attribute("value")
                if value is not None:
                    self.h.select_option(self.TYPE_SELECT, value=value)
                else:
                    self.h.select_option(self.TYPE_SELECT, label=text)
                self.page.wait_for_timeout(500)
                return
        raise RuntimeError(
            f"select_type({visible_text!r}): no option text contained this "
            f"substring among the {count} available Type options"
        )

    def get_selected_type(self):
        el = self.h.wait_for_element_visible(self.TYPE_SELECT)
        return el.locator("option:checked").inner_text().strip()

    def _wait_for_agent_select_populated(self, min_options=2, timeout_ms=15000):
        """Poll until AGENT_SELECT has more than just a placeholder
        option, or timeout elapses. Ported from the confirmed fix on
        RcsCampaignCreatePage._wait_for_select_populated() (see its
        docstring): Agent options here are loaded via an async Livewire
        request slightly after initial page render too, so calling
        select_agent() before that request resolves used to silently
        fall through both the match loop and the "first non-empty
        option" fallback (0 options = 0 iterations either way) without
        raising -- the form then submitted with no agent chosen at all,
        which is what made TC013 (save either redirects or toasts)
        flaky: a required-but-silently-unselected Agent field can block
        the save outright."""
        try:
            return self.h.wait_until(
                lambda: self.page.locator(self.AGENT_SELECT).locator("option").count() >= min_options,
                timeout_ms=timeout_ms,
                interval_ms=300,
            )
        except Exception:
            return False

    def select_agent(self, text_contains):
        el = self.h.wait_for_element_visible(self.AGENT_SELECT)
        self._wait_for_agent_select_populated()
        opts = el.locator("option")
        # Try to find a matching option first
        for i in range(opts.count()):
            opt = opts.nth(i)
            text = opt.inner_text().strip()
            if text_contains.lower() in text.lower():
                self.h.select_option(self.AGENT_SELECT, label=text)
                self.page.wait_for_timeout(500)
                return
        # Fallback to the first non-empty option
        for i in range(opts.count()):
            opt = opts.nth(i)
            val = opt.get_attribute("value")
            text = opt.inner_text().strip()
            if val and text:
                self.h.select_option(self.AGENT_SELECT, label=text)
                self.page.wait_for_timeout(500)
                return
        # Nothing selectable at all (still 0/1 options after the populated
        # wait above) -- raise instead of silently leaving Agent unset, so
        # callers like TC013 fail with an honest "no agent available"
        # reason instead of a confusing downstream save failure.
        raise RuntimeError(
            f"select_agent({text_contains!r}): no matching or fallback "
            f"agent option was available in AGENT_SELECT"
        )

    def fill_rich_card_standalone_fields(self, orientation="VERTICAL",
                                          media_type="Image",
                                          card_height="SHORT_HEIGHT",
                                          card_image=None,
                                          title="Automation Card Title",
                                          description="Automation-generated card description."):
        """Fills the confirmed Rich Card Stand-alone-specific fields (Card
        Orientation, Media Type, Card Height [only when orientation is
        "VERTICAL" -- see below], per-card media upload [only when
        media_type="Image" and card_image is given], Card Title, Card
        Description) -- see the locators' module-level comment above for
        exactly what was captured and what remains deliberately left out
        (Suggested Actions/Reply Buttons). Call this only after
        select_type("Rich Card Stand-alone") has rendered these fields.

        media_type must be one of the confirmed <option> values ("Image",
        "Video", "Document"). Only "Image" has a confirmed upload-input
        locator (_card_media_upload_input()/upload_card_media(), keyed
        off the confirmed accept="image/*" file input) -- for "Video"/
        "Document" no media-source field has been captured, so nothing
        is filled for those and a save may still fail validation on
        whatever field they reveal (see TC022's "launched" skip
        message).

        card_height must be one of the confirmed <option> values
        ("SHORT_HEIGHT", "MEDIUM_HEIGHT") and is only selected when
        orientation="VERTICAL" -- selecting Card Orientation="VERTICAL"
        is confirmed to reveal this select (CARD_MEDIA_HEIGHT_SELECT,
        id="mediaheight.0"); what, if anything, orientation="HORIZONTAL"
        reveals in its place has never been captured, so nothing extra
        is filled for that branch.

        card_image, when given (and media_type="Image"), must be a path
        to a real, existing image file -- it is uploaded via
        upload_card_media(0, card_image). Passing None (the default)
        skips the upload entirely (e.g. for callers exercising a
        media_type where no upload locator is confirmed).

        Returns True if every field applicable to the given
        orientation/media_type/card_image was filled successfully, False
        if any locator wasn't found (e.g. the DOM shape changed)."""
        try:
            self.h.select_option(self.CARD_ORIENTATION_SELECT, value=orientation)
            self.page.wait_for_timeout(300)

            self.h.select_option(self.CARD_MEDIA_TYPE_SELECT, value=media_type)
            self.page.wait_for_timeout(300)

            if orientation == "VERTICAL":
                self.h.select_option(self.CARD_MEDIA_HEIGHT_SELECT, value=card_height)
                self.page.wait_for_timeout(300)

            if media_type == "Image" and card_image:
                self.upload_card_media(0, card_image)

            title_el = self.h.wait_for_element_visible(self.CARD_TITLE_INPUT)
            title_el.fill("")
            title_el.fill(title)

            desc_el = self.h.wait_for_element_visible(self.CARD_DESCRIPTION_TEXTAREA)
            desc_el.fill("")
            desc_el.fill(description)

            self.page.wait_for_timeout(300)
            return True
        except Exception as e:
            print(f"Error in fill_rich_card_standalone_fields: {e}")
            return False

    # -- Per-card media upload (shared: Stand-alone index 0, Carousel any
    #    index) -----------------------------------------------------------
    def _card_media_upload_input(self, index):
        """Per-card image-upload file input -- confirmed via a live DOM
        capture: <input type="file" wire:model.live="media_upload.0"
        accept="image/*" id="default_size">. Deliberately keyed off the
        wire:model.live attribute rather than the id: "default_size" is
        a generic, non-indexed value that is NOT guaranteed unique once
        more than one such input is on the page (e.g. Carousel with 2+
        cards each rendering their own upload widget), whereas
        wire:model.live="media_upload.{index}" follows this page's
        already-confirmed per-instance-unique indexed-attribute pattern.
        Only index 0 has been directly confirmed (Rich Card Stand-alone
        only ever has one card); index 1+ on Carousel is extrapolated
        from that confirmed ".{index}" suffix convention (the project's
        "already-confirmed pattern at a different index" exception,
        already used for media_type.{index}/card_title.{index}-input
        above)."""
        return (
            f"xpath=//input[@type='file' and "
            f"@*[name()='wire:model.live']='media_upload.{index}']"
        )

    def upload_card_media(self, index, filepath):
        """Uploads filepath into the per-card image-upload input at
        *index* (see _card_media_upload_input()'s docstring). filepath
        must point to a real, existing file -- callers are responsible
        for supplying one (see e.g. RCS_CARD_SAMPLE_IMAGE in
        test_rcs_template_create_flow.py). Mirrors the established
        set_carousel_card_file()/_carousel_file_input() pattern already
        proven on WhatsAppTemplateCreatePage (pages/whatsapp/
        whatsapp_template_create_page.py) for the analogous per-card
        media-upload need on WhatsApp Carousel templates."""
        el = self.page.locator(self._card_media_upload_input(index)).first
        el.wait_for(state="attached", timeout=8000)
        el.set_input_files(os.path.abspath(filepath))
        self.page.wait_for_timeout(600)

    # -- Carousel per-card indexed locators -----------------------------
    # Index 0 mirrors the confirmed Standalone id pattern (see the
    # MEDIA_WIDTH_SELECT/ADD_CARD_CAROUSEL_BTN comment block above for what
    # was confirmed vs. extrapolated for index 1+).
    def _carousel_media_type_select(self, index):
        return f"xpath=//select[@id='media_type.{index}']"

    def _carousel_card_title_input(self, index):
        return f"xpath=//input[@id='card_title.{index}-input']"

    def _carousel_card_description_textarea(self, index):
        return f"xpath=//textarea[@id='card_description.{index}-input']"

    def click_add_carousel_card(self):
        """Clicks the confirmed "+ Add Card Carousel" control
        (wire:click="addCardCount") to append another per-card subform.
        See the MEDIA_WIDTH_SELECT/ADD_CARD_CAROUSEL_BTN comment block
        above for the confirmed minCardFieldCount/maxCardFieldCount
        constraints this exists to satisfy."""
        self._js_click(self.ADD_CARD_CAROUSEL_BTN, timeout=10000)
        self.page.wait_for_timeout(500)

    def fill_rich_card_carousel_fields(self, media_width="SMALL_WIDTH",
                                        media_height="SHORT_HEIGHT",
                                        card_count=2,
                                        card_media_type="Image",
                                        card_image=None,
                                        card_title_prefix="Automation Card",
                                        card_description="Automation-generated card description."):
        """Fills the confirmed Rich Card Carousel-specific fields: the two
        required top-level selects (Media Width, Media Height), then
        Media Type + per-card media upload [only when
        card_media_type="Image" and card_image is given] + Card Title +
        Card Description for *card_count* per-card subforms, clicking
        "+ Add Card Carousel" as needed for cards beyond the first
        (which renders by default).

        card_count defaults to 2 to satisfy the confirmed
        minCardFieldCount: 2 constraint from the live wire:snapshot --
        Carousel will not save successfully with fewer than 2 cards.
        Values are not validated against the confirmed
        [2, 10] (min/max) range here; the caller is responsible for
        passing a sane value.

        card_media_type must be one of the confirmed <option> values
        ("Image", "Video" -- Carousel's Media Type does NOT offer
        Document, unlike Standalone) and is applied to every card the
        same way. Only "Image" has a confirmed upload-input locator
        (_card_media_upload_input()/upload_card_media(), shared with
        Rich Card Stand-alone -- see that method's docstring) -- for
        "Video" no media-source field has been captured, so nothing is
        uploaded for that case and a save may still fail validation on
        whatever field it reveals (see TC023's "launched" skip message).
        The per-card "+ Add Suggestion" button and the "Include opt-out
        button for this card" checkbox remain unwired for the same
        "never captured" reason. (A per-card Media Height select was
        briefly wired in here but was corrected back out -- see the
        CORRECTION note in the class-level comment block above
        MEDIA_WIDTH_SELECT; that field belongs to the Stand-alone flow.)

        card_image, when given (and card_media_type="Image"), must be a
        path to a real, existing image file -- it is uploaded via
        upload_card_media(i, card_image) for EVERY card (same file
        reused per card, matching this method's existing pattern of
        applying card_media_type/card_description identically to every
        card). Passing None (the default) skips the upload entirely.

        Only card index 0 and index 1's locators come from live-confirmed
        DOM captures; locators for index 2+ are extrapolated from that
        same confirmed id-pattern (see the class-level comment block
        above MEDIA_WIDTH_SELECT).

        Returns True if Media Width/Height and every requested card's
        Media Type+media upload (if applicable)+Title+Description were
        filled successfully, False on the first failure encountered
        (e.g. a locator not found, or click_add_carousel_card() not
        rendering a new card in time)."""
        try:
            self.h.select_option(self.MEDIA_WIDTH_SELECT, value=media_width)
            self.page.wait_for_timeout(300)
            self.h.select_option(self.MEDIA_HEIGHT_SELECT, value=media_height)
            self.page.wait_for_timeout(300)

            for i in range(card_count):
                if i > 0:
                    self.click_add_carousel_card()

                self.h.select_option(
                    self._carousel_media_type_select(i), value=card_media_type
                )
                self.page.wait_for_timeout(300)

                if card_media_type == "Image" and card_image:
                    self.upload_card_media(i, card_image)

                title_el = self.h.wait_for_element_visible(
                    self._carousel_card_title_input(i)
                )
                title_el.fill("")
                title_el.fill(f"{card_title_prefix} {i + 1}")

                desc_el = self.h.wait_for_element_visible(
                    self._carousel_card_description_textarea(i)
                )
                desc_el.fill("")
                desc_el.fill(card_description)

            self.page.wait_for_timeout(300)
            return True
        except Exception as e:
            print(f"Error in fill_rich_card_carousel_fields: {e}")
            return False

    # -- Rich Message Suggested Action / Reply Button indexed locators --
    # NOTE: unlike the confirmed ".{index}" id-suffix pattern used
    # elsewhere on this page (Rich Card Stand-alone/Carousel's card
    # fields), these three currently target whichever Type of
    # Action/Display Text/Phone Number element is LAST in the DOM (XPath
    # [last()]) rather than a specific numeric index -- *index* is kept
    # as a parameter for call-site compatibility with fill_suggestion()
    # but is not actually used here. This matches fill_rich_message_fields()
    # always calling click_add_suggestion() before filling. Confirmed
    # working end-to-end (fields fill successfully; a real live run's
    # remaining skip was purely the Display Text character-limit issue
    # fixed above, not a locator miss).
    def _suggestion_type_of_action_select(self, index):
        return f"xpath=(//select[contains(@*[name()='wire:model'], 'type_of_action')] | //select[contains(@id, 'type_of_action')])[last()]"

    def _suggestion_text_input(self, index):
        return f"xpath=(//input[contains(@*[name()='wire:model'], 'suggestion_text')] | //input[contains(@id, 'suggestion_text')])[last()]"

    def _suggestion_phone_number_input(self, index):
        return f"xpath=(//input[contains(@*[name()='wire:model'], 'phone_number')] | //input[contains(@id, 'phone_number')])[last()]"

    def click_add_suggestion(self):
        """Clicks the confirmed "+ Add Suggestion" control
        (wire:click="addSuggestionCount") to append another Suggested
        Action/Reply Button subform. The first suggestion (index 0)
        renders by default -- this is only needed for a 2nd+
        suggestion."""
        self._js_click(self.ADD_SUGGESTION_BTN, timeout=10000)
        self.page.wait_for_timeout(500)

    # Confirmed via the live DOM capture: Display Text (suggestion_text)
    # renders a "0/25" character counter, i.e. a 25-char server-side
    # limit. Playwright's .fill() sets the value directly and does NOT
    # respect the input's client-side maxlength, so a caller-supplied
    # *text* over this limit is silently accepted here but then rejected
    # by backend validation on save (no redirect/toast) -- a real,
    # confirmed failure this session hit with the "Automation Suggestion
    # Reply" default (27 chars). fill_suggestion() enforces this limit
    # explicitly instead of letting it fail silently downstream.
    SUGGESTION_TEXT_MAX_LEN = 25

    def fill_suggestion(self, index, action_type="reply",
                         text="Automation Suggestion",
                         phone_number="919999999999"):
        """Fills one Suggested Action/Reply Button subform. *index* is
        accepted for call-site compatibility but the underlying locators
        (_suggestion_type_of_action_select/_suggestion_text_input/
        _suggestion_phone_number_input) currently target the LAST
        matching element in the DOM rather than a specific numeric
        index -- see those methods' comment above for why.

        action_type must be a confirmed <option> value from the Type of
        Action select ("reply", "url_action", "dialer_action",
        "view_location_latlong", "view_location_query",
        "share_location", "calendar_event"). Only "reply" (needs no
        extra field beyond Display Text) and "dialer_action" (fills the
        confirmed Phone Number to Dial field) are actually supported
        here -- every other action type almost certainly renders its
        own extra field(s) (a URL input, lat/long inputs, etc.) that
        were never captured in a DOM dump, so selecting one of those
        here would silently leave a required field unfilled. Raises
        ValueError for an unsupported action_type instead of guessing.

        text must be at most SUGGESTION_TEXT_MAX_LEN (25) characters --
        the confirmed limit on Display Text. Raises ValueError instead
        of silently submitting an over-limit value that would only fail
        later, invisibly, via backend validation on save.

        Returns True if every confirmed field for *action_type* was
        filled successfully, False on any locator failure."""
        if action_type not in ("reply", "dialer_action"):
            raise ValueError(
                f"fill_suggestion(): action_type={action_type!r} is not "
                "supported -- only 'reply' and 'dialer_action' have "
                "their required extra fields confirmed via a live DOM "
                "capture."
            )
        if len(text) > self.SUGGESTION_TEXT_MAX_LEN:
            raise ValueError(
                f"fill_suggestion(): text={text!r} is {len(text)} "
                f"characters, over the confirmed "
                f"{self.SUGGESTION_TEXT_MAX_LEN}-char Display Text limit "
                "-- shorten it. Playwright's .fill() does not enforce "
                "the field's client-side maxlength, so an over-limit "
                "value would otherwise be silently accepted here and "
                "only fail later via backend validation on save (no "
                "redirect/toast, with no clear reason why)."
            )
        try:
            self.h.select_option(
                self._suggestion_type_of_action_select(index), value=action_type
            )
            self.page.wait_for_timeout(300)

            text_el = self.h.wait_for_element_visible(
                self._suggestion_text_input(index)
            )
            text_el.fill("")
            text_el.fill(text)

            if action_type == "dialer_action":
                phone_el = self.h.wait_for_element_visible(
                    self._suggestion_phone_number_input(index)
                )
                phone_el.fill("")
                phone_el.fill(phone_number)

            self.page.wait_for_timeout(300)
            return True
        except Exception as e:
            print(f"Error in fill_suggestion: {e}")
            return False

    def fill_rich_message_fields(self, action_type="reply",
                                  text="Automation Reply"):
        """Fills the confirmed Rich Message-specific field: a Suggested
        Action/Reply Button, via click_add_suggestion() then
        fill_suggestion() (see those methods for the current locator
        strategy). Defaults to the "reply" action type since it needs
        no extra field beyond Display Text; see fill_suggestion()'s
        docstring for why only "reply"/"dialer_action" are supported,
        and for the confirmed 25-char Display Text limit *text* must
        respect (the previous default, "Automation Suggestion Reply",
        was 27 chars and a real, confirmed cause of TC021 skipping --
        Playwright's .fill() doesn't enforce the field's client-side
        maxlength, so it submitted silently and failed backend
        validation on save).

        Returns fill_suggestion(0, ...)'s result."""
        try:
            self.click_add_suggestion()
        except Exception:
            pass
        return self.fill_suggestion(0, action_type=action_type, text=text)

    def fill_body(self, value):
        """Sets the message body textarea value via standard Playwright fill
        so Livewire correctly registers the input."""
        try:
            el = self.h.wait_for_element_visible(self.BODY_TEXTAREA)
            el.fill("")
            el.fill(value)
            self.page.wait_for_timeout(300)
            return True
        except Exception as e:
            print(f"Error in fill_body: {e}")
            return False

    def get_body_value(self):
        try:
            el = self.h.wait_for_element_visible(self.BODY_TEXTAREA)
            return el.input_value() or ""
        except Exception:
            return ""

    def clear_body(self):
        try:
            el = self.h.wait_for_element_visible(self.BODY_TEXTAREA)
            el.evaluate(
                "(elm) => { elm.value = ''; "
                "elm.dispatchEvent(new Event('input', {bubbles: true})); }"
            )
            self.page.wait_for_timeout(300)
        except Exception:
            pass

    def has_emoji_trigger(self):
        return self.is_element_present(self.EMOJI_TRIGGER, timeout=3000)

    # ── Footer actions ───────────────────────────────────────────────────────

    def click_cancel(self):
        self._js_click(self.CANCEL_LINK, timeout=10000)
        self.page.wait_for_timeout(1500)

    def is_save_button_present(self):
        return self.is_element_present(self.SAVE_BTN, timeout=5000)

    def is_save_button_enabled(self):
        try:
            btn = self.page.locator(self.SAVE_BTN).first
            return btn.is_enabled() and btn.get_attribute("disabled") is None
        except Exception:
            return False

    def click_save(self):
        self._js_click(self.SAVE_BTN, timeout=10000)
        self.page.wait_for_timeout(2000)

    # ── Toast / feedback ─────────────────────────────────────────────────────

    def is_success_toast_shown(self, timeout=6000):
        return self.is_element_present(self.NOTIFICATION_TITLE, timeout=timeout)

    # ── Template list export ─────────────────────────────────────────────────

    def click_export_csv(self, timeout_ms=30000):
        """Clicks Export on the Template LIST screen (navigate_to_list()
        first), capturing the resulting download via
        page.expect_download() -- same shape/pattern as
        RCSCampaignPage.click_export_csv(), the confirmed closest sibling
        "list export" screen. BTN_EXPORT itself is a best-effort locator,
        NOT independently confirmed against this screen's live DOM (only
        the header row was, via a real download supplied directly by the
        user) -- so a locator miss here means "not found", not "assert
        against a guessed selector": callers should treat None the same
        way RCSCampaignPage's callers do (skip, don't fail).

        Returns {"elapsed_s", "file_path", "file_size"} on success, or
        None on failure (button not found/not clickable, or no download
        event within timeout_ms)."""
        try:
            btn = self.h.wait_for_element_clickable(self.BTN_EXPORT, timeout=10000)
            btn.scroll_into_view_if_needed()
            start = time.time()
            with self.page.expect_download(timeout=timeout_ms) as dl_info:
                btn.click()
            download = dl_info.value
            filename = download.suggested_filename or "rcs_templates_export.csv"
            dest = os.path.join(DOWNLOAD_DIR, filename)
            download.save_as(dest)
            return {
                "elapsed_s": time.time() - start,
                "file_path": dest,
                "file_size": os.path.getsize(dest),
            }
        except Exception:
            return None

    # ── Template list search / persistence check ─────────────────────────────
    # Confirmed live markup on the RCS Templates list page (/rcs/template,
    # freshly captured DOM): a Livewire-tables list whose tableName is the
    # generic literal "table" (data-tableName holds "table"; the table
    # element itself is id="table-table") -- unlike every WhatsApp list
    # page seen in this suite, which each use a feature-specific tableName.
    # Search input (no debounce):
    #   <input wire:model.live="search" placeholder="Search Template Name" type="text">
    # Added to support a full end-to-end create-then-verify-in-list test,
    # mirroring the already-confirmed RCSCampaignPage.is_campaign_name_in_list().
    LIST_TABLE_ID = "table-table"
    INPUT_SEARCH_LIST = (
        "xpath=//input[@*[name()='wire:model.live' and contains(.,'search')] "
        "or contains(@placeholder,'Search Template')]"
    )

    def _search_list_and_poll_for_name(self, name: str, timeout: int) -> bool:
        """One search-then-poll pass: fills/dispatches events on the
        confirmed search input, then polls the rendered table cells for
        *name* until *timeout* elapses. Factored out of
        is_template_name_in_list() so that method can retry this whole
        pass after a page reload (see its docstring) without duplicating
        the search/poll logic."""
        try:
            inp = self.page.locator(self.INPUT_SEARCH_LIST).first
            inp.wait_for(state="visible", timeout=4000)
            inp.fill("")
            inp.fill(name)
            inp.evaluate(
                "(el) => { el.dispatchEvent(new Event('input', {bubbles:true})); "
                "el.dispatchEvent(new Event('keyup', {bubbles:true})); "
                "el.dispatchEvent(new Event('change', {bubbles:true})); }"
            )
            inp.blur()
            self.page.wait_for_timeout(2500)
        except Exception:
            pass

        deadline = self.page.evaluate("() => Date.now()") + timeout
        while self.page.evaluate("() => Date.now()") < deadline:
            found = self.page.evaluate(
                """([tableId, name]) => {
                    var table = document.getElementById(tableId);
                    var cells = table ? table.querySelectorAll('td, th') : [];
                    for (var i = 0; i < cells.length; i++) {
                        if (cells[i].offsetParent !== null && cells[i].textContent.includes(name)) return true;
                    }
                    return false;
                }""",
                [self.LIST_TABLE_ID, name],
            )
            if found:
                return True
            self.page.wait_for_timeout(500)
        return False

    def is_template_name_in_list(self, name: str, timeout: int = 10000) -> bool:
        """Return True if *name* appears in the RCS Templates table on the
        list page (/rcs/template). Ported from the confirmed reference
        (RCSCampaignPage.is_campaign_name_in_list()): fills the list's
        search box then polls the rendered table cells for the name --
        needed because this list's confirmed pagination
        (.paged-pagination-results, 470+ real templates) means a freshly
        created template could otherwise land on a page far from the
        default view.

        Makes up to TWO full search-then-poll passes (each *timeout*
        long, via _search_list_and_poll_for_name()): a real, user-
        confirmed run showed Save genuinely succeeding (redirect/toast
        confirmed) immediately followed by this check NOT finding the
        template on the very next search -- most consistent with a
        list-refresh/indexing lag on the live app right after a create,
        not a locator problem (the search input and table locators are
        both already confirmed elsewhere; nothing here was guessed). If
        the first pass finds nothing, this reloads the list page
        (forcing a fresh server round-trip rather than relying on
        whatever the client already had cached/hydrated from before the
        create) and retries once before giving up."""
        if self._search_list_and_poll_for_name(name, timeout):
            return True

        try:
            self.page.reload()
            self.page.wait_for_timeout(2000)
        except Exception:
            pass

        return self._search_list_and_poll_for_name(name, timeout)

    # ── Full e2e create+verify, shared across every Template Type ────────────

    def create_and_verify_template(self, name, type_text, body,
                                     agent_hint=None, list_timeout=15000,
                                     extra_fill=None):
        """Shared full end-to-end recipe used by the per-type e2e tests.

        agent_hint defaults to Config.RCS_TEMPLATE_AGENT_NAME (from .env,
        "jioagent" by default) rather than a hardcoded literal -- every
        Template Type dropdown option this suite relies on was confirmed
        live with that specific agent selected (see
        RCS_TEMPLATE_AGENT_NAME's docstring in utils/config.py for why
        this is a SEPARATE .env var from RCS_AGENT_NAME, which is
        Campaign creation's agent). Pass an explicit agent_hint to
        override for a one-off call without touching .env."""
        agent_hint = agent_hint or Config.RCS_TEMPLATE_AGENT_NAME
        self.navigate()
        self.fill_name(name)
        
        agent_available = True
        try:
            self.select_agent(agent_hint)
        except Exception as e:
            print(f"create_and_verify_template: {e}")
            agent_available = False
            return {"agent_available": agent_available, "type_selectable": False, "extra_fields_filled": False, "launched": False, "found_in_list": False}
            
        self.page.wait_for_timeout(1000)
        
        type_selectable = True
        try:
            self.select_type(type_text)
        except Exception as e:
            print(f"create_and_verify_template: {e}")
            type_selectable = False
            return {"agent_available": agent_available, "type_selectable": type_selectable, "extra_fields_filled": False, "launched": False, "found_in_list": False}
            
        self.page.wait_for_timeout(1000)
        
        if "Rich Card" not in type_text:
            self.fill_body(body)
            self.page.wait_for_timeout(1000)
            
        extra_fields_filled = True
        if extra_fill:
            try:
                extra_fields_filled = bool(extra_fill(self))
            except Exception as e:
                print(f"Error in extra_fill: {e}")
                extra_fields_filled = False
            self.page.wait_for_timeout(1000)
            
        self.click_save()
        
        redirected = False
        try:
            self.h.wait_for_url_contains(self.LIST_URL, timeout=list_timeout)
            if "/create" not in self.get_current_url():
                redirected = True
        except Exception:
            pass
            
        toast_shown = self.is_success_toast_shown(timeout=5000)
        launched = redirected or toast_shown
        
        found_in_list = False
        if launched:
            self.navigate_to_list()
            found_in_list = self.is_template_name_in_list(name, timeout=list_timeout)
            
        return {
            "agent_available": agent_available,
            "type_selectable": type_selectable,
            "extra_fields_filled": extra_fields_filled,
            "launched": launched,
            "found_in_list": found_in_list,
        }

    # ── Convenience: full valid submission ───────────────────────────────────

    def create_template(self, name, type_text=None, body=None):
        """Fills all fields and clicks Save. Returns the name used."""
        self.navigate()
        self.fill_name(name)
        if type_text:
            self.select_type(type_text)
        if body:
            self.fill_body(body)
        self.click_save()
        return name

    # ── Performance ──────────────────────────────────────────────────────────

    def get_page_load_time_ms(self):
        try:
            return self.page.evaluate(
                "() => window.performance.timing.loadEventEnd - "
                "window.performance.timing.navigationStart"
            )
        except Exception:
            return None
