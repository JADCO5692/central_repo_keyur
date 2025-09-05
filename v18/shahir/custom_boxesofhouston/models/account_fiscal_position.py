from odoo import models, fields, api

class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"
    
    custom_tax_exemption = fields.Selection(
        [("exempted", "Tax Exempted"), ("not_exempted", "Not Tax Exempted")],
        string="Tax Exemption Status",
        default="not_exempted",
        help="Select the tax exemption status of the fiscal position."
    )