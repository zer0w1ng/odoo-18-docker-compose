from odoo import api, models, fields

class accountTax(models.Model):
    """Extend account.tax with BIR tax type classification"""
    _inherit = 'account.tax'
    
    l10n_ph_bir_tax_type = fields.Selection([
        ('vat', 'VAT (12%)'),
        ('vat_exempt', 'VAT-Exempt'),
        ('zero_rated', 'Zero-Rated'),
        ('non_vat', 'Non-VAT'),
    ], string='BIR Tax Type', 
       help='Classification for BIR reporting in Philippines')
    
    l10n_ph_bir_tax_code = fields.Char(
        string='BIR Tax Code',
        help='BIR-specific tax code for reporting')
    
    l10n_ph_atc_code = fields.Char(
        string='ATC Code',
        help='Alphanumeric Tax Code for withholding tax')
    
    is_bir_compliant = fields.Boolean(
        string='BIR Compliant',
        compute='_compute_is_bir_compliant',
        store=True,
        help='Indicates if this tax has BIR classification')
    
    @api.depends('l10n_ph_bir_tax_type')
    def _compute_is_bir_compliant(self):
        """Mark taxes that have BIR classification"""
        for tax in self:
            tax.is_bir_compliant = bool(tax.l10n_ph_bir_tax_type)
