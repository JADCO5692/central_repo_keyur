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


class ShipstationMarketplaces(models.Model):
    _name = 'shipstation.marketplaces'
    _description = 'ShipStation Marketplaces'

    marketplace_id = fields.Integer(string='Marketplace ID')
    name = fields.Char(string='Marketplace Name')
    shipstation_user_id = fields.Many2one('shipstation.configuration', string='Marketplace User')
    # marketplace_user = fields.Many2one('shipstation.configuration', string='Marketplace User')
