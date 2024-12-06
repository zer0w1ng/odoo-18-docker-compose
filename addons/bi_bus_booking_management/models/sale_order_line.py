from odoo import api, fields, models, _

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    seat_number = fields.Char("Seat No")
    customer_name = fields.Char("Customer Name")
    email = fields.Char("Email")
    age = fields.Integer("Age")
    gender = fields.Char("Gender")
    number = fields.Char("Number")
    bus_routes_line_id = fields.Many2one("bus.routes.line",
                                    string="Route line ID")
    status_booking = fields.Selection([("booked", "Confirm"),("cancel", "Cancel")], string="Booking Status",default='booked')
