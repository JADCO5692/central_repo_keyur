from odoo import models, fields, api, _


class ShopifyInstanceEpt(models.Model):
    _inherit = "shopify.instance.ept"
    _description = "Shopify Instance"

    custom_label_template_id = fields.Many2one(
        comodel_name="custom.label.template", string="Label Template"
    )
    custom_policy = fields.Selection(
        [
            ("products", "Based on Products"),
            ("order", "Based on Order Quantity"),
            ("delivery", "Based on Delivered Quantity"),
        ],
        default="products",
        string="Invoicing Policy",
    )

    custom_from_address_id = fields.Many2one(
        comodel_name="res.partner",
        string="Custom From Address",
        help="This address will be used as the From Address in the Shopify orders.")
