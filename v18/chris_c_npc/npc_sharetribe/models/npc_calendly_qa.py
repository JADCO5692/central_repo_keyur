# -*- coding: utf-8 -*-
from odoo import api, fields, models


class NpcCalendlyQa(models.Model):
    """ This model represents npc.calendly.qa."""
    _name = 'npc.calendly.qa'
    _description = 'Calendly Q&A'

    name = fields.Char(string='Question', required=True)
    answer = fields.Char(string='Answer')
    crm_id = fields.Many2one('crm.lead', string='Crm')
