from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    custom_physician_product = fields.Many2one('product.template', string="Physician Product")