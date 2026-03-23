from odoo import api, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    """
    Extends POS Session to load BIR discount types into the POS frontend
    and handle voided transactions properly in cash counting.
    
    This is the CRITICAL piece that tells Odoo POS to load your discount data
    when the POS opens. Without this, discounts won't be available in the frontend.
    
    VOIDED TRANSACTION HANDLING:
    - Voided orders are EXCLUDED from cash count calculations
    - This ensures cashiers don't need to return money for voided transactions
    - Overrides _get_closed_orders() and _get_captured_payments_domain()
    """
    _inherit = 'pos.session'

    @api.model
    def _load_pos_data_models(self, config_id):
        """
        Override to add BIR discount types and BIR config to the list of models loaded in POS.
        
        This method is called when POS starts. It returns a list of model names
        that should be loaded from the database into the POS frontend.
        
        We call super() to get the standard list, then add our models to it.
        """
        models = super()._load_pos_data_models(config_id)
        models.append('bir.discount.type')
        models.append('bir.config')
        return models
    
    # ==================== VOIDED TRANSACTION EXCLUSION ====================
    
    def _get_closed_orders(self):
        """
        Override to exclude voided orders from closed orders.
        
        BIR COMPLIANCE:
        - Voided orders should NOT be counted in:
          * Cash register balance calculations
          * Closing control totals
          * Session summaries
        - They ARE still tracked separately in void records for audit trail
        
        This ensures that when a cashier closes the session, they are NOT
        expected to return money for voided transactions.
        """
        # Get base closed orders (not draft, not cancelled)
        closed_orders = self.order_ids.filtered(lambda o: o.state not in ['draft', 'cancel'])
        
        # Exclude voided orders from the count
        non_voided_orders = closed_orders.filtered(lambda o: not o.is_voided)
        
        # Log for debugging
        voided_count = len(closed_orders) - len(non_voided_orders)
        if voided_count > 0:
            voided_amount = sum(closed_orders.filtered(lambda o: o.is_voided).mapped('amount_total'))
            _logger.info(
                f"[BIR VOID] Session {self.name}: Excluding {voided_count} voided orders "
                f"(amount: {voided_amount}) from cash count"
            )
        
        return non_voided_orders
    
    def _get_captured_payments_domain(self):
        """
        Override to exclude payments from voided orders.
        
        This domain is used to calculate:
        - cash_register_balance_end (expected cash)
        - total_payments_amount
        
        By excluding voided order payments, the cashier will NOT be expected
        to return money for transactions that were voided.
        
        BIR COMPLIANCE:
        - Voided transactions are tracked separately
        - They don't affect the expected cash balance
        """
        # Original domain from Odoo core
        base_domain = [
            ('session_id', 'in', self.ids),
            ('pos_order_id.state', 'in', ['paid', 'invoiced', 'done'])
        ]
        
        # Add condition to exclude voided orders
        # The pos_order_id.is_voided = False condition excludes voided payments
        voided_exclusion = [('pos_order_id.is_voided', '=', False)]
        
        return base_domain + voided_exclusion

    def action_generate_xreading(self):
        """
        Generate X-Reading for this session and open the report.
        
        This is a simplified, direct approach without a wizard.
        Users just click the button and the X-reading is generated immediately.
        
        X-Reading can be generated for any session state (open or closed)
        for historical analysis and audit purposes.
        """
        self.ensure_one()
        
        # Generate X-reading (returns a dictionary for JS compatibility)
        xreading_data = self.env['pos.xreading'].generate_xreading(self.id)
        
        # Return action to view and print the X-reading
        return {
            'type': 'ir.actions.act_window',
            'name': _('X-Reading Report'),
            'res_model': 'pos.xreading',
            'res_id': xreading_data['id'],
            'view_mode': 'form',
            'target': 'current',
            'context': {'form_view_initial_mode': 'readonly'},
        }

