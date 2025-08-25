from odoo import models, fields, api


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    res_model = fields.Char("Related Document Model")
    res_id = fields.Many2oneReference("Related Document ID", model_field='res_model')

    def action_open_related_record(self):
        print(self.res_model)
        return {
            'name': self.name,
            'view_mode': 'form',
            'res_id': self.res_id,
            'res_model': self.res_model,
            'views': [(False, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
