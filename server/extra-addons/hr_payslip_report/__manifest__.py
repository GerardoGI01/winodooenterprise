# -*- coding: utf-8 -*-
{
    "name": "Reporte personalizado nómina",
    "version": "1.0",
    "summary": "Custom report templates for HR payslips",
    "description": """
        Este módulo agrega plantillas personalizadas de reportes para
        nóminas (payslips) en el módulo de Recursos Humanos (HR).
    """,
    "category": "Human Resources",
    "author": "",
    "website": "",
    
    "depends": [
        "base",
        "hr",
    ],

    "data": [
        "views/report_payslip_templates.xml",
    ],

    "installable": True,
    "auto_install": False,
    "application": True,
    "currency": "COP",
}
