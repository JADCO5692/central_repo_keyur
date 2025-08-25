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
from email import message
import werkzeug
from odoo import http
import logging
_logger = logging.getLogger(__name__)


class ZoomAuth(http.Controller):
    @http.route('/zoom/<int:sequence_no>/OAuth2', type="http", auth="public", csrf=False, website=True)
    def oauth2_verify_user(self, sequence_no, **kw):
        message=''
        oauth2_account_record = http.request.env['res.users'].sudo().search([('id', '=', sequence_no)], limit=1)
        try:
            if (kw.get("code")):
                oauth2_account_record.write(
                    {'code': kw.get("code")})
                message=oauth2_account_record.button_get_code()
                if(message == 'Completed'):
                    oauth2_account_record.authentication_state = 'authorize_token'
                    return http.request.redirect(oauth2_account_record.account_token_page_url)
                elif(message == 'Invalid authorization code'):
                    return http.request.render('zoom_meeting.error_view_1', {'message': message})
                else:
                    oauth2_account_record.authentication_state = 'error'
                    return http.request.render('zoom_meeting.error_view_1', {'message': message})
        except:
            oauth2_account_record.authentication_state = 'error'
            return http.request.render('zoom_meeting.error_view_1', {'message': "Something went Wrong, Please Try Again"})
        
    @http.route('/company/zoom/<int:sequence_no>/OAuth2', type="http", auth="public", csrf=False, website=True)
    def oauth2_verify_company(self, sequence_no, **kw):
        message=''
        oauth2_account_record = http.request.env['res.company'].sudo().browse(sequence_no)
        try:
            if (kw.get("code")):
                oauth2_account_record.write(
                    {'code': kw.get("code")})
                message=oauth2_account_record.button_get_code()
                if(message == 'Completed'):
                    oauth2_account_record.authentication_state = 'authorize_token'
                    return http.request.redirect(oauth2_account_record.account_token_page_url)
                elif(message == 'Invalid authorization code'):
                    return http.request.render('zoom_meeting.error_view_1', {'message': message})
                else:
                    oauth2_account_record.authentication_state = 'error'
                    return http.request.render('zoom_meeting.error_view_1', {'message': message})
        except:
            oauth2_account_record.authentication_state = 'error'
            return http.request.render('zoom_meeting.error_view_1', {'message': "Something went Wrong, Please Try Again"})
            
