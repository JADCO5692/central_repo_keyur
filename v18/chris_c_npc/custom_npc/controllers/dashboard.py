# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, route 
from collections import defaultdict
from datetime import date, datetime
import calendar
from odoo.tools.translate import _

class SalesDashboard(http.Controller):
    @route('/sales/data', type='json', auth="user", website=True)
    def dashboard_sales_data(self, params={}):  
        npc_data = self.get_cumulative_npc_data()
        return {
            'npc_data':npc_data,  
        }
    
    def get_draft_invoide_data(self, month):
        """
        Get total NPC amount for all draft invoices in a given month (YYYY-MM).
        """
        vals = {}
        # Parse month into start & end dates
        start_date = datetime.strptime(month, "%Y-%m").date()
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1, day=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1, day=1)

        # Fetch invoices for given month
        invoices = request.env['account.move'].search([
            ('payment_state', 'in', ['paid', 'in_payment', 'not_paid', 'partial']),
            ('move_type', '=', 'out_invoice'),
            ('commission_id', '=', False),
            ('is_commission_excluded', '=', False),
            ('state', '=', 'draft'),
            ('invoice_date_due', '>=', start_date),
            ('invoice_date_due', '<', end_date),
        ])

        # Calculate total NPC fees for the month
        total_npc = 0.0
        total_npc_100 = 0.0
        for invoice in invoices:
            total_npc += sum(
                line.price_subtotal
                for line in invoice.invoice_line_ids
                if line.product_id.is_np_fees_product
            )
            npc_line = invoice.invoice_line_ids.filtered(lambda a:a.product_id.is_np_fees_product)
            npc_fees = sum(l.price_subtotal for l in npc_line) if npc_line else 0.0
            prorate = self._compute_invoice_prorate(invoice) 
            if prorate != 100:
                total_npc_100 += npc_fees *100 / prorate
            else:
                total_npc_100 += npc_fees

        return {
            'total_npc':total_npc,
            'total_npc_100':total_npc_100,
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
        each_log_pp = defaultdict(list) 
        for log in logs: 
            if log.order_name and log.invoice_date_due:
                month_key = log.invoice_date_due.strftime("%Y-%m") 
                if month_key in months_range: 
                    month_map[month_key] += log.npc_fee 
                    pp = 0
                    if log.prorate_percentage: 
                        pp = log.prorate_percentage*100 
                    each_log_pp[month_key].append(round(pp)) 
        # prepare values
        values = []
        labels = []
        cumulative_total = 0
        today_key = date.today().strftime("%Y-%m")

        for m in months_range:
            # ===
            draft_invoice_total = self.get_draft_invoide_data(m) 
            # ===
            month_each_pp = each_log_pp[m]
            average_pp = sum(month_each_pp) / len(month_each_pp)
            total_moth_npc = month_map[m]
            total_moth_npc_as_pp = total_moth_npc *100 /round(average_pp)
            print(f"====={m}======")
            print(f"total npc fees excl. prorate {total_moth_npc}")
            print(f"total npc fees incl. prorate {total_moth_npc_as_pp} on prorate {round(average_pp)}%")
            print(f"draft invoice total excl. prorate : {draft_invoice_total.get('total_npc')}")
            print(f"draft invoice total incl. prorate : {draft_invoice_total.get('total_npc_100')}")
            
            month_name = calendar.month_abbr[int(m.split("-")[1])] + " " + m.split("-")[0]
            labels.append(month_name)
            temp_chart_value = 0 #this var is for log 
            if m < today_key:
                # past months → take actual only
                values.append(month_map[m])
                temp_chart_value = month_map[m]
            else:
                # future months (including current) → cumulative projection
                # total_cumulative = total_moth_npc_as_pp
                # if draft_invoice_total: 
                #     total_cumulative += draft_invoice_total
                draf_inv = draft_invoice_total.get('total_npc',0)
                draf_inv_100 = draft_invoice_total.get('total_npc_100',0)
                if m == today_key:
                    total_to_add = total_moth_npc_as_pp
                    if draf_inv and draf_inv_100:
                        total_to_add += draf_inv_100 
                    cumulative_total += total_to_add
                    values.append(month_map[m]+draf_inv)
                    temp_chart_value = month_map[m]+draf_inv
                else:
                    total_to_add = total_moth_npc_as_pp
                    if draf_inv and draf_inv_100:
                        total_to_add += draf_inv_100 
                    values.append(cumulative_total+month_map[m]+draf_inv)
                    temp_chart_value = cumulative_total+month_map[m]+draf_inv
                    cumulative_total += total_to_add
                
                # if m == today_key:
                #     cumulative_total += total_moth_npc_as_pp
                #     values.append(month_map[m])
                # else:
                #     values.append(cumulative_total+month_map[m])
                #     cumulative_total += total_moth_npc_as_pp
            print(f"chart value for month {m} : {temp_chart_value}")
            print("=============================")
        return {
            "labels": labels,
            "values": values,
        }
    
    def _compute_invoice_prorate(self,move):
        invoice_prorate = 100 
        if not move.invoice_date:
            return invoice_prorate 
        year = move.invoice_date.year
        month = move.invoice_date.month
        day = move.invoice_date.day

        # total days in that month
        days_in_month = calendar.monthrange(year, month)[1]

        # days covered = from invoice_date to month end
        days_covered = days_in_month - day + 1

        invoice_prorate = round((days_covered / days_in_month) * 100, 2) 

        return invoice_prorate 