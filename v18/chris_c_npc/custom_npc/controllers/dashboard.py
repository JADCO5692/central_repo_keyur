# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, route 
from collections import defaultdict
from datetime import date
import calendar
from odoo.tools.translate import _

class SalesDashboard(http.Controller):
    @route('/sales/data', type='json', auth="user", website=True)
    def dashboard_sales_data(self, params={}):  
        npc_data = self.get_cumulative_npc_data()
        return {
            'npc_data':npc_data,  
        }
    
    def get_cumulative_npc_data(self):
        SaleCommissionLogs = request.env['sale.commission.logs']
        logs = SaleCommissionLogs.search([])

        if not logs:
            return {"labels": [], "values": []}

        # find last invoice_date_due
        last_date = max(log.invoice_date_due for log in logs if log.invoice_date_due)

        # build 12-month window (last_date - 11 months → last_date)
        year, month = last_date.year, last_date.month
        start_year = year if month > 11 else year - 1
        start_month = ((month - 11 - 1) % 12) + 1
        start_year = year if month > 11 else year - 1

        months_range = []
        y, m = start_year, start_month
        for _ in range(12):
            months_range.append(f"{y}-{m:02d}")
            m += 1
            if m > 12:
                m = 1
                y += 1

        # group npc_fee by month-year
        month_map = defaultdict(float)
        for log in logs:
            if log.order_name and log.invoice_date_due:
                month_key = log.invoice_date_due.strftime("%Y-%m")
                if month_key in months_range:
                    month_map[month_key] += log.npc_fee

        # prepare values
        values = []
        labels = []
        cumulative_total = 0
        today_key = date.today().strftime("%Y-%m")

        for m in months_range:
            month_name = calendar.month_abbr[int(m.split("-")[1])] + " " + m.split("-")[0]
            labels.append(month_name)

            if m < today_key:
                # past months → take actual only
                values.append(month_map[m])
            else:
                # future months (including current) → cumulative projection
                cumulative_total += month_map[m]
                values.append(cumulative_total)

        return {
            "labels": labels,
            "values": values,
        }
 