from odoo import _, models
import threading

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _check_amount_and_confirm_order(self):
        # replaced to accept multiple orders
        confirmed_orders = self.env['sale.order']
        orders = self.env['sale.order']
        for tx in self:
            orders |= tx.sale_order_ids
            # We only support the flow where exactly one quotation is linked to a transaction.
            if len(tx.sale_order_ids) == 1:
                quotation = tx.sale_order_ids.filtered(lambda so: so.state in ('draft', 'sent'))
                if quotation and quotation._is_confirmation_amount_reached():
                    quotation.with_context(send_email=True).action_confirm()
                    confirmed_orders |= quotation
            elif len(tx.sale_order_ids) > 1:
                # confirmed_orders = threading.Thread(target=self.check_and_confirm(tx)).start()
                self.check_and_confirm(tx)
        return orders
    

    def check_and_confirm(self,tx):
        confirmed_orders = self.env['sale.order']
        for quotation in tx.sale_order_ids: 
            # quotation = tx.sale_order_ids.filtered(lambda so: so.state in ('draft', 'sent'))
            if quotation and quotation.state in ('draft', 'sent') and quotation._is_confirmation_amount_reached():
                quotation.with_context(send_email=True).action_confirm()
                # threading.Thread(target=quotation.with_context(send_email=True).action_confirm()).start()
                confirmed_orders |= quotation
        return confirmed_orders