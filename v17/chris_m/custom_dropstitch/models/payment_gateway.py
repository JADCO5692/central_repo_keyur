# -*- coding: utf-8 -*- 

from odoo import models, fields 

class ShopifyPaymentGatewayCustom(models.Model):
    _inherit = 'shopify.payment.gateway.ept'
      
    def shopify_search_create_gateway_workflow(self, instance, order_data_queue_line, order_response,gateway):
        res = super(ShopifyPaymentGatewayCustom,self).shopify_search_create_gateway_workflow(instance, order_data_queue_line, order_response,gateway)
        if instance and instance.custom_sale_payment_term_id:
            res = list(res)
            res[2] = instance.custom_sale_payment_term_id 
            res = tuple(res)
        return res