from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class PosXReading(models.Model):
    """
    X-Reading Report Model
    
    X-Reading is a non-reset sales report that shows cumulative sales
    since the last Z-reading. It can be generated multiple times per day
    without resetting counters.
    
    BIR Requirements:
    - Shows all sales transactions since last Z-reading
    - Does NOT reset counters
    - Includes VAT breakdown
    - Shows discount details
    - Lists payment methods
    - Can be printed multiple times
    """
    _name = 'pos.xreading'
    _description = 'POS X-Reading Report'
    _order = 'reading_date desc, id desc'
    _rec_name = 'reading_number'

    # ========== Header Information ==========
    reading_number = fields.Char(
        string='Reading Number',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default='New',
        help='Sequential X-reading number')
    
    reading_date = fields.Datetime(
        string='Reading Date',
        required=True,
        readonly=True,
        default=fields.Datetime.now,
        help='Date and time when X-reading was generated')
    
    session_id = fields.Many2one(
        'pos.session',
        string='POS Session',
        required=True,
        readonly=True,
        ondelete='restrict',
        help='POS session this reading belongs to')
    
    config_id = fields.Many2one(
        'pos.config',
        string='Point of Sale',
        readonly=True,
        compute='_compute_config_id',
        store=True,
        help='POS configuration')
    
    bir_config_id = fields.Many2one(
        'bir.config',
        string='BIR Configuration',
        readonly=True,
        help='BIR configuration at time of reading')
    
    user_id = fields.Many2one(
        'res.users',
        string='Cashier',
        required=True,
        readonly=True,
        default=lambda self: self.env.user,
        help='User who generated this reading')
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        readonly=True,
        default=lambda self: self.env.company)
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True)
    
    # ========== Period Information ==========
    period_start_date = fields.Datetime(
        string='Period Start',
        readonly=True,
        help='Start of reporting period (usually last Z-reading date)')
    
    period_end_date = fields.Datetime(
        string='Period End',
        readonly=True,
        help='End of reporting period (time of this X-reading)')
    
    last_z_reading_date = fields.Datetime(
        string='Last Z-Reading Date',
        readonly=True,
        help='Date of last Z-reading')
    
    z_counter = fields.Integer(
        string='Current Z-Counter',
        readonly=True,
        help='Number of Z-readings already done')
    
    # ========== Transaction Counts ==========
    transaction_count = fields.Integer(
        string='Total Transactions',
        readonly=True,
        help='Number of completed transactions')
    
    voided_transaction_count = fields.Integer(
        string='Voided Transactions',
        readonly=True,
        help='Number of voided transactions')
    
    refunded_transaction_count = fields.Integer(
        string='Refunded Transactions',
        readonly=True,
        help='Number of refunded transactions')
    
    # ========== Sales Amounts ==========
    gross_sales = fields.Monetary(
        string='Gross Sales',
        readonly=True,
        currency_field='currency_id',
        help='Total sales before discounts and taxes')
    
    total_discounts = fields.Monetary(
        string='Total Discounts',
        readonly=True,
        currency_field='currency_id',
        help='Total amount of all discounts')
    
    net_sales = fields.Monetary(
        string='Net Sales',
        readonly=True,
        currency_field='currency_id',
        help='Sales after discounts but before taxes')
    
    # ========== VAT Breakdown ==========
    vatable_sales = fields.Monetary(
        string='VATable Sales',
        readonly=True,
        currency_field='currency_id',
        help='Sales subject to 12% VAT (net of VAT)')
    
    vat_amount = fields.Monetary(
        string='VAT Amount (12%)',
        readonly=True,
        currency_field='currency_id',
        help='12% VAT on VATable sales')
    
    vat_exempt_sales = fields.Monetary(
        string='VAT-Exempt Sales',
        readonly=True,
        currency_field='currency_id',
        help='Sales exempt from VAT (SC/PWD discounts)')
    
    zero_rated_sales = fields.Monetary(
        string='Zero-Rated Sales',
        readonly=True,
        currency_field='currency_id',
        help='Zero-rated sales (exports, etc.)')
    
    # ========== Voided/Refunded Amounts ==========
    voided_amount = fields.Monetary(
        string='Voided Amount',
        readonly=True,
        currency_field='currency_id',
        help='Total amount of voided transactions')
    
    refunded_amount = fields.Monetary(
        string='Refunded Amount',
        readonly=True,
        currency_field='currency_id',
        help='Total amount of refunds')
    
    # ========== Grand Totals ==========
    old_grand_total = fields.Monetary(
        string='Old Grand Total',
        readonly=True,
        currency_field='currency_id',
        help='Accumulated total before this period')
    
    period_sales = fields.Monetary(
        string='Period Sales',
        readonly=True,
        currency_field='currency_id',
        help='Total sales in this period')
    
    new_grand_total = fields.Monetary(
        string='New Grand Total',
        readonly=True,
        currency_field='currency_id',
        help='Accumulated total including this period')
    
    # ========== Breakdown Lines ==========
    discount_line_ids = fields.One2many(
        'pos.xreading.discount.line',
        'xreading_id',
        string='Discount Breakdown',
        readonly=True,
        help='Breakdown of discounts by type')
    
    payment_line_ids = fields.One2many(
        'pos.xreading.payment.line',
        'xreading_id',
        string='Payment Breakdown',
        readonly=True,
        help='Breakdown of payments by method')
    
    # ========== Notes ==========
    notes = fields.Text(
        string='Notes',
        help='Additional notes or remarks')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], string='Status', default='draft', readonly=True)

    @api.depends('session_id')
    def _compute_config_id(self):
        """Compute config_id from session"""
        for record in self:
            record.config_id = record.session_id.config_id.id if record.session_id else False

    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequential reading numbers"""
        for vals in vals_list:
            if vals.get('reading_number', 'New') == 'New':
                session = self.env['pos.session'].browse(vals.get('session_id'))
                if session:
                    # Format: X-{SESSION_NAME}-{SEQUENCE}
                    seq = self.env['ir.sequence'].next_by_code('pos.xreading') or '0001'
                    vals['reading_number'] = f"X-{session.name}-{seq}"
        return super().create(vals_list)

    @api.model
    def generate_xreading(self, session_id):
        """
        Generate X-Reading for a POS session
        
        This method calculates all sales data since the last Z-reading
        and creates an X-reading record.
        
        Args:
            session_id: ID of the POS session
            
        Returns:
            Created X-reading record
        """
        session = self.env['pos.session'].browse(session_id)
        if not session.exists():
            raise UserError(_('Invalid POS session'))
        
        # Allow X-reading for any session state (open or closed)
        # This allows historical X-reading generation for audit purposes
        
        _logger.info(f"Generating X-reading for session {session.name}")
        
        # Get BIR config
        bir_config = session.config_id.bir_config_id
        
        # Determine period start (last Z-reading or session start)
        last_z_reading_date = bir_config.last_z_reading_date if bir_config else None
        period_start = last_z_reading_date or session.start_at
        period_end = fields.Datetime.now()
        
        # Get orders in this period
        orders_domain = [
            ('session_id', '=', session.id),
            ('state', 'in', ['paid', 'done', 'invoiced']),
            ('is_voided', '=', False),
            ('date_order', '>=', period_start),
            ('date_order', '<=', period_end),
        ]
        orders = self.env['pos.order'].search(orders_domain)
        
        # Get voided orders
        voided_orders = self.env['pos.order'].search([
            ('session_id', '=', session.id),
            ('is_voided', '=', True),
            ('void_date', '>=', period_start),
            ('void_date', '<=', period_end),
        ])
        
        _logger.info(f"Found {len(orders)} orders and {len(voided_orders)} voided orders")
        
        # Calculate totals
        totals = self._calculate_totals(orders, voided_orders)
        
        # Calculate discount breakdown
        discount_lines = self._calculate_discount_breakdown(orders)
        
        # Calculate payment breakdown
        payment_lines = self._calculate_payment_breakdown(orders)
        
        # Create X-reading record
        xreading_vals = {
            'session_id': session.id,
            'bir_config_id': bir_config.id if bir_config else False,
            'reading_date': period_end,
            'period_start_date': period_start,
            'period_end_date': period_end,
            'last_z_reading_date': last_z_reading_date,
            'z_counter': bir_config.z_reading_counter if bir_config else 0,
            
            # Transaction counts
            'transaction_count': len(orders),
            'voided_transaction_count': len(voided_orders),
            'refunded_transaction_count': totals['refunded_count'],
            
            # Sales amounts
            'gross_sales': totals['gross_sales'],
            'total_discounts': totals['total_discounts'],
            'net_sales': totals['net_sales'],
            
            # VAT breakdown
            'vatable_sales': totals['vatable_sales'],
            'vat_amount': totals['vat_amount'],
            'vat_exempt_sales': totals['vat_exempt_sales'],
            'zero_rated_sales': totals['zero_rated_sales'],
            
            # Voided/Refunded
            'voided_amount': totals['voided_amount'],
            'refunded_amount': totals['refunded_amount'],
            
            # Grand totals
            'old_grand_total': totals['old_grand_total'],
            'period_sales': totals['period_sales'],
            'new_grand_total': totals['new_grand_total'],
            
            'state': 'done',
            'discount_line_ids': [(0, 0, line) for line in discount_lines],
            'payment_line_ids': [(0, 0, line) for line in payment_lines],
        }
        
        xreading = self.create(xreading_vals)
        _logger.info(f"X-reading {xreading.reading_number} generated successfully")
        
        # Return a dictionary for JSON serialization (required for JS RPC calls)
        return {
            'id': xreading.id,
            'reading_number': xreading.reading_number,
            'reading_date': xreading.reading_date.isoformat() if xreading.reading_date else False,
            'session_id': xreading.session_id.id,
            'session_name': xreading.session_id.name,
        }

    def _calculate_totals(self, orders, voided_orders):
        """Calculate all financial totals for X-reading
        
        BIR Calculation Rules:
        - For VAT-exempt orders (SC/PWD): gross = amount_total / (1 - discount_percent)
        - For regular VATable orders: gross = amount_total, VAT = amount_tax
        - For zero-rated orders: gross = amount_total, no VAT
        """
        totals = {
            'gross_sales': 0.0,
            'total_discounts': 0.0,
            'net_sales': 0.0,
            'vatable_sales': 0.0,
            'vat_amount': 0.0,
            'vat_exempt_sales': 0.0,
            'zero_rated_sales': 0.0,
            'voided_amount': 0.0,
            'refunded_amount': 0.0,
            'refunded_count': 0,
            'old_grand_total': 0.0,
            'period_sales': 0.0,
            'new_grand_total': 0.0,
        }
        
        for order in orders:
            # Check if this is a VAT-exempt order (SC/PWD)
            if order.bir_discount_type_id and order.bir_discount_type_id.is_vat_exempt:
                # For VAT-exempt orders: calculate gross from final amount
                discount_percent = order.bir_discount_type_id.discount_percent / 100.0
                
                if discount_percent > 0 and discount_percent < 1:
                    gross = order.amount_total / (1 - discount_percent)
                    discount_amount = gross - order.amount_total
                else:
                    gross = order.amount_total
                    discount_amount = 0.0
                
                totals['gross_sales'] += gross
                totals['total_discounts'] += discount_amount
                totals['vat_exempt_sales'] += order.amount_total
            else:
                # For regular orders (non VAT-exempt)
                if order.bir_discount_amount and order.bir_discount_amount > 0:
                    gross = order.amount_total + order.bir_discount_amount
                    totals['total_discounts'] += order.bir_discount_amount
                else:
                    gross = order.amount_total
                
                totals['gross_sales'] += gross
                
                # VAT breakdown: use actual order.amount_tax to determine VATable vs zero-rated
                if order.amount_tax and order.amount_tax > 0:
                    # VATable order
                    totals['vatable_sales'] += order.amount_total - order.amount_tax
                    totals['vat_amount'] += order.amount_tax
                else:
                    # Zero-rated sales
                    totals['zero_rated_sales'] += order.amount_total
            
            # Net sales (amount_total is final amount paid)
            totals['period_sales'] += order.amount_total
            
            # Check for refunds
            if order.amount_total < 0:
                totals['refunded_amount'] += abs(order.amount_total)
                totals['refunded_count'] += 1
        
        # Voided amounts
        for voided in voided_orders:
            totals['voided_amount'] += voided.amount_total
        
        # Net sales
        totals['net_sales'] = totals['period_sales']
        
        # Grand totals (we would need to track accumulated sales, for now just use period)
        # TODO: Implement proper accumulated grand total tracking
        totals['new_grand_total'] = totals['period_sales']
        
        return totals

    def _calculate_discount_breakdown(self, orders):
        """Calculate discount breakdown by type"""
        discount_summary = {}
        
        for order in orders:
            if order.bir_discount_type_id:
                discount_type = order.bir_discount_type_id
                key = discount_type.id
                
                if key not in discount_summary:
                    discount_summary[key] = {
                        'discount_type_id': discount_type.id,
                        'discount_type_name': discount_type.name,
                        'count': 0,
                        'amount': 0.0,
                    }
                
                discount_summary[key]['count'] += 1
                discount_summary[key]['amount'] += order.bir_discount_amount or 0.0
        
        return list(discount_summary.values())

    def _calculate_payment_breakdown(self, orders):
        """Calculate payment breakdown by method"""
        payment_summary = {}
        
        for order in orders:
            for payment in order.payment_ids:
                method = payment.payment_method_id
                key = method.id
                
                if key not in payment_summary:
                    payment_summary[key] = {
                        'payment_method_id': method.id,
                        'payment_method_name': method.name,
                        'count': 0,
                        'amount': 0.0,
                    }
                
                payment_summary[key]['count'] += 1
                payment_summary[key]['amount'] += payment.amount
        
        return list(payment_summary.values())

    def action_print_xreading(self):
        """Print X-reading report"""
        self.ensure_one()
        return self.env.ref('cai_pos.action_report_pos_xreading').report_action(self)


class PosXReadingDiscountLine(models.Model):
    """Discount breakdown line for X-reading"""
    _name = 'pos.xreading.discount.line'
    _description = 'X-Reading Discount Line'

    xreading_id = fields.Many2one(
        'pos.xreading',
        string='X-Reading',
        required=True,
        ondelete='cascade')
    
    discount_type_id = fields.Integer(
        string='Discount Type ID',
        help='ID of the discount type')
    
    discount_type_name = fields.Char(
        string='Discount Type',
        required=True)
    
    count = fields.Integer(
        string='Count',
        help='Number of transactions with this discount')
    
    amount = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
        help='Total discount amount')
    
    currency_id = fields.Many2one(
        'res.currency',
        related='xreading_id.currency_id',
        readonly=True)


class PosXReadingPaymentLine(models.Model):
    """Payment breakdown line for X-reading"""
    _name = 'pos.xreading.payment.line'
    _description = 'X-Reading Payment Line'

    xreading_id = fields.Many2one(
        'pos.xreading',
        string='X-Reading',
        required=True,
        ondelete='cascade')
    
    payment_method_id = fields.Integer(
        string='Payment Method ID',
        help='ID of the payment method')
    
    payment_method_name = fields.Char(
        string='Payment Method',
        required=True)
    
    count = fields.Integer(
        string='Count',
        help='Number of transactions with this payment method')
    
    amount = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
        help='Total payment amount')
    
    currency_id = fields.Many2one(
        'res.currency',
        related='xreading_id.currency_id',
        readonly=True)

