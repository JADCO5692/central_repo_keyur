from pprint import pprint
from odoo import api, fields, models, tools, exceptions
import datetime
import re
import logging

_logger = logging.getLogger(__name__)


class CalendlySyncWizard(models.TransientModel):
    _name = 'npc_calendly.sync'
    _description = "Sync Calendly"
    _inherit = ['npc_calendly.mixin']

    def import_events_to_crm(self):
        message = "Success!"
        ir_config = self.env['ir.config_parameter'].sudo()
        organization = ir_config.get_param('npc_calendly.calendly_organization_uri')

        if not organization:
            raise exceptions.ValidationError(
                "Please go to General Settings -> Calendly Integration and then click 'Retrieve Organization'.")

        lead_model = self.env['crm.lead'].sudo()
        stage_model = self.env['crm.stage'].sudo()
        default_team_id = self.env.ref('sales_team.team_sales_department', raise_if_not_found=False)

        if default_team_id:
            stage_ids = stage_model.search([('team_id', '=', default_team_id.id)])
            if stage_ids:
                # We only want to sync the opportunities that are in the first 2 stages
                lead_ids = lead_model.search([('npc_user_type', '=', "APP"), ('stage_id', 'in', stage_ids.ids[:2])])
                for lead_id in lead_ids:
                    email_from = lead_id.email_from
                    write_vals = {
                        'meeting_date': False,
                        'meeting_link': False
                    }

                    _logger.warning(f"Retrieving events for {email_from}")
                    params = {
                        'invitee_email': email_from,
                        'organization': organization,
                        'count': 100,  # limit per page, max 100
                        'min_start_time': datetime.datetime.now(datetime.timezone.utc).isoformat().replace(
                            '+00:00', 'Z'),
                        'sort': 'start_time:asc',
                        'status': 'active',
                    }

                    scheduled_events_data = self.get_data(endpoint='/scheduled_events', params=params)

                    if scheduled_events_data.get('collection'):
                        event = scheduled_events_data['collection'][0]
                        start_time = event['start_time'].replace("Z", "")
                        event_location = event['location']

                        # Get zoom URL
                        # It must have status "pushed" so that the zoom URL is available
                        if event_location.get('type') == "zoom" and event_location.get('status') == "pushed":
                            write_vals['meeting_date'] = datetime.datetime.fromisoformat(start_time)
                            write_vals['meeting_link'] = event_location.get('join_url')

                            if lead_id.type != 'opportunity':
                                # If not yet an opportunity, create the customer contact and convert lead to opportunity
                                write_vals['type'] = 'opportunity'
                                write_vals['date_conversion'] = fields.Datetime.now()
                                # If "Scheduled zoom call" stage is present, move it to that stage
                                zoom_stage_id = stage_model.search(
                                    [
                                        ('name', 'ilike', "Scheduled zoom call"),
                                        ('team_id', '=', default_team_id.id)], limit=1)
                                if zoom_stage_id:
                                    write_vals['stage_id'] = zoom_stage_id.id

                                lead_id._handle_partner_assignment()

                        # Get phone number
                        invitees_data = self.get_data(
                            endpoint=f"/scheduled_events/{event['uri'].split('/')[-1]}/invitees")
                        if invitees_data.get('collection'):
                            invitees = invitees_data['collection']
                            for invitee in invitees:
                                if invitee['email'] == email_from:
                                    questions_and_answers = invitee.get('questions_and_answers')
                                    if questions_and_answers:
                                        for question in questions_and_answers:
                                            if question.get('question') == "Phone Number" and question.get('answer'):
                                                write_vals['phone'] = question['answer']
                                                break
                                    break

                    # Write the meeting info, overriding to False if not found
                    lead_id.write(write_vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': 'success',
                'sticky': False,
                # 'next': {'type': 'ir.actions.act_window_close'},  # force a form reload
            },
        }
