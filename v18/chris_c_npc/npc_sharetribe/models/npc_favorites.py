# -*- coding: utf-8 -*-
from odoo import fields,models

class NpcFavorites(models.Model):
    _name = 'npc.favorites'
    _rec_name = 'partner_id'

    name = fields.Char(string='Name')
    partner_id = fields.Many2one('res.partner', string='Partner')
    custom_physician_product = fields.Many2one('product.template', string="Physician Product", related="partner_id.custom_physician_product")
