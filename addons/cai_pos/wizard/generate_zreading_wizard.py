from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, time

class GenerateZReadingWizard(models.TransientModel):
    """
    Wizard for generating Z-Reading reports
    
    This wizard allows users to:
    1. Select a date for Z-reading generation
    2. View summary information about that date
    3. See warnings if sessions are still open
    4. Generate the Z-reading if all validations pass
    """
    _name = 'generate.zreading.wizard'
    _description = 'Generate Z-Reading Wizard'
    
    reading_date = fields.Date(
        string='Z-Reading Date',
        required=True,
        default=fields.Date.context_today,
        help='Select the business date for Z-reading generation')
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        readonly=True)
    
    # ========== Summary Information (Computed) ==========
    session_count = fields.Integer(
        string='Total Sessions',
        compute='_compute_summary',
        help='Number of POS sessions for this date')
    
    closed_session_count = fields.Integer(
        string='Closed Sessions',
        compute='_compute_summary',
        help='Number of closed sessions')
    
    open_session_count = fields.Integer(
        string='Open Sessions',
        compute='_compute_summary',
        help='Number of sessions still open')
    
    order_count = fields.Integer(
        string='Transactions',
        compute='_compute_summary',
        help='Number of completed transactions')
    
    voided_count = fields.Integer(
        string='Voided',
        compute='_compute_summary',
        help='Number of voided transactions')
    
    total_sales = fields.Monetary(
        string='Total Sales',
        compute='_compute_summary',
        currency_field='currency_id',
        help='Total sales amount for this date')
    
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        readonly=True)
    
    # ========== Status Indicators ==========
    can_generate = fields.Boolean(
        string='Can Generate',
        compute='_compute_summary',
        help='Whether Z-reading can be generated')
    
    warning_message = fields.Html(
        string='Status',
        compute='_compute_summary',
        help='Status messages and warnings')
    
    zreading_exists = fields.Boolean(
        string='Z-Reading Exists',
        compute='_compute_summary',
        help='Z-reading already exists for this date')
    
    existing_zreading_id = fields.Many2one(
        'pos.zreading',
        string='Existing Z-Reading',
        compute='_compute_summary')

    @api.depends('reading_date', 'company_id')
    def _compute_summary(self):
        """Compute summary information and validation status"""
        for wizard in self:
            if not wizard.reading_date:
                wizard.session_count = 0
                wizard.closed_session_count = 0
                wizard.open_session_count = 0
                wizard.order_count = 0
                wizard.voided_count = 0
                wizard.total_sales = 0.0
                wizard.can_generate = False
                wizard.warning_message = '<p style="color: #666;">Please select a date</p>'
                wizard.zreading_exists = False
                wizard.existing_zreading_id = False
                continue
            
            # Date range for queries
            date_start = datetime.combine(wizard.reading_date, time.min)
            date_end = datetime.combine(wizard.reading_date, time.max)
            
            # Get sessions for this date
            sessions = self.env['pos.session'].search([
                ('start_at', '>=', date_start),
                ('start_at', '<=', date_end),
                ('company_id', '=', wizard.company_id.id)
            ])
            
            closed_sessions = sessions.filtered(lambda s: s.state == 'closed')
            open_sessions = sessions.filtered(lambda s: s.state != 'closed')
            
            wizard.session_count = len(sessions)
            wizard.closed_session_count = len(closed_sessions)
            wizard.open_session_count = len(open_sessions)
            
            # Get orders for this date
            orders = self.env['pos.order'].search([
                ('date_order', '>=', date_start),
                ('date_order', '<=', date_end),
                ('state', 'in', ['paid', 'done', 'invoiced']),
                ('is_voided', '=', False),
                ('company_id', '=', wizard.company_id.id)
            ])
            
            voided_orders = self.env['pos.order'].search([
                ('date_order', '>=', date_start),
                ('date_order', '<=', date_end),
                ('is_voided', '=', True),
                ('company_id', '=', wizard.company_id.id)
            ])
            
            wizard.order_count = len(orders)
            wizard.voided_count = len(voided_orders)
            wizard.total_sales = sum(orders.mapped('amount_total'))
            
            # Check if Z-reading already exists
            existing = self.env['pos.zreading'].search([
                ('reading_date', '=', wizard.reading_date),
                ('company_id', '=', wizard.company_id.id)
            ])
            
            wizard.zreading_exists = bool(existing)
            wizard.existing_zreading_id = existing if existing else False
            
            # Build warning/status message
            messages = []
            errors = []
            warnings = []
            info = []
            
            # Check for blocking issues
            if wizard.zreading_exists:
                errors.append(
                    f'❌ <strong>Z-reading already exists</strong>: {existing.reading_number}<br/>'
                    f'   Generated on: {existing.reading_datetime.strftime("%m/%d/%Y %I:%M %p")}<br/>'
                    f'   By: {existing.user_id.name}'
                )
            
            if wizard.open_session_count > 0:
                session_list = '<br/>'.join([
                    f'      • {s.name} - {s.user_id.name} (started {s.start_at.strftime("%I:%M %p")})'
                    for s in open_sessions
                ])
                errors.append(
                    f'❌ <strong>{wizard.open_session_count} session(s) still OPEN:</strong><br/>'
                    f'{session_list}'
                )
            
            if wizard.order_count == 0:
                warnings.append('⚠️  No transactions for this date')
            
            # Add info messages
            if wizard.session_count > 0 and wizard.open_session_count == 0:
                info.append(f'✓ All {wizard.session_count} session(s) are closed')
            
            if wizard.order_count > 0:
                info.append(f'✓ {wizard.order_count} transaction(s) found')
            
            if wizard.voided_count > 0:
                info.append(f'ℹ️  {wizard.voided_count} voided transaction(s)')
            
            # Determine if can generate
            wizard.can_generate = (
                not wizard.zreading_exists and 
                wizard.open_session_count == 0 and 
                wizard.order_count > 0
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
            
            if wizard.can_generate:
                messages.append(
                    '<div style="background: #e3f2fd; padding: 10px; border-left: 3px solid #2196f3;">'
                    '✓ <strong>Ready to generate Z-reading</strong>'
                    '</div>'
                )
            
            wizard.warning_message = ''.join(messages) if messages else '<p style="color: #666;">Loading...</p>'

    def action_generate_zreading(self):
        """Generate the Z-reading"""
        self.ensure_one()
        
        # Final validation before generation
        if self.zreading_exists:
            raise UserError(
                f"Z-reading already exists for {self.reading_date}!\n"
                f"Z-Reading Number: {self.existing_zreading_id.reading_number}"
            )
        
        if self.open_session_count > 0:
            raise UserError(
                f"Cannot generate Z-reading.\n"
                f"{self.open_session_count} session(s) are still open.\n"
                "Please close all sessions first."
            )
        
        if self.order_count == 0:
            raise UserError(
                f"Cannot generate Z-reading for {self.reading_date}.\n"
                "No transactions found for this date."
            )
        
        try:
            # Generate the Z-reading
            zreading = self.env['pos.zreading'].generate_zreading(self.reading_date)
            
            # Return action to view the created Z-reading
            return {
                'type': 'ir.actions.act_window',
                'name': _('Z-Reading Report'),
                'res_model': 'pos.zreading',
                'res_id': zreading.id,
                'view_mode': 'form',
                'target': 'current',
                'context': {'form_view_initial_mode': 'readonly'},
            }
        except UserError as e:
            raise e
        except Exception as e:
            raise UserError(
                f"Error generating Z-reading: {str(e)}\n\n"
                "Please check the logs for more details."
            )

    def action_view_existing_zreading(self):
        """View the existing Z-reading for this date"""
        self.ensure_one()
        
        if not self.existing_zreading_id:
            raise UserError("No Z-reading found for this date.")
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Z-Reading Report'),
            'res_model': 'pos.zreading',
            'res_id': self.existing_zreading_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

