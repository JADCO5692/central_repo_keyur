# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, api
from odoo.exceptions import UserError

class Logger(models.Model):
    _name = 'sh.office365.base.log'
    _description = 'Helps you to maintain the activity done'
    _order = 'id desc'
     
    name = fields.Char("Name")
    error = fields.Char("Message")
    datetime = fields.Datetime("Date & Time")
    base_config_id = fields.Many2one('sh.office365.base.config')
    field_type = fields.Selection([('contact','Contact'),('calender','Calender'),('mail','Mail'),('task','Task')],string="Office365")
    state = fields.Selection([('success','Success'),('error','Failed')])
    operation = fields.Selection([('import','Import'),('export','Export')])