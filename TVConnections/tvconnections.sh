#!/bin/bash 

#rm ${HOME}/.vnc/xstartup

export ConnectionId=$1
export POSTGRES_HOST=$2
export POSTGRES_PORT=$3
export POSTGRES_DB=$4
export POSTGRES_USER=$5
export POSTGRES_PASSWORD="$6"
export passwordDB=${POSTGRES_PASSWORD}
export DEBUG=$7

cd ~
if [ X"$DEBUG" != X"" ]; then
    optDEB="--debug"
fi

export LAUNCH="ipython3  --no-confirm-exit -- /TiledViz/TVConnections/TVConnection.py --host=${POSTGRES_HOST} --port=${POSTGRES_PORT} --login=${POSTGRES_USER}  --databasename=${POSTGRES_DB} --usertest=${POSTGRES_USER} --connectionId=${ConnectionId} $optDEB"
echo $LAUNCH > ~/.vnc/tvconnection.log
#--colors='NoColor' --no-color-info
script -qefc "$LAUNCH" ~/.vnc/tvconnection.log
#$LAUNCH

