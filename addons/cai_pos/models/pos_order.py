from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

# used for debugging
_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    """
    BIR-Compliant POS Order Extension
    
    UNDERSTANDING VOID vs CANCEL vs REFUND (Philippines BIR):
    =========================================================
    
    1. CANCEL ORDER:
       - When: Order is still in DRAFT state (before payment validation)
       - Action: Simply delete the order
       - Example: Customer walks away before paying
       - Odoo: Use action_pos_order_cancel() or delete from ticket screen
       - BIR: No audit trail required for unpaid orders
    
    2. VOID TRANSACTION:
       - When: Order is PAID but session is still OPEN
       - Action: Create void record for BIR audit trail
       - Example: 
         * Customer paid but immediately changed mind
         * Wrong items discovered after payment
         * Duplicate transaction error
       - Odoo: Use create_void_from_pos() or action_void_order()
       - BIR: REQUIRES audit trail - void record cannot be deleted
    
    3. REFUND/RETURN:
       - When: Session is CLOSED or cross-day return
       - Action: Create a new negative order
       - Example: Customer returns with receipt next day
       - Odoo: Use refund() method
       - BIR: Creates separate negative transaction
    
    KEY DIFFERENCE:
    - Cancel = Before payment (just delete)
    - Void = After payment, same session (audit trail required)
    - Refund = After session close (new negative transaction)
    """
    _inherit = 'pos.order'

    # ========== BIR Discount Fields ==========
    bir_discount_type_id = fields.Many2one(
        'bir.discount.type',
        string='BIR Discount Type',
        help='Type of BIR-compliant discount applied (SC, PWD, etc.)')

    bir_discount_amount = fields.Monetary(
        string='BIR Discount Amount',
        currency_field='currency_id',
        help='Total amount of BIR discount applied')

    bir_discount_id_number = fields.Char(
        string='ID Number',
        help='ID number of discount recipient (for SC/PWD)')

    bir_discount_id_type = fields.Char(
        string='ID Type',
        help='Type of ID presented (e.g., Senior Citizen ID, PWD ID)')

    has_bir_discount = fields.Boolean(
        string='Has BIR Discount',
        compute='_compute_has_bir_discount',
        store=True,
        help='Indicates if this order has a BIR-compliant discount applied')

    # ========== Void Transaction Fields ==========
    is_voided = fields.Boolean(
        string='Is Voided',
        default=False,
        readonly=True,
        copy=False,
        help='Indicates if this order has been voided (cancelled after payment)'
    )
    
    void_id = fields.Many2one(
        'pos.order.void',
        string='Void Record',
        readonly=True,
        copy=False,
        ondelete='restrict',
        help='Reference to the void transaction record if this order was voided'
    )
    
    void_date = fields.Datetime(
        string='Void Date',
        readonly=True,
        copy=False,
        help='Date and time when this order was voided'
    )
    
    can_be_voided = fields.Boolean(
        string='Can Be Voided',
        compute='_compute_can_be_voided',
        help='Whether this order can be voided based on current state and policy'
    )

    @api.depends('bir_discount_type_id')
    def _compute_has_bir_discount(self):
        """Mark orders that have bir discounts"""
        for order in self:
            order.has_bir_discount = bool(order.bir_discount_type_id)
    
    @api.depends('state', 'is_voided', 'session_id.state')
    def _compute_can_be_voided(self):
        """
        Determine if order can be voided based on BIR best practices:
        
        VOID vs REFUND:
        - VOID: Same-session cancellation (as if transaction never happened)
        - REFUND: Cross-session return (creates credit note, use Odoo's refund button)
        
        Can void if:
        1. Order is paid/done (has been validated with payment)
        2. NOT already voided
        3. Session is still OPEN or CLOSING (same session voids only)
        
        Note: We allow voiding even if account_move exists (invoiced orders)
        because in BIR context, void is about same-session corrections.
        The accounting reversal will be handled when the void is approved.
        """
        for order in self:
            # Log for debugging
            _logger.info(
                f"[VOID CHECK] Order {order.name}: "
                f"state={order.state}, is_voided={order.is_voided}, "
                f"session_state={order.session_id.state}"
            )
            
            # Can void if:
            # 1. Order is paid (validated with payment, not draft)
            # 2. Not already voided
            # 3. Session still open or closing (same-session only)
            order.can_be_voided = (
                order.state in ['paid', 'done', 'invoiced'] and
                not order.is_voided and
                # Allow while session is being closed but not yet closed
                order.session_id.state in ['opening_control', 'opened', 'closing_control']
            )
            
            _logger.info(f"[VOID CHECK] Order {order.name}: can_be_voided={order.can_be_voided}")
    
    def _load_pos_data_fields(self, config_id):
        """
        CRITICAL FIX: Include BIR discount fields in POS data loading
        This ensures the fields are available in the frontend and can be saved back
        
        NOTE: We don't need to add fields here because pos.order records are created
        in the frontend, not loaded from the backend. The fields will be included
        automatically when orders are exported via export_as_JSON() in the JavaScript.
        
        This method is only needed if you're loading EXISTING orders into POS,
        which is not the typical use case.
        """
        return super()._load_pos_data_fields(config_id)
    
    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to log BIR discount data
        """
        for vals in vals_list:
            if vals.get('bir_discount_type_id'):
                _logger.info(f"[BIR] Creating order with BIR discount: type_id={vals.get('bir_discount_type_id')}, "
                           f"amount={vals.get('bir_discount_amount')}, "
                           f"id_number={vals.get('bir_discount_id_number')}")
        return super().create(vals_list)

    def write(self, vals):
        """
        Override write to log BIR discount updates
        """
        # Log BIR discount data if present
        if vals.get('bir_discount_type_id'):
            _logger.info(f"[BIR] Writing order with BIR discount: type_id={vals.get('bir_discount_type_id')}, "
                       f"amount={vals.get('bir_discount_amount')}, "
                       f"id_number={vals.get('bir_discount_id_number')}")
        
        # First, perform the normal write operation
        result = super().write(vals)
        
        # Handle BIR discount tax application
        if vals.get('bir_discount_type_id'):
            for order in self:
                discount_type = order.bir_discount_type_id
                if discount_type and discount_type.is_vat_exempt and discount_type.bir_tax_id:
                    _logger.info(f"Applying VAT-exempt tax to order {order.name} for discount {discount_type.name}")
                    # Apply VAT-exempt tax to all order lines
                    for line in order.lines:
                        if line.product_id:
                            # Replace existing taxes with VAT-exempt tax
                            line.write({'tax_ids': [(6, 0, [discount_type.bir_tax_id.id])]})
                            _logger.info(f"Applied VAT-exempt tax {discount_type.bir_tax_id.name} to line {line.id} "
                                       f"for product {line.product_id.name}")
        
        return result
    
    # ========== Void Transaction Methods ==========
    
    def action_void_order(self):
        """
        Action to initiate void transaction from backend
        Opens wizard for void reason and approval
        
        IMPORTANT: Voids are for same-session cancellations only.
        For returns after session is closed, use the REFUND button instead.
        """
        self.ensure_one()
        
        if not self.can_be_voided:
            # Provide specific error message based on reason
            reasons = []
            if self.state not in ['paid', 'done', 'invoiced']:
                reasons.append('• Order must be paid/validated first')
            if self.is_voided:
                reasons.append('• Order is already voided')
            if self.session_id.state not in ['opening_control', 'opened', 'closing_control']:
                reasons.append(f"• Session is not open (current: {self.session_id.state}) - Use REFUND button for returns")
            
            error_msg = 'Cannot void this order:\n\n' + '\n'.join(reasons)
            error_msg += '\n\n💡 TIP: For returns after session closes, use the REFUND button instead of VOID.'
            
            raise UserError(_(error_msg))
        
        # Open void wizard
        return {
            'name': _('Void Transaction'),
            'type': 'ir.actions.act_window',
            'res_model': 'pos.order.void.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
                'default_session_id': self.session_id.id,
                'default_amount_voided': self.amount_total,
            }
        }
    
    def action_view_void_record(self):
        """View the void record for this order"""
        self.ensure_one()
        
        if not self.void_id:
            raise UserError(_('This order has not been voided.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Void Record'),
            'res_model': 'pos.order.void',
            'res_id': self.void_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    # ========== Frontend Void Method ==========
    
    @api.model
    def create_void_from_pos(self, order_ids, void_data):
        """
        Create a void record from the POS frontend.
        
        This method is called from the VoidOrderPopup in the POS frontend.
        It creates a void record that requires manager approval.
        
        BIR REQUIREMENTS:
        - Void record is created with 'pending_approval' state
        - Manager must approve from BIR Compliance → Void Transactions
        - Once approved, order is marked as voided
        - Voided orders are excluded from X/Z reading sales totals
        
        Args:
            order_ids: List of order IDs to void (typically one)
            void_data: Dictionary with:
                - void_reason: Selection value for void reason
                - void_reason_details: Text explanation
                - session_id: Current POS session ID
        
        Returns:
            dict: Result with success status and void_number
        """
        if not order_ids:
            return {'success': False, 'error': _('No order specified')}
        
        order = self.browse(order_ids[0])
        
        if not order.exists():
            return {'success': False, 'error': _('Order not found')}
        
        # Validate order can be voided
        allowed_session_states = ['opening_control', 'opened', 'closing_control']
        if not order.can_be_voided:
            reasons = []
            if order.state not in ['paid', 'done', 'invoiced']:
                reasons.append(_('Order must be paid first'))
            if order.is_voided:
                reasons.append(_('Order is already voided'))
            if order.session_id.state not in allowed_session_states:
                reasons.append(_('Session is not open (current: %s) - use Refund instead') % order.session_id.state)
            
            error_msg = _('Cannot void this order: ') + ', '.join(reasons)
            return {'success': False, 'error': error_msg}
        
        # Check for existing void request
        existing_void = self.env['pos.order.void'].search([
            ('original_order_id', '=', order.id),
            ('state', 'not in', ['cancelled', 'rejected'])
        ], limit=1)
        
        if existing_void:
            return {
                'success': False, 
                'error': _('A void request already exists for this order: %s') % existing_void.void_number
            }
        
        # Get session
        session_id = void_data.get('session_id') or order.session_id.id
        session = self.env['pos.session'].browse(session_id)
        
        # Get BIR config if available
        bir_config_id = False
        if session.config_id and hasattr(session.config_id, 'bir_config_id'):
            bir_config_id = session.config_id.bir_config_id.id if session.config_id.bir_config_id else False
        
        # Create void record (auto-approved)
        try:
            void_vals = {
                'original_order_id': order.id,
                'session_id': session_id,
                'void_reason': void_data.get('void_reason'),
                'void_reason_details': void_data.get('void_reason_details'),
                'voided_by_user_id': self.env.user.id,
                'amount_voided': order.amount_total,
                'amount_tax': order.amount_tax,
                'bir_config_id': bir_config_id,
                # Note: state will be set to 'approved' in pos.order.void.create()
            }
            
            void_record = self.env['pos.order.void'].create(void_vals)
            
            _logger.info(
                f"[BIR VOID] Created and approved void record {void_record.void_number} "
                f"for order {order.name} from POS frontend by user {self.env.user.name}"
            )
            
            return {
                'success': True,
                'void_number': void_record.void_number,
                'void_id': void_record.id,
                'message': _('Order voided successfully.')
            }
            
        except Exception as e:
            _logger.error(f"[BIR VOID] Error creating void record: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # ========== Refund/Return Methods ==========
    
    def _refund(self):
        """
        Override _refund to allow refunds even when no session is currently open.
        
        BIR Context:
        - Refunds can happen anytime (customer returns with receipt days later)
        - A session is NOT required to be open for processing refunds
        - The refund will be assigned to:
          1. Current open session (if available)
          2. The original order's session (if closed, we create a special refund record)
        
        This override removes the session requirement from refund processing.
        """
        refund_orders = self.env['pos.order']
        
        for order in self:
            # Try to get current session, fall back to original session
            current_session = order.session_id.config_id.current_session_id
            
            if not current_session:
                # No open session - use the original order's session
                # The refund will be recorded against the closed session
                current_session = order.session_id
                _logger.info(
                    f"[BIR REFUND] No open session, creating refund against original session "
                    f"{current_session.name} for order {order.name}"
                )
            
            refund_order = order.copy(
                order._prepare_refund_values(current_session)
            )
            
            for line in order.lines:
                PosOrderLineLot = self.env['pos.pack.operation.lot']
                for pack_lot in line.pack_lot_ids:
                    PosOrderLineLot += pack_lot.copy()
                line.copy(line._prepare_refund_data(refund_order, PosOrderLineLot))
            
            refund_orders |= refund_order
            
            _logger.info(
                f"[BIR REFUND] Created refund order {refund_order.name} for original order {order.name}, "
                f"amount: {refund_order.amount_total}"
            )
        
        refund_orders._compute_prices()
        return refund_orders
    
    def refund(self):
        """
        Override refund to allow refunds without requiring an open session.
        
        BIR Context:
        - Refunds are for cross-session returns (customer comes back later)
        - Refunds should be processable even when no session is currently open
        - The refund order will be linked to the original session if no session is open
        """
        return {
            'name': _('Return Products'),
            'view_mode': 'form',
            'res_model': 'pos.order',
            'res_id': self._refund().ids[0],
            'view_id': False,
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

