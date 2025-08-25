# -*- coding: utf-8 -*-
from odoo import fields,models

class NpcFavorites(models.Model):
    _name = 'npc.favorites'
    _rec_name = 'partner_id'

    name = fields.Char(string='Name')
    partner_id = fields.Many2one('res.partner', string='Partner')