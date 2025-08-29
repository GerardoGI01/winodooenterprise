from odoo import fields, models, api

class HrLoansSearch(models.Model):
    _name = 'hr.loans.search'
    _description = 'search loans'

    name = fields.Char(
        string="Nombre")
    employee_search_id = fields.Many2one(
        'hr.employee',
        string='Empleado')
