from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CustomProductWarehouse(models.Model):
    _name = "custom.product.warehouse"
    _order = "custom_product_id asc"
    _description = "Set different fulfillment Warehouse Product locations"

    custom_customer_id = fields.Many2one(comodel_name="res.partner", string="Customer")
    custom_product_id = fields.Many2one(
        comodel_name="product.product", string="Product"
    )
    custom_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse", string="Warehouse", required=True
    )
    custom_location_id = fields.Many2one(
        comodel_name="stock.location", string="Component Location", required=True
    )

    _sql_constraints = [
        (
            "unique_product_warehouse_location",
            "unique(custom_customer_id, custom_product_id, custom_warehouse_id)",
            "Product Entry for this Warehouse/Customer already exists",
        )
    ]

    @api.constrains("custom_product_id", "custom_warehouse_id", "custom_location_id")
    def _check_duplicate_entry(self):
        for record in self:
            if self.search(
                [
                    ("custom_customer_id", "=", record.custom_customer_id.id),
                    ("custom_product_id", "=", record.custom_product_id.id),
                    ("custom_warehouse_id", "=", record.custom_warehouse_id.id),
                    ("custom_location_id", "=", record.custom_location_id.id),
                    ("id", "!=", record.id),
                ]
            ):
                raise ValidationError("Product Entry for this location already exists")
