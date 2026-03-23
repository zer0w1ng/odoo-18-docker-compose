from odoo import models, fields, api 

class customDiscounts(models.Model): 
    _name = 'bir.discount.type'
    _description = 'BIR Discount Type'
    _inherit = ['pos.load.mixin']
    _order = 'sequence, name'

    name = fields.Char(
        string='Discount Name',
        required=True,
        translate=True,
        help='Display name for this discount type')

    code = fields.Char(
        string='Discount Code',
        required=True,
        help='Short code for identification (e.g., SC, PWD, GOV)')

    discount_percent = fields.Float(
        string='Discount %',
        default=20.0,
        help='Default discount percentage to apply')

    discount_type = fields.Selection([
        ('sc', 'Senior Citizen'),
        ('pwd', 'PWD (Person with Disability)'),
        ('gov', 'Government'),
        ('promo', 'Promotional'),
        ('other', 'Other')
    ], string='Type', required=True, default='promo')

    requires_id = fields.Boolean(
        string='Requires ID Verification',
        default=False,
        help='If checked, cashier must verify government-issued ID')

    is_vat_exempt = fields.Boolean(
        string='VAT-Exempt',
        default=False,
        help='If checked, sale becomes VAT-exempt after discount')

    bir_tax_id = fields.Many2one(
        'account.tax',
        string='BIR Tax to Apply',
        domain="[('l10n_ph_bir_tax_type', '=', 'vat_exempt')]",
        help='Tax to apply when this discount is used (usually VAT-Exempt)')

    bir_code = fields.Char(
        string='BIR Reporting Code',
        help='Code used in BIR reports and Z-readings')

    active = fields.Boolean(
        string='Active',
        default=True)

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of display in POS')


    # lambda: get company from database
    # "Give me the current user's company"
    # only called when creating a new record 
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company)

    available_in_pos = fields.Boolean(
        string='Available in POS',
        default=True,
        help='If checked, this discount will appear in POS interface')

    description = fields.Text(
        string='Description',
        help='Internal notes about this discount type')

    # Statistics
    usage_count = fields.Integer(
        string='Usage Count',
        compute='_compute_usage_count',
        help='Number of times this discount has been used')

    @api.depends()
    def _compute_usage_count(self):
        """Count how many times this discount type has been used"""
        for discount in self:
            count = self.env['pos.order'].search_count([('bir_discount_type_id', '=', discount.id)])
            discount.usage_count = count
    
    @api.model
    def _load_pos_data_domain(self, data):
        """
        Define which discount records to load in POS.
        Only load active discounts that are marked as available in POS.
        """
        return [('active', '=', True), ('available_in_pos', '=', True)]
    
    @api.model
    def _load_pos_data_fields(self, config_id):
        """
        Define which fields to load for each discount record in POS.
        These fields will be available in the JavaScript frontend.
        Including bir_tax_id so frontend can apply VAT-exempt tax to new items.
        """
        return [
            'name', 'code', 'discount_percent', 'discount_type',
            'requires_id', 'is_vat_exempt', 'sequence', 'bir_tax_id'
        ]
    
    _sql_constraints = [
        ('code_unique', 'unique(code, company_id)', 
         'Discount code must be unique per company!'),
    ]