# Part of Softhealer Technologies.
from odoo import fields, models , _

class MailMess(models.Model):
    _inherit = 'mail.message'
    unique_id = fields.Char("Unique ID")

class AttachmentId(models.Model):
    _inherit = 'ir.attachment'
    attachment_id = fields.Char("Attachment Id")