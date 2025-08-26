from odoo import models, fields, _

class PmallProductMapping(models.Model):
    _name = 'pmall.product.mapping'
    _description = 'Contains the mapping of products created throught the pmall orders log'

    name = fields.Char('Produt Name')
    partner_sku = fields.Char('Partner SkU')
    odoo_product_id = fields.Many2one('product.product','Odoo Product')
    odoo_product_partner_sku = fields.Char('Odoo Product Partner SKU',related="odoo_product_id.default_code")