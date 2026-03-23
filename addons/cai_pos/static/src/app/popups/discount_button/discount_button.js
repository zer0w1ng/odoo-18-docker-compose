/** @odoo-module **/

import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { BIRDiscountPopup } from "@cai_pos/app/popups/discount_popup/discount_popup";

/**
 * Patch ControlButtons to add BIR Discount functionality
 */
patch(ControlButtons.prototype, {
    /**
     * Apply BIR Discount (SC/PWD/etc)
     */
    async applyBIRDiscount() {
        const order = this.pos.get_order();
        
        // Validate order has items
        if (!order || order.get_orderlines().length === 0) {
            this.notification.add(
                _t("Please add items to the cart first before applying a discount."),
                { type: "warning" }
            );
            return;
        }
        
        // Get available discount types from the models
        const birDiscountModel = this.pos.models["bir.discount.type"];
        if (!birDiscountModel) {
            this.notification.add(
                _t("No BIR discount types are configured. Please contact your administrator."),
                { type: "warning" }
            );
            return;
        }
        
        const availableDiscounts = birDiscountModel.getAll ? birDiscountModel.getAll() : [];
        
        if (availableDiscounts.length === 0) {
            this.notification.add(
                _t("No BIR discount types are configured. Please contact your administrator."),
                { type: "warning" }
            );
            return;
        }
        
        // Show discount selection popup
        const payload = await makeAwaitable(this.dialog, BIRDiscountPopup, {
            title: _t("Select BIR Discount Type"),
            discountTypes: availableDiscounts,
        });
        
        if (payload) {
            this._applyDiscountToOrder(payload);
        }
    },
    
    /**
     * Remove BIR Discount from the order
     */
    removeBIRDiscount() {
        const order = this.pos.get_order();
        
        // Validate order exists
        if (!order) {
            this.notification.add(
                _t("No active order found."),
                { type: "warning" }
            );
            return;
        }
        
        // Check if order has a BIR discount
        if (!order.hasBIRDiscount()) {
            this.notification.add(
                _t("No BIR discount is currently applied to this order."),
                { type: "warning" }
            );
            return;
        }
        
        // Get discount info for confirmation message
        const discountInfo = order.getBIRDiscount();
        const discountName = discountInfo?.type?.name || "BIR Discount";
        
        // Remove the discount
        const removed = order.removeBIRDiscount();
        
        if (removed) {
            // Show success message
            this.notification.add(
                _t("%(discountName)s has been removed from all items.", {
                    discountName: discountName
                }),
                { type: "success" }
            );
        } else {
            // Show error message
            this.notification.add(
                _t("Failed to remove discount. Please try again."),
                { type: "error" }
            );
        }
    },
    
    /**
     * Apply the selected discount to the order
     * 
     * BIR-COMPLIANT COMPUTATION (Revenue Regulations No. 5-2017):
     * For PWD/SC discounts:
     * 1. First: Remove 12% VAT from gross amount (VAT exemption)
     * 2. Second: Apply 20% discount on the VAT-exempted amount
     * 
     * Example: ₱1,120 total
     *   - Less 12% VAT: ₱120
     *   - VAT-exempt amount: ₱1,000
     *   - Less 20% discount: ₱200
     *   - Amount due: ₱800
     */
    _applyDiscountToOrder(discountData) {
        const order = this.pos.get_order();
        const discountType = discountData.discountType;
        
        // Replace existing discount if any
        if (order.hasBIRDiscount()) {
            this.notification.add(
                _t("Replacing existing discount with %(name)s.", { name: discountType.name }),
                { type: "info" }
            );
            order.removeBIRDiscount();
        }
        
        // Store discount info using update() to ensure reactivity and proper data persistence
        order.update({
            bir_discount_type_id: discountType.id,
            bir_discount_id_number: discountData.idNumber || '',
            bir_discount_id_type: discountData.idType || ''
        });
        
        const orderlines = order.get_orderlines();
        let totalDiscountAmount = 0;
        let totalDiscountableGrossSales = 0;
        
        // BIR-COMPLIANT COMPUTATION
        if (discountType.is_vat_exempt) {
            // For VAT-exempt discounts (PWD/SC):
            // BIR FORMULA: ((Price ÷ 1.12) × (1 - Discount%))
            // Step 1: Remove VAT from price (Price ÷ 1.12)
            // Step 2: Apply discount on VAT-exempt amount
            
            const taxModel = this.pos.models["account.tax"];
            let exemptTax = null;
            
            if (taxModel && taxModel.get && discountType.bir_tax_id) {
                exemptTax = taxModel.get(discountType.bir_tax_id);
            }
            
            for (const line of orderlines) {
                const product = line.get_product();
                
                // Check if product is discountable (default true if field doesn't exist)
                if (product.is_bir_discountable === false) {
                    // Skip non-discountable items
                    continue;
                }
                
                // Get original price (assumed to include 12% VAT)
                const priceUnit = line.price_unit;
                const qty = line.qty;
                const discountPercent = discountType.discount_percent;
                
                // CRITICAL: Calculate the correct VAT-exempt and discounted price
                // Step 1: Remove 12% VAT from original price
                const priceWithoutVAT = priceUnit / 1.12;
                
                // Step 2: Apply discount on VAT-exempt price
                const finalPrice = priceWithoutVAT * (1 - discountPercent / 100);
                
                // Step 3: Calculate the effective discount percentage from original price
                const effectiveDiscountPercent = ((priceUnit - finalPrice) / priceUnit) * 100;
                
                // Calculate actual discount amount for reporting (discount on VAT-exempt amount only)
                const vatExemptAmount = priceWithoutVAT * qty;
                const lineDiscountAmount = vatExemptAmount * (discountPercent / 100);
                
                totalDiscountAmount += lineDiscountAmount;
                totalDiscountableGrossSales += priceUnit * qty;
                
                // First, apply VAT-exempt tax if available
                if (exemptTax) {
                    line.tax_ids = [exemptTax];
                }
                
                // Then apply the calculated effective discount percentage
                line.set_discount(effectiveDiscountPercent);
            }
        } else {
            // For non-VAT-exempt discounts (regular promotional discounts)
            // Apply discount directly on the regular price
            for (const line of orderlines) {
                const product = line.get_product();
                
                // Check if product is discountable (default true if field doesn't exist)
                if (product.is_bir_discountable === false) {
                    // Skip non-discountable items
                    continue;
                }
                
                const prices = line.get_all_prices();
                const baseAmount = prices.priceWithTax;
                const discountAmount = (baseAmount * discountType.discount_percent) / 100;
                
                totalDiscountAmount += discountAmount;
                totalDiscountableGrossSales += baseAmount;
                line.set_discount(discountType.discount_percent);
            }
        }
        
        // Store the calculated discount amount and gross sales using update() for proper persistence
        order.update({
            bir_discount_amount: totalDiscountAmount,
            bir_discountable_gross_sales: totalDiscountableGrossSales
        });
        
        // Recompute order totals
        order.recomputeOrderData();
        
        // Show success message
        this.notification.add(
            _t("%(name)s has been applied.", {
                name: discountType.name
            }),
            { type: "success" }
        );
    },
});
