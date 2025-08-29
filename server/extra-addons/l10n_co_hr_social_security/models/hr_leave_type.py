from odoo import models, fields, api

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    type_security = fields.Selection([('leave1','VACACIONES'),
            ('leave2','LICENCIAS NO REMUNERADAS'),
            ('leave3','INCAPACIDADES'),
            ('leave4','INCAPACIDAD PROFESIONAL'),
            ('leave5','LICENCIA MATERNIDAD'),('leave6','LICENCIAS REMUNERADAS')], string="Tipo de Ausencia-Aportes", required=True)
