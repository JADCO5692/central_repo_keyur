from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

import logging

_logger = logging.getLogger(__name__)

sel_custom_color_count = [
    ("0", "0"),
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
    ("5", "5"),
    ("6", "6"),
]

sel_custom_mrp_confirm = [("no", "No"), ("yes", "Yes")]

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

sel_custom_fiber = [
    ("na", "N/A"),
    ("mw", "MW - Merino Wool"),
    ("oc", "OC - Organic Cotton"),
    ("ac", "AC - Acrylic"),
    ("ec", "EC - Egyption Cotton"),
    ("rc", "RC - Recycle Cotton"),
    ("cc", "CC - Combed Cotton"),
    ("ac_m", "AC/M - Acrylic with Metallic"),
    ("mw_m", "MW/M - Merino Wool with Metallic"),
    ("mix", "Mix"),
    ("gr", "GR - Sunbrella"),
]

sel_custom_prod_type = [
    ("na", "N/A"),
    ("pre_set", "Pre-Set"),
    ("mtp", "MTO"),
    ("special_mtp_var", "Special MTO(Attribute)"),
    ("special_mtp_prod", "Special MTO(Product)"),
]

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


class ProductTemplate(models.Model):
    _inherit = "product.template"

    custom_is_binding = fields.Boolean(string="Binding Yarn", tracking=True, copy=True)
    custom_is_wash = fields.Boolean(
        string="Wash & Dry", default=True, tracking=True, copy=True
    )
    custom_is_dry = fields.Boolean(string="Dry only", tracking=True, copy=True)
    custom_is_press = fields.Boolean(
        string="Press", default=True, tracking=True, copy=True
    )

    custom_prod_type = fields.Selection(
        sel_custom_prod_type, string="Inventory Type", tracking=True, copy=True
    )

    custom_color_2 = fields.Float("Color 2", tracking=True, copy=True)
    custom_color_3 = fields.Float("Color 3", tracking=True, copy=True)
    custom_color_4 = fields.Float("Color 4", tracking=True, copy=True)
    custom_color_5 = fields.Float("Color 5", tracking=True, copy=True)
    custom_color_6 = fields.Float("Color 6", tracking=True, copy=True)
    custom_color_7 = fields.Float("Color 7", tracking=True, copy=True)

    custom_link_customer = fields.Many2one(
        comodel_name="res.partner",
        string="Customer",
        domain=[("customer_rank", ">", 0)],
        tracking=True,
        copy=True,
    )
    custom_allowed_customer_ids = fields.Many2many(
        "res.partner",
        "res_partner_additional_customer_rel",
        "partner_id",
        "additional_customer_id",
        string="Additional Customers",
        domain=[("customer_rank", ">", 0)],
    )

    custom_machine_no = fields.Selection(
        sel_custom_machine_no,
        string="Machine No",
        compute="_compute_custom_machine_no",
        inverse="_set_custom_machine_no",
        search="_search_custom_machine_no",
        tracking=True,
        store=True,
        copy=True,
    )
    custom_prod_time = fields.Float(
        string="Production Time",
        compute="_compute_custom_prod_time",
        inverse="_set_custom_prod_time",
        search="_search_custom_prod_time",
        tracking=True,
        store=True,
        copy=True,
    )
    custom_customer_sku = fields.Char(
        "Customer SKU",
        compute="_compute_custom_customer_sku",
        inverse="_set_custom_customer_sku",
        search="_search_custom_customer_sku",
        size=80,
        tracking=True,
        store=True,
        copy=True,
    )
    custom_color_count = fields.Selection(
        sel_custom_color_count,
        string="Color Count",
        compute="_compute_custom_color_count",
        inverse="_set_custom_color_count",
        search="_search_custom_color_count",
        tracking=True,
        store=True,
        copy=True,
    )
    custom_prod_size = fields.Selection(
        sel_custom_prod_size,
        string="Size",
        compute="_compute_custom_prod_size",
        inverse="_set_custom_prod_size",
        search="_search_custom_prod_size",
        tracking=True,
        store=True,
        copy=True,
    )
    custom_tiff_file_url = fields.Char(
        "TIF File URL",
        compute="_compute_custom_tiff_file_url",
        inverse="_set_custom_tiff_file_url",
        search="_search_custom_tiff_file_url",
        size=150,
        tracking=True,
        store=True,
        copy=True,
    )
    custom_fiber = fields.Selection(
        sel_custom_fiber,
        string="Fiber",
        compute="_compute_custom_fiber",
        inverse="_set_custom_fiber",
        search="_search_custom_fiber",
        tracking=True,
        store=True,
        copy=True,
    )
    custom_mrp_confirm = fields.Selection(
        sel_custom_mrp_confirm,
        string="Auto MO confirm",
        compute="_compute_custom_mrp_confirm",
        inverse="_set_custom_mrp_confirm",
        search="_search_custom_mrp_confirm",
        tracking=True,
        store=True,
        copy=True,
    )
    custom_needle = fields.Integer(
        string="Needle",
        compute="_compute_custom_needle",
        inverse="_set_custom_needle",
        search="_search_custom_needle",
        tracking=True,
        store=True,
        copy=True,
    )

    @api.depends("product_variant_ids.custom_mrp_confirm")
    def _compute_custom_mrp_confirm(self):
        self._compute_template_field_from_variant_field("custom_mrp_confirm")

    def _set_custom_mrp_confirm(self):
        self._set_product_variant_field("custom_mrp_confirm")

    def _search_custom_mrp_confirm(self, operator, value):
        products = self.env["product.product"].search(
            [("custom_mrp_confirm", operator, value)], limit=None
        )
        return [("id", "in", products.mapped("product_tmpl_id").ids)]

    @api.depends("product_variant_ids.custom_customer_sku")
    def _compute_custom_customer_sku(self):
        self._compute_template_field_from_variant_field("custom_customer_sku")

    def _set_custom_customer_sku(self):
        self._set_product_variant_field("custom_customer_sku")

    def _search_custom_customer_sku(self, operator, value):
        products = self.env["product.product"].search(
            [("custom_customer_sku", operator, value)], limit=None
        )
        return [("id", "in", products.mapped("product_tmpl_id").ids)]

    @api.depends("product_variant_ids.custom_tiff_file_url")
    def _compute_custom_tiff_file_url(self):
        self._compute_template_field_from_variant_field("custom_tiff_file_url")

    def _set_custom_tiff_file_url(self):
        self._set_product_variant_field("custom_tiff_file_url")

    def _search_custom_tiff_file_url(self, operator, value):
        products = self.env["product.product"].search(
            [("custom_tiff_file_url", operator, value)], limit=None
        )
        return [("id", "in", products.mapped("product_tmpl_id").ids)]

    @api.depends("product_variant_ids.custom_color_count")
    def _compute_custom_color_count(self):
        self._compute_template_field_from_variant_field("custom_color_count")

    def _set_custom_color_count(self):
        self._set_product_variant_field("custom_color_count")

    def _search_custom_color_count(self, operator, value):
        products = self.env["product.product"].search(
            [("custom_color_count", operator, value)], limit=None
        )
        return [("id", "in", products.mapped("product_tmpl_id").ids)]

    @api.depends("product_variant_ids.custom_prod_time")
    def _compute_custom_prod_time(self):
        self._compute_template_field_from_variant_field("custom_prod_time")

    def _set_custom_prod_time(self):
        self._set_product_variant_field("custom_prod_time")

    def _search_custom_prod_time(self, operator, value):
        products = self.env["product.product"].search(
            [("custom_prod_time", operator, value)], limit=None
        )
        return [("id", "in", products.mapped("product_tmpl_id").ids)]

    @api.depends("product_variant_ids.custom_prod_size")
    def _compute_custom_prod_size(self):
        self._compute_template_field_from_variant_field("custom_prod_size")

    def _set_custom_prod_size(self):
        self._set_product_variant_field("custom_prod_size")

    def _search_custom_prod_size(self, operator, value):
        products = self.env["product.product"].search(
            [("custom_prod_size", operator, value)], limit=None
        )
        return [("id", "in", products.mapped("product_tmpl_id").ids)]

    @api.depends("product_variant_ids.custom_fiber")
    def _compute_custom_fiber(self):
        self._compute_template_field_from_variant_field("custom_fiber")

    def _set_custom_fiber(self):
        self._set_product_variant_field("custom_fiber")

    def _search_custom_fiber(self, operator, value):
        products = self.env["product.product"].search(
            [("custom_fiber", operator, value)], limit=None
        )
        return [("id", "in", products.mapped("product_tmpl_id").ids)]

    @api.depends("product_variant_ids.custom_machine_no")
    def _compute_custom_machine_no(self):
        self._compute_template_field_from_variant_field("custom_machine_no")

    def _set_custom_machine_no(self):
        self._set_product_variant_field("custom_machine_no")

    def _search_custom_machine_no(self, operator, value):
        products = self.env["product.product"].search(
            [("custom_machine_no", operator, value)], limit=None
        )
        return [("id", "in", products.mapped("product_tmpl_id").ids)]

    @api.depends("product_variant_ids.custom_needle")
    def _compute_custom_needle(self):
        self._compute_template_field_from_variant_field("custom_needle")

    def _set_custom_needle(self):
        self._set_product_variant_field("custom_needle")

    def _search_custom_needle(self, operator, value):
        products = self.env["product.product"].search(
            [("custom_needle", operator, value)], limit=None
        )
        return [("id", "in", products.mapped("product_tmpl_id").ids)]

    def _get_combination_info(
        self,
        combination=False,
        product_id=False,
        add_qty=1.0,
        parent_combination=False,
        only_template=False,
    ):
        res = super()._get_combination_info(
            combination, product_id, add_qty, parent_combination, only_template
        )
        if res.get("product_id"):
            product_obj = (
                self.env["product.product"].sudo().browse(res.get("product_id"))
            )
            res.update({
                "custom_customer_sku": product_obj.custom_customer_sku,
                "custom_prod_size": self.get_custom_size(product_obj.custom_prod_size),
                "custom_fiber": self.get_custom_fiber(product_obj.custom_fiber),
                "weight": product_obj.weight or 0,
            })
        return res
    
    def get_custom_size(self,size):
        if not size:
            return False
        return [item for item in sel_custom_prod_size if item[0] == size][0][1]

    def get_custom_fiber(self,fiber):
        if not fiber:
            return False
        return [item for item in sel_custom_fiber if item[0] == fiber][0][1]
    
    def _get_related_fields_variant_template(self):
        res = super()._get_related_fields_variant_template()
        res.append("custom_machine_no")
        res.append("custom_machine_no")
        res.append("custom_prod_time")
        res.append("custom_customer_sku")
        res.append("custom_color_count")
        res.append("custom_prod_size")
        res.append("custom_tiff_file_url")
        res.append("custom_fiber")
        res.append("custom_mrp_confirm")
        res.append("custom_needle")
        return res
    

    def get_product_accounts(self, fiscal_pos=None):
        accounts = super().get_product_accounts(fiscal_pos)
        if order:= self._context.get("order", False):
            component_location = order.location_src_id
            if component_location.prevent_intrimed_entries:
                accounts['stock_output'] = False
        return accounts


class ProductProduct(models.Model):
    _inherit = "product.product"

    custom_tiff_file_url = fields.Char(string="TIF File URL", size=150, copy=True)
    custom_prod_size = fields.Selection(sel_custom_prod_size, string="Size", copy=True)
    custom_fiber = fields.Selection(sel_custom_fiber, string="Fiber", copy=True)
    custom_color_count = fields.Selection(
        sel_custom_color_count, string="Color Count", copy=True
    )
    custom_prod_time = fields.Float(string="Production Time", copy=True)
    custom_needle = fields.Integer(string="Needle", copy=True)
    custom_customer_sku = fields.Char("Customer SKU", size=80, copy=True)
    custom_machine_no = fields.Selection(
        sel_custom_machine_no, string="Machine No", copy=True
    )
    custom_mrp_confirm = fields.Selection(
        sel_custom_mrp_confirm, string="Auto MO confirm", copy=True
    )
    custom_special_notation_tag_ids = fields.Many2many(
        string="Special Notation",
        comodel_name="product.tag",
        relation="product_tag_product_special_rel",
        tracking=True,
        copy=True,
    )
