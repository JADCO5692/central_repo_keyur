# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta

import logging

_logger = logging.getLogger(__name__)


class ChooseDeliveryCarrierCustom(models.TransientModel):
    _inherit = "choose.delivery.carrier"
    _description = "Delivery Carrier Selection Wizard"

    custom_hide_button = fields.Boolean("Hide Button?", default=False, copy=False)
    custom_picking_id = fields.Many2one(comodel_name="stock.picking", string="Picking")

    def custom_button_confirm(self):
        if (
            self.carrier_id.delivery_type == "shipstation_ept"
            and self.total_weight > 18.5
        ):
            raise ValidationError(
                "Do not use ShipStation for order weight more than 20 Pound"
            )
        self.custom_picking_id.write(
            {
                "carrier_id": self.carrier_id.id,
            }
        )

    def update_price(self):
        default_custom_picking_id = self._context.get("default_custom_picking_id")
        default_order_id = self._context.get("default_order_id")
        default_total_weight = self._context.get("default_total_weight")
        default_custom_hide_button = self._context.get("default_custom_hide_button")
        default_backorder_flag = self._context.get("default_backorder_flag")
        vals = self._get_shipment_rate()
        if vals.get("error_message"):
            raise UserError(vals.get("error_message"))
        return {
            "name": _("Add a shipping method"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "choose.delivery.carrier",
            "res_id": self.id,
            "target": "new",
            "context": {
                "default_order_id": default_order_id,
                "default_total_weight": default_total_weight,
                "default_custom_hide_button": default_custom_hide_button,
                "default_custom_picking_id": default_custom_picking_id,
                "default_backorder_flag": default_backorder_flag,
            },
        }

    def button_confirm(self):
        picking_id = False
        res = False
        self._get_shipment_rate()
        picking_active_id = self.env.context.get("default_custom_picking_id")
        if picking_active_id:
            picking_id = self.env["stock.picking"].browse(picking_active_id)
        order_id = self.env.context.get("default_order_id")
        sale_order_obj = self.env["sale.order"].browse(order_id)
        if (
            self.carrier_id.delivery_type == "shipstation_ept"
            and self.total_weight > 18.5
        ):
            raise ValidationError(
                "Do not use ShipStation for order weight more than 20 Pound"
            )
        if picking_id:
            if picking_id.sale_id.custom_shipping_fees == "no_fees":
                self.delivery_price = 0
            shipstation_service_id = False
            shipstation_carrier_id = False
            carrier_rec = False
            if sale_order_obj:
                if self.carrier_id.get_cheapest_rates:
                    shipstation_service_id = (
                        sale_order_obj.cheapest_service_id.id or False
                    )
                    shipstation_carrier_id = (
                        sale_order_obj.cheapest_carrier_id.id or False
                    )
                    carrier_rec = sale_order_obj.cheapest_carrier_id
                else:
                    shipstation_service_id = (
                        self.carrier_id.shipstation_service_id.id or False
                    )
                    shipstation_carrier_id = (
                        self.carrier_id.shipstation_carrier_id.id or False
                    )
                    carrier_rec = self.carrier_id.shipstation_carrier_id

                if self.carrier_id.delivery_type == "shipstation_ept":
                    carrier_dict_update = {
                        "shipstation_instance_id": sale_order_obj.shipstation_instance_id.id
                        or sale_order_obj.shipstation_store_id.shipstation_instance_id.id,
                        "confirmation": self.carrier_id.confirmation,
                        "is_residential": self.carrier_id.is_residential_address,
                        "shipstation_service_id": shipstation_service_id or False,
                        "shipstation_store_id": sale_order_obj.shipstation_store_id.id
                        or False,
                        "shipstation_package_id": self.carrier_id.shipstation_package_id.id
                        or False,
                        "export_order": sale_order_obj.team_id.export_order,
                        "shipstation_carrier_id": shipstation_carrier_id or False,
                        "state": "invoice_sent",
                    }
                else:
                    carrier_dict_update = {
                        "shipstation_instance_id": False,
                        "confirmation": False,
                        "is_residential": False,
                        "shipstation_service_id": False,
                        "shipstation_store_id": False,
                        "shipstation_package_id": False,
                        "export_order": False,
                        "shipstation_carrier_id": False,
                        "state": "invoice_sent",
                    }
                if sale_order_obj.shopify_order_id:
                    carrier_dict_update["state"] = "ready_to_be_sent"
                if picking_id.backorder_id:
                    sale_order_obj._create_delivery_line(
                        self.carrier_id, self.delivery_price
                    )
                    carrier_dict_update["carrier_id"] = self.carrier_id.id
                    picking_id.write(carrier_dict_update)
                    res = True
                elif picking_id.batch_id:
                    carrier_dict_update = {
                        "shipstation_instance_id": False,
                        "confirmation": False,
                        "is_residential": False,
                        "shipstation_service_id": False,
                        "shipstation_store_id": False,
                        "shipstation_package_id": False,
                        "export_order": False,
                        "shipstation_carrier_id": False,
                        "state": "invoice_sent",
                    }
                    if not picking_id.sale_id.shopify_order_id:
                        sale_order_obj._create_delivery_line(
                            self.carrier_id, self.delivery_price
                        )
                    picking_id.write(carrier_dict_update)
                    res = True
                else:
                    picking_id.write(carrier_dict_update)
                    if picking_id.sale_id.shopify_order_id:
                        res = True
                    else:
                        res = super(ChooseDeliveryCarrierCustom, self).button_confirm()
                picking_id._action_create_invoice_and_payment(sale_order_obj)
        else:
            res = super(ChooseDeliveryCarrierCustom, self).button_confirm()
        return res
    
    @api.depends('partner_id')
    def _compute_available_carrier(self):
        for rec in self:
            carriers = self.env['delivery.carrier'].search(self.env['delivery.carrier']._check_company_domain(rec.order_id.company_id))
            carriers = carriers.filtered(lambda carrier: carrier.custom_hide_for_sel == False)
            
            carriers_non_shipstation = carriers.filtered(lambda carrier: carrier.delivery_type != 'shipstation_ept')
            carriers_shopify = carriers.filtered(lambda carrier: carrier.shopify_source)
            
            if rec.order_id.partner_id.custom_allowed_shipping_ids:
                rec.available_carrier_ids = rec.order_id.partner_id.custom_allowed_shipping_ids
            elif rec.custom_picking_id.shipping_weight > 18.5:
                rec.available_carrier_ids = carriers_non_shipstation
            else:
                if rec.order_id.shopify_instance_id:
                    rec.available_carrier_ids = carriers_shopify
                else:
                    rec.available_carrier_ids = carriers.available_carriers(rec.order_id.partner_shipping_id) if rec.partner_id else carriers
    
    def _get_shipment_rate(self):
        total_weight = self.total_weight
        vals = self.carrier_id.with_context(order_weight=total_weight).rate_shipment(self.order_id)
        if vals.get('success'):
            self.delivery_message = vals.get('warning_message', False)
            self.delivery_price = vals['price']
            self.display_price = vals['carrier_price']
            return {}
        return {'error_message': vals['error_message']}