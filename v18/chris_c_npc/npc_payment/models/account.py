from odoo import models, api
from pprint import pprint
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('amount_residual', 'move_type', 'state', 'company_id', 'matched_payment_ids.state')
    def _compute_payment_state(self):
        super()._compute_payment_state()

        self.set_payment_state_paid()

    def set_payment_state_paid(self):
        for invoice_id in self:
            if invoice_id.state == 'posted' and invoice_id.payment_state != 'paid':
                confirmed_tx_ids = invoice_id.transaction_ids.filtered(lambda tx: tx.state == 'done')

                if confirmed_tx_ids:
                    total_payments = sum(confirmed_tx_ids.mapped("amount"))
                    # if total_payments >= invoice_id.amount_residual:
                    #     invoice_id.payment_state = 'paid'
                    #     _logger.warning(f"Moved {invoice_id.name} to paid")
                    if total_payments >= invoice_id.amount_total:
                        invoice_id.payment_state = 'paid'
                        _logger.warning(f"Moved {invoice_id.name} to paid")
