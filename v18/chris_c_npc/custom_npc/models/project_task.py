from odoo import models, api

class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        for rec in self:
            if rec.stage_id.is_last_state:
                rec.state = '1_done'
            else:
                rec.state = '01_in_progress'

    def write(self,vals):
        res = super(ProjectTask,self).write(vals)
        if vals.get('stage_id'):
           for rec in self: 
                if rec.stage_id.is_last_state:
                    rec.state = '1_done'
                else:
                    rec.state = '01_in_progress'
        return res
