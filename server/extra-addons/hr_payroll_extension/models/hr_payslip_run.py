from odoo import models,fields, api
import logging
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def mail_payslips(self):
        """
        Llama a la función send_mail_paylisp de cada nómina asociada al lote de nóminas (payslip run).
        """
        for record in self:
            for payslip in record.slip_ids:
                if payslip.state != 'done':
                    raise ValidationError(
                        'No es posible enviar los recibos de nómina, verifica que los recibos de nómina se encuentren en estado "DONE"')
                    continue

                try:
                    payslip.send_mail_paylisp()
                    _logger.info(f"Correo enviado para la nómina con ID: {payslip.id}")
                except Exception as e:
                    _logger.error(f"Error al enviar correo para la nómina con ID: {payslip.id}: {e}")


