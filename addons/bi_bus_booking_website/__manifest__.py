                                                                                                                                    # -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
	"name":"Website Bus Reservation System | Bus Ticketing System Portal",
	"version":"18.0.0.0",
	"category":"Website",
	"summary":"Website Bus Booking Front-end Bus Booking Reservation Portal Bus Ticket Reservation Web Store Bus Reservation Software eCommerce Bus Booking Shop Bus Booking Portal Advance Web-shop Ticket Booking Website Transportation Management Ticket Booking Frontend",
	"description":"""
        
        Website Bus Reservation System Odoo App helps users to manage transport business by website. User have to enable bus booking management option to accessing the bus booking from the portal. User can easily searched available buses for selected routes and select the seats as per convenience. User can register the payment for ticket booking and also print bus ticket report in PDF format.
	
    """,
    "author": "BROWSEINFO",
    "price": 120,
    "currency": 'EUR',
    "website" : "https://www.browseinfo.com/demo-request?app=bi_bus_booking_website&version=18&edition=Community",
    "depends":["base",
               "bi_bus_booking_management",
               "website_sale",
              ],
	"data":[
            "data/menu.xml",
            "views/bus_booking_page_view.xml",
            "views/template.xml",
           ],
    "assets": {
        "web.assets_frontend": [
            "bi_bus_booking_website/static/src/js/bus_booking.js",
            "bi_bus_booking_website/static/src/css/bus_booking_seat.css",
        ],
    },
    'license':'OPL-1',
    'installable': True,
    'auto_install': False,
    'live_test_url':'https://www.browseinfo.com/demo-request?app=bi_bus_booking_website&version=18&edition=Communityw',
    "images":['static/description/Website-Bus-Reservation-System-Banner.gif'],
}
