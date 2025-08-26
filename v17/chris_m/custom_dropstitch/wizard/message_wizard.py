from odoo import _, api, fields, models

import logging

_logger = logging.getLogger(__name__)


class MessageWizard(models.TransientModel):
    _name = "custom.message.wizard"
    _description = "Message Wizard"

    message = fields.Html("Gift Message", required=True)

    def action_ok(self):
        """close wizard"""
        return {"type": "ir.actions.act_window_close"}
    
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
        payment_provider = self.env['payment.provider'].sudo().search([('name', '=', 'Wire Transfer')], limit=1)
        payment_method = self.env['payment.method'].sudo().search([('name', '=', 'Wire Transfer')], limit=1)
        
        if self.payment_method_line_id.payment_provider_id:
            payment_provider = self.payment_method_line_id.payment_provider_id
        
        payment_transaction = self.env['payment.transaction'].sudo().create({
            'reference': self.sale_order_id.name,
            'provider_id': payment_provider.id,
            'payment_method_id': payment_method.id,
            'sale_order_ids': [self.sale_order_id.id],
            'partner_id': self.sale_order_id.partner_id.id,
            'amount': self.custom_downpayment_amount,
            'currency_id': self.sale_order_id.company_id.currency_id.id,
        })
        payment_transaction.state = 'done'
        
        # Check partial
        payment = self.env['account.payment'].sudo().create({
            'amount': self.custom_downpayment_amount,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'journal_id': self.journal_id.id,
            'partner_id': self.sale_order_id.partner_id.id,
            'payment_transaction_id': payment_transaction.id,
            'payment_method_line_id': self.payment_method_line_id.id,
        })
        payment.action_post()
        payment_transaction.payment_id = payment.id
        message = _("The down-payment related to the transaction with reference %(ref)s has been posted: %(link)s",
                ref=self.sale_order_id.name, link=payment._get_html_link(),
            )
        self.sale_order_id.message_post(body=message)
        self.sale_order_id.action_confirm()
        self.sale_order_id.custom_hide_register_button = True
        
        self.action_cancel()
    
    def action_cancel(self):
        """close wizard"""
        return {"type": "ir.actions.act_window_close"}

class MessageWizard2(models.TransientModel):
    _name = "custom.message.wizard2"
    _description = "Message Wizard 2"

    message = fields.Html("Message", required=True)
    production_id = fields.Many2one(comodel_name="mrp.production", string="Production")

    def action_ok(self):
        order_url = (
            self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            + "/web#id=%s&view_type=form&model=mrp.production" % self.production_id.id
        )
        sale_order_id = self.env["sale.order"].search(
            [("name", "=", self.production_id.origin)]
        )
        if sale_order_id:
            picking_id = self.env["stock.picking"].sudo().search(
                [("sale_id", "=", sale_order_id.id)], limit=1
            )
            picking_url = (
                self.env["ir.config_parameter"].sudo().get_param("web.base.url")
                + "/web#id=%s&view_type=form&model=stock.picking" % picking_id.id
            )
        else:
            raise UserError(_("Sales Order Not Found !!!"))
        self.production_id.write(
            {
                "custom_current_url": order_url,
                "custom_stock_picking_id": picking_id,
                "custom_stock_picking_url": picking_url,
            }
        )
        xml_id = "custom_dropstitch.action_report_travel_ticket_label_102X45"
        if not xml_id:
            raise UserError(
                _(
                    "Unable to find report template for %s format",
                    self.production_id.print_format,
                )
            )
        report = self.env.ref(xml_id).report_action(self.production_id)
        return report

    def action_cancel(self):
        """close wizard"""
        return {"type": "ir.actions.act_window_close"}
