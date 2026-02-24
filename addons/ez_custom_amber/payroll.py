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

    #add released state
    state = fields.Selection(selection_add=[('released','Released')], ondelete={'released': 'set default'})


    def action_release(self):
        for rec in self:
            if rec.state == 'done':
                rec.state = 'released'


    @api.depends('state')
    def get_color(self):
        for record in self:
             color = 1
             if record.state == 'done':
                 color = 4
             elif record.state == 'released':
                 color = 5
             record.color = color



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
                    # ('name','in',['Absent']),
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


    def action_del_lates_undertime(self):
        self.ensure_one()
        Compensation = self.env['hr.ph.pay.computation']
        for p in self.payslip:
            comp_lines = Compensation.search([
                ('payslip_id','=',p.id),
                ('name','in',['Late','Undertime']),
            ])
            _logger.debug("Payslip: name=%s recs=%s", p.employee_id.name, len(comp_lines))
            recompute = False
            if comp_lines:
                for c in comp_lines:
                    _logger.debug("  Remove: %s %s", c.name, c.amount)
                comp_lines.unlink()
                recompute = True

            #delete absences that are less than 2 hours (1 day = 8 hours, so 2 hours = 2.0/8.0 of daily rate)
            daily_limit = -(p.daily_rate * 2.0 / 8.0)
            comp_lines = Compensation.search([
                ('payslip_id','=',p.id),
                ('name','=','Absent'),
                ('amount','>',daily_limit),
            ])
            _logger.debug("Payslip absent: name=%s recs=%s", p.employee_id.name, len(comp_lines))
            if comp_lines:
                for c in comp_lines:
                    _logger.debug("  Remove absent: %s amt=%s limit=%s", c.name, c.amount, daily_limit)
                #comp_lines.unlink()
                #recompute = True
                
            if recompute:
                p.recompute_deduction()
# ERROR absent
# Ancheta, Jules Angelo Daniel Peneyra
# Kim, Jinmyung
# Malangen, Russ Earl Micah Balagtas 
