from odoo import api, fields, models, exceptions
import requests
from pprint import pprint


class SharetribeMixin(models.AbstractModel):
    _name = 'npc_sharetribe.mixin'
    _description = "Common functions to use Sharetribe API"

    ENDPOINT_BASE_URL = 'https://flex-api.sharetribe.com'

    def get_data(self, endpoint, params=None):
        access_token = self.authenticate()

        if access_token:
            headers = {'Authorization': 'bearer ' + access_token, 'Accept': 'application/json'}
            res = requests.get(
                url=self.ENDPOINT_BASE_URL + endpoint,
                headers=headers,
                params=params)

            return res.json()

        return {}

    def authenticate(self):
        config_param_model = self.env['ir.config_parameter'].sudo()
        client_id = config_param_model.get_param('npc_sharetribe.client_id')
        client_secret = config_param_model.get_param('npc_sharetribe.client_secret')
        access_token = False

        if not client_id or not client_secret:
            raise exceptions.MissingError("Please configure Sharetribe credentials first in General Settings")

        headers = {
            'Content-Type': "application/x-www-form-urlencoded; charset=utf-8",
            'Accept': 'application/json',
        }
        data = {
            'client_id': client_id,
            'grant_type': 'client_credentials',
            'client_secret': client_secret,
            'scope': 'integ',
        }

        res = requests.post(url=self.ENDPOINT_BASE_URL + '/v1/auth/token', data=data, headers=headers)

        if res.status_code == 200:
            access_token = res.json()['access_token']

        return access_token