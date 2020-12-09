#!/bin/bash

#rm ${HOME}/.vnc/xstartup

export ConnectionId=$1
export POSTGRES_HOST=$2
export POSTGRES_DB=$3
export POSTGRES_USER=$4
export POSTGRES_PASSWORD="$5"
export passwordDB=${POSTGRES_PASSWORD}
export DEBUG=$6

cd ~
if [ X"$DEBUG" != X"" ]; then
    optDEB="--debug"
fi

echo ipython3 --colors='NoColor' --no-color-info --no-confirm-exit -- /TiledViz/TVConnections/TVConnection.py --host=${POSTGRES_HOST} --login=${POSTGRES_USER}  --databasename=${POSTGRES_DB} --usertest=${POSTGRES_USER} --connectionId=${ConnectionId} $optDEB > ~/.vnc/tvconnection.log
ipython3 --colors='NoColor' --no-color-info --no-confirm-exit -- /TiledViz/TVConnections/TVConnection.py --host=${POSTGRES_HOST} --login=${POSTGRES_USER}  --databasename=${POSTGRES_DB} --usertest=${POSTGRES_USER} --connectionId=${ConnectionId} $optDEB 2>&1 |tee -a ~/.vnc/tvconnection.log
