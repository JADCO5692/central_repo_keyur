#-- coding: utf-8 --
from odoo import models, fields, api

class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    base = fields.Selection(
        selection_add=[("cost_margin", "Cost Margin")],
        ondelete={"cost_margin": "set default"},
    )
    price_margin = fields.Float(
        string="Price Margin",
        digits="Product Price",
        help="The margin to apply to the cost price, expressed as a percentage.",
    )

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