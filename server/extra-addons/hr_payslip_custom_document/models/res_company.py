from odoo import models, fields, api, _
import logging


class ResCompany(models.Model):
    _inherit = 'res.company'

    mostrar_campos_modulo = fields.Boolean(
        string='PAB nomina Bancolombia')
