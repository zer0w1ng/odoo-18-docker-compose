from odoo import api, fields, models, _

class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    m2o_bus_brand_id = fields.Many2one("bus.brand", string="Barnd")
    m2o_bus_types_id = fields.Many2one("bus.types", string="Bus Type")
    m2m_bus_amenities_ids = fields.Many2many("bus.amenities", string="Amenities")
