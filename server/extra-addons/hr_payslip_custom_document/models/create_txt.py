from odoo import models, fields, api, _
import base64
from io import BytesIO
from datetime import date
from odoo.exceptions import UserError
import logging


class CreateTxt(models.Model):
    _name = 'create.txt'

    archivo_txt = fields.Binary(
        'Archivo TXT',
        readonly=True)
    nombre_archivo = fields.Char(
        'Nombre del Archivo')
    

    def generar_archivo_txt(self, id):
        output = BytesIO()
        registros = self.env['hr.payslip.run'].search([('id', '=', id)])
        pago_total = 0
        for pay in registros.slip_ids:
            if registros.bancolombia_otros == True:
                if pay.employee_id.banco_bancolombia_code == '5600078':
                    pago_total += pay.line_ids.filtered(lambda line: line.code == 'pago_empleado').total
            else:
                if pay.employee_id.banco_bancolombia_code != '5600078':
                    pago_total += pay.line_ids.filtered(lambda line: line.code == 'pago_empleado').total
         
        company_id = registros.company_id
        tipo_registro = "1"
        nit_entidad = company_id.company_registry[:15].rjust(15, '0')
        filler = " ".rjust(15,' ')
        clase_transaccion = "225".rjust(3)
        descripcion_transacciones = 'PAGONOMINA'.ljust(10,' ')
        fecha_a = registros.fecha_de_pago.strftime('%Y%m%d').rjust(8,' ')
        secuencia_envio = registros['secuencia_envio']
        fecha_t = registros.fecha_de_pago.strftime('%Y%m%d').rjust(8,' ')
        if registros.bancolombia_otros == True:
            numero_registros = str(len(registros.slip_ids.filtered(lambda line: line.employee_id.banco_bancolombia_code  == '5600078'))).rjust(6, '0')  # Número total de registros, incluyendo el encabezado
        else:
            numero_registros = str(len(registros.slip_ids.filtered(lambda line: line.employee_id.banco_bancolombia_code  != '5600078'))).rjust(6, '0')  # Número total de registros, incluyendo el encabezado
        
        
        sumatoria_debitos = "0".rjust(17,'0')
        sumatoria_creditos = "{:.2f}".format(pago_total).replace('.', '').rjust(17,'0')
        numero_cuenta_cliente = registros['numero_cuenta_cliente'][:11].rjust(11, '0')
        tipo_cuenta_cliente = registros['tipo_cuenta'].rjust(1)      
        filler2 = " ".rjust(100)
        encabezado = f"{tipo_registro}{nit_entidad}I{filler}{clase_transaccion}{descripcion_transacciones}{fecha_a}{secuencia_envio}{fecha_t}{numero_registros}{sumatoria_debitos}{sumatoria_creditos}{numero_cuenta_cliente}{tipo_cuenta_cliente}{filler2}\n"
        output.write(encabezado.encode('utf-8'))

        for registro in registros.slip_ids:
            if registros.bancolombia_otros == True:
                if registro.employee_id.banco_bancolombia_code == '5600078':

                    nit_beneficiario = str(registro.employee_id.identification_id)[:15].rjust(15,'0')

                    nombre_beneficiario = str(registro.employee_id.name)[:30].ljust(30,' ')
                    bank = registro.employee_id.banco_bancolombia_code
                    if not bank:
                        raise UserError(f"El empleado {registro.employee_id.name} no tiene configurada la cuenta")

                    banco_beneficiario = str(bank).rjust(9,'0')

                    num_cuenta_beneficiario = str(registro.employee_id.bank_account_id.acc_number)[:17].ljust(17,' ')
                    tipo_cuenta_t = " "

                    if not registro.employee_id.tipo_cuenta:
                        raise UserError(f"El empleado {registro.employee_id.name} no tiene configurado el tipo de cuenta")
                    tipo_transaccion = str(registro.employee_id.tipo_cuenta).rjust(2)


                    valor_transaccion = "{:.2f}".format(registro.line_ids.filtered(lambda line: line.code == 'pago_empleado').total).replace('.', '').rjust(17,'0')

                    fecha_aplicacion = "0".rjust(9,'0')

                    referencia_pago = str(registros['descripcion_transacciones'])[:6].ljust(6,' ')

                    filler3 = " ".rjust(121,' ')

                    linea = f"6{nit_beneficiario}{nombre_beneficiario}{banco_beneficiario}{num_cuenta_beneficiario}{tipo_cuenta_t}{tipo_transaccion}{valor_transaccion}{fecha_aplicacion}{referencia_pago}{filler3}\n"                
                    output.write(linea.encode('utf-8'))
            else:
                if registro.employee_id.banco_bancolombia_code != '5600078':

                    nit_beneficiario = str(registro.employee_id.identification_id)[:15].rjust(15,'0')
                    nombre_beneficiario = str(registro.employee_id.name)[:30].ljust(30,' ')
                    bank = registro.employee_id.banco_bancolombia_code
                    if not bank:
                        raise UserError(f"El empleado {registro.employee_id.name} no tiene configurada la cuenta")

                    banco_beneficiario = str(bank).rjust(9,'0')
                    num_cuenta_beneficiario = str(registro.employee_id.bank_account_id.acc_number)[:17].ljust(17,' ')
                    tipo_cuenta_t = " "

                    if not registro.employee_id.tipo_cuenta:
                        raise UserError(f"El empleado {registro.employee_id.name} no tiene configurado el tipo de cuenta")
                    tipo_transaccion = str(registro.employee_id.tipo_cuenta).rjust(2)
                    valor_transaccion = "{:.2f}".format(registro.line_ids.filtered(lambda line: line.code == 'pago_empleado').total).replace('.', '').rjust(17,'0')
                    fecha_aplicacion = "0".rjust(9,'0')
                    referencia_pago = str(registros['descripcion_transacciones'])[:6].ljust(6,' ')
                    filler3 = " ".rjust(121,' ')
                    linea = f"6{nit_beneficiario}{nombre_beneficiario}{banco_beneficiario}{num_cuenta_beneficiario}{tipo_cuenta_t}{tipo_transaccion}{valor_transaccion}{fecha_aplicacion}{referencia_pago}{filler3}\n"                
                    output.write(linea.encode('utf-8'))

        self.archivo_txt = base64.encodebytes(output.getvalue())
        self.nombre_archivo = f"PAB{numero_cuenta_cliente}{fecha_a}{descripcion_transacciones[:2]}.txt"
        output.close()

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self._name}/{self.id}/archivo_txt/{self.nombre_archivo}?download=true',
            'target': 'new',
        }
