from odoo import models, fields, api
from odoo.exceptions import UserError


class SignRequest(models.Model):
    _inherit = 'sign.request'
    
    crm_partner_id = fields.Many2one("res.partner", string="CRM Partner")
    

class SignTemplate(models.Model):
    _inherit = 'sign.template'
    
    crm_partner_id = fields.Many2one("res.partner", string="CRM Partner")
    
    @api.model
    def create_with_attachment_data(self, name, data, active=True, lead_id=False):
        try:
            attachment = self.env['ir.attachment'].create({'name': name, 'datas': data})
            template_data = {'attachment_id': attachment.id, 'active': active}
            if lead_id:
                template_data["crm_partner_id"] = lead_id
            return self.create(template_data).id
        except UserError:
            return 0
        
        
class SignSendRequest(models.TransientModel):
    _inherit = 'sign.send.request'
    
    @api.onchange('template_id', 'set_sign_order')
    def _onchange_template_id(self):
        partner_id = self.template_id.crm_partner_id and self.template_id.crm_partner_id or False
        # Only apply context when partner exist so that the signer is not empty
        if partner_id:
            self = self.with_context(default_signer_id=partner_id)
        return super(SignSendRequest, self)._onchange_template_id()
        

    
