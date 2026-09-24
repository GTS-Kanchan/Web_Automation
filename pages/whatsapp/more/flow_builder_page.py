"""
pages/whatsapp/more/flow_builder_page.py — Page Object for WhatsApp Automation Flow Builder.

Handles both:
  1. Parent page controls (Flow name, Save Flow, Back, Refresh, Livewire spinners).
  2. Flow Builder iframe (React Flow canvas, node palette drawer, node handles,
     drag & drop connections, node configuration drawer, and edge validation).

Grounded in DOM evidence from:
  - Parent page Livewire component flow.create (memo.path="flow/create")
  - Iframe React application bundle (https://flow.cpaas.globeteleservices.com/static/js/main.e7b1dd7c.js)
"""
import logging
from typing import Optional, Dict, Any, Tuple

from playwright.sync_api import Page, Locator, FrameLocator, expect

from pages.common.base_page import BasePage
from utils.config import Config
from data.flow_builder_data import NODE_TYPE_MAP

logger = logging.getLogger(__name__)


class FlowBuilderPage(BasePage):
    """Page Object for WhatsApp Automation Flow Builder."""

    # ══════════════════════════════════════════════════════════════════════════
    # Selectors — Parent Page (Confirmed from Livewire DOM)
    # ══════════════════════════════════════════════════════════════════════════
    CREATE_NEW_FLOW_BTN = "button:has-text('Create New Flow')"
    MODAL_FLOW_NAME_INPUT = "input#name, input[placeholder='Flow Name']"
    MODAL_FLOW_TYPE_SELECT = "select[wire\\:model\\.live='flow_type']"
    MODAL_CREATE_BTN = "button[type='submit']:has-text('Create')"
    MODAL_CANCEL_BTN = "button[wire\\:click*='closeModal']:has-text('Cancel')"
    FLOW_NAME_INPUT = "#name"
    SAVE_FLOW_BTN = "button[type='submit']:has-text('Save Flow')"
    # Both Refresh (onclick="window.location.reload()") and Back (onclick="window.history.back()")
    # are plain <button type="button"> elements on the Flow Edit page, not <a> tags — confirmed
    # from live DOM. The old `a:has-text(...)` selectors matched nothing, silently masked by
    # refresh_flow()'s fallback to a raw page.reload() (functionally the same here, since that's
    # exactly what the button's own onclick does, but not what was actually being clicked).
    REFRESH_BTN = "button:has-text('Refresh')"
    BACK_BTN = "button:has-text('Back')"
    FLOW_IFRAME = "iframe[title='Automation Flow']"
    WIRE_LOADING_SPINNER = "svg[wire\\:loading]"

    # ══════════════════════════════════════════════════════════════════════════
    # Selectors — Iframe / React Flow (Confirmed from React bundle main.js)
    # ══════════════════════════════════════════════════════════════════════════
    CANVAS_WRAPPER = ".reactflow-wrapper"
    CANVAS_PANE = ".react-flow__pane"
    MENU_BTN = "button[aria-label='menu']"
    PALETTE_DRAWER = ".MuiDrawer-paper"
    SEARCH_NODES_INPUT = "input[placeholder='Search nodes...']"
    CONFIG_DRAWER = ".MuiDrawer-paperAnchorRight"
    DONE_BTN = "button:has-text('Done')"
    SNACKBAR_SUCCESS = ".MuiAlert-standardSuccess, .MuiAlert-filledSuccess"
    SNACKBAR_ERROR = ".MuiAlert-standardError, .MuiAlert-filledError"
    EDGE_ELEMENT = ".react-flow__edge"

    def __init__(self, page: Page):
        super().__init__(page)
        self.config = Config

    @property
    def frame(self) -> FrameLocator:
        """Returns the FrameLocator for the Automation Flow iframe."""
        return self.page.frame_locator(self.FLOW_IFRAME)

    def get_canvas_offset(self) -> Tuple[int, int]:
        """
        Returns the page-viewport (x, y) of the Automation Flow iframe's top-left corner.

        `add_node(position=...)` drags a node via `page.mouse`, which operates in main-page
        viewport coordinates — not coordinates relative to the canvas. Positions computed
        without this offset can land above/outside the iframe (e.g. on the flow-name input or
        toolbar row that sits above the canvas), silently failing to move the node and leaving
        it stacked at React Flow's default spawn point. Callers should add this offset to any
        canvas-relative layout coordinates before passing them as a node's `position`.
        """
        box = self.page.locator(self.FLOW_IFRAME).bounding_box()
        if box:
            return int(box["x"]), int(box["y"])
        return 0, 0

    # ══════════════════════════════════════════════════════════════════════════
    # Navigation & Flow Level Actions
    # ══════════════════════════════════════════════════════════════════════════

    def create_new_flow(self, flow_name: str = "WhatsApp_Automation_Flow", flow_type: str = "whatsapp"):
        """
        Navigates to /flow, clicks 'Create New Flow', fills the modal with flow name and type,
        clicks 'Create', and waits for the canvas iframe to mount.
        """
        logger.info(f"Initiating flow creation from /flow: name='{flow_name}', type='{flow_type}'")
        self.open("/flow")
        self.page.wait_for_load_state("domcontentloaded")

        create_btn = self.page.locator(self.CREATE_NEW_FLOW_BTN)
        create_btn.wait_for(state="visible", timeout=self.h.timeout_ms)
        create_btn.click()

        name_input = self.page.locator(self.MODAL_FLOW_NAME_INPUT)
        name_input.wait_for(state="visible", timeout=self.h.timeout_ms)
        name_input.fill(flow_name)

        type_select = self.page.locator(self.MODAL_FLOW_TYPE_SELECT)
        type_select.wait_for(state="visible", timeout=self.h.timeout_ms)
        type_select.select_option(flow_type)
        self.page.wait_for_timeout(500)

        # Guard against duplicate flow name validation
        error_msg = self.page.locator("p:has-text('The name has already been taken'), span:has-text('The name has already been taken')")
        if error_msg.is_visible():
            import time
            flow_name = f"{flow_name}_{int(time.time())}"
            name_input.fill(flow_name)
            self.page.wait_for_timeout(300)

        submit_btn = self.page.locator(self.MODAL_CREATE_BTN)
        submit_btn.wait_for(state="visible", timeout=self.h.timeout_ms)
        expect(submit_btn).to_be_enabled(timeout=5000)
        submit_btn.click()

        # Wait for redirect to /flow/create?id=... and iframe canvas to mount
        self.page.wait_for_load_state("domcontentloaded")
        self.frame.locator(self.CANVAS_WRAPPER).wait_for(state="visible", timeout=30000)
        logger.info("Flow Builder canvas loaded successfully inside iframe after creation.")

    def open_flow(self, flow_id: Optional[str] = None, flow_name: Optional[str] = None):
        """
        Navigates to Flow Builder.
        If flow_id is provided, navigates directly to /flow/{flow_id}/edit.
        If flow_id is None, creates a new flow via /flow 'Create New Flow' modal.
        """
        if flow_id:
            path = f"/flow/{flow_id}/edit"
            logger.info(f"Navigating to Flow Builder edit page: {path}")
            self.open(path)
            self.page.wait_for_load_state("domcontentloaded")
            self.frame.locator(self.CANVAS_WRAPPER).wait_for(state="visible", timeout=30000)
            logger.info("Flow Builder canvas loaded successfully inside iframe.")
        else:
            target_name = flow_name or "WhatsApp_Automation_Flow"
            self.create_new_flow(flow_name=target_name, flow_type="whatsapp")

    def set_flow_name(self, name: str):
        """Sets the flow name in the parent page input field."""
        logger.info(f"Setting flow name to: {name}")
        name_input = self.page.locator(self.FLOW_NAME_INPUT)
        name_input.wait_for(state="visible", timeout=self.h.timeout_ms)
        name_input.fill("")
        name_input.fill(name)

    def get_flow_name(self) -> str:
        """Returns the current flow name entered in the parent page input."""
        return self.page.locator(self.FLOW_NAME_INPUT).input_value()

    # ══════════════════════════════════════════════════════════════════════════
    # Node Palette & Creation
    # ══════════════════════════════════════════════════════════════════════════

    def open_palette(self):
        """Opens the node palette drawer if not already open and stable."""
        search_input = self.frame.locator(self.SEARCH_NODES_INPUT)
        if not search_input.is_visible():
            logger.info("Opening node palette drawer.")
            menu_btn = self.frame.locator(self.MENU_BTN)
            menu_btn.wait_for(state="visible", timeout=5000)
            menu_btn.click()
            search_input.wait_for(state="visible", timeout=5000)
            self.page.wait_for_timeout(300)

    def close_palette(self):
        """Closes the node palette drawer if open."""
        drawer = self.frame.locator(self.PALETTE_DRAWER)
        if drawer.is_visible():
            self.page.keyboard.press("Escape")
            drawer.wait_for(state="hidden", timeout=5000)

    def search_node(self, keyword: str):
        """Searches for nodes in the palette search input."""
        self.open_palette()
        search_input = self.frame.locator(self.SEARCH_NODES_INPUT)
        search_input.fill(keyword)

    def add_node(self, node_type: str, position: Optional[Tuple[int, int]] = None):
        """
        Adds a node to the canvas by selecting it from the palette drawer.
        Optionally repositions the newly created node on the canvas.
        """
        # WhatsApp flows have a default Trigger node pre-created on canvas
        if node_type == "Trigger" and self.verify_node_exists("Trigger"):
            logger.info("Trigger node already exists on canvas by default; skipping addition.")
            return

        logger.info(f"Adding node: {node_type} to canvas.")
        self.open_palette()

        # Locate the specific clickable child item (which has .MuiListItemIcon-root) in the palette list
        node_item = self.frame.locator(
            f"{self.PALETTE_DRAWER} li.MuiListItem-root:has(.MuiListItemIcon-root)"
        ).filter(has_text=node_type).first

        # If not immediately visible, scroll into view or search
        if not node_item.is_visible():
            search_input = self.frame.locator(self.SEARCH_NODES_INPUT)
            search_input.fill(node_type)
            self.page.wait_for_timeout(300)

        node_item.wait_for(state="visible", timeout=5000)
        node_item.click()

        # Resolve the React Flow node locator on canvas
        internal_type = NODE_TYPE_MAP.get(node_type, node_type.lower().replace(" ", ""))
        node_loc = self.frame.locator(f".react-flow__node-{internal_type}").last
        node_loc.wait_for(state="visible", timeout=10000)

        # Wait for palette to finish closing before next operation
        try:
            self.frame.locator(self.SEARCH_NODES_INPUT).wait_for(state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(200)

        # If position is requested, drag the node across canvas so it doesn't stack on top
        # of previously added nodes at React Flow's default spawn point (interaction with a
        # freshly spawned node's handles is unreliable when several nodes occupy the same spot).
        if position:
            x_target, y_target = position
            node_loc.scroll_into_view_if_needed()
            box = node_loc.bounding_box()
            if box:
                start_x = box["x"] + box["width"] / 2
                start_y = box["y"] + box["height"] / 2
                self.page.mouse.move(start_x, start_y)
                self.page.mouse.down()
                self.page.mouse.move(x_target, y_target, steps=5)
                self.page.mouse.up()
                self.page.wait_for_timeout(300)

    def add_configure_connect(
        self,
        node_type: str,
        config: Optional[Dict[str, Any]] = None,
        connect_from: Optional[str] = None,
        branch: Optional[int] = None,
        position: Optional[Tuple[int, int]] = None,
        source_index: int = 0,
        target_index: int = 0,
    ):
        """
        Adds one node, positions it clear of previously added nodes, fills its config fields,
        and connects it to a predecessor — all before moving on to the next node.

        This mirrors how a QA engineer would build the flow by hand (one node at a time,
        fully wired up before starting the next) rather than bulk-adding every node first and
        only connecting them afterward, which leaves many nodes stacked on the same default
        spawn point and makes their handles unreliable to target.

        `target_index` and `source_index` matter once a flow has more than one node of the
        same type on canvas (e.g. several Stop nodes): pass this new node's own index among
        nodes of its type (`target_index`) and connect_from's index among ITS type
        (`source_index`) — both default to 0, correct only while each type is still unique.
        """
        self.add_node(node_type, position=position)
        if config:
            self.configure_node(node_type, config, index=target_index)
        if connect_from:
            self.connect_nodes(
                connect_from, node_type, branch=branch, source_index=source_index, target_index=target_index
            )

    def get_node_locator(self, node_type: str, index: int = 0) -> Locator:
        """
        Returns the Locator for a given node type on the canvas.
        Distinguishes duplicate node types by index.
        """
        internal_type = NODE_TYPE_MAP.get(node_type, node_type.lower().replace(" ", ""))
        return self.frame.locator(f".react-flow__node-{internal_type}").nth(index)

    # ══════════════════════════════════════════════════════════════════════════
    # Node Configuration
    # ══════════════════════════════════════════════════════════════════════════

    def _select_mui_dropdown(self, drawer: Locator, label_text: str, option_text: str):
        """
        Opens a MUI Select identified by its preceding <p> label and picks an option.
        MUI renders the option listbox in a portal outside the drawer's DOM subtree,
        so the option is searched for at the iframe level, not within `drawer`.
        """
        combobox = drawer.locator(
            f"p.MuiTypography-body1:text-is('{label_text}')"
        ).locator("xpath=following-sibling::div[1]//div[@role='combobox']")
        combobox.click()
        self.frame.get_by_role("option", name=option_text, exact=True).click()

    def _fill_key_label_rows(self, drawer: Locator, rows: list):
        """
        Fills a MUI Key/Label row list — used by both Options' branch list and Button's
        "Buttons (Max 3)" list, which share the same component. The drawer starts with only
        one row, so for every row beyond the first this clicks the row's "+" button
        (AddCircleOutlineIcon) to create a new one before filling it — filling by index alone,
        without adding rows first, silently only ever fills whatever row already exists.
        """
        add_btn = drawer.locator("button:has(svg[data-testid='AddCircleOutlineIcon'])")
        key_inputs = drawer.locator("input[placeholder='Key']")
        label_inputs = drawer.locator("input[placeholder='Label']")
        for idx, row in enumerate(rows):
            if key_inputs.count() <= idx:
                add_btn.last.click()
                key_inputs = drawer.locator("input[placeholder='Key']")
                label_inputs = drawer.locator("input[placeholder='Label']")
                key_inputs.nth(idx).wait_for(state="visible", timeout=3000)
            if "key" in row:
                key_inputs.nth(idx).fill(row["key"])
            if "label" in row:
                label_inputs.nth(idx).fill(row["label"])

    def configure_node(self, node_type: str, config: Dict[str, Any], index: int = 0):
        """
        Opens the node's configuration drawer via double-click, fills fields,
        and saves changes via the 'Done' button.

        Field selectors below are grounded in DOM evidence captured per node type
        (Title/body fields use MUI TextField placeholders; dropdowns are MUI Select
        components identified by their preceding label paragraph via
        `_select_mui_dropdown`). Node types not explicitly handled here fall back
        to the generic title fill only.
        """
        logger.info(f"Configuring node: {node_type} (index: {index}) with {config}")
        node_loc = self.get_node_locator(node_type, index)
        node_loc.scroll_into_view_if_needed()

        config_drawer = self.frame.locator(self.CONFIG_DRAWER)
        try:
            node_loc.dblclick(force=True, timeout=3000)
            config_drawer.wait_for(state="visible", timeout=3000)
        except Exception:
            logger.info(f"Config drawer for {node_type} did not open or is not configurable; skipping.")
            return

        # Fill Title if present (first <input> in every drawer is always the Title field)
        if "title" in config:
            title_input = config_drawer.locator("input").first
            if title_input.is_visible():
                title_input.fill(config["title"])

        if node_type == "Text":
            # Fields: Title, "Add text" (textarea), Enable Preview URL (checkbox). The textarea's
            # exact placeholder wasn't confirmed against live DOM, so target it positionally
            # (first textarea in the drawer) rather than risk a placeholder text mismatch.
            if "text" in config:
                config_drawer.locator("textarea").first.fill(config["text"])

        elif node_type == "Question":
            # DOM not captured directly; question text is the drawer's first textarea,
            # analogous to Text's "Add text" field.
            if "question" in config:
                config_drawer.locator("textarea").first.fill(config["question"])

        elif node_type == "Options":
            # Fields: Title, Options list of Key/Label pairs (each row beyond the first
            # requires clicking its "+" icon to create it before it can be filled).
            if "options" in config:
                self._fill_key_label_rows(config_drawer, config["options"])

        elif node_type == "Button":
            # Fields: Title, Body Type (select, default Reply), Header (select, default Text),
            # Header Text, Body Text* (required), Footer, Button Text, Buttons (Max 3) Key/Label list.
            if "header_text" in config:
                config_drawer.get_by_placeholder("Enter header text (max 60 characters)").fill(config["header_text"])
            if "body_text" in config:
                config_drawer.get_by_placeholder("Enter body text (max 1024 characters)").fill(config["body_text"])
            if "footer" in config:
                config_drawer.get_by_placeholder("Enter footer text (max 60 characters)").fill(config["footer"])
            if "button_text" in config:
                config_drawer.get_by_placeholder("Enter button text (max 20 characters)").fill(config["button_text"])
            if "buttons" in config:
                self._fill_key_label_rows(config_drawer, config["buttons"])

        elif node_type == "HTTP":
            # Fields: Title, Protocol (select, default HTTP), HTTP Request Method (select, default GET),
            # HTTP Request URL, Headers (Key/Value list), Body Type (select, default JSON),
            # Parameters (Key/Value list), Auth (select, default Bearer Token), Token, Encryption Enable.
            if "url" in config:
                config_drawer.get_by_placeholder("Enter the HTTP request URL").fill(config["url"])
            if "method" in config:
                self._select_mui_dropdown(config_drawer, "HTTP Request Method", config["method"])
            if "token" in config:
                config_drawer.get_by_placeholder("Enter the token").fill(config["token"])

        elif node_type == "CallToAction":
            # Only extra field is "Select Template" (MUI select) — populated from the account's
            # existing WhatsApp CTA templates, so automation cannot fabricate a value here.
            # Leave unconfigured; the Done->Cancel fallback below handles the unmet requirement.
            pass

        elif node_type == "Livechat":
            # Fields: Title, Access token* (password), Account id* (numeric), Inbox id* (numeric),
            # Send handover message (switch), Pass conversation to live agent (switch).
            if "access_token" in config:
                config_drawer.get_by_placeholder("Enter Access Token").fill(config["access_token"])
            if "account_id" in config:
                config_drawer.get_by_placeholder("Enter Account ID").fill(config["account_id"])
            if "inbox_id" in config:
                config_drawer.get_by_placeholder("Enter Inbox ID").fill(config["inbox_id"])

        elif node_type == "Request Location":
            # Fields: Title, "Bot message to User" (textarea, defaults to "Please share your location"),
            # Failure Message (defaults to "Incorrect format. Click on share and select location.").
            if "message" in config:
                config_drawer.get_by_placeholder(
                    "Enter the message that will be sent to the user"
                ).fill(config["message"])
            if "failure_message" in config:
                config_drawer.get_by_placeholder("Message shown when location sharing fails").fill(
                    config["failure_message"]
                )

        elif node_type == "Request Address":
            # Fields: Title, Country ID (defaults to "IN"), Address (textarea placeholder "Requesting for address").
            if "country_id" in config:
                config_drawer.locator("input").nth(1).fill(config["country_id"])
            if "address" in config:
                config_drawer.get_by_placeholder("Requesting for address").fill(config["address"])

        elif node_type == "Share Location":
            # Fields (all required): Title, Name*, Latitude*, Longitude*, Address*.
            if "name" in config:
                config_drawer.get_by_placeholder("Enter name").fill(config["name"])
            if "latitude" in config:
                config_drawer.get_by_placeholder("e.g. 28.6139 (-90 to 90)").fill(config["latitude"])
            if "longitude" in config:
                config_drawer.get_by_placeholder("e.g. 77.2090 (-180 to 180)").fill(config["longitude"])
            if "address" in config:
                config_drawer.get_by_placeholder("Enter address").fill(config["address"])

        elif node_type == "GoogleForm":
            # Fields: Title, Google Form URL, Bot Message to User (textarea), Validation (switch),
            # Thank You Message (textarea).
            if "form_url" in config:
                config_drawer.get_by_placeholder(
                    "https://docs.google.com/forms/d/... or https://forms.gle/..."
                ).fill(config["form_url"])
            if "message" in config:
                config_drawer.get_by_placeholder(
                    "Enter the message that will be sent to the user"
                ).fill(config["message"])
            if "thank_you_message" in config:
                config_drawer.get_by_placeholder("Thank you for submitting the form!").fill(
                    config["thank_you_message"]
                )

        elif node_type == "Goto":
            # Fields: Title (maxlength 30), Number of Repetitions (numeric, min 1 max 3, default 1).
            if "repetitions" in config:
                config_drawer.locator("input").nth(1).fill(str(config["repetitions"]))

        elif node_type == "Jump":
            # Fields: Title (maxlength 30), Flow (MUI select targeting a *different* saved flow,
            # not an in-canvas node) — left unconfigured unless a target flow name is supplied.
            if "target_flow" in config:
                self._select_mui_dropdown(config_drawer, "Flow", config["target_flow"])

        elif node_type == "Condition":
            # Fields: Title, Configure Paths (each path is a named condition; a fixed "else" path
            # always exists). Paths are plain <p> labels, not text inputs — naming/editing a
            # condition's actual rule requires a rule-builder UI not modeled here. "extra_paths"
            # clicks the "+" (AddIcon) that many times to grow the path count for a multi-way
            # branch: each added "Empty condition" row plus the fixed trailing "else" row becomes
            # one addressable branch index for connect_nodes(branch=...), in the order they
            # appear (0, 1, ... N-1 = the added rows, N = "else").
            extra_paths = config.get("extra_paths", 0)
            if extra_paths:
                add_btn = config_drawer.locator("button:has(svg[data-testid='AddIcon'])")
                for _ in range(extra_paths):
                    add_btn.click()

        # Fill Caption for media nodes (Image/Video/File) sharing the same placeholder pattern.
        if node_type in ("Image", "Video") and "caption" in config:
            config_drawer.get_by_placeholder("Enter image caption").fill(config["caption"])
        elif node_type == "File" and "caption" in config:
            config_drawer.get_by_placeholder("Enter file caption").fill(config["caption"])

        # Click Done button to commit node configuration; fallback to Cancel if validation requires
        # data the automation cannot supply (e.g. an existing template/sender or a real file upload).
        done_btn = config_drawer.locator(self.DONE_BTN)
        cancel_btn = config_drawer.locator("button:has-text('Cancel')")
        if done_btn.is_visible():
            done_btn.click()
            try:
                config_drawer.wait_for(state="hidden", timeout=2000)
            except Exception:
                logger.info(f"Done did not dismiss config drawer for {node_type}; clicking Cancel.")
                if cancel_btn.is_visible():
                    cancel_btn.click()
                    config_drawer.wait_for(state="hidden", timeout=3000)

    # ══════════════════════════════════════════════════════════════════════════
    # Connections
    # ══════════════════════════════════════════════════════════════════════════

    def connect_nodes(
        self,
        source: str,
        target: str,
        branch: Optional[int] = None,
        source_index: int = 0,
        target_index: int = 0,
        source_handle_id: Optional[str] = None,
        target_handle_id: Optional[str] = None,
    ):
        """
        Connects a source node to a target node by dragging source handle to target handle.
        """
        logger.info(f"Connecting node {source} -> {target} (branch: {branch})")
        source_node = self.get_node_locator(source, source_index)
        target_node = self.get_node_locator(target, target_index)

        source_node.scroll_into_view_if_needed()
        target_node.scroll_into_view_if_needed()

        # Identify source handle
        if source_handle_id:
            src_handle = source_node.locator(f"[data-handleid='{source_handle_id}']")
        elif branch is not None:
            # Applies to any multi-branch node (Options, Condition, Goto, HTTP, Template, Button),
            # not just Options — each renders one .react-flow__handle-right dot per branch, in order.
            src_handle = source_node.locator(f"[data-handleid='source-right-{branch}']")
            if not src_handle.is_visible():
                src_handle = source_node.locator(".react-flow__handle-right").nth(branch)
        else:
            src_handle = source_node.locator(".react-flow__handle-right").first

        # Identify target handle
        if target_handle_id:
            tgt_handle = target_node.locator(f"[data-handleid='{target_handle_id}']")
        else:
            tgt_handle = target_node.locator(".react-flow__handle-left").first

        try:
            src_handle.wait_for(state="visible", timeout=3000)
            tgt_handle.wait_for(state="visible", timeout=3000)
            src_handle.drag_to(tgt_handle, force=True)
            self.page.wait_for_timeout(300)
        except Exception as e:
            logger.warning(f"Handle connection attempt for {source} -> {target}: {e}")
            # A drag that fails partway (e.g. "outside of the viewport") can leave the mouse
            # button logically pressed, which corrupts every click/drag after it — release it
            # defensively so one bad connection doesn't cascade into unrelated later failures.
            try:
                self.page.mouse.up()
            except Exception:
                pass

    # ══════════════════════════════════════════════════════════════════════════
    # Verification & Assertions
    # ══════════════════════════════════════════════════════════════════════════

    def verify_node_exists(self, node_type: str, index: int = 0) -> bool:
        """Verifies that a node of given type exists and is visible on canvas."""
        loc = self.get_node_locator(node_type, index)
        return loc.is_visible()

    def get_node_count(self, node_type: Optional[str] = None) -> int:
        """Returns the count of nodes on canvas (either of given type or total)."""
        if node_type:
            internal_type = NODE_TYPE_MAP.get(node_type, node_type.lower().replace(" ", ""))
            return self.frame.locator(f".react-flow__node-{internal_type}").count()
        return self.frame.locator(".react-flow__node").count()

    def get_edge_count(self) -> int:
        """Returns the count of connection edges rendered on canvas."""
        return self.frame.locator(self.EDGE_ELEMENT).count()

    # ══════════════════════════════════════════════════════════════════════════
    # Save & Persistence
    # ══════════════════════════════════════════════════════════════════════════

    def save_flow(self):
        """
        Clicks the parent page 'Save Flow' button and waits for request completion.
        Ensures no validation error alerts appear.
        """
        logger.info("Saving flow via parent page 'Save Flow' button.")
        save_btn = self.page.locator(self.SAVE_FLOW_BTN)
        save_btn.wait_for(state="visible", timeout=self.h.timeout_ms)
        save_btn.click()

        # Wait for livewire spinner to finish if it activates
        spinner = self.page.locator(self.WIRE_LOADING_SPINNER)
        if spinner.is_visible():
            spinner.wait_for(state="hidden", timeout=10000)

        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(1000)

        # If still on editor page, verify no error toast inside iframe
        if self.page.locator(self.FLOW_IFRAME).count() > 0:
            error_alert = self.frame.locator(self.SNACKBAR_ERROR)
            if error_alert.is_visible():
                err_text = error_alert.text_content()
                raise AssertionError(f"Flow save failed with validation error: {err_text}")

        logger.info(f"Save Flow completed. Current URL: {self.page.url}")

    def reopen_saved_flow(self, flow_name: str):
        """
        From the /flow listing page, locates the row matching flow_name and clicks Edit.
        Waits for the Flow Builder canvas iframe to mount.
        """
        logger.info(f"Reopening saved flow '{flow_name}' from /flow listing table.")
        if "/flow" not in self.page.url or "/edit" in self.page.url or "create" in self.page.url:
            self.open("/flow")
            self.page.wait_for_load_state("domcontentloaded")

        row = self.page.locator("tr").filter(has_text=flow_name).first
        row.wait_for(state="visible", timeout=10000)
        edit_btn = row.locator("a[href*='/flow/'][href*='/edit']").first
        edit_btn.wait_for(state="visible", timeout=5000)
        edit_btn.click()

        self.page.wait_for_load_state("domcontentloaded")
        self.frame.locator(self.CANVAS_WRAPPER).wait_for(state="visible", timeout=30000)
        logger.info(f"Flow '{flow_name}' reopened successfully in Flow Builder.")

    def refresh_flow(self, flow_name: Optional[str] = None):
        """
        Reloads the page / re-opens the flow to verify persistence.
        """
        logger.info("Refreshing Flow Builder page.")
        if flow_name and ("/flow" in self.page.url and "/edit" not in self.page.url and "create" not in self.page.url):
            self.reopen_saved_flow(flow_name)
        else:
            refresh_link = self.page.locator(self.REFRESH_BTN)
            if refresh_link.is_visible():
                refresh_link.click()
            else:
                self.page.reload()

            self.page.wait_for_load_state("domcontentloaded")
            self.frame.locator(self.CANVAS_WRAPPER).wait_for(state="visible", timeout=30000)
        logger.info("Flow Builder reloaded successfully.")
