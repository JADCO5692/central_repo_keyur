from odoo import fields, models, api, SUPERUSER_ID


class Partner(models.Model):
    _inherit = 'res.partner'

    sms_ids = fields.One2many('twilio.incoming.sms', 'partner_id', string="Incoming SMS")
