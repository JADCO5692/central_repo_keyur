# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import html_escape

class MrpProduction(models.Model):
    _inherit = "mrp.production"
 
    def action_print_workorder_label(self):
        self.ensure_one() 
        active_ids = self.ids
        active_model = 'mrp.production'
        context = {
            'active_ids': active_ids,
            'active_model': active_model,
        }
        return self.env.ref('custom_dropstitch_reports.action_report_label_workorder'
        ).with_context(context).report_action(self)
    
    def get_display_name(self):
        product = self.product_id.name or ''
        colorway = ''
        if len(self.product_id.product_template_attribute_value_ids):
            # attr_value = self.env.ref() 
            attribute_ids = self.product_id.product_template_attribute_value_ids.mapped('attribute_id.id')
            colorway_attr = self.env['product.attribute'].sudo().search([('id','in',attribute_ids),('name','ilike','colorway')])
            if len(colorway_attr):
                colorway = self.product_id.product_template_attribute_value_ids.filtered(lambda a:a.attribute_id.id in colorway_attr.ids).name or ''
        
        personalize = self.custom_line1 or ''
        return product+'-'+colorway +'-'+personalize

    def get_order_date(self):
        return self.custom_sale_order_line.order_id.create_date.strftime('%Y-%m-%d') or ''