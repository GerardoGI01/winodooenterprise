# -*- coding: utf-8 -*-
"""
Módulo: Herencia de hr.salary.rule
Descripción:
Este archivo extiende el modelo `hr.salary.rule` para incluir campos de
clasificación adicional, como tipo de socio contable y tipo de reporte
en el recibo de nómina.
"""

from odoo import fields, models


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    partner_type = fields.Selection(
        selection=[
            ('employee', 'Employee'),
            ('layoffs', 'Found Layoffs'),
            ('eps', 'EPS'),
            ('afp', 'AFP'),
            ('unemployment', 'Unemployment Fund'),
            ('arl', 'ARL'),
            ('afc', 'AFC'),
            ('compensation', 'Compensation'),
            ('voluntary', 'Voluntary Contribution'),
        ],
        string='Accounting Partner'
    )

    report_type = fields.Selection(
        selection=[
            ('deduction', 'Deducción'),
            ('deven', 'Devengados'),
            ('days', 'Días'),
        ],
        string='Valor Recibo Nómina'
    )
