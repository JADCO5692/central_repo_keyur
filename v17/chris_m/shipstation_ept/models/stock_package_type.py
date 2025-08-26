from odoo import fields, models, api


class StockPackageType(models.Model):
    _inherit = 'stock.package.type'

    package_carrier_type = fields.Selection(selection_add=[('shipstation_ept', 'Shipstation')],
                                            ondelete={'shipstation_ept': 'cascade'})
    shipstation_carrier_id = fields.Many2one('shipstation.carrier.ept',
                                             string='Shipstation Carrier')
    shipstation_instance_id = fields.Many2one('shipstation.instance.ept',
                                              string='Shipstation Instance')

    @api.model_create_multi
    def create(self, vals_list):
        """
        Add: override create method of stock.package.type
        @param vals: record of stock.package.type
        @return: returns the value of stock.package.type
        """
        for vals in vals_list:
            if vals.get('shipstation_carrier_id', False):
                current_carrier_id = self.env["shipstation.carrier.ept"].browse(vals.get('shipstation_carrier_id'))
                vals.update({
                    "shipstation_instance_id": current_carrier_id.shipstation_instance_id.id,
                    "company_id": current_carrier_id.company_id.id,
                    "package_carrier_type": 'shipstation_ept'
                })
        return super(StockPackageType, self).create(vals_list)


class ChooseDeliveryPackage(models.TransientModel):
    _inherit = 'choose.delivery.package'
    _description = 'Delivery Package Selection Wizard'

    shipstation_instance_id = fields.Many2one(related='picking_id.shipstation_instance_id')
    shipstation_carrier_id = fields.Many2one(related='picking_id.shipstation_carrier_id')
