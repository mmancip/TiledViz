#!/bin/env python3

import datetime,time
import argparse

import sys,os,traceback
import pexpect,re
import platform

import code
from getpass import getpass

sys.path.append(os.path.abspath('/TiledViz/TVDatabase'))
from TVDb import tvdb
from TVDb import models

# Add connect module directory
sys.path.append(os.path.realpath('/TiledViz/TVConnections/'))
from connect import sock
from connect.transfer import send_file_server, get_file_client

user='myuser'

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

    args = parser.parse_args(argv[1:])
    return args

if __name__ == '__main__':
    args = parse_args(sys.argv)

    # Connection to DB
    metadata, conn, engine, pool, session = tvdb.SQLconnector(args)
    os.environ["POSTGRES_PASSWORD"]=""
    os.environ["passwordDB"]=""
    print("Build connection number ",args.connectionId)
    
    TVconnection=session.query(models.Connection).filter(models.Connection.id == int(args.connectionId)).one()
    print("From DB connection informations : ",str((TVconnection.auth_type,TVconnection.host_address,TVconnection.scheduler)))
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
            print("Distant machine frontend : "+Frontend)
            UserFront = input("Enter your distant machine user name \n")
            while True:
                try:
                    Password = getpass("Enter your password for this user :\n")
                    break
                except UnicodeDecodeError:
                    print("Error : only ascii chars are available.")
                    
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
                print("ssh key for this connection OK.")
                OK_Key=True
                
            if (TVconnection.auth_type == "ssh"):
                cmdcopy="ssh-copy-id -i "+sshKeyPath+".pub "+UserFront+"@"+Frontend 
                childcopy=pexpect.spawn(cmdcopy)
                #out1=childcopy.expect('.*')
                expindex=childcopy.expect([UserFront+"@"+Frontend+"\'s password: ", pexpect.EOF, pexpect.TIMEOUT])
                if (expindex == 0):
                    outpass = childcopy.sendline(Password)
                    if outpass < len(Password):
                        Password = getpass("Wrong password for "+UserFront+"@"+Frontend+". Try again enter your password for this user :\n")
                        childcopy.close(force=True)                    
                    else:
                        expindex=childcopy.expect([pexpect.EOF, pexpect.TIMEOUT])
                        if (expindex != 0):
                            print(childcopy.buffer.decode("utf-8"))
                        
                        print("ssh key copied on the server.")
                        childcopy.close(force=True)
                        if (childcopy.exitstatus == 0):
                            NOT_CONNECTED=False
                else:
                    sys.stderr.write("Error with copy id ")
                    sys.stderr.write("buffer : "+childcopy.buffer.decode("utf-8"))
                    sys.stderr.write("after : "+childcopy.after.decode("utf-8"))
                    sys.stderr.write("existstatus : ",childcopy.exitstatus, " signalestatus : ",childcopy.signalstatus)
                    # try:
                    #     code.interact(local=locals())
                    # except SystemExit:
                    #     pass

    # Save/restore here ?
    TunnelFrontend = "ssh -4 -i "+sshKeyPath+" -T -N -nf -L 55554:localhost:55554  -L 2222:localhost:22 "+UserFront+"@"+Frontend
    print(TunnelFrontend)
    os.system(TunnelFrontend)
    print("ssh tunneling OK.")

    lshome="ssh -i "+sshKeyPath+" -p 2222 "+UserFront+"@localhost 'ls $HOME/.tiledviz'"
    print(lshome)
    os.system(lshome)
    
    mkdirhome="ssh -i "+sshKeyPath+" -p 2222 "+UserFront+"@localhost 'mkdir $HOME/.tiledviz'"
    print(mkdirhome)
    os.system(mkdirhome)

    chmodhome="ssh -i "+sshKeyPath+" -p 2222 "+UserFront+"@localhost 'chmod og-rx $HOME/.tiledviz'"
    print(chmodhome)
    os.system(chmodhome)
    
    cmdhome="ssh -i "+sshKeyPath+" -p 2222 "+UserFront+"@localhost 'echo $HOME'"
    print(cmdhome)
    childhome=pexpect.spawn(cmdhome)
    expindex=childhome.expect([pexpect.EOF, pexpect.TIMEOUT])
    if ( expindex == 0 ):
        HomeFront = childhome.before.decode("utf-8").replace("\n","").replace("\r","")
        print(HomeFront)
    else:
        sys.stderr.write("Error with requiring remote 'home' dir.")
        HomeFront = os.path.join("/home",UserFront)
    childhome.close(force=True)
    
    TiledVizPath=os.path.join(HomeFront,'.tiledviz')
    
    # import Swarm
    # if (TVconnection.scheduler_file != ""):
    #     print("From DB connection scheduler_file : ",str(TVconnection.scheduler_file))
    # print("Bye !")
    #time.sleep(10)

    DATE=re.sub(r'\..*','',datetime.datetime.isoformat(datetime.datetime.now(),sep='_').replace(":","-"))
    JOBPath=os.path.join(TiledVizPath,TileSet+'_'+DATE)

    if (TVconnection.auth_type == "ssh"):
        WorkdirFrontend = "ssh -i "+sshKeyPath+" -p 2222 "+UserFront+"@localhost mkdir "+JOBPath
        print(WorkdirFrontend)
        os.system(WorkdirFrontend)

    # prepare connect dir :
    CONNECTdir="/TiledViz/TVConnections/connect"
    CONNECTpath=os.path.join(JOBPath,"connect")
    
    ConnectdirFrontend = 'rsync -va -e "ssh -T -i '+sshKeyPath+' -p 2222 " '+CONNECTdir+' '+UserFront+"@localhost"+":"+JOBPath
    print(ConnectdirFrontend)
    os.system(ConnectdirFrontend)

    # Send or test TileServer run on server ??
    cmdServer="ssh -i "+sshKeyPath+" -p 2222 "+UserFront+"@localhost 'sh -c \"ps -Aef |grep TileServer |grep -v grep |grep "+UserFront+"\"'"
    print(cmdServer)
    childServer=pexpect.spawn(cmdServer)
    expindex=childServer.expect([pexpect.EOF, pexpect.TIMEOUT])
    if ( expindex == 0 ):
        ServerFront = childServer.before.decode("utf-8").replace("\n","").replace("\r","")
        print(ServerFront)
        if ( ServerFront == "" ):
            TileServerFrontend = 'scp -i '+sshKeyPath+' -P 2222 /TiledViz/TVConnections/TileServer.py  '+UserFront+"@localhost"+":"+TiledVizPath
            print(TileServerFrontend)
            os.system(TileServerFrontend)
            cmdTileServer="ssh -i "+sshKeyPath+" -p 2222 "+UserFront+"@localhost 'sh -c \"cd "+TiledVizPath+"; cp -rp "+os.path.join(JOBPath,"connect")+" .; HOSTNAME=\""+Frontend+"\" python3 TileServer.py > TileServer_"+DATE+".log 2>&1 & \"'"
            print(cmdTileServer)
            childTileServer=pexpect.spawn(cmdTileServer)
            expindex=childTileServer.expect([pexpect.EOF, pexpect.TIMEOUT])
            if ( expindex == 0 ):
                print("TileServer launched on frontend "+Frontend+" !")
                time.sleep(2)
            else:
                sys.stderr.write("Error on TileServer launched on frontend "+Frontend+".")
            childTileServer.close(force=True)
    childServer.close(force=True)
    
    # Get Job file
    filename=TileSetDB.launch_file

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
    except SystemExit:
        # Clean key :
        if (TVconnection.auth_type == "ssh"):
            myhostname=os.getenv('HOSTNAME', os.getenv('COMPUTERNAME', platform.node())).split('.')[0]
            CleanKeyFrontend = "ssh -i "+sshKeyPath+" -p 2222 "+UserFront+'@localhost bash -c \'\"sed -i.'+DATE+' /'+myhostname+'/d ~/.ssh/authorized_keys\"\''
            print(CleanKeyFrontend)
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
