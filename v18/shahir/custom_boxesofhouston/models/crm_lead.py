from odoo import models, fields, api, _

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    custom_contact_email = fields.Char(
        string='Custom Contact Email',
        help='Custom email field for the contact associated with this lead.'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list: 
            medium = vals.get('medium_id')
            #website order
            if medium == 1:
                vals['partner_name'] = vals.get('name')
            res = super(CrmLead, self).create(vals_list)
            existing_partner = self.env['res.partner'].search([('email','=',vals.get('email_from'))], limit=1)
            if not existing_partner and medium == 1:
                res._handle_partner_assignment(create_missing=True)
                portal_wizard = self.env['portal.wizard'].with_context(active_ids=[res.partner_id.parent_id.id]).create({})
                portal_user = portal_wizard.user_ids.filtered(lambda user: user.email == vals.get('email_from'))
                if portal_user:
                    portal_user.action_grant_access()
            return res
    
    def _prepare_customer_values(self, partner_name, is_company=False, parent_id=False):
        """Prepare values for creating a customer partner."""
        values = super(CrmLead, self)._prepare_customer_values(partner_name, is_company, parent_id)
        if self.custom_contact_email and not is_company:
            values['email'] = self.custom_contact_email
        return values
    
    def _prepare_opportunity_quotation_context(self):
        """Prepare context for creating a new quotation from an opportunity."""
        context = super(CrmLead, self)._prepare_opportunity_quotation_context()
        if self.partner_name and self.partner_id.parent_id:
            context['default_partner_id'] = self.partner_id.parent_id.id
        return context