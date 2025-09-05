from odoo import _, api, fields, models
from odoo.osv import expression

import logging
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)


class CustomPartner(models.Model):
    _inherit = "res.partner"

    custom_resale_permit = fields.Binary(string="Resale Permit")
    custom_resale_permit_f = fields.Char(string="Resale Permit File")
    custom_tax_exem_cert = fields.Binary(string="Tax Exemption Certificate")
    custom_tax_exem_cert_f = fields.Char(string="Tax Exemption Certificate File")
    custom_resale_certificate = fields.Binary(string="Resale Certificate")
    custom_resale_certificate_f = fields.Char(string="Resale Certificate File")
    custom_customer_profile = fields.Binary(string="Customer Profile")
    custom_customer_profile_f = fields.Char(string="Customer Profile File")
    
    custom_tax_exemption = fields.Selection([("exempted", "Tax Exempted"),
                                               ("not_exempted", "Not Tax Exempted")],
                                              string="Tax Exemption Status",
                                              default="not_exempted",
                                              help="Select the tax exemption status of the customer.")

    @api.onchange('custom_tax_exemption')
    def _onchange_custom_tax_exemption(self):
        if self.custom_tax_exemption == "exempted":
            fiscal_position = self.env['account.fiscal.position'].sudo().search([('custom_tax_exemption', '=', 'exempted')], limit=1)
            if fiscal_position:
                self.property_account_position_id = fiscal_position
        else:
            self.property_account_position_id = False
    
    @api.model
    def _commercial_fields(self):
        res = super(CustomPartner,self)._commercial_fields()   
        addtional_fields = [
            'user_id',
            'property_payment_term_id',
            'property_product_pricelist',
            'property_delivery_carrier_id',
            'custom_tax_exemption',
            'property_account_position_id',
        ]
        
        res = res + addtional_fields
        return res
    
    def write(self, vals):
        if not self._context.get('ecommerce_create'):
            for rec in self:
                email = vals.get('email')
                phone = vals.get('phone')
                mobile = vals.get('mobile')
                if phone or email or mobile:
                    params = {}
                    if email:
                        params['email'] = email
                    if phone:
                        params['phone'] = phone
                    if mobile:
                        params['mobile'] = mobile

                    rec.check_for_existing_user(params,'write')
        return super(CustomPartner, self).write(vals)
    
    @api.model_create_multi
    def create(self, vals_list):
        if not self._context.get('ecommerce_create'):
            for vals in vals_list: 
                self.check_for_existing_user(vals,'create') 
        return super(CustomPartner, self).create(vals_list)
     
    def check_for_existing_user(self,vals,action): 
        existing_contact = self.env['res.partner'].sudo()  
        email = vals.get('email')
        phone = vals.get('phone')
        mobile = vals.get('mobile') 
        matched_field = ''
        matched_field_value = ''
        self.env['res.partner'].flush_model(['phone', 'mobile', 'parent_id'])
        if email:  
            params = [email]
            sql = """
                SELECT id
                FROM res_partner
                WHERE active = TRUE
                AND email = %s
            """

            if action == 'write':
                sql += " AND id != %s"
                params.append(self.id)
            if vals.get('parent_id'):
                pid = vals['parent_id']
                sql += " AND id != %s AND parent_id != %s"
                params += [pid, pid]
            if self.parent_id:
                sql += " AND parent_id != %s"
                params.append(self.parent_id.id)
            if self.child_ids:
                sql += " AND parent_id != %s"
                params.append(self.id)

            sql += " LIMIT 1"

            self.env.cr.execute(sql, params)
            contact = self.env.cr.fetchone()
            if contact:
                existing_contact = self.env['res.partner'].browse(contact[0])
                matched_field = 'email'
                matched_field_value = email

        if phone:  
            params = [phone, phone]
            sql = """
                SELECT id
                FROM res_partner
                WHERE active = TRUE
                AND (phone = %s OR mobile = %s)
            """

            if action == 'write':
                sql += " AND id != %s"
                params.append(self.id)
            if vals.get('parent_id'):
                pid = vals['parent_id']
                sql += " AND id != %s AND parent_id != %s"
                params += [pid, pid]
            if self.parent_id:
                sql += " AND parent_id != %s"
                params.append(self.parent_id.id)
            if self.child_ids:
                sql += " AND parent_id != %s"
                params.append(self.id)

            sql += " LIMIT 1"

            self.env.cr.execute(sql, params)
            contact = self.env.cr.fetchone()
            if contact:
                existing_contact = self.env['res.partner'].browse(contact[0])
                matched_field = 'phone'
                matched_field_value = phone

        if mobile: 
            params = [mobile, mobile]
            sql = """
                SELECT id
                FROM res_partner
                WHERE active = TRUE
                AND (phone = %s OR mobile = %s)
            """

            if action == 'write':
                sql += " AND id != %s"
                params.append(self.id)

            if vals.get('parent_id'):
                pid = vals['parent_id']
                sql += " AND id != %s AND parent_id != %s"
                params += [pid, pid]

            if self.parent_id:
                sql += " AND parent_id != %s"
                params.append(self.parent_id.id)

            if self.child_ids:
                sql += " AND parent_id != %s"
                params.append(self.id)

            sql += " LIMIT 1"

            self.env.cr.execute(sql, params)
            contact = self.env.cr.fetchone()
            if contact:
                existing_contact = self.env['res.partner'].browse(contact[0])
                matched_field = 'mobile'
                matched_field_value = mobile

        if existing_contact: 
            raise ValidationError(f'Contact already exist with this {matched_field}({matched_field_value}).')
        
    @api.model
    def _load_pos_data_domain(self, data):
        domain = super()._load_pos_data_domain(data)
        domain = expression.AND([[('parent_id', '=', False)], domain])
        return domain