from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    mail_template_id = fields.Many2one('mail.template', string="Dropship email template",
                                       help="Select email template for quotation email.")