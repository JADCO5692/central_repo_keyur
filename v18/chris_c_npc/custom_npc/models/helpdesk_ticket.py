from odoo import models, api

class HelpdekTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for rec in self:
            if rec.partner_id and rec.partner_id.user_id:
                rec.user_id = rec.partner_id.user_id

    def create(self,vals):
        res = super(HelpdekTicket,self).create(vals)
        for ticket in res:
            if ticket.partner_id and ticket.partner_id.user_id:
                ticket.user_id = ticket.partner_id.user_id
        return res