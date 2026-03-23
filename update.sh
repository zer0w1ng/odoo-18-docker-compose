#!/bin/bash

update_db() {
    CONFIG="/etc/odoo/odoo.conf"
    CMD_OPT="odoo --stop-after-init --update $MODULES -p 19069 -d $DB -c $CONFIG" 
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
<<<<<<< HEAD
    DB="demo-pay2"
    # MODULES="hr_dashboard"
    MODULES="ez_timekeeping,ez_timekeeping_payroll"
=======
    # DB="demo18"
    # MODULES="hr_dashboard"
    # MODULES="heldesk_mgmt_extend"

    #DB="parkingbees"
    #MODULES="parkingbees"

    DB="westmead"
    MODULES="ez_custom_westmead"

>>>>>>> fd1e41417cfb6e9c55665f36f62276ba9c78e5b9

    #MODULES="ez_payroll_manager"
    # MODULES="account_ph_2306_2307"
    # MODULES="account_ph_bir_map"

    # DB="dhl"
    # MODULES="ez_custom_dhl"

    # DB="test2"

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
    # MODULES="ez_custom_holiday"
    # MODULES="ez_custom_payslip"
    # MODULES="ez_payroll_ot_request"

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


