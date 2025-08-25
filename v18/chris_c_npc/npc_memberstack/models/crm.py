from odoo import models, fields, api


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    memberstack_id = fields.Char("Memberstack ID", tracking=True)
    email_verified = fields.Boolean("Email Verified", tracking=True)
    board_certs = fields.Char("Board Certification", tracking=True)
    medical_degree = fields.Char("Medical Degree", tracking=True)
    active_license_state_ids = fields.Many2many(
        'res.country.state', string="Active License States", tracking=True)
