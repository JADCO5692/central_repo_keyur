from odoo import api, fields, models, _
from lxml import html


# class Alarm(models.Model):
#     _inherit = "calendar.alarm"
#
#     default_intro_calls = fields.Boolean(
#         "New Appointments Default", help="Use as default for new Appointment Types")


class Meetings(models.Model):
    _inherit = 'calendar.event'
    
    physician_ids = fields.Many2many("crm.lead", relation="event_partner_physician_rel",
                                     compute="_compute_np_physician_data", string="Physicians")
    np_ids = fields.Many2many("crm.lead", relation="event_partner_np_rel",
                              compute="_compute_np_physician_data", string="NP")
    practice_state_ids = fields.Many2many('res.country.state', compute="_compute_np_physician_data",
                                          string="States Needing Collaborator")
    
    @api.depends('partner_ids', 'partner_ids')
    def _compute_np_physician_data(self):
        for event in self:
            physician_leads = False
            practice_state_ids = False
            
            lead_model = self.env['crm.lead']
            partners = event.partner_ids
            partners_emails = partners.mapped("email")
            
            np_leads = lead_model.search([('npc_user_type', '=', 'APP'),
                                          '|', ('partner_id', 'in', partners.ids),
                                          ('email_from', 'in', partners_emails)])
            
            if np_leads:
                practice_state_ids = np_leads.mapped("practice_state_ids")
                physicians = np_leads.mapped("physician_ids").filtered(lambda p: p.name.id in partners.ids or \
                              p.md_lead_id.email_from in partners_emails)
                physician_leads = physicians.mapped("md_lead_id")
            
            if not physician_leads:
                physician_leads = lead_model.search([('npc_user_type', '=', 'PHYS'),
                                                     '|', ('partner_id', 'in', partners.ids),
                                                     ('email_from', 'in', partners_emails)])
                
            event.physician_ids = physician_leads
            event.np_ids = np_leads
            event.practice_state_ids = practice_state_ids
            
    def _get_email_subject(self):
        self.ensure_one()
        nps = self.np_ids.mapped('name') if self.np_ids else []
        physicians = ['Dr. {}'.format(p.name) for p in self.physician_ids] if self.physician_ids else []
        states = ", ".join(self.practice_state_ids.mapped("code"))
        return "{} intro call ({})".format(" & ".join(physicians + nps), states)
    
    def _get_meeting_link(self):
        for event in self.filtered(lambda e: e.description):
            try:
                desc_tree = html.fromstring(event.description)
                links = desc_tree.xpath('//a/@href')
                for link in links:
                    # Get only google meet and zoom meeting links
                    if ('meet.google.com' in link) or ('web.zoom.us' in link):
                        event.videocall_location = link
                        break
            except Exception as e:
                _logger.exception("Failed to get meeting link for event {} [{}]\n Error: {}".format(event.name, event.id, e))
                
    @api.model_create_multi
    def create(self, vals_list):
        events = super().create(vals_list)
        events.filtered(lambda e: not e.videocall_location)._get_meeting_link()
        return events
    
    def write(self, values):
        res = super().write(values)
        if values.get("description"):
            self._get_meeting_link()
        return res
        
    @api.depends("name")
    def _compute_alarm_ids(self):
        defualt_reminders = self.env["calendar.alarm"].search([("default_for_new_appointment_type", "=", True)])
        for event in self:
            event.alarm_ids = defualt_reminders.ids


        


    
           
