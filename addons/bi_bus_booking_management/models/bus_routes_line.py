from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date

class BusRoutesLine(models.Model):
    _name = "bus.routes.line"
    _description = "Bus Routes Line"

    m2o_bus_routes_id = fields.Many2one("bus.routes",
                                        string="Route")
    m2o_fleet_vehicle_id = fields.Many2one("fleet.vehicle",
                               related="m2o_bus_routes_id.m2o_fleet_vehicle_id",
                               string="Bus", store=True)
    m2o_bus_types_id = fields.Many2one("bus.types",
                              related="m2o_fleet_vehicle_id.m2o_bus_types_id",
                              string="Bus Type", store=True)
    m2o_bus_point_pickup_id = fields.Many2one("bus.point",
                                        string="Start Point")
    m2o_bus_point_dropoff_id = fields.Many2one("bus.point",
                                        string="End Point")
    journey_date = fields.Date(string="Journey Date",
                               related="m2o_bus_routes_id.journey_date",
                               store=True)
    start_time = fields.Datetime(string="Start Time")
    end_time = fields.Datetime(string="End Time")
    price = fields.Float(string="Price")
    total_seat = fields.Integer("Total Seat", compute="get_total_seat")
    remaining_seat = fields.Integer("Remaining Seat", compute="get_remaining_seat")

    @api.constrains('start_time', 'end_time')
    def time_constrains(self):
        for rec in self:
            if rec.end_time < rec.start_time:
                raise ValidationError("You can not add past date and time to the end time.")

            if rec.m2o_bus_routes_id.start_time > rec.start_time:
                raise ValidationError("You cannot add higher than route start time.")

            if rec.m2o_bus_routes_id.end_time < rec.start_time:
                raise ValidationError("You cannot add higher than route end time.")

            if rec.m2o_bus_routes_id.end_time < rec.end_time:
                raise ValidationError("You cannot add higher than route end time.")

    def button_book(self):

        context = self.env.context.copy()
        bus_point_obj = self.env["bus.point"].sudo()
        context.update({
                        "default_routes_line_id":self.id,
                        "default_m2o_fleet_vehicle_id":self.m2o_fleet_vehicle_id.id,
                        "default_price":self.price,
                        "default_pick_up_drop_off_points_1":self.m2o_bus_point_pickup_id.m2m_pickup_dropoff_points_ids.ids,
                        "default_pick_up_drop_off_points_2":self.m2o_bus_point_dropoff_id.m2m_pickup_dropoff_points_ids.ids,
                        "default_m2m_bus_amenities_ids":self.m2o_fleet_vehicle_id.m2m_bus_amenities_ids.ids,
                        })
        return {
            "name": "Bus Book Seat",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "bus.book.seat",
            "target":"new",
            "context":context,
            'body': "body",
        }

    def get_total_seat(self):
        self.total_seat = 0
        for rec in self:
            if rec.m2o_fleet_vehicle_id \
                and rec.m2o_fleet_vehicle_id.m2o_bus_types_id \
                and rec.m2o_fleet_vehicle_id.m2o_bus_types_id.total_row \
                and rec.m2o_fleet_vehicle_id.m2o_bus_types_id.total_seat_in_single_row:
                total_row = rec.m2o_fleet_vehicle_id.m2o_bus_types_id.total_row
                total_seat_in_single_row = rec.m2o_fleet_vehicle_id.m2o_bus_types_id.total_seat_in_single_row
                rec.total_seat = total_row * total_seat_in_single_row

    def get_remaining_seat(self):
        self.remaining_seat = 0
        remaining_seat = 0
        trip_information_line_obj = self.env["trip.information.line"].sudo()
        for rec in self:
            trip_information_line = trip_information_line_obj.search([("trip_information_id.journey_date", "=", rec.journey_date),
                                          ("trip_information_id.m2o_fleet_vehicle_id", "=", rec.m2o_fleet_vehicle_id.id)])
            if trip_information_line:
                remaining_seat = trip_information_line[0].trip_information_id.remaining_seat
            else:
                total_row = rec.m2o_bus_types_id.total_row
                total_seat_in_single_row = rec.m2o_bus_types_id.total_seat_in_single_row
                remaining_seat = (total_row * total_seat_in_single_row)
            rec.remaining_seat = remaining_seat
