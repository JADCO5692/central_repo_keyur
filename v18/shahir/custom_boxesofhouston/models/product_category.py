from odoo import fields, models

class ProductCategory(models.Model):
    _inherit = 'product.category'

    ecommerce_category_id = fields.Many2one('product.public.category','Ecommerce Category')
    pos_category_id = fields.Many2one('pos.category','Pos Category')

    