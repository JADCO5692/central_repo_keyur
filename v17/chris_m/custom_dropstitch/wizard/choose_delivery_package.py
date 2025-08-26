# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, _


class ChooseDeliveryPackage(models.TransientModel):
    _inherit = 'choose.delivery.package'
    
    def action_put_in_pack(self):
        res = super().action_put_in_pack()
        if res and self.picking_id.check_for_auto_export():
            self.picking_id.custom_auto_export_to_shipstation = True
        return res