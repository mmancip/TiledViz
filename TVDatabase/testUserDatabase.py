#!/bin/env python3

import sys,os
import argparse
import re
import datetime

errors=sys.stderr

from TVDb import tvdb

from TVDb import models

POSTGRES_HOST="postgres"
POSTGRES_PORT="6431"
POSTGRES_USER="tiledviz"
POSTGRES_DB="TiledViz"

def parse_args(argv):
    parser = argparse.ArgumentParser(
        'Add User with password and salt Transform old nodes.js database to TiledViz database.')
    parser.add_argument('--host', default=POSTGRES_HOST,
                        help='Database host (default: '+POSTGRES_HOST+')')
    parser.add_argument('--port', default=POSTGRES_PORT,
                        help='Port (default: '+POSTGRES_PORT+')')
    parser.add_argument('-l', '--login', default=POSTGRES_USER,
                        help='Database login (default: '+POSTGRES_USER+')')
    parser.add_argument('-n', '--databasename', default=POSTGRES_DB,
                        help='Database name (default: '+POSTGRES_DB+')')
"    parser.add_argument('-t', '--usertest', default='ddurandi',
                        help='User name for test (default: ddurandi)')
    parser.add_argument('-p', '--passwordtest', default='5#f_@-m/1ArtOvx0',
                        help='Project for test (default: "5#f_@-m/1ArtOvx0")')

    args = parser.parse_args(argv[1:])
    return args


if __name__ == '__main__':
    args = parse_args(sys.argv)

    metadata, conn, engine, pool, session = tvdb.SQLconnector(args)
    # for _t in metadata.tables:
    #     print("Table: ", _t)

    testPassword,testSalt=session.query(models.Users.password,models.Users.salt).filter_by(name=args.usertest).one()
    testP=tvdb.testpassprotected(models.Users,args.usertest,args.passwordtest,testPassword,testSalt)
    if (testP):
        dateVerified=session.query(models.Users.dateverified).filter_by(name=args.usertest).one()[0]
        print("Succes : User successfuly tested at %s." % (dateVerified) )
        #thedatetime=datetime.datetime.strptime(dateVerified, "%Y-%m-%d %H:%M:%S.%f")
        #thedatetime=datetime.date.fromisoformat(dateVerified)
        # diffdate=datetime.datetime.now() - thedatetime
        diffdate=datetime.datetime.now() - dateVerified
        print("There is %s days and %s seconds ago." % (diffdate.days,diffdate.seconds))
    else:
        print("Error : User may have already been registrered.")
        exit(1)
        
