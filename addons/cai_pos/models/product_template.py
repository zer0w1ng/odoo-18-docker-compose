# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    """
    Extend Product Template to add BIR discount eligibility configuration.
    
    Per Philippine BIR regulations and RA 9442 (Magna Carta for PWD), 
    RA 9994 (Senior Citizens Act), some items may be excluded from 
    PWD/SC discounts if they are:
    - Already sold at maximum retail price (e.g., medicine with DOH SRP)
    - Excluded by specific regulations
    - Non-essential items per establishment policy
    """
    _inherit = 'product.template'

    is_bir_discountable = fields.Boolean(
        string='PWD/SC Discountable',
        default=True,
        help='If checked, this product is eligible for Senior Citizen and PWD discounts.\n\n'
             'Uncheck for items like:\n'
             '• Medicine/medical supplies already at maximum retail price per DOH circular\n'
             '• Items specifically excluded by regulations\n'
             '• Non-essential items per establishment policy\n\n'
             'Note: Most products should remain discountable to comply with RA 9442 and RA 9994.')
    
    bir_discount_exclusion_reason = fields.Char(
        string='Exclusion Reason',
        help='Document why this product is not PWD/SC discountable.\n'
             'Example: "Already at maximum retail price per DOH Circular 2009-0011"')
    
    bir_discountable_notes = fields.Text(
        string='Discount Notes',
        help='Additional notes about discount eligibility for this product')


class ProductProduct(models.Model):
    """
    Extend Product Product to make the field accessible at variant level.
    """
    _inherit = 'product.product'
    
    is_bir_discountable = fields.Boolean(
        related='product_tmpl_id.is_bir_discountable',
        string='PWD/SC Discountable',
        store=True,
        readonly=False,
        help='Whether this product variant is eligible for PWD/SC discounts')
    
    @api.model
    def _load_pos_data_fields(self, config_id):
        """
        Add BIR discount eligibility field to POS data loading.
        This ensures the field is available in the frontend for discount checks.
        """
        fields = super()._load_pos_data_fields(config_id)
        fields.append('is_bir_discountable')
        return fields

