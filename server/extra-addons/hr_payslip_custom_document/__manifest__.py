# -*- coding: utf-8 -*-
{
    'name': "Documento de nómina",
    'version': '18.0',
    'license': 'OPL-1',
    'category': 'Human Resources/Payroll',

    'summary': """
        Extiende la gestión de nómina para generar documentos adicionales y configuraciones en recibos de pago.
    """,

    'description': """
        Este módulo agrega funcionalidades adicionales al módulo de nómina en Odoo, 
        permitiendo la generación de archivos TXT, configuraciones específicas por compañía 
        y la personalización de documentos de empleados y corridas de nómina.
        
        Funcionalidades principales:
        - Generación de archivo TXT desde los recibos de nómina.
        - Extensión de la vista de empleados para datos adicionales.
        - Configuración de la compañía para documentos de nómina.
        - Personalización en las corridas de nómina.
    """,

    'author': "",
    'website': "",

    'depends': [
        'base',
        'hr',
        'hr_payroll',
    ],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/create_txt.xml',
        'views/hr_payslip_run.xml',
        'views/hr_employee.xml',
        'views/res_company.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
