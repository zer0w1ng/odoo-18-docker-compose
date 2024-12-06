/** @odoo-module **/

import { formView } from "@web/views/form/form_view";
import { registry } from "@web/core/registry";
import { bus_book_seat_form_controller } from "@bi_bus_booking_management/js/bus_book_seat_form_controller";
export const bus_book = {
    ...formView,
    Controller: bus_book_seat_form_controller,
}
registry.category("views").add("bus_book_seat", bus_book);
