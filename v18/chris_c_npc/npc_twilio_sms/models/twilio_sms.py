from odoo import fields, models, api, SUPERUSER_ID


class TwilioIncomingSMS(models.Model):
    _inherit = 'twilio.incoming.sms'
    _order = 'received_date desc'

    partner_id = fields.Many2one('res.partner', string="Contact")

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)

        res.sms_message_post()

        return res

    def sms_message_post(self):
        partner_model = self.env['res.partner'].with_user(SUPERUSER_ID).sudo()

        for sms in self:
            sms_number = sms.phone

            if sms_number and sms_number.startswith('+1'):
                sms_number = sms_number.replace('+1', '')

            partner_id = partner_model.search(
                [('phone_mobile_search', 'ilike', sms_number)], limit=1)
            if partner_id and sms.id not in partner_id.sms_ids.ids:
                partner_id.message_post(
                    body=f"SMS received from {sms.phone}:\n\n{sms.body}",
                    message_type='sms',
                    subtype_xmlid='mail.mt_note')
                partner_id.sms_ids += sms
