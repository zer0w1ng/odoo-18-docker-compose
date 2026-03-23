/** @odoo-module **/

import { OrderWidget } from "@point_of_sale/app/generic_components/order_widget/order_widget";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";

/**
 * Patch OrderWidget - Green banner removed per user request
 * BIR discount information is shown in the receipt only
 */
patch(OrderWidget.prototype, {
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
    },
});
