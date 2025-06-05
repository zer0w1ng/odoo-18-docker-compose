#!/bin/bash

update_db() {
    CONFIG="/etc/odoo/odoo.conf"
    CMD_OPT="odoo --stop-after-init --update $MODULES -p 9069 -d $DB -c $CONFIG" 
    echo "Update Database db=$DB modules=$MODULES"
    echo $CMD_OPT
    docker-compose exec app bash -c "$CMD_OPT"
    echo
}

echo "Updating modules..."

REMOTE=1
RESTART=0

if (($REMOTE != 0)); then
    echo REMOTE
    # #############################################################
    DB="test2"
    # MODULES="ez_hr"
    # MODULES="ez_hr_namesplit"
    # MODULES="ez_payroll"
    # MODULES="ez_payroll_alphalist"
    # MODULES="ez_payroll_coe"
    # MODULES="ez_payroll_ot_report"
    # MODULES="ez_timekeeping,ez_timekeeping_rotshift"
    # MODULES="ez_timekeeping,ez_timekeeping_request"
    # MODULES="ez_hr"
    # MODULES="ez_hr,ez_hr_namesplit,ez_payroll"
    # MODULES="ez_payroll,ez_payroll_salary_increase"
    # MODULES="ez_payroll,ez_payroll_timekeeping"
    # MODULES="ez_hr_esignature"
    # MODULES="ez_payroll_ess,ez_hr_esignature"
    MODULES="ez_custom_holiday"
    # MODULES="ez_custom_payslip"
    update_db
else
    echo LOCAL
    DB=$1
    MODULES=$2
    update_db
fi

if (($RESTART != 0)); then
    docker-compose restart app
fi

#echo
echo "done."


