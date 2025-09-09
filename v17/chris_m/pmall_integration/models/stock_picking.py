# -*- coding: utf-8 -*-

from odoo import api, models, _
from datetime import date
import requests

class Picking(models.Model):
    _inherit = "stock.picking" 

    @api.onchange('carrier_tracking_ref','state')
    def _create_pmall_invoice(self):
        pm_config = self.env['pmall.config'].sudo().search([],limit=1)
        if self.carrier_tracking_ref and self.state == 'done' and self.sale_id and pm_config:
            pmall = pm_config.pmall_dropship_api_url
            url = pmall + "/api/v1/Invoice/CreateInvoice" 
            headers = {
                "Authorization": f"Bearer {pm_config.client_access_token}",  
                "Content-Type": "application/json"
            }
            sale_order = self.sale_id
            today_date = date.today()
            today_date = today_date.strftime("%Y-%m-%dT00:00:00")
            payload = { 
                "invoice": {
                    "invoiceNumber": sale_order.invoice_ids[0].name if sale_order.invoice_ids else '', 
                    "InvoiceDate": sale_order.invoice_ids[0].invoice_date.strftime("%Y-%m-%dT00:00:00") if sale_order.invoice_ids else '',
                    "orders":[
                        {
                            "orderNumber": sale_order.name,
                            "shipments": [
                            {
                                "orderItemIds": [],
                                "carrier": self.get_delivery_type(),
                                "shipMethod": self.carrier_id.name, 
                                "trackingNumber": self.carrier_tracking_ref,
                                "shipDate": today_date,
                            }], 
                        }
                    ]  
                }
            }
            response = requests.post(url, headers=headers, json=payload) 
            print(response.json())

    def get_delivery_type(self):
        carrier = ''
        if self.carrier_id.delivery_type:
            dtype = self.carrier_id.delivery_type
            if dtype == 'base_on_rule':
                carrier = 'Based on Rules'
            elif dtype == 'fixed':
                carrier = 'Fixed Price'
            elif dtype == 'fedex':
                carrier = 'FedEx (Legacy)'
            elif dtype == 'fedex_rest':
                carrier = 'FedEx'
            elif dtype == 'ups_rest':
                carrier = 'UPS'
            elif dtype == 'usps':
                carrier = 'USPS (Legacy)'
            elif dtype == 'onsite':
                carrier = 'Pickup in store'
            elif dtype == 'shipstation_ept':
                carrier = 'Shipstation'
        return carrier