from odoo import fields, models, api, exceptions
import io
import base64
import xlwt
import xlrd
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from babel.numbers import format_currency
import locale
import xlsxwriter
locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
from dateutil.relativedelta import relativedelta
from odoo.tools import pycompat
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class HrSocialSecurity(models.Model):
    _name = 'hr.social.security'
    _description = 'Social Security'

    name = fields.Char()
    start_date_month = fields.Selection([
        ('01', 'Enero'),
        ('02', 'Febrero'),
        ('03', 'Marzo'),
        ('04', 'Abril'),
        ('05', 'Mayo'),
        ('06', 'Junio'),
        ('07', 'Julio'),
        ('08', 'Agosto'),
        ('09', 'Septiembre'),
        ('10', 'Octubre'),
        ('11', 'Noviembre'),
        ('12', 'Diciembre'),
    ], string='Mes', required=True)
    start_date_year = fields.Integer(string='', default=datetime.now().year, required=True)
    end_date_month = fields.Selection([
        ('01', 'Enero'),
        ('02', 'Febrero'),
        ('03', 'Marzo'),
        ('04', 'Abril'),
        ('05', 'Mayo'),
        ('06', 'Junio'),
        ('07', 'Julio'),
        ('08', 'Agosto'),
        ('09', 'Septiembre'),
        ('10', 'Octubre'),
        ('11', 'Noviembre'),
        ('12', 'Diciembre'),
    ], string='Mes', required=True)
    end_date_year = fields.Integer(string='Año', default=datetime.now().year, required=True)
    date_month_pension = fields.Selection([
        ('01', 'Enero'),
        ('02', 'Febrero'),
        ('03', 'Marzo'),
        ('04', 'Abril'),
        ('05', 'Mayo'),
        ('06', 'Junio'),
        ('07', 'Julio'),
        ('08', 'Agosto'),
        ('09', 'Septiembre'),
        ('10', 'Octubre'),
        ('11', 'Noviembre'),
        ('12', 'Diciembre'),
    ], string='Mes', required=True)
    date_year_pension = fields.Integer(string='', default=datetime.now().year, required=True)
    code = fields.Integer(string='Código', related = 'company_id.code_company')
    employee_arl = fields.Selection([('na','NINGUNA'),
            ('alfa','ALFA'),
            ('sura','ARL SURA'),
            ('colpatria','COLPATRIA ARP'),
            ('colsanitas','COLSANITAS ARL'),
            ('fondo', 'FONDO DE RIESGOS LABORALES'),
            ('equidad', 'LA EQUIDAD SEGUROS'),
            ('mapfre', 'MAPFRE COLOMBIA VIDA SEGUROS S.A'),
            ('positiva', 'POSITIVA COMPAÑIA DE SEGUROS'),
            ('bolivar', 'SEGUROS BOLIVAR'),
            ('aurora', 'SEGUROS DE VIDA AURORA'),], string="Adm.Riesgos", required = True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company.id)
    company_name = fields.Char(string='Nombre Sucursal', related='company_id.company_name')
    porcent_other = fields.Char(string='Porcentaje', default='4,00%')
    porcent_16 = fields.Char(string='Porcentaje', default='16,00%')
    porcent_1 = fields.Char(string='Porcentaje', default='1,00%')
    porcent_2 = fields.Char(string='Porcentaje', default='2,00%')
    porcent_3 = fields.Char(string='Porcentaje', default='3,00%')
    porcent_12 = fields.Char(string='Porcentaje', default='12,5%')

    def generate_social_report(self):
        if not self.company_id:
            raise UserError("Por favor, seleccione una compañía.")

        domain = [('company_id', '=', self.company_id.id)]
        social_records = self.env['hr.social.security'].search(domain)

        if not social_records:
            raise UserError("No se encontraron registros para esta compañía.")

        wb = xlwt.Workbook()
        title = 'Liquidaciones'
        ws = wb.add_sheet(title, cell_overwrite_ok=True)
        style_calibri_11 = xlwt.easyxf('font: name Calibri, height 220;')
        company_name = self.company_id.name
        identification_document = self.company_id.company_registry
        company_logo = self.company_id.logo
        pension_date = str(self.end_date_year) + "-" + self.end_date_month
        next_month = int(self.end_date_month) + 1

        if next_month == 13:
            next_month = 1

        next_month_formatted = str(next_month).zfill(2)
        health_date = str(self.end_date_year) + "-" + next_month_formatted
        code = self.code
        name = self.company_name
        arl = self.employee_arl
        arl_label = dict(self.env['hr.social.security']._fields['employee_arl'].selection).get(arl)

        style_other = xlwt.easyxf('align: horiz left; borders: top thin, bottom thin, left thin, right thin;')
        style_other_lines = xlwt.easyxf('align: horiz center; borders: top thin, bottom thin, left thin, right thin; font: color-index gray25;')
        style_line = xlwt.easyxf('pattern: pattern solid, fore_colour 0x15;'
                                 'font: bold on, color white; align: horiz center;'
                                 'borders: top thin, bottom thin, left thin, right thin;')
        style_line_header = xlwt.easyxf(
            'pattern: pattern solid, fore_colour 0x15;'  # Cambiar el color del fondo
            'font: bold on, color white; align: horiz left;'  # Fuente en negrita, color blanco, alineado a la izquierda
            'borders: top thin, bottom thin, left thin, right thin;'  # Bordes delgados
        )
        style_company = xlwt.easyxf('font: height 180')

        ws.write_merge(6, 6, 0, 10, "Datos Generales de la Liquidación", style_other)
        ws.write_merge(7,7, 0,2, "Periodo",style_line)
        ws.write(7, 3, "Tipo",style_line)
        ws.write_merge(7,7, 4, 5, "Planilla Asociada",style_line)
        ws.write_merge(7,7,6,7, "Sucursal",style_line)
        ws.write_merge(7,7, 8,9, "Tipo",style_line)
        ws.write(7, 10, "Administradora",style_line)
        ws.write_merge(8,8, 0,1, "Pensión",style_line)
        ws.write(8, 2, "Salud",style_line)
        ws.write(8, 3, "Planilla",style_line)
        ws.write(8, 4, "Fecha",style_line)
        ws.write(8, 5, "Clave",style_line)
        ws.write(8, 6, "Código",style_line)
        ws.write(8, 7, "Nombre",style_line)
        ws.write_merge(8,8, 8,9, "Aportante",style_line)
        ws.write(8, 10, "Riesgos", style_line)
        ws.write_merge(9,9, 0,1, pension_date,style_other)
        ws.write(9, 2, health_date,style_other)
        ws.write(9, 3, "E",style_other)
        ws.write(9, 4, " ",style_other)
        ws.write(9, 5, " ",style_other)
        ws.write(9, 6, code,style_other)
        ws.write(9, 7, name,style_other)
        ws.write_merge(9,9, 8,9, "EMPLEADOR",style_other)
        ws.write(9, 10, arl_label,style_other)
        ws.write_merge(11, 11, 0, 6, "Datos Generales de Pago", style_other)
        ws.write_merge(12,12 ,0,1, "Clave", style_line)
        ws.write_merge(12,12,2,3, "Fecha", style_line)
        ws.write_merge(12,12,4,6, "Pago", style_line)
        ws.write(13, 0, "Pago", style_line)
        ws.write(13, 1, "Planilla", style_line)
        ws.write(13, 2, "Límite", style_line)
        ws.write(13, 3, "Pago", style_line)
        ws.write(13, 4, "Banco", style_line)
        ws.write(13, 5, "Días Mora", style_line)
        ws.write(13, 6, "Valor", style_line)
        ws.write(14, 0, " ", style_other)
        ws.write(14, 1, " ", style_other)
        ws.write(14, 2, " ", style_other)
        ws.write(14, 3, " ", style_other)
        ws.write(14, 4, " ", style_other)
        ws.write(14, 5, " ", style_other)
        ws.write(14, 6, " ", style_other)
        ws.write_merge(16, 16, 0, 14, "Empleado", style_other_lines)
        ws.write_merge(16, 16, 15, 45, "Novedades", style_other_lines)
        ws.write_merge(16, 16, 46, 48, "Salario", style_other_lines)
        ws.write_merge(16, 16, 49, 61, "Pensión", style_other_lines)
        ws.write_merge(16, 16, 62, 72, "Salud", style_other_lines)
        ws.write_merge(16, 16, 73, 80, "Riesgos", style_other_lines)
        ws.write_merge(16, 16, 81, 95, "Parafiscales", style_other_lines)
        ws.write_merge(16, 16, 96, 97, "Cotizante de UPC Adicional", style_other_lines)

        #ENCABEZADOS
        headers = ["No.", "Tipo ID", "No ID", "Primer Apellido", "Segundo Apellido", "Primer Nombre", "Segundo Nombre",
                   "Departamento", "Ciudad",
                   "Tipo de Cotizante", "Subtipo de Cotizante", "Horas Laboradas", "Extranjero",
                   "Residente en el Exterior", "Fecha Radicación en el Exterior",
                   "ING", "Fecha ING", "RET", "Fecha RET", "TDE", "TAE", "TDP", "TAP", "VSP", "Fecha VSP", "VST", "SLN",
                   "Inicio SLN", "Fin SLN", "IGE", "Inicio IGE", "Fin IGE", "LMA",
                   "Inicio LMA", "Fin LMA", "VAC-LR", "Inicio VAC-LR", "Fin VAC-LR", "AVP", "VCT", "Inicio VCT",
                   "Fin VCT", "IRL", "Inicio IRL", "Fin IRL", "Correcciones","Salario Mensual($)","Salario Integral"," Salario Variable","Administradora","Días","IBC",
                   "Tarifa","Valor Cotización","Indicador Alto Riesgo","Cotización Voluntaria Afiliado","Cotización Voluntaria Empleador","Fondo Solidaridad Pensional",
                   "Fondo Subsistencia","Valor no Retenido","Total","AFP Destino","Administradora","Días","IBC","Tarifa","Valor Cotización","Valor UPC",
                   "N° Autorización Incapacidad EG","Valor Incapacidad EG","N° Autorización LMA","Valor Licencia Maternidad","EPS Destino",
                   "Administradora","Días","IBC","Tarifa","Clase","Centro de Trabajo","Actividad Económica","Valor Cotización",
                   "Días","Administradora CCF","IBC CCF","Tarifa CCF","Valor Cotización CCF","IBC Otros Parafiscales","Tarifa SENA",
                   "Valor Cotización SENA","Tarifa ICBF","Valor Cotización ICBF","Tarifa ESAP","Valor Cotización ESAP","Tarifa MEN",
                   "Valor Cotización MEN","Exonerado parafiscales y salud","Tipo ID","N° ID"]
        for col_num, header in enumerate(headers):
            ws.write(17, col_num, header, style_line_header)


        line_number = 1
        row_num = 18
        start_date = datetime(self.start_date_year, int(self.start_date_month), 1)
        end_date = datetime(self.end_date_year, int(self.end_date_month), 1) + relativedelta(months=1, days=-1)
        contracts = self.env['hr.contract'].sudo().search([
            '|', '|',
            ('date_end', '>=', start_date),  # Contratos que finalizan después de start_date
            ('date_end', '<=', end_date),  # Contratos que finalizan antes de end_date
            ('state', '=', 'open')  # Contratos activos
        ])

        employee_ids = contracts.mapped('employee_id.id')
        employees = self.env['hr.employee'].sudo().browse(employee_ids)

        for employee in employees:
            partner = employee.address_id
            leaves = self.env['hr.leave'].sudo().search([('employee_id', '=', employee.id), ('state', '=', 'validate'),('employee_company_id', '=', self.env.company.id)])
            contract = self.env['hr.contract'].sudo().search([('employee_id', '=', employee.id), ('state', '=', 'open'),('company_id', '=', self.env.company.id)])
            contract_end = self.env['hr.contract'].sudo().search(
                [
                    ('employee_id', '=', employee.id),
                    ('state', '=', 'close'),
                    ('company_id', '=', self.env.company.id)
                ],
                order='date_end desc',
                limit=1
            )
            department_name = dict(employee._fields['department'].selection).get(employee.department)
            city_name = dict(employee._fields['type_city'].selection).get(employee.type_city)
            type_iden_name = dict(employee._fields['type_iden'].selection).get(employee.type_iden)
            admin_ccf_name = dict(employee._fields['admin_ccf'].selection).get(employee.admin_ccf)
            types_contributor_name = dict(employee._fields['types_contributor'].selection).get(employee.types_contributor)
            type_sub_iden_name = dict(employee._fields['type_sub_iden'].selection).get(employee.type_sub_iden)
            colom_foreign_name = dict(employee._fields['colom_foreign'].selection).get(employee.colom_foreign)
            foreign_name = dict(employee._fields['foreign'].selection).get(employee.foreign)
            type_admin_name = dict(employee._fields['type_admin'].selection).get(employee.type_admin)
            admin_risk_name = dict(employee._fields['admin_risk'].selection).get(employee.admin_risk)
            risk_indicator_name = dict(employee._fields['risk_indicator'].selection).get(employee.risk_indicator)
            fee_salary_name = dict(employee._fields['fee_salary'].selection).get(employee.fee_salary)
            comprehensive_salary_name = dict(contract._fields['comprehensive_salary'].selection).get(contract.comprehensive_salary)
            comprehensive_salary_other = dict(contract_end._fields['comprehensive_salary'].selection).get(contract_end.comprehensive_salary)
            variable_salary_name = dict(contract._fields['variable_salary'].selection).get(contract.variable_salary)
            types_admin_name = dict(employee._fields['types_admin'].selection).get(employee.types_admin)
            payslip = self.env['hr.payslip'].sudo().search([
                ('employee_id', '=', employee.id),
                ('date_from', '>=', start_date),
                ('date_to', '<=', end_date)
                , ('company_id', '=', self.env.company.id)
            ])
            style_percent =xlwt.easyxf(num_format_str='0.00%')
            style_number = xlwt.easyxf(num_format_str='0.00')

            porcent_4 = 3.99999991059303 / 100
            porcent_16 = 15.9999996423721 / 100
            porcent_1 = 1.04400003328919 / 100
            porcent_2 = 1.99999995529652 / 100
            porcent_3 = 2.99999993294477 / 100

            text_style = xlwt.XFStyle()  # Crear un estilo nvo
            text_style.num_format_str = '@'  # Establecer el formato de número como texto
            ws.write(row_num, 0, line_number)
            ws.write(row_num, 1, type_iden_name or '', text_style)
            style_money = xlwt.easyxf("align: horiz right", num_format_str='0')
            ws.write(row_num, 2, employee.identification_id or '')
            ws.write(row_num, 3, partner.lastname or '',text_style)
            ws.write(row_num, 4, partner.lastname2 or '',text_style)
            ws.write(row_num, 5, partner.firstname or '',text_style)
            ws.write(row_num, 6, partner.othernames or '',text_style)
            ws.write(row_num, 7, department_name or '',text_style)
            ws.write(row_num, 8, city_name or '',text_style)
            ws.write(row_num, 9, types_contributor_name or '')
            ws.write(row_num, 10, type_sub_iden_name or '')
            ws.write(row_num, 12, colom_foreign_name or '')
            ws.write(row_num, 13, foreign_name or '')
            ws.write(row_num, 14, employee.foreign_date.strftime('%Y-%m-%d') if employee.foreign_date else '')
            if contract and contract.date_start and start_date.date() <= contract.date_start <= end_date.date():
                ws.write(row_num, 15, 'Todos los sistemas (ARL, AFP, CCF, EPS)')
                ws.write(row_num, 16, contract.date_start.strftime('%Y-%m-%d'))
            else:
                ws.write(row_num, 15, 'NO')
                ws.write(row_num, 16, '')
            if contract_end and contract_end.date_end and start_date.date() <= contract_end.date_end <= end_date.date():
                ws.write(row_num, 17, 'Todos los sistemas (ARL, AFP, CCF, EPS)')
                ws.write(row_num, 18, contract_end.date_end.strftime('%Y-%m-%d'))

            else:
                ws.write(row_num, 17, 'NO')
                ws.write(row_num, 18, '')
            ws.write(row_num, 19, 'NO')
            ws.write(row_num, 20, 'NO')
            ws.write(row_num, 21, 'NO')
            ws.write(row_num, 22, 'NO')
            ws.write(row_num, 23, 'NO')
            ws.write(row_num, 24, '')
            ws.write(row_num, 26, 'NO')
            ws.write(row_num, 29, 'NO')
            ws.write(row_num, 32, 'NO')
            ws.write(row_num, 35, 'NO')
            ws.write(row_num, 38, 'NO')
            ws.write(row_num, 39, 'NO')
            ws.write(row_num, 42,  '', style_money)
            ws.write(row_num, 45, 'NO')
            if contract_end.date_end:
                num_contract = round(contract.custom_wage)
                ws.write(row_num, 47, comprehensive_salary_other or '')
            else:
                num_contract = round(contract.custom_wage)
            ws.write(row_num, 46, num_contract,style_money or '')
            ws.write(row_num, 47, comprehensive_salary_name or '')
            ws.write(row_num, 48, variable_salary_name or '')
            if employee.types_contributor in ('f', 'b'):
                ws.write(row_num, 47, '', style_money)
                ws.write(row_num, 48, '', style_money)
            ws.write(row_num, 48, variable_salary_name or '')
            ws.write(row_num, 49, type_admin_name or '')
            work100_line = payslip.line_ids.filtered(lambda x: x.salary_rule_id.code == 'd_trab')
            if work100_line:
                total_number_of_days_work100 = sum(work100_line.amount for work100_line in work100_line)
                total_days = round(7.6667 * total_number_of_days_work100, 2)
                rounded_total_days = int(total_days)
                ws.write(row_num, 11, rounded_total_days or '')
                ws.write(row_num, 50, total_number_of_days_work100 or '')
                if employee.types_contributor in ('f', 'b'):
                    ws.write(row_num, 50, '')
                ws.write(row_num, 63, total_number_of_days_work100 or '')
                ws.write(row_num, 74, total_number_of_days_work100 or '')
                if employee.types_contributor == 'b':
                    ws.write(row_num, 74, '')
                ws.write(row_num, 81, total_number_of_days_work100 or '')
                if employee.types_contributor in ('f', 'b'):
                    ws.write(row_num, 81, '')

            ibc_ss_1_amount = 0.0
            ibc_parafiscal_amount_na = 0.0
            ibc_parafiscal_amount_other = 0.0
            total_ibc = 0.0
            found_ibc_ss_1 = False
            found_learner = False
            found_ibc_parafiscal_na = False
            learner_amount = 0.0
            total_learner = 0.0
            found_cant = False
            learner_cant = 0.0
            total_cant = 0.0

            if payslip:
                for line in payslip.line_ids:
                    if line.code == 'IBC_parafiscal':
                        found_ibc_parafiscal_na = True
                        ibc_parafiscal_amount_na += line.amount
                        subtotal_ibc_parafiscal = ibc_parafiscal_amount_other / 30
                        total_ibc_parafiscal_na = subtotal_ibc_parafiscal * total_number_of_days_work100
                    if line.code == 'IBC_ARL':
                        found_ibc_ss_1 = True
                        ibc_ss_1_amount += line.amount
                        subtotal_ibc = ibc_ss_1_amount / 30
                        total_ibc = subtotal_ibc * total_number_of_days_work100
                    if line.code == 'IBC_SS_2':
                        found_learner = True
                        learner_amount += line.amount
                        subtotal_learner = ibc_ss_1_amount / 30
                        total_learner = subtotal_learner * total_number_of_days_work100
                    if line.code == 'ded_15':
                        found_cant = True
                        learner_cant += line.amount
                        subtotal_cant = ibc_ss_1_amount / 30
                        total_cant = subtotal_cant * total_number_of_days_work100
                ws.write(row_num, 54, risk_indicator_name)
                ws.write(row_num, 25, 'NO')
                if found_ibc_ss_1:
                    num_ibc = round(ibc_ss_1_amount)
                    if employee.types_contributor in ('f', 'b'):
                        ws.write(row_num, 51, '', style_money)
                        ws.write(row_num, 52, '', style_number)
                        ws.write(row_num, 25, 'NO')
                    else:
                        ws.write(row_num, 51, num_ibc, style_money)
                        ws.write(row_num, 52, 0.16, style_number)
                        if num_ibc > num_contract:
                            ws.write(row_num, 25, 'SI')

                if found_learner:
                    if employee.types_contributor in ('f', 'b'):
                        leaner = round(learner_amount)
                        ws.write(row_num, 64, leaner, style_money or '')
                    else:
                        ws.write(row_num, 64, num_ibc, style_money or '')
                if ibc_parafiscal_amount_na > self.company_id.salary_min * 10:
                    fee_salary_total = ibc_ss_1_amount * 0.125
                    rounded_fee_salary_total = round(fee_salary_total)
                    last_three_digits = rounded_fee_salary_total % 100

                    if '01' <= str(last_three_digits) <= '50':
                        rounded_fee_salary_total = round(fee_salary_total, -2) + 100
                    elif str(last_three_digits) > '50':
                        rounded_fee_salary_total = round(fee_salary_total, -2)
                    else:
                        pass

                    if rounded_fee_salary_total != '':
                        rounded_fee_salary_total = int(rounded_fee_salary_total)

                    ws.write(row_num, 66, rounded_fee_salary_total, style_money)
                    ws.write(row_num, 65, 0.125)

                else:
                    if employee.types_contributor in ('f', 'b'):
                        fee_salary_total = learner_amount * 0.125
                        rounded_fee_salary_total = round(fee_salary_total)

                        last_three_digits = rounded_fee_salary_total % 100

                        if '01' <= str(last_three_digits) <= '50':
                            rounded_fee_salary_total = round(fee_salary_total, -2) + 100
                        elif str(last_three_digits) > '50':
                            rounded_fee_salary_total = round(fee_salary_total, -2)
                        else:
                            pass

                        if rounded_fee_salary_total != '':
                            rounded_fee_salary_total = int(rounded_fee_salary_total)
                        last_three_digits = rounded_fee_salary_total % 1000
                        ws.write(row_num, 65, 0.125)
                        ws.write(row_num, 66, rounded_fee_salary_total, style_money)
                    else:
                        # Calcular fee_salary_total
                        fee_salary_total = ibc_ss_1_amount * 0.04

                        rounded_fee_salary_total = round(fee_salary_total)

                        last_three_digits = rounded_fee_salary_total % 100

                        if '01' <= str(last_three_digits) <= '50':
                            rounded_fee_salary_total = round(fee_salary_total, -2) + 100
                        elif str(last_three_digits) > '50':
                            rounded_fee_salary_total = round(fee_salary_total, -2)
                        else:
                            pass

                        if rounded_fee_salary_total != '':
                            rounded_fee_salary_total = int(rounded_fee_salary_total)

                        ws.write(row_num, 66, rounded_fee_salary_total, style_money)
                        ws.write(row_num, 65, 0.04, style_number)
            else:
                ws.write(row_num, 65, '', style_number)
                ws.write(row_num, 66, '', style_money)

            if learner_amount != 0:
                if employee.types_contributor in ('f', 'b'):
                    ws.write(row_num, 53, '', style_money)
                else:
                    price = num_ibc * 0.16
                    rounded_price = round(price)
                    last_three_digits = rounded_price % 100

                    if '01' <= str(last_three_digits) <= '50':
                        rounded_price = round(price, -2) + 100
                    elif str(last_three_digits) > '50':
                        rounded_price = round(price, -2)
                    else:
                        pass

                    if rounded_price != '':
                        rounded_price = int(rounded_price)

                    ws.write(row_num, 53, rounded_price, style_money or '')

            else:
                ws.write(row_num, 53, '', style_money)
                ws.write(row_num, 54, risk_indicator_name)
                ws.write(row_num, 55,  '', style_money)
                ws.write(row_num, 56, '', style_money)
            found_ded_7 = False

            ded_7_amount = 0.0
            subtotal_ded_7 = 0.0

            if payslip:
                found_ded_7 = False
                for line in payslip.line_ids:
                    if line.code == 'ded_1':
                        found_ded_7 = True
                        ded_7_amount += line.amount

                if found_ded_7:
                    subtotal_ded_7 = (num_ibc * 0.01) / 2
                    rounded_ded_7 = round(subtotal_ded_7, -2)
                    last_three_digits = rounded_ded_7 % 1000
                    if 000 <= last_three_digits <= 100:
                        if subtotal_ded_7 % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                            rounded_ded_7 += 100
                    elif last_three_digits > 100:  # Si los últimos tres dígitos están entre 000 y 099, no hacemos nada
                        if subtotal_ded_7 % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                            rounded_ded_7 += 100

                    ws.write(row_num, 57, rounded_ded_7 or '', style_money)
                    ws.write(row_num, 58, rounded_ded_7 or '', style_money)
                    price_total = (rounded_price + (rounded_ded_7 * 2))
                    ws.write(row_num, 60, price_total, style_money or '')
                    if employee.types_contributor in ('f', 'b'):
                        ws.write(row_num, 60, '', style_money)
                    else:
                        ws.write(row_num, 60, price_total, style_money or '')
                else:
                    price_total = (rounded_price)
                    ws.write(row_num, 60, price_total, style_money or '')

            ws.write(row_num, 61, 'NINGUNA')
            ws.write(row_num, 62, types_admin_name)
            ws.write(row_num, 67, ' ',style_money)
            ws.write(row_num, 69, ' ',style_money)
            ws.write(row_num, 71, ' ',style_money)
            ws.write(row_num, 72, 'NINGUNA')
            ws.write(row_num, 73, admin_risk_name)
            ibc_arl_amount = 0.0
            total_ibc_arl = 0.0
            found_ibc_arl = False

            if payslip:
                for line in payslip.line_ids:
                    if line.code == 'IBC_ARL':
                        found_ibc_arl = True
                        ibc_arl_amount += line.amount
                        subtotal_ibc_arl = ibc_arl_amount / 30
                        total_ibc_arl = subtotal_ibc_arl * total_number_of_days_work100

                if found_ibc_arl:
                    if employee.types_contributor == 'b':
                        ws.write(row_num, 75, '', style_money)
                        ws.write(row_num, 76, '', style_number)
                        ws.write(row_num, 77, '')
                    else:
                        num_ibc_arl = round(ibc_arl_amount)
                        ws.write(row_num, 75, num_ibc_arl, style_money or '')
            style_percent_contributor = xlwt.easyxf(num_format_str='0.00%')
            if employee.risk_classes_type == 'na':
                ws.write(row_num, 80, '', style_money)
            if employee.risk_classes_type == 'risk1':
                ws.write(row_num, 76, 0.00522, style_number)
                ws.write(row_num, 77, 1)
                if ibc_arl_amount != 0:
                    risk_total = ibc_arl_amount * 0.00522
                    rounded_risk_total = round(risk_total, -2)
                    last_three_digits = rounded_risk_total % 1000
                    if 000 <= last_three_digits <= 100:
                         if risk_total % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                            rounded_risk_total += 100
                    elif last_three_digits > 100:  # Si los últimos tres dígitos están entre 000 y 099, no hacemos nada
                        if risk_total % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                            rounded_risk_total += 100
                    ws.write(row_num, 80, rounded_risk_total, style_money)
                else:
                    ws.write(row_num, 80, '', style_money)
            elif employee.risk_classes_type == 'risk2':
                ws.write(row_num, 76, 0.01044, style_number)
                ws.write(row_num, 77, 2)
                if ibc_arl_amount != 0:
                    risk_total = ibc_arl_amount * 0.01044
                    rounded_risk_total = round(risk_total, -2)
                    last_three_digits = rounded_risk_total % 1000
                    if 000 <= last_three_digits <= 100:
                        if risk_total % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                            rounded_risk_total += 100
                    elif last_three_digits > 100:  # Si los últimos tres dígitos están entre 000 y 099, no hacemos nada
                        if risk_total % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                            rounded_risk_total += 100
                    ws.write(row_num, 80, rounded_risk_total, style_money)
                else:
                    ws.write(row_num, 80, '', style_money)
            elif employee.risk_classes_type == 'risk3':
                ws.write(row_num, 76, 0.02436, style_number)
                ws.write(row_num, 77, 3)
                if ibc_arl_amount != 0:
                    risk_total = round(ibc_arl_amount * 0.02436, -2) + 100
                    ws.write(row_num, 80, risk_total, style_money)
                else:
                    ws.write(row_num, 80, '', style_money)
            elif employee.risk_classes_type == 'risk4':
                ws.write(row_num, 76, 0.04350, style_number)
                ws.write(row_num, 77, 4)
                if ibc_arl_amount != 0:
                    risk_total = round(ibc_arl_amount * 0.04350, -2) + 100
                    ws.write(row_num, 80, risk_total, style_money)
                else:
                    ws.write(row_num, 80, '', style_money)
            elif employee.risk_classes_type == 'risk5':
                ws.write(row_num, 76, 0.06960, style_number)
                ws.write(row_num, 77, 5)
                if ibc_arl_amount != 0:
                    risk_total = round(ibc_arl_amount * 0.06960, -2) + 100
                    ws.write(row_num, 80, risk_total, style_money)
                else:
                    ws.write(row_num, 80, '', style_money)
            else:
                ws.write(row_num, 76, '', style_number)
                ws.write(row_num, 77, '')
            ws.write(row_num, 78, employee.center_work_2 or '')
            ws.write(row_num, 79, employee.economic_activity or '')
            ws.write(row_num, 82,admin_ccf_name or '')
            ibc_parafiscal_amount = 0.0
            total_ibc_parafiscal = 0.0
            found_ibc_parafiscal = False

            if payslip:
                for line in payslip.line_ids:
                    if line.code == 'IBC_ARL':
                        found_ibc_parafiscal = True
                        ibc_parafiscal_amount += line.amount
                        subtotal_ibc_parafiscal = ibc_parafiscal_amount / 30
                        total_ibc_parafiscal = subtotal_ibc_parafiscal * total_number_of_days_work100

                if found_ibc_parafiscal:
                    if employee.types_contributor in ('f', 'b'):
                        ws.write(row_num, 83, '')
                    else:
                        round_parafiscal = round(total_ibc_parafiscal)
                        ws.write(row_num, 83, round_parafiscal, style_money or '')


            ws.write(row_num, 85, '', style_money)
            ws.write(row_num, 84, '', style_number)
            if ibc_parafiscal_amount:
                if employee.types_contributor in ('f', 'b'):
                    ws.write(row_num, 85, '', style_money)
                    ws.write(row_num, 84, '', style_number)
                else:
                    ws.write(row_num, 84, 0.04,style_number)
                    fee = round_parafiscal * 0.04
                    rounded_fee = round(fee, -2)
                    last_three_digits = rounded_fee % 1000

                    # Redondear al siguiente múltiplo de 100 y sumar 100 si los últimos tres dígitos están entre 100 y 999
                    if 000 <= last_three_digits <= 100:
                        if fee % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                            rounded_fee += 100
                    elif last_three_digits > 100:  # Si los últimos tres dígitos están entre 000 y 099, no hacemos nada
                        if fee % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                            rounded_fee += 100
                    ws.write(row_num, 85, rounded_fee, style_money or '')
            ws.write(row_num, 95, 'SI')
            if employee.types_contributor in ('f', 'b'):
                ws.write(row_num, 95, 'N')
            ibc_parafiscal_amount_other = 0.0
            ibc_parafiscal_2 = 0.0
            total_ibc_parafiscal_other = 0.0
            found_ibc_parafiscal_other = False

            if payslip:
                for line in payslip.line_ids:
                    if line.code == 'IBC_parafiscal':
                        found_ibc_parafiscal_other = True
                        ibc_parafiscal_amount_other += line.amount
                        subtotal_ibc_parafiscal = ibc_parafiscal_amount_other / 30
                        total_ibc_parafiscal_other = subtotal_ibc_parafiscal * total_number_of_days_work100
                    if line.code == 'IBC_parafiscales2':
                        found_ibc_parafiscal_other = True
                        ibc_parafiscal_2 += line.amount
                        subtotal_ibc_parafiscal_2 = ibc_parafiscal_amount_other / 30
                        total_ibc_ibc_parafiscal_2 = subtotal_ibc_parafiscal * total_number_of_days_work100
                    if found_ibc_parafiscal_other:
                        if ibc_parafiscal_amount_other > self.company_id.salary_min * 10:
                            ws.write(row_num, 86, ibc_parafiscal_2, style_money or '')
                            ws.write(row_num, 87, 0.02,style_number)
                            sena = ibc_parafiscal_2 * 0.02
                            rounded_sena = round(sena, -2)
                            last_three_digits = rounded_sena % 1000

                            # Redondear al siguiente múltiplo de 100 y sumar 100 si los últimos tres dígitos están entre 100 y 999
                            if 000 <= last_three_digits <= 100:
                                if sena % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                    rounded_sena += 100
                            elif last_three_digits > 100:  # Si los últimos tres dígitos están entre 000 y 099, no hacemos nada
                                if sena % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                    rounded_sena += 100
                            ws.write(row_num, 88, rounded_sena, style_money)
                            ws.write(row_num, 89, 0.03,style_number)
                            icbf = ibc_parafiscal_2 * 0.03
                            rounded_icbf = round(icbf, -2)
                            last_three_digits = rounded_icbf % 1000

                            # Redondear al siguiente múltiplo de 100 y sumar 100 si los últimos tres dígitos están entre 100 y 999
                            if 000 <= last_three_digits <= 100:
                                if icbf % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                    rounded_icbf += 100
                            elif last_three_digits > 100:  # Si los últimos tres dígitos están entre 000 y 099, no hacemos nada
                                if icbf % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                    rounded_icbf += 100
                            ws.write(row_num, 90, rounded_icbf, style_money)
                            ws.write(row_num, 95, 'NO')
                        else:
                            ws.write(row_num, 86, '', style_money)
                            ws.write(row_num, 87, '', style_number)
                            ws.write(row_num, 88, '', style_money)
                            ws.write(row_num, 89, '', style_number)
                            ws.write(row_num, 90, 000000, style_money)
                    else:
                        ws.write(row_num, 86, '', style_money)
                        ws.write(row_num, 87, '', style_number)
                        ws.write(row_num, 88, '', style_money)
                        ws.write(row_num, 89, '', style_number)
                        ws.write(row_num, 90, 000000, style_money)
                row_num += 1
                line_number += 1

            for leave in leaves:
                if leave.date_from and start_date <= leave.date_from <= end_date:
                    if leave.holiday_status_id.type_security == 'leave2':
                        ws.write(row_num, 0, line_number)
                        ws.write(row_num, 1, type_iden_name or '')
                        ws.write(row_num, 2, employee.identification_id or '')
                        ws.write(row_num, 3, partner.lastname or '')
                        ws.write(row_num, 4, partner.lastname2 or '')
                        ws.write(row_num, 5, partner.firstname or '')
                        ws.write(row_num, 6, partner.othernames or '')
                        ws.write(row_num, 7, department_name or '')
                        ws.write(row_num, 8, city_name or '')
                        ws.write(row_num, 9, types_contributor_name or '')
                        ws.write(row_num, 10, type_sub_iden_name or '')
                        ws.write(row_num, 11,  0, style_money)
                        ws.write(row_num, 12, colom_foreign_name or '')
                        ws.write(row_num, 13, employee.foreign_date.strftime('%Y-%m-%d') if employee.foreign_date else '')
                        ws.write(row_num, 14, '' )
                        ws.write(row_num, 15, 'NO')
                        ws.write(row_num, 16, '')
                        ws.write(row_num, 17, 'NO')
                        ws.write(row_num, 18, '')
                        ws.write(row_num, 19, 'NO')
                        ws.write(row_num, 20, 'NO')
                        ws.write(row_num, 21, 'NO')
                        ws.write(row_num, 22, 'NO')
                        ws.write(row_num, 23, 'NO')
                        ws.write(row_num, 24, '')
                        ws.write(row_num, 25, 'NO')
                        ws.write(row_num, 26, 'LICENCIA NO REMUNERADA')
                        ws.write(row_num, 27, leave.date_from.strftime('%Y-%m-%d'),style_money)
                        ws.write(row_num, 28, leave.date_to.strftime('%Y-%m-%d'), style_money)
                        ws.write(row_num, 29, 'NO')
                        ws.write(row_num, 32, 'NO')
                        ws.write(row_num, 35, 'NO')
                        ws.write(row_num, 38, 'NO')
                        ws.write(row_num, 39, 'NO')
                        ws.write(row_num, 42,  '', style_money)
                        ws.write(row_num, 45, 'NO')
                        num_contract = round(contract.custom_wage)
                        ws.write(row_num, 46, num_contract, style_money or '')
                        ws.write(row_num, 47, comprehensive_salary_name or '')
                        ws.write(row_num, 48, variable_salary_name or '')
                        ws.write(row_num, 49, type_admin_name or '')
                        days = int(leave.duration_display.split()[0])
                        ws.write(row_num, 50, days or '')

                        ibc_ss_1_amount = 0.0
                        total_ibc = 0.0
                        found_ibc_ss_1 = False

                        if payslip:
                            ibc_ss_1_amount_set = set()  # Conjunto para almacenar valores únicos
                            for line in payslip.line_ids:
                                if line.code == 'BASIC' and line.amount not in ibc_ss_1_amount_set:
                                    found_ibc_ss_1 = True
                                    ibc_ss_1_amount_set.add(line.amount)  # Agrega el valor al conjunto
                                    ibc_ss_1_amount += line.amount
                                    subtotal_ibc = ibc_ss_1_amount / 30
                                    total_ibc = round(subtotal_ibc * days)

                            if found_ibc_ss_1:
                                ws.write(row_num, 51, total_ibc, style_money or '')
                                ws.write(row_num, 64, total_ibc, style_money or '')
                                ws.write(row_num, 75, total_ibc, style_money or '')
                                ws.write(row_num, 83, total_ibc, style_money or '')
                        ws.write(row_num, 52, 0.16,style_number)
                        price = total_ibc * 0.16

                        # Redondear al múltiplo de 100 más cercano
                        rounded_price = round(price)

                        # Obtener los últimos tres dígitos del precio
                        last_three_digits = rounded_price % 100

                        # Redondear al siguiente múltiplo de 100 y sumar 100 si los últimos tres dígitos están entre 001 y 100
                        if '01' <= str(last_three_digits) <= '50':
                            rounded_price = round(price, -2) + 100
                        elif str(last_three_digits) > '50':
                            rounded_price = round(price, -2)
                        else:
                            pass

                        if rounded_price != '':
                            rounded_price = int(rounded_price)

                        # Escribir en la celda correspondiente en tu archivo de Excel
                        ws.write(row_num, 53, rounded_price, style_money or '')
                        ws.write(row_num, 54, risk_indicator_name)
                        ws.write(row_num, 55, '', style_money)
                        ws.write(row_num, 56,  '', style_money)

                        ded_7_amount = 0.0
                        subtotal_ded_7 = 0.0
                        found_ded_7 = False

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'ded_7':
                                    found_ded_7 = True
                                    ded_7_amount += line.amount

                        if found_ded_7:
                            subtotal_ded_7 = round(total_ibc * 0.01) / 2
                            rounded_ded_7 = round(subtotal_ded_7, -2)
                            last_three_digits = rounded_ded_7 % 1000
                            if 000 <= last_three_digits <= 100:
                                if subtotal_ded_7 % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                    rounded_ded_7 += 100
                            elif last_three_digits > 100:  # Si los últimos tres dígitos están entre 000 y 099, no hacemos nada
                                if subtotal_ded_7 % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                    rounded_ded_7 += 100
                            ws.write(row_num, 57, rounded_ded_7, style_money)
                            ws.write(row_num, 58, rounded_ded_7, style_money)
                        else:
                            ws.write(row_num, 57, '', style_money)
                            ws.write(row_num, 58, '', style_money)


                        ws.write(row_num, 59, '',style_money)
                        # for fila in range(18, row_num):
                        #     numero_fila = fila + 1
                        #     formula_suma = f'SUM(BB{numero_fila};BE{numero_fila})'
                        #     ws.write(fila, 60, xlwt.Formula(formula_suma), style_money)
                        ws.write(row_num, 61, 'NINGUNA')
                        ws.write(row_num, 62, types_admin_name)
                        ws.write(row_num, 63, days or '')
                        ws.write(row_num, 65, 0.0, style_number)
                        ws.write(row_num, 66, '')
                        ws.write(row_num, 67, '', style_money)
                        ws.write(row_num, 69, '', style_money)
                        ws.write(row_num, 71, '', style_money)
                        ws.write(row_num, 72, 'NINGUNA')
                        ws.write(row_num, 73, admin_risk_name)
                        ws.write(row_num, 74, days or '')
                        ibc_arl_amount = 0.0
                        total_ibc_arl = 0.0
                        found_ibc_arl = False

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'IBC_ARL':
                                    found_ibc_arl = True
                                    ibc_arl_amount += line.amount
                                    subtotal_ibc_arl = ibc_arl_amount / 30
                                    total_ibc_arl = subtotal_ibc_arl * days

                        if employee.risk_classes_type == 'risk1':
                            ws.write(row_num, 76, 0.0, style_number)
                            ws.write(row_num, 77, 1)
                            risk_total = round(total_ibc_arl * 0.522)
                            ws.write(row_num, 80, ' ', style_money)
                        elif employee.risk_classes_type == 'risk2':
                            ws.write(row_num, 76, 0.0, style_number)
                            ws.write(row_num, 77, 2)
                            risk_total = round(total_ibc_arl * 1.044)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk3':
                            ws.write(row_num, 76, 0.0, style_number)
                            ws.write(row_num, 77, 3)
                            risk_total = round(total_ibc_arl * 2.436)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk4':
                            ws.write(row_num, 76, 0.0, style_number)
                            ws.write(row_num, 77, 4)
                            risk_total = round(total_ibc_arl * 4.350)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk5':
                            ws.write(row_num, 76, 0.0, style_number)
                            ws.write(row_num, 77, 5)
                            risk_total = round(total_ibc_arl * 6.960)
                            ws.write(row_num, 80, '', style_money)
                        else:
                            ws.write(row_num, 76, 0, style_number)
                            ws.write(row_num, 77, '')

                        ws.write(row_num, 79, employee.economic_activity or '')
                        ws.write(row_num, 81, days or '')
                        ws.write(row_num, 82, admin_ccf_name or '')
                        ibc_parafiscal_amount = 0.0
                        total_ibc_parafiscal = 0.0
                        found_ibc_parafiscal = False

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'IBC_SS_11':
                                    found_ibc_parafiscal = True
                                    ibc_parafiscal_amount += line.amount
                                    subtotal_ibc_parafiscal = ibc_parafiscal_amount / 30
                                    total_ibc_parafiscal = subtotal_ibc_parafiscal * total_number_of_days_work100

                        ws.write(row_num, 85, '', style_money)
                        ws.write(row_num, 84, '', style_number)

                        ibc_parafiscal_amount_other = 0.0
                        total_ibc_parafiscal_other = 0.0
                        found_ibc_parafiscal_other = False

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'IBC_parafiscal':
                                    found_ibc_parafiscal_other = True
                                    ibc_parafiscal_amount_other += line.amount
                                    subtotal_ibc_parafiscal = ibc_parafiscal_amount_other / 30
                                    total_ibc_parafiscal_other = subtotal_ibc_parafiscal * total_number_of_days_work100
                                if found_ibc_parafiscal_other:
                                    if ibc_parafiscal_amount_other > self.company_id.salary_min * 10:
                                        ws.write(row_num, 86, ibc_parafiscal_amount_other, style_money or '')
                                        ws.write(row_num, 87, 0.02,style_number)
                                        sena = ibc_parafiscal_amount_other * 0.02
                                        rounded_sena = round(sena, -2)
                                        last_three_digits = rounded_sena % 1000

                                        # Redondear al siguiente múltiplo de 100 y sumar 100 si los últimos tres dígitos están entre 100 y 999
                                        if 000 <= last_three_digits <= 100:
                                            if sena % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                                rounded_sena += 100
                                        elif last_three_digits > 100:  # Si los últimos tres dígitos están entre 000 y 099, no hacemos nada
                                            if sena % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                                rounded_sena += 100
                                        ws.write(row_num, 88, '', style_money)
                                        ws.write(row_num, 89, '', style_number)

                                        ws.write(row_num, 90, '', style_money)
                                    else:
                                        ws.write(row_num, 86, '', style_money)
                                        ws.write(row_num, 87, '', style_number)
                                        ws.write(row_num, 88, '', style_money)
                                        ws.write(row_num, 89, '', style_number)
                                        ws.write(row_num, 90, '', style_money)

                            ws.write(row_num, 91, 0, style_percent)
                            ws.write(row_num, 92, '', style_money)
                            ws.write(row_num, 93, 0, style_percent)
                            ws.write(row_num, 94, '', style_money)
                            ws.write(row_num, 95, 'SI')

                        row_num += 1
                        line_number += 1
    #INCAPACIDADES
                    if leave.holiday_status_id.type_security == 'leave3':
                        ws.write(row_num, 0, line_number)
                        ws.write(row_num, 1, type_iden_name or '')
                        ws.write(row_num, 2, employee.identification_id or '')
                        ws.write(row_num, 3, partner.lastname or '')
                        ws.write(row_num, 4, partner.lastname2 or '')
                        ws.write(row_num, 5, partner.firstname or '')
                        ws.write(row_num, 6, partner.othernames or '')
                        ws.write(row_num, 7, department_name or '')
                        ws.write(row_num, 8, city_name or '')
                        ws.write(row_num, 9, types_contributor_name or '')
                        ws.write(row_num, 10, type_sub_iden_name or '')
                        ws.write(row_num, 11, 0, style_money)
                        ws.write(row_num, 12, colom_foreign_name or '')
                        ws.write(row_num, 13, foreign_name or '')
                        ws.write(row_num, 14,
                                 employee.foreign_date.strftime('%Y-%m-%d') if employee.foreign_date else '')
                        ws.write(row_num, 15, 'NO')
                        ws.write(row_num, 16, '')
                        ws.write(row_num, 17, 'NO')
                        ws.write(row_num, 18, '')
                        ws.write(row_num, 19, 'NO')
                        ws.write(row_num, 20, 'NO')
                        ws.write(row_num, 21, 'NO')
                        ws.write(row_num, 22, 'NO')
                        ws.write(row_num, 23, 'NO')
                        ws.write(row_num, 24, '')
                        ws.write(row_num, 25, 'NO')
                        ws.write(row_num, 26, 'NO')
                        ws.write(row_num, 29, 'SI')
                        ws.write(row_num, 30, leave.date_from.strftime('%Y-%m-%d'))
                        ws.write(row_num, 31, leave.date_to.strftime('%Y-%m-%d'))
                        ws.write(row_num, 32, 'NO')
                        ws.write(row_num, 35, 'NO')
                        ws.write(row_num, 36, '')
                        ws.write(row_num, 37, '')
                        ws.write(row_num, 38, 'NO')
                        ws.write(row_num, 39, 'NO')
                        ws.write(row_num, 42, '', style_money)
                        ws.write(row_num, 45, 'NO')
                        rounded_contract= round(contract.custom_wage)
                        ws.write(row_num, 46, rounded_contract, style_money or '')
                        ws.write(row_num, 47, comprehensive_salary_name or '')
                        ws.write(row_num, 48, variable_salary_name or '')
                        ws.write(row_num, 49, type_admin_name or '')
                        days = int(leave.duration_display.split()[0])
                        ws.write(row_num, 50, days or '')

                        if contract.custom_wage == self.company_id.salary_min:
                            ibc_ss = (contract.custom_wage / 30) * days
                            round_ibc_ss = round(ibc_ss)
                        else:
                            ibc_ss = (contract.custom_wage / 30) * days * 0.6667
                            round_ibc_ss = round(ibc_ss)

                        ws.write(row_num, 51, round_ibc_ss, style_money or '')
                        ws.write(row_num, 64, round_ibc_ss, style_money or '')
                        ws.write(row_num, 75, round_ibc_ss, style_money or '')
                        ws.write(row_num, 83, round_ibc_ss, style_money or '')
                        found_cant = False
                        learner_cant = 0.0
                        total_cant = 0.0

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'ded_15':
                                    found_cant = True
                                    learner_cant += line.amount
                                    subtotal_cant = ibc_ss_1_amount / 30
                                    total_cant = subtotal_cant * total_number_of_days_work100
                        if round_ibc_ss:
                            if round_ibc_ss > self.company_id.salary_min * 10 or learner_cant > 10.00:
                                fee_salary_total = round_ibc_ss * 0.125
                                rounded_fee_salary_total = round(fee_salary_total)

                                last_three_digits = rounded_fee_salary_total % 100

                                if '01' <= str(last_three_digits) <= '50':
                                    rounded_fee_salary_total = round(fee_salary_total, -2) + 100
                                elif str(last_three_digits) > '50':
                                    rounded_fee_salary_total = round(fee_salary_total, -2)
                                else:
                                    pass

                                if rounded_fee_salary_total != '':
                                    rounded_fee_salary_total = int(rounded_fee_salary_total)

                                ws.write(row_num, 66, rounded_fee_salary_total, style_money)
                                ws.write(row_num, 65, 0.125)
                            else:
                                fee_salary_total = round_ibc_ss * 0.04

                                rounded_fee_salary_total = round(fee_salary_total)

                                last_three_digits = rounded_fee_salary_total % 100

                                if '01' <= str(last_three_digits) <= '50':
                                    rounded_fee_salary_total = round(fee_salary_total, -2) + 100
                                elif str(last_three_digits) > '50':
                                    rounded_fee_salary_total = round(fee_salary_total, -2)
                                else:
                                    pass

                                if rounded_fee_salary_total != '':
                                    rounded_fee_salary_total = int(rounded_fee_salary_total)
                                ws.write(row_num, 66, rounded_fee_salary_total, style_money)
                                ws.write(row_num, 65, 0.04)
                        else:
                            ws.write(row_num, 65, '', style_number)
                            ws.write(row_num, 66, '', style_money)
                        ws.write(row_num, 52, 0.16, style_number)
                        price = round_ibc_ss * 0.16

                        # Redondear al múltiplo de 100 más cercano
                        rounded_price = round(price)

                        # Obtener los últimos tres dígitos del precio
                        last_three_digits = rounded_price % 100

                        # Redondear al siguiente múltiplo de 100 y sumar 100 si los últimos tres dígitos están entre 001 y 100
                        if '01' <= str(last_three_digits) <= '50':
                            rounded_price = round(price, -2) + 100
                        elif str(last_three_digits) > '50':
                            rounded_price = round(price, -2)
                        else:
                            pass

                        if rounded_price != '':
                            rounded_price = int(rounded_price)

                        # Escribir en la celda correspondiente en tu archivo de Excel
                        ws.write(row_num, 53, rounded_price, style_money or '')
                        ws.write(row_num, 54, risk_indicator_name or '')
                        ws.write(row_num, 55, '', style_money)
                        ws.write(row_num, 56, '', style_money)
                        ded_7_amount = 0.0
                        subtotal_ded_7 = 0.0
                        found_ded_7 = False

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'ded_1':
                                    found_ded_7 = True
                                    ded_7_amount += line.amount

                        if found_ded_7:
                            subtotal_ded_7 = round(round_ibc_ss * 0.01 / 2)
                            rounded_ded_7 = round(subtotal_ded_7, -2)
                            last_three_digits = rounded_ded_7 % 1000
                            if 000 <= last_three_digits <= 100:
                                if subtotal_ded_7 % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                    rounded_ded_7 += 100
                            elif last_three_digits > 100:  # Si los últimos tres dígitos están entre 000 y 099, no hacemos nada
                                if subtotal_ded_7 % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                    rounded_ded_7 += 100
                            ws.write(row_num, 57, rounded_ded_7, style_money)
                            ws.write(row_num, 58, rounded_ded_7, style_money)
                            price_total = round(rounded_price + (rounded_ded_7 * 2))
                            ws.write(row_num, 60, price_total, style_money or '')
                        else:
                            ws.write(row_num, 57, '', style_money)
                            ws.write(row_num, 58, '', style_money)



                        ws.write(row_num, 59, '', style_money)
                        ws.write(row_num, 61, 'NINGUNA')
                        ws.write(row_num, 62, types_admin_name)
                        ws.write(row_num, 63, days or '')

                        ws.write(row_num, 67, '', style_money)
                        ws.write(row_num, 69, '', style_money)
                        ws.write(row_num, 71, '', style_money)
                        ws.write(row_num, 72, 'NINGUNA')
                        ws.write(row_num, 73, admin_risk_name)
                        ws.write(row_num, 74, days or '')
                        ibc_arl_amount = 0.0
                        total_ibc_arl = 0.0
                        found_ibc_arl = False
                        if payslip:
                            for line in payslip.line_ids:
                                if line.code in ('inc_gen', 'inc_genp1', 'inc_gen_2', 'inc_gen_P2'):
                                    found_ibc_arl = True
                                    ibc_arl_amount += line.amount
                                    subtotal_ibc_arl = ibc_arl_amount / 30
                                    total_ibc_arl = subtotal_ibc_arl * days

                        round_amount = round(total_ibc_arl)

                        if employee.risk_classes_type == 'risk1':
                            ws.write(row_num, 76, 0.0, style_number)
                            ws.write(row_num, 77, 1)
                            risk_total = round(total_ibc_arl * 0.522)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk2':
                            ws.write(row_num, 76, 0.0, style_number)
                            ws.write(row_num, 77, 2)
                            risk_total = round(total_ibc_arl * 1.044)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk3':
                            ws.write(row_num, 76, 0.0, style_number)
                            ws.write(row_num, 77, 3)
                            risk_total = round(total_ibc_arl * 2.436)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk4':
                            ws.write(row_num, 76, 0.0, style_percent)
                            ws.write(row_num, 77, 4)
                            risk_total = round(total_ibc_arl * 4.350)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk5':
                            ws.write(row_num, 76, 0.0, style_percent)
                            ws.write(row_num, 77, 5)
                            risk_total = round(total_ibc_arl * 6.960)
                            ws.write(row_num, 80, '', style_money)
                        else:
                            ws.write(row_num, 76, 0, style_percent)
                            ws.write(row_num, 77, '')

                        ws.write(row_num, 79, employee.economic_activity or '')
                        ws.write(row_num, 81, days or '')
                        ws.write(row_num, 82, admin_ccf_name or '')
                        ibc_parafiscal_amount = 0.0
                        total_ibc_parafiscal = 0.0
                        found_ibc_parafiscal = False

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'IBC_parafiscal':
                                    found_ibc_parafiscal = True
                                    ibc_parafiscal_amount += line.amount
                                    subtotal_ibc_parafiscal = ibc_parafiscal_amount / 30
                                    total_ibc_parafiscal = subtotal_ibc_parafiscal * days
                        ws.write(row_num, 86, '', style_money)
                        ws.write(row_num, 87, 0.0, style_number)
                        ws.write(row_num, 88, '', style_money)
                        ws.write(row_num, 89, '', style_number)
                        ws.write(row_num, 90, '', style_money)
                        ws.write(row_num, 95, 'SI')
                        if found_ibc_parafiscal:
                            if ibc_parafiscal_amount > self.company_id.salary_min * 10:
                                ws.write(row_num, 95, 'N')

                        #         ws.write(row_num, 86, ibc_parafiscal_amount, style_money or '')
                        #         ws.write(row_num, 87, self.porcent_2)
                        #         sena = ibc_parafiscal_amount * 0.02
                        #         rounded_sena = round(sena, -2)
                        #         last_three_digits = rounded_sena % 1000
                        #
                        #         # Redondear al siguiente múltiplo de 100 y sumar 100 si los últimos tres dígitos están entre 100 y 999
                        #         if 000 <= last_three_digits <= 100:
                        #             if sena % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                        #                 rounded_sena += 100
                        #         elif last_three_digits > 100:  # Si los últimos tres dígitos están entre 000 y 099, no hacemos nada
                        #             if sena % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                        #                 rounded_sena += 100
                        #         ws.write(row_num, 88, '', style_money)
                        #         ws.write(row_num, 89, '', style_percent)
                        #
                        #         ws.write(row_num, 90, '', style_money)
                        # else:

                        ws.write(row_num, 84, 0.0, style_number)
                        ws.write(row_num, 85, '', style_money)
                        # ws.write(row_num, 84, 0.04,style_number)
                        # fee = round_ibc_ss * 0.04
                        # rounded_fee = round(fee, -2)
                        # last_three_digits = rounded_fee % 1000
                        #
                        # # Redondear al siguiente múltiplo de 100 y sumar 100 si los últimos tres dígitos están entre 100 y 999
                        # if 000 <= last_three_digits <= 100:
                        #     if fee % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                        #         rounded_fee += 100
                        # elif last_three_digits > 100:  # Si los últimos tres dígitos están entre 000 y 099, no hacemos nada
                        #     if fee % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                        #         rounded_fee += 100
                        # ws.write(row_num, 85, rounded_fee, style_money or '')

                        ws.write(row_num, 91, 0.00, style_percent)
                        ws.write(row_num, 92, '', style_money)
                        ws.write(row_num, 93, 0.00, style_percent)
                        ws.write(row_num, 94, '', style_money)

                        row_num += 1
                        line_number += 1

                    #*************************************************
                    if leave.holiday_status_id.type_security == 'leave1':
                        ws.write(row_num, 0, line_number)
                        ws.write(row_num, 1, type_iden_name or '')
                        ws.write(row_num, 2, employee.identification_id or '')
                        ws.write(row_num, 3, partner.lastname or '')
                        ws.write(row_num, 4, partner.lastname2 or '')
                        ws.write(row_num, 5, partner.firstname or '')
                        ws.write(row_num, 6, partner.othernames or '')
                        ws.write(row_num, 7, department_name or '')
                        ws.write(row_num, 8, city_name or '')
                        ws.write(row_num, 9, types_contributor_name or '')
                        ws.write(row_num, 10, type_sub_iden_name or '')
                        ws.write(row_num, 11, 0, style_money)
                        ws.write(row_num, 12, colom_foreign_name or '')
                        ws.write(row_num, 13, foreign_name or '')
                        ws.write(row_num, 14, employee.foreign_date.strftime('%Y-%m-%d') if employee.foreign_date else '')
                        ws.write(row_num, 15, 'NO')
                        ws.write(row_num, 16, '')
                        ws.write(row_num, 17, 'NO')
                        ws.write(row_num, 18, '')
                        ws.write(row_num, 19, 'NO')
                        ws.write(row_num, 20, 'NO')
                        ws.write(row_num, 21, 'NO')
                        ws.write(row_num, 22, 'NO')
                        ws.write(row_num, 23, 'NO')
                        ws.write(row_num, 24, '')
                        ws.write(row_num, 25, 'NO')
                        ws.write(row_num, 26, 'NO')
                        ws.write(row_num, 29, 'NO')
                        ws.write(row_num, 32, 'NO')
                        ws.write(row_num, 35, 'VACACIONES')
                        ws.write(row_num, 36, leave.date_from.strftime('%Y-%m-%d'))
                        ws.write(row_num, 37, leave.date_to.strftime('%Y-%m-%d'))
                        ws.write(row_num, 38, 'NO')
                        ws.write(row_num, 39, 'NO')
                        ws.write(row_num, 42, '', style_money)
                        ws.write(row_num, 45, 'NO')
                        num_contract = round(contract.custom_wage)
                        ws.write(row_num, 46, num_contract,style_money or '')
                        ws.write(row_num, 47, comprehensive_salary_name or '')
                        ws.write(row_num, 48, variable_salary_name or '')
                        ws.write(row_num, 49, type_admin_name or '')
                        days = int(leave.duration_display.split()[0])
                        ws.write(row_num, 50, days or '')

                        ibc_ss_1_amount = 0.0
                        total_ibc = 0.0
                        found_ibc_ss_1 = False

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'prom_prov':
                                    found_ibc_ss_1 = True
                                    ibc_ss_1_amount = line.amount
                                    subtotal_ibc = ibc_ss_1_amount / 30
                                    total_ibc = subtotal_ibc * days

                            if found_ibc_ss_1:
                                ibc_amount = round(total_ibc)
                                ws.write(row_num, 51, ibc_amount, style_money or '')
                                ws.write(row_num, 64, ibc_amount, style_money or '')
                                ws.write(row_num, 75, ibc_amount, style_money or '')

                        if ibc_ss_1_amount != 0:
                            if ibc_amount > self.company_id.salary_min * 10:
                                ws.write(row_num, 65, 0.125,style_number)
                                fee_salary_total = round(ibc_amount * 0.125)
                                rounded_fee_salary_total = round(fee_salary_total)

                                last_three_digits = rounded_fee_salary_total % 100

                                if '01' <= str(last_three_digits) <= '50':
                                    rounded_fee_salary_total = round(fee_salary_total, -2) + 100
                                elif str(last_three_digits) > '50':
                                    rounded_fee_salary_total = round(fee_salary_total, -2)
                                else:
                                    pass

                                if rounded_fee_salary_total != '':
                                    rounded_fee_salary_total = int(rounded_fee_salary_total)
                                ws.write(row_num, 66, fee_salary_total, style_money)
                            else:
                                fee_salary_total = ibc_amount * 0.04

                                rounded_fee_salary_total = round(fee_salary_total)

                                last_three_digits = rounded_fee_salary_total % 100

                                if '01' <= str(last_three_digits) <= '50':
                                    rounded_fee_salary_total = round(fee_salary_total, -2) + 100
                                elif str(last_three_digits) > '50':
                                    rounded_fee_salary_total = round(fee_salary_total, -2)
                                else:
                                    pass

                                if rounded_fee_salary_total != '':
                                    rounded_fee_salary_total = int(rounded_fee_salary_total)
                                ws.write(row_num, 65, 0.04,style_number)
                                ws.write(row_num, 66, rounded_fee_salary_total, style_money)
                        else:
                            ws.write(row_num, 65, '', style_percent)
                            ws.write(row_num, 66, '', style_money)
                        ws.write(row_num, 52, 0.16,style_number)
                        price = ibc_amount * 0.16

                        # Redondear al múltiplo de 100 más cercano
                        rounded_price = round(price)

                        # Obtener los últimos tres dígitos del precio
                        last_three_digits = rounded_price % 100

                        # Redondear al siguiente múltiplo de 100 y sumar 100 si los últimos tres dígitos están entre 001 y 100
                        if '01' <= str(last_three_digits) <= '50':
                            rounded_price = round(price, -2) + 100
                        elif str(last_three_digits) > '50':
                            rounded_price = round(price, -2)
                        else:
                            pass

                        if rounded_price != '':
                            rounded_price = int(rounded_price)

                        # Escribir en la celda correspondiente en tu archivo de Excel
                        ws.write(row_num, 53, rounded_price, style_money or '')
                        ws.write(row_num, 54, risk_indicator_name or '')
                        ws.write(row_num, 55, '', style_money)
                        ws.write(row_num, 56, '', style_money)
                        ded_7_amount = 0.0
                        subtotal_ded_7 = 0.0
                        found_ded_7 = False

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'ded_1':
                                    found_ded_7 = True
                                    ded_7_amount += line.amount

                            if found_ded_7:
                                subtotal_ded_7 = round(ibc_amount * 0.01) / 2
                                rounded_ded_7 = round(subtotal_ded_7, -2)
                                last_three_digits = rounded_ded_7 % 1000
                                if 000 <= last_three_digits <= 100:
                                    if subtotal_ded_7 % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                        rounded_ded_7 += 100
                                elif last_three_digits > 100:  # Si los últimos tres dígitos están entre 000 y 099, no hacemos nada
                                    if subtotal_ded_7 % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                        rounded_ded_7 += 100
                                ws.write(row_num, 57, rounded_ded_7, style_money or '')
                                ws.write(row_num, 58, rounded_ded_7, style_money or '')
                            else:
                                subtotal_ded_7 = ''

                        ws.write(row_num, 59, '',style_money)
                        ws.write(row_num, 60, rounded_price, style_money)
                        ws.write(row_num, 61, 'NINGUNA')
                        ws.write(row_num, 62, types_admin_name)
                        ws.write(row_num, 63, days or '')

                        ws.write(row_num, 67, '', style_money)
                        ws.write(row_num, 69, '', style_money)
                        ws.write(row_num, 71, '', style_money)
                        ws.write(row_num, 72, 'NINGUNA')
                        ws.write(row_num, 73, admin_risk_name)
                        ws.write(row_num, 74, days or '')
                        ibc_arl_amount = 0.0
                        total_ibc_arl = 0.0
                        found_ibc_arl = False
                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'prom_prov':
                                    found_ibc_arl = True
                                    ibc_arl_amount += line.amount
                                    subtotal_ibc_arl = ibc_arl_amount / 30
                                    total_ibc_arl = subtotal_ibc_arl * days

                        round_amount = round(total_ibc_arl)


                        if employee.risk_classes_type == 'risk1':
                            ws.write(row_num, 76, 0.0, style_percent)
                            ws.write(row_num, 77, 1)
                            risk_total = round(total_ibc_arl * 0.522)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk2':
                            ws.write(row_num, 76, 0.0, style_percent)
                            ws.write(row_num, 77, 2)
                            risk_total = round(total_ibc_arl * 1.044)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk3':
                            ws.write(row_num, 76, 0.0, style_percent)
                            ws.write(row_num, 77, 3)
                            risk_total = round(total_ibc_arl * 2.436)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk4':
                            ws.write(row_num, 76, 0.0, style_percent)
                            ws.write(row_num, 77, 4)
                            risk_total = round(total_ibc_arl * 4.350)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk5':
                            ws.write(row_num, 76, 0.0, style_percent)
                            ws.write(row_num, 77, 5)
                            risk_total = round(total_ibc_arl * 6.960)
                            ws.write(row_num, 80, '', style_money)
                        else:
                            ws.write(row_num, 76, 0, style_percent)
                            ws.write(row_num, 77, '')

                        ws.write(row_num, 79, employee.economic_activity or '')
                        ws.write(row_num, 81, days or '')
                        ws.write(row_num, 82, admin_ccf_name or '')
                        ibc_parafiscal_amount = 0.0
                        total_ibc_parafiscal = 0.0
                        found_ibc_parafiscal = False

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'prom_prov':
                                    found_ibc_parafiscal = True
                                    ibc_parafiscal_amount += line.amount
                                    subtotal_ibc_parafiscal = ibc_parafiscal_amount / 30
                                    total_ibc_parafiscal = subtotal_ibc_parafiscal * days

                            if found_ibc_parafiscal:
                                round_parafiscal = round(total_ibc_parafiscal)
                                ws.write(row_num, 83, round_parafiscal, style_money or '')

                        ws.write(row_num, 84, '', style_number)
                        ws.write(row_num, 85, '', style_money)
                        if ibc_parafiscal_amount:
                            ws.write(row_num, 84, 0.04)
                            fee = total_ibc_parafiscal * 0.04
                            rounded_fee = round(fee, -2)
                            last_three_digits = rounded_fee % 1000

                            # Redondear al siguiente múltiplo de 100 y sumar 100 si los últimos tres dígitos están entre 100 y 999
                            if 000 <= last_three_digits <= 100:
                                if fee % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                    rounded_fee += 100
                            elif last_three_digits > 100:  # Si los últimos tres dígitos están entre 000 y 099, no hacemos nada
                                if fee % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                    rounded_fee += 100
                            ws.write(row_num, 85, rounded_fee, style_money or '')
                        ibc_parafiscal_amount_other = 0.0
                        total_ibc_parafiscal_other = 0.0
                        found_ibc_parafiscal_other = False

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'IBC_parafiscal':
                                    found_ibc_parafiscal_other = True
                                    ibc_parafiscal_amount_other += line.amount
                                    subtotal_ibc_parafiscal = ibc_parafiscal_amount_other / 30
                                    total_ibc_parafiscal_other = subtotal_ibc_parafiscal * total_number_of_days_work100
                                if found_ibc_parafiscal_other:
                                    if ibc_parafiscal_amount_other > self.company_id.salary_min * 10:
                                        round_parafiscal_other = round(ibc_parafiscal_amount_other)
                                        ws.write(row_num, 86, round_parafiscal_other, style_money or '')
                                        ws.write(row_num, 87, 0.02,style_number)
                                        sena = ibc_parafiscal_amount_other * 0.02
                                        rounded_sena = round(sena, -2)
                                        last_three_digits = rounded_sena % 1000

                                        # Redondear al siguiente múltiplo de 100 y sumar 100 si los últimos tres dígitos están entre 100 y 999
                                        if 000 <= last_three_digits <= 100:
                                            if sena % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                                rounded_sena += 100
                                        elif last_three_digits > 100:  # Si los últimos tres dígitos están entre 000 y 099, no hacemos nada
                                            if sena % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                                rounded_sena += 100
                                        ws.write(row_num, 88, '', style_money)
                                        ws.write(row_num, 89, '', style_number)

                                        ws.write(row_num, 90, '', style_money)
                                    else:
                                        ws.write(row_num, 86, '', style_money)
                                        ws.write(row_num, 87, '', style_number)
                                        ws.write(row_num, 88, '', style_money)
                                        ws.write(row_num, 89, '', style_number)
                                        ws.write(row_num, 90, '', style_money)

                            ws.write(row_num, 91, 0.00, style_percent)
                            ws.write(row_num, 92, '', style_money)
                            ws.write(row_num, 93, 0.00, style_percent)
                            ws.write(row_num, 94, '', style_money)
                            ws.write(row_num, 95, 'SI' or '')

                        row_num += 1
                        line_number += 1

#**********************************************************************************************************
                    if leave.holiday_status_id.type_security == 'leave6':
                        ws.write(row_num, 0, line_number)
                        ws.write(row_num, 1, type_iden_name or '')
                        ws.write(row_num, 2, employee.identification_id or '')
                        ws.write(row_num, 3, partner.lastname or '')
                        ws.write(row_num, 4, partner.lastname2 or '')
                        ws.write(row_num, 5, partner.firstname or '')
                        ws.write(row_num, 6, partner.othernames or '')
                        ws.write(row_num, 7, department_name or '')
                        ws.write(row_num, 8, city_name or '')
                        ws.write(row_num, 9, types_contributor_name or '')
                        ws.write(row_num, 10, type_sub_iden_name or '')
                        ws.write(row_num, 11, 0, style_money)
                        ws.write(row_num, 12, colom_foreign_name or '')
                        ws.write(row_num, 13, foreign_name or '')
                        ws.write(row_num, 14,
                                 employee.foreign_date.strftime('%Y-%m-%d') if employee.foreign_date else '')
                        ws.write(row_num, 15, 'NO')
                        ws.write(row_num, 16, '')
                        ws.write(row_num, 17, 'NO')
                        ws.write(row_num, 18, '')
                        ws.write(row_num, 19, 'NO')
                        ws.write(row_num, 20, 'NO')
                        ws.write(row_num, 21, 'NO')
                        ws.write(row_num, 22, 'NO')
                        ws.write(row_num, 23, 'NO')
                        ws.write(row_num, 24, '')
                        ws.write(row_num, 25, 'NO')
                        ws.write(row_num, 26, 'NO')
                        ws.write(row_num, 29, 'NO')
                        ws.write(row_num, 32, 'NO')
                        ws.write(row_num, 35, 'LICENCIA REMUNERADA')
                        ws.write(row_num, 36, leave.date_from.strftime('%Y-%m-%d'))
                        ws.write(row_num, 37, leave.date_to.strftime('%Y-%m-%d'))
                        ws.write(row_num, 38, 'NO')
                        ws.write(row_num, 39, 'NO')
                        ws.write(row_num, 42, '', style_money)
                        ws.write(row_num, 45, 'NO')
                        num_contract = round(contract.custom_wage)
                        ws.write(row_num, 46, num_contract, style_money or '')
                        ws.write(row_num, 47, comprehensive_salary_name or '')
                        ws.write(row_num, 48, variable_salary_name or '')
                        ws.write(row_num, 49, type_admin_name or '')
                        days = int(leave.duration_display.split()[0])
                        ws.write(row_num, 50, days or '')

                        ibc_ss_1_amount = 0.0
                        total_ibc = 0.0
                        found_ibc_ss_1 = False

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'BASIC':
                                    found_ibc_ss_1 = True
                                    ibc_ss_1_amount = line.amount
                                    subtotal_ibc = ibc_ss_1_amount / 30
                                    total_ibc = subtotal_ibc * days

                            if found_ibc_ss_1:
                                ibc_amount = round(total_ibc)
                                ws.write(row_num, 51, ibc_amount, style_money or '')
                                ws.write(row_num, 64, ibc_amount, style_money or '')
                                ws.write(row_num, 75, ibc_amount, style_money or '')

                        if ibc_ss_1_amount != 0:
                            if ibc_amount > self.company_id.salary_min * 10:
                                ws.write(row_num, 65, 0.125,style_number)
                                fee_salary_total = round(ibc_amount * 0.125)
                                rounded_fee_salary_total = round(fee_salary_total)

                                last_three_digits = rounded_fee_salary_total % 100

                                if '01' <= str(last_three_digits) <= '50':
                                    rounded_fee_salary_total = round(fee_salary_total, -2) + 100
                                elif str(last_three_digits) > '50':
                                    rounded_fee_salary_total = round(fee_salary_total, -2)
                                else:
                                    pass
                                if rounded_fee_salary_total != '':
                                    rounded_fee_salary_total = int(rounded_fee_salary_total)
                                ws.write(row_num, 66, fee_salary_total, style_money)
                            else:
                                fee_salary_total = ibc_amount * 0.04

                                rounded_fee_salary_total = round(fee_salary_total)

                                last_three_digits = rounded_fee_salary_total % 100

                                if '01' <= str(last_three_digits) <= '50':
                                    rounded_fee_salary_total = round(fee_salary_total, -2) + 100
                                elif str(last_three_digits) > '50':
                                    rounded_fee_salary_total = round(fee_salary_total, -2)
                                else:
                                    pass
                                if rounded_fee_salary_total != '':
                                    rounded_fee_salary_total = int(rounded_fee_salary_total)
                                ws.write(row_num, 65, 0.04, style_number)
                                ws.write(row_num, 66, rounded_fee_salary_total, style_money)
                        else:
                            ws.write(row_num, 65, '', style_percent)
                            ws.write(row_num, 66, '', style_money)
                        ws.write(row_num, 52, 0.16, style_number)
                        price = ibc_amount * 0.16

                        # Redondear al múltiplo de 100 más cercano
                        rounded_price = round(price)

                        # Obtener los últimos tres dígitos del precio
                        last_three_digits = rounded_price % 100

                        # Redondear al siguiente múltiplo de 100 y sumar 100 si los últimos tres dígitos están entre 001 y 100
                        if '01' <= str(last_three_digits) <= '50':
                            rounded_price = round(price, -2) + 100
                        elif str(last_three_digits) > '50':
                            rounded_price = round(price, -2)
                        else:
                            pass

                        if rounded_price != '':
                            rounded_price = int(rounded_price)

                        # Escribir en la celda correspondiente en tu archivo de Excel
                        ws.write(row_num, 53, rounded_price, style_money or '')
                        ws.write(row_num, 54, risk_indicator_name or '')
                        ws.write(row_num, 55, '', style_money)
                        ws.write(row_num, 56, '', style_money)
                        ded_7_amount = 0.0
                        subtotal_ded_7 = 0.0
                        found_ded_7 = False

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'ded_1':
                                    found_ded_7 = True
                                    ded_7_amount += line.amount

                            if found_ded_7:
                                subtotal_ded_7= round(ibc_amount * 0.01) / 2
                                rounded_ded_7 = round(subtotal_ded_7, -2)
                                last_three_digits = rounded_ded_7 % 1000
                                if 000 <= last_three_digits <= 100:
                                    if subtotal_ded_7 % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                        rounded_ded_7 += 100
                                elif last_three_digits > 100:  # Si los últimos tres dígitos están entre 000 y 099, no hacemos nada
                                    if subtotal_ded_7 % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                        rounded_ded_7 += 100
                                ws.write(row_num, 57, rounded_ded_7, style_money or '')
                                ws.write(row_num, 58, rounded_ded_7, style_money or '')
                            else:
                                subtotal_ded_7 = ''


                        ws.write(row_num, 59, '', style_money)
                        ws.write(row_num, 60, rounded_price, style_money)
                        ws.write(row_num, 61, 'NINGUNA')
                        ws.write(row_num, 62, types_admin_name)
                        ws.write(row_num, 63, days or '')

                        ws.write(row_num, 67, '', style_money)
                        ws.write(row_num, 69, '', style_money)
                        ws.write(row_num, 71, '', style_money)
                        ws.write(row_num, 72, 'NINGUNA')
                        ws.write(row_num, 73, admin_risk_name)
                        ws.write(row_num, 74, days or '')
                        ibc_arl_amount = 0.0
                        total_ibc_arl = 0.0
                        found_ibc_arl = False
                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'BASIC':
                                    found_ibc_arl = True
                                    ibc_arl_amount += line.amount
                                    subtotal_ibc_arl = ibc_arl_amount / 30
                                    total_ibc_arl = subtotal_ibc_arl * days

                        round_amount = round(total_ibc_arl)

                        if employee.risk_classes_type == 'risk1':
                            ws.write(row_num, 76, 0.0, style_percent)
                            ws.write(row_num, 77, 1)
                            risk_total = round(total_ibc_arl * 0.522)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk2':
                            ws.write(row_num, 76, 0.0, style_percent)
                            ws.write(row_num, 77, 2)
                            risk_total = round(total_ibc_arl * 1.044)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk3':
                            ws.write(row_num, 76, 0.0, style_percent)
                            ws.write(row_num, 77, 3)
                            risk_total = round(total_ibc_arl * 2.436)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk4':
                            ws.write(row_num, 76, 0.0, style_percent)
                            ws.write(row_num, 77, 4)
                            risk_total = round(total_ibc_arl * 4.350)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk5':
                            ws.write(row_num, 76, 0.0, style_percent)
                            ws.write(row_num, 77, 5)
                            risk_total = round(total_ibc_arl * 6.960)
                            ws.write(row_num, 80, '', style_money)
                        else:
                            ws.write(row_num, 76, 0, style_percent)
                            ws.write(row_num, 77, '')

                        ws.write(row_num, 79, employee.economic_activity or '')
                        ws.write(row_num, 81, days or '')
                        ws.write(row_num, 82, admin_ccf_name or '')
                        ibc_parafiscal_amount = 0.0
                        total_ibc_parafiscal = 0.0
                        found_ibc_parafiscal = False

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'BASIC':
                                    found_ibc_parafiscal = True
                                    ibc_parafiscal_amount += line.amount
                                    subtotal_ibc_parafiscal = ibc_parafiscal_amount / 30
                                    total_ibc_parafiscal = subtotal_ibc_parafiscal * days

                            if found_ibc_parafiscal:
                                round_parafiscal = round(total_ibc_parafiscal)
                                ws.write(row_num, 83, round_parafiscal, style_money or '')

                        ws.write(row_num, 84, '', style_percent)
                        ws.write(row_num, 85, '', style_money)
                        if ibc_parafiscal_amount:
                            ws.write(row_num, 84, 0.04,style_number)
                            fee = total_ibc_parafiscal * 0.04
                            rounded_fee = round(fee, -2)
                            last_three_digits = rounded_fee % 1000

                            # Redondear al siguiente múltiplo de 100 y sumar 100 si los últimos tres dígitos están entre 100 y 999
                            if 000 <= last_three_digits <= 100:
                                if fee % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                    rounded_fee += 100
                            elif last_three_digits > 100:  # Si los últimos tres dígitos están entre 000 y 099, no hacemos nada
                                if fee % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                    rounded_fee += 100
                            ws.write(row_num, 85, rounded_fee, style_money or '')
                        ibc_parafiscal_amount_other = 0.0
                        total_ibc_parafiscal_other = 0.0
                        found_ibc_parafiscal_other = False

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'IBC_parafiscal':
                                    found_ibc_parafiscal_other = True
                                    ibc_parafiscal_amount_other += line.amount
                                    subtotal_ibc_parafiscal = ibc_parafiscal_amount_other / 30
                                    total_ibc_parafiscal_other = subtotal_ibc_parafiscal * total_number_of_days_work100
                                if found_ibc_parafiscal_other:
                                    if ibc_parafiscal_amount_other > self.company_id.salary_min * 10:
                                        round_parafiscal_other = round(ibc_parafiscal_amount_other)
                                        ws.write(row_num, 86, round_parafiscal_other, style_money or '')
                                        ws.write(row_num, 87, 0.02, style_number)
                                        sena = ibc_parafiscal_amount_other * 0.02
                                        rounded_sena = round(sena, -2)
                                        last_three_digits = rounded_sena % 1000

                                        # Redondear al siguiente múltiplo de 100 y sumar 100 si los últimos tres dígitos están entre 100 y 999
                                        if 000 <= last_three_digits <= 100:
                                            if sena % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                                rounded_sena += 100
                                        elif last_three_digits > 100:  # Si los últimos tres dígitos están entre 000 y 099, no hacemos nada
                                            if sena % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                                rounded_sena += 100
                                        ws.write(row_num, 88, '', style_money)
                                        ws.write(row_num, 89, '', style_number)

                                        ws.write(row_num, 90, '', style_money)
                                    else:
                                        ws.write(row_num, 86, '', style_money)
                                        ws.write(row_num, 87, '', style_number)
                                        ws.write(row_num, 88, '', style_money)
                                        ws.write(row_num, 89, '', style_number)
                                        ws.write(row_num, 90, '', style_money)

                                ws.write(row_num, 91, 0.00, style_percent)
                                ws.write(row_num, 92, '', style_money)
                                ws.write(row_num, 93, 0.00, style_percent)
                                ws.write(row_num, 94, '', style_money)
                                ws.write(row_num, 95, 'SI' or '')

                        row_num += 1
                        line_number += 1
# LICENCIA MATERNIDAD
                    if leave.holiday_status_id.type_security == 'leave5':
                        ws.write(row_num, 0, line_number)
                        ws.write(row_num, 1, type_iden_name or '')
                        ws.write(row_num, 2, employee.identification_id or '')
                        ws.write(row_num, 3, partner.lastname or '')
                        ws.write(row_num, 4, partner.lastname2 or '')
                        ws.write(row_num, 5, partner.firstname or '')
                        ws.write(row_num, 6, partner.othernames or '')
                        ws.write(row_num, 7, department_name or '')
                        ws.write(row_num, 8, city_name or '')
                        ws.write(row_num, 9, types_contributor_name or '')
                        ws.write(row_num, 10, type_sub_iden_name or '')
                        ws.write(row_num, 11, 0, style_money)
                        ws.write(row_num, 12, colom_foreign_name or '')
                        ws.write(row_num, 13, foreign_name or '')
                        ws.write(row_num, 14,
                                 employee.foreign_date.strftime('%Y-%m-%d') if employee.foreign_date else '')
                        ws.write(row_num, 15, 'NO')
                        ws.write(row_num, 16, '')
                        ws.write(row_num, 17, 'NO')
                        ws.write(row_num, 18, '')
                        ws.write(row_num, 19, 'NO')
                        ws.write(row_num, 20, 'NO')
                        ws.write(row_num, 21, 'NO')
                        ws.write(row_num, 22, 'NO')
                        ws.write(row_num, 23, 'NO')
                        ws.write(row_num, 24, '')
                        ws.write(row_num, 25, 'NO')
                        ws.write(row_num, 26, 'NO')
                        ws.write(row_num, 29, 'NO')
                        ws.write(row_num, 32, 'LICENCIA DE MATERNIDAD (LMA)')
                        ws.write(row_num, 33, leave.date_from.strftime('%Y-%m-%d'))
                        ws.write(row_num, 34, leave.date_to.strftime('%Y-%m-%d'))
                        ws.write(row_num, 35, 'NO')
                        ws.write(row_num, 36, '')
                        ws.write(row_num, 37, '')
                        ws.write(row_num, 38, 'NO')
                        ws.write(row_num, 39, 'NO')
                        ws.write(row_num, 42, '', style_money)
                        ws.write(row_num, 45, 'NO')
                        num_contract = round(contract.custom_wage)
                        ws.write(row_num, 46, num_contract, style_money or '')
                        ws.write(row_num, 47, comprehensive_salary_name or '')
                        ws.write(row_num, 48, variable_salary_name or '')
                        ws.write(row_num, 49, type_admin_name or '')
                        days = int(leave.duration_display.split()[0])
                        ws.write(row_num, 50, days or '')

                        ibc_ss = (contract.custom_wage / 30) * days
                        round_ibc_ss = round(ibc_ss)

                        ws.write(row_num , 51, round_ibc_ss, style_money or '')
                        ws.write(row_num, 64, round_ibc_ss, style_money or '')
                        ws.write(row_num, 75, round_ibc_ss, style_money or '')
                        ws.write(row_num, 83, round_ibc_ss, style_money or '')
                        found_cant = False
                        learner_cant = 0.0
                        total_cant = 0.0

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'ded_15':
                                    found_cant = True
                                    learner_cant += line.amount
                                    subtotal_cant = ibc_ss_1_amount / 30
                                    total_cant = subtotal_cant * total_number_of_days_work100
                            if round_ibc_ss > self.company_id.salary_min * 10 or learner_cant > 10.00:
                                fee_salary_total = round_ibc_ss * 0.125
                                rounded_fee_salary_total = round(fee_salary_total)

                                last_three_digits = rounded_fee_salary_total % 100

                                if '01' <= str(last_three_digits) <= '50':
                                    rounded_fee_salary_total = round(fee_salary_total, -2) + 100
                                elif str(last_three_digits) > '50':
                                    rounded_fee_salary_total = round(fee_salary_total, -2)
                                else:
                                    pass
                                if rounded_fee_salary_total != '':
                                    rounded_fee_salary_total = int(rounded_fee_salary_total)
                                ws.write(row_num, 66, rounded_fee_salary_total, style_money)
                                ws.write(row_num, 65, 0.125, style_number)
                            else:
                                fee_salary_total = round_ibc_ss * 0.04

                                rounded_fee_salary_total = round(fee_salary_total)

                                last_three_digits = rounded_fee_salary_total % 100

                                if '01' <= str(last_three_digits) <= '50':
                                    rounded_fee_salary_total = round(fee_salary_total, -2) + 100
                                elif str(last_three_digits) > '50':
                                    rounded_fee_salary_total = round(fee_salary_total, -2)
                                else:
                                    pass
                                if rounded_fee_salary_total != '':
                                    rounded_fee_salary_total = int(rounded_fee_salary_total)
                                ws.write(row_num, 66, rounded_fee_salary_total, style_money)
                                ws.write(row_num, 65, 0.04, style_number)
                        else:
                            ws.write(row_num, 65, '', style_number)
                            ws.write(row_num, 66, '', style_money)
                        ws.write(row_num, 52, 0.16, style_number)
                        price = round_ibc_ss * 0.16

                        # Redondear al múltiplo de 100 más cercano
                        rounded_price = round(price)

                        # Obtener los últimos tres dígitos del precio
                        last_three_digits = rounded_price % 100

                        # Redondear al siguiente múltiplo de 100 y sumar 100 si los últimos tres dígitos están entre 001 y 100
                        if '01' <= str(last_three_digits) <= '50':
                            rounded_price = round(price, -2) + 100
                        elif str(last_three_digits) > '50':
                            rounded_price = round(price, -2)
                        else:
                            pass

                        if rounded_price != '':
                            rounded_price = int(rounded_price)

                        # Escribir en la celda correspondiente en tu archivo de Excel
                        ws.write(row_num, 53, rounded_price, style_money or '')
                        ws.write(row_num, 54, risk_indicator_name or '')
                        ws.write(row_num, 55, '', style_money)
                        ws.write(row_num, 56, '', style_money)
                        ded_7_amount = 0.0
                        subtotal_ded_7 = 0.0
                        found_ded_7 = False

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'ded_1':
                                    found_ded_7 = True
                                    ded_7_amount += line.amount

                        if found_ded_7:
                            subtotal_ded_7 = round(round_ibc_ss * 0.01 / 2)
                            rounded_ded_7 = round(subtotal_ded_7, -2)
                            last_three_digits = rounded_ded_7 % 1000
                            if 000 <= last_three_digits <= 100:
                                if subtotal_ded_7 % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                    rounded_ded_7 += 100
                            elif last_three_digits > 100:  # Si los últimos tres dígitos están entre 000 y 099, no hacemos nada
                                if subtotal_ded_7 % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                    rounded_ded_7 += 100
                            ws.write(row_num, 57, rounded_ded_7, style_money)
                            ws.write(row_num, 58, rounded_ded_7, style_money)
                            price_total = round(rounded_price + (rounded_ded_7 * 2))
                            ws.write(row_num, 60, price_total, style_money or '')

                        else:
                            ws.write(row_num, 57, '', style_money)
                            ws.write(row_num, 58, '', style_money)
                            price_total = round(rounded_price)
                            ws.write(row_num, 60, price_total, style_money or '')


                        ws.write(row_num, 59, '', style_money)
                        ws.write(row_num, 61, 'NINGUNA')
                        ws.write(row_num, 62, types_admin_name)
                        ws.write(row_num, 63, days or '')

                        ws.write(row_num, 67, '', style_money)
                        ws.write(row_num, 69, '', style_money)
                        ws.write(row_num, 71, '', style_money)
                        ws.write(row_num, 72, 'NINGUNA')
                        ws.write(row_num, 73, admin_risk_name)
                        ws.write(row_num, 74, days or '')
                        ibc_arl_amount = 0.0
                        total_ibc_arl = 0.0
                        found_ibc_arl = False
                        if payslip:
                            for line in payslip.line_ids:
                                if line.code in ('inc_gen', 'inc_genp1', 'inc_gen_2', 'inc_gen_P2'):
                                    found_ibc_arl = True
                                    ibc_arl_amount += line.amount
                                    subtotal_ibc_arl = ibc_arl_amount / 30
                                    total_ibc_arl = subtotal_ibc_arl * days

                        round_amount = round(total_ibc_arl)

                        if employee.risk_classes_type == 'risk1':
                            ws.write(row_num, 76, 0.0, style_number)
                            ws.write(row_num, 77, 1)
                            risk_total = round(total_ibc_arl * 0.522)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk2':
                            ws.write(row_num, 76, 0.0, style_number)
                            ws.write(row_num, 77, 2)
                            risk_total = round(total_ibc_arl * 1.044)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk3':
                            ws.write(row_num, 76, 0.0, style_number)
                            ws.write(row_num, 77, 3)
                            risk_total = round(total_ibc_arl * 2.436)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk4':
                            ws.write(row_num, 76, 0.0, style_percent)
                            ws.write(row_num, 77, 4)
                            risk_total = round(total_ibc_arl * 4.350)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk5':
                            ws.write(row_num, 76, 0.0, style_percent)
                            ws.write(row_num, 77, 5)
                            risk_total = round(total_ibc_arl * 6.960)
                            ws.write(row_num, 80, '', style_money)
                        else:
                            ws.write(row_num, 76, 0, style_percent)
                            ws.write(row_num, 77, '')

                        ws.write(row_num, 79, employee.economic_activity or '')
                        ws.write(row_num, 81, days or '')
                        ws.write(row_num, 82, admin_ccf_name or '')
                        ibc_parafiscal_amount = 0.0
                        total_ibc_parafiscal = 0.0
                        found_ibc_parafiscal = False

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'IBC_parafiscales2':
                                    found_ibc_parafiscal = True
                                    ibc_parafiscal_amount += line.amount
                                    subtotal_ibc_parafiscal = ibc_parafiscal_amount / 30
                                    total_ibc_parafiscal = subtotal_ibc_parafiscal * days
                        ws.write(row_num, 86, '', style_money)
                        ws.write(row_num, 87, 0.0, style_number)
                        ws.write(row_num, 88, '', style_money)
                        ws.write(row_num, 89, '', style_number)
                        ws.write(row_num, 90, '', style_money)
                        ws.write(row_num, 84, 0.0, style_number)
                        ws.write(row_num, 85, '', style_money)
                        ws.write(row_num, 91, 0.00, style_percent)
                        ws.write(row_num, 92, '', style_money)
                        ws.write(row_num, 93, 0.00, style_percent)
                        ws.write(row_num, 94, '', style_money)
                        ws.write(row_num, 95, 'N')

                        row_num += 1
                        line_number += 1
# INCAPACIDAD PROFESIONAL
                    if leave.holiday_status_id.type_security == 'leave4':
                        ws.write(row_num, 0, line_number)
                        ws.write(row_num, 1, type_iden_name or '')
                        ws.write(row_num, 2, employee.identification_id or '')
                        ws.write(row_num, 3, partner.lastname or '')
                        ws.write(row_num, 4, partner.lastname2 or '')
                        ws.write(row_num, 5, partner.firstname or '')
                        ws.write(row_num, 6, partner.othernames or '')
                        ws.write(row_num, 7, department_name or '')
                        ws.write(row_num, 8, city_name or '')
                        ws.write(row_num, 9, types_contributor_name or '')
                        ws.write(row_num, 10, type_sub_iden_name or '')
                        ws.write(row_num, 11, 0, style_money)
                        ws.write(row_num, 12, colom_foreign_name or '')
                        ws.write(row_num, 13, foreign_name or '')
                        ws.write(row_num, 14,
                                 employee.foreign_date.strftime('%Y-%m-%d') if employee.foreign_date else '')
                        ws.write(row_num, 15, 'NO')
                        ws.write(row_num, 16, '')
                        ws.write(row_num, 17, 'NO')
                        ws.write(row_num, 18, '')
                        ws.write(row_num, 19, 'NO')
                        ws.write(row_num, 20, 'NO')
                        ws.write(row_num, 21, 'NO')
                        ws.write(row_num, 22, 'NO')
                        ws.write(row_num, 23, 'NO')
                        ws.write(row_num, 24, '')
                        ws.write(row_num, 25, 'NO')
                        ws.write(row_num, 26, 'NO')
                        ws.write(row_num, 29, 'NO')
                        ws.write(row_num, 32, 'NO')
                        ws.write(row_num, 35, 'NO')
                        ws.write(row_num, 36, '')
                        ws.write(row_num, 37, '')
                        ws.write(row_num, 38, 'NO')
                        ws.write(row_num, 39, 'NO')
                        ws.write(row_num, 45, 'NO')
                        num_contract = round(contract.custom_wage)
                        ws.write(row_num, 46, num_contract, style_money or '')
                        ws.write(row_num, 47, comprehensive_salary_name or '')
                        ws.write(row_num, 48, variable_salary_name or '')
                        ws.write(row_num, 49, type_admin_name or '')
                        days = int(leave.duration_display.split()[0])
                        ws.write(row_num, 50, days or '')
                        ws.write(row_num, 42, days, style_money)
                        ws.write(row_num, 43, leave.date_from.strftime('%Y-%m-%d'))
                        ws.write(row_num, 44, leave.date_to.strftime('%Y-%m-%d'))

                        ibc_ss = (contract.custom_wage / 30) * days
                        round_ibc_ss = round(ibc_ss)

                        ws.write(row_num, 51, round_ibc_ss, style_money or '')
                        ws.write(row_num, 64, round_ibc_ss, style_money or '')
                        ws.write(row_num, 75, round_ibc_ss, style_money or '')
                        ws.write(row_num, 83, round_ibc_ss, style_money or '')
                        found_cant = False
                        learner_cant = 0.0
                        total_cant = 0.0

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'ded_15':
                                    found_cant = True
                                    learner_cant += line.amount
                                    subtotal_cant = ibc_ss_1_amount / 30
                                    total_cant = subtotal_cant * total_number_of_days_work100
                            if round_ibc_ss > self.company_id.salary_min * 10 or learner_cant > 10.00:
                                fee_salary_total = round_ibc_ss * 0.125
                                rounded_fee_salary_total = round(fee_salary_total)

                                last_three_digits = rounded_fee_salary_total % 100

                                if '01' <= str(last_three_digits) <= '50':
                                    rounded_fee_salary_total = round(fee_salary_total, -2) + 100
                                elif str(last_three_digits) > '50':
                                    rounded_fee_salary_total = round(fee_salary_total, -2)
                                else:
                                    pass
                                if rounded_fee_salary_total != '':
                                    rounded_fee_salary_total = int(rounded_fee_salary_total)
                                ws.write(row_num, 66, rounded_fee_salary_total, style_money)
                                ws.write(row_num, 65, 0.125, style_number)
                            else:
                                fee_salary_total = round_ibc_ss * 0.04

                                rounded_fee_salary_total = round(fee_salary_total)

                                last_three_digits = rounded_fee_salary_total % 100

                                if '01' <= str(last_three_digits) <= '50':
                                    rounded_fee_salary_total = round(fee_salary_total, -2) + 100
                                elif str(last_three_digits) > '50':
                                    rounded_fee_salary_total = round(fee_salary_total, -2)
                                else:
                                    pass
                                if rounded_fee_salary_total != '':
                                    rounded_fee_salary_total = int(rounded_fee_salary_total)
                                ws.write(row_num, 66, rounded_fee_salary_total, style_money)
                                ws.write(row_num, 65, 0.04, style_number)
                        else:
                            ws.write(row_num, 65, '', style_number)
                            ws.write(row_num, 66, '', style_money)
                        ws.write(row_num, 52, 0.16, style_number)
                        price = round_ibc_ss * 0.16

                        # Redondear al múltiplo de 100 más cercano
                        rounded_price = round(price)

                        # Obtener los últimos tres dígitos del precio
                        last_three_digits = rounded_price % 100

                        # Redondear al siguiente múltiplo de 100 y sumar 100 si los últimos tres dígitos están entre 001 y 100
                        if '01' <= str(last_three_digits) <= '50':
                            rounded_price = round(price, -2) + 100
                        elif str(last_three_digits) > '50':
                            rounded_price = round(price, -2)
                        else:
                            pass

                        if rounded_price != '':
                            rounded_price = int(rounded_price)

                        # Escribir en la celda correspondiente en tu archivo de Excel
                        ws.write(row_num, 53, rounded_price, style_money or '')
                        ws.write(row_num, 54, risk_indicator_name or '')
                        ws.write(row_num, 55, '', style_money)
                        ws.write(row_num, 56, '', style_money)
                        ded_7_amount = 0.0
                        subtotal_ded_7 = 0.0
                        found_ded_7 = False

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'ded_1':
                                    found_ded_7 = True
                                    ded_7_amount += line.amount

                        if found_ded_7:
                            subtotal_ded_7 = round(round_ibc_ss * 0.01 / 2)
                            rounded_ded_7 = round(subtotal_ded_7, -2)
                            last_three_digits = rounded_ded_7 % 1000
                            if 000 <= last_three_digits <= 100:
                                if subtotal_ded_7 % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                    rounded_ded_7 += 100
                            elif last_three_digits > 100:  # Si los últimos tres dígitos están entre 000 y 099, no hacemos nada
                                if subtotal_ded_7 % 100 <= 50:  # Agregar condición para verificar los últimos dos dígitos
                                    rounded_ded_7 += 100
                            ws.write(row_num, 57, rounded_ded_7, style_money)
                            ws.write(row_num, 58, rounded_ded_7, style_money)
                            price_total = round(rounded_price + (rounded_ded_7 * 2))
                            ws.write(row_num, 60, price_total, style_money or '')

                        else:
                            ws.write(row_num, 57, '', style_money)
                            ws.write(row_num, 58, '', style_money)
                            price_total = round(rounded_price)
                            ws.write(row_num, 60, price_total, style_money or '')

                        ws.write(row_num, 59, '', style_money)
                        ws.write(row_num, 61, 'NINGUNA')
                        ws.write(row_num, 62, types_admin_name)
                        ws.write(row_num, 63, days or '')

                        ws.write(row_num, 67, '', style_money)
                        ws.write(row_num, 69, '', style_money)
                        ws.write(row_num, 71, '', style_money)
                        ws.write(row_num, 72, 'NINGUNA')
                        ws.write(row_num, 73, admin_risk_name)
                        ws.write(row_num, 74, days or '')
                        ibc_arl_amount = 0.0
                        total_ibc_arl = 0.0
                        found_ibc_arl = False
                        if payslip:
                            for line in payslip.line_ids:
                                if line.code in ('inc_gen', 'inc_genp1', 'inc_gen_2', 'inc_gen_P2'):
                                    found_ibc_arl = True
                                    ibc_arl_amount += line.amount
                                    subtotal_ibc_arl = ibc_arl_amount / 30
                                    total_ibc_arl = subtotal_ibc_arl * days

                        round_amount = round(total_ibc_arl)

                        if employee.risk_classes_type == 'risk1':
                            ws.write(row_num, 76, 0.0, style_number)
                            ws.write(row_num, 77, 1)
                            risk_total = round(total_ibc_arl * 0.522)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk2':
                            ws.write(row_num, 76, 0.0, style_number)
                            ws.write(row_num, 77, 2)
                            risk_total = round(total_ibc_arl * 1.044)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk3':
                            ws.write(row_num, 76, 0.0, style_number)
                            ws.write(row_num, 77, 3)
                            risk_total = round(total_ibc_arl * 2.436)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk4':
                            ws.write(row_num, 76, 0.0, style_percent)
                            ws.write(row_num, 77, 4)
                            risk_total = round(total_ibc_arl * 4.350)
                            ws.write(row_num, 80, '', style_money)
                        elif employee.risk_classes_type == 'risk5':
                            ws.write(row_num, 76, 0.0, style_percent)
                            ws.write(row_num, 77, 5)
                            risk_total = round(total_ibc_arl * 6.960)
                            ws.write(row_num, 80, '', style_money)
                        else:
                            ws.write(row_num, 76, 0, style_percent)
                            ws.write(row_num, 77, '')

                        ws.write(row_num, 79, employee.economic_activity or '')
                        ws.write(row_num, 81, days or '')
                        ws.write(row_num, 82, admin_ccf_name or '')
                        ibc_parafiscal_amount = 0.0
                        total_ibc_parafiscal = 0.0
                        found_ibc_parafiscal = False

                        if payslip:
                            for line in payslip.line_ids:
                                if line.code == 'IBC_parafiscales2':
                                    found_ibc_parafiscal = True
                                    ibc_parafiscal_amount += line.amount
                                    subtotal_ibc_parafiscal = ibc_parafiscal_amount / 30
                                    total_ibc_parafiscal = subtotal_ibc_parafiscal * days
                        ws.write(row_num, 86, '', style_money)
                        ws.write(row_num, 87, 0.0, style_number)
                        ws.write(row_num, 88, '', style_money)
                        ws.write(row_num, 89, '', style_number)
                        ws.write(row_num, 90, '', style_money)
                        ws.write(row_num, 84, 0.0, style_number)
                        ws.write(row_num, 85, '', style_money)
                        ws.write(row_num, 91, 0.00, style_percent)
                        ws.write(row_num, 92, '', style_money)
                        ws.write(row_num, 93, 0.00, style_percent)
                        ws.write(row_num, 94, '', style_money)
                        ws.write(row_num, 95, 'SI')
                        row_num += 1
                        line_number += 1

        for col_num, header in enumerate(headers):
            col_width = max(256 * (len(header) + 1), ws.col(col_num).get_width())
            ws.col(col_num).width = col_width
        archivo = io.BytesIO()
        wb.save(archivo)
        archivo.seek(0)
        data = archivo.read()
        if data:
            file_id = self.env['file.imp'].create(
                {'filecontent': base64.b64encode(data)}
            )
            filename_field = 'Liquidaciones'
            if file_id and file_id.id:
                return {
                    'res_model': 'ir.actions.act_url',
                    'type': 'ir.actions.act_url',
                    'target': 'new',
                    'url': (
                        'web/content/?model=file.imp&id={0}'
                        '&filename_field={1}'
                        '&field=filecontent&download=true'
                        '&filename={1}.xls'.format(
                            file_id.id,
                            filename_field,
                        )
                    ),
                }
        else:
            raise ValueError(
                'Error de Descarga - No se pudo generar el archivo solicitado.'
            )
