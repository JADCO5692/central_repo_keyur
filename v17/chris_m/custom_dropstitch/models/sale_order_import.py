from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError
import csv
import base64
import xlrd
import logging

_logger = logging.getLogger(__name__)

from io import BytesIO
from odoo import models, fields, api

from io import StringIO
from collections import defaultdict

IMPORT_ORDER_STATE = [("draft", "Draft"), ("done", "Completed"), ("error", "Failed")]

sel_custom_prod_size = [
    ("6_50", "6 * 50"),
    ("10_80", "10 * 80"),
    ("12_78", "12 * 78"),
    ("12_84", "12 * 84"),
    ("15_15", "15 * 15"),
    ("20_20", "20 * 20"),
    ("22_28", "22 * 28"),
    ("22_30", "22 * 30"),
    ("30_40", "30 * 40"),
    ("31_38", "31 * 38"),
    ("32_105", "32 * 105"),
    ("36_48", "36 * 48"),
    ("36_53", "36 * 53"),
    ("36_54", "36 * 54"),
    ("40_30", "40 * 30"),
    ("40_40", "40 * 40"),
    ("40_50", "40 * 50"),
    ("40_60", "40 * 60"),
    ("48_36", "48 * 36"),
    ("50_50", "50 * 50"),
    ("50_56", "50 * 56"),
    ("50_60", "50 * 60"),
    ("50_62", "50 * 62"),
    ("50_70", "50 * 70"),
    ("55_65", "55 * 65"),
    ("60_50", "60 * 50"),
    ("60_60", "60 * 60"),
    ("60_70", "60 * 70"),
    ("60_72", "60 * 72"),
    ("60_80", "60 * 80"),
    ("60_84", "60 * 84"),
    ("60_106", "60 * 106"),
]


class CustomOrderProcessingImport(models.Model):
    _name = "custom.order.processing.import"
    _description = "Order Processing"
    _order = "id desc"
    _inherit = [
        "portal.mixin",
        "product.catalog.mixin",
        "mail.thread",
        "mail.activity.mixin",
        "utm.mixin",
    ]

    partner_id = fields.Many2one("res.partner", string="Customer", tracking=True)
    sale_order_id = fields.Many2one("sale.order", string="Sales Order", tracking=True)

    name = fields.Char(
        string="Sequence",
        default=lambda self: _("New"),
        required=True,
        copy=False,
        readonly=False,
    )
    file_name = fields.Char(string="File Name")
    template_name = fields.Char(string="Template Name")
    reference = fields.Char("Reference", tracking=True)

    import_csv = fields.Binary(string="Import CSV")
    template_csv = fields.Binary(string="Customer Template")

    order_lines = fields.One2many(
        "custom.order.line.import", "order_id", string="Order Lines"
    )
    error_order_lines = fields.One2many(
        "custom.order.line.import",
        "order_id",
        string="Error Order Lines",
        domain=[("error_status", "=", True)],
    )

    custom_mass_imp_val = fields.Selection(
        string="Mass Import Validation", related="partner_id.custom_mass_imp_val"
    )

    state = fields.Selection(
        selection=IMPORT_ORDER_STATE,
        string="Status",
        readonly=True,
        copy=False,
        index=True,
        tracking=3,
        default="draft",
    )

    error_message = fields.Text(string="Error Message", tracking=True)
    order_date = fields.Date("Order Date", default=fields.Date.today, tracking=True)
    sale_order_count = fields.Integer(
        string="Sale Order Count", compute="_compute_sale_order_count"
    )

    def _compute_sale_order_count(self):
        for record in self:
            sale_orders = self.env["sale.order"].search(
                [("custom_import_id", "=", record.id)]
            )
            record.sale_order_count = len(sale_orders)

    def action_show_sale_order_count(self):
        self.ensure_one()
        sale_orders = self.env["sale.order"].search(
            [("custom_import_id", "=", self.id)]
        )
        self.ensure_one()

        tree_view = self.env.ref("sale.view_quotation_tree_with_onboarding")
        form_view = self.env.ref("sale.view_order_form")

        return {
            "type": "ir.actions.act_window",
            "name": "Sales Order",
            "res_model": "sale.order",
            "view_mode": "form",
            "views": [(tree_view.id, "tree"), (form_view.id, "form")],
            "view_id": tree_view.id,
            "domain": [("custom_import_id", "=", self.id)],
            "context": dict(self.env.context, create=False),
            "target": "current",
        }

    @api.onchange("import_csv")
    def _onchange_import_csv(self):
        if self.order_lines:
            self.order_lines.unlink()
            self.error_message = ""

        if self.import_csv:
            # Decode the base64 encoded xls file
            file_content = base64.b64decode(self.import_csv)
            file_io = BytesIO(file_content)

            # Open the workbook
            workbook = xlrd.open_workbook(file_contents=file_io.read())
            sheet = workbook.sheet_by_index(
                0
            )  # Assuming you want to read the first sheet
            order_lines_data = []
            headers = sheet.row_values(0)
            for row_idx in range(1, sheet.nrows):
                row_values = sheet.row_values(row_idx)
                row_dict = dict(zip(headers, row_values))
                custom_gift_mess = row_dict.get("Gift Message") or ""
                if custom_gift_mess and custom_gift_mess.strip():
                    # Split the string by newline characters
                    lines = custom_gift_mess.split("\n")
                    # Enclose each line with <p> and </p>
                    custom_gift_mess = "".join(f"<p>{line}</p>" for line in lines)
                order_lines_data.append(
                    (
                        0,
                        0,
                        {
                            "import_order_id": self.return_correct_excel_value(
                                row_dict.get("OrderID")
                            ),
                            "customer_ref": self.return_correct_excel_value(
                                row_dict.get("Customer Reference")
                            ),
                            "ship_to": (
                                row_dict.get("ShipTo") if row_dict.get("ShipTo") else ""
                            ),
                            "company_atten": (
                                row_dict.get("Purchaser")
                                if row_dict.get("Purchaser")
                                else ""
                            ),
                            "address": (
                                row_dict.get("Address")
                                if row_dict.get("Address")
                                else ""
                            ),
                            "address_2": (
                                row_dict.get("Address2")
                                if row_dict.get("Address2")
                                else ""
                            ),
                            "city": (
                                row_dict.get("City") if row_dict.get("City") else ""
                            ),
                            "state": (
                                row_dict.get("State") if row_dict.get("State") else ""
                            ),
                            "country": (
                                row_dict.get("Country")
                                if row_dict.get("Country")
                                else ""
                            ),
                            "zip": self.return_correct_excel_value(row_dict.get("Zip")),
                            "product": (
                                row_dict.get("Product")
                                if row_dict.get("Product")
                                else ""
                            ),
                            "colorway": (
                                row_dict.get("Colorway")
                                if row_dict.get("Colorway")
                                else ""
                            ),
                            "alphabets": (
                                row_dict.get("Alphabets")
                                if row_dict.get("Alphabets")
                                else ""
                            ),
                            "size": (
                                row_dict.get("Size") if row_dict.get("Size") else ""
                            ),
                            "font_case": (
                                row_dict.get("FontCase")
                                if row_dict.get("FontCase")
                                else ""
                            ),
                            "font": (
                                row_dict.get("Font") if row_dict.get("Font") else ""
                            ),
                            "personalize_line_1": (
                                str((row_dict.get("Line1")))
                                if row_dict.get("Line1")
                                else ""
                            ),
                            "personalize_line_2": (
                                str((row_dict.get("Line2")))
                                if row_dict.get("Line2")
                                else ""
                            ),
                            "personalize_line_3": (
                                str((row_dict.get("Line3")))
                                if row_dict.get("Line3")
                                else ""
                            ),
                            "quantity": row_dict.get("Quantity"),
                            "open_text": (
                                str((row_dict.get("Open Text")))
                                if row_dict.get("Open Text")
                                else ""
                            ),
                            "etail_ticket_no": self.return_correct_excel_value(
                                row_dict.get("Etail Ticket No")
                            ),
                            "custom_color_3": (
                                str((row_dict.get("Yarn(MTO)1")))
                                if row_dict.get("Yarn(MTO)1")
                                else ""
                            ),
                            "custom_color_6": (
                                str((row_dict.get("Yarn(MTO)2")))
                                if row_dict.get("Yarn(MTO)2")
                                else ""
                            ),
                            "custom_color_7": (
                                str((row_dict.get("Yarn(MTO)Metallic")))
                                if row_dict.get("Yarn(MTO)Metallic")
                                else ""
                            ),
                            "custom_design": self.return_correct_excel_value(
                                row_dict.get("Design")
                            ),
                            "custom_gift_mess": custom_gift_mess,
                        },
                    )
                )
            self.order_lines = order_lines_data

    def return_correct_excel_value(self, val):
        if val:
            if isinstance(val, float) and val.is_integer():
                return str(int(val))  # Convert to integer if it's a whole number
        else:
            val = ""
        return str(val)  # Return the original value otherwise

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            seq = (
                self.env["ir.sequence"].next_by_code("custom.order.processing.import")
                or "/"
            )
            vals["name"] = seq
        return super(CustomOrderProcessingImport, self).create(vals_list)

    def action_create_order(self):
        self.ensure_one()  # Ensure the record is saved
        if self.partner_id:
            data_final = []
            route_obj = self.env.ref("custom_dropstitch.record_custom_route")
            error_msg = ""

            for row in self.order_lines:
                header_vals = {
                    "OrderID": row.import_order_id,
                    "OrderDate": self.order_date,
                    "CustomerReference": row.customer_ref,
                    "ShipTo": row.ship_to,
                    "Purchaser": row.company_atten,
                    "Address": row.address,
                    "Address2": row.address_2,
                    "City": row.city,
                    "State": row.state,
                    "Country": row.country,
                    "Zip": row.zip,
                    "Product": row.product,
                    "Colorway": row.colorway,
                    "Alphabets": row.alphabets,
                    "Size": row.size or "",
                    "FontCase": row.font_case,
                    "Font": row.font,
                    "PersonalizeLine1": row.personalize_line_1,
                    "PersonalizeLine2": row.personalize_line_2,
                    "PersonalizeLine3": row.personalize_line_3,
                    "Quantity": row.quantity,
                    "RowID": row.id,
                    "OpenText": row.open_text,
                    "EtailTicketNo": row.etail_ticket_no,
                    "YarnMTO1": row.custom_color_3,
                    "YarnMTO2": row.custom_color_6,
                    "YarnMTO3": row.custom_color_7,
                    "Design": row.custom_design,
                    "GiftMessage": row.custom_gift_mess,
                }
                data_final.append(header_vals)
            grouped_data = defaultdict(list)
            grouped_data2 = defaultdict(list)

            for entry in data_final:
                key = (
                    entry["ShipTo"],
                    entry["City"],
                    entry["State"],
                    entry["Country"],
                    entry["OrderDate"],
                    entry["Zip"],
                    entry["Purchaser"],
                )
                grouped_data[key].append(entry)
            grouped_data = dict(grouped_data)

            for key, values in grouped_data.items():
                for value in values:
                    import_row_id = self.env["custom.order.line.import"].search(
                        [("id", "=", value["RowID"])]
                    )
                    (
                        error,
                        product_template_id,
                        product_variant_rec,
                        product_attribute_yarn1,
                        product_attribute_yarn2,
                        product_attribute_yarn3,
                        product_attribute_design,
                        delivery_rec,
                    ) = self.validate_row(value)
                    value["product_template_id"] = product_template_id
                    value["product_variant_rec"] = product_variant_rec

                    value["product_attribute_yarn1"] = product_attribute_yarn1
                    value["product_attribute_yarn2"] = product_attribute_yarn2
                    value["product_attribute_yarn3"] = product_attribute_yarn3
                    value["product_attribute_design"] = product_attribute_design
                    grouped_data2[key].append(delivery_rec)

                    if len(error) > 0:
                        import_row_id.error_status = True
                        import_row_id.error_message = error
                        error_msg = error_msg + error
                    else:
                        import_row_id.error_status = False
                        import_row_id.error_message = ""

            if len(error_msg) > 0:
                self.write({"error_message": error_msg, "state": "error"})
                return True
            else:
                grouped_data2 = dict(grouped_data2)
                for key, values in grouped_data.items():
                    name = key[0]
                    order_date_group = key[4]
                    create_delivery = False
                    sales_obj = False
                    dropship = False
                    purchaser = False
                    if key[6]:
                        dropship = True
                        purchaser = key[6]
                    if name:
                        order_header_vals = {
                            "partner_id": self.partner_id.id,
                            "partner_invoice_id": self.partner_id.id,
                            "partner_shipping_id": grouped_data2[key][0].id if grouped_data2[key][0] else False,
                            "date_order": order_date_group,
                            "currency_id": self.env.user.company_id.currency_id.id,
                            "company_id": self.env.user.company_id.id,
                            "custom_policy": self.partner_id.custom_policy,
                            "payment_term_id": self.partner_id.property_payment_term_id.id,
                            "custom_import_id": self.id,
                            "client_order_ref": self.reference,
                            "custom_dropship_order": dropship,
                            "custom_from": purchaser,
                        }
                    else:
                        order_header_vals = {
                            "partner_id": self.partner_id.id,
                            "partner_invoice_id": self.partner_id.id,
                            "partner_shipping_id": self.partner_id.id,
                            "date_order": order_date_group,
                            "currency_id": self.env.user.company_id.currency_id.id,
                            "company_id": self.env.user.company_id.id,
                            "custom_policy": self.partner_id.custom_policy,
                            "payment_term_id": self.partner_id.property_payment_term_id.id,
                            "custom_import_id": self.id,
                            "client_order_ref": self.reference,
                            "custom_dropship_order": dropship,
                            "custom_from": purchaser,
                        }
                    if self.partner_id.shipstation_store_id:
                        shipstation_store_id = self.partner_id.shipstation_store_id
                        order_header_vals.update({
                            'shipstation_store_id': shipstation_store_id and shipstation_store_id.id,
                            'shipstation_instance_id': shipstation_store_id and shipstation_store_id.shipstation_instance_id.id
                        })
                    sales_obj = self.env["sale.order"].create(order_header_vals)
                    sales_obj._compute_require_payment()
                    sales_obj._compute_prepayment_percent()
                    sales_obj._onchange_custom_partner_id()
                    sales_obj._compute_allowed_customer_ids()
                    if sales_obj:
                        if sales_obj.team_id and not self.partner_id.shipstation_store_id:
                            team_id = sales_obj.team_id
                            shipstation_store_id = team_id.with_company(sales_obj.company_id.id).store_id or False
                            order_header_vals.update({
                                'shipstation_store_id': shipstation_store_id and shipstation_store_id.id,
                                'shipstation_instance_id': shipstation_store_id and shipstation_store_id.shipstation_instance_id.id
                            })
                        amount_total = 0
                        insert_values = []
                        error_flag = False
                        error_msg = ""
                        sale_order_lines_data = []
                        for value in values:
                            errors = ""
                            custom_line1 = ""
                            custom_line2 = ""
                            custom_line3 = ""
                            row_error_message = ""
                            route_id = False
                            error_flag = False
                            product_variant_rec = False
                            attribute_id_ids = []
                            attribute_value_ids = []

                            personalize_line1_excel = value["PersonalizeLine1"] or ""
                            personalize_line2_excel = value["PersonalizeLine2"] or ""
                            personalize_line3_excel = value["PersonalizeLine3"] or ""

                            import_row_id = self.env["custom.order.line.import"].search(
                                [("id", "=", value["RowID"])]
                            )

                            product_template_id = value["product_template_id"]
                            product_variant_rec = value["product_variant_rec"]

                            sales_obj.custom_gift_mess = value["GiftMessage"] or ""

                            if (
                                personalize_line1_excel
                                or personalize_line2_excel
                                or personalize_line3_excel
                            ):
                                if not product_variant_rec and not (
                                    value["Colorway"] or value["Alphabets"]
                                ):
                                    product_variant_rec = self.env[
                                        "product.product"
                                    ].search(
                                        [("name", "=ilike", value["Product"])], limit=1
                                    )
                                for (
                                    each_attr_line
                                ) in product_template_id.attribute_line_ids:
                                    if (
                                        each_attr_line.attribute_id.name
                                        == "Personalize"
                                    ):
                                        for each_val in each_attr_line.value_ids:
                                            if (
                                                each_val.name == "1 Line"
                                                and personalize_line1_excel
                                            ):
                                                custom_line1 = (
                                                    "\nLine 1 :"
                                                    + personalize_line1_excel
                                                )
                                            if (
                                                each_val.name == "2 Lines"
                                                and personalize_line2_excel
                                            ):
                                                custom_line1 = (
                                                    "\nLine 1 :"
                                                    + personalize_line1_excel
                                                )
                                                custom_line2 = (
                                                    "\nLine 2 :"
                                                    + personalize_line2_excel
                                                )
                                            if (
                                                each_val.name == "3 Lines"
                                                and personalize_line3_excel
                                            ):
                                                custom_line1 = (
                                                    "\nLine 1 :"
                                                    + personalize_line1_excel
                                                )
                                                custom_line2 = (
                                                    "\nLine 2 :"
                                                    + personalize_line2_excel
                                                )
                                                custom_line3 = (
                                                    "\nLine 3 :"
                                                    + personalize_line3_excel
                                                )
                                route_id = route_obj.id if len(route_obj) else False

                            customer_sku_excel = value["CustomerReference"] or ""
                            font_excel = value["Font"] or ""
                            font_case_excel = value["FontCase"] or ""

                            if font_excel:
                                font_excel = "\nFont :" + font_excel
                                route_id = route_obj.id if len(route_obj) else False
                            if font_case_excel:
                                font_case_excel = "\nFont Case :" + font_case_excel
                                route_id = route_obj.id if len(route_obj) else False

                            sub_total = product_variant_rec.lst_price * float(
                                value["Quantity"]
                            )
                            sale_order_lines_data.append(
                                (
                                    0,
                                    0,
                                    {
                                        "order_id": sales_obj.id,
                                        "state": "draft",
                                        "name": product_variant_rec.name
                                        + custom_line1
                                        + custom_line2
                                        + custom_line3
                                        + font_excel
                                        + font_case_excel,
                                        "product_id": product_variant_rec.id,
                                        "custom_customer_product": customer_sku_excel,
                                        "product_uom": product_variant_rec.uom_id.id,
                                        "product_uom_qty": value["Quantity"],
                                        "price_unit": product_variant_rec.lst_price,
                                        "price_subtotal": sub_total,
                                        "price_total": sub_total,
                                        "customer_lead": 10,
                                        "company_id": self.env.user.company_id.id,
                                        "currency_id": self.env.user.company_id.currency_id.id,
                                        "custom_line1": personalize_line1_excel,
                                        "custom_line2": personalize_line2_excel,
                                        "custom_line3": personalize_line3_excel,
                                        "custom_order_no": value["OrderID"],
                                        "route_id": route_id,
                                        "custom_font": value["Font"] or "",
                                        "custom_fontcase": value["FontCase"] or "",
                                        "custom_opentext": value["OpenText"] or "",
                                        "custom_etail_ticket_no": value["EtailTicketNo"]
                                        or "",
                                        "custom_color_3": (
                                            value["product_attribute_yarn1"]
                                            if value["product_attribute_yarn1"]
                                            else ""
                                        ),
                                        "custom_color_6": (
                                            value["product_attribute_yarn2"]
                                            if value["product_attribute_yarn2"]
                                            else ""
                                        ),
                                        "custom_color_7": (
                                            value["product_attribute_yarn3"]
                                            if value["product_attribute_yarn3"]
                                            else ""
                                        ),
                                        "custom_attribute_1": (
                                            value["product_attribute_design"].id
                                            if value["product_attribute_design"]
                                            else ""
                                        ),
                                        "custom_item_image": (
                                            value[
                                                "product_attribute_design"
                                            ].custom_design_image
                                            if value["product_attribute_design"]
                                            else ""
                                        ),
                                    },
                                )
                            )
                            amount_total += sub_total
                            import_row_id.error_status = False

                        sales_obj._compute_amounts()
                        sales_obj.write(
                            {
                                "amount_to_invoice": amount_total,
                                "amount_total": amount_total,
                            }
                        )
                        self.write({"error_message": "", "state": "done"})
                        sales_obj.order_line = sale_order_lines_data
                        for each_order_line in sales_obj.order_line:
                            each_order_line._onchange_custom_product_no_variant_attribute_value_ids()

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.template_csv = self.partner_id.custom_sale_order_template_id or False
            self.template_name = (
                self.partner_id.custom_sale_order_template_name or False
            )

    def validate_row(self, value):
        errors = ""
        delivery_rec = False

        if value.get("ShipTo") and value.get("Product"):
            state_id = False
            country_id = False
            parent_id = False

            if value.get("State"):
                state = value["State"]
                state_id = self.env["res.country.state"].search(
                    [("name", "=ilike", state)], limit=1
                )
                if not state_id:
                    state_id = self.env["res.country.state"].search(
                        [("code", "=ilike", state)], limit=1
                    )
                    if not state_id:
                        errors = (
                            errors
                            + " \n "
                            + " - State not found for "
                            + value.get("ShipTo")
                        )
            if not value.get("Country"):
                errors = (
                    errors + " \n " + " - Country not found for " + value.get("ShipTo")
                )
            else:
                country = value["Country"]
                country_id = self.env["res.country"].search(
                    [("name", "=ilike", country)], limit=1
                )
                if not country_id:
                    errors = (
                        errors
                        + " \n "
                        + " - Country not found for "
                        + value.get("ShipTo")
                    )
            if country_id:
                search_term = False
                if value.get("ShipTo"):
                    if search_term:
                        search_term = search_term + " - " + value.get("ShipTo")
                    else:
                        search_term = value.get("ShipTo")

                delivery_rec = self.env["res.partner"].search(
                    [("name", "=ilike", search_term)], limit=1
                )

                company_id = self.partner_id.id

                if not delivery_rec and company_id:
                    partner_vals = {
                        "name": value.get("ShipTo"),
                        "type": "delivery",
                        "street": value.get("Address"),
                        "street2": value.get("Address2"),
                        "city": value.get("City"),
                        "state_id": state_id.id if state_id else False,
                        "country_id": country_id.id,
                        "zip": value.get("Zip"),
                        "is_company": False,
                        "custom_generate_type": "mass_import",
                    }
                    delivery_rec = self.env["res.partner"].create(partner_vals)

        if not value.get("OrderID"):
            if value.get("Product"):
                errors = (
                    errors
                    + " \n "
                    + " - OrderID is required for '"
                    + value.get("Product")
                    + "'"
                )
            else:
                errors = errors + " \n " + " - OrderID is required for the row"

        if value.get("Quantity") == 0 or not value.get("Quantity"):
            if value.get("Product"):
                errors = (
                    errors
                    + " \n "
                    + " - Quantity is required for '"
                    + value.get("Product")
                    + "'"
                )
            else:
                errors = errors + " \n " + " - Quantity is required for the row"

        (
            errors,
            product_template_id,
            product_variant_rec,
            product_attribute_yarn1,
            product_attribute_yarn2,
            product_attribute_yarn3,
            product_attribute_design,
        ) = self.validate_get_product_var(value, errors)

        return (
            errors,
            product_template_id,
            product_variant_rec,
            product_attribute_yarn1,
            product_attribute_yarn2,
            product_attribute_yarn3,
            product_attribute_design,
            delivery_rec,
        )

    def validate_get_product_var(self, value, errors):
        product_template_id = False
        product_variant_rec = False

        product_attribute_colorway = False
        product_attribute_alphabet = False
        product_attribute_size = False

        check_alphabhet = False
        check_colorway = False
        check_size = False

        check_personalize_allowed = False

        check_line1_allowed = False
        check_line2_allowed = False
        check_line3_allowed = False
        check_stock_allowed = False

        attribute_id_ids = []
        attribute_value_ids = []

        attribute_colorway = self.partner_id.custom_mass_imp_colorway
        attribute_alphabet = self.env["ir.model.data"]._xmlid_to_res_id(
            "custom_dropstitch.custom_alphabet_pre_set_bau"
        )
        attribute_size = self.env["ir.model.data"]._xmlid_to_res_id(
            "custom_dropstitch.custom_size_pre_set_bau"
        )
        attribute_personalize = self.env["ir.model.data"]._xmlid_to_res_id(
            "custom_dropstitch.custom_personalize_2"
        )

        product_attribute_yarn1 = False
        product_attribute_yarn2 = False
        product_attribute_yarn3 = False
        product_attribute_design = False

        product_attribute_yarn1_component = False
        product_attribute_yarn2_component = False
        product_attribute_yarn3_component = False

        attribute_yarn_mto = self.env["ir.model.data"]._xmlid_to_res_id(
            "custom_dropstitch.custom_yarn_colour_no"
        )
        attribute_design = self.env["ir.model.data"]._xmlid_to_res_id(
            "custom_dropstitch.custom_design_but_ac"
        )
        attribute_design_met = self.env["ir.model.data"]._xmlid_to_res_id(
            "custom_dropstitch.custom_design_but_ac_m"
        )

        if not value.get("Product"):
            errors = errors + " \n " + " - Product Code Is required. "
        else:
            product = value.get("Product")
            product_template_id = self.env["product.template"].search(
                [("name", "=ilike", product)], limit=1
            )
            if not product_template_id:
                errors = (
                    errors
                    + " \n "
                    + " - Product not found in Odoo for '"
                    + value.get("Product")
                    + "'"
                )

        if self.partner_id.custom_mass_imp_val != "design":
            if value.get("Colorway"):
                check_colorway = True
                product_attribute_colorway = self.env["product.attribute.value"].search(
                    [
                        ("name", "=ilike", value.get("Colorway")),
                        ("attribute_id", "=", attribute_colorway.id),
                    ],
                    limit=1,
                )
                if product_attribute_colorway:
                    product_attribute_colorway = self.env[
                        "product.attribute.value"
                    ].search(
                        [
                            ("name", "=ilike", value.get("Colorway")),
                            ("attribute_id", "=", attribute_colorway.id),
                            (
                                "pav_attribute_line_ids.product_tmpl_id",
                                "=",
                                product_template_id.id,
                            ),
                        ],
                        limit=1,
                    )
                    if product_attribute_colorway:
                        attribute_value_ids.append(product_attribute_colorway.id)
                    else:
                        errors = (
                            errors
                            + " \n "
                            + " - Colorway '"
                            + value.get("Colorway")
                            + "' not found in '"
                            + value.get("Product")
                            + "'"
                        )
                else:
                    errors = (
                        errors
                        + " \n "
                        + " - Colorway '"
                        + value.get("Colorway")
                        + "' not found in the system for '"
                        + value.get("Product")
                        + "'"
                    )

            if value.get("Alphabets"):
                check_alphabhet = True
                product_attribute_alphabet = self.env["product.attribute.value"].search(
                    [
                        ("name", "=ilike", value.get("Alphabets")),
                        ("attribute_id", "=", attribute_alphabet),
                    ],
                    limit=1,
                )
                if product_attribute_alphabet:
                    product_attribute_alphabet = self.env[
                        "product.attribute.value"
                    ].search(
                        [
                            ("name", "=ilike", value.get("Alphabets")),
                            ("attribute_id", "=", attribute_alphabet),
                            (
                                "pav_attribute_line_ids.product_tmpl_id",
                                "=",
                                product_template_id.id,
                            ),
                        ],
                        limit=1,
                    )
                    if product_attribute_alphabet:
                        attribute_value_ids.append(product_attribute_alphabet.id)
                    else:
                        errors = (
                            errors
                            + " \n "
                            + " - Alphabets '"
                            + value.get("Alphabets")
                            + "' not found in '"
                            + value.get("Product")
                            + "'"
                        )
                else:
                    errors = (
                        errors
                        + " \n "
                        + " - Alphabets '"
                        + value.get("Alphabets")
                        + "' not found in the system for '"
                        + value.get("Product")
                        + "'"
                    )

            if self.partner_id.custom_mass_imp_val == "size" and value.get("Size"):
                check_size = True
                product_attribute_size = self.env["product.attribute.value"].search(
                    [
                        ("name", "=ilike", value.get("Size")),
                        ("attribute_id", "=", attribute_size),
                    ],
                    limit=1,
                )
                if product_attribute_size:
                    product_attribute_size = self.env["product.attribute.value"].search(
                        [
                            ("name", "=ilike", value.get("Size")),
                            ("attribute_id", "=", attribute_size),
                            (
                                "pav_attribute_line_ids.product_tmpl_id",
                                "=",
                                product_template_id.id,
                            ),
                        ],
                        limit=1,
                    )
                    if product_attribute_size:
                        attribute_value_ids.append(product_attribute_size.id)
                    else:
                        errors = (
                            errors
                            + " \n "
                            + " - Size '"
                            + value.get("Size")
                            + "' not found in '"
                            + value.get("Product")
                            + "'"
                        )
                else:
                    errors = (
                        errors
                        + " \n "
                        + " - Size '"
                        + value.get("Size")
                        + "' not found in the system for '"
                        + value.get("Product")
                        + "'"
                    )
        else:
            color_1_ok = False
            color_2_ok = False
            color_3_ok = False
            if not value.get("YarnMTO1"):
                errors = errors + " \n " + " - Yarn(MTO) 1 Is required. "
            else:
                product_attribute_yarn1 = self.env["product.attribute.value"].search(
                    [
                        ("name", "=ilike", value.get("YarnMTO1")),
                        ("attribute_id", "=", attribute_yarn_mto),
                    ],
                    limit=1,
                )
                if product_attribute_yarn1:
                    product_attribute_yarn1 = self.env[
                        "product.attribute.value"
                    ].search(
                        [
                            ("name", "=ilike", value.get("YarnMTO1")),
                            ("attribute_id", "=", attribute_yarn_mto),
                            (
                                "pav_attribute_line_ids.product_tmpl_id",
                                "=",
                                product_template_id.id,
                            ),
                        ],
                        limit=1,
                    )
                    if product_attribute_yarn1:
                        color_1_ok = True
                        product_attribute_yarn1_component = (
                            product_attribute_yarn1.custom_product_component.id
                        )
                    else:
                        errors = (
                            errors
                            + " \n "
                            + " - Yarn 1 '"
                            + value.get("YarnMTO1")
                            + "' not found in '"
                            + value.get("Product")
                            + "'"
                        )
                else:
                    errors = (
                        errors
                        + " \n "
                        + " - Yarn 1 '"
                        + value.get("YarnMTO1")
                        + "' not found in the system for '"
                        + value.get("Product")
                        + "'"
                    )

            if not value.get("YarnMTO2"):
                errors = errors + " \n " + " - Yarn(MTO) 2 Is required. "
            else:
                product_attribute_yarn2 = self.env["product.attribute.value"].search(
                    [
                        ("name", "=ilike", value.get("YarnMTO2")),
                        ("attribute_id", "=", attribute_yarn_mto),
                    ],
                    limit=1,
                )
                if product_attribute_yarn2:
                    product_attribute_yarn2 = self.env[
                        "product.attribute.value"
                    ].search(
                        [
                            ("name", "=ilike", value.get("YarnMTO2")),
                            ("attribute_id", "=", attribute_yarn_mto),
                            (
                                "pav_attribute_line_ids.product_tmpl_id",
                                "=",
                                product_template_id.id,
                            ),
                        ],
                        limit=1,
                    )
                    if product_attribute_yarn2:
                        color_2_ok = True
                        product_attribute_yarn2_component = (
                            product_attribute_yarn2.custom_product_component.id
                        )
                    else:
                        errors = (
                            errors
                            + " \n "
                            + " - Yarn 2 '"
                            + value.get("YarnMTO2")
                            + "' not found in '"
                            + value.get("Product")
                            + "'"
                        )
                else:
                    errors = (
                        errors
                        + " \n "
                        + " - Yarn 2 '"
                        + value.get("YarnMTO2")
                        + "' not found in the system for '"
                        + value.get("Product")
                        + "'"
                    )

            if product_template_id.custom_color_count == "3":
                if not value.get("YarnMTO3"):
                    errors = errors + " \n " + " - Yarn(MTO) 3 Is required. "
                else:
                    product_attribute_yarn3 = self.env[
                        "product.attribute.value"
                    ].search(
                        [
                            ("name", "=ilike", value.get("YarnMTO3")),
                            ("attribute_id", "=", attribute_yarn_mto),
                        ],
                        limit=1,
                    )
                    if product_attribute_yarn3:
                        product_attribute_yarn3 = self.env[
                            "product.attribute.value"
                        ].search(
                            [
                                ("name", "=ilike", value.get("YarnMTO3")),
                                ("attribute_id", "=", attribute_yarn_mto),
                                (
                                    "pav_attribute_line_ids.product_tmpl_id",
                                    "=",
                                    product_template_id.id,
                                ),
                            ],
                            limit=1,
                        )
                        if product_attribute_yarn3:
                            color_3_ok = True
                            product_attribute_yarn3_component = (
                                product_attribute_yarn3.custom_product_component.id
                            )
                        else:
                            errors = (
                                errors
                                + " \n "
                                + " - Yarn 3 '"
                                + value.get("YarnMTO3")
                                + "' not found in '"
                                + value.get("Product")
                                + "'"
                            )
                    else:
                        errors = (
                            errors
                            + " \n "
                            + " - Yarn 3 '"
                            + value.get("YarnMTO3")
                            + "' not found in the system for '"
                            + value.get("Product")
                            + "'"
                        )
            if not value.get("Design"):
                errors = errors + " \n " + " - Design Is required. "
            else:
                if product_template_id.custom_color_count == "3":
                    attribute_design = attribute_design_met
                product_attribute_design = self.env["product.attribute.value"].search(
                    [
                        ("name", "=ilike", value.get("Design")),
                        ("attribute_id", "=", attribute_design),
                    ],
                    limit=1,
                )
                if product_attribute_design:
                    product_attribute_design = self.env[
                        "product.attribute.value"
                    ].search(
                        [
                            ("name", "=ilike", value.get("Design")),
                            ("attribute_id", "=", attribute_design),
                            (
                                "pav_attribute_line_ids.product_tmpl_id",
                                "=",
                                product_template_id.id,
                            ),
                        ],
                        limit=1,
                    )
                    if not product_attribute_design:
                        errors = (
                            errors
                            + " \n "
                            + " - Design '"
                            + value.get("Design")
                            + "' not found in '"
                            + value.get("Product")
                            + "'"
                        )
                else:
                    errors = (
                        errors
                        + " \n "
                        + " - Design '"
                        + value.get("Design")
                        + "' not found in the system for '"
                        + value.get("Product")
                        + "'"
                    )

        if product_template_id:
            color_loop = 0
            for each_attr_line in product_template_id.attribute_line_ids:
                if self.partner_id.custom_mass_imp_val != "design":
                    if each_attr_line.attribute_id.id == attribute_colorway.id:
                        attribute_id_ids.append(attribute_colorway.id)
                        if not check_colorway:
                            errors = (
                                errors
                                + " \n "
                                + " - Kindly provide value for Attribute '"
                                + each_attr_line.attribute_id.name
                                + "' for '"
                                + value.get("Product")
                                + "'"
                            )
                    if each_attr_line.attribute_id.id == attribute_alphabet:
                        attribute_id_ids.append(attribute_alphabet)
                        if not check_alphabhet:
                            errors = (
                                errors
                                + " \n "
                                + " - Kindly provide value for Attribute '"
                                + each_attr_line.attribute_id.name
                                + "' for '"
                                + value.get("Product")
                                + "'"
                            )
                    if self.partner_id.custom_mass_imp_val == "size":
                        if each_attr_line.attribute_id.id == attribute_size:
                            attribute_id_ids.append(attribute_size)
                            if not check_size:
                                errors = (
                                    errors
                                    + " \n "
                                    + " - Kindly provide value for Attribute '"
                                    + each_attr_line.attribute_id.name
                                    + "' for '"
                                    + value.get("Product")
                                    + "'"
                                )
                else:
                    if each_attr_line.attribute_id.id == attribute_yarn_mto:
                        color_loop += 1
                        if color_loop == 1:
                            if product_attribute_yarn1 not in each_attr_line.value_ids:
                                errors = (
                                    errors
                                    + " \n "
                                    + " - Yarn 1 '"
                                    + value.get("YarnMTO1")
                                    + "' not found in '"
                                    + value.get("Product")
                                    + "'"
                                )
                        elif color_loop == 2:
                            if product_attribute_yarn2 not in each_attr_line.value_ids:
                                errors = (
                                    errors
                                    + " \n "
                                    + " - Yarn 2 '"
                                    + value.get("YarnMTO2")
                                    + "' not found in '"
                                    + value.get("Product")
                                    + "'"
                                )
                        elif color_loop == 3:
                            if product_attribute_yarn3 not in each_attr_line.value_ids:
                                errors = (
                                    errors
                                    + " \n "
                                    + " - Yarn 3 '"
                                    + value.get("YarnMTO3")
                                    + "' not found in '"
                                    + value.get("Product")
                                    + "'"
                                )

                if each_attr_line.attribute_id.id == attribute_personalize:
                    check_personalize_allowed = True
                    for each_val in each_attr_line.value_ids:
                        if each_val.name == "1 Line":
                            check_line1_allowed = True
                        if each_val.name == "2 Lines":
                            check_line2_allowed = True
                        if each_val.name == "3 Lines":
                            check_line3_allowed = True
                        if each_val.name == "Stock":
                            check_stock_allowed = True

            if self.partner_id.custom_mass_imp_val != "design":
                if len(attribute_value_ids) == len(attribute_id_ids):
                    product_template_variant_value_ids = self.env[
                        "product.template.attribute.value"
                    ].search(
                        [
                            ("product_tmpl_id", "=", product_template_id.id),
                            ("attribute_id", "in", attribute_id_ids),
                            ("product_attribute_value_id", "in", attribute_value_ids),
                        ]
                    )
                    if product_template_variant_value_ids:
                        if len(attribute_id_ids) == 1:
                            product_variant_rec = self.env["product.product"].search(
                                [
                                    ("name", "=ilike", value.get("Product")),
                                    (
                                        "product_template_variant_value_ids",
                                        "in",
                                        product_template_variant_value_ids.ids,
                                    ),
                                ],
                                limit=1,
                            )
                        elif len(attribute_id_ids) == 2:
                            product_variant_rec = self.env["product.product"].search(
                                [
                                    ("name", "=ilike", value.get("Product")),
                                    (
                                        "product_template_variant_value_ids",
                                        "in",
                                        product_template_variant_value_ids.ids[1],
                                    ),
                                    (
                                        "product_template_variant_value_ids",
                                        "in",
                                        product_template_variant_value_ids.ids[0],
                                    ),
                                ],
                                limit=1,
                            )
                        else:
                            product_variant_rec = self.env["product.product"].search(
                                [
                                    ("name", "=ilike", value.get("Product")),
                                    (
                                        "product_template_variant_value_ids",
                                        "in",
                                        product_template_variant_value_ids.ids[1],
                                    ),
                                    (
                                        "product_template_variant_value_ids",
                                        "in",
                                        product_template_variant_value_ids.ids[2],
                                    ),
                                    (
                                        "product_template_variant_value_ids",
                                        "in",
                                        product_template_variant_value_ids.ids[0],
                                    ),
                                ],
                                limit=1,
                            )

            personalize_line1_excel = value.get("PersonalizeLine1") or ""
            personalize_line2_excel = value.get("PersonalizeLine2") or ""
            personalize_line3_excel = value.get("PersonalizeLine3") or ""
            if check_personalize_allowed:
                if (
                    personalize_line1_excel
                    or personalize_line2_excel
                    or personalize_line3_excel
                ):
                    if self.partner_id.custom_mass_imp_val != "design":
                        if not product_variant_rec and not (
                            value.get("Colorway") or value.get("Alphabets")
                        ):
                            product_variant_rec = self.env["product.product"].search(
                                [("name", "=ilike", value.get("Product"))], limit=1
                            )
                    for each_attr_line in product_template_id.attribute_line_ids:
                        if each_attr_line.attribute_id.name == "Personalize":
                            for each_val in each_attr_line.value_ids:
                                if each_val.name == "1 Line":
                                    if not personalize_line1_excel:
                                        errors = (
                                            errors
                                            + " \n "
                                            + " - Line 1 not found for '"
                                            + value.get("Product")
                                            + "'"
                                        )
                                if each_val.name == "2 Lines":
                                    if (
                                        personalize_line1_excel
                                        or personalize_line2_excel
                                    ):
                                        if not personalize_line1_excel:
                                            errors = (
                                                errors
                                                + " \n "
                                                + " - Line 1 not found for '"
                                                + value.get("Product")
                                                + "'"
                                            )
                                        if (
                                            not personalize_line2_excel
                                            and not check_line1_allowed
                                        ):
                                            errors = (
                                                errors
                                                + " \n "
                                                + " - Line 2 not found for '"
                                                + value.get("Product")
                                                + "'"
                                            )
                                if each_val.name == "3 Lines":
                                    if (
                                        personalize_line2_excel
                                        or personalize_line3_excel
                                    ):
                                        if not personalize_line1_excel:
                                            errors = (
                                                errors
                                                + " \n "
                                                + " - Line 1 not found for '"
                                                + value.get("Product")
                                                + "'"
                                            )
                                        if not personalize_line2_excel:
                                            errors = (
                                                errors
                                                + " \n "
                                                + " - Line 2 not found for '"
                                                + value.get("Product")
                                                + "'"
                                            )
                                        if not personalize_line3_excel:
                                            errors = (
                                                errors
                                                + " \n "
                                                + " - Line 3 not found for '"
                                                + value.get("Product")
                                                + "'"
                                            )
                    if (
                        check_line1_allowed
                        and (not check_line2_allowed)
                        and (not check_line3_allowed)
                    ):
                        if personalize_line2_excel:
                            errors = (
                                errors
                                + " \n "
                                + " - Line 2 not found for '"
                                + value.get("Product")
                                + "'"
                            )
                        if personalize_line3_excel:
                            errors = (
                                errors
                                + " \n "
                                + " - Line 3 not found for '"
                                + value.get("Product")
                                + "'"
                            )
                else:
                    if not check_stock_allowed:
                        errors = (
                            errors
                            + " \n "
                            + " - Kindly maintain 'Personalization' for '"
                            + value.get("Product")
                            + "'"
                        )
            else:
                if (
                    personalize_line1_excel
                    or personalize_line2_excel
                    or personalize_line3_excel
                ):
                    errors = (
                        errors
                        + " \n "
                        + " - Personalization not found in '"
                        + value.get("Product")
                        + "'"
                    )

            if self.partner_id.custom_mass_imp_val != "design":
                if product_variant_rec:
                    custom_allowed_customer_ids = (
                        self.partner_id.custom_allowed_customer_ids.ids
                    )
                    custom_allowed_customer_ids.append(self.partner_id.id)
                    custom_allowed_customer_ids.append(False)
                    if not (
                        product_variant_rec.product_tmpl_id.custom_link_customer.id
                        in custom_allowed_customer_ids
                    ):
                        errors = (
                            errors
                            + "\n- Customer Mapping Not Found for product "
                            + product_variant_rec.name
                        )
                    elif product_variant_rec.active == False:
                        errors = (
                            errors + "\n- Product Inactive " + product_variant_rec.name
                        )
            else:
                if product_template_id:
                    custom_allowed_customer_ids = (
                        self.partner_id.custom_allowed_customer_ids.ids
                    )
                    custom_allowed_customer_ids.append(self.partner_id.id)
                    custom_allowed_customer_ids.append(False)
                    if not (
                        product_template_id.custom_link_customer.id
                        in custom_allowed_customer_ids
                    ):
                        errors = (
                            errors
                            + "\n- Customer Mapping Not Found for product "
                            + product_template_id.name
                        )

                    product_variant_rec = self.env["product.product"].search(
                        [("product_tmpl_id", "=", product_template_id.id)], limit=1
                    )

        return (
            errors,
            product_template_id,
            product_variant_rec,
            product_attribute_yarn1_component,
            product_attribute_yarn2_component,
            product_attribute_yarn3_component,
            product_attribute_design,
        )


class CustomOrderLine(models.Model):
    _name = "custom.order.line.import"
    _description = "Order Line"

    order_id = fields.Many2one("custom.order.processing.import", string="Order")

    import_order_id = fields.Char(string="Order ID")
    ship_to = fields.Char(string="Ship To")
    company_atten = fields.Char(string="Purchaser")
    address = fields.Char(string="Address")
    address_2 = fields.Char(string="Address 2")
    city = fields.Char(string="City")
    state = fields.Char(string="State")
    country = fields.Char(string="Country")
    zip = fields.Char(string="Zip")
    customer_ref = fields.Char(string="Customer Ref")
    product = fields.Char(string="Product")
    colorway = fields.Char(string="Colorway")
    alphabets = fields.Char(string="Alphabets")
    size = fields.Char(string="Size")
    font_case = fields.Char(string="Font Case")
    font = fields.Char(string="Font")
    open_text = fields.Char(string="Open Text")
    etail_ticket_no = fields.Char(string="Etail Ticket No")

    personalize_line_1 = fields.Char(string="Line 1")
    personalize_line_2 = fields.Char(string="Line 2")
    personalize_line_3 = fields.Char(string="Line 3")

    quantity = fields.Integer(string="Quantity")
    error_status = fields.Boolean("Error Status")
    error_message = fields.Text("Error Message")
    order_date = fields.Date(string="Order Date")

    custom_design = fields.Char(string="Design")
    custom_color_3 = fields.Char(string="Color 3")
    custom_color_6 = fields.Char(string="Color 6")
    custom_color_7 = fields.Char(string="Color 7")

    custom_gift_mess = fields.Html("Gift Message")

    def action_show_error(self):
        for record in self:
            if record.error_message:
                raise ValidationError(f"Error Message: {record.error_message}")
            else:
                raise ValidationError("No error message available.")

    def action_show_gift_message(self):
        for record in self:
            if record.custom_gift_mess:
                message_id = self.env["custom.message.wizard"].create(
                    {"message": record.custom_gift_mess}
                )
                return {
                    "name": _("Gift Message"),
                    "type": "ir.actions.act_window",
                    "view_mode": "form",
                    "res_model": "custom.message.wizard",
                    # pass the id
                    "res_id": message_id.id,
                    "target": "new",
                }
