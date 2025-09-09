from odoo import models, fields


class PaymentMethod(models.Model):
    _inherit = "payment.method"

    custom_fee_applicable = fields.Boolean(string="Fee Applicable")
