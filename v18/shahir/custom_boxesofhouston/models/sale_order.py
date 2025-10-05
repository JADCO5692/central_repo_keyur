from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)
from collections import defaultdict
from datetime import datetime

class SaleOrder(models.Model):
    _inherit = "sale.order"

    stock_route_id = fields.Many2one('stock.route', 'Routes')
    partner_email = fields.Char('Email', related="partner_id.email")
    partner_phone = fields.Char('Phone', related="partner_id.phone")
    margine_percentage = fields.Float('Global Margin %')
    customer_statement = fields.Monetary('Customer Statement',compute='_compute_total_due')
    custom_quote = fields.Boolean('Custom Created Quotation')

    @api.depends("partner_id", "state", "payment_term_id")
    def _compute_is_immediate_payment(self):
        payment_term = self.env.ref("account.account_payment_term_immediate")
        if self.state in ['sale', 'cancel']:
            self.custom_hide_register_button = True
        elif not self.payment_term_id:
            self.custom_hide_register_button = False
        elif payment_term == self.payment_term_id:
            self.custom_hide_register_button = False
        else:
            self.custom_hide_register_button = True

    custom_hide_register_button = fields.Boolean(
        string="Hide Register Button",
        compute="_compute_is_immediate_payment",
        store=False
    )

    def custom_action_confirm(self):
        for order in self:
            if order.stock_route_id and order.stock_route_id.is_address_mandatory:
                order.check_delivery_address()
            order._check_negative_margin()
            if order.stock_route_id:
                if order.payment_term_id.id in [self.env.ref("account.account_payment_term_immediate").id, False, None]:
                    payment_ids = self.env['payment.transaction'].sudo().search([('sale_order_ids', 'in', [order.id])])
                    amount = 0
                    downpayment = 1
                    downpayment_amount = order.amount_total * downpayment
                    for payment_id in payment_ids:
                        amount = amount + payment_id.amount
                    if amount >= downpayment_amount:
                        order.action_confirm()
                        invoice = order._create_invoices()
                        invoice.action_post()
                    else:
                        raise UserError("Waiting for %s Payment to proceed" % downpayment_amount)
                else:
                    order.action_confirm()
                    invoice = order._create_invoices()
                    invoice.action_post()
                self.send_notification()
            else:
                raise UserError("Please add 'Route' on order to proceed")
        
        return True

    def _check_negative_margin(self): 
        for line in self.order_line:
            if line.custom_margin_percentage < 0:
                raise ValidationError(_(
                    "Negative margin percentage is not allowed.\n"
                    "Product: %s has margin %.2f%%"
                ) % (line.product_id.display_name, (line.custom_margin_percentage * 100)))

    def check_delivery_address(self):
        partner = self.partner_shipping_id
        if not partner:
            raise ValidationError(_("Shipping address is missing."))

        # Map technical field names to human labels
        required = {
            'street': _("Street"),
            'city': _("City"),
            'state_id': _("State"),
            'country_id': _("Country"),
            'zip': _("Zip"),
        }

        missing = [label for field, label in required.items()
                   if not getattr(partner, field)]

        if missing:
            field_list = ", ".join(missing)
            message = _("Address is incomplete. Missing fields: %s") % field_list
            raise ValidationError(message)

    def custom_register_payment(self):
        """Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        """
        self._check_negative_margin()
        if not self.stock_route_id:
            raise UserError("Please add 'Route' on order to proceed")
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

    def action_update_pricelist(self):
        pricelists = self.env['product.pricelist'].sudo().search([])
        for rec in self:
            if rec.partner_id:
                self._check_negative_margin()
                customer_id = rec.partner_id.id
                customer_pricelist = pricelists.filtered(lambda p: customer_id in p.customer_id.ids)
                if customer_pricelist:
                    self.update_pricelist_item(rec, customer_pricelist)
                else:
                    self.create_pricelist_item(rec)
                rec.custom_quote = False

    def action_confirm(self):
        res = super().action_confirm()
        if not self._context.get('ecommerce_create'):
            pricelists = self.env['product.pricelist'].sudo().search([])
            for rec in self:
                if rec.partner_id:
                    customer_id = rec.partner_id.id
                    customer_pricelist = pricelists.filtered(lambda p: customer_id in p.customer_id.ids)
                    if customer_pricelist:
                        self.update_pricelist_item(rec, customer_pricelist)
                    else:
                        self.create_pricelist_item(rec)
        for rec in self:
            if rec.stock_route_id.is_auto_complete:
                rec._simple_force_validate()
        self.send_notification()
        return res

    def update_pricelist_item(self, order, pricelist):
        item_obj = self.env['product.pricelist.item'].sudo()
        for line in order.order_line:
            line_items = pricelist.item_ids.filtered(lambda x: x.product_tmpl_id.id == line.product_template_id.id)
            if line_items:
                offered_qty_line = line_items.filtered(lambda x: x.min_quantity == line.product_uom_qty)
                if not offered_qty_line:
                    less_qty_lines = line_items.filtered(lambda x: x.min_quantity < line.product_uom_qty)
                    max_qty = max(less_qty_lines.mapped('min_quantity'))
                    immediate_less_line = line_items.filtered(lambda x: x.min_quantity == max_qty)
                    if not immediate_less_line:
                        item_obj.create(self.prepare_pl_item_vals(line, pricelist, line.product_uom_qty))
                    else:
                        if immediate_less_line.fixed_price != line.price_unit:
                            item_obj.create(self.prepare_pl_item_vals(line, pricelist, line.product_uom_qty))
                else:
                    offered_qty_line.update({
                        'fixed_price': line.price_unit,
                    })
            else:
                if line.product_uom_qty > 1:
                    item_obj.create(self.prepare_pl_item_vals(line, pricelist, line.product_uom_qty))
                item_obj.create(self.prepare_pl_item_vals(line, pricelist, 0.0))

    def create_pricelist_item(self, order):
        pricelist_obj = self.env['product.pricelist'].sudo()
        item_obj = self.env['product.pricelist.item'].sudo()
        prepare_pricelist_data = self.prepare_pricelist_data(order)
        pricelist_obj = pricelist_obj.create(prepare_pricelist_data)
        if order.partner_id and pricelist_obj:
            order.partner_id.property_product_pricelist = pricelist_obj.id
        if pricelist_obj:
            for line in order.order_line:
                if line.product_uom_qty > 1:
                    item_obj.create(self.prepare_pl_item_vals(line, pricelist_obj, line.product_uom_qty))
                item_obj.create(self.prepare_pl_item_vals(line, pricelist_obj, 0.0))

    def prepare_pricelist_data(self, order):
        partner_id = order.partner_id and order.partner_id.id or False
        vals = {
            'name': order.partner_id.name or '',
            'customer_id': partner_id if partner_id else False
        }
        return vals

    def prepare_pl_item_vals(self, line, pl, qty):
        return {
            'applied_on': '1_product',
            'product_tmpl_id': line.product_template_id.id,
            'compute_price': 'fixed',
            'fixed_price': line.price_unit,
            'min_quantity': qty,
            'pricelist_id': pl.id
        }

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id()
        self._recompute_taxes()
        return res

    @api.onchange('stock_route_id')
    def onchange_route(self):
        dropship_route = self.env.ref('stock_dropshipping.route_drop_shipping').id
        for rec in self:
            for line in rec.order_line:
                # ✅ Skip if dropshipping route is already set
                if line.route_id and line.route_id.id == dropship_route:
                    continue
                line.route_id = rec.stock_route_id.id

    def action_quotation_send(self):
        if 'unset_payment' not in self.env.context:
            for order in self:
                order.require_payment = False
        return super().action_quotation_send()

    def custom_action_send_email(self):
        self._check_negative_margin()
        if not self.stock_route_id:
            raise UserError("Please add 'Route' on order to proceed")

        self.require_payment = True
        return self.with_context(unset_payment=True).action_quotation_send()

    @api.onchange('margine_percentage')
    def onchange_margine_percentage(self):
        for rec in self:
            margine_percentage = rec.margine_percentage
            for line in rec.order_line:
                line.custom_margin_percentage = margine_percentage
                line._inverse_margin_percentage()

    def _simple_force_validate(self):
        """Simple force validation method"""
        for picking in self.picking_ids.filtered(lambda pick: pick.state not in ('done','cancel')):
            try:
                # Confirm picking
                if picking.state == 'draft':
                    picking.action_confirm()

                # Create move lines and set quantities
                for move in picking.move_ids:
                    if not move.move_line_ids:
                        # Create move line
                        self.env['stock.move.line'].create({
                            'move_id': move.id,
                            'product_id': move.product_id.id,
                            'product_uom_id': move.product_uom.id,
                            'location_id': move.location_id.id,
                            'location_dest_id': move.location_dest_id.id,
                            'quantity': move.product_uom_qty,
                        })
                    else:
                        # Update existing move lines
                        move.move_line_ids.write({'quantity': move.product_uom_qty})
                picking.move_ids.picked = True
                # Validate picking
                picking.button_validate()

            except Exception as e:
                _logger.warning(f"Simple force validation failed for {picking.name}: {str(e)}")

    def _compute_total_due(self):
        due_data = defaultdict(float)
        overdue_data = defaultdict(float)
        receivable_due_data = defaultdict(float)
        receivable_overdue_data = defaultdict(float)
        unreconciled_aml_ids = defaultdict(list)
        for order in self:
            partner = order.partner_id
            for account_type, overdue, partner, amount_residual_sum, aml_ids in self.env['account.move.line']._read_group(
                domain=partner._get_unreconciled_aml_domain(),
                groupby=['account_type', 'followup_overdue', 'partner_id'],
                aggregates=['amount_residual:sum', 'id:array_agg'],
            ):
                if account_type == 'asset_receivable':
                    unreconciled_aml_ids[partner] += aml_ids
                    receivable_due_data[partner] += amount_residual_sum
                    if overdue:
                        receivable_overdue_data[partner] += amount_residual_sum
                due_data[partner] += amount_residual_sum
                if overdue:
                    overdue_data[partner] += amount_residual_sum

             
            order.customer_statement = due_data.get(partner, 0.0) or 0

    def send_notification(self):
        params = {
            'message': 'New Created',
            'type': 'record_create_notify',
        } 
        users = self.env['res.users'].sudo().search([])
        users._bus_send("dashboard_notify", params)

    def write(self,vals):
        res = super(SaleOrder,self).write(vals)
        if 'state' in vals and vals.get('state') == 'sent':
            params = {
                'message': 'New Created',
                'type': 'record_create_notify',
            } 
            users = self.env['res.users'].sudo().search([])
            users._bus_send("dashboard_notify", params) 
        return res
        
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_so_as_sent'):
            self.filtered(lambda o: o.state == 'draft').write({'state': 'sent'})
        return super().message_post(**kwargs)
     
    def get_orders_sent(self,date_domain):
        """Return sale orders that moved from draft → sent in the current month."""
        domain = [('field_id.name', '=', 'state'),('old_value_char', 'in', ['draft', 'Quotation']),('new_value_char', 'in', ['sent', 'Quotation Sent'])]+date_domain
        tracking_vals = self.env['mail.tracking.value'].search(domain) 
        order_ids = tracking_vals.mapped('mail_message_id.res_id')
        result = self.env['sale.order'].browse(order_ids)
        return result
        
    def _action_cancel(self):
        result = super(SaleOrder, self)._action_cancel()
        if result:
            for sale_order in self:
                for invoice in sale_order.invoice_ids:
                    if invoice.state in ["posted"] and invoice.status_in_payment in ["not_paid"]:
                        invoice.button_draft()
                        invoice.button_cancel()
        return result
        
    def _create_or_update_orderpoints_for_lines(self):
        Orderpoint = self.env["stock.warehouse.orderpoint"]
        for line in self.order_line:
            prod = line.product_id
            # if not prod.auto_create_orderpoint:
            #     continue
            if prod.type != 'consu':  # only for storable
                continue
            # Use available quantity (or forecast) at this moment
            qty_available = prod.qty_available
            threshold = prod.replenishment_threshold or 0.0
            order_qty = line.product_uom_qty or 0.0
            if order_qty >= qty_available and order_qty > 0:
                domain = [
                    ("product_id", "=", prod.id),
                    ("warehouse_id", "=", line.warehouse_id.id),
                ]
                op = Orderpoint.search(domain, limit=1)
                if not op:
                    # create
                    op_vals = {
                        "product_id": prod.id,
                        "warehouse_id": line.warehouse_id.id,
                        "product_min_qty": threshold,  # or some default
                        "product_max_qty": prod.replenishment_threshold,
                        "qty_multiple": 1,
                        # you could set other fields as needed (location_id, orderpoint name, etc.)
                    }
                    op = Orderpoint.create(op_vals)
                else:
                    # op.write({ "product_min_qty": threshold, ... })
                    pass