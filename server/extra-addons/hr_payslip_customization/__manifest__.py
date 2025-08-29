# -*- coding: utf-8 -*-
{
    'name': "Personalizaciones de nómina",
    'version': '18.0',
    'summary': "Personalización de Nómina (Payslip)",
    'description': """
Módulo para extender y personalizar la funcionalidad de las nóminas en Odoo.
Incluye vistas adicionales y modificaciones en el modelo de `hr.payslip`.
    """,
    'category': 'Human Resources/Payroll',
    'author': "",
    'website': "",
    'license': 'OPL-1',

    # Dependencias necesarias
    'depends': [
        'base',
        'hr_payroll',
    ],

    # Archivos cargados
    'data': [
        'views/hr_payslip.xml',
        'views/hr_payslip_replace.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
