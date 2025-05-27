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
#from multiprocess import multi_load, chunks, MultiProcess, lprint
#from odoo_utils import *

import requests, base64
from PIL import Image
from io import BytesIO


def create_demo_timekeeping(odoo, setting):
    if not setting['create_timekeeping']:
        return

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

    months = setting["months"]
    date_end = datetime.today() \
        .replace(day=1, hour=0, minute=0, second=0, microsecond=0) 
    d1 = date_end.replace(day=1) - relativedelta(months=months)
    d2 = d1 + relativedelta(months=months, days=-1)

    employee_ids = Employee.browse(Employee.search([]))
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
        print(" create tc: ", id, pformat(rec))

    TimeCard.gen_default_lines(ids)
    print(" gen_default_lines: ", ids)
    TimeCard.fill_from_attendance(ids, summarized=False)
    print(" fill_from_attendance: ", ids)
    TimeCard.approve_record(ids)
    print(" approve_record: ", ids)


def create_demo_payroll_rate(odoo, setting):
    if not setting['create_payroll_rate']:
        return

    # date_start = datetime.strptime("2022-08-01","%Y-%m-%d")
    # date_end = datetime.strptime("2024-05-16","%Y-%m-%d")
    Rates = odoo.env["ez.employee.salary.rate"]
    ids = Rates.search([])
    Rates.unlink(ids)

    months = setting["months"]
    date_end = datetime.today() \
        .replace(day=1, hour=0, minute=0, second=0, microsecond=0) \
        - relativedelta(days=30)
    date_start = date_end.replace(day=1) - relativedelta(months=months+1)

    # date_start = datetime.strptime("2023-04-01","%Y-%m-%d")
    # date_end = datetime.strptime("2025-04-30","%Y-%m-%d")

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


def create_demo_payroll(odoo, setting):
    if not setting['create_payroll']:
        return

    model = odoo.env["hr.ph.payroll"]
    months = setting["months"]
    date_end = datetime.today() \
        .replace(day=1, hour=0, minute=0, second=0, microsecond=0) \
        - relativedelta(days=1)
    date_start = date_end.replace(day=1) - relativedelta(months=months)

    # date_start = datetime.strptime("2023-04-01","%Y-%m-%d")
    # date_end = datetime.strptime("2025-04-30","%Y-%m-%d")

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

    if 0:
        model = odoo.env["ez.employee.salary.rate"]
        ids = model.search([])
        print("Delete Rate:", ids)
        res = model.unlink(ids)
        print("Delete", res)

def get_odoo_connection(settings):
    odoo = odoorpc.ODOO(
        settings['host'],
        port=settings['port'],
        protocol=settings['protocol'],
    )
    odoo.login(settings['dbname'], settings['user'], settings['admin_pwd'])
    return odoo

####################################################

def create_demo_employees(odoo, setting):
    if setting['create_employees']:
        Employee = odoo.env['hr.employee']
        res = Employee.demo_create_employee(setting['hired'])
        admin_id = Employee.search([('name', '=', 'Administrator')], limit=1)
        if admin_id:
            Employee.write(admin_id, {
                'last_name': 'Doe',
                'first_name': 'Johnny Admin',
                'middle_name': 'Cruz',
            })
        ids = Employee.search([])
        Employee.write(ids, {
            'tz': 'Asia/Manila',
        })
        print(f"Create employees: {pformat(res)}")


def create_demo_attendance(odoo, setting):
    if setting['create_attendance']:
        Attendance = odoo.env["hr.attendance"]
        Employee = odoo.env['hr.employee']

        #delete all attendance
        ids = Attendance.search([])
        Attendance.unlink(ids)

        months = setting['months']
        d1 = datetime.today() \
            .replace(day=1, hour=0, minute=0, second=0, microsecond=0) \
            - relativedelta(months=months)
        d2 = d1 + relativedelta(months=months+1)
        sd1 = d1.strftime('%Y-%m-%d')
        sd2 = d2.strftime('%Y-%m-%d')
        print("Create Attendance from", sd1, "to", sd2)

        employee_ids = Employee.search_read([], ['id', 'name'])
        TIMEZONE_ADJUSTMENT = relativedelta(hours=8)

        header = [
            'id', 'employee_id', 'check_in', 'check_out',
        ]

        i = 0
        while d1<=d2:
            data = []
            for e in employee_ids:
                id = f"__import__.attendance_line_{d1.strftime('%Y%m%d')}_{i}"
                i += 1

                chance = 1
                if d1.weekday()==6:
                    #1 day of a month will work on a day-off
                    chance = random.randrange(1, 31)

                if chance==1:
                    dd1 = datetime.combine(d1, datetime.min.time()).replace(hour=8, minute=0)
                    #dd1 -= TIMEZONE_ADJUSTMENT
                    dd2 = dd1 + relativedelta(hours=9)

                    #with late
                    late = random.randrange(1, 6)
                    if late==1:
                        dd1 += relativedelta(minutes=random.randrange(1, 20))

                    #with ot
                    ot = random.randrange(1, 6)
                    if ot==1:
                        dd2 += relativedelta(minutes=random.randrange(10, 120))

                data.append([
                    id,
                    e['name'],
                    f"{dd1}",
                    f"{dd2}",
                ])

            d1 += relativedelta(days=1)

            print()
            print(header)
            for d in data:
                pprint(d)
            res = Attendance.load(header, data)
            pprint(res)


def create_deduction_entry(odoo, date, name):
    Deduction = odoo.env['hr.ph.pay.deduction.entry']
    Employee = odoo.env['hr.employee']
    DeductionLine = odoo.env['hr.ph.pay.deduction.entry.details']
     
    res = Deduction.search([('name','=',name)])
    if res:
        print('Already create deduction:', name)
        return False
    
    print('Creating deduction:', name)

    ded_id = Deduction.create({
        'name': name,
        'date': date,
        'state': 'done',
    })

    emp_ids = Employee.search([])
    seq = 0
    for emp_id in emp_ids:
        seq += 10
        DeductionLine.create({
            'other_deduction_id': ded_id,
            'seq': seq,
            'employee_id': emp_id,
            'amount': 2000.0 * random.random(),
        })



def create_demo_others(odoo, setting):
    if not setting['create_others']:
        return

    today = datetime.today()
    start = today - relativedelta(months=1)

    Loan = odoo.env['hr.ph.loan']
    Loan.create_demo_data((start-relativedelta(months=2)).strftime("%Y-%m-%d"), "A001")
    Loan.create_demo_data((start-relativedelta(months=2)).strftime("%Y-%m-%d"), "A002")

    Compensation = odoo.env['ez.work.summary.sheet']
    Compensation.create_demo_data(start.strftime('Adjustments %b %Y'), start.strftime('%Y-%m-1'), False)

    create_deduction_entry(odoo, start.strftime('%Y-%m-02'), start.strftime('Canteen %b %Y A'))
    create_deduction_entry(odoo, start.strftime('%Y-%m-02'), start.strftime('Union Dues %b %Y A'))
    create_deduction_entry(odoo, start.strftime('%Y-%m-18'), start.strftime('Canteen %b %Y B'))
    create_deduction_entry(odoo, start.strftime('%Y-%m-18'), start.strftime('Union Dues %b %Y B'))


def create_demo_employee_images(odoo, setting):
    if setting['create_employee_images']:

        #create picturs
        def _get_random_image():
            url = "https://100k-faces.glitch.me/random-image"
            response = requests.get(url)
            image_bytes = BytesIO(response.content)
            image_1920 = base64.b64encode(image_bytes.getvalue()).decode("utf-8")
            #print(type(image_1920), len(image_1920))
            return image_1920
            
        Employee = odoo.env['hr.employee']
        employee_ids = Employee.search([])

        for emp_id in employee_ids:
            image_1920 = _get_random_image()
            res = Employee.write(emp_id, {
                'image_1920': image_1920,
            })
            print(res)



SETTINGS = {
    'kinsenas-demo18': {
        'dbname': "zer0w1ng-ez-addons-prod-20714000",
        'host': "kinsenas-demo18.odoo.com",
        'port': 443,
        'protocol': 'jsonrpc+ssl',
        'user': 'admin',
        'admin_pwd': "12345",
        'hired': '2022',
        'months': 24,

        'create_employees': 0,
        'create_attendance': 0,
        'create_timekeeping': 0,
        'create_payroll_rate': 0,
        'create_others': 0,
        'create_payroll': 0,
        'create_employee_images': 0,
    },
}

if __name__ == "__main__":
    setting = SETTINGS['kinsenas-demo18']
    odoo = get_odoo_connection(setting)

    create_demo_employees(odoo, setting)
    create_demo_attendance(odoo, setting)
    create_demo_timekeeping(odoo, setting)
    create_demo_payroll_rate(odoo, setting)
    create_demo_others(odoo, setting)
    create_demo_payroll(odoo, setting)

    create_demo_employee_images(odoo, setting)
