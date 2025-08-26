# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockQuant(models.Model):
    """ This model represents stock.quant."""
    _inherit = "stock.quant"

    free_qty = fields.Float(string='Free To Use', compute='_compute_computed_field', store=True)
    incoming_qty = fields.Float(string='Incoming Quantity', compute='_compute_quantities', store=True)
    outgoing_qty = fields.Float(string='Outgoing Quantity', compute='_compute_quantities', store=True)
    virtual_available = fields.Float(string='Forecasted Quantity', compute='_compute_quantities', store=True)

    @api.depends('inventory_quantity_auto_apply','reserved_quantity')
    def _compute_computed_field(self):
        """Compute the value of the field computed_field."""
        for record in self:
            record.free_qty = record.inventory_quantity_auto_apply - record.reserved_quantity

    @api.depends('product_id','location_id')
    def _compute_quantities(self):
        """Compute the incoming quantity."""
        for record in self:
            vals = record.product_id.with_context(location=record.location_id.id)._compute_quantities_dict(lot_id=record.lot_id.id, package_id=record.package_id.id, owner_id=record.owner_id.id)
            vals = vals.get(record.product_id.id)
            record.incoming_qty = vals.get('incoming_qty', 0.0)
            record.outgoing_qty = vals.get('outgoing_qty', 0.0)
            record.virtual_available = vals.get('virtual_available', 0.0)
