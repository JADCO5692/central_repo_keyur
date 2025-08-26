# -*- coding: utf-8 -*-
from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    prevent_intrimed_entries = fields.Boolean(
        string="Prevent Intrimed Entries",
        help="If checked, Accounting entries for the stock output account and expense will not be generated for such moves",
        default=False,
    )
