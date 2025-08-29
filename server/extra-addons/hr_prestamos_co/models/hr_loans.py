# -*- coding: utf-8 -*-
"""
Módulo: hr_prestamos_co
================

Este modelo extiende la funcionalidad de Odoo para gestionar los préstamos de empleados.
Permite registrar información sobre:
- El empleado que solicita el préstamo.
- Tipo de préstamo y concepto asociado.
- Valor solicitado, cuotas, acumulados y saldo pendiente.
- Fechas de inicio, fin y pago.
- Estado del préstamo (activo, completado o cancelado).
- Relación con recibos de nómina.

Incluye validaciones para evitar duplicados en conceptos
y cálculos automáticos para cuotas, acumulados, saldo y fechas.
"""

from datetime import timedelta

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class HrLoans(models.Model):
    _name = 'hr.loans'
    _description = 'Préstamos de empleados'

    # -------------------------------------------------------------------------
    # Campos básicos
    # -------------------------------------------------------------------------
    name = fields.Char(string="Referencia")
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    identification = fields.Char(
        string='Cédula',
        related='employee_id.identification_id',
        readonly=True
    )
    type_loans = fields.Many2one(
        'hr.payslip.input.type',
        string="Tipo",
        domain=[('code', 'ilike', 'ded%')]
    )
    concept = fields.Char(string='Concepto')
    requested_value = fields.Monetary(string='Valor Total Solicitado')
    refund_date = fields.Date(string='Fecha de Reembolso')
    method = fields.Selection(
        [
            ('first', 'Primera'),
            ('second', 'Segunda'),
            ('both', 'Ambas Quincenas')
        ],
        string='Método'
    )
    duration = fields.Float(
        string='Duración',
        help='Indique el tiempo estimado en meses'
    )
    start_discounting = fields.Date(
        string='Empezar a Descontar',
        help='Indicar la quincena para comenzar proceso de descuento'
    )
    currency_id = fields.Many2one('res.currency', string='Moneda')

    # -------------------------------------------------------------------------
    # Campos calculados
    # -------------------------------------------------------------------------
    installment_value = fields.Monetary(
        string='Valor de Cuota',
        compute='_compute_installment_value',
        store=True
    )
    accrued = fields.Monetary(
        string='Acumulado',
        compute='_compute_accrued',
        store=True
    )
    total = fields.Monetary(
        string='Saldo Pendiente',
        compute='_compute_total',
        store=True
    )
    date_end_accrued = fields.Date(
        string='Fecha Finalización Préstamo',
        compute='_compute_date_end_accrued',
        store=True
    )
    payment_date = fields.Date(
        string='Fecha de Pago',
        compute='_compute_payment_date',
        store=True
    )

    # -------------------------------------------------------------------------
    # Estado y seguimiento
    # -------------------------------------------------------------------------
    paid_installments = fields.Integer(string='Quincenas Pagadas', default=0)
    state = fields.Selection(
        [
            ('active', 'Activo'),
            ('complete', 'Completado'),
            ('cancel', 'Cancelado'),
        ],
        string='Estado',
        default='active'
    )
    date_next = fields.Date(string='Fecha Siguiente Descuento')
    current_date = fields.Date(
        string='Fecha Actual',
        default=fields.Date.today
    )
    computed_first_time = fields.Boolean(
        string='Primera vez',
        default=True
    )
    observation = fields.Text(string='Observación')
    attachment = fields.Binary(string='Adjunto')
    attachment_filename = fields.Char(string='Nombre del Archivo Adjunto')

    # -------------------------------------------------------------------------
    # Relaciones
    # -------------------------------------------------------------------------
    payslip_ids = fields.Many2many(
        'hr.payslip',
        string='Recibos de Nómina Asociados',
        readonly=True
    )

    # -------------------------------------------------------------------------
    # Restricciones y validaciones
    # -------------------------------------------------------------------------
    @api.constrains('concept')
    def _check_unique_concept(self):
        """Evita duplicidad de conceptos en préstamos."""
        for loan in self:
            if loan.concept:
                duplicate_loans = self.env['hr.loans'].search([
                    ('concept', '=', loan.concept),
                    ('id', '!=', loan.id)
                ])
                if duplicate_loans:
                    raise ValidationError(
                        'El concepto ya está siendo utilizado en otro registro. '
                        'Por favor verifique nuevamente.'
                    )

    # -------------------------------------------------------------------------
    # Cálculos automáticos
    # -------------------------------------------------------------------------
    @api.depends('start_discounting', 'method', 'computed_first_time')
    def _compute_payment_date(self):
        """Calcula la fecha de pago del préstamo según el método de descuento."""
        for record in self:
            if record.start_discounting:
                start_date = fields.Date.from_string(record.start_discounting)

                if record.computed_first_time:
                    record.payment_date = start_date
                    record.computed_first_time = False
                else:
                    payment_date = start_date + timedelta(days=31)

                    if payment_date == fields.Date.today():
                        payment_date += timedelta(days=30)

                    if record.method == 'both':
                        payment_date += timedelta(days=15)

                    record.payment_date = payment_date

    @api.depends('requested_value', 'duration')
    def _compute_installment_value(self):
        """Divide el préstamo en cuotas según duración."""
        for record in self:
            record.installment_value = (
                record.requested_value / record.duration
                if record.requested_value and record.duration else 0.0
            )

    @api.depends('duration', 'start_discounting')
    def _compute_date_end_accrued(self):
        """Calcula la fecha final del préstamo y cambia estado automáticamente."""
        for loan in self:
            if loan.duration and loan.start_discounting:
                duration_in_days = int(loan.duration * 30.44)  # promedio mensual
                start_discounting_date = fields.Date.from_string(loan.start_discounting)
                end_accrued_date = start_discounting_date + timedelta(days=duration_in_days)
                loan.date_end_accrued = end_accrued_date

                today = fields.Date.today()
                loan.state = 'complete' if end_accrued_date <= today else 'active'

    @api.depends('payslip_ids.input_line_ids.amount')
    def _compute_accrued(self):
        """Suma los descuentos acumulados en nómina."""
        for loan in self:
            total_accrued = sum(
                line.amount
                for payslip in loan.payslip_ids
                for line in payslip.input_line_ids
                if line.name == loan.concept
            )
            loan.accrued = total_accrued

    @api.depends('requested_value', 'accrued')
    def _compute_total(self):
        """Calcula el saldo pendiente restando lo acumulado al valor solicitado."""
        for record in self:
            record.total = record.requested_value - record.accrued
