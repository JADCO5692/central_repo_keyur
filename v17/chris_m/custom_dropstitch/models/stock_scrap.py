from odoo import _, api, fields, models


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    def do_scrap(self):
        context = dict(self.env.context)
        context.update({"custom_scrap_flag": True})
        super(StockScrap, self.with_context(context)).do_scrap()
        return True
