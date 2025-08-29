# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)

sel_custom_color_no = [
    ("2", "Color 2"),
    ("3", "Color 3"),
    ("4", "Color 4"),
    ("5", "Color 5"),
    ("6", "Color 6"),
    ("7", "Color 7"),
]


class StockMove(models.Model):
    _inherit = "stock.move"

    custom_bom_item_image = fields.Binary(
        string="BoM Image", related="bom_line_id.custom_bom_item_image"
    )
    custom_variant_item_image = fields.Binary(
        string="Item Image", related="product_id.image_1920"
    )
    custom_color_no = fields.Selection(sel_custom_color_no, string="Color")
    custom_item_image = fields.Binary(string="Item Image", related="sale_line_id.custom_item_image")
    custom_production_id = fields.Many2one(comodel_name="mrp.production", string="Production", compute='_compute_custom_production_order')
    
    @api.depends('product_id')
    def _compute_custom_production_order(self):
        for move in self:
            prod_order_rec = self.env["mrp.production"].search(
                    [
                        ("origin", "=", move.origin),
                        ("state", "!=", "cancel")
                    ], limit=1
                )
            move.custom_production_id = prod_order_rec.id

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        partners = self.mapped("partner_id")
        if not partners.property_delivery_carrier_id:
            origin = self.mapped("origin")
            if origin:
                sale_id = self.env["sale.order"].search(
                    [("name", "=", origin)], limit=1
                )
                if sale_id:
                    vals["carrier_id"] = (
                        sale_id.partner_id.property_delivery_carrier_id.id
                    )
        else:
            vals["carrier_id"] = partners.property_delivery_carrier_id.id
        return vals

    def _account_entry_move(self, qty, description, svl_id, cost):
        self.ensure_one()
        customer = False
        if self.sale_line_id:
            customer = self.sale_line_id.order_id.partner_id

        elif self.picking_id and self.picking_id.partner_id:
            customer = self.picking_id.partner_id

        elif self.group_id:
            sale = self.env['sale.order'].search([('procurement_group_id', '=', self.group_id.id)], limit=1)
            if sale:
                customer = sale.partner_id

        if customer and customer.prevent_intrimed_entries:
            return self.env['account.move']
        mrp = self.env['mrp.production'].search([('name', '=', self.origin)], limit=1)

        if mrp and mrp.custom_partner.prevent_intrimed_entries:
            # return False
            return self.env['account.move']
        return super()._account_entry_move(qty, description, svl_id, cost)

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"
    
    @api.depends('product_id')
    def _compute_custom_production_order(self):
        for move_line in self:
            prod_order_rec = self.env["mrp.production"].search(
                    [
                        ("custom_sale_order_line", "=", move_line.move_id.sale_line_id.id),
                    ], limit=1
                )
            move_line.custom_production_id = prod_order_rec.id

    custom_move_state = fields.Selection(
        string="Move State", related="picking_id.state", store=True
    )
    custom_production_id = fields.Many2one(comodel_name="mrp.production", string="Production", compute='_compute_custom_production_order', store=True)

    def _get_aggregated_product_quantities(self, **kwargs):
        """Returns dictionary of products and corresponding values of interest + hs_code

        Unfortunately because we are working with aggregated data, we have to loop through the
        aggregation to add more values to each datum. This extension adds on the hs_code value.

        returns: dictionary {same_key_as_super: {same_values_as_super, hs_code}, ...}
        """
        aggregated_move_lines = super()._get_aggregated_product_quantities(**kwargs)
        for aggregated_move_line in aggregated_move_lines:
            if self.picking_id.custom_client_order_ref:
                aggregated_move_lines[aggregated_move_line]['order_ref'] = self.picking_id.custom_client_order_ref
            if self.move_id.sale_line_id.mapped('custom_customer_product'):
                customer_products = [
                    str(prod) for prod in self.move_id.sale_line_id.mapped('custom_customer_product') if prod
                ]
                aggregated_move_lines[aggregated_move_line]['customer_sku'] = ', '.join(customer_products)

        return aggregated_move_lines
