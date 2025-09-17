from odoo import _, api, fields, models
from odoo.http import request


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_advanced_payment = fields.Boolean('Advanced Payment')
    of_payment_percentage = fields.Float('Of')
    user_pwd = fields.Char('User Pin')
    so_id = fields.Many2one('sale.order')
    order_type = fields.Selection([
        ('bulk', 'Bulk Order'),
        ('dropship', 'Dropship'),
        ], string='Order Type')
    
    def create(self,vals):
        if request:
            if request.session.get('sale_order_id') and request.session.get('dropship'):
                vals.update({
                    'so_id':request.session.get('sale_order_id'),
                    'order_type':'dropship'
                })
        return super(ResPartner,self).create(vals)