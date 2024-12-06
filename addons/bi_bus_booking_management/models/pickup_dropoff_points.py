from odoo import api, fields, models, _

class PickupDroppoffPoints(models.Model):
    _name = "pickup.dropoff.points"
    _description = "Pick up Dropp off Points"

    name = fields.Char(string="Name")
