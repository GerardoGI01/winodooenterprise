# -*- coding: utf-8 -*-
"""
Módulo: HR Payslip Custom
Descripción:
    Este módulo extiende los modelos 'hr.payslip' y 'hr.payslip.line' para:
      - Reasignar dinámicamente los partners en las líneas contables de la nómina.
      - Eliminar las líneas de nómina con valor total en cero durante el cálculo.
      - Determinar el partner correspondiente según el tipo de regla salarial.
"""

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def action_payslip_done(self):
        for record in self:
            aux = record.payslip_run_id
            record.payslip_run_id = False
            record.ensure_one()

            res = super(HrPayslip, record).action_payslip_done()
            payslips_to_post = record.filtered(lambda slip: slip.move_id)

            for slip in payslips_to_post:
                for move_line in slip.move_id.line_ids:
                    partner = slip.employee_id.address_id
                    slip_line = record.env['hr.payslip.line'].search([
                        ('slip_id', '=', slip.id),
                        ('employee_id', '=', slip.employee_id.id),
                        ('company_id', '=', self.env.company.id),
                        ('name', '=', move_line.name),
                    ], limit=1)

                    if slip_line:
                        partner = slip_line.get_partner(
                            slip_line.salary_rule_id, slip.employee_id
                        )

                    move_line.write({'partner_id': partner.id})

            record.payslip_run_id = aux
        return res

    def compute_sheet(self):
        result = super(HrPayslip, self).compute_sheet()

        for struct in self.struct_id:
            for line in self.line_ids:
                if line.total == 0:
                    line.unlink()

        return result


class HrPayslipLine(models.Model):
    _inherit = "hr.payslip.line"

    def get_partner(self, rule, employee):
        partner = employee.address_id
        if rule:
            if rule.partner_type == 'eps':
                partner = employee.eps_id
            elif rule.partner_type == 'afp':
                partner = employee.afp_id
            elif rule.partner_type == 'arl':
                partner = employee.arl_id
            elif rule.partner_type == 'afc':
                partner = employee.afc_id
            elif rule.partner_type == 'compensation':
                partner = employee.compensation_box
            elif rule.partner_type == 'voluntary':
                partner = employee.voluntary_contribution_id

        return partner
