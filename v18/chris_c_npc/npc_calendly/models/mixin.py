from odoo import api, fields, models, exceptions
import requests
import logging
from pprint import pprint

_logger = logging.getLogger(__name__)


class MemberstackMixin(models.AbstractModel):
    _name = 'npc_calendly.mixin'
    _description = "Common functions to use Calendly API"

    ENDPOINT_BASE_URL = 'https://api.calendly.com'

    def get_data(self, endpoint, params=None):
        config_param_model = self.env['ir.config_parameter'].sudo()
        access_token = config_param_model.get_param('npc_calendly.calendly_token')
        headers = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json"
        }
        res = requests.get(
            url=self.ENDPOINT_BASE_URL + endpoint,
            headers=headers,
            params=params)

        json_res = {}

        try:
            json_res = res.json()
        except Exception as e:
            _logger.warning(e)

        return json_res
