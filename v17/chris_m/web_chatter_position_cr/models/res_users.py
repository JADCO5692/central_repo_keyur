# -*- coding: utf-8 -*-
from odoo import fields, models
import json


class ResUsers(models.Model):
    _inherit = "res.users"

    chatter_position = fields.Selection([
        ("auto", "Responsive"),
        ("bottom", "Bottom"),
        ("sided", "Side"), ], default="auto")
    
    ir_model_ids = fields.Many2many(comodel_name='ir.model',string='Models')

    def get_chat_models(self):
        models_str = ''
        for model in self.ir_model_ids:
            models_str += model.model + ','
        return models_str

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ["chatter_position","ir_model_ids"]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ["chatter_position","ir_model_ids"]
