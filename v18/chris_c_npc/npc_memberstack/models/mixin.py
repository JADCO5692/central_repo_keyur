from odoo import api, fields, models, exceptions
import requests
from pprint import pprint


class MemberstackMixin(models.AbstractModel):
    _name = 'npc_memberstack.mixin'
    _description = "Common functions to use Memberstack API"

    ENDPOINT_BASE_URL = 'https://admin.memberstack.com'

    def get_data(self, endpoint, params=None):
        config_param_model = self.env['ir.config_parameter'].sudo()
        secret_key = config_param_model.get_param('npc_memberstack.secret_key')
        headers = {
            'X-API-KEY': secret_key
        }
        res = requests.get(
            url=self.ENDPOINT_BASE_URL + endpoint,
            headers=headers,
            params=params)

        return res.json()
