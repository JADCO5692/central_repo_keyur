from odoo import models, api, _, fields
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.onchange('categ_id')
    def on_change_category_id(self):
        if self.categ_id and self.categ_id.pos_category_id:
            if not self.categ_id.pos_category_id.id in self.pos_categ_ids.ids:
                # pos_category_ids = self.pos_categ_ids.ids.append(self.categ_id.pos_category_id.id)
                self.pos_categ_ids = self.categ_id.pos_category_id.ids

        if self.categ_id and self.categ_id.ecommerce_category_id:
            if not self.categ_id.ecommerce_category_id.id in self.public_categ_ids.ids:
                # ecommerce_category_ids = self.public_categ_ids.ids.append(self.categ_id.ecommerce_category_id.id)
                self.public_categ_ids = self.categ_id.ecommerce_category_id.ids 

    @api.onchange('default_code')
    def _onchange_default_code(self):
        if not self.default_code:
            return

        domain = [('default_code', '=ilike', self.default_code)]
        if self.id.origin:
            domain.append(('id', '!=', self.id.origin))

        if self.env['product.template'].search_count(domain, limit=1):
            raise ValidationError(_("The Internal Reference '%s' already exists.", self.default_code))
        
    def _is_pricelist_item(self): 
        pricelist = self.env['product.pricelist'].sudo().search([('customer_id','in',self.env.user.partner_id.ids)]) 
        items = self.env['product.pricelist.item']
        for pr in pricelist:
            if pr.item_ids:
                items = items+ pr.item_ids 
        return len(items.filtered(lambda a:a.product_tmpl_id.id == self.id))
    
    def get_price_list_ids(self): 
        pricelist = self.env['product.pricelist'].sudo().search([('customer_id','in',self.env.user.partner_id.ids)]) 
        items = self.env['product.pricelist.item']
        for pr in pricelist:
            if pr.item_ids:
                items = items+ pr.item_ids 
        return items.mapped('product_tmpl_id.id')
    

class ProductProductCustom(models.Model):
    _inherit = 'product.product'

    replenishment_threshold = fields.Float(
        string="Replenishment Threshold",
        default=0.0,
        help="If on-hand is *at least* this, when sale order is confirmed, a replenishment request is created."
    )