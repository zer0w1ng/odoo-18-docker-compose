# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import json
import base64
import odoo
import odoo.release
from odoo.exceptions import UserError, ValidationError
from datetime import date

class BusBooking(models.TransientModel):
    _name = "bus.booking"
    _description = "Bus Booking"

    m2o_bus_point_pickup_id = fields.Many2one("bus.point",
                                        string="Start Point")
    m2o_bus_point_dropoff_id = fields.Many2one("bus.point",
                                        string="End Point")
    m2o_bus_types_id = fields.Many2one("bus.types", string="Bus Type")
    journey_date = fields.Date(string="Journey Date")

    def button_search_buses(self):
        if self.journey_date and self.journey_date < date.today():
            raise ValidationError("You can not select the past date.")
        bus_routes_line_obj = self.env["bus.routes.line"]
        domain = [
            ("m2o_bus_point_pickup_id", "=", self.m2o_bus_point_pickup_id.id),
            ("m2o_bus_point_dropoff_id", "=", self.m2o_bus_point_dropoff_id.id),
            ("journey_date", "=", self.journey_date),
            ("m2o_bus_types_id", "=", self.m2o_bus_types_id.id),
                 ]
        bus_routes_ids = bus_routes_line_obj.search(domain)
        if bus_routes_ids:
            return{
                    "name":"Results",
                    "view_mode": "list",
                    "res_model": "bus.routes.line",
                    "type": "ir.actions.act_window",
                    "target": "current",
                    "domain":[("id", "in", bus_routes_ids.ids)],
            }
        else:
            raise ValidationError(_("Buses not available"))
            
