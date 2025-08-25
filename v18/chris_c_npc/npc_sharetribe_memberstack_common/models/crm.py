from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    merged = fields.Boolean("Merged")

    @api.model
    def sync_sharetribe_memberstack(self):
        sharetribe_sync_model = self.env['npc_sharetribe.sync']
        memberstack_sync_model = self.env['npc_memberstack.sync']
        st_tag_id = self.env.ref('npc_sharetribe.crm_tag_user')

        _logger.info("Share tribe sync")
        sharetribe_sync_model.import_users_to_crm()
        _logger.info("memberstack sync")
        memberstack_sync_model.import_members_to_crm()
        _logger.info("memberstack sync - end")

        # Merge PHYS user type records
        st_lead_ids = self.search([
            ('npc_user_type', '=', 'PHYS'),
            ('npi_number', '!=', False),
            ('merged', '=', False),
            ('tag_ids', 'in', [st_tag_id.id])
        ])
        _logger.info("Find Physicians from Sharetribe")
        for st_lead_id in st_lead_ids:
            ms_lead_id = self.with_context(active_test=False).search([
                ('npc_user_type', '=', 'PHYS'),
                ('npi_number', '=', st_lead_id.npi_number),
                ('tag_ids', 'in', [self.env.ref('npc_memberstack.crm_tag_member').id]),
            ])
            if ms_lead_id:
                _logger.info("Member stack lead found - Start")
                _logger.info(ms_lead_id)
                _logger.info("Member stack lead found - End")
                # Copy sharetribe fields to memberstack lead
                vals_to_copy = {
                    'merged': True,
                    'sharetribe_id': st_lead_id.sharetribe_id,
                    'summary': st_lead_id.summary,
                    'license_type': st_lead_id.license_type,
                    'years_experience': st_lead_id.years_experience,
                    'availability_start': st_lead_id.availability_start,
                    'availability_start_pub': st_lead_id.availability_start_pub,
                    'has_linkedin': st_lead_id.has_linkedin,
                    'linkedin_url': st_lead_id.linkedin_url,
                }
                if st_lead_id.practice_state_ids:
                    _logger.info("practice_state_ids found - Start")
                    _logger.info(st_lead_id.practice_state_ids)
                    _logger.info("practice_state_ids found - End")
                    safe_states = st_lead_id.practice_state_ids.filtered(lambda s: isinstance(s.display_name, str))
                    vals_to_copy['practice_state_ids'] = [(4, ps.id) for ps in safe_states]
                
                if st_lead_id.tag_ids:
                    _logger.info("st_lead_id.tag_ids found - Start")
                    _logger.info(st_lead_id.tag_ids)
                    _logger.info("st_lead_id.tag_ids found - End")
                    safe_tags = st_lead_id.tag_ids.filtered(lambda t: isinstance(t.display_name, str))
                    vals_to_copy['tag_ids'] = [(4, t.id) for t in safe_tags]
                    
                invalid_states = st_lead_id.practice_state_ids.filtered(lambda s: not isinstance(s.display_name, str))
                if invalid_states:
                    _logger.warning(f"Invalid states on lead {st_lead_id.id}: {[s.id for s in invalid_states]}")
                
                invalid_tags = st_lead_id.tag_ids.filtered(lambda t: not isinstance(t.display_name, str))
                if invalid_tags:
                    _logger.warning(f"Invalid tags on lead {st_lead_id.id}: {[t.id for t in invalid_tags]}")


                ms_lead_id.write(vals_to_copy)
                for wh_id in st_lead_id.work_history_ids:
                    wh_id.lead_id = ms_lead_id
                # Delete sharetribe record after merging with matching memberstack record
                st_lead_id.unlink()
                
                lead_message = ', '.join(map(str, ms_lead_id.mapped('id'))) if ms_lead_id else ""
                _logger.warning(f"Merged ShareTribe record with Memberstack record with ID {lead_message}")
        _logger.info("Job ended")
