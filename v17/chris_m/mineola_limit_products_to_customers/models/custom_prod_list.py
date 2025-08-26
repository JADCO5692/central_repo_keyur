from odoo import api, fields, models


class CustomProdList(models.Model):
    _name = 'custom.prod.list'
    _description = 'Custom Product List'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Description', required=True)
    partner_ids = fields.One2many(string='Customers', comodel_name='res.partner', inverse_name='custom_prod_list_id')
    product_tmpl_ids = fields.Many2many(string='Products', comodel_name='product.template')
    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(string='Sequence', default=10)
