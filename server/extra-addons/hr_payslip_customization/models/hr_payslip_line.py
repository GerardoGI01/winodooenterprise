# -*- coding: utf-8 -*-
"""
Módulo que extiende el modelo hr.payslip.line para agregar campos calculados:
- description: Descripción basada en la regla salarial correspondiente.
- other_amount: Monto asociado a la regla salarial.
Los valores se calculan automáticamente a partir de las líneas de entrada del payslip.
"""

from odoo import models, fields, api, _

class HrPayslipLine(models.Model):
    _inherit = "hr.payslip.line"

    description = fields.Char(
        string="Descripción",
        compute="compute_fields_in_line",
        default='',
    )

    other_amount = fields.Float(
        string="Cuenta",
        compute="compute_fields_in_line",
        default=0,
    )

    @api.depends('slip_id.input_line_ids', 'salary_rule_id')
    def compute_fields_in_line(self):
        """
        Calcula automáticamente la descripción y el monto asociado a la línea del payslip
        según la regla salarial correspondiente en input_line_ids.
        """
        for line in self:
            line.description = ''
            line.other_amount = 0
            for inp in line.slip_id.input_line_ids:
                if inp.input_type_id.code == line.salary_rule_id.code:
                    line.description = inp.name
                    line.other_amount = inp.amount
