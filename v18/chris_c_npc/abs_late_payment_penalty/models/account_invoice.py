# -*- coding: utf-8 -*-
#################################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2023-today Ascetic Business Solution <www.asceticbs.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################

from odoo import api,fields,models,_
import odoo.addons.decimal_precision as dp
from datetime import date
from dateutil.relativedelta import relativedelta


class AccountMove(models.Model):
    _inherit = "account.move"
    
    late_penalty = fields.Boolean(store=True, compute="compute_late_penalty", string="Late Penalty Applied")
    # penalty_source_invoice = fields.Char('Penalty Source Invoice')

    @api.depends('invoice_line_ids')
    def compute_late_penalty(self):
        late_penalty_product_id = self.env.ref('abs_late_payment_penalty.penalty_product', raise_if_not_found=False)
        for invoice in self:
            inv_products = invoice.invoice_line_ids.mapped('product_id')
            if late_penalty_product_id and late_penalty_product_id.id in inv_products.ids:
                invoice.late_penalty = True
            else:
                invoice.late_penalty = False
    
    # create function for late payment penalty.
    def late_payment_penalty(self, date=False):
        today_date = date and fields.Date.to_date(date) or fields.Date.today()
        product = self.env.ref('abs_late_payment_penalty.penalty_product', raise_if_not_found=False)
        inc_acc = product.categ_id.property_account_income_categ_id
        invoice_ids = self.env['account.move'].search([('payment_state', '=', 'not_paid'),
                                                       ('state', '=', 'posted'),
                                                       ('invoice_date', '!=', False),
                                                       ('move_type', 'in', ['out_invoice', 'out_refund']),
                                                       ('late_penalty', '=', False)])
        if product and invoice_ids:
            for invoice_id in invoice_ids:
                    if invoice_id.invoice_date + relativedelta(days=10) <= today_date:
                        sequence = max(invoice_id.invoice_line_ids.mapped("sequence"))
                        # Reset to draft so the fee would reflect on journal items and amount due
                        invoice_id.sudo().button_draft()
                        invoice_id.write({'invoice_line_ids': [(0, 0, {'sequence': sequence + 1,
                                                                                'product_id': product.id,
                                                                                'price_unit': product.list_price,
                                                                                'account_id': inc_acc.id,
                                                                                'name': '',
                                                                       })],
                                                                         })
                        invoice_id.sudo().action_post()
    
    # def late_payment_penalty(self, date=False):
    #     today_date = date and fields.Date.to_date(date) or fields.Date.today()
    #     product = self.env.ref('abs_late_payment_penalty.penalty_product')
    #     inc_acc = product.categ_id.property_account_income_categ_id
    #     invoice_ids = self.env['account.move'].search([('payment_state', '=', 'not_paid'),
    #                                                    ('state', '=', 'posted'),
    #                                                    ('invoice_date', '!=', False),
    #                                                    ('move_type', 'in', ['out_invoice', 'out_refund']),
    #                                                    ('late_penalty', '=', False)])
    #     if invoice_ids:
    #         for invoice_id in invoice_ids:
    #             # Add penalty 10th day after invoice date
    #             if invoice_id.invoice_date + relativedelta(days=10) <= today_date:
    #                 self.env['account.move'].create({
    #                     'partner_id': invoice_id.partner_id.id,
    #                     'invoice_date': today_date,
    #                     'move_type': 'out_invoice',
    #                     'penalty_source_invoice': invoice_id.name,
    #                     'invoice_line_ids': [(0, 0, {
    #                         'product_id': product.id,
    #                         'price_unit': product.list_price,
    #                         'account_id': inc_acc.id,
    #                     })],
    #                 })
    #
