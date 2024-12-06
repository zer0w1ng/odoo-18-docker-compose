from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _send_payment_succeeded_for_order_mail(self):
        """ Send a mail to the SO customer to inform them that a payment has been initiated.

        :return: None
        """
        mail_template = self.env.ref(
            'sale.mail_template_sale_payment_executed', raise_if_not_found=False
        )
        for order in self:
            ### START ###
            if order.is_bus_order:
                mail_template = self.env.ref('bi_bus_booking_management.mail_template_ticket_confirmation', raise_if_not_found=False)
            ### STOP ###
            order._send_order_notification_mail(mail_template)

    def button_register_payment(self):
        self.action_confirm()
        customer_invoice_id = self._create_invoices(final=True)
        if customer_invoice_id:
            customer_invoice_id.action_post()
            return customer_invoice_id.action_register_payment()