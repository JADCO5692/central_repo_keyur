# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import requests
import re
import base64
import logging

_logger = logging.getLogger(__name__)

sel_custom_machine_no = [
    ("na", "N/A"),
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
    ("5", "5"),
    ("6", "6"),
    ("7", "7"),
    ("8", "8"),
    ("9", "9"),
    ("10", "10"),
    ("11", "11"),
    ("12", "12"),
    ("13", "13"),
    ("14", "14"),
    ("15", "15"),
    ("16", "16"),
    ("17", "17"),
    ("18", "18"),
    ("19", "19"),
    ("20", "20"),
    ("21", "21"),
]


class CustomMrpProduction(models.Model):
    _inherit = "mrp.production"

    custom_label_type = fields.Selection(
        string="Label Type", related="custom_sale_order_line.order_id.custom_label_type"
    )
    custom_label_placement = fields.Selection(
        string="Label Placement",
        related="custom_sale_order_line.order_id.custom_label_placement",
    )
    custom_bag_info = fields.Selection(
        string="Bag Info", related="custom_sale_order_line.order_id.custom_bag_info"
    )
    custom_box_info = fields.Selection(
        string="Box Info", related="custom_sale_order_line.order_id.custom_box_info"
    )

    custom_brand_label = fields.Integer(
        "Brand Label", related="custom_sale_order_line.order_id.custom_brand_label"
    )
    custom_care_label = fields.Integer(
        "Care Label", related="custom_sale_order_line.order_id.custom_care_label"
    )

    custom_instruction = fields.Char(
        "Label Special Instruction",
        related="custom_sale_order_line.order_id.custom_instruction",
    )
    custom_pack_instr = fields.Char(
        "Packaging Instruction",
        related="custom_sale_order_line.order_id.custom_pack_instr",
    )

    custom_prod_var_image = fields.Binary(
        string="Prod Var Image", related="product_id.image_1920"
    )
    custom_label_image = fields.Binary(
        string="Label Image",
        related="custom_sale_order_line.order_id.custom_label_image",
    )
    custom_item_image = fields.Binary(
        string="Item Image", related="custom_sale_order_line.custom_item_image"
    )

    custom_personalize = fields.Char("Personalize", size=80, tracking=True)
    custom_line1 = fields.Char("Line 1", size=80, tracking=True)
    custom_line2 = fields.Char("Line 2", size=80, tracking=True)
    custom_line3 = fields.Char("Line 3", size=80, tracking=True)
    custom_initials = fields.Char("Initials", size=80, tracking=True)
    custom_font = fields.Char(string="Font", size=80, tracking=True)
    custom_fontcase = fields.Char(string="Font Case", size=80, tracking=True)
    custom_opentext = fields.Char(string="Open Text", size=80, tracking=True)
    custom_etail_ticket_no = fields.Char(
        string="Etail Ticket No", size=80, tracking=True
    )
    custom_customer_product = fields.Char(string="Customer SKU", tracking=True)

    custom_prod_size = fields.Selection(
        string="Size", related="product_id.custom_prod_size", store=True
    )
    custom_needle = fields.Integer(
        string="Needle", related="product_id.custom_needle", store=True
    )
    custom_tiff_file_url = fields.Char(string="TIF File URL", size=150, tracking=True)
    custom_tiff_file = fields.Binary(
        string="TIF File", related="custom_sale_order_line.custom_tiff_file"
    )
    custom_tiff_file_name = fields.Char(
        string="TIF File Name", related="custom_sale_order_line.custom_tiff_file_name"
    )

    custom_machine_no = fields.Selection(
        sel_custom_machine_no, string="Machine No", tracking=True
    )
    custom_is_binding = fields.Boolean(
        string="Binding Yarn", related="product_id.custom_is_binding"
    )
    custom_is_wash = fields.Boolean(
        string="Wash & Dry", related="product_id.custom_is_wash"
    )
    custom_is_dry = fields.Boolean(
        string="Dry only", related="product_id.custom_is_dry"
    )
    custom_is_press = fields.Boolean(
        string="Press", related="product_id.custom_is_press"
    )
    custom_prod_type = fields.Selection(
        string="Inventory Type", related="product_id.custom_prod_type"
    )
    custom_special_notation_tag_ids = fields.Many2many(
        comodel_name="product.tag",
        string="Special Notation",
        related="product_id.custom_special_notation_tag_ids",
    )
    custom_prod_time = fields.Float(string="Production Time", tracking=True)

    custom_current_url = fields.Char(string="URL")
    custom_stock_picking_id = fields.Many2one(
        comodel_name="stock.picking", string="Stock Picking"
    )
    custom_stock_picking_url = fields.Char(string="Picking URL")

    custom_order_no = fields.Char("Order No", size=80)

    custom_so_special_inst = fields.Html("Customer Special Instruction", related="custom_sale_order_line.order_id.custom_so_special_inst")

    custom_sale_order_line = fields.Many2one(
        comodel_name="sale.order.line", string="Sale Order Line"
    )

    custom_traveler_printed = fields.Boolean("Traveler Printed?")
    traveler_batch_count = fields.Integer('Traveler batch count', default=5, tracking=True)
    custom_sale_order_date = fields.Datetime(
        string="Order Date", related="custom_sale_order_line.order_id.date_order", store=True
    )

    @api.model
    def read_group(
        self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True
    ):
        res = super(CustomMrpProduction, self).read_group(
            domain,
            fields,
            groupby,
            offset=offset,
            limit=limit,
            orderby=orderby,
            lazy=lazy,
        )
        if "custom_prod_time" in fields:
            for line in res:
                if "__domain" in line:
                    lines = self.search(line["__domain"])
                    total_custom_prod_time = 0.0
                    for record in lines:
                        total_custom_prod_time += record.custom_prod_time
                    line["custom_prod_time"] = total_custom_prod_time
        return res

    custom_color_2 = fields.Many2one(comodel_name="product.product", string="Color 2")
    custom_color_3 = fields.Many2one(comodel_name="product.product", string="Color 3")
    custom_color_4 = fields.Many2one(comodel_name="product.product", string="Color 4")
    custom_color_5 = fields.Many2one(comodel_name="product.product", string="Color 5")
    custom_color_6 = fields.Many2one(comodel_name="product.product", string="Color 6")
    custom_color_7 = fields.Many2one(comodel_name="product.product", string="Color 7")

    custom_attribute_1 = fields.Many2one(
        comodel_name="product.attribute.value", string="Design 1"
    )

    custom_released = fields.Boolean(string="Released")
    custom_partner = fields.Many2one(comodel_name="res.partner", string="Customer")
    custom_is_scrap_mo = fields.Boolean(string="is Scrap Order?")
    custom_scrap_mrp_id = fields.Many2one(
        comodel_name="mrp.production", string="Scrap Order"
    )
    custom_mrp_parent_id = fields.Many2one(
        comodel_name="mrp.production", string="Parent Order"
    )
    custom_is_parent_mo = fields.Boolean(string="is Parent Order?")

    @api.onchange("product_id")
    def _onchange_custom_product_id(self):
        for production in self:
            if not production.custom_tiff_file_url:
                if production.product_id.custom_tiff_file_url:
                    production.custom_tiff_file_url = production.product_id.custom_tiff_file_url

    def custom_action_confirm(self):
        if ( not self.custom_tiff_file ) and ( not self.custom_tiff_file_url ):
            raise UserError(_("Cannot Proceed. Add TIFF File URL"))
        if not self.bom_id:
            raise UserError(_("Cannot Proceed. BoM missing"))
        if not self.move_raw_ids:
            raise UserError(_("Cannot Proceed. BoM components missing"))
        
        self.custom_released = True
        self.action_confirm()

    def action_confirm(self):
        for production in self:
            if (not production.bom_id) or (not production.move_raw_ids):
                production.custom_released = False
            if production.custom_released:
                super(CustomMrpProduction, production).action_confirm()
                proc_grp_id = self.env["procurement.group"].search(
                    [("name", "=", production.name)], limit=1
                )
                if production.state == "confirmed":
                    seq = 1
                    for component in production.move_raw_ids:
                        if production.product_id.custom_color_count == "1":
                            if seq == 1:
                                seq = 3
                        elif production.product_id.custom_color_count == "2":
                            if seq == 1:
                                seq = 3
                            elif seq == 3:
                                seq = 6
                        elif production.product_id.custom_color_count == "3":
                            if seq == 1:
                                seq = 3
                            elif seq == 3:
                                seq = 6
                            elif seq == 6:
                                seq = 7
                        elif production.product_id.custom_color_count == "4":
                            if seq == 1:
                                seq = 3
                            elif seq == 3:
                                seq = 4
                            elif seq == 4:
                                seq = 5
                            elif seq == 5:
                                seq = 6
                        elif production.product_id.custom_color_count == "6":
                            if seq == 1:
                                seq = 2
                            elif seq == 2:
                                seq = 3
                            elif seq == 3:
                                seq = 4
                            elif seq == 4:
                                seq = 5
                            elif seq == 5:
                                seq = 6
                            elif seq == 6:
                                seq = 7
                        component.custom_color_no = str(seq)
                        field_name = "custom_color_" + str(seq)
                        production.update({field_name: component.product_id.id})
                        if proc_grp_id:
                            component.group_id = proc_grp_id.id
        return True

    def button_mark_done(self):
        for production in self:
            if production.components_availability_state != "available":
                raise UserError(
                    _("Cannot Produce. All raw materials/components not available")
                )
        res = super().button_mark_done()
        return res

    def action_download_travel_ticket(self):
        self.ensure_one()
        if self.custom_traveler_printed:
            if self.env.user.has_group("mrp.group_mrp_manager"):
                message_id = self.env["custom.message.wizard2"].create(
                    {
                        "message": "Traveler is already printed once. Want to Reprint",
                        "production_id": self.id,
                    }
                )
                return {
                    "name": _("Message"),
                    "type": "ir.actions.act_window",
                    "view_mode": "form",
                    "res_model": "custom.message.wizard2",
                    # pass the id
                    "res_id": message_id.id,
                    "target": "new",
                }
            else:
                raise UserError(
                    _("Reprint of Traveler ticket not allowed. Contact Administrator")
                )
        order_url = (
            self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            + "/web#id=%s&view_type=form&model=mrp.production" % self.id
        )
        sale_order_id = self.env["sale.order"].search([("name", "=", self.origin)])
        if sale_order_id:
            picking_id = self.env["stock.picking"].search(
                [("sale_id", "=", sale_order_id.id)], limit=1
            )
            picking_url = (
                self.env["ir.config_parameter"].sudo().get_param("web.base.url")
                + "/web#id=%s&view_type=form&model=stock.picking" % picking_id.id
            )
        else:
            raise UserError(_("Sales Order Not Found !!!"))
        self.write(
            {
                "custom_current_url": order_url,
                "custom_stock_picking_id": picking_id,
                "custom_stock_picking_url": picking_url,
            }
        )
        xml_id = "custom_dropstitch.action_report_travel_ticket_label_102X45"
        if not xml_id:
            raise UserError(
                _("Unable to find report template for %s format", self.print_format)
            )
        self.custom_traveler_printed = True
        report = self.env.ref(xml_id).report_action(self)
        return report

    def action_confirm_orders(self):
        has_draft = False
        for rec in self:
            if rec.state == "draft":
                has_draft = True
                rec.custom_action_confirm()
        if not has_draft:
            raise UserError("Please select draft orders")

    def action_print_mass_traveller_tickets(self):
        xml_id = "custom_dropstitch.action_report_mass_travel_ticket_labels_102X45"
        if not xml_id:
            raise UserError(
                _("Unable to find report template for %s format", self.print_format)
            )
        manu_orders = self.env["mrp.production"].search(
            [("id", "in", self.ids), ("custom_traveler_printed", "=", False)]
        )
        if manu_orders:
            for manu_order in self:
                order_url = (
                    self.env["ir.config_parameter"].sudo().get_param("web.base.url")
                    + "/web#id=%s&view_type=form&model=mrp.production" % manu_order.id
                )
                sale_order_id = self.env["sale.order"].search([("name", "=", manu_order.origin)])
                if sale_order_id:
                    picking_id = self.env["stock.picking"].search(
                        [("sale_id", "=", sale_order_id.id)], limit=1
                    )
                    picking_url = (
                        self.env["ir.config_parameter"].sudo().get_param("web.base.url")
                        + "/web#id=%s&view_type=form&model=stock.picking" % picking_id.id
                    )
                else:
                    raise UserError(_("Sales Order Not Found !!!"))
                manu_order.write(
                    {
                        "custom_current_url": order_url,
                        "custom_stock_picking_id": picking_id,
                        "custom_stock_picking_url": picking_url,
                    }
                )

                manu_order.custom_traveler_printed = True
            report = self.env.ref(xml_id).report_action(manu_orders)
            return report
        else:
            raise UserError(
                _("All selected Traveler Tickets already printed once. Contact Administrator")
            )

    def action_download_tiff_file(self):
        self.ensure_one()
        if self.custom_tiff_file_url:
            file_id = self.extract_drive_file_id(self.custom_tiff_file_url)
            if not file_id:
                raise UserError("Invalid Google Drive file path")
            download_url = f"https://drive.google.com/uc?id={file_id}"
            response = requests.get(download_url)

            if response.status_code == 200:
                if response.headers["Content-Type"] == "application/octet-stream":
                    mimetype = "image/tif"
                else:
                    mimetype = response.headers["Content-Type"]
                # Save and ensure proper format
                from PIL import Image
                from io import BytesIO

                image = Image.open(BytesIO(response.content))
                buffer = BytesIO()
                image.save(buffer, format="tiff")
                buffer.seek(0)

                # Create attachment in Odoo
                attachment = self.env["ir.attachment"].create(
                    {
                        "name": self.name,
                        "type": "binary",
                        "datas": base64.b64encode(buffer.read()).decode("utf-8"),
                        "res_model": "mrp.production",
                        "res_id": self.id,
                        "mimetype": mimetype,
                    }
                )
                download_url = f"/download/file/{attachment.id}"

                # Return the download action
                return {
                    "type": "ir.actions.act_url",
                    "url": download_url,
                    "target": "self",
                }
            else:
                raise UserError("Failed to download the file. Check the URL/Access.")


    def action_download_custom_tiff_file(self):
        self.ensure_one()
        if self.custom_tiff_file:
            self.ensure_one()
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/mo_tiff/{self.id}',
                'target': 'self',
            }

            

    def extract_drive_file_id(self, url):
        uc_id_pattern = r"uc\?id=([a-zA-Z0-9_-]+)"
        file_d_pattern = r"/file/d/([a-zA-Z0-9_-]+)"

        match = re.search(uc_id_pattern, url)
        if match:
            return match.group(1)

        match = re.search(file_d_pattern, url)
        if match:
            return match.group(1)
        return None

    def action_merge(self):
        customer_id = False
        tiff_file = False
        sale_order_id = False
        product_id = False
        mo_order = False

        for production in self:
            mo_order = production
            if product_id:
                if product_id != production.product_id.id:
                    raise ValidationError(_("Product must be same for order merging"))
            else:
                product_id = production.product_id.id

            if not production.custom_tiff_file_url:
                raise ValidationError(
                    _("TIF File URL must be present to initiate order merging")
                )

            if customer_id:
                if customer_id != production.custom_partner.id:
                    raise ValidationError(_("Customer must be same for order merging"))
            else:
                customer_id = production.custom_partner.id

            if tiff_file:
                if tiff_file != production.custom_tiff_file_url:
                    raise ValidationError(
                        _("TIF File URL must be same for order merging")
                    )
            else:
                tiff_file = production.custom_tiff_file_url

            if sale_order_id:
                if sale_order_id != production.custom_sale_order_line.order_id.id:
                    raise ValidationError(
                        _("Sales Order must be same for order merging")
                    )
            else:
                sale_order_id = production.custom_sale_order_line.order_id.id

        res = super().action_merge()
        if res and "res_id" in res:
            prod_id = res["res_id"]
            prod_rec = self.env["mrp.production"].browse(prod_id)

            if mo_order:
                prod_rec.update(
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
                        "custom_sale_order_line": mo_order.custom_sale_order_line,
                        "custom_customer_product": mo_order.custom_customer_product,
                        "custom_etail_ticket_no": mo_order.custom_etail_ticket_no,
                        "custom_opentext": mo_order.custom_opentext,
                        "custom_fontcase": mo_order.custom_fontcase,
                        "custom_font": mo_order.custom_font,
                    }
                )

        return res
    
    @api.depends('procurement_group_id', 'procurement_group_id.stock_move_ids.group_id')
    def _compute_picking_ids(self):
        for order in self:
            order.picking_ids = self.env['stock.picking'].search([('sale_id', '=', order.custom_sale_order_line.order_id.id)])
            order.delivery_count = len(order.picking_ids)
