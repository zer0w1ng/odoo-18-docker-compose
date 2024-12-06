# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
import pytz
from datetime import datetime
from odoo.addons.website_sale.controllers.main import WebsiteSale

class BusBookingWebsiteSale(WebsiteSale):

    @http.route(['/shop/payment'], type='http', auth="public", website=True, sitemap=False)
    def shop_payment(self, **post):
        res = super(BusBookingWebsiteSale, self).shop_payment()

        order = request.website.sale_get_order()
        for line in order.order_line:
            if line.bus_routes_line_id and line.order_id.is_bus_order:
                line.price_unit = line.bus_routes_line_id.price
        return res

class BusBooking(http.Controller):

    @http.route('/bus_booking', type='http', auth='public', website=True, sitemap=False)
    def bus_booking_page(self, **kw):
        bus_dict = {}
        bus_point_obj = request.env["bus.point"].sudo()
        bus_types_obj = request.env["bus.types"].sudo()
        bus_point_ids = bus_point_obj.search([])
        bus_types_ids = bus_types_obj.search([])
        if bus_point_ids and bus_types_ids:
            bus_dict.update({
                            "start_point_ids":bus_point_ids,
                            "end_point_ids":bus_point_ids,
                            "bus_types_ids":bus_types_ids,
                           })
        return http.request.render('bi_bus_booking_website.bus_booking_website_page', bus_dict)

    @http.route(['/search_bus'], type='json', auth="public", 
                                methods=['POST'], website=True, csrf=False)
    def search_bus(self, start_point, end_point, bus_journey_date_id, bus_types):
        bus_routes_line_ids = False
        routes_line_list = []
        trip_information_line_obj = request.env["trip.information.line"].sudo()
        if start_point and end_point and bus_journey_date_id and bus_types:
            bus_routes_line_obj = request.env["bus.routes.line"].sudo()
            domain = [
                        ("m2o_bus_point_pickup_id", "=", int(start_point)),
                        ("m2o_bus_point_dropoff_id", "=", int(end_point)),
                        ("journey_date", "=",bus_journey_date_id),
                        ("m2o_bus_types_id", "=", int(bus_types)),
            ]
            bus_routes_line_ids = bus_routes_line_obj.search(domain)
            if bus_routes_line_ids:
                total_seats = 0
                remaining_seat = 0
                for bus_routes_line_id in bus_routes_line_ids:
                    trip_information_line = trip_information_line_obj.search([("trip_information_id.journey_date", "=", bus_routes_line_id.journey_date),
                                          ("trip_information_id.m2o_fleet_vehicle_id", "=", bus_routes_line_id.m2o_fleet_vehicle_id.id)])
                    if trip_information_line:
                        total_seats = trip_information_line[0].trip_information_id.total_seat
                        remaining_seat = trip_information_line[0].trip_information_id.remaining_seat
                    else:
                        total_row = bus_routes_line_id.m2o_bus_types_id.total_row
                        total_seat_in_single_row = bus_routes_line_id.m2o_bus_types_id.total_seat_in_single_row
                        total_seats = (total_row * total_seat_in_single_row)
                        remaining_seat = (total_row * total_seat_in_single_row)
                    routes_line_list.append({
                                             "routes_line":bus_routes_line_id.id,
                                             "route":bus_routes_line_id.m2o_bus_routes_id.name,
                                             "m2o_fleet_vehicle_id":bus_routes_line_id.m2o_fleet_vehicle_id.name,
                                             "m2o_bus_point_pickup_id":bus_routes_line_id.m2o_bus_point_pickup_id.name,
                                             "m2o_bus_point_dropoff_id":bus_routes_line_id.m2o_bus_point_dropoff_id.name,
                                             "m2o_bus_types_id":bus_routes_line_id.m2o_bus_types_id.name,
                                             "date":bus_routes_line_id.journey_date,
                                             "total_seats":total_seats,
                                             "remaining_seat":remaining_seat,
                                             "start_time":self.get_local_date_time(bus_routes_line_id.start_time),
                                             "end_time":self.get_local_date_time(bus_routes_line_id.end_time),
                                           })
                return routes_line_list

    def get_local_date_time(self, current_date_time):
        user_tz = request.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        if datetime:
            current_date = datetime.strptime(str(current_date_time), "%Y-%m-%d %H:%M:%S")
            current_date_local = datetime.strftime(pytz.utc.localize(datetime.strptime(str(current_date_time),'%Y-%m-%d %H:%M:%S')).astimezone(local),'%Y-%m-%d %H:%M:%S')
            current_date_local = datetime.strptime(current_date_local,'%Y-%m-%d %H:%M:%S')
            return current_date_local

    @http.route(['/bus_booking_confirm/<int:route_line_id>'], type='http', auth="public", 
                                methods=['POST','GET'], website=True, csrf=False, sitemap=False)
    def bus_booking_confirm_website(self,route_line_id, **kwargs):
        if route_line_id:
            bus_routes_line_obj = request.env["bus.routes.line"].sudo()
            trip_information_line_obj = request.env["trip.information.line"].sudo()
            bus_routes_line_id = bus_routes_line_obj.browse(int(route_line_id))
            if bus_routes_line_id and bus_routes_line_id.m2o_fleet_vehicle_id:
                trip_information_line = trip_information_line_obj.search([("trip_information_id.journey_date", "=", bus_routes_line_id.journey_date),
                                          ("trip_information_id.m2o_fleet_vehicle_id", "=", bus_routes_line_id.m2o_fleet_vehicle_id.id)])
                seat_list = []
                if trip_information_line:
                    for trip_information in trip_information_line:
                        if trip_information.is_booked:
                            seat_list.append(int(trip_information.seat_number))
                return http.request.render('bi_bus_booking_website.bus_booking_website_page_1', {
                                            "bus_routes_line_id":bus_routes_line_id.id,
                                            "price":bus_routes_line_id.price,
                                            "bus_type":bus_routes_line_id.m2o_fleet_vehicle_id.m2o_bus_types_id.bus_type,
                                            "booked_seat":seat_list,
                                            "pick_up_drop_off_points_1":bus_routes_line_id.m2o_bus_point_pickup_id.m2m_pickup_dropoff_points_ids,
                                            "pick_up_drop_off_points_2":bus_routes_line_id.m2o_bus_point_dropoff_id.m2m_pickup_dropoff_points_ids,
                                            "m2m_bus_amenities_ids":bus_routes_line_id.m2o_fleet_vehicle_id.m2m_bus_amenities_ids,
                                            "total_row":bus_routes_line_id.m2o_fleet_vehicle_id.m2o_bus_types_id.total_row,
                                            "total_seat_in_single_row":bus_routes_line_id.m2o_fleet_vehicle_id.m2o_bus_types_id.total_seat_in_single_row,

                })

    @http.route(['/bus_detail'], type='http', auth="public", 
                                methods=['POST','GET'], website=True, csrf=False, sitemap=False)
    def bus_booking_button_checkout(self, **kwargs):
        record_list = []
        order_line_list = []
        order_line_dict = {}
        order_dict = {}
        bus_routes_line_obj = request.env["bus.routes.line"].sudo()
        pickup_dropoff_points_obj = request.env["pickup.dropoff.points"].sudo()
        trip_information_obj = request.env["trip.information"].sudo()
        trip_information_line_obj = request.env["trip.information.line"].sudo()

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
                name = "\n Seat No:- %s \
                        \n Customer Name:- %s \
                        \n Email:- %s \
                        \n Age:- %s \
                        \n Gender:- %s \
                        \n Number:- %s"% (record_list[count+1], record_list[count+2], record_list[count+3], record_list[count+4], record_list[count+5], record_list[count+6])

                order_line_dict = (0,0,{
                                "product_id":request.env.ref('bi_bus_booking_management.bus_ticket_product').id,
                                "name":name,
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
            request.session['sale_order_id'] = sale_order.id
            return request.redirect('/shop/cart')

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
