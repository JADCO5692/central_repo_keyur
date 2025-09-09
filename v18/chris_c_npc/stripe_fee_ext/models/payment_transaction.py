# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.addons.payment import utils as payment_utils


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _stripe_prepare_payment_intent_payload(self):
        """Prepare the payload for the creation of a payment intent in Stripe format.

        Note: This method serves as a hook for modules that would fully implement Stripe Connect.
        Note: self.ensure_one()

        :return: The Stripe-formatted payload for the payment intent request
        :rtype: dict
        """

        res = super(PaymentTransaction, self)._stripe_prepare_payment_intent_payload()
        res.update(
            {
                "amount": payment_utils.to_minor_currency_units(
                    self.amount + self.fees, self.currency_id
                ),
            }
        )
        return res
