#!/bin/bash

# official way to provide password to psql:  http://www.postgresql.org/docs/9.3/static/libpq-envars.html
if [ ! -v POSTGRES_PASSWORD ]; then
   echo "POSTGRES_PASSWORD must have been sets."
   exit 1
fi
if [ ! -v POSTGRES_PORT ]; then
   echo "POSTGRES_PORT must have been sets."
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
echo psql -h "${POSTGRES_HOST}" -p ${POSTGRES_PORT} -U "$POSTGRES_USER" -d "$POSTGRES_DB"  -f TVDatabase/TiledViz.sql
psql -h "${POSTGRES_HOST}" -p ${POSTGRES_PORT} -U "$POSTGRES_USER" -d "$POSTGRES_DB"  -f TVDatabase/TiledViz.sql
RET=$?
if [ $RET -gt 0 ]; then
    exit $RET
fi
echo "Filled done."
echo

export passwordDB="$POSTGRES_PASSWORD"

#Test user with password
python3 TVDatabase/newUserDatabase.py  --host=${POSTGRES_HOST} --port=${POSTGRES_PORT} --login=${POSTGRES_USER}  --databasename=${POSTGRES_DB}  --usertest="mmartial" --passwordtest="m_P@ssw0rd/08"
RET=$?
if [ $RET -gt 0 ]; then
    exit $RET
fi
python3 TVDatabase/newUserDatabase.py  --host=${POSTGRES_HOST} --port=${POSTGRES_PORT} --login=${POSTGRES_USER}  --databasename=${POSTGRES_DB}  --usertest="ddurandi" --passwordtest="OtherP@ssw/31d"
echo "User register done."
echo

python3 TVDatabase/BuildOldDatabase.py --host=${POSTGRES_HOST} --port=${POSTGRES_PORT} --login=${POSTGRES_USER}
RET=$?
if [ $RET -gt 0 ]; then
    exit $RET
fi
echo "Default old case done."
echo
python3 TVDatabase/BuildOldDatabase.py --oldcasefile='TVDatabase/OLDcases/VMD/case_config_mandelbrot' --oldnodefile='TVDatabase/OLDcases/VMD/nodes.js'  --host=${POSTGRES_HOST}  --port=${POSTGRES_PORT}  --login=${POSTGRES_USER}  --databasename=${POSTGRES_DB}  --usertest="mmartial" --haveconnection --connecthost="hostname.domainname.fr" --testsets="testVMDcase" --typeoftiles="CONNECTION" 
RET=$?
if [ $RET -gt 0 ]; then
    exit $RET
fi
echo "VMD old case done."
echo
python3 TVDatabase/BuildOldDatabase.py --oldcasefile='TVDatabase/OLDcases/CLIMAF/case_config_ciclad' --oldnodefile='TVDatabase/OLDcases/CLIMAF/nodes.js_CLIMAF'  --host=${POSTGRES_HOST}  --port=${POSTGRES_PORT}  --login=${POSTGRES_USER}  --databasename=${POSTGRES_DB}  --usertest="mmartial"  --testsets="CLIMAFcase" --typeoftiles="PICTURE"
RET=$?
if [ $RET -gt 0 ]; then
    exit $RET
fi
echo "CLIMAF Ciclad old case done."
echo
python3 TVDatabase/BuildOldDatabase.py --oldcasefile='TVDatabase/OLDcases/CLIMAF/case_config_mandelbrot' --oldnodefile='TVDatabase/OLDcases/CLIMAF/nodes.js_mandelbrot'  --host=${POSTGRES_HOST}  --port=${POSTGRES_PORT}  --login=${POSTGRES_USER}  --databasename=${POSTGRES_DB}  --usertest="mmartial"  --testsets="CLIMAFcase2" --typeoftiles="PICTURE"
RET=$?
if [ $RET -gt 0 ]; then
    exit $RET
fi
echo "CLIMAF Mandelbrot old case done."
echo
python3 TVDatabase/BuildOldDatabase.py --oldcasefile='TVDatabase/OLDcases/CLIMAF/case_config_mandelbrot' --oldnodefile='TVDatabase/OLDcases/CLIMAF/nodes.js_TR6AV'  --host=${POSTGRES_HOST}  --port=${POSTGRES_PORT}  --login=${POSTGRES_USER}  --databasename=${POSTGRES_DB}  --usertest="ddurandi"  --testsets="CLIMAFcase3" --typeoftiles="PICTURE"
RET=$?
if [ $RET -gt 0 ]; then
    exit $RET
fi
echo "CLIMAF TR6AV old case done."
