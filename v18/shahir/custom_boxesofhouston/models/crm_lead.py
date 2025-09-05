from odoo import models, fields, api, _

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    custom_contact_email = fields.Char(
        string='Custom Contact Email',
        help='Custom email field for the contact associated with this lead.'
    )

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