#! /usr/bin/env python
import subprocess
import threading

import time

import docker
import sys,os,stat
import argparse
import json
import datetime
import traceback
import re
import configparser

import tarfile
from io import BytesIO
# import tempfile
import json

import socket

sys.path.append(os.path.abspath('./TVDatabase'))
from TVDb import tvdb
from TVDb import models

sys.path.append(os.path.realpath('./TVConnections/'))
from connect import sock

import argparse

import code

import logging

errors=sys.stderr
listerrors={"createError":1,"ImageError":2,"APIError":3,"start":4}


TVrunDir=os.environ['HOME']+'/.tiledviz'
TVconf=TVrunDir+"/tiledviz.conf"
configExist=False
if (os.path.isdir(TVrunDir)):
    if (os.path.isfile(TVconf)):
        configExist=True
else:
    os.mkdir(TVrunDir)
    mode = os.stat(TVrunDir).st_mode
    mode -= (mode & (stat.S_IRWXG | stat.S_IRWXO))
    os.chmod(TVrunDir,mode)
    
if (configExist):
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(TVconf)

    # Max number of connections before relaunch TVSecure
    NbSecureConnection=int(config['TVSecure']['NbSecureConnection'])

    # Start port for ssh connection between TVConnection.py and TVSecure.py through ssh
    ConnectionPort=int(config['TVSecure']['ConnectionPort'])
    
    # Start port for connection between TVConnection.py and TVSecure.py through socat and docker0
    ActionPort=int(config['TVSecure']['ActionPort'])
else:
    NbSecureConnection=59
    # Default init connection PORT
    ConnectionPort=54040
    ActionPort=64040

nbLinesLogs=100
timeAliveServ=0.2
timeAliveConn=0.1
timeWait=2
CONNECTION_RESOL='1350x660'

DEBUG_ANALYSE=False
debug_Flask=False

#sys.path.append(os.path.abspath('./'))

POSTGRES_HOST="postgres"
POSTGRES_IP="172.17.0.2"
POSTGRES_PORT="6431"
POSTGRES_USER="tiledviz"
POSTGRES_DB="TiledViz"
POSTGRES_PASSWORD="m_test/@03"
secretKey="my Preci0us secr_t key for t&sts."

client = docker.from_env()
def parse_args(argv):
    parser = argparse.ArgumentParser(
        'Launch Flask docker with postgres parameters. Lauch on-demand connections.')
    parser.add_argument('--POSTGRES_HOST', default=POSTGRES_HOST,
                        help='POSTGRES_HOST (default: '+POSTGRES_HOST+')')
    parser.add_argument('--POSTGRES_IP', default=POSTGRES_IP,
                        help='POSTGRES_IP (default: '+POSTGRES_IP+')')
    parser.add_argument('--POSTGRES_PORT', default=POSTGRES_PORT,
                        help='POSTGRES_PORT (default: '+POSTGRES_PORT+')')
    parser.add_argument('--POSTGRES_USER', default=POSTGRES_USER,
                        help='POSTGRES_USER (default: '+POSTGRES_USER+')')
    parser.add_argument('--POSTGRES_DB', default=POSTGRES_DB,
                        help='POSTGRES_DB (Default: '+POSTGRES_DB+')')
    parser.add_argument('--POSTGRES_PASSWORD', default='"'+POSTGRES_PASSWORD+'"',
                        help='POSTGRES_PASSWORD (default: "'+POSTGRES_PASSWORD+'")')
    parser.add_argument('--secretKey', default=secretKey,
                        help='secretKey (default: "'+secretKey+'")')
    args = parser.parse_args(argv[1:])
    return args

TVvolume=docker.types.Mount(target='/TiledViz',source=os.getenv('PWD'),type='bind',read_only=False)

threads={}

sqltConnections={"username":"none","connectionid":-1}
Connections=[sqltConnections] * NbSecureConnection
usedConnections=[False] * NbSecureConnection

# Get string of exec_run output
def container_exec_out(thecontainer, cmd, user='root'):
    res=thecontainer.exec_run(cmd=cmd,user=user,stream=True,demux=False,detach=False)
    return "".join([ str(out,'utf-8') for out in res.output ])

# Get the new last part string between old string1 and new string2 for the log output.
# from https://stackoverflow.com/a/46757885
def NewStringFinder(string1, string2):
    answer = ""
    len1, len2 = len(string1), len(string2)
    ansK=0
    for i in range(len1):
        for j in range(len2):
            lcs_temp=0
            match=''
            while ((i+lcs_temp < len1) and (j+lcs_temp<len2) and string1[i+lcs_temp] == string2[j+lcs_temp]):
                match += string2[j+lcs_temp]
                lcs_temp+=1
            if (len(match) > len(answer)):
                answer = match
                ansK=j+lcs_temp
    return string2[ansK:len2]

class FlaskDocker(threading.Thread):
    def __init__(self,
                 POSTGRES_HOST=POSTGRES_HOST, POSTGRES_IP=POSTGRES_IP, POSTGRES_PORT=POSTGRES_PORT,
                 POSTGRES_DB=POSTGRES_DB, POSTGRES_USER=POSTGRES_USER, POSTGRES_PASSWORD=POSTGRES_PASSWORD,
                 secretKey=secretKey ):

        self.thread = threading.Thread(target=self.run, args=( POSTGRES_HOST, POSTGRES_IP, POSTGRES_PORT,
                                                               POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD,
                                                               secretKey ))
        
        threads["flaskdock"]=self.thread
        self.thread.start()

    def run(self,
            POSTGRES_HOST=POSTGRES_HOST, POSTGRES_IP=POSTGRES_IP, POSTGRES_PORT=POSTGRES_PORT,
            POSTGRES_DB=POSTGRES_DB, POSTGRES_USER=POSTGRES_USER, POSTGRES_PASSWORD=POSTGRES_PASSWORD,
            secretKey=secretKey ):

        self.oldtime=time.time()

        flaskaddr=socket.gethostbyname(socket.gethostname())
        self.commandFlask=[POSTGRES_HOST,POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, flaskaddr, str(os.getuid()),str(os.getgid()), secretKey]
        
        # Si on passe secretKey et password comme secret (seulement comme services dans un swarm!), on doit modifier TVWeb/FlaskDocker/launch_flask
        # pgpassword=client.secrets.create(name="POSTGRES_PASSWORD",data=POSTGRES_PASSWORD)
        # flsecret=client.secrets.create(name="secretKey",data=secretKey)
        # client.swarm.init(
        #     advertise_addr='eth0', listen_addr='0.0.0.0:5000',
        #     force_new_cluster=False, snapshot_interval=5000,
        #     log_entries_for_slow_followers=1200
        # )                        
        # client.service.create(....,secrets=[pgpassword,flsecret],...)
        # $ docker service  create --name redis --secret my_secret_data redis:alpine
        # $ docker container exec $(docker ps --filter name=redis -q) ls -l /run/secrets

        # total 4
        # -r--r--r--    1 root     root            17 Dec 13 22:48 my_secret_data
        
        # $ docker container exec $(docker ps --filter name=redis -q) cat /run/secrets/my_secret_data

        # postgres service
        self.postgresHost={POSTGRES_HOST:POSTGRES_IP}
        # Flask external port
        self.flaskPORT={'5000/tcp':('0.0.0.0',5000)}
        for i in range(NbSecureConnection): 
            self.flaskPORT[str(ConnectionPort+i)+'/tcp']=('0.0.0.0',ConnectionPort+i)

        healthcheckN=docker.types.Healthcheck(interval=50000000) #test=['NONE'])

        if (debug_Flask):
            ENVFlask=["debug_Flask=true"]
        else:
            ENVFlask=["debug_Flask=false"]

        # ENVFlask=ENVFlask+["DATABASE_URL=postgresql://"+POSTGRES_USER+"@"+POSTGRES_HOST+":"+POSTGRES_PORT]
        # logging.error("Before create Flask docker. env variables :" +str(ENVFlask))
        
        # Detect or create flask container :
        try:
            self.containerFlask=client.containers.create(
                name="flaskdock", image="flaskimage",
                mounts=[TVvolume], extra_hosts=self.postgresHost,
                command=self.commandFlask,
                ports=self.flaskPORT,
                environment=ENVFlask,
                healthcheck=healthcheckN,
                detach=True) #auto_remove=True,
            
        except docker.errors.ContainerError:
            logging.error("The container exits with a non-zero exit code and detach is False.")
            traceback.print_exc(file=errors)
            sys.exit(listerrors["createError"])
        except docker.errors.ImageNotFound:
            logging.error("The specified image does not exist.")
            traceback.print_exc(file=errors)
            sys.exit(listerrors["ImageError"])
        except docker.errors.APIError:
            logging.error("The server returns an error.")
            traceback.print_exc(file=errors)
            sys.exit(listerrors["APIError"])
            
        self.user="flaskusr"
        self.home="/home/flaskusr"
        self.idFlask = self.containerFlask.id

        self.daterun=datetime.datetime.now()
        logging.warning("Ready to start flaskdock.")
        try :
            self.containerFlask.start()
        except docker.errors.APIError :
            traceback.print_exc(file=errors)
            sys.exit(listerrors["start"])
            
        logging.warning("After start Flask, containers list :"+str(client.containers.list()))

        self.containerFlask.reload()
        ipFlask = self.containerFlask.attrs["NetworkSettings"]["Networks"]["bridge"]["IPAddress"]
        logging.debug("We have built container for user "+self.user+" with postgresql user "+POSTGRES_USER+" and password '"+POSTGRES_PASSWORD+"' with IP "+ipFlask+".")
        logging.warning("Flask container status :"+str(self.containerFlask.status))

        # string from Flask for new connection

        createnewconnection=r'WARNING:.*addconnection:\s*(?P<username>\w+)\s*;\s*(?P<hostname>[^ ;]+)\s*;\s*(?P<connection>\w+)\s*;\s*(?P<containers>\w+)\s*;\s*(?P<scheduler>\w+)\s*;\s*(?P<idTS>\d+)\s*;\s*(?P<idCon>\d+)\s*;\s*(?P<Debug>\d)'
        create_newconnection = re.compile(r''+createnewconnection)

        # string from Flask for edit old connection
        editoldconnection=r'WARNING:.*editconnection:\s*(?P<username>\w+)\s*;\s*(?P<hostname>[^ ;]+)\s*;\s*(?P<connection>\w+)\s*;\s*(?P<containers>\w+)\s*;\s*(?P<scheduler>\w+)\s*;\s*(?P<idTS>\d+)\s*;\s*(?P<idCon>\d+)'
        edit_oldconnection = re.compile(r''+editoldconnection)

        # string from Flask for kill old connection
        quitoldconnection=r'WARNING:.*removeconnection:\s*(?P<username>\w+)\s*;\s*(?P<idTS>\d+)\s*;\s*(?P<idCon>\d+)'
        quit_oldconnection = re.compile(r''+quitoldconnection)
        
        # string from Flask for kill old connection
        killoldconnection=r'WARNING:.*killconnection:\s*(?P<username>\w+)\s*;\s*(?P<idTS>\d+)\s*;\s*(?P<idCon>\d+)'
        kill_oldconnection = re.compile(r''+killoldconnection)
        
        # string from Flask for action
        actionoldconnection=r'WARNING:.*action:\s*(?P<username>\w+)\s*;\s*(?P<idTS>\d+)\s*;\s*(?P<idCon>\d+)\s*;\s*(?P<selection>[0-9,]*)'
        action_oldconnection = re.compile(r''+actionoldconnection)
        
        oldLogs=""
        Logs=""
        
        logging.warning("Start log detection loop.")
        while True:
            # Detect all command to request new thread here

            NewLog=NewStringFinder(oldLogs, Logs)
            if (DEBUG_ANALYSE):
                logging.error("Get new log "+NewLog)
            if (len(NewLog) > 0):
                # newconnection
                create_newconnect=create_newconnection.search(NewLog)
                # editconnection
                edit_oldconnect=edit_oldconnection.search(NewLog)
                # delconnection
                quit_oldconnect=quit_oldconnection.search(NewLog)
                # kill tunnel connection
                kill_oldconnect=kill_oldconnection.search(NewLog)
                # saveconnection
                # restartconnection
                # actions
                action_oldconnect=action_oldconnection.search(NewLog)
            else:
                create_newconnect=False
                # editconnection
                edit_oldconnect=False
                # delconnection
                quit_oldconnect=False
                # killconnection
                kill_oldconnect=False
                # actions
                action_oldconnect=False

            if (DEBUG_ANALYSE):
                logging.error("Before create_newconnect :"+str(create_newconnect))

            find_connect=True
            if (create_newconnect):
                if (DEBUG_ANALYSE):
                    logging.error("Match create connection ")
                match_connect=create_newconnect
            elif (edit_oldconnect):
                if (DEBUG_ANALYSE):
                    logging.error("Match edit connection ")
                match_connect=edit_oldconnect
            elif (quit_oldconnect):
                if (DEBUG_ANALYSE):
                    logging.error("Match quit connection ")
                match_connect=quit_oldconnect
            elif (kill_oldconnect):
                if (DEBUG_ANALYSE):
                    logging.error("Match edit connection ")
                match_connect=kill_oldconnect
            elif (action_oldconnect):
                if (DEBUG_ANALYSE):
                    logging.error("Match action connection :"+NewLog)
                match_connect=action_oldconnect
            else:
                find_connect=False

            test_notconnect=False
            if (find_connect):
                if (DEBUG_ANALYSE):
                    logging.error("After test create_newconnect :"+str(match_connect.groups()))
                # test if there is no existing connection
                boolTestNotAlreadyConnect=(not any([ (match_connect.group("username") == theConnection["username"] and
                                                      match_connect.group("idCon") == theConnection["connectionid"])
                                                     for theConnection in Connections]))
                test_notconnect=(len(Connections) == 0 or boolTestNotAlreadyConnect)
            
                if (DEBUG_ANALYSE):
                    logging.error("after test_notconnect "+str(test_notconnect))
            
            if create_newconnect:
                logging.warning("Create new connect :"+str(create_newconnect.groups()))
                if test_notconnect:
                    # logging.warning("Get connection parameters :"
                    #                 +" "+create_oldconnect.group("username")+" "+create_oldconnect.group("hostname")
                    #                 +" "+create_oldconnect.group("connection")+" "+create_oldconnect.group("containers")
                    #                 +" "+create_oldconnect.group("scheduler")+" "+create_oldconnect.group("idTS")
                    #                 +" "+create_oldconnect.group("idCon") +" "+create_newconnect.group("Debug"))
                    logging.debug("Connection container type :"+create_newconnect.group("containers"))

                    # Find the first free Connection
                    ReverseFreeConnect= usedConnections.copy()
                    ReverseFreeConnect.reverse() 
                    FindFree=True
                    try:
                        firstFree=NbSecureConnection - ReverseFreeConnect.index(True)
                    except:
                        firstFree=0
                    if (firstFree == NbSecureConnection):
                        FindFree=False
                        try:
                            firstFree=usedConnections.index(False)
                            logging.warning("Connection pool loop :"+str(firstFree))
                            FindFree=True
                        except:
                            traceback.print_exc(file=errors)
                            logging.error("ERROR : Full Connection pool. No new connection possible.")
                    logging.warning("Connection pool slot :"+str(firstFree))

                    if (FindFree):
                        usedConnections[firstFree]=True
                        logging.warning("Connection table :"+str(usedConnections))
                    
                        # then create the new connection
                        Connections[firstFree]=({"username":create_newconnect.group("username"),
                                                 "hostname":create_newconnect.group("hostname"),
                                                 "connection":create_newconnect.group("connection"),
                                                 "containers":create_newconnect.group("containers"),
                                                 "tilesetid":create_newconnect.group("idTS"),
                                                 "connectionid":create_newconnect.group("idCon"),
                                                 "ThisConnection":""})

                        debug=bool(int(create_newconnect.group("Debug")))
                        if (debug):
                            logging.warning("Debug mode for connection.")
                        ThisConnection=ConnectionDocker(self.containerFlask, debug, firstFree,
                                                        POSTGRES_HOST, POSTGRES_IP, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
                        Connections[firstFree]["ThisConnection"]=ThisConnection
                else:
                    logging.warning("A connection already exists with parameters :"+create_newconnect.group("username")+" "+create_newconnect.group("hostname")+" "+str(create_newconnect.group("idCon")))
                    logging.error("connections : "+str( [ theConnection["username"]+" "+theConnection["hostname"]+" "+str(theConnection["connectionid"]) for theConnection in Connections] ))
                    
            elif (edit_oldconnect):
                logging.warning("Edit old connect :"+str(edit_oldconnect.groups()))
                if (not test_notconnect ):
                    logging.warning("Edit connection parameters :"
                                    +" "+edit_oldconnect.group("username")+" "+edit_oldconnect.group("hostname")
                                    +" "+edit_oldconnect.group("connection")+" "+edit_oldconnect.group("containers")
                                    +" "+edit_oldconnect.group("scheduler")+" "+edit_oldconnect.group("idTS")
                                    +" "+edit_oldconnect.group("idCon") )
                    logging.debug("Connection container type :"+edit_oldconnect.group("containers"))
                    for theConnection in Connections:
                        if( edit_oldconnect.group("username") == theConnection["username"] and
                            edit_oldconnect.group("hostname") == theConnection["hostname"] and
                            edit_oldconnect.group("idCon") == theConnection["connectionid"] ):
                            logging.warning("Update script for connection "+str(theConnection["connectionid"]))
                            theConnection["ThisConnection"].callfunction("updateScripts")
                            logging.warning("Reconnect "+str(theConnection["connectionid"]))
                            theConnection["ThisConnection"].callfunction("reconnect")
                else:
                    logging.warning("No connection found with parameters :"+edit_oldconnect.group("username")+" "+edit_oldconnect.group("hostname")+" "+str(edit_oldconnect.group("idCon")))
                    #logging.error("connections : "+str( [ theConnection["username"]+" "+theConnection["hostname"]+" "+str(theConnection["connectionid"]) for theConnection in Connections] ))

            elif (quit_oldconnect):
                logging.warning("Quit old connect :"+str(quit_oldconnect.groups()))
                if (not test_notconnect ): 
                    logging.warning("Quit connection parameters :"+quit_oldconnect.group("username")
                                    +" "+quit_oldconnect.group("idTS")+" "+quit_oldconnect.group("idCon"))
                    logging.debug("Connection container type :"+quit_oldconnect.group("idCon"))
                    for theConnection in Connections:
                        if( quit_oldconnect.group("username") == theConnection["username"] and
                            quit_oldconnect.group("idCon") == theConnection["connectionid"] ):
                            logging.warning("Quit connection "+str(theConnection["connectionid"]))                            
                            theConnection["ThisConnection"].callfunction("quitConnection")
                else:
                    logging.error("No connection found with parameters :"+quit_oldconnect.group("username")+" "+str(quit_oldconnect.group("idCon")))
                    #logging.error("connections : "+str( [ theConnection["username"]+" "+theConnection["hostname"]+" "+str(theConnection["connectionid"]) for theConnection in Connections] )) 
                            
            elif (kill_oldconnect):
                logging.warning("Kill old connect :"+str(kill_oldconnect.groups()))
                if (not test_notconnect ): 
                    logging.warning("Kill connection parameters :"+kill_oldconnect.group("username")
                                    +" "+kill_oldconnect.group("idTS")+" "+kill_oldconnect.group("idCon"))
                    logging.debug("Connection container type :"+kill_oldconnect.group("idCon"))
                    for theConnection in Connections:
                        if( kill_oldconnect.group("username") == theConnection["username"] and
                            kill_oldconnect.group("idCon") == theConnection["connectionid"] ):
                            logging.warning("Kill connection "+str(theConnection["connectionid"]))
                            theConnection["ThisConnection"].callfunction("killTunnel")
                else:
                    logging.error("No connection found with parameters :"+kill_oldconnect.group("username")+" "+str(kill_oldconnect.group("idCon")))
                    #logging.error("connections : "+str( [ theConnection["username"]+" "+theConnection["hostname"]+" "+str(theConnection["connectionid"]) for theConnection in Connections] )) 

            elif (action_oldconnect):
                logging.warning("action old connect :"+str(action_oldconnect.groups()))
                if (not test_notconnect ): 
                    logging.warning("Action connection parameters :"+action_oldconnect.group("username")
                                    +" "+action_oldconnect.group("idTS")+" "+action_oldconnect.group("idCon")
                                    +" "+action_oldconnect.group("selection"))
                    logging.debug("Connection container type :"+action_oldconnect.group("idCon"))
                    for theConnection in Connections:
                        if( action_oldconnect.group("username") == theConnection["username"] and
                            action_oldconnect.group("idCon") == theConnection["connectionid"] ):
                            #logging.warning("Action connection "+str(theConnection["connectionid"]))
                            logging.warning("Action connection "+str(theConnection["connectionid"])+" function "+str("action="+action_oldconnect.group("selection")))
                            theConnection["ThisConnection"].callfunction("action="+action_oldconnect.group("selection"))
                else:
                    logging.error("No connection found with parameters :"+action_oldconnect.group("username")+" "+str(action_oldconnect.group("idCon")))
                    #logging.error("connections : "+str( [ theConnection["username"]+" "+theConnection["hostname"]+" "+str(theConnection["connectionid"]) for theConnection in Connections] )) 
                    
            time.sleep(timeAliveServ)
            # logging.debug("Log loop")
            
            oldLogs=Logs
            Logs=str(self.containerFlask.logs(timestamps=True,since=int(self.oldtime),tail=nbLinesLogs))
            self.oldtime=time.time()            

    def isalive(self):
        # try:
        #     self.containerFlask.reload()
        # except:
        #     return False
        logging.debug("Flask container status :"+str(self.containerFlask.status))
        return self.containerFlask.status == "running"
    
    def getLog(self,nbLines):
        # print(re.sub(r'\*n',r'\\n',str(self.Logs,'utf-8')))
        self.Logs=self.containerFlask.logs(timestamps=True,since=int(self.oldtime),tail=nbLines).decode("utf-8")
        self.oldtime=time.time()
        
        logging.warning(self.Logs)

    def getContainerFlask(self):
        return self.containerFlask

class ConnectionDocker(threading.Thread):
    
    def __init__(self,containerFlask, debug, ConnectNum,
                 POSTGRES_HOST=POSTGRES_HOST, POSTGRES_IP=POSTGRES_IP, POSTGRES_PORT=POSTGRES_PORT,
                 POSTGRES_DB=POSTGRES_DB, POSTGRES_USER=POSTGRES_USER, POSTGRES_PASSWORD=POSTGRES_PASSWORD):
        threading.Thread.__init__(self)
        self.thread = threading.Thread(target=self.run,args=(containerFlask,debug, ConnectNum,
                                                             POSTGRES_HOST, POSTGRES_IP, POSTGRES_PORT,
                                                             POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD,)).start()
        
        time.sleep(10)
        threads[self.name]=self.thread
        #threading.Thread.__init__(self, target=self.run_forever)

    def run(self,containerFlask,debug, ConnectNum,
            POSTGRES_HOST=POSTGRES_HOST, POSTGRES_IP=POSTGRES_IP, POSTGRES_PORT=POSTGRES_PORT,
            POSTGRES_DB=POSTGRES_DB, POSTGRES_USER=POSTGRES_USER, POSTGRES_PASSWORD=POSTGRES_PASSWORD):

        self.user="myuser"
        self.home='/home/'+self.user

        self.oldtime=time.time()

        self.ConnectNum=ConnectNum
        self.name="connectiondock"+str(Connections[self.ConnectNum]["connectionid"])
        self.tilesetId=int(Connections[self.ConnectNum]["tilesetid"])
        self.connectionId=int(Connections[self.ConnectNum]["connectionid"])
        
        self.containerFlask = containerFlask
        self.IPFlask=self.containerFlask.attrs["NetworkSettings"]["Networks"]["bridge"]["IPAddress"]

        self.call_list=[]
        
        logging.warning("Connection creation :"+self.name)
        self.dir='/tmp/'+self.name
        if (not os.path.isdir(self.dir)): os.mkdir(self.dir)

                              
        VncVolume=docker.types.Mount(source=self.dir,target=self.home+"/.vnc",type='bind',read_only=False)
        XLocale=docker.types.Mount(source="/usr/share/X11/locale",target="/usr/share/X11/locale",type='bind')

        if (debug):
            self.commandConnect=[str(self.connectionId),POSTGRES_HOST,POSTGRES_PORT,POSTGRES_DB,POSTGRES_USER,POSTGRES_PASSWORD,'-r',CONNECTION_RESOL,'-u',str(os.getuid()),'-g',str(os.getgid()),'-d']
            self.cont_auto_remove=False
        else:
            self.commandConnect=[str(self.connectionId),POSTGRES_HOST,POSTGRES_PORT,POSTGRES_DB,POSTGRES_USER,POSTGRES_PASSWORD,'-r',CONNECTION_RESOL,'-u',str(os.getuid()),'-g',str(os.getgid())]
            self.cont_auto_remove=True

        logging.debug("Input param commandConnect : '"+str(self.commandConnect)+"'")

        self.postgresHost={POSTGRES_HOST:POSTGRES_IP}

        if ( os.path.exists( "/dev/nvidia0" ) ):
            list_gpu_dev=["/dev/nvidia0:/dev/nvidia0:rw","/dev/nvidiactl:/dev/nvidiactl:rw"]
        else:
            logging.debug("ConnectionDocker : no GPU device find in /dev")
            list_gpu_dev=[]

        outHandler.flush()

        healthcheckN=docker.types.Healthcheck(interval=50000000) #test=['NONE'])
            
        # Detect or create flask container :
        try:

            self.containerConnect=client.containers.create(
                name=self.name, image="mageiaconnect",
                mounts=[VncVolume,XLocale], 
                extra_hosts=self.postgresHost,
                command=self.commandConnect,
                devices=list_gpu_dev,
                healthcheck=healthcheckN,
                auto_remove=self.cont_auto_remove, detach=True)

        except docker.errors.ContainerError:
            logging.error("The container exits with a non-zero exit code and detach is False.")
            traceback.print_exc(file=errors)
            sys.exit(listerrors["createError"])
        except docker.errors.ImageNotFound:
            logging.error("The specified image does not exist.")
            traceback.print_exc(file=errors)
            sys.exit(listerrors["ImageError"])
        except docker.errors.APIError:
            logging.error("The server returns an error.")
            traceback.print_exc(file=errors)
            sys.exit(listerrors["APIError"])

        self.daterun=datetime.datetime.now()
        logging.warning("Ready to start "+self.name+".")
        try:
            self.containerConnect.start()
            logging.warning("Connection started.")
        except docker.errors.APIError :
            traceback.print_exc(file=errors)
            sys.exit(listerrors["start"])
            
        logging.warning("After start "+self.name+", containers list :"+str(client.containers.list()))

        searchpassword=r'Random Password Generated:\s*(?P<passwd>[-._+0-9a-zA-Z]+)'
        search_passwd = re.compile(r''+searchpassword)
        while True:
            info_passwd=self.grepLog(100,search_passwd)
            if info_passwd:
                self.password=info_passwd.group("passwd")
                break
            time.sleep(0.5)
        logging.warning("After password.")

        self.containerConnect.reload()
        ipconnect = self.containerConnect.attrs["NetworkSettings"]["Networks"]["bridge"]["IPAddress"]
        logging.debug("We have built container for user '"+self.user+"' with IP "+ipconnect+".")
        logging.warning("User container status :"+str(self.containerConnect.status))
        time.sleep(timeWait)
        
        # Create temporary user on flask docker :
        self.flaskusr="connect"+str(self.connectionId)
        flaskhome="/home/"+self.flaskusr
        
        uid=str(os.getuid()+1+self.connectionId)
        gid=str(uid)
        uid=str(uid)
        commandAdduser="bash -c 'groupadd -r -g "+gid+" "+self.flaskusr+ \
            " && useradd -r -u "+uid+" -g "+self.flaskusr+" "+self.flaskusr+" && cp -rp /etc/skel "+flaskhome+\
            " && chown -R "+self.flaskusr+":"+self.flaskusr+" "+flaskhome+"'"
        self.LogAddUser=container_exec_out(self.containerFlask, commandAdduser)
        logging.debug("Add user "+self.flaskusr+" on Flask container."+re.sub(r'\*n',r'\\n',self.LogAddUser))
        
        # Get id_rsa.pub for tunneling VNC flux
        time.sleep(timeWait)
        commandAuthKey = "cat "+self.home+"/.ssh/id_rsa.pub"
        self.LogAuthKey = container_exec_out(self.containerConnect, commandAuthKey)
        self.LogAuthorized_key = re.sub(r'\n',r'',self.LogAuthKey)
        # print("Key : ",self.LogAuthorized_key)
        authorized_key=re.sub(r'\*n',r'\\n',self.LogAuthorized_key)
        logging.debug("Authorized_key from connection container : \n'"+authorized_key+"'")

        # Put this key in flask docker
        commandBuildSsh="mkdir "+flaskhome+"/.ssh"
        self.LogBuildSsh=container_exec_out(self.containerFlask, commandBuildSsh,user=self.flaskusr)
        logging.debug("Create .ssh to Flask docker :\n'"+re.sub(r'\*n',r'\\n',self.LogBuildSsh)+"'")
        commandBuildSsh="chmod 700 "+flaskhome+"/.ssh"
        self.LogBuildSsh=container_exec_out(self.containerFlask, commandBuildSsh,user=self.flaskusr)
        logging.debug("Protect .ssh to Flask docker :\n'"+re.sub(r'\*n',r'\\n',self.LogBuildSsh)+"'")

        # Use awk to insert key in .ssh/authorized_key file !
        commandBuildSsh="awk 'BEGIN {print \""+authorized_key+"\" >>\""+flaskhome+"/.ssh/authorized_keys\"}' /dev/null"
        self.LogBuildSsh=container_exec_out(self.containerFlask, commandBuildSsh,user=self.flaskusr)
        logging.debug("Add autorized_key to Flask docker :\n'"+re.sub(r'\*n',r'\\n',self.LogBuildSsh)+"'")

        # List .ssh/authorized_key in Flask
        # commandBuildSsh="ls -la "+flaskhome+"/.ssh/authorized_keys"
        # self.LogBuildSsh=self.containerFlask.exec_run(cmd=commandBuildSsh,user=self.flaskusr)
        # logging.debug("List .ssh/authorized_key in Flask docker :\n"+re.sub(r'\*n',r'\\n',str(self.LogBuildSsh.output,'utf-8')))

        # Add password for temporary connection
        commandBuildVNC="awk 'BEGIN {print \""+self.password+"\" >>\""+flaskhome+"/vncpassword\"}' /dev/null"
        self.LogBuildVNC=container_exec_out(self.containerFlask, commandBuildVNC,user=self.flaskusr)
        logging.debug("Add VNC password to Flask docker :\n"+re.sub(r'\*n',r'\\n',self.LogBuildVNC))

        #  Test connection type dans launch a script (in the start xterm full-screen ?) 
        # in python in container to manage the expect or get ssh private for HPC connection
        internPort=ConnectionPort+self.ConnectNum
        externPort=internPort
        #externPort=internPort+random.randint(100,400)
        #socatCMD="socat TCP-LISTEN:"+str(externPort)+",fork,reuseaddr TCP:127.0.0.1:"+str(internPort)
        #1 externPort = internPort avec GatewayPorts=yes
        #2 socat avec port extern sur un plage aléatoire ?
        # self.LogSocat=container_exec_out(self.containerFlask, socatCMD)
        # logging.debug("Socat "+str(internPort)+" to "+str(externPort)" :\n"+re.sub(r'\*n',r'\\n',self.LogSocat))
        
        # Get connection and tileset informations :
        self.ConnectionDB=session.query(models.Connection).filter(models.Connection.id == int(self.connectionId)).one()
        self.TileSetDB=session.query(models.TileSet).filter_by(id=self.tilesetId).one()
        session.refresh(self.TileSetDB)
        self.updateScripts()

        # Write connection PORT in DB for vncconnection.html
        try:
            self.ConnectionDB.connection_vnc=externPort-32768
            session.commit()
        except:
            traceback.print_exc(file=errors)
        logging.warning("Connection VNC port saved : "+str(self.ConnectionDB.connection_vnc)+" real : "+str(self.ConnectionDB.connection_vnc+32768))

        # Tunnel to Flask : Give access from vncconnection page to this container
        vnc_command="if [ X\\\"\\$( pgrep -fla x11vnc )\\\" == X\\\"\\\" ]; then /opt/vnccommand; fi &"
        self.tunnel_script=os.path.join(self.home,".vnc","tunnel_flask")
        self.tunnel_command="ssh -4 -T -N -nf -R 0.0.0.0:"+str(externPort)+":localhost:5902 "+self.flaskusr+"@"+self.IPFlask+" &"
        scriptTunnel="awk 'BEGIN {print \""+vnc_command+" \\n "+self.tunnel_command+"\" >>\""+self.tunnel_script+"\"}' > /dev/null &"
        logging.debug("awk command to build tunnel script : "+scriptTunnel)
        
        self.LogScrTunnel=self.containerConnect.exec_run(cmd=scriptTunnel,user=self.user,detach=True)
        time.sleep(0.5)
        self.LogModTunnel=self.containerConnect.exec_run(cmd="chmod u+x "+self.tunnel_script,user=self.user,detach=True)
        
        self.kill_tunnel_script=os.path.join(self.home,".vnc","kill_tunnel_flask")
        out_kill_tunnel=os.path.join(self.home,".vnc","out_killtunnel")
        killTunnel='Tunnel=$(pgrep -fla \\"ssh.*@'+self.IPFlask+'\\" |grep -v -- \\"-c\\" | sed -e \\"s@\\\\([0-^]*\\\\) .*@\\\\1@\\");\\nif [ X\\"$Tunnel\\" != X\\"\\" ]; then \\n  echo $Tunnel > '+out_kill_tunnel+';\\n  kill -9 $Tunnel 2>&1 >> '+out_kill_tunnel+';\\n fi'

        scriptTunnel="awk 'BEGIN {print \""+killTunnel+"\" >>\""+self.kill_tunnel_script+"\"}' > "+out_kill_tunnel

        logging.debug("awk command to build kill tunnel script : "+scriptTunnel)

        self.LogScrTunnel=self.containerConnect.exec_run(cmd=scriptTunnel,user=self.user,detach=True)
        time.sleep(0.5)
        self.LogModTunnel=self.containerConnect.exec_run(cmd="chmod u+x "+self.kill_tunnel_script,user=self.user,detach=True)
        logging.warning("tunnel script built.")
        
        self.connect()

        # Connect to TVConnection in connectionDocker to send actions commands.
        actionPort=ActionPort+self.ConnectNum
        search_docker0_ip="ip -4 addr show docker0 | grep -Po 'inet \K[\d.]+'"
        p=subprocess.Popen(search_docker0_ip, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)        
        output, errs = p.communicate()
        ipdocker0=output.decode('utf-8').replace('\n','')
        logging.warning("ConnectionDocker : connection for actions with port %d and ip for docker0 %s" % (actionPort,ipdocker0))

        self.action_script=os.path.join(self.home,".vnc","tunnel_action")
        action_command="socat TCP-LISTEN:"+str(ActionPort)+",fork,reuseaddr TCP:"+ipdocker0+":"+str(actionPort)+" &"
        scriptAction="awk 'BEGIN {print \""+action_command+"\" >>\""+self.action_script+"\"}' 2>&1 /dev/null"
        logging.debug("awk command to build action script : "+scriptAction)

        self.LogScrAction=self.containerConnect.exec_run(cmd=scriptAction,user=self.user,detach=True)
        time.sleep(0.5)
        self.LogModAction=self.containerConnect.exec_run(cmd="chmod u+x "+self.action_script,user=self.user,detach=True)
        #logging.warning("action script built.")
        time.sleep(0.5)
        self.LogAction=self.containerConnect.exec_run(cmd="sh -c "+self.action_script,user=self.user,detach=True)
        logging.warning("action script executed.")
        outHandler.flush()
        time.sleep(0.5)
        
        search_action = re.compile(r''+"action=")

        path_nodesjson=os.path.join(self.home,"nodes.json")
        self.dir_out="TVFiles/"+str(self.ConnectionDB.id_users)+"/"+str(self.ConnectionDB.id)
        time.sleep(timeAliveConn)

        nodes_ok=False
        while True:
            #logging.debug("Container "+self.name+" wake up.")
            
            if (not nodes_ok):
                try: 
                    # Get back nodes.json from connection docker ?
                    bits, stat = self.containerConnect.get_archive(path=path_nodesjson)
                    logging.warning("GET "+path_nodesjson+ " file from Connection Docker.")
                    
                    if (debug):
                        logging.error("Infos "+str(stat))
                    else:
                        logging.warning("Infos "+str(stat))
                
                    outHandler.flush()
                    try:
                        if stat["size"]==0 :
                            logging.error(" nodes.json size == 0")
                            # code.interact(banner="Test stat0 :",local=dict(globals(), **locals()))
                            raise ValueError                        
                        # raise NodeSizeError
                        # Write nodes.json file in TVFile dir.
                        filetar = BytesIO()
                        for chunk in bits:
                            filetar.write(chunk)
                            # logging.error("chunk "+str(len(chunk)))
                        filetar.seek(0)
                        
                        # tf=tempfile.NamedTemporaryFile(mode="w+b",dir="/tmp",prefix="",suffix=".tar",delete=False)
                        # tf.write(filetar.read())
                        # tf.close()
                        
                        mytar=tarfile.TarFile(fileobj=filetar, mode='r')
                        mytar.extractall(self.dir_out)
                        mytar.close()
                        # os.system("ls -la "+self.dir_out)
                        filetar.close()

                    except ValueError as err:
                        traceback.print_exc(file=errors)
                        logging.error("ValueError with GET "+path_nodesjson+" : try again."+str(err))
                        time.sleep(2)
                        # Get back nodes.json from connection docker ?
                        bits, stat = self.containerConnect.get_archive(path=path_nodesjson)
                        if (debug):
                            logging.error("Infos "+str(stat))
                        else:
                            logging.warning("Infos "+str(stat))
                
                        outHandler.flush()
                        try:
                            if stat["size"]==0 :
                                logging.error("Infos "+str(stat))
                                logging.error(" nodes.json size == 0")
                                # code.interact(banner="Test stat0 :",local=dict(globals(), **locals()))
                                raise ValueError                        
                            # raise NodeSizeError
                            # Write nodes.json file in TVFile dir.
                            filetar = BytesIO()
                            for chunk in bits:
                                filetar.write(chunk)
                            filetar.seek(0)
                            
                            mytar=tarfile.TarFile(fileobj=filetar, mode='r')
                            mytar.extractall(self.dir_out)
                            mytar.close()
                            filetar.close()
                        except Exception as err:
                            traceback.print_exc(file=errors)
                            logging.error("Error with GET "+path_nodesjson+" : stop trying. "+str(err))

                    except Exception as err:
                        traceback.print_exc(file=errors)
                        logging.error("Error with GET "+path_nodesjson+". tar error.")

                        # Send again get via action launch_nodes_json
                        #raise ValueError                        
                        
                    nodes_ok=True
                    outHandler.flush()

                    # Server in TVSecure wait for connection from TVConnection in connectionDocker to send actions commands.
                    self.ActionConnect=sock.server(actionPort)
                    try:
                        logging.warning("Action server launched on "+str(actionPort)+".")
                        outHandler.flush()
                        self.ActionConnect.new_connect(1)
                        # Send Not an action message after Hello
                        HelloMsg=self.ActionConnect.recv(1)
                        logging.warning("Action client hello message : "+HelloMsg)
                        outHandler.flush()

                        self.ActionConnect.send_client(1,"Hello connection"+str(self.ConnectionDB.id))
                        logging.warning("Action client receive OK "+str(self.ActionConnect.get_OK(1)))
                        outHandler.flush()
                        
                        self.ActionConnect.send_client(1,"Not an action first.")
                        logging.warning("Action client receive OK from not-an-action message "+str(self.ActionConnect.get_OK(1)))
                        outHandler.flush()
                    except Exception as err:
                        traceback.print_exc(file=errors)
                        logging.error("Error with Action client "+str(self.ConnectionDB.id)+" : "+str(err))

                    self.killTunnel()
                    logging.warning("Job started.")
                    outHandler.flush()
                except:
                    outHandler.flush()
                    pass

            # Wrapper to private members :
            while( len(self.call_list) > 0 ):
                logging.warning("Container "+self.name+" call list : "+str(self.call_list))
                outHandler.flush()
                callfunc=self.call_list[0] 
                if callfunc == "updateScripts":
                    self.updateScripts()
                elif callfunc == "quitConnection":
                    logging.error("Before quitConnection : ")
                    self.quitConnection()
                elif callfunc == "killTunnel":
                    self.killTunnel()
                elif callfunc == "reconnect":
                    self.connect();
                elif (search_action.search(callfunc)):
                    logging.warning("Action detected "+str(callfunc))
                    self.action(callfunc)
                else:
                    logging.error("Error with calling function "+callfunc+ " for Connection "+self.name+" .")
                self.call_list.pop(0)

            if not self.isalive():
                self.quitConnection()
            # else:
            #     logging.debug("Connection "+str(self.connectionId)+" alive.")

            time.sleep(timeAliveConn)
            #logging.debug("Container loop.")

    def callfunction (self,myfunc):
        logging.debug("From Flask thread calling function "+myfunc+ " for Connection "+self.name+" .")
        self.call_list+=[myfunc]
        #logging.error("From Flask thread Container "+self.name+" call list : "+str(self.call_list))
            
    def updateScripts(self):
        logging.warning("updateScripts : Config files for tileset "+str(self.TileSetDB.config_files)+" and connection "+str(self.ConnectionDB.config_files))

        # Create a memory archive file for config files
        filetar = BytesIO()
        intar = tarfile.TarFile(fileobj=filetar, mode='w')
        ConnConfigFiles=self.ConnectionDB.config_files
        for filename in ConnConfigFiles:
            tmpfile=ConnConfigFiles[filename].replace("/TiledViz",".") 
            tf=open(tmpfile,'rb')
            tfd=tf.read()
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(tfd)
            tarinfo.mtime = time.time()
            tarinfo.uid = os.getuid()
            tarinfo.gid = os.getgid()
            intar.addfile(tarinfo, BytesIO(tfd))
            tf.close()
        
        TSConfigFiles=self.TileSetDB.config_files
        for filename in TSConfigFiles:
            tmpfile=TSConfigFiles[filename].replace("/TiledViz",".")
            tf=open(tmpfile,'rb')
            tfd=tf.read()
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(tfd)
            tarinfo.mtime = time.time()
            tarinfo.uid = os.getuid()
            tarinfo.gid = os.getgid()
            intar.addfile(tarinfo, BytesIO(tfd))
            tf.close()

        logging.warning("Config files for tileset "+str(self.TileSetDB.name)+" and connection "+str(self.ConnectionDB.id))
        intar.list()
        intar.close()
        filetar.seek(0)

        # Use put_archive to cp config files 
        self.LogPut=self.containerConnect.put_archive(path=self.home, data=filetar)
        logging.warning("Put config file to connection docker :\n"+str(self.LogPut))
        filetar.close()

    def killTunnel(self):
        # stop tunnel ssh for VNC
        self.LogTunnel=self.containerConnect.exec_run(cmd="sh -c "+self.kill_tunnel_script,user=self.user,detach=True)

        logging.warning("Kill tunnel end to Flask docker")
        # logging.warning("Kill tunnel to Flask docker :\n"+re.sub(r'\*n',r'\\n',self.LogTunnel))

    def quitConnection(self):
        # Erase login on flask
        commandRmuser="bash -c 'userdel -r -f "+self.flaskusr+"'"
        self.LogRmUser=container_exec_out(self.containerFlask, commandRmuser)
        logging.warning("Rm user "+self.flaskusr+" on Flask container."+re.sub(r'\*n',r'\\n',self.LogRmUser))

        # TODO : End action connection ?
        # suppress Action tunnel
        # killAction="sh -c \'Tunnel=$(pgrep -fla \"socat.*"+str(actionPort)+".*\" |grep -v -- \"-c\" | sed -e \"s@\\([0-^]*\\) .*@\\1@\"); echo $Tunnel; if [ X\"$Tunnel\" != X\"\" ]; then kill -9 $Tunnel; fi\' &"
        # self.LogKillAction=container_exec_out(self.containerConnect, killAction,user=self.user,detach=True)
        # logging.warning("Kill Action connection in conncetion docker :\n"+re.sub(r'\*n',r'\\n',self.LogKillAction))

        # suppress connection docker
        try:
            self.containerConnect.stop()
            if ( not self.cont_auto_remove ):
                self.containerConnect.remove(v=True,force=True)
        except:
            pass
        logging.warning("After remove "+self.name+", containers list :"+str(client.containers.list()))
        Connections[self.ConnectNum]=sqltConnections
        usedConnections[self.ConnectNum]=False
        logging.warning("Connection table :"+str(usedConnections))
        outHandler.flush()

        self.thread.join()
        
    def connect(self):
        logging.debug("Tunnel command in "+self.tunnel_script+" : "+self.tunnel_command)
        self.LogTunnel=self.containerConnect.exec_run(cmd="sh -c "+self.tunnel_script,user=self.user,detach=True)
        time.sleep(1)
        # outHandler.flush()
        # testTunnel="sh -c \'pgrep -fla \"ssh.*"+self.flaskusr+"\"\'"
        # self.LogTestTunnel=container_exec_out(self.containerConnect, testTunnel,user=self.user)
        # logging.debug("Tunnel to Flask docker :\n"+re.sub(r'\*n',r'\\n',self.LogTestTunnel))
        logging.warning("Container connected.")
        outHandler.flush()

    def action(self,callfunct):
        # Get action num + selection of tiles (if needed by the function)
        actionlist=re.sub(r'action=',r'',callfunct)
        #logging.warning("Action for tileset %s. command %s" % (self.tilesetId,actionlist))
        self.ActionConnect.send_client(1,actionlist)
        RET=self.ActionConnect.get_OK(1)
        logging.warning("Action for tileset %s. command %s return %d" % (self.tilesetId,actionlist,RET))
        if (re.sub(r',.*',r'',actionlist)=="0"):
            time.sleep(2)
            path_nodesjson=os.path.join(self.home,"nodes.json")
            try: 
                # Get back nodes.json from connection docker ?
                bits, stat = self.containerConnect.get_archive(path=path_nodesjson)
                logging.warning("GET renew "+path_nodesjson+ " file from Connection Docker.")
                logging.debug("Infos "+str(stat))
                os.system('mv -f '+self.dir_out+'nodes.json '+self.dir_out+'nodes.json.'+datetime.datetime.now().isoformat())
                # Write new nodes.json file in TVFile dir.
                filetar = BytesIO()
                for chunk in bits:
                    filetar.write(chunk)
                    filetar.seek(0)
                                    
                mytar=tarfile.TarFile(fileobj=filetar, mode='r')
                mytar.extractall(self.dir_out)
                mytar.close()
                filetar.close()
                #os.system('diff '+self.dir_out+'/nodes.json '+self.dir_out+'/tmp/nodes.json') 
            except:
                logging.error("Fail to renew "+path_nodesjson+ " from Connection Docker.")
                pass

    
    def isalive(self):
        # try:
        #     self.containerFlask.reload()
        # except:
        #     return False
        logging.debug("User container "+self.name+" status :"+str(self.containerFlask.status))
        return self.containerFlask.status == "running"
    
    def grepLog(self,nbLines,re_searchstr):
        self.Logs=str(self.containerConnect.logs(since=int(self.oldtime),tail=nbLines))
        self.oldtime=time.time()

        #logging.debug("\ngrepLog :\n"+self.Logs+"\n")
        m = re_searchstr.search(self.Logs)
        # m = re.search(searchstr,self.Logs,flags=0)
        #print(m,"\n\n")
        if m:
            for g in m.groups():
                logging.debug(g)
            return m

if __name__ == '__main__':
    logFormatter = logging.Formatter("TVSecure %(asctime)s - %(threadName)s - %(levelname)s: %(message)s ")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)
    fileHandler = logging.FileHandler("TVSecure.log")
    fileHandler.setLevel(logging.WARNING) #DEBUG
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)
    outHandler = logging.StreamHandler(sys.stdout)
    outLevel=logging.DEBUG
    #=logging.WARNING
    outHandler.setLevel(outLevel)
    outHandler.setFormatter(logFormatter)
    rootLogger.addHandler(outHandler)
    #rootLogger.handlers[0].flush()

    args = parse_args(sys.argv)
    #print("call args :",str(args))

    args.__dict__['host']=args.POSTGRES_HOST
    args.__dict__['login']=args.POSTGRES_USER
    args.__dict__['port']=args.POSTGRES_PORT
    args.__dict__['databasename']=args.POSTGRES_DB
    metadata, conn, engine, pool, session = tvdb.SQLconnector(args)
    
    FlaskDock= FlaskDocker(POSTGRES_HOST=args.POSTGRES_HOST,
                           POSTGRES_IP=args.POSTGRES_IP,
                           POSTGRES_PORT=args.POSTGRES_PORT,
                           POSTGRES_DB=args.POSTGRES_DB,
                           POSTGRES_USER=args.POSTGRES_USER,
                           POSTGRES_PASSWORD=args.POSTGRES_PASSWORD,
                           secretKey=args.secretKey)
    time.sleep(4)
    #FlaskDock.getLog(35)

    while (FlaskDock.isalive()):
        time.sleep(30)
        # time.sleep(5)
        #     logging.debug("Is Alive.")
        
    logging.critical('Finish')
