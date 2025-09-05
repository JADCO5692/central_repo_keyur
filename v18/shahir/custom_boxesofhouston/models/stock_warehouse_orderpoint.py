from odoo import models, fields

class StockWarehouseOrderpoint(models.Model):
    _inherit='stock.warehouse.orderpoint'

    product_tag_ids = fields.Many2many(string="Tags", comodel_name='product.tag', 
                                       relation='product_tag_stock_warehouse_orderpoint__rel',
                                       related='product_tmpl_id.product_tag_ids')