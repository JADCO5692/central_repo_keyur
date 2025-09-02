from odoo import models, fields, api, _


class ShopifyInstanceEpt(models.Model):
    _inherit = "shopify.instance.ept"

    custom_label_template_id = fields.Many2one(
        comodel_name="custom.label.template", string="Label Template"
    )
    custom_policy = fields.Selection(
        [
            ("products", "Based on Products"),
            ("order", "Based on Order Quantity"),
            ("delivery", "Based on Delivered Quantity"),
            ("intent", "Based on Intent"),
        ],
        default="products",
        string="Invoicing Policy",
    )
    custom_from_address_id = fields.Many2one(
        comodel_name="res.partner",
        string="Custom From Address",
        help="This address will be used as the From Address in the Shopify orders.")
    custom_tag_invoice_ids = fields.One2many('custom.shopify.instance.ept.tags', 'custom_shopify_instance_ept_id', string='Tag Invoice Ids')
    custom_sale_payment_term_id = fields.Many2one(
        comodel_name="account.payment.term",
        string="Payment Terms",
        tracking=True,
    )

class ShopifyInstanceEptTags(models.Model):
    _name = "custom.shopify.instance.ept.tags"
    _description = 'Map tags to customer for Invoice address'
    
    custom_shopify_instance_ept_id = fields.Many2one(
        comodel_name="shopify.instance.ept", string="Shopify Instance Ept ID"
    )
    custom_tags = fields.Many2one(
        comodel_name="res.partner.category", string="Tags"
    )
    custom_invoice_partner = fields.Many2one(
        comodel_name="res.partner", string="Invoice Partner"
    )