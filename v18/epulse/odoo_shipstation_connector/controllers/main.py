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

from odoo import http
from odoo.http import request
import logging
import json
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)


class ShipstationControllers(http.Controller):

    @http.route(['/shipstation/webhook/event_FULFILLMENT_SHIPPED'], type='json', auth="public", methods=['GET','POST'], csrf=False)
    def shipstation_webhooks(self,*args,**kw):
        webhook_payload = json.loads(request.httprequest.data)
        webhook_id = request.env['shipstation.webhooks'].sudo().search([('event', '=', webhook_payload.get('resource_type'))])
        json_response = webhook_id.get_webhook_response(webhook_payload.get('resource_url'))
        for record in json_response.get('fulfillments'):
            order = request.env['sale.order'].sudo().search([('name', '=', record.get('orderNumber'))])
            vals = {
                'webhook_id' : webhook_id.id,
                'json_response' : json_response,
                'fulfillment_id': record.get('fulfillmentId'),
                'tracking_number': record.get('trackingNumber'),
                'create_date': record.get('createDate'),
                'ship_date': record.get('shipDate'),
                'delivery_date': record.get('deliveryDate'),
                'carrier_code': record.get('carrierCode'),
                'fulfillment_provider_code': record.get('fulfillmentProviderCode'),
            }
            if not order:
                vals.update({
                    'shipstation_order_id' : False,
                    'state' : 'error',
                    'error_desc' : f'No order Found with order number : {record.get("orderNumber")}'
                })
            elif len(order)>1:
                vals.update({
                    'shipstation_order_id' : False,
                    'state' : 'error',
                    'error_desc' : f'More than one order Found with same order number : {record.get("orderNumber")}'
                })
            else:
                vals.update({
                    'shipstation_order_id' : order.id,
                    'state' : 'draft',
                })
            logs = request.env['webhooks.event.logs'].sudo().create(vals)
            _logger.info(f"========logs = {logs}========")
        return True
    
            
         
        




