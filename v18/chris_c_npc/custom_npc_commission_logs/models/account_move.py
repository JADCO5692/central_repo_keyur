from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = "account.move"

    commission_id = fields.One2many('sale.commission.logs','invoice_id',string="Related Commission Log")
    is_commission_excluded = fields.Boolean(default=False, copy=False, string="Exclude from Commission Logs?")
    
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