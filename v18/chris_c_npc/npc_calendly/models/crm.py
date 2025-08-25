from odoo import models, api, fields
from pprint import pprint
import logging

_logger = logging.getLogger(__name__)


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    meeting_date = fields.Datetime(string="Meeting Date", tracking=True)
    meeting_link = fields.Char(string="Meeting Link", tracking=True)
    calendly_created_at = fields.Datetime(string="Calendly Created At")
    calendly_event_uri = fields.Char(string="Calendly Event URI")
    calendly_event_type = fields.Char(string="Calendly Event Type")
    calendly_guest_email = fields.Char(string="Calendly Guest Email")
    calendly_guest_name = fields.Char(string="Calendly Guest Name")
    calendly_questions_answers = fields.Text(string="Calendly Q&A")
    calendly_json_data = fields.Text(string="Calendly Raw JSON")

    def open_meeting_link(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_url',
            'url': self.meeting_link,
            'target': 'new'
        }
