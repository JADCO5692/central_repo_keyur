from odoo import models, api, _
import pytz
import dateutil
import datetime
import logging

_logger = logging.getLogger(__name__)

class DashboardBase(models.AbstractModel):
    _inherit = 'base'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(DashboardBase, self).create(vals_list)
        if self._name in ['crm.lead','sale.order']:  
            params = {
                'message': 'New Created',
                'type': 'record_create_notify',
            } 
            users = self.env['res.users'].sudo().search([])
            users._bus_send("dashboard_notify", params) 
        return res
    
 
class CustomBus(models.Model):
    _inherit = 'bus.bus'

    @api.model
    def _sendmany(self, notifications):
        for notification in notifications:
            self._sendone(*notification)