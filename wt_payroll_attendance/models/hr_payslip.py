# -*- coding: utf-8 -*-

from odoo import fields, models


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    attendance_rule = fields.Boolean('Is Attendence Rule ?')
    hour_price_lines = fields.One2many('hour.price.line', 'salary_rule', 'Hour Price Lines')


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def compute_sheet(self):
        res = super(HrPayslip, self).compute_sheet()
        for payslip in self:
            payslip_att_line = payslip.line_ids.filtered(lambda b: b.category_id.code == 'ATTN')
            attendance_lines = payslip.env['hr.attendance'].search([('employee_id', '=', payslip.employee_id.id), ('check_in', '>=', payslip.date_from), ('check_out', '<=', payslip.date_to)])
            if payslip_att_line and attendance_lines:
                total_hours = 0.00
                total_hours = sum(attendance_lines.mapped('worked_hours'))
                payslip_att_line.quantity = total_hours
                if payslip_att_line.salary_rule_id and payslip_att_line.salary_rule_id.hour_price_lines:
                    hour_price_line = payslip_att_line.salary_rule_id.hour_price_lines.filtered(lambda b: b.start <= total_hours and b.end >= total_hours)
                    if hour_price_line:
                        payslip_att_line.amount = hour_price_line[0].amount
        return res

    def _get_worked_day_lines(self):
        """
        :returns: a list of dict containing the worked days values that should be applied for the given payslip
        """
        res = []
        # fill only if the contract as a working schedule linked
        self.ensure_one()
        contract = self.contract_id
        if contract.resource_calendar_id:
            paid_amount = self._get_contract_wage()
            unpaid_work_entry_types = self.struct_id.unpaid_work_entry_type_ids.ids

            work_hours = contract._get_work_hours(self.date_from, self.date_to)
            total_hours = sum(work_hours.values()) or 1
            work_hours_ordered = sorted(work_hours.items(), key=lambda x: x[1])
            biggest_work = work_hours_ordered[-1][0] if work_hours_ordered else 0
            add_days_rounding = 0
            for work_entry_type_id, hours in work_hours_ordered:
                work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_type_id)
                is_paid = work_entry_type_id not in unpaid_work_entry_types
                calendar = contract.resource_calendar_id
                days = round(hours / calendar.hours_per_day, 5) if calendar.hours_per_day else 0
                if work_entry_type_id == biggest_work:
                    days += add_days_rounding
                day_rounded = self._round_days(work_entry_type, days)
                add_days_rounding += (days - day_rounded)
                if self.contract_id.wage_type == "hourly":
                    amount = self.contract_id.hourly_wage * hours
                else:
                    amount = hours * paid_amount / total_hours if is_paid else 0
                if work_entry_type.code == 'WORK100':
                    attendance_lines = self.env['hr.attendance'].search([('employee_id', '=', contract.employee_id.id), ('check_in', '>=', self.date_from), ('check_out', '<=', self.date_to)])
                    if attendance_lines :
                        hours = sum(attendance_lines.mapped('worked_hours')) or 0.00
                        if self.contract_id.wage_type == "hourly":
                            amount = self.contract_id.hourly_wage * hours
                        else:
                            amount = hours * paid_amount / total_hours if is_paid else 0
                        use_date = []
                        day = 0
                        for al_line in attendance_lines:
                            if al_line.check_in.date() not in use_date:
                                use_date.append(al_line.check_in.date())
                                day += 1
                        day_rounded = day
                attendance_line = {
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type_id,
                    'number_of_days': day_rounded,
                    'number_of_hours': hours,
                    'amount': amount,
                }
                res.append(attendance_line)
        return res


class HourPriceLine(models.Model):
    _name = 'hour.price.line'

    salary_rule = fields.Many2one('hr.salary.rule')
    start = fields.Float(required=True)
    end = fields.Float(required=True)
    amount = fields.Float(required=True, string='Amount/Hour')
