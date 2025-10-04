from datetime import datetime
from odoo import models, fields, api, _
from collections import defaultdict

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    np_partner_id = fields.Many2one('res.partner','NP Partner')
    tickets_count = fields.Integer(compute='_compute_tickets_count', default=0, string="Tickets")

    @api.onchange('user_id')
    def _onchange_user_id(self):
        for rec in self:
            rec.partner_id.user_id = self.user_id


    def _compute_tickets_count(self):
        request_model = self.env['helpdesk.ticket'] 
        partner_ids = set(self.mapped('partner_id').ids + self.mapped('np_partner_id').ids) 
        tickets_data = request_model.sudo()._read_group([('partner_id', 'in', list(partner_ids))],['partner_id'],['__count']) 
        tickets_data_mapped = {partner.id: count for partner, count in tickets_data}
 
        for lead in self:
            lead.tickets_count = (tickets_data_mapped.get(lead.partner_id.id, 0) +tickets_data_mapped.get(lead.np_partner_id.id, 0))
    
    def open_tickets(self):
        self.ensure_one() 
        partner_ids = []
        if self.partner_id:
            partner_ids.append(self.partner_id.id)
        if self.np_partner_id:
            partner_ids.append(self.np_partner_id.id) 
        tickets = self.env['helpdesk.ticket'].search([('partner_id', 'in', partner_ids)])

        return {
            'type': 'ir.actions.act_window',
            'name': _('Helpdesk Tickets'),
            'view_mode': 'list,kanban,form',
            'res_model': 'helpdesk.ticket',
            'domain': [('id', 'in', tickets.ids)],
            'context': {
                'default_partner_id': self.partner_id.id or self.np_partner_id.id,
            },
        }
    
    def get_lead_assigned(self, date_domain): 
        domain = [
            ('field_id.name', '=', 'user_id'),
            ('new_value_integer', '!=', False)
        ] + date_domain

        tracking_vals = self.env['mail.tracking.value'].sudo().search(domain) 

        result = {}       # counts
        record_ids = {}   # lead IDs per salesperson
        rids = []
        for val in tracking_vals:
            salesperson_id = val.new_value_integer
            lead_id = val.mail_message_id.res_id
            print(lead_id)
            leadobj = self.search([('id','=',lead_id)],limit=1)
            if len(leadobj) and lead_id not in rids: 
                if salesperson_id:
                    # Count
                    result.setdefault(salesperson_id, 0)
                    result[salesperson_id] += 1

                    # Record IDs
                    record_ids.setdefault(salesperson_id, [])
                    record_ids[salesperson_id].append(lead_id)
                    rids.append(lead_id)

        # Add salesperson names
        salespersons = self.env['res.users'].browse(result.keys())
        final_counts = {sp.name: result[sp.id] for sp in salespersons}
        final_records = {sp.name: record_ids.get(sp.id, []) for sp in salespersons}

        return {
            "counts": final_counts,
            "record_ids": final_records,
        }


    def get_won_leads_by_date(self, date_domain):
        Tracking = self.env['mail.tracking.value']
        LeadStage = self.env['crm.stage'] 
        # Get all "won" stage names
        won_stages = LeadStage.search([('is_won', '=', True)]).mapped('name')

        # Find leads that were moved into a "won" stage in given range
        records = Tracking.sudo().search([
            ('field_id.model', '=', 'crm.lead'),
            ('field_id.name', '=', 'stage_id'),
            ('new_value_char', 'in', won_stages)]+date_domain)
         
        result = {}
        for rec in records:
            lead = rec.mail_message_id.record_ref
            if lead.npc_user_type != 'APP':
                continue
            if lead and lead.user_id:
                result.setdefault(lead.user_id.name, 0)
                result[lead.user_id.name] += 1 
        return result

    def get_stage_durations(self, domain=None):
        domain = domain or []

        # Preload stage IDs
        pr_reg_stage = self.env['crm.stage'].search([('name', '=', 'Partner Referral - Registered')], limit=1)
        reg_stage = self.env['crm.stage'].search([('name', '=', 'Registered')], limit=1)
        zoom_stage = self.env['crm.stage'].search([('name', '=', 'Scheduled zoom call')], limit=1)
        meet_stage = self.env['crm.stage'].search([('name', '=', 'Matched with physician')], limit=1)

        stage_map = {
            zoom_stage.id: "zoom",
            meet_stage.id: "meet",
        }

        results = defaultdict(lambda: {"zoom_durations": [], "meet_durations": []})

        # Query mail.tracking.value directly instead of looping mail.message
        trackings = self.env["mail.tracking.value"].sudo().search(
            [("field_id.name", "=", "stage_id"), ("mail_message_id.model", "=", "crm.lead")] + domain,
            order="create_date asc"
        )

        # Group trackings by lead for faster processing
        leads_map = defaultdict(list)
        for tr in trackings:
            leads_map[tr.mail_message_id.res_id].append(tr)

        # Process each lead once
        for lead_id, tracks in leads_map.items():
            lead = self.env['crm.lead'].browse(lead_id)
            if lead and lead.npc_user_type != 'APP':
                continue
            if not lead or not lead.user_id:
                continue

            salesperson = lead.user_id.name
            pr_reg_time,reg_time = None,None
            zoom_time, meet_time = None, None

            for tr in tracks:
                if tr.new_value_integer == reg_stage.id:
                    reg_time = tr.create_date
                if tr.new_value_integer == pr_reg_stage.id:
                    pr_reg_time = tr.create_date
                
                if tr.new_value_integer == zoom_stage.id and not zoom_time:
                    zoom_time = tr.create_date
                elif tr.new_value_integer == meet_stage.id and not meet_time:
                    meet_time = tr.create_date
            
            if reg_time and pr_reg_time:
                # if register and partner ref register found
                reg_time = reg_time + (pr_reg_time - reg_time) / 2
            elif pr_reg_time:
                # if only partner ref register found
                # assume lead creats as registered date
                reg_time = lead.create_date + (pr_reg_time - lead.create_date) / 2
            else:
                # if both tracking not found 
                reg_time = lead.create_date

            if reg_time and zoom_time:
                diff_days = (zoom_time - reg_time).total_seconds() / 86400
                results[salesperson]["zoom_durations"].append(diff_days) 
            if zoom_time and meet_time:
                diff_days = (meet_time - zoom_time).total_seconds() / 86400
                results[salesperson]["meet_durations"].append(diff_days)

        # Final aggregation
        final_data = {}
        for salesperson, vals in results.items():
            final_data[salesperson] = {
                "avg_zoom_days": round(sum(vals["zoom_durations"]) / len(vals["zoom_durations"]), 2) if vals["zoom_durations"] else 0,
                "avg_meet_days": round(sum(vals["meet_durations"]) / len(vals["meet_durations"]), 2) if vals["meet_durations"] else 0,
            }

        return final_data