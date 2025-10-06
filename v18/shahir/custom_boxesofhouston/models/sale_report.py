from odoo import models, fields

class SaleReport(models.Model):
    _inherit = 'sale.report'

    margin_percent = fields.Float('Margin Percent',aggregator="avg")
    distinct_customer = fields.Integer(string="Distinct Customers", readonly=True)
    
    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        # include margin_percent in select:
        res['margin_percent'] = "s.margin_percent * 100"
        res['distinct_customer'] = "COUNT(DISTINCT s.partner_id)"
        return res