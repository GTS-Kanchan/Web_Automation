"""
utils/date_module_config.py

Single source of truth for WHICH date/date-time columns each SMS module's
UI table and export file actually have -- per this project's own
constants/*_ui_headers.py / *_headers.py files (the already-existing,
already-confirmed single source of truth for every module's real column
set, built from live DOM/export captures -- see each constants file's
own docstring). Nothing here invents a column that isn't already present
in one of those confirmed lists.

Each module entry:
    "date_columns"    -- the CANONICAL name for each date/date-time
                          field, one per real field this module has.
                          This is the export's own header text where an
                          export exists (matches constants/*_headers.py
                          exactly), since utils.file_validator.read_file_rows()
                          returns dicts keyed by the export's real header
                          row -- using any other spelling here would
                          silently fail to match those keys.
    "ui_column_names" -- {canonical_name: real_ui_header_text}, ONLY for
                          a column whose UI label differs from its
                          canonical/export name. This project's UI and
                          export header labels for the SAME real field
                          routinely differ only in casing (UI "Created
                          at" vs export "Created At" -- confirmed across
                          every constants/*_ui_headers.py / *_headers.py
                          pair). A column omitted from this dict uses its
                          canonical name unchanged as the UI lookup name
                          too (correct when both sides are identical,
                          e.g. SMS Messages' "Received At").
    "export_date_columns" -- subset of "date_columns" that a CONFIRMED
                          bulk export actually carries. None (not an
                          empty list) means this module has no bulk
                          export whose date columns are known to
                          represent the SAME field as anything in the UI
                          table (see Download Center below) -- UI-side
                          format-only validation applies, no UI-vs-export
                          comparison is attempted.
    "field_kinds"     -- {canonical_name: "date" | "date-time" | "auto"}.
                          "date-time" only where this project has
                          independently confirmed the column always
                          carries a time component in practice (SMS
                          Messages' 3 timestamp columns, already
                          validated as such by
                          tests/sms/campaigns/test_sms_campaign_message_report_flow.py's
                          TOTAL_MESSAGES_TYPE_SPEC; Campaign List's
                          "Created at", user-confirmed directly in this
                          project's own test-authoring session).
                          Everything else defaults to "auto" (valid as
                          either dd-mm-yyyy or dd-mm-yyyy hh:mm:ss) since
                          this project has not independently confirmed a
                          stricter shape for those columns.

Two modules -- Block Keywords, Error Codes -- are deliberately absent
from DATE_MODULE_CONFIG: their own confirmed UI header lists
(constants/sms_blocked_keywords_ui_headers.py: Action/Keyword/Status;
constants/sms_error_codes_ui_headers.py: Name/code/description) contain
NO date/date-time column at all, and neither page object has any
export/download capability. Per this task's own rule ("Do not fail a
test merely because a module does not contain a date column"), these
two are not silently included with a fabricated column -- see
tests/sms/opt_out/test_sms_blocked_keywords_flow.py and
tests/sms/reports/test_sms_error_codes_flow.py for the documented no-op
test that records this rather than skipping it invisibly.
"""

DATE_MODULE_CONFIG = {
    "sms_messages": {
        "date_columns": ["Received At", "Submitted At", "DLR Received At"],
        "ui_column_names": {},  # identical casing both sides
        "export_date_columns": ["Received At", "Submitted At", "DLR Received At"],
        "field_kinds": {
            "Received At": "date-time",
            "Submitted At": "date-time",
            "DLR Received At": "date-time",
        },
    },
    "campaign_list": {
        "date_columns": ["Created At", "Scheduled At"],
        "ui_column_names": {"Created At": "Created at", "Scheduled At": "Scheduled at"},
        # No confirmed bulk CSV/XLSX export header spec exists yet for
        # the Campaign LIST page itself (SMSCampaignPage.export_campaigns()
        # triggers a real download, but no constants/*_headers.py was
        # ever built to confirm its column set/order -- unlike every
        # other module below). UI-side format validation only.
        "export_date_columns": None,
        "field_kinds": {
            "Created At": "date-time",
            "Scheduled At": "auto",
        },
    },
    "sender_ids": {
        "date_columns": ["Created At", "Updated At"],
        "ui_column_names": {"Created At": "Created at", "Updated At": "Updated at"},
        "export_date_columns": ["Created At", "Updated At"],
        "field_kinds": {"Created At": "auto", "Updated At": "auto"},
    },
    "templates": {
        "date_columns": ["Created At"],
        "ui_column_names": {"Created At": "Created at"},
        "export_date_columns": ["Created At"],
        "field_kinds": {"Created At": "auto"},
    },
    "download_center": {
        "date_columns": ["Created At"],
        "ui_column_names": {"Created At": "Created at"},
        # The Download Center list's "Created at" column is when the
        # DOWNLOAD REQUEST was created. Its own bulk export headers
        # (constants/sms_download_headers.py: Created At/Submitted
        # At/Dlr Received At/Clicked At) describe the CONTENT of each
        # individual downloaded report file (per-row download, not a
        # table-level export of the list itself) -- a different,
        # unrelated date field, not a second representation of the same
        # value. Comparing them as if UI vs export of the same field
        # would be a fabricated correspondence, so this module gets
        # UI-side format validation only, same as Campaign List above.
        "export_date_columns": None,
        "field_kinds": {"Created At": "auto"},
    },
    "incoming_messages": {
        "date_columns": ["Received At"],
        "ui_column_names": {},  # identical casing both sides
        "export_date_columns": ["Received At"],
        "field_kinds": {"Received At": "auto"},
    },
    "block_numbers": {
        "date_columns": ["Created At"],
        "ui_column_names": {"Created At": "Created at"},
        "export_date_columns": ["Created At"],
        "field_kinds": {"Created At": "auto"},
    },

    # ------------------------------------------------------------------
    # RCS modules (7, per explicit project-owner scope: RCS Messages,
    # RCS Campaign List, RCS Agents, RCS Templates, RCS Download Center,
    # RCS Incoming Messages, RCS Blocked Numbers -- "Capability Checks"
    # and "RCS Campaign/Message Reports" explicitly dropped from scope;
    # the existing RCS Analytics report "Duration" date tests, which use
    # accept_iso=True, are untouched by this section). Column sets are
    # taken directly from each module's own already-confirmed
    # constants/rcs/**/*_ui_headers.py / *_headers.py files -- the same
    # single source of truth used for the SMS entries above. Every RCS
    # UI/export date value observed so far in this project (including a
    # real pasted DOM capture of the RCS Templates list, e.g.
    # "28-09-2026 15:44:33") carries a full dd-mm-yyyy hh:mm:ss shape, so
    # no accept_no_seconds/accept_iso relaxation is configured for any
    # RCS entry below -- this task requires strict dd-mm-yyyy /
    # dd-mm-yyyy hh:mm:ss only, with yyyy-mm-dd, dd/mm/yyyy, dd-mm-yy,
    # no-seconds timestamps, and ISO-8601 all explicitly rejected.
    # ------------------------------------------------------------------
    "rcs_messages": {
        # Constants: constants/rcs/messaging/rcs_message_ui_headers.py
        # (UI) / rcs_message_headers.py (export). "Clicked At" is UI-only
        # (no export column of that name) so it is left out of this
        # UI-vs-export pipeline, same convention as every SMS entry
        # above (a column config here always represents a genuine,
        # confirmed UI+export correspondence for the SAME field).
        "date_columns": ["Submitted At", "Delivered At", "Read At", "Failed At", "Created At"],
        "ui_column_names": {
            "Submitted At": "Submitted at",
            "Delivered At": "Delivered at",
            "Read At": "Read at",
            "Failed At": "Failed at",
            "Created At": "Created at",
        },
        "export_date_columns": ["Submitted At", "Delivered At", "Read At", "Failed At", "Created At"],
        "field_kinds": {
            "Submitted At": "date-time",
            "Delivered At": "date-time",
            "Read At": "date-time",
            "Failed At": "date-time",
            "Created At": "date-time",
        },
    },
    "rcs_campaign_list": {
        # Constants: constants/rcs/campaigns/rcs_campaign_ui_headers.py
        # (UI) / rcs_campaign_headers.py (export). Export-only columns
        # (Started At/Completed At/Updated At) are deliberately excluded
        # here, same convention as SMS Campaign List above.
        "date_columns": ["Created At", "Scheduled At"],
        "ui_column_names": {},  # identical casing both sides (confirmed via EXPECTED_RCS_CAMPAIGN_UI_HEADERS)
        "export_date_columns": ["Created At", "Scheduled At"],
        "field_kinds": {"Created At": "auto", "Scheduled At": "auto"},
    },
    "rcs_agents": {
        # Constants: constants/rcs/agent/rcs_agent_ui_headers.py (UI) /
        # rcs_agent_list_headers.py (export). Export-only "Updated At"
        # excluded, same convention as above.
        "date_columns": ["Created At"],
        "ui_column_names": {"Created At": "Created at"},
        "export_date_columns": ["Created At"],
        "field_kinds": {"Created At": "auto"},
    },
    "rcs_templates": {
        # Constants: real pasted DOM of /rcs/template (UI header order
        # Action/Name/Message Type/Agent/Status/Product/Is Public/
        # Last Used At/Created At/Updated At) / constants/rcs/templates/
        # rcs_template_list_headers.py (export). "Last Used At" is
        # UI-only (no export column of that name) so it is excluded from
        # this UI-vs-export pipeline, same convention as "Clicked At"
        # above. Real observed Created At/Updated At values in the
        # pasted DOM (e.g. "28-09-2026 15:44:33", "25-09-2026 16:19:55")
        # all carry seconds -- field_kind="date-time", no relaxation.
        "date_columns": ["Created At", "Updated At"],
        "ui_column_names": {},  # UI table renders "Created At"/"Updated At" verbatim (confirmed via pasted DOM)
        "export_date_columns": ["Created At", "Updated At"],
        "field_kinds": {"Created At": "date-time", "Updated At": "date-time"},
    },
    "rcs_download_center": {
        # Constants: constants/rcs/reports/rcs_download_center_ui_headers.py
        # (UI). Like SMS Download Center, the per-row REPORT's own export
        # headers (rcs_download_center_headers.py) describe the content
        # of an individual downloaded report file, not a second
        # representation of the LIST's own "Created At" -- so
        # export_date_columns is None (UI-side format validation only),
        # same convention/reasoning as SMS Download Center above.
        "date_columns": ["Created At"],
        "ui_column_names": {},  # EXPECTED_RCS_DOWNLOAD_CENTER_UI_HEADERS already lists "Created At" verbatim
        "export_date_columns": None,
        "field_kinds": {"Created At": "auto"},
    },
    "rcs_incoming_messages": {
        # Constants: constants/rcs/messaging/rcs_incoming_messages_ui_headers.py
        # (UI) / rcs_incoming_messages_headers.py (export). Both columns
        # confirmed present, identical casing, on both sides.
        "date_columns": ["Received At", "Created At"],
        "ui_column_names": {},  # identical casing both sides
        "export_date_columns": ["Received At", "Created At"],
        "field_kinds": {"Received At": "auto", "Created At": "auto"},
    },
    "rcs_blocked_numbers": {
        # Constants: constants/rcs/opt_out/rcs_optout_ui_headers.py (UI)
        # / rcs_optout_headers.py (export). Export-only "Reason"/"ID" are
        # not date columns so nothing to exclude there.
        "date_columns": ["Opted Out At"],
        "ui_column_names": {},  # identical casing both sides
        "export_date_columns": ["Opted Out At"],
        "field_kinds": {"Opted Out At": "auto"},
    },
    # ------------------------------------------------------------------
    # WhatsApp modules (11, per explicit project-owner scope document:
    # WhatsApp Messages, WhatsApp Campaign List, WhatsApp Number,
    # WhatsApp Templates, WhatsApp Download Center, WhatsApp Incoming
    # Messages, WhatsApp Blocked Users, WhatsApp Campaign
    # Reports/Message Reports, WhatsApp Opt-in, WhatsApp Opt-out,
    # WhatsApp Flows). Unlike RCS/SMS, NO constants/whatsapp/*_headers.py
    # files exist for any module (confirmed: `find constants -iname
    # "*whatsapp*"` returns nothing) -- every column name below is taken
    # instead from each module's own already-confirmed evidence already
    # living in this project's page objects/tests (a COLUMN_INDEX dict,
    # a "sortBy(...)" applied-sort pill assertion e.g. "created at:
    # Z-A", or a docstring/test listing real captured DOM column
    # headers -- see each entry's own comment for its specific source).
    # None of these modules has a confirmed bulk-export column-name
    # correspondence for any date field (every export capability seen so
    # far -- CSV href, "Export to XLSX" trigger -- is only asserted by
    # href/dialog-presence, never downloaded and parsed against a real
    # header list), so every entry's "export_date_columns" is None and
    # verification is UI-format-only, same convention as
    # "campaign_list"/"download_center" above. Do not add an export
    # correspondence here without first downloading and parsing a real
    # file to confirm the column name, per this project's own rule.
    # ------------------------------------------------------------------
    "whatsapp_messages": {
        # WhatsApp Messages (Messages Report) --
        # pages/whatsapp/messaging/whatsapp_message_report_page.py.
        # Columns confirmed via
        # tests/whatsapp/messaging/test_whatsapp_message_report_flow.py's
        # own _ROW_HEADERS_FOR_POPUP_CROSSCHECK dict (real
        # get_column_values() lookups against the live table): "created
        # at", "submitted at", "delivered at", "read at". A confirmed
        # "failed at" sort button exists (SORT_FAILED_AT_BTN) but no
        # test ever confirmed it as a visible TABLE column (only the
        # Timeline popup section renders "Failed"), so it is left out of
        # this table-level entry, not fabricated in.
        "date_columns": ["Created At", "Submitted At", "Delivered At", "Read At"],
        "ui_column_names": {
            "Created At": "created at",
            "Submitted At": "submitted at",
            "Delivered At": "delivered at",
            "Read At": "read at",
        },
        "export_date_columns": None,
        "field_kinds": {
            "Created At": "auto",
            "Submitted At": "auto",
            "Delivered At": "auto",
            "Read At": "auto",
        },
    },
    "whatsapp_campaign_list": {
        # WhatsApp Campaign List --
        # pages/whatsapp/campaigns/whatsapp_campaign_page.py. "Created
        # At" confirmed via test_TC_sorting's applied-sort-pill assertion
        # ("created at" in pill.lower()); "Scheduled at" confirmed via
        # this page's own module docstring/sorting comment ("Action/Total
        # Messages/Scheduled at are [not sortable]" -- i.e. the column
        # exists, just isn't a sort target).
        "date_columns": ["Created At", "Scheduled At"],
        "ui_column_names": {"Created At": "created at", "Scheduled At": "scheduled at"},
        "export_date_columns": None,
        "field_kinds": {"Created At": "auto", "Scheduled At": "auto"},
    },
    "whatsapp_number": {
        # WhatsApp Number (Sender ID) --
        # pages/whatsapp/sender_id/whatsapp_sender_id_page.py. Only
        # "created_at" appears in this page's own confirmed COLUMN_INDEX
        # dict (Action/App Name/WABA Number/Status/Quality/Message
        # Limit/MM Lite APIs/Created At) -- unlike SMS's Sender ID
        # module, there is no confirmed "Updated At" column here, so
        # none is added.
        "date_columns": ["Created At"],
        "ui_column_names": {"Created At": "created at"},
        "export_date_columns": None,
        "field_kinds": {"Created At": "auto"},
    },
    "whatsapp_templates": {
        # WhatsApp Templates -- pages/whatsapp/templates/whatsapp_template_page.py.
        # "created_at" confirmed via this page's own SORT_KEYS dict and
        # test_TC013_sorting_created_at_column's applied-sort-pill
        # assertion ("created at" in pill.lower()).
        "date_columns": ["Created At"],
        "ui_column_names": {"Created At": "created at"},
        "export_date_columns": None,
        "field_kinds": {"Created At": "auto"},
    },
    "whatsapp_download_center": {
        # WhatsApp Download Center --
        # pages/whatsapp/download_center/whatsapp_download_center_page.py.
        # "Created At" confirmed verbatim via
        # tests/whatsapp/download_center/test_whatsapp_download_center_flow.py's
        # own TestTC02TableColumns docstring, itself built from a real
        # captured column list (Actions, Name, Category, From, To,
        # Created At, Status), and independently via the "created-at"
        # slug used elsewhere in that same test file. "From"/"To" are
        # real confirmed columns too, but no test/DOM evidence confirms
        # they actually hold date VALUES (as opposed to e.g. a
        # date-range filter echo or free text) rather than assuming, so
        # they are deliberately left out here -- same "do not invent"
        # convention as RCS Templates' "Last Used At" above.
        "date_columns": ["Created At"],
        "ui_column_names": {"Created At": "created at"},
        "export_date_columns": None,
        "field_kinds": {"Created At": "auto"},
    },
    "whatsapp_incoming_messages": {
        # WhatsApp Incoming Messages --
        # pages/whatsapp/messaging/whatsapp_incoming_messages_page.py.
        # Both columns confirmed via this page's own COLUMN_INDEX dict
        # (Action/Campaign Name/WABA Number/Country Code/User
        # Number/User Name/Type/Received At/Created At) and via
        # tests/whatsapp/more/test_whatsapp_incoming_messages_flow.py's
        # own comment ("only Received At / Created At are sortable").
        "date_columns": ["Received At", "Created At"],
        "ui_column_names": {"Received At": "received at", "Created At": "created at"},
        "export_date_columns": None,
        "field_kinds": {"Received At": "auto", "Created At": "auto"},
    },
    "whatsapp_blocked_users": {
        # WhatsApp Blocked Users -- pages/whatsapp/more/whatsapp_blocked_users_page.py.
        # "blocked_at" confirmed via this page's own COLUMN_INDEX dict
        # (bulk_checkbox/phone_number/sender_id/blocked_at/actions) and
        # sort_by_blocked_at() used in
        # tests/whatsapp/more/test_whatsapp_blocked_users_flow.py.
        "date_columns": ["Blocked At"],
        "ui_column_names": {"Blocked At": "blocked at"},
        "export_date_columns": None,
        "field_kinds": {"Blocked At": "auto"},
    },
    "whatsapp_campaign_reports": {
        # WhatsApp Campaign Reports / Message Reports (per-campaign
        # report page, DISTINCT from the top-level "WhatsApp Messages"
        # report above) --
        # pages/whatsapp/campaigns/whatsapp_campaign_report_page.py.
        # Columns confirmed via
        # tests/whatsapp/campaigns/test_whatsapp_campaign_report_flow.py's
        # own _ROW_HEADERS_FOR_POPUP_CROSSCHECK dict (real
        # get_column_values() lookups): "created at", "sent at",
        # "delivered at", "read at".
        "date_columns": ["Created At", "Sent At", "Delivered At", "Read At"],
        "ui_column_names": {
            "Created At": "created at",
            "Sent At": "sent at",
            "Delivered At": "delivered at",
            "Read At": "read at",
        },
        "export_date_columns": None,
        "field_kinds": {
            "Created At": "auto",
            "Sent At": "auto",
            "Delivered At": "auto",
            "Read At": "auto",
        },
    },
    "whatsapp_optin": {
        # WhatsApp Opt-in -- pages/whatsapp/more/whatsapp_optin_page.py.
        # "opted_in_at" confirmed via this page's own COLUMN_INDEX dict
        # (bulk_checkbox/action/phone_number/sender/opted_in_at) and
        # sort_by_opted_in_at() used in
        # tests/whatsapp/more/test_whatsapp_optin_flow.py.
        "date_columns": ["Opted In At"],
        "ui_column_names": {"Opted In At": "opted in at"},
        "export_date_columns": None,
        "field_kinds": {"Opted In At": "auto"},
    },
    "whatsapp_optout": {
        # WhatsApp Opt-out -- pages/whatsapp/more/whatsapp_optout_page.py.
        # "opted_out_at" confirmed via this page's own COLUMN_INDEX dict
        # (bulk_checkbox/action/phone_number/sender/opted_out_at) and
        # sort_by_opted_out_at() used in
        # tests/whatsapp/more/test_whatsapp_optout_flow.py.
        "date_columns": ["Opted Out At"],
        "ui_column_names": {"Opted Out At": "opted out at"},
        "export_date_columns": None,
        "field_kinds": {"Opted Out At": "auto"},
    },
    "whatsapp_flows": {
        # WhatsApp Flows -- pages/whatsapp/more/whatsapp_flows_page.py
        # (the Flows LIST page -- disambiguated from
        # whatsapp_flow_builder_page.py/flow_builder_page.py/
        # test_flow_builder.py, which build/edit a single flow's canvas
        # and have no list-table date column at all). Only "created_at"
        # appears in this page's own confirmed COLUMN_INDEX dict
        # (Action/Flow ID/Name/WABA Number/Status/Categories/Created
        # At), confirmed too via
        # tests/whatsapp/more/test_whatsapp_flows_flow.py's
        # applied-sort-pill assertion ("created at" in pill.lower()).
        # The spec's "creation/update/publish" date fields degrade to
        # creation-only here since no Updated At/Published At column is
        # present in this list table -- not fabricated in.
        "date_columns": ["Created At"],
        "ui_column_names": {"Created At": "created at"},
        "export_date_columns": None,
        "field_kinds": {"Created At": "auto"},
    },
}

