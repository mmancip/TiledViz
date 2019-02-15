#!/bin/env python3

import docker

import sys,os
import argparse
import json
import datetime
#import glob
import traceback

errors=sys.stderr

sys.path.append(os.path.abspath('./TVDatabase'))
from TVDb import tvdb

# from app import models
from TVDb import models

client = docker.from_env()

projectNAME='VMD'
sessionNAME='testSESSION'
jsoninputFile='OutputTestfile.json'

def parse_args(argv):
    parser = argparse.ArgumentParser(
        'From a (users,project,session) get tile_sets, tiles and connections tables and build a session json structure from TiledViz database.')
    parser.add_argument('--host', default='localhost',
                        help='Database host (default: localhost)')
    parser.add_argument('-l', '--login', default='tiledviz',
                        help='Database login (default: tiledviz)')
    parser.add_argument('-n', '--databasename', default='TiledViz',
                        help='Database name (default: TiledViz)')
    parser.add_argument('-p', '--projectNAME', default=projectNAME,
                        help='Project for test (default: '+projectNAME+')')
    parser.add_argument('-s', '--sessionNAME', default=sessionNAME,
                        help='Session for test (default: '+sessionNAME+')')
    parser.add_argument('-t', '--tileset', default='testVMDcase',
                        help='TileSet name for test (default: testVMDcase)')
    parser.add_argument('-f', '--jsonfile', default=jsoninputFile,
                        help='Json input file (default: '+jsoninputFile+' )')

    args = parser.parse_args(argv[1:])
    return args

if __name__ == '__main__':
    args = parse_args(sys.argv)

    metadata, conn, engine, pool, session = tvdb.SQLconnector(args)
    # for _t in metadata.tables:
    #     print("Table: ", _t)
    try:
        g=open(args.jsonfile,'r')
    except Exception:
        print('unable to open '+args.jsonfile+' file for reading.')
        errors.write(traceback.format_exc() + '\n')
        errors.write("\n\n")
        exit(2)
    JsonSession=json.load(g)
    g.close()

    ThisSession=session.query(models.Session).filter(models.Session.name == args.sessionNAME).first()
    ListAllTileSet_ThisSession=ThisSession.tile_sets
    
    tileset=[ thistileset for thistileset in ListAllTileSet_ThisSession ]
    #connection=session.query(models.Connection).filter(id==tileset[0].id_connections)
    connection=tileset[0].connection
    user=session.query(models.User).filter(models.User.id==connection.id_users).first().name
    print("Session : "+ThisSession.name+" \nTileSet : "+tileset[0].name+" \nConnection : "+connection.host_address+" \nUser : "+str(user))
    
    # Build proxy container
    passproxy=tvdb.passrandom(8).decode("utf-8","ignore")
    containerProxy=client.containers.run("alpine-ssh", name="myproxy", command=user+" \""+passproxy+"\" 1002", detach=True)
    print("We have built container for simulate ssh proxy machine with password '"+passproxy+"'.")
    
    # Build HPC container
    passHPC=tvdb.passrandom(8).decode("utf-8","ignore")
    containerHPC=client.containers.run("alpine-ssh", name="myHPC", command=user+" \""+passHPC+"\" 1002", detach=True)
    print("We have built container for simulate HPC machine with password '"+passHPC+"'.")

    # Create connection entry and build container for TiledViz connection to HPC machine
    passUser=tvdb.passrandom(8).decode("utf-8","ignore")
    containerUser=client.containers.run("teracy/ubuntu:16.04-dind-17.06.0-ce", name="my"+user, command="sshd", detach=True)
    print("We have built container for user "+user+" with password '"+passUser+"'.")
    print("User container name :",containerUser.name)
