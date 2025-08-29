{
    'name': "Préstamos",
    'version': '18.0',
    'summary': "Gestión de préstamos para empleados",
    'description': """
Módulo de gestión de préstamos en Recursos Humanos.
====================================================
Este módulo extiende las funcionalidades de RRHH para administrar:
- Registro de préstamos a empleados.
- Integración con nómina.
- Vínculo con contabilidad y contactos.
    """,
    'author': "",
    'website': "",
    'category': 'Human Resources',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr',
        'contacts',
        'hr_payroll',
        'hr_payroll_account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_loans_view.xml',
        'views/hr_paylisp.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}
