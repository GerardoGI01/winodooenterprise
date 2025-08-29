{
    "name": "Extensión básica de Recursos Humanos",
    "version": "18.0",
    "summary": "Extensiones básicas para módulos de Recursos Humanos",
    "description": """
Este módulo hereda y amplía funcionalidades de Recursos Humanos,
añadiendo campos, vistas y asistentes personalizados para la gestión
de empleados, contratos, nómina y ausencias.
    """,
    "author": "",
    "website": "",
    "category": "Human Resources",
    "license": "LGPL-3",
    "depends": [
        "base",
        "contacts",
        "product",
        "hr",
        "hr_payroll",
        "hr_payroll_account",
        "hr_holidays",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_employee.xml",
        "views/res_partner.xml",
        "views/hr_salary_rule.xml",
        "views/hr_contract.xml",
        "views/hr_leave_view.xml",
        "wizard/wizard_vacation_report.xml",
        "views/hr_paysilp_run.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
