# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
	"name":"Bus Booking Management",
	"version":"18.0.0.0",
	"category":"Sales",
	"summary":"Bus Ticketing System Bus Booking Software Bus Ticket Reservation Bus Reservation Software Bus Booking Application Bus Booking System Bus Ticket Reservation System Advance Ticket Booking Management Transportation Management System Ticket Booking Back-end",
	"description":"""
        
        Bus Booking Management Odoo App helps users to manage transport business by bus booking. User have to enable bus booking management option to accessing the bus booking. User can configure buses with types as seating and sleeper then add pick up and drop off points and amenities of the bus. User can easily searched available buses for selected routes and select the seats as per convenience. User can register the payment for ticket booking and also print bus ticket report in PDF format.
	
    """,
    "author": "BROWSEINFO",
    "price": 69,
    "currency": 'EUR',
    "website" : "https://www.browseinfo.com/demo-request?app=bi_bus_booking_management&version=17&edition=Community",
    "depends":["base",
               "fleet",
               "sale_management",
               'web',
               'website',
              
               
              ],
	"data":[
            "security/bi_bus_booking_management_security.xml",
            "security/ir.model.access.csv",
            "data/product_data.xml",
            "views/template.xml",
            "views/fleet_vehicle_view.xml",
            "wizard/bus_booking_view.xml",
            "views/bus_routes_view.xml",
            "views/bus_types_view.xml",
            "views/bus_brand_view.xml",
            "views/pickup_dropoff_points_view.xml",
            "views/bus_point_view.xml",
            "views/bus_amenities_view.xml",
            "views/bus_routes_line_view.xml",
            "views/trip_information_view.xml",
            "wizard/bus_book_seat_views.xml",
            "views/sale_order_view.xml",
            "report/ticket_report_action.xml",
            "report/ticket_report_template.xml",
            "data/mail_data.xml",
           ],

    "assets":  {
        "web.assets_backend": [
            "bi_bus_booking_management/static/src/js/bus_book_seat_form_controller.js",
            "bi_bus_booking_management/static/src/js/bus_book_seat_view.js",
            "bi_bus_booking_management/static/src/js/select_bus_seat.js",
            "bi_bus_booking_management/static/src/css/bus_booking_seat.css",
        ],
    },
    'license':'OPL-1',
    'installable': True,
    'auto_install': False,
    'live_test_url':'https://www.browseinfo.com/demo-request?app=bi_bus_booking_management&version=17&edition=Community',
    "images":['static/description/Bus-Booking-Management-Banner.gif'],
}

