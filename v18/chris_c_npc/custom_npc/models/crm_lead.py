from odoo import models, fields, api, _

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    np_partner_id = fields.Many2one('res.partner','NP Partner')
    tickets_count = fields.Integer(compute='_compute_tickets_count', default=0, string="Tickets")

    @api.onchange('user_id')
    def _onchange_user_id(self):
        for rec in self:
            rec.partner_id.user_id = self.user_id


    def _compute_tickets_count(self):
        request_model = self.env['helpdesk.ticket'] 
        partner_ids = set(self.mapped('partner_id').ids + self.mapped('np_partner_id').ids) 
        tickets_data = request_model.sudo()._read_group([('partner_id', 'in', list(partner_ids))],['partner_id'],['__count']) 
        tickets_data_mapped = {partner.id: count for partner, count in tickets_data}
 
        for lead in self:
            lead.tickets_count = (tickets_data_mapped.get(lead.partner_id.id, 0) +tickets_data_mapped.get(lead.np_partner_id.id, 0))
    
    def open_tickets(self):
        self.ensure_one() 
        partner_ids = []
        if self.partner_id:
            partner_ids.append(self.partner_id.id)
        if self.np_partner_id:
            partner_ids.append(self.np_partner_id.id) 
        tickets = self.env['helpdesk.ticket'].search([('partner_id', 'in', partner_ids)])

        return {
            'type': 'ir.actions.act_window',
            'name': _('Helpdesk Tickets'),
            'view_mode': 'list,kanban,form',
            'res_model': 'helpdesk.ticket',
            'domain': [('id', 'in', tickets.ids)],
            'context': {
                'default_partner_id': self.partner_id.id or self.np_partner_id.id,
            },
        }