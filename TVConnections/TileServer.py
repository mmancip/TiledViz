#!python3
# coding: utf-8

import errno
import threading, time
import sys,os,re
from subprocess import Popen as Popen
import subprocess as subp
import shlex
from operator import itemgetter

import argparse

import traceback

import socket

sys.path.append(os.path.abspath('./connect'))
from connect import sock
IdTS=sock.PORTServer+1

import logging

#import code
#            code.interact(local=locals())

DEBUG=False
TRACE=False

MaxWaitExecute=120
waitsleep=0.5


def parse_args(argv):
    parser = argparse.ArgumentParser(
        'TiledViz frontend server to dispatch orders on all tiles of each TileSets on its HPC machine.')
    parser.add_argument('--debug', action='store_true',
                        help='Debug TileServer messages.',default=DEBUG)
    parser.add_argument('--trace', action='store_true',
                        help='Debug TileServer with ipdb trace calls.',default=TRACE)
    parser.add_argument('--idts', default=IdTS,
                        help='WARNING: Do not change this value only if you know what you are doing !! \n'\
                        'Default port for first TiledSet (default: localhost)')
    parser.add_argument('--maxwaitexecute', default=MaxWaitExecute,
                        help='Number max of seconds waiting for a response for TileServer messages.')
    
    args = parser.parse_args(argv[1:])
    return args



TSthreads={}

# Tile Management
class TileConnection:
    def __init__(self, TSserver, TileSetName, id, container, password):
        self.TSserver=TSserver
        self.TileSetName=TileSetName
        self.Id=id
        self.ids=(container, password)
        self.laststate=False
        self.lastval=255
        serverLogger.debug("New connection : "+str(self.TSserver)+self.TileSetName+str(self.Id)+str(self.ids))

    def get_laststate(self):
        if (self.laststate):
            return self.lastval
        else:
            return False

    def execute(self,command):
        self.laststate=False
        ExecuteMsg="execute "+command
        serverLogger.debug("in tile command "+ExecuteMsg)
        self.TSserver.send_client(self.Id,ExecuteMsg)
        RET=self.TSserver.get_OK(self.Id)
        serverLogger.debug("in tile command return "+str(RET))
        self.lastval=RET
        self.laststate=True

# TileSet management
class TilesSet(threading.Thread):
    def __init__(self, TileSetName, Nb):
        threading.Thread.__init__(self)
        self.thread = threading.Thread(target=self.run, args=(TileSetName,Nb,))
        self.thread.start()
        self.laststate=False
        self.lastval=255

    def __del__(self):
        # !! Must have kill tiles before !!
        for tileconnection in self.ListClient:
            del tileconnection
        del TSthreads[self.TileSetName]
        serverLogger.warning("Remove TileSet "+TileSetName
              +" , thread "+str(self.thread)
              +" and id "+str(self.id))
        self.thread.join()
        
    def run(self, TileSetName, Nb):
        # Launch TileSet ??

        self.TileSetName=TileSetName
        self.Nb=Nb

        self.ListClient=[]
        self.ClientNotReady=True
        self.TileJson=[]
        self.TileSetPort=0
        self.laststate=False

        TSthreads[TileSetName]=self.thread
        
        self.lock = threading.Lock()
        global IdTS
        self.lock.acquire()
        IdTS=IdTS+1
        self.id=IdTS-sock.PORTServer
        self.lock.release()
        # detect a free port here
        s=socket.socket()
        s.bind(("", 0))
        self.TileSetPort=int(s.getsockname()[1])
        s.close()

        serverLogger.warning("for TileSet "+TileSetName
              +" TSthreads is modified with thread "+str(self.thread)
              +" and id "+str(self.id))
        serverLogger.warning("Port "+str(self.TileSetPort)+" for TileSet "+TileSetName+".")
        try: 
            self.TSconnect=sock.server(self.TileSetPort)
            TSconnect=self.TSconnect
        except OSError as oserror:
            logging.error("Error with connection to TileSet "+TileSetName+" and PORT "+str(self.TileSetPort)+" : "+str(oserror))
            return False

        count=0
        while count < self.Nb:
            serverLogger.warning( "TileSet "+self.TileSetName
                   +" with "+str(self.Nb)
                   +" tiles id "+str(count+1)
                   +" Listening to clients ...")
            id=count+1
            TSconnect.new_connect(id)
            
            try: 
                while True:
                    data = TSconnect.recv(id)
                    if not data: break
                    # Send back Hello message
                    serverLogger.info("Hello from tile "+data)
                    TSconnect.send_client(id,data)
                    
                    # Get id and password from tile
                    data = TSconnect.recv(id)
                    if not data: break
                    serverLogger.debug("msg password "+data)
                    (container, password) = data.split(':')

                    # Get back error for each send ? 
                    thisTile=TileConnection(TSconnect, TileSetName, id, container, password)
                    self.ListClient.append((thisTile, self, TileSetName, id, container, password))
                    # Get Tile properties + password !!
                    # thisTile.properties()
                    break
            except Exception as err:
                serverLogger.error("Exception with list of tiles : "+str(err))
                traceback.print_exc(file=sys.stderr)
                
            count=count+1

        serverLogger.warning("All socket opened for "+self.TileSetName+" : "+str(len(self.ListClient)))
 
        # Sort clients by container IDs :
        if ( self.Nb > 2 ):
            self.ListClient=sorted(self.ListClient,key=itemgetter(4))

        self.ClientNotReady=False

        serverLogger.warning("All client sorted for %s : %d " % (self.TileSetName,len(self.ListClient)))

    def wait_client(self,callfun,command):
        count=0
        while(self.ClientNotReady):
            serverLogger.debug("Wait for clients. "+callfun)
            time.sleep(waitsleep)
            count=count+1
            if (count > MaxWaitExecute):
                serverLogger.error(self.TileSetName+" : Wait too much on command" +command)
                break
            
    def execute_all(self,command):
        serverLogger.warning(self.TileSetName+" : Command on all tiles : "+command)
        self.wait_client("execute_all",command)
            
        self.laststate=False
        # if (len(self.ListClient) == 0):
        #     self.TSconnect.send_OK(self.id,-1)
        #     serverLogger.error("Error calling execute_all : no client yet.")
        #     return False

        if (TRACE):
            import ipdb; ipdb.set_trace()
        for (client, TSserver, TSName, id, container, password) in self.ListClient:
            client.execute(command)
        self.laststate=True
        
    def get_laststate_execute_all(self):
        serverLogger.warning(self.TileSetName+" : Get state on all tiles.")
        self.wait_client("get_laststate_execute_all","")

        # if (len(self.ListClient) == 0):
        #     self.TSconnect.send_OK(self.id,-1)
        #     serverLogger.error("Error calling get_laststate_execute_all : no client yet.")
        #     return False

        RET=0 
        if (self.laststate):
            for (client, TSserver, TSName, id, container, password) in self.ListClient:
                count=0
                while True:
                    laststate=client.get_laststate()
                    if (type(laststate) == int):
                        RET=RET+laststate
                        break
                    else:
                        time.sleep(1)
                        count=count+1
                        serverLogger.debug(self.TileSetName+" : Wait for state on all tiles %d." % (count))
                        if (count > MaxWaitExecute):
                            serverLogger.error(self.TileSetName+" : No state on all tiles %d." % (count))
                            RET=-1
                            break
            serverLogger.warning(self.TileSetName+" : State on all tiles : "+str(RET))
            return RET
        else:
            return False
        
    def execute_list(self,tilesId,command):
        serverLogger.warning(self.TileSetName+" : Command on list "+str(tilesId)+" of tiles : "+command)
        self.wait_client("execute_list",command)

        self.laststate=False
        # if (len(self.ListClient) == 0):
        #     self.TSconnect.send_OK(self.id,-1)
        #     serverLogger.error("Error calling execute_list : no client yet.")
        #     return False

        if (TRACE):
            import ipdb; ipdb.set_trace()
        try:
            for tileId in tilesId:
                AllTileId=list(filter(lambda x:tileId in x, self.ListClient))
                serverLogger.debug(self.TileSetName+" : execute on "+str(tileId)+" in client : "+str(AllTileId))
                if (len(AllTileId) == 1):
                    (client, TSserv, TSName, id, container, password)=AllTileId[0]
                    client.execute(command)
                else:
                    serverLogger.error("Error with list "+str(tileId)+" of tiles : "+str(AllTileId))
                    serverLogger.error("tileId %s AllTileId %s ListClient : %s " % (str(tileId),str(AllTileId),str(self.ListClient)))
            self.laststate=True
        except Exception as err:
            self.TSconnect.send_OK(self.id,-9)
            serverLogger.error("Exception with list of tiles : "+str(err))
            

    def get_laststate_execute_list(self,tilesId):
        serverLogger.warning(self.TileSetName+" : Get state on list "+str(tilesId)+" of tiles.")
        self.wait_client("get_laststate_execute_list","")

        # if (len(self.ListClient) == 0):
        #     self.TSconnect.send_OK(self.id,-1)
        #     serverLogger.error("Error calling get_laststate_execute_list : no client yet.")
        #     return False
        
        if (TRACE):
            import ipdb; ipdb.set_trace()
        RET=0 
        if (self.laststate):
            for tileId in tilesId:
                AllTileId=list(filter(lambda x:tileId in x, self.ListClient))
                serverLogger.debug(self.TileSetName+" : laststate on "+str(tileId)+" in client : "+str(AllTileId))
                if (len(AllTileId) == 1):
                    (client, TSserv, TSName, id, container, password)=AllTileId[0]
                    count=0
                    while True:
                        laststate=client.get_laststate()
                        if (type(laststate) == int):
                            RET=RET+laststate
                            break
                        else:
                            time.sleep(1)
                            count=count+1
                            serverLogger.debug(self.TileSetName+" : Wait for state on list "+str(tilesId)+" of tiles %d." % (count))
                            if (count > MaxWaitExecute):
                                serverLogger.error(self.TileSetName+" : No state on list "+str(tilesId)+" of tiles %d." % (count))
                                RET=-1
                                break
                else:
                    return False
            serverLogger.warning(self.TileSetName+" : State on list "+str(tilesId)+" of tiles : "+str(RET))
            return RET
        else:
            return False


# class for each ClientId instance (multiple client connections).
class ClientConnect(threading.Thread):
    def __init__(self, id, Connect):
        threading.Thread.__init__(self)
        self.thread = threading.Thread(target=self.run, args=(id, Connect),)
        self.thread.start()

    def __del__(self):
        serverLogger.warning("Remove ClientConnect "
              +" , thread "+str(self.thread)
              +" and id "+str(self.id))
        self.close()
        self.thread.join()

    def run(self, id, connect):
        self.id=id
        self.Connect=Connect
        # One client can have many tilesets.
        self.TileSets = {}

        serverLogger.warning("Listen to connection socket to send commands to tiles")
        while True:
            serverLogger.debug("Wait for command in server run.")
            data = self.Connect.recv(self.id)
    
            if not data: break
            CommandRecv=data
            if (re.search(r'create TS',CommandRecv)):
                p=re.compile(r'create TS=(\w*) Nb=([0-9]*)')
                TSName=p.sub(r'\1',CommandRecv)
                self.Nb=int(p.sub(r'\2',CommandRecv))
                serverLogger.warning("Create TileSet "+TSName+" with "+str(self.Nb)+" tiles.")
                TS = TilesSet(TSName,self.Nb)
                self.TileSets[TSName]=TS
            
                # TODO : give password to connection after create TS
            
            elif (re.search(r'remove TS',CommandRecv)):
                p=re.compile(r'remove TS=(\w*)')
                TSName=p.sub(r'\1',CommandRecv)
                serverLogger.warning('Receive remove command for TileSet "'+TSName+'".')
                outHandler.flush()
                
                del self.TileSets[TSName]
                self.__del__()
                
            elif (re.search(r'execute all',CommandRecv)):
                p=re.compile(r'execute all (.*)')
                serverLogger.warning('Execute all TileSets command "'+CommandTS+'"')
                
                for TheTS in self.TileSets:
                    CommandTS=p.sub(r'\1',CommandRecv)
                    serverLogger.debug('Execute all command on tileset '+TheTS)
                    TheTS.execute_all(CommandTS)

                RET=0
                for TheTS in self.TileSets:
                    count=0
                    while True:
                        laststate=TheTS.get_laststate_execute_all()
                        if (type(laststate) == int):
                            RET=RET+laststate
                            break
                        else:
                            time.sleep(1)
                            count=count+1
                            serverLogger.debug(str(TheTS)+" : Wait for state on list command "+CommandRecv+" %d." % (count))
                            if (count > MaxWaitExecute):
                                CommandTS=p.sub(r'\1',CommandRecv)
                                serverLogger.error(str(TheTS)+" : No state on list command "+CommandRecv+"\n"+
                                                   "command send "+CommandTS+" %d." % (count))
                                RET=-1
                                break
                    serverLogger.debug(str(TheTS)+" : Get state on list command "+CommandRecv+" %d." % (RET))
                serverLogger.debug(str(TheTS)+" : Get Send OK for command "+CommandRecv+" %d." % (RET))
                self.Connect.send_OK(self.id,RET)

            elif (re.search(r'execute TS',CommandRecv)):
                p0=re.compile(r'execute TS=(\w*) (.*)')
                TSName=p0.sub(r'\1',CommandRecv)
                CommandTS=p0.sub(r'\2',CommandRecv)
                p=re.compile(r"Tiles=[(\[]([0-9, ']*)[)\]] (.*)")

                if (re.match(p,CommandTS)):
                    StrTiles=p.sub(r'\1',CommandTS)
                    # ListStrTiles=StrTiles.split(', ')
                    # serverLogger.debug('ListTiles '+str(ListStrTiles))
                    # ListTiles=list(map(int, ListStrTiles))
                    ListTiles=list(map(lambda x:x.replace("'",""), StrTiles.split(', ')))
                    serverLogger.warning('Execute command "'+CommandTS+'" on tileset '+TSName+' on list '+str(ListTiles))
                    CommandTile=p.sub(r'\2',CommandTS)
                    self.TileSets[TSName].execute_list(ListTiles,CommandTile)
                
                    serverLogger.debug('Get laststate on list '+str(ListTiles))
                    RET=0
                    count=0
                    while True:
                        laststate=self.TileSets[TSName].get_laststate_execute_list(ListTiles)
                        serverLogger.debug('laststate for '+TSName+' is '+str(laststate))
                        if (type(laststate) == int):
                            RET=RET+laststate
                            break
                        else:
                            time.sleep(1)
                            count=count+1
                            serverLogger.debug(TSName+" : Wait for state on list command "+CommandRecv+" %d." % (count))
                            if (count > MaxWaitExecute):
                                serverLogger.error(TSName+" : No state "+str(laststate)+" on list command "+CommandRecv+"\n"+
                                                   "CommandTS "+CommandTS+"  StrTiles "+str(StrTiles)+" \n"+
                                                   " %d." % (count))
                                RET=-1
                                break
                    serverLogger.debug(TSName+" : Get state on list command "+CommandRecv+" %d." % (RET))
                else:
                    serverLogger.warning('Execute all command "'+CommandTS+'" on tileset '+TSName)
                    try:
                        self.TileSets[TSName].execute_all(CommandTS)

                        RET=0
                        count=0
                        while True:
                            laststate=self.TileSets[TSName].get_laststate_execute_all()
                            serverLogger.debug('laststate for '+TSName+' is '+str(laststate))
                            if (type(laststate) == int):
                                RET=RET+laststate
                                break
                            else:
                                time.sleep(1)
                                count=count+1
                                serverLogger.debug(TSName+" : Wait for state on all command "+CommandRecv+" %d." % (count))
                                if (count > MaxWaitExecute):
                                    serverLogger.error(TSName+" : No state on all command "+CommandRecv+"\n"+
                                                       "CommandTS "+CommandTS+"\n"+
                                                       " %d." % (count))
                                    RET=-1
                                    break
                        serverLogger.debug(TSName+" : Get state on all command "+CommandRecv+" %d." % (RET))
                    except KeyError as err:
                        serverLogger.error("KeyError exception "+str(err)+"\n for "+TSName+" tileset and command :\n"+CommandTS)
                        RET=255
                        continue
                serverLogger.debug(TSName+" : Send OK for command "+CommandRecv+" %d." % (RET))
                self.Connect.send_OK(self.id,RET)

            elif (re.search(r'launch TS',CommandRecv)):
                p=re.compile(r'launch TS=(\w*) (.*)')
                TSName=p.sub(r'\1',CommandRecv)
                CommandTS=p.sub(r'\2',CommandRecv)
                serverLogger.warning('Launch on tileset "'+TSName+'" and command "'+CommandTS+'"')

                p=re.compile(r'([^ ]*) (.*)')
                CommandPATH=p.sub(r'\1',CommandTS)
                CommandEXE=p.sub(r'\2',CommandTS)
                
                # Give the connection PORT to server
                if (re.search(r'TileSetPort',CommandEXE)):
                    CommandEXE=CommandEXE.replace('TileSetPort',str(self.TileSets[TSName].TileSetPort))
                    serverLogger.warning('Change TileSetPort on tileset "'+TSName+'" and command "'+CommandEXE+'"')

                # TEST command and path validity ??
                serverLogger.info('Launch command "'+CommandEXE+'" with path "'+CommandPATH+'" on tileset '+TSName)
                args='cd '+CommandPATH+'; bash -vxc '+shlex.quote(CommandEXE)
                p=subp.Popen(args, shell=True,stdout=subp.PIPE,stderr=subp.PIPE)
                output, errors = p.communicate()
                #serverLogger.warning(output.decode('utf-8'))
                if (len(errors) >0):
                    serverLogger.info("stderr : "+errors.decode('utf-8'))
                
                self.Connect.send_OK(self.id,p.returncode)

            elif (re.search(r'putfile TS',CommandRecv)):
                p=re.compile(r'putfile TS=(\w*) (.*)')
                TSName=p.sub(r'\1',CommandRecv)
                FileInfos=p.sub(r'\2',CommandRecv)

                p=re.compile(r'([^ ]*) ([^ ]*) ([0-9]*) ([a-z0-9]*)')
                CommandPath=p.sub(r'\1',FileInfos)
                CommandFilename=p.sub(r'\2',FileInfos)
                CommandSize=p.sub(r'\3',FileInfos)
                CommandSha256=p.sub(r'\4',FileInfos)

                serverLogger.warning('Put file for tileset "'+TSName+'" : '+CommandFilename)

                serverLogger.info('Put file in path "'+CommandPath+' with filename '+CommandFilename+' and size '+CommandSize+' MD5sum : '+CommandSha256)
                self.Connect.send_OK(self.id,0)

                self.Connect.get_file(self.id,CommandPath,CommandFilename,int(CommandSize),CommandSha256)

            elif (re.search(r'askfile TS',CommandRecv)):
                p=re.compile(r'askfile TS=(\w*) (.*)')
                TSName=p.sub(r'\1',CommandRecv)
                FileInfos=p.sub(r'\2',CommandRecv)

                p=re.compile(r'([^ ]*) (.*)')
                CommandPath=p.sub(r'\1',FileInfos)
                CommandFilename=p.sub(r'\2',FileInfos)

                serverLogger.warning('Ask for a file from server on tileset "%s" and file name "%s" in path "%s" ' %\
                                     (TSName,CommandFilename,CommandPath))

                (FileSize, FileSha256) = self.Connect.send_file(self.id,CommandPath,CommandFilename)
                serverLogger.warning('File sent with size %d and sha256 %s ' % (FileSize,FileSha256))
                
            else:
                serverLogger.error("*********** UNRECOGNIZED COMMAND FROM CLIENT "+str(self.Connect.clientinfos[self.id])+" *********** :")
                serverLogger.error(CommandRecv)

    def close(self):
        self.Connect.close(self.id)


if __name__ == '__main__':
    args = parse_args(sys.argv)

    DEBUG=args.debug
    if (DEBUG):
        logging.warning("TileServer with debug mode on.")
    TRACE=args.trace
    if (TRACE):
        logging.warning("TileServer with trace mode on.")
    IdTS=args.idts
    MaxWaitExecute=args.maxwaitexecute

    #logging.basicConfig(level=logging.WARNING)
    serverLogger = logging.getLogger("Server")
    logFormatter = logging.Formatter("\n%(asctime)s - Server - %(threadName)s - %(levelname)s: %(message)s ")
    #serverLogger.setLevel(logging.ERROR)
    if (DEBUG):
        serverLogger.setLevel(logging.DEBUG)
    else:
        serverLogger.setLevel(logging.WARNING)
    #serverLogger.setLevel(logging.INFO)
    outHandler = logging.StreamHandler(sys.stdout)
    outHandler.setFormatter(logFormatter)
    serverLogger.addHandler(outHandler)

    serverLogger.info ("Launch TiledViz server on "+os.getenv("HOSTNAME"))

    Connect=sock.server(sock.PORTServer)

    ClientId=0
    Clients=[]

    while True:
        serverLogger.warning( "Listening to connection from TiledViz ...")
        Connect.new_connect(ClientId)
            
        while True:
            data = Connect.recv(ClientId)
            if not data: break
            serverLogger.info("Hello from connection "+data)
            serverLogger.warning("New client num "+str(ClientId))
            # Send back Hello message
            Connect.send_client(ClientId,data)
            thisclient=ClientConnect(ClientId,Connect)
            ClientId=ClientId+1
            Clients.append(thisclient)
            break 


    Connect.close_all()
