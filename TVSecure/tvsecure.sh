#!/bin/bash

export DOCKER_HOST=$1

export POSTGRES_HOST=$2
export POSTGRES_DB=$3
export POSTGRES_USER=$4
export POSTGRES_PASSWORD="$5"
export SECRET_KEY="$6"
export OUT=$7
export VirtualENV=$8
export IPPOST=$(grep ${POSTGRES_HOST} /etc/hosts | tr '[:space:]*' '\n' | head -1)
export passwordDB=${POSTGRES_PASSWORD}

source ${VirtualENV}/bin/activate

python3 TVSecure/TVSecure.py --POSTGRES_HOST=${POSTGRES_HOST} --POSTGRES_IP=$IPPOST --POSTGRES_DB=${POSTGRES_DB} --POSTGRES_USER=${POSTGRES_USER} --POSTGRES_PASSWORD=${POSTGRES_PASSWORD} --secretKey=${SECRET_KEY} > ${OUT} 2>&1 &
sleep 20