from odoo import fields, http, api, SUPERUSER_ID
from odoo.http import request
from odoo.modules.registry import Registry
from pprint import pprint
import json
import datetime
import logging

_logger = logging.getLogger(__name__)


class CalendlyController(http.Controller):

    @http.route('/npc_calendly/webhook', type='json', auth='public')
    def calendly_webhook(self, **kw):
        json_data = request.get_json_data()
        _logger.info(f"Received Calendly webhook data: {json_data}")

        if json_data.get('event') == "invitee.created":
            payload = json_data['payload']
            email = payload['email']
            event = payload['scheduled_event']
            questions_and_answers = [(0, 0, {'name': p.get('question'), 'answer': p.get('answer')}) for p in payload.get('questions_and_answers')]

            with Registry(request.db).cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, request.context)
                lead_model = env['crm.lead']
                stage_model = env['crm.stage']
                lead_id = lead_model.search([('email_from', '=', email)], limit=1)
                default_team_id = request.env.ref('sales_team.team_sales_department', raise_if_not_found=False)

                if lead_id:
                    event_location = event['location']
                    # Prepare Calendly fields
                    calendly_vals = {
                        'calendly_created_at': datetime.datetime.fromisoformat(payload.get('created_at').replace("Z", "")).strftime('%Y-%m-%d %H:%M:%S') if payload.get('created_at') else False,
                        'calendly_event_uri': payload.get('uri'),
                        'calendly_event_type': event.get('name'),
                        'calendly_guest_email': email,
                        'calendly_guest_name': payload.get('name'),
                        'custom_calendly_qa_ids': questions_and_answers,
                        'calendly_json_data': json.dumps(json_data),
                    }
                    # Meeting info
                    if event_location.get('type') == "zoom" and event_location.get('status') == "pushed":
                        start_time = event['start_time'].replace("Z", "")
                        calendly_vals.update({
                            'meeting_date': datetime.datetime.fromisoformat(start_time),
                            'meeting_link': event_location.get('join_url')
                        })
                        if lead_id.type != 'opportunity':
                            calendly_vals['type'] = 'opportunity'
                            calendly_vals['date_conversion'] = fields.Datetime.now()
                            zoom_stage_id = stage_model.search([
                                ('name', 'ilike', "Scheduled zoom call"),
                                ('team_id', '=', default_team_id.id)], limit=1)
                            if zoom_stage_id:
                                calendly_vals['stage_id'] = zoom_stage_id.id
                            lead_id._handle_partner_assignment()
                        # Update phone number
                        if questions_and_answers:
                            for question in questions_and_answers:
                                if question[2].get('question') == "Phone Number" and question[2].get('answer'):
                                    calendly_vals['phone'] = question[2]['answer']
                                    break
                    lead_id.write(calendly_vals)
                    _logger.warning(f"Successfully converted lead {lead_id.id} to opportunity with meeting info and Calendly data.")
        return http.Response("OK", status=200)
