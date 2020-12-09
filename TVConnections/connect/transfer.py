# -*- coding: utf-8 -*-

import os, sys
import hashlib
import time
import stat
import re

Blocksize=65536

def hashfile(blockfile):
    for block in blockfile:
        hashlib.sha256().update(block)
    return hashlib.sha256().hexdigest()
    
def readblock(filed):
    with filed:
        block = filed.read(Blocksize)
        while len(block) > 0:
            yield block
            block = filed.read(Blocksize)

def send_file_server(client,TileSet,pathin,filename,pathout):
    filein=os.path.join(pathin,filename)
    filesize = os.path.getsize(filein)
    filed=open(filein, 'rb')
    filesha256=hashfile(readblock(filed))
    filed.close()
    command='putfile TS='+TileSet+" "+pathout+" "+filename+" "+str(filesize)+" "+str(filesha256)
    print("Command putfile : %s" % (command))
    client.send_server(command)
    print("Out of send command %s" % (str(client.get_OK())))
    client.send_file(pathin,filename)
    print("Out of send file %s" % (str(client.get_OK())))
    # detect executable file
    if oct((os.stat(filein).st_mode & stat.S_IRWXU+stat.S_IRWXG+stat.S_IRWXO) > stat.S_IRWXU) == oct(1):
        command='launch TS='+TileSet+" "+pathout+" chmod u+x "+filename
        client.send_server(command)
        print("Chmod %s : %s" % (pathout, str(client.get_OK())))


def get_file_client(client,TileSet,pathserv,filename,pathout):
    command='askfile TS='+TileSet+" "+pathserv+" "+filename
    print("Command askfile : %s" % (command))
    client.send_server(command)
    print("Out of ask command and file exists %s" % (str(client.get_OK())))

    while True:
        fileinfos=client.recv()
        if not fileinfos or fileinfos == 0:
            print("Error with fileinfos %s" % (str(fileinfos)))
            return -1
        else:
            print("Retrieve fileinfos : %s" % (str(fileinfos)))
            break

    if (re.search(r'fileinfos',fileinfos)):
        p=re.compile(r'fileinfos ([^ ]*) ([0-9]*) ([a-z0-9]*)')
        CommandFilename=p.sub(r'\1',fileinfos)
        CommandSize=int(p.sub(r'\2',fileinfos))
        CommandSha256=p.sub(r'\3',fileinfos)


        print("File transfer with filename %s with size %d and sha256 %s " % (CommandFilename,CommandSize,CommandSha256))

        client.get_file(pathout,filename,CommandSize,CommandSha256)
        print("Out of get file %s" % (str(client.get_OK())))
        return(int(CommandSize))
    else:
        return -2


