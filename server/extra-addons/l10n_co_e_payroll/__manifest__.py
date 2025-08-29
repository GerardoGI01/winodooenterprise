# -*- coding: utf-8 -*-
{
    "name": "Nómina Electrónica CO",
    "version": "18.0",
    "summary": "Implementación de la Nómina Electrónica para Colombia",
    "description": """
Módulo para la gestión y generación de la Nómina Electrónica en Colombia.
Incluye configuraciones, métodos de pago, reportes y ajustes a la nómina según la normativa local.
    """,
    "category": "Human Resources/Payroll",
    "author": "",
    "website": "",
    "license": "LGPL-3",
    "depends": [
        "base",
        "account",
        "hr_payroll",
        "hr_payroll_account",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/res_company_views.xml",
        "views/payroll_views.xml",
        "views/pay_method.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
