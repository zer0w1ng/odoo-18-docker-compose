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

    # @api.model
    # def create_sss_line(self, payslip, ptotal):
    #     # check if second pay
    #     year_month = payslip.year_month
    #     ps_recs = self.env["hr.ph.payslip"].search([
    #         ("employee_id", "=", payslip.employee_id.id),
    #         ("year_month", "=", year_month),
    #         ("date_to", "<", payslip.date_from),
    #         ("id", "!=", payslip.id),
    #     ])
    #     _logger.info("create_sss_line_inh: %s", ps_recs)
    #     if len(ps_recs) >= 1:
    #         #2nd payslip for the month
    #         _logger.info("create_sss_line_inh: create SSS")
    #         return self.create_sss_line_amber(payslip, ptotal)
    #     else:
    #         _logger.info("create_sss_line_inh: return null")
    #         return []


    # def create_sss_line_amber(self, payslip, ptotal):
    @api.model
    def create_sss_line(self, payslip, ptotal):
        res0 = []
        if payslip.no_deductions:
            return res0

        #get salary base
        sql = """
            SELECT sss_salary_base 
            FROM hr_ph_gov_deductions 
            WHERE (date_from <= %s AND date_to >= %s)
            LIMIT 1
        """
        param = (payslip.payroll_id.date_to, payslip.payroll_id.date_to)
        self.env.cr.execute(sql, param)
        res = self.env.cr.fetchone()
        if not res:
            raise ValidationError(_("Government deductions not set properly."))
        sss_salary_base = res[0]

        code = "SSS"
        pgross_pay, ptaxable, pbasic, pded = ptotal
        pee = pded.get(code, {}).get("amount", 0.0)
        per = pded.get(code, {}).get("er_amount1", 0.0)
        pec = pded.get(code, {}).get("er_amount2", 0.0)

        if sss_salary_base=='gross':
            #sum old_payslips.de_minimus to be deducted
            old_payslips = self.env["hr.ph.payslip"].search([
                ("employee_id", "=", payslip.employee_id.id),
                ("year_month", "=", payslip.year_month),
                ("id", "!=", payslip.id),
                ("date_to", "<", payslip.date_from),
                ("state", "!=", "draft")
            ])

            tdeminimis = payslip.de_minimis
            for p in old_payslips:
                tdeminimis += p.de_minimis

            ee, er, ec = self.compute_sss_using_table(
                payslip.gross_pay + pgross_pay - tdeminimis,
                payslip.payroll_id.date_to)
        else:
            ee, er, ec = self.compute_sss_using_table(
                payslip.basic_pay + pbasic,
                payslip.payroll_id.date_to)

        _logger.info("create_sss_line_amber: ee=%s er=%s ec=%s\npee=%s per=%s pec=%s", ee, er, ec, pee, per, pec)

        val1 = {
            'seq': 10,
            'name': 'SSS Premium',
            'amount': max(0.0, round(ee - pee, 2)),
            'er_amount1': max(0.0, round(er - per, 2)),
            'er_amount2': max(0.0, round(ec - pec, 2)),
            'code': code,
            'computed': True,
            'tax_deductible': True,
            'payslip_id': payslip.id,
        }

        if val1["amount"] > 0.0 or val1["er_amount1"] > 0.0 or val1["er_amount2"] > 0.0:
            #payslip.deduction_line.create(val1)
            res0.append(val1)

        return res0


