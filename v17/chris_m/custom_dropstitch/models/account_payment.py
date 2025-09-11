# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountPayment(models.Model):
    """ This model represents account.payment."""
    _inherit = 'account.payment'

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        template_id = self.env.ref('account.mail_template_data_payment_receipt')
        notify_partner = res.partner_id._get_notify_partner_ids('custom_payment_completed_ids', self)
        if template_id and notify_partner:
            res.with_context(custom_notify=True).message_post_with_source(
                template_id,
                subtype_xmlid='mail.mt_comment',
                message_type='comment',
            )
        return  res