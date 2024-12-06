from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = "sale.order"

    m2o_bus_point_pickup_id = fields.Many2one("pickup.dropoff.points",
                                        string="Pick-up")
    m2o_bus_point_dropoff_id = fields.Many2one("pickup.dropoff.points",
                                        string="Drop off")
    start_time = fields.Datetime(string="Pickup Start Time")
    end_time = fields.Datetime(string="Drop off End Time")
    journey_date = fields.Date("Journey Date")
    m2o_bus_start_point_id = fields.Many2one("bus.point",
                                        string="Start Point")
    m2o_bus_end_point_id = fields.Many2one("bus.point",
                                        string="End Point")
    point_start_time = fields.Datetime(string="Start Time")
    point_end_time = fields.Datetime(string="End Time")
    trip_information_id = fields.Many2one("trip.information",
                                        "Trip Info")
    is_bus_order = fields.Boolean("Is bus order?", copy=False)

    def button_register_payment(self):
        self.action_confirm()
        customer_invoice_id = self._create_invoices(final=True)
        if customer_invoice_id:
            customer_invoice_id.action_post()
            return customer_invoice_id.action_register_payment()

    def _get_confirmation_template(self):
        res = super(SaleOrder, self)._get_confirmation_template()
        template_id = res
        if self.is_bus_order:
            template_id = self.env.ref('bi_bus_booking_management.mail_template_ticket_confirmation', raise_if_not_found=False)
        return template_id
