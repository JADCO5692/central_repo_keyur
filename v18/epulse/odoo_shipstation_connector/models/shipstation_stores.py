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

from odoo import fields, models, api


class ShipstationStores(models.Model):
    _name = 'shipstation.stores'
    _description = 'ShipStation Stores'

    store_id = fields.Integer(string='Store ID')
    name = fields.Char(string='Store Name')
    marketplace_id = fields.Many2one('shipstation.marketplaces', string='Marketplace ID')
    marketplace_name = fields.Char(string='Marketplace Name')
    shipstation_user_id = fields.Many2one('shipstation.configuration', string="Shipstatino User")
