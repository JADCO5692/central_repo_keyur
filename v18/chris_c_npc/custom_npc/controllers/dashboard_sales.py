# -*- coding: utf-8 -*-
from odoo import http, fields,_
from odoo.http import request, route 
from datetime import date ,datetime, timedelta
from collections import defaultdict
from . import date_util as du 
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

class NpsDashboard(http.Controller):
    @route('/np/sales/data', type='json', auth="user", website=True)
    def dashboard_sales_data(self, params={}):  
        new_onboarded_cust = self.get_np_sined_contract(params)
        sales_p = request.env['res.users'].search([
            ('groups_id', 'in', request.env.ref('sales_team.group_sale_salesman').id)
        ]).mapped('name')
        return {
            'new_leads_assigned':new_onboarded_cust,
            'signed_contract':self.get_signed_contracts_report(params),
            'stage_durations':self.get_speed_ti_interview(params),
            'activity_complete_avg':self.get_avg_completion_time(params),
            'contract_signed_not_cnl':self.get_contract_signed_not_cnl(params),
            'salespersons':sales_p
        }

    def get_speed_ti_interview(self, params): 
        date_domain = self.prepare_date_domain('create_date', params)
        vals = request.env['crm.lead'].sudo().get_stage_durations(date_domain) 
        return vals 
    
    def get_np_sined_contract(self, params):
        lead_obj = request.env['crm.lead'] 
        date_domain = self.prepare_date_domain('create_date', params)
        vals = lead_obj.get_lead_assigned(date_domain)
        return vals
    
    def get_signed_contracts_report(self,params):
        Model = request.env['sale.order'].sudo()
        date_domain = self.prepare_date_domain('create_date', params)
        # build domain
        domain = [('state','in',['sale']),('subscription_state','=','3_progress')] + date_domain
         
        # 1) Total per salesperson (fast via read_group)
        totals = {}
        record_ids = defaultdict(list)
        try:
            grp_totals = Model.read_group(domain, fields=['user_id'], groupby=['user_id'], lazy=False)
        except Exception:
            grp_totals = []
        for rec in grp_totals:
            user_val = rec.get('user_id')
            name = user_val[1] if user_val else 'Unassigned'
            count = rec.get("user_id_count") or rec.get("__count") or 0
            totals[name] = count

        matching_orders = Model.search(domain)
        for order in matching_orders:
            salesrep = order.user_id.name or "Unassigned"
            record_ids[salesrep].append(order.id)
        # 2) Monthly per salesperson
        monthly = defaultdict(dict)  # { salesperson_name: { 'YYYY-MM': count } }
        # group by user + month of date_field
        try:
            grp_monthly = Model.read_group(domain,
                                          fields=['user_id', 'create_date'],
                                          groupby=['user_id', f"{'create_date'}:month"],
                                          lazy=False)
        except Exception:
            grp_monthly = []

        for rec in grp_monthly:
            user_val = rec.get('user_id')
            name = user_val[1] if user_val else 'Unassigned'
            month_key = rec.get(f"{'create_date'}:month")  # e.g. '2025-08'
            count = rec.get(f"{'user_id'}_count") or rec.get("__count") or 0
            if month_key:
                monthly[name][month_key] = monthly[name].get(month_key, 0) + count

        return {
            'total_per_rep': totals, 
            'record_ids': dict(record_ids),
        }
    
    def get_won_leads(self,params):
        lead_obj = request.env['crm.lead']
        date_domain = self.prepare_date_domain('create_date', params)
        vals = lead_obj.get_won_leads_by_date(date_domain)
        return vals
    
    def get_sales_conversion_report(self):
        result = {
            'total_per_rep': {},
            'monthly_per_rep': {}
        }

        # Total won per rep
        won_leads = self.env['crm.lead'].read_group(
            domain=[('stage_id.is_won', '=', True)],
            fields=['user_id'],
            groupby=['user_id']
        )
        for rec in won_leads:
            result['total_per_rep'][rec['user_id'][1]] = rec['user_id_count']

        # Monthly won per rep
        monthly = self.env['crm.lead'].read_group(
            domain=[('stage_id.is_won', '=', True), ('date_closed', '!=', False)],
            fields=['user_id', 'date_closed'],
            groupby=['user_id', 'date_closed:month']
        )
        for rec in monthly:
            rep = rec['user_id'][1] if rec['user_id'] else 'Unassigned'
            month = rec['date_closed:month']
            result['monthly_per_rep'].setdefault(rep, {})[month] = rec['__count']

        return result


    def get_avg_completion_time(self, params):
        zoom_stage = request.env['crm.stage'].search([('name', '=', 'Scheduled zoom call')], limit=1)
        date_domain = self.prepare_date_domain('create_date', params)

        completed_activities = request.env['mail.message'].search([
            ('model', '=', 'crm.lead'),
            ('subtype_id', '=', request.env.ref('mail.mt_activities').id)
        ] + date_domain)

        salesperson_wise = {}

        for act in completed_activities:
            lead = act.record_ref
            salesrep = lead.user_id

            # tracking for stage changes
            trackings = request.env["mail.tracking.value"].sudo().search(
                [
                    ("field_id.name", "=", "stage_id"),
                    ("mail_message_id.model", "=", "crm.lead"),
                    ("mail_message_id.res_id", "=", lead.id),
                ] + date_domain,
                order="create_date asc",
            )

            # filter only zoom stage changes
            zoom_trackings = trackings.filtered(lambda a: a.new_value_integer == zoom_stage.id)

            if zoom_trackings:
                last_zoom_tracking = zoom_trackings.sorted(lambda r: r.create_date)[-1]

                if last_zoom_tracking and last_zoom_tracking.create_date > act.create_date:
                    if salesrep.name not in salesperson_wise:
                        salesperson_wise[salesrep.name] = {
                            'count': 0,
                            'ids':[]
                        }

                    salesperson_wise[salesrep.name]['count'] += 1
                    salesperson_wise[salesrep.name]['ids'] += [act.id]

        return salesperson_wise

    
    def get_contract_signed_not_cnl(self, params):
        """
        Get leads with signed contracts (not cancelled) and count them by salesperson.
        """
        crm_lead_obj = request.env['crm.lead'].sudo()
        
        # Prepare the date domain for filtering
        date_domain = self.prepare_date_domain('custom_all_contracts_signed2', params)
        
        # Search leads with non-false custom_all_contracts_signed2 and date domain
        leads = crm_lead_obj.search([('custom_all_contracts_signed2', '!=', False)] + date_domain)
        
        # Filter leads where no order has subscription_state == '6_churn'
        lead_ids = [
            ld.id for ld in leads
            if not any(order.subscription_state == '6_churn' for order in ld.order_ids)
        ]
        
        # Group leads by salesperson (user_id) and count them
        salesperson_counts = {}
        for lead in leads:
            if lead.id in lead_ids:  # Only count leads that passed the filter
                salesperson = lead.user_id
                if salesperson:  # Ensure salesperson exists 
                    salesperson_counts[salesperson.name] = salesperson_counts.get(salesperson.name, 0) + 1
                else:
                    # Handle leads with no salesperson (optional)
                    salesperson_counts['no_salesperson'] = salesperson_counts.get('no_salesperson', 0) + 1
         
        
        return {
            'lead_ids': lead_ids,
            'lead_counts': len(lead_ids),
            'salesperson_counts': salesperson_counts
        }
    
    def prepare_date_domain(self,date_field,params): 
        time_frame = params.get('time_frame')
        if time_frame == 'custom':
            start_date = params.get('start_date')
            end_date = params.get('end_date')
            cst_dates_domain = self.get_cst_dates(date_field,start_date,end_date)
            return cst_dates_domain
        domain = [] 
        start_date = ''
        end_date = ''
        today = date.today()
        if time_frame: 
            if time_frame == "next_week":
                start_date, end_date = du.next_week_dates(today)
            elif time_frame == "next_month":
                start_date, end_date = du.next_month_dates(today) 
            elif time_frame == "this_week":
                start_date, end_date = du.current_week_dates(today)
            elif time_frame == "this_month":
                start_date, end_date = du.current_month_dates(today)
            elif time_frame == "this_year":
                start_date, end_date = du.current_year_dates(today) 
            elif time_frame == "last_week":
                start_date, end_date = du.past_week_dates(today)
            elif time_frame == "last_month":
                start_date, end_date = du.past_month_dates(today)  

            if start_date:
                if start_date == end_date:
                    end_date = start_date + timedelta(days=1)
                self.start_date = start_date
                domain.append((date_field,">=",fields.datetime.strftime(start_date, DEFAULT_SERVER_DATETIME_FORMAT),))

            if end_date:
                domain.append((date_field,"<",fields.datetime.strftime(end_date, DEFAULT_SERVER_DATETIME_FORMAT),))
        return domain
    
    def get_cst_dates(self, date_field, start_date, end_date):
        domain = []
        if start_date: 
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            domain.append((date_field, ">=", start))
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            domain.append((date_field, "<=", end))
        return domain