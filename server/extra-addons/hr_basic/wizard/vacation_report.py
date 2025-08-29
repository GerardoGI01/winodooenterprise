from odoo import fields, models, api, exceptions
import io
import base64
import xlwt
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from babel.numbers import format_currency
import locale
locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
from dateutil.relativedelta import relativedelta


class VacationReport(models.Model):
    _name = 'vacation.report'
    _description = 'Vacation Report'

    name = fields.Char(string='nombre')
    is_employee = fields.Boolean(string='Por Empleado')
    is_all_employee = fields.Boolean(string='Por Fecha')
    start_date = fields.Date(string="Fecha inicio")
    end_date = fields.Date(string="Fecha fin")
    employee_id = fields.Many2one('hr.employee', string=' Empleado', domain=[('is_contract', '=', True)])
    is_consolidated_report = fields.Boolean(string='Informe Consolidado Vacaciones')
    is_disabilities_report = fields.Boolean(string='Informe Consolidado Incapacidades')
    is_vacation = fields.Boolean(string='Vacaciones')
    is_disabilities = fields.Boolean(string='Incapacidades')
    id_company = fields.Integer(string='ID compañía',related='company_id.id')
    company_id = fields.Many2one('res.company', string='Compañía', required=True)
    date_days_worked = fields.Date(string="Fecha Días Trabajados", default=fields.Date.today)

    def generate_excel_report_vacation(self):
        if not (self.is_vacation or self.is_disabilities or self.is_consolidated_report):
            raise exceptions.ValidationError("Debe seleccionar una opción para generar el Informe correspondiente.")
        if self.is_vacation:
            return self.generate_individual_report()
        if self.is_disabilities:
            return self.generate_disabilities_report()

    def generate_individual_report(self):
        employee_id = self.employee_id.id
        wb = xlwt.Workbook()
        title = 'LIQUIDACIÓN DE VACACIONES'
        ws = wb.add_sheet(title, cell_overwrite_ok=True)
        title_style = xlwt.easyxf('pattern: pattern solid, fore_colour 0x12;'
                                  'font: bold on, height 400, color white; align: horiz center;'
                                  'borders: top thin, bottom thin, left thin, right thin;')
        ws.write_merge(0, 0, 0, 10, title, title_style)
        nominal_title = 'CÁLCULO NOMINAL'
        nominal_style = xlwt.easyxf('pattern: pattern solid, fore_colour 0x36;'
                                    'font: bold on, height 400, color white; align: horiz center;'
                                    'borders: top thin, bottom thin, left thin, right thin;')
        ws.write_merge(0, 0, 11, 14, nominal_title, nominal_style)
        headers = ['CEDULA', 'NOMBRE', 'CARGO', 'CENTRO DE COSTOS', 'JEFE DIRECTO', 'FECHA DE INGRESO', 'SALARIO',
                   'DIAS TRABAJADOS', 'PERIODO', 'DIA INICIAL', 'DIA FINAL', 'DIAS TOMADOS',
                   'DIAS PENDIENTES POR PERIODO', 'DIAS TOTALES',
                   'T.DIAS TOMADOS', 'DIAS VAC PENDIENTES', 'TIPO DE AUSENCIA']
        header_style = xlwt.easyxf('pattern: pattern solid, fore_colour 0x1F;'
                                   'font: bold on, height 200, color black; align: horiz center;'
                                   'borders: top thin, bottom thin, left thin, right thin;')
        for col_num, header in enumerate(headers):
            ws.write(1, col_num, header, header_style)
        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
            employees = self.env['hr.employee'].search([('id', '=', employee.id)])

        else:
            employees = self.env['hr.employee'].search([('is_contract', '=', True)])
        leave_domain = []
        row_num = 2
        for employee in employees:
            if not employee_id:
                leave_domain = [('employee_id', '=', employee.id), ('holiday_status_id.type_absence', '=', 'absence2')]
            else:
                leave_domain = [('employee_id', '=', employee_id), ('holiday_status_id.type_absence', '=', 'absence2')]

            leave_allocations = self.env['hr.leave'].search(leave_domain)
            salary = format_currency(employee.contract_id.wage, 'COP', locale='es_CO')
            init_date = employee.contract_id.date_start
            total_leave_durations = []
            total_leave_duration = sum(leave.weekend_days for leave in leave_allocations)
            total_leave_durations.append(total_leave_duration)
            ws.write(row_num, 0, employee.identification_id)
            ws.write(row_num, 1, employee.name)
            ws.write(row_num, 2, employee.job_id.name)
            ws.write(row_num, 4, employee.parent_id.name)
            ws.write(row_num, 5, init_date.strftime("%d-%m-%Y") if init_date else '')
            ws.write(row_num, 6, salary)
            today_days = self.date_days_worked
            diff_days = (relativedelta(today_days, init_date).years * 360 +
                         relativedelta(today_days, init_date).months * 30 +
                         relativedelta(today_days, init_date).days)

            ws.write(row_num, 7, diff_days)
            # Ajuste en los cálculos según el valor de company_id
            if self.company_id.id == 1:
                result = (diff_days * 15) / 360
            elif self.company_id.id in (2, 9):
                result = (diff_days - total_leave_duration) / 330 * 30
            else:
                result = 0
            ws.write(row_num, 13, result)
            for total_leave_duration in total_leave_durations:
                ws.write(row_num, 14, total_leave_duration)
            if total_leave_duration:
                general_total = result - total_leave_duration
            else:
                if self.company_id.id == 1:
                    general_total = 15
                else:
                    general_total = 15
            ws.write(row_num, 15, general_total)
            provision_subtotal = (employee.contract_id.wage * diff_days) / 720
            provision_subtotal_cop = format_currency(provision_subtotal, 'COP', locale='es_CO')
            total_provision = (employee.contract_id.wage / 30) * general_total
            if leave_allocations:
                # Ordenar las leave_allocations por fecha de leave_from_date de menor a mayor
                sorted_leave_allocations = sorted(leave_allocations, key=lambda x: x.date_from)

                for leave in sorted_leave_allocations:
                    leave_from_date = leave.date_from.strftime('%d/%m/%Y')
                    leave_to_date = leave.date_to.strftime('%d/%m/%Y')
                    leave_duration = leave.weekend_days

                    leave_from_year = leave.date_from.strftime('%Y')
                    if self.company_id.id == 1:
                        leave_duration_minus_15 = 15 - leave_duration
                    else:
                        leave_duration_minus_15 = 30 - leave_duration
                    red_style = xlwt.easyxf('pattern: pattern solid, fore_colour red;')
                    pending = leave.days_pending
                    ws.write(row_num, 9, leave_from_date)  # Mostrar leave_from_date en lugar de period
                    ws.write(row_num, 10, leave_to_date)
                    ws.write(row_num, 11, leave_duration)
                    if pending == '0':
                        ws.write(row_num, 12, pending, red_style)
                    else:
                        ws.write(row_num, 12, pending)
                    holiday_status_id = leave.holiday_status_id.name
                    ws.write(row_num, 17, holiday_status_id)
                    # Mantener la columna 8 como period si lo necesitas
                    period = leave.period
                    ws.write(row_num, 8, period)
                    row_num += 1
            else:
                ws.write(row_num, 9, '')
                ws.write(row_num, 10, '')
                ws.write(row_num, 11, '')
                ws.write(row_num, 12, '')
                row_num += 1
            default_col_width = 256 * 20

            for col_num, header in enumerate(headers):
                col_width = max(default_col_width, ws.col(col_num).get_width())
                ws.col(col_num).width = col_width

        self.write({'employee_id': False})

        archivo = io.BytesIO()
        wb.save(archivo)
        archivo.seek(0)
        data = archivo.read()
        if data:
            file_id = self.env['file.imp'].create(
                {'filecontent': base64.b64encode(data)}
            )
            filename_field = 'Informe Vacaciones por Empleado'
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

    def generate_disabilities_report(self):
        employee_id = self.employee_id.id
        wb = xlwt.Workbook()
        title = 'LIBRO DE INCAPACIDADES'
        ws = wb.add_sheet(title, cell_overwrite_ok=True)
        title_style = xlwt.easyxf(
            'pattern: pattern solid, fore_colour 0x12;'
            'font: bold on, height 400, color white; align: horiz center;'
            'borders: top thin, bottom thin, left thin, right thin;'
        )
        ws.write_merge(0, 0, 0, 10, title, title_style)

        headers = [
            'CEDULA', 'NOMBRE', 'CARGO', 'FECHA DE INGRESO', 'SALARIO', 'MES',
            'TOTAL DIAS', 'DIAS TRABAJADOS','MESES LABORADOS', 'DIAS CAUSADOS', 'T.DIAS TOMADOS', 'DIAS PENDIENTES'
        ]
        header_style = xlwt.easyxf(
            'pattern: pattern solid, fore_colour 0x1F;'
            'font: bold on, height 200, color black; align: horiz center;'
            'borders: top thin, bottom thin, left thin, right thin;'
        )

        for col_num, header in enumerate(headers):
            ws.write(1, col_num, header, header_style)

        employee = self.env['hr.employee'].search([] if not employee_id else [('id', '=', employee_id)])
        leave_domain_dis = []
        row_num = 2
        total_days = 0  # Inicializar el total de días
        pending_days = 0  # Inicializar los días pendientes
        for employee in employee:

            leave_domain_dis = [('employee_id', '=', employee.id), ('holiday_status_id.type_absence', '=', 'absence1')]
            leave_allocations = self.env['hr.leave'].search(leave_domain_dis)

            init_date = employee.contract_id.date_start
            salary = format_currency(employee.contract_id.wage, 'COP', locale='es_CO')

            today = datetime.today().date()

            if init_date:
                diff_days = (today - init_date).days + 1
            else:
                diff_days = 0  # Valor predeterminado cuando init_date es None

            month_totals = {}
            if leave_allocations:
                for leave in leave_allocations:
                    leave_from_date = leave.date_from.strftime('%d/%m/%Y')
                    leave_to_date = leave.date_to.strftime('%d/%m/%Y')
                    leave_duration = float(leave.duration_display.split()[0])
                    leave_month = leave.date_from.strftime('%B').capitalize()

                    if leave_month not in month_totals:
                        month_totals[leave_month] = 0
                    month_totals[leave_month] += leave_duration

                    # Obtener el año del leave_from_date
                    # Obtener el año del leave_from_date
                    leave_from_year = int(leave_from_date[-4:])

                    # Obtener el año de init_date
                    init_date_year = init_date.year

            ws.write(row_num, 0, employee.identification_id)
            ws.write(row_num, 1, employee.name)
            ws.write(row_num, 2, employee.job_id.name)

            if init_date:
                format_date = init_date.strftime("%d-%m-%Y")
                ws.write(row_num, 3, format_date)
            else:
                ws.write(row_num, 3, '')

            ws.write(row_num, 4, salary)


            today = datetime.today().date()

            if init_date:
                diff_days = (relativedelta(today, init_date).years * 360 +
                             relativedelta(today, init_date).months * 30 +
                             relativedelta(today, init_date).days)+ 1
                ws.write(row_num, 7, diff_days)
            else:
                ws.write(row_num, 7, '')
            total_month = round((diff_days) / 30)
            ws.write(row_num, 8, total_month)
            caused_days = round(total_month * 1.5, 2)
            if caused_days >= 36:
                caused_days = 36
            formatted_caused_days = '{:.2f}'.format(caused_days).replace('.', ',')  # Formato con coma en lugar de punto
            ws.write(row_num, 9, formatted_caused_days)

            total_days_month_sum = sum(month_totals.values())
            pending_days += caused_days - total_days_month_sum

            while pending_days >= 12:
                pending_days -= 12

            total_days_month_sum = sum(month_totals.values())
            pending_days = (caused_days - total_days_month_sum)

            for month, total_days_month in month_totals.items():
                ws.write(row_num, 5, month)
                ws.write(row_num, 6, total_days_month)
                ws.write(row_num, 10, total_days_month_sum)
                if pending_days < 0:
                    style = xlwt.easyxf('pattern: pattern solid, fore_colour red; font: color white;')
                    ws.write(row_num, 11, pending_days, style)
                else:
                    ws.write(row_num, 11, pending_days)
                row_num += 1

            total_days += total_days_month_sum

            total_days_month_sum = 0
            month_totals = {}

        default_col_width = 256 * 20

        for col_num, header in enumerate(headers):
            col_width = max(default_col_width, ws.col(col_num).get_width())
            ws.col(col_num).width = col_width

        self.employee_id = False

        archivo = io.BytesIO()
        wb.save(archivo)
        archivo.seek(0)
        data = archivo.read()
        if data:
            file_id = self.env['file.imp'].create(
                {'filecontent': base64.b64encode(data)}
            )
            filename_field = 'Libro Incapacidades'
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


class FileImp(models.TransientModel):
        _name = 'file.imp'
        _description = u'Documentos para descargar'

        filecontent = fields.Binary(string="Impresión")