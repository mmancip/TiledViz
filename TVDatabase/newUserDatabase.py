#!/bin/env python3

import sys,os
import argparse
import re
import datetime

errors=sys.stderr

from TVDb import tvdb

def parse_args(argv):
    parser = argparse.ArgumentParser(
        'Add User with password and salt Transform old nodes.js database to TiledViz database.')
    parser.add_argument('--host', default='localhost',
                        help='Database host (default: localhost)')
    parser.add_argument('-l', '--login', default='tiledviz',
                        help='Database login (default: tiledviz)')
    parser.add_argument('-n', '--databasename', default='TiledViz',
                        help='Database name (default: TiledViz)')
    parser.add_argument('-t', '--usertest', default='ddurandi',
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

    hashpass, salt=tvdb.passprotected(args.passwordtest)
    id_users, uniqUser = tvdb.insert_table('users',{"name":args.usertest,"salt":salt,"password":hashpass,"dateverified":datetime.datetime.now()})
    tvdb.print_table("users")
    
    if (not uniqUser):
        print("Error : User may have already been registrered.")
        exit(1)
    else:
        print("Succes : User successfuly registrered.")

