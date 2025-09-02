# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.sale.models.sale_order_line import SaleOrderLine
from odoo.tools.json import scriptsafe as json_scriptsafe
import logging
import json
import logging
from datetime import datetime, timedelta
import time
import pytz  
from odoo.addons.shopify_ept import shopify 
_logger = logging.getLogger(__name__)

sel_custom_label_type = [
    ("na", "N/A"),
    ("cust_label", "Customer Label"),
    ("biquette_label", "Biquette Label"),
    ("no_label", "No Label"),
    ("alc_cust_label", "Alcantara Customer Label"),
]

sel_custom_bag_info = [
    ("plastic_bag", "Plastic Bag"),
    ("no_bag", "No Bag"),
    ("cust_bag", "Customer Brand Bag"),
    ("biquette_bag", "Biquette bag"),
    ("mineola_bag", "Mineola Bag"),
]

sel_custom_label_placement = [
    ("na", "N/A"),
    ("front_right", "Front Right (Low)"),
    ("front_left", "Front left (Low)"),
    ("back_right", "Back Right (Low)"),
    ("back_left", "Back Left (Low)"),
    ("back_left_top", "Back Left (Top)"),
    ("fold_right_low", "Fold Around (Right Low)"),
]

sel_custom_box_info = [("one_unit_box", "1 Unit Box"), ("bulk", "Bulk Box")]

sel_shipping_fees = [
    ("charge_fees", "Charge Shipping Fees"),
    ("no_fees", "No Shipment Fees"),
]


class CustomSaleOrder(models.Model):
    _inherit = "sale.order"

    custom_label_type = fields.Selection(
        sel_custom_label_type, string="Label Type", tracking=True
    )
    custom_label_placement = fields.Selection(
        sel_custom_label_placement, string="Label Placement", tracking=True
    )
    custom_bag_info = fields.Selection(
        sel_custom_bag_info, string="Bag Info", tracking=True
    )
    custom_box_info = fields.Selection(
        sel_custom_box_info, string="Box Info", tracking=True
    )
    custom_shipping_fees = fields.Selection(
        sel_shipping_fees, string="Shipping Fees", default="charge_fees", tracking=True
    )

    custom_brand_label = fields.Integer("Brand Label", tracking=True)
    custom_care_label = fields.Integer("Care Label", tracking=True)

    custom_instruction = fields.Char(
        "Label Special Instruction", size=80, tracking=True
    )
    custom_pack_instr = fields.Char("Packaging Instruction", size=80, tracking=True)

    custom_label_image = fields.Binary(string="Label Image")
    custom_allowed_customer_ids = fields.Many2many(
        "res.partner",
        compute="_compute_allowed_customer_ids",
        string="Allowed Customers",
    )
    custom_gift_mess = fields.Html("Gift Message", copy=False)
    custom_so_special_inst = fields.Html("Customer Special Instruction", copy=False)

    custom_policy = fields.Selection(
        [
            ("products", "Based on Products"),
            ("order", "Based on Order Quantity"),
            ("delivery", "Based on Delivered Quantity"),
            ("intent", "Based on Intent"),
        ],
        default="products",
        string="Invoicing Policy",
        tracking=True,
    )
    custom_import_id = fields.Many2one(
        "custom.order.processing.import", string="Order Import", copy=False
    )
    custom_dropship_order = fields.Boolean(
        string="Dropship",
        tracking=True,
        copy=False
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        results = super().create(vals_list)
        for res in results:
            if res.partner_id.shipstation_store_id:
                shipstation_store_id = res.partner_id.shipstation_store_id
                res.update({
                    'shipstation_store_id': shipstation_store_id.id,
                    'shipstation_instance_id': shipstation_store_id.shipstation_instance_id.id
                })
        return results
    
    @api.depends("partner_id", "state", "shopify_order_id", "payment_term_id")
    def _compute_is_drop_ship_product(self):
        payment_term = self.env.ref("account.account_payment_term_immediate")
        if self.shopify_order_id or self.state in ['sale', 'cancel']:
            self.custom_hide_register_button = True
        elif not self.payment_term_id:
            self.custom_hide_register_button = False
        elif payment_term == self.payment_term_id: 
            self.custom_hide_register_button = False
        else:
            self.custom_hide_register_button = True

    custom_hide_register_button = fields.Boolean(
        string="Hide Register Button",
        compute="_compute_is_drop_ship_product",
        store=False
    )
    custom_from = fields.Char("From", size=80, tracking=True, copy=False)
    partial_pay_amount = fields.Float(string="Down-Payment Amount", copy=False)
    
    @api.depends("company_id")
    def _compute_require_payment(self):
        for order in self:
            if order.partner_id.custom_require_payment:
                order.require_payment = order.partner_id.custom_require_payment
            else:
                order.require_payment = order.company_id.portal_confirmation_pay

    @api.depends("require_payment")
    def _compute_prepayment_percent(self):
        for order in self:
            if order.partner_id.custom_require_payment:
                order.prepayment_percent = order.partner_id.custom_prepayment_percent
            else:
                order.prepayment_percent = order.company_id.prepayment_percent

    @api.onchange("partner_id")
    def _compute_allowed_customer_ids(self):
        for order in self:
            if order.partner_id:
                order.custom_allowed_customer_ids = (
                    order.partner_id.custom_allowed_customer_ids
                )
            else:
                order.custom_allowed_customer_ids = []
    
    @api.onchange("payment_term_id","state")
    def _compute_hide_register_button(self):
        for order in self:
            payment_term = self.env.ref("account.account_payment_term_immediate")
            if order.state in ['sale', 'cancel']:
                order.custom_hide_register_button = True
            elif not order.payment_term_id:
                order.custom_hide_register_button = False
            elif payment_term != order.payment_term_id: 
                order.custom_hide_register_button = True
            else:
                order.custom_hide_register_button = False

    @api.onchange("partner_id")
    def _onchange_custom_partner_id(self):
        for order in self:
            order.custom_label_type = order.partner_id.custom_label_type
            order.custom_label_placement = order.partner_id.custom_label_placement
            order.custom_bag_info = order.partner_id.custom_bag_info
            order.custom_box_info = order.partner_id.custom_box_info

            order.custom_brand_label = order.partner_id.custom_brand_label
            order.custom_care_label = order.partner_id.custom_care_label

            order.custom_instruction = order.partner_id.custom_instruction
            order.custom_pack_instr = order.partner_id.custom_pack_instr

            order.custom_label_image = order.partner_id.custom_label_image
            order.prepayment_percent = order.partner_id.custom_prepayment_percent
            order.require_payment = order.partner_id.custom_require_payment
            order.custom_policy = order.partner_id.custom_policy
            order.custom_shipping_fees = order.partner_id.custom_shipping_fees
            order.custom_dropship_order = order.partner_id.custom_dropship_order

    def _prepare_order_line_values(
        self,
        product_id,
        quantity,
        linked_line_id=False,
        no_variant_attribute_values=None,
        product_custom_attribute_values=None,
        **kwargs,
    ):
        values = super()._prepare_order_line_values(
            product_id,
            quantity,
            linked_line_id,
            no_variant_attribute_values,
            product_custom_attribute_values,
            **kwargs,
        )
        product = self.env["product.product"].browse(product_id)
        if product.custom_prod_type == "pre_set":
            received_no_variant_values = product.env[
                "product.template.attribute.value"
            ].browse([int(ptav["value"]) for ptav in no_variant_attribute_values])

            values["custom_item_image"] = product.image_1920
         
        combination = [int(ptav['value'])for ptav in no_variant_attribute_values]
        design_attribute = (self.env["product.template.attribute.value"].sudo().browse(combination).filtered(lambda a: a.attribute_id.is_special_mto_attr))
        yarn_attrib_ids = (self.env["product.template.attribute.value"].sudo().browse(combination).filtered(lambda a: a.attribute_id.show_yarn_component_image))
        if yarn_attrib_ids and len(yarn_attrib_ids):
            if design_attribute and 'custom_item_image' not in values.keys():
                values['custom_item_image'] = design_attribute.product_attribute_value_id.custom_design_image
        return values

    def prepare_shopify_order_vals(
        self,
        instance,
        partner,
        shipping_address,
        invoice_address,
        order_response,
        payment_gateway,
        workflow,
    ): 
        order_vals = super(CustomSaleOrder, self).prepare_shopify_order_vals(
            instance,
            partner,
            shipping_address,
            invoice_address,
            order_response,
            payment_gateway,
            workflow,
        )
        update_shopify_dict = {
            "custom_label_type": partner.custom_label_type,
            "custom_label_placement": partner.custom_label_placement,
            "custom_bag_info": partner.custom_bag_info,
            "custom_box_info": partner.custom_box_info,
            "custom_brand_label": partner.custom_brand_label,
            "custom_care_label": partner.custom_care_label,
            "custom_instruction": partner.custom_instruction,
            "custom_pack_instr": partner.custom_pack_instr,
            "custom_label_image": partner.custom_label_image,
            "custom_policy": instance.custom_policy,
            "payment_term_id": instance.custom_sale_payment_term_id.id,
            "custom_dropship_order": True,
        }
        
        order_vals.update(update_shopify_dict)
        
        mapped_tag_ids = instance.custom_tag_invoice_ids.mapped("custom_tags").ids
        order_tag_ids = order_vals.get("tag_ids", [])
        matching_tags = set(order_tag_ids).intersection(set(mapped_tag_ids))
        
        if matching_tags:
            # find the mapped invoice partner(s)
            mapped_partner = instance.custom_tag_invoice_ids.filtered(
                lambda r: r.custom_tags.id in matching_tags
            ).custom_invoice_partner
    
            if mapped_partner:
                # override invoice partner on order
                order_vals["partner_invoice_id"] = mapped_partner.id

        return order_vals

    def prepare_vals_for_sale_order_line(self, product, product_name, price, quantity):
        line_vals = super(CustomSaleOrder, self).prepare_vals_for_sale_order_line(
            product, product_name, price, quantity
        )
        if line_vals:
            if product.custom_prod_type == "pre_set":
                line_vals.update({"custom_item_image": product.image_1920})
        return line_vals

    def _get_estimated_weight(self):
        self.ensure_one()
        weight = 0.0
        if self.custom_policy == "intent":
            for order_line in self.order_line.filtered(
                lambda l: l.product_id.type in ["product", "consu"]
                and not l.is_delivery
                and not l.display_type
                and l.qty_to_intent > 0
            ):
                weight += order_line.qty_to_intent * order_line.product_id.weight
        else:
            for order_line in self.order_line.filtered(
                lambda l: l.product_id.type in ["product", "consu"]
                and not l.is_delivery
                and not l.display_type
                and l.product_uom_qty > 0
            ):
                weight += order_line.product_qty * order_line.product_id.weight
        return weight

    def process_orders_and_invoices_ept(self):
        """
        Method overridden from shopify
        """
        for order in self:
            work_flow_process_record = order.auto_workflow_process_id
            if order.invoice_status == "invoiced":
                continue
            if work_flow_process_record.validate_order:
                order.validate_order_ept()
            # Start Himanshu
            # order_lines = order.mapped('order_line').filtered(lambda l: l.product_id.invoice_policy == 'order')
            order_lines = order.mapped("order_line").filtered(
                lambda l: l.order_id.custom_policy == "intent"
            )
            # End Himanshu
            if not order_lines.filtered(
                lambda l: l.product_id.type == "product"
            ) and len(order.order_line) != len(
                order_lines.filtered(
                    lambda l: l.product_id.type in ["service", "consu"]
                )
            ):
                continue
            # order.validate_and_paid_invoices_ept(work_flow_process_record)
            order.custom_shopify_register_payment(work_flow_process_record)
        return True

    def custom_shopify_register_payment(self,work_flow_process_record):
        payment_provider = self.env['payment.provider'].sudo().search([('name', '=', 'Wire Transfer')], limit=1)
        payment_method = self.env['payment.method'].sudo().search([('name', '=', 'Wire Transfer')], limit=1)
        payment_method_line_id = False
         
        if work_flow_process_record.journal_id:
            payment_method_line_id = work_flow_process_record.journal_id._get_available_payment_method_lines("inbound")
            payment_method = payment_method_line_id.payment_method_id
            if payment_method_line_id.payment_provider_id:
                payment_provider = payment_method_line_id.payment_provider_id

        payment_transaction = self.env['payment.transaction'].sudo().create({
            'reference': self.name,
            'provider_id': payment_provider and payment_provider.id,
            'payment_method_id': payment_method and payment_method.id,
            'sale_order_ids': [self.id],
            'partner_id': self.partner_id.id,
            'amount': self.amount_total,
            'currency_id': self.company_id.currency_id.id,
        })
        payment_transaction.state = 'done'
        
        # Check partial 
        payment = self.env['account.payment'].sudo().create({
            'amount': self.amount_total,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'journal_id': work_flow_process_record.journal_id and work_flow_process_record.journal_id.id,
            'partner_id': self.partner_id.id,
            'payment_transaction_id': payment_transaction and payment_transaction.id,
            'payment_method_line_id': payment_method_line_id and payment_method_line_id.id,
        })
        payment.action_post()
        payment_transaction.payment_id = payment.id
        message = _("The payment related to the transaction with reference %(ref)s has been posted: %(link)s",
                ref=self.name, link=payment._get_html_link(),
            )
        self.message_post(body=message)
        # self.action_confirm()
        self.custom_hide_register_button = True
    
    def _action_cancel(self):
        result = super(CustomSaleOrder, self)._action_cancel()
        if result:
            for sale_order in self:
                for production_order in sale_order.mrp_production_ids:
                    if production_order.state in ["draft", "confirmed"]:
                        production_order.action_cancel()
                    elif production_order.state == "progress":
                        if self.env.user.has_group("mrp.group_mrp_manager"):
                            raise UserError(
                                _(
                                    "Kindly complete the 'In Progress' MO with manufactured quantity before canceling"
                                )
                            )
                        else:
                            raise UserError(
                                _(
                                    "Kindly reach out to user with Manufacturing/Admin role to proceed as a MO is in progress"
                                )
                            )
        return result

    def prepare_order_vals_from_order_response(
        self, order_response, instance, workflow, payment_gateway
    ):
        order_vals = super(
            CustomSaleOrder, self
        ).prepare_order_vals_from_order_response(
            order_response, instance, workflow, payment_gateway
        )
        if order_response.get("note"):
            custom_gift_mess = order_response.get("note")
            if custom_gift_mess.strip():
                # Split the string by newline characters
                lines = custom_gift_mess.split("\n")
                # Enclose each line with <p> and </p>
                result = "".join(f"<p>{line}</p>" for line in lines)
                order_vals.update({"custom_gift_mess": result})
        return order_vals

    def shopify_create_sale_order_line(
        self,
        line,
        product,
        quantity,
        product_name,
        price,
        order_response,
        is_shipping=False,
        previous_line=False,
        is_discount=False,
        is_duties=False,
    ):
        order_line = super(CustomSaleOrder, self).shopify_create_sale_order_line(
            line,
            product,
            quantity,
            product_name,
            price,
            order_response,
            is_shipping,
            previous_line,
            is_discount,
            is_duties,
        )
        if "properties" in line:
            if len(line["properties"]) > 0:
                route_obj = self.env.ref("custom_dropstitch.record_custom_route")
                route_id = route_obj.id if len(route_obj) else False

                personalize_1text = ""
                personalize_1text2 = ""
                personalize_1text3 = ""
                if "Shopify Collective Retailer" not in line["properties"][0]["name"]:
                    personalize_1 = line["properties"][0]["value"]
                    personalize_1text = "\nLine 1 :" + personalize_1
                    personalize_1text = order_line.name + personalize_1text
                    line_vals = {
                        "custom_line1": personalize_1,
                        "route_id": route_id,
                    }
                    if len(line["properties"]) > 1:
                        if "Shopify Collective Retailer" not in line["properties"][1]["name"]:
                            personalize_2 = line["properties"][1]["value"]
                            personalize_1text2 = "\nLine 2 :" + personalize_2
                            personalize_1text = personalize_1text + personalize_1text2
                            line_vals["custom_line2"] = personalize_2
                            if len(line["properties"]) > 2:
                                if "Shopify Collective Retailer" not in line["properties"][2]["name"]:
                                    personalize_3 = line["properties"][2]["value"]
                                    personalize_1text3 = "\nLine 3 :" + personalize_3
                                    personalize_1text = personalize_1text + personalize_1text3
                                    line_vals["custom_line3"] = personalize_3
                    line_vals["name"] = personalize_1text
                    order_line.write(line_vals)
        return order_line

    def action_confirm_orders(self):
        has_draft = False
        context = self._context.copy()
        if "params" in context:
            context.pop("params", None)
        if "active_id" in context:
            context.pop("active_id", None)
        for rec in self:
            if rec.state == "draft":
                has_draft = True
                rec.with_context(context).action_confirm()
        if not has_draft:
            raise UserError("Please select atleast one Quotation")
    
    def custom_client_order_ref(self, client_order_ref, custom_so_special_inst):
        self.sudo().client_order_ref = client_order_ref
        self.sudo().custom_so_special_inst = custom_so_special_inst

    # aspl partial payment
    def get_discount_amount(self):
        values = {} 
        partner_id = self.env.user.partner_id
        from_website_adv_payment_amount = float(self.env['ir.config_parameter'].sudo().get_param(
            'aspl_website_partial_payment_ee.adv_payment_amount'))
        if partner_id and partner_id.adv_payment_amount:
            adv_payment_amount = partner_id.adv_payment_amount
        else:
            adv_payment_amount = from_website_adv_payment_amount
        need_to_pay_amount = (self.amount_total * adv_payment_amount) / 100
        if partner_id.property_payment_term_id.id != self.env.ref("account.account_payment_term_immediate").id:
            need_to_pay_amount = 0

        return need_to_pay_amount
    
    def custom_action_confirm(self):
        for order in self:
            if order.shopify_order_id or order.payment_term_id.id != self.env.ref("account.account_payment_term_immediate").id:
                order.with_context(validate_analytic=True).action_confirm()
            else:
                payment_ids = self.env['payment.transaction'].sudo().search([('sale_order_ids', 'in', [order.id])])
                amount = 0
                downpayment = order.partner_id.custom_prepayment_percent
                downpayment_amount = order.amount_total * downpayment
                for payment_id in payment_ids:
                    amount = amount + payment_id.amount
                if amount >= downpayment_amount:
                    order.with_context(validate_analytic=True).action_confirm()
                else:
                    raise UserError("Waiting for %s Downpayment to proceed" % downpayment_amount)       
        return True
    
    def custom_register_payment(self):
        """Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        """      
        message_id = self.env["custom.order.payment"].create(
            {
                "custom_downpayment_amount": self.amount_total * self.prepayment_percent,
                "sale_order_id": self.id,
            }
        )
        return {
            "name": _("Message"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "custom.order.payment",
            # pass the id
            "res_id": message_id.id,
            "target": "new",
        }
    

    def import_shopify_orders(self, order_data_lines, instance):
        """
        This method used to create a sale orders in Odoo.
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 11/11/2019.
        Task Id : 157350
        @change: By Maulik Barad on Date 21-Sep-2020.
        @change: By Meera Sidapara on Date 27-Oct-2021 for Task Id : 179249.
        """
        order_risk_obj = self.env["shopify.order.risk"]
        common_log_line_obj = self.env["common.log.lines.ept"]
        order_ids = []
        commit_count = 0

        instance.connect_in_shopify()

        for order_data_line in order_data_lines:
            if commit_count == 5:
                self._cr.commit()
                commit_count = 0
            commit_count += 1
            order_data = order_data_line.order_data
            order_response = json.loads(order_data)

            order_number = order_response.get("order_number")
            shopify_financial_status = order_response.get("financial_status")
            _logger.info("Started processing Shopify order(%s) and order id is(%s)", order_number,
                         order_response.get("id"))

            date_order = self.convert_order_date(order_response)
            if str(instance.import_order_after_date) > date_order:
                message = "Order %s is not imported in Odoo due to configuration mismatch.\n Received order date is " \
                          "%s. \n Please check the order after date in shopify configuration." % (order_number,
                                                                                                  date_order)
                _logger.info(message)
                common_log_line_obj.create_common_log_line_ept(shopify_instance_id=instance.id, module="shopify_ept",
                                                               message=message,
                                                               model_name='sale.order',
                                                               order_ref=order_response.get("name"),
                                                               shopify_order_data_queue_line_id=order_data_line.id if order_data_line else False)
                order_data_line.write({'state': 'failed', 'processed_at': datetime.now()})
                continue

            sale_order = self.search_existing_shopify_order(order_response, instance, order_number)

            if sale_order:
                order_data_line.write({"state": "done", "processed_at": datetime.now(),
                                       "sale_order_id": sale_order.id, "order_data": False})
                _logger.info("Done the Process of order Because Shopify Order(%s) is exist in Odoo and Odoo order is("
                             "%s)", order_number, sale_order.name)
                continue

            pos_order = order_response.get("source_name", "") == "pos"
            partner, delivery_address, invoice_address = self.prepare_shopify_customer_and_addresses(
                order_response, pos_order, instance, order_data_line)
            if not partner:
                continue

            lines = order_response.get("line_items")
            if self.check_mismatch_details(lines, instance, order_number, order_data_line):
                _logger.info("Mismatch details found in this Shopify Order(%s) and id (%s)", order_number,
                             order_response.get("id"))
                order_data_line.write({"state": "failed", "processed_at": datetime.now()})
                continue

            sale_order = self.shopify_create_order(instance, partner, delivery_address, invoice_address,
                                                   order_data_line, order_response, lines, order_number)
            if not sale_order:
                message = "Configuration missing in Odoo while importing Shopify Order(%s) and id (%s)" % (
                    order_number, order_response.get("id"))
                _logger.info(message)
                common_log_line_obj.create_common_log_line_ept(shopify_instance_id=instance.id, module="shopify_ept",
                                                               message=message,
                                                               model_name='sale.order',
                                                               order_ref=order_response.get('name'),
                                                               shopify_order_data_queue_line_id=order_data_line.id if order_data_line else False)
                continue
            order_ids.append(sale_order.id)

            location_vals = self.set_shopify_location_and_warehouse(order_response, instance, pos_order, sale_order)

            if instance.is_delivery_multi_warehouse:
                warehouses = sale_order.order_line.filtered(lambda line_item: line_item.warehouse_id_ept).mapped(
                    'warehouse_id_ept')
                if warehouses and len(set(warehouses.ids)) == 1:
                    location_vals.update({"warehouse_id": warehouses.id})

            sale_order.write(location_vals)

            if sale_order.shopify_order_status != "fulfilled":
                risk_result = shopify.OrderRisk().find(order_id=order_response.get("id"))
                if risk_result:
                    order_risk_obj.shopify_create_risk_in_order(risk_result, sale_order)
                    risk = sale_order.risk_ids.filtered(lambda x: x.recommendation != "accept")
                    if risk:
                        sale_order.is_risky_order = True

            _logger.info("Starting auto workflow process for Odoo order(%s) and Shopify order is (%s)",
                         sale_order.name, order_number)
            message = ""
            try:
                context = dict(self.env.context)
                if not self._context.get('shopify_order_financial_status'):
                    context.update({'shopify_order_financial_status': order_response.get(
                        "financial_status")})
                context.update({'order_data_line': order_data_line})
                self.env.context = context
                if sale_order.shopify_order_status == "fulfilled":
                    sale_order.auto_workflow_process_id.shipped_order_workflow_ept(sale_order)
                    if order_data_line and order_data_line.shopify_order_data_queue_id.created_by == "scheduled_action":
                        created_by = 'Scheduled Action'
                    else:
                        created_by = self.env.user.name
                    # Below code add for create partially/fully refund
                    message = self.create_shipped_order_refund(shopify_financial_status, order_response, sale_order,
                                                               created_by)
                elif not sale_order.is_risky_order:
                    # CH:vishal Added condition check transactions
                    if order_response.get('transaction'):
                        if sale_order.shopify_order_status == "partial":
                            sale_order.process_order_fullfield_qty(order_response)
                            sale_order.with_context(shopify_order_financial_status=order_response.get(
                                "financial_status")).process_orders_and_invoices_ept()
                            if order_data_line and order_data_line.shopify_order_data_queue_id.created_by == \
                                    "scheduled_action":
                                created_by = 'Scheduled Action'
                            else:
                                created_by = self.env.user.name
                            # Below code add for create partially/fully refund
                            message = self.create_shipped_order_refund(shopify_financial_status, order_response, sale_order,
                                                                    created_by)
                        else:
                            sale_order.with_context(shopify_order_financial_status=order_response.get(
                                "financial_status")).process_orders_and_invoices_ept()
                    else:
                        sale_order.shopify_custom_confirm_order()


            except Exception as error:
                if order_data_line:
                    order_data_line.write({"state": "failed", "processed_at": datetime.now(),
                                           "sale_order_id": sale_order.id})
                message = "Receive error while process auto invoice workflow, Error is:  (%s)" % (error)
                _logger.info(message)
                common_log_line_obj.create_common_log_line_ept(shopify_instance_id=instance.id, module="shopify_ept",
                                                               message=message,
                                                               model_name=self._name,
                                                               order_ref=order_response.get("name"),
                                                               shopify_order_data_queue_line_id=order_data_line.id if order_data_line else False)
                continue
            _logger.info("Done auto workflow process for Odoo order(%s) and Shopify order is (%s)", sale_order.name,
                         order_number)

            if message:
                common_log_line_obj.create_common_log_line_ept(shopify_instance_id=instance.id, module="shopify_ept",
                                                               message=message,
                                                               model_name=self._name,
                                                               order_ref=order_response.get("name"),
                                                               shopify_order_data_queue_line_id=order_data_line.id if order_data_line else False)
                order_data_line.write({'state': 'failed', 'processed_at': datetime.now()})
            else:
                order_data_line.write({"state": "done", "processed_at": datetime.now(),
                                       "sale_order_id": sale_order.id, "order_data": False})
            _logger.info("Processed the Odoo Order %s process and Shopify Order (%s)", sale_order.name, order_number)

        return order_ids
    
    def shopify_custom_confirm_order(self):
        work_flow_process_record = self.auto_workflow_process_id
        if self.invoice_status == "invoiced":
            return
        if work_flow_process_record.validate_order:
            self.validate_order_ept()