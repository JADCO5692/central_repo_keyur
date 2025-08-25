from odoo import models, api, fields


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    @api.depends('user_id')
    def _compute_team_id(self):
        res = super()._compute_team_id()

        for convert_id in self:
            convert_id.team_id = convert_id.lead_id.team_id

        return res

    @api.depends('lead_id')
    def _compute_action(self):
        super()._compute_action()
        for convert in self:
            if convert.lead_id:
                convert.action = 'create'

    def action_apply(self):
        """ Override convert to opportunity function so that we always create a contact when converting lead to
        opportunity, merging any contact that already exists as they are generated when sending calendar invites
        """
        merge_model = self.env['base.partner.merge.automatic.wizard']
        lead = self.lead_id
        
        # Partner is generated after converting lead to opportunity
        partner_id = lead.partner_id
        
        matched_partner_ids = self.env['res.partner'].sudo().search([
            ('email', '=', lead.email_from),
            ('name', '=', lead.email_from),
            ('id', '!=', partner_id.id)])

        res = super().action_apply()

        # merge one by one since you can only merge 3 records at once
        if partner_id:
            for matched_partner_id in matched_partner_ids:
                merge_model._merge([matched_partner_id.id, partner_id.id], partner_id)

        return res
