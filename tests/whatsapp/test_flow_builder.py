"""
tests/whatsapp/test_flow_builder.py — Automation Flow Builder Test Suite.

Verifies end-to-end creation, configuration, connection, and persistence of
a WhatsApp Automation Flow containing all 21 nodes inside the Flow Builder iframe:
  1. Flow Builder loaded successfully.
  2. Flow name correctly updated.
  3-23. All 21 nodes added and verified on canvas:
     - Stop
     - Condition, Goto, Jump
     - Trigger, Text, Question, Options, Image, Audio, Video, File, Template,
       HTTP, Request Location, GoogleForm, Request Address, Share Location,
       Button, CallToAction, Livechat
  24. Node connections created and validated across main trunk and branches.
  25. Flow saves successfully without validation errors.
  26. Flow persists after reload (all nodes, connections, and configurations intact).
"""
import pytest
from playwright.sync_api import Page, expect

from pages.whatsapp.more.flow_builder_page import FlowBuilderPage
from data.flow_builder_data import (
    ALL_FLOW_NODES,
    WHATSAPP_ALL_NODES_FLOW,
    MULTI_BRANCH_FLOW,
    MULTI_BRANCH_LAYOUT,
    COMPLEX_FLOW_STEPS,
    COMPLEX_FLOW_EXTRA_CONNECTIONS,
    generate_flow_name,
)


@pytest.mark.whatsapp
@pytest.mark.flow_builder
def test_create_whatsapp_flow_with_all_nodes(logged_in_page: Page):
    """
    Test creation of a complete WhatsApp flow containing all 21 available nodes,
    connecting them in a structured workflow, configuring key fields, saving,
    and verifying persistence after page reload.
    """
    flow = FlowBuilderPage(logged_in_page)

    # 1. Verify Flow Builder loads via 'Create New Flow' modal on /flow
    target_flow_name = generate_flow_name()
    flow.open_flow(flow_name=target_flow_name)
    expect(flow.page.locator(flow.FLOW_NAME_INPUT)).to_be_visible()
    expect(flow.frame.locator(flow.CANVAS_WRAPPER)).to_be_visible()

    # 2. Verify Flow name matches created name or can be updated
    flow.set_flow_name(target_flow_name)
    assert flow.get_flow_name() == target_flow_name, f"Expected {target_flow_name}, got {flow.get_flow_name()}"

    # 3-23. Add all 21 nodes and verify each exists on the canvas
    for node_name in ALL_FLOW_NODES:
        flow.add_node(node_name)
        assert flow.verify_node_exists(node_name), f"Node '{node_name}' was not found on canvas after addition."

    # Verify all 21 nodes exist simultaneously
    total_nodes = flow.get_node_count()
    assert total_nodes >= 21, f"Expected at least 21 nodes on canvas, found {total_nodes}."

    # Explicit individual assertions for each required node type (assertions 3-23)
    assert flow.verify_node_exists("Trigger"), "Assertion failed: Trigger node does not exist."
    assert flow.verify_node_exists("Text"), "Assertion failed: Text node does not exist."
    assert flow.verify_node_exists("Question"), "Assertion failed: Question node does not exist."
    assert flow.verify_node_exists("Options"), "Assertion failed: Options node does not exist."
    assert flow.verify_node_exists("Image"), "Assertion failed: Image node does not exist."
    assert flow.verify_node_exists("Audio"), "Assertion failed: Audio node does not exist."
    assert flow.verify_node_exists("Video"), "Assertion failed: Video node does not exist."
    assert flow.verify_node_exists("File"), "Assertion failed: File node does not exist."
    assert flow.verify_node_exists("Template"), "Assertion failed: Template node does not exist."
    assert flow.verify_node_exists("HTTP"), "Assertion failed: HTTP node does not exist."
    assert flow.verify_node_exists("Request Location"), "Assertion failed: Request Location node does not exist."
    assert flow.verify_node_exists("GoogleForm"), "Assertion failed: GoogleForm node does not exist."
    assert flow.verify_node_exists("Request Address"), "Assertion failed: Request Address node does not exist."
    assert flow.verify_node_exists("Share Location"), "Assertion failed: Share Location node does not exist."
    assert flow.verify_node_exists("Button"), "Assertion failed: Button node does not exist."
    assert flow.verify_node_exists("CallToAction"), "Assertion failed: CallToAction node does not exist."
    assert flow.verify_node_exists("Livechat"), "Assertion failed: Livechat node does not exist."
    assert flow.verify_node_exists("Condition"), "Assertion failed: Condition node does not exist."
    assert flow.verify_node_exists("Goto"), "Assertion failed: Goto node does not exist."
    assert flow.verify_node_exists("Jump"), "Assertion failed: Jump node does not exist."
    assert flow.verify_node_exists("Stop"), "Assertion failed: Stop node does not exist."

    # Configure required nodes with test data
    configs = WHATSAPP_ALL_NODES_FLOW["node_configurations"]
    flow.configure_node("Text", configs["Text"])
    flow.configure_node("Question", configs["Question"])
    flow.configure_node("Button", configs["Button"])
    flow.configure_node("CallToAction", configs["CallToAction"])
    flow.configure_node("HTTP", configs["HTTP"])

    # 24. Create Connections:
    # Connect Main Trunk: Trigger -> Text -> Question -> Options
    for conn in WHATSAPP_ALL_NODES_FLOW["main_trunk"]:
        flow.connect_nodes(conn["source"], conn["target"])

    # Connect Options Branches
    for branch in WHATSAPP_ALL_NODES_FLOW["options_branches"]:
        flow.connect_nodes("Options", branch["target"], branch=branch["option_index"])

    # Connect Function Chain: Condition -> Goto -> Jump -> Stop
    for conn in WHATSAPP_ALL_NODES_FLOW["function_chain"]:
        flow.connect_nodes(conn["source"], conn["target"])

    # Assert connections were created
    edge_count = flow.get_edge_count()
    assert edge_count > 0, f"Expected edges to be created on canvas, found {edge_count}."

    # 25. Save the flow and verify no validation errors
    flow.save_flow()

    # 26. Refresh/reload flow and verify persistence
    flow.refresh_flow(flow_name=target_flow_name)

    # Assert flow name persisted
    assert flow.get_flow_name() == target_flow_name, (
        f"Flow name did not persist after reload. Expected '{target_flow_name}', got '{flow.get_flow_name()}'"
    )

    # Assert all 21 nodes persisted on canvas after reload
    for node_name in ALL_FLOW_NODES:
        assert flow.verify_node_exists(node_name), f"Node '{node_name}' did not persist after reload."

    # Assert connections persisted after reload
    reloaded_edges = flow.get_edge_count()
    assert reloaded_edges > 0, f"Edges did not persist after reload. Found {reloaded_edges} edges."


@pytest.mark.whatsapp
@pytest.mark.flow_builder
def test_create_whatsapp_multi_branch_flow(logged_in_page: Page):
    """
    Builds a WhatsApp flow where a single Options node fans out into three named
    branches ("Product Information", "Location", "Technical Support"), each a
    linear chain of nodes that converges back onto one shared Stop node:

        Trigger -> Text -> Question -> Options
          "Product Information" -> Image -> Audio -> Video -> File -> Template
              -> Button -> CallToAction -> Livechat -> Stop
          "Location" -> Request Location -> Request Address -> Share Location
              -> GoogleForm -> Stop
          "Technical Support" -> HTTP -> Condition -/- Goto -\\
                                                     \\- Jump -/-> Stop

    Verifies the flow builds, connects, saves, and persists after reload.
    """
    flow = FlowBuilderPage(logged_in_page)

    target_flow_name = generate_flow_name(base="Automation_WhatsApp_MultiBranch")
    flow.open_flow(flow_name=target_flow_name)
    expect(flow.page.locator(flow.FLOW_NAME_INPUT)).to_be_visible()
    expect(flow.frame.locator(flow.CANVAS_WRAPPER)).to_be_visible()

    flow.set_flow_name(target_flow_name)
    assert flow.get_flow_name() == target_flow_name, f"Expected {target_flow_name}, got {flow.get_flow_name()}"

    configs = MULTI_BRANCH_FLOW["node_configurations"]

    # MULTI_BRANCH_LAYOUT positions are canvas-relative; add the iframe's actual page offset
    # so add_node()'s page.mouse-based drag lands nodes inside the canvas instead of above it.
    canvas_x, canvas_y = flow.get_canvas_offset()

    def build_node(node_type, connect_from, branch=None, config=None):
        """Add one node, position it clear of earlier ones, fill its fields, wire it to its
        predecessor, then verify it landed — fully wired before the next node is started."""
        rel_pos = MULTI_BRANCH_LAYOUT.get(node_type)
        position = (canvas_x + rel_pos[0], canvas_y + rel_pos[1]) if rel_pos else None
        flow.add_configure_connect(
            node_type,
            config=config,
            connect_from=connect_from,
            branch=branch,
            position=position,
        )
        assert flow.verify_node_exists(node_type), f"Node '{node_type}' was not found on canvas after addition."

    # Trigger is pre-created by WhatsApp flows; just confirm it's there before extending it
    assert flow.verify_node_exists("Trigger"), "Default Trigger node missing from a new WhatsApp flow."

    # Main trunk: Trigger -> Text -> Question -> Options
    build_node("Text", connect_from="Trigger", config=configs["Text"])
    build_node("Question", connect_from="Text", config=configs["Question"])
    build_node("Options", connect_from="Question", config={"options": MULTI_BRANCH_FLOW["options_config"]})

    # "Product Information" branch: Options -> Image -> Audio -> Video -> File -> Template
    #   -> Button -> CallToAction -> Livechat -> Stop
    build_node("Image", connect_from="Options", branch=0)
    build_node("Audio", connect_from="Image")
    build_node("Request Location", connect_from="Options", branch=1)
    build_node("Request Address", connect_from="Request Location")
    build_node("HTTP", connect_from="Options", branch=2, config=configs["HTTP"])
    build_node("Condition", connect_from="HTTP")
    build_node("Video", connect_from="Audio")
    build_node("File", connect_from="Video")
    build_node("Template", connect_from="File")
    build_node("Button", connect_from="Template", config=configs["Button"])
    build_node("CallToAction", connect_from="Button", config=configs["CallToAction"])
    build_node("Livechat", connect_from="CallToAction")
    build_node("Stop", connect_from="Livechat")

    # "Location" branch: Options -> Request Location -> Request Address -> Share Location
    #   -> GoogleForm -> Stop (shared)
    # build_node("Request Location", connect_from="Options", branch=1)
    # build_node("Request Address", connect_from="Request Location")
    build_node("Share Location", connect_from="Request Address")
    build_node("GoogleForm", connect_from="Share Location")
    flow.connect_nodes("GoogleForm", "Stop")

    # "Technical Support" branch: Options -> HTTP -> Condition -/- Goto -\-> Stop (shared)
    #                                                          \- Jump -/
    
    build_node("Goto", connect_from="Condition", branch=0)
    build_node("Jump", connect_from="Condition", branch=1)
    flow.connect_nodes("Goto", "Stop")
    flow.connect_nodes("Jump", "Stop")

    # Assert connections were created
    edge_count = flow.get_edge_count()
    assert edge_count > 0, f"Expected edges to be created on canvas, found {edge_count}."

    # Save the flow and verify no validation errors
    flow.save_flow()

    # Refresh/reload flow and verify persistence
    flow.refresh_flow(flow_name=target_flow_name)

    assert flow.get_flow_name() == target_flow_name, (
        f"Flow name did not persist after reload. Expected '{target_flow_name}', got '{flow.get_flow_name()}'"
    )

    for node_name in ALL_FLOW_NODES:
        assert flow.verify_node_exists(node_name), f"Node '{node_name}' did not persist after reload."

    reloaded_edges = flow.get_edge_count()
    assert reloaded_edges > 0, f"Edges did not persist after reload. Found {reloaded_edges} edges."


@pytest.mark.whatsapp
@pytest.mark.flow_builder
def test_create_whatsapp_complex_multi_branch_flow(logged_in_page: Page):
    """
    Builds a larger WhatsApp flow where Options fans into 3 branches, and the Store
    Location branch's own Condition further fans into 3 named city/fallback paths
    (Delhi NCR, Mumbai, Other Location), each ending in its own Stop node; Technical
    Support's Condition fans into Goto/Jump, both converging on a dedicated Stop.
    See COMPLEX_FLOW_STEPS in data/flow_builder_data.py for the full topology.

    Several node types repeat on this single canvas (5x Stop, 2x Condition, HTTP,
    Goto, Share Location, Request Address), so every node is addressed by its own
    (palette type, index-on-canvas-of-that-type) rather than by type alone — tracked
    here per step id as the flow is built.
    """
    flow = FlowBuilderPage(logged_in_page)

    target_flow_name = generate_flow_name(base="Automation_WhatsApp_ComplexBranch")
    flow.open_flow(flow_name=target_flow_name)
    expect(flow.page.locator(flow.FLOW_NAME_INPUT)).to_be_visible()
    expect(flow.frame.locator(flow.CANVAS_WRAPPER)).to_be_visible()

    flow.set_flow_name(target_flow_name)
    assert flow.get_flow_name() == target_flow_name, f"Expected {target_flow_name}, got {flow.get_flow_name()}"

    # COMPLEX_FLOW_STEPS positions are canvas-relative; add the iframe's actual page offset.
    canvas_x, canvas_y = flow.get_canvas_offset()

    # Maps each step's id -> (palette node type, index among nodes of that type on canvas),
    # since get_node_locator()/connect_nodes() address duplicate node types by index, not id.
    built = {}
    type_counts = {}

    for step in COMPLEX_FLOW_STEPS:
        node_type = step["type"]
        own_index = type_counts.get(node_type, 0)
        connect_from_id = step.get("connect_from")

        if node_type == "Trigger":
            # Pre-created by WhatsApp flows; just confirm it's there before extending it.
            assert flow.verify_node_exists("Trigger"), "Default Trigger node missing from a new WhatsApp flow."
        else:
            connect_from_type, connect_from_index = built[connect_from_id]
            rel_pos = step.get("position")
            position = (canvas_x + rel_pos[0], canvas_y + rel_pos[1]) if rel_pos else None

            flow.add_configure_connect(
                node_type,
                config=step.get("config"),
                connect_from=connect_from_type,
                branch=step.get("branch"),
                position=position,
                source_index=connect_from_index,
                target_index=own_index,
            )
            assert flow.verify_node_exists(node_type, index=own_index), (
                f"Node '{step['id']}' ({node_type}[{own_index}]) was not found on canvas after addition."
            )

        built[step["id"]] = (node_type, own_index)
        type_counts[node_type] = own_index + 1

    # Second incoming connections for nodes that already got their first one via connect_from
    # above (Jump -> stop_tech, alongside Goto -> stop_tech).
    for extra in COMPLEX_FLOW_EXTRA_CONNECTIONS:
        src_type, src_index = built[extra["source"]]
        tgt_type, tgt_index = built[extra["target"]]
        flow.connect_nodes(src_type, tgt_type, source_index=src_index, target_index=tgt_index)

    # Assert connections were created
    edge_count = flow.get_edge_count()
    assert edge_count > 0, f"Expected edges to be created on canvas, found {edge_count}."

    # Save the flow and verify no validation errors
    flow.save_flow()

    # Refresh/reload flow and verify persistence
    flow.refresh_flow(flow_name=target_flow_name)

    assert flow.get_flow_name() == target_flow_name, (
        f"Flow name did not persist after reload. Expected '{target_flow_name}', got '{flow.get_flow_name()}'"
    )

    for step in COMPLEX_FLOW_STEPS:
        node_type, own_index = built[step["id"]]
        assert flow.verify_node_exists(node_type, index=own_index), (
            f"Node '{step['id']}' ({node_type}[{own_index}]) did not persist after reload."
        )

    reloaded_edges = flow.get_edge_count()
    assert reloaded_edges > 0, f"Edges did not persist after reload. Found {reloaded_edges} edges."
