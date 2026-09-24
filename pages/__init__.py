"""
pages package.
Organized into channel and section subpackages:
  - pages.common
  - pages.chatbot (download_center, reports)
  - pages.email (campaigns, messages, overview, templates)
  - pages.rcs (agent, campaigns, messaging, opt_out, overview, reports, templates)
  - pages.sms (campaigns, messaging, opt_out, overview, reports, sender_id, templates)
  - pages.whatsapp (campaigns, download_center, messaging, more, overview, reports, sender_id, templates)

Supports both:
  1. Section-wise imports:
     from pages.sms.campaigns.sms_campaign_page import SMSCampaignPage
  2. Legacy channel-level imports for backward compatibility:
     from pages.sms.sms_campaign_page import SMSCampaignPage
"""

import sys
import importlib
from importlib.abc import MetaPathFinder, Loader
from importlib.machinery import ModuleSpec

LEGACY_PAGES_MAP = {'pages.chatbot.chatbot_request_report_page': 'pages.chatbot.download_center.chatbot_request_report_page', 'pages.chatbot.chatbot_summary_report_page': 'pages.chatbot.reports.chatbot_summary_report_page', 'pages.chatbot.chatbot_detailed_report_page': 'pages.chatbot.reports.chatbot_detailed_report_page', 'pages.chatbot.chatbot_repetitive_user_report_page': 'pages.chatbot.reports.chatbot_repetitive_user_report_page', 'pages.email.email_campaign_page': 'pages.email.campaigns.email_campaign_page', 'pages.email.email_campaign_create_page': 'pages.email.campaigns.email_campaign_create_page', 'pages.email.email_messages_page': 'pages.email.messages.email_messages_page', 'pages.email.email_overview_page': 'pages.email.overview.email_overview_page', 'pages.email.email_template_page': 'pages.email.templates.email_template_page', 'pages.email.email_template_create_page': 'pages.email.templates.email_template_create_page', 'pages.rcs.rcs_agent_page': 'pages.rcs.agent.rcs_agent_page', 'pages.rcs.rcs_agent_analytics_page': 'pages.rcs.agent.rcs_agent_analytics_page', 'pages.rcs.rcs_campaign_page': 'pages.rcs.campaigns.rcs_campaign_page', 'pages.rcs.rcs_campaign_create_page': 'pages.rcs.campaigns.rcs_campaign_create_page', 'pages.rcs.rcs_campaign_analytics_page': 'pages.rcs.campaigns.rcs_campaign_analytics_page', 'pages.rcs.rcs_message_page': 'pages.rcs.messaging.rcs_message_page', 'pages.rcs.rcs_incoming_messages_page': 'pages.rcs.messaging.rcs_incoming_messages_page', 'pages.rcs.rcs_optout_page': 'pages.rcs.opt_out.rcs_optout_page', 'pages.rcs.rcs_overview_page': 'pages.rcs.overview.rcs_overview_page', 'pages.rcs.rcs_country_analytics_page': 'pages.rcs.reports.rcs_country_analytics_page', 'pages.rcs.rcs_download_center_page': 'pages.rcs.reports.rcs_download_center_page', 'pages.rcs.rcs_report_create_page': 'pages.rcs.reports.rcs_report_create_page', 'pages.rcs.rcs_error_codes_page': 'pages.rcs.reports.rcs_error_codes_page', 'pages.rcs.rcs_error_code_analytics_page': 'pages.rcs.reports.rcs_error_code_analytics_page', 'pages.rcs.rcs_message_type_analytics_page': 'pages.rcs.reports.rcs_message_type_analytics_page', 'pages.rcs.rcs_status_analytics_page': 'pages.rcs.reports.rcs_status_analytics_page', 'pages.rcs.rcs_usage_analytics_page': 'pages.rcs.reports.rcs_usage_analytics_page', 'pages.rcs.rcs_template_create_page': 'pages.rcs.templates.rcs_template_create_page', 'pages.rcs.rcs_template_analytics_page': 'pages.rcs.templates.rcs_template_analytics_page', 'pages.sms.sms_campaign_page': 'pages.sms.campaigns.sms_campaign_page', 'pages.sms.sms_campaign_message_report_page': 'pages.sms.campaigns.sms_campaign_message_report_page', 'pages.sms.sms_message_page': 'pages.sms.messaging.sms_message_page', 'pages.sms.sms_incoming_messages_page': 'pages.sms.messaging.sms_incoming_messages_page', 'pages.sms.sms_blocked_keywords_page': 'pages.sms.opt_out.sms_blocked_keywords_page', 'pages.sms.sms_blocked_numbers_page': 'pages.sms.opt_out.sms_blocked_numbers_page', 'pages.sms.sms_overview_page': 'pages.sms.overview.sms_overview_page', 'pages.sms.sms_campaign_report_page': 'pages.sms.reports.sms_campaign_report_page', 'pages.sms.sms_country_report_page': 'pages.sms.reports.sms_country_report_page', 'pages.sms.sms_download_center_page': 'pages.sms.reports.sms_download_center_page', 'pages.sms.sms_report_create_page': 'pages.sms.reports.sms_report_create_page', 'pages.sms.sms_error_codes_page': 'pages.sms.reports.sms_error_codes_page', 'pages.sms.sms_error_code_report_page': 'pages.sms.reports.sms_error_code_report_page', 'pages.sms.sms_latency_report_page': 'pages.sms.reports.sms_latency_report_page', 'pages.sms.sms_sender_report_page': 'pages.sms.reports.sms_sender_report_page', 'pages.sms.sms_status_report_page': 'pages.sms.reports.sms_status_report_page', 'pages.sms.sms_usage_report_page': 'pages.sms.reports.sms_usage_report_page', 'pages.sms.sms_sender_id_page': 'pages.sms.sender_id.sms_sender_id_page', 'pages.sms.sms_template_page': 'pages.sms.templates.sms_template_page', 'pages.sms.sms_template_report_page': 'pages.sms.templates.sms_template_report_page', 'pages.whatsapp.whatsapp_campaign_page': 'pages.whatsapp.campaigns.whatsapp_campaign_page', 'pages.whatsapp.whatsapp_campaign_create_page': 'pages.whatsapp.campaigns.whatsapp_campaign_create_page', 'pages.whatsapp.whatsapp_campaign_report_page': 'pages.whatsapp.campaigns.whatsapp_campaign_report_page', 'pages.whatsapp.whatsapp_download_center_page': 'pages.whatsapp.download_center.whatsapp_download_center_page', 'pages.whatsapp.whatsapp_incoming_messages_page': 'pages.whatsapp.messaging.whatsapp_incoming_messages_page', 'pages.whatsapp.whatsapp_message_report_page': 'pages.whatsapp.messaging.whatsapp_message_report_page', 'pages.whatsapp.whatsapp_blocked_users_page': 'pages.whatsapp.more.whatsapp_blocked_users_page', 'pages.whatsapp.whatsapp_flow_builder_page': 'pages.whatsapp.more.whatsapp_flow_builder_page', 'pages.whatsapp.whatsapp_flows_page': 'pages.whatsapp.more.whatsapp_flows_page', 'pages.whatsapp.whatsapp_optin_page': 'pages.whatsapp.more.whatsapp_optin_page', 'pages.whatsapp.whatsapp_optout_page': 'pages.whatsapp.more.whatsapp_optout_page', 'pages.whatsapp.whatsapp_overview_page': 'pages.whatsapp.overview.whatsapp_overview_page', 'pages.whatsapp.whatsapp_campaign_analytics_page': 'pages.whatsapp.reports.whatsapp_campaign_analytics_page', 'pages.whatsapp.whatsapp_country_code_analytics_page': 'pages.whatsapp.reports.whatsapp_country_code_analytics_page', 'pages.whatsapp.whatsapp_message_type_analytics_page': 'pages.whatsapp.reports.whatsapp_message_type_analytics_page', 'pages.whatsapp.whatsapp_report_create_page': 'pages.whatsapp.reports.whatsapp_report_create_page', 'pages.whatsapp.whatsapp_status_analytics_page': 'pages.whatsapp.reports.whatsapp_status_analytics_page', 'pages.whatsapp.whatsapp_usage_analytics_page': 'pages.whatsapp.reports.whatsapp_usage_analytics_page', 'pages.whatsapp.whatsapp_waba_number_analytics_page': 'pages.whatsapp.reports.whatsapp_waba_number_analytics_page', 'pages.whatsapp.whatsapp_sender_id_page': 'pages.whatsapp.sender_id.whatsapp_sender_id_page', 'pages.whatsapp.whatsapp_template_page': 'pages.whatsapp.templates.whatsapp_template_page', 'pages.whatsapp.whatsapp_template_create_page': 'pages.whatsapp.templates.whatsapp_template_create_page', 'pages.whatsapp.whatsapp_template_analytics_page': 'pages.whatsapp.templates.whatsapp_template_analytics_page'}


class _LegacyPagesLoader(Loader):
    def __init__(self, target_name):
        self.target_name = target_name

    def create_module(self, spec):
        mod = importlib.import_module(self.target_name)
        sys.modules[spec.name] = mod
        return mod

    def exec_module(self, module):
        pass


class _LegacyPagesFinder(MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname in LEGACY_PAGES_MAP:
            target_name = LEGACY_PAGES_MAP[fullname]
            return ModuleSpec(fullname, _LegacyPagesLoader(target_name))
        return None


if not any(isinstance(f, _LegacyPagesFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, _LegacyPagesFinder())
