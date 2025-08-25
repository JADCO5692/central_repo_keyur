from pprint import pprint
from odoo import api, fields, models, tools
import logging
import datetime
import json
from urllib.parse import urljoin

_logger = logging.getLogger(__name__)


class SharetribeSyncWizard(models.TransientModel):
    _name = 'npc_sharetribe.sync'
    _description = "Sync Sharetribe"
    _inherit = ['npc_sharetribe.mixin']

    def import_users_to_crm(self):
        message = "Success!"

        def get_users(page=1):
            params = {
                'page': page,
                'perPage': 100
            }

            _logger.warning(f"Retrieving page {page} of users query results...")
            data = self.get_data(endpoint='/v1/integration_api/users/query', params=params)

            if data.get('data'):
                crm_model = self.env['crm.lead'].sudo()

                for user in data['data']:
                    sharetribe_id = user['id']
                    lead_id = crm_model.with_context(active_test=False).search([('sharetribe_id', '=', sharetribe_id)], limit=1)
                    attributes = user['attributes']
                    profile = attributes['profile']
                    first_name = (profile.get("firstName") or "").title()
                    last_name = (profile.get("lastName") or "").title()
                    contact_name = f"{first_name} {last_name}".strip()
                    email = attributes['email']
                    public_data = profile['publicData']
                    favorites = profile['privateData'].get('favorites', [])
                    favorites = list(set(favorites))  # Remove duplicates if any
                    favorites_model = self.env['npc.favorites']
                    existing_favorites = favorites_model.search([('name', 'in', favorites)])
                    existing_names = set(existing_favorites.mapped('name'))
                    new_names = set(favorites) - existing_names
                    new_favorites = favorites_model.create([{'name': name} for name in new_names]) if new_names else favorites_model
                    favorites_ids = [(4, fav.id) for fav in (existing_favorites | new_favorites) if fav.id and isinstance(fav.display_name, str)]
                    calendly_data = profile['privateData'].get('calendlyInitializations', {})
                    tag_id = self.env.ref('npc_sharetribe.crm_tag_user', raise_if_not_found=False)
                    team_id = self.env.ref('sales_team.team_sales_department', raise_if_not_found=False)
                    user_type = public_data.get('userType')
                    practice_state_id = self.env['res.country.state'].search([
                        ('code', '=', public_data.get('pub_State') or public_data.get('state')),
                        ('country_id', '=', self.env.ref('base.us').id)
                    ], limit=1)
                    practice_type_ids = self.env['npc_crm.practice_type'].search(
                        [('name', 'in',
                          public_data.get('pub_practice_types', []) or public_data.get('practice_types', []))])
                    try:
                        reg_date = datetime.datetime.fromisoformat(attributes['createdAt'])
                    except ValueError:
                        reg_date = datetime.datetime.strptime(attributes['createdAt'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    work_histories = public_data.get('pub_workHistory') or public_data.get('workHistory')
                    
                    invalid_favorites = (existing_favorites | new_favorites).filtered(lambda f: not f.id or not isinstance(f.display_name, str))
                    if invalid_favorites:
                        _logger.warning(f"Invalid favorite(s) found: {[f.id for f in invalid_favorites]}")

                    lead_data = {
                        'sharetribe_id': sharetribe_id,
                        'name': f"{contact_name or email}",
                        'contact_name': contact_name,
                        'custom_first_name': first_name,
                        'custom_last_name': last_name,
                        'email_from': email,
                        'phone': public_data.get('phone'),
                        'npc_user_type': user_type in ('APP', 'PHYS') and user_type,
                        'has_linkedin': public_data.get('pub_hasLinkedin') == "yes" or public_data.get(
                            'hasLinkedin') == "yes",
                        'linkedin_url': public_data.get('pub_linkedinUrl') or public_data.get('linkedinUrl'),
                        'summary': profile.get('bio'),
                        'license_type': public_data.get('pub_License') or public_data.get('License'),
                        'npi_number': public_data.get('NPI'),
                        'controlled_substances': public_data.get(
                            'pub_controlled_substances') == "yes" or public_data.get('controlled_substances') == "yes",
                        'practice_type_ids': [(6, 0, practice_type_ids.ids)],
                        'years_experience': public_data.get('pub_yearsExperience') or public_data.get(
                            'yearsExperience'),
                        'availability_start': public_data.get('start_date'),
                        'availability_start_pub': public_data.get('pub_start_date'),
                        'reg_date': reg_date.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT),
                        'custom_user_referral': public_data.get('referral', {}).get('ref'),
                        'work_history_ids': work_histories and [(0, 0, {
                            'name': wh.get('title'),
                            'company': wh.get('company'),
                            'location': wh.get('location'),
                            'year_end': wh.get('endYear'),
                            'month_end': wh.get('endMonth'),
                            'year_start': wh.get('startYear'),
                            'month_start': wh.get('startMonth'),
                            'is_current': wh.get('isCurrent'),
                            'description': wh.get('description'),
                        }) for wh in work_histories],
                        'favorites_ids': favorites_ids,
                    }
                    if calendly_data:
                        calendly_data = next(iter(calendly_data.values()), None)
                        lead_data.update({
                            'calendlyintialisation': json.dumps(calendly_data),
                            'calendlyintialisation_url': urljoin("https://app.npcollaborator.com/",calendly_data.get('path', '')),
                            'calendlyintialisation_date': datetime.datetime.strptime(calendly_data.get('initializedAt'), '%Y-%m-%dT%H:%M:%S.%fZ')
                        })
                    if tag_id:
                        lead_data['tag_ids'] = [(4, tag_id.id)]
                    if practice_state_id:
                        lead_data['practice_state_ids'] = [(4, practice_state_id.id)]
                    if not lead_id:
                        if team_id and user_type != 'PHYS':
                            lead_data['team_id'] = team_id.id
                            lead_data['user_id'] = team_id.user_id.id
                        lead_id = crm_model.with_context(mail_auto_subscribe_no_notify=True).create([{
                            'type': 'lead',
                            **lead_data
                        }])
                        # Make the members of the team as followers
                        lead_id.message_subscribe(team_id.member_ids.mapped('partner_id').ids)
                    else:
                        if lead_data.get('favorites_ids'):
                            lead_id.write({'favorites_ids': lead_data['favorites_ids']})
                        if lead_data.get('calendlyintialisation'):
                            lead_id.write({
                                'calendlyintialisation': lead_data['calendlyintialisation'],
                                'calendlyintialisation_url': lead_data['calendlyintialisation_url'],
                                'calendlyintialisation_date': lead_data['calendlyintialisation_date'],
                            })

            if data.get('meta'):
                total_pages = data['meta']['totalPages']
                if total_pages > 1 and page < total_pages:
                    get_users(page + 1)

        get_users()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': 'success',
                'sticky': False,
            },
        }
