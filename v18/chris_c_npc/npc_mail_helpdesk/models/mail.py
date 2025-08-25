from odoo import models, fields, api, exceptions, SUPERUSER_ID
from pprint import pprint
import logging

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)

        for msg_id in res:
            author_id = msg_id.author_id
            model = msg_id.model
            res_id = msg_id.res_id
            email_reply = self.env.ref("npc_mail_helpdesk.helpdesk_email", raise_if_not_found=False)
            stage_solved = self.env.ref("helpdesk.stage_solved")
            existing_tickets = self.env['helpdesk.ticket']
            odoobot = self.env.ref("base.partner_root")
            # Prevents error when during upgrade where helpdesk_email team is not yet created.
            if email_reply:
                existing_tickets = self.env['helpdesk.ticket'].sudo().search([('res_model', '=', model),
                                                                              ('res_id', '=', res_id),
                                                                              ('team_id', '=', email_reply.id),
                                                                              ('stage_id', '!=', stage_solved.id)])
            
            if existing_tickets and msg_id.message_type in ('email', 'comment'):
                existing_tickets.write({'stage_id': stage_solved.id})

            elif not author_id or author_id.partner_share and msg_id.message_type in ('email', 'comment') \
                    or author_id.id == odoobot.id and msg_id.message_type == 'sms':

                if model != 'helpdesk.ticket' and res_id:
                    rec_id = self.env[model].sudo().browse(res_id)
                    ticket_vals = {
                        'name': msg_id.subject or msg_id.record_name or rec_id.display_name,
                        'res_id': res_id,
                        'res_model': model,
                        'description': msg_id.body,
                    }

                    # if getattr(rec_id, 'user_id'):
                    #     ticket_vals['user_id'] = rec_id.user_id.id

                    # Teams
                    if author_id.partner_share and msg_id.message_type in ('email', 'comment'):
                        ticket_vals['team_id'] = self.env.ref("npc_mail_helpdesk.helpdesk_email").id
                    if msg_id.message_type == 'sms':
                        ticket_vals['team_id'] = self.env.ref("npc_mail_helpdesk.helpdesk_sms").id

                    # ticket_id = self.env['helpdesk.ticket'].sudo().create([ticket_vals])
                    # ticket_id.with_user(SUPERUSER_ID).message_post(
                    #     body="Click 'Open Related Record' to find the message from the customer and reply from there.",
                    #     subtype_xmlid='mail.mt_note',
                    # ) 
        return res
