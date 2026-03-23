/** @odoo-module **/

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

/**
 * Patch PosStore to auto-apply BIR discount when new products are added
 * 
 * This is done at the store level (addLineToCurrentOrder) rather than ProductScreen
 * to ensure the discount is applied consistently.
 */
patch(PosStore.prototype, {
    async addLineToCurrentOrder(vals, opts = {}, configure = true) {
        const order = this.get_order();
        
        // Check if BIR discount is active BEFORE adding the line
        let hasBIRDiscount = false;
        let discountTypeId = null;
        
        if (order) {
            // Check if BIR discount is active using direct property access
            discountTypeId = order.bir_discount_type_id;
            hasBIRDiscount = !!discountTypeId;
        }
        
        // Call the original method to add the line
        const line = await super.addLineToCurrentOrder(...arguments);
        
        // After adding/merging the line, apply discount if active
        if (hasBIRDiscount && line && order) {
            try {
                // Apply discount to the newly added/merged line
                const discountApplied = order.applyBIRDiscountToLine && order.applyBIRDiscountToLine(line);
                
                if (discountApplied) {
                    // Recalculate the BIR discount totals
                    if (order.recalculateBIRDiscount && typeof order.recalculateBIRDiscount === 'function') {
                        order.recalculateBIRDiscount();
                    }
                    
                    // Trigger recompute to update totals and UI
                    if (order.recomputeOrderData && typeof order.recomputeOrderData === 'function') {
                        order.recomputeOrderData();
                    }
                }
            } catch (e) {
                console.warn('[BIR] Failed to auto-apply discount to new line:', e);
            }
        }
        
        return line;
    },
});
