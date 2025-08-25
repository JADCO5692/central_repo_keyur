# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models

class OfficeQueue(models.Model):
    _name = 'sh.office.queue'
    _description = 'Helps you to add incoming req in queue'
    _order = 'id desc'

    queue_type = fields.Selection([('contact','Contact'),('calendar','Calendar')])
    sh_contact_id = fields.Char("Contacts")
    sh_queue_name = fields.Char("Name")
    sh_calendar_id = fields.Char("Calendar")
    queue_sync_date = fields.Datetime("Sync Date-Time")
    sh_current_config = fields.Many2one('sh.office365.base.config', string='Current Config')
    sh_current_state = fields.Selection([('draft','Draft'),('done','Done'),('error','Failed')],string="State")
    sh_message = fields.Char(string='Message')

    def _done(self):
        self.write({
            'sh_current_state': 'done',
            'sh_message': ''
        })

    def import_office_manually(self):
        active_queue_ids = self.env['sh.office.queue'].browse(self.env.context.get('active_ids'))
        contact_ids = active_queue_ids.filtered(lambda l : l.sh_contact_id != False)
        calendar_ids = active_queue_ids.filtered(lambda l : l.sh_calendar_id != False)
        import_limit = 100
        if contact_ids:
            for data in contact_ids:
                if not import_limit:
                    break
                data.sh_current_config.import_contacts(data.sh_contact_id)
                import_limit -= 1
        if calendar_ids:
            for data in calendar_ids:
                if not import_limit:
                    break
                data.sh_current_config.import_calendar_data(data)
                import_limit -= 1
