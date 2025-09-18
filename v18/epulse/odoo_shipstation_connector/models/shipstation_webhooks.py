# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
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

import logging
import requests
import json
import ast
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError, AccessError

_logger = logging.getLogger(__name__)


EVENTS = [
    # ('ORDER_NOTIFY', 'ORDER_NOTIFY'),
    # ('ITEM_ORDER_NOTIFY', 'ITEM_ORDER_NOTIFY'),
    # ('SHIP_NOTIFY', 'SHIP_NOTIFY'),
    # ('ITEM_SHIP_NOTIFY', 'ITEM_SHIP_NOTIFY'),
    ('FULFILLMENT_SHIPPED', 'FULFILLMENT_SHIPPED'),
    # ('FULFILLMENT_REJECTED', 'FULFILLMENT_REJECTED'),
    ]

STATE = [
    ('draft', 'Draft'),
    ('done', 'Done'),
    ('error', 'Error'),
    ('cancel', 'Cancel'),
    ]


class ShipstationWebhooks(models.Model):
    _name = 'shipstation.webhooks'
    _description = "Shipstation Webhooks"
    
    name = fields.Char(string='Name')
    shipstation_store_id = fields.Many2one('shipstation.stores', string="ShipStation Store ID")
    event = fields.Selection(selection = EVENTS, string='Events', required=True)
    target_url = fields.Char(compute="_get_webhook_target_url", string='Webhook Target URL')
    shipstation_user_id = fields.Many2one('shipstation.configuration', string='ShipStation User')
    webhook_id = fields.Char(string="Webhook ID", readonly=True)


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('event', False) and vals.get('event', False) in self.search([]).mapped('event'):
                raise UserError("Another entry with the same event already exists!!")
        res = super().create(vals)
        return res
    
    def write(self, vals):
        _logger.info(vals)
        if vals.get('event', False) and vals.get('event', False) in self.search([]).mapped('event'):
            raise UserError("Another entry with the same event already exists!!")
        
        res = super().write(vals)
        return res
    
    def unlink(self):
        for record in self:
            if record.webhook_id:
                raise UserError("Deleting subscribed webhooks isn't possible directly. To remove a webhook, you must first unsubscribe from it!!")
        res = super().unlink()
        return res

    @api.depends('event')
    def _get_webhook_target_url(self):
        for rec in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            rec.target_url = f"{base_url}/shipstation/webhook/event_{rec.event or ''}"
    
    def subscribe_webhook(self):
        try:
            path = '/webhooks/subscribe'
            payload = {}
            payload['target_url'] = self.target_url
            payload['event'] = self.event
            payload['store_id'] = self.shipstation_store_id.store_id if self.shipstation_store_id else None
            payload['friendly_name'] = self.name
            request = requests.post(url=self.shipstation_user_id.request_url+path, headers=self.shipstation_user_id.request_header(), data=json.dumps(payload))
            json_data = request.json()
            if not (type(json_data) == type(list())):
                response_error = self.shipstation_user_id.check_error_response(json_data)
                if response_error.get('error'):
                    raise UserError(response_error.get('error_message')+" "+response_error.get('message_details')+" "+response_error.get('message_exception'))
            self.webhook_id = json_data.get('id')

        except Exception as e:
            raise UserError(e)
        
    def unsubscribe_webhook(self):
        try:
            path = '/webhooks/'
            request = requests.delete(url=self.shipstation_user_id.request_url+path+self.webhook_id, headers=self.shipstation_user_id.request_header())
            if request.status_code in [200]:
                self.webhook_id = False
        except Exception as e:
            raise UserError(e)
        
    def get_webhook_response(self, resource_url):
        try:
            _logger.info("=============resource_url============== %s", resource_url)
            request = requests.get(url=resource_url, headers=self.shipstation_user_id.request_header())
            json_data = request.json()
            if request.status_code not in [200] :
                response_error = self.shipstation_user_id.check_error_response(json_data)
                if response_error.get('error'):
                    raise UserError(response_error.get('error_message')+" "+response_error.get('message_details')+" "+response_error.get('message_exception'))
            else:
                return json_data
        except Exception as e:
            raise UserError(e)
        

class ShipstationWebhookLogs(models.Model):
    _name = 'webhooks.event.logs'
    _description = "Shipstation Webhooks Event Logs"


    webhook_id = fields.Many2one('shipstation.webhooks', string="Webhook ID")
    shipstation_order_id = fields.Many2one('sale.order', string="Shipstation Order")
    json_response = fields.Text(string="Json Response")
    state = fields.Selection(selection = STATE, string='State')
    error_desc = fields.Char(string="Error Description")

    fulfillment_id = fields.Char(string = "Fulfillment ID")
    tracking_number = fields.Char(string = "Tracking Number")
    create_date = fields.Char(string = "Create Date")
    ship_date = fields.Char(string = "Ship Date")
    delivery_date = fields.Char(string = "Delivery Date")
    carrier_code = fields.Char(string = "Carrier Code")
    fulfillment_provider_code = fields.Char(string = "Fulfillment Provider Code")


    

