{
    "name": "Seguridad social (Colombia)",
    "version": "18.0",
    "summary": "Gestión de seguridad social para empleados en Colombia",
    "description": """
Módulo para gestionar la seguridad social en Colombia dentro de Odoo HR.

Características principales:
- Campos adicionales en empleados y contratos.
- Configuración de empresa relacionada con seguridad social.
- Reportes y wizard para generación de informes.
- Integración con vacaciones (hr_holidays).
    """,
    "author": "",
    "website": "",
    "category": "Human Resources",
    "license": "LGPL-3",
    "depends": [
        "base",
        "hr",
        "contacts",
        "hr_holidays",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_employee_view.xml",
        "views/hr_contract.xml",
        "views/hr_leave_type.xml",
        "views/res_company_view.xml",
        "wizard/social_security_report.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
