from odoo import http, fields,_
from odoo.http import request, route
from odoo.addons.portal.controllers.portal import CustomerPortal 
from dateutil.relativedelta import relativedelta
from odoo.tools import date_utils
from odoo.osv.expression import AND

class CustomerPortalCustom(CustomerPortal):
    @route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw): 
        values = super().home(**kw) 
        request.env.registry.clear_cache()
        return values

    def get_active_subscription(self):
        partner = request.env.user.partner_id
        Order = request.env['sale.order']
        domain = [
            ('partner_id', 'in', [partner.id, partner.commercial_partner_id.id]),
            ('subscription_state', 'in', ['3_progress']),
            ('is_subscription', '=', True),
            ('plan_id', '!=', False)
        ]
        subscriptions = Order.sudo().search(domain)
        if len(subscriptions):
            return subscriptions
        return {}

    @route(['/my/attendances'], type='http',auth="user", website=True)
    def my_attendances(self, **kw):
        params = request.params
        domain = [] 
        today = fields.Date.today()
        quarter_start, quarter_end = date_utils.get_quarter(today)
        last_quarter_date = date_utils.subtract(quarter_start, weeks=1)
        last_quarter_start, last_quarter_end = date_utils.get_quarter(last_quarter_date)
        last_week = today + relativedelta(weeks=-1)
        last_month = today + relativedelta(months=-1)
        last_year = today + relativedelta(years=-1)

        searchbar_filters = {
            # 'all': {'label': _('All'), 'domain': []},
            'month': {'label': _('This Month'), 'domain': [('check_in', '>=', date_utils.start_of(today, 'month')), ('check_in', '<=', date_utils.end_of(today, 'month'))]},
            'last_month': {'label': _('Last Month'), 'domain': [('check_in', '>=', date_utils.start_of(last_month, 'month')), ('check_in', '<=', date_utils.end_of(last_month, 'month'))]},
            'week': {'label': _('This Week'), 'domain': [('check_in', '>=', date_utils.start_of(today, "week")), ('check_in', '<=', date_utils.end_of(today, 'week'))]},
            'last_week': {'label': _('Last Week'), 'domain': [('check_in', '>=', date_utils.start_of(last_week, "week")), ('check_in', '<=', date_utils.end_of(last_week, 'week'))]},
            # 'last_year': {'label': _('Last Year'), 'domain': [('check_in', '>=', date_utils.start_of(last_year, 'year')), ('check_in', '<=', date_utils.end_of(last_year, 'year'))]},
            # 'last_quarter': {'label': _('Last Quarter'), 'domain': [('check_in', '>=', last_quarter_start), ('check_in', '<=', last_quarter_end)]},
            # 'today': {'label': _('Today'), 'domain': [("date", "=", today)]},
            # 'quarter': {'label': _('This Quarter'), 'domain': [('check_in', '>=', quarter_start), ('check_in', '<=', quarter_end)]},
            # 'year': {'label': _('This Year'), 'domain': [('check_in', '>=', date_utils.start_of(today, 'year')), ('check_in', '<=', date_utils.end_of(today, 'year'))]},
            'custom': {'label': _('Custom'), 'domain': []},
        }
        hr_attendence = request.env['hr.attendance'].sudo()
        emp = request.env.user.partner_id.employee_ids[0] if request.env.user.partner_id.employee_ids else False
        if not emp:
            return request.render('website.page_404')
        filterby = params.get('filterby') 
        if not filterby:
            filterby = 'month'
        if filterby == 'custom':
            domain = self.get_date_domain(params)
        else:
            domain = AND([domain, searchbar_filters[filterby]['domain']])
        domain += [('employee_id','=',emp.id)]
        attendances = hr_attendence.search(domain)
        return  request.render('custom_boxesofhouston.my_attendances_view',{
            'searchbar_filters':searchbar_filters,
            'attendances':attendances,
            'default_url': '/my/attendances',
            'coast':emp.hourly_cost,
            'filterby': filterby,
            'employee':emp,
            'sdate':params.get('sdate',''),
            'edate':params.get('edate',''),
        })  
    
    def get_date_domain(self, params):
        domain = []
        sdate = params.get('sdate')
        edate = params.get('edate')
        if params.get('filterby') == 'custom' and sdate and edate:
            start = fields.Date.to_date(sdate)
            end = fields.Date.to_date(edate)
            domain.append(('check_in', '>=', start))
            domain.append(('check_in', '<=', end))
        
        return domain
      
