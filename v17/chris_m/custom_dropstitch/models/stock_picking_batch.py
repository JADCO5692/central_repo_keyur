# -*- coding: utf-8 -*-
from odoo import Command, models, fields, api, _
from odoo.exceptions import ValidationError, UserError

import logging

_logger = logging.getLogger(__name__)

sel_shipping_fees = [
    ("charge_fees", "Charge Shipping Fees"),
    ("no_fees", "No Shipment Fees"),
]


class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"
    _description = "Batch Transfer"

    custom_available_carrier_ids = fields.Many2many("delivery.carrier", compute='_compute_custom_available_carrier', string="Available Carriers")
    custom_carrier_id = fields.Many2one(
        "delivery.carrier", string="Carrier", check_company=True, tracking=True
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_progress", "In progress"),
            ("invoice_sent", "Invoice Sent"),
            ("ready_to_be_sent", "Ready to be Sent"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        default="draft",
        store=True,
        compute="_compute_state",
        copy=False,
        tracking=True,
        required=True,
        readonly=True,
        index=True,
        ondelete="set default",
    )

    custom_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
        store=True,
        readonly=False,
        check_company=True,
        domain="[('type', 'in', ('bank', 'cash'))]",
        tracking=True,
    )

    custom_sale_payment_term_id = fields.Many2one(
        comodel_name="account.payment.term",
        string="Payment Terms",
        compute="_compute_batch_payment_term_id",
        store=True,
        readonly=False,
        check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        tracking=True,
    )

    custom_invoice_payment_state = fields.Boolean(
        compute="_compute_invoice_payment_state_custom"
    )
    custom_delivery_set = fields.Boolean(compute="_compute_delivery_state_custom")

    custom_auto_pay_limit = fields.Float(string="Customer Auto Payment Limit")
    custom_sale_total_amount = fields.Float(string="Total Amount")
    custom_delivery_price = fields.Float()
    custom_display_price = fields.Float(string="Delivery Cost", readonly=True)

    custom_order_payment_term = fields.Char(
        related="custom_sale_payment_term_id.name", string="Payment Term"
    )
    is_show_gift_lable_action = fields.Boolean(compute="_compute_show_gift_label")
    custom_shipping_fees = fields.Selection(
        sel_shipping_fees, string="Shipping Fees", default="charge_fees", tracking=True
    )
    is_shipping_lebel_generated = fields.Boolean("Is Shipping Lebel generated")
    custom_carrier_tracking_ref = fields.Char(
        string="Tracking Reference", copy=False, tracking=True
    )

    def write(self, vals):
        res = super(StockPickingBatch, self).write(vals)
        if "custom_carrier_id" in vals:
            for batch in self:
                for picking in batch.picking_ids:
                    picking.carrier_id = vals["custom_carrier_id"]
        return res

    @api.depends("custom_carrier_id")
    def _compute_batch_payment_term_id(self):
        for batch in self:
            pickings = batch.mapped("picking_ids").filtered(
                lambda picking: picking.state not in ("cancel", "done")
            )
            custom_sale_total_amount = 0
            for picking in pickings:
                batch.custom_sale_payment_term_id = picking.sale_id.payment_term_id.id
                batch.custom_auto_pay_limit = (
                    picking.sale_id.partner_id.custom_auto_pay_limit
                )
                custom_sale_total_amount += picking.sale_id.amount_total
            batch.custom_sale_total_amount = custom_sale_total_amount
            if batch.custom_shipping_fees == "charge_fees":
                batch.get_shipment_rate()
            else:
                batch.custom_display_price = 0

    def _compute_delivery_state_custom(self):
        for batch in self:
            pickings = batch.mapped("picking_ids").filtered(
                lambda picking: picking.state not in ("cancel", "done")
            )
            custom_delivery_set_list = []
            for picking in pickings:
                custom_delivery_set_list.append(
                    any(line.is_delivery for line in picking.sale_id.order_line)
                )
            if any(not value for value in custom_delivery_set_list):
                batch.custom_delivery_set = False
            else:
                batch.custom_delivery_set = True

    def _compute_invoice_payment_state_custom(self):
        for batch in self:
            pickings = batch.mapped("picking_ids").filtered(
                lambda picking: picking.state not in ("cancel", "done")
            )
            if pickings:
                payment_state_list = []
                for each_pick in pickings:
                    payment_state = (
                        self.env["account.move"]
                        .search(
                            [("invoice_origin", "=", each_pick.sale_id.name)], limit=1
                        )
                        .payment_state
                    )
                    payment_state_list.append(payment_state)

                if any(
                    state in ["not_paid", "partial"] for state in payment_state_list
                ):
                    batch.custom_invoice_payment_state = True
                else:
                    batch.custom_invoice_payment_state = False

            else:
                batch.custom_invoice_payment_state = False

    def get_shipment_rate(self):
        self.custom_delivery_price = 0
        self.custom_display_price = 0
        pickings = self.mapped("picking_ids").filtered(
            lambda picking: picking.state not in ("cancel", "done")
        )
        if self.custom_carrier_id:
            for each_picking in pickings:
                vals = self.custom_carrier_id.with_context(
                    order_weight=each_picking.sale_id.shipping_weight
                ).rate_shipment(each_picking.sale_id)
                if vals.get("success"):
                    self.custom_delivery_price += vals["price"]
                    self.custom_display_price += vals["carrier_price"]

    def _get_intent_estimated_weight(self):
        self.ensure_one()
        pickings = self.mapped("picking_ids").filtered(
            lambda picking: picking.state not in ("cancel", "done")
        )
        weight = 0
        for each_pick in pickings:
            weight += each_pick.shipping_weight
            if weight == 0:
                for move in each_pick.move_ids:
                    weight += move.product_qty * move.product_id.weight
        return weight

    def action_open_batch_delivery_stock_wizard(self):
        if not self.custom_carrier_id:
            raise ValidationError(_("Carrier required for this operation"))
        if (
            not self.custom_journal_id
            and self.custom_sale_payment_term_id.name == "PrePayment"
        ):
            raise ValidationError(_("Bank Journal required for this operation"))

        pickings = self.mapped("picking_ids").filtered(
            lambda picking: picking.state not in ("cancel", "done")
        )
        if pickings:
            for each_pick in pickings:
                each_pick.write({"carrier_id": self.custom_carrier_id.id})
                if each_pick.custom_gift_mess:
                    if not each_pick.custom_gift_label_print:
                        raise ValidationError(
                            _("Please print gift label first for %s", each_pick.name)
                        )
                each_pick.action_open_delivery_stock_wizard()

        if self.custom_sale_payment_term_id.name == "PrePayment":
            delivery_state_list = []
            for each_pick in pickings:
                delivery_state_list.append(each_pick.state)

            if self.custom_auto_pay_limit < self.custom_sale_total_amount:
                self.state = "invoice_sent"
            else:
                if any(state in ["invoice_sent"] for state in delivery_state_list):
                    self.state = "invoice_sent"
                elif any(
                    state in ["ready_to_be_sent"] for state in delivery_state_list
                ):
                    self.state = "ready_to_be_sent"
        else:
            self.state = "ready_to_be_sent"

        return True

    def action_register_payment_batch_delivery_custom(self):
        pickings = self.mapped("picking_ids").filtered(
            lambda picking: picking.state not in ("cancel", "done")
        )
        if pickings:
            for each_pick in pickings:
                invoice_id = self.env["account.move"].search(
                    [("invoice_origin", "=", each_pick.sale_id.name)], limit=1
                )
                payment_vals = {
                    "payment_type": "inbound",
                    "partner_type": "customer",
                    "can_edit_wizard": True,
                    "partner_id": invoice_id.partner_id.id,
                    "amount": invoice_id.amount_total,
                    "payment_date": fields.Date.today(),
                    "journal_id": self.custom_journal_id.id,
                }
                wizard = (
                    self.env["account.payment.register"]
                    .with_context(
                        active_model="account.move",
                        active_ids=invoice_id.ids,
                        dont_redirect_to_payments=True,
                        display_account_trust=True,
                    )
                    .create(payment_vals)
                )
                wizard._create_payments()
        self.state = "ready_to_be_sent"

    # wave transfer gift card report action
    def action_download_delivery_gift_label(self):
        self.ensure_one()
        xml_id = "custom_dropstitch.action_report_wt_gift_label_print"
        if not xml_id:
            raise UserError(
                _("Unable to find report template for %s format", self.print_format)
            )
        for picking_id in self.picking_ids:
            picking_id.custom_gift_label_print = True
        report = self.env.ref(xml_id).report_action(self)
        return report

    def _compute_show_gift_label(self):
        for rec in self:
            is_show_gift_lable_action = False
            for picking in self.picking_ids:
                if picking.custom_gift_mess and not picking.custom_gift_mess.isspace():
                    is_show_gift_lable_action = True
            rec.is_show_gift_lable_action = is_show_gift_lable_action

    @api.onchange("custom_carrier_tracking_ref")
    def on_change_tracking_referece(self):
        for record in self:
            for move in record.move_ids:
                move.picking_id.carrier_tracking_ref = (
                    record.custom_carrier_tracking_ref
                )

    def _get_report_lang(self):
        return self.picking_ids and self.picking_ids[0].partner_id.lang or self.picking_ids.lang or self.env.lang
    
    def action_done(self):
        for wave in self:
            for picking in wave.picking_ids:
                picking.carrier_id = ""
        res = super(StockPickingBatch, self).action_done()
        if self.custom_carrier_id.delivery_type == "fedex_rest":
            self.custom_carrier_id.fedex_rest_send_shipping_wave(self)
        elif self.custom_carrier_id.delivery_type == "ups_rest":
            self.custom_carrier_id.ups_rest_send_shipping_wave(self)
        return res
    
    @api.depends('picking_ids')
    def _compute_custom_available_carrier(self):
        for rec in self:
            partner_id = False
            for picking in rec.picking_ids:
                partner_id = picking.sale_id.partner_id
                break
            carriers = self.env['delivery.carrier'].search(self.env['delivery.carrier']._check_company_domain(rec.company_id))
            carriers = carriers.filtered(lambda carrier: carrier.custom_hide_for_sel == False)
            carriers_non_shipstation = carriers.filtered(lambda carrier: carrier.delivery_type != 'shipstation_ept')
            if partner_id and partner_id.custom_allowed_shipping_ids:
                rec.custom_available_carrier_ids = partner_id.custom_allowed_shipping_ids
            else:
                rec.custom_available_carrier_ids = carriers_non_shipstation