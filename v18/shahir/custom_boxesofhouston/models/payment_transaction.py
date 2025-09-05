from odoo import models, fields

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _check_amount_and_confirm_order(self):
        context = dict(self._context)
        context['ecommerce_create'] = True
        self = self.with_context(context)
        res = super(PaymentTransaction, self)._check_amount_and_confirm_order()
        return res