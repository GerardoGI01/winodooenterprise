from odoo import fields, models, api

class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    loan_value_input = fields.Float(
        string='Valor de Cuota')
