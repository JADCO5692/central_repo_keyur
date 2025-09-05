# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, route
from odoo.tools import lazy
from odoo.osv import expression
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute
from odoo.addons.portal.controllers.portal import pager
from . import date_util as du
from datetime import date ,datetime, timedelta

from werkzeug.exceptions import NotFound 
from odoo import fields 
from odoo.tools import float_round, groupby, SQL
from odoo.tools.translate import _
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

class SalesDashboard(http.Controller):
    @route('/sales/data', type='json', auth="user", website=True)
    def dashboard_sales_data(self, params={}):
        # product_obj = request.env['product.template'].sudo()
        # website = request.env['website'].get_current_website()  
        new_onboarded_cust = self.get_new_customers_data(params.get('time_frame')) 
        salesperson_summary = self.get_salesperson_summary(params.get('time_frame'))
        return {
            'salesperson_summary':salesperson_summary, 
            'new_onboard_customers':new_onboarded_cust, 
            'total_sales_for_new_leads':[],
        } 
    
    def get_salesperson_summary(self, time_frame):
        order_obj = request.env['sale.order']
        #  Leads 
        date_domain = self.prepare_date_domain('create_date', time_frame)
        leads_data = request.env['crm.lead'].read_group(
            domain=date_domain,
            fields=['id'],
            groupby=['user_id'],
        )

        leads_dict = {}
        for rec in leads_data:
            sp = rec['user_id'][1] if rec.get('user_id') else 'Unassigned'
            leads_dict[sp] = rec['user_id_count']

         # Fetch partner_ids from leads in this time frame
        leads = request.env['crm.lead'].search(date_domain)
        lead_partner_map = {l.id: l.partner_id.id for l in leads if l.partner_id}

        new_customer_ids = set(lead_partner_map.values())
        #  Sales 
        domain_sales = [('user_id','!=',False),('state', 'in', ['sale'])]
        if date_domain:
            domain_sales += date_domain

        sales_data = order_obj.read_group(
            domain=domain_sales,
            fields=['amount_total:sum'],
            groupby=['user_id'],
        )

        sales_dict = {}
        for rec in sales_data:
            sp = rec['user_id'][1] if rec.get('user_id') else 'Unassigned'
            sales_dict[sp] = rec['amount_total']

        #  Sales from *new leads customers*
        new_leads_sales_data = order_obj.read_group(
            domain = domain_sales + [('partner_id', 'in', list(new_customer_ids))],
            fields = ['amount_total:sum'],
            groupby=['user_id'],
        )

        new_leads_sales_dict = {}
        for rec in new_leads_sales_data:
            sp = rec['user_id'][1] if rec.get('user_id') else 'Unassigned'
            new_leads_sales_dict[sp] = rec['amount_total']

        #  Quotations 
        orders = order_obj.get_orders_sent(date_domain)
        domain_quo = [('id','in',orders.ids),('user_id','!=',False)]
        if date_domain:
            domain_quo += date_domain
        

        quo_data = order_obj.read_group(
            domain=domain_quo,
            fields=['id'],
            groupby=['user_id'],
        )

        quo_dict = {}
        for rec in quo_data:
            sp = rec['user_id'][1] if rec.get('user_id') else 'Unassigned'
            quo_dict[sp] = rec['user_id_count']

        #  Merge dict 
        all_salespersons = set(leads_dict.keys()) | set(sales_dict.keys()) | set(quo_dict.keys())
        results = []
        for sp in all_salespersons:
            results.append({
                'salesperson': sp,
                'new_leads': leads_dict.get(sp, 0),
                'sales_amount': sales_dict.get(sp, 0.0),
                'new_leads_sales_amount': new_leads_sales_dict.get(sp, 0.0),
                'quotations_sent': quo_dict.get(sp, 0),
            })
        results = sorted(results,key=lambda x: x['sales_amount'],reverse=True)
        return results

    def get_new_customers_data(self, time_frame):
        date_domain = self.prepare_date_domain('create_date',time_frame) 
        domain = [('user_id','!=',False),('state', 'in', ['sale'])]
        if date_domain:
            domain += date_domain 

        SaleOrder = request.env['sale.order']
 
        orders = SaleOrder.search(domain, order="date_order asc")

        first_orders = {}
        for order in orders: 
            customer_id = order.partner_id.id
            old_order = SaleOrder.search([('id','!=',order.id),('partner_id','=',customer_id),('user_id','!=',False),('state', 'in', ['sale'])],limit="1")
            if not old_order and customer_id not in first_orders:
                first_orders[customer_id] = order
 
        results = {}
        new_customer_ids = []
        for order in first_orders.values():
            salesperson = order.user_id.name or "Unassigned"
            if salesperson not in results:
                results[salesperson] = {
                    'new_customers': 0,
                    'new_customer_sales_amount': 0.0,
                    'new_customer_ids':[]
                } 
            results[salesperson]['new_customers'] += 1
            results[salesperson]['new_customer_ids'].append(order.partner_id.id)
            results[salesperson]['new_customer_sales_amount'] += order.amount_total
 
        res = [{'salesperson': sp,
                'new_customers': vals['new_customers'],
                'new_customer_sales_amount': vals['new_customer_sales_amount'],
                'new_customer_ids':vals['new_customer_ids']
                }for sp, vals in results.items()] 
        return res

    def prepare_date_domain(self,date_field="create_date",time_frame='this_month'): 
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
    
    