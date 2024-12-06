# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import json
import base64
import odoo
import odoo.release
from odoo.exceptions import UserError, ValidationError

class BusBookSeat(models.TransientModel):
    _name = "bus.book.seat"
    _description = "Bus Book Seat"

    m2o_fleet_vehicle_id = fields.Many2one("fleet.vehicle",
                               string="Bus")
