# -*- coding: utf-8 -*-

import socket
import sys,os,stat, errno
import logging
import platform
import configparser

import datetime

from .transfer import hashfile,readblock

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

    # Default port for connection between client in sock.py and TVSecure.py 
    PORTServer=int(config['sock']['PORTServer'])

    # Message fix size for data transfert through socket
    MSGsize=int(config['sock']['MSGsize'])
else:
    # Default port for connection between client in sock.py and TVSecure.py 
    PORTServer=55554
    
    # Message fix size for data transfert through socket
    MSGsize=1024

logFormatter = logging.Formatter("%(asctime)s - sock - %(threadName)s - %(levelname)s: %(message)s ")
#logging.basicConfig(level=logging.WARNING)
sockLogger = logging.getLogger("sock")
#sockLogger.setLevel(logging.ERROR)
sockLogger.setLevel(logging.WARNING)
#sockLogger.setLevel(logging.INFO)
#sockLogger.setLevel(logging.DEBUG)
#sockLogger.setLevel(9)
outHandler = logging.StreamHandler(sys.stdout)
outHandler.setFormatter(logFormatter)
sockLogger.addHandler(outHandler)

class client:
    def __init__(self,port=PORTServer):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(('localhost', port))
        sockLogger.log(9,str(self.s))

        Hostname=os.getenv("HOSTNAME", os.getenv('COMPUTERNAME', platform.node())).split('.')[0]
        HelloMsg=('Connection from '+Hostname).encode('utf-8').ljust(MSGsize,b'\00')
        sockLogger.warning(HelloMsg.rstrip(b'\00'))
        self.s.sendall(HelloMsg)

        data = self.s.recv(MSGsize).rstrip(b'\00')
        sockLogger.info('Received my hostname from server : %s' % (repr(data)))

    def send_server(self,command):
        sockLogger.log(9,"Send command '%s' to server." % (command))        
        self.s.sendall(command.replace("  "," ").encode('utf-8').ljust(MSGsize,b'\00'))

    def receive(self,nb):
        while True:
            sockLogger.log(9,"Wait for receive %d octets." % (nb))
            try:
                data = self.s.recv(nb)
            except socket.error as serr:
                if serr.errno != errno.ECONNREFUSED:
                    # Not the error we are looking for, re-raise
                    #raise serr
                    #errno  If using Python 3.3 it now has ConnectionRefusedError and socket.error is deprecated.
                    sockLogger.error("Error not ECONNREFUSED.")
                sockLogger.error("Error with connection to server. we quit with error %s " % (str(serr.errno)))
                sys.exit(serr.errno)
                # errno.ECONNABORTED
                # errno.ECONNRESET

            if not data: return False
            break
        data_ = str(data.rstrip(b'\x00').decode('utf-8'))
        return data_

    def recv(self):
        messg=self.receive(MSGsize)
        sockLogger.log(9,"Receive '%s' from server." % (messg))        
        return messg

    def send_OK(self,iRET):
        if not type(iRET)==int: 
            sockLogger.log(9,"iRET"+str(type(iRET)))
            self.s.sendall('ff'.encode('utf-8'))
        else:
            sRET=hex(iRET).replace('0x',"").encode('utf-8')
            if (len(sRET) < 2):
                sRET=b'0'+sRET
            elif(len(sRET)>2):
                sRET=sRET[(len(sRET)-2):len(sRET)]
            self.s.sendall(sRET)

    def get_OK(self):
        RET=self.receive(2)
        sockLogger.log(9,"Wait for OK from server : "+str(RET))
        intRET=-1
        if not RET: return intRET
        try:
            intRET=int(RET,16)
        except:
            sockLogger.error("OK error from server : "+str(RET)+self.receive(MSGsize-2))
        return intRET
 
    def send_file(self, path, filename):
        filein=os.path.join(path,filename)
        sockLogger.warning("Send data from file %s." % (filein))

        totbyte=0
        filesize=os.path.getsize(filein)
        f = open(filein,'rb')
        if (filesize < MSGsize):
            l = f.read(filesize).ljust(MSGsize,b'\00')
        else:
            l = f.read(MSGsize)
        #iter=0

        while (l):
            self.s.send(l)
            totbyte=totbyte+MSGsize
            # iter=iter+1
            # sockLogger.error("Client iter %d" % (iter))
            rest=filesize-totbyte;
            if (rest > MSGsize ):
                l = f.read(MSGsize)
            else:
                if (rest > 0):
                    l = f.read(rest).ljust(MSGsize,b'\00')
                    self.s.send(l)
                    # iter=iter+1
                    # sockLogger.error("Client rest %d iter %d" % (rest,iter))
                break

        f.close()
        sockLogger.warning("File sent.")

    def get_file(self, path, filename, filesize, filesha256):
        fileout=os.path.join(path,os.path.basename(filename))
        sockLogger.info("Wait for data of size %d and hash %s." % (filesize,filesha256))
        sockLogger.warning("Write data received from server in file %s." % (fileout))
        self.send_OK(0)

        Date=datetime.datetime.isoformat(datetime.datetime.now(),sep='_').replace(":","-")
        if (os.path.exists(fileout)):
            fileout_=fileout
            fileout=fileout+'_'+Date
            sockLogger.error("Can't overwrite existing file %s. Add date : %s" % (fileout_, fileout))
            
        try:
            f=open(fileout, 'wb')
            totbyte=0
            #iter=0
            while True:
                #iter=iter+1
                #sockLogger.error("Server iter %d" % (iter))
                data = self.s.recv(MSGsize)
                if not data:
                    break
                totbyte=totbyte+MSGsize
                if totbyte < filesize:
                    f.write(data)
                    sockLogger.log(9,'data %d inf %d=%s' % (totbyte,filesize,str(data)))
                else:
                    data=data.rstrip(b'\x00')
                    sockLogger.log(9,'data rest %d=%s' % (totbyte-filesize,str(data)))
                    f.write(data)
                    f.close()
                    break
        except socket.error as serr:
            sockLogger.error("Error with downloading file %s from %d : %s" % (str(fileout),id,str(serr)))
        except Exception as e:
            sockLogger.error("Unknown error with downloading file %s from %d : %s" % (str(fileout),id,str(e)))
        
        # Test for size and sha256 
        sockLogger.log(9,'Test for size and sha256 ')
        outsize = os.path.getsize(fileout)
        #statinfo = os.stat(fileout)
        #statinfo.st_size
        if ( not outsize == filesize ):
            sockLogger.error("File %s downloaded hasn't the size %d given by client : %d.\n It will be removed." % (fileout, filesize, outsize))
            #os.remove(fileout)
            self.send_OK(1)
            return 1

        filed=open(fileout, 'rb')
        outsha256=hashfile(readblock(filed))
        if ( outsha256 != filesha256 ):
            sockLogger.error("File %s downloaded hasn't the size %d given by client : %d.\n It will be removed." % (fileout, filesize, outsize))
            #os.remove(fileout)
            self.send_OK(2)
            return 1
        self.send_OK(0)
        return 0

    def close(self):
        self.s.close(); 


class server:
    def __init__(self, serverPORT):
        self.tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcpsock.bind(("",serverPORT))
        self.tcpsock.listen(200)
        self.clientsocket={}
        self.clientinfos={}
        self.clientids=[]

    def new_connect(self,id):
        (clientsocket, (ip, port)) = self.tcpsock.accept()
        self.clientsocket[id]=clientsocket
        self.clientids.append(id)
        self.clientinfos[id]=(ip, port)
        sockLogger.warning( "Accept port %d" % (port))
        sockLogger.info( "Accept %s ip %s port %d" % (str(clientsocket), str(ip), port))

    def send_client(self,id,command):
        self.clientsocket[id].sendall(command.replace("  "," ").encode('utf-8').ljust(MSGsize,b'\00'))
        # while True:
        #     self.s.recv(OK)
        #     if (int(OK)==1):
        #         break

    def receive(self,id,nb):
        sockLogger.log(9,"Wait from %d client for receive %d octets." % (id,nb))
        try:
            data = self.clientsocket[id].recv(nb)
        except socket.error as serr:
            if serr.errno != errno.ECONNREFUSED:
                # Not the error we are looking for, re-raise
                #raise serr
                #errno  If using Python 3.3 it now has ConnectionRefusedError and socket.error is deprecated.
                sockLogger.error("Not ECONNREFUSED.")
            sockLogger.error("Error with connection on client : %d . We quit with error %d " % (id , serr.errno))
            sys.exit(serr.errno)
            # errno.ECONNABORTED
            # errno.ECONNRESET

        if not data: return False
        data_ = str(data.rstrip(b'\x00').decode('utf-8'))
        return data_

    def recv(self,id):
        sockLogger.log(9,"wait for receive %d octets." % (MSGsize))
        return self.receive(id,MSGsize)

    def send_OK(self,id,iRET):
        sockLogger.log(9,"Send to %d status %d." % (id,iRET))
        sRET=hex(iRET).replace('0x',"").encode('utf-8')
        if (len(sRET) < 2):
            sRET=b'0'+sRET
        elif(len(sRET)>2):
            sRET=sRET[(len(sRET)-2):len(sRET)]
        self.clientsocket[id].sendall(sRET)

    def get_OK(self,id):
        sockLogger.log(9,"Wait for OK from %d." % (id))
        RET=self.receive(id,2)
        if not RET: return -1
        return int(RET,16)

    def get_file(self, id, path, filename, filesize, filesha256):
        fileout=os.path.join(path,os.path.basename(filename))
        sockLogger.warning("Write data received from %d in file %s." % (id,fileout))
        sockLogger.info("Wait for data of size %d and hash %s." % (filesize,filesha256))
        Date=datetime.datetime.isoformat(datetime.datetime.now(),sep='_').replace(":","-")
        if (os.path.exists(fileout)):
            fileout_=fileout
            fileout=fileout+'_'+Date
            sockLogger.error("Can't overwrite existing file %s. Add date : %s" % (fileout_, fileout))
            
        try:
            f=open(fileout, 'wb')
            totbyte=0
            # iter=0
            while True:
                # iter=iter+1
                # sockLogger.error("Server iter %d" % (iter))
                data = self.clientsocket[id].recv(MSGsize)
                if not data:
                    break
                totbyte=totbyte+MSGsize
                if totbyte < filesize:
                    f.write(data)
                    # sockLogger.log(9,'data %d inf %d=%s' % (totbyte,filesize,str(data)))
                else:
                    data=data.rstrip(b'\x00')
                    # sockLogger.log(9,'data rest %d=%s' % (totbyte-filesize,str(data)))
                    f.write(data)
                    f.close()
                    break
        except socket.error as serr:
            sockLogger.error("Error with downloading file %s from %d : %s" % (str(fileout),id,str(serr)))
        except Exception as e:
            sockLogger.error("Unknown error with downloading file %s from %d : %s" % (str(fileout),id,str(e)))
        
        # Test for size and sha256 
        sockLogger.log(9,'Test for size and sha256 ')
        outsize = os.path.getsize(fileout)
        #statinfo = os.stat(fileout)
        #statinfo.st_size
        if ( not outsize == filesize ):
            sockLogger.error("File %s downloaded hasn't the size %d given by client : %d.\n It will be removed." % (fileout, filesize, outsize))
            #os.remove(fileout)
            self.send_OK(id,1)
            return 1

        filed=open(fileout, 'rb')
        outsha256=hashfile(readblock(filed))
        if ( outsha256 != filesha256 ):
            sockLogger.error("File %s downloaded hasn't the size %d given by client : %d.\n It will be removed." % (fileout, filesize, outsize))
            #os.remove(fileout)
            self.send_OK(id,2)
            return 1
        self.send_OK(id,0)

    def send_file(self,id,path,filename):
        filein=os.path.join(path,filename)
        sockLogger.warning("Send data from file %s." % (filein))

        if (os.path.exists(filein)):
            self.send_OK(id,0)
            filesize = os.path.getsize(filein)
            filed=open(filein, 'rb')
            filesha256=hashfile(readblock(filed))
            filed.close()
            
            totbyte=0
            
            # Send filesize and filesha256 to client."
            command="fileinfos %s %d %s" % (filename,filesize,filesha256)
            sockLogger.info("Fileinfos sent to %d : %s." % (id,command))
            self.send_client(id,command)
            sockLogger.warning("Fileinfos sent : %s." % (str(self.get_OK(id))))
            
            f = open(filein,'rb') 
            if (filesize < MSGsize):
                l = f.read(filesize).ljust(MSGsize,b'\00')
            else:
                l = f.read(MSGsize)
            
            #iter=0
            while (l):
                self.clientsocket[id].send(l)
                totbyte=totbyte+MSGsize
                #iter=iter+1
                #sockLogger.error("Client iter %d" % (iter))
                rest=filesize-totbyte;
                if (rest > MSGsize ):
                    l = f.read(MSGsize)
                else:
                    if (rest > 0):
                        l = f.read(rest).ljust(MSGsize,b'\00')
                        self.clientsocket[id].send(l)
                        #iter=iter+1
                        #sockLogger.error("Client rest %d iter %d" % (rest,iter))
                    break
            
            f.close()
            sockLogger.warning("File sent : %s." % (str(self.get_OK(id))))
            self.send_OK(id,0)
            return (filesize,filesha256)
        else:
            FileERROR="File %s does not exist." % (filein)
            sockLogger.error(FileERROR)
            # response to ask
            self.send_OK(id,100)
            self.send_client(id,FileERROR)
            # response to send
            self.send_OK(id,110)
            return (0,0)

    def close(self,id):
        sockLogger.warning("Close client %d server %s." % (id,str(self.tcpsock)))
        self.clientsocket[id].close()

    def close_all(self):
        sockLogger.warning("Close server %s." % (str(self.tcpsock)))
        for id in self.clientids:
            self.clientsocket[id].close()
        time.sleep(2)
        self.tcpsock.close(); 
