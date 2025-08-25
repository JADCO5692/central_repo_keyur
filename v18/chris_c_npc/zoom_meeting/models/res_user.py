# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2016-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
import logging,requests,json
from odoo.http import request
from odoo import models, fields, api, _
from odoo.exceptions import UserError
_logger=logging.getLogger(__name__)
class ZoomUsers(models.Model):
    _inherit = 'res.users'
    client_id = fields.Char(string="Client Id")
    secret_id = fields.Char(string="Secret Id")
    redirect_urls = fields.Char(string="Redirect Url",compute="_comute_callback")
    code = fields.Char(string="Code")
    access_token = fields.Text(string="Access Token", readonly=True)
    refresh_token = fields.Char(
        string="Refresh Token", readonly=True)
    authentication_state = fields.Selection([('new', 'New'),(
        'error', 'Error'), ('authorize_token', 'Access Token')], default='new')
    account_token_page_url = fields.Char(string="Token page url",
                                         help="After token generate redirect page", compute="_compute_token_page_url")
    def _compute_token_page_url(self):
        for page in self:
            page.account_token_page_url = request.httprequest.host_url+"web#id="+str(page.id)+"&action="+str(
                page.env.ref("base.action_res_users").id)+"&model=res.company&view_type=form"
    def generate_access_token(self):
        if self.client_id:
            authorization_redirect_url = "https://zoom.us/oauth/authorize?client_id="+self.client_id+"&response_type=code&redirect_uri="+self.redirect_urls
            return {
                'type': 'ir.actions.act_url',
                'url': authorization_redirect_url,
                'target': 'self',  # open in a new tab
            }
        else:
            raise UserError(_("Please insert details in all fields"))

    def _comute_callback(self):
        for domain_sequence in self:
            domain_sequence.redirect_urls = self.env['ir.config_parameter'].sudo().get_param('web.base.url') + \
                    "/zoom/"+str(self.id)+"/OAuth2"

    def button_get_code(self):
        data = {'grant_type': 'authorization_code',
                'code': self.code, 'redirect_uri': self.redirect_urls}
        resp = requests.post('https://zoom.us/oauth/token', data=data,auth=(self.client_id, self.secret_id))
        status_code = resp.status_code
        resp = json.loads(resp.text)
        if status_code == 400:
            return resp.get('reason')
        if resp.get('access_token') and resp.get('refresh_token'):
            try:
                self.access_token = resp.get('access_token')
                self.refresh_token = resp.get('refresh_token')
                message = "Completed"
            except:
                self.access_token = None
                self.refresh_token = None
                message = str(resp.get('error'))
        else:
            self.access_token = None
            self.refresh_token = None
            message = "No Data in Authentication Token, Please Check the Entered Detail and Try again"
        return message

    def reset_state(self):
        self.company_id.reset_fun(self)

    def refresh_access_token(self):
        self.company_id.refresh_fun(self)