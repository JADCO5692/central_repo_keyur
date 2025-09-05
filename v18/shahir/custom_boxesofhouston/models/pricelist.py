# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    customer_id = fields.Many2one('res.partner',string="Customer")
    cust_company_id = fields.Many2one('res.partner','Parent Company',related="customer_id.parent_id")
    phone = fields.Char('Phone Number',related="customer_id.phone")
    email = fields.Char('Email',related="customer_id.email")

    @api.model
    def create(self, vals):  
        pricelist = super().create(vals)
        pos_configs = self.env['pos.config'].search([])
        for pconfig in pos_configs:
            pconfig.write({
                'available_pricelist_ids': [(4, pricelist.id)]
            })
        return pricelist
    
    @api.onchange('customer_id')
    def _onchange_(self):
        if self.customer_id:
            pr = self.search([('customer_id','=',self.customer_id.id)])
            if pr:
                self.customer_id = False
                raise ValidationError(_('A pricelist is already assigned to this customer.'))