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


export passwordDB="$POSTGRES_PASSWORD"
python3 TVDatabase/SessionDatabase.py --host=${POSTGRES_HOST} --login=${POSTGRES_USER}
RET=$?
if [ $RET -gt 0 ]; then
    exit $RET
fi
echo "OK for SessionDatabase with default values."
echo
python3 TVDatabase/SessionDatabase.py  --sessionNAME='session1_manual' --host=${POSTGRES_HOST} --login=${POSTGRES_USER}  --databasename=${POSTGRES_DB}
RET=$?
if [ $RET -gt 0 ]; then
    exit $RET
fi
echo "VMD old case done."
echo
python3 TVDatabase/SessionDatabase.py   --sessionNAME='testSESSION' --enablejsonwrite --host=${POSTGRES_HOST} --login=${POSTGRES_USER}  --databasename=${POSTGRES_DB}
RET=$?
if [ $RET -gt 0 ]; then
    exit $RET
fi
cat OutputTestfile.json
RET=$?
if [ $RET -gt 0 ]; then
    echo "error OutputTestfile.json"
    exit $RET
fi
echo
echo "CLIMAF Ciclad old case done."
echo
python3 TVDatabase/SessionDatabase.py --sessionNAME='Mandelbrot' --enablejsonwrite --jsonfile=/tmp/testMandelbrot.json --host=${POSTGRES_HOST} --login=${POSTGRES_USER}  --databasename=${POSTGRES_DB}
RET=$?
if [ $RET -gt 0 ]; then
    exit $RET
fi
cat /tmp/testMandelbrot.json
RET=$?
if [ $RET -gt 0 ]; then
    echo "error testMandelbrot.json"
    exit $RET
fi
echo
echo "CLIMAF Mandelbrot old case done."
echo

#Test user with password
python3 TVDatabase/testUserDatabase.py  --host=${POSTGRES_HOST} --login=${POSTGRES_USER}  --databasename=${POSTGRES_DB}  --usertest="mmartial" --passwordtest="m_P@ssw0rd/08"
RET=$?
if [ $RET -gt 0 ]; then
    exit $RET
fi
python3 TVDatabase/testUserDatabase.py  --host=${POSTGRES_HOST} --login=${POSTGRES_USER}  --databasename=${POSTGRES_DB}  --usertest="ddurandi" --passwordtest="OtherP@ssw/31d"
echo "User register done."
echo

