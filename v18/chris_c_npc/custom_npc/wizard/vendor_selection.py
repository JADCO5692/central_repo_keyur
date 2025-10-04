# -*- coding: utf-8 -*-
from odoo import api, fields, models


class VendorSelection(models.TransientModel):
    """ This model represents vendor.selection."""
    _name = 'vendor.selection'
    _description = 'VendorSelection'

    invoice_line_ids = fields.Many2many('account.move.line', string='Invoice Lines')
    vendor_id = fields.Many2one("res.partner", string="Vendor")
    lead_partner_ids = fields.Many2many(
        'res.partner',related='invoice_line_ids.lead_partner_ids')
    invoice_date = fields.Date(string='Invoice Date')

    @api.model
    def default_get(self, fields):
        res = super(VendorSelection, self).default_get(fields)
        if 'invoice_line_ids' in fields:
            line_ids = self._context.get('invoice_line_ids')
            if line_ids:
                res.update({'invoice_line_ids': [(6, 0, line_ids)]})
        return res


    def process(self):
        return self.invoice_line_ids.move_id._action_create_vendor_bill(self.vendor_id, self.invoice_line_ids, self.invoice_date_due)