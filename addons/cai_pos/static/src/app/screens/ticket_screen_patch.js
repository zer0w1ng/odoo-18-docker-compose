/** @odoo-module **/
/**
 * Ticket Screen Patch for BIR Void Functionality
 * 
 * Adds a VOID button to paid orders in the ticket screen.
 */

import { patch } from "@web/core/utils/patch";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { VoidOrderPopup } from "@cai_pos/app/popups/void_popup/void_popup";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

patch(TicketScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialog = useService("dialog");
        this.notification = useService("notification");
    },
    
    /**
     * Check if order can be voided
     * Only check if order is paid and not already voided
     */
    canVoidOrder(order) {
        if (!order) return false;
        
        // Order must be in paid/done/invoiced state
        const isPaid = order.state === "paid" || order.state === "done" || order.state === "invoiced";
        if (!isPaid) {
            return false;
        }
        
        // Order must not already be voided
        if (order.is_voided) {
            return false;
        }
        
        // Session must be open (check current session, not order's session)
        const session = this.pos.session;
        if (!session) return false;
        
        const sessionOpen = ["opened", "opening_control", "closing_control"].includes(session.state);
        if (!sessionOpen) {
            return false;
        }
        
        return true;
    },
    
    /**
     * Show void popup for the selected order
     */
    async onVoidOrder(order) {
        if (!order) {
            this.notification.add(_t("No order selected"), { type: "warning" });
            return;
        }
        
        if (!this.canVoidOrder(order)) {
            let message = _t("Cannot void this order.");
            
            if (order.state === "draft") {
                message = _t("Order is not paid yet. Use 'Cancel Order' (trash icon) instead.");
            } else if (order.state === "cancel") {
                message = _t("Order is already cancelled.");
            } else if (order.is_voided) {
                message = _t("Order is already voided.");
            } else if (!["opened", "opening_control", "closing_control"].includes(this.pos.session?.state)) {
                message = _t("Session is closed. Please open a session first.");
            }
            
            this.notification.add(message, { type: "warning" });
            return;
        }
        
        // Open void popup
        this.dialog.add(VoidOrderPopup, {
            order: order,
        });
    },
    
    /**
     * Check if void button should be shown for this order
     */
    shouldShowVoidButton(order) {
        return this.canVoidOrder(order);
    },
});

