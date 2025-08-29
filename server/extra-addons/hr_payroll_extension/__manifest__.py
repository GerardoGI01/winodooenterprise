# -*- coding: utf-8 -*-
{
    'name': "HR Payroll Extension",

    'version': '18.0',
    'summary': "Extensión de nómina y RRHH en Odoo",
    'description': """
Módulo de extensión para la gestión de nómina en Odoo.
=======================================================
Este módulo agrega campos y funcionalidades adicionales 
para los procesos de Recursos Humanos y Nómina:

- Extiende los modelos de empleados.
- Añade mejoras en el manejo de ausencias y permisos.
- Integra funciones adicionales con nómina contable.
    """,

    'author': "",
    'website': "",
    'license': 'OPL-1',
    'category': 'Human Resources/Payroll',
    'depends': [
        'base',
        'hr',
        'contacts',
        'hr_payroll',
        'hr_payroll_account',
    ],

    'data': [
        'views/hr_leave_view.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}

