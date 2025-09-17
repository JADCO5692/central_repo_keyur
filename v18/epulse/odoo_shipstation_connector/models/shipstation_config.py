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

from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ShipStationConfig(models.Model):
    _name = 'shipstation.configuration'
    _description = 'ShipStation Configuration'

    name = fields.Char(string='Name')
    shipstation_apikey = fields.Char(string='ShipStation API Key', required=True)
    shipstation_secret = fields.Char(string='ShipStation Secret', required=True)
    request_url = fields.Char(string='ShipStation Request URL', required=True, default='https://ssapi.shipstation.com')

    shipstation_store_count = fields.Integer(compute="_get_shipstation_store_count")
    shipstation_carrier_count = fields.Integer(compute="_get_shipstation_carrier_count")
    shipstation_service_count = fields.Integer(compute="_get_shipstation_service_count")
    shipstation_package_count = fields.Integer(compute="_get_shipstation_package_count")
    shipstation_marketplace_count = fields.Integer(compute="_get_shipstation_marketplace_count")
    shipstation_order_count = fields.Integer(compute="_get_shipstation_order_count")
    shipstation_customer_count = fields.Integer(compute="_get_shipstation_customer_count")
    shipstation_product_count = fields.Integer(compute="_get_shipstation_product_count")

    shipstation_webhooks = fields.One2many('shipstation.webhooks', 'shipstation_user_id', string="Shipstation Webhooks",)
    has_shipstation_webhooks = fields.Boolean(string="Has webhooks", compute="_check_shipstation_webhooks")


    @api.depends('shipstation_webhooks')
    def _check_shipstation_webhooks(self):
        for rec in self:
            rec.has_shipstation_webhooks = bool(rec.shipstation_webhooks)


    def _get_shipstation_store_count(self):
        for record in self:
            stores = len(record.env['shipstation.stores'].sudo().search([('shipstation_user_id', '=', self.id)]))
            record.shipstation_store_count = stores

    def _get_shipstation_carrier_count(self):
        for record in self:
            carriers = len(record.env['shipstation.carriers'].sudo().search([('shipstation_user_id', '=', self.id)]))
            record.shipstation_carrier_count = carriers

    def _get_shipstation_package_count(self):
        for record in self:
            packages = len(record.env['shipstation.packages'].sudo().search([('shipstation_user_id', '=', self.id)]))
            record.shipstation_package_count = packages

    def _get_shipstation_marketplace_count(self):
        for record in self:
            marketplace = len(record.env['shipstation.marketplaces'].sudo().search([('shipstation_user_id', '=', self.id)]))
            record.shipstation_marketplace_count = marketplace

    def _get_shipstation_service_count(self):
        for record in self:
            services = len(record.env['shipstation.services'].sudo().search([('shipstation_user_id', '=', self.id)]))
            record.shipstation_service_count = services

    def _get_shipstation_order_count(self):
        for record in self:
            orders = len(record.env['sale.order'].sudo().search([('shipstation_user_id', '=', self.id)]))
            record.shipstation_order_count = orders

    def _get_shipstation_customer_count(self):
        for record in self:
            customers = len(record.env['res.partner'].sudo().search([('shipstation_user_id', '=', self.id)]))
            record.shipstation_customer_count = customers

    def _get_shipstation_product_count(self):
        for record in self:
            products = len(record.env['product.product'].sudo().search([('shipstation_user_id', '=', self.id)]))
            record.shipstation_product_count = products

    def request_header(self):
        shipstation_apikey = self.shipstation_apikey
        shipstation_secret  = self.shipstation_secret
        shipstation_creds = '{}:{}'.format(shipstation_apikey, shipstation_secret)
        headers = {
                    'Authorization': 'Basic {}'.format(base64.b64encode(shipstation_creds.encode('utf-8')).decode('utf-8')),
                    'Content-Type': 'application/json'
                }
        return headers

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

    def get_shipstation_marketplaces(self):
        try:
            path = '/stores/marketplaces'
            request = requests.get(url=self.request_url+path, headers=self.request_header())
            json_data = request.json()
            if not (type(json_data) == type(list())):
                response_error = self.check_error_response(json_data)
                if response_error.get('error'):
                    raise UserError(response_error.get('error_message')+" "+response_error.get('message_details')+" "+response_error.get('message_exception'))
            for mp in json_data:
                marketplace_exists = self.env['shipstation.marketplaces'].sudo().search([('marketplace_id','=', mp.get('marketplaceId'))])
                if marketplace_exists:
                    continue
                data = {}
                data['name'] = mp.get('name')
                data['marketplace_id'] = mp.get('marketplaceId')
                data['shipstation_user_id'] = self.id
                self.env['shipstation.marketplaces'].sudo().create(data)
        except Exception as e:
            raise UserError(e)

    def get_shipstation_stores(self):
        try:
            path = '/stores'
            request = requests.get(url=self.request_url+path, headers=self.request_header())
            json_data = request.json()
            if not (type(json_data) == type(list())):
                response_error = self.check_error_response(json_data)
                if response_error.get('error'):
                    raise UserError(response_error.get('error_message')+" "+response_error.get('message_details')+" "+response_error.get('message_exception'))
            for store in json_data:
                store_exists = self.env['shipstation.stores'].sudo().search([('store_id','=', store.get('storeId'))])
                if store_exists:
                    continue
                data = {}
                data['store_id'] = store.get('storeId')
                data['name'] = store.get('storeName')
                data['marketplace_name'] = store.get('marketplaceName')
                marketplace_id = self.env['shipstation.marketplaces'].sudo().search([('marketplace_id','=', store.get('marketplaceId'))]).id
                data['marketplace_id'] = marketplace_id
                data['shipstation_user_id'] = self.id
                self.env['shipstation.stores'].sudo().create(data)
        except Exception as e:
            raise UserError(e)

    def get_shipstation_carriers(self):
        try:
            path = '/carriers'
            request = requests.get(url=self.request_url+path, headers=self.request_header())
            json_data = request.json()
            if not (type(json_data) == type(list())):
                response_error = self.check_error_response(json_data)
                if response_error.get('error'):
                    raise UserError(response_error.get('error_message')+" "+response_error.get('message_details')+" "+response_error.get('message_exception'))
            for carrier in json_data:
                carrier_exists = self.env['shipstation.carriers'].sudo().search([('carrier_code','=', carrier.get('code'))])
                if carrier_exists:
                    continue
                data = {}
                data['name'] = carrier.get('name')
                data['shipstation_user_id'] = self.id
                data['carrier_code'] = carrier.get('code')
                data['carrier_account_number'] = carrier.get('accountNumber')
                data['carrier_balance'] = carrier.get('balance')
                data['shipping_provide_id'] = carrier.get('shippingProviderId')
                data['is_primary'] = carrier.get('primary')
                data['requires_funded_account'] = carrier.get('requiresFundedAccount')
                self.env['shipstation.carriers'].sudo().create(data)
        except Exception as e:
            raise UserError(e)

    def get_shipstation_carrier_services(self):
        try:
            carriers = self.env['shipstation.carriers'].sudo().search([('shipstation_user_id', '=', self.id)])
            for carrier in carriers:
                path = '/carriers/listservices?carrierCode={}'.format(carrier.carrier_code)
                request = requests.get(url=self.request_url+path, headers=self.request_header())
                json_data = request.json()
                if not (type(json_data) == type(list())):
                    response_error = self.check_error_response(json_data)
                    if response_error.get('error'):
                        raise UserError(response_error.get('error_message')+" "+response_error.get('message_details')+" "+response_error.get('message_exception'))
                for service in json_data:
                    service_exists = self.env['shipstation.services'].sudo().search([('service_code','=', service.get('code'))])
                    if service_exists:
                        continue
                    data = {}
                    data['name'] = service.get('name')
                    data['carrier_code'] = carrier.id
                    data['service_code'] = service.get('code')
                    data['is_domestic'] = service.get('domestic')
                    data['is_international'] = service.get('international')
                    data['shipstation_user_id'] = self.id
                    self.env['shipstation.services'].sudo().create(data)
        except Exception as e:
            raise UserError(e)

    def get_shipstation_carrier_packages(self):
        try:
            carriers = self.env['shipstation.carriers'].sudo().search([('shipstation_user_id', '=', self.id)])
            for carrier in carriers:
                path = '/carriers/listpackages?carrierCode={}'.format(carrier.carrier_code)
                request = requests.get(url=self.request_url+path, headers=self.request_header())
                json_data = request.json()
                if not (type(json_data) == type(list())):
                    response_error = self.check_error_response(json_data)
                    if response_error.get('error'):
                        raise UserError(response_error.get('error_message')+" "+response_error.get('message_details')+" "+response_error.get('message_exception'))
                for package in json_data:
                    package_exists = self.env['shipstation.packages'].sudo().search([('package_code','=', package.get('code'))])
                    if package_exists:
                        continue
                    data = {}
                    data['name'] = package.get('name')
                    data['carrier_code'] = carrier.id
                    data['package_code'] = package.get('code')
                    data['is_domestic'] = package.get('domestic')
                    data['is_international'] = package.get('international')
                    data['shipstation_user_id'] = self.id
                    self.env['shipstation.packages'].sudo().create(data)
        except Exception as e:
            raise UserError(e)

    def get_shipstation_orders(self):
        response = {
            "total_records": 0,
            "success_records":[],
            "failed_records":[],
            }
        shipstation_carrier_exists = self.env['delivery.carrier'].search([('delivery_type', '=', 'shipstation')])
        if not len(shipstation_carrier_exists):
            raise UserError("Please create shipstation Shipping carrier first")
        path = '/orders'
        request = requests.get(url=self.request_url+path, headers=self.request_header())
        json_data = request.json()
        response_error = self.check_error_response(json_data)
        if response_error.get('error'):
            raise UserError(response_error.get('error_message')+" "+response_error.get('message_details')+" "+response_error.get('message_exception'))
        response['total_records'] = len(json_data.get('orders'))
        try:
            # self.get_shipstation_products()
            # self.get_shipstation_customers()
            for order in json_data.get('orders'):
                partner_exists = self.env['res.partner'].search([('shipstation_customer_id','=', order.get('customerId'))])
                if not partner_exists:
                    response['failed_records'].append({
                        "ShipstationOrderNumber":order.get('orderNumber'),
                        "customerId":order.get('customerId'),
                        "error":f"Customer not found given CustomerID : {order.get('customerId')}, you need to import customer first !!!"
                    })
                    continue
                elif len(partner_exists)>1:
                    response['failed_records'].append({
                        "ShipstationOrderNumber":order.get('orderNumber'),
                        "customerId":order.get('customerId'),
                        "error":f"More than 1 Customer found with same CustomerID : {order.get('customerId')}, FIx it !!!"
                    })
                    continue
                data = {}
                data['shipstation_order_number'] = order.get('orderNumber')
                data['shipstation_order_key'] = order.get('orderKey')
                data['shipstation_order_status'] = order.get('orderStatus')
                data['shipstation_order_id'] = order.get('orderId')
                data['shipstation_order_date'] = datetime.strptime(order.get('orderDate').split('.')[0], "%Y-%m-%dT%H:%M:%S")
                data['shipstation_shipped_date'] = order.get('shipByDate') and datetime.strptime(order.get('shipByDate').split('.')[0], "%Y-%m-%dT%H:%M:%S")
                data['shipstation_customer_id'] = order.get('customerId')
                shipstatsion_store = self.env['shipstation.stores'].search([('store_id', '=', order.get('advancedOptions').get('storeId'))])
                if shipstatsion_store:
                    data['shipstation_store_id'] = shipstatsion_store.id
                # if not data['shipstation_store_id']:
                #     raise UserError("Please create Shipstation Stores First!")
                data['partner_id'] = partner_exists.id
                data['shipstation_user_id'] = self.id
                order_exists = self.env['sale.order'].sudo().search([('name', '=' ,order.get('orderNumber'))])
                if len(order_exists)>1:
                    response['failed_records'].append({
                        "ShipstationOrderNumber":order.get('orderNumber'),
                        "error": f"More than 1 Order found with same order number : {order.get('orderNumber')}, Fix it !!!"
                    })
                    continue
                if not order_exists:
                    data['name'] = order.get('orderNumber')
                    f_carr = False
                    for ss_carrier in shipstation_carrier_exists:
                        if ss_carrier.service_id.service_code == order.get('serviceCode') and ss_carrier.shipstation_carrier_id.carrier_code == order.get('carrierCode'):
                            f_carr = ss_carrier
                    if not f_carr:
                        response['failed_records'].append({
                        "ShipstationOrderNumber":order.get('orderNumber'),
                        "serviceCode":order.get('serviceCode'),
                        "error":f"Carrier not found with given service code : {order.get('serviceCode')} , you need to create shipping method with this spefic service code !!!"
                        })
                        continue
                    data['carrier_id'] = f_carr and f_carr.id
                    sale_order_line = []
                    items_error = []
                    for line in order.get('items'):
                        product_exists = self.env['product.product'].search([('shipstation_product_id', '=', line.get('productId'))])
                        if not product_exists:
                            items_error.append({
                                "ShipstationProductId":line.get('productId'),
                                "error":f"Product not found with given product code : {line.get('productId')}, you need to import products first !!!"
                            })
                            continue
                        elif len(product_exists)>1:
                            items_error.append({
                                "ShipstationProductId":line.get('productId'),
                                "error":f"More than 1 Product found with given product code {line.get('productId')}, fix it !!!"
                            })
                            continue
                        so_line = (0, 0, {
                            'product_id' : product_exists.id,
                            'product_uom_qty' : line.get('quantity')
                        })
                        sale_order_line.append(so_line)
                    if items_error:
                        response['failed_records'].append({
                        "ShipstationOrderNumber":order.get('orderNumber'),
                        "items_error":items_error,
                        "error":"Error in products/items !!"
                        })
                        continue
                    if f_carr and f_carr.product_id:
                        carrier_line = (0, 0, {
                            'product_id': f_carr.product_id.id,
                            'product_uom_qty': 1,
                            'price_unit': order.get('shippingAmount'),
                            'is_delivery' : True
                        })
                        sale_order_line.append(carrier_line)
                    data['order_line'] = sale_order_line
                    sale_id = self.env['sale.order'].sudo().create(data)
                    response['success_records'].append({
                        "ShipstationOrderNumber":order.get('orderNumber'),
                        "OdooOrderNUmber":sale_id.name,
                        "OdooOrderID":sale_id.id,
                        "Action":"Create"
                    })
                else:
                    order_exists.sudo().write(data)
                    response['success_records'].append({
                        "ShipstationOrderNumber":order.get('orderNumber'),
                        "OdooOrderNumber":order_exists.name,
                        "OdooOrderID":order_exists.id,
                        "Action":"Update"
                    })
            _logger.info("Response= %r"%response)
            if response:
                return self.show_import_order_details(response)
            # shipstation_carrier_exists._shipping_genrated_message(response)
        except Exception as e:
            raise UserError(e)
    
    def show_import_order_details(self, response):
        vals = dict()
        vals['total_success'] = len(response.get('success_records'))
        vals['total_failed'] = len(response.get('failed_records'))
        res = self.env['shipstation.error.show'].sudo().create(vals)
        if response.get('success_records'):
            Success_Rec = self.env['shipstation.error.info'].sudo()
            for record in response.get('success_records'):
                data = dict()
                data['order_number'] = record.get('ShipstationOrderNumber')
                data['action'] = record.get('Action')
                data['success_record_id'] = res.id
                Success_Rec.create(data)

        if response.get('failed_records'):
            Failed_Rec = self.env['shipstation.error.info'].sudo()
            for record in response.get('failed_records'):
                data = dict()
                data['order_number'] = record.get('ShipstationOrderNumber')
                data['reason'] = record.get('error')
                data['failed_record_id'] = res.id
                Failed_Rec.create(data)

        view = self.env.ref('odoo_shipstation_connector.shipstation_info_wizard')
        return {
            'name': _("Shipstation Order Import Information"),
            'view_mode': 'form',
            'view_id': view.id,
            'res_id': res.id,
            'res_model': 'shipstation.error.show',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }   

    def get_shipstation_customers(self):
        try:
            path = '/customers'
            request = requests.get(url=self.request_url+path, headers=self.request_header())
            json_data = request.json()
            response_error = self.check_error_response(json_data)
            if response_error.get('error'):
                raise UserError(response_error.get('error_message')+" "+response_error.get('message_details')+" "+response_error.get('message_exception'))
            for customer in json_data.get('customers'):
                customer_exists = self.env['res.partner'].search([('shipstation_customer_id', '=', customer.get('customerId'))])
                if customer_exists:
                    continue
                data = {}
                data['name'] = customer.get('name') or ""
                data['phone'] = customer.get('phone') or ""
                data['email'] = customer.get('email') or ""
                data['shipstation_customer_id'] = customer.get('customerId')
                data['is_shipstation_customer'] = True
                data['street'] = customer.get('street1') or ""
                data['street2'] = customer.get('street2') or ""
                data['city'] = customer.get('city') or ""
                data['zip'] = customer.get('postalCode') or ""
                data['shipstation_user_id'] = self.id
                data['country_id'] = self.env['res.country'].search([('code', '=', customer.get('countryCode'))]).id
                state_id = self.env['res.country.state'].search([('country_id', '=', customer.get('countryCode')), ('code', '=', customer.get('state'))])
                data['state_id'] = state_id and state_id.id or self.env['res.country.state'].create({
                    'country_id' : self.env['res.country'].search([('code', '=', customer.get('countryCode'))]).id,'name':customer.get('countryCode'),
                    'code' : customer.get('countryCode')
                    }).id
                self.env['res.partner'].sudo().create(data)
        except Exception as e:
            raise UserError(e)

    def get_shipstation_products(self):
        try:
            path = '/products'
            request = requests.get(url=self.request_url+path, headers=self.request_header())
            json_data =  request.json()
            response_error = self.check_error_response(json_data)
            if response_error.get('error'):
                raise UserError(response_error.get('error_message')+" "+response_error.get('message_details')+" "+response_error.get('message_exception'))
            for product in json_data.get('products'):
                product_exists = self.env['product.product'].search(['|', ('shipstation_product_id', '=', product.get('productId')), ('default_code', '=', product.get('sku'))])
                if product_exists:
                    product_exists.shipstation_product_id = product.get('productId')
                    product_exists.is_shipstation_product = True
                    product_exists.shipstation_user_id = self.id
                    continue
                data = {}
                data['name'] = product.get('name')
                data['type'] = 'consu'
                data['shipstation_product_id'] = product.get('productId')
                data['is_shipstation_product'] = True
                data['default_code'] = product.get('sku')
                data['weight'] = product.get('weightOz')
                data['lst_price'] = product.get('price')
                data['shipstation_user_id'] = self.id
                data['is_storable'] = True
                self.env['product.product'].sudo().create(data)  
        except Exception as e:
            raise UserError(e)

    def get_shipstation_data(self):
        view = self.env.ref('odoo_shipstation_connector.shipstation_import_data_wizard')
        return {
            'name': _('Shipstation Data'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'shipstation.wizard',
            'view_id': view.id,
            'views': [(view.id, 'form')],
            'target': 'new',
        }

    def show_shipstation_stores(self):
        return {
            'name': 'Shipstation Stores',
            'type': 'ir.actions.act_window',
            'res_model': 'shipstation.stores',
            'view_type': 'list',
            'view_mode': 'list,form',
            'view_id': False,
            'domain': [('shipstation_user_id', '=', self.id)]
        }

    def show_shipstation_carriers(self):
        return {
            'name': 'Shipstation Carriers',
            'type': 'ir.actions.act_window',
            'res_model': 'shipstation.carriers',
            'view_mode': 'list,form',
            'view_id': False,
            'domain': [('shipstation_user_id', '=', self.id)]
        }

    def show_shipstation_packages(self):
        return {
            'name': 'Shipstation Packages',
            'type': 'ir.actions.act_window',
            'res_model': 'shipstation.packages',
            'view_mode': 'list,form',
            'view_id': False,
            'domain': [('shipstation_user_id', '=', self.id)]
        }

    def show_shipstation_marketplaces(self):
        return {
            'name': 'Shipstation Marketplaces',
            'type': 'ir.actions.act_window',
            'res_model': 'shipstation.marketplaces',
            'view_mode': 'list,form',
            'view_id': False,
            'domain': [('shipstation_user_id', '=', self.id)]
        }

    def show_shipstation_services(self):
        return {
            'name': 'Shipstation Services',
            'type': 'ir.actions.act_window',
            'res_model': 'shipstation.services',
            'view_mode': 'list,form',
            'view_id': False,
            'domain': [('shipstation_user_id', '=', self.id)]
        }

    def show_shipstation_orders(self):
        return {
            'name': 'Shipstation Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'view_id': False,
            'domain': [('shipstation_user_id', '=', self.id)]
        }

    def show_shipstation_customers(self):
        return {
            'name': 'Shipstation Customers',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'list,form',
            'view_id': False,
            'domain': [('shipstation_user_id', '=', self.id)]
        }

    def show_shipstation_products(self):
        return {
            'name': 'Shipstation Products',
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'list,form',
            'view_id': False,
            'domain': [('shipstation_user_id', '=', self.id)]
        }
