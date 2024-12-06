from odoo import api, fields, models, _

class BusPoint(models.Model):
    _name = "bus.point"
    _description = "Bus Point"

    name = fields.Char(string="Name")
    m2m_pickup_dropoff_points_ids = fields.Many2many("pickup.dropoff.points",
                                        string="Pick-up Drop off Points")
