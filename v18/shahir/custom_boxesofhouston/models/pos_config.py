from odoo import models, fields

class Posconfig(models.Model):
    _inherit = 'pos.config'

    route_ids = fields.Many2many('stock.route',string='Additional Routes')

    def get_pos_routes(self):
        routes = self.sudo().route_ids.read()
        return routes or {}
    
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_route_ids = fields.Many2many('stock.route',string='Additional Routes',
                                    related="pos_config_id.route_ids",readonly=False,
                                    domain="[('available_for_pos_order','=',True)]")