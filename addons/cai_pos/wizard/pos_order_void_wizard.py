# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class PosOrderVoidWizard(models.TransientModel):
    """
    Wizard for voiding POS orders
    Ensures proper authorization and reason documentation per BIR requirements
    """
    _name = 'pos.order.void.wizard'
    _description = 'POS Order Void Wizard'
    
    # Reference to order being voided
    order_id = fields.Many2one(
        'pos.order',
        string='Order to Void',
        required=True,
        readonly=True,
        help='The POS order that will be voided'
    )
    
    order_name = fields.Char(
        related='order_id.name',
        string='Order Number',
        readonly=True
    )
    
    order_date = fields.Datetime(
        related='order_id.date_order',
        string='Order Date',
        readonly=True
    )
    
    amount_total = fields.Monetary(
        related='order_id.amount_total',
        string='Order Amount',
        readonly=True
    )
    
    currency_id = fields.Many2one(
        related='order_id.currency_id',
        readonly=True
    )
    
    session_id = fields.Many2one(
        'pos.session',
        string='Session',
        required=True,
        readonly=True
    )
    
    # Void reason
    void_reason = fields.Selection([
        ('customer_request', 'Customer Request'),
        ('wrong_item', 'Wrong Item Entered'),
        ('wrong_price', 'Wrong Price'),
        ('wrong_quantity', 'Wrong Quantity'),
        ('payment_error', 'Payment Error'),
        ('system_error', 'System Error'),
        ('duplicate_transaction', 'Duplicate Transaction'),
        ('order_cancelled', 'Order Cancelled'),
        ('training_mode', 'Training/Testing'),
        ('other', 'Other Reason'),
    ], string='Void Reason',
        required=True,
        help='Select the reason for voiding this transaction'
    )
    
    void_reason_details = fields.Text(
        string='Detailed Explanation',
        required=True,
        help='Provide detailed explanation for voiding this transaction (required for BIR audit trail)'
    )
    
    # Authorization
    requires_supervisor_approval = fields.Boolean(
        string='Requires Supervisor Approval',
        default=True,
        readonly=True,
        help='Whether this void requires manager approval'
    )
    
    # Additional info
    notes = fields.Text(
        string='Additional Notes',
        help='Any additional notes or comments'
    )
    
    # Warnings/Info
    warning_message = fields.Text(
        string='Warning',
        compute='_compute_warning_message',
        readonly=True
    )
    
    @api.depends('order_id', 'order_id.state', 'order_id.is_voided')
    def _compute_warning_message(self):
        """Display warnings about voiding this order"""
        for wizard in self:
            messages = []
            
            if wizard.order_id:
                if wizard.order_id.is_voided:
                    messages.append('⚠️ This order is already voided!')
                
                if wizard.order_id.state == 'cancel':
                    messages.append('⚠️ This order is already cancelled!')
                
                if wizard.order_id.state not in ['paid', 'done', 'invoiced']:
                    messages.append('⚠️ Order must be in paid/done state to be voided!')
                
                if wizard.order_id.session_id.state == 'closed':
                    messages.append('⚠️ Cannot void orders from closed sessions!')
                
                if wizard.order_id.has_bir_discount:
                    messages.append('ℹ️ This order has BIR discount (SC/PWD). Void will be tracked separately.')
                
                # Check void age
                if wizard.order_id.date_order:
                    from datetime import datetime
                    age_hours = (datetime.now() - wizard.order_id.date_order.replace(tzinfo=None)).total_seconds() / 3600
                    if age_hours > 24:
                        messages.append(f'⚠️ This order is {int(age_hours)} hours old. Consider creating a refund instead.')
            
            wizard.warning_message = '\n'.join(messages) if messages else False
    
    def action_void_order(self):
        """
        Process the void transaction
        Creates void record and marks order as voided
        """
        self.ensure_one()
        
        # Validate order can be voided
        if not self.order_id.can_be_voided:
            raise UserError(_(
                'This order cannot be voided. Please check:\n'
                '- Order state must be paid/done/invoiced\n'
                '- Order must not already be voided\n'
                '- Session must still be open'
            ))
        
        # Create void record (always pending approval)
        void_vals = {
            'original_order_id': self.order_id.id,
            'session_id': self.session_id.id,
            'void_reason': self.void_reason,
            'void_reason_details': self.void_reason_details,
            'notes': self.notes,
            'voided_by_user_id': self.env.user.id,
            'amount_voided': self.order_id.amount_total,
            'bir_config_id': self.session_id.config_id.bir_config_id.id if self.session_id.config_id.bir_config_id else False,
            'state': 'pending_approval',  # Always pending, approve from menu
        }
        
        void_record = self.env['pos.order.void'].create(void_vals)
        
        _logger.info(f"[BIR VOID] Created void record {void_record.void_number} for order {self.order_id.name}")
        
        # Add message to void record for user to see
        message = _('⏳ Void request created. Approve it from: BIR Compliance → Void Transactions')
        void_record.message_post(
            body=message,
            message_type='notification'
        )
        
        # Return simple action to view the void record
        return {
            'type': 'ir.actions.act_window',
            'name': _('Void Record'),
            'res_model': 'pos.order.void',
            'res_id': void_record.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    
    @api.onchange('void_reason')
    def _onchange_void_reason(self):
        """Auto-fill common descriptions based on reason"""
        if self.void_reason:
            descriptions = {
                'customer_request': 'Customer requested to cancel this transaction.',
                'wrong_item': 'Wrong item was entered in the order.',
                'wrong_price': 'Incorrect price was entered.',
                'wrong_quantity': 'Wrong quantity was entered.',
                'payment_error': 'Payment processing error occurred.',
                'system_error': 'System error during transaction processing.',
                'duplicate_transaction': 'This is a duplicate of another transaction.',
                'order_cancelled': 'Order was cancelled by customer before completion.',
                'training_mode': 'Transaction was created during training/testing.',
            }
            if self.void_reason in descriptions and not self.void_reason_details:
                self.void_reason_details = descriptions[self.void_reason]

