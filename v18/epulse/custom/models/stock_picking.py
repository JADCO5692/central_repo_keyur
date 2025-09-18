from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from datetime import timedelta
class StockPicking(models.Model):
    _inherit = "stock.picking"
    is_urgent=fields.Boolean('Urgent')
    urgency_badge = fields.Char(compute="_compute_urgency_badge", store=False)

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

    # def button_validate(self):
    #     res = super(StockPicking, self).button_validate()
    #     for picking in self:
    #         if picking.state == 'done':
    #             # Send Email using the existing _send_confirmation_email method
    #             try:
    #                 picking._send_confirmation_email()
    #             except Exception as e:
    #                 picking.message_post(body=f"Failed to send Email: {str(e)}")

    #     return res
