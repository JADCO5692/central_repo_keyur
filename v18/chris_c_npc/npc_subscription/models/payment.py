from odoo import models, fields, api
from pprint import pprint
import psycopg2
import logging

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    is_manual_adjusted_transaction = fields.Boolean("Manually adjusted Transaction")

    def _get_mandate_values(self):
        mandate_values = super()._get_mandate_values()

        datetime_now = fields.Datetime.now()

        if 'start_datetime' in mandate_values and mandate_values['start_datetime'] <= datetime_now:
            mandate_values['start_datetime'] = fields.Datetime.now()

        return mandate_values

    def _server_action_post_process_npc(self):
        """ Trigger the post-processing of the transactions that were not handled by the client in
        the `poll_status` controller method.

        :return: None
        """
        for record in self:
            record.write({
                'is_manual_adjusted_transaction' : True
            })
            transaction_create_date = record.create_date.month
            # raise UserError(transaction_create_date)
            linked_moves_with_transaction = self.env['account.move'].search([('transaction_ids', '=', record.id)])
            for move in linked_moves_with_transaction:
                if not move.payment_ids and move.payment_state in ['paid','in_payment'] and move.state == 'posted' and move.create_date.month != transaction_create_date:
                    move.write({
                        'transaction_ids': [(3, record.id, 0)],
                        'payment_state': 'not_paid',
                    })
                if not move.payment_ids and move.payment_state in ['paid','in_payment'] and move.state == 'posted' and move.create_date.month == transaction_create_date and not record.payment_id:
                    move.write({
                        'payment_state': 'not_paid',
                    })
            try:
                if record.state == 'done':
                    record._post_process()
                self.env.cr.commit()
            except psycopg2.OperationalError:
                self.env.cr.rollback()  # Rollback and try later.
            except Exception as e:
                _logger.exception(
                    "encountered an error while post-processing transaction with reference %s:\n%s",
                    record.reference, e
                )
                self.env.cr.rollback()


    def _create_payment(self, **extra_create_values):
        """Create an `account.payment` record for the current transaction.

        If the transaction is linked to some invoices, their reconciliation is done automatically.

        Note: self.ensure_one()

        :param dict extra_create_values: Optional extra create values
        :return: The created payment
        :rtype: recordset of `account.payment`
        """
        self.ensure_one()

        reference = (f'{self.reference} - '
                     f'{self.partner_id.display_name or ""} - '
                     f'{self.provider_reference or ""}'
                    )

        payment_method_line = self.provider_id.journal_id.inbound_payment_method_line_ids\
            .filtered(lambda l: l.payment_provider_id == self.provider_id)
        payment_values = {
            'amount': abs(self.amount),  # A tx may have a negative amount, but a payment must >= 0
            'payment_type': 'inbound' if self.amount > 0 else 'outbound',
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.commercial_partner_id.id,
            'partner_type': 'customer',
            'journal_id': self.provider_id.journal_id.id,
            'company_id': self.provider_id.company_id.id,
            'payment_method_line_id': payment_method_line.id,
            'payment_token_id': self.token_id.id,
            'payment_transaction_id': self.id,
            'memo': reference,
            'write_off_line_vals': [],
            'invoice_ids': self.invoice_ids,
            **extra_create_values,
        }
        if self.is_manual_adjusted_transaction:
            payment_values['date'] = self.create_date

        for invoice in self.invoice_ids:
            if invoice.state != 'posted':
                continue
            next_payment_values = invoice._get_invoice_next_payment_values()
            if next_payment_values['installment_state'] == 'epd' and self.amount == next_payment_values['amount_due']:
                aml = next_payment_values['epd_line']
                epd_aml_values_list = [({
                    'aml': aml,
                    'amount_currency': -aml.amount_residual_currency,
                    'balance': -aml.balance,
                })]
                open_balance = next_payment_values['epd_discount_amount']
                early_payment_values = self.env['account.move']._get_invoice_counterpart_amls_for_early_payment_discount(epd_aml_values_list, open_balance)
                for aml_values_list in early_payment_values.values():
                    if (aml_values_list):
                        aml_vl = aml_values_list[0]
                        aml_vl['partner_id'] = invoice.partner_id.id
                        payment_values['write_off_line_vals'] += [aml_vl]
                break

        payment = self.env['account.payment'].create(payment_values)
        payment.action_post()

        # Track the payment to make a one2one.
        self.payment_id = payment

        # Reconcile the payment with the source transaction's invoices in case of a partial capture.
        if self.operation == self.source_transaction_id.operation:
            invoices = self.source_transaction_id.invoice_ids
        else:
            invoices = self.invoice_ids
        if invoices:
            invoices.filtered(lambda inv: inv.state == 'draft').action_post()

            (payment.move_id.line_ids + invoices.line_ids).filtered(
                lambda line: line.account_id == payment.destination_account_id
                and not line.reconciled
            ).reconcile()

        return payment
