from odoo import fields, models


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    is_special_mto_attr = fields.Boolean("Special MTO attribute")
    show_yarn_component_image = fields.Boolean("Show Yarn Component Image")
    custom_show_image = fields.Boolean("Show Design in Tree")
    is_personalize = fields.Boolean("Is Personalize")


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    custom_product_component = fields.Many2one(
        comodel_name="product.product", string="Component"
    )
    line_number = fields.Integer("No. of lines", default=1)
    custom_color_2 = fields.Float("Color 2 % ")
    custom_color_3 = fields.Float("Color 3 % ")
    custom_color_4 = fields.Float("Color 4 % ")
    custom_color_5 = fields.Float("Color 5 % ")
    custom_color_6 = fields.Float("Color 6 % ")
    custom_color_7 = fields.Float("Color 7 % ")
    custom_design_image = fields.Binary(string="Design Image")


class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    line_number = fields.Integer(
        "No. of lines", related="product_attribute_value_id.line_number"
    )
