from odoo import models, fields, api, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    po_origin = fields.Char(compute='_compute_po_origin', string='PO Origin', store=True, readonly=False)

    @api.depends('move_ids.purchase_line_id.order_id.origin')
    def _compute_po_origin(self):
        for picking in self:
            if picking.move_ids and picking.move_ids.purchase_line_id:
                picking.po_origin = picking.move_ids.purchase_line_id.order_id.origin
            else:
                picking.po_origin = ''