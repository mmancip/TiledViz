#!/bin/bash

#rm ${HOME}/.vnc/xstartup

export ConnectionId=$1
export POSTGRES_HOST=$2
export POSTGRES_DB=$3
export POSTGRES_USER=$4
export POSTGRES_PASSWORD="$5"
export passwordDB=${POSTGRES_PASSWORD}

cd ~
echo python3 /TiledViz/TVConnections/TVConnection.py --host=${POSTGRES_HOST} --login=${POSTGRES_USER}  --databasename=${POSTGRES_DB} --usertest=${POSTGRES_USER} --connectionId=${ConnectionId} > ~/tvconnection.log
python3 /TiledViz/TVConnections/TVConnection.py --host=${POSTGRES_HOST} --login=${POSTGRES_USER}  --databasename=${POSTGRES_DB} --usertest=${POSTGRES_USER} --connectionId=${ConnectionId} 2>&1 |tee -a ~/tvconnection.log
