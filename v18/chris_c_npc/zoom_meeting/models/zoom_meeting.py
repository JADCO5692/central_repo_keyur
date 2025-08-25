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
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging,requests,json
_logger=logging.getLogger(__name__)
class ZoomMeeting(models.Model):
    _inherit = 'calendar.event'
    zoom_description=fields.Html("Zoom meeting Description")
    meeting_id=fields.Char("Meeting Id")
    password=fields.Char("Password")
    start_meeting_url=fields.Char("Start meeting Url")
    alternative_hosts = fields.Text(string = "Alternative Hosts")
    

    def start_zoom_meeting(self):
        if self.start_meeting_url:
            return {
                'type': 'ir.actions.act_url',
                'url': self.start_meeting_url,
                'target': '_new',  # open in a new tab
            }

    def generate_meeting_link(self):
        return {
            "name": "Create Zoom Meeting",
            "type": "ir.actions.act_window",
            "res_model": "wizard.zoom",
            "view_id": self.env.ref("zoom_meeting.zoom_meeting_form").id,
            "view_mode": "form",
            "target": "new",
        }

    def update_meeting(self):
        return {
            "name": "Update Zoom Meeting",
            "type": "ir.actions.act_window",
            "res_model": "wizard.zoom",
            "view_id": self.env.ref("zoom_meeting.zoom_meeting_update_form").id,
            "view_mode": "form",
            "target": "new",
        }

    def delete_meeting(self):
        return {
            "name": "Delete Zoom Meeting",
            "type": "ir.actions.act_window",
            "res_model": "wizard.zoom",
            "view_id": self.env.ref("zoom_meeting.zoom_meeting_delete_form").id,
            "view_mode": "form",
            "target": "new",
        }
    
   