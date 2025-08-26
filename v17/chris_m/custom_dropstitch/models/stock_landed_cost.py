# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)


class StockLandedCost(models.Model):
    _inherit = "stock.landed.cost"
    
    custom_picking_ids = fields.Many2many('stock.picking', compute='_compute_custom_available_picking')
    
    @api.depends('vendor_bill_id')
    def _compute_custom_available_picking(self):
        for landed in self:
            purchase_orders = self.env['purchase.order'].search([('id', 'in', landed.vendor_bill_id.line_ids.purchase_line_id.order_id.ids)])
            landed_cost = self.env['stock.landed.cost'].search([('id', '!=', landed.id)])
            if purchase_orders:
                landed.custom_picking_ids = self.env['stock.picking'].search([('picking_type_code', '=', "incoming"),('company_id', '=', landed.company_id.id), ('move_ids.stock_valuation_layer_ids', '!=', False),('id', 'not in', landed_cost.picking_ids.ids),('id', 'in', purchase_orders.picking_ids.ids)])
            else:
                landed.custom_picking_ids = self.env['stock.picking'].search([('picking_type_code', '=', "incoming"),('company_id', '=', landed.company_id.id), ('move_ids.stock_valuation_layer_ids', '!=', False),('id', 'not in', landed_cost.picking_ids.ids)])
