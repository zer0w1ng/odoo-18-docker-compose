# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
import werkzeug

class BusBookSeat(http.Controller):

    @http.route(['/bus_booking_seat'], type='json', auth="user", methods=['POST'])
    def bus_booking_seat(self, m2o_fleet_vehicle_id):
        fleet_vehicle_obj = request.env["fleet.vehicle"].sudo()
        trip_information_line_obj = request.env["trip.information.line"].sudo()
        pickup_dropoff_points_obj = request.env["pickup.dropoff.points"].sudo()
        bus_routes_line_obj = request.env["bus.routes.line"].sudo()
        bus_amenities_obj = request.env["bus.amenities"].sudo()
        if m2o_fleet_vehicle_id.get("context",False):
            fleet_vehicle_id = m2o_fleet_vehicle_id["context"]
            pickup_dropoff_points_1_ids = False
            pickup_dropoff_points_2_ids = False
            bus_amenities_ids = False
            if fleet_vehicle_id.get("default_m2o_fleet_vehicle_id",False):
                fleet_vehicle = fleet_vehicle_id["default_m2o_fleet_vehicle_id"]
                bus_id = fleet_vehicle_obj.browse(fleet_vehicle)
                if fleet_vehicle_id.get("default_pick_up_drop_off_points_1",False):
                    pickup_dropoff_points_1_ids = pickup_dropoff_points_obj.browse(fleet_vehicle_id.get("default_pick_up_drop_off_points_1",False))
                if fleet_vehicle_id.get("default_pick_up_drop_off_points_1",False):
                    pickup_dropoff_points_2_ids = pickup_dropoff_points_obj.browse(fleet_vehicle_id.get("default_pick_up_drop_off_points_2",False))
                if fleet_vehicle_id.get("default_m2m_bus_amenities_ids",False):
                    bus_amenities_ids = bus_amenities_obj.browse(fleet_vehicle_id.get("default_m2m_bus_amenities_ids",False))
                bus_routes_line_id = bus_routes_line_obj.browse(int(fleet_vehicle_id.get("default_routes_line_id",False)))
                seat_detail = {
                                      "bus_routes_line_id":fleet_vehicle_id.get("default_routes_line_id",False),
                                      "total_row":bus_id.m2o_bus_types_id.total_row,
                                      "total_seat_in_single_row":bus_id.m2o_bus_types_id.total_seat_in_single_row,
                                      "bus_type":bus_id.m2o_bus_types_id.bus_type,
                                      "price":fleet_vehicle_id.get("default_price",False),
                                      "pick_up_drop_off_points_1":pickup_dropoff_points_1_ids,
                                      "pick_up_drop_off_points_2":pickup_dropoff_points_2_ids,
                                      "m2m_bus_amenities_ids":bus_amenities_ids,
                                     }
                trip_information_line = trip_information_line_obj.search([("trip_information_id.journey_date", "=", bus_routes_line_id.journey_date),
                                          ("trip_information_id.m2o_fleet_vehicle_id", "=", bus_routes_line_id.m2o_fleet_vehicle_id.id)])
                seat_list = []
                if trip_information_line:
                    for trip_information in trip_information_line:
                        if trip_information.is_booked:
                            seat_list.append(int(trip_information.seat_number))
                    seat_detail.update({"booked_seat":seat_list})
                return request.env['ir.ui.view']._render_template("bi_bus_booking_management.bus_book_seat",seat_detail)

    @http.route(['/bus_booking_confirm'], type='http', auth="public", 
                                methods=['POST','GET'], website=True, csrf=False, sitemap=True)
    def bus_booking_confirm_checkout(self, **kwargs):
        record_list = []
        order_line_list = []
        order_line_dict = {}
        order_dict = {}
        bus_routes_line_obj = request.env["bus.routes.line"].sudo()
        pickup_dropoff_points_obj = request.env["pickup.dropoff.points"].sudo()
        trip_information_obj = request.env["trip.information"].sudo()
        trip_information_line_obj = request.env["trip.information.line"].sudo()
        sale_order = False

        for a, b in kwargs.items():
            if "seat_number" in a:
                record_list.append(b)
            if "name" in a:
                record_list.append(b)
            if "email" in a:
                record_list.append(b)
            if "age" in a:
                record_list.append(b)
            if "gender" in a:
                record_list.append(b)
            if "number" in a:
                record_list.append(b)
            if "seat_line" in a:
                record_list.append(b)

        bus_routes_line_id = bus_routes_line_obj.browse(int(kwargs.get("route_line",False)))
        trip_information_line = trip_information_line_obj.search([("trip_information_id.journey_date", "=", bus_routes_line_id.journey_date),
                                          ("trip_information_id.m2o_fleet_vehicle_id", "=", bus_routes_line_id.m2o_fleet_vehicle_id.id)])
        seat_list = []
        seat_dict = {}
        if record_list:
            total = len(record_list) / 8
            count = 0
            for i in range(int(total)):
                order_line_dict = (0,0,{
                                "product_id":request.env.ref('bi_bus_booking_management.bus_ticket_product').id,
                                "seat_number":record_list[count+1],
                                "customer_name":record_list[count+2],
                                "email":record_list[count+3],
                                "age":int(record_list[count+4]),
                                "gender":record_list[count+5],
                                "number":record_list[count+6],
                                "price_unit":bus_routes_line_id.price,
                                "bus_routes_line_id":bus_routes_line_id.id,
                               })

                seat_dict = (0,0,{
                                "seat_number":record_list[count+1],
                                "customer_name":record_list[count+2],
                                "email":record_list[count+3],
                                "age":int(record_list[count+4]),
                                "gender":record_list[count+5],
                                "number":record_list[count+6],
                                "m2o_bus_point_pickup_id":pickup_dropoff_points_obj.browse(int(kwargs.get("pick_up_drop_off_points_1",False))).id,
                                "m2o_bus_point_dropoff_id":pickup_dropoff_points_obj.browse(int(kwargs.get("pick_up_drop_off_points_2",False))).id,
                                "start_time":bus_routes_line_id.start_time,
                                "end_time":bus_routes_line_id.end_time,
                                "is_booked":True,
                                'booking_status':'booked'
                               })
                seat_list.append(seat_dict)
                count += 8
                order_line_list.append(order_line_dict)

            order_dict = self.get_order_details(order_dict,kwargs,bus_routes_line_id,order_line_list)
            sale_order = request.env["sale.order"].sudo().create(order_dict)

            trip_information_dict = {}
            trip_information_dict = self.trip_information_detail(seat_list, bus_routes_line_id, trip_information_dict)
            if not trip_information_line:
                trip_information_id = trip_information_obj.create(trip_information_dict)
                sale_order.trip_information_id = trip_information_id.id

            elif trip_information_line:
                trip_information_line[0].trip_information_id.sudo().write({"trip_information_line_ids":seat_list})
                sale_order.trip_information_id = trip_information_line[0].trip_information_id.id

            action_id = request.env.ref('bi_bus_booking_management.action_bus_tickets')
            return request.redirect('/web#id=%s&action=%s&model=sale.order&view_type=form' %(sale_order.id,action_id.id))

    def get_order_details(self, order_dict, kwargs, bus_routes_line_id, order_line_list):
        pickup_dropoff_points_obj = request.env["pickup.dropoff.points"].sudo()
        order_dict = {
                      "partner_id":request.env.user.partner_id.id,
                      "m2o_bus_point_pickup_id":pickup_dropoff_points_obj.browse(int(kwargs.get("pick_up_drop_off_points_1",False))).id,
                      "m2o_bus_point_dropoff_id":pickup_dropoff_points_obj.browse(int(kwargs.get("pick_up_drop_off_points_2",False))).id,
                      "journey_date":bus_routes_line_id.m2o_bus_routes_id.journey_date,
                      "start_time":bus_routes_line_id.start_time,
                      "end_time":bus_routes_line_id.end_time,
                      "m2o_bus_start_point_id":bus_routes_line_id.m2o_bus_routes_id.m2o_bus_point_pickup_id.id,
                      "m2o_bus_end_point_id":bus_routes_line_id.m2o_bus_routes_id.m2o_bus_point_dropoff_id.id,
                      "point_start_time":bus_routes_line_id.m2o_bus_routes_id.start_time,
                      "point_end_time":bus_routes_line_id.m2o_bus_routes_id.end_time,
                      "order_line":order_line_list,
                      "is_bus_order":True,
        }
        return order_dict

    def trip_information_detail(self, seat_list, bus_routes_line_id, trip_information_dict):
        trip_information_dict = {
                                 "bus_routes_id":bus_routes_line_id.m2o_bus_routes_id.id,
                                 "m2o_fleet_vehicle_id":bus_routes_line_id.m2o_fleet_vehicle_id.id,
                                 "m2o_bus_point_pickup_id":bus_routes_line_id.m2o_bus_point_pickup_id.id,
                                 "m2o_bus_point_dropoff_id":bus_routes_line_id.m2o_bus_point_dropoff_id.id,
                                 "journey_date":bus_routes_line_id.journey_date,
                                 "start_time":bus_routes_line_id.m2o_bus_routes_id.start_time,
                                 "end_time":bus_routes_line_id.m2o_bus_routes_id.end_time,
                                 "trip_information_line_ids":seat_list,
                                }
        return trip_information_dict
