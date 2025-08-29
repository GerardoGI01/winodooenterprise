# -*- coding: utf-8 -*-
"""
Módulo: Extensión de hr.payslip
Descripción:
Este archivo extiende el modelo de nómina (`hr.payslip`) en Odoo para añadir 
campos adicionales, cálculos personalizados y funciones relacionadas con:
- Estados adicionales de la nómina y gestión de aprobación.
- Cálculo de IBC en diferentes períodos (meses, quincenas, semestres).
- Cálculo de promedios y días contables (método 360).
- Gestión de pagos anticipados (vacaciones, días no hábiles, etc.).
- Envío de correos electrónicos y generación de PDFs de nómina.
"""

# ======================
#       LIBRERÍAS
# ======================
import uuid
import base64
import logging
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import models, fields, _, api
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


# ======================
#    MODELO EXTENDIDO
# ======================
class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    # ----------------------
    #        CAMPOS
    # ----------------------
    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('pre_payslip', 'Prenómina'),
        ('done', 'Done'),
        ('paid', 'Paid'),
        ('cancel', 'Rejected')],
        string="Estado")

    email_state_response = fields.Selection([
        ('send', 'Enviado'),
        ('accepted', 'Aceptado'),
        ('rejected', 'Rechazado')],
        string="Respuesta Prenómina")

    token = fields.Char(
        string='Access Token for approve',
        copy=False
    )

    email_state_badge = fields.Html(
        string="Prenómina",
        compute='_compute_email_state_badge',
        readonly=True)

    ibc_previus_month = fields.Float(
        string='IBC mes anterior',
        compute='_compute_ibc_previus_month')

    ibc_sum_previous_month = fields.Float(
        string='Suma IBC mes anterior',
        compute='_compute_ibc_sum_previous_month')

    total_dev_previus_month = fields.Float(
        string='Total devolución mes anterior',
        compute='_compute_total_dev_previus_month')

    average_ibc_last_12 = fields.Float(
        compute='_compute_average_ibc_last_12',
        string='Promedio IBC Últimos 12')

    days_360 = fields.Float(
        compute='_compute_day_360',
        string='Días contables 360')

    not_avilable_days_pay = fields.Float(
        compute='_compute_not_avilable_days_pay',
        string='Pago anticipado días no hábiles')

    not_avilable_days_pay_thr_mounth = fields.Float(
        compute='_compute_not_avilable_days_pay_thr_mounth',
        string='Pago anticipado días no hábiles tercer mes')

    anticiped_vacations_pay_prov = fields.Float(
        compute='_compute_anticiped_vacations_pay_prov',
        string='Pago anticipado de vacaciones prov')

    anticiped_vacations_pay = fields.Float(
        compute='_compute_anticiped_vacations_pay',
        string='Pago anticipado de vacaciones')

    total_income_not_wage = fields.Float(
        compute='_compute_total_income_not_wage',
        string='Total ingreso no salarial')

    anticiped_pay_thr_mounth = fields.Float(
        compute='_compute_anticiped_pay_thr_mounth',
        string='Pago anticipado tercer mes')

    base_pro_prov = fields.Float(
        compute='_compute_base_pro_prov',
        string='Base promedio provisional')

    extra_time_1q = fields.Float(
        compute='_compute_extra_time_1q',
        string='Horas extra primera quincena')

    des_social_1q = fields.Float(
        compute='_compute_des_social_1q',
        string='Descuento seguridad primera quincena')

    des_social_2q = fields.Float(
        compute='_compute_des_social_2q',
        string='Descuento seguridad segunda quincena')

    dias_trab_1q = fields.Float(
        compute='_compute_dias_trab_1q',
        string='Días trabajados primera quincena')

    addh_bonification_1q = fields.Float(
        compute='_compute_addh_bonification_1q',
        string='Bonificación de adherencia primera quincena')

    ing_salarial_add_1q = fields.Float(
        compute='_compute_ing_salarial_add_1q',
        string='Ingreso salarial primera quincena')

    ibc_sum_within_april = fields.Float(
        string='IBC Abril',
        compute='_compute_ibc_within_april',
        store=True)

    ibc_sum_within_august = fields.Float(
        string='IBC Agosto',
        compute='_compute_ibc_within_august',
        store=True)

    ibc_sum_within_december = fields.Float(
        string='IBC Diciembre',
        compute='_compute_ibc_within_december',
        store=True)

    ibc_sum_within_junary = fields.Float(
        string='IBC Enero',
        compute='_compute_ibc_within_junary',
        store=True)

    ibc_sum_within_june = fields.Float(
        string='IBC Junio',
        compute='_compute_ibc_within_june',
        store=True)

    accountable_days_july_or_january = fields.Float(
        string="Días desde la Prima",
        compute="_compute_accountable_days_july_or_january")

    accountable_days_from_january = fields.Float(
        string="Días desde la Cesantías",
        compute="_compute_accountable_days_from_january")

    # ----------------------
    #        MÉTODOS
    # ----------------------

    @api.depends('date_from', 'date_to', 'employee_id.contract_id.date_start')
    def _compute_accountable_days_from_january(self):
        for payslip in self:
            contract_date_start = payslip.employee_id.contract_id.date_start
            january_start_date = fields.Date.from_string(f'{payslip.date_to.year}-01-01')

            # Tomar la fecha más reciente entre el 1 de enero y la fecha de inicio del contrato
            if contract_date_start.year == january_start_date.year:
                start_date =  max(january_start_date, contract_date_start)
            else:
                start_date = january_start_date

            if start_date == january_start_date:
                dias_from = 0
                dias_to = (payslip.date_to.month - 1) * 30 + min(payslip.date_to.day, 30)
            else:
                dias_from = (start_date.month - 1) * 30 + min(start_date.day - 1, 30)
                dias_to = (payslip.date_to.month - 1) * 30 + min(payslip.date_to.day, 30)

            # Calcular la diferencia de días
            payslip.accountable_days_from_january = dias_to - dias_from

    @api.depends('date_from', 'date_to', 'employee_id.contract_id.date_start')
    def _compute_accountable_days_july_or_january(self):
        for payslip in self:
            contract_date_start = payslip.employee_id.contract_id.date_start
            january_start_date = fields.Date.from_string(f'{payslip.date_to.year}-01-01')
            july_start_date = fields.Date.from_string(f'{payslip.date_to.year}-07-01')

            if payslip.date_to >= july_start_date:

                start_date = july_start_date
                if contract_date_start > start_date:
                    start_date = contract_date_start
            else:

                start_date = january_start_date
                if contract_date_start > start_date:
                    start_date = contract_date_start

            if start_date == january_start_date:

                dias_from = 0
                dias_to = (payslip.date_to.month - 1) * 30 + min(payslip.date_to.day, 30)

            else:
                dias_from = (start_date.month - 1) * 30 + min(start_date.day - 1, 30)
                dias_to = (payslip.date_to.month - 1) * 30 + min(payslip.date_to.day, 30)

            # Calcular la diferencia de días
            payslip.accountable_days_july_or_january = dias_to - dias_from

    @api.depends('email_state_response')
    def _compute_email_state_badge(self):
        for record in self:
            style = ''
            text = ''
            if record.email_state_response == 'send':
                style = """ background-color: blue;
                            border: 1px solid rgba(27, 31, 35, .15);
                            border-radius: 6px;
                            box-shadow: rgba(27, 31, 35, .1) 0 1px 0;
                            box-sizing: border-box;
                            color: #fff;                            
                            font-family: -apple-system,system-ui,"Segoe UI",Helvetica,Arial,sans-serif,"Apple Color Emoji","Segoe UI Emoji";
                            font-size: 14px;
                            font-weight: 600;
                            line-height: 20px;
                            padding: 6px 16px;                            
                            text-align: center;
                            text-decoration: none;
                            vertical-align: middle;
                            white-space: nowrap;"""
                text = 'Enviado'
            elif record.email_state_response == 'accepted':
                style = """ background-color: green;
                            border: 1px solid rgba(27, 31, 35, .15);
                            border-radius: 6px;
                            box-shadow: rgba(27, 31, 35, .1) 0 1px 0;
                            box-sizing: border-box;
                            color: #fff;                            
                            font-family: -apple-system,system-ui,"Segoe UI",Helvetica,Arial,sans-serif,"Apple Color Emoji","Segoe UI Emoji";
                            font-size: 14px;
                            font-weight: 600;
                            line-height: 20px;
                            padding: 6px 16px;                            
                            text-align: center;
                            text-decoration: none;
                            vertical-align: middle;
                            white-space: nowrap;"""
                text = 'Aceptado'
            elif record.email_state_response == 'rejected':
                style = """ background-color: red;
                            border: 1px solid rgba(27, 31, 35, .15);
                            border-radius: 6px;
                            box-shadow: rgba(27, 31, 35, .1) 0 1px 0;
                            box-sizing: border-box;
                            color: #fff;                            
                            font-family: -apple-system,system-ui,"Segoe UI",Helvetica,Arial,sans-serif,"Apple Color Emoji","Segoe UI Emoji";
                            font-size: 14px;
                            font-weight: 600;
                            line-height: 20px;
                            padding: 6px 16px;                            
                            text-align: center;
                            text-decoration: none;
                            vertical-align: middle;
                            white-space: nowrap;"""
                text = 'Rechazado'
            else:
                style = """ background-color: grey;
                            border: 1px solid rgba(27, 31, 35, .15);
                            border-radius: 6px;
                            box-shadow: rgba(27, 31, 35, .1) 0 1px 0;
                            box-sizing: border-box;
                            color: #fff;                            
                            font-family: -apple-system,system-ui,"Segoe UI",Helvetica,Arial,sans-serif,"Apple Color Emoji","Segoe UI Emoji";
                            font-size: 14px;
                            font-weight: 600;
                            line-height: 20px;
                            padding: 6px 16px;                            
                            text-align: center;
                            text-decoration: none;
                            vertical-align: middle;
                            white-space: nowrap;"""
                text = 'Sin enviar'
            record.email_state_badge = f"""
                <div style="width: 100px; text-align: center; {style} color: white;">
                    <span style="display: block;">{text}</span>
                </div>
            """

    def button_send_mail_and_change_state(self):

        if self.state != 'pre_payslip':
            self.ensure_one()
            self.token = str(uuid.uuid4())

            template = self.env.ref('coondev_payslip_custom.email_template_for_payslip', False)
            
            if not template:
                raise UserError(_("Email Template is not found!"))
            
            for payslip in self:            
                if not payslip.id:
                    raise UserError(_("The payslip record is not found!"))
                
                
                try:
                    template.send_mail(payslip.id, force_send=True)
                except Exception as e:
                    raise UserError(_("An error occurred while sending the email: %s") % str(e))
                            
                payslip.state = 'pre_payslip'
                payslip.email_state_response = 'send'

        else:
            for payslip in self:            
                if not payslip.id:
                    raise UserError(_("The payslip record is not found!"))
                
                payslip.state = 'verify'

    @api.depends('date_from', 'date_to')
    def _compute_ibc_previus_month(self):
        for payslip in self:
            day_from = payslip.date_from.day
            day_to = payslip.date_to.day
            payslip.ibc_previus_month = 0

            if day_from == 1 and day_to == 15:
                pass
            elif day_from == 16:
                for payslip in self.filtered(lambda slip: slip.state in ['draft', 'verify']):
                    # Buscar el recibo de salario anterior
                    previous_payslip = self.env['hr.payslip'].search([
                        ('employee_id', '=', payslip.employee_id.id),
                        ('state', '=', 'done'),
                        ('date_to', '<', payslip.date_from),
                    ], order='date_to desc', limit=1)
                    
                    if previous_payslip:
                        ibc_ss_1_line = sum(previous_payslip.line_ids.filtered(lambda l: l.code in ['IBC_SS_1']).mapped('total'))
                        
                        if ibc_ss_1_line:
                            payslip.ibc_previus_month = ibc_ss_1_line

    @api.depends('date_from', 'date_to')
    def _compute_total_dev_previus_month(self):
        for payslip in self:
            day_from = payslip.date_from.day
            day_to = payslip.date_to.day
            
            payslip.total_dev_previus_month = 0

            if day_from == 1 and day_to == 15:
                pass
            elif day_from == 16:
                for payslip in self.filtered(lambda slip: slip.state in ['draft', 'verify']):
                    # Buscar el recibo de salario anterior
                    previous_payslip = self.env['hr.payslip'].search([
                        ('employee_id', '=', payslip.employee_id.id),
                        ('state', '=', 'done'),
                        ('date_to', '<', payslip.date_from),
                    ], order='date_to desc', limit=1)
                    
                    if previous_payslip:
                        # Buscar la línea con el código "total_dev" en el recibo anterior
                        total_dev_pm = previous_payslip.line_ids.filtered(lambda line: line.code == 'total_dev')
                        
                        if total_dev_pm:
                            payslip.total_dev_previus_month = total_dev_pm.total

    @api.depends('date_from','company_id')
    def _compute_ibc_within_april(self):
 
        for record in self:
            record.ibc_sum_within_april = 0
            year_of_interest = record.date_from.year
            employee_id = record.employee_id.id
            specific_date_from = f'{year_of_interest - 1}-12-16'
            specific_date_to = f'{year_of_interest}-04-15'            
            record.ibc_sum_within_april = self.calculate_sum_of_ibc(specific_date_from,specific_date_to,record.company_id,employee_id)

    @api.depends('date_from','company_id')
    def _compute_ibc_within_august(self):
        for record in self:
            record.ibc_sum_within_august = 0
            year_of_interest = record.date_from.year
            employee_id = record.employee_id.id
            specific_date_from = f'{year_of_interest}-04-16'
            specific_date_to = f'{year_of_interest}-08-15'           
            record.ibc_sum_within_august = self.calculate_sum_of_ibc(specific_date_from,specific_date_to,record.company_id,employee_id)

    @api.depends('date_from','company_id')
    def _compute_ibc_within_december(self):
        for record in self:
            record.ibc_sum_within_december = 0
            year_of_interest = record.date_from.year
            employee_id = record.employee_id.id
            specific_date_from = f'{year_of_interest}-07-01'
            specific_date_to = f'{year_of_interest}-12-15'
            alt_date = f'{year_of_interest}-12-30'
            record.ibc_sum_within_december = self.calculate_sum_of_ibc(specific_date_from,specific_date_to,record.company_id,employee_id,alt_date,decree=True)

    @api.depends('date_from','company_id')
    def _compute_ibc_within_junary(self):
        for record in self:
            record.ibc_sum_within_junary = 0
            year_of_interest = record.date_from.year
            employee_id = record.employee_id.id
            specific_date_from = f'{year_of_interest}-01-01'
            specific_date_to = f'{year_of_interest}-06-15'
            alt_date = f'{year_of_interest}-06-30'
            record.ibc_sum_within_junary = self.calculate_sum_of_ibc(specific_date_from,specific_date_to,record.company_id,employee_id,alt_date,decree=True)

    @api.depends('date_from','company_id')
    def _compute_ibc_within_june(self):
        for record in self:
            record.ibc_sum_within_june = 0
            year_of_interest = record.date_from.year
            employee_id = record.employee_id.id
            specific_date_from = f'{year_of_interest}-08-16'
            specific_date_to = f'{year_of_interest}-12-15'
            record.ibc_sum_within_june = self.calculate_sum_of_ibc(specific_date_from,specific_date_to,record.company_id,employee_id)

    def calculate_sum_of_ibc(self,month_day_from,month_day_to,company_id,employee_id,atl_date='1990-01-01',decree=False):
        res = 0
        if atl_date != '1900-01-01':
        
            payslips_of_interest = self.env['hr.payslip'].search([                
                ('state', '=', 'done'),
                ('employee_id', '=', employee_id),
                ('date_from', '>=', month_day_from),
                '|', 
                ('date_to', '<=', atl_date),
                ('date_to', '<=', month_day_to),
                ('company_id', '=', company_id.id),
            ])
        else:
            payslips_of_interest = self.env['hr.payslip'].search([                
                ('state', '=', 'done'),
                ('employee_id', '=', employee_id),
                ('date_from', '>=', month_day_from),
                ('date_to', '<=', month_day_to),
                ('company_id', '=', company_id.id),
            ])

        if decree == True:
            for ps in payslips_of_interest: 
                res += sum(ps.line_ids.filtered(lambda l: l.code in ['IBC_SS_1','vac','vac_1','lic_rem']).mapped('total'))

        else:
            for ps in payslips_of_interest:                
                for line in ps.line_ids.filtered(lambda l: l.code == 'IBC_SS_1'):
                    res += line.total
        return res

    def _compute_average_ibc_last_12(self):
        for record in self:
            record.average_ibc_last_12 = self.calculate_average_ibc_last_12(record)

    def calculate_average_ibc_last_12(self, current_payslip):
        res = 0
        count = 0
        # Calcula la fecha de inicio, 12 meses antes del date_from del recibo actual
        start_date = current_payslip.date_from - relativedelta(months=12)

        # Buscar los recibos de nómina de los últimos 12 meses en estado 'hecho'
        payslips_of_interest = self.env['hr.payslip'].search([
            ('employee_id', '=', current_payslip.employee_id.id),
            ('date_from', '>=', start_date),
            ('date_from', '<', current_payslip.date_from),
            ('state', '=', 'done'),
            ('id', '!=', current_payslip.id),
            ('company_id', '=', current_payslip.company_id.id),
        ],)

        # Sumar los valores de 'IBC_SS_1' y contar los recibos
        for ps in payslips_of_interest:
            for line in ps.line_ids:
                if line.code in ['IBC_SS_1','vac','vac_1','lic_rem'] :
                    res += line.total
                    count += 1 if line.code == 'IBC_SS_1' else 0
        average = res / count if count > 0 else 0
        return average

    def custom_generate_pdf(self):
        mapped_reports = self._get_pdf_reports()
        attachments_vals_list = []
        generic_name = _("Payslip")
        template = self.env.ref('hr_payroll.mail_template_new_payslip', raise_if_not_found=False)

        for report, payslips in mapped_reports.items():
            for payslip in payslips:
                try:
                    pdf_content, dummy = self.env['ir.actions.report'].sudo().with_context(lang=payslip.employee_id.address_home_id.lang)._render_qweb_pdf(report, payslip.id)
                except Exception as e:
                    raise UserError(_("Error while generating PDF: %s") % e)

                if report.print_report_name:
                    pdf_name = safe_eval(report.print_report_name, {'object': payslip})
                else:
                    pdf_name = generic_name

                attachment = self.env['ir.attachment'].sudo().create({
                    'name': pdf_name,
                    'type': 'binary',
                    'datas': base64.b64encode(pdf_content),
                    'res_model': payslip._name,
                    'res_id': payslip.id
                })

                # Send email to employees
                if template:
                    template.send_mail(payslip.id, email_values={'attachment_ids': [(4, attachment.id)]})



    # calcular 30 dias contables

    def _compute_day_360(self):
        for record in self:
            record.days_360 = self.accountable_days_year_360(record)


    def accountable_days_year_360(self,payslip):
        
        # Extraer la fecha 'date_from' y 'date_to' de 'payslip'
        date_from = payslip.employee_id.contract_id.date_start
        date_to = payslip['date_to']
        
        # Calcular los días desde el inicio del año hasta 'date_from' y 'date_to'
        if date_from.year < date_to.year:
            dias_from = 0 
        else:
            dias_from = (date_from.month - 1) * 30 + min(date_from.day - 1, 30)


        dias_to = (date_to.month - 1) * 30 + min(date_to.day, 30)

        # Calcular la diferencia de días
        dias = dias_to - dias_from

        return dias


    #pago anticipo dias no habiles 

    @api.depends('date_from', 'date_to')
    def _compute_not_avilable_days_pay(self):
        for payslip in self:
            day_from = payslip.date_from.day
            day_to = payslip.date_to.day
            
            payslip.not_avilable_days_pay = 0


            for payslip in self.filtered(lambda slip: slip.state in ['draft', 'verify']):
                # Buscar el recibo de salario anterior
                previous_payslip = self.env['hr.payslip'].search([
                    ('employee_id', '=', payslip.employee_id.id),
                    ('state', '=', 'done'),
                    ('date_to', '<', payslip.date_from),
                ], order='date_to desc', limit=1)
                
                if previous_payslip:
                    # Buscar la línea con el código "add_17" en el recibo anterior
                    add_17_line = previous_payslip.line_ids.filtered(lambda line: line.code == 'add_17')
                    
                    if add_17_line:
                        payslip.not_avilable_days_pay = add_17_line.total



    @api.depends('date_from', 'date_to')
    def _compute_anticiped_vacations_pay_prov(self):
        for payslip in self:
            day_from = payslip.date_from.day
            day_to = payslip.date_to.day
            
            payslip.anticiped_vacations_pay_prov = 0

            for payslip in self.filtered(lambda slip: slip.state in ['draft', 'verify']):
                # Buscar el recibo de salario anterior
                previous_payslip = self.env['hr.payslip'].search([
                    ('employee_id', '=', payslip.employee_id.id),
                    ('state', '=', 'done'),
                    ('date_to', '<', payslip.date_from),
                ], order='date_to desc', limit=1)
                
                if previous_payslip:
                    # Buscar la línea con el código "add_19" en el recibo anterior
                    add_10_line = previous_payslip.line_ids.filtered(lambda line: line.code == 'add_10')
                    
                    if add_10_line:
                        payslip.anticiped_vacations_pay_prov = add_10_line.total




    @api.depends('date_from', 'date_to')
    def _compute_not_avilable_days_pay_thr_mounth(self):
        for payslip in self:
            
            payslip.not_avilable_days_pay_thr_mounth = 0

            for payslip in self.filtered(lambda slip: slip.state in ['draft', 'verify']):                
                previous_payslip = self.env['hr.payslip'].search([
                    ('employee_id', '=', payslip.employee_id.id),
                    ('state', '=', 'done'),
                    ('date_to', '<', payslip.date_from),
                ], order='date_to desc', limit=1)
                
                if previous_payslip:
                    # Buscar el recibo de salario anterior al anterior
                    second_previous_payslip = self.env['hr.payslip'].search([
                        ('employee_id', '=', payslip.employee_id.id),
                        ('state', '=', 'done'),
                        ('date_to', '<', previous_payslip.date_from),
                    ], order='date_to desc', limit=1)
                    
                    if second_previous_payslip:
                        # Buscar la línea con el código "add_19" en el segundo recibo anterior
                        add_19_line = second_previous_payslip.line_ids.filtered(lambda line: line.code == 'add_19')
                        
                        if add_19_line:
                            payslip.not_avilable_days_pay_thr_mounth = add_19_line.total




    @api.depends('date_from', 'date_to')
    def _compute_anticiped_pay_thr_mounth(self):
        for payslip in self:
            
            payslip.anticiped_pay_thr_mounth = 0

            for payslip in self.filtered(lambda slip: slip.state in ['draft', 'verify']):                
                previous_payslip = self.env['hr.payslip'].search([
                    ('employee_id', '=', payslip.employee_id.id),
                    ('state', '=', 'done'),
                    ('date_to', '<', payslip.date_from),
                ], order='date_to desc', limit=1)
                
                if previous_payslip:
                    # Buscar el recibo de salario anterior al anterior
                    second_previous_payslip = self.env['hr.payslip'].search([
                        ('employee_id', '=', payslip.employee_id.id),
                        ('state', '=', 'done'),
                        ('date_to', '<', previous_payslip.date_from),
                    ], order='date_to desc', limit=1)
                    
                    if second_previous_payslip:
                        # Buscar la línea con el código "add_5" en el segundo recibo anterior
                        add_5_line = second_previous_payslip.line_ids.filtered(lambda line: line.code == 'add_5')
                        
                        if add_5_line:
                            payslip.anticiped_pay_thr_mounth = add_5_line.total




    @api.depends('date_from', 'date_to')
    def _compute_base_pro_prov(self):
        for payslip in self:
            
            payslip.base_pro_prov = 0

            for payslip in self.filtered(lambda slip: slip.state in ['draft', 'verify']):
                # Buscar el recibo de salario anterior
                previous_payslip = self.env['hr.payslip'].search([
                    ('employee_id', '=', payslip.employee_id.id),
                    ('state', '=', 'done'),
                    ('id', '!=', payslip.id),
                ], order='date_to desc', limit=1)
                
                if previous_payslip:
                    # Buscar la línea con el código "prom_prov" en el recibo anterior
                    prom_prov_line = previous_payslip.line_ids.filtered(lambda line: line.code == 'prom_prov')
                    
                    if prom_prov_line:
                        payslip.base_pro_prov = prom_prov_line.total





    @api.depends('date_from', 'date_to')
    def _compute_anticiped_vacations_pay(self):
        for payslip in self:
            day_from = payslip.date_from.day
            day_to = payslip.date_to.day
            
            payslip.anticiped_vacations_pay = 0

            if day_from == 1 and day_to == 15:
                pass
            elif day_from == 16:
                for payslip in self.filtered(lambda slip: slip.state in ['draft', 'verify']):
                    # Buscar el recibo de salario anterior
                    previous_payslip = self.env['hr.payslip'].search([
                        ('employee_id', '=', payslip.employee_id.id),
                        ('state', '=', 'done'),
                        ('date_to', '<', payslip.date_from),
                    ], order='date_to desc', limit=1)
                    
                    if previous_payslip:
                        # Buscar la línea con el código "add_9" en el recibo anterior
                        add_9_line = previous_payslip.line_ids.filtered(lambda line: line.code == 'add_9')
                        
                        if add_9_line:
                            payslip.anticiped_vacations_pay = add_9_line.total


    @api.depends('date_from', 'date_to')
    def _compute_total_income_not_wage(self):
        for payslip in self:
            day_from = payslip.date_from.day
            day_to = payslip.date_to.day
            
            payslip.total_income_not_wage = 0

            if day_from == 1 and day_to == 15:
                pass
            elif day_from == 16:
                for payslip in self.filtered(lambda slip: slip.state in ['draft', 'verify']):
                    # Buscar el recibo de salario anterior
                    previous_payslip = self.env['hr.payslip'].search([
                        ('employee_id', '=', payslip.employee_id.id),
                        ('state', '=', 'done'),
                        ('date_to', '<', payslip.date_from),
                    ], order='date_to desc', limit=1)
                    
                    if previous_payslip:
                        # Buscar la línea con el código "ingr_no_salarial" en el recibo anterior
                        ingr_no_salarial_line = previous_payslip.line_ids.filtered(lambda line: line.code == 'ingr_no_salarial')
                        
                        if ingr_no_salarial_line:
                            payslip.total_income_not_wage = ingr_no_salarial_line.total





    @api.depends('date_from', 'date_to')
    def _compute_ibc_sum_previous_month(self):
        for payslip in self:
            
            payslip.ibc_sum_previous_month = 0

            first_day_of_current_month = payslip.date_from.replace(day=1)
            last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
            first_day_of_previous_month = last_day_of_previous_month.replace(day=1)


            for payslip in self.filtered(lambda slip: slip.state in ['draft', 'verify']):
                # Buscar el recibo de salario anterior
                previous_payslip = self.env['hr.payslip'].search([
                    ('employee_id', '=', payslip.employee_id.id),
                    ('state', '=', 'done'),
                    ('date_to', '>=', first_day_of_previous_month),
                    ('date_from', '<', first_day_of_current_month),
                ], order='date_to desc', limit=1)

                if previous_payslip:
                    # Buscar la línea con el código "IBC_SS_1" en el recibo anterior
                    IBC_SS_1_line = previous_payslip.line_ids.filtered(lambda line: line.code == 'IBC_SS_1')
                    # IBC_SS_line_prev_bill = previous_payslip.ibc_previus_month
                    IBC_SS_line_prev_bill = previous_payslip.line_ids.filtered(lambda line: line.code == 'IBC_PREV_MONTH')
                    
                    if IBC_SS_1_line:
                        payslip.ibc_sum_previous_month = IBC_SS_1_line.total + IBC_SS_line_prev_bill.total



    @api.depends('date_from', 'date_to')
    def _compute_extra_time_1q(self):
        for payslip in self:
            
            payslip.extra_time_1q = 0

            for payslip in self.filtered(lambda slip: slip.state in ['draft', 'verify']):
                # Buscar el recibo de salario anterior
                previous_payslip = self.env['hr.payslip'].search([
                    ('employee_id', '=', payslip.employee_id.id),
                    ('state', '=', 'done'),
                    ('id', '!=', payslip.id),
                ], order='date_to desc', limit=1)
                
                if previous_payslip:
                    # Buscar la línea con el código "subtotal_HE_R" en el recibo anterior
                    subtotal_HE_R_line = previous_payslip.line_ids.filtered(lambda line: line.code == 'subtotal_HE_R')
                    
                    if subtotal_HE_R_line:
                        payslip.extra_time_1q = subtotal_HE_R_line.total







    @api.depends('date_from', 'date_to')
    def _compute_des_social_1q(self):
        for payslip in self:
            
            payslip.des_social_1q = 0

            for payslip in self.filtered(lambda slip: slip.state in ['draft', 'verify']):
                # Buscar el recibo de salario anterior
                previous_payslip = self.env['hr.payslip'].search([
                    ('employee_id', '=', payslip.employee_id.id),
                    ('state', '=', 'done'),
                    ('id', '!=', payslip.id),
                ], order='date_to desc', limit=1)
                
                if previous_payslip:
                    # Buscar la línea con el código "seg_1" en el recibo anterior
                    seg_1_line = previous_payslip.line_ids.filtered(lambda line: line.code == 'seg_1')
                    
                    if seg_1_line:
                        payslip.des_social_1q = seg_1_line.total


    @api.depends('date_from', 'date_to')
    def _compute_des_social_2q(self):
        for payslip in self:
            
            payslip.des_social_2q = 0

            for payslip in self.filtered(lambda slip: slip.state in ['draft', 'verify']):                
                previous_payslip = self.env['hr.payslip'].search([
                    ('employee_id', '=', payslip.employee_id.id),
                    ('state', '=', 'done'),
                    ('date_to', '<', payslip.date_from),
                ], order='date_to desc', limit=1)
                
                if previous_payslip:
                    # Buscar el recibo de salario anterior al anterior
                    second_previous_payslip = self.env['hr.payslip'].search([
                        ('employee_id', '=', payslip.employee_id.id),
                        ('state', '=', 'done'),
                        ('date_to', '<', previous_payslip.date_from),
                    ], order='date_to desc', limit=1)
                    
                    if second_previous_payslip:
                        # Buscar la línea con el código "seg_2" en el segundo recibo anterior
                        seg_2_line = second_previous_payslip.line_ids.filtered(lambda line: line.code == 'seg_2')
                        
                        if seg_2_line:
                            payslip.des_social_2q = seg_2_line.total



    @api.depends('date_from', 'date_to')
    def _compute_dias_trab_1q(self):
        for payslip in self:
            
            payslip.dias_trab_1q = 0

            for payslip in self.filtered(lambda slip: slip.state in ['draft', 'verify']):
                # Buscar el recibo de salario anterior
                previous_payslip = self.env['hr.payslip'].search([
                    ('employee_id', '=', payslip.employee_id.id),
                    ('state', '=', 'done'),
                    ('id', '!=', payslip.id),
                ], order='date_to desc', limit=1)
                
                if previous_payslip:
                    # Buscar la línea con el código "d_trab" en el recibo anterior
                    d_trab_line = previous_payslip.line_ids.filtered(lambda line: line.code == 'd_trab')
                    
                    if d_trab_line:
                        payslip.dias_trab_1q = d_trab_line.total



    @api.depends('date_from', 'date_to')
    def _compute_addh_bonification_1q(self):
        for payslip in self:
            
            payslip.addh_bonification_1q = 0

            for payslip in self.filtered(lambda slip: slip.state in ['draft', 'verify']):
                # Buscar el recibo de salario anterior
                previous_payslip = self.env['hr.payslip'].search([
                    ('employee_id', '=', payslip.employee_id.id),
                    ('state', '=', 'done'),
                    ('id', '!=', payslip.id),
                ], order='date_to desc', limit=1)
                
                if previous_payslip:
                    # Buscar la línea con el código "add_0" en el recibo anterior
                    add_0_line = previous_payslip.line_ids.filtered(lambda line: line.code == 'add_0')
                    
                    if add_0_line:
                        payslip.addh_bonification_1q = add_0_line.total




    @api.depends('date_from', 'date_to')
    def _compute_ing_salarial_add_1q(self):
        for payslip in self:
            
            payslip.ing_salarial_add_1q = 0

            for payslip in self.filtered(lambda slip: slip.state in ['draft', 'verify']):
                # Buscar el recibo de salario anterior
                previous_payslip = self.env['hr.payslip'].search([
                    ('employee_id', '=', payslip.employee_id.id),
                    ('state', '=', 'done'),
                    ('id', '!=', payslip.id),
                ], order='date_to desc', limit=1)
                
                if previous_payslip:
                    # Buscar la línea con el código "ingr_salarial_ad" en el recibo anterior
                    ingr_salarial_ad_line = previous_payslip.line_ids.filtered(lambda line: line.code == 'ingr_salarial_ad')
                    
                    if ingr_salarial_ad_line:
                        payslip.ing_salarial_add_1q = ingr_salarial_ad_line.total
