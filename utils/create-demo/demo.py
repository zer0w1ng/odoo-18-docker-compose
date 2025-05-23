from __future__ import print_function
#from odoo_connection import OdooConnection
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pprint import pprint
import odoorpc
import math
import random
import csv
#import random_names
import os, time 
#from multiprocess import multi_load, chunks, MultiProcess, lprint
#from odoo_utils import *

def create_demo_attendance(odoo):
    model = odoo.env["hr.attendance"]
    res = model.create_demo_data()
    print(res)


def create_demo_timekeeping(odoo):
    model = odoo.env["ez.shift"]
    header = ['id', 'name', 'default_schedule', 'auto_auth']
    data = [
        [
            '__demo__.day_shift',
            'Day Shift',
            '08:00-11:30 12:30-17:00',
            '1',
        ]
    ]
    res = model.load(header, data)
    shift_id = model.search([('name','=','Day Shift')])
    rec = model.browse(shift_id)
    rec.create_details()
    print("Shift:", res)

    model = odoo.env["hr.employee"]
    ids = model.search([])
    print(ids)
    res = model.write(ids, {'shift_id': shift_id[0]})
    print(res)

    Employee = odoo.env['hr.employee']
    TimeCard = odoo.env["ez.time.card"]

    #delete all timecard
    ids = TimeCard.search([])
    TimeCard.write(ids, {'state': 'draft'})
    TimeCard.unlink(ids)
    print("Timecard Deleted:", ids)

    date_end = datetime.strptime("2025-05-01","%Y-%m-%d")
    months = 24
    d1 = date_end.replace(day=1) - relativedelta(months=months)

    employee_ids = Employee.browse(Employee.search([]))

    d2 = d1 + relativedelta(months=months, days=-1)
    new_recs = []
    for e in employee_ids:
        dd1 = d1

        employee_name = e.name
        employee_id = e.id
        shift = e.shift_id
        shift_id = shift.id
        shift_name = shift.name
        auto_auth = shift.auto_auth
        flex_time = shift.flex_time
        minimum_ot_minutes = shift.minimum_ot_minutes
        late_allowance_minutes = shift.late_allowance_minutes

        while dd1<=d2 and shift_id:
            print("DEMO:", employee_name, shift_name)
            val1 = {
                'employee_id': employee_id,
                'date1' : dd1.strftime('%Y-%m-%d'),
                'date2' : (dd1 + relativedelta(days=14)).strftime('%Y-%m-%d'),
                'note' : 'Demo Time Card1',
                'state' : 'draft',
                'shift_id' : shift_id,
                'auto_auth' : auto_auth,
                'flex_time' : flex_time,
                'minimum_ot_minutes' : minimum_ot_minutes,
                'late_allowance_minutes' : late_allowance_minutes,
            }

            val2 = {
                'employee_id': employee_id,
                'date1' : (dd1 + relativedelta(days=15)).strftime('%Y-%m-%d'),
                'date2' : (dd1 + relativedelta(months=1,days=-1)).strftime('%Y-%m-%d'),
                'note' : 'Demo Time Card2',
                'state' : 'draft',
                'shift_id' : shift_id,
                'auto_auth' : auto_auth,
                'flex_time' : flex_time,
                'minimum_ot_minutes' : minimum_ot_minutes,
                'late_allowance_minutes' : late_allowance_minutes,
            }

            new_recs.append(val1)
            new_recs.append(val2)
            dd1 += relativedelta(months=1)

    pprint(new_recs)

    ids = []
    for rec in new_recs:
        id = TimeCard.create(rec)
        ids.append(id)
        print(" create tc: ", id, pprint.pformat(rec))

    TimeCard.gen_default_lines(ids)
    print(" gen_default_lines: ", ids)
    TimeCard.fill_from_attendance(ids, summarized=False)
    print(" fill_from_attendance: ", ids)
    TimeCard.approve_record(ids)
    print(" approve_record: ", ids)


def create_demo_payroll_rate(odoo):
    # date_start = datetime.strptime("2022-08-01","%Y-%m-%d")
    # date_end = datetime.strptime("2024-05-16","%Y-%m-%d")
    Rates = odoo.env["ez.employee.salary.rate"]
    ids = Rates.search([])
    Rates.unlink(ids)

    date_start = datetime.strptime("2023-04-01","%Y-%m-%d")
    date_end = datetime.strptime("2025-04-30","%Y-%m-%d")

    # create increasing salary rate every 3 months
    employees = odoo.env["hr.employee"].search_read([], ['salary_rate', 'name'])
    d0 = date_start
    i = 1
    while d0 < date_end:
        print(d0)
        for employee in employees:
            if employee['salary_rate'] <= 0.0:
                employee['salary_rate'] = random.randrange(1000000,5000000) / 100.0

            rnd = random.randrange(-20, 20)
            dd0 = d0 + relativedelta(days=rnd) 
            val = {
                'employee_id': employee['id'],
                'date' : dd0.strftime('%Y-%m-%d'),
                'salary_rate' : employee['salary_rate'] * i,
            }
            print(employee["name"], rnd, val)
            odoo.env["ez.employee.salary.rate"].create(val)
        
        i *= 1.1
        d0 += relativedelta(months=3)


def create_demo_payroll(odoo):
    model = odoo.env["hr.ph.payroll"]
    date_start = datetime.strptime("2023-04-01","%Y-%m-%d")
    date_end = datetime.strptime("2025-04-30","%Y-%m-%d")

    #delete all payroll
    ids = model.search([])
    model.write(ids, {'state': 'draft'})
    model.unlink(ids)

    d0 = date_start
    while d0 < date_end:
        dd0 = d0.strftime("%Y-%m-%d")
        dd1 = (d0 + relativedelta(days=14)).strftime("%Y-%m-%d")
        name = d0.strftime("Payroll %B %Y A")
        print("Create Payroll:", name, dd0, dd1)
        res = model.create_demo_data(name, dd0, dd1, True)

        dd0 = (d0 + relativedelta(days=15)).strftime("%Y-%m-%d")
        dd1 = (d0 + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")
        name = d0.strftime("Payroll %B %Y B")
        print("Create Payroll:", name, dd0, dd1)
        res = model.create_demo_data(name, dd0, dd1, True)

        d0 += relativedelta(months=1)


def delete_demo_payroll(odoo):
    model = odoo.env["hr.ph.payroll"]
    ids = model.search([])
    print("Delete Payroll:", ids)
    res = model.write(ids, {'state': 'draft'})
    print("Set to draft:", res)
    res = model.unlink(ids)
    print("Delete", res)
    print()

    if 1:
        model = odoo.env["ez.employee.salary.rate"]
        ids = model.search([])
        print("Delete Rate:", ids)
        res = model.unlink(ids)
        print("Delete", res)


if __name__ == "__main__":

    # dbname = "zer0w1ng-test-upgrade17-stage-20678451"
    # host = "zer0w1ng-test-upgrade17-stage-20678451.dev.odoo.com"
    # port = 443
    # protocol = 'jsonrpc+ssl'
    # user = 'admin'
    # admin_pwd = "70f50d3e76b422ef25d8ae29ddacd9b5f28620ba"

    dbname = "zer0w1ng-test-upgrade17-prod-20678384"
    host = "zer0w1ng-test-upgrade17-prod-20678384.dev.odoo.com"
    port = 443
    protocol = 'jsonrpc+ssl'
    user = 'admin'
    admin_pwd = "12345"

    super_password = "x"

    odoo = odoorpc.ODOO(
        host,
        port=port,
        protocol=protocol,
        # protocol='jsonrpc+ssl'
        # protocol='jsonrpc'
    )

    print("Connect", host)
    odoo.login(dbname, user, admin_pwd)
    # print(odoo)

    # conn = OdooConnection(host, port, admin_pwd, super_password)
    # odoo = conn.get_session(dbname)

    if 0:
        #                               hired
        hired = '2022'
        res = odoo.env['hr.employee'].demo_create_employee(hired)
        pprint(res)

    if 0:
        create_demo_attendance(odoo)

    if 0:
        create_demo_timekeeping(odoo)

    if 0:
        create_demo_payroll_rate(odoo)

    if 1:
        create_demo_payroll(odoo)

