
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
    'quest-staging': {
        'dbname': "quest-dental-stage2-20995329",
        'host': "quest-dental-stage2-20995329.dev.odoo.com",
        'port': 443,
        'protocol': 'jsonrpc+ssl',
        'user': 'qdmcit@questdental.com.ph',
        'admin_pwd': "5adf5704705b0d7401c08f99b61df590cf81e0c7",
    },
    'quest-prod': {
        'dbname': "quest-dental-prod-19092293",
        'host': "quest-dental.odoo.com",
        'port': 443,
        'protocol': 'jsonrpc+ssl',
        'user': 'qdmcit@questdental.com.ph',
        'admin_pwd': "5adf5704705b0d7401c08f99b61df590cf81e0c7",
    },
}


if __name__ == "__main__":
    # setting = SETTINGS['quest-staging']
    setting = SETTINGS['quest-prod']
    odoo = get_odoo_connection(setting)
    Shift = odoo.env['ez.shift']

    ids = Shift.search([])
    pprint(setting)
    print(ids)

    if 0:
        Shift.write(ids, {
            'rounding_regular_work_minutes': 30,
            'rounding_ot_minutes': 30,
            'early_overtime': True,
        })
