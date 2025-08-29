from odoo import models, fields, api, _
import logging


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    mostrar_campos_modulo = fields.Boolean(
        string='Mostrar Campos del Módulo',
        related="company_id.mostrar_campos_modulo")
    tipo_cuenta = fields.Selection([
        ('37', 'Ahorros'),
        ('27', 'Corriente'),],string="Tipo")
    banco_bancolombia_code = fields.Selection([
            ('1059', 'BANCAMIA S.A'),
            ('1040', 'BANCO AGRARIO'),
            ('6013677', 'BANCO AV VILLAS'),
            ('1805', 'BANCO BTG PACTUAL'),
            ('5600829', 'BANCO CAJA SOCIAL BCSC SA'),
            ('1066', 'BANCO COOPERATIVO COOPCENTRAL'),
            ('1558', 'BANCO CREDIFINANCIERA SA.'),
            ('5895142', 'BANCO DAVIVIENDA SA'),
            ('5600010', 'BANCO DE BOGOTA'),
            ('5600230', 'BANCO DE OCCIDENTE'),
            ('1062', 'BANCO FALABELLA S.A.'),
            ('1063', 'BANCO FINANDINA S.A.'),
            ('5600120', 'BANCO GNB SUDAMERIS'),
            ('1071', 'BANCO J.P. MORGAN COLOMBIA S.A'),
            ('1064', 'BANCO MULTIBANK S.A.'),
            ('1047', 'BANCO MUNDO MUJER'),
            ('1060', 'BANCO PICHINCHA'),
            ('5600023', 'BANCO POPULAR'),
            ('1058', 'BANCO PROCREDIT COL'),
            ('1065', 'BANCO SANTANDER DE NEGOCIOS CO'),
            ('1069', 'BANCO SERFINANZA S.A'),
            ('1303', 'BANCO UNION S.A'),
            ('1053', 'BANCO W S.A'),
            ('1031', 'BANCOLDEX S.A.'),
            ('5600078', 'BANCOLOMBIA'),
            ('1061', 'BANCOOMEVA'),
            ('5600133', 'BBVA COLOMBIA'),
            ('1808', 'BOLD CF'),
            ('5600094', 'CITIBANK'),
            ('1812', 'COINK'),
            ('1370', 'COLTEFINANCIERA S.A'),
            ('1292', 'CONFIAR COOPERATIVA FINANCIERA'),
            ('1291', 'COOFINEP COOPERATIVA FINANCIER'),
            ('1283', 'COOPERATIVA FINANCIERA DE ANTI'),
            ('1289', 'COOTRAFA COOPERATIVA FINANCIER'),
            ('1551', 'DAVIPLATA'),
            ('1802', 'DING TECNIPAGOS SA'),
            ('1121', 'FINANCIERA JURISCOOP S.A. COMP'),
            ('1814', 'GLOBAL66'),
            ('5600104', 'HSBC'),
            ('1637', 'IRIS'),
            ('5600146', 'ITAU'),
            ('5600065', 'ITAU antes Corpbanca'),
            ('1286', 'JFK COOPERATIVA FINANCIERA'),
            ('1070', 'LULO BANK S.A.'),
            ('1067', 'MIBANCO S.A.'),
            ('1801', 'MOVII'),
            ('1507', 'NEQUI'),
            ('1560', 'PIBANK'),
            ('1803', 'POWWI'),
            ('1811', 'RAPPIPAY'),
            ('1813', 'SANTANDER CONSUMER'),
            ('5600191', 'SCOTIABANK COLPATRIA S.A'),
            ('1804', 'Ualá'),
    ], string='Codigo Bancolombia')
