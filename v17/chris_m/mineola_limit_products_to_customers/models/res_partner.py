from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    custom_prod_list_id = fields.Many2one(string='Custom Product List', comodel_name='custom.prod.list')
    