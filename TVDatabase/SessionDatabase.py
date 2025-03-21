#!/bin/env python3

import sys,os
import argparse
import json
import datetime
#import glob
import traceback

errors=sys.stderr

from TVDb import tvdb

POSTGRES_HOST="postgres"
POSTGRES_PORT="6431"
POSTGRES_USER="tiledviz"
POSTGRES_DB="TiledViz"

# sys.path.append(os.path.abspath('./TVWeb'))
# from app import models
from TVDb import models

projectNAME='VMD'
sessionNAME='testSESSION'
jsonoutputFile='OutputTestfile.json'

def parse_args(argv):
    parser = argparse.ArgumentParser(
        'From a (users,project,session) get tile_sets, tiles and connections tables and build a session json structure from TiledViz database.')
    parser.add_argument('--host', default=POSTGRES_HOST,
                        help='Database host (default: '+POSTGRES_HOST+')')
    parser.add_argument('--port', default=POSTGRES_PORT,
                        help='Port (default: '+POSTGRES_PORT+')')
    parser.add_argument('-l', '--login', default=POSTGRES_USER,
                        help='Database login (default: '+POSTGRES_USER+')')
    parser.add_argument('-n', '--databasename', default=POSTGRES_DB,
                        help='Database name (default: '+POSTGRES_DB+')')
    parser.add_argument('-t', '--usertest', default='ddurandi',
                        help='User name for test (default: ddurandi)')
    parser.add_argument('-p', '--projectNAME', default=projectNAME,
                        help='Project for test (default: '+projectNAME+')')
    parser.add_argument('-s', '--sessionNAME', default=sessionNAME,
                        help='Session for test (default: '+sessionNAME+')')
    parser.add_argument('-j', '--enablejsonwrite', action='store_true',
                        help='Active json data save.')
    parser.add_argument('-f', '--jsonfile', default=jsonoutputFile,
                        help='Json output file (default: '+jsonoutputFile+' )')

    args = parser.parse_args(argv[1:])
    return args

if __name__ == '__main__':
    args = parse_args(sys.argv)
    if (args.enablejsonwrite):
        print("Json output file enable :",args.jsonfile)

    metadata, conn, engine, pool, session = tvdb.SQLconnector(args)
    for _t in metadata.tables:
        print("Table: ", _t)

    print("Session id for sessionname = "+args.sessionNAME+" : ",
          session.query(models.Sessions.id).filter_by(name=args.sessionNAME).scalar())
    #session.query(models.Users).join(models.Users.username)

    ThisSession=session.query(models.Sessions).filter(models.Sessions.name == args.sessionNAME).first()
    # ThisTileSet_ThisSession=ThisSession.tile_sets[0]
    # print("First TileSet for this session "+sessionNAME+" : ", ThisTileSet_ThisSession.name)

    # ThoseSession=session.query(models.Sessions).filter(models.Sessions.name == "Mandelbrot").first()
    # ListAllTileSet_ThoseSession=session.query(models.Sessions).filter(models.Sessions.name == "Mandelbrot").first().tile_sets
    # print("All TileSets for this session 'Mandelbrot' : ",
    #       [ thistileset.name for thistileset in ListAllTileSet_ThoseSession ])

    ListAllTileSet_ThisSession=ThisSession.tile_sets
    print("All TileSets for this session "+args.sessionNAME+" : ",
          [ thistileset.name for thistileset in ListAllTileSet_ThisSession ])

    JsonSession=tvdb.encode_session(args.sessionNAME,models.Sessions)

    if ( args.enablejsonwrite ):
        try:
            g=open(args.jsonfile,'w+')
        except Exception:
            print('unable to open '+args.jsonfile+' file for writing.')
            errors.write(traceback.format_exc() + '\n')
            errors.write("\n\n")
            exit(2)
        json.dump(JsonSession,g)
        g.close()
    else:
        print("In memory Json Session : ",json.dumps(JsonSession))
        
