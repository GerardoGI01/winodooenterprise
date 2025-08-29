from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrContract(models.Model):
    _inherit = 'hr.contract'

    comprehensive_salary = fields.Selection([('na', ''),('no', 'NO'), ('si', 'SI')], string='Salario Integral')
    variable_salary = fields.Selection([('na', ''),('no', 'NO'), ('si', 'SI')], string='Salario Variable')
