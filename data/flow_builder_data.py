"""
data/flow_builder_data.py — Test data for WhatsApp Automation Flow Builder.

Defines the complete test scenario with all 21 available nodes, their canvas
layout positions, connection topology, and required node field values.
"""

import time

# All 21 supported nodes categorized by palette group
ALL_FLOW_NODES = [
    # STOP
    "Stop",
    # FUNCTION
    "Condition",
    "Goto",
    "Jump",
    # CHATBOT / WHATSAPP
    "Trigger",
    "Text",
    "Question",
    "Options",
    "Image",
    "Audio",
    "Video",
    "File",
    "Template",
    "HTTP",
    "Request Location",
    "GoogleForm",
    "Request Address",
    "Share Location",
    "Button",
    "CallToAction",
    "Livechat",
]

# Mapping of display/palette name to internal React Flow node type
NODE_TYPE_MAP = {
    "Stop": "stop",
    "Condition": "condition",
    "Goto": "goto",
    "Jump": "jump",
    "Trigger": "trigger",
    "Text": "text",
    "Question": "question",
    "Options": "options",
    "Image": "image",
    "Audio": "audio",
    "Video": "video",
    "File": "file",
    "Template": "template",
    "HTTP": "http",
    "Request Location": "requestlocation",
    "GoogleForm": "googleform",
    "Request Address": "requestaddress",
    "Share Location": "sharelocation",
    "Button": "button",
    "CallToAction": "calltoaction",
    "Livechat": "livechat",
}

# Reverse mapping from React Flow node type to display name
TYPE_TO_DISPLAY_MAP = {v: k for k, v in NODE_TYPE_MAP.items()}

def generate_flow_name(base: str = "Automation_WhatsApp_All_Nodes") -> str:
    """Generates a timestamped unique flow name to prevent uniqueness constraint errors."""
    return f"{base}_{int(time.time())}"


# Main flow & branch connection topology
WHATSAPP_ALL_NODES_FLOW = {
    "flow_name": generate_flow_name(),
    "nodes": ALL_FLOW_NODES,
    # Main trunk sequence
    "main_trunk": [
        {"source": "Trigger", "target": "Text"},
        {"source": "Text", "target": "Question"},
        {"source": "Question", "target": "Options"},
    ],
    # Branching from Options to the remaining 14 leaf/sub-flow nodes
    "options_branches": [
        {"option_index": 0, "target": "Image", "label": "Option Image"},
        {"option_index": 1, "target": "Audio", "label": "Option Audio"},
        {"option_index": 2, "target": "Video", "label": "Option Video"},
        {"option_index": 3, "target": "File", "label": "Option File"},
        {"option_index": 4, "target": "Template", "label": "Option Template"},
        {"option_index": 5, "target": "HTTP", "label": "Option HTTP"},
        {"option_index": 6, "target": "Request Location", "label": "Option Location"},
        {"option_index": 7, "target": "GoogleForm", "label": "Option Form"},
        {"option_index": 8, "target": "Request Address", "label": "Option Address"},
        {"option_index": 9, "target": "Share Location", "label": "Option ShareLoc"},
        {"option_index": 10, "target": "Button", "label": "Option Button"},
        {"option_index": 11, "target": "CallToAction", "label": "Option CTA"},
        {"option_index": 12, "target": "Livechat", "label": "Option Livechat"},
        {"option_index": 13, "target": "Condition", "label": "Option Condition"},
    ],
    # Sequential chain from Condition to Stop
    "function_chain": [
        {"source": "Condition", "target": "Goto"},
        {"source": "Goto", "target": "Jump"},
        {"source": "Jump", "target": "Stop"},
    ],
    # Node-specific configuration data
    "node_configurations": {
        "Text": {
            "title": "Welcome Text",
            "text": "Welcome to our WhatsApp automation flow.",
        },
        "Question": {
            "title": "Support Inquiry",
            "question": "How can we help you today?",
        },
        "Button": {
            "title": "Action Button",
            "body_text": "Please choose an option below.",
            "button_text": "Select",
        },
        "CallToAction": {
            "title": "CTA Link",
            # "Select Template" is a required MUI dropdown populated from the account's
            # existing WhatsApp CTA templates; automation cannot fabricate a value here.
        },
        "HTTP": {
            "title": "Webhook Endpoint",
            "url": "https://example.com/webhook",
        },
    },
}

# Multi-branch flow topology: Trigger -> Text -> Question -> Options, fanning out into three
# named branches off a single Options node, each a linear chain that converges back onto one
# shared Stop node:
#
#   Options ── "Product Information" ── Image -> Audio -> Video -> File -> Template -> Button
#                                         -> CallToAction -> Livechat -> Stop
#           ── "Location"           ── Request Location -> Request Address -> Share Location
#                                         -> GoogleForm -> Stop
#           ── "Technical Support"  ── HTTP -> Condition -/- Goto -\
#                                                          \- Jump -/-> Stop
#
# Condition's two outgoing paths use its default "Empty condition" path (index 0) and the
# fixed "else" path (index 1) — both exist without clicking Condition's "+" (AddIcon).
MULTI_BRANCH_FLOW = {
    "flow_name": generate_flow_name(base="Automation_WhatsApp_MultiBranch"),
    "nodes": ALL_FLOW_NODES,
    "main_trunk": [
        {"source": "Trigger", "target": "Text"},
        {"source": "Text", "target": "Question"},
        {"source": "Question", "target": "Options"},
    ],
    # Options node's 3 named branches — filled via configure_node()'s "options" key/label rows
    "options_config": [
        {"key": "product_info", "label": "Product Information"},
        {"key": "location", "label": "Location"},
        {"key": "tech_support", "label": "Technical Support"},
    ],
    # Each branch's head connection, keyed to options_config's row order
    "options_branches": [
        {"option_index": 0, "target": "Image"},             # "Product Information"
        {"option_index": 1, "target": "Request Location"},  # "Location"
        {"option_index": 2, "target": "HTTP"},               # "Technical Support"
    ],
    # "Product Information" branch: linear chain ending at the shared Stop
    "product_info_chain": [
        {"source": "Image", "target": "Audio"},
        {"source": "Audio", "target": "Video"},
        {"source": "Video", "target": "File"},
        {"source": "File", "target": "Template"},
        {"source": "Template", "target": "Button"},
        {"source": "Button", "target": "CallToAction"},
        {"source": "CallToAction", "target": "Livechat"},
        {"source": "Livechat", "target": "Stop"},
    ],
    # "Location" branch: linear chain ending at the shared Stop
    "location_chain": [
        {"source": "Request Location", "target": "Request Address"},
        {"source": "Request Address", "target": "Share Location"},
        {"source": "Share Location", "target": "GoogleForm"},
        {"source": "GoogleForm", "target": "Stop"},
    ],
    # "Technical Support" branch: HTTP -> Condition, then Condition fans into Goto & Jump
    "tech_support_chain": [
        {"source": "HTTP", "target": "Condition"},
    ],
    "condition_branches": [
        {"option_index": 0, "target": "Goto"},  # Condition's default "Empty condition" path
        {"option_index": 1, "target": "Jump"},  # Condition's fixed "else" path
    ],
    # Goto and Jump both converge back onto the single shared Stop node
    "converge_to_stop": [
        {"source": "Goto", "target": "Stop"},
        {"source": "Jump", "target": "Stop"},
    ],
    # Node-specific configuration data, filled in immediately after each node is added
    "node_configurations": {
        "Text": {
            "title": "Welcome Text",
            "text": "Welcome! What can we help you with today?",
        },
        "Question": {
            "title": "Menu Question",
            "question": "Choose a topic: Product Information, Location, or Technical Support.",
        },
        "Button": {
            "title": "Product Options",
            "body_text": "Here's what we offer. Tap below to continue.",
            "button_text": "Continue",
        },
        "CallToAction": {
            "title": "Product CTA",
            # "Select Template" is a required MUI dropdown populated from the account's
            # existing WhatsApp CTA templates; automation cannot fabricate a value here.
        },
        "HTTP": {
            "title": "Support Ticket Webhook",
            "url": "https://example.com/support/ticket",
        },
    },
}

# Drop position for each node in MULTI_BRANCH_FLOW, expressed as an (x, y) offset from the
# Automation Flow iframe's top-left corner — NOT raw page coordinates. Every node gets its own
# clear spot instead of stacking on React Flow's default spawn point. Callers must add the
# iframe's actual page offset (FlowBuilderPage.get_canvas_offset()) before using these as a
# node's `position`, since `add_node()` drags via `page.mouse`, which operates in page-viewport
# coordinates.
#
# Kept deliberately compact (well under 900x600) rather than spread across a large virtual
# canvas: `connect_nodes()` drags directly between two node handles, and Playwright's `drag_to`
# needs BOTH endpoints simultaneously inside the actual browser viewport — it cannot pan
# React Flow's canvas mid-drag the way it can auto-scroll a regular DOM container. Headed runs
# use `no_viewport=True` (window-size-dependent, not a guaranteed 1920x1080 like headless CI —
# see conftest.py::_viewport_context_args), so a layout sized for a big viewport can silently
# place far-apart nodes where no single window size shows both at once, breaking every drag
# between them ("Element is outside of the viewport"). Trigger is omitted — WhatsApp flows
# pre-create it and it's left where it spawns.
MULTI_BRANCH_LAYOUT = {

    # =========================================================
    # MAIN TRUNK
    # =========================================================

    "Text": (150, 100),
    "Question": (350, 100),
    "Options": (550, 100),


    # =========================================================
    # PRODUCT INFORMATION BRANCH
    # Options → Product Information
    # Single horizontal chain
    # =========================================================

    "Image": (750, 100),
    "Audio": (950, 100),
    "Video": (1150, 100),
    "File": (1350, 100),

    "Template": (1550, 100),
    "Button": (1750, 100),
    "CallToAction": (1950, 100),
    "Livechat": (2150, 100),


    # =========================================================
    # LOCATION BRANCH
    # Options → Find Nearest Store
    #
    # Row 1:
    # Request Location → Request Address
    #
    # Row 2:
    # Share Location → GoogleForm
    # =========================================================

    "Request Location": (750, 300),
    "Request Address": (1000, 300),

    "Share Location": (750, 450),
    "GoogleForm": (1000, 450),


    # =========================================================
    # TECHNICAL SUPPORT BRANCH
    #
    # HTTP → Condition
    #             ↙       ↘
    #          Goto       Jump
    # =========================================================

    "HTTP": (750, 650),
    "Condition": (1000, 650),

    "Goto": (900, 800),
    "Jump": (1150, 800),


    # =========================================================
    # COMMON CONVERGENCE
    # All branches eventually connect to Stop
    # =========================================================

    "Stop": (1400, 800),
}
# Reference of the real config-drawer fields per node type, captured from the live
# Automation Flow Builder DOM. Field keys here match what `configure_node()` in
# FlowBuilderPage understands; node types not yet wired into configure_node are
# documented for when the test scenario needs to configure them.
NODE_CONFIG_FIELDS = {
    "Text": {
        "text": "textarea, placeholder 'Please provide your reply message'",
        # also: "Enable Preview URL" checkbox (not automated)
    },
    "Image": {
        "caption": "input, placeholder 'Enter image caption'",
        # "Upload Image" is a file input (accept=image/*) — real upload not automated
    },
    "Video": {
        "caption": "input, placeholder 'Enter image caption' (shared placeholder, likely a copy-paste in their UI)",
        # "Upload Video" is a file input (accept=video/*) — real upload not automated
    },
    "Audio": {
        # "Add Audio via URL" text input has no placeholder attribute (positional only)
        # OR "Upload Audio" file input (accept=audio/*) — neither automated
    },
    "File": {
        "caption": "input, placeholder 'Enter file caption'",
        # "Add PDF File via URL" text input has no placeholder attribute (positional only)
        # OR "Upload PDF File" file input (accept=.pdf,application/pdf) — neither automated
    },
    "Template": {
        # "Select Sender" (MUI select, placeholder 'Select a sender')
        # "Select Template" (MUI select, disabled until a sender is picked) — requires real account data
    },
    "HTTP": {
        "url": "input, placeholder 'Enter the HTTP request URL'",
        "method": "MUI select 'HTTP Request Method', default GET",
        "token": "password input, placeholder 'Enter the token' (shown when Auth = Bearer Token)",
        # also: Protocol select (default HTTP), Headers/Parameters Key-Value lists,
        # Body Type select (default JSON), Encryption Enable checkbox
    },
    "Request Location": {
        "message": "textarea, placeholder 'Enter the message that will be sent to the user', "
                    "defaults to 'Please share your location'",
        "failure_message": "input, placeholder 'Message shown when location sharing fails', "
                            "defaults to 'Incorrect format. Click on share and select location.'",
    },
    "GoogleForm": {
        "form_url": "input, placeholder 'https://docs.google.com/forms/d/... or https://forms.gle/...'",
        "message": "textarea, placeholder 'Enter the message that will be sent to the user', "
                    "defaults to 'Please fill out this form to continue'",
        "thank_you_message": "textarea, placeholder 'Thank you for submitting the form!' (also the default value)",
        # also: "Validation" switch
    },
    "Request Address": {
        "country_id": "2nd input on the drawer, defaults to 'IN' (no placeholder attribute)",
        "address": "textarea, placeholder 'Requesting for address'",
    },
    "Share Location": {
        "name": "input, placeholder 'Enter name' (required)",
        "latitude": "input, placeholder 'e.g. 28.6139 (-90 to 90)' (required)",
        "longitude": "input, placeholder 'e.g. 77.2090 (-180 to 180)' (required)",
        "address": "textarea, placeholder 'Enter address' (required)",
    },
    "Button": {
        "header_text": "input, placeholder 'Enter header text (max 60 characters)'",
        "body_text": "textarea, placeholder 'Enter body text (max 1024 characters)' (required)",
        "footer": "input, placeholder 'Enter footer text (max 60 characters)'",
        "button_text": "input, placeholder 'Enter button text (max 20 characters)'",
        "buttons": "list of {key, label} rows (Max 3), same Key/Label inputs as Options",
        # also: Body Type select (default Reply), Header select (default Text)
    },
    "CallToAction": {
        # "Select Template" (MUI select, placeholder 'Select a template') — requires real account data
    },
    "Livechat": {
        "access_token": "password input, placeholder 'Enter Access Token' (required)",
        "account_id": "numeric input, placeholder 'Enter Account ID' (required)",
        "inbox_id": "numeric input, placeholder 'Enter Inbox ID' (required)",
        # also: "Send handover message" and "Pass conversation to live agent" switches
    },
    "Goto": {
        "repetitions": "2nd input on the drawer ('Number of Repetitions'), numeric, min 1 max 3, default 1",
    },
    "Jump": {
        "target_flow": "MUI select 'Flow' (aria-label 'Select flow') — targets a *different* saved flow, "
                        "not an in-canvas node",
    },
    "Condition": {
        # "Configure Paths": each path is a plain <p> label (not a text input) with a delete icon;
        # a "+" icon (AddIcon) adds a new "Empty condition" path. A fixed "else" path always exists.
        # Editing a path's actual rule is not modeled here.
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# Complex multi-branch flow: Options fans into 3 branches (Product Information,
# Store Location, Technical Support); the Store branch's own Condition further fans
# into 3 named city/fallback paths (Delhi NCR, Mumbai, Other Location), each ending
# in its own Stop node; Technical Support's Condition fans into Goto/Jump, both
# converging on a dedicated Stop. Several node types repeat (5x Stop, 2x Condition,
# HTTP, Goto, Share Location, Request Address), so each step below carries a unique
# `id` distinct from its palette `type` — the test tracks each id's (type, index-on-
# canvas) as it builds, since get_node_locator()/connect_nodes() address duplicate
# node types by index, not by any on-canvas label.
#
# Each step is built fully before the next starts (add -> position -> configure ->
# connect to its `connect_from` id), except `COMPLEX_FLOW_EXTRA_CONNECTIONS`, applied
# after every step exists, for the one case where a node needs a second incoming
# connection (Jump -> the Technical Support Stop, alongside Goto -> the same Stop).
#
# Positions are canvas-relative (x, y) offsets, kept compact (max ~925x520) for the
# same reason as MULTI_BRANCH_LAYOUT: connect_nodes() drags directly between two
# node handles, and both must be simultaneously inside the real browser viewport.
COMPLEX_FLOW_STEPS = [
    {"id": "trigger", "type": "Trigger"},

    # ============================================================
    # MAIN TRUNK
    # ============================================================

    {"id": "text", "type": "Text",
     "position": (150, 100),
     "connect_from": "trigger",
     "config": {
         "title": "Welcome Text",
         "text": "Welcome! What can we help you with today?"
     }},

    {"id": "question", "type": "Question",
     "position": (350, 100),
     "connect_from": "text",
     "config": {
         "title": "Menu Question",
         "question": "Choose a topic: Product Information, Store Location, or Technical Support."
     }},

    {"id": "options", "type": "Options",
     "position": (550, 100),
     "connect_from": "question",
     "config": {
         "options": [
             {"key": "product_info", "label": "Product Information"},
             {"key": "store_location", "label": "Store Location"},
             {"key": "technical_support", "label": "Technical Support"},
         ]
     }},


    # ============================================================
    # PRODUCT INFORMATION BRANCH
    # Options branch 0
    #
    # Image → Audio → Video → File
    #                       ↓
    # Template → Button → CallToAction → Livechat → Stop
    # ============================================================

    {"id": "image", "type": "Image",
     "position": (800, 40),
     "connect_from": "options",
     "branch": 0},

    {"id": "audio", "type": "Audio",
     "position": (1000, 40),
     "connect_from": "image"},

    {"id": "video", "type": "Video",
     "position": (1200, 40),
     "connect_from": "audio"},

    {"id": "file", "type": "File",
     "position": (1400, 40),
     "connect_from": "video"},

    {"id": "template", "type": "Template",
     "position": (1600, 40),
     "connect_from": "file"},

    {"id": "button", "type": "Button",
     "position": (1800, 40),
     "connect_from": "template",
     "config": {
         "title": "Product Options",
         "body_text": "Here's what we offer. Tap below to continue.",
         "button_text": "Continue"
     }},

    {"id": "calltoaction", "type": "CallToAction",
     "position": (2000, 40),
     "connect_from": "button",
     "config": {
         "title": "Product CTA"
     }},

    {"id": "livechat_product", "type": "Livechat",
     "position": (2200, 40),
     "connect_from": "calltoaction"},

    {"id": "stop_product", "type": "Stop",
     "position": (2400, 40),
     "connect_from": "livechat_product"},


    # ============================================================
    # STORE LOCATION BRANCH
    # Options branch 1
    # ============================================================

    {"id": "request_location", "type": "Request Location",
     "position": (800, 300),
     "connect_from": "options",
     "branch": 1},

    {"id": "condition_store", "type": "Condition",
     "position": (1050, 300),
     "connect_from": "request_location",
     "config": {
         "extra_paths": 1
     }},


    # ------------------------------------------------------------
    # Delhi NCR
    # ------------------------------------------------------------

    {"id": "share_location_delhi", "type": "Share Location",
     "position": (1300, 220),
     "connect_from": "condition_store",
     "branch": 0},

    {"id": "request_address_delhi", "type": "Request Address",
     "position": (1500, 220),
     "connect_from": "share_location_delhi"},

    {"id": "googleform", "type": "GoogleForm",
     "position": (1700, 220),
     "connect_from": "request_address_delhi"},

    {"id": "stop_delhi", "type": "Stop",
     "position": (1900, 220),
     "connect_from": "googleform"},


    # ------------------------------------------------------------
    # Mumbai
    # ------------------------------------------------------------

    {"id": "share_location_mumbai", "type": "Share Location",
     "position": (1300, 380),
     "connect_from": "condition_store",
     "branch": 1},

    {"id": "request_address_mumbai", "type": "Request Address",
     "position": (1500, 380),
     "connect_from": "share_location_mumbai"},

    {"id": "stop_mumbai", "type": "Stop",
     "position": (1700, 380),
     "connect_from": "request_address_mumbai"},


    # ------------------------------------------------------------
    # Other Location
    # ------------------------------------------------------------

    {"id": "http_other", "type": "HTTP",
     "position": (1300, 540),
     "connect_from": "condition_store",
     "branch": 2},

    {"id": "goto_other", "type": "Goto",
     "position": (1500, 540),
     "connect_from": "http_other"},

    {"id": "stop_other", "type": "Stop",
     "position": (1700, 540),
     "connect_from": "goto_other"},


    # ============================================================
    # TECHNICAL SUPPORT BRANCH
    # Options branch 2
    #
    # HTTP → Condition
    #           ↙       ↘
    #        Goto       Jump
    #           \       /
    #             Stop
    # ============================================================

    {"id": "http_tech", "type": "HTTP",
     "position": (800, 700),
     "connect_from": "options",
     "branch": 2,
     "config": {
         "title": "Support Ticket Webhook",
         "url": "https://example.com/support/ticket"
     }},

    {"id": "condition_tech", "type": "Condition",
     "position": (1050, 700),
     "connect_from": "http_tech"},

    {"id": "goto_tech", "type": "Goto",
     "position": (1250, 630),
     "connect_from": "condition_tech",
     "branch": 0},

    {"id": "jump_tech", "type": "Jump",
     "position": (1250, 770),
     "connect_from": "condition_tech",
     "branch": 1},

    {"id": "stop_tech", "type": "Stop",
     "position": (1500, 700),
     "connect_from": "goto_tech"},
]

# Applied after every step in COMPLEX_FLOW_STEPS exists: a second incoming connection for a
# node that already got its first one via `connect_from` above (Jump -> stop_tech, alongside
# Goto -> stop_tech from the step list).
COMPLEX_FLOW_EXTRA_CONNECTIONS = [
    {"source": "jump_tech", "target": "stop_tech"},
]
