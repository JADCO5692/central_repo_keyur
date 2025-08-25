from odoo import models, fields, api, exceptions
from pprint import pprint
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    start_date = fields.Date(copy=False, default=fields.Date.context_today)

    def action_quotation_send(self):
        res = super().action_quotation_send()

        for order_id in self:
            # If this is a subscription and there are no invoice yet, we generate the first invoice
            if order_id.is_subscription and not order_id.invoice_ids:
                create_invoice_wizard = self.env['sale.advance.payment.inv'].create([{
                    'sale_order_ids': [(4, order_id.id)],
                }])
                invoice_id = create_invoice_wizard._create_invoices(order_id)
                invoice_id.action_post()

                # ctx = res.get('context')
                # if ctx:
                #     invoice_attach_id = self.env['ir.attachment'].create([{
                #
                #     }])
                #     ctx['default_attachment_ids'] = [(4, invoice_attach_id.id)]

        return res

    def _notify_get_recipients_groups(self, message, model_description, msg_vals=None):
        """Modify portal customer's access link to the invoice
         so that customers can directly pay"""

        groups = super()._notify_get_recipients_groups(message, model_description, msg_vals=msg_vals)
        self.ensure_one()
        for index, group in enumerate(groups):
            if group[0] == 'portal_customer':
                posted_invoice_ids = self.invoice_ids.filtered(lambda i: i.state == 'posted')
                if posted_invoice_ids:
                    invoice_id = posted_invoice_ids.sorted(key='invoice_date', reverse=False)[0]
                    local_msg_vals = {**msg_vals, "model": 'account.move', "res_id": invoice_id.id,
                                      "access_token": invoice_id._portal_ensure_token()}
                    access_link = self._notify_get_action_link('view', **local_msg_vals)
                    group[2]['button_access'] = {'title': 'View Invoice', 'url': access_link}
                    groups[index] = group

        return groups

