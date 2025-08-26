# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    def get_fees(self, amount, partner_id, pm_sudo):
        if pm_sudo:
            if pm_sudo.custom_fee_applicable:
                fees = 0.0
                if amount and partner_id:
                    partner = self.env["res.partner"].browse(partner_id)
                    fees = self._compute_fees(amount, partner.country_id)
            else:
                fees = 0.0
        else:
            fees = 0.0
        return fees
