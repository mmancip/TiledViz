#!/bin/bash

# official way to provide password to psql:  http://www.postgresql.org/docs/9.3/static/libpq-envars.html
if [ ! -v POSTGRES_PASSWORD ]; then
   echo "POSTGRES_PASSWORD must have been sets."
   exit 1
fi
if [ ! -v POSTGRES_HOST ]; then
   echo "POSTGRES_HOST must have been sets."
   exit 1
fi
if [ ! -v POSTGRES_USER ]; then
   echo "POSTGRES_USER must have been sets."
   exit 1
fi
if [ ! -v POSTGRES_DB ]; then
   echo "POSTGRES_DB must have been sets."
   exit 1
fi


export PGPASSWORD=$POSTGRES_PASSWORD

export passwordDB="$POSTGRES_PASSWORD"

python3 TVConnections/create_HPC.py  --sessionNAME='testSESSION' --host=${POSTGRES_HOST} --login=${POSTGRES_USER}  --databasename=${POSTGRES_DB}
RET=$?
if [ $RET -gt 0 ]; then
    exit $RET
fi
echo "create HPC container chain done."
echo

