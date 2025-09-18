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

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)


class ShipstationImportWizard(models.TransientModel):
    _name = "shipstation.wizard"
    _description = "Shipstation Import Data Wizard"

    is_marketplace = fields.Boolean(string="Marketplace")
    is_stores = fields.Boolean(string="Store")
    is_carriers = fields.Boolean(string="Carriers")
    is_packages = fields.Boolean(string="Packages")
    is_services = fields.Boolean(string="Carrier Services")
    is_orders = fields.Boolean(string="Orders")
    is_customers = fields.Boolean(string="Customers")
    is_products = fields.Boolean(string="Products")

    @api.onchange('is_services', 'is_packages')
    def _onchange_user_type_id(self):
        if self.is_services or self.is_packages:
            self.is_carriers = True


    def import_shipstation_data(self):
        active_id = self.env.context.get('active_id')
        shipstation = self.env['shipstation.configuration'].sudo().search([('id', '=', int(active_id))])
        if self.is_carriers:
            shipstation.get_shipstation_carriers()
        if self.is_stores:
            shipstation.get_shipstation_stores()
        if self.is_services:
            if not self.env['shipstation.carriers'].sudo().search([('shipstation_user_id', '=', shipstation.id)]):
                raise UserError("No Carrier available for this shipstation ID. Please Import Carrier First!")
            # shipstation.get_shipstation_carriers()
            shipstation.get_shipstation_carrier_services()
        if self.is_packages:
            if not self.env['shipstation.carriers'].sudo().search([('shipstation_user_id', '=', shipstation.id)]):
                raise UserError("No carrier available for this shipstation ID. Please Import Carrier First!")
            # shipstation.get_shipstation_carriers()
            shipstation.get_shipstation_carrier_packages()
        if self.is_customers:
            shipstation.get_shipstation_customers()
        if self.is_products:
            shipstation.get_shipstation_products()
        if self.is_marketplace:
            shipstation.get_shipstation_marketplaces()
        if self.is_orders:
            return shipstation.get_shipstation_orders()
