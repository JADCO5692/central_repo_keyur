from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = "account.move"

    commission_id = fields.One2many('sale.commission.logs','invoice_id',string="Related Commission Log")
    is_commission_excluded = fields.Boolean(default=False, copy=False, string="Exclude from Commission Logs?")
    related_commission_id = fields.Many2one('sale.commission.logs', string="Vendor Commission Log", copy=False, ondelete='cascade')
    vendor_bill_count_cl = fields.Integer(compute='_compute_vendor_bill_count_cl')

    @api.depends('vendor_bill_ids')
    def _compute_vendor_bill_count_cl(self):
        for record in self:
            record.vendor_bill_count_cl = len(
                record.vendor_bill_ids.filtered(lambda bill: bill.related_commission_id.id != False))

    def button_cancel(self):
        res = super().button_cancel()
        # Unlink related commission logs
        for move in self:
            move.commission_id.unlink()
        return res
        
    def button_draft(self):
        res = super().button_draft()
        # Unlink related commission logs
        for move in self:
            move.commission_id.unlink()
        return res

    def action_view_vendor_bills_cl(self):
        """Action to view related vendor bills"""
        vals = {
            'type': 'ir.actions.act_window',
            'name': 'Related Vendor Bills (CL)',
            'res_model': 'account.move',
            'domain': [('id', 'in', self.vendor_bill_ids.ids), ('related_commission_id','!=',False)],
            'view_mode': 'list,form' if len(self.vendor_bill_ids) > 1 else 'form',
            'target': 'current',
        }
        if len(self.vendor_bill_ids) == 1:
            vals['res_id'] = self.vendor_bill_ids[0].id
        return vals

    @api.depends('invoice_line_ids.vendor_bill_id', 'related_commission_id')
    def compute_related_invoice_count(self):
        for record in self:
            related_invoices = self.env['account.move.line'].search([('vendor_bill_id', 'in', record.ids)]).move_id
            commission_invoice = record.related_commission_id.invoice_id
            record.related_invoice_count = len(related_invoices+commission_invoice)

    def _get_related_invoices(self):
        invoice = super()._get_related_invoices()
        invoice |= self.related_commission_id.invoice_id
        return invoice