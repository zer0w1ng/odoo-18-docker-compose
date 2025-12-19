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


class PayslipInherit(models.Model):
    _inherit = "hr.ph.payslip"

    @api.model
    def get_timecard_compensation_lines(self):
        # unlink timekeeping 
        return []


    @api.model
    def get_compensation_lines(self):
        res = super().get_compensation_lines()

        # delete Leave
        for r in res:
            if r['computed'] and r['seq']>=900 and r['seq']<2000:
                r['qty'] = 0.0
        
        return [r for r in res if (r.get('computed') and r.get('qty') > 0.0)]
        #return res
