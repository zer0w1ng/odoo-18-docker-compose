from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    bir_config_id = fields.Many2one(
        'bir.config',
        string='BIR Configuration',
        domain="[('company_id', '=', company_id), ('active', '=', True)]",
        help='BIR compliance settings for this POS terminal'
    )
    
    @api.constrains('bir_config_id', 'company_id')
    def _check_bir_config_company(self):
        """Ensure BIR config belongs to the same company as POS config"""
        for config in self:
            if config.bir_config_id and config.bir_config_id.company_id != config.company_id:
                raise ValidationError(
                    _("The BIR Configuration must belong to the same company as the POS Configuration.")
                )
    
    def _get_forbidden_change_fields(self):
        """Add bir_config_id to forbidden fields during active session"""
        forbidden_keys = super()._get_forbidden_change_fields()
        forbidden_keys.append('bir_config_id')
        return forbidden_keys
