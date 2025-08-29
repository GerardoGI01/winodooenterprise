from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    company_name = fields.Char(string='Nombre Sucursal')
    salary_min = fields.Integer(string='Salario Minimo (SMLV)')
    code_company = fields.Integer(string='Código' )
