from odoo import models, fields

class ShippingStatus(models.Model):
    _name = 'shipping.status'

    name = fields.Char('Shipping Status')
    tech_name = fields.Char('Technical Name')
