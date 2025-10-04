from odoo import _, api, fields, models
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'
    
    order_type = fields.Selection(
        [
            ('bulk', 'Bulk Order'),
            ('dropship', 'Dropship'),
        ], string='Order Type')

    is_custom_cargo = fields.Boolean(string='Is Delivery Cargo')

    def _is_available_for_order(self, order):
        bulk_bool = request.session.get('bulk')
        dropship_bool = request.session.get('dropship')
        order_type = 'bulk'
        if dropship_bool:
            order_type = 'dropship'
            
        if self.order_type == order_type or not self.order_type:
            return True
        return False

class PickingType(models.Model):
    _inherit = 'stock.picking'

    is_cargo_shipping = fields.Boolean(string='Is Cargo Shipping',related='carrier_id.is_custom_cargo', store=True)