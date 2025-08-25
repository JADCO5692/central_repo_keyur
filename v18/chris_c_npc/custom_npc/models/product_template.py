from odoo import fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_np_fees_product = fields.Boolean('NPC fees')
    is_np_main_fees_product = fields.Boolean('NPC Primary fees')
    is_physician_fees_product = fields.Boolean('Physician fees')
    is_physician_main_fees_product = fields.Boolean('Physician Primary fees')
