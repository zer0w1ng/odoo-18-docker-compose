from odoo import api, fields, models, _

class BusAmenities(models.Model):
    _name = "bus.amenities"
    _description = "Bus Amenities"

    name = fields.Char(string="Name")
