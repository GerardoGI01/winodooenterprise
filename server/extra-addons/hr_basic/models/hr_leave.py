# -*- coding: utf-8 -*-
"""
Modulo: HR Leave Custom
Descripción:
    Este módulo extiende el modelo 'hr.leave' para gestionar ausencias con periodos,
    cálculo de días pendientes, alertas y validaciones adicionales.
"""

import logging
from datetime import datetime, timedelta
from operator import attrgetter
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, exceptions
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    # Campos
    date_update = fields.Boolean(string='Actualizar Fechas')
    days_request = fields.Char(string='Días Disponibles')
    start_date = fields.Date(string='Periodo Inicial No')
    end_date = fields.Date(string='Periodo Final No')
    alert_days = fields.Boolean(string='Alerta Dia')
    days_count_alert = fields.Integer(string='Días de Ausencia (Alerta)')
    total_days_count = fields.Integer(string='Total Days Count')
    total_days_assigned = fields.Boolean(string='Total Days Assigned', default=False)

    # Usados
    period_init = fields.Date(string='Período Inicio')
    period_end = fields.Date(string='Período Final')
    period = fields.Char(string='Período', compute='_compute_period_display')
    days_count = fields.Integer(string='Días Contados')
    days_pending = fields.Char(string='Días Pendientes')
    alert_days = fields.Boolean(string='Alerta Dia')
    date_contract = fields.Date(string='Fecha Contrato', related='employee_id.contract_id.date_start')
    updating_days_pending = fields.Boolean(string='Actualizando Días Pendientes', default=False)
    last_days_count = fields.Integer(string='Últimos Días Contados')

    # Onchange
    @api.onchange('date_contract', 'employee_id', 'holiday_status_id')
    def _onchange_date_contract(self):
        for record in self:
            if record.employee_id and record.holiday_status_id:
                # Buscar la última ausencia validada
                last_leave = self.env['hr.leave'].search(
                    [
                        ('employee_id', '=', record.employee_id.id),
                        ('holiday_status_id.type_absence', '=', 'absence2'),
                        ('state', '=', 'validate')
                    ],
                    order='date_from desc',
                    limit=1
                )

                if last_leave and last_leave.period_init:
                    record.period_init = last_leave.period_init
                    record.period_end = last_leave.period_end
                else:
                    record.period_init = record.date_contract
                    record.period_end = record.date_contract + timedelta(days=365)

    @api.onchange('employee_id', 'holiday_status_id')
    def _onchange_last_days_count(self):
        for record in self:
            if (
                record.employee_id
                and record.holiday_status_id
                and record.holiday_status_id.type_absence == 'absence2'
            ):
                last_leave = self.env['hr.leave'].search(
                    [
                        ('employee_id', '=', record.employee_id.id),
                        ('holiday_status_id.type_absence', '=', 'absence2'),
                        ('state', '=', 'validate')
                    ],
                    order='date_from desc',
                    limit=1
                )
                last_days_count = last_leave.days_count if last_leave else 0
                _logger.info(f"Calculated last_days_count for {record.employee_id.name}: {last_days_count}")

                record.last_days_count = last_days_count
            else:
                record.last_days_count = 0

    # Compute
    @api.depends('period_init', 'period_end')
    def _compute_period_display(self):
        for record in self:
            if record.period_init and record.period_end:
                record.period = f"{record.period_init} - {record.period_end}"
            else:
                record.period = ''

    # Business logic
    def _update_days_pending(self):
        for record in self:
            if record.holiday_status_id.type_absence == 'absence2':
                last_updating_leave = self.env['hr.leave'].search(
                    [
                        ('employee_id', '=', record.employee_id.id),
                        ('holiday_status_id.type_absence', '=', 'absence2'),
                        ('state', '=', 'validate'),
                        ('updating_days_pending', '=', True)
                    ],
                    order='date_from desc',
                    limit=1
                )

                if last_updating_leave:
                    leaves = self.env['hr.leave'].search(
                        [
                            ('employee_id', '=', record.employee_id.id),
                            ('holiday_status_id.type_absence', '=', 'absence2'),
                            ('state', '=', 'validate'),
                            ('date_from', '>=', last_updating_leave.date_from)
                        ]
                    )
                else:
                    leaves = self.env['hr.leave'].search(
                        [
                            ('employee_id', '=', record.employee_id.id),
                            ('holiday_status_id.type_absence', '=', 'absence2'),
                            ('state', '=', 'validate')
                        ]
                    )

                total_days_count = sum(leaves.mapped('weekend_days'))
                total_days_pending = 15 - total_days_count

                last_days_count = record.last_days_count
                _logger.info(f"***************** {record.employee_id.name}: {last_days_count}")

                if last_days_count >= 15:
                    if not record.total_days_assigned:
                        current_period_start_year = record.period_init.year
                        new_period_start_year = current_period_start_year + 1

                        new_period_init = record.period_init.replace(year=new_period_start_year)
                        new_period_end = record.period_init.replace(year=new_period_start_year + 1)

                        record.write({
                            'period_init': new_period_init,
                            'period_end': new_period_end,
                            'days_count': record.weekend_days,
                            'updating_days_pending': True,
                        })
                    else:
                        record.write({
                            'days_count': record.weekend_days,
                            'updating_days_pending': True,
                        })

                    leaves = self.env['hr.leave'].search(
                        [
                            ('employee_id', '=', record.employee_id.id),
                            ('holiday_status_id.type_absence', '=', 'absence2'),
                            ('state', '=', 'validate'),
                            ('date_from', '>=', record.date_from)
                        ]
                    )
                    total_days_count = sum(leaves.mapped('weekend_days'))
                    total_days_pending = 15 - total_days_count

                else:
                    if total_days_count > 15:
                        remaining_days = 15 - last_days_count
                        raise UserError(
                            f"En esta ausencia solo se pueden tomar {remaining_days} días. "
                            f"Actualmente tienes {total_days_count} días contados, "
                            f"lo que excede el límite permitido en días."
                        )

                record.write({
                    'days_count': total_days_count,
                    'days_pending': total_days_pending,
                    'alert_days': True
                })

    # Overrides
    def action_approve(self):
        res = super(HrLeave, self).action_approve()
        self._update_days_pending()
        return res
