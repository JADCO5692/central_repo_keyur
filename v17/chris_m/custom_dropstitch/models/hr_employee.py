from odoo import models, fields, api
from datetime import date, datetime, timedelta

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.model
    def create_daily_attendance(self,day=0): 
        Attendance = self.env['hr.attendance']
        target_date = date.today() + timedelta(days=day)
 
        if target_date.weekday() >= 5:
            return

        employees = self.search([('active', '=', True)])
        for emp in employees:
            exists = Attendance.search([
                ('employee_id', '=', emp.id),
                ('check_in', '>=', datetime.combine(target_date, datetime.min.time())),
                ('check_in', '<', datetime.combine(target_date + timedelta(days=1), datetime.min.time())),
            ], limit=1)

            if not exists:
                check_in = datetime.combine(target_date, datetime.strptime("08:00:00", "%H:%M:%S").time())
                check_out = datetime.combine(target_date, datetime.strptime("17:00:00", "%H:%M:%S").time())

                Attendance.create({
                    'employee_id': emp.id,
                    'check_in': check_in,
                    'check_out': check_out,
                })
