# -*- coding: utf-8 -*-
"""
Extensión de hr.payslip para gestionar préstamos de empleados en las nóminas.

Este modelo permite:
- Asociar un préstamo a un recibo de nómina.
- Generar automáticamente líneas de entrada en la nómina según el préstamo.
- Actualizar el estado de los préstamos (activo, completado).
- Recalcular fechas de pago según el método de descuento.
"""

from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import fields, models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    # -------------------------------------------------------------------------
    # Campos
    # -------------------------------------------------------------------------
    loan_id = fields.Many2one('hr.loans', string='Préstamo')
    loan_value = fields.Monetary(string='Valor de Cuota')

    # -------------------------------------------------------------------------
    # Métodos
    # -------------------------------------------------------------------------
    def create_loan_payslip_line(self):
        """Genera líneas de entrada de préstamos en la nómina."""
        for payslip in self:
            # Verificar si el payslip ya está asociado a préstamos
            loans_with_payslip = self.env['hr.loans'].search([
                ('payslip_ids', 'in', payslip.id)
            ])
            if loans_with_payslip:
                continue

            if payslip.employee_id:
                # Buscar préstamos aplicables en el rango de fechas del payslip
                loans = self.env['hr.loans'].search([
                    ('employee_id', '=', payslip.employee_id.id),
                    ('payment_date', '>=', payslip.date_from),
                    ('payment_date', '<=', payslip.date_to),
                ])

                # Cambiar a completados los préstamos que ya se cubrieron
                completed_loans = loans.filtered(lambda loan: loan.total <= 0)
                completed_loans.write({'state': 'complete'})

                # Procesar préstamos activos
                active_loans = loans.filtered(lambda loan: loan.state == 'active')
                input_lines = []

                for loan in active_loans:
                    existing_entry = payslip.input_line_ids.filtered(
                        lambda line: line.name == loan.concept
                    )
                    if not existing_entry:
                        new_entry_vals = {
                            'payslip_id': payslip.id,
                            'input_type_id': loan.type_loans.id,
                            'name': loan.concept,
                            'amount': loan.installment_value,
                            'contract_id': payslip.contract_id.id,
                            'sequence': 10,
                        }
                        input_lines.append(new_entry_vals)
                        payslip.write({'loan_value': loan.installment_value})

                        # Recalcular próxima fecha de pago según método
                        if loan.method == 'both':
                            if payslip.date_from.day == 1:
                                new_payment_date = loan.payment_date.replace(day=16)
                            elif payslip.date_from.day == 16:
                                new_payment_date = loan.payment_date.replace(day=1) + relativedelta(months=1)
                                if new_payment_date.month != loan.payment_date.month:
                                    new_payment_date = new_payment_date.replace(day=1)
                            loan.write({'payment_date': new_payment_date})
                        elif loan.method in ('first', 'second'):
                            new_payment_date = loan.payment_date + timedelta(days=31)
                            loan.write({'payment_date': new_payment_date})

                # Crear en batch todas las líneas de préstamos encontradas
                if input_lines:
                    created_entries = self.env['hr.payslip.input'].create(input_lines)
                    for entry in created_entries:
                        loan = self.env['hr.loans'].search(
                            [('concept', '=', entry.name)], limit=1
                        )
                        if loan:
                            loan.write({'payslip_ids': [(4, payslip.id)]})
