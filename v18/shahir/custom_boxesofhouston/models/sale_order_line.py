from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    custom_margin_percentage = fields.Float(
        string="Margin Percentage",
        compute="_compute_margin_percentage",
        inverse="_inverse_margin_percentage",
        store=True,
    ) 

    @api.depends('price_subtotal', 'product_uom_qty', 'purchase_price', 'price_unit')
    def _compute_margin_percentage(self):
        for line in self:
            # Find alternative calculation when line is added to order from delivery
            if line.qty_delivered and not line.product_uom_qty:
                calculated_subtotal = line.price_unit * line.qty_delivered
                line.custom_margin_percentage = calculated_subtotal and line.margin / calculated_subtotal
            else:
                line.custom_margin_percentage = line.price_subtotal and line.margin / line.price_subtotal

    @api.onchange('purchase_price', 'custom_margin_percentage')
    def _inverse_margin_percentage(self):
        for line in self:
            if line.purchase_price:
                try:
                    line.price_unit = line.purchase_price / (1 - line.custom_margin_percentage)
                except ZeroDivisionError:
                    line.price_unit = 0.0

    def create(self,vals):
        lines = super().create(vals)
        for line in lines: 
            if line.order_id.stock_route_id:
               line.route_id = line.order_id.stock_route_id.id
        return lines