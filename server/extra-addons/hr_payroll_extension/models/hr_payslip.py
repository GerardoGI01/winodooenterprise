from odoo import models, fields, api, _
from datetime import timedelta
from odoo.tools.safe_eval import safe_eval
import logging
_logger = logging.getLogger(__name__)
import base64

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def compute_sheet(self):
        result = super(HrPayslip, self).compute_sheet()

        for payslip in self:
            if payslip.company_id.id != 1:
                continue

            work_entry_type = payslip.env['hr.work.entry.type']
            payslip_line_obj = payslip.env['hr.payslip.line']

            d_nohab_type = work_entry_type.search([('code', '=', 'd_nohab')], limit=1)
            d_vac1_type = work_entry_type.search([('code', 'in', ['d_vac'])], limit=1)
            contract = payslip.employee_id.contract_id

            if d_nohab_type and d_vac1_type:
                d_vac1_line = payslip.worked_days_line_ids.filtered(lambda line: line.work_entry_type_id == d_vac1_type)
                if not d_vac1_line:
                    continue

                new_line_days = []
                employee_leaves = payslip.env['hr.leave'].search([
                    ('employee_id.id', '=', payslip.employee_id.id),
                    ('date_from', '<=', payslip.date_to),
                    ('date_to', '>=', payslip.date_from),
                ])

                weekend_days = 0
                for leave in employee_leaves:
                    start_date = max(leave.date_from.date(), payslip.date_from)
                    end_date = min(leave.date_to.date(), payslip.date_to)
                    for day in range((end_date - start_date).days + 1):
                        date_to_check = start_date + timedelta(days=day)
                        if date_to_check.weekday() == 6:  # 6 es domingo
                            weekend_days += 1

                _logger.info(
                    "Total de días de fin de semana en las ausencias dentro del rango de fechas del recibo de nómina: %s",
                    weekend_days)

                existing_line = payslip.worked_days_line_ids.filtered(
                    lambda line: line.work_entry_type_id == d_nohab_type)

                if not existing_line and weekend_days > 0:
                    worked_days_line = payslip.env['hr.payslip.worked_days'].create({
                        'work_entry_type_id': d_nohab_type.id,
                        'name': 'Días no hábiles vacaciones',
                        'payslip_id': payslip.id,
                        'number_of_days': weekend_days,
                    })

                    worked_hours = weekend_days * (
                        payslip.employee_id.hours_day if payslip.employee_id.hours_day else 8)
                    hourly_wage = contract.hourly_wage
                    amount = worked_hours * hourly_wage

                    worked_days_line.write({
                        'number_of_hours': worked_hours,
                        'amount': amount
                    })

                    # Buscar la regla salarial dinámicamente
                    salary_rule = payslip.env['hr.salary.rule'].search([('code', '=', 'd_nohab')], limit=1)

                    payslip_line = payslip.env['hr.payslip.line'].search(
                        [('code', '=', 'd_nohab'), ('slip_id', '=', payslip.id)], limit=1)
                    payslip_line_total = payslip.env['hr.payslip.line'].search(
                        [('code', 'in', ['d_vac', 'd_vac1']), ('slip_id', '=', payslip.id)], limit=1)

                    if not payslip_line:
                        payslip_line_obj.create({
                            'name': 'Días no hábiles vacaciones',
                            'code': 'd_nohab',
                            'contract_id': contract.id,
                            'quantity': 1.00000,
                            'rate': 100.00000,
                            'amount': weekend_days,
                            'total': weekend_days,
                            'slip_id': payslip.id,
                            'salary_rule_id': salary_rule.id,
                        })
                    else:
                        _logger.warning("La línea de nómina con el código 'd_nohab' ya existe para el ID de nómina %s",
                                        payslip.id)

                    if d_vac1_line and d_vac1_line.number_of_days > weekend_days:
                        d_vac1_line.write({
                            'number_of_days': d_vac1_line.number_of_days - weekend_days,
                            'number_of_hours': d_vac1_line.number_of_hours - worked_hours,
                        })

                    if payslip_line_total:
                        payslip_line_total.write({
                            'amount': payslip_line_total.amount - amount,
                            'total': payslip_line_total.total - amount,
                        })

        return result

    def action_payslip_done(self):

        res = super(HrPayslip, self).action_payslip_done()
        for record in self:
            if record.state == 'done':
                if record.struct_id.is_send_mail:
                     record.send_mail_paylisp()

        return res

    def send_mail_paylisp(self):
        mapped_reports = self._get_pdf_reports()
        attachments_vals_list = []
        generic_name = _("Payslip")
        template = self.env.ref('hr_payroll.mail_template_new_payslip', raise_if_not_found=False)

        for report, payslips in mapped_reports.items():
            for payslip in payslips:
                # Simula la generación del PDF y la acción de imprimir el informe
                pdf_content, dummy = self.env['ir.actions.report'].sudo().with_context(lang=payslip.employee_id.address_id.lang)._render_qweb_pdf(report, payslip.id)

                if report.print_report_name:
                    pdf_name = safe_eval(report.print_report_name, {'object': payslip})
                else:
                    pdf_name = generic_name

                # Crea el registro de adjunto directamente sin usar sudo
                attachment = self.env['ir.attachment'].create({
                    'name': pdf_name + '.pdf',
                    'type': 'binary',
                    'datas': base64.encodebytes(pdf_content),
                    'res_model': payslip._name,
                    'res_id': payslip.id,
                })

                attachments_vals_list.append({
                    'name': pdf_name + '.pdf',
                    'type': 'binary',
                    'raw': pdf_content,
                    'res_model': payslip._name,
                    'res_id': payslip.id,
                })

                # Envia el correo electrónico con el adjunto
                if template:
                    # Ajusta el contexto para incluir el ID del adjunto
                    context = {
                        'default_model': 'hr.payslip',
                        'default_res_id': payslip.id,
                        'default_attachment_ids': [(6, 0, [attachment.id])],
                    }

                    # Envía el correo electrónico
                    template.with_context(**context).send_mail(
                        payslip.id,
                        email_layout_xmlid='mail.mail_notification_light'
                    )

        # Opcional: Puedes eliminar los adjuntos después de enviar los correos si lo deseas
        # self.env['ir.attachment'].sudo().create(attachments_vals_list).unlink()