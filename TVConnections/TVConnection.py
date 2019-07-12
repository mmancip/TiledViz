#!/bin/env python3

import datetime,time
import argparse

import sys,os
import pexpect,re

sys.path.append(os.path.abspath('./TVDatabase'))
from TVDb import tvdb
from TVDb import models

def parse_args(argv):
    parser = argparse.ArgumentParser(
        'From a connection Id in PostgreSQL DB get connection parameters from TiledViz database.')
    parser.add_argument('--host', default='localhost',
                        help='Database host (default: localhost)')
    parser.add_argument('-l', '--login', default='tiledviz',
                        help='Database login (default: tiledviz)')
    parser.add_argument('-n', '--databasename', default='TiledViz',
                        help='Database name (default: TiledViz)')
    parser.add_argument('-u', '--usertest', default='ddurandi',
                        help='User name for test (default: ddurandi)')
    parser.add_argument('-t', '--connectionId', 
                        help='Connection Id in DB.')

    args = parser.parse_args(argv[1:])
    return args

if __name__ == '__main__':
    args = parse_args(sys.argv)
    metadata, conn, engine, pool, session = tvdb.SQLconnector(args)
    print("Build connection number ",args.connectionId)
    
    Connection=session.query(models.Connection).filter(models.Connection.id == int(args.connectionId)).one()
    print("From DB connection informations : ",str((Connection.auth_type,Connection.host_address,Connection.scheduler)))

    NbFrontendTo=0
    NbFrontendFrom=0
    if (Connection.auth_type == "ssh_rebound"):
        NbFrontendTo = input("Give the number of frontends to go to the HPC frontend (0 if direct connectio) :")
        NbFrontendFrom = input("Give the number of gateways to go back from HPC nodes to the Flask server (1 if they need to rebound from the HPC frontend) :")
    Password = input("Enter your password !")

    import Swarm
    if (Connection.scheduler_file != ""):
        print("From DB connection scheduler_file : ",str(Connection.scheduler_file))
    print("Bye !")
    time.sleep(10)
    os.system("ps -Aef | grep 'connect.*@172.17.*' |grep -v grep | sed -e 's%myuser\\s*\\([0-9]*\\).*%\\1%' |xargs kill")
