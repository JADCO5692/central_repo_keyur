from odoo import models, fields,api


class Message(models.Model):
    _inherit = 'mail.message'
    
    npc_disable_access_btn = fields.Boolean(compute="compute_display_access_btn")

    def compute_display_access_btn(self):
        for message in self:
            model = message.model
            record_id = self.env[model].browse(message.res_id)
            is_invoice = bool(model == 'account.move' and record_id.move_type in ['out_invoice', 'out_refund'])
            is_subscription = bool(model == 'sale.order' and record_id.is_subscription)
            is_user_email = bool(model == 'res.users' or message.subject and 'Security Update' in message.subject)
            is_invitation = bool(message.email_layout_xmlid == 'mail.mail_notification_invite')
            if is_invoice or is_subscription or is_user_email or is_invitation:
                message.npc_disable_access_btn = False
            else:
                message.npc_disable_access_btn = True


