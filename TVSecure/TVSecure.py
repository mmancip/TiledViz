#! /usr/bin/env python
import subprocess
import threading

import time

import docker
import sys,os
import argparse
import json
import datetime
import traceback
import re

import argparse

import logging
errors=sys.stderr
error={"createError":1,"ImageError":2,"APIError":3,"start":4}

timeAlive=2

#sys.path.append(os.path.abspath('./'))

POSTGRES_HOST="postgres"
POSTGRES_IP="192.168.0.12"
POSTGRES_USER="tiledviz"
POSTGRES_DB="TiledViz"
POSTGRES_PASSWORD="m_test/@03"
secretKey="my Preci0us secr_t key for t&sts."

client = docker.from_env()
def parse_args(argv):
    parser = argparse.ArgumentParser(
        'Launch Flask docker with postgres parameters. Lauch on-demand connections.')
    parser.add_argument('--POSTGRES_HOST', default='postgres',
                        help='POSTGRES_HOST (default: postgres)')
    parser.add_argument('--POSTGRES_IP', default='192.168.0.12',
                        help='POSTGRES_IP (default: 192.168.0.12)')
    parser.add_argument('--POSTGRES_USER', default='tiledviz',
                        help='POSTGRES_USER (default: tiledviz)')
    parser.add_argument('--POSTGRES_DB', default='TiledViz',
                        help='POSTGRES_DB (Default: TiledViz)')
    parser.add_argument('--POSTGRES_PASSWORD', default='"m_test/@03"',
                        help='POSTGRES_PASSWORD (default: "m_test/@03")')
    parser.add_argument('--secretKey', default="my Preci0us secr_t key for t&sts.",
                        help='secretKey (default: "my Preci0us secr_t key for t&sts.")')
    args = parser.parse_args(argv[1:])
    return args

TVvolume=docker.types.Mount(target='/TiledViz',source=os.getenv('PWD'),type='bind',read_only=False)

threads={}
NbConnect=0
Connections=[]

ConnectionPort=54040
NbSecureConnection=10

class FlaskDocker(threading.Thread):
    def __init__(self,
                 POSTGRES_HOST=POSTGRES_HOST, POSTGRES_IP=POSTGRES_IP,
                 POSTGRES_DB=POSTGRES_DB, POSTGRES_USER=POSTGRES_USER, POSTGRES_PASSWORD=POSTGRES_PASSWORD,
                 secretKey=secretKey ):
        self.thread = threading.Thread(target=self.run, args=( POSTGRES_HOST, POSTGRES_IP,
                                                               POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD,
                                                               secretKey ))
        threads["flaskdock"]=self.thread
        self.thread.start()

    def run(self,
            POSTGRES_HOST=POSTGRES_HOST, POSTGRES_IP=POSTGRES_IP,
            POSTGRES_DB=POSTGRES_DB, POSTGRES_USER=POSTGRES_USER, POSTGRES_PASSWORD=POSTGRES_PASSWORD,
            secretKey=secretKey ):

        global NbConnect
        
        self.commandFlask=[POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, secretKey,str(os.getuid()),str(os.getgid())]
        
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

        try:
            self.containerFlask=client.containers.create(
                name="flaskdock", image="flaskimage",
                mounts=[TVvolume], extra_hosts=self.postgresHost,
                command=self.commandFlask,
                ports=self.flaskPORT,
                detach=True) #auto_remove=True,
            
        except docker.errors.ContainerError:
            logging.error("The container exits with a non-zero exit code and detach is False.")
            traceback.print_exc(file=errors)
            sys.exit(error["createError"])
        except docker.errors.ImageNotFound:
            logging.error("The specified image does not exist.")
            traceback.print_exc(file=errors)
            sys.exit(error["ImageError"])
        except docker.errors.APIError:
            logging.error("The server returns an error.")
            traceback.print_exc(file=errors)
            sys.exit(error["APIError"])
            
        self.user="flaskusr"
        self.idFlask = self.containerFlask.id

        self.daterun=datetime.datetime.now()
        logging.warning("Ready to start flaskdock.")
        try :
            self.containerFlask.start()
        except docker.errors.APIError :
            traceback.print_exc(file=errors)
            sys.exit(error["start"])
        
        logging.warning("After start Flask, containers list :"+str(client.containers.list()))

        self.containerFlask.reload()
        ipFlask = self.containerFlask.attrs["NetworkSettings"]["Networks"]["bridge"]["IPAddress"]
        logging.debug("We have built container for user "+self.user+" with postgresql user "+POSTGRES_USER+" and password '"+POSTGRES_PASSWORD+"' with IP "+ipFlask+".")
        logging.warning("Flask container status :"+str(self.containerFlask.status))

        # string from Flask for new connection
        searchnewconnection=r'WARNING:.*addconnection:\s*(?P<username>\w+)\s*;\s*(?P<hostname>\w+)\s*;\s*(?P<connection>\w+)\s*;\s*(?P<containers>\w+)\s*;\s*(?P<scheduler>\w+)\s*;\s*(?P<id>\d+)'
        search_newconnection = re.compile(r''+searchnewconnection)
        
        while True:
            # Detect all command to request new thread here
            # newconnection
            info_newconnect=self.grepLog(1,search_newconnection)
            # saveconnection
            # delconnection
            # restartconnection
            
            if info_newconnect:
                # test
                boolTestNotAlreadyConnect=(not all([ (info_newconnect.group("username") == Connections["username"] and
                               info_newconnect.group("hostname") == Connections["hostname"] and
                               info_newconnect.group("id") == Connections["connectionid"]) for Connections in Connections]))
                # logging.debug("test if connection (host) has not already been connected len(Connections) == 0 : "+str(len(Connections) == 0)
                #               +"; and boolTestNotAlreadyConnect = "+str(boolTestNotAlreadyConnect))
                if (len(Connections) == 0 or boolTestNotAlreadyConnect):
                    logging.warning("Get connection parameters :"+str(info_newconnect.groups()))
                    logging.debug("Connection "+str(NbConnect)+" container type :"+info_newconnect.group("containers"))
                    # then create the new connection
                    Connections.append({"username":info_newconnect.group("username"),
                                        "hostname":info_newconnect.group("hostname"),
                                        "connection":info_newconnect.group("connection"),
                                        "containers":info_newconnect.group("containers"),
                                        "connectionid":info_newconnect.group("id"),
                                        "ThisConnection":""})
                    ThisConnection=ConnectionDocker(self.containerFlask, POSTGRES_HOST, POSTGRES_IP, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
                    Connections[NbConnect]["ThisConnection"]=ThisConnection
                    NbConnect+=1
            time.sleep(timeAlive)
        

    def isalive(self):
        # try:
        #     self.containerFlask.reload()
        # except:
        #     return False
        logging.debug("Flask container status :"+str(self.containerFlask.status))
        return self.containerFlask.status == "running"
    
    def getLog(self,nbLines):
        # print(re.sub(r'\+n',r'\\n',str(self.Logs,'utf-8')))
        self.Logs=self.containerFlask.logs(timestamps=True,tail=nbLines).decode("utf-8")
        logging.warning(self.Logs)

    def grepLog(self,nbLines,re_searchstr):
        self.Logs=str(self.containerFlask.logs(tail=nbLines))

        # logging.debug("\ngrepLog :\n"+self.Logs+"\n")
        m = re_searchstr.search(self.Logs)
        # m = re.search(searchstr,self.Logs,flags=0)
        #print(m,"\n\n")
        if m:
            # for g in m.groups():
            #     logging.debug(g)
            return m

    def getContainerFlask():
        return self.containerFlask

class ConnectionDocker(threading.Thread):
    global NbConnect
    
    def __init__(self,containerFlask, 
                 POSTGRES_HOST=POSTGRES_HOST, POSTGRES_IP=POSTGRES_IP,
                 POSTGRES_DB=POSTGRES_DB, POSTGRES_USER=POSTGRES_USER, POSTGRES_PASSWORD=POSTGRES_PASSWORD):
        threading.Thread.__init__(self)
        self.thread = threading.Thread(target=self.run,args=(containerFlask,
                                                             POSTGRES_HOST, POSTGRES_IP,
                                                             POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD,)).start()

        time.sleep(10)
        threads[self.name]=self.thread
        #threading.Thread.__init__(self, target=self.run_forever)

    def run(self,containerFlask,
            POSTGRES_HOST=POSTGRES_HOST, POSTGRES_IP=POSTGRES_IP,
            POSTGRES_DB=POSTGRES_DB, POSTGRES_USER=POSTGRES_USER, POSTGRES_PASSWORD=POSTGRES_PASSWORD):

        self.name="connectiondock"+str(NbConnect)
        self.connectionId=int(Connections[NbConnect]["connectionid"])

        self.containerFlask = containerFlask
        self.IPFlask=self.containerFlask.attrs["NetworkSettings"]["Networks"]["bridge"]["IPAddress"]

        logging.warning("Connection creation :"+self.name)
        self.dir='/tmp/'+self.name
        if (not os.path.isdir(self.dir)): os.mkdir(self.dir)

        VncVolume=docker.types.Mount(source=self.dir,target="/home/myuser/.vnc",type='bind',read_only=False)
        XLocale=docker.types.Mount(source="/usr/share/X11/locale",target="/usr/share/X11/locale",type='bind')

        logging.debug("Input param commandConnect :"+str(self.connectionId)+" "+str(POSTGRES_HOST)+" "+str(POSTGRES_DB)+" "+str(POSTGRES_USER)+" "+str(POSTGRES_PASSWORD)+' -r '+' 1600x900'+' -u'+' 1002'+' -g'+' 1002')
#2019-05-09 15:11:54,670 - Thread-3 - ERROR: Input param commandConnect :<class 'int'><class 'int'><class 'str'><class 'str'><class 'str'>-r  1600x900 -u 1002 -g 1002 
#2019-05-09 15:25:02,157 - Thread-3 - ERROR: Input param commandConnect :2 0 TiledViz tiledviz m_test/@03 -r  1600x900 -u 1002 -g 1002 

        try:

            self.commandConnect=[str(self.connectionId),POSTGRES_HOST,POSTGRES_DB,POSTGRES_USER,POSTGRES_PASSWORD,'-r','1600x900','-u',str(os.getuid()),'-g',str(os.getgid())]
            
            self.containerConnect=client.containers.create(
                name=self.name, image="mageiaconnect",
                mounts=[VncVolume,XLocale], 
                command=self.commandConnect,
                devices=["/dev/nvidia0:/dev/nvidia0:rw","/dev/nvidiactl:/dev/nvidiactl:rw"],
                auto_remove=True, detach=True)

        except docker.errors.ContainerError:
            logging.error("The container exits with a non-zero exit code and detach is False.")
            traceback.print_exc(file=errors)
            sys.exit(error["createError"])
        except docker.errors.ImageNotFound:
            logging.error("The specified image does not exist.")
            traceback.print_exc(file=errors)
            sys.exit(error["ImageError"])
        except docker.errors.APIError:
            logging.error("The server returns an error.")
            traceback.print_exc(file=errors)
            sys.exit(error["APIError"])

        self.user="myuser"
        
        self.daterun=datetime.datetime.now()
        logging.warning("Ready to start "+self.name+".")
        try :
            self.containerConnect.start()
            logging.warning("Connection started.")
        except docker.errors.APIError :
            traceback.print_exc(file=errors)
            sys.exit(error["start"])
        
        logging.warning("After start "+self.name+", containers list :"+str(client.containers.list()))

        searchpassword=r'Random Password Generated:\s*(?P<passwd>[-._+0-9a-zA-Z]+)'
        search_passwd = re.compile(r''+searchpassword)
        while True:
            info_passwd=self.grepLog(2,search_passwd)
            if info_passwd:
                self.password=info_passwd.group("passwd")
                break
            time.sleep(1)

        self.containerConnect.reload()
        ipconnect = self.containerConnect.attrs["NetworkSettings"]["Networks"]["bridge"]["IPAddress"]
        logging.debug("We have built container for user "+self.user+"' with IP "+ipconnect+".")
        logging.warning("User container status :"+str(self.containerConnect.status))
        time.sleep(2)

        # Create temporary user on flask docker :
        flaskusr="connect"+str(self.connectionId)
        uid=str(1001+self.connectionId)
        gid=str(uid)
        uid=str(uid)
        commandAdduser="bash -c 'groupadd -r -g "+gid+" "+flaskusr+" && useradd -r -u "+uid+" -g "+flaskusr+" "+flaskusr+" && cp -rp /etc/skel /home/"+flaskusr+" && chown -R "+flaskusr+":"+flaskusr+" /home/"+flaskusr+"'"
        self.LogAddUser=self.containerFlask.exec_run(cmd=commandAdduser)
        logging.debug("Add user "+flaskusr+" on Flask container."+re.sub(r'\+n',r'\\n',str(self.LogAddUser.output,'utf-8')))
        
        # Get id_rsa.pub for tunneling VNC flux
        time.sleep(timeAlive)
        commandAuthKey = "cat /home/myuser/.ssh/id_rsa.pub"
        self.LogAuthorized_key = re.sub(r'\n',r'',str(self.containerConnect.exec_run(cmd=commandAuthKey).output,'utf-8'))
        # print("Key : ",self.LogAuthorized_key)
        authorized_key=re.sub(r'\+n',r'\\n',self.LogAuthorized_key)
        logging.debug("Authorized_key from connection container : \n|"+authorized_key+"|")

        # Put this key in flask docker
        commandBuildSsh="mkdir /home/"+flaskusr+"/.ssh"
        self.LogBuildSsh=self.containerFlask.exec_run(cmd=commandBuildSsh,user=flaskusr)
        logging.debug("Create .ssh to Flask docker :\n"+re.sub(r'\+n',r'\\n',str(self.LogBuildSsh.output,'utf-8')))
        commandBuildSsh="chmod 700 /home/"+flaskusr+"/.ssh"
        self.LogBuildSsh=self.containerFlask.exec_run(cmd=commandBuildSsh,user=flaskusr)
        logging.debug("Protect .ssh to Flask docker :\n"+re.sub(r'\+n',r'\\n',str(self.LogBuildSsh.output,'utf-8')))

        # Use awk to insert key in .ssh/authorized_key file !
        commandBuildSsh="awk 'BEGIN {print \""+authorized_key+"\" >>\"/home/"+flaskusr+"/.ssh/authorized_keys\"}' /dev/null"
        self.LogBuildSsh=self.containerFlask.exec_run(cmd=commandBuildSsh,user=flaskusr)
        logging.debug("Add autorized_key to Flask docker :\n"+re.sub(r'\+n',r'\\n',str(self.LogBuildSsh.output,'utf-8')))

        # List .ssh/authorized_key in Flask
        # commandBuildSsh="ls -la /home/"+flaskusr+"/.ssh/authorized_keys"
        # self.LogBuildSsh=self.containerFlask.exec_run(cmd=commandBuildSsh,user=flaskusr)
        # logging.debug("List .ssh/authorized_key in Flask docker :\n"+re.sub(r'\+n',r'\\n',str(self.LogBuildSsh.output,'utf-8')))

        # Add password for temporary connection
        commandBuildSsh="awk 'BEGIN {print \""+self.password+"\" >>\"/home/"+flaskusr+"/vncpassword\"}' /dev/null"
        self.LogBuildSsh=self.containerFlask.exec_run(cmd=commandBuildSsh,user=flaskusr)
        logging.debug("Add VNC password to Flask docker :\n"+re.sub(r'\+n',r'\\n',str(self.LogBuildSsh.output,'utf-8')))

        # TODO :
        #  Test connection type dans launch a script (in the start xterm full-screen ?) 
        # in python in container to manage the expect or get ssh private for HPC connection
        internPort=ConnectionPort+self.connectionId
        externPort=internPort
        #externPort=internPort+random.randint(100,400)
        #socatCMD="socat TCP-LISTEN:"+str(externPort)+",fork,reuseaddr TCP:127.0.0.1:"+str(internPort)
        #1 externPort = internPort avec GatewayPorts=yes
        #2 socat avec port extern sur un plage aléatoire ?
        # self.LogSocat=self.containerFlask.exec_run(cmd=socatCMD)
        # logging.debug("Socat "+str(internPort)+" to "+str(externPort)" :\n"+re.sub(r'\+n',r'\\n',str(self.LogSocat.output,'utf-8')))
        
        # Tunnel to Flask :( block this thread)
        commandTunnel="ssh -T -N -nf -R 0.0.0.0:"+str(externPort)+":localhost:5902 "+flaskusr+"@"+self.IPFlask
        print("Tunnel command : ",commandTunnel)
        self.LogTunnel=self.containerConnect.exec_run(cmd=commandTunnel,user="myuser")
        logging.debug("Tunnel to Flask docker :\n"+re.sub(r'\+n',r'\\n',str(self.LogTunnel.output,'utf-8')))

        # Get connection information : launch frontend on connectiondock
        # End of getinfo : stop tunnel, erase login on flask 

        
        while True:
            # Detect all command to request new thread here
            if not self.isalive():
                break
            time.sleep(timeAlive)

    def isalive(self):
        # try:
        #     self.containerFlask.reload()
        # except:
        #     return False
        logging.debug("User container "+self.name+" status :"+str(self.containerFlask.status))
        return self.containerFlask.status == "running"
            
    def grepLog(self,nbLines,re_searchstr):
        self.Logs=str(self.containerConnect.logs(tail=nbLines))

        #logging.debug("\ngrepLog :\n"+self.Logs+"\n")
        m = re_searchstr.search(self.Logs)
        # m = re.search(searchstr,self.Logs,flags=0)
        #print(m,"\n\n")
        if m:
            for g in m.groups():
                logging.debug(g)
            return m

if __name__ == '__main__':
    logFormatter = logging.Formatter("%(asctime)s - %(threadName)s - %(levelname)s: %(message)s ")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)
    fileHandler = logging.FileHandler("TVSecure.log")
    fileHandler.setLevel(logging.WARNING)
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)
    outHandler = logging.StreamHandler(sys.stdout)
    #outHandler.setLevel(logging.WARNING)
    outHandler.setLevel(logging.DEBUG)
    outHandler.setFormatter(logFormatter)
    rootLogger.addHandler(outHandler)

    args = parse_args(sys.argv)
    #print("call args :",str(args))
    
    FlaskDock= FlaskDocker(POSTGRES_HOST=args.POSTGRES_HOST,
                           POSTGRES_IP=args.POSTGRES_IP,
                           POSTGRES_DB=args.POSTGRES_DB,
                           POSTGRES_USER=args.POSTGRES_USER,
                           POSTGRES_PASSWORD=args.POSTGRES_PASSWORD,
                           secretKey=args.secretKey)
    time.sleep(4)
    FlaskDock.getLog(35)

    while (FlaskDock.isalive()):
        time.sleep(5)
        
    logging.critical('Finish')
