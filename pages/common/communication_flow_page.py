"""
NOTE: unused placeholder page object, ported for structural parity with the
Selenium suite. No test file in this project exercises CommunicationFlowPage
(there was none in tests/ for the Selenium version either) — every locator
below is a guess ("Locators (Placeholders - need to be updated with actual
UI locators)" in the original) rather than something CONFIRMED against a
real DOM, unlike the rest of this app's page objects. Treat this file as a
starting point for a future Communication Flow Builder suite, not as
something already validated against the real app.
"""
import logging

from pages.common.base_page import BasePage
from utils.flow_data import FLOW_NODE_CONFIG

logger = logging.getLogger(__name__)


class CommunicationFlowPage(BasePage):
    # Locators (Placeholders - need to be updated with actual UI locators)
    FLOW_MENU = "xpath=//a[contains(text(), 'Communication Flow')]"
    CREATE_FLOW_BTN = "xpath=//button[contains(text(), 'Create Flow')]"
    FLOW_NAME_INPUT = "#flow-name"
    SAVE_FLOW_BTN = "xpath=//button[contains(text(), 'Save Flow')]"
    PUBLISH_FLOW_BTN = "xpath=//button[contains(text(), 'Publish Flow')]"
    TRIGGER_FLOW_BTN = "xpath=//button[contains(text(), 'Trigger')]"

    # Node Palette Locators
    NODE_WEBHOOK = "[data-node-type='webhook']"
    NODE_SMS = "[data-node-type='sms']"
    NODE_EMAIL = "[data-node-type='email']"
    NODE_WHATSAPP = "[data-node-type='whatsapp']"
    NODE_RCS = "[data-node-type='rcs']"
    NODE_STOP = "[data-node-type='stop']"

    # Canvas and node elements (in canvas)
    CANVAS = "#flow-canvas"
    CANVAS_NODE = "[class*='canvas-node']"

    def navigate_to_flow_builder(self):
        logger.info("Navigating to Communication Flow Builder")
        self.h.wait_for_element_clickable(self.FLOW_MENU).click()
        self.page.wait_for_timeout(1000)

    def create_new_flow(self, flow_name):
        logger.info(f"Creating new flow: {flow_name}")
        self.h.wait_for_element_clickable(self.CREATE_FLOW_BTN).click()
        self.h.clear_and_type(self.FLOW_NAME_INPUT, flow_name)

    def add_node(self, node_name, x_offset, y_offset):
        """
        Dynamically adds a node to the canvas at the specified x, y offset.
        Playwright has no direct "drag by offset" API (Selenium's
        ActionChains.drag_and_drop_by_offset), so this drives the mouse
        manually: move to the source element's centre, press down, move by
        the offset, release.
        """
        logger.info(f"Adding node: {node_name} at ({x_offset}, {y_offset})")
        node_locator_map = {
            "WEBHOOK": self.NODE_WEBHOOK,
            "SMS": self.NODE_SMS,
            "EMAIL": self.NODE_EMAIL,
            "WHATSAPP": self.NODE_WHATSAPP,
            "RCS": self.NODE_RCS,
            "STOP": self.NODE_STOP,
        }

        locator = node_locator_map.get(node_name.upper())
        if not locator:
            raise ValueError(f"Unsupported node type: {node_name}")

        source = self.page.locator(locator).first
        source.wait_for(state="attached", timeout=self.h.timeout_ms)
        self.page.locator(self.CANVAS).first.wait_for(state="attached", timeout=self.h.timeout_ms)

        box = source.bounding_box()
        if box is None:
            raise Exception(f"Could not resolve bounding box for node: {node_name}")
        start_x = box["x"] + box["width"] / 2
        start_y = box["y"] + box["height"] / 2

        self.page.mouse.move(start_x, start_y)
        self.page.mouse.down()
        self.page.mouse.move(start_x + x_offset, start_y + y_offset, steps=10)
        self.page.mouse.up()
        self.page.wait_for_timeout(500)

    def connect_nodes(self, source_index, target_index):
        """
        Connects two nodes based on their index on the canvas.
        Assuming each node has an output port and an input port.
        """
        logger.info(f"Connecting node at index {source_index} to index {target_index}")
        nodes = self.page.locator(self.CANVAS_NODE)
        if nodes.count() <= max(source_index, target_index):
            raise Exception("Nodes not found on canvas to connect.")

        source_node = nodes.nth(source_index)
        target_node = nodes.nth(target_index)

        # This heavily depends on the UI. Typically:
        # 1. Hover on source node to reveal connection point
        # 2. Click and hold connection point
        # 3. Move to target node
        # 4. Release
        try:
            source_port = source_node.locator(".output-port").first
            target_port = target_node.locator(".input-port").first

            s_box = source_port.bounding_box()
            t_box = target_port.bounding_box()
            if s_box is None or t_box is None:
                raise Exception("Could not resolve connection port bounding boxes.")

            self.page.mouse.move(s_box["x"] + s_box["width"] / 2, s_box["y"] + s_box["height"] / 2)
            self.page.mouse.down()
            self.page.mouse.move(t_box["x"] + t_box["width"] / 2, t_box["y"] + t_box["height"] / 2, steps=10)
            self.page.mouse.up()
            self.page.wait_for_timeout(500)
        except Exception as e:
            logger.error(f"Failed to connect nodes: {e}")
            raise

    def configure_node(self, node_name, index):
        """
        Clicks on the node and fills out the configuration panel based on node type.
        """
        logger.info(f"Configuring node: {node_name}")
        nodes = self.page.locator(self.CANVAS_NODE)
        node_element = nodes.nth(index)

        # Double click to open config
        node_element.dblclick()
        self.page.wait_for_timeout(1000)

        config_data = FLOW_NODE_CONFIG.get(node_name.upper(), {})

        if node_name.upper() == "SMS":
            self._configure_sms(config_data)
        elif node_name.upper() == "EMAIL":
            self._configure_email(config_data)
        elif node_name.upper() == "WHATSAPP":
            self._configure_whatsapp(config_data)
        elif node_name.upper() == "RCS":
            self._configure_rcs(config_data)

        # Save node config (assuming a save button in side panel)
        self.page.locator("xpath=//button[contains(text(), 'Save Configuration')]").first.click()
        self.page.wait_for_timeout(500)

    def _configure_sms(self, data):
        self.page.locator("#sms-sender-id").fill(data.get("sender_id") or "")
        self.page.locator("#sms-template").fill(data.get("template") or "")

    def _configure_email(self, data):
        self.page.locator("#email-sender").fill(data.get("sender") or "")
        self.page.locator("#email-subject").fill(data.get("subject") or "")

    def _configure_whatsapp(self, data):
        self.page.locator("#wa-template").fill(data.get("template") or "")

    def _configure_rcs(self, data):
        self.page.locator("#rcs-agent").fill(data.get("agent") or "")

    def save_flow(self):
        logger.info("Saving flow")
        self.h.wait_for_element_clickable(self.SAVE_FLOW_BTN).click()
        self.page.wait_for_timeout(1000)

    def publish_flow(self):
        logger.info("Publishing flow")
        self.h.wait_for_element_clickable(self.PUBLISH_FLOW_BTN).click()
        self.page.wait_for_timeout(1000)

    def execute_flow(self):
        logger.info("Triggering flow execution")
        self.h.wait_for_element_clickable(self.TRIGGER_FLOW_BTN).click()
        self.page.wait_for_timeout(2000)

    def delete_flow(self, flow_name):
        logger.info(f"Deleting flow: {flow_name}")
        # Navigate back to list, search and delete
        pass
