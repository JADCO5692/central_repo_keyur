from odoo import models, api, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    np_partner_id = fields.Many2one('res.partner','NP Partner')
    npc_fees_waiver_months = fields.Integer(default=0, string="NPC Fees - Waiver Months")
    
    npc_fees_waiver_days = fields.Integer(string="NPC Fees - Waiver Days")

    @api.onchange("npc_fees_waiver_months")
    def _onchange_npc_fees_waiver_months(self):
        """Update waiver days when months change"""
        for record in self:
            record.npc_fees_waiver_days = npc_fees_waiver_months * 30

    @api.onchange('opportunity_id')
    def create_sale_lines(self): 
        for rec in self: 
            if rec.opportunity_id and rec.opportunity_id.physician_ids:
                # physicial_fee =  sum(rec.opportunity_id.physician_ids.mapped('collab_fee'))
                # npc_fee =  sum(rec.opportunity_id.physician_ids.mapped('npc_fee')) 
                product_obj = self.env['product.template'].sudo()
                npc_prod_id = product_obj.search([('is_np_main_fees_product','=',True)])
                physician_prod_id = product_obj.search([('is_physician_main_fees_product','=',True)])
                line_dics = []
                for physician in rec.opportunity_id.physician_ids:
                    # Collabs line
                    if physician.name and physician.name.custom_physician_product:
                        line_dics.append((0,0,{
                            'product_id':physician.name.custom_physician_product.product_variant_id.id, 
                            'name':physician.name.custom_physician_product.name,
                            'price_unit':physician.collab_fee,
                            'product_uom_qty': 1,
                        }))
                    elif physician_prod_id:
                        line_dics.append((0,0,{
                            'product_id':physician_prod_id.product_variant_id.id, 
                            'name':physician_prod_id.name,
                            'price_unit':physician.collab_fee,
                            'product_uom_qty': 1,
                        }))
                    # NPC line
                    if npc_prod_id:
                        line_dics.append((0,0,{
                            'product_id':npc_prod_id.product_variant_id.id, 
                            'name':npc_prod_id.name,
                            'price_unit':physician.npc_fee,
                            'product_uom_qty': 1,
                        }))
                if len(line_dics):
                    rec.order_line = line_dics 

            if rec.opportunity_id:
                rec.np_partner_id = rec.opportunity_id.np_partner_id.id