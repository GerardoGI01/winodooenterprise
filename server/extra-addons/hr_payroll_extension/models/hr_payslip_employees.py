from odoo import models, fields, api
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)

class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    structure_type_id = fields.Many2many(
        'hr.payroll.structure.type',
        string='Tipo Estructura'
    )

    @api.onchange('structure_type_id')
    def _onchange_structure_type_id(self):
        if self.structure_type_id:
            employees = self.env['hr.employee'].search([
                ('contract_id.structure_type_id', 'in', self.structure_type_id.ids),
            ])
            _logger.info("Empleados filtrados: %s", employees.mapped('name'))
        else:
            _logger.info("No hay structure_type_id seleccionado, trayendo todos los empleados.")
            employees = self.env['hr.employee'].search([])
            _logger.info("Todos los empleados (sin filtro por estructura): %s", employees.mapped('name'))

        # Actualiza el campo employee_ids con los empleados filtrados
        self.employee_ids = employees


