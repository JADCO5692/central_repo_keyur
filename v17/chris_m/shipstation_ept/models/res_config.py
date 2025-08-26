
from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    shipstation_instance_id = fields.Many2one("shipstation.instance.ept", string="Shipstation Instance")
    tracking_link = fields.Char(string="Tracking Link",
                                help="Tracking link(URL) useful to track the "
                                     "shipment or package from this URL.",
                                size=256)
    shipstation_weight_uom = fields.Selection([('grams', 'Grams'),
                                               ('pounds', 'Pounds'),
                                               ('ounces', 'Ounces')], default='grams',
                                              string="Supported Weight UoM",
                                              help="Supported Weight UoM by ShipStation")
    shipstation_package_id = fields.Many2one('stock.package.type', string='Shipstation Package')
    shipstation_last_export_order = fields.Datetime(string='Last Export Order')
    last_import_product = fields.Datetime(string='Last Sync Product')
    active_debug_mode = fields.Boolean(string='Active Debug Mode', copy=False, default=False)
    use_same_tracking_link_for_all_shipping_provider = fields.Boolean(
        string='Do you want to use Shipstation Tracking Link for all shipping provider?',
        copy=False,
        default=False)
    contents_of_international_shipment = fields.Selection([('merchandise', 'Merchandise'),
                                                           ('documents', 'Documents'),
                                                           ('gift', 'Gift'),
                                                           ('returned_goods', 'Returned Goods'),
                                                           ('sample', 'Sample')], default='merchandise',
                                                          string="Contents of International Shipment",
                                                          help="Contents of International Shipment by ShipStation")
    non_delivery_option = fields.Selection([('return_to_sender', 'Return to Sender'),
                                            ('treat_as_abandoned', 'Treat as Abandoned')],
                                           default='return_to_sender',
                                           string="Non-Delivery Option",
                                           help="Non-Delivery option for International Shipment by ShipStation")
    is_shipping_label_package_wise = fields.Boolean(string="Generate Shipping Label Put In Pack Wise",
                                                    help="It Will Use To Generate The Shipping Label Put In Pack Wise", default=False)

    @api.onchange('shipstation_instance_id')
    def onchange_shipstation_instance_id(self):
        """
        Modify By - Vaibhav Chadaniya
        19728 - Generate the Shipping Label Package wise (Put-in-Pack) v17
        add is_shipping_label_package_wise vals
        """
        vals = {}
        if self.shipstation_instance_id:
            instance_id = self.shipstation_instance_id
            vals['tracking_link'] = instance_id.tracking_link or False
            vals['shipstation_weight_uom'] = instance_id.shipstation_weight_uom or False
            vals['active_debug_mode'] = instance_id.active_debug_mode or False
            vals['use_same_tracking_link_for_all_shipping_provider'] = instance_id.use_same_tracking_link_for_all_shipping_provider or False
            vals['contents_of_international_shipment'] = instance_id.contents_of_international_shipment or False
            vals['non_delivery_option'] = instance_id.non_delivery_option or False
            vals['is_shipping_label_package_wise'] = instance_id.is_shipping_label_package_wise or False
        return {'value': vals}
    
    def execute(self):
        instance_id = self.shipstation_instance_id
        values = {}
        res = super().execute()
        ctx = {}
        if instance_id:
            ctx.update({'default_instance_id': instance_id.id})
            values['tracking_link'] = self.tracking_link or False
            values['shipstation_weight_uom'] = self.shipstation_weight_uom or False
            values['active_debug_mode'] = self.active_debug_mode or False
            values['is_shipping_label_package_wise'] = self.is_shipping_label_package_wise or False
            mapping_rec = self.env["shipstation.weight.mapping"].search(
                [('shipstation_weight_uom', '=', self.shipstation_weight_uom)], limit=1)
            if mapping_rec:
                values['weight_uom_id'] = mapping_rec.shipstation_weight_uom_id.id or False

            values['use_same_tracking_link_for_all_shipping_provider'] = self.use_same_tracking_link_for_all_shipping_provider or False
            values['contents_of_international_shipment'] = self.contents_of_international_shipment or False
            values['non_delivery_option'] = self.non_delivery_option or False

            instance_id.sudo().write(values)
        return res
