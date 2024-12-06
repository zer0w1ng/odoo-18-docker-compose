from odoo import api, fields, models, _

class TripInformationLine(models.Model):
    _name = "trip.information.line"
    _description = "Trip Information Line"

    trip_information_id = fields.Many2one("trip.information",
                                        string="Route")
    seat_number = fields.Char("Seat No")
    customer_name = fields.Char("Customer Name")
    email = fields.Char("Email")
    age = fields.Integer("Age")
    gender = fields.Char("Gender")
    number = fields.Char("Number")
    m2o_bus_point_pickup_id = fields.Many2one("pickup.dropoff.points",
                                        string="Pick-up")
    m2o_bus_point_dropoff_id = fields.Many2one("pickup.dropoff.points",
                                        string="Drop off")
    amount = fields.Float("Amount")
    start_time = fields.Datetime(string="Start Time")
    end_time = fields.Datetime(string="End Time")
    is_booked = fields.Boolean("Booked?", copy=False)
    booking_status = fields.Selection([("booked", "Confirm"), ("cancel", "Cancel")],
                                      string="Booking Status")

    def button_cancel_ticket(self):
        if self.is_booked:
            order_line = self.env['sale.order.line'].search([('seat_number','=',self.seat_number),('customer_name','=',self.customer_name),('order_id.trip_information_id','=',self.trip_information_id.id)])
            if order_line:
                for rec in order_line:
                    if rec.order_id.m2o_bus_point_pickup_id == self.m2o_bus_point_pickup_id and rec.order_id.start_time == self.start_time:
                        rec.status_booking = 'cancel'
            self.is_booked = False
            self.unlink()
