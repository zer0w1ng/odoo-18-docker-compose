/** @odoo-module **/

import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(Navbar.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.notification = useService("notification");
    },

    /**
     * Generate X-Reading for current session
     */
    async generateXReading() {
        const session = this.pos.session;
        
        if (!session || !session.id) {
            this.dialog.add(AlertDialog, {
                title: "No Active Session",
                body: "There is no active POS session. Please open a session first.",
            });
            return;
        }

        try {
            // Show loading notification
            this.notification.add("Generating X-Reading...", {
                type: "info",
            });

            // Call backend to generate X-reading
            const result = await this.orm.call(
                "pos.xreading",
                "generate_xreading",
                [session.id]
            );

            // Validate result
            if (!result || !result.id) {
                throw new Error("Invalid response from server");
            }

            // Success notification
            this.notification.add(`X-Reading ${result.reading_number || result.id} generated successfully!`, {
                type: "success",
            });

            // Open the X-reading in a new window/tab to download PDF
            const reportUrl = `/report/pdf/cai_pos.report_pos_xreading_document/${result.id}`;
            window.open(reportUrl, '_blank');

        } catch (error) {
            console.error("Error generating X-reading:", error);
            this.dialog.add(AlertDialog, {
                title: "X-Reading Error",
                body: `Failed to generate X-Reading: ${error.message || "Unknown error"}`,
            });
        }
    },
});

