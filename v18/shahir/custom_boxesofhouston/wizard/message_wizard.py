from odoo import _, api, fields, models

import logging

_logger = logging.getLogger(__name__)

class MessageWizard(models.TransientModel):
    _name = "custom.order.payment"
    _description = "Order Payment"

    custom_downpayment_amount = fields.Float("Down-Payment Amount", required=True)
    sale_order_id = fields.Many2one(comodel_name="sale.order", string="Order")
    journal_id = fields.Many2one(comodel_name="account.journal", string="Journal", domain=[('type', 'in', ["cash", "bank"])])

    payment_method_line_id = fields.Many2one('account.payment.method.line', string='Payment Method',
        readonly=False, store=True,
        compute='_compute_payment_method_line_id',
        domain="[('id', 'in', available_payment_method_line_ids)]",
        help="Manual: Pay or Get paid by any method outside of Odoo.\n"
        "Payment Providers: Each payment provider has its own Payment Method. Request a transaction on/to a card thanks to a payment token saved by the partner when buying or subscribing online.\n"
        "Check: Pay bills by check and print it from Odoo.\n"
        "Batch Deposit: Collect several customer checks at once generating and submitting a batch deposit to your bank. Module account_batch_payment is necessary.\n"
        "SEPA Credit Transfer: Pay in the SEPA zone by submitting a SEPA Credit Transfer file to your bank. Module account_sepa is necessary.\n"
        "SEPA Direct Debit: Get paid in the SEPA zone thanks to a mandate your partner will have granted to you. Module account_sepa is necessary.\n")
    available_payment_method_line_ids = fields.Many2many('account.payment.method.line', compute='_compute_payment_method_line_fields')

    @api.depends('journal_id')
    def _compute_payment_method_line_id(self):
        for wizard in self:
            if wizard.journal_id:
                available_payment_method_lines = wizard.journal_id._get_available_payment_method_lines("inbound")
            else:
                available_payment_method_lines = False

            if available_payment_method_lines and wizard.payment_method_line_id in available_payment_method_lines:
                continue

            # Select the first available one by default.
            if available_payment_method_lines:
                wizard.payment_method_line_id = available_payment_method_lines[0]._origin
            else:
                wizard.payment_method_line_id = False

    @api.depends('journal_id')
    def _compute_payment_method_line_fields(self):
        for wizard in self:
            if wizard.journal_id:
                wizard.available_payment_method_line_ids = wizard.journal_id._get_available_payment_method_lines("inbound")
            else:
                wizard.available_payment_method_line_ids = False

    def action_ok(self):
        self.sale_order_id.action_confirm()
        self.sale_order_id.custom_hide_register_button = True

        invoice = self.sale_order_id.with_context(
            default_journal_id=self.journal_id.id
        )._create_invoices()
        invoice.action_post()

        payment_register = (
            self.env["account.payment.register"]
            .with_context(
                active_model="account.move",
                active_ids=invoice.ids,
            )
            .create(
                {
                    "amount": self.custom_downpayment_amount,
                    "payment_type": "inbound",
                    "partner_type": "customer",
                    "journal_id": self.journal_id.id,
                    "partner_id": self.sale_order_id.partner_id.id,
                    "payment_method_line_id": self.payment_method_line_id.id,
                }
            )
        )

        payments = payment_register._create_payments()

        payment = payments and payments[0] or None
        if payment:
            message = _(
                "The payment related to the transaction with reference %(ref)s has been posted: %(link)s",
                ref=self.sale_order_id.name,
                link=payment._get_html_link(),
            )
            self.sale_order_id.message_post(body=message)

        self.action_cancel()

    def action_cancel(self):
        """close wizard"""
        return {"type": "ir.actions.act_window_close"}
