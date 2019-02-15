#!/bin/env python3

import sys,os
import argparse
import re
import json
import datetime
import traceback

errors=sys.stderr

from TVDb import tvdb

oldnodefile='TVDatabase/OLDcases/ANATOMIST/nodes.js'
oldcasefile='TVDatabase/OLDcases/ANATOMIST/case_config_mandelbrot'
projectNAME='testCASE'
sessionNAME='testSESSION'
datapath='/home/brain/BrainDatas3/archi-sulci'

def parse_args(argv):
    parser = argparse.ArgumentParser(
        'Transform old nodes.js database to TiledViz database.')
    parser.add_argument('-c', '--oldcasefile', default=oldcasefile,
                        help='Old case_config_machine path (default: ANATOMIST Mandelbrot).')
    parser.add_argument('-f', '--oldnodefile', default=oldnodefile,
                        help='Old nodes.js path (default: ANATOMIST Mandelbrot).')
    parser.add_argument('--host', default='localhost',
                        help='Database host (default: localhost)')
    parser.add_argument('-l', '--login', default='tiledviz',
                        help='Database login (default: tiledviz)')
    parser.add_argument('-n', '--databasename', default='TiledViz',
                        help='Database name (default: TiledViz)')
    parser.add_argument('-t', '--usertest', default='ddurandi',
                        help='User name for test (default: ddurandi)')
    parser.add_argument('-p', '--projectNAME', default=projectNAME,
                        help='Project for test (default: '+projectNAME+')')
    parser.add_argument('-s', '--sessionNAME', default=sessionNAME,
                        help='Session for test (default: '+sessionNAME+')')
    parser.add_argument('-C', '--haveconnection', action='store_true',
                        help='Activate a connection object for the TileSet')
    parser.add_argument('-H', '--connecthost', default='HPCmachine',
                        help='Create a connection object to this host')
    parser.add_argument('-r', '--testsets', default='testTileSets',
                        help='Type for test (default: testTileSets)')
    parser.add_argument('-m', '--typeoftiles', default='CONTAINER',
                        help='Type of tiles (default: CONTAINER, PICTURE, HTML)')
    parser.add_argument('-d', '--datapath', default=datapath,
                        help='Path for data (default: '+datapath+')')

    args = parser.parse_args(argv[1:])
    return args

def read_old_casefile(case_config_file,args):

    try:
        f=open(args.oldcasefile,'r')
    except Exception:
        print('unable to open old case file.')
        errors.write(traceback.format_exc() + '\n')
        errors.write("\n\n")
        exit(1)

    re_def=re.compile("^\\w*=[A-Za-z0-9/_-]*")
    while 1:
        line = f.readline()
        if not line:
            break
        else:
            matchdef=re_def.match(line)
            #print("matchdef :",matchdef)
            if (matchdef):
                key=line.split('=')[0]
                #print(line,matchdef.span()[1])
                value=line[0:matchdef.span()[1]].split('=')[1]
                #print ("line :",line," | key : ",key," | value : ",value)
                if (key == "CASE_NAME" ):
                    args.projectNAME=value
                elif (key == "DATA_PATH" ):
                    args.datapath=value
                elif (re.match(r'.*(session|SESSION).*',key)):
                    args.sessionNAME=value
            #else:
                #print ("bad line :",line)
        # #pour la source :
    # # case=open("case_config_mandelbrot") #DATA_PATH=/home/brain/BrainDatas3/archi-sulci
    # # anatomist_json=json.load("case_data_config.json") #=>boucle sur les subjects de data_list 
    

class OldJson:
    
    def __init__(self,nodesfilename):
        try:
            f=open(nodesfilename,'r')
        except Exception:
            print('unable to open old node.js file.')
            errors.write(traceback.format_exc() + '\n')
            errors.write("\n\n")
            exit(2)

        #outnodejson="/tmp/tmpoutnode.json"
        # try:
        #     g=open(outnodejson,'w')
        # except Exception:
        #     print('unable to open '+outnodejson+' file for writing.')
        #     errors.write(traceback.format_exc() + '\n')
        #     errors.write("\n\n")
        #     exit(2)
            
        line = f.readline()
        line = f.readline()

        #replace first line
        if (re.match(r'.*\[',line)):
            line__="[ "
        else:
            line__="" #re.sub("\s*var\s*text_\s*=\s*{","{",line).replace('nodes:','\"nodes\":')
        myjson=""

        lineno=1
        #print(str(lineno)+" : "+line_)

        line = f.readline()
        line_= line

        simplecote_def=re.compile("^\\s*\"\\w*\"\\s*:\\s*'.*'")
        simple_def=re.compile("\'")
        double_def=re.compile("\"")
        pipe_def=re.compile("\|")
        
        while 1:
            line = f.readline()
            if not line:
                #suppress last line and last "};"
                #myjson=myjson[:len(myjson)-2]
                break
            else:
                #One must simple cote for comment in tags... 
                matchdef=simplecote_def.match(line__)
                if (matchdef):
                    linesplit=line__[0:matchdef.span()[1]].split(':')
                    value=linesplit[1]
                    value=double_def.sub("|",value)
                    value=simple_def.sub("\"",value)
                    value=pipe_def.sub("'",value)
                    line__=linesplit[0]+" : "+value+",\n"                    
                #g.write(line__)
                #line without carriage return
                myjson=myjson+line__[:-1]
            line__=line_
            line_=line
            lineno = lineno + 1
            #print(str(lineno)+" : "+line_)

        #suppress last line and last "};"
        if (re.match(r'\]',line__)):
            line__="]"
            myjson=myjson+line__
            #g.write(line__)
        
        #print(len(myjson),myjson[len(myjson)-100:])
        
        # g.close
        # try:
        #     g=open(outnodejson,'r')
        # except Exception:
        #     print('unable to open '+outnodejson+' file for writing.')
        #     errors.write(traceback.format_exc() + '\n')
        #     errors.write("\n\n")
        #     exit(2)

        #self.nodesjson=json.load(g)
        self.nodesjson=json.loads(myjson)


    def __getitem__(self,num):
        return self.nodesjson[num]
    
    def __len__(self):
        return len(self.nodesjson)

if __name__ == '__main__':
    args = parse_args(sys.argv)
    print('case file : ',args.oldcasefile)
    print('node file : ',args.oldnodefile)
    read_old_casefile(args.oldcasefile,args)
    #print("args.projectNAME",args.projectNAME,"args.datapath",args.datapath,"args.sessionNAME=",args.sessionNAME)
    print("")

    Mynodes=OldJson(args.oldnodefile)
    print("Test one (second) element : |", Mynodes[1]["comment"],"|")
    # print("Test json.dumps of that element :",json.dumps(Mynodes[1], indent=4))
    # print("Pass: ",os.getenv("passwordDB"))
    
    metadata, conn, engine, pool, session = tvdb.SQLconnector(args)
    for _t in metadata.tables:
        print("Table: ", _t)

    id_users, uniqUser = tvdb.insert_table('users',{"name":args.usertest})
    # print("connections :",pool.checkedout())
    tvdb.print_table("users")
    
    id_projects, uniq = tvdb.insert_table('projects',{"name":args.projectNAME,"id_users":id_users,"description":"This is an old case "+args.projectNAME})
    tvdb.print_table("projects")

    id_sessions, uniqSession = tvdb.insert_table('sessions',{"name":args.sessionNAME,"id_projects":id_projects,"description":"This is an old case "+args.projectNAME+" session "+args.sessionNAME,"Number_of_active_users":1,"timeout":480})
    tvdb.print_table("sessions")

    if (uniqSession or uniqUser):
        id_users_sessions, uniq = tvdb.insert_table('many_users_has_many_sessions',{"id_sessions":id_sessions,"id_users":id_users})

    if (args.haveconnection):
        id_connection, uniqConnection = tvdb.insert_table('connections',{"host_address":args.connecthost,"id_users":id_users})
        tvdb.print_table("connections")
        
        id_tile_sets, uniqTileSet = tvdb.insert_table('tile_sets',{"name":args.testsets,"type_of_tiles":args.typeoftiles,"Dataset_path":args.datapath,"id_connections":id_connection})
    else:
        id_tile_sets, uniqTileSet = tvdb.insert_table('tile_sets',{"name":args.testsets,"type_of_tiles":args.typeoftiles,"Dataset_path":args.datapath})

    tvdb.print_table("tile_sets")

    if (uniqSession or uniqTileSet):
        id_sessions_tilesets, uniq = tvdb.insert_table('many_sessions_has_many_tile_sets',{"id_sessions":id_sessions,"id_tile_sets":id_tile_sets})

    
    now = datetime.datetime.now()
    print ("Tiles creation : ",now)
    try:
        Mynodes[1]["tags"]
    except :
        for i in range(len(Mynodes)):
            Mynodes[i]["tags"]=""
    tiles=[]
    for i in range(len(Mynodes)):
        searchPort=re.search(r'port=\d+',Mynodes[i]["url"])
        if (searchPort):
            ConnectionPort=int(searchPort.group().replace('port=',''))
        else:
            ConnectionPort=0
        tiles.append({"title" :   Mynodes[i]["title"],
                      "comment" : Mynodes[i]["comment"],
                      "tags":     Mynodes[i]["tags"],
                      "source" :  {"connection" : ConnectionPort,
                                   "url" : Mynodes[i]["url"]
                                  },
                      "pos_px_x": -1,
                      "pos_px_y": -1,
                      'creation_date' : now
        })

    table_tiles = metadata.tables['tiles']
    #myinsert=table_tiles.insert().returning(table_tiles.c.id)
    #myinsert=table_tiles.insert(returning=[table_tiles.c.id])
    myinsert=table_tiles.insert()
    connexe=conn.execute(myinsert, tiles)
    #connexe.inserted_primary_key() -> Can't call inserted_primary_key when returning() is used.
    #connexe.first() -> sqlalchemy.exc.ResourceClosedError: This result object does not return rows. It has been closed automatically.
    #connexe.fetchone() -> psycopg2.ProgrammingError: no results to fetch    
    #id_tiles=connexe.commit()
    #id_tiles=connexe.fetchall()
    #connexe.close()
    #print("All tiles:",id_tiles)

    select_st = table_tiles.select().where(table_tiles.c.creation_date==now)
    res = conn.execute(select_st)
    #print("All tiles:")
    id_tiles=[]
    many_tiles_has_many_tile_sets=[]
    for _row in res:
        #print(_row)
        id_tiles.append(_row[0])
        many_tiles_has_many_tile_sets.append({"id_tiles":_row[0], "id_tile_sets":id_tile_sets})
    print("All tiles:",id_tiles)


    table_tilesets_tiles = metadata.tables['many_tiles_has_many_tile_sets']
    #myinsert = table_tilesets_tiles.insert().returning(table_tilesets_tiles.c.id_tiles).values(id_tiles=id_tiles,id_tile_sets=)
    myinsert = table_tilesets_tiles.insert()
    #connexe=conn.execute(myinsert)
    connexe=conn.execute(myinsert, many_tiles_has_many_tile_sets)
    #id_tilesets_tiles=connexe.fetchall()
    #connexe.close()
    #print("All tiles in this tile_set :",id_tilesets_tiles)
    
    # #conn.close()
    # #engine.disconnect()
