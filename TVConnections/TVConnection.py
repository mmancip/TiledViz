#!/bin/env python3

import datetime,time
import argparse

import sys,os,traceback
import pexpect,re
import platform
import threading

import code
from getpass import getpass

import logging

import inspect

sys.path.append(os.path.abspath('/TiledViz/TVDatabase'))
from TVDb import tvdb
from TVDb import models

# Add connect module directory
sys.path.append(os.path.realpath('/TiledViz/TVConnections/'))
from connect import sock
from connect.transfer import send_file_server, get_file_client

user='myuser'
ActionPort=64040


def containerId(num):
    return '{:03d}'.format(num)

def parse_args(argv):
    parser = argparse.ArgumentParser(
        'From a connection Id in PostgreSQL DB get connection parameters from TiledViz database.')
    parser.add_argument('--host', default='localhost',
                        help='Database host (default: localhost)')
    parser.add_argument('-l', '--login', default='tiledviz',
                        help='Database login (default: tiledviz)')
    parser.add_argument('-n', '--databasename', default='TiledViz',
                        help='Database name (default: TiledViz)')
    parser.add_argument('-u', '--usertest', default='ddurandi',
                        help='User name for test (default: ddurandi)')
    parser.add_argument('-c', '--connectionId', 
                        help='Connection Id in DB.')
    parser.add_argument('--debug', action='store_false',
                        help='Debug switch for new job.')

    args = parser.parse_args(argv[1:])
    return args

class ClientAction(threading.Thread):
    
    def __init__(self,connectionId,globals,locals):
        threading.Thread.__init__(self)
        self.thread = threading.Thread(target=self.run,args=(connectionId,globals,locals,)).start()

    def run(self,connectionId,globals,locals):

        self.actionclient=sock.client(ActionPort)
        self.actionclient.send_OK(1)
        logging.warning("ClientAction : connect server connectiondock")

        self.iter=0
        # Wait for commands by TVSecure.py
        while True:
            if (self.detect()):
                self.execute(globals,locals)
            time.sleep(0.1)

    def detect(self):
        global tiles_actions
        
        #logging.warning("ClientAction : detect")
        data=self.actionclient.recv()
        if not data:
            return False
        self.actionclient.send_OK(self.iter)
        self.iter=self.iter+1
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
            logging.error("ClientAction : error readding "+self.thisAction)
            self.isSelection=False
            return False
        
    def execute(self,globals,locals):
        # Separate Execute
        logging.debug("ClientAction : run")
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
                
if __name__ == '__main__':
    args = parse_args(sys.argv)

    logFormatter = logging.Formatter("TVConnection %(asctime)s - %(threadName)s - %(levelname)s: %(message)s ")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.WARNING)
    fileHandler = logging.FileHandler("/home/myuser/.vnc/TVConnection.log")
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
            UserFront = input("Enter your distant machine user name \n")
            while True:
                try:
                    Password = getpass("Enter your password for this user :\n")
                    break
                except UnicodeDecodeError:
                    logging.error("Error : only ascii chars are available.")
                    
        # After connection save (test save/restore container)
        resp=input("Hit enter or save connection data now of 'n' to change remote login/password.\n")

        if (resp != 'n'):
            
            sshKeyPath=os.path.join(os.getenv("HOME"),".ssh","id_rsa_"+Frontend)
            
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
                cmdcopy="ssh-copy-id -i "+sshKeyPath+".pub "+UserFront+"@"+Frontend 
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
                                logging.error("Error respond from server : "+str(childcopy.buffer.decode("utf-8")))
                            except:
                                logging.error("Error respond from server. "+expindex)
                        else:                        
                            logging.warning("ssh key copied on the server.")
                        childcopy.close(force=True)
                        if (childcopy.exitstatus == 0):
                            NOT_CONNECTED=False
                else:
                    try:
                        logging.warning("Error with copy id ")
                        logging.warning("buffer : "+childcopy.buffer.decode("utf-8"))
                        if (expindex == 3):
                            logging.warning("after TIMEOUT ")
                        else:
                            logging.warning("after "+childcopy.after.decode("utf-8"))
                        logging.warning("existstatus : ",childcopy.exitstatus, " signalestatus : ",childcopy.signalstatus)
                    except:                        
                        logging.warning("ssh key copied on the server.")

                    try:
                        code.interact(banner="Try connection :",local=dict(globals(), **locals()))
                    except SystemExit:
                        pass
                    childcopy.close(force=True)
                    if (childcopy.exitstatus == 0):
                        NOT_CONNECTED=False

    # Save/restore here ?
    TunnelFrontend = "ssh -4 -i "+sshKeyPath+" -T -N -nf -L 55554:localhost:55554  -L 2222:localhost:22 "+UserFront+"@"+Frontend
    logging.debug(TunnelFrontend)
    os.system(TunnelFrontend)
    logging.info("ssh tunneling OK.")

    lshome="ssh -i "+sshKeyPath+" -p 2222 "+UserFront+"@localhost 'ls $HOME/.tiledviz'"
    logging.debug(lshome)
    os.system(lshome)
    
    mkdirhome="ssh -i "+sshKeyPath+" -p 2222 "+UserFront+"@localhost 'mkdir $HOME/.tiledviz'"
    logging.debug(mkdirhome)
    os.system(mkdirhome)

    chmodhome="ssh -i "+sshKeyPath+" -p 2222 "+UserFront+"@localhost 'chmod og-rx $HOME/.tiledviz'"
    logging.debug(chmodhome)
    os.system(chmodhome)
    
    cmdhome="ssh -i "+sshKeyPath+" -p 2222 "+UserFront+"@localhost 'echo $HOME'"
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
    
    TiledVizPath=os.path.join(HomeFront,'.tiledviz')
    
    # import Swarm
    # if (TVconnection.scheduler_file != ""):
    #     logging.warning("From DB connection scheduler_file : "+str(TVconnection.scheduler_file))
    # logging.warning("Bye !")
    #time.sleep(10)

    DATE=re.sub(r'\..*','',datetime.datetime.isoformat(datetime.datetime.now(),sep='_').replace(":","-"))
    JOBPath=os.path.join(TiledVizPath,TileSet+'_'+DATE)

    if (TVconnection.auth_type == "ssh"):
        WorkdirFrontend = "ssh -i "+sshKeyPath+" -p 2222 "+UserFront+"@localhost mkdir "+JOBPath
        logging.debug(WorkdirFrontend)
        os.system(WorkdirFrontend)

    # prepare connect dir :
    CONNECTdir="/TiledViz/TVConnections/connect"
    CONNECTpath=os.path.join(JOBPath,"connect")
    
    ConnectdirFrontend = 'rsync -va -e "ssh -T -i '+sshKeyPath+' -p 2222 " '+CONNECTdir+' '+UserFront+"@localhost"+":"+JOBPath
    logging.debug(ConnectdirFrontend)
    os.system(ConnectdirFrontend)

    # Send or test TileServer run on server ??
    cmdServer="ssh -i "+sshKeyPath+" -p 2222 "+UserFront+"@localhost 'sh -c \"ps -Aef |grep TileServer |grep -v grep |grep "+UserFront+"\"'"
    logging.debug(cmdServer)
    childServer=pexpect.spawn(cmdServer)
    expindex=childServer.expect([pexpect.EOF, pexpect.TIMEOUT])
    if ( expindex == 0 ):
        ServerFront = childServer.before.decode("utf-8").replace("\n","").replace("\r","")
        logging.debug(ServerFront)
        if ( ServerFront == "" ):
            TileServerFrontend = 'scp -i '+sshKeyPath+' -P 2222 /TiledViz/TVConnections/TileServer.py  '+UserFront+"@localhost"+":"+TiledVizPath
            logging.debug(TileServerFrontend)
            os.system(TileServerFrontend)
            cmdTileServer="ssh -i "+sshKeyPath+" -p 2222 "+UserFront+"@localhost 'sh -c \"cd "+TiledVizPath+"; cp -rp "+os.path.join(JOBPath,"connect")+" .; HOSTNAME=\""+Frontend+"\" python3 TileServer.py > TileServer_"+DATE+".log 2>&1 & \"'"
            logging.debug(cmdTileServer)
            childTileServer=pexpect.spawn(cmdTileServer)
            expindex=childTileServer.expect([pexpect.EOF, pexpect.TIMEOUT])
            if ( expindex == 0 ):
                logging.debug("TileServer launched on frontend "+Frontend+" !")
                time.sleep(2)
            else:
                logging.warning("Error on TileServer launched on frontend "+Frontend+".")
            childTileServer.close(force=True)
    childServer.close(force=True)
    
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
    
    # Execute launch file
    try:
        client=sock.client()
        exec(compile(open(filename, "rb").read(), filename, 'exec'), globals(), locals())
        #filename.job(globals(), locals())
    except SystemExit:
        # Clean key :
        if (TVconnection.auth_type == "ssh"):
            myhostname=os.getenv('HOSTNAME', os.getenv('COMPUTERNAME', platform.node())).split('.')[0]
            CleanKeyFrontend = "ssh -i "+sshKeyPath+" -p 2222 "+UserFront+'@localhost bash -c \'\"sed -i.'+DATE+' /'+myhostname+'/d ~/.ssh/authorized_keys\"\''
            logging.debug(CleanKeyFrontend)
            os.system(CleanKeyFrontend)
        # On localhost (no need) "ssh-keygen -R "+Frontend+" -f ~/.ssh/known_hosts"
    except :
        traceback.print_exc(file=sys.stderr)
        #myglobals=globals()
        #code.interact(local=locals())
        pass
    
    
    # Kill ssh tunneling for VNC :
    #os.system("ps -Aef | grep 'connect.*@172.17.*' |grep -v grep | sed -e 's%myuser\\s*\\([0-9]*\\).*%\\1%' |xargs kill")
    os.system('killall -9 ssh')

    if (args.debug):
        try:
            code.interact(banner="Stop Connections :",local=dict(globals(), **locals()))
        except SystemExit:
            pass
        except :
            traceback.print_exc(file=sys.stderr)

