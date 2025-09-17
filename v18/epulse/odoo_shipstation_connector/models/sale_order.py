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
from odoo.http import request

import base64
import json
import logging
import requests
import secrets
from odoo import api, fields, models, _, SUPERUSER_ID

from datetime import datetime
from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

ORDER_STATUS = [
                ('awaiting_payment', 'awaiting_payment'),
                ('awaiting_shipment', 'awaiting_shipment'),
                ('on_hold', 'on_hold'),
                ('cancelled', 'cancelled'),
                ('shipped', 'shipped'),
            ]


class ShipStationSaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _set_default_store(self):
        return self.env['shipstation.stores'].search([], limit=1)

    shipstation_order_id = fields.Integer('ShipStation Order Id')
    shipstation_order_key = fields.Char('ShipStation Order Key')
    shipstation_order_number = fields.Char('ShipStation Order Number')
    shipstation_order_status = fields.Selection(selection=ORDER_STATUS, string='ShipStation Order Status', default='awaiting_shipment')
    shipstation_customer_id = fields.Char('ShipStation Customer ID')
    shipstation_store_id = fields.Many2one('shipstation.stores', string="ShipStation Store ID", default=_set_default_store, ondelete='cascade')
    shipstation_order_date = fields.Datetime(string='ShipStation Order Date')
    shipstation_shipped_date = fields.Datetime(string='ShipStation Shipped Date')
    ssca = fields.Selection(related='carrier_id.delivery_type', string='SSCA')
    shipstation_user_id = fields.Many2one('shipstation.configuration', string="Shipstation User")
    webhook_logs = fields.One2many('webhooks.event.logs', 'shipstation_order_id', string="Webhook Logs")
    has_webhook_logs = fields.Boolean(string="Has webhook logs", compute="_check_for_webhooks")

    shipstation_delivery_amount = fields.Monetary(
        string="Amount Delivery",
        compute='_compute_shipstation_delivery_amount',
        help="Tax included or excluded depending on the website configuration.",
    )


    @api.depends('order_line.price_total', 'order_line.price_subtotal')
    def _compute_shipstation_delivery_amount(self):
        self.shipstation_delivery_amount = 0.0
        for order in self:
            delivery_lines = order.order_line.filtered('is_delivery')
            order.shipstation_delivery_amount = sum(delivery_lines.mapped('price_subtotal')) if not order.amount_delivery else order.amount_delivery
    
    @api.depends('webhook_logs')
    def _check_for_webhooks(self):
        for rec in self:
            rec.has_webhook_logs = bool(rec.webhook_logs)


    def check_error_response(self, json_data):
        data = {}
        data['error'] = False
        data['error_message'] = ""
        data['message_details'] = ""
        if json_data.get('Message'):
            data['error'] = True
            data['error_message'] = json_data.get('Message', '')
            data['message_details'] = json_data.get('MessageDetail', '')
            data['message_exception'] = json_data.get('ExceptionMessage', '')
        return data

    def generate_order_key(self):
        token = secrets.token_urlsafe()
        return token

    def add_sale_order_reponse_data(self, data):
        self.shipstation_order_number = data.get("orderNumber")
        self.shipstation_order_key = data.get("orderKey")
        self.shipstation_order_status = data.get("orderStatus")
        self.shipstation_order_id = data.get("orderId")
        self.shipstation_order_date = datetime.strptime(data.get('orderDate').split('.')[0], "%Y-%m-%dT%H:%M:%S")
        self.shipstation_shipped_date = data.get('shipByDate') and datetime.strptime(data.get('shipByDate').split('.')[0], "%Y-%m-%dT%H:%M:%S")
        self.shipstation_customer_id = data.get("customerId")
        self.shipstation_store_id = self.env['shipstation.stores'].search([('store_id', '=', data.get('advancedOptions').get('storeId'))]).id
        self.shipstation_user_id = self.carrier_id.shipstation_user_id
        
        if data.get("customerId"):
            self.partner_id.shipstation_customer_id = data.get("customerId")
            self.partner_id.is_shipstation_customer = True

        # for item in data.get('items'):
        #     product = self.env['product.product'].search([('id', '=', item.get('lineItemKey'))])
        #     if product.shipstation_product_id == -1:
        #         if item.get('orderItemId'):
        #             product.shipstation_product_id =  int(item.get('orderItemId'))
        #             product.is_shipstation_product = True

    def upload_order_data(self):
        try:
            path = '/orders/createorder'
            shipper_info = self.carrier_id.get_shipment_shipper_address(self)
            recipient_info  = self.carrier_id.get_shipment_recipient_address(self)
            data = {}
            data['orderNumber'] = self.name
            data['orderKey'] = self.shipstation_order_key or self.generate_order_key()
            data['orderDate'] = self.date_order.strftime("%Y-%m-%dT%H:%M:%S.%f")
            data['orderStatus'] = self.shipstation_order_status or 'awaiting_shipment'
            data['customerId'] = self.partner_id.shipstation_customer_id
            data['customerUsername'] = self.partner_id.email or ""
            data['customerEmail'] = self.partner_id.email or ""
            data['billTo'] =  {
                'name' : shipper_info.get('name'),
                'street1' : shipper_info.get('street'),
                'street2' : shipper_info.get('street2') if shipper_info.get('street2') else '',
                'city' : shipper_info.get('city'),
                'state' : shipper_info.get('state_code'),
                'postalCode' : shipper_info.get('zip'),
                'country' : shipper_info.get('country_code'),
                'phone' : shipper_info.get('phone'),
            }
            data['shipTo'] = {
                'name' : recipient_info.get('name'),
                'street1' : recipient_info.get('street'),
                'street2' : recipient_info.get('street2') if recipient_info.get('street2') else '',
                'city' : recipient_info.get('city'),
                'state' : recipient_info.get('state_code'),
                'postalCode' : recipient_info.get('zip'),
                'country' : recipient_info.get('country_code'),
                'phone' : recipient_info.get('phone'),   
            }
            items = []
            total_weight = 0
            for line in self.order_line:
                if line.product_id.type != "service" and not line.is_delivery:
                    total_weight += line.product_id.weight * line.product_uom_qty
                    itm_sku = line.product_id.default_code
                    if not itm_sku:
                        raise UserError("Please enter item SKU for shipstation order")
                    itm_data = {
                        'lineItemKey' : line.product_id.id,
                        'sku' : itm_sku,
                        'name' : line.product_id.name,
                        'weight' : {
                            'value' : line.product_id.weight,
                            'units' : self.carrier_id.weight_unit,
                        },
                        'quantity' : int(line.product_uom_qty),
                        'unitPrice' : line.price_subtotal/line.product_uom_qty,
                        'taxAmount' : line.price_tax/line.product_uom_qty
                    }
                    items.append(itm_data)
            data['items'] = items
            data['amountPaid'] = self.amount_total
            data['taxAmount'] = self.amount_tax
            data['shippingAmount'] = self.shipstation_delivery_amount
            data['carrierCode'] = self.carrier_id.shipstation_carrier_id.carrier_code
            data['serviceCode'] = self.carrier_id.service_id.service_code
            data['packageCode'] = self.carrier_id.package_id.package_code
            data['weight'] = {
                    'value' : total_weight,
                    'units' : self.carrier_id.weight_unit
                }
            if self.carrier_id.shipstation_store_id:
                data['advancedOptions'] = {
                    'storeId' : self.carrier_id.shipstation_store_id.store_id
                }
            request = requests.request('POST', url=self.carrier_id.shipstation_user_id.request_url+path, headers=self.carrier_id.shipstation_user_id.request_header(), data=json.dumps(data))
            json_data =  request.json()
            response_error = self.check_error_response(json_data)
            if response_error.get('error'):
                raise UserError(response_error.get('error_message')+" "+response_error.get('message_details')+" "+response_error.get('message_exception'))
            self.add_sale_order_reponse_data(json_data)
            # self.carrier_id.shipstation_user_id.get_shipstation_data()
        except Exception as e:
            raise UserError(e)

    def create_shipstation_order(self):
        REQ_COUNT = 2
        for i in range(REQ_COUNT):
            self.upload_order_data()

    def action_confirm(self):
        if self.carrier_id.delivery_type == "shipstation":
            self.create_shipstation_order()
        return super(ShipStationSaleOrder, self).action_confirm()
    
