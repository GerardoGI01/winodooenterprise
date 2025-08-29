from odoo import models, fields, api, _
import logging


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    fecha_de_pago = fields.Date(
        string="Fecha de pago",
        default=fields.Date.today)
    secuencia_envio = fields.Char(
        string='Secuencia',
        size=2,
        help="Se debe poner AA, BB, CC ... solo una secuencia al dia")
    numero_cuenta_cliente = fields.Char(
        string='Cuenta salida',
        size=11,
        help="Cuenta desde la que se realiza el pago")
    descripcion_transacciones = fields.Char(
        string='Descripcion transaccion',
        size=10,
        help="Descripcion para el nombre del archivo")
    tipo_cuenta = fields.Selection([
        ('S', 'Ahorros'),
        ('D', 'Corriente'),],string="Tipo", default="S")
    mostrar_campos_modulo = fields.Boolean(
        string='Mostrar Campos del Módulo',
        related="company_id.mostrar_campos_modulo")
    bancolombia_otros = fields.Boolean(
        string='PAB solo bancolombia',
        default=True)


    def llamar_generar_archivo_txt(self):
        create_text = self.env['create.txt'].create({})
        return create_text.generar_archivo_txt(self.id)
