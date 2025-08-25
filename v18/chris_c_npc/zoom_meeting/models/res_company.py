# -*- coding: utf-8 -*-
##########################################################################
# Author : Webkul Software Pvt. Ltd. (<https://webkul.com/>;)
# Copyright(c): 2017-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>;
##########################################################################
import logging
import requests
import json
from odoo.http import request
from odoo import models, fields, api, _
from odoo.exceptions import UserError
_logger=logging.getLogger(__name__)



class ResCompany(models.Model):
    _inherit = 'res.company'
    client_id = fields.Char(string="Client Id")
    secret_id = fields.Char(string="Secret Id")
    redirect_urls = fields.Char(
        string="Redirect Url", compute="_comute_callback")
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
            page.account_token_page_url = f"{request.httprequest.host_url}web#id={page.id}&action={page.env.ref('base.action_res_company_form').id}&model=res.company&view_type=form"


    def generate_access_token(self):
        if self.client_id and self.secret_id:
            authorization_redirect_url = f"https://zoom.us/oauth/authorize?client_id={self.client_id}&response_type=code&redirect_uri={self.redirect_urls}"
            return {
                'type': 'ir.actions.act_url',
                'url': authorization_redirect_url,
                'target': 'self',  # open in a same tab
            }
        else:
            raise UserError(_("Please insert details in all fields"))

    def _comute_callback(self):
        for domain_sequence in self:
            domain_sequence.redirect_urls = self.env['ir.config_parameter'].sudo().get_param('web.base.url') + \
                    "/company/zoom/"+str(self.env.company.id)+"/OAuth2"



    def button_get_code(self):
        # Define the data for the request
        data = {
            'grant_type': 'authorization_code',
            'code': self.code,
            'redirect_uri': self.redirect_urls
        }

        # Make the POST request to obtain the token
        resp = requests.post('https://zoom.us/oauth/token', data=data, auth=(self.client_id, self.secret_id))

        # Get the HTTP status code and parse the response as JSON
        status_code = resp.status_code
        resp_data = resp.json()

        if status_code == 400:
            # Handle the case where there's an error
            return resp_data.get('reason')

        if 'access_token' in resp_data and 'refresh_token' in resp_data:
            try:
                # Assign the tokens if they are present
                self.access_token = resp_data['access_token']
                self.refresh_token = resp_data['refresh_token']
                message = "Completed"
            except Exception as e:
                # Handle any exceptions that might occur during token assignment
                self.access_token = None
                self.refresh_token = None
                message = str(e)
        else:
            # Handle the case where there are no access and refresh tokens
            self.access_token = None
            self.refresh_token = None
            message = "No Data in Authentication Token, Please Check the Entered Detail and Try again"

        return message
    
    def reset_fun(self,obj):
        for rec in obj:
                rec.write({'authentication_state':'new', 'refresh_token':False, 'access_token': False})
    
    def reset_state(self):
        self.reset_fun(self)

    def refresh_fun(self,obj):
        if obj._name=="res.company":
            if self.refresh_token:
                data = {
                    'grant_type': 'refresh_token',
                    'refresh_token': self.refresh_token
                }

                # Make the POST request to refresh the token
                resp = requests.post('https://zoom.us/oauth/token', data=data, auth=(self.client_id, self.secret_id))
                resp_data = resp.json()

                if 'access_token' in resp_data:
                    # Update access and refresh tokens
                    self.sudo().write({'access_token':resp_data['access_token'],'refresh_token':resp_data.get('refresh_token', self.refresh_token),'authentication_state':'authorize_token'})
                else:
                    # Handle the case where token refresh fails
                    self.sudo().write({'access_token':False,'refresh_token':False,'authentication_state':'error'})
                    return self.env['wk.wizard.message'].genrated_message("Token has expired; please regenerate it.", name='Message')

            return False  # Or return True if you need to indicate a successful refresh
        else:
            if obj.refresh_token:
                data = {
                    'grant_type': 'refresh_token',
                    'refresh_token': obj.refresh_token
                }

                # Make the POST request to refresh the token
                resp = requests.post('https://zoom.us/oauth/token', data=data, auth=(obj.client_id, obj.secret_id))
                resp_data = resp.json()

                if 'access_token' in resp_data:
                    # Update access and refresh tokens
                    obj.sudo().write({'access_token':resp_data['access_token'],'refresh_token':resp_data.get('refresh_token', obj.refresh_token),'authentication_state':'authorize_token'})
                else:
                    # Handle the case where token refresh fails
                    obj.sudo().write({'access_token':False,'refresh_token':False,'authentication_state':'error'})
                    return self.env['wk.wizard.message'].genrated_message("Token has expired; please regenerate it.", name='Message')

            return False  # Or return True if you need to indicate a successful refresh
            

    def refresh_access_token(self):
        self.refresh_fun(self)


