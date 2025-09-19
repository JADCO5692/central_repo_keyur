from odoo import models, fields, api, _
from odoo.tools.misc import get_lang
from odoo.exceptions import ValidationError

from werkzeug.urls import url_join, url_quote
from odoo.tools import config, email_normalize, get_lang, is_html_empty, format_date, formataddr, groupby
from odoo.exceptions import UserError

class SignRequest(models.Model):
    _inherit = "sign.request"

    def _send_completed_document_mail(self, signers, request_edited, partner, access_token=None, with_message_cc=True, force_send=False):
        # Replaced base method 
        # To restrict sending attechment after sign document
        self.ensure_one()
        if access_token is None:
            access_token = self.access_token
        partner_lang = get_lang(self.env, lang_code=partner.lang).code
        base_url = self.get_base_url()
        body = self.env['ir.qweb']._render('custom_sign_changes.sign_template_mail_completed_custom', {
            'record': self,
            'link': url_join(base_url, '/my/payment_method'),
            'subject': '%s signed' % self.reference,
            'body': self.message_cc if with_message_cc and not is_html_empty(self.message_cc) else False,
            'recipient_name': partner.name,
            'recipient_id': partner.id,
            'signers': signers,
            'request_edited': request_edited,
            }, lang=partner_lang, minimal_qcontext=True)
        notification_template = 'mail.mail_notification_light'
        if self.env.ref('sign.sign_mail_notification_light', raise_if_not_found=False):
            notification_template = 'sign.sign_mail_notification_light'
        self.env['sign.request']._message_send_mail(
            body, notification_template,
            {'record_name': self.reference},
            {
                'model_description': _('Signature'),
                'company': self.communication_company_id or self.create_uid.company_id
            },
            {'email_from': self.create_uid.email_formatted,
             'author_id': self.create_uid.partner_id.id,
             'email_to': partner.email_formatted,
             'subject': _('%s has been edited and signed', self.reference) if request_edited else _('%s has been signed', self.reference),
             'attachment_ids': []},
            force_send=force_send,
            lang=partner_lang,
        )

    def get_sign_attechment_ids(self):
        user = self.env.user
        sign_requests = self.search([('request_item_ids.partner_id','in',user.partner_id.ids)])
        doc_ids = []
        for sr in sign_requests:
            if sr.attachment_ids:
                doc_ids += sr.attachment_ids.ids
            if sr.completed_document_attachment_ids:
                doc_ids += sr.completed_document_attachment_ids.ids
        return doc_ids
            
