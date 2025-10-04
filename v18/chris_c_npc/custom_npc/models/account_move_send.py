# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMoveSend(models.AbstractModel):
    """ This model represents account.move.send."""
    _inherit = 'account.move.send'

    def _get_default_mail_partner_ids(self, move, mail_template, mail_lang):
        res = super()._get_default_mail_partner_ids(move, mail_template, mail_lang)
        #if self.move_id:
        #    if self.move_id.np_partner_id:
        #        res = self.move_id.np_partner_id
        #    else:
        #        res = self.move_id.partner_id
        return res
