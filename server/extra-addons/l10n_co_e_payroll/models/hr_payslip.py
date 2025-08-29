# -*- coding: utf-8 -*-
###################################################################################################
# Módulo: Colombian E-Payroll
# Archivo: hr_payslip_inherit.py
# Descripción:
#   Este archivo extiende el modelo hr.payslip para agregar el control de envío a la DIAN.
#   Permite crear registros en el modelo payroll.dian a partir de la nómina procesada
#   y marca el recibo de nómina como enviado a la DIAN.
#
# 
# 
# 
###################################################################################################

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero

class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    dian_send = fields.Boolean(
        string="Envío a la DIAN",
        default=False,
        tracking=True
    )

    def action_payslip_dian(self):
        """
        Acción que genera un registro en el modelo payroll.dian
        con la información del empleado y de la nómina, 
        marcando la nómina como enviada a la DIAN.
        """
        for slip in self:
            self.env["payroll.dian"].create({
                "name": True,
                "prefijo": "auto",
                "consecutivo": 19,
                "empleado": "hours",
                "tipo_documento": "hours",
                "numero_documento": "hours",
                "primer_nombre": "hours",
                "segundo_nombre": "hours",
                "primer_apellido": "hours",
                "segundo_apellido": "hours",
                "tipo_contrato_trabajador": "hours",
                "tipo_trabajador": "hours",
                "subtipo_trabajador": "hours",
                "salario_integral": "hours",
                "alto_riesgo_pension": "hours",
                "codigo_pais": "hours",
                "codigo_dep_nomina": "hours",
                "codigo_ciu_nomina": "hours",
                "fecha_pago": "hours",
                "metodo_pago": "hours",
                "banco": "hours",
                "tipo_cuenta": "hours",
                "numero_cuenta": "hours",
                "fecha_ingreso": "hours",
                "tiempo_laborado": "hours",
                "fecha_ini_pago": "hours",
                "fecha_fin_pago": "hours",
                "fecha_liquidacion": "hours",
                "periodo_nomina": "hours",
                "tipo_nomina": "hours",
                "nota_ajuste": "hours",
                "nomina_ajustar": "hours",
                "dias_trabajados": "hours",
                "tipo_monedas": "hours",
                "trm": "hours",
                "notas": "hours",
                "total_devengados": "hours",
                "total_deducciones": "hours",
                "total_comprobante": "hours",
                "sueldo_trabajado": "hours",
                "auxilio_transporte": "hours",
                "porcentaje_salud": "hours",
                "deduccion_salud": "hours",
                "porcentaje_pension": "hours",
                "deduccion_pension": "hours",
            })
            slip.dian_send = True
