from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class BusTypes(models.Model):
    _name = "bus.types"
    _description = "Bus Types"

    name = fields.Char(string="Name")
    total_row = fields.Integer("Total Row")
    total_seat_in_single_row = fields.Integer("Total Seat in Single row")
    bus_type = fields.Selection([("seating", "Seating"),("sleeper", "Sleeper")],
                                default="seating", string="Bus Type")

    @api.constrains('total_row', 'total_seat_in_single_row')
    def row_constrains(self):
        if self.total_row > 5:
            raise ValidationError("You can not add row more than 5.")
        if self.total_row <= 0:
            raise ValidationError("Please add valid row.")
        if self.total_seat_in_single_row > 12:
            raise ValidationError("You can not add row more than 12.")
        if self.total_seat_in_single_row <= 0:
            raise ValidationError("Please add valid row.")
