from odoo import api, fields, models, _

class BusBrand(models.Model):
    _name = "bus.brand"
    _description = "Bus Brand"

    name = fields.Char(string="Name")
