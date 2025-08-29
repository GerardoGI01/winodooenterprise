from odoo import http
from odoo.http import request
import logging


class PayslipResponse(http.Controller):

    @http.route('/payslip/response/<int:payslip_id>/<string:response>/<string:token>', type='http', auth='public')    
    def payslip_response(self, payslip_id, response, token, **kwargs):
        payslip = request.env['hr.payslip'].sudo().search([('token', '=', token)])

        if payslip.exists() and payslip.token == token:
            if response == 'accept':
                payslip.message_post(body="La nómina ha sido aceptada por el empleado.")
                payslip.write({'email_state_response': 'accepted'})
            elif response == 'reject':
                payslip.message_post(body="La nómina ha sido rechazada por el empleado.")
                payslip.write({'email_state_response': 'rejected'})            
            return "Gracias por su respuesta."
        else:
            return "Acceso denegado o nómina no encontrada."