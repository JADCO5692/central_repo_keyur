from odoo import api, models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sharetribe_client_id = fields.Char("Sharetribe Client ID", config_parameter='npc_sharetribe.client_id')
    sharetribe_client_secret = fields.Char(
        "Sharetribe Client Secret", config_parameter='npc_sharetribe.client_secret')

