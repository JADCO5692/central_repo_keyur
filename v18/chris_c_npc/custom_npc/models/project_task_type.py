from odoo import models, fields

class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    is_last_state = fields.Boolean('Is Last Stage')
    