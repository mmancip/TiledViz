#!/bin/env python3

import sys,os
import re
import datetime
import json
import hashlib, binascii
import random
import crypt

from sqlalchemy.engine.url import make_url
from sqlalchemy import create_engine
#from sqlalchemy import pool
from sqlalchemy.pool import QueuePool
from sqlalchemy import MetaData
from sqlalchemy import select
# # from sqlalchemy.orm import scoped_session, sessionmaker
# # from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, joinedload, subqueryload, Session

from psycopg2 import IntegrityError as psIntegrityError

from sqlalchemy.exc import IntegrityError

def SQLconnector(args):
    global metadata,conn,engine,pool,session
    engine = create_engine(make_url("postgresql://"+args.login+":"+os.getenv("passwordDB")+"@"+args.host+":"+args.port+"/"+args.databasename),
                           convert_unicode= True,
                           poolclass= QueuePool
                           )
    # def status(self):
    #     return "Pool size: %d  Connections in pool: %d "\
    #         "Current Overflow: %d Current Checked out "\
    #         "connections: %d" % (self.size(),
    #                              self.checkedin(),
    #                              self.overflow(),
    #                              self.checkedout())
    metadata = MetaData()
    metadata.reflect(engine)

    conn=engine.connect()

    # conn = conn.execution_options(
    #     isolation_level="READ COMMITTED"
    # )
    # #Valid values for isolation_level include:
    # READ COMMITTED
    # READ UNCOMMITTED
    # REPEATABLE READ
    # SERIALIZABLE
    # AUTOCOMMIT

    pool=QueuePool(conn,
                   pool_size= 10,
                   max_overflow= 10)
    # ,
    #                pool_timeout= 30,
    #                pool_recycle= 1800

    session = Session(engine)
    # pre-connect so this part isn't profiled (if we choose)
    session.connection()
    return(metadata,conn,engine,pool,session)

def insert_table(table_name,values):
    table_ = metadata.tables[table_name]
    now = datetime.datetime.now()

    try:
        if ("creation_date" in table_.c and "creation_date" in values):
            values["creation_date"]=now
        myinsert = table_.insert().returning(table_.c.id).values(values)
    except (KeyError, AttributeError):
        myinsert = table_.insert().returning(table_.c[values.copy().popitem()[0]]).values(values)

    uniq=True
    try:
        connexe=conn.execute(myinsert)
        id_val=connexe.fetchall()[0][0] 
        connexe.close()
        print("Add "+table_name+" :",id_val)
    except (psIntegrityError, IntegrityError):
        uniq=False
        print('Warning IntegrityError: in '+table_name+' values '+values["name"]+' already exist.')
        print('We will use previous value.')
        id_val=session.query(table_).filter(table_.c.name==values["name"]).one()[0]
        print("Reuse "+table_name+" :",id_val)
        
    return id_val,uniq

def print_table(table_name):
    table_ = metadata.tables[table_name]
    select_st = select([table_])
    res = conn.execute(select_st)
    for _row in res:
        print(_row)

def encode_tileset(thistileset):
    nbtiles=len(thistileset.tiles)
    tile=thistileset.tiles[int(nbtiles/2)]
    try:
        tile.source["name"]
        hasname=True
    except:
        hasname=False
    try:
        tile.source["variable"]
        hasvariable=True
    except:
        hasvariable=False
            
    tiledata=[]
    try:
        listiles=sorted((tile for tile in thistileset.tiles),key=lambda x: int(x.source["connection"]));
    except:
        listiles=sorted((tile for tile in thistileset.tiles),key=lambda x: int(x.id));
    for tile in listiles:
        if(hasname):
            name=tile.source["name"]
        else:
            name=tile.title
        if (hasvariable):
            var=tile.source["variable"]
        else:
            var=name
        # If connection ? Test tileset connection ok ??
        tiledata.append({"title":tile.title,
                         "url":tile.source["url"],
                         "comment":tile.comment,
                         "tags":tile.tags,
                         "name":name,
                         "variable":var,
                         "pos_px_x":tile.pos_px_x,
                         "pos_px_y":tile.pos_px_y,
                         "IdLocation" : tile.IdLocation,
                         "dbid":tile.id
                         })
    return tiledata

def decode_tileset(thistileset):
    # If connection ? Test tileset connection ok ??
    try:
        tile=thistileset.tiles[0]
    except:
        return ""

    try:
        tile.source["name"]
        hasname=True
    except:
        hasname=False
    try:
        tile.source["variable"]
        hasvariable=True
    except:
        hasvariable=False

    try:
        listiles=sorted((tile for tile in thistileset.tiles),key=lambda x: int(x.source["connection"]));
    except:
        listiles=sorted((tile for tile in thistileset.tiles),key=lambda x: int(x.id));
    if(hasname):
        if (hasvariable):
            json_tiles={"nodes":
                        [{"title":tile.title,
                          "url" :tile.source["url"],
                          "comment" :tile.comment,
                          "tags" :tile.tags,
                          "variable" :tile.source["variable"],
                          "pos_px_x" :tile.pos_px_x,
                          "pos_px_y" :tile.pos_px_y,
                          "IdLocation" : tile.IdLocation,
                          "name" :tile.source["name"],
                          "connection" :tile.source["connection"],
                        } for tile in listiles ]}
        else:
            json_tiles={"nodes":
                        [{"title":tile.title,
                          "url" :tile.source["url"],
                          "comment" :tile.comment,
                          "tags" :tile.tags,
                          "variable" : "",
                          "pos_px_x" :tile.pos_px_x,
                          "pos_px_y" :tile.pos_px_y,
                          "IdLocation" : tile.IdLocation,
                          "name" :tile.source["name"],
                          "connection" :tile.source["connection"],
                        } for tile in listiles ]}
    elif (hasvariable):
        json_tiles={"nodes":
                    [{"title":tile.title,
                      "url" :tile.source["url"],
                      "comment" :tile.comment,
                      "tags" :tile.tags,
                      "variable" :tile.source["variable"],
                      "pos_px_x" :tile.pos_px_x,
                      "pos_px_y" :tile.pos_px_y,
                      "IdLocation" : tile.IdLocation,
                      "name" : "",
                      "connection" :tile.source["connection"],
                    } for tile in listiles ]}
    else:
        json_tiles={"nodes":
                    [{"title":tile.title,
                      "url" :tile.source["url"],
                      "comment" :tile.comment,
                      "tags" :tile.tags,
                      "variable" : "",
                      "pos_px_x" :tile.pos_px_x,
                      "pos_px_y" :tile.pos_px_y,
                      "IdLocation" : tile.IdLocation,
                      "name" : "",
                      "connection" :tile.source["connection"],
                    } for tile in listiles ]}

    try:
        json_tiles_text=json.JSONEncoder().encode(json_tiles)
    except:
        json_tiles_text=""
    return json_tiles_text

def encode_session(sessionNAME,Session):
    ThisSession=session.query(Session).filter(Session.name == sessionNAME).first()
    ListAllTileSet_ThisSession=ThisSession.tile_sets
    JsonSession=json.JSONEncoder().encode(
        {"info": {"SessionName" : sessionNAME,
                  "ProjectName" : ThisSession.project.name,
                  "Users" : list(set([ThisSession.project.user.name]+
                                      [SessionUser.name for SessionUser in ThisSession.users]))},
         "tilesets": [ {"name":thistileset.name,
                        "Dataset_path":thistileset.Dataset_path,
                        "tiles": [ {"id" : tile.id,
                                    "title" : tile.title,
                                    "comment": tile.comment,
                                    "source": tile.source,
                                    "tags": tile.tags
                        } for tile in thistileset.tiles ] }
                       for thistileset in ListAllTileSet_ThisSession ]
        })

    return JsonSession

def passrandom(nbchar):
    #ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ/@_.-"
    ALPHABET = "B6P8VbhZoGp9JYd0.uLCsAT4DXF1xqIUSyQMniNgje5_~3crvlHR-7W2f@kEtmazwKO$"
    mystring=''.join(random.choice(ALPHABET) for i in range(nbchar)).encode('utf-8')
    #mystring = os.urandom(nbchar)
    #mystring=crypt.mksalt(crypt.METHOD_SHA512).encode('utf-8')
    return mystring

def passprotected(password):
    mysalt=passrandom(20)
    passhash = hashlib.pbkdf2_hmac('sha512',password.encode('utf-8'),mysalt,100000)
    hexpass = binascii.hexlify(passhash)
    return hexpass.decode("utf-8","ignore"),mysalt.decode("utf-8","ignore")


def testpassprotected(Users,user,password,savedhash,savedsalt):
    mysalt=savedsalt.encode('utf-8')
    passhash = hashlib.pbkdf2_hmac('sha512',password.encode('utf-8'),mysalt,100000)
    hexpass = binascii.hexlify(passhash)
    thisUser=session.query(Users).filter_by(name=user).one()
    readHash=thisUser.password
    if (hexpass.decode("utf-8","ignore")==readHash):
        now = datetime.datetime.now()
        thisUser.dateverified=now
        session.commit()
        return True
    else:
        print('mysalt= %s\n passhash = %s\n hexpass = %s\n hexpass.decode("utf-8","ignore") = %s\n readHash = %s' % (mysalt, passhash, hexpass, hexpass.decode("utf-8","ignore"), readHash))
        return False
