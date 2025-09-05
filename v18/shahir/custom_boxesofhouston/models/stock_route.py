from odoo import models, fields

class StockRoute(models.Model):
    _inherit = 'stock.route'

    sale_order_line_selectable = fields.Boolean('Sale Order')
    available_for_pos_order = fields.Boolean('POS Order')
    is_address_mandatory = fields.Boolean('Is Address Mandatory')
    is_auto_complete = fields.Boolean('Is Auto Complete')