from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from datetime import timedelta
class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_urgent = fields.Boolean('Urgent')
    urgency_badge = fields.Char(compute="_compute_urgency_badge", store=False)
    cargo_location = fields.Char("Cargo Location", related="sale_id.cargo_location")
    cargo_instructions = fields.Html("Cargo Instructions", related="sale_id.cargo_instructions")

    @api.depends('is_urgent', 'state')
    def _compute_urgency_badge(self):
        for rec in self:
            if rec.is_urgent and rec.state != 'done':
                rec.urgency_badge = "🔴 URGENT"
            else:
                rec.urgency_badge = ""

    def create(self, vals):
        if vals.get('origin'):
            order_id = self.env['sale.order'].search([('name','=',vals.get('origin'))])
            urgent_pricelist = self.env['product.pricelist'].browse(order_id.pricelist_id.id)
            if urgent_pricelist.name == 'Urgent':
                vals['is_urgent']=True
        return super(StockPicking, self).create(vals)
