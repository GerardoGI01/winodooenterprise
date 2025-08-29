# -*- coding: utf-8 -*-
"""
Modulo: HR Contract Custom
Descripción:
    Este archivo .PY extiende el modelo 'hr.contract' para añadir campos adicionales 
    relacionados con beneficios, descuentos y condiciones especiales en los contratos 
    laborales. También incluye lógica para sincronizar el estado del contrato con el 
    empleado y permite personalizar el salario mediante un campo específico.
"""

from odoo import models, fields, api
from datetime import datetime, timedelta


class HrContract(models.Model):
    _inherit = 'hr.contract'

    # Campos
    funeral_contract = fields.Float(string='Plan excequial')
    insurance_contract = fields.Float(string='Seguros')
    loan_contract = fields.Float(string='Prestamos')
    bearing_contract = fields.Float(string='Auxilios')
    discount_contract = fields.Float(string='Bonificacion por cargo')
    interest_contract = fields.Float(string='Intereses')
    embargos_contract = fields.Float(string='Embargos')

    today_date = fields.Date(string="Today's Date", default=fields.Date.today)
    company_id_contract = fields.Char(string='Id Compañia', related='company_id.name')

    is_pensioner = fields.Boolean(string='Pensionado')
    is_attachment = fields.Boolean(string='Embargos')
    custom_wage = fields.Monetary(string='Salario', store=True)

    # Métodos
    @api.onchange('custom_wage')
    def _onchange_custom_wage(self):
        if self.custom_wage != 0:
            self.wage = self.custom_wage

    def write_is_contract(self):
        for record in self:
            if record.state == 'open':
                record.employee_id.write({'is_contract': True})
            else:
                record.employee_id.write({'is_contract': False})

    def write(self, vals):
        self.write_is_contract()
        return super(HrContract, self).write(vals)
