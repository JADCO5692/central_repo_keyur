from odoo import models, fields, api, _


class Partner(models.Model):
    _inherit = 'res.partner'

    npc_user_type = fields.Selection(
        [
            ('APP', "Nurse Practitioner/PA"),
            ('PHYS', "Physician"),
        ],
        "User Type")
    custom_first_name = fields.Char("First Name", tracking=True)
    custom_last_name = fields.Char("Last Name", tracking=True)

    def open_signatures(self):
        self.ensure_one()
        request_ids = self.env['sign.request.item'].search([('partner_id', '=', self.id)]).mapped('sign_request_id')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Signature(s)'),
            'view_mode': 'list,kanban,form',  # default view should be list view
            'res_model': 'sign.request',
            'domain': [('id', 'in', request_ids.ids)],
            'context': {
                'search_default_reference': self.name,
                'search_default_signed': 1,
                'search_default_in_progress': 1,
            },
        }
