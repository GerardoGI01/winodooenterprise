# -*- coding: utf-8 -*-
# Autor: Luis Felipe Paternina
# Ingeniero de Sistemas
# Contacto: lfpaternina93@gmail.com
# Cel: +57 321 506 2353
# Ubicación: Bogotá, Colombia
#################################################################################################################

from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Empleados'

    # Campos
    eps_id = fields.Many2one('res.partner', string="EPS")
    afp_id = fields.Many2one('res.partner', string="Fondo de Pensiones")
    afc_id = fields.Many2one('res.partner', string="Fondo de Cesantías")
    arl_id = fields.Many2one('res.partner', string="Aseguradora de Riesgos Laborales")
    compensation_box = fields.Many2one('res.partner', string="Caja de compensación")
    risk_classes_type = fields.Selection(
        [
            ('risk1', 'Clase de Riesgo 1'),
            ('risk2', 'Clase de Riesgo 2'),
            ('risk3', 'Clase de Riesgo 3'),
            ('risk4', 'Clase de Riesgo 4'),
            ('risk5', 'Clase de Riesgo 5'),
        ],
        string="ARL - Clases de Riesgos"
    )
    date_of_joining = fields.Date(string='Fecha de Ingreso', related='contract_id.date_start')
    is_contract = fields.Boolean(string='Está contratado')
    hours_day = fields.Float(string='Jornada Laboral')

    # Métodos
    def _update_hours_day(self):
        for employee in self:
            if employee.resource_calendar_id.id == 1:
                employee.hours_day = 7.50
            else:
                employee.hours_day = 3.55

    def write(self, vals):
        # Verificar si la actualización ya se ha realizado en este contexto
        if not self.env.context.get('skip_update_hours_day'):
            result = super(HrEmployee, self).write(vals)

            # Establecer el contexto para evitar la llamada recursiva
            self = self.with_context(skip_update_hours_day=True)
            self._update_hours_day()

            return result
        else:
            # Si ya se ha realizado la actualización, simplemente llamar a la implementación original
            return super(HrEmployee, self).write(vals)
