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
    #MODULES="all"
    # DB="pitx"
    # MODULES="ez_custom_pitx"

    DB="dhl"
    MODULES="ez_custom_dhl"
 
    update_db
fi

if (($RESTART != 0)); then
    docker-compose restart app
fi

#echo
echo "done."


