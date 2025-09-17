from odoo import _, api, fields, models
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    is_online = fields.Boolean(string='Is Online')
    order_type = fields.Selection([
        ('bulk', 'Bulk Order'),
        ('dropship', 'Dropship'),
        ], string='Order Type')

    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        if order.partner_id.is_advanced_payment and order.partner_id.of_payment_percentage:
            order.require_payment = True
            order.prepayment_percent = order.partner_id.of_payment_percentage
        for line in order.order_line:
            line.tax_id = [(5, 0, 0)]
            line._compute_amount()
        return order

    def write(self, vals):
        if 'order_line' in vals:
            for line in vals['order_line']:
                if line[0] in (0, 1):# here check is made only for create and update calls
                    line_vals = line[2]#checking dictionary in the nested list
                    if 'tax_id' in line_vals:
                        line_vals['tax_id'] = [(5, 0, 0)]

        result = super(SaleOrder, self).write(vals)

        for order in self:
            for line in order.order_line:
                if line.tax_id:
                    line.tax_id = [(5, 0, 0)]
                    line._compute_amount()
        return result

    def action_custom_checkout(self, order_type):
        template = self._find_mail_template()
        self.write(
            {
                'is_online':True,
                'order_type': order_type,
            }
        )

        if template:
            self._send_order_notification_mail(template)        

        portal_url = self.get_portal_url()
        return portal_url
