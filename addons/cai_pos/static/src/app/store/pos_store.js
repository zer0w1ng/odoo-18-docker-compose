/** @odoo-module **/

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { PosOrder } from "@point_of_sale/app/models/pos_order";

patch(PosStore.prototype, {
    getBIRDiscountTypes() {
        if (!this.models || !this.models["bir.discount.type"]) {
            return [];
        }
        const birDiscounts = this.models["bir.discount.type"];
        return birDiscounts.getAll ? birDiscounts.getAll() : [];
    },
    
    getBIRConfig() {
        if (!this.models || !this.models["bir.config"]) {
            return null;
        }
        const birConfigModel = this.models["bir.config"];
        const configs = birConfigModel.getAll ? birConfigModel.getAll() : [];
        return configs.length > 0 ? configs[0] : null;
    },
});


patch(PosOrder.prototype, {
    setup(vals) {
        super.setup(...arguments);
        
        // Initialize BIR discount properties directly on the order object
        this.bir_discount_type_id = vals.bir_discount_type_id || null;
        this.bir_discount_amount = vals.bir_discount_amount || 0;
        this.bir_discount_id_number = vals.bir_discount_id_number || '';
        this.bir_discount_id_type = vals.bir_discount_id_type || '';
        this.bir_discountable_gross_sales = vals.bir_discountable_gross_sales || 0;
    },
    
    /**
     * Apply BIR discount to a single NEW line (used when adding products to an order with active discount)
     */
    applyBIRDiscountToLine(line) {
        const typeId = this.bir_discount_type_id;
        if (!typeId || !this.models) {
            return false;
        }
        
        const birDiscountModel = this.models["bir.discount.type"];
        if (!birDiscountModel) {
            return false;
        }
        
        const discountType = birDiscountModel.get(typeId);
        if (!discountType) {
            return false;
        }
        
        const product = line.get_product ? line.get_product() : line.product_id;
        if (!product) {
            return false;
        }
        
        // Check if product is discountable
        if (product.is_bir_discountable === false) {
            return false;
        }
        
        // Apply discount based on type (VAT-exempt or regular)
        if (discountType.is_vat_exempt) {
            const priceUnit = line.price_unit;
            const priceWithoutVAT = priceUnit / 1.12;
            const finalPrice = priceWithoutVAT * (1 - discountType.discount_percent / 100);
            const effectiveDiscountPercent = ((priceUnit - finalPrice) / priceUnit) * 100;
            
            // Apply VAT-exempt tax if available
            const taxModel = this.models["account.tax"];
            if (taxModel && taxModel.get && discountType.bir_tax_id) {
                const exemptTax = taxModel.get(discountType.bir_tax_id);
                if (exemptTax) {
                    line.tax_ids = [exemptTax];
                }
            }
            
            line.discount = effectiveDiscountPercent;
        } else {
            line.discount = discountType.discount_percent;
        }
        
        return true;
    },
    
    /**
     * Recalculate total BIR discount amount and gross sales from all lines
     */
    recalculateBIRDiscount() {
        const typeId = this.bir_discount_type_id;
        if (!typeId || !this.models) {
            return;
        }
        
        const birDiscountModel = this.models["bir.discount.type"];
        if (!birDiscountModel) {
            return;
        }
        
        const discountType = birDiscountModel.get(typeId);
        if (!discountType) {
            return;
        }
        
        let totalDiscountAmount = 0;
        let totalGrossSales = 0;
        
        const orderlines = this.get_orderlines();
        for (const line of orderlines) {
            const product = line.get_product();
            
            // Only calculate discount for discountable items
            if (product.is_bir_discountable === false) {
                continue;
            }
            
            const prices = line.get_all_prices();
            
            if (discountType.is_vat_exempt) {
                // For VAT-exempt: discount is on the base amount (without tax)
                const lineDiscountAmount = prices.priceWithoutTaxBeforeDiscount - prices.priceWithoutTax;
                totalDiscountAmount += lineDiscountAmount;
                totalGrossSales += prices.priceWithTaxBeforeDiscount;
            } else {
                // For regular discounts: calculate from price with tax
                const lineDiscountAmount = prices.priceWithTaxBeforeDiscount - prices.priceWithTax;
                totalDiscountAmount += lineDiscountAmount;
                totalGrossSales += prices.priceWithTaxBeforeDiscount;
            }
        }
        
        // Use update() to ensure reactivity and proper data persistence
        this.update({
            bir_discount_amount: totalDiscountAmount,
            bir_discountable_gross_sales: totalGrossSales
        });
    },
    
    /**
     * Override removeOrderline to recalculate BIR discount when lines are removed
     */
    removeOrderline(line) {
        const result = super.removeOrderline(...arguments);
        
        // Recalculate BIR discount after line removal
        if (this.bir_discount_type_id) {
            this.recalculateBIRDiscount();
        }
        
        return result;
    },
    
    /**
     * Override recomputeOrderData to also recalculate BIR discount
     */
    recomputeOrderData() {
        super.recomputeOrderData(...arguments);
        
        // Recalculate BIR discount when order data changes
        if (this.bir_discount_type_id) {
            this.recalculateBIRDiscount();
        }
    },
    
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        
        // Export BIR discount fields to JSON for backend persistence
        json.bir_discount_type_id = this.bir_discount_type_id || false;
        json.bir_discount_amount = this.bir_discount_amount || 0;
        json.bir_discount_id_number = this.bir_discount_id_number || '';
        json.bir_discount_id_type = this.bir_discount_id_type || '';
        json.bir_discountable_gross_sales = this.bir_discountable_gross_sales || 0;
        
        return json;
    },
    
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        
        // Initialize BIR discount fields from JSON
        this.bir_discount_type_id = json.bir_discount_type_id || null;
        this.bir_discount_amount = json.bir_discount_amount || 0;
        this.bir_discount_id_number = json.bir_discount_id_number || '';
        this.bir_discount_id_type = json.bir_discount_id_type || '';
        this.bir_discountable_gross_sales = json.bir_discountable_gross_sales || 0;
    },
    
    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(baseUrl, headerData);
        result.is_reprint = Boolean(this.id);
        
        // Add BIR discount information for printing
        result.bir_discount = null;
        
        if (this.bir_discount_type_id) {
            const birDiscountModel = this.models ? this.models["bir.discount.type"] : null;
            
            if (birDiscountModel) {
                const discountType = birDiscountModel.get(this.bir_discount_type_id);
                if (discountType) {
                    result.bir_discount = {
                        name: discountType.name,
                        code: discountType.code,
                        percent: discountType.discount_percent,
                        amount: this.bir_discount_amount || 0,
                        id_number: this.bir_discount_id_number || '',
                        id_type: this.bir_discount_id_type || '',
                        is_vat_exempt: discountType.is_vat_exempt,
                        discountable_gross_sales: this.bir_discountable_gross_sales || 0,
                    };
                }
            }
        }
        
        // Add BIR config information for printing
        result.bir_config = null;
        const birConfigModel = this.models ? this.models["bir.config"] : null;
        
        if (birConfigModel) {
            const configs = birConfigModel.getAll ? birConfigModel.getAll() : [];
            if (configs.length > 0) {
                const config = configs[0];
                result.bir_config = {
                    business_name: config.business_name,
                    business_address: config.business_address,
                    tin: config.tin,
                    permit_number: config.permit_number,
                    accreditation_number: config.accreditation_number,
                    min_number: config.min_number,
                    serial_number: config.serial_number,
                    terminal_id: config.terminal_id,
                    receipt_prefix: config.receipt_prefix,
                    pos_software_name: config.pos_software_name,
                    pos_software_version: config.pos_software_version,
                };
            }
        }
        
        // Calculate BIR-compliant VAT breakdown
        result.bir_vat_breakdown = this._calculateBIRVATBreakdown(result);
        
        return result;
    },
    
    _calculateBIRVATBreakdown(printData) {
        const breakdown = {
            vatable_sales: 0,
            vat_amount: 0,
            vat_exempt_sales: 0,
            zero_rated_sales: 0,
        };
        
        if (!printData.taxTotals || !printData.taxTotals.subtotals) {
            return breakdown;
        }
        
        const hasVATExemptDiscount = printData.bir_discount && printData.bir_discount.is_vat_exempt;
        
        if (hasVATExemptDiscount) {
            breakdown.vat_exempt_sales = printData.taxTotals.base_amount_currency || 0;
        } else {
            for (const subtotal of printData.taxTotals.subtotals) {
                const taxAmount = subtotal.tax_amount_currency || 0;
                const baseAmount = subtotal.base_amount_currency || 0;
                
                if (taxAmount > 0) {
                    breakdown.vatable_sales += baseAmount;
                    breakdown.vat_amount += taxAmount;
                } else if (baseAmount > 0) {
                    breakdown.zero_rated_sales += baseAmount;
                }
            }
        }
        
        return breakdown;
    },
    
    getBIRDiscount() {
        if (!this.bir_discount_type_id) {
            return null;
        }
        
        if (!this.models || !this.models["bir.discount.type"]) {
            return {
                type: { name: "Unknown Discount", discount_percent: 0 },
                amount: this.bir_discount_amount || 0,
                id_number: this.bir_discount_id_number || '',
                id_type: this.bir_discount_id_type || '',
            };
        }
        
        const birDiscountModel = this.models["bir.discount.type"];
        const discountType = birDiscountModel.get(this.bir_discount_type_id);
        
        if (!discountType) {
            return {
                type: { name: "Unknown Discount", discount_percent: 0 },
                amount: this.bir_discount_amount || 0,
                id_number: this.bir_discount_id_number || '',
                id_type: this.bir_discount_id_type || '',
            };
        }
        
        return {
            type: discountType,
            amount: this.bir_discount_amount || 0,
            id_number: this.bir_discount_id_number || '',
            id_type: this.bir_discount_id_type || '',
        };
    },
    
    hasBIRDiscount() {
        return Boolean(this.bir_discount_type_id);
    },
    
    removeBIRDiscount() {
        if (!this.bir_discount_type_id) {
            return false;
        }
        
        try {
            const orderlines = this.get_orderlines();
            
            for (const line of orderlines) {
                line.discount = 0;
                // Restore original taxes
                const product = line.get_product();
                if (product && product.taxes_id) {
                    line.tax_ids = product.taxes_id;
                }
            }
            
            // Use update() to ensure data is properly cleared and persisted
            this.update({
                bir_discount_type_id: null,
                bir_discount_amount: 0,
                bir_discount_id_number: '',
                bir_discount_id_type: '',
                bir_discountable_gross_sales: 0
            });
            
            // Recompute order totals
            this.recomputeOrderData();
        } catch (e) {
            console.warn('[BIR] Error removing discount:', e);
        }
        
        return true;
    },
});
