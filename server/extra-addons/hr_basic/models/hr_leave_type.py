from odoo import models, fields, api

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    type_absence = fields.Selection([('absence1','Incapacidad'),
            ('absence2','Vacaciones'),
            ('absence3','Licencias'),
            ('absence4','Suspenciones'),
            ('absence4','Otros')], string="Tipo de Ausencia Informe")
