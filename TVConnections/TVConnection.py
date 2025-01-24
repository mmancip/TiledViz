#!/bin/env python3

import datetime,time
import argparse

import sys,os,traceback
import pexpect,re
import platform
import configparser
import threading
import pickle

import code
import IPython
from IPython.terminal.embed import InteractiveShellEmbed

from traitlets.config import get_config

from getpass import getpass

import logging

import inspect

Home=os.environ['HOME']
user=os.environ["USER"]
TiledVizPath='/TiledViz'

TilesScriptsPath='/opt'


sys.path.append(os.path.abspath(TiledVizPath+'/TVDatabase'))
from TVDb import tvdb
from TVDb import models

# Add connect module directory
sys.path.append(os.path.realpath(TiledVizPath+'/TVConnections/'))
from connect import sock
from connect.transfer import send_file_server, get_file_client

# Read TiledViz config
TVrunDir=Home+'/.tiledviz'
TVconf=TVrunDir+"/tiledviz.conf"

config = configparser.ConfigParser()
config.optionxform = str
config.read(TVconf)
ActionPort=int(config['TVSecure']['ActionPort'])

# Default port for connection between client in sock.py and TVSecure.py 
#PORTServer=int(config['sock']['PORTServer'])

# Message fix size for data transfert through socket
MSGsize=int(config['sock']['MSGsize'])

# Usefull fuction for debugging CASE script:
def cat_between(b,e,f):
    os.system('/cat_between %d %d %s' % ( b, e, f))

def containerId(num):
    return '{:03d}'.format(num)

def parse_args(argv):
    parser = argparse.ArgumentParser(
        'From a connection Id in PostgreSQL DB get connection parameters from TiledViz database.')
    parser.add_argument('--host', default='localhost',
                        help='Database host (default: localhost)')
    parser.add_argument('--port', default='6431',
                        help='Port (default: 6431)')
    parser.add_argument('-l', '--login', default='tiledviz',
                        help='Database login (default: tiledviz)')
    parser.add_argument('-n', '--databasename', default='TiledViz',
                        help='Database name (default: TiledViz)')
    parser.add_argument('-u', '--usertest', default='ddurandi',
                        help='User name for test (default: ddurandi)')
    parser.add_argument('-c', '--connectionId', 
                        help='Connection Id in DB.')
    parser.add_argument('--debug', action='store_true',
                        help='Debug switch for new job.',default=False)

    args = parser.parse_args(argv[1:])
    return args



class ClientAction(threading.Thread):
    
    def __init__(self,connectionId,globals,locals):
        threading.Thread.__init__(self)
        self.thread = threading.Thread(target=self.run,args=(connectionId,globals,locals,)).start()

    def run(self,connectionId,globals,locals):
        global tiles_actions
        tiles_actions["action0"]=["get_new_nodes","system_update_alt"]

        try:
            self.actionclient=sock.client(ActionPort)
            self.actionclient.send_OK(1)
            logging.warning("ClientAction : connect server connectiondock")
        except:
            logging.error("ClientAction : can't connect to server connectiondock")
            traceback.print_exc(file=sys.stderr)
            
        self.iter=0
        # Wait for commands by TVSecure.py
        while True:
            detectActionConnection=self.detect()
            if (detectActionConnection):
                self.execute(globals,locals)
            elif (detectActionConnection == -1):
                return
            time.sleep(0.1)
            if (self.iter > 100):
                logging.error("No ActionServer detected after 100 tries.")
                return

    def detect(self):
        global tiles_actions
        self.IsActionConnected=False
        self.iter=self.iter+1
        #logging.warning("ClientAction : detect")
        if ("actionclient" in dir(self)):
            data=self.actionclient.recv()
            if not data:
                return False
        else:
            # No ActionConnection server
            logging.error("ClientAction : No more Action connection to server connectiondock")
            return -1
        self.actionclient.send_OK(self.iter)
        self.IsActionConnected=True

        try:
            actiontiles=list(map(int,data.replace(',,','').split(",")))
            logging.warning("ClientAction : get actionTile message "+str(actiontiles))
            actionId=actiontiles.pop(0)
        except:
            logging.warning("ClientAction : not an action "+data)
            return False
        # test if it is a valid action command
        self.thisAction="action"+str(actionId)
        if (self.thisAction in tiles_actions):
            self.isSelection=False
            if (len(actiontiles) > 0):
                self.isSelection=True
                try:
                    self.thisSelection=list(map(int,actiontiles))
                    logging.debug("ClientAction : detect a valid selection "+str(self.thisSelection))
                except:
                    return False
            else:
                logging.warning("ClientAction : detect a global action ")
            return True
        else: 
            logging.error("ClientAction : error reading "+self.thisAction)
            self.isSelection=False
            return False
        
    def execute(self,globals,locals):
        # Separate Execute
        logging.debug("ClientAction : run")
        if (not self.IsActionConnected):
            return
        try:
            funaction=tiles_actions[self.thisAction][0]
            functionAction=eval(funaction)
            search_tileNum=inspect.signature(functionAction).parameters
            logging.debug("ClientAction : "+funaction+" parameters :"+str(search_tileNum))
            if ("tileNum" in search_tileNum):
                if (self.isSelection):
                    for num in self.thisSelection:
                        action=funaction+"(tileNum="+str(num)+")"
                        logging.warning("ClientAction : send action "+action)
                        eval(action,globals,locals)
                else:
                    logging.warning("ClientAction : Apply this action "+funaction+" on all tiles.")
                    for num in range(NUM_DOCKERS):
                        action=funaction+"(tileNum="+str(num)+")"
                        logging.warning("ClientAction : send action "+action)
                        eval(action,globals,locals)
            else: 
                action=funaction+"()"
                logging.warning("ClientAction : No tile for this action "+action)
                eval(action,globals,locals)
            logging.warning("ClientAction : action "+action+" launched.")
        except:
            traceback.print_exc(file=sys.stderr)
            logging.warning("ClientAction : problem with action "+funaction+" launch.")
            pass

### Functions used in case job ###

# Those functions must be overlap in CASE job script for specific request.

# Launch dockers
def Run_dockers():
    COMMAND="bash -c \""+os.path.join(TILEDOCKERS_path,"launch_dockers")+" "+REF_CAS+" "+GPU_FILE+" "+SSH_FRONTEND+":"+SSH_IP+\
             " "+network+" "+nethost+" "+domain+" "+init_IP+" TileSetPort "+UserFront+"@"+Frontend+" "+OPTIONS+\
             " > "+os.path.join(JOBPath,"output_launch")+" 2>&1 \"" 
    logging.warning("\nCommand dockers : "+COMMAND)
    client.send_server(LaunchTS+' '+COMMAND)
    state=client.get_OK()
    logging.warning("Out of launch docker : "+ str(state))
    sys.stdout.flush()
    stateVM=(state == 0)
    return stateVM

# Build nodes.json file from new dockers list
def build_nodes_file():
    logging.warning("Build nodes.json file from new dockers list.")
    COMMAND=LaunchTS+' ./build_nodes_file '+os.path.join(JOBPath,CASE_config)+' '+os.path.join(JOBPath,SITE_config)+' '+TileSet
    logging.warning("\nCommand dockers : "+COMMAND)
    client.send_server(COMMAND)
    state=client.get_OK()
    logging.warning("Out of build_nodes_file : "+ str(state))
    time.sleep(2)
    stateVM=(state == 0)
    state=launch_nodes_json()
    stateVM=stateVM and (state == 0)
    os.system("mv nodes.json nodes.json_init")
    return stateVM

def replaceconf(x):
    if (re.search('}',x)):
        varname=x.replace("{","").replace("}","")
        return config['CASE'][varname]
    else:
        return x
        
def kill_all_containers():
    stateVM=True
    client.send_server(LaunchTS+" "+COMMANDStop)
    print("Out of COMMANDStop.")
    # state=client.get_OK()
    # print("Out of COMMANDStop : "+ str(state))
    # stateVM=(state == 0)
    # client.send_server(ExecuteTS+' killall -9 Xvfb')
    # state=client.get_OK()
    # print("Out of killall command : "+ str(state))
    time.sleep(2)
    Remove_TileSet()
    return stateVM
        
# return the IP of a client tileNum or tileId
def Get_client_IP(tileNum=-1,tileId='001'):
    if ( tileNum > -1 ):
        TilesStr=' Tiles=('+containerId(tileNum+1)+') '
        Id=containerId(tileNum+1)
    else:
        TilesStr=' Tiles=('+tileId+') '
        Id=tileId
    fileIP='IP_'+Id
    client.send_server(ExecuteTS+TilesStr+
                       'bash -c "/usr/local/bin/get_ip.sh;' +
                       'scp .vnc/myip '+HTTP_LOGIN+'@'+HTTP_FRONTEND+':'+JOBPath+'/'+fileIP+'"')
    logging.debug("Out of get %s ip : %s " % ( Id,str(client.get_OK()) ))
    get_file_client(client,TileSet,JOBPath,fileIP,".")
    # while( get_file_client(client,TileSet,JOBPath,"serverip",".") < 0):
    #     time.sleep(1)
    #     pass
    try:
        with open(fileIP,'r') as fip:
            IP=fip.read().replace(domain+'.',"").replace("\n","")
            logging.warning("%s ip : "+domain+'.'+IP)
            sys.stdout.flush()
            return IP
    except:
        logging.error("Cannot retreive ip from %s." % (Id) )
        return "-1"

def read_nodes_init():
    # Update nodes.json locally
    JsonFile="nodes.json_init"
    logging.warning("Before read  : "+ str(JsonFile))
    try:
        with open(JsonFile) as json_tiles_file:
            nodes_json=json.loads(json_tiles_file.read())
    except:
        sys.stdout.flush()
        traceback.print_exc(file=sys.stdout)
        os.system('ls -la '+JsonFile)
        kill_all_containers()
    return nodes_json

def nodes_json_init():
    with open("listPortsTiles.pickle", 'rb') as file_pi:
        listPortsTilesIE=pickle.load(file_pi)

    nodes_json=read_nodes_init()
    
    for tilei in range(NUM_DOCKERS):
        nodeurl=nodes_json["nodes"][tilei]["url"]
        nodeurl=re.sub(r'https://[^/]*',r'https://'+listPortsTilesIE["TiledVizHost"],nodeurl)
        nodeurl=re.sub(r'host=[^&]*',r'host='+listPortsTilesIE["TiledVizHost"],nodeurl)
        oldport=int(re.sub(r'.*port=([^&]*)&.*',r'\1',nodeurl))
        tileip=oldport % 1000 - 1
        #logging.warning("tile %d update nodes.json : new url %s with old port %d" % (tilei, nodeurl, oldport)) 
        if ( str(tileip) in listPortsTilesIE):
            extern=listPortsTilesIE[str(tileip)][1]
            nodes_json["nodes"][tilei]["url"]=re.sub(r'port=[^&]*',r'port='+str(extern),nodeurl)
            logging.warning("tile %d : new url %s" % (tilei,nodes_json["nodes"][tilei]["url"])) 
        sys.stdout.flush()
    logging.warning("Before write nodes.json")
    with open("nodes.json",'w') as nodesf:
        nodesf.write(json.dumps(nodes_json))
    return True

# share ssh key for each docker
def share_ssh_key_docker():
    # Share ssh connection keys whith tiles
    stateVM=True
    # TODO : secure that action ?
    totbyte=0
    filesize=os.path.getsize(sshKeyPath)
    connectionkey=os.path.join(Home,".ssh/id_rsa_connection")
    os.system("cp "+sshKeyPath+".pub "+os.path.join(Home,".ssh/authorized_keys"))
    packet_id_length=MSGsize-200
    with open(sshKeyPath,'rb') as privatek:
        l = '\\\"'+str(privatek.read(packet_id_length).replace(b"\n",b""),"utf-8")+'\\\"'
        COMMANDid=ExecuteTS+' bash -c "echo '+l+' > '+connectionkey+'; chmod 600 '+connectionkey+'"'
        logging.warning("Send id_rsa with %s." % (COMMANDid) )
        client.send_server(COMMANDid)
        state=client.get_OK()
        stateVM=stateVM and (state == 0)
        while (l):
            totbyte=totbyte+packet_id_length
            rest=filesize-totbyte;
            if (rest > packet_id_length ):
                l = '\\\"'+str(privatek.read(packet_id_length).replace(b"\n",b""),"utf-8")+'\\\"'
                COMMANDid=ExecuteTS+' bash -c "echo '+l+' >> '+connectionkey+'"'
                logging.warning("Send id_rsa with %s." % (COMMANDid) )
                client.send_server(COMMANDid)
                state=client.get_OK()
                stateVM=stateVM and (state == 0)
            else:
                if (rest > 0):
                    l = '\\\"'+str(privatek.read(rest).replace(b"\n",b""),"utf-8")+'\\\"'
                    COMMANDid=ExecuteTS+' bash -c "echo '+l+' >> '+connectionkey+'"'
                    logging.warning("Send id_rsa with %s." % (COMMANDid) )
                    client.send_server(COMMANDid)
                    state=client.get_OK()
                    stateVM=stateVM and (state == 0)
                break
    logging.warning("Out of id_rsa : "+ str(stateVM))
    COMMANDid=ExecuteTS+' bash -c "sed -e \\\"s&KEY-----&KEY-----\\\\n&\\\" -e \\\"s&-----END&\\\\n-----END&\\\" -i '+connectionkey+'"'
    logging.warning("Send id_rsa with %s." % (COMMANDid) )
    client.send_server(COMMANDid)
    state=client.get_OK()
    stateVM=stateVM and (state == 0)
    with open(sshKeyPath+'.pub','rb') as publick:
        l = '\\\"'+str(publick.read().replace(b"\n",b""),"utf-8")+'\\\"'
        COMMANDid=ExecuteTS+' bash -c "echo '+l+' > '+connectionkey+'.pub"'
        logging.warning("Send id_rsa.pub with %s." % (COMMANDid) )
        client.send_server(COMMANDid)
        state=client.get_OK()
        stateVM=stateVM and (state == 0)
    logging.warning("Out of id_rsa.pub : "+ str(stateVM))
    if (not stateVM):
        logging.error("!! Error send id_rsa.!!")
    return stateVM

# share ssh key on home for singularity
def share_ssh_key_singularity():
    stateVM=True

    # Share ssh connection keys whith tiles
    connectionkey=os.path.join(HomeFront,".ssh/id_rsa_connection")
    os.system("cp "+sshKeyPath+".pub "+os.path.join(Home,".ssh/authorized_keys"))
    send_file_server(client,TileSet,os.path.join(Home,".ssh"), "id_rsa_"+Frontend, JOBPath)
    COMMANDid=LaunchTS+' bash -c "mv '+os.path.join(JOBPath,"id_rsa_"+Frontend)+' '+connectionkey+'; chmod 600 '+connectionkey+'"'
    logging.warning("Send id_rsa with \"%s\"." % (COMMANDid) )
    client.send_server(COMMANDid)
    state=client.get_OK()
    stateVM=stateVM and (state == 0)

    send_file_server(client,TileSet,os.path.join(Home,".ssh"), "id_rsa_"+Frontend+".pub", JOBPath)
    COMMANDid=LaunchTS+' bash -c "mv '+os.path.join(JOBPath,"id_rsa_"+Frontend+".pub")+' '+connectionkey+".pub"+'; chmod 666 '+connectionkey+".pub"+'"'
    logging.warning("Send id_rsa with \"%s\"." % (COMMANDid) )
    client.send_server(COMMANDid)
    state=client.get_OK()
    stateVM=stateVM and (state == 0)
    logging.warning("Out of id_rsa.pub : "+ str(stateVM))
    if (not stateVM):
        logging.error("!! Error send id_rsa.!!")
    return stateVM

share_ssh_key=share_ssh_key_docker

# commande de tunnel :
def launch_tunnel_docker():
    global TilesScriptsPath
    logging.warning("TilesScriptsPath : %s" % (TilesScriptsPath))
    stateVM=True
    
    connectionkey="/home/myuser/.ssh/id_rsa_connection"

    with open("listPortsTiles.pickle", 'rb') as file_pi:
        listPortsTilesIE=pickle.load(file_pi)
    # Call tunnel for VNC
    for i in range(NUM_DOCKERS):
        i0="%0.3d" % (i+1)
        TILEi=ExecuteTS+' Tiles=('+containerId(i+1)+') '
        internPort=listPortsTilesIE[str(i)][0]
        WebServerHost=listPortsTilesIE["TiledVizHost"]
        ServerTSPortSSH=listPortsTilesIE["TiledVizConnectionPort"]
        COMMANDi=' ssh-agent '+TilesScriptsPath+'/tunnel_ssh '+SSH_FRONTEND+' '+SSH_LOGIN+' '+str(internPort)+' '+WebServerHost+' '+str(ServerTSPortSSH)+' -i '+connectionkey
        client.send_server(TILEi+COMMANDi)
        state=client.get_OK()
        logging.warning("%s | %s : %s" % (TILEi, COMMANDi,state)) 
        stateVM=stateVM and (state == 0)
    if (not stateVM):
        print("!! Error launch_tunnel.!!")
        return stateVM
    sys.stdout.flush()

    logging.warning("Out of tunnel_ssh : "+ str(stateVM))
    return stateVM

# Launch singularity tunnels
def launch_tunnel_singularity():
    global TilesScriptsPath
    logging.warning("Singularity TilesScriptsPath : %s" % (TilesScriptsPath))
    logging.warning("Frontend Home in anatomist_job: "+HomeFront)
    stateVM=True

    connectionkey=os.path.join(HomeFront,".ssh/id_rsa_connection")
    
    with open("listPortsTiles.pickle", 'rb') as file_pi:
        listPortsTilesIE=pickle.load(file_pi)
    # Call tunnel for VNC
    for i in range(NUM_DOCKERS):
        i0="%0.3d" % (i+1)
        TILEi=ExecuteTS+' Tiles=('+containerId(i+1)+') '
        internPort=listPortsTilesIE[str(i)][0]
        WebServerHost=listPortsTilesIE["TiledVizHost"]
        ServerTSPortSSH=listPortsTilesIE["TiledVizConnectionPort"]
        #COMMANDi=' '+TilesScriptsPath+'/tunnel_ssh '+SSH_FRONTEND+' '+SSH_LOGIN+' '+str(internPort)+' '+WebServerHost+' '+str(ServerTSPortSSH)+' -i '+connectionkey
        #COMMANDi=' ssh-agent '+TilesScriptsPath+'/tunnel_ssh '+SSH_FRONTEND+' '+SSH_LOGIN+' '+str(internPort)+' '+WebServerHost+' '+str(ServerTSPortSSH)+' -i '+connectionkey
        COMMANDi=" nohup bash -c ' ssh-agent "+TilesScriptsPath+'/tunnel_ssh '+SSH_FRONTEND+' '+SSH_LOGIN+' '+str(internPort)+' '+WebServerHost+' '+str(ServerTSPortSSH)+' -i '+connectionkey+" '&"
        client.send_server(TILEi+COMMANDi)
        state=client.get_OK()
        logging.warning("%s | %s : %s" % (TILEi, COMMANDi,state)) 
        stateVM=stateVM and (state == 0)
    if (not stateVM):
        print("!! Error launch_tunnel.!!")
        return stateVM
    sys.stdout.flush()
    #time.sleep(2)
    
    logging.warning("Out of tunnel_ssh : "+ str(stateVM))
    return stateVM

launch_tunnel=launch_tunnel_docker

def launch_vnc():
    client.send_server(ExecuteTS+' '+TilesScriptsPath+'/vnccommand')
    state=client.get_OK()
    logging.warning("Out of vnccommand : "+ str(state))
    stateVM=(state == 0)
    return stateVM


def init_wmctrl():
    client.send_server(ExecuteTS+' wmctrl -l -G')
    state=client.get_OK()
    logging.warning("Out of wmctrl : "+ str(state))
    stateVM=(state == 0)
    return stateVM

    
def clear_vnc(tileNum=-1,tileId='001'):
    if ( tileNum > -1 ):
        TilesStr=' Tiles=('+containerId(tileNum+1)+') '
    else:
        TilesStr=' Tiles=('+tileId+') '
    client.send_server(ExecuteTS+TilesStr+' x11vnc -R clear-all')
    state=client.get_OK()
    logging.warning("Out of clear-vnc : "+ str(state))
    stateVM=(state == 0)
    return stateVM


def clear_vnc_all():
    os.system('x11vnc -R clear-all')
    stateVM=True
    for i in range(NUM_DOCKERS):
        stateVM=stateVM and clear_vnc(i)
        #clear_vnc(tileId=containerId(i))
    return stateVM

def changeSize(RESOL="1920x1080",tileNum=-1,tileId='001'):
    if ( tileNum > -1 ):
        TilesStr=' Tiles=('+containerId(tileNum+1)+') '
    else:
        TilesStr=' Tiles=('+tileId+') '
    COMMAND=ExecuteTS+TilesStr+' xrandr --fb '+RESOL
    logging.warning("call server with : "+COMMAND)
    client.send_server(COMMAND)
    state=client.get_OK()
    logging.warning("server answer is "+str(state))
    stateVM=(state == 0)
    return stateVM

def all_resize(RESOL="1280x800"): #"1440x900"
    client.send_server(ExecuteTS+' bash -c "export DISPLAY=:1; xrandr --fb '+RESOL+'"')
    state=client.get_OK()
    logging.warning("Out of xrandr : "+ str(state))
    stateVM=(state == 0)
    return stateVM

# def fullscreenThisApp(App="xterm",tileNum=-1,tileId='001'):
#     COMMAND=TilesScriptsPath+'/movewindows '+App+' -b toggle,fullscreen'
#     if ( tileNum > -1 ):
#         TilesStr=' Tiles=('+containerId(tileNum+1)+') '            
#     else:
#         TilesStr=' Tiles=('+tileId+') '
#     client.send_server(ExecuteTS+TilesStr+COMMAND)
#     client.get_OK()

App="N/A"
def fullscreenApp(windowname=App,tileNum=-1,tileId='001'):
    if ( tileNum > -1 ):
        stateVM=movewindows(windowname=windowname,wmctrl_option='toggle,fullscreen',tileNum=tileNum)
    else:
        stateVM=movewindows(windowname=windowname,wmctrl_option='toggle,fullscreen',tileId=tileId)
    return stateVM
    
def movewindows(windowname=App,wmctrl_option='toggle,fullscreen',tileNum=-1,tileId='001'):
    COMMAND=TilesScriptsPath+'/movewindows '+windowname+' -b '+wmctrl_option
    #remove,maximized_vert,maximized_horz
    #toggle,above
    if ( tileNum > -1 ):
        TilesStr=' Tiles=('+containerId(tileNum+1)+') '
    else:
        TilesStr=' Tiles=('+tileId+') '
    client.send_server(ExecuteTS+TilesStr+COMMAND)
    state=client.get_OK()
    stateVM=(state == 0)
    return stateVM
    
def showThisGUI(App="xterm",tileNum=-1,tileId='001'):
    COMMAND=TilesScriptsPath+'/movewindows '+App+' -b toggle,above'
    if ( tileNum > -1 ):
        TilesStr=' Tiles=('+containerId(tileNum+1)+') '            
    else:
        TilesStr=' Tiles=('+tileId+') '
    client.send_server(ExecuteTS+TilesStr+COMMAND)
    state=client.get_OK()
    stateVM=(state == 0)
    return stateVM

def click_point(tileNum=-1,tileId='001',X=0,Y=0):
    if ( tileNum > -1 ):
        TilesStr=' Tiles=('+containerId(tileNum+1)+') '
    else:
        TilesStr=' Tiles=('+tileId+') '
    COMMAND=" xdotool mousemove "+str(X)+" "+str(Y)+" click 1 mousemove restore"
    # -> xdotool getmouselocation
    client.send_server(ExecuteTS+TilesStr+COMMAND)
    state=client.get_OK()
    logging.warning("Out of click_point : "+ str(state))
    stateVM=(state == 0)
    return stateVM

        
if __name__ == '__main__':
    args = parse_args(sys.argv)

    logFormatter = logging.Formatter("TVConnection %(asctime)s - %(threadName)s - %(levelname)s: %(message)s ")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.WARNING)
    fileHandler = logging.FileHandler(Home+"/.vnc/TVConnection.log")
    fileHandler.setLevel(logging.DEBUG)
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)
    outHandler = logging.StreamHandler(sys.stdout)
    outLevel=logging.DEBUG
    #=logging.WARNING
    outHandler.setLevel(outLevel)
    outHandler.setFormatter(logFormatter)
    rootLogger.addHandler(outHandler)
    #rootLogger.handlers[0].flush()
    #outHandler.flush()
    
    # Connection to DB
    metadata, conn, engine, pool, session = tvdb.SQLconnector(args)
    os.environ["POSTGRES_PASSWORD"]=""
    os.environ["passwordDB"]=""
    connectionId=int(args.connectionId)
    logging.warning("Build connection number "+args.connectionId)
    
    TVconnection=session.query(models.Connection).filter(models.Connection.id == connectionId).one()
    logging.warning("From DB connection informations : "+str((TVconnection.auth_type,TVconnection.host_address,TVconnection.scheduler)))
    TileSetDB=session.query(models.TileSet).filter_by(id_connections=args.connectionId).order_by(models.TileSet.id.desc()).first()
    TileSet=TileSetDB.name
    
    # Default values for TileSet
    CreateTS='create TS='+TileSet+' Nb='+str(1)

    # Execute on each/a set of tiles
    ExecuteTS='execute TS='+TileSet+" "
    # Launch a command on the frontend
    LaunchTS='launch TS='+TileSet+" ."

    def Remove_TileSet():
        # Remove TileSet in TileServer
        RemoveTS='remove TS='+TileSet
        client.send_server(RemoveTS)
        logging.warning("TileSet "+TileSet+" removed on server")
    
    # User not used
    TVuser=session.query(models.User).filter(models.User.id==TVconnection.id_users).first().name

    session.close()

    NbFrontendTo=0
    NbFrontendFrom=0
    # choices=[("ssh","Direct ssh connection"),
    #          ("rebound","ssh through a gateway"),
    #          ("persistent","define ssh connection an save it.")
    if (TVconnection.auth_type == "rebound"):
        NbFrontendTo = input("Give the number of frontends to go to the HPC frontend (0 if direct connectio) :")
        NbFrontendFrom = input("Give the number of gateways to go back from HPC nodes to the Flask server (1 if they need to rebound from the HPC frontend) :")
    NOT_CONNECTED=True
    OK_Key=False
    while NOT_CONNECTED:

        if (TVconnection.auth_type == "rebound"):
            #TODO
            pass
        elif (TVconnection.auth_type == "ssh"):
            Frontend = TVconnection.host_address
            logging.warning("Distant machine frontend : "+Frontend)
            while True:
                try:
                    UserFront = input("Enter your distant machine user name \n")
                    UserFront = UserFront.encode('ascii').decode()
                    break
                except UnicodeDecodeError:
                    logging.error("Error : only ascii chars are available.")
            while True:
                try:
                    Password = getpass("Enter your password for this user :\n")
                    break
                except UnicodeDecodeError:
                    logging.error("Error : only ascii chars are available.")
                    
        # After connection save (test save/restore container)
        resp=input("Hit enter or save connection data now of 'n' to change remote login/password.\n")

        if (resp != 'n'):
            
            sshKeyPath=os.path.join(Home,".ssh","id_rsa_"+Frontend)
            
            if (TVconnection.auth_type == "ssh" and not OK_Key):
                cmdgen="ssh-keygen -b 1024 -t rsa -N '' -f /home/"+user+"/.ssh/id_rsa_"+Frontend
                childgen=pexpect.spawn(cmdgen)
                childgen.expect('Generating public/private rsa key pair.')
                # childgen.expect('Your identification has been saved in /home/'+user+'/.ssh/id_rsa_'+Frontend+'.')
                # childgen.expect('Your public key has been saved in /home/'+user+'/.ssh/id_rsa.pub_'+Frontend+'.')
                # childgen.expect('The key fingerprint is:')
                # sha_re=re.compile(r"SHA256:.* "+user+"@.*")
                # childgen.expect(sha_re)
                # childgen.expect('The key\'s randomart image is:')
                # childgen.expect('\+---[RSA 1024]----\+')
                # rsa_re=re.compile(r"\|.*\|")
                # for i in xrange(9):
                #     childgen.expect(rsa_re)
                # childgen.expect('\+----[SHA256]-----\+')
                childgen.expect(pexpect.EOF)
                childgen.close(force=True)
                logging.warning("ssh key for this connection OK.")
                OK_Key=True
                
            if (TVconnection.auth_type == "ssh"):
                cmdcopy="ssh-copy-id -f -o ForwardX11=no -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i "+sshKeyPath+".pub "+UserFront+"@"+Frontend
                #cmdcopy="bash -c 'ssh-copy-id -f -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i "+sshKeyPath+".pub "+UserFront+"@"+Frontend+ " 2>&1 $HOME/.vnc/out_copy_id'"                
                logging.warning("ssh-copy-id command :"+cmdcopy)
                childcopy=pexpect.spawn(cmdcopy)
                #out1=childcopy.expect('.*')
                expindex=childcopy.expect([UserFront+"@"+Frontend+"\'s password: ", ".*Password: ",pexpect.EOF, pexpect.TIMEOUT])
                if (expindex == 0 or expindex == 1 ):
                    outpass = childcopy.sendline(Password)
                    if outpass < len(Password):
                        Password = getpass("Wrong password for "+UserFront+"@"+Frontend+". Try again enter your password for this user :\n")
                        childcopy.close(force=True)                    
                    else:
                        expindex=childcopy.expect([pexpect.EOF, pexpect.TIMEOUT])
                        if (expindex != 0):
                            try:
                                logging.error("Error respond from server : "+str(childcopy.buffer,"utf-8"))
                            except:
                                logging.error("Error respond from server. "+str(expindex))
                        else:                        
                            logging.warning("ssh key copied on the server.")
                        childcopy.close(force=True)
                        if (childcopy.exitstatus == 0):
                            NOT_CONNECTED=False
                else:
                    try:
                        logging.error("Error with copy id "+str(expindex))
                        logging.error("buffer : |"+childcopy.buffer.decode("utf-8")+"|")
                        if (expindex == 3):
                            logging.warning("after TIMEOUT ")
                        else:
                            logging.warning("after "+childcopy.after.decode("utf-8"))
                        logging.warning("existstatus : ",childcopy.exitstatus, " signalestatus : ",childcopy.signalstatus)
                    except:                        
                        logging.warning("ssh key copied on the server.")

                    try:
                        logging.error("load interact prompt to test by hand :")
                        code.interact(banner="Try connection :",local=dict(globals(), **locals()))
                    except SystemExit:
                        pass
                    childcopy.close(force=True)
                    if (childcopy.exitstatus == 0):
                        NOT_CONNECTED=False

    # Get free local PORT for ssh to Frontend TileServer
    import socket;
    s=socket.socket();
    s.bind(("", 0));
    sshPORT=str(int(s.getsockname()[1]));
    s.close()
    # Save/restore here ?
    TunnelFrontend = "ssh  -o ForwardX11=no -4 -i "+sshKeyPath+" -T -N -nf"+\
                     "  -L "+str(sock.PORTServer)+":"+Frontend+":"+str(sock.PORTServer)+\
                     "  -L "+sshPORT+":localhost:22 "+UserFront+"@"+Frontend

    logging.debug(TunnelFrontend)
    os.system(TunnelFrontend)
    logging.info("ssh tunneling OK.")

    lshome="ssh -o ForwardX11=no -i "+sshKeyPath+" -p "+sshPORT+" "+UserFront+"@localhost 'ls $HOME/.tiledviz'"
    logging.debug(lshome)
    os.system(lshome)
    
    mkdirhome="ssh -o ForwardX11=no -i "+sshKeyPath+" -p "+sshPORT+" "+UserFront+"@localhost 'mkdir $HOME/.tiledviz'"
    logging.debug(mkdirhome)
    os.system(mkdirhome)

    chmodhome="ssh -o ForwardX11=no -i "+sshKeyPath+" -p "+sshPORT+" "+UserFront+"@localhost 'chmod og-rx $HOME/.tiledviz'"
    logging.debug(chmodhome)
    os.system(chmodhome)
    
    cmdhome="ssh -o ForwardX11=no -i "+sshKeyPath+" -p "+sshPORT+" "+UserFront+"@localhost 'echo $HOME'"
    logging.debug(cmdhome)
    childhome=pexpect.spawn(cmdhome)
    expindex=childhome.expect([pexpect.EOF, pexpect.TIMEOUT])
    if ( expindex == 0 ):
        HomeFront = childhome.before.decode("utf-8").replace("\n","").replace("\r","")
        logging.warning(HomeFront)
    else:
        logging.warning("Error with requiring remote 'home' dir.")
        HomeFront = os.path.join("/home",UserFront)
    childhome.close(force=True)
    
    TiledVizConfPath=os.path.join(HomeFront,'.tiledviz')
    
    # import Swarm
    # if (TVconnection.scheduler_file != ""):
    #     logging.warning("From DB connection scheduler_file : "+str(TVconnection.scheduler_file))
    # logging.warning("Bye !")
    #time.sleep(10)

    DATE=re.sub(r'\..*','',datetime.datetime.isoformat(datetime.datetime.now(),sep='_').replace(":","-"))
    JOBPath=os.path.join(TiledVizConfPath,TileSet+'_'+DATE)

    if (TVconnection.auth_type == "ssh"):
        WorkdirFrontend = "ssh -o ForwardX11=no -i "+sshKeyPath+" -p "+sshPORT+" "+UserFront+"@localhost mkdir "+JOBPath
        logging.debug(WorkdirFrontend)
        os.system(WorkdirFrontend)

    # prepare connect dir :
    CONNECTdir=TiledVizPath+"/TVConnections/connect"
    CONNECTpath=os.path.join(JOBPath,"connect")
    
    ConnectdirFrontend = 'rsync -va -e "ssh -o ForwardX11=no -T -i '+sshKeyPath+' -p '+sshPORT+' " '+CONNECTdir+' '+UserFront+"@localhost"+":"+JOBPath
    logging.debug(ConnectdirFrontend)
    os.system(ConnectdirFrontend)

    # Send or test TileServer run on server ??
    def launch_server(ServerFront):
        if ( ServerFront == "" ):
            TileServerFrontend = 'scp -o ForwardX11=no -i '+sshKeyPath+' -P '+sshPORT+' '+TiledVizPath+'/TVConnections/TileServer.py  '+UserFront+"@localhost"+":"+TiledVizConfPath
            logging.debug(TileServerFrontend)
            os.system(TileServerFrontend)
            cmdTileServer="ssh -o ForwardX11=no -i "+sshKeyPath+" -p "+sshPORT+" "+UserFront+"@localhost 'sh -c \"cd "+TiledVizConfPath+"; cp -rp "+os.path.join(JOBPath,"connect")+" .; HOSTNAME=\""+Frontend+"\" python3 TileServer.py > TileServer_"+DATE+".log 2>&1 & \"'"
            logging.debug(cmdTileServer)
            childTileServer=pexpect.spawn(cmdTileServer)
            expindex=childTileServer.expect([pexpect.EOF, pexpect.TIMEOUT])
            if ( expindex == 0 ):
                logging.warning("TileServer launched on frontend "+Frontend+" !")
                time.sleep(2)
            else:
                logging.warning("Error on TileServer launched on frontend "+Frontend+".")
            childTileServer.close(force=True)

    def test_TileServer():
        cmdServer="ssh -o ForwardX11=no -i "+sshKeyPath+" -p "+sshPORT+" "+UserFront+"@localhost 'sh -c \"ps -Aef |grep TileServer |grep -v grep |grep "+UserFront+"\"'"
        logging.debug(cmdServer)
        childServer=pexpect.spawn(cmdServer)
        expindex=childServer.expect([pexpect.EOF, pexpect.TIMEOUT])
        if ( expindex == 0 ):
            ServerFront = childServer.before.decode("utf-8").replace("\n","").replace("\r","")
            logging.debug(ServerFront)
            launch_server(ServerFront)
        childServer.close(force=True)

    test_TileServer()
    
    # Get Job file
    filename=TileSetDB.launch_file
    #eval(import filename, dict(globals()), dict(locals()))

    # ConnectionForm.scheduler = RadioField(label='Type of scheduler on HPC machine',
    #                                       description='How to launch containers job on the machine :',
    #                                       choices=[("none","No schedule at all : you will have to give the list of machines."),
    #                                                ("slurm","Slurm scheduler."),
    #                                                ("loadleveler","Loadleveler scheduler.")
    #                                       ],
    #                                       default=scheduler,
    #                                       validators=[Optional()])

    # Empty function to let TVSecure get new nodes.json from connectiondock.
    def get_new_nodes():
        return
    
    # Launch nodes.json file
    def launch_nodes_json():
        if (os.path.exists("nodes.json")):
                os.system('bash -c "mv nodes.json nodes.json_$(date +%F_%H-%M-%S)"')
        out_get=get_file_client(client,TileSet,JOBPath,"nodes.json",".")
        logging.warning("out of get_file nodes.json size : "+str(out_get))
        iter=0
        while( out_get <= 0):
            time.sleep(2)
            out_get=get_file_client(client,TileSet,JOBPath,"nodes.json",".")
            logging.warning("out of get_file "+str(iter)+" nodes.json : "+str(out_get))
            iter=iter+1
            if (iter > 10):
                logging.error("Something go wrong with nodes.json. We quit.")
                kill_all_containers()
                break
        #os.system('rm -f ./nodes.json')
        return True
    
    if (args.debug):
        try:
            code.interact(banner="Before client :",local=dict(globals(), **locals()))
        except SystemExit:
            pass
        except :
            traceback.print_exc(file=sys.stderr)
            pass

    # build connection with TileServer on Frontend
    try:
        client=sock.client()
    except:
        logging.warning("Connection is not working with TileServer on Frontend, but the process exists. We ")
        cmdServer="ssh -o ForwardX11=no -i "+sshKeyPath+" -p "+sshPORT+" "+UserFront+"@localhost 'sh -c \"pgrep TileServer |xargs kill \"'"
        os.system(cmdServer)
        logging.debug(cmdServer)
        
        test_TileServer()
        try:
            client=sock.client()
        except:
            logging.warning("Second test. Can not connect with TileServer on Frontend. We may stop.")
            try:
                sys.ps1="$$$ "
                code.interact(banner="Before client :",local=dict(globals(), **locals()))
                sys.ps1=">>> "
            except SystemExit:
                exit(0)
            except :
                traceback.print_exc(file=sys.stderr)

    isActions=False
    # Launch Action connection
    def launch_actions():
        global isActions
        try:
            time.sleep(2)
            logging.warning("Launch actions thread.")
            sys.stdout.flush()
            
            GetActions=ClientAction(connectionId,globals=dict(globals()),locals=dict(**locals()))
            outHandler.flush()
        except:
            traceback.print_exc(file=sys.stdout)
            code.interact(banner="Error ClientAction :",local=dict(globals(), **locals()))
        
        #logging.warning("Actions \n",str(tiles_actions))
        sys.stdout.flush()
        isActions=True
        
    # Launch Server for commands from FlaskDock
    def launch_actions_and_interact():
        global isActions
        if (not isActions):
            launch_actions()
            
        # if (not args.debug):
        #     try:
        #         code.interact(banner="Interactive console to use actions directly :",local=dict(globals(), **locals()))
        #     except SystemExit:
        #         pass
        #     except:
        #         pass

        # else:
        #     input("Debug mode : Wait for you hit return to close connection.\n")
        c = get_config()
        #c.InteractiveShellEmbed.colors="NoColor"
        c.InteractiveShellEmbed.banner1 = "Please type exit() to terminate launch script ."
        c.InteractiveShellEmbed.confirm_exit = False
        #c.InteractiveShellEmbed.color_info=False
        IPython.embed(config=c)
                
    # Execute launch file
    try:
        COMMANDStop="echo 'error script "+filename+"'"
        exec(compile(open(filename, "rb").read(), filename, 'exec'), globals(), locals())
        #filename.job(globals(), locals())
    except SystemExit:
        # Clean key :
        if (TVconnection.auth_type == "ssh"):
            myhostname=os.getenv('HOSTNAME', os.getenv('COMPUTERNAME', platform.node())).split('.')[0]
            CleanKeyFrontend = "ssh -o ForwardX11=no -i "+sshKeyPath+" -p "+sshPORT+" "+UserFront+'@localhost bash -c \'\"sed -i.'+DATE+' /'+myhostname+'/d ~/.ssh/authorized_keys\"\''
            logging.debug(CleanKeyFrontend)
            os.system(CleanKeyFrontend)
        # On localhost (no need) "ssh-keygen -R "+Frontend+" -f ~/.ssh/known_hosts"
    except :
        # stop containers
        kill_all_containers()
        traceback.print_exc(file=sys.stderr)
        #myglobals=globals()
        #code.interact(local=locals())
        pass

    # close connection with server. 
    client.close()

    # Kill ssh tunneling for VNC :
    #os.system("ps -Aef | grep 'connect.*@172.17.*' |grep -v grep | sed -e 's%'+user+'\\s*\\([0-9]*\\).*%\\1%' |xargs kill")
    os.system('killall -9 ssh')

    if (args.debug):
        try:
            code.interact(banner="Stop Connections :",local=dict(globals(), **locals()))
        except SystemExit:
            pass
        except :
            traceback.print_exc(file=sys.stderr)

