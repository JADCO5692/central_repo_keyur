#-- coding: utf-8 --
from odoo import models, fields, api

class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"
    _order = "product_tmpl_id, min_quantity"

    base = fields.Selection(
        selection_add=[("cost_margin", "Cost Margin")],
        ondelete={"cost_margin": "set default"},
    )
    price_margin = fields.Float(
        string="Price Margin",
        digits="Product Price",
        compute="compute_price_margin",
        help="The margin to apply to the cost price, expressed as a percentage.",
    )
    product_cost = fields.Float(
        string="Cost Price",
        related="product_tmpl_id.standard_price",
        digits="Product Price",
        store=True,
        readonly=True,
    )
    margin_percent = fields.Float(
        string="Margin Percent",
        digits="Product Price",
        compute="compute_price_margin")

    @api.depends('product_tmpl_id', 'compute_price','fixed_price')
    def compute_price_margin(self):
        for item in self:
            item.price_margin = 0.0
            item.margin_percent = 0.0
            if item.display_applied_on == "1_product" and item.product_tmpl_id and item.compute_price == 'fixed':
                item.price_margin = item.fixed_price - (item.product_tmpl_id.standard_price * 1)
                if item.price_margin:
                    item.margin_percent = item.fixed_price and (item.price_margin/item.fixed_price) or 0.0

    def _compute_price(self, product, quantity, uom, date, currency=None):
        if self.base == "cost_margin":
            price = product.standard_price  / (1 - self.price_margin / 100.0)
        else:
            price = super()._compute_price(product, quantity, uom, date, currency)
        return price
    
    def _compute_price_label(self):
        for item in self:
            if item.base == "cost_margin":
                item.price = f"{item.price_margin}% Margin on Cost Price"
            else:
                return super()._compute_price_label()