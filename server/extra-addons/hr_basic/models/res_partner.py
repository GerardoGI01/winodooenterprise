# ==========================================================================================
#   Autor:        Luis Felipe Paternina
#   Profesión:    Ingeniero de Sistemas
#   Email:        lfpaternina93@gmail.com
#   Teléfono:     +57 321 506 2353
#   Ubicación:    Bogotá, Colombia
# ==========================================================================================

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Contactos'

    # Indicadores de tipo de entidad
    is_eps = fields.Boolean(string="Es EPS")
    is_afp = fields.Boolean(string="Es Fondo de Pensiones")
    is_afc = fields.Boolean(string="Es Fondo de Cesantías")
    is_arl = fields.Boolean(string="Es Aseguradora de Riesgos Laborales")
    is_compensation_box = fields.Boolean(string="Es Caja de Compensación")

    # Cuentas contables relacionadas
    account_eps_id = fields.Many2one('account.account', string='Cuenta EPS')
    account_afp_id = fields.Many2one('account.account', string='Cuenta Pensión')
    account_afc_id = fields.Many2one('account.account', string='Cuenta Cesantías')
