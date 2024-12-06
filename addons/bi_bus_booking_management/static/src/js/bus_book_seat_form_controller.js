/** @odoo-module **/

import { Component, onWillStart } from "@odoo/owl";
import { FormController } from '@web/views/form/form_controller';
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

export class bus_book_seat_form_controller extends FormController {
	setup() {
		super.setup();
		const ormService = useService("orm");
		onWillStart(async () => {
			const data = await this;
			if (data.props.context) {
				return this._bus_book_seat(
					data.props.context.default_m2o_fleet_vehicle_id
				).then(function () {
					return true;
				});
			}
			return true;
		})
	};

	_bus_book_seat(m2o_fleet_vehicle_id) {
		var self = this;
		var m2o_fleet_vehicle_id = m2o_fleet_vehicle_id;
		var data = this.props;
		return rpc('/bus_booking_seat', {
			"m2o_fleet_vehicle_id": data,
		}).then(function (configurator) {
			self.render = configurator;
			self.custom_render(configurator)
			setTimeout(function(){
				var cla = document.getElementsByClassName("o_bus_book_seat_view");
				 cla[0].innerHTML = self.render; 
			}, 20)
		})
	}

	custom_render(configurator){
	}
}
