/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";

/**
 * BIR Discount Selection Popup
 * 
 * Popup for selecting discount type and entering ID information
 * for SC/PWD discounts that require verification.
 */
export class BIRDiscountPopup extends Component {
    static template = "cai_pos.BIRDiscountPopup";
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        discountTypes: { type: Array, optional: true },
        getPayload: Function,
        close: Function,
    };
    static defaultProps = {
        title: _t("Apply Discount"),
        discountTypes: [],
    };

    setup() {
        this.state = useState({
            selectedDiscount: null,
            idNumber: "",
            idType: "",
            showIdFields: false,
        });
    }

    get discountTypes() {
        return this.props.discountTypes || [];
    }

    selectDiscount(discountType) {
        this.state.selectedDiscount = discountType;
        this.state.showIdFields = discountType.requires_id;
        
        // Pre-fill ID type based on discount type
        if (discountType.discount_type === 'sc') {
            this.state.idType = _t("Senior Citizen ID");
        } else if (discountType.discount_type === 'pwd') {
            this.state.idType = _t("PWD ID");
        } else if (discountType.discount_type === 'gov') {
            this.state.idType = _t("Government ID / PO");
        }
    }

    getDiscountClass(discountType) {
        const baseClass = "discount-option btn btn-lg m-2 p-3";
        if (this.state.selectedDiscount === discountType) {
            return baseClass + " btn-success";
        }
        
        // Color code by type
        if (discountType.discount_type === 'sc') {
            return baseClass + " btn-info";
        } else if (discountType.discount_type === 'pwd') {
            return baseClass + " btn-warning";
        } else if (discountType.discount_type === 'gov') {
            return baseClass + " btn-secondary";
        }
        return baseClass + " btn-primary";
    }

    getDiscountIcon(discountType) {
        if (discountType.discount_type === 'sc') {
            return "fa-user-md";
        } else if (discountType.discount_type === 'pwd') {
            return "fa-wheelchair";
        } else if (discountType.discount_type === 'gov') {
            return "fa-university";
        }
        return "fa-tag";
    }

    updateIdNumber(event) {
        this.state.idNumber = event.target.value;
    }

    updateIdType(event) {
        this.state.idType = event.target.value;
    }

    computePayload() {
        const discount = this.state.selectedDiscount;
        
        if (!discount) {
            return null;
        }

        if (discount.requires_id && !this.state.idNumber) {
            return null;
        }

        return {
            discountType: discount,
            idNumber: this.state.idNumber,
            idType: this.state.idType,
        };
    }

    confirm() {
        const discount = this.state.selectedDiscount;
        
        if (!discount) {
            alert(_t("Please select a discount type"));
            return;
        }

        if (discount.requires_id && !this.state.idNumber) {
            alert(_t("ID Number is required for this discount type"));
            return;
        }

        const payload = this.computePayload();
        this.props.getPayload(payload);
        this.props.close();
    }

    cancel() {
        this.props.getPayload(null);
        this.props.close();
    }
}

