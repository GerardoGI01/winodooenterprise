from odoo import models


class AccountOnlineLink(models.Model):
    _inherit = 'account.online.link'

    def _update_payments_activated(self, data):
        self.ensure_one()

        if not self.provider_type:
            self.provider_type = ''

        # Hacky way to know whether the synchronization has payment enabled/activated or not
        if data.get('is_payment_enabled') is not None and 'payment' not in self.provider_type:
            self.provider_type = f'{self.provider_type}_payment'

        if data.get('is_payment_activated') is not None and 'activated' not in self.provider_type:
            self.provider_type = f'{self.provider_type}_activated'

    def _update_connection_status(self):
        # EXTENDS account_online_synchronization
        data = super()._update_connection_status()

        self._update_payments_activated(data)

        return data
