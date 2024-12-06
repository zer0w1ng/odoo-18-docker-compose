from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date

class BusRoutes(models.Model):
    _name = "bus.routes"
    _description = "Bus Routes"

    name = fields.Char(string="Name", required=True, copy=False, readonly=True,
                       index=True, default=lambda self: _("New"))
    m2o_fleet_vehicle_id = fields.Many2one("fleet.vehicle",
                                        string="Bus")
    m2o_bus_point_pickup_id = fields.Many2one("bus.point",
                                        string="Pick-up")
    m2o_bus_point_dropoff_id = fields.Many2one("bus.point",
                                        string="Drop off")
    journey_date = fields.Date(string="Journey Date")
    start_time = fields.Datetime(string="Start Time")
    end_time = fields.Datetime(string="End Time")
    bus_routes_line_ids = fields.One2many("bus.routes.line","m2o_bus_routes_id",
                                          string="Routes Line")

    @api.model_create_multi
    def create(self, vals_list):
        templates = super(BusRoutes, self).create(vals_list)
        for template, vals in zip(templates, vals_list):    
            if template.name == _("New"):
                template.name = self.env["ir.sequence"].next_by_code \
                            ("bus.routes") or _("New")
        return templates

    @api.constrains('start_time', 'end_time', 'journey_date')
    def time_constrains(self):
        if self.journey_date < date.today():
            raise ValidationError("You can not add past date")
