/** @odoo-module **/
/**
 * VoidOrderPopup - BIR-Compliant Void Transaction Popup
 * 
 * Simple void popup for POS interface.
 * Voiding creates a record for BIR audit trail and marks the order as voided.
 */

import { Component, useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";

export class VoidOrderPopup extends Component {
    static template = "cai_pos.VoidOrderPopup";
    static components = { Dialog };
    static props = {
        order: Object,
        close: Function,
    };

    setup() {
        this.pos = usePos();
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        this.state = useState({
            voidReason: "",
            voidReasonDetails: "",
            isProcessing: false,
            errorMessage: "",
        });
        
        // Predefined void reasons per BIR requirements
        this.voidReasons = [
            { value: "customer_request", label: _t("Customer Request"), description: _t("Customer requested to cancel this transaction.") },
            { value: "wrong_item", label: _t("Wrong Item Entered"), description: _t("Wrong item was entered in the order.") },
            { value: "wrong_price", label: _t("Wrong Price"), description: _t("Incorrect price was entered.") },
            { value: "wrong_quantity", label: _t("Wrong Quantity"), description: _t("Wrong quantity was entered.") },
            { value: "payment_error", label: _t("Payment Error"), description: _t("Payment processing error occurred.") },
            { value: "system_error", label: _t("System Error"), description: _t("System error during transaction processing.") },
            { value: "duplicate_transaction", label: _t("Duplicate Transaction"), description: _t("This is a duplicate of another transaction.") },
            { value: "order_cancelled", label: _t("Order Cancelled"), description: _t("Order was cancelled.") },
            { value: "other", label: _t("Other Reason"), description: "" },
        ];
    }

    get order() {
        return this.props.order;
    }
    
    onReasonChange(ev) {
        this.state.voidReason = ev.target.value;
        // Auto-fill description based on selected reason
        const selectedReason = this.voidReasons.find(r => r.value === this.state.voidReason);
        if (selectedReason && selectedReason.description && !this.state.voidReasonDetails) {
            this.state.voidReasonDetails = selectedReason.description;
        }
    }
    
    onDetailsChange(ev) {
        this.state.voidReasonDetails = ev.target.value;
    }
    
    async confirmVoid() {
        // Validate inputs
        if (!this.state.voidReason) {
            this.state.errorMessage = _t("Please select a void reason.");
            return;
        }
        
        if (!this.state.voidReasonDetails || this.state.voidReasonDetails.trim().length < 5) {
            this.state.errorMessage = _t("Please provide a reason (minimum 5 characters).");
            return;
        }
        
        this.state.isProcessing = true;
        this.state.errorMessage = "";
        
        try {
            // Get order ID - handle both number and object with id property
            const orderId = typeof this.order.id === 'number' ? this.order.id : this.order.id;
            
            // Call backend to create void record
            const result = await this.orm.call(
                "pos.order",
                "create_void_from_pos",
                [[orderId], {
                    void_reason: this.state.voidReason,
                    void_reason_details: this.state.voidReasonDetails,
                    session_id: this.pos.session.id,
                }]
            );
            
            if (result.success) {
                this.notification.add(
                    _t("Order voided successfully: %s", result.void_number),
                    { type: "success" }
                );
                
                // Mark order as voided in frontend
                if (this.order) {
                    this.order.is_voided = true;
                }
                
                // Close the popup
                this.props.close();
            } else {
                this.state.errorMessage = result.error || _t("Failed to void order.");
            }
        } catch (error) {
            console.error("[VOID] Error:", error);
            this.state.errorMessage = error.message || _t("An error occurred.");
        } finally {
            this.state.isProcessing = false;
        }
    }
    
    cancel() {
        this.props.close();
    }
}
