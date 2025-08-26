from odoo import models, fields

class Website(models.Model):
    _inherit = 'website'

    def sale_get_order(self, force_create=False, update_pricelist=False):
        order = super(Website, self).sale_get_order(force_create, update_pricelist)
        if order and len(order):
            order._compute_require_payment()
            order._compute_prepayment_percent()
            order._onchange_custom_partner_id()
            order._compute_allowed_customer_ids()
            order.custom_policy = "intent"
        return order