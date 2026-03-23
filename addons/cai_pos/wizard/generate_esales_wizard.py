from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta
import logging
import calendar

_logger = logging.getLogger(__name__)


class GenerateEsalesWizard(models.TransientModel):
    """
    Wizard for generating BIR eSales Monthly Reports
    
    This wizard allows users to:
    1. Select a month for eSales generation
    2. View summary information about that month
    3. Generate daily lines from Z-readings or orders
    4. Generate the CSV file
    """
    _name = 'generate.esales.wizard'
    _description = 'Generate eSales Report Wizard'
    
    report_month = fields.Date(
        string='Report Month',
        required=True,
        default=lambda self: self._default_report_month(),
        help='Select the month for eSales report generation')
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        readonly=True)
    
    bir_config_id = fields.Many2one(
        'bir.config',
        string='BIR Configuration',
        compute='_compute_bir_config',
        help='BIR configuration to be used')
    
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        readonly=True)
    
    # Summary Information
    zreading_count = fields.Integer(
        string='Z-Readings',
        compute='_compute_summary',
        help='Number of Z-readings for this month')
    
    transaction_count = fields.Integer(
        string='Transactions',
        compute='_compute_summary',
        help='Number of completed transactions')
    
    total_sales = fields.Monetary(
        string='Total Sales',
        compute='_compute_summary',
        currency_field='currency_id',
        help='Total sales amount for this month')
    
    days_with_sales = fields.Integer(
        string='Days with Sales',
        compute='_compute_summary',
        help='Number of days with sales transactions')
    
    # Status Indicators
    can_generate = fields.Boolean(
        string='Can Generate',
        compute='_compute_summary',
        help='Whether eSales report can be generated')
    
    warning_message = fields.Html(
        string='Status',
        compute='_compute_summary',
        help='Status messages and warnings')
    
    esales_exists = fields.Boolean(
        string='eSales Report Exists',
        compute='_compute_summary',
        help='eSales report already exists for this month')
    
    existing_esales_id = fields.Many2one(
        'pos.esales.report',
        string='Existing eSales Report',
        compute='_compute_summary')
    
    generation_method = fields.Selection([
        ('zreading', 'From Z-Readings'),
        ('orders', 'From Orders'),
        ('from_order', 'From Specific Order'),
    ], string='Generation Method',
       default='zreading',
       required=True,
       help='Method to use for generating eSales data')
    
    starting_order_id = fields.Many2one(
        'pos.order',
        string='Starting Order',
        help='Select the order to start from (this order and all orders after it will be included)')
    
    starting_order_date = fields.Datetime(
        string='Order Date',
        related='starting_order_id.date_order',
        readonly=True)
    
    starting_order_amount = fields.Monetary(
        string='Order Amount',
        related='starting_order_id.amount_total',
        currency_field='currency_id',
        readonly=True)
    
    @api.model
    def _default_report_month(self):
        """Default to first day of previous month"""
        today = date.today()
        first_of_current_month = today.replace(day=1)
        last_month = first_of_current_month - relativedelta(months=1)
        return last_month
    
    @api.depends('company_id')
    def _compute_bir_config(self):
        """Get active BIR configuration for company"""
        for wizard in self:
            bir_config = self.env['bir.config'].search([
                ('company_id', '=', wizard.company_id.id),
                ('active', '=', True)
            ], limit=1)
            wizard.bir_config_id = bir_config
    
    @api.depends('report_month', 'company_id', 'generation_method')
    def _compute_summary(self):
        """Compute summary information and validation status"""
        for wizard in self:
            if not wizard.report_month:
                wizard._reset_summary_fields()
                continue
            
            # Get month range
            first_day = wizard.report_month.replace(day=1)
            last_day_num = calendar.monthrange(first_day.year, first_day.month)[1]
            last_day = first_day.replace(day=last_day_num)
            
            date_start = datetime.combine(first_day, time.min)
            date_end = datetime.combine(last_day, time.max)
            
            # Check if eSales report already exists
            existing = self.env['pos.esales.report'].search([
                ('report_month', '=', first_day),
                ('company_id', '=', wizard.company_id.id)
            ])
            
            wizard.esales_exists = bool(existing)
            wizard.existing_esales_id = existing if existing else False
            
            # Get Z-readings for this month (reading_date is Date field)
            zreadings = self.env['pos.zreading'].search([
                ('reading_date', '>=', fields.Date.to_string(first_day)),
                ('reading_date', '<=', fields.Date.to_string(last_day)),
                ('company_id', '=', wizard.company_id.id)
            ])
            
            wizard.zreading_count = len(zreadings)
            
            # Get orders for this month or from specific order
            if wizard.generation_method == 'from_order' and wizard.starting_order_id:
                # Get orders from the starting order onwards
                orders = self.env['pos.order'].search([
                    ('date_order', '>=', wizard.starting_order_id.date_order),
                    ('state', 'in', ['paid', 'done', 'invoiced']),
                    ('is_voided', '=', False),
                    ('company_id', '=', wizard.company_id.id)
                ])
            else:
                # Get orders for the month
                orders = self.env['pos.order'].search([
                    ('date_order', '>=', date_start),
                    ('date_order', '<=', date_end),
                    ('state', 'in', ['paid', 'done', 'invoiced']),
                    ('is_voided', '=', False),
                    ('company_id', '=', wizard.company_id.id)
                ])
            
            wizard.transaction_count = len(orders)
            wizard.total_sales = sum(orders.mapped('amount_total'))
            
            # Count days with sales
            dates_with_sales = set(order.date_order.date() for order in orders)
            wizard.days_with_sales = len(dates_with_sales)
            
            # Build warning/status message
            wizard._build_status_message()
    
    def _reset_summary_fields(self):
        """Reset all summary fields"""
        self.zreading_count = 0
        self.transaction_count = 0
        self.total_sales = 0.0
        self.days_with_sales = 0
        self.can_generate = False
        self.warning_message = '<p style="color: #666;">Please select a month</p>'
        self.esales_exists = False
        self.existing_esales_id = False
    
    def _build_status_message(self):
        """Build status message HTML"""
        messages = []
        errors = []
        warnings = []
        info = []
        
        # Check for blocking issues
        if self.esales_exists:
            errors.append(
                f'❌ <strong>eSales report already exists</strong>: {self.existing_esales_id.name}<br/>'
                f'   Generated on: {self.existing_esales_id.generated_date.strftime("%m/%d/%Y %I:%M %p") if self.existing_esales_id.generated_date else "Draft"}<br/>'
                f'   State: {dict(self.existing_esales_id._fields["state"].selection).get(self.existing_esales_id.state)}'
            )
        
        if not self.bir_config_id:
            errors.append('❌ <strong>No active BIR configuration found</strong>')
        
        if self.generation_method == 'zreading' and self.zreading_count == 0:
            warnings.append('⚠️  No Z-readings found for this month. Consider using "From Orders" method.')
        
        if self.generation_method == 'from_order' and not self.starting_order_id:
            warnings.append('⚠️  Please select a starting order')
        
        if self.transaction_count == 0:
            warnings.append('⚠️  No transactions found')
        
        # Add info messages
        if self.zreading_count > 0:
            info.append(f'✓ {self.zreading_count} Z-reading(s) available')
        
        if self.transaction_count > 0:
            info.append(f'✓ {self.transaction_count} transaction(s) found')
        
        if self.days_with_sales > 0:
            info.append(f'✓ {self.days_with_sales} day(s) with sales')
        
        if self.generation_method == 'from_order' and self.starting_order_id:
            info.append(
                f'✓ Starting from order: {self.starting_order_id.pos_reference} '
                f'({self.starting_order_id.date_order.strftime("%m/%d/%Y %I:%M %p")})'
            )
        
        # Determine if can generate
        can_generate_from_order = True
        if self.generation_method == 'from_order':
            can_generate_from_order = bool(self.starting_order_id)
        
        self.can_generate = (
            not self.esales_exists and 
            self.bir_config_id and 
            self.transaction_count > 0 and
            can_generate_from_order
        )
        
        # Build final message
        if errors:
            messages.append('<div style="background: #ffebee; padding: 10px; border-left: 3px solid #f44336; margin-bottom: 10px;">')
            messages.extend(errors)
            messages.append('</div>')
        
        if warnings:
            messages.append('<div style="background: #fff3e0; padding: 10px; border-left: 3px solid #ff9800; margin-bottom: 10px;">')
            messages.extend(warnings)
            messages.append('</div>')
        
        if info and not errors:
            messages.append('<div style="background: #e8f5e9; padding: 10px; border-left: 3px solid #4caf50; margin-bottom: 10px;">')
            messages.extend(info)
            messages.append('</div>')
        
        if self.can_generate:
            messages.append(
                '<div style="background: #e3f2fd; padding: 10px; border-left: 3px solid #2196f3;">'
                '✓ <strong>Ready to generate eSales report</strong>'
                '</div>'
            )
        
        self.warning_message = ''.join(messages) if messages else '<p style="color: #666;">Loading...</p>'
    
    def action_generate_esales(self):
        """Generate the eSales report"""
        self.ensure_one()
        
        # Final validation
        if self.esales_exists:
            raise UserError(
                f"eSales report already exists for {self.report_month.strftime('%B %Y')}!\n"
                f"Report Name: {self.existing_esales_id.name}"
            )
        
        if not self.bir_config_id:
            raise UserError(_("No active BIR configuration found for this company."))
        
        if self.transaction_count == 0:
            raise UserError(
                f"Cannot generate eSales report for {self.report_month.strftime('%B %Y')}.\n"
                "No transactions found for this month."
            )
        
        try:
            # Create eSales report
            first_day = self.report_month.replace(day=1)
            
            esales = self.env['pos.esales.report'].create({
                'report_month': first_day,
                'company_id': self.company_id.id,
                'bir_config_id': self.bir_config_id.id,
                'state': 'draft',
            })
            
            _logger.info(f"Created eSales report: {esales.name}")
            
            # Generate daily lines
            if self.generation_method == 'zreading':
                self._generate_lines_from_zreadings(esales)
            elif self.generation_method == 'from_order':
                self._generate_lines_from_specific_order(esales)
            else:
                self._generate_lines_from_orders(esales)
            
            _logger.info(f"Generated {len(esales.line_ids)} daily lines for eSales report")
            
            # Return action to view the created eSales report
            return {
                'type': 'ir.actions.act_window',
                'name': _('eSales Report'),
                'res_model': 'pos.esales.report',
                'res_id': esales.id,
                'view_mode': 'form',
                'target': 'current',
            }
            
        except UserError as e:
            raise e
        except Exception as e:
            _logger.error(f"Error generating eSales report: {str(e)}", exc_info=True)
            raise UserError(
                f"Error generating eSales report: {str(e)}\n\n"
                "Please check the logs for more details."
            )
    
    def _generate_lines_from_zreadings(self, esales):
        """Generate eSales daily lines from Z-readings"""
        self.ensure_one()
        
        first_day = self.report_month.replace(day=1)
        last_day_num = calendar.monthrange(first_day.year, first_day.month)[1]
        last_day = first_day.replace(day=last_day_num)
        
        # Get Z-readings for this month (reading_date is Date field)
        zreadings = self.env['pos.zreading'].search([
            ('reading_date', '>=', fields.Date.to_string(first_day)),
            ('reading_date', '<=', fields.Date.to_string(last_day)),
            ('company_id', '=', self.company_id.id)
        ], order='reading_date')
        
        if not zreadings:
            raise UserError(_("No Z-readings found for the selected month. Use 'From Orders' method instead."))
        
        # Get the accumulated total from the most recent Z-reading before this month
        accumulated_total = 0.0
        prev_zreading = self.env['pos.zreading'].search([
            ('reading_date', '<', zreadings[0].reading_date),
            ('company_id', '=', self.company_id.id)
        ], order='reading_date desc', limit=1)
        
        if prev_zreading:
            accumulated_total = prev_zreading.new_grand_total
            _logger.info(f"[eSales Z-Reading] Starting with previous Z-reading {prev_zreading.reading_number} "
                        f"new_grand_total: {accumulated_total:.2f}")
        else:
            # First Z-reading ever - start from 0
            accumulated_total = 0.0
            _logger.info(f"[eSales Z-Reading] No previous Z-reading found, starting from 0")
        
        # Create daily lines from Z-readings
        for zreading in zreadings:
            old_grand_total = accumulated_total
            new_grand_total = old_grand_total + zreading.net_sales
            accumulated_total = new_grand_total
            
            # Get first and last receipt for this date
            date_start = datetime.combine(zreading.reading_date, time.min)
            date_end = datetime.combine(zreading.reading_date, time.max)
            
            orders = self.env['pos.order'].search([
                ('date_order', '>=', date_start),
                ('date_order', '<=', date_end),
                ('state', 'in', ['paid', 'done', 'invoiced']),
                ('is_voided', '=', False),
                ('company_id', '=', self.company_id.id)
            ], order='pos_reference')
            
            begin_or = orders[0].pos_reference if orders else ''
            end_or = orders[-1].pos_reference if orders else ''
            
            # Calculate discount breakdown from orders (Z-reading doesn't track by type)
            discount_breakdown = self._calculate_discount_breakdown(orders)
            
            # Create line
            self.env['pos.esales.report.line'].create({
                'report_id': esales.id,
                'date': zreading.reading_date,
                'old_grand_total': old_grand_total,
                'new_grand_total': new_grand_total,
                'gross_sales': zreading.gross_sales,
                'sc_disc': discount_breakdown['sc_disc'],
                'pwd_disc': discount_breakdown['pwd_disc'],
                'athlete_mov_disc': discount_breakdown['athlete_mov_disc'],
                'other_disc': discount_breakdown['other_disc'],
                'whtax': 0.0,
                'vat_from_disc': 0.0,
                'total_sales': zreading.net_sales,
                'vatable_sales': zreading.vatable_sales,
                'vat_amount': zreading.vat_amount,
                'vat_exempt_sales': zreading.vat_exempt_sales,
                'zero_rated_sales': zreading.zero_rated_sales,
                'net_sales': zreading.net_sales,
                'service_charge': 0.0,
                'refund_amount': zreading.refund_amount or 0.0,  # Get refund amount from Z-reading
                'void_amount': zreading.voided_amount,
                'begin_or': begin_or,
                'end_or': end_or,
                'or_count': len(orders),
                'terminal_read_count': zreading.transaction_count,
            })
    
    def _calculate_discount_breakdown(self, orders):
        """Calculate discount breakdown by type from orders
        
        This method categorizes discounts into SC, PWD, Athlete/MOV, and Other
        based on the discount_type field OR the code field of bir.discount.type
        
        BIR Calculation for VAT-exempt discounts (SC/PWD):
        - VAT-exempt base = original_price / 1.12 (VAT removed first)
        - Discount = VAT-exempt base * discount_percent
        """
        breakdown = {
            'sc_disc': 0.0,
            'pwd_disc': 0.0,
            'athlete_mov_disc': 0.0,
            'other_disc': 0.0,
        }
        
        for order in orders:
            # Skip refund orders (negative amounts)
            if order.amount_total < 0:
                continue
            
            if not order.bir_discount_type_id:
                continue
            
            discount_type = order.bir_discount_type_id
            discount_type_code = discount_type.discount_type  # 'sc', 'pwd', 'gov', 'promo', 'other'
            discount_code = (discount_type.code or '').upper().strip()  # Free text code like "SC", "PWD"
            discount_percent = discount_type.discount_percent / 100.0
            
            # Determine category: check both discount_type selection AND code field
            # This handles cases where user set code="SC" but left discount_type as default
            category = self._get_discount_category(discount_type_code, discount_code)
            
            # Check if VAT-exempt (SC/PWD are always VAT-exempt by BIR rules)
            is_vat_exempt = discount_type.is_vat_exempt or category in ('sc', 'pwd')
            
            if is_vat_exempt and discount_percent > 0:
                # For VAT-exempt discounts, calculate from order lines
                for line in order.lines:
                    original_price = line.price_unit * line.qty
                    
                    # Check if this product is discountable
                    is_discountable = getattr(line.product_id, 'is_bir_discountable', True)
                    if is_discountable is None:
                        is_discountable = True
                    
                    if is_discountable:
                        # BIR Formula: Remove VAT first, then apply discount
                        vat_exempt_base = original_price / 1.12
                        discount_amount = vat_exempt_base * discount_percent
                        
                        # Categorize by discount type
                        if category == 'sc':
                            breakdown['sc_disc'] += discount_amount
                        elif category == 'pwd':
                            breakdown['pwd_disc'] += discount_amount
                        elif category == 'athlete_mov':
                            breakdown['athlete_mov_disc'] += discount_amount
                        else:
                            breakdown['other_disc'] += discount_amount
            else:
                # For non-VAT-exempt discounts, use bir_discount_amount
                if order.bir_discount_amount and order.bir_discount_amount > 0:
                    if category == 'sc':
                        breakdown['sc_disc'] += order.bir_discount_amount
                    elif category == 'pwd':
                        breakdown['pwd_disc'] += order.bir_discount_amount
                    elif category == 'athlete_mov':
                        breakdown['athlete_mov_disc'] += order.bir_discount_amount
                    else:
                        breakdown['other_disc'] += order.bir_discount_amount
        
        return breakdown
    
    def _get_discount_category(self, discount_type_code, discount_code):
        """Determine discount category from both discount_type and code fields
        
        Args:
            discount_type_code: Selection value ('sc', 'pwd', 'gov', 'promo', 'other')
            discount_code: Free text code (e.g., "SC", "PWD", "SENIOR")
        
        Returns:
            Category string: 'sc', 'pwd', 'athlete_mov', or 'other'
        """
        # First check the discount_type selection field (most reliable)
        if discount_type_code == 'sc':
            return 'sc'
        elif discount_type_code == 'pwd':
            return 'pwd'
        elif discount_type_code in ('athlete', 'mov'):
            return 'athlete_mov'
        
        # Fallback: check the code field (case-insensitive)
        # This handles cases where user set code="SC" but left discount_type as default 'promo'
        if discount_code:
            code_upper = discount_code.upper()
            if code_upper in ('SC', 'SENIOR', 'SENIOR CITIZEN', 'SENIORCITIZEN'):
                return 'sc'
            elif code_upper in ('PWD', 'DISABLED', 'PERSON WITH DISABILITY'):
                return 'pwd'
            elif code_upper in ('ATHLETE', 'MOV', 'MEDAL OF VALOR', 'MEDALOFVALOR'):
                return 'athlete_mov'
        
        return 'other'
    
    def _generate_lines_from_orders(self, esales):
        """Generate eSales daily lines directly from orders"""
        self.ensure_one()
        
        first_day = self.report_month.replace(day=1)
        last_day_num = calendar.monthrange(first_day.year, first_day.month)[1]
        last_day = first_day.replace(day=last_day_num)
        
        date_start = datetime.combine(first_day, time.min)
        date_end = datetime.combine(last_day, time.max)
        
        # Get all orders for this month
        orders = self.env['pos.order'].search([
            ('date_order', '>=', date_start),
            ('date_order', '<=', date_end),
            ('state', 'in', ['paid', 'done', 'invoiced']),
            ('is_voided', '=', False),
            ('company_id', '=', self.company_id.id)
        ], order='date_order')
        
        if not orders:
            raise UserError(_("No orders found for the selected month."))
        
        # Group orders by date
        orders_by_date = {}
        for order in orders:
            order_date = order.date_order.date()
            if order_date not in orders_by_date:
                orders_by_date[order_date] = []
            orders_by_date[order_date].append(order)
        
        # Get accumulated total from the most recent Z-reading before this month
        accumulated_total = 0.0
        first_order_date = min(orders_by_date.keys()) if orders_by_date else first_day
        
        prev_zreading = self.env['pos.zreading'].search([
            ('reading_date', '<', first_order_date),
            ('company_id', '=', self.company_id.id)
        ], order='reading_date desc', limit=1)
        
        if prev_zreading:
            accumulated_total = prev_zreading.new_grand_total
            _logger.info(f"[eSales Orders] Starting with previous Z-reading {prev_zreading.reading_number} "
                        f"new_grand_total: {accumulated_total:.2f}")
        else:
            # No previous Z-reading - start from 0
            accumulated_total = 0.0
            _logger.info(f"[eSales Orders] No previous Z-reading found, starting from 0")
        
        # Create daily lines
        for order_date in sorted(orders_by_date.keys()):
            daily_orders = orders_by_date[order_date]
            
            # Get voided orders for this date
            date_start_daily = datetime.combine(order_date, time.min)
            date_end_daily = datetime.combine(order_date, time.max)
            
            voided_orders = self.env['pos.order'].search([
                ('date_order', '>=', date_start_daily),
                ('date_order', '<=', date_end_daily),
                ('is_voided', '=', True),
                ('company_id', '=', self.company_id.id)
            ])
            
            # Calculate totals for this date
            totals = self._calculate_daily_totals(daily_orders, voided_orders)
            
            old_grand_total = accumulated_total
            new_grand_total = old_grand_total + totals['net_sales']
            accumulated_total = new_grand_total
            
            # Get first and last receipt
            sorted_orders = sorted(daily_orders, key=lambda o: o.pos_reference or '')
            begin_or = sorted_orders[0].pos_reference if sorted_orders else ''
            end_or = sorted_orders[-1].pos_reference if sorted_orders else ''
            
            # Create line
            self.env['pos.esales.report.line'].create({
                'report_id': esales.id,
                'date': order_date,
                'old_grand_total': old_grand_total,
                'new_grand_total': new_grand_total,
                'gross_sales': totals['gross_sales'],
                'sc_disc': totals['sc_disc'],
                'pwd_disc': totals['pwd_disc'],
                'athlete_mov_disc': totals['athlete_mov_disc'],
                'other_disc': totals['other_disc'],
                'whtax': 0.0,
                'vat_from_disc': 0.0,
                'total_sales': totals['total_sales'],
                'vatable_sales': totals['vatable_sales'],
                'vat_amount': totals['vat_amount'],
                'vat_exempt_sales': totals['vat_exempt_sales'],
                'zero_rated_sales': totals['zero_rated_sales'],
                'net_sales': totals['net_sales'],
                'service_charge': 0.0,
                'refund_amount': totals.get('refund_amount', 0.0),
                'void_amount': totals['void_amount'],
                'begin_or': begin_or,
                'end_or': end_or,
                'or_count': len(daily_orders),
                'terminal_read_count': len(daily_orders),
            })
    
    def _calculate_daily_totals(self, orders, voided_orders):
        """Calculate daily totals from orders
        
        BIR eSales Calculation Rules (per order line):
        - For VAT-exempt discountable items (SC/PWD): 
          - Gross = price_unit * qty / 1.12 (VAT-exempt base before discount)
          - Discount = gross * discount_percent
          - VAT-Exempt Sales = final line total after discount
        - For non-discountable items in VAT-exempt orders:
          - Treated as regular VATable sales (VAT-inclusive gross)
        - For regular VATable orders: gross = amount_total, VAT = amount_tax
        - For zero-rated orders: gross = amount_total, no VAT
        - Refund orders (negative amount_total) are tracked separately
        """
        totals = {
            'gross_sales': 0.0,
            'sc_disc': 0.0,
            'pwd_disc': 0.0,
            'athlete_mov_disc': 0.0,
            'other_disc': 0.0,
            'total_sales': 0.0,
            'vatable_sales': 0.0,
            'vat_amount': 0.0,
            'vat_exempt_sales': 0.0,
            'zero_rated_sales': 0.0,
            'net_sales': 0.0,
            'void_amount': 0.0,
            'refund_amount': 0.0,
        }
        
        for order in orders:
            # Check if this is a refund order (negative amount_total)
            if order.amount_total < 0:
                # This is a refund - track it separately
                # Store refund as positive value
                totals['refund_amount'] += abs(order.amount_total)
                # Refunds reduce net_sales (they're already included in the negative amount)
                totals['net_sales'] += order.amount_total  # Will be negative
                totals['total_sales'] += order.amount_total  # Will be negative
                continue
            
            # Check if this is a VAT-exempt order (SC/PWD)
            # SC and PWD are ALWAYS VAT-exempt by BIR rules, regardless of is_vat_exempt flag
            is_vat_exempt_order = False
            discount_category = 'other'
            if order.bir_discount_type_id:
                discount_type = order.bir_discount_type_id
                discount_type_code = discount_type.discount_type  # 'sc', 'pwd', 'gov', etc.
                discount_code = (discount_type.code or '').upper().strip()  # Free text code
                # Get the category using both discount_type and code fields
                discount_category = self._get_discount_category(discount_type_code, discount_code)
                # Check if VAT-exempt (SC/PWD are always VAT-exempt by BIR rules)
                is_vat_exempt_order = discount_type.is_vat_exempt or discount_category in ('sc', 'pwd')
            
            if is_vat_exempt_order:
                discount_percent = order.bir_discount_type_id.discount_percent / 100.0
                
                # Process each order line separately
                for line in order.lines:
                    line_total = line.price_subtotal_incl  # Final price paid for this line
                    original_price = line.price_unit * line.qty  # Original price before any discount
                    
                    # Check if this product is discountable
                    is_discountable = getattr(line.product_id, 'is_bir_discountable', True)
                    if is_discountable is None:
                        is_discountable = True  # Default to True if field doesn't exist
                    
                    if is_discountable and discount_percent > 0:
                        # For discountable items with VAT-exempt discount:
                        # Calculate the VAT-exempt gross (original price / 1.12)
                        vat_exempt_gross = original_price / 1.12
                        # The discount is applied on the VAT-exempt amount
                        discount_amount = vat_exempt_gross * discount_percent
                        
                        totals['gross_sales'] += vat_exempt_gross
                        totals['vat_exempt_sales'] += line_total
                        
                        # Categorize the discount using determined category
                        if discount_category == 'sc':
                            totals['sc_disc'] += discount_amount
                        elif discount_category == 'pwd':
                            totals['pwd_disc'] += discount_amount
                        elif discount_category == 'athlete_mov':
                            totals['athlete_mov_disc'] += discount_amount
                        else:
                            totals['other_disc'] += discount_amount
                    else:
                        # For non-discountable items: treat as regular VATable
                        # Gross = VAT-inclusive price (original)
                        totals['gross_sales'] += original_price
                        
                        # Calculate VAT (assuming 12% VAT inclusive price)
                        vatable_base = original_price / 1.12
                        vat_amount = original_price - vatable_base
                        
                        totals['vatable_sales'] += vatable_base
                        totals['vat_amount'] += vat_amount
                
            else:
                # For regular orders (non VAT-exempt)
                if order.bir_discount_amount and order.bir_discount_amount > 0:
                    gross = order.amount_total + order.bir_discount_amount
                    # Categorize the discount using determined category
                    if discount_category == 'sc':
                        totals['sc_disc'] += order.bir_discount_amount
                    elif discount_category == 'pwd':
                        totals['pwd_disc'] += order.bir_discount_amount
                    elif discount_category == 'athlete_mov':
                        totals['athlete_mov_disc'] += order.bir_discount_amount
                    else:
                        totals['other_disc'] += order.bir_discount_amount
                else:
                    gross = order.amount_total
                
                totals['gross_sales'] += gross
                
                # VAT breakdown: use actual order.amount_tax to determine if VATable or zero-rated
                if order.amount_tax and order.amount_tax > 0:
                    totals['vatable_sales'] += order.amount_total - order.amount_tax
                    totals['vat_amount'] += order.amount_tax
                else:
                    totals['zero_rated_sales'] += order.amount_total
            
            # Total and net sales (always the final amount paid)
            totals['total_sales'] += order.amount_total
            totals['net_sales'] += order.amount_total
        
        # Voided amounts
        for voided in voided_orders:
            totals['void_amount'] += voided.amount_total
        
        return totals
    
    def action_view_existing_esales(self):
        """View the existing eSales report for this month"""
        self.ensure_one()
        
        if not self.existing_esales_id:
            raise UserError(_("No eSales report found for this month."))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('eSales Report'),
            'res_model': 'pos.esales.report',
            'res_id': self.existing_esales_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _generate_lines_from_specific_order(self, esales):
        """Generate eSales daily lines from a specific order onwards"""
        self.ensure_one()
        
        if not self.starting_order_id:
            raise UserError(_("Please select a starting order."))
        
        # Get all orders from the starting order onwards
        orders = self.env['pos.order'].search([
            ('date_order', '>=', self.starting_order_id.date_order),
            ('state', 'in', ['paid', 'done', 'invoiced']),
            ('is_voided', '=', False),
            ('company_id', '=', self.company_id.id)
        ], order='date_order')
        
        if not orders:
            raise UserError(_("No orders found from the selected starting order."))
        
        _logger.info(f"[eSales] Generating from order {self.starting_order_id.pos_reference} - Found {len(orders)} orders")
        
        # Group orders by date
        orders_by_date = {}
        for order in orders:
            order_date = order.date_order.date()
            if order_date not in orders_by_date:
                orders_by_date[order_date] = []
            orders_by_date[order_date].append(order)
        
        # Get accumulated total from the most recent Z-reading before the starting order
        accumulated_total = 0.0
        first_order_date = min(orders_by_date.keys()) if orders_by_date else self.starting_order_id.date_order.date()
        
        prev_zreading = self.env['pos.zreading'].search([
            ('reading_date', '<', first_order_date),
            ('company_id', '=', self.company_id.id)
        ], order='reading_date desc', limit=1)
        
        if prev_zreading:
            accumulated_total = prev_zreading.new_grand_total
            _logger.info(f"[eSales From Order] Starting with previous Z-reading {prev_zreading.reading_number} "
                        f"new_grand_total: {accumulated_total:.2f}")
        else:
            # No previous Z-reading - start from 0
            accumulated_total = 0.0
            _logger.info(f"[eSales From Order] No previous Z-reading found, starting from 0")
        
        # Create daily lines
        for order_date in sorted(orders_by_date.keys()):
            daily_orders = orders_by_date[order_date]
            
            # Get voided orders for this date
            date_start_daily = datetime.combine(order_date, time.min)
            date_end_daily = datetime.combine(order_date, time.max)
            
            voided_orders = self.env['pos.order'].search([
                ('date_order', '>=', date_start_daily),
                ('date_order', '<=', date_end_daily),
                ('is_voided', '=', True),
                ('company_id', '=', self.company_id.id)
            ])
            
            # Calculate totals for this date
            totals = self._calculate_daily_totals(daily_orders, voided_orders)
            
            old_grand_total = accumulated_total
            new_grand_total = old_grand_total + totals['net_sales']
            accumulated_total = new_grand_total
            
            # Get first and last receipt
            sorted_orders = sorted(daily_orders, key=lambda o: o.pos_reference or '')
            begin_or = sorted_orders[0].pos_reference if sorted_orders else ''
            end_or = sorted_orders[-1].pos_reference if sorted_orders else ''
            
            # Create line
            self.env['pos.esales.report.line'].create({
                'report_id': esales.id,
                'date': order_date,
                'old_grand_total': old_grand_total,
                'new_grand_total': new_grand_total,
                'gross_sales': totals['gross_sales'],
                'sc_disc': totals['sc_disc'],
                'pwd_disc': totals['pwd_disc'],
                'athlete_mov_disc': totals['athlete_mov_disc'],
                'other_disc': totals['other_disc'],
                'whtax': 0.0,
                'vat_from_disc': 0.0,
                'total_sales': totals['total_sales'],
                'vatable_sales': totals['vatable_sales'],
                'vat_amount': totals['vat_amount'],
                'vat_exempt_sales': totals['vat_exempt_sales'],
                'zero_rated_sales': totals['zero_rated_sales'],
                'net_sales': totals['net_sales'],
                'service_charge': 0.0,
                'refund_amount': totals.get('refund_amount', 0.0),
                'void_amount': totals['void_amount'],
                'begin_or': begin_or,
                'end_or': end_or,
                'or_count': len(daily_orders),
                'terminal_read_count': len(daily_orders),
            })
        
        _logger.info(f"[eSales] Generated {len(orders_by_date)} daily lines from specific order")

