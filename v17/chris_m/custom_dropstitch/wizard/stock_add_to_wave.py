from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta

import logging

_logger = logging.getLogger(__name__)


class StockPickingToWave(models.TransientModel):
    _inherit = "stock.add.to.wave"
    _description = "Wave Transfer Lines"

    def attach_pickings(self):
        sale_ids = self.picking_ids.sale_id
        if sale_ids and sale_ids.filtered(lambda a:a.shopify_order_id):
            raise UserError(_('Wave picking is not allowed for shopify order'))
        
        res = super(StockPickingToWave, self).attach_pickings()
        custom_policy_list = []
        custom_pay_term_list = []
        custom_delivery_address_id_list = []
        custom_shipping_fees_list = []
        
        wave_id = False
        picking_id = False
        # Dropship validation
        if self.picking_ids:
            sale_orders = self.picking_ids.mapped('sale_id')
            custom_dropship_orders = sale_orders.filtered(lambda order: order.custom_dropship_order)
            non_dropship_orders = sale_orders - custom_dropship_orders
            if custom_dropship_orders and non_dropship_orders:
                raise ValidationError(_("Dropship and Non-Dropship orders cannot be combined"))
            
        if self.picking_ids:
            for each_picking in self.picking_ids:
                custom_policy_list.append(each_picking.sale_id.custom_policy)
                custom_pay_term_list.append(each_picking.sale_id.payment_term_id.id)
                custom_delivery_address_id_list.append(each_picking.partner_id.id)
                custom_shipping_fees_list.append(
                    each_picking.sale_id.custom_shipping_fees
                )

                wave_id = each_picking.batch_id
                picking_id = each_picking

        if self.line_ids:
            for each_line in self.line_ids:
                custom_policy_list.append(each_line.picking_id.sale_id.custom_policy)
                custom_pay_term_list.append(
                    each_line.picking_id.sale_id.payment_term_id.id
                )
                custom_delivery_address_id_list.append(
                    each_line.picking_id.partner_id.id
                )
                custom_shipping_fees_list.append(
                    each_line.picking_id.sale_id.custom_shipping_fees
                )

                wave_id = each_line.picking_id.batch_id
                picking_id = each_line.picking_id

        if self.picking_ids or self.line_ids:
            if "intent" in custom_policy_list:
                if not all(item == "intent" for item in custom_policy_list):
                    raise ValidationError(
                        _("Customer Invoice Policy Should be same for all orders ")
                    )
            if not all(
                id == custom_delivery_address_id_list[0]
                for id in custom_delivery_address_id_list
            ):
                raise ValidationError(_("All Delivery Address should be same"))
            if not all(id == custom_pay_term_list[0] for id in custom_pay_term_list):
                raise ValidationError(
                    _("All Delivery Should have the same payment term")
                )
            if not all(
                id == custom_shipping_fees_list[0] for id in custom_shipping_fees_list
            ):
                raise ValidationError(
                    _("All Delivery Should have the Shipping charge policy")
                )

        if wave_id:
            if picking_id:
                if picking_id.sale_id.partner_id.property_delivery_carrier_id.id:
                    wave_id.custom_carrier_id = (
                        picking_id.sale_id.partner_id.property_delivery_carrier_id.id
                    )
            wave_id.custom_journal_id = (
                self.env["account.journal"].search([("type", "=", "bank")], limit=1).id
            )
            if picking_id.sale_id.custom_shipping_fees:
                wave_id.custom_shipping_fees = picking_id.sale_id.custom_shipping_fees
            else:
                wave_id.custom_shipping_fees = "charge_fees"
        return res
