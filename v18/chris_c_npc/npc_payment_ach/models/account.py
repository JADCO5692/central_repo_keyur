from odoo import models, api
from pprint import pprint
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('amount_residual', 'move_type', 'state', 'company_id', 'matched_payment_ids.state')
    def _compute_payment_state(self):
        super()._compute_payment_state()

        self.set_payment_state_from_ach()

    def set_payment_state_from_ach(self):
        ach_payment_method_id = self.env.ref('payment.payment_method_ach_direct_debit', raise_if_not_found=False)

        for invoice_id in self:
            if invoice_id.state == 'posted' and invoice_id.payment_state not in ('in_payment', 'paid'):
                tx_ids = invoice_id.transaction_ids.filtered(
                    lambda tx: tx.state in (
                        'draft',
                        'pending',
                        'authorized') and tx.payment_method_id == ach_payment_method_id and tx.provider_reference)

                if tx_ids:
                    invoice_id.payment_state = 'in_payment'
                    _logger.warning(f"Moved {invoice_id.name} to in payment")
