# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tests import Form
from markupsafe import Markup

import threading
import logging
import time

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    custom_delivery_set = fields.Boolean(compute="_compute_delivery_state_custom")
    custom_invoice_state = fields.Char(compute="_compute_invoice_state_custom")
    custom_invoice_payment_state = fields.Char(
        compute="_compute_invoice_payment_state_custom"
    )
    custom_invoice_move_type = fields.Char(compute="_compute_invoice_move_type_custom")
    custom_client_order_ref = fields.Char(
        related="sale_id.client_order_ref", string="Customer Ref"
    )
    carrier_id = fields.Many2one(
        "delivery.carrier", string="Carrier", check_company=True, copy=False
    )
    custom_order_policy = fields.Selection(
        related="sale_id.custom_policy", string="Invoice Policy"
    )
    custom_order_payment_term = fields.Char(
        related="sale_id.payment_term_id.name", string="Payment Term"
    )
    custom_gift_mess = fields.Html(
        related="sale_id.custom_gift_mess", string="Gift Message"
    )
    custom_gift_label_print = fields.Boolean("Printed Gift Label ?")
    custom_shipping_label_name = fields.Char(string="Customer Shipping Label Name")
    custom_shipping_label = fields.Binary(string="Customer Shipping Label")
    
    custom_packing_list_name = fields.Char(string="Customer Packing List Name")
    custom_packing_list = fields.Binary(string="Customer Packing List")

    state = fields.Selection(
        selection_add=[
            ("invoice_sent", "Invoice Sent"),
            ("ready_to_be_sent", "Ready to be Sent"),
            ("done",),
        ]
    )
    carrier_tracking_ref = fields.Char(
        string="Tracking Reference", copy=False, tracking=True
    )
    custom_auto_export_to_shipstation = fields.Boolean("Auto Export to Shipstation", default=False, tracking=True)
    custom_so_special_inst = fields.Html("Customer Special Instruction", related="sale_id.custom_so_special_inst")
    custom_customer_name = fields.Char("Customer Name", related="sale_id.partner_id.name")
    custom_customer_id = fields.Many2one('res.partner', "Customer", related="sale_id.partner_id")
    amount_residual = fields.Float(string="Balance Due", compute="_compute_amount_residual")
    order_line_ref = fields.Char(string="Order Line Ref", compute="_compute_order_line_ref")

    def _compute_order_line_ref(self):
        for picking in self:
            picking.order_line_ref = False
            order_lines = picking.sale_id.order_line
            line_refs = []
            for line in order_lines:
                if line.custom_order_no:
                    line_refs.append(line.custom_order_no)
            if line_refs:
                picking.order_line_ref = ', '.join(line_refs)

    def _compute_amount_residual(self):
        for picking in self:
            invoices = self.env['account.move'].search([('invoice_origin', '=', picking.sale_id.name)])
            picking.amount_residual = sum(invoices.mapped('amount_residual'))

    def _compute_delivery_state_custom(self):
        for picking in self:
            if picking.sale_id.shopify_instance_id:
                if picking.carrier_id:
                    picking.custom_delivery_set = True
                else:
                    picking.custom_delivery_set = False
            else:
                picking.custom_delivery_set = False
                for line in picking.sale_id.order_line:
                    if line.is_delivery:
                        picking.custom_delivery_set = True
                        break

    def _compute_invoice_state_custom(self):
        for picking in self:
            self.custom_invoice_state = (
                self.env["account.move"]
                .search([("invoice_origin", "=", picking.sale_id.name)], limit=1)
                .state
            )

    def _compute_invoice_payment_state_custom(self):
        for picking in self:
            self.custom_invoice_payment_state = (
                self.env["account.move"]
                .search([("invoice_origin", "=", picking.sale_id.name)], limit=1)
                .payment_state
            )

    def _compute_invoice_move_type_custom(self):
        for picking in self:
            self.custom_invoice_move_type = (
                self.env["account.move"]
                .search([("invoice_origin", "=", picking.sale_id.name)], limit=1)
                .move_type
            )

    def _get_intent_estimated_weight(self):
        self.ensure_one()
        weight = self.shipping_weight
        if weight == 0:
            for move in self.move_ids:
                weight += move.product_qty * move.product_id.weight
        return weight

    def action_open_delivery_stock_wizard(self):
        done_qty = 0
        for move_lines in self.move_ids_without_package:
            done_qty = done_qty + move_lines.quantity
        if done_qty <= 0:
            raise ValidationError(_("Please add Done Qty!"))
        if self.custom_gift_mess:
            if not self.custom_gift_label_print:
                raise ValidationError(_("Kindly print gift label as a first step"))
        view_id = self.env.ref("delivery.choose_delivery_carrier_view_form").id
        new_context = dict(self.env.context)
        new_context.update({"sale_order_id": self.sale_id})

        custom_hide_button = False
        order_id = self.sale_id
        shipstation_service_id = False
        shipstation_carrier_id = False

        #if self.sale_id.shopify_instance_id:
        #    custom_hide_button = True

        if self.carrier_id and self.batch_id:
            if order_id:
                if self.carrier_id.get_cheapest_rates:
                    shipstation_service_id = order_id.cheapest_service_id.id or False
                    shipstation_carrier_id = order_id.cheapest_carrier_id.id or False
                else:
                    shipstation_service_id = (
                        self.carrier_id.shipstation_service_id.id or False
                    )
                    shipstation_carrier_id = (
                        self.carrier_id.shipstation_carrier_id.id or False
                    )
            carrier_dict_update = {
                "carrier_id": self.carrier_id.id,
            }
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=self.sale_id.id,
                default_carrier_id=self.carrier_id,
                default_total_weight=self._get_intent_estimated_weight(),
                default_custom_hide_button=custom_hide_button,
                default_custom_picking_id=self.id,
            ).create(carrier_dict_update).button_confirm()
            
            return True

        self.env.context = new_context
        carrier_ids = self.env["delivery.carrier"].search([])
        if carrier_ids:
            name = _("Update Shipping Cost")
            carrier = self.carrier_id
            if self.sale_id and self.sale_id.partner_id.property_delivery_carrier_id:
                carrier = self.sale_id.partner_id.property_delivery_carrier_id
        else:
            raise UserError(_("Unable to find Shipping Method"))
        if self.shipping_weight > 18.5 and carrier.delivery_type == "shipstation_ept":
            secondary_default_carrier = self.env["delivery.carrier"].search(
                [("custom_secondary_default_carrier", "=", True)], limit=1
            )
            if secondary_default_carrier:
                carrier = secondary_default_carrier
        return {
            "name": name,
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "choose.delivery.carrier",
            "view_id": view_id,
            "views": [(view_id, "form")],
            "target": "new",
            "context": {
                "default_order_id": self.sale_id.id,
                "default_carrier_id": carrier.id,
                "default_total_weight": self._get_intent_estimated_weight(),
                "default_custom_hide_button": custom_hide_button,
                "default_custom_picking_id": self.id,
            },
        }

    def action_register_payment_custom(self):
        invoice_id = self.env["account.move"].search(
            [("invoice_origin", "=", self.sale_id.name)], limit=1
        )
        return {
            "name": _("Register Payment"),
            "res_model": "account.payment.register",
            "view_mode": "form",
            "views": [[False, "form"]],
            "context": {
                "active_model": "account.move.line",
                "active_ids": invoice_id.line_ids.ids,
            },
            "target": "new",
            "type": "ir.actions.act_window",
        }

    def custom_validate_validation(self, back_order_flag=False):
        if (
            self.picking_type_code == "outgoing"
        ):
            move_line_ids = self._package_move_lines()
            if move_line_ids:
                raise UserError(_("Kindly process the operation 'Put in Pack'"))
            
        if (
            self.picking_type_code == "outgoing"
            and self.sale_id.custom_policy == "intent"
            and not self.is_shopify_delivery_order
        ):
            if not self.carrier_id or not self.custom_delivery_set:
                if not self.batch_id:
                    raise UserError(
                        _(
                            "Unable to Validate - Delivery Cost needs to be added as a pre-requisite"
                        )
                    )
            elif self.custom_invoice_move_type != "out_invoice":
                raise UserError(_("Unable to Validate - Invoice Type not Valid"))
            elif (
                self.custom_invoice_payment_state in ("not_paid", "partial")
                and self.sale_id.payment_term_id.name == "PrePayment"
            ):
                raise UserError(
                    _(
                        "Unable to Validate - Invoice needs to be paid as a pre-requisite"
                    )
                )
            elif self.custom_invoice_state != "posted":
                raise UserError(
                    _("Unable to Validate - Invoice Status Should be Posted!")
                )
            else:
                if self.state == "ready_to_be_sent" and not self.batch_id:
                    diff_qty = {
                        move: move.product_uom_qty - move.quantity
                        for move in self.move_ids
                    }
                    for move, diff in diff_qty.items():
                        if diff != 0:
                            back_order_flag = True
                            break
                    if back_order_flag:
                        wiz = self.with_context(
                            default_show_transfers=False
                        ).button_validate()
                        wiz = Form(
                            self.env["stock.backorder.confirmation"].with_context(
                                wiz["context"]
                            )
                        ).save()
                        wiz.with_context(
                            button_validate_picking_ids=[self.id],
                            default_show_transfers=False,
                        ).process()
        return back_order_flag

    def button_validate(self):
        back_order_flag = False
        if "default_show_transfers" in self.env.context:
            res = super().button_validate()
            return res
        for picking in self:
            back_order_flag = False
            if not picking.location_dest_id.is_subcontracting_location:
                back_order_flag = picking.custom_validate_validation(back_order_flag)
        if not back_order_flag:
            return super(Picking, self).button_validate()

    def _action_done(self):
        """
        Method overridden from shopify
        """
        result = super(Picking, self)._action_done()
        for picking in self:
            if picking.sale_id.invoice_status == "invoiced":
                continue
            order = picking.sale_id
            work_flow_process_record = order and order.auto_workflow_process_id
            # delivery_lines = picking.move_line_ids.filtered(lambda l: l.product_id.invoice_policy == 'delivery')
            delivery_lines = picking.move_line_ids.filtered(
                lambda l: l.picking_id.sale_id.custom_policy in ("delivery", "intent")
            )

            if (
                work_flow_process_record
                and delivery_lines
                and work_flow_process_record.create_invoice
                and picking.location_dest_id.usage == "customer"
            ):
                order.validate_and_paid_invoices_ept(work_flow_process_record)
        return result

    def _action_create_invoice_and_payment(self, sale_order_obj):
        check_autopaylimit = True
        template = self.env.ref(
            "account.email_template_edi_invoice", raise_if_not_found=False
        )
        saved_payment_token = self.env["payment.token"].search(
            [("partner_id", "=", sale_order_obj.partner_id.id)], limit=1
        )
        if self.batch_id:
            if (
                self.batch_id.custom_auto_pay_limit
                < self.batch_id.custom_sale_total_amount
            ):
                check_autopaylimit = False

        invoice = (
            self.env["sale.advance.payment.inv"]
            .with_context(
                {
                    "active_model": "sale.order",
                    "active_id": sale_order_obj.id,
                }
            )
            .create(
                {
                    "advance_payment_method": "delivered",
                }
            )
            ._create_invoices(sale_order_obj)
        )
        invoice.with_context(order=self.move_ids.created_production_id, custom_notify=True).action_post()
        invoice.with_context(custom_notify=True)._generate_pdf_and_send_invoice(template=template)

        if (
            saved_payment_token
            and sale_order_obj.payment_term_id.name == "PrePayment"
            and sale_order_obj.partner_id.custom_auto_pay_limit
            > sale_order_obj.amount_total
            and check_autopaylimit
        ):
            account_payment_method_line = self.env[
                "account.payment.method.line"
            ].search(
                [("payment_provider_id", "=", saved_payment_token.provider_id.id)],
                limit=1,
            )
            payment_vals = {
                "payment_type": "inbound",
                "partner_type": "customer",
                "can_edit_wizard": True,
                "payment_method_code": account_payment_method_line.code,
                "partner_id": invoice.partner_id.id,
                "amount": invoice.amount_total,
                "payment_date": fields.Date.today(),
                "journal_id": self.env["account.journal"]
                .search([("type", "=", "bank")], limit=1)
                .id,
                "payment_method_line_id": account_payment_method_line.id,
                "payment_token_id": saved_payment_token.id,
            }
            wizard = (
                self.env["account.payment.register"]
                .with_context(
                    active_model="account.move",
                    active_ids=invoice.ids,
                    dont_redirect_to_payments=True,
                    display_account_trust=True,
                )
                .create(payment_vals)
            )
            wizard._create_payments()
            sale_order_obj.write({"invoice_status": "invoiced"})
        if (
            sale_order_obj.payment_term_id.name == "PrePayment"
            and sale_order_obj.partner_id.custom_auto_pay_limit
            < sale_order_obj.amount_total
        ):
            self.write({"state": "invoice_sent"})
        if sale_order_obj.payment_term_id.name != "PrePayment" or sale_order_obj.amount_total == 0:
            self.write({"state": "ready_to_be_sent"})
        if sale_order_obj.shopify_order_id:
            self.write({"state": "ready_to_be_sent"})

    def action_download_gift_label(self):
        self.ensure_one()
        xml_id = "custom_dropstitch.action_report_gift_label_print"
        if not xml_id:
            raise UserError(
                _("Unable to find report template for %s format", self.print_format)
            )
        report = self.env.ref(xml_id).report_action(self)
        self.custom_gift_label_print = True
        return report

    @api.returns("mail.message", lambda value: value.id)
    def message_post(self, **kwargs):
        body = kwargs.get("body")
        attachments = kwargs.get("attachments")
        if attachments and body and self.contains_words(["UPS", "fedex", "USPS"], body):
            if self.batch_id and not self.batch_id.is_shipping_lebel_generated:
                self.batch_id.message_post(**kwargs)
                self.batch_id.is_shipping_lebel_generated = True
        return super(Picking, self).message_post(**kwargs)

    def contains_words(self, word_list, string):
        return any(word in string for word in word_list)

    def export_order_to_shipstation(self, log_line=False):
        """
        This method is used to export the orders to shipstation.
        """
        "Custom code start"
        for picking in self:
            picking.custom_validate_validation(False)
        "Custom code end"

        if self.state not in ["assigned", "ready_to_be_sent"]:
            raise UserError(
                "Picking {} must be in ready state for export order to shipstation.".format(
                    self.name
                )
            )
        # if not self.carrier_id:
        #     raise UserError("Need to select Carrier in Picking for export order to shipstation.")
        self.is_picking_contains_store()

        model_id = self.env["ir.model"].sudo().search([("model", "=", self._name)]).id

        total_amount, tax_amount, shipping_amount, shipping_tax = 0, 0, 0, 0
        shipstation_instance = self.shipstation_store_id.shipstation_instance_id
        shipping_line = self.sale_id.order_line.filtered(lambda x: x.is_delivery)
        order_data = self.prepare_order_export_data()
        msg = isinstance(order_data, str) and order_data or ""

        exported_picking = self.get_exported_pickings()
        if not exported_picking:
            shipping_amount = self.convert_amount_to_company_currency(
                sum(shipping_line.mapped("price_subtotal"))
            )
            shipping_tax = self.convert_amount_to_company_currency(
                sum(shipping_line.mapped("price_tax"))
            )

        # Prepare order lines data
        process_lines = []
        line_list = []
        for line in self.move_ids.filtered(lambda move: move.quantity > 0):
            sale_line = line.sale_line_id
            line_data, sale_total_data = self.prepare_line_export_data(
                sale_line, move_id=line, process_lines=process_lines
            )

            msg += (
                isinstance(line_data, str) and not sale_total_data and line_data or ""
            )
            if msg:
                if self.exception_counter >= 3 and self._context.get("from_cron"):
                    self.message_post(
                        body="Export Order Cron Failed as Exception has already "
                        "been generated for 3 times while Processing this Picking."
                    )
                else:
                    self.message_post(
                        body="Following parameters are missing, when order exported to shipstation: "
                        + msg
                    )

                if self._context.get("from_cron"):
                    self.exception_counter += 1
                return

            if not line_data:
                return False
            process_lines.append(sale_line.id)
            line_list += line_data
            line.write({"shipstation_exported_qty": line.quantity})
            total_amount += sale_total_data.get("total", 0)
            tax_amount += sale_total_data.get("tax", 0)

        order_data.update(
            {
                "orderStatus": "awaiting_shipment",
                "amountPaid": total_amount
                + shipping_tax
                + shipping_amount
                + tax_amount,
                "taxAmount": tax_amount + shipping_tax,
                "shippingAmount": shipping_amount,
                "items": line_list,
                "requestedShippingService": self.carrier_id.shipstation_carrier_code
                or self.carrier_id.name,
            }
        )
        response, code = shipstation_instance.get_connection(
            url="/orders/createorder", data=order_data, method="POST"
        )
        if code.status_code != 200:
            try:
                res = json.loads(code.content.decode("utf-8")).get("ExceptionMessage")
            except:
                res = code.content.decode("utf-8")

            msg = (
                "106: Something went wrong while exporting order to ShipStation.\n\n %s",
                res,
            )
            _logger.exception(msg)
            if not self._context.get("from_delivery_order", True):
                if self.exception_counter >= 3 and self._context.get("from_cron"):
                    self.message_post(
                        body="Export Order Cron Failed as Exception has already "
                        "been generated for 3 times while Processing this Picking."
                    )
                else:
                    self.message_post(body=msg)

                if self._context.get("from_cron"):
                    self.exception_counter += 1
                return
            else:
                raise UserError(msg)

        msg = (
            "Order exported to ShipStation."
            + Markup("<br/>")
            + "ShipStation order id : %s" % (response.get("orderId"))
        )
        self.unlink_old_message_and_post_new_message(body=msg)
        self.write(
            {
                "shipstation_order_id": response.get("orderId"),
                "is_exported_to_shipstation": True,
            }
        )

        # Update related outgoing picking in case of Multi-Step Routes
        is_multi_step = (
            True
            if self.picking_type_id.warehouse_id.delivery_steps
            in ("pick_ship", "pick_pack_ship")
            else False
        )
        if is_multi_step:
            int_picks = self.get_internal_pickings()
            int_picks.write({"related_outgoing_picking": self.id})
        log_line = self.env["common.log.lines.ept"]
        log_line.create_common_log_line_ept(
            message="Order Exported successfully",
            operation_type="export",
            model_id=model_id,
            res_id=self.id,
            module="shipstation_ept",
            log_line_type="success",
        )
        return True

    def check_for_auto_delivery(self):
        if self.location_dest_id.is_subcontracting_location:
            return False
        done_qty = 0
        for move_lines in self.move_ids_without_package:
            done_qty = done_qty + move_lines.quantity
        if done_qty <= 0:
            return False
        elif self.custom_gift_mess:
            if not self.custom_gift_label_print:
                return False
            elif self.carrier_id:
                if self.state == 'ready_to_be_sent':
                    return False
                else:
                    return True
            else:
                return False
        else:
            if self.carrier_id:
                if self.state == 'ready_to_be_sent':
                    return False
                else:
                    return True
            else:
                return False
    
    def check_for_auto_export(self):
        done_qty = 0
        if self.location_dest_id.is_subcontracting_location:
            return False
        if self.carrier_id and self.carrier_id.delivery_type == "shipstation_ept":
            for move_lines in self.move_ids_without_package:
                done_qty = done_qty + move_lines.quantity
            if done_qty <= 0:
                return False
            elif self.custom_gift_mess:
                if not self.custom_gift_label_print:
                    return False
                elif self.carrier_id:
                    if self.state == 'ready_to_be_sent' and self.export_order and not self.is_exported_to_shipstation:
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                if self.carrier_id:
                    if self.state == 'ready_to_be_sent' and self.export_order and not self.is_exported_to_shipstation:
                        return True
                    else:
                        return True
                else:
                    return False
        else:
            return False

    def action_open_delivery_stock_thread(self):
        time.sleep(2)
        with self.pool.cursor() as new_cr:
            self = self.with_env(self.env(cr=new_cr))
            self.action_open_delivery_stock_wizard()
    
    def action_check_for_auto_export(self):
        time.sleep(1)
        with self.pool.cursor() as new_cr:
            self = self.with_env(self.env(cr=new_cr))
            _logger.info("Exporting picking %s to shipstation - Auto", self.name)
            if not self.location_dest_id.is_subcontracting_location:
                self.export_order_to_shipstation()
    
    def _track_subtype(self, init_values):
        # EXTENDS mail mail.thread
        # add custom subtype depending of the state.
        self.ensure_one()

        _logger.info("Track Sub-Type")
        if self.state in ['assigned'] and self.picking_type_id.code == 'outgoing':
            _logger.info("Auto-Delivery Check - Assigned")
            if self.check_for_auto_delivery():
                _logger.info("Auto-Delivery Initiated - Assigned")
                threading.Thread(target=self.action_open_delivery_stock_thread).start()
        elif self.state in ['ready_to_be_sent'] and self.picking_type_id.code == 'outgoing':
             _logger.info("Auto-Delivery Check - Ready to Sent")
             if self.check_for_auto_export():
                 _logger.info("Auto-Delivery Initiated - Ready to Sent")
                 threading.Thread(target=self.action_check_for_auto_export).start()
        
        return super()._track_subtype(init_values)

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create method to set default values for custom fields.
        """
        pickings = super(Picking, self).create(vals_list)
        for picking in pickings:
            subscribe_partners = picking.partner_id._get_notify_partner_ids('custom_shipping_confirmation_ids', picking)
            if subscribe_partners and (picking.partner_id.custom_shipping_confirmation_ids.ids or picking.shopify_instance_id.id):
                picking.message_subscribe(partner_ids=subscribe_partners)
        return pickings
    
    def get_converted_weight_for_shipstation(self, weight=0):
        return self.carrier_id.convert_weight_for_shipstation(self.company_id.get_weight_uom_id(),
                                                              self.shipstation_instance_id.weight_uom_id,
                                                              weight or self.shipping_weight)

    def _send_confirmation_email(self):
        if not self.shopify_instance_id and not self.partner_id.custom_shipping_confirmation_ids:
            return False
        return super()._send_confirmation_email()