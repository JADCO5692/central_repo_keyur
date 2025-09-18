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

from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


WEIGHT_UNIT = [
    ('pounds', 'pounds'),
    ('ounces', 'ounces'),
    ('grams', 'grams'),
    ]

SHIPSTATION_PACKAGE_UNIT = [
    ('inches', 'inches'),
    ('centimeters', 'centimeters'),
    ]

CONFIRMATION = [
    ('none', 'none'),
    ('delivery', 'delivery'),
    ('signature', 'signature'),
    ('adult_signature', 'adult_signature'),
    ('direct_signature', 'direct_signature'),
]

RESIDENTIAL = [
    ('commercial', 'commercial'),
    ('residential', 'residential'),
]


class DeliveryCarriers(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add = [('shipstation','ShipStation')], ondelete={'shipstation': 'cascade'})
    shipstation_carrier_id = fields.Many2one('shipstation.carriers', string='ShipStation Carrier')
    service_id = fields.Many2one('shipstation.services', string='Carrier Service')
    package_id = fields.Many2one('shipstation.packages', string='Carrier Packages')
    shipstation_user_id = fields.Many2one('shipstation.configuration', string='ShipStation User')
    shipstation_store_id = fields.Many2one('shipstation.stores', string="ShipStation Store ID", ondelete='cascade')
    weight_unit = fields.Selection(selection = WEIGHT_UNIT, string = 'Weight Unit', default = 'ounces')
    delivery_confirmation = fields.Selection(selection = CONFIRMATION, string = 'Delivery Confirmation', default = 'none')
    address_type = fields.Selection(selection = RESIDENTIAL, string = 'Address Type', default = 'commercial')
    shipstation_package_unit = fields.Selection(selection = SHIPSTATION_PACKAGE_UNIT, string = 'Package UOM', default = 'centimeters')



class ProductPackage(models.Model):
    _inherit = 'product.package'

    delivery_type = fields.Selection(
        selection_add=[('shipstation', 'ShipStation')]
    )


class ProductPackaging(models.Model):
    _inherit = 'stock.package.type'

    package_carrier_type = fields.Selection(
        selection_add=[('shipstation', 'ShipStation')]
    )


class ShipStationCarriers(models.Model):
    _name = 'shipstation.carriers'
    _description = 'ShipStation Carriers'

    name = fields.Char(string='Carrier Name')
    carrier_code = fields.Char(string='Carrier Code')
    carrier_account_number = fields.Char(string='Carrier Account Number')
    requires_funded_account = fields.Boolean(string='Funded Account')
    carrier_balance = fields.Float(string='Carrier Balance')
    shipping_provide_id = fields.Char(string='Shipping Provider ID')
    is_primary = fields.Boolean(string='Is Primary')
    # marketplace_user = fields.Many2one('shipstation.configuration', string='Marketplace User')
    shipstation_user_id = fields.Many2one('shipstation.configuration', string='Shipstation User')

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

    def get_carrier_services(self):
        try:
            path = '/carriers/listservices?carrierCode={}'.format(self.carrier_code)
            request = requests.get(url=self.shipstation_user_id.request_url+path, headers=self.shipstation_user_id.request_header())
            json_data =  request.json()
            if not (type(json_data) == type(list())):
                response_error = self.check_error_response(json_data)
                if response_error.get('error'):
                    raise UserError(response_error.get('error_message')+" "+response_error.get('message_details')+" "+response_error.get('message_exception'))
            for service in json_data:
                data = {}
                data['name'] = service.get('name')
                data['carrier_code'] = self.id
                data['service_code'] = service.get('code')
                data['is_domestic'] = service.get('domestic')
                data['is_international'] = service.get('international')
                service_exists = self.env['shipstation.services'].sudo().search([('service_code','=', service.get('code'))])
                if not service_exists:
                    self.env['shipstation.services'].sudo().create(data)
        except Exception as e:
            raise UserError(e)

    def get_carrier_packages(self):
        try:
            path = '/carriers/listpackages?carrierCode={}'.format(self.carrier_code)
            request = requests.get(url=self.shipstation_user_id.request_url+path, headers=self.shipstation_user_id.request_header())
            json_data =  request.json()
            if not (type(json_data) == type(list())):
                response_error = self.check_error_response(json_data)
                if response_error.get('error'):
                    raise UserError(response_error.get('error_message')+" "+response_error.get('message_details')+" "+response_error.get('message_exception'))
            for package in json_data:
                data = {}
                data['name'] = package.get('name')
                data['carrier_code'] = self.id
                data['package_code'] = package.get('code')
                data['is_domestic'] = package.get('domestic')
                data['is_international'] = package.get('international')
                package_exists = self.env['shipstation.packages'].sudo().search([('package_code','=', package.get('code'))])
                if not package_exists:
                    self.env['shipstation.packages'].sudo().create(data)
        except Exception as e:
            raise UserError(e)
