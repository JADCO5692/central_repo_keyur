from docutils.nodes import organization

from odoo import api, models, fields
from odoo.exceptions import ValidationError, MissingError
import requests
import json
from pprint import pprint
import logging

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    calendly_token = fields.Char(
        "Calendly Access Token", config_parameter='npc_calendly.calendly_token')
    calendly_webhook_uri = fields.Char(
        "Calendly Webhook URI", config_parameter='npc_calendly.calendly_webhook_uri')
    calendly_organization_uri = fields.Char(
        "Calendly Organization URI", config_parameter='npc_calendly.calendly_organization_uri')

    def subscribe_to_calendly_webhook(self):
        access_token = self.calendly_token
        message = "Failed to subscribe to Calendly Webhook"

        if not access_token:
            raise MissingError("Access token is required!")

        ir_config = self.env['ir.config_parameter'].sudo()
        webhook_uri = self.calendly_webhook_uri
        api_url = 'https://api.calendly.com'
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}

        # If webhook uri is present, unsubscribe it first
        if webhook_uri:
            result = requests.delete(url=webhook_uri, headers=headers)
            if result.status_code == 204:
                message = f"Deleted webhook uri {webhook_uri}."
                _logger.warning(message)
            else:
                message = f"Failed to delete webhook uri {webhook_uri}."
        else:
            message = ""

        # Get organization
        organization = self.retrieve_calendly_organization()

        # Subscribe webhook
        base_url = ir_config.get_param('web.base.url')
        payload = {
            "url": f"{base_url}/npc_calendly/webhook",
            "events": ["invitee.created", "invitee.canceled"],
            "organization": organization,
            "scope": "organization",
        }
        result = requests.post(url=f'{api_url}/webhook_subscriptions', headers=headers, json=payload)
        if result.status_code == 201:
            webhook_uri = result.json()['resource']['uri']
            ir_config.set_param('npc_calendly.calendly_webhook_uri', webhook_uri)
            self.calendly_webhook_uri = webhook_uri
            success_msg = f"Successfully created webhook uri {webhook_uri}"
            message += f"\n{success_msg}"
            _logger.warning(success_msg)
        else:
            raise ValidationError(f"Failed to create webhook uri with error code {result.status_code}")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': 'success',
                'sticky': False,
                # 'next': {'type': 'ir.actions.act_window_close'},  # force a form reload
            },
        }

    def retrieve_calendly_organization(self):
        access_token = self.calendly_token
        organization = self.calendly_organization_uri

        if not access_token:
            raise MissingError("Access token is required!")

        ir_config = self.env['ir.config_parameter'].sudo()
        api_url = 'https://api.calendly.com'
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}

        # Get organization
        result = requests.get(url=f'{api_url}/users/me', headers=headers)

        if result.status_code == 200:
            organization = result.json()['resource']['current_organization']
            ir_config.set_param('npc_calendly.calendly_organization_uri', organization)
            self.calendly_organization_uri = organization

            _logger.warning(f"Successfully retrieved organization uri {organization}")

        return organization
