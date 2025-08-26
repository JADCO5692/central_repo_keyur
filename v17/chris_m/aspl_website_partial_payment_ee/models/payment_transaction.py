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
import logging

from odoo import models
from odoo.tools import format_amount
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _check_amount_and_confirm_order(self):
        """ Confirm the sales order based on the amount of a transaction.

        Confirm the sales orders only if the transaction amount (or the sum of the partial
        transaction amounts) is equal to or greater than the required amount for order confirmation

        Grouped payments (paying multiple sales orders in one transaction) are not supported.

        :return: The confirmed sales orders.
        :rtype: a `sale.order` recordset
        """
        confirmed_orders = super(PaymentTransaction,self)._check_amount_and_confirm_order() 
        for tx in self:
            # We only support the flow where exactly one quotation is linked to a transaction.
            if len(tx.sale_order_ids) == 1:
                quotation = tx.sale_order_ids.filtered(lambda so: so.state in ('draft', 'sent'))
                # if quotation and quotation._is_confirmation_amount_reached():
                if quotation and quotation.currency_id.compare_amounts(tx.amount,  quotation.partial_pay_amount or quotation.amount_total) >= 0:
                    quotation.with_context(send_email=True).action_confirm()
                    confirmed_orders |= quotation
        return confirmed_orders


# class SaleOrder(models.Model):
#     _inherit = 'sale.order'


#     def _is_paid(self):
#         """ Return whether the sale order is paid or not based on the linked transactions.

#         A sale order is considered paid if the sum of all the linked transaction is equal to or
#         higher than `self.amount_total`.

#         :return: Whether the sale order is paid or not.
#         :rtype: bool
#         """
#         self.ensure_one()
#         return self.currency_id.compare_amounts(self.amount_paid, self.partial_pay_amount or self.amount_total) >= 0

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
