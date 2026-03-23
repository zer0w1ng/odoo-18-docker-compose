from odoo import api, fields, models, _
import uuid


class BIRConfig(models.Model):
    _name = 'bir.config'
    _description = 'BIR Configuration'
    _rec_name = 'name'
    _inherit = ['pos.load.mixin']

    name = fields.Char(string='Name', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, 
                                default=lambda self: self.env.company)
    
    # Company/Business Information (for receipt)
    business_name = fields.Char(
        string='Registered Business Name',
        help='Business name as registered with BIR (appears on receipt)'
    )
    business_address = fields.Text(
        string='Business Address',
        help='Complete business address for receipt'
    )
    
    # BIR Registration
    tin = fields.Char(string='TIN', required=True, help='Tax Identification Number')
    permit_number = fields.Char(string='BIR Permit Number', required=True)
    permit_date_issued = fields.Date(string='Permit Date Issued')
    permit_valid_until = fields.Date(string='Permit Valid Until')
    
    # BIR Accreditation
    accreditation_number = fields.Char(
        string='Accreditation Number',
        help='BIR POS system accreditation number'
    )
    min_number = fields.Char(
        string='MIN',
        help='Machine Identification Number'
    )
    serial_number = fields.Char(
        string='Serial Number',
        help='POS terminal serial number'
    )
    branch_code = fields.Char(
        string='Branch Code',
        size=2,
        required=True,
        default='01',
        help='2-digit branch code for eSales (e.g., 01 for main branch, 02 for branch 2)'
    )
    
    # POS Terminal Information
    terminal_id = fields.Char(
        string='Terminal ID',
        help='Unique identifier for this POS terminal'
    )
    pos_machine_brand = fields.Char(
        string='POS Machine Brand/Model',
        help='Brand and model of POS hardware'
    )
    
    # POS Software
    pos_software_name = fields.Char(
        string='POS Software Name',
        default='Odoo POS',
        help='Name of POS software'
    )
    pos_software_version = fields.Char(
        string='POS Software Version',
        default='18.0',
        help='Version of POS software'
    )
    
    # Receipt Numbering
    receipt_prefix = fields.Char(
        string='Receipt Prefix',
        default='OR',
        help='Prefix for receipt numbers (e.g., OR, SI)'
    )
    current_receipt_number = fields.Integer(
        string='Current Receipt Number',
        default=1,
        help='Current receipt serial number for this terminal'
    )
    
    # Z-Reading
    z_reading_counter = fields.Integer(
        string='Z-Reading Counter',
        default=0,
        help='Number of Z-readings generated'
    )
    last_z_reading_date = fields.Date(
        string='Last Z-Reading Date',
        help='Date of last Z-reading'
    )
    
    # Validity
    valid_from = fields.Date(string='Valid From')
    valid_until = fields.Date(string='Valid Until')
    
    active = fields.Boolean(default=True)
    
    @api.constrains('company_id', 'active')
    def _check_active_config(self):
        """Ensure only one active BIR configuration per company"""
        for record in self:
            if record.active:
                existing = self.search([
                    ('company_id', '=', record.company_id.id),
                    ('active', '=', True),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise models.ValidationError(
                        _("Only one active BIR configuration is allowed per company."))
    
    @api.constrains('permit_valid_until')
    def _check_permit_validity(self):
        """Warn if permit is expired or expiring soon"""
        from datetime import date, timedelta
        for record in self:
            if record.permit_valid_until:
                if record.permit_valid_until < date.today():
                    raise models.ValidationError(
                        _("BIR Permit has expired. Please renew your permit before using this configuration."))
                elif record.permit_valid_until < date.today() + timedelta(days=30):
                    # This is just a warning, not blocking
                    pass
    
    @api.constrains('current_receipt_number')
    def _check_receipt_number(self):
        """Ensure receipt number is positive"""
        for record in self:
            if record.current_receipt_number < 1:
                raise models.ValidationError(
                    _("Receipt number must be at least 1."))
    
    def get_next_receipt_number(self):
        """Get and increment the next receipt number with transaction safety"""
        self.ensure_one()
        import logging
        _logger = logging.getLogger(__name__)
        
        # Use database-level locking to prevent race conditions
        # This ensures that concurrent POS terminals cannot generate duplicate receipt numbers
        try:
            self.env.cr.execute(
                "SELECT current_receipt_number FROM bir_config "
                "WHERE id = %s FOR UPDATE NOWAIT",
                (self.id,)
            )
            result = self.env.cr.fetchone()
            if not result:
                raise models.ValidationError(_("BIR Config record not found"))
            
            current = result[0]
            
            # Update in same transaction
            self.env.cr.execute(
                "UPDATE bir_config SET current_receipt_number = %s WHERE id = %s",
                (current + 1, self.id)
            )
            
            receipt_no = f"{self.receipt_prefix}{current:08d}"
            _logger.info(f"Generated receipt number {receipt_no} for terminal {self.terminal_id}")
            
            return receipt_no
            
        except Exception as e:
            _logger.error(f"Failed to generate receipt number: {str(e)}")
            # If locking fails, fall back to regular method (with warning)
            _logger.warning("Using non-locked receipt number generation - potential race condition!")
            current = self.current_receipt_number
            self.write({'current_receipt_number': current + 1})
            return f"{self.receipt_prefix}{current:08d}"
    
    def increment_z_reading(self):
        """Increment Z-reading counter"""
        self.ensure_one()
        from datetime import date
        self.write({
            'z_reading_counter': self.z_reading_counter + 1,
            'last_z_reading_date': date.today()
        })
        return self.z_reading_counter
    
    # POS Load Mixin Implementation
    @api.model
    def _load_pos_data_domain(self, data):
        """Define which BIR config records to load for this POS session
        
        The data parameter is the response dictionary from pos.session.load_data()
        containing loaded model data. We extract the pos.config record to find the linked BIR config.
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            # data is a dictionary like: {'pos.config': {'data': [...], 'fields': [...]}, ...}
            # Get the first pos.config record if it exists
            if not isinstance(data, dict):
                _logger.warning(f"[BIR Config] Unexpected data type: {type(data)}, returning empty domain")
                return [('id', '=', False)]
            
            if 'pos.config' not in data or not data['pos.config'].get('data'):
                _logger.warning("[BIR Config] No pos.config data found in load data")
                return [('id', '=', False)]
            
            config_data = data['pos.config']['data']
            if not config_data:
                _logger.warning("[BIR Config] pos.config data list is empty")
                return [('id', '=', False)]
            
            # Get the first config's ID
            config_id = config_data[0].get('id')
            if not config_id:
                _logger.warning("[BIR Config] No config ID found in pos.config data")
                return [('id', '=', False)]
            
            config = self.env['pos.config'].browse(config_id)
            if not config.exists():
                _logger.warning(f"[BIR Config] POS Config with ID {config_id} does not exist")
                return [('id', '=', False)]
            
            if config.bir_config_id:
                _logger.info(f"[BIR Config] Loading BIR config: {config.bir_config_id.name} for POS: {config.name}")
                return [('id', '=', config.bir_config_id.id)]
            
            _logger.debug(f"[BIR Config] No BIR config linked to POS config: {config.name}")
            return [('id', '=', False)]
            
        except Exception as e:
            _logger.error(f"[BIR Config] Error in _load_pos_data_domain: {str(e)}", exc_info=True)
            return [('id', '=', False)]
    
    @api.model
    def _load_pos_data_fields(self, config_id):
        """Define which fields to load into POS frontend"""
        return [
            'name',
            'business_name',
            'business_address',
            'tin',
            'permit_number',
            'accreditation_number',
            'serial_number',
            'min_number',
            'terminal_id',
            'receipt_prefix',
            'current_receipt_number',
            'pos_software_name',
            'pos_software_version',
            'permit_valid_until',
            'valid_from',
            'valid_until',
        ]
