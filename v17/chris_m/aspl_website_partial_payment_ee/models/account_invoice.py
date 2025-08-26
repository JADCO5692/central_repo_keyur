# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    partial_pay = fields.Float(string="Partial Payment Amount")


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def write(self, vals):
        for rec in self:
            if rec and vals.get("state") == "posted":
                if rec.payment_transaction_id.invoice_ids:
                    rec.payment_transaction_id.invoice_ids[
                        0
                    ].partial_pay = rec.payment_transaction_id.invoice_ids[
                        0
                    ].amount_residual_signed
        return super(AccountPayment, self).write(vals)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
