"""
utils/header_module_config.py

Single source of truth for each module's expected UI/export table
headers, for utils/header_verification.py's verify_module_headers().
Same convention as utils/date_module_config.py's DATE_MODULE_CONFIG for
dates -- do not hard-code a module's expected header list inline in a
test file; import EXPECTED_HEADERS from here.

Each module entry:
    "ui"     -- ordered list of the module's confirmed, real, default-
                rendered on-screen table column headers (a blank/
                icon-only column such as a bulk-select checkbox is
                deliberately left OUT of this list -- it has no header
                text to name). This project's table columns are
                user-toggleable (a "Columns" dropdown lets a user
                show/hide optional columns), so verify_ui_headers()
                checks PRESENCE only (every "ui" entry must be found
                somewhere on screen), never exact-set/order equality --
                an extra, currently-toggled-on optional column is not a
                failure.
    "export" -- ordered list of the module's confirmed real export
                header row, or None when no export capability has been
                downloaded and parsed yet to confirm one (UI Header
                Verification only applies then -- see this file's
                module docstring).
    "case_insensitive" -- comparison case-sensitivity for the UI side
                (and, by default, the UI-vs-export comparison). Defaults
                to True everywhere below, matching this project's
                already-established UI-header convention (see
                tests/sms/sender_id/test_sms_sender_id.py's
                test_ui_default_table_headers_full).
    "export_case_insensitive" -- comparison case-sensitivity for the
                export side. Defaults to False (case-SENSITIVE exact
                match), matching this project's existing
                utils.file_validator.validate_file_headers() convention.
    "order_sensitive" -- whether the EXPORT header row's column order
                must match "export" exactly. Defaults to False (order
                not currently confirmed as application-required for any
                WhatsApp module); flip to True only once a real,
                confirmed fixed-order requirement is established for a
                specific module's export.

Unlike RCS/SMS, no constants/whatsapp/*_headers.py files exist for any
WhatsApp module (confirmed: `find constants -iname "*whatsapp*"`
returns nothing) -- every "ui" list below is taken instead from
already-confirmed evidence living in this project's own page objects (a
COLUMN_INDEX dict explicitly documented as "confirmed default-rendered
column order", or a docstring enumerating the real captured DOM column
list / selectable-columns snapshot) -- see each entry's own comment for
its specific source. As of 2026-09-30, 6 of these 11 modules have a
real, confirmed "export" list, sourced from 7 real downloaded/parsed
export files (whatsapp_messages, whatsapp_campaign_list, whatsapp_number,
whatsapp_templates, whatsapp_incoming_messages, whatsapp_campaign_reports).
The remaining 5 (whatsapp_download_center, whatsapp_blocked_users,
whatsapp_opt_in, whatsapp_opt_out, whatsapp_flows) still have
"export": None -- no export file has been downloaded and parsed for
them yet. Do not add an "export" list here without first downloading
and parsing a real file to confirm it.
"""

EXPECTED_HEADERS = {
    # ------------------------------------------------------------------
    # WhatsApp modules (11, per explicit project-owner scope document).
    # ------------------------------------------------------------------
    "whatsapp_messages": {
        # WhatsApp Messages (Messages Report) --
        # pages/whatsapp/messaging/whatsapp_message_report_page.py.
        # Confirmed DEFAULT-visible columns: the 10 real columns named in
        # tests/whatsapp/messaging/test_whatsapp_message_report_flow.py's
        # own _ROW_HEADERS_FOR_POPUP_CROSSCHECK dict (a live
        # get_column_values() lookup against each), plus "Action"
        # (confirmed via TC008's View-icon-in-Actions-column test). This
        # table also has a "Columns" dropdown with additional optional
        # columns (module docstring: "16-18 possibly-toggled columns")
        # not individually confirmed by name here -- not fabricated in;
        # verify_ui_headers() only checks presence, so an extra toggled
        # column never fails this list.
        "ui": [
            "Action", "To Number", "Country Code", "Source", "Sub-Source",
            "Template Category", "Status", "Created At", "Submitted At",
            "Delivered At", "Read At",
        ],
        # Export CONFIRMED via a real downloaded/parsed file (WhatsApp
        # Messages Report export, 20 columns) -- far more detail columns
        # than the UI's default 11 (ID/Message ID/Correlation ID/
        # Recipient Number/Template Name/Template Type/MM Lite
        # Status/Error Description are export-only). Note the export's
        # "Recipient Number" is the same real field as the UI's "To
        # Number" (different label, same column -- NOT wired into
        # compare_ui_export_headers() as a correspondence here since
        # this engine does exact-name matching only; a synonym map would
        # be needed to compare them, out of scope for this pass).
        "export": [
            "ID", "Message ID", "Correlation ID", "Campaign Name",
            "Recipient Number", "Country Code", "Status", "Template Name",
            "Template Category", "Template Type", "WABA Number",
            "MM Lite Status", "Source", "Sub-Source", "Created At",
            "Submitted At", "Delivered At", "Read At", "Failed At",
            "Error Description",
        ],
        "export_only": [
            "ID", "Message ID", "Correlation ID", "Campaign Name",
            "Template Name", "Template Type", "WABA Number",
            "MM Lite Status", "Error Description",
        ],
        "ui_column_names": {
            "Recipient Number": "To Number",
        },
    },
    "whatsapp_campaign_list": {
        # WhatsApp Campaign List --
        # pages/whatsapp/campaigns/whatsapp_campaign_page.py. Confirmed
        # via this page's own sort-button set (Name/Type/Template/WABA
        # Number/Status/Created At) plus its own comment naming the 3
        # non-sortable-but-real columns (Action/Total Messages/Scheduled
        # at).
        "ui": [
            "Action", "Name", "Type", "Template", "WABA Number", "Status",
            "Total Messages", "Scheduled At", "Created At",
        ],
        # Export CONFIRMED via a real downloaded/parsed file (Whatsapp
        # Campaign Summary export). Note two real UI-vs-export naming
        # differences: export "Campaign Name" vs UI "Name", and
        # export "Template Name" vs UI "Template" -- mapped via
        # ui_column_names below. ID is export-only.
        "export": [
            "ID", "Campaign Name", "Type", "Template Name", "WABA Number",
            "Status", "Total Messages", "Created At", "Scheduled At",
        ],
        "export_only": ["ID"],
        "ui_column_names": {
            "Campaign Name": "Name",
            "Template Name": "Template",
        },
    },
    "whatsapp_number": {
        # WhatsApp Number (Sender ID) --
        # pages/whatsapp/sender_id/whatsapp_sender_id_page.py. Confirmed
        # via this page's own COLUMN_INDEX dict, documented as "Confirmed
        # default-rendered column order (8 of 10 selectable columns --
        # Department/User are deselected by default)".
        "ui": [
            "Action", "App Name", "WABA Number", "Status", "Quality",
            "Message Limit", "MM Lite APIs", "Created At",
        ],
        # Export CONFIRMED via two real downloaded/parsed files (Whatsapp
        # SenderId Summary, identical headers both times). Real
        # UI-vs-export naming differences mapped via ui_column_names:
        # export "Name" vs UI "App Name", export "Number" vs UI "WABA Number",
        # export "MM Lite API" (singular) vs UI "MM Lite APIs" (plural).
        # Export also carries "Department"/"User" (deselected by default
        # in the UI) and "Updated At" -- declared in export_only.
        "export": [
            "ID", "Name", "Number", "Department", "User", "Status",
            "Quality", "Message Limit", "MM Lite API", "Created At",
            "Updated At",
        ],
        "export_only": ["ID", "Department", "User", "Updated At"],
        "ui_column_names": {
            "Name": "App Name",
            "Number": "WABA Number",
            "MM Lite API": "MM Lite APIs",
        },
    },
    "whatsapp_templates": {
        # WhatsApp Templates -- pages/whatsapp/templates/whatsapp_template_page.py.
        # Confirmed via this page's own module docstring: "Default
        # selectedColumns (8, confirmed from the snapshot) excludes
        # department and user" and "Column headers in DOM order: Action
        # (static), then 7 CONFIRMED sortable columns: Name, Category,
        # Type, WABA Number, Status, Quality, Created at".
        "ui": [
            "Action", "Name", "Category", "Type", "WABA Number", "Status",
            "Quality", "Created At",
        ],
        # Export CONFIRMED via a real downloaded/parsed file (Whatsapp
        # Template Summary export) -- matches the UI list closely (minus
        # the UI-only "Action" column), same names both sides.
        "export": ["Name", "Category", "Type", "WABA Number", "Status", "Quality", "Created at"],
        "export_case_insensitive": True,
    },
    "whatsapp_download_center": {
        # WhatsApp Download Center --
        # pages/whatsapp/download_center/whatsapp_download_center_page.py.
        # Confirmed verbatim via
        # tests/whatsapp/download_center/test_whatsapp_download_center_flow.py's
        # own TestTC02TableColumns docstring: "7 confirmed: Actions,
        # Name, Category, From, To, Created At, Status".
        "ui": ["Actions", "Name", "Category", "From", "To", "Created At", "Status"],
        "export": None,
    },
    "whatsapp_incoming_messages": {
        # WhatsApp Incoming Messages --
        # pages/whatsapp/messaging/whatsapp_incoming_messages_page.py.
        # Confirmed via this page's own COLUMN_INDEX dict, documented as
        # "Confirmed column order (all 9 columns selected by default)".
        "ui": [
            "Action", "Campaign Name", "WABA Number", "Country Code",
            "User Number", "User Name", "Type", "Received At", "Created At",
        ],
        # Export CONFIRMED via a real downloaded/parsed file (WhatsApp
        # Incoming Messages export). Matches the UI list closely (minus
        # the UI-only "Action" column), same names both sides. Export
        # also carries an extra "Message" column with no corresponding
        # confirmed UI column -- export-only, not a problem.
        "export": [
            "Campaign Name", "WABA Number", "Country Code", "User Number",
            "User Name", "Type", "Message", "Received At", "Created At",
        ],
        "export_only": ["Message"],
    },
    "whatsapp_blocked_users": {
        # WhatsApp Blocked Users -- pages/whatsapp/more/whatsapp_blocked_users_page.py.
        # Confirmed via this page's own COLUMN_INDEX dict, documented as
        # "Confirmed column order (bulk-select checkbox column + 4 real
        # columns, all selected by default)". The bulk-select checkbox
        # column has no header text, so it is left out of this list (see
        # this file's module docstring).
        "ui": ["Phone Number", "Sender Id", "Blocked At", "Actions"],
        "export": None,
    },
    "whatsapp_campaign_reports": {
        # WhatsApp Campaign Reports / Message Reports (per-campaign
        # report page, DISTINCT from the top-level "WhatsApp Messages"
        # report above) --
        # pages/whatsapp/campaigns/whatsapp_campaign_report_page.py.
        # Confirmed via this page's own module docstring: "The 'All
        # Columns' checkbox here is CHECKED BY DEFAULT" and "Selectable
        # columns confirmed: action, contact, country-code, status,
        # is-mm-lite-used, created-at, sent-at, delivered-at, failed-at,
        # read-at".
        "ui": [
            "Action", "Contact", "Country Code", "Status", "Is MM Lite Used",
            "Created At", "Sent At", "Delivered At", "Failed At", "Read At",
        ],
        # Export CONFIRMED via a real downloaded/parsed file
        # (campaign_export, the per-campaign report export). Matches the
        # UI list cleanly (minus the UI-only "Action" column), same
        # names both sides.
        "export": [
            "Contact", "Country Code", "Status", "Is MM Lite Used",
            "Created At", "Sent At", "Delivered At", "Failed At", "Read At",
        ],
    },
    "whatsapp_opt_in": {
        # WhatsApp Opt-in -- pages/whatsapp/more/whatsapp_optin_page.py.
        # Confirmed via this page's own COLUMN_INDEX dict, documented as
        # "Confirmed column order for the DEFAULT (all-selected) column
        # state, including the leading bulk-selection checkbox column"
        # (that checkbox column itself has no header text, so it is left
        # out of this list, same convention as Blocked Users above).
        "ui": ["Action", "Phone Number", "Sender", "Opted In At"],
        "export": None,
    },
    "whatsapp_opt_out": {
        # WhatsApp Opt-out -- pages/whatsapp/more/whatsapp_optout_page.py.
        # Confirmed via this page's own COLUMN_INDEX dict, documented as
        # "Confirmed column order for the DEFAULT (all-selected) column
        # state only" (leading bulk-selection checkbox column left out,
        # same convention as above).
        "ui": ["Action", "Phone Number", "Sender", "Opted Out At"],
        "export": None,
    },
    "whatsapp_flows": {
        # WhatsApp Flows -- pages/whatsapp/more/whatsapp_flows_page.py
        # (the Flows LIST page). Confirmed via this page's own
        # COLUMN_INDEX dict, documented as "Confirmed default-rendered
        # column order (7 of 8 selectable columns -- Sender is
        # deselected by default)".
        "ui": [
            "Action", "Flow ID", "Name", "WABA Number", "Status",
            "Categories", "Created At",
        ],
        "export": None,
    },
}
