
from __future__ import print_function
#from odoo_connection import OdooConnection
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pprint import pprint, pformat
import odoorpc
import math
import random
import csv
#import random_names
import os, time 


def get_odoo_connection(settings):
    odoo = odoorpc.ODOO(
        settings['host'],
        port=settings['port'],
        protocol=settings['protocol'],
    )
    odoo.login(settings['dbname'], settings['user'], settings['admin_pwd'])
    return odoo


SETTINGS = {
    'kinsenas-demo18': {
        'dbname': "zer0w1ng-ez-addons-prod-20714000",
        'host': "kinsenas-demo18.odoo.com",
        'port': 443,
        'protocol': 'jsonrpc+ssl',
        'user': 'admin',
        'admin_pwd': "12345",
    },

    'jetserv-staging': {
        'dbname': "zer0w1ng-jetserv-stage4-20877998",
        'host': "zer0w1ng-jetserv-stage4-20877998.dev.odoo.com",
        'port': 443,
        'protocol': 'jsonrpc+ssl',
        'user': 'evillareal@jetsitransport.com',
        'admin_pwd': "12345",
    },

}


if __name__ == "__main__":
    setting_kinsenas = SETTINGS['kinsenas-demo18']
    setting_jetserv = SETTINGS['jetserv-staging']
    odoo_jetserv = get_odoo_connection(setting_jetserv)
    odoo_kinsenas = get_odoo_connection(setting_kinsenas)

    kres_menu = odoo_kinsenas.env['ir.ui.menu'].search_read([
            ('parent_id', '=', False),
        ], [
            'name', 
            'web_icon', 
            #'web_icon_data',
        ])
    kmenu = {}
    for r in kres_menu:
        kmenu[r['name']] = r

    jres_menu = odoo_jetserv.env['ir.ui.menu'].search_read([
            ('parent_id', '=', False),
        ], [
            'name', 
            'web_icon', 
            #'web_icon_data',
        ])
    #pprint(kres_menu)
    #pprint(jres_menu)
    
    if 1:
        Menu = odoo_jetserv.env['ir.ui.menu']
        for j in jres_menu:
            # TODO - update accounting first
            menu = kmenu[j['name']]
            print(j['id'], j['name'], j['web_icon'], menu)
            Menu.write(j['id'], {
                'web_icon': menu['web_icon'],
                'web_icon_data': False,
            })


    #pprint(kmenu)