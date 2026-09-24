"""
constants package.
Organized into channel and section subpackages:
  - constants.common
  - constants.chatbot (download_center, reports)
  - constants.email (messages)
  - constants.rcs (agent, campaigns, messaging, opt_out, reports, templates)
  - constants.sms (campaigns, messaging, opt_out, reports, sender_id, templates)

Supports both:
  1. Structured imports:
     from constants.common.activity_ui_headers import EXPECTED_ACTIVITY_UI_HEADERS
     from constants.chatbot.reports.chatbot_detailed_constants import ...
  2. Legacy flat imports for backward compatibility:
     from constants.activity_ui_headers import EXPECTED_ACTIVITY_UI_HEADERS
"""

import sys
import importlib
from importlib.abc import MetaPathFinder, Loader
from importlib.machinery import ModuleSpec

# Map legacy module names to their new structured paths
LEGACY_MODULE_MAP = {'activity_ui_headers': 'constants.common.activity_ui_headers', 'document_ui_headers': 'constants.common.document_ui_headers', 'monthly_usage_ui_headers': 'constants.common.monthly_usage_ui_headers', 'tags': 'constants.common.tags', 'chatbot_report_constants': 'constants.chatbot.download_center.chatbot_report_constants', 'chatbot_summary_headers': 'constants.chatbot.reports.chatbot_summary_headers', 'chatbot_detailed_constants': 'constants.chatbot.reports.chatbot_detailed_constants', 'chatbot_repetitive_user_constants': 'constants.chatbot.reports.chatbot_repetitive_user_constants', 'email_message_headers': 'constants.email.messages.email_message_headers', 'email_message_ui_headers': 'constants.email.messages.email_message_ui_headers', 'rcs_agent_analytics_headers': 'constants.rcs.agent.rcs_agent_analytics_headers', 'rcs_agent_analytics_ui_headers': 'constants.rcs.agent.rcs_agent_analytics_ui_headers', 'rcs_agent_list_headers': 'constants.rcs.agent.rcs_agent_list_headers', 'rcs_agent_ui_headers': 'constants.rcs.agent.rcs_agent_ui_headers', 'rcs_campaign_analytics_headers': 'constants.rcs.campaigns.rcs_campaign_analytics_headers', 'rcs_campaign_analytics_ui_headers': 'constants.rcs.campaigns.rcs_campaign_analytics_ui_headers', 'rcs_campaign_headers': 'constants.rcs.campaigns.rcs_campaign_headers', 'rcs_campaign_ui_headers': 'constants.rcs.campaigns.rcs_campaign_ui_headers', 'rcs_incoming_messages_headers': 'constants.rcs.messaging.rcs_incoming_messages_headers', 'rcs_incoming_messages_ui_headers': 'constants.rcs.messaging.rcs_incoming_messages_ui_headers', 'rcs_message_headers': 'constants.rcs.messaging.rcs_message_headers', 'rcs_message_ui_headers': 'constants.rcs.messaging.rcs_message_ui_headers', 'rcs_optout_headers': 'constants.rcs.opt_out.rcs_optout_headers', 'rcs_optout_ui_headers': 'constants.rcs.opt_out.rcs_optout_ui_headers', 'rcs_country_analytics_headers': 'constants.rcs.reports.rcs_country_analytics_headers', 'rcs_country_analytics_ui_headers': 'constants.rcs.reports.rcs_country_analytics_ui_headers', 'rcs_download_center_headers': 'constants.rcs.reports.rcs_download_center_headers', 'rcs_download_center_ui_headers': 'constants.rcs.reports.rcs_download_center_ui_headers', 'rcs_error_code_analytics_headers': 'constants.rcs.reports.rcs_error_code_analytics_headers', 'rcs_error_code_analytics_ui_headers': 'constants.rcs.reports.rcs_error_code_analytics_ui_headers', 'rcs_error_codes_ui_headers': 'constants.rcs.reports.rcs_error_codes_ui_headers', 'rcs_message_type_analytics_headers': 'constants.rcs.reports.rcs_message_type_analytics_headers', 'rcs_message_type_analytics_ui_headers': 'constants.rcs.reports.rcs_message_type_analytics_ui_headers', 'rcs_status_analytics_headers': 'constants.rcs.reports.rcs_status_analytics_headers', 'rcs_status_analytics_ui_headers': 'constants.rcs.reports.rcs_status_analytics_ui_headers', 'rcs_usage_analytics_headers': 'constants.rcs.reports.rcs_usage_analytics_headers', 'rcs_usage_analytics_ui_headers': 'constants.rcs.reports.rcs_usage_analytics_ui_headers', 'rcs_template_analytics_headers': 'constants.rcs.templates.rcs_template_analytics_headers', 'rcs_template_analytics_ui_headers': 'constants.rcs.templates.rcs_template_analytics_ui_headers', 'rcs_template_list_headers': 'constants.rcs.templates.rcs_template_list_headers', 'sms_campaign_report_headers': 'constants.sms.campaigns.sms_campaign_report_headers', 'sms_campaign_report_ui_headers': 'constants.sms.campaigns.sms_campaign_report_ui_headers', 'sms_campaign_ui_headers': 'constants.sms.campaigns.sms_campaign_ui_headers', 'sms_incoming_messages_headers': 'constants.sms.messaging.sms_incoming_messages_headers', 'sms_incoming_messages_ui_headers': 'constants.sms.messaging.sms_incoming_messages_ui_headers', 'sms_message_headers': 'constants.sms.messaging.sms_message_headers', 'sms_message_ui_headers': 'constants.sms.messaging.sms_message_ui_headers', 'sms_blocked_keywords_ui_headers': 'constants.sms.opt_out.sms_blocked_keywords_ui_headers', 'sms_blocked_numbers_headers': 'constants.sms.opt_out.sms_blocked_numbers_headers', 'sms_blocked_numbers_ui_headers': 'constants.sms.opt_out.sms_blocked_numbers_ui_headers', 'sms_country_report_headers': 'constants.sms.reports.sms_country_report_headers', 'sms_country_report_ui_headers': 'constants.sms.reports.sms_country_report_ui_headers', 'sms_download_center_ui_headers': 'constants.sms.reports.sms_download_center_ui_headers', 'sms_download_headers': 'constants.sms.reports.sms_download_headers', 'sms_error_code_report_headers': 'constants.sms.reports.sms_error_code_report_headers', 'sms_error_code_report_ui_headers': 'constants.sms.reports.sms_error_code_report_ui_headers', 'sms_error_codes_ui_headers': 'constants.sms.reports.sms_error_codes_ui_headers', 'sms_latency_report_headers': 'constants.sms.reports.sms_latency_report_headers', 'sms_latency_report_ui_headers': 'constants.sms.reports.sms_latency_report_ui_headers', 'sms_sender_report_headers': 'constants.sms.reports.sms_sender_report_headers', 'sms_sender_report_ui_headers': 'constants.sms.reports.sms_sender_report_ui_headers', 'sms_status_report_headers': 'constants.sms.reports.sms_status_report_headers', 'sms_status_report_ui_headers': 'constants.sms.reports.sms_status_report_ui_headers', 'sms_usage_report_headers': 'constants.sms.reports.sms_usage_report_headers', 'sms_usage_report_ui_headers': 'constants.sms.reports.sms_usage_report_ui_headers', 'sms_sender_id_headers': 'constants.sms.sender_id.sms_sender_id_headers', 'sms_sender_id_ui_headers': 'constants.sms.sender_id.sms_sender_id_ui_headers', 'sms_template_headers': 'constants.sms.templates.sms_template_headers', 'sms_template_report_headers': 'constants.sms.templates.sms_template_report_headers', 'sms_template_report_ui_headers': 'constants.sms.templates.sms_template_report_ui_headers', 'sms_template_ui_headers': 'constants.sms.templates.sms_template_ui_headers'}


class _LegacyConstantsLoader(Loader):
    def __init__(self, target_name):
        self.target_name = target_name

    def create_module(self, spec):
        mod = importlib.import_module(self.target_name)
        sys.modules[spec.name] = mod
        return mod

    def exec_module(self, module):
        pass


class _LegacyConstantsFinder(MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname.startswith("constants."):
            subname = fullname[len("constants."):]
            if subname in LEGACY_MODULE_MAP:
                target_name = LEGACY_MODULE_MAP[subname]
                return ModuleSpec(fullname, _LegacyConstantsLoader(target_name))
        return None


# Register finder at the head of sys.meta_path
if not any(isinstance(f, _LegacyConstantsFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, _LegacyConstantsFinder())
