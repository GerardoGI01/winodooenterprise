from odoo import models,fields, api
import logging

_logger = logging.getLogger(__name__)

class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    is_send_mail = fields.Boolean(string='Envio Nómina Aútomatico')


