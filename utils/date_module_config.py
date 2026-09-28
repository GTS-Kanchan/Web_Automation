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
}
