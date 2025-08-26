from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    partial_pay = fields.Float(string="Down-Payment Amount")
    
    def _get_invoice_in_payment_state(self):
        res = super(AccountMove, self)._get_invoice_in_payment_state()
        if res in ("in_payment", "paid"):
            order_id = self.line_ids.sale_line_ids.order_id
            if order_id:
                pickings = self.env["stock.picking"].search(
                    [("origin", "=", order_id.name)]
                )
                for picking in pickings:
                    if picking.state == "invoice_sent":
                        picking.state = "ready_to_be_sent"
                        if picking.batch_id:
                            all_pickings = picking.batch_id.mapped(
                                "picking_ids"
                            ).filtered(
                                lambda picking: picking.state not in ("cancel", "done")
                            )
                            ready_to_be_sent_pickings = picking.batch_id.mapped(
                                "picking_ids"
                            ).filtered(
                                lambda picking: picking.state in ("ready_to_be_sent")
                            )
                            if len(all_pickings.ids) == len(
                                ready_to_be_sent_pickings.ids
                            ):
                                picking.batch_id.state = "ready_to_be_sent"
                    if picking.state == "ready_to_be_sent":
                        if picking.batch_id:
                            all_pickings = picking.batch_id.mapped(
                                "picking_ids"
                            ).filtered(
                                lambda picking: picking.state not in ("cancel", "done")
                            )
                            ready_to_be_sent_pickings = picking.batch_id.mapped(
                                "picking_ids"
                            ).filtered(
                                lambda picking: picking.state in ("ready_to_be_sent")
                            )
                            if len(all_pickings.ids) == len(
                                ready_to_be_sent_pickings.ids
                            ):
                                picking.batch_id.state = "ready_to_be_sent"
        return res

    def action_load_previous_bill(self):
        if not self.partner_id:
            raise UserError(_("Please select vendor first."))
        previous_bill = self.env['account.move'].search([
            ('partner_id', '=', self.partner_id.id),
            ('move_type', '=', 'in_invoice'),   
            ('state', 'in', ['posted']),  
        ], order='create_date desc', limit=1)
        if len(previous_bill):
            account_move_line = self.env['account.move.line']
            for line in previous_bill.invoice_line_ids:
                account_move_line.create({
                    'name':line.name,
                    'move_id':self.id,
                    'account_id':line.account_id.id,
                    'product_id':line.product_id.id,
                })
        else:
            raise UserError(_("Previous posted bill doesn't exist for this vendor."))
        

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    custom_order_line_id = fields.Many2one(
        "sale.order.line",
        string="Custom Order Line",
        compute="_compute_custom_order_line_id",
        readonly=True,
        copy=False,
    )
    custom_item_image = fields.Binary(string="Item Image")

    @api.depends("sale_line_ids")
    def _compute_custom_order_line_id(self):
        for line in self:
            if line.sale_line_ids:
                line.custom_order_line_id = line.sale_line_ids[0].id
            else:
                line.custom_order_line_id = False
