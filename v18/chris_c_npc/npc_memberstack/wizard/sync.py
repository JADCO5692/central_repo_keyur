from pprint import pprint
from odoo import api, fields, models, tools
import datetime
import logging

_logger = logging.getLogger(__name__)


class MemberstackSyncWizard(models.TransientModel):
    _name = 'npc_memberstack.sync'
    _description = "Sync Memberstack"
    _inherit = ['npc_memberstack.mixin']

    def import_members_to_crm(self):
        message = "Success!"

        def get_users(end_cursor=None):
            _logger.warning(f"Retrieving from cursor {end_cursor} of members results...")
            params = {
                'order': 'ASC',
                'limit': 50,  # limit per page
            }
            if end_cursor:
                params['after'] = end_cursor

            data = self.get_data(endpoint='/members', params=params)

            if data.get('data'):
                crm_model = self.env['crm.lead'].sudo()
                practice_type_model = self.env['npc_crm.practice_type']

                for user in data['data']:
                    memberstack_id = user['id']
                    lead_id = crm_model.with_context(active_test=False).search([('memberstack_id', '=', memberstack_id)], limit=1)
                    custom_fields = user['customFields']
                    contact_name = f"{custom_fields.get('first-name', '')} {custom_fields.get('last-name', '')}"
                    contact_name = contact_name.strip()
                    email = user['auth']['email']
                    tag_id = self.env.ref('npc_memberstack.crm_tag_member', raise_if_not_found=False)
                    team_id = self.env.ref('npc_crm.team_physician', raise_if_not_found=False)
                    try:
                        reg_date = datetime.datetime.fromisoformat(user['createdAt'])
                    except ValueError:
                        reg_date = datetime.datetime.strptime(user['createdAt'], '%Y-%m-%dT%H:%M:%S.%fZ')

                    practice_types = custom_fields.get('practice-types', "").split(',')
                    practice_type_ids = practice_type_model.browse()
                    for practice_type in practice_types:
                        practice_type = practice_type.strip().capitalize()
                        practice_type_id = practice_type_model.search([('name', 'ilike', practice_type)])
                        if not practice_type_id:
                            practice_type_id = practice_type_model.create([{'name': practice_type}])
                        practice_type_ids += practice_type_id

                    active_license_states = custom_fields.get('active-license-states', "").split(',')
                    active_license_states = [state_name.strip().capitalize() for state_name in active_license_states]
                    active_license_state_ids = self.env['res.country.state'].search(
                        [('name', 'in', active_license_states)])

                    lead_data = {
                        'memberstack_id': memberstack_id,
                        'name': f"{contact_name or email}",
                        'contact_name': contact_name,
                        'email_from': email,
                        'email_verified': user['verified'],
                        'reg_date': reg_date.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT),
                        'board_certs': custom_fields.get('board-certification'),
                        'npi_number': custom_fields.get('npi'),
                        'controlled_substances': custom_fields.get('controlled-substances-needed') == 'yes',
                        'medical_degree': custom_fields.get('degree-type'),
                        'npc_user_type': 'PHYS',
                        'practice_type_ids': [(6, 0, practice_type_ids.ids)],
                        'active_license_state_ids': [(6, 0, active_license_state_ids.ids)],
                    }
                    if tag_id:
                        lead_data['tag_ids'] = [(4, tag_id.id)]
                    if not lead_id:
                        if team_id:
                            lead_data['team_id'] = team_id.id
                            lead_data['user_id'] = team_id.user_id.id
                        lead_id.with_context(mail_auto_subscribe_no_notify=True).create([{
                            'type': 'lead',
                            **lead_data
                        }])

                    # Override for existing leads
                    # TODO: add force sync action that will override the data
                    # else:
                    #     lead_id.write(lead_data)

            if data.get('hasNextPage'):
                has_next_page = data['hasNextPage']
                end_cursor = data['endCursor']
                if has_next_page:
                    get_users(end_cursor)

        get_users()

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
