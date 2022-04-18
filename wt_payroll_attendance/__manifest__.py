# -*- coding: utf-8 -*-

{
    'name': 'Attendance on Payslips',
    'description': 'Get Attendence hours onto Employee Payslips.',
    'version': '1.0',
    'author': 'Smartboss.fr',
    'suuport': 'smartboss@smartboss.fr',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/hr_payslip.xml'
    ],
    'depends': [
        'hr_payroll',
        'hr_attendance'
    ],
}
