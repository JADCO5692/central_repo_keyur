from odoo import api, fields, models
from odoo.exceptions import ValidationError

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

class CustomDesignTif(models.Model):
    _name = "custom.design.tif"
    _order = "custom_design_id asc"
    _description = "Maintain TIF file URL per design and size"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
    ]

    custom_attribute_id = fields.Many2one(
        comodel_name="product.attribute", string="Attribute"
    )
    custom_design_id = fields.Many2one(
        comodel_name="product.attribute.value", string="Design"
    )
    custom_prod_size = fields.Selection(
        sel_custom_prod_size, string="Size", tracking=True
    )
    custom_tiff_file_url = fields.Char(string="TIF File URL", size=150, tracking=True)

    _sql_constraints = [
        (
            "unique_design_size",
            "unique(custom_design_id, custom_prod_size)",
            "Design Entry for this Size already exists",
        )
    ]

    @api.constrains("custom_design_id", "custom_prod_size")
    def _check_duplicate_entry(self):
        for record in self:
            if self.search(
                [
                    ("custom_design_id", "=", record.custom_design_id.id),
                    ("custom_prod_size", "=", record.custom_prod_size),
                    ("id", "!=", record.id),
                ]
            ):
                raise ValidationError("Design Entry for this Size already exists")
