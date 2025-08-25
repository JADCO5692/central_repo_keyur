# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, _
import requests
from odoo.exceptions import UserError
from datetime import datetime

API = "https://graph.microsoft.com/v1.0/me/"
AUTH_API = "https://login.microsoftonline.com/common/oauth2/v2.0/"
SCOPE = "Contacts.ReadWrite Tasks.ReadWrite offline_access Mail.ReadWrite Mail.Send Mail.Send.Shared"


class Authorize(models.Model):
    _name = 'sh.office365.base.config'
    _description = 'Authorize your credentials'

    name = fields.Char("Name")
    user_id = fields.Many2one('res.users', string='User', required=True, default=lambda self: self.env.user)
    client_id = fields.Char("Client ID")
    client_secret = fields.Char("Client Secret")
    redirect_url = fields.Char("Redirect Url")
    # code = fields.Char("Code")
    # access_token = fields.Char("Access Token")
    auth_token = fields.Char("Auth Token")
    refresh_token = fields.Char("Refresh Token")
    from_office365 = fields.Boolean("Imported from Office365")
    auto_schedule = fields.Boolean("Auto Schedule")
    manage_log = fields.Boolean("Manage Log History")
    sh_queue_ids = fields.One2many("sh.office.queue",'sh_current_config')
    log_historys = fields.One2many('sh.office365.base.log','base_config_id',string="Log History")
    with_mobile = fields.Boolean("Phone Number")
    with_email = fields.Boolean("Email Address")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('failed','Failed'),
        ('confirm', 'Authorized')
    ], string="state", default="draft")

    def _log(self, field_type, msg, state, operation):
        self.env['sh.office365.base.log'].create({
            "name" : self.name,
            "base_config_id" : self.id,
            "datetime" : datetime.now(),
            "field_type" : field_type,
            "error" : msg,
            "state" : state,
            "operation" : operation
        })

    def AuthorizeCreds(self):
        try:
            if self.client_id and self.redirect_url:
                return {
                    'type' : 'ir.actions.act_url',
                    'target' : '_blank',
                    'url' : f"{AUTH_API}authorize?client_id={self.client_id}&response_type=code&redirect_url={self.redirect_url}&scope={SCOPE}&response_mode=query&state={self.id}"
                }
            else:
                raise UserError("Plz enter Credentials and Try again")
        except Exception as e:
            raise UserError(e)

    def _process_token(self, payload):
        if not (self.client_id and self.client_secret and self.redirect_url):
            raise UserError("Enter credentials Frist")
        payload.update({
            "client_id" : self.client_id,
            "client_secret" : self.client_secret,
            "redirect_url" : self.redirect_url,
            "scope" : SCOPE
        })
        try:
            response = requests.post(
                url = f'{AUTH_API}token',
                data=payload)
            res_json = response.json()
            if res_json.get('access_token'):
                self.write({
                    'state': 'confirm',
                    # 'access_token': res_json['access_token'],
                    'refresh_token': res_json['refresh_token'],
                    'auth_token': f"{res_json['token_type']} {res_json['access_token']}"
                })
            else:
                self.write({'state': 'failed'})
                raise UserError(_(res_json['error_description']))
        except Exception as ex:
            raise UserError(ex)

    def generate_token(self, code):
        self._process_token({
            # "code" : self.code,
            "code" : code,
            "grant_type" : "authorization_code"
        })

    def RefreshToken(self):
        self._process_token({
            "refresh_token" : self.refresh_token,
            "grant_type" : "refresh_token"
        })

    def _headers(self):
        return {
            "Authorization": self.auth_token,
            "Content-Type": "application/json"
        }

    def _get(self, endpoint):
        '''
            returns the json_data,'' if success,
            else False, Reason of failed request
        '''
        response = requests.get(
            url = f"{API}{endpoint}",
            headers = self._headers()
        )
        if response.status_code == 200:
            return {'data': response.json()}
            # return response.json(), ''
        # return False, response.text
        return {'error': response.text}

    def _post(self, endpoint, json_dumps):
        response = requests.post(
            url = f"{API}{endpoint}",
            headers = self._headers(),
            data=json_dumps
        )
        return response.json()


class ResPartner(models.Model):
    _inherit= 'res.partner'

    contacts_imported = fields.Boolean("Imported")
    contacts_exported = fields.Boolean("Exported")
    office365_id = fields.Char("Office365 Ids")
