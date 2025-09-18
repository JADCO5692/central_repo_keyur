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

import base64
import json
import logging
import requests
import secrets
import binascii

from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

ORDER_STATUS = [
                ('awaiting_payment', 'awaiting_payment'),
                ('awaiting_shipment', 'awaiting_shipment'),
                ('on_hold', 'on_hold'),
                ('cancelled', 'cancelled'),
                ('shipped', 'shipped'),
            ]


class ShipstationStockPicking(models.Model):
    _inherit = 'stock.picking'


    def get_all_wk_carriers(self):
        res = super(ShipstationStockPicking,self).get_all_wk_carriers()
        res.append('shipstation')
        return res

    @api.model
    def _set_default_store(self):
        return self.env['shipstation.stores'].search([], limit=1)

    shipstation_order_id = fields.Integer('ShipStation Order Id', related='sale_id.shipstation_order_id')
    shipstation_order_key = fields.Char('ShipStation Order Key', related='sale_id.shipstation_order_key')
    shipstation_order_number = fields.Char('ShipStation Order Number', related='sale_id.shipstation_order_number')
    shipstation_order_status = fields.Selection(string='ShipStation Order Status', related='sale_id.shipstation_order_status')
    shipstation_customer_id = fields.Char('ShipStation Customer ID', related='sale_id.shipstation_customer_id')
    shipstation_store_id = fields.Many2one('shipstation.stores', string="ShipStation Store ID", related='carrier_id.shipstation_store_id')
    shipstation_order_date = fields.Datetime(string='ShipStation Order Date', related='sale_id.shipstation_order_date')
    shipstation_shipped_date = fields.Datetime(string='ShipStation Shipped Date', related='sale_id.shipstation_shipped_date')

    def send_shipment_request(self,data):
        tracking_result = {}
        tracking_number = data.get('trackingNumber')
        label_data = data.get('labelData')
        tracking_result[tracking_number]= ('SHIPSTATION' + str(tracking_number) + '.pdf', binascii.a2b_base64(label_data))
        return dict(
            tracking_result=tracking_result,
            tracking_number = data.get('trackingNumber'),
            shipment_cost = data.get('shipmentCost')
        )

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

    def get_shipstation_label(self):
        try:
            path = '/orders/createlabelfororder'
            data = {}
            data['orderId'] = self.shipstation_order_id
            data['carrierCode'] = self.carrier_id.shipstation_carrier_id.carrier_code
            data['serviceCode'] = self.carrier_id.service_id.service_code
            data['confirmation'] = self.carrier_id.delivery_confirmation if self.carrier_id.delivery_confirmation else 'none'
            data['shipDate'] = self.scheduled_date.strftime("%Y-%m-%dT%H:%M:%S.%f")

            package = self.move_line_ids.result_package_id
            if len(package)>1:
                raise UserError("More than one package found!! Shipstation does not support multiple package currently.")

            data['weight'] = {
                'value' : sum(package.mapped('shipping_weight')),
                'units' : self.carrier_id.weight_unit
            }
            #data['testLabel'] = True
            data['dimensions'] = {
                'length' : package.length,
                'width' : package.width,
                'height' : package.height,
                'units' : self.carrier_id.shipstation_package_unit
            }
            request = requests.request('POST', url=self.carrier_id.shipstation_user_id.request_url+path, headers=self.carrier_id.shipstation_user_id.request_header(), data=json.dumps(data))
            json_data = request.json()
            if not (type(json_data) == type(list())):
                response_error = self.check_error_response(json_data)
                if response_error.get('error'):
                    raise UserError(response_error.get('error_message')+" "+response_error.get('message_details')+" "+response_error.get('message_exception'))
            return self.send_shipment_request(json_data)
        except Exception as e:
            raise UserError(e)

    def get_shipment_label(self):
        res = {}
        response = self.get_shipstation_label()
        tracking_result = response.get('tracking_result')
        if tracking_result:
            res['tracking_number'] = ','.join(tracking_result.keys())
            res['attachments'] = list(tracking_result.values())
        self.carrier_tracking_ref = res.get(
            'tracking_number') and res.get('tracking_number').strip(',')
        msg = _("Shipment sent to carrier %s for expedition with tracking number %s") % (
            self.carrier_id.delivery_type, self.carrier_tracking_ref)
        self.message_post(
            body=msg,
            subject="Attachments of tracking",
            attachments=res.get('attachments')
        )
