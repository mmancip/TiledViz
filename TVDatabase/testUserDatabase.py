#!/bin/env python3

import sys,os
import argparse
import re
import datetime

errors=sys.stderr

from TVDb import tvdb

from TVDb import models

def parse_args(argv):
    parser = argparse.ArgumentParser(
        'Add User with password and salt Transform old nodes.js database to TiledViz database.')
    parser.add_argument('--host', default='localhost',
                        help='Database host (default: localhost)')
    parser.add_argument('-l', '--login', default='tiledviz',
                        help='Database login (default: tiledviz)')
    parser.add_argument('-n', '--databasename', default='TiledViz',
                        help='Database name (default: TiledViz)')
    parser.add_argument('-t', '--usertest', default='mmancip',
                        help='User name for test (default: mmancip)')
    parser.add_argument('-p', '--passwordtest', default='5#f_@-m/1ArtOvx0',
                        help='Project for test (default: "5#f_@-m/1ArtOvx0")')

    args = parser.parse_args(argv[1:])
    return args


if __name__ == '__main__':
    args = parse_args(sys.argv)

    metadata, conn, engine, pool, session = tvdb.SQLconnector(args)
    # for _t in metadata.tables:
    #     print("Table: ", _t)

    testPassword,testSalt=session.query(models.User.password,models.User.salt).filter_by(name=args.usertest).one()
    testP=tvdb.testpassprotected(models.User,args.usertest,args.passwordtest,testPassword,testSalt)
    if (testP):
        dateVerified=session.query(models.User.dateverified).filter_by(name=args.usertest).one()[0]
        print("Succes : User successfuly tested at %s." % (dateVerified) )
        #thedatetime=datetime.datetime.strptime(dateVerified, "%Y-%m-%d %H:%M:%S.%f")
        #thedatetime=datetime.date.fromisoformat(dateVerified)
        # diffdate=datetime.datetime.now() - thedatetime
        diffdate=datetime.datetime.now() - dateVerified
        print("There is %s days and %s seconds ago." % (diffdate.days,diffdate.seconds))
    else:
        print("Error : User may have already been registrered.")
        exit(1)
        
