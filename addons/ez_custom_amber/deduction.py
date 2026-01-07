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


class PayslipDeduction(models.Model):
    _inherit = "hr.ph.pay.deduction"

    @api.model
    def compute_hdmf_using_table(self, gross, date, prev_ee=0, prev_er=0):
        #only send on the beginning of month
        if prev_ee > 0.0 or prev_er > 0.0:
            return 0, 0
        return super().compute_hdmf_using_table(gross, date, prev_ee, prev_er)
        

class Phic(models.Model):
    _inherit = "hr.ph.phic"

    @api.model
    def create_phic_line(self, payslip, ptotal):
        code = "PHIC"
        pgross_pay, ptaxable, pbasic_pay, pded = ptotal
        pee = pded.get(code, {}).get("amount", 0.0)
        per = pded.get(code, {}).get("er_amount1", 0.0)

        if pee > 0.0 or per > 0.0:
            return []
        else:
            return super().create_phic_line(payslip, ptotal)


class Sss(models.Model):
    _inherit = "hr.ph.sss"

    @api.model
    def create_sss_line(self, payslip, ptotal):
        # check if second pay
        year_month = payslip.year_month
        ps_recs = self.env["hr.ph.payslip"].search([
            ("employee_id", "=", payslip.employee_id.id),
            ("year_month", "=", year_month),
            ("date_to", "<", payslip.date_from),
            ("id", "!=", payslip.id),
        ])
        _logger.info("create_sss_line_inh: %s", ps_recs)
        if len(ps_recs) >= 1:
            #2nd payslip for the month
            _logger.info("create_sss_line_inh: create SSS")
            return super().create_sss_line(payslip, ptotal)
        else:
            _logger.info("create_sss_line_inh: return null")
            return []


