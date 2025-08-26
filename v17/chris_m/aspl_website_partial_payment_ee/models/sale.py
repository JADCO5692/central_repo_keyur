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

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    partial_pay_amount = fields.Float(string="Partial Payment Amount")

    def _is_paid(self):
        """ Return whether the sale order is paid or not based on the linked transactions.

        A sale order is considered paid if the sum of all the linked transaction is equal to or
        higher than `self.amount_total`.

        :return: Whether the sale order is paid or not.
        :rtype: bool
        """
        self.ensure_one()
        return self.currency_id.compare_amounts(self.amount_paid, self.partial_pay_amount or self.amount_total) >= 0


class ResPartner(models.Model):
    _inherit = "res.partner"

    allow_partial_payment = fields.Boolean(string="Partial Payment")
    min_order_amount = fields.Float(string='Minimum Order Amount')
    adv_payment_amount = fields.Integer(string='Advance Payment Amount(%)')
    min_payment_term = fields.Integer(string='Minimum Payment Term')
    max_partial_order = fields.Integer(string='Maximum Partial Payment')
