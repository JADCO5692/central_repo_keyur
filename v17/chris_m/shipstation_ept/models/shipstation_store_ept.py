from odoo import models, fields


class ShipstationStore(models.Model):
    """
    class for shipstation stores.
    """
    _name = 'shipstation.store.ept'
    _description = 'Shipstation Store'

    name = fields.Char(string='Name')
    shipstation_identification = fields.Integer(string='Store Id')
    marketplace_id = fields.Many2one('shipstation.marketplace.ept', string='Marketplace', ondelete="restrict")
    company_name = fields.Char(string='Company Name')
    active = fields.Boolean(string='Is Active')
    website = fields.Char(string='Website')
    shipstation_instance_id = fields.Many2one('shipstation.instance.ept', string='Instance', ondelete='cascade')
    company_id = fields.Many2one(related='shipstation_instance_id.company_id', store=True, string='Company')
