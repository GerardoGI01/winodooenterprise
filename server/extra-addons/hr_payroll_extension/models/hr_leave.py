from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import ValidationError

class HrPayslip(models.Model):
    _inherit = 'hr.leave'

    weekend_days = fields.Integer(string='Días hábiles', compute='_compute_weekend_days')
    monday_friday = fields.Boolean("Lunes a Viernes")
    monday_sunday = fields.Boolean("Lunes a Sabado")

    @api.constrains('monday_friday', 'monday_sunday')
    def _check_days_selection(self):
        for record in self:
            if record.monday_friday and record.monday_sunday:
                raise ValidationError("Por favor, solo seleccione una franja para los días hábiles.")
            if not record.monday_friday and not record.monday_sunday:
                raise ValidationError("Seleccione los días hábiles a tener en cuenta.")

    def _compute_weekend_days(self):
        for leave in self:
            weekday_days = 0
            current_date = leave.date_from

            if leave.monday_friday:
                valid_days = [0, 1, 2, 3, 4]
            elif leave.monday_sunday:
                valid_days = [0, 1, 2, 3, 4, 5]
            else:
                raise ValidationError("Seleccione los días hábiles a tener en cuenta.")

            while current_date <= leave.date_to:
                if current_date.weekday() in valid_days:
                    weekday_days += 1
                current_date += timedelta(days=1)

            leave.weekend_days = weekday_days