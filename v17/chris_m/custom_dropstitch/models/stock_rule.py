# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models

import logging

_logger = logging.getLogger(__name__)
from odoo import api, fields, models, SUPERUSER_ID, _


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _prepare_mo_vals(
        self,
        product_id,
        product_qty,
        product_uom,
        location_id,
        name,
        origin,
        company_id,
        values,
        bom,
    ):
        res = super()._prepare_mo_vals(
            product_id,
            product_qty,
            product_uom,
            location_id,
            name,
            origin,
            company_id,
            values,
            bom,
        )
        sale_order_id = self.env["sale.order"].search([("name", "=", origin)], limit=1)
        if sale_order_id:
            res["custom_partner"] = sale_order_id.partner_id.id
            res["custom_machine_no"] = product_id.custom_machine_no
            res["custom_prod_time"] = product_id.custom_prod_time * product_qty

            if product_id.custom_mrp_confirm == "yes":
                res["custom_released"] = True

            custom_pwl_cus_pro_rec = self.env["custom.product.warehouse"].search(
                [
                    ("custom_warehouse_id", "=", sale_order_id.warehouse_id.id),
                    ("custom_customer_id", "=", sale_order_id.partner_id.id),
                    ("custom_product_id", "=", product_id.id),
                ],
                limit=1,
            )
            if custom_pwl_cus_pro_rec:
                # If both customer and product is set
                res["location_src_id"] = custom_pwl_cus_pro_rec.custom_location_id.id
            else:
                custom_pwl_cus_rec = self.env["custom.product.warehouse"].search(
                    [
                        ("custom_warehouse_id", "=", sale_order_id.warehouse_id.id),
                        ("custom_customer_id", "=", sale_order_id.partner_id.id),
                        ("custom_product_id", "=", False),
                    ],
                    limit=1,
                )
                if custom_pwl_cus_rec:
                    # If only customer is set
                    res["location_src_id"] = custom_pwl_cus_rec.custom_location_id.id
                else:
                    custom_pwl_pro_rec = self.env["custom.product.warehouse"].search(
                        [
                            ("custom_warehouse_id", "=", sale_order_id.warehouse_id.id),
                            ("custom_customer_id", "=", False),
                            ("custom_product_id", "=", product_id.id),
                        ],
                        limit=1,
                    )
                    if custom_pwl_pro_rec:
                        # If only product is set
                        res["location_src_id"] = (
                            custom_pwl_pro_rec.custom_location_id.id
                        )
        if "move_dest_ids" in values:
            for stock_move in values["move_dest_ids"]:
                res["custom_tiff_file_url"] = stock_move.product_id.custom_tiff_file_url

                sale_order_line_id = stock_move.sale_line_id
                if sale_order_line_id:
                    res["custom_sale_order_line"] = sale_order_line_id.id
                    res["custom_released"] = True
                    if sale_order_line_id.custom_color_2:
                        res["custom_color_2"] = sale_order_line_id.custom_color_2.id
                    if sale_order_line_id.custom_color_3:
                        res["custom_color_3"] = sale_order_line_id.custom_color_3.id
                    if sale_order_line_id.custom_color_4:
                        res["custom_color_4"] = sale_order_line_id.custom_color_4.id
                    if sale_order_line_id.custom_color_5:
                        res["custom_color_5"] = sale_order_line_id.custom_color_5.id
                    if sale_order_line_id.custom_color_6:
                        res["custom_color_6"] = sale_order_line_id.custom_color_6.id
                    if sale_order_line_id.custom_color_7:
                        res["custom_color_7"] = sale_order_line_id.custom_color_7.id
                    if sale_order_line_id.custom_personalize:
                        res["custom_personalize"] = (
                            sale_order_line_id.custom_personalize
                        )
                        res["custom_tiff_file_url"] = ""
                        res["custom_released"] = False
                    if sale_order_line_id.custom_line1:
                        res["custom_line1"] = sale_order_line_id.custom_line1
                        res["custom_tiff_file_url"] = ""
                        res["custom_released"] = False
                    if sale_order_line_id.custom_line2:
                        res["custom_line2"] = sale_order_line_id.custom_line2
                        res["custom_tiff_file_url"] = ""
                        res["custom_released"] = False
                    if sale_order_line_id.custom_line3:
                        res["custom_line3"] = sale_order_line_id.custom_line3
                        res["custom_tiff_file_url"] = ""
                        res["custom_released"] = False
                    if sale_order_line_id.custom_initials:
                        res["custom_initials"] = sale_order_line_id.custom_initials
                        res["custom_tiff_file_url"] = ""
                        res["custom_released"] = False
                    if sale_order_line_id.custom_order_no:
                        res["custom_order_no"] = sale_order_line_id.custom_order_no
                    if sale_order_line_id.custom_font:
                        res["custom_font"] = sale_order_line_id.custom_font
                        res["custom_tiff_file_url"] = ""
                        res["custom_released"] = False
                    if sale_order_line_id.custom_fontcase:
                        res["custom_fontcase"] = sale_order_line_id.custom_fontcase
                        res["custom_tiff_file_url"] = ""
                        res["custom_released"] = False
                    if sale_order_line_id.custom_tiff_file_url:
                        res["custom_tiff_file_url"] = sale_order_line_id.custom_tiff_file_url
                        res["custom_released"] = False

                    if (
                        res["custom_released"] == False
                        and sale_order_line_id.custom_attribute_1
                        and sale_order_line_id.product_id.custom_prod_type
                        in [
                            "mtp",
                            "special_mtp_var",
                            "special_mtp_prod",
                        ]
                    ):
                        custom_deisgn_tif_rec = self.env["custom.design.tif"].search(
                            [
                                ("custom_prod_size", "=", product_id.custom_prod_size),
                                (
                                    "custom_design_id",
                                    "=",
                                    sale_order_line_id.custom_attribute_1.id,
                                ),
                            ],
                            limit=1,
                        )
                        if custom_deisgn_tif_rec:
                            res["custom_tiff_file_url"] = (
                                custom_deisgn_tif_rec.custom_tiff_file_url
                            )
                            res["custom_released"] = True
                    if sale_order_line_id.custom_opentext:
                        res["custom_opentext"] = sale_order_line_id.custom_opentext
                    if sale_order_line_id.custom_etail_ticket_no:
                        res["custom_etail_ticket_no"] = (
                            sale_order_line_id.custom_etail_ticket_no
                        )
                    if sale_order_line_id.custom_customer_product:
                        res["custom_customer_product"] = (
                            sale_order_line_id.custom_customer_product
                        )

                    if stock_move.product_id.custom_prod_type in [
                        "mtp",
                        "special_mtp_var",
                        "special_mtp_prod",
                    ]:
                        if sale_order_line_id.custom_attribute_1:
                            res["custom_attribute_1"] = (
                                sale_order_line_id.custom_attribute_1.id
                            )

                        move_raw_ids = []

                        if sale_order_line_id.custom_color_2:
                            line_id = {
                                "product_id": sale_order_line_id.custom_color_2.id
                            }
                            line_id["location_dest_id"] = (
                                sale_order_line_id.product_id.property_stock_production.id
                            )
                            line_id["location_id"] = (
                                sale_order_line_id.warehouse_id.lot_stock_id.id
                            )
                            line_id["name"] = (
                                "For MO(MTO) of " + sale_order_line_id.order_id.name
                            )
                            line_id["origin"] = sale_order_line_id.order_id.name
                            line_id["custom_color_no"] = "2"
                            if stock_move.product_id.custom_prod_type == "mtp":
                                line_id["product_uom_qty"] = (
                                    sale_order_line_id.product_id.custom_color_2
                                )
                            if (
                                stock_move.product_id.custom_prod_type
                                == "special_mtp_var"
                            ):
                                line_id["product_uom_qty"] = (
                                    sale_order_line_id.custom_attribute_1.custom_color_2
                                    * sale_order_line_id.product_id.weight
                                ) / 100
                            if (
                                stock_move.product_id.custom_prod_type
                                == "special_mtp_prod"
                            ):
                                line_id["product_uom_qty"] = (
                                    sale_order_line_id.product_id.custom_color_2
                                    * sale_order_line_id.product_id.weight
                                ) / 100

                            if "location_src_id" in res:
                                line_id["location_id"] = res["location_src_id"]
                            move_id = self.env["stock.move"].create(line_id)
                            move_raw_ids.append(move_id.id)

                        if sale_order_line_id.custom_color_3:
                            line_id = {
                                "product_id": sale_order_line_id.custom_color_3.id
                            }
                            line_id["location_dest_id"] = (
                                sale_order_line_id.product_id.property_stock_production.id
                            )
                            line_id["location_id"] = (
                                sale_order_line_id.warehouse_id.lot_stock_id.id
                            )
                            line_id["name"] = (
                                "For MO(MTO) of " + sale_order_line_id.order_id.name
                            )
                            line_id["origin"] = sale_order_line_id.order_id.name
                            line_id["custom_color_no"] = "3"
                            if stock_move.product_id.custom_prod_type == "mtp":
                                line_id["product_uom_qty"] = (
                                    sale_order_line_id.product_id.custom_color_3
                                )
                            if (
                                stock_move.product_id.custom_prod_type
                                == "special_mtp_var"
                            ):
                                line_id["product_uom_qty"] = (
                                    sale_order_line_id.custom_attribute_1.custom_color_3
                                    * sale_order_line_id.product_id.weight
                                ) / 100
                            if (
                                stock_move.product_id.custom_prod_type
                                == "special_mtp_prod"
                            ):
                                line_id["product_uom_qty"] = (
                                    sale_order_line_id.product_id.custom_color_3
                                    * sale_order_line_id.product_id.weight
                                ) / 100

                            if "location_src_id" in res:
                                line_id["location_id"] = res["location_src_id"]
                            move_id = self.env["stock.move"].create(line_id)
                            move_raw_ids.append(move_id.id)

                        if sale_order_line_id.custom_color_4:
                            line_id = {
                                "product_id": sale_order_line_id.custom_color_4.id
                            }
                            line_id["location_dest_id"] = (
                                sale_order_line_id.product_id.property_stock_production.id
                            )
                            line_id["location_id"] = (
                                sale_order_line_id.warehouse_id.lot_stock_id.id
                            )
                            line_id["name"] = (
                                "For MO(MTO) of " + sale_order_line_id.order_id.name
                            )
                            line_id["origin"] = sale_order_line_id.order_id.name
                            line_id["custom_color_no"] = "4"
                            if stock_move.product_id.custom_prod_type == "mtp":
                                line_id["product_uom_qty"] = (
                                    sale_order_line_id.product_id.custom_color_4
                                )
                            if (
                                stock_move.product_id.custom_prod_type
                                == "special_mtp_var"
                            ):
                                line_id["product_uom_qty"] = (
                                    sale_order_line_id.custom_attribute_1.custom_color_4
                                    * sale_order_line_id.product_id.weight
                                ) / 100
                            if (
                                stock_move.product_id.custom_prod_type
                                == "special_mtp_prod"
                            ):
                                line_id["product_uom_qty"] = (
                                    sale_order_line_id.product_id.custom_color_4
                                    * sale_order_line_id.product_id.weight
                                ) / 100

                            if "location_src_id" in res:
                                line_id["location_id"] = res["location_src_id"]
                            move_id = self.env["stock.move"].create(line_id)
                            move_raw_ids.append(move_id.id)

                        if sale_order_line_id.custom_color_5:
                            line_id = {
                                "product_id": sale_order_line_id.custom_color_5.id
                            }
                            line_id["location_dest_id"] = (
                                sale_order_line_id.product_id.property_stock_production.id
                            )
                            line_id["location_id"] = (
                                sale_order_line_id.warehouse_id.lot_stock_id.id
                            )
                            line_id["name"] = (
                                "For MO(MTO) of " + sale_order_line_id.order_id.name
                            )
                            line_id["origin"] = sale_order_line_id.order_id.name
                            line_id["custom_color_no"] = "5"
                            if stock_move.product_id.custom_prod_type == "mtp":
                                line_id["product_uom_qty"] = (
                                    sale_order_line_id.product_id.custom_color_5
                                )
                            if (
                                stock_move.product_id.custom_prod_type
                                == "special_mtp_var"
                            ):
                                line_id["product_uom_qty"] = (
                                    sale_order_line_id.custom_attribute_1.custom_color_5
                                    * sale_order_line_id.product_id.weight
                                ) / 100
                            if (
                                stock_move.product_id.custom_prod_type
                                == "special_mtp_prod"
                            ):
                                line_id["product_uom_qty"] = (
                                    sale_order_line_id.product_id.custom_color_5
                                    * sale_order_line_id.product_id.weight
                                ) / 100

                            if "location_src_id" in res:
                                line_id["location_id"] = res["location_src_id"]
                            move_id = self.env["stock.move"].create(line_id)
                            move_raw_ids.append(move_id.id)

                        if sale_order_line_id.custom_color_6:
                            line_id = {
                                "product_id": sale_order_line_id.custom_color_6.id
                            }
                            line_id["location_dest_id"] = (
                                sale_order_line_id.product_id.property_stock_production.id
                            )
                            line_id["location_id"] = (
                                sale_order_line_id.warehouse_id.lot_stock_id.id
                            )
                            line_id["name"] = (
                                "For MO(MTO) of " + sale_order_line_id.order_id.name
                            )
                            line_id["origin"] = sale_order_line_id.order_id.name
                            line_id["custom_color_no"] = "6"
                            if stock_move.product_id.custom_prod_type == "mtp":
                                line_id["product_uom_qty"] = (
                                    sale_order_line_id.product_id.custom_color_6
                                )
                            if (
                                stock_move.product_id.custom_prod_type
                                == "special_mtp_var"
                            ):
                                line_id["product_uom_qty"] = (
                                    sale_order_line_id.custom_attribute_1.custom_color_6
                                    * sale_order_line_id.product_id.weight
                                ) / 100
                            if (
                                stock_move.product_id.custom_prod_type
                                == "special_mtp_prod"
                            ):
                                line_id["product_uom_qty"] = (
                                    sale_order_line_id.product_id.custom_color_6
                                    * sale_order_line_id.product_id.weight
                                ) / 100

                            if "location_src_id" in res:
                                line_id["location_id"] = res["location_src_id"]
                            move_id = self.env["stock.move"].create(line_id)
                            move_raw_ids.append(move_id.id)

                        if sale_order_line_id.custom_color_7:
                            line_id = {
                                "product_id": sale_order_line_id.custom_color_7.id
                            }
                            line_id["location_dest_id"] = (
                                sale_order_line_id.product_id.property_stock_production.id
                            )
                            line_id["location_id"] = (
                                sale_order_line_id.warehouse_id.lot_stock_id.id
                            )
                            line_id["name"] = (
                                "For MO(MTO) of " + sale_order_line_id.order_id.name
                            )
                            line_id["origin"] = sale_order_line_id.order_id.name
                            line_id["custom_color_no"] = "7"
                            if stock_move.product_id.custom_prod_type == "mtp":
                                line_id["product_uom_qty"] = (
                                    sale_order_line_id.product_id.custom_color_7
                                )
                            if (
                                stock_move.product_id.custom_prod_type
                                == "special_mtp_var"
                            ):
                                line_id["product_uom_qty"] = (
                                    sale_order_line_id.custom_attribute_1.custom_color_7
                                    * sale_order_line_id.product_id.weight
                                ) / 100
                            if (
                                stock_move.product_id.custom_prod_type
                                == "special_mtp_prod"
                            ):
                                line_id["product_uom_qty"] = (
                                    sale_order_line_id.product_id.custom_color_7
                                    * sale_order_line_id.product_id.weight
                                ) / 100

                            if "location_src_id" in res:
                                line_id["location_id"] = res["location_src_id"]
                            move_id = self.env["stock.move"].create(line_id)
                            move_raw_ids.append(move_id.id)

                        res["move_raw_ids"] = move_raw_ids
        if self._context.get("custom_scrap_flag"):
            active_id = self._context.get("active_id")
            mo_order = self.env["mrp.production"].browse(active_id)
            if mo_order:
                res.update(
                    {
                        "custom_label_type": mo_order.custom_label_type,
                        "custom_label_placement": mo_order.custom_label_placement,
                        "custom_bag_info": mo_order.custom_bag_info,
                        "custom_box_info": mo_order.custom_box_info,
                        "custom_brand_label": mo_order.custom_brand_label,
                        "custom_care_label": mo_order.custom_care_label,
                        "custom_instruction": mo_order.custom_instruction,
                        "custom_pack_instr": mo_order.custom_pack_instr,
                        "custom_prod_var_image": mo_order.custom_prod_var_image,
                        "custom_personalize": mo_order.custom_personalize,
                        "custom_line1": mo_order.custom_line1,
                        "custom_line2": mo_order.custom_line2,
                        "custom_line3": mo_order.custom_line3,
                        "custom_initials": mo_order.custom_initials,
                        "custom_prod_size": mo_order.custom_prod_size,
                        "custom_tiff_file_url": mo_order.custom_tiff_file_url,
                        "custom_machine_no": mo_order.custom_machine_no,
                        "custom_is_binding": mo_order.custom_is_binding,
                        "custom_is_wash": mo_order.custom_is_wash,
                        "custom_is_dry": mo_order.custom_is_dry,
                        "custom_is_press": mo_order.custom_is_press,
                        "custom_prod_type": mo_order.custom_prod_type,
                        "custom_prod_time": mo_order.custom_prod_time,
                        "custom_current_url": mo_order.custom_current_url,
                        "custom_stock_picking_id": mo_order.custom_stock_picking_id.id,
                        "custom_stock_picking_url": mo_order.custom_stock_picking_url,
                        "custom_order_no": mo_order.custom_order_no,
                        "custom_color_2": mo_order.custom_color_2.id,
                        "custom_color_3": mo_order.custom_color_3.id,
                        "custom_color_4": mo_order.custom_color_4.id,
                        "custom_color_5": mo_order.custom_color_5.id,
                        "custom_color_6": mo_order.custom_color_6.id,
                        "custom_color_7": mo_order.custom_color_7.id,
                        "custom_attribute_1": mo_order.custom_attribute_1.id,
                        "custom_released": mo_order.custom_released,
                        "custom_partner": mo_order.custom_partner.id,
                        "custom_is_scrap_mo": True,
                        "custom_is_parent_mo": False,
                        "custom_mrp_parent_id": mo_order.id,
                        "custom_sale_order_line": mo_order.custom_sale_order_line.id if mo_order.custom_sale_order_line else False,
                        "custom_customer_product": mo_order.custom_customer_product,
                        "custom_etail_ticket_no": mo_order.custom_etail_ticket_no,
                        "custom_opentext": mo_order.custom_opentext,
                        "custom_fontcase": mo_order.custom_fontcase,
                        "custom_font": mo_order.custom_font,
                        "location_src_id": mo_order.location_src_id.id,
                    }
                )
                for stock_move in mo_order.move_raw_ids:
                    stock_move.location_id = mo_order.location_src_id.id
        return res

    def _should_auto_confirm_procurement_mo(self, p):
        res = super()._should_auto_confirm_procurement_mo(p)
        if self._context.get("custom_scrap_flag"):
            active_id = self._context.get("active_id")
            mo_order = self.env["mrp.production"].browse(active_id)
            if mo_order:
                mo_order.write(
                    {"custom_scrap_mrp_id": p.id, "custom_is_parent_mo": True}
                )
                sale_order_id = self.env["sale.order"].search(
                    [("name", "=", mo_order.origin)]
                )
                if sale_order_id:
                    p.procurement_group_id.write(
                        {
                            "partner_id": mo_order.custom_partner.id,
                            "sale_id": sale_order_id.id,
                        }
                    )
        return res
