# -*- coding: utf-8 -*-
###############################################
# Regulus Berdin / rberdin@gmail.com (c) 2025
###############################################
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import time
import logging

_logger = logging.getLogger(__name__)


class Payroll(models.Model):
    _inherit = "hr.ph.payroll"

    def action_merge_leaves(self):
        self.ensure_one()
        Compensation = self.env['hr.ph.pay.computation']

        for p in self.payslip:

            comp_lines = Compensation.search([
                ('payslip_id','=',p.id),
                ('seq','>=',900),
                ('seq','<',100000),
                ('computed','=',True),
                ('unit','=','day'),
                ('factor','=',1),
            ])
            minutes_leaves = sum([c.qty for c in comp_lines]) * 8.0 * 60.0

            if minutes_leaves:
                absences = Compensation.search([
                    ('payslip_id','=',p.id),
                    ('name','in',['Absent','Undertime']),
                ])

                minutes_absent = 0.0
                for absent in absences:
                    if absent.unit == 'hour':
                        minutes_absent += absent.qty * 60
                    elif absent.unit == 'minute':
                        minutes_absent += absent.qty
                
                absent_remaining = minutes_absent - minutes_leaves
                if absences and absent_remaining > 0.0:
                    Compensation.create({
                        'payslip_id' : p.id,
                        'seq': absences[0].seq,
                        'name': 'Absent',
                        'computed' : True,
                        'factor' : -1,
                        'basic_pay' : True,
                        'taxable' : True,
                        'unit': 'hour',
                        'qty': absent_remaining / 60.0
                    })
                absences.unlink()
                comp_lines.unlink()

                p.recompute_deduction()


    def action_del_lates_undertime_absences(self):
        self.ensure_one()
        Compensation = self.env['hr.ph.pay.computation']
        for p in self.payslip:
            comp_lines = Compensation.search([
                ('payslip_id','=',p.id),
                ('name','in',['Absent','Late','Undertime']),
            ])
            _logger.debug("Payslit: name=%s recs=%s", p.employee_id.name, len(comp_lines))
            if comp_lines:
                for c in comp_lines:
                    _logger.debug("  Remove: %s", c.name)
                comp_lines.unlink()
                p.recompute_deduction()

