/** @odoo-module **/

import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { patch } from "@web/core/utils/patch";

/**
 * Patch PosOrderline to fix the misleading discount percentage display
 * 
 * For BIR VAT-exempt discounts (SC/PWD), the effective discount stored in line.discount
 * includes both VAT removal (÷1.12) and the actual discount (20%), resulting in ~28.57%
 * 
 * This patch modifies getDisplayData() to show a cleaner message instead of the 
 * confusing combined percentage.
 */
patch(PosOrderline.prototype, {
    getDisplayData() {
        const data = super.getDisplayData(...arguments);
        
        // Check if this line has a significant discount (> 20%) which indicates 
        // it's a VAT-exempt discount (SC/PWD) with combined VAT removal + discount
        const discountValue = parseFloat(this.discount) || 0;
        
        if (discountValue > 20) {
            // This is likely a VAT-exempt discount - replace the confusing percentage
            // with a cleaner display message
            data.discount = "VAT-Exempt+20";
        }
        
        return data;
    },
});

