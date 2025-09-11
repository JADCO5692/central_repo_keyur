# -*- coding: utf-8 -*-
from odoo import api, fields, models

model_field_dict = {
    'sale.order': 'custom_order_confirmation_ids',
    'account.payment': 'custom_payment_completed_ids',
    'account.move': 'custom_invoice_generated_ids',
    'stock.picking': 'custom_shipping_confirmation_ids',
}

class MailThread(models.AbstractModel):
    """ This model represents mail.thread."""
    _inherit = 'mail.thread'

    def _notify_get_recipients(self, message, msg_vals, **kwargs):
        recipients_data = super()._notify_get_recipients(message, msg_vals=msg_vals, **kwargs)
        if self._name not in model_field_dict or not self._context.get('custom_notify'):
            return recipients_data
        field_name = model_field_dict[self._name]
        notify_partner = self.partner_id._get_notify_partner_ids(field_name, self)
        new_recipients_data = []
        for partner in recipients_data:
            if partner['id'] in notify_partner:
                new_recipients_data.append(partner)
        return new_recipients_data