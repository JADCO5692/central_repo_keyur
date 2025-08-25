from odoo import api, models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    memberstack_secret_key = fields.Char("Memberstack Secret Key", config_parameter='npc_memberstack.secret_key')

