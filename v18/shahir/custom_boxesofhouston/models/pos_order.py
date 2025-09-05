from odoo import models, api, fields

class PosOrder(models.Model):
    _inherit = 'pos.order'

    route_id = fields.Many2one('stock.route','Selected Route') 

    @api.model
    def _order_fields(self, ui_order):
        order = super()._order_fields(ui_order)
        order["route_id"] = ui_order.get('route_id', False) 
        return order
    
    def _export_for_ui(self, order):
        ui_order = super()._export_for_ui(order)
        ui_order["route_id"] = order.route_id
        return ui_order

    @api.model
    def _process_order(self, order, existing_order):
        res = super()._process_order(order, existing_order)
        if res:
            pricelists = self.env['product.pricelist'].sudo().search([])
            order = self.browse([res]) 
            if order.partner_id:
                customer_id = order.partner_id.id
                customer_pricelist = pricelists.filtered(lambda p:customer_id in p.customer_id.ids)
                if customer_pricelist:
                    self.update_pricelist_item(order,customer_pricelist[0])
                else:
                    self.create_pricelist_item(order)
        return res

    def update_pricelist_item(self,order,pricelist):
        item_obj = self.env['product.pricelist.item'].sudo()
        for line in order.lines:
            line_items = pricelist.item_ids.filtered(lambda x:x.product_tmpl_id.id == line.product_id.product_tmpl_id.id)
            if line_items:
                offered_qty_line = line_items.filtered(lambda x:x.min_quantity == line.qty)
                if not offered_qty_line:
                    less_qty_lines = line_items.filtered(lambda x:x.min_quantity < line.qty)
                    max_qty = max(less_qty_lines.mapped('min_quantity'))
                    immediate_less_line = line_items.filtered(lambda x:x.min_quantity == max_qty)
                    if not immediate_less_line:
                        item_obj.create(self.prepare_pl_item_vals(line, pricelist, line.qty))
                    else:
                        if immediate_less_line.fixed_price != line.price_unit:
                            item_obj.create(self.prepare_pl_item_vals(line, pricelist, line.qty))
                else:        
                    offered_qty_line.update({
                        'fixed_price':line.price_unit,
                    })  
            else:
                if line.qty > 1:
                    item_obj.create(self.prepare_pl_item_vals(line, pricelist, line.qty))
                item_obj.create(self.prepare_pl_item_vals(line, pricelist, 0.0))
    
    def create_pricelist_item(self,order):
        pricelist_obj = self.env['product.pricelist'].sudo()
        item_obj = self.env['product.pricelist.item'].sudo()
        prepare_pricelist_data = self.prepare_pricelist_data(order)
        pricelist_obj = pricelist_obj.create(prepare_pricelist_data)
        if order.partner_id and pricelist_obj:
            order.partner_id.property_product_pricelist = pricelist_obj.id
        if pricelist_obj:
            for line in order.lines:
                if line.qty > 1:
                    item_obj.create(self.prepare_pl_item_vals(line,pricelist_obj,line.qty)) 
                item_obj.create(self.prepare_pl_item_vals(line, pricelist_obj, 0.0))
    
    def prepare_pricelist_data(self,order):
        partner_id = order.partner_id and order.partner_id.id or False
        vals = {
            'name':order.partner_id.name or '',
            'customer_id':partner_id if partner_id else False
        }
        return vals
    
    def prepare_pl_item_vals(self,line,pl,qty):
        return{
            'applied_on':'1_product',
            'product_tmpl_id':line.product_id.product_tmpl_id.id,
            'product_id':line.product_id.id,
            'compute_price':'fixed',
            'fixed_price':line.price_unit,
            'min_quantity':qty,
            'pricelist_id':pl.id
        }
    
class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    def _prepare_procurement_values(self,group_id):
        res = super()._prepare_procurement_values(group_id)
        if self.order_id.route_id:
           res.update({'route_ids':self.order_id.route_id}) 
        return res