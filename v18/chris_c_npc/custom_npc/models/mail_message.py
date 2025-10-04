from odoo import models, fields, api

class MailMessage(models.Model):
    _inherit='mail.message'

    activity_type = fields.Char('Activity Type',compute="_compute_activity_type")

    @api.model
    def _compute_activity_type(self):
        for msg in self:
            if msg.preview:
               msg.activity_type = msg.preview.split("done :", 1)[0].strip() if "done :" in msg.preview else ''
            else:
                msg.activity_type = '' 