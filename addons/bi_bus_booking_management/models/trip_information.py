from odoo import api, fields, models, _

class TripInformation(models.Model):
    _name = "trip.information"
    _description = "Trip Information"

    name = fields.Char(string="Name", required=True, copy=False, readonly=True,
                       index=True, default=lambda self: _("New"))
    bus_routes_id = fields.Many2one("bus.routes",
                                        string="Route")
    m2o_fleet_vehicle_id = fields.Many2one("fleet.vehicle",
                                        string="Bus")
    m2o_bus_point_pickup_id = fields.Many2one("bus.point",
                                        string="Start Point")
    m2o_bus_point_dropoff_id = fields.Many2one("bus.point",
                                        string="End Point")
    journey_date = fields.Date(string="Journey Date")
    start_time = fields.Datetime(string="Start Time")
    end_time = fields.Datetime(string="End Time")
    trip_information_line_ids = fields.One2many("trip.information.line",
                                            "trip_information_id",
                                            string="Trip Info Line")

    total_seat = fields.Integer("Total Seat", compute="get_total_seat")
    booked_seat = fields.Integer("Booked Seat", compute="get_booked_seat")
    remaining_seat = fields.Integer("Remaining Seat", compute="get_remaining_seat")

    @api.model_create_multi
    def create(self, vals_list):
        templates = super(TripInformation, self).create(vals_list)
        for template, vals in zip(templates, vals_list):    
            if template.name == _("New"):
                template.name = self.env["ir.sequence"].next_by_code \
                            ("trip.information") or _("New")
        return templates

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

    def get_booked_seat(self):
        self.booked_seat = 0
        for rec in self:
            if rec.trip_information_line_ids:
                booked_list = rec.trip_information_line_ids.mapped('is_booked')
                if booked_list:
                    rec.booked_seat = len(booked_list)

    def get_remaining_seat(self):
        self.remaining_seat = 0
        for rec in self:
            if rec.trip_information_line_ids:
                booked_list = rec.trip_information_line_ids.mapped('is_booked')
                if booked_list:
                    rec.remaining_seat = rec.total_seat - len(booked_list)
